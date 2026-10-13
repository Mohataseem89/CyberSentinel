# Detection quality audit

Source: `backend/data/model_evaluation.json` from the governed immutable domain-grouped holdout.

## Current measured quality
- Holdout rows: 33,453
- Accuracy: 0.8897
- ROC-AUC: 0.9191
- PR-AUC: 0.7904
- Brier score: 0.0792
- Expected calibration error: 0.0311
- Phishing precision: 0.7804
- Phishing recall: 0.6090
- Phishing F1: 0.6841
- Confusion matrix (`legitimate`, `phishing`): `[[25769,1124],[2565,3995]]`

## Release interpretation
The model is not accurate enough to present an ML-only low score as a guarantee of safety. On this holdout it missed 2,565 of 6,560 phishing examples at the recorded 0.5 model threshold. The production risk engine therefore must remain conservative: missing evidence and borderline evidence stay `Unknown`; independent reputation positives escalate the verdict; UI copy must describe `Safe` as a risk indicator rather than a guarantee.

## Required next model iteration
1. Preserve the immutable holdout; do not tune on it.
2. Tune operating thresholds on a separate validation/calibration split for higher phishing recall while measuring the false-positive cost.
3. Add a newer, independently sourced evaluation set with trustworthy provenance/timestamps. The current governance report explicitly says a temporal split is unavailable because the source has no trustworthy collection timestamp.
4. Report precision/recall/F1/PR-AUC/calibration and false-positive/false-negative counts by slice.
5. Manually review representative false negatives and false positives before changing features.
6. Re-run disagreement tests for ML vs VirusTotal and unavailable-provider behavior.

This audit intentionally does not change the trained artifact or threshold without a validation-backed experiment.
