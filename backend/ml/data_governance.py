"""Deterministic, privacy-conscious training-data governance helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

try:
    import tldextract
    _TLD_EXTRACT = tldextract.TLDExtract(suffix_list_urls=None)
except ImportError:  # Dependency is declared; fallback keeps governance readable in minimal tooling.
    _TLD_EXTRACT = None

LABEL_MAPPING = {"good": "legitimate", "bad": "phishing"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def registrable_domain(url: str) -> str:
    """Return a stable grouping key without any DNS or network access.

    This deliberately uses the hostname (not an IP address or a fetched page).
    It is conservative: a multi-part public suffix such as ``co.uk`` may be
    grouped less precisely than a Public Suffix List based implementation.
    """
    candidate = url if "://" in url else f"https://{url}"
    try:
        host = (urlsplit(candidate).hostname or "").lower().rstrip(".")
    except ValueError:
        host = ""
    if not host:
        return f"invalid:{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}"
    if _TLD_EXTRACT:
        extracted = _TLD_EXTRACT(host)
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
    labels = host.split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else host


def load_labeled_urls(dataset_path: str | Path) -> tuple[pd.DataFrame, dict]:
    """Load supported source data and remove exact duplicate URL/label rows.

    Conflicting labels for the same exact URL are excluded. They are ambiguous
    examples and retaining either label would contaminate evaluation.
    """
    dataset_path = Path(dataset_path)
    source = pd.read_csv(dataset_path, usecols=["url", "label"])
    raw_rows = len(source)
    source["url"] = source["url"].fillna("").astype(str).str.strip()
    source["label"] = source["label"].fillna("").astype(str).str.strip().str.lower().map(LABEL_MAPPING)
    source = source[(source["url"] != "") & source["label"].notna()].copy()
    valid_rows = len(source)
    source = source.drop_duplicates(subset=["url", "label"])
    duplicate_rows_removed = valid_rows - len(source)

    label_counts = source.groupby("url")["label"].nunique()
    conflicting_urls = set(label_counts[label_counts > 1].index)
    source = source[~source["url"].isin(conflicting_urls)].copy()
    source["domain_group"] = source["url"].map(registrable_domain)
    source = source.drop_duplicates(subset=["url"]).reset_index(drop=True)
    if source["label"].nunique() != 2:
        raise ValueError("Training data must include both legitimate and phishing labels.")


    return source, {
        "source_sha256": sha256_file(dataset_path),
        "raw_rows": int(raw_rows),
        "valid_rows": int(valid_rows),
        "exact_duplicate_rows_removed": int(duplicate_rows_removed),
        "conflicting_urls_excluded": int(len(conflicting_urls)),
        "usable_rows": int(len(source)),
        "class_balance": {str(label): int(count) for label, count in source["label"].value_counts().sort_index().items()},
        "temporal_split": {
            "status": "unavailable",
            "reason": "The current source has no trustworthy collection timestamp column; dates must not be inferred from URLs.",
        },
    }
