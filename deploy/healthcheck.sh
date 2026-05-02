#!/bin/bash
# ARGOS — Post-Deploy Healthcheck

IMAC="gianlucadistasi@192.168.1.2"
PASS=0
FAIL=0

check() {
    if [ "$1" = "PASS" ]; then
        echo "  OK  $2"
        PASS=$((PASS+1))
    else
        echo "  FAIL $2"
        FAIL=$((FAIL+1))
    fi
}

echo "=== ARGOS Healthcheck ==="

# 1. WA Daemon reachable
STATUS=$(ssh "$IMAC" "curl -sf http://localhost:9191/status" 2>/dev/null)
if [ -n "$STATUS" ]; then
    WA=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('wa_status','?'))" 2>/dev/null)
    [ "$WA" = "connected" ] && check "PASS" "WA daemon connected" || check "FAIL" "WA daemon status: $WA"
else
    check "FAIL" "WA daemon unreachable"
fi

# 2. DB integrity
INTEGRITY=$(ssh "$IMAC" "sqlite3 /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite 'PRAGMA integrity_check;'" 2>/dev/null)
[ "$INTEGRITY" = "ok" ] && check "PASS" "DB integrity OK" || check "FAIL" "DB integrity: $INTEGRITY"

# 3. PM2 process online
PM2_STATUS=$(ssh "$IMAC" "export PATH=\$HOME/.nvm/versions/node/v20.11.0/bin:\$HOME/.npm-global/bin:\$PATH; pm2 jlist 2>/dev/null | python3 -c \"import sys,json; procs=json.load(sys.stdin); print('online' if any(p.get('pm2_env',{}).get('status')=='online' for p in procs) else 'down')\"" 2>/dev/null)
[ "$PM2_STATUS" = "online" ] && check "PASS" "PM2 process online" || check "FAIL" "PM2 status: $PM2_STATUS"

# 4. Conversations table exists
CONV=$(ssh "$IMAC" "sqlite3 /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite 'SELECT COUNT(*) FROM conversations;'" 2>/dev/null)
[ -n "$CONV" ] && check "PASS" "Conversations table: $CONV dealers" || check "FAIL" "Conversations table missing"

echo ""
echo "Result: $PASS PASS / $FAIL FAIL"
[ $FAIL -eq 0 ] && echo "HEALTHY" || echo "UNHEALTHY"
exit $FAIL
