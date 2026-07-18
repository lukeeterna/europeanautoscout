# S198 — AMBRA stress + E2E Luke fisico + matrix Day 1 Stile Car

> **Sblocco**: S197 STEP 6.1+6.2 chiusi VERDE post 2 bug forward-fixed (vedi memory `s197_deploy_imac_verde_post_2bug_strutturali.md`). Deploy iMac `releases/20260527_083951` operativo. 4/4 procs online.
>
> **Deadline Day 1 Stile Car**: 2026-06-03 = **7gg residui**.

---

## Stato S197 closed (commit S197-deploy-fix da fare PRIMA di partire S198)

| Asset | Status |
|---|---|
| `wa-intelligence/ecosystem.config.js` | dirty (fix interpreter python3.13) |
| `prompts/s197_*` + `prompts/s198_*` | dirty (handoff + nuovo) |
| Memory `s197_deploy_imac_verde_post_2bug_strutturali.md` | written |
| pm2 iMac 4/4 online | ✅ |
| dashboard :8080 / → 303 | ✅ |
| wa-daemon :9191/status → 200 | ✅ |
| runtime test 5/5 PASS | ✅ |

**STEP 0 obbligatorio S198**: commit S197 fix prima di muovere su STEP 7. Comando suggerito:
```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git add wa-intelligence/ecosystem.config.js prompts/s198_ambra_e2e_decision_day1.md
git commit -m "feat(S197-deploy-fix): ecosystem.config.js interpreter python3.13 + handoff S198"
git push
```

NON `git add -A` perché working tree contiene D/ M residui di altre sessioni fuori scope S197.

---

## STEP 7 — AMBRA stress test (5 scenari response-analyzer reactive)

Pre-existing: `wa-intelligence/response-analyzer.py` su TEST_FOUNDER **39<TEST_FOUNDER_NUM>** (FLUXION SIM, autorizzato ARGOS).

### Scenari da inviare via curl/dashboard verso AMBRA

| # | Intent | Messaggio simulato | Atteso AMBRA |
|---|---|---|---|
| 1 | VEHICLE_REQUEST | "cerco BMW X3 2021 max €18.000" | broker reply "ci sto lavorando, le scrivo entro 24-48h" |
| 2 | PRICE_NEGOTIATION | "posso prendere a 17?" su contratto attivo | ResponseValidator hallucination check (no veicolo inventato) |
| 3 | CONTRACT_REQUEST | "ok mando bonifico" post DOSSIER_SENT | handler `create_contract_for_interest` → DRAFT contract |
| 4 | OPT_OUT | "non mi scrivere più" | opt_out flag DB + stop sequence |
| 5 | AMBIGUOUS | "rispondo domani" | HITL queue PENDING (no auto-send) |

### Esecuzione

Vedi script pre-esistente in `tools/test_ambra_5scenarios.py` (se assente, creare con loop 5 POST a `wa-intelligence/response-analyzer.py` via subprocess o direct call).

### Gate STEP 7
- 5/5 reply LLM_MULTI `approved=1` su `replies` table
- 0 hallucination flag (target_lexicon PASS, ban argos PASS, no veicolo inventato)
- Scenario 4 (OPT_OUT) → `dealers.opt_out_flag=1` + sequence stop
- Scenario 5 (AMBIGUOUS) → row PENDING in HITL queue

Se 4/5 → handoff S199 con scenario specifico fail. NO "verde sostanzialmente".

---

## STEP 8 — E2E TEST_FOUNDER fisico Luke (9 step)

Pre-existing: `prompts/s190_e2e_physical_close.md`. Riusabile post-S196/S197 (HITL gate immutato).

### Step bloccanti Luke fisico
| # | Azione | Tool |
|---|---|---|
| 4 | approve via dashboard:8080 (login + click APPROVE su TEST_FOUNDER pending) | browser MacBook → tunnel iMac o ssh -L |
| 6 | mark-paid via form dashboard:8080 | browser |
| 8 | verifica WA inbound TEST_FOUNDER su sim FLUXION fisica | smartphone Luke |

### Gate STEP 8
- 9/9 step PASS
- Contract test PAID in `~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite` (o DB autorevole post-S193)
- `audit_log` completo: `REPLY_APPROVED` + `BRIDGE_INSERTED` per la pending approvata
- WA delivery confermato OUTBOUND `wa_sent=true`

---

## STEP 9 — Matrix decisione Day 1 Stile Car 2026-06-03

### Input gate

| Componente | Stato | Bloccante? |
|---|---|---|
| AMBRA 5/5 PASS (STEP 7) | TBD | SÌ |
| E2E Luke 9/9 PASS (STEP 8) | TBD | SÌ |
| Sanitizer S183-bis closure VERDE | VERDE pre-existing | SÌ |
| WA daemon online + quota disponibile | VERDE (verificato S197) | SÌ |
| Dossier sanitizer reale production-verified | VERDE post-S191/S193 | SÌ |
| HITL gate dashboard funzionante | VERDE post-S196 + S197 fix | SÌ |
| Materiale Day 1 Stile Car (foto, dossier specifico) | Verifica `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` | SÌ |

### Decision tree

- **TUTTI verdi** → GO Stile Car Day 1 **2026-06-03** (5gg buffer pre-deadline, se chiusura S198 entro 28-29 maggio)
- **1+ giallo** → handoff S199 con preconditions Day 1 specifiche
- **1+ rosso** → STOP Day 1, riprogrammazione + nuovo handoff diagnosi

---

## Anti-pattern da NON ripetere in S198

1. **Loop gate Claude AI esterno** (CLAUDE.md S197): STEP 7 o 8 fallisce → diagnosi via log/SSH, NON nuovo bundle V5 + claude.ai V5.
2. **PARTIAL/ARANCIONE**: ogni step gate binario. STEP 7 4/5 = ROSSO, handoff S199.
3. **TEST_FOUNDER = Luke fisico reale** (memory `feedback_test_founder_means_real_interactive.md`): NON simulare risposte via subprocess args o admin API dummy. Aspettare Luke risponda fisicamente sulla SIM FLUXION <TEST_FOUNDER_NUM>.
4. **Cross-platform false-positive S160/S197**: ogni nuovo file Python deploiato iMac → pre-flight `ssh imac "/usr/local/bin/python3.13 -c 'import ast; ast.parse(open(file).read())'"` PRIMA del rsync. Aggiungere a sync.sh in BACKLOG #S197-4.

---

## BACKLOG cumulato S197+S198 (non bloccante Day 1)

- #S197-1 logger `argos.dashboard` no handler stdout (STARTUP log invisibile)
- #S197-2 path hardcoded `/usr/local/bin/python3.13` fragile → env var `PYTHON313_BIN`
- #S197-3 pre-flight ABI Node automatico (evitare rebuild manuale post-deploy)
- #S197-4 cross-platform Python syntax check pre-rsync (mypy py-version 3.9 o ssh ast.parse)
- #S196-1 audit-loss MED-2 senza rate-limit (noise risk 60gg)
- #S196-2 schema check solo "tabella esiste", non verifica colonne
- #S196-3 fixture S196 stale se schema iMac drifta silently → auto-dump schema

---

## Risorse

- pm2 iMac status: `ssh gianlucadistasi@192.168.1.2 "pm2 jlist | python3 -c 'import json,sys; [print(p[\"name\"], p[\"pm2_env\"][\"status\"]) for p in json.load(sys.stdin)]'"`
- dashboard log: `ssh gianlucadistasi@192.168.1.2 "tail -50 /tmp/argos-dashboard-out.log"`
- runtime test locale: `python3 tools/tests/test_approve_reply_runtime.py`
- TEST_FOUNDER override autorizzato: `feedback_test_founder_<TEST_FOUNDER_NUM>_argos_authorized.md`
- Memory S197 dettaglio: `s197_deploy_imac_verde_post_2bug_strutturali.md`

## Day 1 Stile Car deadline tracker
- 2026-06-03 = T-7gg al momento del handoff S198 (2026-05-27)
- T-5gg buffer richiesto pre-deadline → chiusura S198 entro **2026-05-29**
- Domenica 2026-05-31 OFF (memory `user_luke_finanzia_canone_lavapiatti_domenica.md`)
- Finestra utile: 27-28-29 maggio (3 giorni lavorativi)
