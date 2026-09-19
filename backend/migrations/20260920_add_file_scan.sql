CREATE TABLE IF NOT EXISTS file_scan_jobs (
  id SERIAL PRIMARY KEY,
  public_id VARCHAR(36) UNIQUE NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status VARCHAR(32) NOT NULL DEFAULT 'QUEUED',
  attempts INTEGER NOT NULL DEFAULT 0,
  original_name VARCHAR(120) NOT NULL,
  storage_path TEXT,
  sha256 VARCHAR(64) NOT NULL,
  size_bytes INTEGER NOT NULL,
  detected_kind VARCHAR(32),
  detected_mime VARCHAR(120),
  malware_status VARCHAR(32),
  html_risk VARCHAR(16),
  verdict VARCHAR(40),
  indicators_json TEXT,
  error_code VARCHAR(64),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  expires_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_file_scan_jobs_owner_status ON file_scan_jobs(user_id,status);
CREATE INDEX IF NOT EXISTS ix_file_scan_jobs_expiry ON file_scan_jobs(expires_at);
