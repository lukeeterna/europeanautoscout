# S199 — Track A classifier fix Day 1 Stile Car + Opzione 3 critica architetturale (post Claude AI feedback 2026-05-27)

> **Apertura sessione**: leggi PRIMA `memory/s198_step7_rosso_3_5_classifier_gaps.md` + `memory/s198_closure_handoff_s199.md` + `prompts/s199_claude_ai_output_20260527.md` (risposta critica peer Claude AI web).
>
> **Convergenza esterna**: Claude AI ha confermato 3/3 le mie autocritiche S198 closure (DATI inesistenti vertical, over-engineering N=1, conflitto priorità). Design full 8000 parole SCARTATO data-supported.
>
> **Deadline Day 1 Stile Car**: 2026-06-03 = T-6gg al S199 start (2026-05-28). Finestra utile: 28-29 maggio (2gg lavorativi, domenica 31 OFF).

---

## STEP 0 — Pre-flight + decisione scope (10 min)

1. Verifica working tree:
   ```bash
   cd /Users/macbook/Documents/combaretrovamiauto-enterprise && git status -s
   ```
   Asset S198 NON committati:
   - `tools/test_ambra_5scenarios.py` (NEW)
   - `prompts/s199_claude_ai_design_autonomous_sales_agent.md` (NEW)
   - `prompts/s199_resume_classifier_fix_and_claude_ai_eval.md` (NEW, questo file)
   - `prompts/s199_claude_ai_output_20260527.md` (NEW, risposta peer Claude AI)

2. **Domanda scope Luke STEP 0**: commit ora o fine S199?
   Suggerito: `feat(S198-S199-bootstrap): AMBRA stress ROSSO + prompt design + peer feedback Claude AI`

3. **Domanda scope Luke STEP 0-bis** (post lettura Claude AI output):
   - **Opzione A** (raccomandata mia): Track A pieno + Opzione 3 critica 3/12 feature post-Track A se context ≤55%
   - **Opzione B**: Solo Track A, no Opzione 3 (focus chirurgico Stile Car)
   - **Opzione C**: Opzione 2 design 2500 parole onesto SOSPENDE Track A (sconsigliato T-6gg)

4. pm2 iMac health-check:
   ```bash
   ssh gianlucadistasi@192.168.1.2 "pm2 jlist | python3 -c 'import json,sys; [print(p[\"name\"], p[\"pm2_env\"][\"status\"]) for p in json.load(sys.stdin)]'"
   ```
   Atteso 4/4 online.

---

## TRACK A — Classifier fix P1+P2+P3 + re-test 5/5 + E2E Luke fisico

### P1 BLOCKER — CONTRACT_REQUEST_PATTERNS (`wa-intelligence/response-analyzer.py:233-238`)

Aggiungere 2 regex:
```python
CONTRACT_REQUEST_PATTERNS = [
    # ... 4 pattern esistenti ...
    r'\b(ok|va\s+bene|perfetto|d[\'\u2019]accordo|certo)\b.{0,40}\b(bonifico|pagamento|pago|trasferisco|procediamo)\b',
    r'\b(mando|invio|faccio)\b.{0,20}\b(bonifico|pagamento|trasferimento)\b',
]
```

Edge case da coprire (validato S198 validator):
- "ok mando bonifico" → CONTRACT_REQUEST
- "ok va bene procediamo" → CONTRACT_REQUEST
- "mando il bonifico" → CONTRACT_REQUEST

### P2 BLOCKER — PATTERNS['NEGATIVE']['exact'] (`wa-intelligence/response-analyzer.py:1164-1171`)

Aggiungere 6 entry:
```python
'non mi scrivere', 'non mi scrivere più',
'non mi contattare', 'non mi contattare più',
'non mi chiamare', 'non mi chiamare più',
```

Edge case:
- "non mi scrivere più" → NEGATIVE
- "non mi contattare più" → NEGATIVE

### P3 STESSO COMMIT — handler NEGATIVE opt_out persistence (`wa-intelligence/response-analyzer.py:2114-2123`)

```python
if cls_type == 'NEGATIVE':
    from db_utils import get_connection
    con = get_connection(args.db_path)
    con.execute("""
        UPDATE conversations
        SET current_step = 'CLOSED_NO',
            opt_out = 1,
            opt_out_at = datetime('now'),
            opt_out_source = 'auto_negative_classifier',
            opt_out_raw_message = ?,
            analyzed_at = datetime('now')
        WHERE dealer_id = ?
    """, [args.msg_body[:500], args.dealer_id])
    con.commit()
    con.close()
    # ... audit_log existing ...
```

### Esecuzione Track A (delega aggressiva REGOLA #0)

1. **code-reviewer** sui 3 patch (NO full file scan)
2. **implementer** applica P1+P2+P3 (NO scope creep, NO refactor)
3. **Re-run**:
   ```bash
   python3 tools/test_ambra_5scenarios.py
   ```
   **Gate VERDE Track A**: 5/5 PASS.
   **Gate ROSSO**: ≥1 FAIL → diagnosi root cause, iterazione (NO handoff S200 ancora).

4. **STEP 4 E2E TEST_FOUNDER Luke fisico** (post-Track A VERDE):
   - Riferimento: `prompts/s190_e2e_physical_close.md` (9 step)
   - Bloccanti Luke fisico:
     - Step 4: approve dashboard:8080 (browser + ssh -L 8080:localhost:8080 imac)
     - Step 6: mark-paid form
     - Step 8: verifica WA inbound TEST_FOUNDER 39<TEST_FOUNDER_NUM> SIM FLUXION
   - Gate: 9/9 PASS + contract test PAID in `~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite`

5. **STEP 5 matrix decisione Day 1 Stile Car** (post-STEP 4 VERDE):
   - Riferimento: `prompts/s198_ambra_e2e_decision_day1.md` STEP 9
   - Input gate:
     - AMBRA 5/5 ✓ (Track A STEP 3)
     - E2E Luke 9/9 ✓ (STEP 4)
     - Sanitizer S183-bis VERDE pre-existing
     - WA daemon VERDE post-S197
     - HITL gate VERDE post-S196+S197
     - Materiale Day 1 (`.planning/launch_luca_ferretti/DAY1_STILE_CAR.md`) → VERIFY
   - Decision: tutti verdi → GO Stile Car 2026-06-03; 1+ giallo → handoff S200 con preconditions; 1+ rosso → STOP riprogrammazione

---

## OPZIONE 3 (post-Track A VERDE, SE context ≤55%)

### Scope micro (~30 min)

Re-invocare Claude AI web (stessa chat) con prompt:

```
Procedi con Opzione 3 — solo critica architetturale del design AMBRA-successore.
Per ogni delle 12 feature (A→L) del mio prompt originale, classifica:
- VALE ORA (giustificata da volume <5 dealer chiusi) → max 3 feature
- VALE A 30-60-90gg (specifica trigger volume)
- NON VALE MAI (motivazione)

Per le ≤3 feature VALE ORA: design tecnico essenziale (~600 parole tot), agnostic da volume futuro.
Per le altre: 1 riga ciascuna, no design.

Niente sezione DATI. Niente tabelle benchmark. Solo architettura + decisione GO/DEFER/NO per feature.
```

### Output atteso Opzione 3
File `prompts/s199_claude_ai_opzione3_critica.md` con:
- 3 feature GO motivate con architettura tecnica essenziale
- 9 feature DEFER/NO con motivazione singola riga
- Ipotesi peer Claude AI da validare: A (proattività) + B (persona-detection) + K (trust-calibration)

### Quando attivare Opzione 3
- SOLO se Track A VERDE chiuso entro context ≤55%
- SOLO se Luke autorizza esplicitamente (decisione scope)
- Altrimenti → handoff S200 con Opzione 3 pending

---

## Vincoli S199 invariati

- Italiano verso Luke
- Mai PARTIAL/ARANCIONE (gate binario)
- Una raccomandazione singola motivata con DATI (vincolo #3)
- Mai "hai ragione" diplomatico (vincolo #9): accordo motivato con DATI o disaccordo motivato con DATI
- Zero costi
- HITL gate immutato per scelte irreversibili
- TEST_FOUNDER 39<TEST_FOUNDER_NUM> autorizzato (SIM FLUXION Luke)
- Domenica 2026-05-31 OFF
- WebSearch prima di decisioni stack (anti-S159)
- Context >50% durante Track A → STOP Opzione 3 → handoff S200
- REGOLA #0 delegation-first: code-reviewer + implementer + validator obbligatori Track A

---

## Risorse

- Memory ROSSO STEP 7: `memory/s198_step7_rosso_3_5_classifier_gaps.md`
- Memory closure S198: `memory/s198_closure_handoff_s199.md`
- Output peer Claude AI: `prompts/s199_claude_ai_output_20260527.md`
- Prompt design Claude AI (origine): `prompts/s199_claude_ai_design_autonomous_sales_agent.md`
- Test script: `tools/test_ambra_5scenarios.py`
- E2E Luke ref: `prompts/s190_e2e_physical_close.md`
- Matrix Day 1 ref: `prompts/s198_ambra_e2e_decision_day1.md` STEP 9
- DECISIONS founder ARGOS: `~/venture-os/wiki/projects/ARGOS/DECISIONS.md`
