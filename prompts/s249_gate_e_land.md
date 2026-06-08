# S249 — ARGOS · LAND Gate E refinement (attende verdetto Claude AI)

> Questo prompt si ATTENDE che il verdetto esterno di Claude AI sia gia' stato incollato
> nel packet PRIMA di ritentare il land. Senza verdetto + approve, NON procedere.

## STEP 0 — verdetto esterno Claude AI (PREREQUISITO, fuori sessione)
File da far rivedere a Claude AI (incollarne il contenuto):
  **`/Users/macbook/Documents/combaretrovamiauto-enterprise/.harness/gate_e.py.new`**
  (refinement gia' validato: `python3 .harness/gate_e.py.new selftest` → 19/19 PASS)

Domande per Claude AI (vincolo #4 — modifica strutturale a un guardrail):
  (a) l'operand-matching (`lossy_operands()`: target di `>`/`>>` su file + arg di
      mv/cp/rm/sed -i/tee/truncate/chmod col verbo in posizione di comando) e' una
      difesa SUFFICIENTE per il threat-model "sbadataggine di CC" (Rule 1d: euristica
      best-effort OK), o introduce falsi-NEGATIVI gravi?
  (b) il restringimento SoT-DB a {dealer_network.sqlite, comm-broker/bridge.sqlite,
      src/cove/data/cove_tracker.duckdb} lascia scoperto un DB che andava protetto?
  (c) l'escape `ARGOS_HARNESS_UNLOCK=1` in run_hook e' coerente con state_guard.gate_c?
  Residuo noto onesto: un `git commit` con HEREDOC che contiene LETTERALMENTE `> STATE.md`
  nel body resta un FP teorico (raro, accettato).

Il verdetto va incollato in:
  **`/Users/macbook/Documents/combaretrovamiauto-enterprise/.harness/pending_review/disable_hook-d312c497fe.md`**
  (sezione `## Verdetto esterno`).

## STEP 1 — approvazione (azione di LUKE, prefisso `!`)
  ! python3 .harness/gate_e.py approve disable_hook-d312c497fe --verdict "<sintesi Claude AI>"

## STEP 2 — land (CC, UNA volta)
  cp .harness/gate_e.py.new .harness/gate_e.py
  (il gate_e ATTUALE lo blocca con slug disable_hook-d312c497fe; col token registrato passa)

## STEP 3 — verifica post-land (CC)
  - `python3 .harness/gate_e.py selftest`  → atteso 19/19 PASS
  - `bash state/refresh.sh S249`           → ora deve PASSARE (era l'FP che bloccava l'avvio)
  - `rm .harness/gate_e.py.new`            → pulizia staging
  - rimuovere i packet FP: `.harness/pending_review/disable_hook-dca8f6243f.md` (refresh.sh 2>&1)
    e `.harness/pending_review/disable_hook-d312c497fe.md` (consumato)
  - commit + push

## STEP 4 — restano (DOPO il land, ordine STATE.md sez.3)
  - item #1b: aggiungere `gate_e.py` a `PROTECTED_FILES` di `state_guard.py`
    (defense-in-depth secondario; editare state_guard.py e' doppio-gated → stessa procedura).
  - #2 COVERAGE-CHECK (production-blocking `outreach_real`): confermare che Gate E intercetti
    il path-tool REALE con cui AMBRA invia (MCP/Python che bypassa il matcher-shell → REJECT).
  - #3 6-7 E2E: gate HITL iMac (fastapi) + invio PDF su TEST_FOUNDER 393314928901 (mai dealer reale).

## Contesto cosa cambia il refinement (vs gate_e.py attuale)
1. FP fix: disable_hook/overwrite_sot SOLO su operandi reali di op lossy → niente piu' FP su
   script eseguito (`bash refresh.sh ... 2>&1`), body di commit-message (FP S247 ×2), fd-dup.
2. SoT-DB ristretto (non piu' qualunque .db sotto ROOT → escludeva DB-spazzatura profilo Chrome).
3. Escape `ARGOS_HARNESS_UNLOCK=1`.
Tutto su branch `s210/audit-master-plan`, staging committato in `69df132`.
