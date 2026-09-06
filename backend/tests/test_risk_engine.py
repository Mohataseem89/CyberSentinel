import unittest

from services.risk_engine import RiskEngine


DISABLED_CONTENT = {"available": False, "score": None, "indicators": []}


class RiskEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RiskEngine({"f1_phishing": 0.66})

    def test_unavailable_signals_are_unknown_not_safe(self):
        result = self.engine.evaluate(url="https://example.test", ml={"available": False, "message": "model unavailable"}, virustotal={"available": False, "message": "quota exhausted"}, content=DISABLED_CONTENT)

        self.assertEqual(result["final_verdict"], "Unknown")
        self.assertIsNone(result["threat_score"])

    def test_low_ml_score_without_reputation_is_unknown(self):
        result = self.engine.evaluate(url="https://example.test", ml={"available": True, "score": 3, "message": "low model score"}, virustotal={"available": True, "evidence_available": False, "message": "not found"}, content=DISABLED_CONTENT)

        self.assertEqual(result["final_verdict"], "Unknown")

    def test_multiple_malicious_vendor_detections_are_dangerous(self):
        result = self.engine.evaluate(url="https://example.test", ml={"available": True, "score": 20, "message": "model score"}, virustotal={"available": True, "evidence_available": True, "score": 5, "malicious": 2, "positives": 2, "message": "2/40 vendors flagged"}, content=DISABLED_CONTENT)

        self.assertEqual(result["final_verdict"], "Dangerous")
        self.assertGreater(result["threat_score"], 0)

    def test_corrobated_low_risk_signals_can_be_safe_with_limitation(self):
        result = self.engine.evaluate(url="https://example.test", ml={"available": True, "score": 2, "message": "model score"}, virustotal={"available": True, "evidence_available": True, "score": 0, "malicious": 0, "positives": 0, "message": "0/40 vendors flagged"}, content=DISABLED_CONTENT)

        self.assertEqual(result["final_verdict"], "Safe")
        self.assertTrue(any("not a guarantee" in item for item in result["limitations"]))
