# Incident response runbook

## 1. Triage

Classify the incident: credential exposure, unauthorized account/admin access, user-data exposure, model/artifact tampering, dependency compromise, abusive traffic, outage, or third-party reputation-service incident.

Record UTC timestamps, affected environment/version, observable symptoms, and the minimum evidence required for investigation. Avoid copying raw sensitive URLs into broad-access tickets.

## 2. Contain

Depending on the incident:

- Disable or restrict the affected endpoint at the load balancer/application layer.
- Revoke/rotate compromised API keys, JWT signing keys, database credentials, and deployment tokens.
- Invalidate sessions when signing/authentication material is compromised.
- Restrict administrative access.
- Roll back to the last known-good application/model version.
- Disable a compromised third-party integration.

## 3. Preserve evidence

Preserve relevant deployment logs, audit logs, commit/deployment identifiers, model hashes, database audit evidence, and infrastructure events under restricted access. Do not modify original evidence during analysis.

## 4. Eradicate and recover

Patch the root cause, run tests, review adjacent trust boundaries, deploy through normal review controls, verify health, and monitor for recurrence. Restore data only from known-good backups.

## 5. Communication

Use factual language. State what is known, what remains unknown, the affected time window, affected data/systems, actions taken, and required user actions. Do not claim that no data was accessed unless evidence supports that conclusion.

## 6. Post-incident review

Document root cause, detection gaps, time-to-containment, control failures, remediation owners, deadlines, and tests that prevent regression. Update the threat model/runbooks when assumptions changed.
