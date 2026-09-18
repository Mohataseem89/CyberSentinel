# Threat model

## Assets

- User credentials and JWT signing material.
- Database credentials and stored account/feedback/history data.
- VirusTotal API key when configured.
- Model artifacts and their integrity.
- Service availability and reputation quotas.
- Privacy of URLs submitted by users.

## Primary adversaries

- Anonymous internet users abusing public scan/auth endpoints.
- Attackers submitting crafted URLs or oversized/malformed payloads.
- Credential-stuffing or account-takeover attempts.
- Malicious users trying to access another user's history or administrative feedback.
- Supply-chain attackers modifying model/code/dependencies.
- Attackers seeking SSRF through URL-scanning behavior.

## Major threats and controls

### SSRF and target-side interaction

**Threat:** a scanner that fetches arbitrary user URLs can reach private network resources or dangerous protocols.

**Control:** CyberSentinel's online URL analyzer uses local lexical analysis and optional reputation evidence; remote webpage-content fetching is disabled. URL normalization restricts accepted schemes and validates input before analysis.

### Cross-user data exposure

**Threat:** global history/analytics endpoints can leak scans between users.

**Control:** owner-scoped `/api/history` routes require JWT authentication. The legacy global analytics blueprint is not registered.

### Unnecessary URL retention

**Threat:** raw user URLs may contain private identifiers or secrets.

**Control:** scan history is explicit opt-in and stores a hash plus redacted URL. Feedback is a separate workflow that intentionally stores the reported URL for review and therefore needs stronger access/retention controls.

### Brute force and API abuse

**Threat:** repeated scans or auth attempts can exhaust resources or attack accounts.

**Control:** a fixed-window rate limiter covers `/analyze`, login, and registration. Production multi-replica systems need a shared limiter such as Redis, upstream WAF/rate controls, and account-abuse monitoring.

### Model evasion and unsafe certainty

**Threat:** attackers can craft novel URLs that evade lexical patterns; users may overtrust a low score.

**Control:** evidence-aware risk aggregation, calibration, model card/evaluation artifacts, and an `Unknown` verdict when evidence is insufficient. A low ML score alone is not sufficient to call a URL safe.

### Malicious or poisoned feedback

**Threat:** attackers submit mislabeled feedback to poison the model.

**Control:** feedback requires human review and does not automatically retrain or promote a model.

### Secret leakage

**Threat:** committed `.env` values, logs, screenshots, CI output, or copied examples expose credentials.

**Control:** examples contain placeholders only; real secrets remain environment-specific. Follow `docs/runbooks/KEY_ROTATION.md` after suspected exposure.

## Out of scope / residual risk

- Detecting every compromised legitimate website.
- Browser exploit detection or sandboxing.
- Email attachment malware analysis.
- DNS/network telemetry unless explicitly added later.
- Guaranteed detection of newly registered or previously unseen malicious URLs.
- Protection from infrastructure misconfiguration outside this repository.
