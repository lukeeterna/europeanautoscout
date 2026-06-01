#!/bin/bash
# CHAOS Test Suite — Daemon ARGOS

API_KEY="${ARGOS_API_KEY:?set ARGOS_API_KEY env var (see wa-intelligence/.env)}"
HOST="localhost:9191"
DRY_RUN="true"

echo "=== CHAOS 4: Sequential 10 requests ==="
COUNT=0
for i in 1 2 3 4 5 6 7 8 9 10; do
  RESP=$(curl -s -X POST "$HOST/send" \
    -H 'Content-Type: application/json' \
    -H "X-API-Key: $API_KEY" \
    -d "{\"phone\":\"393314928901\",\"message\":\"Load test $i\",\"dry_run\":$DRY_RUN}")
  if echo "$RESP" | grep -q '"status":"sent"'; then
    ((COUNT++))
  fi
  echo "Request $i: $RESP"
done
echo "CHAOS 4 Result: $COUNT/10 successful"

echo ""
echo "=== CHAOS 5: 50 sequential requests (HTTP codes) ==="
CODES=""
for i in $(seq 1 50); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$HOST/send" \
    -H 'Content-Type: application/json' \
    -H "X-API-Key: $API_KEY" \
    -d "{\"phone\":\"393314928901\",\"message\":\"Flood test $i\",\"dry_run\":$DRY_RUN}")
  CODES="$CODES $CODE"
done
echo "HTTP Codes: $CODES"
echo "CHAOS 5 Result: Should all be 200"

echo ""
echo "=== CHAOS 9: Oversized dealer_id ==="
BIG_ID=$(python3 -c "print('A' * 1000)")
RESP=$(curl -s -X POST "$HOST/send" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $API_KEY" \
  -d "{\"phone\":\"393314928901\",\"message\":\"test\",\"dealer_id\":\"$BIG_ID\",\"template_id\":\"DAY1_PREMIUM\",\"dry_run\":true}")
echo "CHAOS 9 Response: $RESP"

echo ""
echo "=== CHAOS 10: Special characters ==="
RESP=$(curl -s -X POST "$HOST/send" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $API_KEY" \
  -d "{\"phone\":\"393314928901\",\"message\":\"Test con euro € e apostrofo 's e accenti àèìòù\",\"dry_run\":true}")
echo "CHAOS 10 Response: $RESP"

echo ""
echo "=== CHAOS 14: Telegram logging check ==="
ssh gianlucadistasi@192.168.1.2 "export PATH=\$HOME/.npm-global/bin:/usr/local/bin:\$PATH && pm2 logs argos-wa-daemon --lines 30 --nostream 2>&1" > /tmp/daemon_logs.txt
echo "Logs saved to /tmp/daemon_logs.txt"
grep -i "telegram\|dispatch" /tmp/daemon_logs.txt | head -5
