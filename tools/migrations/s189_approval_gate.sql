-- Migration S189: HITL approval gate for dossier dispatch
-- Target DB: ~/Documents/app-antigravity-auto/dealer_network.sqlite (iMac)
-- Idempotent: safe to re-run (CREATE IF NOT EXISTS throughout)

PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=10000;

CREATE TABLE IF NOT EXISTS dossiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dealer_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT,
    created_ts INTEGER NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(approval_status IN ('PENDING','APPROVED','REJECTED')),
    approval_ts INTEGER,
    approval_user TEXT,
    reject_reason TEXT,
    UNIQUE(dealer_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_dossier_pending ON dossiers(approval_status)
    WHERE approval_status = 'PENDING';
