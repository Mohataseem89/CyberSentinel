import os, uuid
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from models import Session, FileScanJob
from services.file_scan import stream_upload, safe_original_name, public_result
from services.file_types import detect_file, FileTypeError

file_scan_bp=Blueprint('file_scan',__name__)
ENABLED=os.getenv('FILE_SCAN_ENABLED','false').lower()=='true'
MAX_BYTES=int(os.getenv('FILE_SCAN_MAX_BYTES','10485760'))
MAX_ACTIVE=int(os.getenv('FILE_SCAN_MAX_ACTIVE_PER_USER','2'))
MAX_DAILY=int(os.getenv('FILE_SCAN_MAX_DAILY_PER_USER','20'))
RETENTION=int(os.getenv('FILE_SCAN_RESULT_RETENTION_HOURS','24'))
QUARANTINE=os.path.abspath(os.getenv('FILE_SCAN_QUARANTINE_DIR',os.path.join(os.path.dirname(__file__),'..','var','quarantine')))
ALLOWED={x.strip() for x in os.getenv('FILE_SCAN_ALLOWED_TYPES','html,text,pdf,png,jpeg,gif').split(',') if x.strip()}
ACTIVE={'QUEUED','SCANNING'}

def owned(s,pid,uid): return s.query(FileScanJob).filter(FileScanJob.public_id==pid,FileScanJob.user_id==int(uid)).first()

@file_scan_bp.get('/file-scans/capabilities')
@jwt_required()
def capabilities():
    return jsonify({'enabled':ENABLED,'max_bytes':MAX_BYTES,'allowed_types':sorted(ALLOWED),'archives_supported':False,'consent_required':True})

@file_scan_bp.post('/file-scans')
@jwt_required()
def create_file_scan():
    if not ENABLED: return jsonify({'error':'File analysis is currently disabled.','code':'feature_disabled'}),503
    if request.form.get('consent')!='true': return jsonify({'error':'Explicit analysis consent is required.','code':'consent_required'}),400
    upload=request.files.get('file')
    if not upload or not upload.filename: return jsonify({'error':'A file is required.','code':'file_required'}),400
    uid=int(get_jwt_identity()); s=Session(); path=None
    try:
        now=datetime.utcnow()
        if s.query(FileScanJob).filter(FileScanJob.user_id==uid,FileScanJob.status.in_(ACTIVE)).count()>=MAX_ACTIVE:
            return jsonify({'error':'Active file scan limit reached.','code':'active_scan_quota'}),429
        if s.query(FileScanJob).filter(FileScanJob.user_id==uid,FileScanJob.created_at>=now-timedelta(days=1)).count()>=MAX_DAILY:
            return jsonify({'error':'Daily file scan limit reached.','code':'daily_scan_quota'}),429
        try: path,size,digest=stream_upload(upload,QUARANTINE,MAX_BYTES)
        except ValueError as e:
            code=str(e); msg='File is too large.' if code=='file_too_large' else 'Empty files are not accepted.'
            return jsonify({'error':msg,'code':code}),413 if code=='file_too_large' else 400
        try: detected=detect_file(path,ALLOWED)
        except FileTypeError as e:
            os.remove(path); path=None
            return jsonify({'error':e.message,'code':e.code}),415
        job=FileScanJob(public_id=str(uuid.uuid4()),user_id=uid,status='QUEUED',original_name=safe_original_name(upload.filename),storage_path=path,sha256=digest,size_bytes=size,detected_kind=detected.kind,detected_mime=detected.mime,created_at=now,expires_at=now+timedelta(hours=RETENTION))
        s.add(job); s.commit(); path=None
        return jsonify({'job':public_result(job)}),202
    finally:
        if path:
            try: os.remove(path)
            except OSError: pass
        s.close()

@file_scan_bp.get('/file-scans')
@jwt_required()
def list_file_scans():
    s=Session()
    try: return jsonify({'jobs':[public_result(j) for j in s.query(FileScanJob).filter_by(user_id=int(get_jwt_identity())).order_by(FileScanJob.created_at.desc()).limit(50)]})
    finally:s.close()

@file_scan_bp.get('/file-scans/<job_id>')
@jwt_required()
def get_file_scan(job_id):
    s=Session()
    try:
        job=owned(s,job_id,get_jwt_identity())
        if not job:return jsonify({'error':'Scan job not found.'}),404
        return jsonify({'job':public_result(job)})
    finally:s.close()
