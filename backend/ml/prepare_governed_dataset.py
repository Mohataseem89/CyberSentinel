"""Create the immutable, domain-grouped evaluation holdout and dataset registry.

Run from ``backend`` with ``python -m ml.prepare_governed_dataset``.  Existing
holdouts are never overwritten unless ``--force`` is deliberately supplied.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sklearn.model_selection import GroupShuffleSplit

try:
    from .data_governance import load_labeled_urls, sha256_file
except ImportError:
    from data_governance import load_labeled_urls, sha256_file


def prepare_governed_dataset(dataset_path: str | Path | None = None, data_dir: str | Path | None = None, force: bool = False) -> dict:
    backend_dir = Path(__file__).resolve().parent.parent
    dataset_path = Path(dataset_path) if dataset_path else backend_dir / "data" / "final_training_dataset.csv"
    data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    holdout_path = data_dir / "immutable_holdout.csv"
    registry_path = data_dir / "dataset_registry.json"
    if holdout_path.exists() and not force:
        raise FileExistsError(f"{holdout_path} already exists. Refusing to change the immutable holdout without --force.")

    source, governance = load_labeled_urls(dataset_path)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.10, random_state=42)
    _, holdout_indices = next(splitter.split(source, source["label"], groups=source["domain_group"]))
    holdout = source.iloc[holdout_indices].sort_values(["domain_group", "url"]).reset_index(drop=True)
    holdout[["url", "label", "domain_group"]].to_csv(holdout_path, index=False)

    registry = {
        "dataset_name": dataset_path.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "split_strategy": "deterministic_group_shuffle_by_registrable_domain",
        "split_random_state": 42,
        "immutable_holdout_fraction_target": 0.10,
        "immutable_holdout_rows": int(len(holdout)),
        "immutable_holdout_sha256": sha256_file(holdout_path),
        "holdout_rule": "Never use this file to fit features, calibrators, thresholds, or models. Regenerate only with an explicit --force and a new registry version.",
        "provenance": governance,
    }
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")
    return registry



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Replace the existing immutable holdout intentionally.")
    args = parser.parse_args()
    print(json.dumps(prepare_governed_dataset(force=args.force), indent=2, sort_keys=True))
