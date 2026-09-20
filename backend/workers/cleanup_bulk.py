"""Hard-delete expired bulk jobs/results to enforce configured retention."""
from datetime import datetime
from models import Session, BulkScanJob

def cleanup():
    s=Session()
    try:
        jobs=s.query(BulkScanJob).filter(BulkScanJob.expires_at<=datetime.utcnow()).all()
        count=len(jobs)
        for job in jobs: s.delete(job)
        s.commit(); return count
    finally:s.close()
if __name__=='__main__': print(f'Deleted {cleanup()} expired bulk jobs')
