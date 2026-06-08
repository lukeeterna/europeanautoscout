# S251 — applica 1b + fix #2 (sessione UNLOCK) + chiudi #3

> S250 ha verificato tutto. I 2 fix sono PRONTI ma editano file-harness → richiedono
> rilancio CC con `ARGOS_HARNESS_UNLOCK=1`. Apri così:
>
>     ARGOS_HARNESS_UNLOCK=1 claude   # nella dir del progetto
>
> Patch esatte (copy-paste) in:
> `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s250_gate_e_coverage_findings.md`

## Apri così
`bash state/refresh.sh S251`

## Item (in ordine, sessione UNLOCK)
1. **1b** — `state_guard.py`: aggiungi `GATE_E` a `PROTECTED_FILES` (patch pronta nel memory file).
   Verifica: edit di prova su file non-protetto = allow; sessione riparte pulita.
2. **#2 fix** — `gate_e.py`: aggiungi `OUTREACH_SCRIPT_SIGNATURES` + ramo `hit_script` in `classify_bash`
   (patch pronta). Aggiungi i 2 selftest case (DENY su `send_day1_stile_car.py`, ALLOW su `--dry-run`).
   Gate: `python3 .harness/gate_e.py selftest` deve passare (28/28).
3. **MEMORY.md index** — in UNLOCK puoi indicizzare `s250_gate_e_coverage_findings.md`.
   POI decidi con Luke (pendenza aperta): eccezione narrow Gate E per index-append a MEMORY.md
   OPPURE documentare che il protocollo fine-sessione gira sotto UNLOCK.
4. **Pulizia** — rimuovi i 2 packet collaterali `.harness/pending_review/disable_hook-16c78a2921.md`
   e `outreach_real-4440890e8c.md` (tentativi bloccati S250, innocui).
5. **commit + push** su `s210/audit-master-plan`.

## #3 — E2E anelli 6-7 (NON in questa sessione)
BLOCKED-ON: Luke fisico + iMac/fastapi (app.py richiede fastapi assente su MacBook).
Gate HITL dossier + invio PDF SOLO a TEST_FOUNDER 393314928901 (MAI dealer reale).
Vedi `feedback_e2e_full_test_founder_before_day1.md`. Resta l'unico item che NON è codice.

## Correzione al prompt S250 (verificata)
1b: l'`approve` di gate_e da solo NON sblocca l'edit di `state_guard.py` — Gate C suo non ha token.
UNICA via = `ARGOS_HARNESS_UNLOCK=1`. (Da qui il rilancio in testa a questo prompt.)
