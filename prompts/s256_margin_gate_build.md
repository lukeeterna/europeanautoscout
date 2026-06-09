# S256 — Completare gate margine: IT distribution + wiring runner + PDF + E2E 20 reali

**Generato S255** (2026-06-09). Stage 0-1 del brief CHIUSI e verificati. Restano stage 2-3-4.
Apri fresco. NON ri-investigare i fatti già verificati qui sotto.

## Contesto (perché)
Il dossier X1 ha certificato un affare da €167 di margine dealer. Root cause: CoVe misura
la bontà dell'AUTO, non dell'AFFARE. Si aggiunge un asse separato "gate margine" con VETO.
Brief completo founder in prompts/s255_e2e_dossier_invio_test_founder.md NON contiene il brief;
il brief vero è nel messaggio S255 di Luke (riprofilazione target + gate margine + multi-portale + report).

## FATTI VERIFICATI S255 (non ri-controllare)
- **Il "prezzo mercato IT" è FALSO ovunque**: `prezzo × 1.15` (o 1.12) hardcoded. NON esiste
  fetcher comparabili IT reali. Punti: `pdf_generator_enterprise.py:1805` (path `--data` usato dal
  runner), `:2057`, `:155`; `src/cove/scraper_cove_pipeline.py:95`, `dossier_standard.py:152`,
  `pipeline_orchestrator.py:530`, `dealer_matcher.py:101`. Fee flat **€900 hardcoded** a
  `pdf_generator_enterprise.py:498` e `:797`.
- **AS24.it scraping FUNZIONA in produzione** (GO, validato live S255): 19 listing reali con
  prezzo/km/anno/trim/url in 1s. Comando:
  `python3 -m tools.scrapers.autoscout_scraper --make BMW --model "Serie 3" --country IT --pages 2 --year-min 2021 --year-max 2024`
  Primitiva comparabili IT = `AutoScoutScraper("autoscout24_it").scrape_model(make, model, year_min, year_max)`.
- **`tools/margin_gate.py` FATTO + committato `eb68342`** (selftest verde). `evaluate_margin(prezzo_de,
  prezzo_mercato_it, friction_eur=1915, dealer_floor_pct=0.12, argos_share=0.40)` → `MarginResult`
  con decision PASS|REJECT. **DoD #3 GIÀ DIMOSTRATO**: X1 21795/22862 (friction=0) → REJECT, surplus −1676.
- `on_demand_runner.py`: scrape de/nl (riga 378), NON calcola margine/fee/IT. CoVe in `score_vehicles`
  (223-270), aggiunge `_cove_score/_cove_recommendation/_cove_confidence`. Gates A0 (404-420) e A4 (439-465).
  PDF via subprocess `--data` JSON (293-326 → `generate_dossier_from_data` :1779+).
- `pdf_generator_enterprise.py`: input = `VehicleData` dataclass (60-117). Tabella finanziaria
  `_create_financial_analysis_v2` (781-851) ha già la FORMA giusta (chiavi_in_mano/margine_lordo/netto)
  ma con `market_it` finto e fee 900 — è il template da clonare.
- `market_price_index.py` ha matematica median/percentile/outlier riusabile (`estimate()` ~243) — MA
  va alimentata con SOLO punti IT, non riusare l'index persistito (DE-dominato).
- `cove_engine_v4.py` NON modificare. `result.market_price_ref` è un riferimento **DE**, NON usarlo come prezzo IT.
- `fee_calculator.py` è **dead code** (nessun caller runtime) — non patcharlo.

## STAGE RIMANENTI

### Stage 2 — `tools/it_market_price.py` (NEW)
`get_it_distribution(make, model, year, km, fuel=None) -> {median, p25, p75, min, max, n, source, listings[]}`.
Instanzia `AutoScoutScraper("autoscout24_it")`, `scrape_model(make, model, year_min=year-1, year_max=year+1)`,
filtra km band ±30k, calcola percentili con `statistics`. source="AutoScout24.it". Gestire n<5 → flag bassa confidenza.

### Stage 3 — wire nel runner (`on_demand_runner.py` run(), dopo riga ~465)
Per ogni veicolo sopravvissuto ai gate: `get_it_distribution(...)` → `prezzo_mercato_it = median`;
`margin_gate.evaluate_margin(price_eur, prezzo_mercato_it)`; attacca `_margin_*` + `_it_distribution` al dict;
**VETO**: filtra `_margin_decision == "REJECT"` (gate parallelo ad A0/A4); logga PASS count. Bias sourcing premium/recenti.

### Stage 4 — PDF (`pdf_generator_enterprise.py`)
Sostituire `market_it = int(price*1.15)` (:1805) e `argos_fee = 900` (:498, :797) con i valori passati dal runner
via `--data` JSON. Aggiungere campi a `VehicleData` (margin_decision, chiavi_in_mano, spread_lordo, dealer_floor,
surplus, fee_argos, margine_netto_pct, it_median, it_p25, it_p75, it_n, it_source). Aggiungere
`_create_margin_verdict_section()` + `_create_it_distribution_section()` (clonare `_create_financial_analysis_v2`).

## DEFINITION OF DONE (terminal facts — Rule 1b)
1. Runner su **≥20 annunci reali live** (incolla URL): per ciascuno make/model/trim, anno, prezzo_DE,
   prezzo_mercato_IT (+N comparabili+percentile), frizione, spread_lordo, dealer_floor, surplus, fee_ARGOS,
   margine_netto_dealer %, DECISIONE. Riporta PASS su 20.
2. 1 annuncio PASS → **PDF reale** (incolla path).
3. X1 → REJECT **attraverso il gate** (già provato in margin_gate selftest; rifarlo end-to-end nel report).

## VINCOLI
- Chiudi AutoScout24 E2E PRIMA di aggiungere adapter (mobile.de/automobile.de/Vincario v3.2 = DOPO, verificare con WebSearch al loro turno).
- Compilare/smoke NON è prova. Prova = margine su annunci reali + PDF reale.
- NON toccare payment-gating né CoVe. Il gate margine si AGGIUNGE.
- Nessun contatto dealer reali.
- Il "delta optional DE↔IT in €" del brief è la parte più fragile (manca listino optional per trim):
  se non hai una fonte reale, dichiaralo [unverified], NON inventare il numero — sarebbe il €167 mascherato.
