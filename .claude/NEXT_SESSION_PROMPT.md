# S213 — Implementazione gating pagamento→rilascio-fonte (C-GATE-FONTE-001)

> Branch: `s210/audit-master-plan`. S212 chiusa VERDE (commit `c2dde5a`).
> S212 era SOLO documentale: ha aggiunto la feature `gating pagamento→rilascio-fonte: MISSING` a /PLAN.md. S213 = il CODICE.

## STATO S212 (fatto)
Riconciliazione /PLAN.md ↔ ARGOS_MASTER applicata (delta A/B/E approvati Luke riga-per-riga):
- Nuova FEATURE `gating pagamento→rilascio-fonte: MISSING` + CRITIQUE `C-GATE-FONTE-001` in /PLAN.md.
- sales agent riformulato (outbound=target vs realtà reattivo+HITL) + GATE-CAMPO in METRICHE.
- sanitizer C-SAN-001 annotato 2° strato; gating-fonte 1° strato.
- Fee Luke S212: **STARTUP €400 flat → SCALING a salire (€800+)**. Stock target <20.
- Nuovi: C-IDENTITY-RESIDUE-001 (identity.md "30-80" da correggere), C-MASTER-SYNC-001 (4 dettagli da backportare nel MASTER).
Memory: `s212_plan_reconciliation_applied.md`.

## GAP da non dimenticare
Delta #3 e #14 (su 15 dichiarati S211) NON persistiti, non recuperabili. 13/15 documentati, 3 critici coperti. Se Luke li ricorda, riaprire.

## DESIGN GATING concordato (da implementare in S213)
- Innesto: **state machine** (`comm-broker/deal_state_machine.py`: 8 stati, confirm_payment :92, hook on_transition :171, audit state_transitions).
- Deliverable post-pagamento = **2° PDF gated** su transizione `confirm_payment` (riuso `tools/scripts/pdf_generator_enterprise.py`, 0-cost). NO portale (over-eng N=0 paganti).
- Conferma pagamento = **manuale Luke** (no webhook SEPA) via **G-APPROVAL CLI CC** → azione atomica: marca fattura PAID (payment_handler.py mark_paid :251) + avanza stato + rilascia fonte.
- Fonte vive in `metadata_json.source_locked` (deal_state_machine.py :35), salvata a creazione deal, mai in output finché stato != payment_confirmed.
- FIX collaterale: `payment_handler.py:38` path DB STALE (`~/Documents/app-antigravity-auto/.../dealer_network.duckdb`, workspace morto) → puntare al DB autoritativo.
- I due NON si parlano oggi: DuckDB fee_invoices vs SQLite deals.sqlite; mark_paid non chiama confirm_payment. Da collegare.
- CAVEAT: garanzia parziale finché C-SAN-001 BLOCKED (gating-fonte + sanitizer = due metà stessa serratura).

## PRIMA AZIONE S213
1. Rileggi /PLAN.md CRITIQUE C-GATE-FONTE-001 + memory s212.
2. Delega architect: piano implementazione gating su deal_state_machine (innesto confirm_payment → release source_locked → genera 2° PDF). NO codice prima del piano approvato Luke.
3. Vincolo: zero-cost, conferma manuale Luke, idempotenza, test su TEST_FOUNDER 393314928901 prima di qualsiasi dealer reale.

Day 1 Stile Car (2026-06-03) resta BLOCCATO su: C-COMM-INTEL-001 (intel/AMBRA funnel) + C-SAN-001 + C-GATE-FONTE-001 + C-E2E-ZERO.
