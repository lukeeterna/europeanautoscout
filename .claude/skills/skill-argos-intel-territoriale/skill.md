---
name: argos-intel-territoriale
description: >
  Intelligence territoriale ARGOS: raccoglie dati REALI su dealer e territorio
  da fonti primarie (Subito.it stock, AS24 recensioni, Google Maps reviews,
  Facebook pagine dealer, Instagram post). NON web search generiche —
  scraping diretto delle piattaforme dove i dealer SONO.
  TRIGGER su: "intel dealer", "recensioni dealer", "stock dealer",
  "territorio", "zona auto", "facebook dealer", "instagram dealer",
  "google maps dealer", "quanti dealer", "concorrenza zona".
version: 1.0.0
allowed-tools: Bash, Read, Write, Agent, Edit
---

# ARGOS™ Intelligence Territoriale

## SCOPO
Raccogliere dati REALI e VERIFICABILI su dealer specifici e territori.
NON web search generiche — scraping diretto delle fonti primarie.

## FONTI PRIMARIE (in ordine di affidabilità)

### 1. AutoScout24.it — Stock e recensioni dealer
```python
# Stock dealer: https://www.autoscout24.it/concessionari/{slug}/
# Recensioni: https://www.autoscout24.it/concessionari/{slug}/recensioni
# Inventario: https://www.autoscout24.it/concessionari/{slug}/veicoli
# Usare resilient_fetcher.py per fetch
```

### 2. Subito.it — Profilo shop e annunci
```python
# Shop: https://impresapiu.subito.it/shops/{id}-{slug}
# Annunci provincia: https://www.subito.it/annunci-{regione}/vendita/auto/{provincia}/
# Parsing via __NEXT_DATA__ JSON
# Tool: tools/dealer_discovery/subito_dealer_scraper.py
```

### 3. Google Maps — Recensioni, rating, foto
```python
# Query: "autosalone {città}" o nome dealer specifico
# Dati: rating, numero recensioni, TESTO recensioni, foto, orari
# Tool: Playwright per scraping (no API a pagamento)
```

### 4. Facebook — Pagine business dealer
```python
# Cercare: "{nome dealer} {città}" su Facebook
# Dati: ultimi post, tipo contenuti, interazioni, foto consegne
# Tool: Playwright browser
```

### 5. Instagram — Feed dealer
```python
# Cercare: nome dealer o hashtag + città
# Dati: tipo contenuti, frequenza post, foto consegne vs stock
```

### 6. Registro Imprese — Dati societari
```python
# Via Atoka, Kompass, o ricerca diretta
# Dati: ragione sociale, ATECO, fatturato, dipendenti, anno fondazione
```

## COMANDI

### `intel <dealer_name> <città>`
Raccoglie TUTTI i dati disponibili sul dealer da tutte le fonti.
Output: profilo strutturato con dati verificati e fonte per ogni dato.

### `territorio <provincia>`
Mappa del territorio:
- Quanti dealer nella provincia (da discovery engine)
- Zone auto (concentrazioni geografiche)
- Dealer più forti (per recensioni/stock)
- Gap di mercato (zone senza premium)

### `recensioni <dealer_name>`
Estrae e analizza le recensioni REALI del dealer:
- Testo completo di ogni recensione
- Pattern: cosa lodano i clienti? cosa criticano?
- Segnali import EU nelle recensioni
- Tono del dealer nelle risposte

### `concorrenza <città>`
Analisi competitiva nella zona:
- Tutti i dealer nella città e zone limitrofe
- Chi tratta premium? Chi importa?
- Gap: cosa manca? Dove si inserisce ARGOS?

## REGOLE
- OGNI dato deve avere la FONTE specificata
- Se un dato NON è verificabile, scrivere "NON VERIFICATO"
- MAI inventare dati — meglio "non trovato" che dato falso
- Usare resilient_fetcher.py per fetch anti-bot
- Rate limiting: 5-10s tra richieste
- Salvare risultati in research/s94_intel_{dealer_name}.md

## ASSET ESISTENTI
```
tools/dealer_discovery/discovery_engine.py  ← scraper Subito.it
tools/scrapers/resilient_fetcher.py         ← fetch anti-bot multi-backend
tools/dealer_crm.py                         ← CRM SQLite
research/s94_top6_dealer_profiles.md        ← profili già fatti
research/s94_intel_reale_enzo_dream.md      ← intel Enzo Car + Dream Car
research/s94_dinamiche_territorio_foggiano.md ← territorio Foggia
```
