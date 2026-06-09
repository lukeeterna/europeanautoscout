# Breadcrumb ripartenza — S257

**Generato**: 2026-06-09 (S256 close, context 60% mandate) · commit `1e509c2`

## Prossimo prompt
`prompts/s257_stage4_pdf_margin.md` (self-contained, committato)

## Stato S256 (gate margine)
- Stage 2 DONE: `tools/it_market_price.py` — mediana comparabili IT reali (sostituisce ×1.15). Smoke live OK.
- Stage 3 DONE: `on_demand_runner.py` Step 2c — margin gate con VETO, attacca `_margin_*`/`_it_distribution`.
- DoD #1 VERDE: `python3 -m tools.margin_e2e` → 22 annunci DE reali, 10 PASS / 12 REJECT (mercato IT €41.200).
- DoD #3 VERDE: X1 dossier S254 → REJECT end-to-end.
- RESTA DoD #2: Stage 4 PDF (editing `pdf_generator_enterprise.py`) → vedi prompt s257.

## Debito flaggato
Mediana IT non discrimina anno/trim (identica €41.200 ogni anno) — `[unverified-precisione]`, non blocca DoD.

## Come riprendere
1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. Incolla `prompts/s257_stage4_pdf_margin.md`
3. Primo movimento: aggiungere campi `_margin_*` a `VehicleData` + rimuovere `price*1.15` (:1805) e fee 900 (:498,:797)
