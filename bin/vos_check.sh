#!/usr/bin/env bash
set -euo pipefail

PASS=0
FAIL=0

result() {
  local status="$1" label="$2"
  if [ "$status" = "PASS" ]; then
    echo "PASS $label"
    PASS=$((PASS + 1))
  else
    echo "FAIL $label"
    FAIL=$((FAIL + 1))
  fi
}

# a) HEAD == origin/s210/audit-master-plan (NON master)
LOCAL=$(git rev-parse HEAD 2>/dev/null)
REMOTE=$(git rev-parse origin/s210/audit-master-plan 2>/dev/null)
[ "$LOCAL" = "$REMOTE" ] && result PASS "a) HEAD==origin/s210/audit-master-plan" || result FAIL "a) HEAD!=origin/s210/audit-master-plan ($LOCAL vs $REMOTE)"

# b) porcelain vuoto salvo carve-out ARGOS
DIRTY=$(git status --porcelain | \
  grep -v '^.. data/recon' | \
  grep -v '^.. data/registry' | \
  grep -v '^.. data/pool_icp' | \
  grep -v '^.. incoming/' | \
  grep -v '^.. \.vos/' | \
  grep -v '^.. \.env\.test' || true)
[ -z "$DIRTY" ] && result PASS "b) porcelain-clean-salvo-carveout" || result FAIL "b) porcelain-dirty: $(echo "$DIRTY" | head -3)"

# c) STATE.md e PROTOCOLLO.md esistono e non vuoti
[ -s "docs/judge/STATE.md" ]      && result PASS "c) docs/judge/STATE.md esiste" || result FAIL "c) docs/judge/STATE.md mancante/vuoto"
[ -s "docs/judge/PROTOCOLLO.md" ] && result PASS "c) docs/judge/PROTOCOLLO.md esiste" || result FAIL "c) docs/judge/PROTOCOLLO.md mancante/vuoto"

# d) HEAD ATTESO in STATE.md è antenato di HEAD (o uguale)
ATTESO=$(grep 'HEAD ATTESO:' docs/judge/STATE.md 2>/dev/null | awk '{print $NF}' | head -1)
if git merge-base --is-ancestor "$ATTESO" HEAD 2>/dev/null; then
  result PASS "d) STATE.md HEAD ATTESO ($ATTESO) raggiungibile da HEAD"
else
  result FAIL "d) STATE.md HEAD ATTESO ($ATTESO) NON raggiungibile da HEAD"
fi

# e) .claude/NEXT_SESSION_PROMPT.md assente
[ ! -f ".claude/NEXT_SESSION_PROMPT.md" ] && result PASS "e) NEXT_SESSION_PROMPT.md assente" || result FAIL "e) NEXT_SESSION_PROMPT.md PRESENTE"

# f) HANDOFF_CURRENT.md NON tracciato in git (file su disco legittimo; criterio = tracking, non esistenza)
if git ls-files --error-unmatch HANDOFF_CURRENT.md 2>/dev/null; then
  result FAIL "f) HANDOFF_CURRENT.md TRACCIATO in git (deve essere gitignorato)"
else
  result PASS "f) HANDOFF_CURRENT.md non tracciato in git"
fi

# g) Nessun path PII tracciato
PII_TRACKED=$(git ls-files -- data/recon data/registry data/pool_icp 2>/dev/null | wc -l | tr -d ' ')
[ "$PII_TRACKED" -eq 0 ] && result PASS "g) zero path PII tracciati" || result FAIL "g) $PII_TRACKED path PII tracciati in git"

echo "---"
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
