-- Apply once to an existing PostgreSQL database before enabling opt-in history.
ALTER TABLE scans ADD COLUMN IF NOT EXISTS url_hash VARCHAR(64);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS url_redacted VARCHAR(255);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;
CREATE INDEX IF NOT EXISTS ix_scans_url_hash ON scans (url_hash);
-- Existing raw URL records must be removed or migrated through an audited
-- one-time job before the legacy `url` column is dropped. Do not copy them
-- into the new history fields.
