# Production release audit

This checklist is a release gate, not a claim that any scanner guarantees safety.

## Reliability and security
- Single URL scans reject non-HTTP(S), credentials, localhost/private IP literals and oversized input. Remote page fetching remains disabled.
- Bulk jobs are authenticated, owner-scoped, paginated, quota-limited, cancellable, retry-bounded and retention-cleaned.
- File scans require authentication and explicit consent; validate magic/type and size; never execute uploads; originals are deleted after analysis. Scanner failure must yield `UNABLE_TO_COMPLETE`, never a clean verdict.
- Production secrets stay in provider secret/env configuration and must never be logged or committed.
- CORS uses explicit HTTPS origins; security headers and no-store API caching are enabled.
- Before horizontal backend scaling, replace the in-process rate-limit store with a shared backend.

## Detection quality
- Re-run the governed holdout evaluation after every model/artifact change. Record precision, recall, F1, confusion matrix and calibration.
- Maintain separate benign, phishing and malicious URL sets with provenance and no train/test overlap.
- Review false positives and false negatives manually. Do not tune against the final holdout.
- Verify: unavailable evidence => Unknown; borderline score => Unknown; VirusTotal positives escalate; disagreement is exposed in evidence/limitations.
- Never market `Safe` as a guarantee.

## Performance
- `python backend/scripts/profile_scan.py` remains within its ML latency budget.
- `npm run perf:build` passes bundle budgets.
- Run Lighthouse against production mobile and desktop; investigate LCP, CLS, INP/TBT, accessibility, best practices and SEO regressions.
- Verify bulk polling stops/backs off appropriately and result pagination never downloads the entire job unintentionally.

## UX/accessibility
- Keyboard navigation, focus states, labels, alert semantics and contrast are checked.
- Scanner, bulk, QR and file flows have explicit loading, unavailable, rate-limit and failure states.
- Risk verdicts always include reasons/limitations where evidence exists.
- Test narrow mobile widths and large desktop widths.

## SEO/public pages
- Generate sitemap with the production origin before release.
- Verify canonical, title, description, OG/Twitter metadata and public-only sitemap routes.
- Authenticated/private routes remain noindex.
- Verify Vercel SPA rewrites and direct navigation.

## Privacy
- No raw QR payload logging.
- No Authorization headers, cookies, URL query strings, reset tokens or uploaded bytes in application/Sentry logs.
- Retention workers are scheduled and verified.
- Feedback is the intentional exception that may retain a submitted URL; privacy documentation must say so.

## Dependencies
- Review `npm audit` and Python dependency advisories individually. Do not use `npm audit fix --force`.
- Remove unused runtime packages only after import/build/test verification.

## Browser extension
- Package with `EXTENSION_API_ORIGIN=https://cybersentinel-1-ib7e.onrender.com npm run extension:package`.
- Confirm least-privilege permissions, explicit user action, no background browsing monitoring, privacy wording, production API host, icons and manual Chrome testing.

## Final gate
Run lint, backend unit tests, frontend tests, production build, build budget, Playwright, Lighthouse and production smoke tests. Verify `/health`, `/ready`, one URL scan, auth, owner boundaries, bulk create/cancel/download, QR scan and file scan.
