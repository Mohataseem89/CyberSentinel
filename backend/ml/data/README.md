# Training-data governance

`final_training_dataset.csv` is the current source dataset. It is handled as raw
input: do not add unreviewed user feedback, URLs from scans, secrets, or private
URLs to it. Keep original dataset licences and provenance records with the source
before publishing or redistributing it.

Run `python -m ml.prepare_governed_dataset` from `backend/` once for a source
version. It creates an immutable domain-grouped holdout and a dataset registry.
The source has no collection timestamps, so this project does **not** claim a
temporal split. `dataset_registry.json` records that limitation.

The holdout is only for final evaluation. It must never be used for fitting,
calibration, threshold selection, or manual model tuning.
