"""Bounded URL analysis that never fetches a submitted webpage."""

from services.content_analyzer import ContentAnalyzer
from services.ml_predictor import predictor
from services.risk_engine import RiskEngine
from services.virustotal_service import check_url_reputation


class HybridURLAnalyzer:
    @classmethod
    def analyze(cls, url: str) -> dict:
        ml_result = predictor.predict(url)
        vt_result = check_url_reputation(url)
        content_result = ContentAnalyzer.analyze_content(url)
        quality = (predictor.manifest or {}).get("risk_signal_quality", {})
        return RiskEngine(quality).evaluate(url=url, ml=ml_result, virustotal=vt_result, content=content_result)
