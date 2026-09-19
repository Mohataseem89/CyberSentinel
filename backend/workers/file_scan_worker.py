"""Run as a separate, non-root process/container. Never import or execute uploaded content."""
import json, os, time
from datetime import datetime, timedelta
from sqlalchemy import text
from models import Session, FileScanJob
from services.clamav_adapter import ClamAVAdapter, ClamAVError
from services.html_static_analyzer import analyze_html_bytes

POLL=float(os.getenv('FILE_SCAN_WORKER_POLL_SECONDS','2'))
STALE=int(os.getenv('FILE_SCAN_STALE_SECONDS','300'))
MAX_ATTEMPTS=int(os.getenv('FILE_SCAN_MAX_ATTEMPTS','2'))
MAX_HTML=int(os.getenv('FILE_SCAN_HTML_MAX_BYTES','2097152'))
clam=ClamAVAdapter(os.getenv('CLAMAV_HOST','127.0.0.1'),int(os.getenv('CLAMAV_PORT','3310')),float(os.getenv('CLAMAV_TIMEOUT_SECONDS','30')),int(os.getenv('FILE_SCAN_MAX_BYTES','10485760')))

def claim():
    s=Session()
    try:
        # Recover work abandoned by a crashed worker. No uploaded content is executed.
        stale_before=datetime.utcnow()-timedelta(seconds=STALE)
        stale=s.query(FileScanJob).filter(FileScanJob.status=='SCANNING',FileScanJob.started_at<stale_before).all()
        for job in stale:
            if job.attempts>=MAX_ATTEMPTS:
                job.status='FAILED'; job.verdict='UNABLE_TO_COMPLETE'; job.error_code='worker_retry_exhausted'; job.completed_at=datetime.utcnow()
                if job.storage_path:
                    try: os.remove(job.storage_path)
                    except OSError: pass
                    job.storage_path=None
            else:
                job.status='QUEUED'; job.started_at=None
        s.commit()
        row=s.execute(text("SELECT id FROM file_scan_jobs WHERE status='QUEUED' AND expires_at > NOW() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1")).first()
        if not row: s.rollback(); return None
        job=s.get(FileScanJob,row[0]); job.status='SCANNING'; job.started_at=datetime.utcnow(); job.attempts+=1; s.commit(); return job.id
    finally:s.close()

def process(job_id):
    s=Session(); path=None
    try:
        job=s.get(FileScanJob,job_id)
        if not job or job.status!='SCANNING': return
        path=job.storage_path
        try:
            av=clam.scan_file(path)
            job.malware_status=av['status']
            if av['status']=='malware_detected':
                job.verdict='THREAT_DETECTED'; job.indicators_json=json.dumps([{'code':'antivirus_detection','severity':'high','signature':av.get('signature')}])
            else:
                html=None
                if job.detected_kind=='html':
                    with open(path,'rb') as f: raw=f.read(MAX_HTML+1)
                    if len(raw)>MAX_HTML: raise RuntimeError('html_too_large')
                    html=analyze_html_bytes(raw); job.html_risk=html['risk_level']; job.indicators_json=json.dumps(html['indicators'])
                if html and html['risk_level'] in {'medium','high'}: job.verdict='SUSPICIOUS_INDICATORS'
                else: job.verdict='CLEAN_CHECKS_COMPLETED'
            job.status='COMPLETED'
        except ClamAVError as e:
            job.status='FAILED'; job.error_code=e.code; job.verdict='UNABLE_TO_COMPLETE'; job.malware_status='scan_failed'
        except Exception:
            job.status='FAILED'; job.error_code='analysis_failed'; job.verdict='UNABLE_TO_COMPLETE'; job.malware_status=job.malware_status or 'scan_failed'
        finally:
            job.completed_at=datetime.utcnow(); job.storage_path=None
            if path:
                try: os.remove(path)
                except OSError: pass
        s.commit()
    finally:s.close()

def main():
    while True:
        jid=claim()
        if jid: process(jid)
        else: time.sleep(POLL)
if __name__=='__main__': main()
