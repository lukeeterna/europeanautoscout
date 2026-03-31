#!/bin/bash
# ARGOS Daily Scrape — cron: 0 5 * * *
# Scrapes BMW X3, GLC, Q5, Macan from AutoScout24 DE
# Persists to DuckDB as DISCOVERED state
set -euo pipefail

cd "$(dirname "$0")/.."
LOG="logs/scraper_$(date +%Y%m%d).log"
mkdir -p logs

echo "=== ARGOS Daily Scrape $(date) ===" >> "$LOG"

for spec in "BMW X3" "Mercedes GLC" "Audi Q5" "Porsche Macan"; do
    MAKE=$(echo "$spec" | cut -d' ' -f1)
    MODEL=$(echo "$spec" | cut -d' ' -f2-)
    echo "Scraping $MAKE $MODEL..." >> "$LOG"
    python3 src/cove/scraper_cove_pipeline.py "$MAKE" "$MODEL" --pages 3 \
        --portals autoscout24_de >> "$LOG" 2>&1 || true
    sleep 10
done

echo "=== Scrape complete $(date) ===" >> "$LOG"

# Telegram alert
python3 -c "
import urllib.request, json, os
token = os.environ.get('TG_BOT_TOKEN', '')
chat = os.environ.get('TG_CHAT_ID', '931063621')
if token:
    msg = 'ARGOS Daily Scrape completato. Controlla pipeline.'
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = json.dumps({'chat_id': chat, 'text': msg}).encode()
    req = urllib.request.Request(url, data, {'Content-Type': 'application/json'})
    try: urllib.request.urlopen(req)
    except: pass
" 2>/dev/null || true
