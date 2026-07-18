# S197 — Deploy iMac + AMBRA stress + E2E + decisione Day 1 Stile Car

> **Sblocco**: gate S196 VERDE post-preconditions. External score 7.4/10 (claude.ai web) → GO_WITH_PRECONDITIONS. 4 preconditions incorporate in commit S196-preconditions (vedi sotto). Day 1 Stile Car deadline 2026-06-03 (8gg residui).

---

## Stato S196 closed (commit precedente)

| Fix | Self | External | Status |
|-----|------|----------|--------|
| P1 runtime test | PASS | **PASS** | 5/5 fixture schema reale iMac |
| P2 signature dict | PASS | **PASS** | 7 error codes strutturati |
| P3 BRIDGE_DB_PATH | PASS | **PARTIAL** | Risolto via precondition-1 (schema check) |
| P4 sentinel const | PASS | **PASS** | 1 match grep (solo definizione) |

**4 preconditions incorporate**:
1. `app.py` startup schema check `SELECT FROM sqlite_master WHERE name='bridge_outbound'` + busy_timeout=3000 (code-review LOW-1)
2. `db.py` audit-loss reclassification MED-2 → log ERROR esplicito + bridge inserted resta valido
3. STEP 6.2 lsof :8080 + pm2 delete prima del reload (procedurale qui sotto)
4. `test_approve_reply_runtime.py` docstring "4/4 PASS" → "5/5 PASS"

Runtime test 5/5 PASS confermato post-preconditions. Code-reviewer PASS (2 LOW, 1 fixato inline, 1 no-op).

---

## STEP 6.1 — Deploy iMac (rsync atomico + symlink swap)

```bash
# Working dir locale
cd /Users/macbook/Documents/combaretrovamiauto-enterprise

# Pre-flight locale: runtime test deve passare PRIMA del deploy
python3 tools/tests/test_approve_reply_runtime.py | tail -3
# Atteso: "RUNTIME TEST RESULT: 5/5 PASS"

# Deploy
bash deploy/sync.sh
# Atteso: release dir `releases/YYYYMMDD_HHMMSS` su iMac + symlink `current` aggiornato
```

**Gate**: deploy log conferma symlink swap atomico OK. Se rsync fallisce → STOP, no procedere.

---

## STEP 6.2 — pm2 reload con safety check doppio listener

**Precondition 3 revisore esterno**: argos-dashboard era avviato manualmente fuori ecosystem (root cause silent-failure pre-S196). Se quel processo è ancora vivo, pm2 reload crea SECONDO listener su :8080 → due processi competono sulla porta → bug P3 può ripresentarsi mascherato.

```bash
ssh imac '
  # 1. Verifica stato porta PRIMA del reload
  echo "=== Pre-reload state ==="
  lsof -i :8080 2>/dev/null || echo "porta 8080 libera"

  # 2. Kill esplicito eventuale dashboard manuale (out-of-ecosystem)
  #    pm2 delete è no-op se non esiste (2>/dev/null)
  pm2 delete argos-dashboard 2>/dev/null || true

  # 3. Kill processi python su :8080 NON gestiti da pm2 (manuali zombie)
  PIDS=$(lsof -ti :8080 2>/dev/null)
  if [ -n "$PIDS" ]; then
    echo "WARNING: PID residui su :8080: $PIDS — kill"
    echo "$PIDS" | xargs kill -TERM 2>/dev/null || true
    sleep 2
  fi

  # 4. Verifica porta libera
  echo "=== Pre-reload state (post-cleanup) ==="
  lsof -i :8080 2>/dev/null || echo "porta 8080 libera ✓"

  # 5. pm2 reload ecosystem (carica nuovo argos-dashboard con SHARED_ENV)
  cd ~/Documents/app-antigravity-auto/wa-intelligence
  pm2 reload ecosystem.config.js --update-env

  # 6. Verifica post-reload
  sleep 5
  pm2 jlist | python3 -c "
import json, sys
data = json.load(sys.stdin)
for proc in data:
    name = proc[\"name\"]
    status = proc[\"pm2_env\"][\"status\"]
    restart = proc[\"pm2_env\"][\"restart_time\"]
    print(f\"{name}: {status} (restarts={restart})\")
"
  echo "=== Post-reload state ==="
  lsof -i :8080 2>/dev/null

  # 7. Verifica startup log dashboard (cerca riga BRIDGE_DB_PATH OK)
  tail -30 /tmp/argos-dashboard-out.log | grep -E "(STARTUP|BRIDGE_DB_PATH|FATAL)" | tail -5
'
```

**Gate**:
- `argos-dashboard: online` in pm2 jlist
- `BRIDGE_DB_PATH OK: ... (schema bridge_outbound verified)` nei log
- UN solo PID su :8080
- Se log mostra `[STARTUP][FATAL]` → STOP, fix env in ecosystem.config.js + re-deploy

---

## STEP 6.3 — Smoke E2E approve_reply via dashboard live

```bash
# Da MacBook, simula approve via API dashboard
ssh imac 'curl -s -X POST http://localhost:8080/api/actions/approve-reply \
  -H "Content-Type: application/json" \
  -H "Cookie: argos_session=$(cat ~/.argos_dashboard_session 2>/dev/null)" \
  -d "{\"reply_id\":\"<reply_id_test_da_pending>\"}" | python3 -m json.tool'
```

Atteso: `{"ok": true, "approved": true, "bridge_queued": true, "error": null}`.

**Se in produzione non c'è una pending_reply test** → skip STEP 6.3, gate è il runtime test locale + dashboard log clean.

---

## STEP 7 — AMBRA stress test (5 scenari response-analyzer reactive)

Pre-existing handoff: `prompts/s194_deploy_ambra_e2e.md` STEP 3-4. Re-eseguibili identici post-S196.

5 scenari da `wa-intelligence/response-analyzer.py` su TEST_FOUNDER 39<TEST_FOUNDER_NUM>:
1. VEHICLE_REQUEST esplicito (BMW X3 2021 €18k) → AMBRA broker reply
2. PRICE_NEGOTIATION ("posso prendere a 17?") → ResponseValidator hallucination check
3. CONTRACT_REQUEST ("ok mando bonifico") → handler create_contract_for_interest
4. OPT_OUT ("non mi scrivere più") → opt_out flag + stop sequence
5. AMBIGUOUS ("rispondo domani") → HITL queue PENDING

**Gate**: 5/5 reply LLM_MULTI approved (no hallucination, no ban argos, target_lexicon PASS).

---

## STEP 8 — E2E TEST_FOUNDER fisico Luke (9 step)

Pre-existing: `prompts/s190_e2e_physical_close.md` + S190 closure verde HITL committed 7002a42.
Re-eseguibile post-S196 dato che HITL gate immutato.

**Step bloccanti Luke fisico**:
- Step 4 approve via dashboard:8080 (login + click approve su TEST_FOUNDER pending)
- Step 6 mark-paid via dashboard form
- Step 8 verifica WA inbound delivery TEST_FOUNDER su MacBook

**Gate**: 9/9 step PASS + contract test PAID + audit_log completo (`REPLY_APPROVED` + `BRIDGE_INSERTED` per la pending approvata).

---

## STEP 9 — Matrix decisione Day 1 Stile Car 2026-06-03

Input:
- STEP 7 AMBRA 5/5 PASS
- STEP 8 E2E 9/9 PASS + Luke fisico OK
- Sanitizer S183-bis closure VERDE (pre-existing)
- WA daemon online + sent quota disponibile
- Dossier sanitizer reale verificato post-S191/S193

**Decision tree**:
- TUTTI verdi → GO Stile Car Day 1 2026-06-03 (5gg buffer pre-deadline)
- 1+ giallo → handoff S198 con preconditions Day 1
- 1+ rosso → STOP Day 1, riprogrammazione

---

## BACKLOG cumulato S196 (da non riaprire qui)

- #S196-1 MED-2 audit-loss ora ha log ERROR ma NON ha rate-limit (60gg risk noise)
- #S196-2 schema check su `bridge_outbound` non verifica colonne (es. body NOT NULL rimosso) — sufficiente per "tabella esiste"
- #S196-3 auto-dump schema iMac → fixture S196 (critica strutturale CTO #3 — fixture stale se schema drifta silently)
- code-review LOW-2 annotation audit-flow safety (no-op, già safe)

Nessuno bloccante Day 1.

---

## Anti-pattern da NON ripetere in S197

- **S194/S195 inflation -0.8/-0.9**: gate primario era py_compile + code-reviewer LLM (segnali deboli). S196 fix = runtime test schema reale. **NON tornare** a "scrivo bundle V4 + re-validation claude.ai V4" se STEP 6 fallisce — è loop di gate. Se STEP 6 fallisce, è un blocker fisico (env iMac, schema drift, pm2 zombie) da diagnosticare con SSH + log, non con nuovo gate esterno.
- **Single-operator assumption**: critica CTO #1 S196 → se 2 operatori dashboard, race window UPDATE/INSERT. In S197 deploy reale è ancora 1 operatore (Luke). BACKLOG futuro multi-op.
- **PARTIAL/ARANCIONE**: CLAUDE.md #6. Se STEP 7 AMBRA 4/5 PASS → handoff S198 strutturato con scenario specifico fail, NON "diciamo verde sostanzialmente".
