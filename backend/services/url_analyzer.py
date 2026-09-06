"""Bounded URL analysis that never fetches a submitted webpage."""

from services.content_analyzer import ContentAnalyzer
from services.ml_predictor import predictor
from services.virustotal_service import check_url_reputation


class HybridURLAnalyzer:
    """Combine only available URL-safe signals.

    Weights are provisional and normalized over available evidence. They will be
    calibrated against held-out evaluation data in the risk-engine phase.
    """

    WEIGHTS = {"ml": 0.60, "virustotal": 0.40}

    @classmethod
    def analyze(cls, url: str) -> dict:
        ml_result = predictor.predict(url)
        vt_result = check_url_reputation(url)
        content_result = ContentAnalyzer.analyze_content(url)
        breakdown = {"ml": ml_result, "virustotal": vt_result, "content": content_result}
        available = {
            name: result for name, result in (("ml", ml_result), ("virustotal", vt_result))
            if result.get("available") and isinstance(result.get("score"), (int, float))
        }
        if not available:
            return {
                "url": url, "final_verdict": "Unknown", "threat_score": None,
                "confidence": "unavailable", "breakdown": breakdown, "indicators": [],
                "recommendations": ["No reliable risk signal was available. Do not treat this as a safe result."],
            }

        weight_total = sum(cls.WEIGHTS[name] for name in available)
        threat_score = round(sum(result["score"] * cls.WEIGHTS[name] for name, result in available.items()) / weight_total, 2)
        if threat_score >= 75:
            verdict, confidence = "Dangerous", "medium" if len(available) == 1 else "high"
            recommendations = ["Do not enter credentials or payment information.", "Verify through an independent trusted channel."]
        elif threat_score >= 40:
            verdict, confidence = "Suspicious", "low" if len(available) == 1 else "medium"
            recommendations = ["Proceed with caution and verify the destination independently."]
        else:
            verdict, confidence = "Safe", "low" if len(available) == 1 else "medium"
            recommendations = ["No current signal indicates elevated risk. This is not a guarantee of safety."]

        indicators = []
        if ml_result.get("available"):
            indicators.append(f"ML: {ml_result['prediction']} ({ml_result['probabilities']['phishing']:.1%} phishing probability)")
        if vt_result.get("available") and vt_result.get("positives", 0) > 0:
            indicators.append(f"VirusTotal: {vt_result['positives']}/{vt_result['total']} vendors flagged the URL")
        return {
            "url": url, "final_verdict": verdict, "threat_score": threat_score,
            "confidence": confidence, "breakdown": breakdown, "indicators": indicators,
            "recommendations": recommendations,
        }
