"""PostgreSQL-backed bulk worker. Run as a separate production process."""
import logging, os, time
from datetime import datetime, timedelta
from sqlalchemy import text
from models import Session, BulkScanJob, BulkScanItem
from services.url_analyzer import HybridURLAnalyzer
from workers.cleanup_bulk import cleanup

log=logging.getLogger(__name__)
POLL=float(os.getenv('BULK_WORKER_POLL_SECONDS','2'))
RETRIES=int(os.getenv('BULK_ITEM_MAX_RETRIES','2'))
STALE=int(os.getenv('BULK_JOB_STALE_SECONDS','900'))
CLEANUP_INTERVAL=int(os.getenv('BULK_CLEANUP_INTERVAL_SECONDS','3600'))

def recover_stale():
    s=Session()
    try:
        cutoff=datetime.utcnow()-timedelta(seconds=STALE)
        jobs=s.query(BulkScanJob).filter(BulkScanJob.status=='RUNNING',BulkScanJob.started_at<cutoff).all()
        for job in jobs:
            for item in job.items:
                if item.status=='RUNNING': item.status='QUEUED'
            job.status='QUEUED'; job.started_at=None
        s.commit()
        if jobs: log.warning('Recovered %s stale bulk jobs',len(jobs))
    finally:s.close()

def claim_job():
    s=Session()
    try:
        row=s.execute(text("SELECT id FROM bulk_scan_jobs WHERE status='QUEUED' AND expires_at > NOW() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1")).first()
        if not row:s.rollback();return None
        job=s.get(BulkScanJob,row[0]);job.status='RUNNING';job.started_at=datetime.utcnow();s.commit();return job.id
    finally:s.close()

def process(job_id):
    analyzer=HybridURLAnalyzer()
    while True:
        s=Session()
        try:
            job=s.get(BulkScanJob,job_id)
            if not job or job.status not in {'RUNNING','CANCELLING'}: return
            if job.expires_at<=datetime.utcnow(): job.status='EXPIRED';job.completed_at=datetime.utcnow();s.commit();return
            if job.status=='CANCELLING': job.status='CANCELLED';job.completed_at=datetime.utcnow();s.commit();return
            item=s.query(BulkScanItem).filter_by(job_id=job_id,status='QUEUED').order_by(BulkScanItem.row_number).first()
            if not item:
                job.status='PARTIALLY_COMPLETED' if job.failed else 'COMPLETED';job.completed_at=datetime.utcnow();s.commit();return
            item.status='RUNNING';s.commit(); url=item.normalized_url; item_id=item.id
        finally:s.close()
        try:
            result=analyzer.analyze(url); verdict=result.get('final_verdict','Unknown'); score=result.get('threat_score')
            s=Session(); item=s.get(BulkScanItem,item_id); job=s.get(BulkScanJob,job_id)
            if not item or not job: s.close(); return
            item.status='COMPLETED';item.final_verdict=verdict;item.threat_score=score;item.normalized_url=None;job.processed+=1;job.successful+=1;s.commit();s.close()
        except Exception:
            log.exception('Bulk item scan failed job_id=%s item_id=%s',job_id,item_id)
            s=Session(); item=s.get(BulkScanItem,item_id); job=s.get(BulkScanJob,job_id)
            if not item or not job: s.close(); return
            item.attempts+=1; attempts=item.attempts
            if attempts<=RETRIES:item.status='QUEUED'
            else:item.status='FAILED';item.error_code='scan_failed';item.normalized_url=None;job.processed+=1;job.failed+=1
            s.commit();s.close();time.sleep(min(2**max(attempts,1),8))

def main():
    """
    Process queued bulk jobs.

    Default mode is run-to-completion for Cloud Run Jobs:
    process all currently queued jobs, then exit.

    Set BULK_WORKER_CONTINUOUS=true only when running as a
    traditional always-on background worker.
    """
    continuous = os.getenv(
        "BULK_WORKER_CONTINUOUS", "false"
    ).strip().lower() in {"1", "true", "yes"}

    recover_stale()

    try:
        cleanup()
    except Exception:
        log.exception("Bulk retention cleanup failed")

    while True:
        job_id = claim_job()

        if job_id:
            log.info("Processing bulk job %s", job_id)
            process(job_id)
            continue

        if not continuous:
            log.info("No queued bulk jobs. Worker exiting.")
            return

        time.sleep(POLL)


if __name__ == "__main__":
    main()
