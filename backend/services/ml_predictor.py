"""Validated model loading and explicit class-to-risk mapping."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import pandas as pd
import sklearn

from ml.feature_extractor import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, URLFeatureExtractor

logger = logging.getLogger(__name__)


class MLPredictor:
    """Load only a model artifact compatible with the current feature schema."""

    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parents[1] / "data"
        self.model = None
        self.manifest = None
        self.unavailable_reason = "Model has not been loaded."
        self.load_model()

    def load_model(self) -> bool:
        model_path = self.data_dir / "phishing_model.pkl"
        manifest_path = self.data_dir / "model_manifest.json"
        try:
            if not model_path.exists() or not manifest_path.exists():
                raise FileNotFoundError("A compatible model and model_manifest.json are required.")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
                raise ValueError("Model feature schema version does not match the application.")
            if tuple(manifest.get("feature_names", ())) != FEATURE_NAMES:
                raise ValueError("Model feature names do not match the application.")
            if manifest.get("class_labels") != ["legitimate", "phishing"]:
                raise ValueError("Model manifest class labels are invalid.")
            if manifest.get("scikit_learn_version") != sklearn.__version__:
                raise ValueError("Model scikit-learn version does not match the runtime.")
            model = joblib.load(model_path)
            if getattr(model, "n_features_in_", None) != len(FEATURE_NAMES):
                raise ValueError("Model feature count does not match the feature schema.")
            if list(getattr(model, "classes_", ())) != ["legitimate", "phishing"]:
                raise ValueError("Model classes do not match the manifest.")
            self.model, self.manifest, self.unavailable_reason = model, manifest, ""
            logger.info("Validated ML model loaded: %s", manifest.get("model_version", "unknown"))
            return True
        except Exception as error:
            self.model, self.manifest, self.unavailable_reason = None, None, str(error)
            logger.warning("ML model unavailable: %s", self.unavailable_reason)
            return False

    def reload_model(self) -> bool:
        return self.load_model()

    def predict(self, url: str) -> dict:
        if self.model is None:
            return {"score": None, "prediction": "unknown", "confidence": 0.0, "available": False,
                    "message": "ML analysis is unavailable until a compatible model is trained."}
        try:
            features = URLFeatureExtractor.extract_features(url)
            frame = pd.DataFrame([[features[name] for name in FEATURE_NAMES]], columns=FEATURE_NAMES)
            probabilities = dict(zip(self.model.classes_, self.model.predict_proba(frame)[0], strict=True))
            phishing_probability = float(probabilities["phishing"])
            legitimate_probability = float(probabilities["legitimate"])
            prediction = "phishing" if phishing_probability >= 0.5 else "legitimate"
            confidence = phishing_probability if prediction == "phishing" else legitimate_probability
            return {
                "score": round(phishing_probability * 100, 2), "prediction": prediction,
                "confidence": round(confidence, 6), "available": True,
                "probabilities": {"legitimate": round(legitimate_probability, 6), "phishing": round(phishing_probability, 6)},
                "message": "ML probability is one risk signal, not a safety guarantee.",
            }
        except Exception:
            logger.exception("ML prediction failed")
            return {"score": None, "prediction": "unknown", "confidence": 0.0, "available": False,
                    "message": "ML analysis could not be completed."}


predictor = MLPredictor()
