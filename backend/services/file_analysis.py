"""Production-safe file analysis. Uploaded bytes are never executed or sent to VirusTotal."""
import json, os
from datetime import datetime
from services.clamav_adapter import ClamAVAdapter, ClamAVError
from services.html_static_analyzer import analyze_html_bytes
from services.virustotal_service import check_file_hash_reputation

MAX_HTML=int(os.getenv("FILE_SCAN_HTML_MAX_BYTES","2097152"))

def _html_analysis(path, kind):
    if kind!="html": return None, []
    with open(path,"rb") as fh: raw=fh.read(MAX_HTML+1)
    if len(raw)>MAX_HTML: raise ValueError("html_too_large")
    report=analyze_html_bytes(raw)
    return report["risk_level"], report["indicators"]

def analyze_file(path, kind, sha256):
    html_risk=None; indicators=[]
    try:
        html_risk,indicators=_html_analysis(path,kind)
    except (OSError,ValueError):
        return {"status":"FAILED","verdict":"UNABLE_TO_COMPLETE","malware_status":"scan_failed","html_risk":None,"indicators":[],"error_code":"static_analysis_failed"}

    # Use local ClamAV when an operator provides it. The short ping avoids blocking normal Render deployments.
    probe=ClamAVAdapter(os.getenv("CLAMAV_HOST","127.0.0.1"),int(os.getenv("CLAMAV_PORT","3310")),0.25,int(os.getenv("FILE_SCAN_MAX_BYTES","10485760")))
    if probe.ping():
        scanner=ClamAVAdapter(probe.host,probe.port,float(os.getenv("CLAMAV_TIMEOUT_SECONDS","30")),probe.max_bytes)
        try:
            av=scanner.scan_file(path)
            if av["status"]=="malware_detected":
                indicators.insert(0,{"code":"antivirus_detection","severity":"high","signature":av.get("signature")})
                return {"status":"COMPLETED","verdict":"THREAT_DETECTED","malware_status":"malware_detected","html_risk":html_risk,"indicators":indicators,"error_code":None}
            if html_risk in {"medium","high"}:
                return {"status":"COMPLETED","verdict":"SUSPICIOUS_INDICATORS","malware_status":"clean","html_risk":html_risk,"indicators":indicators,"error_code":None}
            return {"status":"COMPLETED","verdict":"CLEAN_CHECKS_COMPLETED","malware_status":"clean","html_risk":html_risk,"indicators":indicators,"error_code":None}
        except ClamAVError:
            pass

    # Lightweight production fallback: reputation lookup by SHA-256 only. File bytes never leave CyberSentinel.
    vt=check_file_hash_reputation(sha256)
    if vt.get("evidence_available") and int(vt.get("positives",0))>0:
        indicators.insert(0,{"code":"file_hash_reputation_detection","severity":"high" if int(vt.get("malicious",0))>0 else "medium","detections":int(vt.get("positives",0)),"vendors":int(vt.get("total",0))})
        return {"status":"COMPLETED","verdict":"THREAT_DETECTED" if int(vt.get("malicious",0))>0 else "SUSPICIOUS_INDICATORS","malware_status":"malware_detected","html_risk":html_risk,"indicators":indicators,"error_code":None}
    if html_risk in {"medium","high"}:
        return {"status":"COMPLETED","verdict":"SUSPICIOUS_INDICATORS","malware_status":"reputation_only","html_risk":html_risk,"indicators":indicators,"error_code":None}
    if vt.get("evidence_available"):
        return {"status":"COMPLETED","verdict":"CLEAN_CHECKS_COMPLETED","malware_status":"reputation_clean","html_risk":html_risk,"indicators":indicators,"error_code":None}
    # Unknown hash/provider outage is not evidence of safety.
    return {"status":"FAILED","verdict":"UNABLE_TO_COMPLETE","malware_status":"reputation_unavailable","html_risk":html_risk,"indicators":indicators,"error_code":"malware_evidence_unavailable"}

def apply_result(job,result):
    job.status=result["status"]; job.verdict=result["verdict"]; job.malware_status=result["malware_status"]
    job.html_risk=result["html_risk"]; job.indicators_json=json.dumps(result["indicators"]); job.error_code=result["error_code"]; job.completed_at=datetime.utcnow()
