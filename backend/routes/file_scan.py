import os
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Session, FileScanJob
from services.file_scan import stream_upload, safe_original_name, public_result
from services.file_types import detect_file, FileTypeError
from services.file_analysis import analyze_file, apply_result


file_scan_bp = Blueprint("file_scan", __name__)

ENABLED = os.getenv("FILE_SCAN_ENABLED", "false").lower() == "true"
MAX_BYTES = int(os.getenv("FILE_SCAN_MAX_BYTES", "10485760"))
MAX_ACTIVE = int(os.getenv("FILE_SCAN_MAX_ACTIVE_PER_USER", "2"))
MAX_DAILY = int(os.getenv("FILE_SCAN_MAX_DAILY_PER_USER", "20"))
RETENTION = int(os.getenv("FILE_SCAN_RESULT_RETENTION_HOURS", "24"))

QUARANTINE = os.path.abspath(
    os.getenv(
        "FILE_SCAN_QUARANTINE_DIR",
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "var",
            "quarantine",
        ),
    )
)

ALLOWED = {
    value.strip()
    for value in os.getenv(
        "FILE_SCAN_ALLOWED_TYPES",
        "html,text,pdf,png,jpeg,gif",
    ).split(",")
    if value.strip()
}

ACTIVE = {"QUEUED", "SCANNING"}

TRUTHY_CONSENT_VALUES = {"true", "1", "yes", "on"}


def owned(session, public_id, user_id):
    return (
        session.query(FileScanJob)
        .filter(
            FileScanJob.public_id == public_id,
            FileScanJob.user_id == int(user_id),
        )
        .first()
    )


def has_explicit_consent():
    """
    File scans use multipart/form-data.

    Consent must therefore be read from request.form rather than JSON.
    Only explicit truthy values are accepted.
    """
    value = request.form.get("consent", "")
    return str(value).strip().lower() in TRUTHY_CONSENT_VALUES


@file_scan_bp.get("/file-scans/capabilities")
@jwt_required()
def capabilities():
    return jsonify(
        {
            "enabled": ENABLED,
            "max_bytes": MAX_BYTES,
            "allowed_types": sorted(ALLOWED),
            "archives_supported": False,
            "consent_required": True,
        }
    )


@file_scan_bp.post("/file-scans")
@jwt_required()
def create_file_scan():
    if not ENABLED:
        return (
            jsonify(
                {
                    "error": "File analysis is currently disabled.",
                    "code": "feature_disabled",
                }
            ),
            503,
        )

    # This endpoint receives multipart/form-data.
    # Accept only explicit affirmative consent.
    if not has_explicit_consent():
        return (
            jsonify(
                {
                    "error": "Explicit analysis consent is required.",
                    "code": "consent_required",
                }
            ),
            400,
        )

    upload = request.files.get("file")

    if not upload or not upload.filename:
        return (
            jsonify(
                {
                    "error": "A file is required.",
                    "code": "file_required",
                }
            ),
            400,
        )

    uid = int(get_jwt_identity())
    session = Session()
    path = None

    try:
        now = datetime.utcnow()

        active_count = (
            session.query(FileScanJob)
            .filter(
                FileScanJob.user_id == uid,
                FileScanJob.status.in_(ACTIVE),
            )
            .count()
        )

        if active_count >= MAX_ACTIVE:
            return (
                jsonify(
                    {
                        "error": "Active file scan limit reached.",
                        "code": "active_scan_quota",
                    }
                ),
                429,
            )

        daily_count = (
            session.query(FileScanJob)
            .filter(
                FileScanJob.user_id == uid,
                FileScanJob.created_at >= now - timedelta(days=1),
            )
            .count()
        )

        if daily_count >= MAX_DAILY:
            return (
                jsonify(
                    {
                        "error": "Daily file scan limit reached.",
                        "code": "daily_scan_quota",
                    }
                ),
                429,
            )

        try:
            path, size, digest = stream_upload(
                upload,
                QUARANTINE,
                MAX_BYTES,
            )
        except ValueError as exc:
            code = str(exc)

            if code == "file_too_large":
                return (
                    jsonify(
                        {
                            "error": "File is too large.",
                            "code": code,
                        }
                    ),
                    413,
                )

            return (
                jsonify(
                    {
                        "error": "Empty files are not accepted.",
                        "code": code,
                    }
                ),
                400,
            )

        try:
            detected = detect_file(path, ALLOWED)
        except FileTypeError as exc:
            try:
                os.remove(path)
            except OSError:
                pass

            path = None

            return (
                jsonify(
                    {
                        "error": exc.message,
                        "code": exc.code,
                    }
                ),
                415,
            )

        job = FileScanJob(
            public_id=str(uuid.uuid4()),
            user_id=uid,
            status="QUEUED",
            original_name=safe_original_name(upload.filename),
            storage_path=path,
            sha256=digest,
            size_bytes=size,
            detected_kind=detected.kind,
            detected_mime=detected.mime,
            created_at=now,
            expires_at=now + timedelta(hours=RETENTION),
        )

        session.add(job)
        session.commit()

        job.status = "SCANNING"
        job.started_at = datetime.utcnow()
        job.attempts = 1
        session.commit()

        result = analyze_file(
            path,
            detected.kind,
            digest,
        )

        apply_result(job, result)

        # Never retain the original uploaded file after analysis.
        job.storage_path = None
        session.commit()

        try:
            os.remove(path)
        except OSError:
            pass

        path = None

        return jsonify({"job": public_result(job)}), 200

    except Exception:
        # Do not leave the SQLAlchemy session in a failed transaction state.
        session.rollback()
        raise

    finally:
        # Defense-in-depth cleanup for every failure path.
        if path:
            try:
                os.remove(path)
            except OSError:
                pass

        session.close()


@file_scan_bp.get("/file-scans")
@jwt_required()
def list_file_scans():
    session = Session()

    try:
        jobs = (
            session.query(FileScanJob)
            .filter_by(user_id=int(get_jwt_identity()))
            .order_by(FileScanJob.created_at.desc())
            .limit(50)
            .all()
        )

        return jsonify(
            {
                "jobs": [
                    public_result(job)
                    for job in jobs
                ]
            }
        )

    finally:
        session.close()


@file_scan_bp.get("/file-scans/<job_id>")
@jwt_required()
def get_file_scan(job_id):
    session = Session()

    try:
        job = owned(
            session,
            job_id,
            get_jwt_identity(),
        )

        if not job:
            return (
                jsonify(
                    {
                        "error": "Scan job not found.",
                        "code": "not_found",
                    }
                ),
                404,
            )

        return jsonify({"job": public_result(job)})

    finally:
        session.close()