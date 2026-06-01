#!/bin/bash
# CHAOS 13: Graceful shutdown test

export PATH=$HOME/.npm-global/bin:/usr/local/bin:$PATH

echo "=== CHAOS 13: Graceful shutdown test ==="

echo "Pre-stop status:"
pm2 list | grep argos-wa-daemon

echo ""
echo "Stopping daemon..."
pm2 stop argos-wa-daemon

sleep 3

echo ""
echo "Chrome processes after stop (should be 0):"
CHROME_COUNT=$(ps aux | grep chromium | grep -v grep | wc -l)
echo "Count: $CHROME_COUNT"

echo ""
echo "Restarting daemon..."
pm2 start argos-wa-daemon

echo "Waiting 15 sec for WA reconnection..."
sleep 15

echo ""
echo "Post-restart status:"
curl -s localhost:9191/status | python3 -m json.tool

echo ""
echo "Graceful shutdown verdict:"
if [ "$CHROME_COUNT" -eq 0 ]; then
  echo "PASS: Chrome cleanly shutdown (0 processes)"
else
  echo "WARN: $CHROME_COUNT Chrome processes remained"
fi

curl -s localhost:9191/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"WA Status: {d['wa_status']}\")"
