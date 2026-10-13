"""Hard-delete expired bulk jobs/results to enforce configured retention."""
from datetime import datetime
from models import Session, BulkScanJob


def cleanup(now=None):
    """Delete expired jobs. ORM delete-orphan cascade removes their result rows."""
    session = Session()
    try:
        cutoff = now or datetime.utcnow()
        jobs = session.query(BulkScanJob).filter(BulkScanJob.expires_at <= cutoff).all()
        count = len(jobs)
        for job in jobs:
            session.delete(job)
        session.commit()
        return count
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print(f"Deleted {cleanup()} expired bulk jobs")
