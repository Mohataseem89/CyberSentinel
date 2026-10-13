import unittest
from services.risk_engine import RiskEngine

DISABLED_CONTENT = {"available": False, "score": None, "indicators": []}


class RiskEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RiskEngine({"f1_phishing": 0.66})

    def evaluate(self, ml_score=None, vt=None):
        ml = {"available": ml_score is not None, "score": ml_score, "message": "model"}
        vt = vt or {"available": True, "evidence_available": False, "message": "not found"}
        return self.engine.evaluate(url="https://example.test", ml=ml, virustotal=vt, content=DISABLED_CONTENT)

    def test_unavailable_signals_are_unknown_not_safe(self):
        result = self.engine.evaluate(url="https://example.test", ml={"available": False, "message": "model unavailable"}, virustotal={"available": False, "message": "quota exhausted"}, content=DISABLED_CONTENT)
        self.assertEqual(result["final_verdict"], "Unknown")
        self.assertIsNone(result["threat_score"])

    def test_low_ml_score_without_reputation_is_safe_low_confidence(self):
        result = self.evaluate(3)
        self.assertEqual(result["final_verdict"], "Safe")
        self.assertEqual(result["confidence"], "low")
        self.assertTrue(any("primarily" in x for x in result["limitations"]))

    def test_borderline_score_remains_unknown(self):
        self.assertEqual(self.evaluate(35)["final_verdict"], "Unknown")

    def test_medium_score_is_suspicious(self):
        self.assertEqual(self.evaluate(55)["final_verdict"], "Suspicious")

    def test_high_score_is_dangerous(self):
        self.assertEqual(self.evaluate(80)["final_verdict"], "Dangerous")

    def test_vt_positive_escalates_to_suspicious(self):
        vt = {"available": True, "evidence_available": True, "score": 0, "malicious": 0, "positives": 1, "message": "1 vendor flagged"}
        self.assertEqual(self.evaluate(3, vt)["final_verdict"], "Suspicious")

    def test_multiple_malicious_vendor_detections_are_dangerous(self):
        vt = {"available": True, "evidence_available": True, "score": 5, "malicious": 2, "positives": 2, "message": "2 vendors flagged"}
        self.assertEqual(self.evaluate(20, vt)["final_verdict"], "Dangerous")

    def test_corrobated_low_risk_signals_can_be_safe_with_limitation(self):
        vt = {"available": True, "evidence_available": True, "score": 0, "malicious": 0, "positives": 0, "message": "0 vendors flagged"}
        result = self.evaluate(2, vt)
        self.assertEqual(result["final_verdict"], "Safe")
        self.assertEqual(result["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
