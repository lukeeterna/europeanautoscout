#!/bin/bash
# sync_db_snapshot.sh — Copia snapshot SQLite da iMac per query locali
# Uso: ./tools/sync_db_snapshot.sh
# Il DB viene copiato in /tmp/argos_dashboard_snapshot.db (read-only locale)

set -e

REMOTE="gianlucadistasi@192.168.1.2"
REMOTE_DB="~/Documents/app-antigravity-auto/dealer_network.sqlite"
LOCAL_DB="/tmp/argos_dashboard_snapshot.db"

echo "[SYNC] Copying DB snapshot from iMac..."
scp "${REMOTE}:${REMOTE_DB}" "${LOCAL_DB}"
echo "[SYNC] Done: ${LOCAL_DB} ($(du -h ${LOCAL_DB} | cut -f1))"
echo "[SYNC] Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
