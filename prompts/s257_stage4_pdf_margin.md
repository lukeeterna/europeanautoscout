# S257 — Stage 4: PDF con verdetto margine reale (chiude DoD #2)

**Generato S256** (2026-06-09). Stage 2-3 CHIUSI e committati (`1e509c2`). DoD #1 + #3 VERDI.
Apri fresco. NON ri-investigare i fatti verificati qui sotto.

## STATO (cosa è fatto)
- **Stage 2 DONE** `tools/it_market_price.py`: `get_it_distribution(make, model, year, km, fuel=None)`
  → `{median, p25, p75, min, max, n, n_raw, low_confidence, source, listings[]}`. Mediana comparabili
  REALI AutoScout24.it. Smoke live OK (BMW Serie 3 2022 → median €35.900, n=11).
- **Stage 3 DONE** `on_demand_runner.py` Step 2c (dopo A4, prima del PDF): per ogni veicolo top calcola
  `get_it_distribution` → `evaluate_margin` → attacca `_margin_*` + `_it_distribution`, VETO sui REJECT.
- **DoD #1 VERDE** `tools/margin_e2e.py`: 22 annunci DE reali → 10 PASS / 12 REJECT (mercato IT €41.200, n=19).
  Comando: `python3 -m tools.margin_e2e --make BMW --model "Serie 3" --year-min 2021 --year-max 2024 --pages 3 --limit 22`
- **DoD #3 VERDE**: X1 (21795/22862, friction=0) → REJECT end-to-end nello stesso harness.

## RESTA — DoD #2: 1 annuncio PASS → PDF reale (Stage 4)

### Dove agire (`tools/scripts/pdf_generator_enterprise.py`)
- `VehicleData` dataclass (righe ~60-117): AGGIUNGI campi opzionali:
  `margin_decision, chiavi_in_mano, spread_lordo, dealer_floor, surplus, fee_argos,
   margine_netto_dealer, margine_netto_pct, it_median, it_p25, it_p75, it_n, it_source`.
- Sostituire i FALSI hardcoded (verificati S255):
  - `market_it = int(price*1.15)` a **riga ~1805** (path `--data` usato dal runner) → usa `it_median` dal JSON.
  - `argos_fee = 900` a **righe ~498 e ~797** → usa `fee_argos` dal JSON (ZERO se REJECT/no-surplus).
- Clonare `_create_financial_analysis_v2` (righe ~781-851, ha già la forma chiavi_in_mano/margine_lordo/netto)
  in due sezioni nuove: `_create_margin_verdict_section()` (decisione PASS/REJECT + surplus + fee + netto%)
  e `_create_it_distribution_section()` (median/p25/p75/N comparabili, source AutoScout24.it).
- `on_demand_runner.generate_dossier` passa i `_margin_*` / `_it_distribution` nel JSON `--data` → mapparli su VehicleData.

### DoD #2 (terminal fact — Rule 1b)
Prendere 1 annuncio PASS reale (es. dal report margin_e2e), generare il PDF via runner/generate_dossier,
**incollare il path del PDF** e confermare a vista che mostra: prezzo DE reale, mercato IT = mediana reale (NON ×1.15),
fee ARGOS reale (quota surplus, NON €900 flat), decisione PASS.

## DEBITO ONESTO da chiudere (non bloccante DoD ma flaggato)
La mediana IT esce **identica per ogni anno** (€41.200, n=19) → lo scrape IT `scrape_model` con year±1 non
discrimina anno/trim (page-1 dominata da 2025 MSport €43-52k). Per ARGOS production serve discriminazione
anno+trim sulla distribuzione IT (più pagine + filtro trim/fuel). Marcato `[unverified-precisione]`.
NON è il bug €167 (risolto: X1 REJECT). Valutare in S257 dopo il PDF, o parcheggiare in BACKLOG.

## VINCOLI
- NON toccare CoVe né payment-gating. Il gate margine si AGGIUNGE.
- mobile.de/Vincario v3.2 = DOPO aver chiuso AutoScout E2E (verificare con WebSearch al loro turno).
- Compilare/smoke NON è prova. Prova = PDF reale che mostra i numeri reali.
- Nessun contatto dealer reali.
- "delta optional DE↔IT in €": se non hai fonte listino reale per trim, dichiara `[unverified]`, NON inventare (= €167 mascherato).
