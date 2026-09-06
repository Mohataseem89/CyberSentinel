"""Train a versioned URL classifier without evaluating on training domains."""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             classification_report, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit

try:
    from .data_governance import load_labeled_urls
    from .feature_extractor import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, URLFeatureExtractor
    from .prepare_governed_dataset import prepare_governed_dataset
except ImportError:  # Allows `python ml/train_model.py` from the backend directory.
    from data_governance import load_labeled_urls
    from feature_extractor import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, URLFeatureExtractor
    from prepare_governed_dataset import prepare_governed_dataset

RANDOM_STATE = 42


def _probabilities(model, features: pd.DataFrame):
    return model.predict_proba(features)[:, list(model.classes_).index("phishing")]


def _classification_metrics(y_true, probabilities, threshold: float) -> dict:
    predictions = ["phishing" if probability >= threshold else "legitimate" for probability in probabilities]
    binary_truth = [label == "phishing" for label in y_true]
    return {
        "threshold": round(float(threshold), 6),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 6),
        "precision_phishing": round(float(precision_score(y_true, predictions, pos_label="phishing", zero_division=0)), 6),
        "recall_phishing": round(float(recall_score(y_true, predictions, pos_label="phishing", zero_division=0)), 6),
        "f1_phishing": round(float(f1_score(y_true, predictions, pos_label="phishing", zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(binary_truth, probabilities)), 6),
        "pr_auc": round(float(average_precision_score(binary_truth, probabilities)), 6),
        "brier_score": round(float(brier_score_loss(binary_truth, probabilities)), 6),
        "confusion_matrix_labels": ["legitimate", "phishing"],
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=["legitimate", "phishing"]).tolist(),
        "classification_report": classification_report(y_true, predictions, labels=["legitimate", "phishing"], output_dict=True, zero_division=0),
    }


def _calibration_metrics(y_true, probabilities) -> dict:
    truth = [label == "phishing" for label in y_true]
    observed, predicted = calibration_curve(truth, probabilities, n_bins=10, strategy="uniform")
    error = sum(abs(float(a) - float(b)) for a, b in zip(observed, predicted, strict=True)) / len(observed) if len(observed) else None
    return {"bins": [{"mean_predicted": round(float(pred), 6), "observed_frequency": round(float(obs), 6)} for obs, pred in zip(observed, predicted, strict=True)], "expected_calibration_error": round(error, 6) if error is not None else None}


def _slice_metrics(frame: pd.DataFrame, probabilities, threshold: float) -> dict:
    evaluated = frame.copy()
    evaluated["probability"] = probabilities
    evaluated["url_length_slice"] = pd.cut(evaluated["url"].str.len(), bins=[-1, 50, 100, float("inf")], labels=["0-50", "51-100", "101+"])
    evaluated["ip_literal"] = evaluated["url"].str.contains(r"://\d{1,3}(?:\.\d{1,3}){3}(?::|/|$)", regex=True)
    results = {}
    for dimension in ("url_length_slice", "ip_literal"):
        results[dimension] = {}
        for value, group in evaluated.groupby(dimension, observed=True):
            if group["label"].nunique() < 2:
                results[dimension][str(value)] = {"rows": int(len(group)), "status": "insufficient_class_coverage"}
                continue
            metrics = _classification_metrics(group["label"], group["probability"], threshold)
            results[dimension][str(value)] = {key: metrics[key] for key in ("accuracy", "precision_phishing", "recall_phishing", "f1_phishing")}
            results[dimension][str(value)]["rows"] = int(len(group))
    return results


def _model_card(manifest: dict, evaluation: dict) -> str:
    metrics = evaluation["immutable_holdout"]
    return f"""# CyberSentinel URL model card

## Model

- Version: `{manifest['model_version']}`
- Type: lexical URL Random Forest with isotonic probability calibration
- Features: {len(FEATURE_NAMES)} fixed, local lexical features; no URL is fetched
- Dataset source SHA-256: `{manifest['dataset_sha256']}`

## Evaluation protocol

An immutable domain-grouped holdout was excluded before fitting, calibration, and
threshold selection. Exact duplicates and conflicting duplicate labels were
removed. The source has no trustworthy timestamps, so no temporal claim is made.

## Immutable-holdout results

- Precision (phishing): {metrics['precision_phishing']}
- Recall (phishing): {metrics['recall_phishing']}
- F1 (phishing): {metrics['f1_phishing']}
- PR AUC: {metrics['pr_auc']}
- ROC AUC: {metrics['roc_auc']}
- Brier score: {metrics['brier_score']}

## Limitations

This is a risk signal, not proof that a URL is safe. The model does not inspect
page content, execute scripts, resolve DNS, or assess newly registered domains.
Scores can be wrong for novel attacks, benign URLs that resemble phishing, and
dataset populations that do not match real user traffic. Do not use the holdout
to improve this model; create a new versioned split for a new dataset release.
"""


def train_phishing_model(dataset_path: str | Path | None = None, output_dir: str | Path | None = None, n_estimators: int = 60, governance_dir: str | Path | None = None):
    current_dir = Path(__file__).resolve().parent
    backend_dir = current_dir.parent
    dataset_path = Path(dataset_path) if dataset_path else backend_dir / "data" / "final_training_dataset.csv"
    output_dir = Path(output_dir) if output_dir else backend_dir / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    governance_dir = Path(governance_dir) if governance_dir else current_dir / "data"
    holdout_path, registry_path = governance_dir / "immutable_holdout.csv", governance_dir / "dataset_registry.json"
    if not holdout_path.exists() or not registry_path.exists():
        prepare_governed_dataset(dataset_path=dataset_path, data_dir=governance_dir)

    source, governance = load_labeled_urls(dataset_path)
    holdout = pd.read_csv(holdout_path, usecols=["url", "label", "domain_group"])
    holdout_urls = set(holdout["url"])
    training_pool = source[~source["url"].isin(holdout_urls)].reset_index(drop=True)
    if training_pool.empty or set(training_pool["domain_group"]) & set(holdout["domain_group"]):
        raise ValueError("Invalid holdout: training and immutable evaluation domains must not overlap.")

    extractor = URLFeatureExtractor()
    all_features = pd.DataFrame([extractor.extract_features(url) for url in source["url"]], columns=FEATURE_NAMES)
    features_by_url = dict(zip(source["url"], all_features.to_dict("records"), strict=True))
    def features_for(frame: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame([features_by_url[url] for url in frame["url"]], columns=FEATURE_NAMES)

    split = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=RANDOM_STATE)
    fit_idx, calibration_idx = next(split.split(training_pool, training_pool["label"], groups=training_pool["domain_group"]))
    fit_data, calibration_data = training_pool.iloc[fit_idx], training_pool.iloc[calibration_idx]
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=20, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced_subsample")
    model.fit(features_for(fit_data), fit_data["label"])
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(_probabilities(model, features_for(calibration_data)), calibration_data["label"].eq("phishing").astype(int))

    holdout_probabilities = calibrator.transform(_probabilities(model, features_for(holdout)))
    threshold = 0.50
    evaluation = {
        "protocol": {"immutable_holdout": "domain_grouped; excluded before model fit, calibrator fit, and threshold selection", "calibration_split": "domain_grouped 15% of non-holdout data", "temporal_split": governance["temporal_split"], "dataset_governance": governance},
        "immutable_holdout": _classification_metrics(holdout["label"], holdout_probabilities, threshold),
        "calibration": _calibration_metrics(holdout["label"], holdout_probabilities),
        "slices": _slice_metrics(holdout, holdout_probabilities, threshold),
    }
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    training_parameters = {"n_estimators": n_estimators, "max_depth": 20, "class_weight": "balanced_subsample"}
    version_material = json.dumps({"source": governance["source_sha256"], "holdout": registry["immutable_holdout_sha256"], "features": FEATURE_NAMES, "parameters": training_parameters, "random_state": RANDOM_STATE}, sort_keys=True).encode("utf-8")
    model_version = f"url-rf-v{FEATURE_SCHEMA_VERSION}-{hashlib.sha256(version_material).hexdigest()[:12]}"
    manifest = {
        "model_version": model_version, "feature_schema_version": FEATURE_SCHEMA_VERSION, "feature_names": list(FEATURE_NAMES), "class_labels": ["legitimate", "phishing"], "dataset_sha256": governance["source_sha256"], "dataset_rows": governance["usable_rows"], "holdout_sha256": registry["immutable_holdout_sha256"], "holdout_rows": registry["immutable_holdout_rows"], "split_strategy": registry["split_strategy"], "calibration": {"method": "isotonic", "fitted_on": "domain_grouped non-holdout calibration split"}, "risk_signal_quality": {"f1_phishing": evaluation["immutable_holdout"]["f1_phishing"], "precision_phishing": evaluation["immutable_holdout"]["precision_phishing"], "recall_phishing": evaluation["immutable_holdout"]["recall_phishing"]}, "random_state": RANDOM_STATE, "training_parameters": training_parameters, "scikit_learn_version": sklearn.__version__, "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(model, output_dir / "phishing_model.pkl")
    joblib.dump(calibrator, output_dir / "probability_calibrator.pkl")
    joblib.dump(list(FEATURE_NAMES), output_dir / "feature_columns.pkl")
    (output_dir / "model_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "model_evaluation.json").write_text(json.dumps(evaluation, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "MODEL_CARD.md").write_text(_model_card(manifest, evaluation), encoding="utf-8")
    return model, manifest, evaluation



if __name__ == "__main__":
    _, manifest, evaluation = train_phishing_model()
    print(f"Trained {manifest['model_version']}")
    print(json.dumps(evaluation["immutable_holdout"], indent=2, sort_keys=True))
