# S212 — Applicare i delta PLAN.md ↔ ARGOS_MASTER (approvazione riga-per-riga)

> Branch: `s210/audit-master-plan`. Chiusura S211 ordinata, context gate 50%.
> Source-of-truth: `ARGOS_MASTER/00_INDEX/ARGOS_MASTER_PLAN.md` + `ARGOS_MASTER/04_STATO_TECNICO/STATO_COMPONENTI.md`.
> PLAN operativo VOS reale = `/PLAN.md` (root, UNICO — gli altri PLAN sono storici/pre-pivot, solo `ref:` in METODO).

## STATO S211 (fatto, NO modifiche applicate)
Prodotta tabella 15 delta PLAN.md ↔ master. Nessuna modifica al PLAN. Attesa approvazione Luke riga-per-riga.
Aperti in TextEdit per ispezione: `src/marketing/payment_handler.py` (ha `mark_paid`), `comm-broker/deal_state_machine.py`. ESISTONO — da leggere per verificare se contengono già un abbozzo del gating pagamento→fonte (priorità #1 master, oggi flaggato ASSENTE in STATO_FEATURE).

## I 15 delta (sintesi — dettaglio in memory s211_delta_plan_vs_master.md)
CRITICI:
- #1 [AGGIORNA] gating pagamento→fonte ASSENTE da STATO_FEATURE → aggiungi MISSING + CRITIQUE. PRIMA leggi payment_handler.py + deal_state_machine.py (verifica se gating già abbozzato).
- #2 [AGGIORNA] sales agent inquadrato REATTIVO; master = OUTBOUND + KB pre-addestrata + gate TEST CAMPIONE → riformula STATO_FEATURE + aggiungi GATE-CAMPO.
- #8 [AGGIORNA] sanitizer: PLAN "over-mask" vs master "becca watermark URL non targhe (5FP/0TP)". Aggiungi: sanitizer = 2° strato, fonte-gating = 1°.
TIENI: #5 pricing pay-on-delivery, #7 scrapers count (già onesto), #9 CoVe 2955, #15 scope nazionale.
ARRICCHISCI MASTER (dettaglio solo nel PLAN): #9 CoVe run, #10 split-brain DB, #11 daemon 48 restart, #12 GDPR intel.
MASTER INCOMPLETO: #4 soglia stock numerica, #5 range fee €800/€400 da riconfermare Luke, #13 corpus_register 171 frasi → nel PLAN.
CAT.1 PRE-PIVOT: #4 "30-80 auto" in identity.md, #6 argos-proxy possibile ridondante vs AS24 source=DE.

## PRIMA AZIONE S212
1. Leggi `src/marketing/payment_handler.py` + `comm-broker/deal_state_machine.py` → aggiorna riga #1 (gating davvero inesistente o abbozzo?).
2. Chiedi a Luke conferma riga-per-riga sui 15 delta.
3. Applica SOLO le righe approvate a `/PLAN.md`. Branch dedicato, no master.
