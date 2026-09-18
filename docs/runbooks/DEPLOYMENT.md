# Deployment runbook

## Pre-deployment

- Review the target commit/PR and dependency changes.
- Run frontend lint, unit tests, build, bundle-budget check, and Playwright tests.
- Run backend unit/security tests.
- Confirm required environment variables exist in the deployment secret store.
- Confirm `FRONTEND_URL` and `VITE_API_BASE_URL` use production HTTPS origins.
- Set `VITE_PUBLIC_SITE_URL` to the canonical frontend HTTPS origin.
- Run `PUBLIC_SITE_URL=https://your-production-origin npm run seo:sitemap` so every sitemap `<loc>` is an absolute canonical production URL.
- Confirm robots/noindex behavior for private routes.
- Review model manifest/evaluation/model card when model artifacts changed.
- Confirm database migrations/backups and rollback steps.

## Deploy

Deploy frontend/backend using immutable version identifiers where possible. Do not build production images with `.env` files containing secrets copied into the image layers.

## Smoke tests

- `GET /health` succeeds.
- Public scanner loads.
- A known benign test URL and a synthetic suspicious test URL return valid schema responses without visiting the target page.
- Login works for a test account.
- Cross-user history access is impossible.
- Admin-only feedback endpoints reject non-admin users.
- `/robots.txt` and `/sitemap.xml` are reachable.
- Public pages have canonical metadata.
- Private/dashboard/admin/result routes have `noindex`.

## Rollback

Roll back the application and, when relevant, model artifacts together to a previously verified release. Database schema changes require a separately tested rollback or forward-fix plan.
