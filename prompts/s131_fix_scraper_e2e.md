# S131 — Fix scraper + E2E demo

## Contesto (leggi prima di tutto)
- HANDOFF.md ha il dettaglio completo della sessione S130
- MEMORY.md (in ~/.claude/projects/.../memory/) ha framework messaggi aggiornato
- Contesto S130 saturo (73%) — questa sessione riparte da zero

## Stato sistema
- WA daemon: ONLINE (iMac, porta 9191)
- TEST_FOUNDER (393314928901): silenzio atteso, Day 7 = 23 Aprile 2026. NON inviare nulla fino ad allora.
- E2E pipeline: MAI completata end-to-end

## 3 problemi da risolvere in ordine

### PROBLEMA 1 — Scraper slug rotti (P0)
File: `tools/scrapers/autoscout_scraper.py`, dict `MODEL_SLUG`
- BMW Serie 3 ("3er-reihe"), Serie 5 ("5er-reihe") → 404
- Mercedes GLC, C-Klasse, E-Klasse, GLE → 404
- Audi A3, A4, A6 → da verificare
- BMW X3, X1, X5 e Audi Q5 → funzionano (200)

**Fix**: trova slug corretti su autoscout24.de e aggiorna MODEL_SLUG
Metodo: `curl -s -o /dev/null -w '%{http_code}' 'https://www.autoscout24.de/lst/mercedes-benz/[slug]?atype=C&cy=D&fregfrom=2020&sort=standard' -H 'User-Agent: Mozilla/5.0'`
Verifica: `python3 tools/on_demand_runner.py --marca Mercedes --modello "Classe C" --budget 35000 --anno-min 2020` deve tornare listing reali

### PROBLEMA 2 — seller_name NULL nei listing IT (P0)
File: `tools/scrapers/autoscout_scraper.py`
- `vehicle_listings.seller_name` = NULL su tutti i listing autoscout24_it
- Il sistema non sa a quale dealer appartiene un listing italiano
- Aggiungere estrazione seller_name + seller_city dal parsing HTML AS24.it
- Salvare in vehicle_listings (campo seller_name già esiste, seller_city da aggiungere se mancante)

### PROBLEMA 3 — Contraddizione framework messaggi (P0 — chiedi al founder)
PRIMA DI SCRIVERE CODICE, chiedi al founder:
"Per il messaggio Day 1 a Stile Car: Opus dice che l'anchor su un dato specifico del loro
veicolo (es. BMW X4 2022, 140k km, prezzo +7.9% vs benchmark) è più efficace della
osservazione generica di mercato. Tu hai detto no brand/no auto nel Day 1.
Come risolviamo? Opzione A: cito il loro veicolo specifico ma senza dire 'cerco auto'.
Opzione B: resto generico sul mercato regionale senza nominare modelli."
Attendi risposta prima di procedere con il template.

## Demo E2E finale (solo dopo fix 1+2+3)
1. Prendi Stile Car (Orta Nova FG, RELAZIONALE, score 8.5)
2. Calcola anomalia automaticamente dal DB (X4 2022, 140k km, €35.499 vs €32.900)
3. Genera messaggio Day 1 con template approvato dal founder
4. Invia a TEST_FOUNDER (393314928901) — UNA SOLA VOLTA
5. Aspetta risposta prima di procedere a dealer reale

## Regole invariate
- MAI inviare a dealer reali senza test green su TEST_FOUNDER
- MAI inviare più di 1 messaggio Day 1 allo stesso numero
- Warming account: verificare `curl localhost:9191/status` prima di ogni invio
