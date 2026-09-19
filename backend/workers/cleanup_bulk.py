from datetime import datetime
from models import Session, BulkScanJob

def cleanup():
 s=Session()
 try:
  jobs=s.query(BulkScanJob).filter(BulkScanJob.expires_at<=datetime.utcnow(),BulkScanJob.status!='EXPIRED').all()
  for job in jobs:
   for item in job.items: item.normalized_url=None
   job.status='EXPIRED'
  s.commit(); return len(jobs)
 finally:s.close()
if __name__=='__main__': print(f'Expired {cleanup()} bulk jobs')
