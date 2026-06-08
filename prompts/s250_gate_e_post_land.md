# S250 — ARGOS · Gate E post-land (1b → #2 → #3)

> S249 CHIUSA VERDE: Gate E refinement LANDATO (commit `d60b6f3`, pushato su
> `s210/audit-master-plan`). selftest 26/26, `refresh.sh S249` senza FP.
> La condizione #1 del verdetto Claude AI ha scovato e chiuso un falso-negativo reale
> (`sed -i` su `.harness/state_guard.py` non protetto — filtro substring `s/`).

## Apri così
`bash state/refresh.sh S250` (stato anelli generato, mai hand-editare).
NON ri-litigare il design Gate E: è APPROVED da Claude AI S248. Solo i 3 item sotto.

### 1b — gate_e.py in PROTECTED_FILES di state_guard.py (~15 min)
Aggiungi `.harness/gate_e.py` ai PROTECTED_FILES di `.harness/state_guard.py`.
Editare state_guard.py è doppio-gated → serve `! python3 .harness/gate_e.py approve <slug>`
di Luke, oppure rilancio CC con `ARGOS_HARNESS_UNLOCK=1`. Poi selftest deve restare verde.

### #2 — coverage-check production-blocking outreach_real (il punto cieco vero)
Gate E intercetta il path-tool REALE con cui AMBRA invia? Il matcher è SHELL-scoped
(`classify_bash` su `:9191/send`, `send_message.js`, ...). Se AMBRA invia via MCP /
`python -c` / client diretto → BYPASSA → breaker decorativo. Verifica il callsite reale;
se bypassa, flip a REJECT su quel path.

### #3 — E2E anelli 6-7
Gate HITL dossier (app.py, fastapi → solo iMac/CI) + invio PDF su TEST_FOUNDER
393314928901 (MAI dealer reale). Vedi `feedback_e2e_full_test_founder_before_day1.md`.

## Pendenze minori
- MEMORY.md index: puntatore a `s249_gate_e_landed.md` NON aggiunto (gate overwrite_sot
  l'ha bloccato — vero-positivo). Il file memoria È scritto. Indicizzare con approve o unlock.
- DA DECIDERE: il gate blocca OGNI edit di MEMORY.md (protocollo fine-sessione). Scegliere:
  eccezione narrow per index-append OR documentare `ARGOS_HARNESS_UNLOCK=1` per le memorie.

## Riferimenti
Commit land `d60b6f3` · branch `s210/audit-master-plan` · memory `s249_gate_e_landed.md`
Gate E `.harness/gate_e.py` (26/26) · state_guard `.harness/state_guard.py`
