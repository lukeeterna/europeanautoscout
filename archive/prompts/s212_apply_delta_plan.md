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

## GATING PAGAMENTO→FONTE — verificato sul codice (S211, NO abbozzo)
Letti i due file. Gating CONFERMATO inesistente:
- `payment_handler.py`: DuckDB + `fee_invoices` + `mark_paid()` (riga 251) fa UPDATE fee_invoices PAID + dealer_leads CLOSED. **Path DB STALE** riga 38 `~/Documents/app-antigravity-auto/.../dealer_network.duckdb` (workspace morto S210) → DA FIXARE.
- `deal_state_machine.py`: SQLite `deals.sqlite`, 8 stati forward +aborted, `confirm_payment` (riga 92) payment_pending→payment_confirmed, hook `on_transition` (riga 171) + audit `state_transitions` + `history()`. Ben fatto.
- **I due NON si parlano**: DB diversi, `mark_paid` non chiama `confirm_payment`, nessuno rilascia la fonte. NESSUN campo `source_locked` (solo `metadata_json` free-form riga 35).

## DESIGN GATING concordato (flusso, codice in S212)
- Innesto: **state machine** (è il posto giusto, impalcatura già presente).
- Deliverable post-pagamento = **SECONDO PDF gated** su transizione `confirm_payment` (riuso `pdf_generator_enterprise.py`, 0-cost). NO portale (over-engineering N=0 paganti).
- Conferma pagamento = **manuale Luke** (no webhook SEPA) via G-APPROVAL CLI CC → unica azione atomica che marca fattura PAID + avanza stato + rilascia fonte.
- Fonte vive in `metadata_json.source_locked`, salvata a creazione deal, mai in output finché stato != payment_confirmed.
- CAVEAT: garanzia parziale finché sanitizer C-SAN-001 BLOCKED (gating-fonte + sanitizer = due metà stessa serratura).

## 3 VERIFICHE PENDENTI prima di scrivere il PLAN (Claude AI flag, NON confermate a memoria)
1. AS24 param: `source=DE` (master) vs `cy=D` (Claude AI dice audit) → grep scraper reale.
2. Plate-detector: "becca watermark 5FP" (master) vs "RIMOSSO/maschera cieca" (audit S210) → leggi AUDIT_E2E.md.
3. corpus_register: "171 frasi utili" (master) vs "223 frammenti troncati inservibili" (audit) → verifica file reale.

## PRIMA AZIONE S212
1. Esegui le 3 verifiche sopra (grep + AUDIT_E2E.md) → fissa i fatti.
2. Chiedi a Luke conferma riga-per-riga sui 15 delta (corretti con i fatti verificati).
3. Applica SOLO le righe approvate a `/PLAN.md` + aggiungi feature `gating pagamento→fonte: MISSING`. Branch dedicato, no master.
