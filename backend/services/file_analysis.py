"""Production-safe file analysis.

Uploaded files are treated as untrusted data.

They are:
- never executed;
- analyzed locally using lightweight static checks;
- never uploaded to VirusTotal;
- checked against VirusTotal by SHA-256 reputation only;
- deleted by the route after analysis.

A clean result means that the available checks found no suspicious
indicators. It is not a guarantee that the file is malware-free.
"""

import json
import logging
import os
from datetime import datetime

from services.html_static_analyzer import analyze_html_bytes
from services.lightweight_file_analyzer import (
    analyze_lightweight_file,
    highest_indicator_severity,
)
from services.virustotal_service import check_file_hash_reputation


logger = logging.getLogger(__name__)

MAX_HTML = int(
    os.getenv(
        "FILE_SCAN_HTML_MAX_BYTES",
        "2097152",
    )
)


def _html_analysis(path, kind):
    """Run the existing static HTML analyzer for HTML uploads."""

    if kind != "html":
        return None, []

    with open(path, "rb") as file_handle:
        raw = file_handle.read(MAX_HTML + 1)

    if len(raw) > MAX_HTML:
        raise ValueError("html_too_large")

    report = analyze_html_bytes(raw)

    return (
        report["risk_level"],
        report["indicators"],
    )


def _result(
    *,
    status,
    verdict,
    malware_status,
    html_risk,
    indicators,
    error_code=None,
):
    """Build file-analysis results consistently."""

    return {
        "status": status,
        "verdict": verdict,
        "malware_status": malware_status,
        "html_risk": html_risk,
        "indicators": indicators,
        "error_code": error_code,
    }


def analyze_file(path, kind, sha256):
    """Analyze one validated upload without executing or uploading it."""

    html_risk = None
    indicators = []

    # ------------------------------------------------------------------
    # Local static analysis
    # ------------------------------------------------------------------

    try:
        html_risk, html_indicators = _html_analysis(
            path,
            kind,
        )

        indicators.extend(html_indicators)

        local_indicators = analyze_lightweight_file(
            path,
            kind,
        )

        indicators.extend(local_indicators)

    except (OSError, ValueError):
        logger.warning(
            "Static file analysis failed.",
            exc_info=True,
        )

        return _result(
            status="FAILED",
            verdict="UNABLE_TO_COMPLETE",
            malware_status="scan_failed",
            html_risk=html_risk,
            indicators=indicators,
            error_code="static_analysis_failed",
        )

    local_severity = highest_indicator_severity(
        indicators
    )

    # ------------------------------------------------------------------
    # Reputation evidence: VirusTotal SHA-256 lookup only
    #
    # The uploaded file itself is NEVER submitted to VirusTotal.
    # ------------------------------------------------------------------

    try:
        vt = check_file_hash_reputation(sha256)
    except Exception:
        # Reputation is supplementary. A provider/network failure must not
        # prevent the local static analysis result from being returned.
        logger.warning(
            "File hash reputation lookup failed.",
            exc_info=True,
        )

        vt = {
            "evidence_available": False,
            "positives": 0,
            "malicious": 0,
            "total": 0,
        }

    evidence_available = bool(
        vt.get("evidence_available")
    )

    try:
        positives = int(
            vt.get("positives", 0) or 0
        )
    except (TypeError, ValueError):
        positives = 0

    try:
        malicious = int(
            vt.get("malicious", 0) or 0
        )
    except (TypeError, ValueError):
        malicious = 0

    try:
        total = int(
            vt.get("total", 0) or 0
        )
    except (TypeError, ValueError):
        total = 0

    # ------------------------------------------------------------------
    # Known reputation detection
    # ------------------------------------------------------------------

    if evidence_available and positives > 0:
        reputation_severity = (
            "high"
            if malicious > 0
            else "medium"
        )

        indicators.insert(
            0,
            {
                "code": "file_hash_reputation_detection",
                "severity": reputation_severity,
                "detections": positives,
                "vendors": total,
            },
        )

        return _result(
            status="COMPLETED",
            verdict=(
                "THREAT_DETECTED"
                if malicious > 0
                else "SUSPICIOUS_INDICATORS"
            ),
            malware_status=(
                "malware_detected"
                if malicious > 0
                else "reputation_suspicious"
            ),
            html_risk=html_risk,
            indicators=indicators,
        )

    # ------------------------------------------------------------------
    # Local suspicious indicators
    #
    # Static indicators can make a file suspicious, but they are not
    # sufficient by themselves to label the file as confirmed malware.
    # ------------------------------------------------------------------

    if (
        local_severity in {"medium", "high"}
        or html_risk in {"medium", "high"}
    ):
        return _result(
            status="COMPLETED",
            verdict="SUSPICIOUS_INDICATORS",
            malware_status=(
                "reputation_clean"
                if evidence_available
                else "static_analysis_only"
            ),
            html_risk=html_risk,
            indicators=indicators,
        )

    # ------------------------------------------------------------------
    # Reputation available and no suspicious evidence
    # ------------------------------------------------------------------

    if evidence_available:
        return _result(
            status="COMPLETED",
            verdict="CLEAN_CHECKS_COMPLETED",
            malware_status="reputation_clean",
            html_risk=html_risk,
            indicators=indicators,
        )

    # ------------------------------------------------------------------
    # No reputation evidence
    #
    # Local static analysis still completed successfully, so this is not
    # an analysis failure. However, the result must not imply that an
    # antivirus engine verified the file as malware-free.
    # ------------------------------------------------------------------

    return _result(
        status="COMPLETED",
        verdict="CLEAN_CHECKS_COMPLETED",
        malware_status="static_checks_only",
        html_risk=html_risk,
        indicators=indicators,
        error_code="malware_reputation_unavailable",
    )


def apply_result(job, result):
    """Persist an analysis result onto a FileScanJob."""

    job.status = result["status"]
    job.verdict = result["verdict"]
    job.malware_status = result["malware_status"]
    job.html_risk = result["html_risk"]

    job.indicators_json = json.dumps(
        result["indicators"]
    )

    job.error_code = result["error_code"]
    job.completed_at = datetime.utcnow()