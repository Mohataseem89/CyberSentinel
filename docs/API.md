# API reference

Base URL in local development: `http://localhost:5000`.

All clients should treat error bodies as untrusted text for display and should not expose authorization tokens in logs or URLs.

## Public health

### `GET /health`

Returns a small health response describing the active analyzer and that remote content fetching is disabled.

## URL scanning

### `POST /analyze`

Request:

```json
{
  "url": "https://example.com/path"
}
```

Requirements:

- HTTP/HTTPS URL only.
- Request body subject to `MAX_REQUEST_BYTES`.
- Endpoint is rate-limited.

Optional authentication can be supplied with `Authorization: Bearer <token>`.

To persist owner-scoped history, an authenticated client must additionally send:

```http
X-Retain-Scan: true
```

Without that explicit header, no scan-history row is created.

Representative response fields:

```json
{
  "url": "https://example.com/path",
  "final_verdict": "Unknown",
  "threat_score": null,
  "confidence": "low",
  "evidence": [],
  "limitations": [],
  "indicators": [],
  "recommendations": []
}
```

Verdicts: `Safe`, `Suspicious`, `Dangerous`, `Unknown`.

## Authentication

### `POST /api/auth/register`
Creates a user account after server-side validation and rate limiting.

### `POST /api/auth/login`
Returns an access token and user object after credential verification. Rate-limited.

### `GET /api/auth/me`
Requires JWT.

### `GET /api/auth/check`
Authentication/status helper defined by the auth blueprint.

## Owner-scoped history

All history endpoints require JWT authentication and operate on the authenticated user's rows only.

### `GET /api/history?limit=25`
Returns retained scans, maximum requested limit 100.

### `GET /api/history/export`
Returns up to the export limit from the authenticated user's retained history.

### `DELETE /api/history/{scan_id}`
Deletes a retained scan only when it belongs to the authenticated user.

## Feedback

### `POST /api/feedback`
Submits a URL classification report for human review. May be anonymous or authenticated.

### `GET /api/feedback`
Admin only.

### `PUT /api/feedback/{id}/approve`
Admin only. Marks feedback reviewed/approved; does not automatically retrain the model.

### `PUT /api/feedback/{id}/reject`
Admin only.

### `GET /api/feedback/export-approved`
Admin only. Downloads approved feedback in CSV form.

### `GET /api/feedback/stats`
Admin only.

## Model administration

### `POST /api/admin/retrain-model`
The project does not support online retraining as the trusted production training path. Model training must be performed offline through the governed ML pipeline.

### `POST /api/admin/reload-model`
Treat runtime model replacement as an operationally controlled action. Review the implementation and deployment policy before exposing any such control in production.

## QR scanning

### `POST /api/qr/scan`
Accepts multipart input for QR URL extraction/scanning. Apply upload-size and content-type controls at both application and reverse-proxy layers.

## Disabled legacy analytics

`backend/analytics.py` remains in the repository for historical/refactoring purposes, but its blueprint is not registered in the active app because the previous global queries could expose data across users. Do not document those endpoints as production APIs until they are rewritten and tested as owner-scoped aggregates.
