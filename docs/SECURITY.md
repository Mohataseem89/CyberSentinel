# Security guidance

## Reporting a vulnerability

Do not publish exploit details, secrets, database contents, or private user URLs in a public issue. Contact the repository maintainers through a private channel when possible and include only the minimum information needed to reproduce the problem safely.

## Baseline production controls

- Terminate TLS and redirect HTTP to HTTPS.
- Restrict CORS to the real frontend origin.
- Store secrets in a managed secret store, not repository files.
- Use a least-privilege PostgreSQL role and encrypted database connections.
- Put the backend behind upstream request-size limits, rate limiting/WAF controls, and health monitoring.
- Use a shared rate-limit store for multiple replicas.
- Centralize logs while minimizing sensitive values.
- Back up the database according to an explicit retention policy and test restore procedures.
- Pin/review dependency updates and protect the deployment branch.
- Keep model artifacts versioned and roll-backable.

## Content/security headers

The Flask app currently adds `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`. Production frontends should also configure a deployment-appropriate Content Security Policy (CSP) after enumerating the exact required origins.

## Secret examples

Documentation intentionally does not include working secrets. Generate unique random values per environment. If a secret appears in source control, logs, screenshots, a ticket, or chat, assume exposure and rotate it.
