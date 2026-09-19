"""PostgreSQL-backed bulk worker. Run as a separate process."""
import os,time
from datetime import datetime
from sqlalchemy import text
from models import Session, BulkScanJob, BulkScanItem
from services.url_analyzer import HybridURLAnalyzer

POLL=float(os.getenv('BULK_WORKER_POLL_SECONDS','2')); RETRIES=int(os.getenv('BULK_ITEM_MAX_RETRIES','2'))

def claim_job():
 s=Session()
 try:
  row=s.execute(text("SELECT id FROM bulk_scan_jobs WHERE status='QUEUED' AND expires_at > NOW() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1")).first()
  if not row:s.rollback();return None
  job=s.get(BulkScanJob,row[0]);job.status='RUNNING';job.started_at=job.started_at or datetime.utcnow();s.commit();return job.id
 finally:s.close()

def process(job_id):
 analyzer=HybridURLAnalyzer()
 while True:
  s=Session()
  try:
   job=s.get(BulkScanJob,job_id)
   if not job:return
   if job.status=='CANCELLING': job.status='CANCELLED';job.completed_at=datetime.utcnow();s.commit();return
   item=s.query(BulkScanItem).filter_by(job_id=job_id,status='QUEUED').order_by(BulkScanItem.row_number).first()
   if not item:
    job.status='PARTIALLY_COMPLETED' if job.failed else 'COMPLETED';job.completed_at=datetime.utcnow();s.commit();return
   item.status='RUNNING';s.commit(); url=item.normalized_url; item_id=item.id
  finally:s.close()
  try:
   result=analyzer.analyze(url); verdict=result.get('final_verdict','Unknown'); score=result.get('threat_score')
   s=Session(); item=s.get(BulkScanItem,item_id); job=s.get(BulkScanJob,job_id); item.status='COMPLETED';item.final_verdict=verdict;item.threat_score=score;item.normalized_url=None;job.processed+=1;job.successful+=1;s.commit();s.close()
  except Exception:
   s=Session(); item=s.get(BulkScanItem,item_id); job=s.get(BulkScanJob,job_id); item.attempts+=1
   if item.attempts<=RETRIES:item.status='QUEUED'
   else:item.status='FAILED';item.error_code='scan_failed';item.normalized_url=None;job.processed+=1;job.failed+=1
   s.commit();s.close();time.sleep(min(2**max(item.attempts,1),8))

def main():
 while True:
  job_id=claim_job()
  if job_id:process(job_id)
  else:time.sleep(POLL)
if __name__=='__main__':main()
