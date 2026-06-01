#!/bin/bash
# CHAOS 8: Rapid PM2 restart (5x in 30 sec)

export PATH=$HOME/.npm-global/bin:/usr/local/bin:$PATH

echo "=== CHAOS 8: Rapid PM2 restart 5x (30 sec total) ==="
echo "Pre-restart status:"
pm2 list | grep argos-wa-daemon

for i in 1 2 3 4 5; do
  echo "Restart $i/5..."
  pm2 restart argos-wa-daemon --silent
  sleep 6
done

echo "Waiting 15 sec for daemon stabilization..."
sleep 15

echo ""
echo "Post-restart status:"
pm2 list | grep argos-wa-daemon

echo ""
echo "Health check post-restart:"
curl -s localhost:9191/status | python3 -m json.tool

echo ""
echo "Chrome processes:"
ps aux | grep chromium | grep -v grep | wc -l

echo ""
echo "Daemon uptime (should be low, few seconds):"
curl -s localhost:9191/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Uptime: {d['uptime_sec']}s\")"
