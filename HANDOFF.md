# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S130 — 2026-04-16

---

## S130 — COSA È SUCCESSO

### Fatto
- Verificato iMac online, WA daemon connected (uptime 27h, 4 sent, 6 remaining)
- TEST_FOUNDER: 0 INBOUND — silenzio normale, Day 7 = 23 Aprile 2026
- image_sanitizer: PASS (2 img sanitizzate da autoscout24_de_a610dd1c6a97)
- validation_log: PASS (schema corretto: decision/motivation/mode/ts)
- CoVe schema verificato: colonna `km` (NON mileage), `analyzed_at`
- Trovato Stile Car su AutoScout24 come "Stile Car.it Srls" (Orta Nova FG)
- Anomalia calcolata: BMW X4 2022, 140k km, €35.499 (+7.9% vs benchmark)

### Scoperto (problemi reali)
1. **Scraper rotto** — BMW Serie 3/5 e TUTTI i modelli Mercedes → 404. Solo BMW SUV e Audi Q5/A4 funzionano.
2. **seller_name NULL** — listing autoscout24_it non collegati ai dealer nel DB
3. **E2E mai completato** — scrape→score→PDF→WA non ha mai girato end-to-end
4. **days_on_market** — non recuperabile dai search results, solo dal detail page

### Framework messaggi ridefinito dal founder
- V3 (CHI+PERCHÉ+DOMANDA) è SBAGLIATO: "Germania", "premium", "cerco auto" = trigger difensivo
- Day 1 NON nomina mai un'auto specifica e NON nomina brand
- Anchor = osservazione di mercato regionale con dati verificabili
- Zero CTA, solo firma
- **CONTRADDIZIONE APERTA**: Opus dice versione specifica (con dati veicolo) > generica. Founder dice no brand/no auto. Da risolvere.

---

## S131 DEVE FARE (in ordine)

### 1. Fix scraper slug Mercedes + BMW sedan
File: `tools/scrapers/autoscout_scraper.py`, dict `MODEL_SLUG`
Problema: slug "glc", "c-klasse", "5er-reihe" → 404 su autoscout24.de
Soluzione: verificare slug corretti attuali su AS24 e aggiornare la dict
Test: `curl -s -o /dev/null -w '%{http_code}' 'https://www.autoscout24.de/lst/mercedes-benz/[slug]?...'`

### 2. Fix scraper autoscout24_it → salvare seller_name + seller_city
File: `tools/scrapers/autoscout_scraper.py`
Aggiungere estrazione `seller_name` e `seller_city` dal HTML di AS24.it
Salvarli in `vehicle_listings.seller_name` e nuovo campo `seller_city`

### 3. Risolvere contraddizione Day 1 con founder
Domanda diretta: "anchor su veicolo specifico del dealer (Opus) vs no brand/no auto (tua regola)?"
Solo dopo risposta founder → template definitivo

### 4. Demo E2E su TEST_FOUNDER
Solo dopo fix 1+2+3:
- Scrape fresh per dealer reale (Stile Car o altro)
- Calcola anomalia automaticamente
- Genera messaggio Day 1
- Invia a TEST_FOUNDER (393314928901) — UNA SOLA VOLTA
- Aspetta risposta

---

## File chiave S131
```
tools/scrapers/autoscout_scraper.py    ← fix slug + seller_name
tools/on_demand_runner.py              ← testa dopo fix
dealer_network.sqlite (iMac)           ← dealer queue
src/cove/data/cove_tracker.duckdb     ← benchmark listing IT
```

## Stile Car dati verificati
- Nome AS24: "Stile Car.it Srls", Orta Nova FG
- BMW X4 xdrive20d 2022, 140.000km, €35.499 (vs €32.900 comparabile = +7.9%)
- BMW 118d 2021, 130.000km, €21.500
- BMW 216d 2020, 180.000km, €10.999
- Persona: RELAZIONALE, score 8.5

## Regola assoluta invariata
Test su TEST_FOUNDER (393314928901) obbligatorio prima di qualsiasi dealer reale.
