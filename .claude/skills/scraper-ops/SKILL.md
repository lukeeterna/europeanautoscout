---
name: scraper-ops
description: >
  Fix e manutenzione scraper AutoScout24. Carica quando Luke dice "fix scraper",
  "scraper rotto", "404 listing", "MODEL_SLUG", "seller_name NULL", "on_demand_runner",
  o quando stai lavorando su tools/scrapers/autoscout_scraper.py o
  tools/on_demand_runner.py. NON caricare per scoring CoVe o invio WA.
---

# Scraper Ops — Stato e protocollo fix

## Stato attuale (S132)
| Modello | Slug | Status |
|---|---|---|
| BMW X3 | `x3` | OK |
| BMW X1 | `x1` | OK |
| BMW X5 | `x5` | OK |
| Audi Q5 | `q5` | OK |
| Audi A4 | `a4` | OK |
| BMW Serie 3 | `3er-(alle)` | FIXATO S132 |
| BMW Serie 5 | `5er-(alle)` | FIXATO S132 |
| Mercedes GLC | `glc-(alle)` | FIXATO S132 |
| Mercedes C | `c-klasse-(alle)` | FIXATO S132 |
| Mercedes E | `e-klasse-(alle)` | FIXATO S132 |
| Mercedes GLE | `gle-(alle)` | FIXATO S132 |

**Pattern AS24 2026**: `{model}-(alle)` per sedan/wagon (SUV mantengono slug corto).
**Portali testati OK**: DE, AT, IT, NL, FR, SE. BE usa path `/fr/lst/` o `/nl/lst/`.

## Fix scraper slug — procedura
1. Apri manualmente su browser: `https://www.autoscout24.it/lst/mercedes-benz/c-klasse`
2. Verifica se redirect → trova slug corretto nella URL finale
3. Aggiorna dict `MODEL_SLUG` in `tools/scrapers/autoscout_scraper.py`
4. Test: `python3 tools/on_demand_runner.py --marca Mercedes --modello "Classe C" --budget 50000`
5. DONE quando: ≥3 listing con prezzo e km

## Fix seller_name NULL — procedura
Tutti i listing da `autoscout24_it` hanno `seller_name = NULL` e `matched_dealer = NULL`.
Il parser non estrae il nome del venditore dalla pagina.

1. Ispeziona HTML di un listing AS24.it → trova il tag che contiene seller name
2. Aggiungi parsing in `tools/scrapers/autoscout_scraper.py`
3. Salva su `vehicle_listings.seller_name` e `vehicle_listings.seller_city`
4. DONE quando: `SELECT COUNT(*) FROM vehicle_listings WHERE source='autoscout24_it' AND seller_name IS NOT NULL` > 0

## Regole scraper — IMMUTABILI
- `sleep(15)` tra richieste — non ridurre
- `Semaphore(5)` — non aumentare
- `DAILY_LIMIT = 30` — non aumentare senza approvazione
- User-Agent: sempre Mozilla/5.0 realistico (no bot string)
- SOLO dati strutturati — MAI CSS selectors fragili

## File coinvolti
- `tools/scrapers/autoscout_scraper.py` — scraper principale + MODEL_SLUG dict
- `tools/on_demand_runner.py` — runner on-demand
- `src/cove/data/cove_tracker.duckdb` — destinazione dati (iMac)

## Test command
```bash
python3 tools/on_demand_runner.py --marca BMW --modello "X3" --budget 40000 --dealer "Test"
# Output atteso: ≥3 listing con listing_id, price, km
```
