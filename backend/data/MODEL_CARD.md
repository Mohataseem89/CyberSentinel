# CyberSentinel URL model card

## Model

- Version: `url-rf-v1-1d07855c7a6a`
- Type: lexical URL Random Forest with isotonic probability calibration
- Features: 21 fixed, local lexical features; no URL is fetched
- Dataset source SHA-256: `567071f89972e444dc9fd239c2eceb112eed2128a2b33fbea41976d767a5b758`

## Evaluation protocol

An immutable domain-grouped holdout was excluded before fitting, calibration, and
threshold selection. Exact duplicates and conflicting duplicate labels were
removed. The source has no trustworthy timestamps, so no temporal claim is made.

## Immutable-holdout results

- Precision (phishing): 0.780426
- Recall (phishing): 0.608994
- F1 (phishing): 0.684134
- PR AUC: 0.790449
- ROC AUC: 0.919146
- Brier score: 0.079174

## Limitations

This is a risk signal, not proof that a URL is safe. The model does not inspect
page content, execute scripts, resolve DNS, or assess newly registered domains.
Scores can be wrong for novel attacks, benign URLs that resemble phishing, and
dataset populations that do not match real user traffic. Do not use the holdout
to improve this model; create a new versioned split for a new dataset release.
