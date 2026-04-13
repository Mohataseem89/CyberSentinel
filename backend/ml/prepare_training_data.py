import csv
import os
from typing import Dict, List, Set

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")

ORIGINAL_DATASET = os.path.join(DATA_DIR, "url_dataset.csv")
APPROVED_FEEDBACK_CSV = os.path.join(DATA_DIR, "approved_feedback.csv")
OUTPUT_DATASET = os.path.join(DATA_DIR, "final_training_dataset.csv")

# Label mapping
BAD_LABELS = {"phishing", "malware", "defacement"}
GOOD_LABELS = {"benign", "safe", "benign/safe"}

def normalize_text(value: str) -> str:
    return (value or "").strip().lower()

def map_actual_threat_to_label(actual_threat: str) -> str | None:
    value = normalize_text(actual_threat)

    if value in BAD_LABELS:
        return "bad"
    if value in GOOD_LABELS:
        return "good"
    return None

def load_original_dataset(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    if not os.path.exists(path):
        print(f" Original dataset not found: {path}")
        return rows

    with open(path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if "url" not in reader.fieldnames or "label" not in reader.fieldnames:
            raise ValueError(
                f"Original dataset must contain 'url' and 'label' columns. Found: {reader.fieldnames}"
            )

        for row in reader:
            url = (row.get("url") or "").strip()
            label = (row.get("label") or "").strip().lower()

            if not url or label not in {"good", "bad"}:
                continue

            rows.append({
                "url": url,
                "label": label
            })

    return rows

def load_approved_feedback_dataset(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    print(f"Reading approved feedback from: {path}")

    if not os.path.exists(path):
        print(f" Approved feedback CSV not found: {path}")
        return rows

    with open(path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required_columns = {"url", "actual_threat", "status"}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"Approved feedback CSV must contain {required_columns}. Found: {reader.fieldnames}"
            )

        for row in reader:
            status = normalize_text(row.get("status", ""))
            url = (row.get("url") or "").strip()
            actual_threat = row.get("actual_threat", "")

            if not url:
                continue

            if status and status != "approved":
                continue

            mapped_label = map_actual_threat_to_label(actual_threat)
            if mapped_label is None:
                continue

            rows.append({
                "url": url,
                "label": mapped_label
            })

    return rows

def merge_datasets(
    original_rows: List[Dict[str, str]],
    approved_rows: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    merged: List[Dict[str, str]] = []
    seen_urls: Set[str] = set()

    # keep original first
    for row in original_rows:
        normalized_url = row["url"].strip().lower()
        if normalized_url in seen_urls:
            continue

        merged.append(row)
        seen_urls.add(normalized_url)

    # append approved feedback only if URL not already present
    added_count = 0
    skipped_duplicates = 0

    for row in approved_rows:
        normalized_url = row["url"].strip().lower()

        if normalized_url in seen_urls:
            skipped_duplicates += 1
            continue

        merged.append(row)
        seen_urls.add(normalized_url)
        added_count += 1

    print(f" Added approved feedback rows: {added_count}")
    print(f" Skipped duplicate URLs: {skipped_duplicates}")

    return merged

def save_final_dataset(path: str, rows: List[Dict[str, str]]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["url", "label"])
        writer.writeheader()
        writer.writerows(rows)

def main() -> None:
    print("=" * 60)
    print(" Preparing final training dataset")
    print("=" * 60)

    original_rows = load_original_dataset(ORIGINAL_DATASET)
    print(f" Original dataset rows: {len(original_rows)}")

    approved_rows = load_approved_feedback_dataset(APPROVED_FEEDBACK_CSV)
    print(f" Approved feedback rows: {len(approved_rows)}")

    merged_rows = merge_datasets(original_rows, approved_rows)
    print(f" Final merged rows: {len(merged_rows)}")

    save_final_dataset(OUTPUT_DATASET, merged_rows)
    print(f" Saved final dataset to: {OUTPUT_DATASET}")

    print("=" * 60)
    print("Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()