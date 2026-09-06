"""Explainable, conservative aggregation of independent URL risk signals."""

from __future__ import annotations

from typing import Any


class RiskEngine:
    """Combine calibrated ML and existing reputation evidence without certainty."""

    def __init__(self, ml_quality: dict[str, Any] | None = None):
        quality = ml_quality or {}
        # The ML contribution is capped by its immutable-holdout F1, rather than
        # a static marketing weight. It cannot dominate independent reputation.
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
        return ["No sufficient corroborated evidence is available. Do not treat this result as safe."]

    def evaluate(self, *, url: str, ml: dict, virustotal: dict, content: dict) -> dict:
        evidence, weighted = [], []
        ml_score = ml.get("score")
        if ml.get("available") and isinstance(ml_score, (int, float)):
            evidence.append({"source": "ml", "status": "available", "risk_score": ml_score, "weight": round(self.ml_weight, 3), "detail": ml.get("message")})
            weighted.append((float(ml_score), self.ml_weight))
        else:
            evidence.append({"source": "ml", "status": "unavailable", "detail": ml.get("message")})

        vt_score = virustotal.get("score")
        if virustotal.get("evidence_available") and isinstance(vt_score, (int, float)):
            evidence.append({"source": "virustotal", "status": "available", "risk_score": vt_score, "weight": self.vt_weight, "detail": virustotal.get("message")})
            weighted.append((float(vt_score), self.vt_weight))
        else:
            evidence.append({"source": "virustotal", "status": "unavailable", "detail": virustotal.get("message")})

        limitations = ["Results are risk indicators, not a guarantee that a URL is safe.", "Remote page-content fetching is disabled for SSRF protection."]
        if not weighted:
            verdict, score, confidence = "Unknown", None, "unavailable"
        else:
            score = round(sum(value * weight for value, weight in weighted) / sum(weight for _, weight in weighted), 2)
            vt_malicious, vt_positives = int(virustotal.get("malicious", 0)), int(virustotal.get("positives", 0))
            if vt_malicious >= 2 or score >= 75:
                verdict = "Dangerous"
            elif score >= 40 or vt_positives > 0:
                verdict = "Suspicious"
            elif virustotal.get("evidence_available") and len(weighted) == 2:
                verdict = "Safe"
            else:
                verdict = "Unknown"
                limitations.append("A low ML score alone is not enough evidence to call a URL safe.")
            confidence = "high" if len(weighted) == 2 and verdict != "Unknown" else "medium" if verdict != "Unknown" else "low"
        indicators = [entry["detail"] for entry in evidence if entry.get("status") == "available" and entry.get("detail")]
        return {"url": url, "final_verdict": verdict, "threat_score": score, "confidence": confidence, "evidence": evidence, "limitations": limitations, "breakdown": {"ml": ml, "virustotal": virustotal, "content": content}, "indicators": indicators, "recommendations": self._recommendations(verdict)}
