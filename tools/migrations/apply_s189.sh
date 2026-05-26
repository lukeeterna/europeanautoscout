#!/usr/bin/env bash
# apply_s189.sh — S189 HITL approval gate migration
# Runs via SSH on iMac, applies s189_approval_gate.sql
# Idempotent: safe to re-run. Output: JSON {status, backup_path, integrity}
# Usage: bash apply_s189.sh

set -euo pipefail

IMAC_HOST="gianlucadistasi@192.168.1.2"
DB_PATH="Documents/app-antigravity-auto/dealer_network.sqlite"
MIGRATION_SQL="$(cd "$(dirname "$0")" && pwd)/s189_approval_gate.sql"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# --- 1. Verify migration file exists locally ---
if [[ ! -f "$MIGRATION_SQL" ]]; then
    echo '{"status":"ERROR","error":"migration file not found: '"$MIGRATION_SQL"'"}' >&2
    exit 1
fi

# --- 2. Copy migration SQL to iMac /tmp ---
scp -q "$MIGRATION_SQL" "${IMAC_HOST}:/tmp/s189_approval_gate.sql"

# --- 3. Execute full migration sequence on iMac ---
ssh "$IMAC_HOST" bash -s -- "$DB_PATH" "$TIMESTAMP" << 'REMOTE_EOF'
set -euo pipefail

DB_PATH="$HOME/$1"
TIMESTAMP="$2"
BACKUP_PATH="${DB_PATH%.sqlite}_backup_${TIMESTAMP}.sqlite"

# --- Pre-check: DB file must exist ---
if [[ ! -f "$DB_PATH" ]]; then
    printf '{"status":"ERROR","error":"DB not found: %s"}\n' "$DB_PATH" >&2
    exit 1
fi

# --- Pre-check: WAL mode ---
JOURNAL_MODE=$(sqlite3 "$DB_PATH" "PRAGMA journal_mode;")
BUSY_TIMEOUT=$(sqlite3 "$DB_PATH" "PRAGMA busy_timeout;")

if [[ "$JOURNAL_MODE" != "wal" ]]; then
    # Enable WAL — safe even with active readers
    sqlite3 "$DB_PATH" "PRAGMA journal_mode=WAL;"
    JOURNAL_MODE="wal(set-by-migration)"
fi

if [[ "$BUSY_TIMEOUT" -lt 10000 ]]; then
    sqlite3 "$DB_PATH" "PRAGMA busy_timeout=10000;"
    BUSY_TIMEOUT="10000(set-by-migration)"
fi

# --- Idempotency pre-check: skip if table already exists ---
TABLE_EXISTS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='dossiers';")

if [[ "$TABLE_EXISTS" -eq 1 ]]; then
    # Table exists — verify index also present, then report already-applied
    INDEX_EXISTS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_dossier_pending';")
    INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | head -1)
    printf '{"status":"ALREADY_APPLIED","table":"dossiers","index_exists":%s,"integrity":"%s","journal_mode":"%s","busy_timeout":"%s"}\n' \
        "$INDEX_EXISTS" "$INTEGRITY" "$JOURNAL_MODE" "$BUSY_TIMEOUT"
    exit 0
fi

# --- Backup via sqlite3 .backup (safe with WAL) ---
sqlite3 "$DB_PATH" ".backup '$BACKUP_PATH'"

if [[ ! -f "$BACKUP_PATH" ]]; then
    printf '{"status":"ERROR","error":"backup failed — file not created at %s"}\n' "$BACKUP_PATH" >&2
    exit 1
fi

# --- Apply migration ---
sqlite3 "$DB_PATH" < /tmp/s189_approval_gate.sql

# --- Post-migration: integrity check ---
INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | head -1)
if [[ "$INTEGRITY" != "ok" ]]; then
    printf '{"status":"ERROR","error":"integrity_check failed: %s","backup_path":"%s"}\n' \
        "$INTEGRITY" "$BACKUP_PATH" >&2
    exit 1
fi

# --- Verify table + index exist ---
TABLE_OK=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='dossiers';")
INDEX_OK=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_dossier_pending';")

if [[ "$TABLE_OK" -ne 1 || "$INDEX_OK" -ne 1 ]]; then
    printf '{"status":"ERROR","error":"post-apply verify failed table=%s index=%s","backup_path":"%s"}\n' \
        "$TABLE_OK" "$INDEX_OK" "$BACKUP_PATH" >&2
    exit 1
fi

# --- Cleanup migration SQL from /tmp ---
rm -f /tmp/s189_approval_gate.sql

# --- Success output ---
printf '{"status":"OK","backup_path":"%s","integrity":"ok","table":"dossiers","index":"idx_dossier_pending","journal_mode":"%s","busy_timeout":"%s"}\n' \
    "$BACKUP_PATH" "$JOURNAL_MODE" "$BUSY_TIMEOUT"
REMOTE_EOF
