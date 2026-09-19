import csv, io, os, uuid
from datetime import datetime, timedelta
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from models import Session, BulkScanJob, BulkScanItem
from services.bulk_scan import BulkValidationError, parse_csv_bytes, csv_safe, can_transition

bulk_bp=Blueprint('bulk',__name__)
MAX_BYTES=int(os.getenv('BULK_MAX_CSV_BYTES','1048576')); MAX_URLS=int(os.getenv('BULK_MAX_URLS_PER_JOB','1000')); MAX_ACTIVE=int(os.getenv('BULK_MAX_ACTIVE_JOBS_PER_USER','2')); MAX_DAILY=int(os.getenv('BULK_MAX_JOBS_PER_DAY','10')); RETENTION_HOURS=int(os.getenv('BULK_RETENTION_HOURS','24'))
ACTIVE={'QUEUED','RUNNING','CANCELLING'}

def owned_job(session,job_id,user_id): return session.query(BulkScanJob).filter(BulkScanJob.public_id==job_id,BulkScanJob.user_id==int(user_id)).first()
def serialize(job):
    remaining=max(job.total_urls-job.processed,0); pct=round((job.processed/job.total_urls)*100,1) if job.total_urls else 0
    return {'id':job.public_id,'status':job.status,'total':job.total_urls,'processed':job.processed,'successful':job.successful,'failed':job.failed,'remaining':remaining,'progress_percent':pct,'created_at':job.created_at.isoformat() if job.created_at else None,'started_at':job.started_at.isoformat() if job.started_at else None,'completed_at':job.completed_at.isoformat() if job.completed_at else None,'expires_at':job.expires_at.isoformat() if job.expires_at else None}

@bulk_bp.post('/bulk/jobs')
@jwt_required()
def create_job():
    upload=request.files.get('file'); user_id=int(get_jwt_identity())
    if not upload or not upload.filename: return jsonify({'error':'CSV file is required.','code':'file_required'}),400
    if not upload.filename.lower().endswith('.csv'): return jsonify({'error':'Only .csv files are accepted.','code':'invalid_file_type'}),415
    raw=upload.stream.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: return jsonify({'error':'CSV is too large.','code':'file_too_large'}),413
    try: rows,validation_errors=parse_csv_bytes(raw,MAX_URLS)
    except BulkValidationError as e: return jsonify({'error':e.message,'code':e.code}),400
    s=Session()
    try:
      now=datetime.utcnow(); active=s.query(BulkScanJob).filter(BulkScanJob.user_id==user_id,BulkScanJob.status.in_(ACTIVE)).count()
      daily=s.query(BulkScanJob).filter(BulkScanJob.user_id==user_id,BulkScanJob.created_at>=now-timedelta(days=1)).count()
      if active>=MAX_ACTIVE: return jsonify({'error':'Active bulk job limit reached.','code':'active_job_quota'}),429
      if daily>=MAX_DAILY: return jsonify({'error':'Daily bulk job limit reached.','code':'daily_job_quota'}),429
      job=BulkScanJob(public_id=str(uuid.uuid4()),user_id=user_id,status='QUEUED',total_urls=len(rows),expires_at=now+timedelta(hours=RETENTION_HOURS)); s.add(job); s.flush()
      s.add_all([BulkScanItem(job_id=job.id,row_number=r['row'],normalized_url=r['url'],url_redacted=r['display_url'],status='QUEUED') for r in rows]); s.commit()
      return jsonify({'job':serialize(job),'validation_errors':validation_errors[:100]}),202
    finally:s.close()

@bulk_bp.get('/bulk/jobs')
@jwt_required()
def list_jobs():
    s=Session(); user_id=int(get_jwt_identity())
    try:return jsonify({'jobs':[serialize(j) for j in s.query(BulkScanJob).filter_by(user_id=user_id).order_by(BulkScanJob.created_at.desc()).limit(50)]})
    finally:s.close()

@bulk_bp.get('/bulk/jobs/<job_id>')
@jwt_required()
def get_job(job_id):
    s=Session()
    try:
      job=owned_job(s,job_id,get_jwt_identity())
      if not job:return jsonify({'error':'Job not found.'}),404
      items=s.query(BulkScanItem).filter_by(job_id=job.id).order_by(BulkScanItem.row_number).limit(200).all()
      return jsonify({'job':serialize(job),'results':[i.to_dict() for i in items]})
    finally:s.close()

@bulk_bp.post('/bulk/jobs/<job_id>/cancel')
@jwt_required()
def cancel_job(job_id):
    s=Session()
    try:
      job=owned_job(s,job_id,get_jwt_identity())
      if not job:return jsonify({'error':'Job not found.'}),404
      target='CANCELLED' if job.status=='QUEUED' else 'CANCELLING'
      if not can_transition(job.status,target): return jsonify({'error':'Job cannot be cancelled in its current state.','code':'invalid_state'}),409
      job.status=target
      if target=='CANCELLED': job.completed_at=datetime.utcnow()
      s.commit(); return jsonify({'job':serialize(job)})
    finally:s.close()

@bulk_bp.get('/bulk/jobs/<job_id>/results.csv')
@jwt_required()
def export_job(job_id):
    s=Session()
    try:
      job=owned_job(s,job_id,get_jwt_identity())
      if not job:return jsonify({'error':'Job not found.'}),404
      if job.status not in {'COMPLETED','PARTIALLY_COMPLETED','CANCELLED'}: return jsonify({'error':'Results are not ready.'}),409
      out=io.StringIO(); w=csv.writer(out); w.writerow(['row','url','status','verdict','risk_score','error'])
      for i in s.query(BulkScanItem).filter_by(job_id=job.id).order_by(BulkScanItem.row_number): w.writerow([i.row_number,csv_safe(i.url_redacted),i.status,csv_safe(i.final_verdict),i.threat_score,csv_safe(i.error_code)])
      return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename="cybersentinel-{job.public_id}.csv"'})
    finally:s.close()
