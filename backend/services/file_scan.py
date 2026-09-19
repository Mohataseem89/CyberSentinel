"""Shared Phase 17 validation/result helpers."""
import hashlib, os, re, uuid
from pathlib import Path
from services.file_types import detect_file

TERMINAL={'COMPLETED','REJECTED','FAILED','EXPIRED'}

def safe_original_name(name):
    raw=os.path.basename((name or '').replace('\\','/'))
    value=re.sub(r'[^A-Za-z0-9._-]+','_',raw).strip('._')[:120]
    return value or 'upload'

def stream_upload(upload, directory, max_bytes):
    Path(directory).mkdir(parents=True, exist_ok=True)
    tmp=Path(directory)/(uuid.uuid4().hex+'.upload')
    size=0; digest=hashlib.sha256()
    try:
        with tmp.open('xb') as out:
            while True:
                chunk=upload.stream.read(65536)
                if not chunk: break
                size+=len(chunk)
                if size>max_bytes: raise ValueError('file_too_large')
                digest.update(chunk); out.write(chunk)
        if size==0: raise ValueError('empty_file')
        return str(tmp), size, digest.hexdigest()
    except Exception:
        tmp.unlink(missing_ok=True); raise

def public_result(job):
    result={
      'id':job.public_id,'status':job.status,'file_name':job.original_name,'file_type':job.detected_kind,
      'mime_type':job.detected_mime,'size_bytes':job.size_bytes,'verdict':job.verdict,
      'malware_status':job.malware_status,'html_risk':job.html_risk,'error_code':job.error_code,
      'created_at':job.created_at.isoformat() if job.created_at else None,
      'started_at':job.started_at.isoformat() if job.started_at else None,
      'completed_at':job.completed_at.isoformat() if job.completed_at else None,
      'expires_at':job.expires_at.isoformat() if job.expires_at else None,
    }
    if job.indicators_json:
        import json
        try: result['indicators']=json.loads(job.indicators_json)
        except Exception: result['indicators']=[]
    else: result['indicators']=[]
    return result
