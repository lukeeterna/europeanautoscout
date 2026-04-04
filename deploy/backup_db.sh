#!/bin/bash
# ARGOS — SQLite Backup (cron every 6h on iMac)
# Crontab: 0 */6 * * * bash /Users/gianlucadistasi/Documents/app-antigravity-auto/current/deploy/backup_db.sh

DB="/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite"
BACKUP_DIR="/Users/gianlucadistasi/Documents/argos-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Use sqlite3 .backup (safe with WAL) — NEVER use cp
sqlite3 "$DB" ".backup '$BACKUP_DIR/dealer_network_$TIMESTAMP.sqlite'" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "$(date) — Backup OK: dealer_network_$TIMESTAMP.sqlite" >> "$BACKUP_DIR/backup.log"
else
    echo "$(date) — Backup FAILED" >> "$BACKUP_DIR/backup.log"
    # Alert via Telegram
    TOKEN=$(grep ARGOS_TELEGRAM_TOKEN /Users/gianlucadistasi/Documents/app-antigravity-auto/wa-intelligence/.env 2>/dev/null | cut -d= -f2)
    CHAT=$(grep ARGOS_TELEGRAM_CHAT_ID /Users/gianlucadistasi/Documents/app-antigravity-auto/wa-intelligence/.env 2>/dev/null | cut -d= -f2)
    [ -n "$TOKEN" ] && curl -sf "https://api.telegram.org/bot$TOKEN/sendMessage" \
        -d "chat_id=${CHAT:-931063621}&text=ARGOS BACKUP FAILED: $(date)" > /dev/null 2>&1
fi

# Keep last 20 backups
ls -t "$BACKUP_DIR"/dealer_network_*.sqlite 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null
