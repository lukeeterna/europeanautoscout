# S249 — ARGOS · LAND Gate E (verdetto Claude AI = APPROVE-appena-confermato)

Piano completo: `prompts/s249_gate_e_land.md`. Verdetto S248 ricevuto: **APPROVE** del design,
land condizionato a 3 punti (minuti). Stato: **#2 e #3 DONE**, **#1 RESIDUO** (sotto).

## #1 RESIDUO pre-land (1 edit + 1 run, poi land) — l'unico rischio vero = falsi NEGATIVI
Aggiungere a `cli_selftest()` di `.harness/gate_e.py.new` i TP-SoT espliciti vs matcher NUOVO
e ri-eseguire `python3 .harness/gate_e.py.new selftest` (atteso PASS, deve includerli):
```
({"tool_name":"Write","tool_input":{"file_path":"CLAUDE.md","content":"x"}}, "deny"),
({"tool_name":"Write","tool_input":{"file_path":os.path.join(HOME,".claude/projects/p/memory/MEMORY.md"),"content":"x"}}, "deny"),
({"tool_name":"Write","tool_input":{"file_path":os.path.join(HOME,"venture-os/wiki/projects/G/DECISIONS.md"),"content":"x"}}, "deny"),
({"tool_name":"Bash","tool_input":{"command":"rm dealer_network.sqlite"}}, "deny"),
({"tool_name":"Bash","tool_input":{"command":"truncate -s 0 comm-broker/bridge.sqlite"}}, "deny"),
({"tool_name":"Bash","tool_input":{"command":"sed -i '' 's/a/b/' .harness/state_guard.py"}}, "deny"),
({"tool_name":"Bash","tool_input":{"command":"rm src/cove/data/nhtsa_wmi.duckdb"}}, "allow"),
```
Riportare il breakdown del conteggio (vecchi TP + nuove regressioni FP + questi). = condizione #1.

## GIA' FATTO S248 (de-risk del verdetto)
- **#2 DONE**: `SEND_SIGNATURES`/`PHONE_RE` + branch `outreach_real` identici all'originale
  (provato con grep old vs new) → il diff NON ha toccato la detection numero-reale-≠-test.
- **#3 DONE**: gap over-narrow scritti nel docstring di gate_e.py.new — `sudo rm X`, `dd of=X`,
  redirect con path da variabile `> "$VAR"` = NON intercettati (accettati, threat=sbadataggine,
  Rule 1d); `A=1 rm X` invece E' gestito. + nota narrowing shell-scoped (Write/python -c/MCP fuori).

## LAND (dopo #1) — gated, prova in-vivo della classe disable_hook
1. CC: `cp .harness/gate_e.py.new .harness/gate_e.py` → BLOCK slug **`disable_hook-d312c497fe`**
   (= il matcher NUOVO blocca la propria installazione = dimostrazione live che disable_hook
   e' sopravvissuto al narrowing, E2E della condizione #1c del verdetto).
2. Luke: incolla verdetto nel packet `.harness/pending_review/disable_hook-d312c497fe.md` +
   `! python3 .harness/gate_e.py approve disable_hook-d312c497fe --verdict "APPROVE Claude AI S248: ..."`
3. CC: ritenta lo STESSO cp UNA volta → token consumato → land.
4. CC verifica: `python3 .harness/gate_e.py selftest` (PASS) + `bash state/refresh.sh S249` (ora passa) +
   `rm .harness/gate_e.py.new` + rimuovere packet FP `disable_hook-dca8f6243f.md` e `...d312c497fe.md`.
   Commit + push.

## DOPO il land (STATE.md sez.3 — NON fondere nel verdetto, sarebbe ri-litigazione)
- #1b: `gate_e.py` in `PROTECTED_FILES` di `state_guard.py` (defense-in-depth; editare e' doppio-gated).
- #2 COVERAGE-CHECK production-blocking `outreach_real`: Gate E intercetta il path-tool REALE di AMBRA?
  (MCP/Python che bypassa il matcher-shell → breaker decorativo → flip REJECT). Non urgente (gia' gated).
- #3 6-7 E2E: gate HITL iMac (fastapi) + invio PDF su TEST_FOUNDER 393314928901 (mai dealer reale).

Branch `s210/audit-master-plan`. Staging committato. Chiusura S248 a 77% (hard-stop).
