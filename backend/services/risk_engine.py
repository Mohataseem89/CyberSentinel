"""Explainable aggregation of URL risk signals with stable public verdicts."""
from __future__ import annotations
from typing import Any


class RiskEngine:
    """Combine calibrated ML and reputation evidence without claiming certainty."""

    def __init__(self, ml_quality: dict[str, Any] | None = None):
        quality = ml_quality or {}
        self.ml_weight = max(0.20, min(float(quality.get("f1_phishing", 0.50)), 0.75))
        self.vt_weight = 0.75

    @staticmethod
    def _recommendations(verdict: str) -> list[str]:
        if verdict == "Dangerous":
            return ["Do not open the link or enter credentials.", "Verify the request through a trusted, independent channel."]
        if verdict == "Suspicious":
            return ["Do not enter passwords or payment information.", "Verify the destination independently before continuing."]
        if verdict == "Safe":
            return ["No current signal indicates elevated risk. This is not a guarantee of safety."]
        return ["Available evidence is insufficient or borderline. Do not treat this result as safe."]

    def evaluate(self, *, url: str, ml: dict, virustotal: dict, content: dict) -> dict:
        evidence: list[dict[str, Any]] = []
        weighted: list[tuple[float, float]] = []
        ml_score = ml.get("score")
        ml_available = bool(ml.get("available") and isinstance(ml_score, (int, float)))
        if ml_available:
            evidence.append({"source": "ml", "status": "available", "risk_score": ml_score, "weight": round(self.ml_weight, 3), "detail": ml.get("message")})
            weighted.append((float(ml_score), self.ml_weight))
        else:
            evidence.append({"source": "ml", "status": "unavailable", "detail": ml.get("message")})

        vt_score = virustotal.get("score")
        vt_available = bool(virustotal.get("evidence_available") and isinstance(vt_score, (int, float)))
        if vt_available:
            evidence.append({"source": "virustotal", "status": "available", "risk_score": vt_score, "weight": self.vt_weight, "detail": virustotal.get("message")})
            weighted.append((float(vt_score), self.vt_weight))
        else:
            evidence.append({"source": "virustotal", "status": "unavailable", "detail": virustotal.get("message")})

        limitations = [
            "Results are risk indicators, not a guarantee that a URL is safe.",
            "Remote page-content fetching is disabled for SSRF protection.",
        ]
        if not weighted:
            verdict, score, confidence = "Unknown", None, "unavailable"
        else:
            score = round(sum(value * weight for value, weight in weighted) / sum(weight for _, weight in weighted), 2)
            vt_malicious = int(virustotal.get("malicious", 0) or 0)
            vt_positives = int(virustotal.get("positives", 0) or 0)
            if vt_malicious >= 2 or score >= 75:
                verdict = "Dangerous"
            elif vt_positives > 0 or score >= 40:
                verdict = "Suspicious"
            elif score < 30 and ml_available:
                verdict = "Safe"
                if not vt_available:
                    limitations.append("Safe is based primarily on the URL model because independent reputation evidence was unavailable.")
            else:
                verdict = "Unknown"
                limitations.append("The available risk score is borderline or lacks enough evidence for a Safe verdict.")

            if verdict == "Unknown":
                confidence = "low"
            elif ml_available and vt_available:
                confidence = "high"
            elif verdict == "Safe":
                confidence = "low"
            else:
                confidence = "medium"

        indicators = [entry["detail"] for entry in evidence if entry.get("status") == "available" and entry.get("detail")]
        return {
            "url": url,
            "final_verdict": verdict,
            "threat_score": score,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": limitations,
            "breakdown": {"ml": ml, "virustotal": virustotal, "content": content},
            "indicators": indicators,
            "recommendations": self._recommendations(verdict),
        }
