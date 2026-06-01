# NEXT SESSION — S212

> Branch: `s210/audit-master-plan`. Chiusura S211 al gate context 62%.
> Leggi PRIMA: `prompts/s212_apply_delta_plan.md` (handoff completo).

## STATO S211 (fatto)
1. Diagnosi 15 delta `/PLAN.md` (VOS operativo, UNICO) ↔ ARGOS_MASTER. NO modifiche al PLAN — attesa approvazione Luke riga-per-riga.
2. Gating pagamento→fonte (priorità #1): **verificato INESISTENTE sul codice** (non abbozzo). Due DB scollegati (payment_handler DuckDB+path STALE / state machine SQLite), `mark_paid`↛`confirm_payment`, nessun `source_locked`.
3. Design concordato: secondo PDF gated su `confirm_payment`, innesto state machine, conferma manuale Luke via G-APPROVAL. NO portale. Caveat: garanzia parziale finché sanitizer C-SAN-001 BLOCKED.

## PRIMA AZIONE S212
1. 3 verifiche pendenti (NON a memoria): AS24 `source=DE` vs `cy=D`; plate-detector "becca watermark" vs "rimosso"; corpus "171 frasi" vs "223 frammenti troncati" → grep scraper + leggi AUDIT_E2E.md.
2. Conferma Luke riga-per-riga sui 15 delta corretti.
3. Applica righe approvate a `/PLAN.md` + aggiungi `gating pagamento→fonte: MISSING`.

Memory: `s211_delta_plan_vs_master.md`.
