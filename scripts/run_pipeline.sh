#!/bin/bash
# ARGOS Pipeline Runner — cron: 0 */4 * * *
# Advances all vehicles through 7-state pipeline
# DISCOVERED → SCORED → ENRICHED → DATA_COMPLETE → DOSSIER_READY
set -euo pipefail

cd "$(dirname "$0")/.."
LOG="logs/pipeline_$(date +%Y%m%d).log"
mkdir -p logs

echo "=== ARGOS Pipeline Run $(date) ===" >> "$LOG"
python3 src/cove/pipeline_orchestrator.py --max-score 60 >> "$LOG" 2>&1

# Count DOSSIER_READY for alert
READY=$(python3 -c "
import duckdb
con = duckdb.connect('src/cove/data/cove_tracker.duckdb', read_only=True)
r = con.execute(\"SELECT COUNT(*) FROM vehicle_listings WHERE pipeline_state = 'DOSSIER_READY'\").fetchone()[0]
print(r)
con.close()
" 2>/dev/null || echo 0)

echo "DOSSIER_READY: $READY" >> "$LOG"
echo "=== Pipeline complete $(date) ===" >> "$LOG"

# Telegram alert if new dossiers ready
if [ "$READY" -gt 0 ]; then
    python3 -c "
import urllib.request, json, os
token = os.environ.get('TG_BOT_TOKEN', '')
chat = os.environ.get('TG_CHAT_ID', '931063621')
if token:
    msg = f'ARGOS Pipeline: $READY veicoli DOSSIER_READY per review.'
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = json.dumps({'chat_id': chat, 'text': msg}).encode()
    req = urllib.request.Request(url, data, {'Content-Type': 'application/json'})
    try: urllib.request.urlopen(req)
    except: pass
" 2>/dev/null || true
fi
