# S196 — Fix P1-P4 silent-failure + sentinel + runtime test + re-validation

> Handoff post-S195 gate fail. S195 STEP 0.5 V2 NO_GO 5.5/10 (< 7.0). Deploy iMac correttamente bloccato. Revisore esterno diff-grounded ha identificato 5 red flag mai visti da CTO interno + code-reviewer agent. S196 risolve P1-P4 strutturalmente + runtime test reale prima di self-score.

---

## Contesto S195 chiuso

**Verdict revisore esterno claude.ai web** (bundle V2 INLINE 444 righe):
- `external_score = 5.5/10`
- `go_no_go = NO_GO`
- 3/3 fix S193 = PARTIAL
- 5 red flag specifici diff-grounded (vedi `memory/s195_gate_fail_handoff_s196.md`)

**Pattern strutturale 2 gate consecutivi**:
- S194: self 7.2 / external 6.3 (delta -0.9)
- S195: self 6.3 / external 5.5 (delta -0.8)
- Root cause: validation interna con segnali deboli (py_compile + code-reviewer LLM)
- **Mitigazione S196**: runtime test reale = unica gate per self-score

---

## STEP 0 — Verifica apertura (5 min)

```bash
git log -3 --oneline
# Atteso top: commit S195 close

ssh gianlucadistasi@192.168.1.2 'readlink ~/Documents/app-antigravity-auto/current'
# Atteso INVARIATO: .../releases/20260525_211041

curl -s --max-time 5 http://192.168.1.2:9191/status | head -5
# Atteso: connected, 1/20

cat state/s195_validation_log.jsonl | tail -2
# Atteso: verdict 5.5/10 NO_GO + pattern_recognition
```

---

## STEP 1 — P4 Costante SENTINEL_SKIP_PROMO modulo-level (15 min)

**Issue**: 4 callsite hardcoded `"__SKIP_PROMO__"` (verificato grep S195 close):
- `src/cove/image_sanitizer.py:959` (return)
- `src/cove/image_sanitizer.py:1068` (check 1)
- `src/cove/image_sanitizer.py:1070` (check 2)
- `src/cove/image_sanitizer.py:1168` (check CLI)
- `tools/scripts/pdf_generator_enterprise.py:1653` (subprocess wrapper)

**Fix**: aggiungere costante top-level `image_sanitizer.py`:
```python
# Modulo-level sentinel — distinguishes intentional skip (promo-slide)
# from crash (None). Import this rather than hardcoding the string.
SENTINEL_SKIP_PROMO = "__SKIP_PROMO__"
```

Sostituire i 4 hardcoded con `SENTINEL_SKIP_PROMO`. In `pdf_generator_enterprise.py` aggiungere `from src.cove.image_sanitizer import SENTINEL_SKIP_PROMO` (verificare path import esistente).

**Gate STEP 1**: `grep -rn '"__SKIP_PROMO__"' src/ tools/` ritorna 0 match (solo costante).

---

## STEP 2 — P2 Fix semantica return True silent-failure (30 min)

**Issue 2a**: `wa-intelligence/dashboard/db.py:~260` except OperationalError → `con.commit() + return True` senza bridge_outbound INSERT. Reply approvata UI ma daemon non riceve.

**Issue 2b**: `wa-intelligence/dashboard/db.py:~290` `elif not bridge_db_path` → log warning + return True. Stessa classe.

**Fix scelta singola raccomandata** (vincolo #3 no liste A/B/C/D):
Cambiare signature `approve_reply` da `bool` a `dict`:
```python
def approve_reply(reply_id: str) -> dict:
    """
    Returns:
        {"approved": bool, "bridge_queued": bool, "error": Optional[str]}

    Caller (app.py:690) interpreta:
    - approved=True + bridge_queued=True → "✅ Inviato a daemon"
    - approved=True + bridge_queued=False → "⚠️ Approvato ma daemon NON in coda (verifica BRIDGE_DB_PATH)"
    - approved=False → "❌ Reply non trovata o già processata"
    """
```

Aggiornare `app.py:690 action_approve_reply` per propagare lo stato + alert Telegram se `bridge_queued=False`.

**Trade-off motivato**: cambia signature pubblica db.py ma path felice S193-fix HIGH-2 dipende da env non verificata → degradazione silenziosa è bug peggiore di breaking change interno (un solo callsite app.py:690).

**Gate STEP 2**: pytest unitario nuovo `test_approve_reply_returns_dict` con 3 scenari (happy/schema-drift/bridge-missing).

---

## STEP 3 — P3 BRIDGE_DB_PATH precondition hard (10 min)

**Issue**: env var marcata PENDING in S193 close-out. Path felice fix HIGH-2 dipende da essa.

**Fix**: pre-flight check in `app.py` startup (FastAPI lifespan event):
```python
@app.on_event("startup")
async def verify_bridge_db_path():
    bp = os.environ.get('BRIDGE_DB_PATH', '')
    if not bp or not os.path.exists(bp):
        log.error(f"[FATAL] BRIDGE_DB_PATH missing or invalid: '{bp}'. Reply approval will degrade.")
        # NON crashare — log + alert Telegram (operatore decide)
        send_telegram_alert(f"BRIDGE_DB_PATH non set su iMac: replies HITL non andranno in coda daemon")
```

Verificare ecosystem.config.js iMac che setti `BRIDGE_DB_PATH=/Users/gianlucadistasi/Documents/app-antigravity-auto/comm-broker/bridge.sqlite` per processo argos-dashboard.

**Gate STEP 3**: SSH iMac `pm2 jlist | grep -A2 BRIDGE_DB_PATH` ritorna path valido.

---

## STEP 4 — P1 Runtime functional test approve_reply (45 min, CORE)

**Issue**: nessun test runtime con DB reale. Tutti i fix S193 validati solo py_compile + code-reviewer LLM = 2 segnali deboli.

**Fix**: script test runtime `tools/tests/test_approve_reply_runtime.py` che:

1. **Setup**: crea fixture sqlite temporanea con schema reale dealer_network.sqlite (conversations + pending_replies + audit_log) + bridge.sqlite (bridge_outbound)
2. **Scenario A — happy path**: INSERT pending_reply con dealer_id valido → call `approve_reply()` → SELECT bridge_outbound conferma riga inserita con phone, body, deal_id corretti
3. **Scenario B — schema drift**: rinomina conversations.phone_number → conversations.phone_num_old → call `approve_reply()` → return dict con `bridge_queued=False`, NO crash
4. **Scenario C — BRIDGE_DB_PATH missing**: unset env → call `approve_reply()` → return dict con `bridge_queued=False`, log warning
5. **Scenario D — duplicate**: INSERT reply, approve 2 volte → seconda chiamata `approved=False` (UPDATE rowcount=0)

**Output atteso**: 4/4 PASS con SELECT real DB su bridge_outbound mostrando riga effettiva.

**Gate STEP 4**: `python3 tools/tests/test_approve_reply_runtime.py` ritorna 4/4 PASS. NO mock, NO stub. DB SQLite reali (fixture temporanee).

---

## STEP 5 — Code-reviewer + commit + re-validation bundle V3 (30 min)

5.1 Delega `code-reviewer` agent su file modificati (image_sanitizer.py, db.py, app.py, pdf_generator_enterprise.py, test runtime). NO go-ahead solo su questo.

5.2 Commit single atomic `feat(S196): silent-failure fix + sentinel const + runtime test + bridge env hard`

5.3 Genera bundle V3 `/tmp/s196_QUALITY_VALIDATION_PROMPT_v3.md` con INLINE:
   - Diff S196 completo
   - Output `test_approve_reply_runtime.py` reale (NON py_compile)
   - Auto-valutazione CTO con caveat "py_compile + code-reviewer NON sono validation gate, runtime test PASS lo è"

5.4 AskUserQuestion: paste bundle V3 su claude.ai web. Gate `external_score ≥ 7.0/10` per sblocco STEP 6.

---

## STEP 6 — Deploy iMac + AMBRA stress + E2E + Day 1 decision (post-validation)

Solo se STEP 5 PASS gate ≥7.0. Sequenza identica a S195 STEP 1-3-4 (deploy + 5 scenari AMBRA + 9-step E2E + matrix Day 1).

---

## Gate cumulato S196

| Step | Gate |
|------|------|
| 1 | grep `"__SKIP_PROMO__"` 0 match in src/ tools/ |
| 2 | pytest test_approve_reply_returns_dict 3/3 PASS |
| 3 | SSH iMac BRIDGE_DB_PATH set in PM2 env |
| 4 | runtime test 4/4 PASS con SELECT bridge_outbound reale |
| 5 | external_score ≥ 7.0/10 + GO/GO_WITH_PRECONDITIONS |
| 6 | deploy + 5/5 AMBRA + 9/9 E2E → GO Day 1 Stile Car |

---

## Asset pronti per S196

- `state/s195_validation_log.jsonl` (verdict 5.5/10 + pattern recognition)
- `memory/s195_gate_fail_handoff_s196.md` (audit close + critica 4 punti)
- `/tmp/s195_QUALITY_VALIDATION_PROMPT_v2.md` (archiviare in `prompts/archived/` come reference)

---

## Vincoli ricordati

- CLAUDE.md #0 delegation-first: code-reviewer agent obbligatorio STEP 5
- CLAUDE.md #1 verifica fattuale: runtime test = unico gate self-score (no py_compile, no LLM-approva-LLM)
- CLAUDE.md #3 no liste A/B/C/D: STEP 2 single fix raccomandato (signature dict) con trade-off motivato
- CLAUDE.md #4 critica strutturale 4 punti: applicata in handoff S195
- CLAUDE.md #6 no PARTIAL/ARANCIONE: S195 chiusa VERDE su gate detection corretta, S196 handoff strutturato
- CLAUDE.md #7 ctx >60% closure: monitorare /context durante STEP 4 (runtime test puo' generare output verboso)
- CLAUDE.md #9 no "hai ragione" diplomatico: revisore S195 ha trovato 5 red flag reali, accepted con evidence
- CLAUDE.md #11 pattern recognition: 2 gate consecutivi self-assessment inflation -0.8/-0.9pt → mitigation runtime test
- `feedback_smoke_test_not_uat_gate.md`: applicato a runtime test (non smoke 3/3 PASS auto)
- `feedback_test_founder_means_real_interactive.md`: STEP 6 Luke fisico, non simulazione

---

## Deadline Day 1 Stile Car 2026-06-03

Apertura S196 atteso 2026-05-27. Mancano **7 giorni** (incl. domenica 31 OFF).
Slot realistici: S196 mer 27 (fix P1-P4 + runtime test), S197 gio 28 (re-validation + deploy), S198 ven 29 (AMBRA stress 5 scenari), S199 sab 30 (E2E 9-step + decisione), S200 lun 1 (buffer), S201 mar 2 (buffer), S202 mer 3 (Day 1 send dealer reale).
**Margine 2 slot buffer**. Se S196 sfora, escalation a Luke con scenario re-pianificazione Stile Car.

---

## Riferimenti rapidi

- WA daemon: `ssh imac "curl -s localhost:9191/status"`
- Dashboard: `http://192.168.1.2:8080/replies`
- DB autoritativo: `~/Documents/app-antigravity-auto/dealer_network.sqlite` (iMac)
- bridge_outbound: `~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite` (iMac)
- Sign endpoint: `https://argos-automotive.pages.dev/sign/<token>`
