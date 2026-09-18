# URL phishing model card

The runtime-generated source of truth is [`backend/data/MODEL_CARD.md`](../backend/data/MODEL_CARD.md). This document explains how to interpret that generated artifact operationally.

## Intended use

The model is one risk signal for HTTP/HTTPS URL phishing detection. It is designed to support cautious triage and is combined with independent reputation evidence when available.

## Not intended for

- Declaring a URL mathematically or legally “safe”.
- Making a sole authorization decision for payments, credentials, data release, or security-control bypasses.
- Detecting malicious page content that is not represented in the URL text.
- Claiming real-world performance for populations not represented by the evaluation data.

## Inputs and features

The current model uses a fixed set of local lexical URL features. The online model path does not need to open the target webpage.

## Evaluation

The generated model card reports the exact model version, feature count, dataset hash, immutable domain-grouped holdout protocol, precision, recall, F1, PR AUC, ROC AUC, and Brier score.

The current dataset does not provide trustworthy collection timestamps, so the project deliberately makes no temporal-split claim.

## Promotion requirements

Before replacing runtime artifacts:

1. Build a governed dataset version and immutable holdout.
2. Review duplicate/conflict handling and provenance.
3. Train/calibrate offline.
4. Review `model_evaluation.json` and generated `MODEL_CARD.md`.
5. Confirm the feature schema and class labels match runtime expectations.
6. Run backend tests.
7. Deploy as a versioned release with rollback capability.

Never use the immutable holdout to iteratively tune the same model version.
