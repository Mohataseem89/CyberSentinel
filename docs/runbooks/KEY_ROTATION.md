# Key and credential rotation runbook

Rotate a credential after suspected disclosure, unauthorized use, maintainer offboarding, provider guidance, or scheduled security maintenance.

## Order of operations

1. Identify every environment and consumer of the credential.
2. Create a replacement through the provider/secret manager.
3. Update the target environment using the deployment secret mechanism.
4. Restart/redeploy only the components that need the new value.
5. Verify authentication/integration health.
6. Revoke the old credential.
7. Review logs for misuse during the exposure window.
8. Document the rotation without recording the secret value.

## JWT / application signing keys

Changing `JWT_SECRET_KEY` invalidates existing JWTs when the old key is no longer accepted. Treat this as desirable during compromise and communicate the need to sign in again.

`SECRET_KEY` and `JWT_SECRET_KEY` should be unique values, not aliases of the same secret.

## Database credentials

Use a new password/credential, update the secret store, verify connectivity, and revoke the old password. If database compromise is suspected, also review roles, grants, connections, audit logs, and backups.

## VirusTotal

Generate/revoke keys using the provider account. After rotation, verify that unavailable/limited reputation service degrades safely to reduced evidence rather than a false `Safe` conclusion.
