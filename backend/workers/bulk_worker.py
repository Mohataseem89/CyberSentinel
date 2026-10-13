"""PostgreSQL-backed bulk worker. Run as a separate production process."""

import logging
import os
import time
from datetime import datetime, timedelta

from sqlalchemy import text

from models import Session, BulkScanJob, BulkScanItem
from services.url_analyzer import HybridURLAnalyzer
from workers.cleanup_bulk import cleanup


log = logging.getLogger(__name__)

POLL = float(os.getenv("BULK_WORKER_POLL_SECONDS", "2"))
RETRIES = int(os.getenv("BULK_ITEM_MAX_RETRIES", "2"))
STALE = int(os.getenv("BULK_JOB_STALE_SECONDS", "900"))
CLEANUP_INTERVAL = int(
    os.getenv("BULK_CLEANUP_INTERVAL_SECONDS", "3600")
)


def recover_stale():
    """Return stale RUNNING jobs/items to the queue."""

    s = Session()

    try:
        cutoff = datetime.utcnow() - timedelta(seconds=STALE)

        jobs = (
            s.query(BulkScanJob)
            .filter(
                BulkScanJob.status == "RUNNING",
                BulkScanJob.started_at < cutoff,
            )
            .all()
        )

        for job in jobs:
            for item in job.items:
                if item.status == "RUNNING":
                    item.status = "QUEUED"

            job.status = "QUEUED"
            job.started_at = None

        s.commit()

        if jobs:
            log.warning(
                "Recovered %s stale bulk jobs",
                len(jobs),
            )

    finally:
        s.close()


def claim_job():
    """Atomically claim the oldest queued, non-expired job."""

    s = Session()

    try:
        row = s.execute(
            text(
                """
                SELECT id
                FROM bulk_scan_jobs
                WHERE status = 'QUEUED'
                  AND expires_at > NOW()
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
                """
            )
        ).first()

        if not row:
            s.rollback()
            return None

        job = s.get(BulkScanJob, row[0])

        if not job:
            s.rollback()
            return None

        job.status = "RUNNING"
        job.started_at = datetime.utcnow()

        s.commit()

        return job.id

    finally:
        s.close()


def process(job_id):
    """
    Process one bulk scan job.

    The analyzer is created lazily only after an actual queued item has
    been claimed. This prevents unnecessary analyzer initialization for
    cancelled, expired, or already-completed jobs.
    """

    analyzer = None

    while True:
        s = Session()

        try:
            job = s.get(BulkScanJob, job_id)

            if not job:
                return

            if job.status not in {"RUNNING", "CANCELLING"}:
                return

            # The retention window expired while the job was running.
            if job.expires_at <= datetime.utcnow():
                for item in job.items:
                    if item.status in {"QUEUED", "RUNNING"}:
                        item.normalized_url = None

                job.status = "EXPIRED"
                job.completed_at = datetime.utcnow()

                s.commit()
                return

            # Cancellation must happen before analyzer construction.
            if job.status == "CANCELLING":
                for item in job.items:
                    if item.status in {"QUEUED", "RUNNING"}:
                        item.normalized_url = None

                job.status = "CANCELLED"
                job.completed_at = datetime.utcnow()

                s.commit()
                return

            item = (
                s.query(BulkScanItem)
                .filter_by(
                    job_id=job_id,
                    status="QUEUED",
                )
                .order_by(BulkScanItem.row_number)
                .first()
            )

            # No queued items remain. Finalize the job.
            if not item:
                job.status = (
                    "PARTIALLY_COMPLETED"
                    if job.failed
                    else "COMPLETED"
                )
                job.completed_at = datetime.utcnow()

                s.commit()
                return

            item.status = "RUNNING"
            s.commit()

            url = item.normalized_url
            item_id = item.id

        finally:
            s.close()

        # Do not initialize the analyzer until there is work to do.
        if analyzer is None:
            analyzer = HybridURLAnalyzer()

        try:
            result = analyzer.analyze(url)

            verdict = result.get(
                "final_verdict",
                "Unknown",
            )
            score = result.get("threat_score")

            s = Session()

            try:
                item = s.get(BulkScanItem, item_id)
                job = s.get(BulkScanJob, job_id)

                if not item or not job:
                    return

                item.status = "COMPLETED"
                item.final_verdict = verdict
                item.threat_score = score

                # Do not retain the normalized/raw working URL after
                # processing has completed.
                item.normalized_url = None

                job.processed += 1
                job.successful += 1

                s.commit()

            finally:
                s.close()

        except Exception:
            log.exception(
                "Bulk item scan failed job_id=%s item_id=%s",
                job_id,
                item_id,
            )

            s = Session()

            try:
                item = s.get(BulkScanItem, item_id)
                job = s.get(BulkScanJob, job_id)

                if not item or not job:
                    return

                item.attempts += 1
                attempts = item.attempts

                if attempts <= RETRIES:
                    # Retry this item on the next loop iteration.
                    item.status = "QUEUED"

                else:
                    # Retry budget exhausted.
                    item.status = "FAILED"
                    item.error_code = "scan_failed"
                    item.normalized_url = None

                    job.processed += 1
                    job.failed += 1

                s.commit()

            finally:
                s.close()

            # Small bounded exponential backoff.
            time.sleep(
                min(
                    2 ** max(attempts, 1),
                    8,
                )
            )


def main():
    """
    Process queued bulk jobs.

    Default mode is run-to-completion for Cloud Run Jobs:
    process all currently queued jobs, then exit.

    Set BULK_WORKER_CONTINUOUS=true only when running as a
    traditional always-on background worker.
    """

    continuous = (
        os.getenv(
            "BULK_WORKER_CONTINUOUS",
            "false",
        )
        .strip()
        .lower()
        in {"1", "true", "yes"}
    )

    # Recover jobs abandoned by a previous worker execution.
    recover_stale()

    # Apply retention cleanup whenever the Cloud Run job starts.
    try:
        cleanup()
    except Exception:
        log.exception(
            "Bulk retention cleanup failed"
        )

    while True:
        job_id = claim_job()

        if job_id:
            log.info(
                "Processing bulk job %s",
                job_id,
            )
            process(job_id)
            continue

        # Cloud Run Jobs use run-to-completion mode.
        if not continuous:
            log.info(
                "No queued bulk jobs. Worker exiting."
            )
            return

        time.sleep(POLL)


if __name__ == "__main__":
    main()