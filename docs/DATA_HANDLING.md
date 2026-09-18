# Data handling

## URL scans

A URL submitted to `POST /analyze` is processed to produce the response. The backend intentionally does not open the destination webpage.

Persistent scan history is **opt-in**. A scan is saved only when:

1. a valid authenticated identity is present, and
2. the client sends `X-Retain-Scan: true`.

Saved history stores:

- user ID
- SHA-256 hash of the submitted raw URL
- redacted URL form (`domain/…`)
- domain
- verdict and risk fields
- model/reputation summary fields
- creation timestamp

The raw URL is not stored in the `Scan` history model.

## Feedback reports

Feedback submitted to `POST /api/feedback` is designed for human review. The current `Feedback` model stores the submitted URL, category, observed classification, CyberSentinel prediction, description, status, timestamp, and optional user ID.

Because a feedback report can contain a raw URL, operators must apply an explicit retention/deletion policy and restrict access to administrators who need it.

Approved feedback does not automatically modify the model. Promotion into a training dataset is an offline governance step.

## Accounts

The `User` model stores username, email, password hash, role, account state, and creation timestamp. Passwords are hashed with bcrypt.

## Third parties

VirusTotal is optional. When enabled, CyberSentinel computes VirusTotal's URL report identifier locally and requests an existing report. It does not submit the URL to VirusTotal for a new scan. VirusTotal still operates under its own terms, retention practices, and privacy policy. Operators must disclose any additional third-party services they enable.

## Logs and infrastructure

The source code sets an access logger hook and request ID, but actual production log retention depends on hosting configuration. Do not claim that URLs, IP addresses, headers, or account identifiers are absent from infrastructure logs unless that has been verified in the deployed environment.

## Sensitive input warning

Do not submit passwords, API keys, access tokens, password-reset links, private document links, or confidential internal URLs.
