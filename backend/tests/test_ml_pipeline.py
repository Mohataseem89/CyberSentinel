import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ml.feature_extractor import FEATURE_NAMES, URLFeatureExtractor
from ml.train_model import train_phishing_model
from services.ml_predictor import MLPredictor


class MLPipelineTests(unittest.TestCase):
    def test_extractor_always_uses_one_fixed_schema(self):
        features = URLFeatureExtractor.extract_features("not a normal url")

        self.assertEqual(tuple(features), FEATURE_NAMES)
        self.assertNotIn("feature_0", features)

    def test_trained_artifact_has_manifest_and_correct_probability_mapping(self):
        rows = [
            ("https://example.org", "good"), ("https://docs.example.org", "good"),
            ("https://shop.example.org", "good"), ("https://news.example.org", "good"),
            ("http://login-check-account.example", "bad"), ("http://verify-paypal-login.example", "bad"),
            ("http://secure-update-account.example", "bad"), ("http://signin-confirm-bank.example", "bad"),
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            dataset = base / "dataset.csv"
            pd.DataFrame(rows, columns=["url", "label"]).to_csv(dataset, index=False)
            _, manifest, _ = train_phishing_model(dataset, base, n_estimators=10)

            self.assertEqual(manifest["class_labels"], ["legitimate", "phishing"])
            self.assertEqual(json.loads((base / "model_manifest.json").read_text())["feature_names"], list(FEATURE_NAMES))
            result = MLPredictor(base).predict("http://login-verify-account.example")

        self.assertTrue(result["available"])
        self.assertEqual(set(result["probabilities"]), {"legitimate", "phishing"})
        self.assertAlmostEqual(sum(result["probabilities"].values()), 1.0, places=5)
        self.assertEqual(result["score"], round(result["probabilities"]["phishing"] * 100, 2))
