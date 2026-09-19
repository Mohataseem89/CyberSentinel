import os
from datetime import datetime
from models import Session, FileScanJob

def cleanup():
    s=Session(); count=0
    try:
        jobs=s.query(FileScanJob).filter(FileScanJob.expires_at<=datetime.utcnow()).all()
        for job in jobs:
            if job.storage_path:
                try: os.remove(job.storage_path)
                except OSError: pass
            s.delete(job); count+=1
        s.commit(); return count
    finally:s.close()
if __name__=='__main__': print(f'Deleted {cleanup()} expired file-scan jobs')
