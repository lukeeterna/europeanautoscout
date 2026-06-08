#!/bin/bash
# ARGOS — Session Start Verification
# Eseguito automaticamente da SessionStart hook

cd "$(dirname "$0")/../.." 2>/dev/null || cd /Users/macbook/Documents/combaretrovamiauto-enterprise

echo "=== ARGOS Session Start ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Verifica skill critiche
MISSING=0
for skill in skill-argos skill-cove skill-argos-debug skill-loader skill-handover; do
  if [ ! -f ".claude/skills/$skill/SKILL.md" ] && [ ! -f ".claude/skills/$skill/skill.md" ]; then
    echo "MISSING SKILL: $skill"
    MISSING=$((MISSING+1))
  fi
done
[ $MISSING -eq 0 ] && echo "Skills: OK (0 missing)" || echo "Skills: $MISSING MISSING"

# 2. Verifica CLAUDE.md (lean v2026.4 — TEST_FOUNDER + @-include rules sono i marker)
if grep -q "TEST_FOUNDER" CLAUDE.md 2>/dev/null && grep -q "^@.claude/rules/" CLAUDE.md 2>/dev/null; then
  LINES=$(wc -l < CLAUDE.md | tr -d ' ')
  echo "CLAUDE.md: OK ($LINES lines)"
else
  echo "WARN: CLAUDE.md missing TEST_FOUNDER rule or @-include rules block"
fi

# 3. Verifica rules
RULES=$(ls .claude/rules/*.md 2>/dev/null | wc -l | tr -d ' ')
echo "Rules: $RULES files"

# 4. Verifica connessione iMac (timeout 5s, non bloccante)
WA_STATUS=$(ssh -o ConnectTimeout=5 -o ServerAliveInterval=5 gianlucadistasi@192.168.1.2 "curl -sf -m 5 http://localhost:9191/status" 2>/dev/null)
if [ -n "$WA_STATUS" ]; then
  echo "$WA_STATUS" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  wa=d.get('wa_status','?')
  sent=d.get('daily_sent',0)
  limit=d.get('daily_limit',30)
  remain=d.get('daily_remaining',0)
  print(f'WA Daemon: {wa} | Sent: {sent}/{limit} | Remaining: {remain}')
except:
  print('WA Daemon: PARSE ERROR')
" 2>/dev/null
else
  echo "WA Daemon: UNREACHABLE (iMac offline or daemon down)"
fi

echo ""

# 5. Substrato stato (Gate A): rigenera la tabella anelli da check eseguibili PRIMA di CC.
#    "VERIFIED" sopravvive solo se il check ripassa in questa sessione (refresh.py).
#    SESSION_ID: env ARGOS_SESSION se settato, altrimenti label auto (cosmetico: il
#    downgrade dello stale funziona comunque; Luke puo' rilanciare con S<N> reale).
SESS="${ARGOS_SESSION:-auto-$(date +%Y%m%dT%H%M%SZ)}"
if [ -f state/refresh.sh ]; then
  echo "State refresh ($SESS):"
  bash state/refresh.sh "$SESS" 2>&1 | sed 's/^/  /' || echo "  refresh FAILED (vedi STATE.md)"
else
  echo "State refresh: SKIP (state/refresh.sh assente)"
fi

echo ""
echo "=== Ready ==="
