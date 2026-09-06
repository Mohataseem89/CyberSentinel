# CyberSentinel URL model card

## Model

- Version: `url-rf-v1-158b9501bf24`
- Type: lexical URL Random Forest with isotonic probability calibration
- Features: 21 fixed, local lexical features; no URL is fetched
- Dataset source SHA-256: `8399b37755fdbf6b44a660d3a790a17d99b9791107b7e6a156ab43e53e16f3c6`

## Evaluation protocol

An immutable domain-grouped holdout was excluded before fitting, calibration, and
threshold selection. Exact duplicates and conflicting duplicate labels were
removed. The source has no trustworthy timestamps, so no temporal claim is made.

## Immutable-holdout results

- Precision (phishing): 0.78064
- Recall (phishing): 0.610428
- F1 (phishing): 0.685121
- PR AUC: 0.792283
- ROC AUC: 0.921723
- Brier score: 0.075052

## Limitations

This is a risk signal, not proof that a URL is safe. The model does not inspect
page content, execute scripts, resolve DNS, or assess newly registered domains.
Scores can be wrong for novel attacks, benign URLs that resemble phishing, and
dataset populations that do not match real user traffic. Do not use the holdout
to improve this model; create a new versioned split for a new dataset release.
