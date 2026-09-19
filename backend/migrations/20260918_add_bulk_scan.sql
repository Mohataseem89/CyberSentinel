CREATE TABLE IF NOT EXISTS bulk_scan_jobs (
 id SERIAL PRIMARY KEY, public_id VARCHAR(36) UNIQUE NOT NULL, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 status VARCHAR(32) NOT NULL, total_urls INTEGER NOT NULL DEFAULT 0, processed INTEGER NOT NULL DEFAULT 0, successful INTEGER NOT NULL DEFAULT 0, failed INTEGER NOT NULL DEFAULT 0,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, started_at TIMESTAMP NULL, completed_at TIMESTAMP NULL, expires_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_bulk_scan_jobs_owner_status ON bulk_scan_jobs(user_id,status);
CREATE TABLE IF NOT EXISTS bulk_scan_items (
 id SERIAL PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES bulk_scan_jobs(id) ON DELETE CASCADE, row_number INTEGER NOT NULL,
 normalized_url TEXT NULL, url_redacted VARCHAR(512) NOT NULL, status VARCHAR(32) NOT NULL DEFAULT 'QUEUED', attempts INTEGER NOT NULL DEFAULT 0,
 final_verdict VARCHAR(50) NULL, threat_score FLOAT NULL, error_code VARCHAR(64) NULL,
 UNIQUE(job_id,row_number)
);
CREATE INDEX IF NOT EXISTS ix_bulk_scan_items_job_status ON bulk_scan_items(job_id,status);
