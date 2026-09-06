"""Reproducibly train a model compatible with the runtime predictor."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

try:
    from .feature_extractor import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, URLFeatureExtractor
except ImportError:  # Allows `python ml/train_model.py` from the backend directory.
    from feature_extractor import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, URLFeatureExtractor

LABEL_MAPPING = {"good": "legitimate", "bad": "phishing"}
RANDOM_STATE = 42


def dataset_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metrics(y_true, probabilities, predictions) -> dict:
    return {
        "accuracy": round(float(accuracy_score(y_true, predictions)), 6),
        "precision_phishing": round(float(precision_score(y_true, predictions, pos_label="phishing", zero_division=0)), 6),
        "recall_phishing": round(float(recall_score(y_true, predictions, pos_label="phishing", zero_division=0)), 6),
        "f1_phishing": round(float(f1_score(y_true, predictions, pos_label="phishing", zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score([label == "phishing" for label in y_true], probabilities)), 6),
        "confusion_matrix_labels": ["legitimate", "phishing"],
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=["legitimate", "phishing"]).tolist(),
        "classification_report": classification_report(y_true, predictions, labels=["legitimate", "phishing"], output_dict=True, zero_division=0),
    }


def train_phishing_model(dataset_path: str | Path | None = None, output_dir: str | Path | None = None, n_estimators: int = 100):
    current_dir = Path(__file__).resolve().parent
    backend_dir = current_dir.parent
    dataset_path = Path(dataset_path) if dataset_path else backend_dir / "data" / "final_training_dataset.csv"
    output_dir = Path(output_dir) if output_dir else backend_dir / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    source = pd.read_csv(dataset_path, usecols=["url", "label"])
    source["url"] = source["url"].fillna("").astype(str).str.strip()
    source["label"] = source["label"].fillna("").astype(str).str.strip().str.lower().map(LABEL_MAPPING)
    source = source[(source["url"] != "") & source["label"].notna()].drop_duplicates(subset=["url"])
    if source["label"].nunique() != 2:
        raise ValueError("Training data must include both legitimate and phishing labels.")

    extractor = URLFeatureExtractor()
    features = pd.DataFrame([extractor.extract_features(url) for url in source["url"]], columns=FEATURE_NAMES)
    labels = source["label"].reset_index(drop=True)
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=RANDOM_STATE, stratify=labels
    )
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=20, random_state=RANDOM_STATE, n_jobs=-1)
    model.fit(x_train, y_train)

    probabilities = model.predict_proba(x_test)[:, list(model.classes_).index("phishing")]
    predictions = model.predict(x_test)
    metrics = _metrics(y_test, probabilities, predictions)
    source_hash = dataset_sha256(dataset_path)
    manifest = {
        "model_version": f"url-rf-v{FEATURE_SCHEMA_VERSION}-{source_hash[:12]}",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "class_labels": ["legitimate", "phishing"],
        "source_label_mapping": LABEL_MAPPING,
        "dataset_sha256": source_hash,
        "dataset_rows": int(len(source)),
        "random_state": RANDOM_STATE,
        "training_parameters": {"n_estimators": n_estimators, "max_depth": 20},
        "scikit_learn_version": sklearn.__version__,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(model, output_dir / "phishing_model.pkl")
    joblib.dump(list(FEATURE_NAMES), output_dir / "feature_columns.pkl")
    (output_dir / "model_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "model_evaluation.json").write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    return model, manifest, metrics


if __name__ == "__main__":
    _, manifest, metrics = train_phishing_model()
    print(f"Trained {manifest['model_version']}")
    print(json.dumps(metrics, indent=2, sort_keys=True))
