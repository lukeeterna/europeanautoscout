# S88 — Pipeline E2E Reale + TIER1 + Schema DB + RDW/Car-Pass

## Contesto — LEGGI PRIMA DI TUTTO

S87 e' stata MASSIVA. Il sistema ora e' autonomo:
- Agente Luca Ferretti risponde in auto (Haiku + KB 13 sezioni)
- VIN Verification integrata: NHTSA vPIC + freevindecoder + recalls (€0)
- 3 dealer TIER0 contattati, Day 3 follow-up automatico schedulato 30/03
- Health monitor, cap per-dealer, fee validator, business hours fixati

Ma il lavoro NON e' finito. I pezzi ci sono, mancano i COLLEGAMENTI.

## Cosa funziona (NON toccare)
```
wa-intelligence/wa-daemon.js         ← autonomo, scheduler Day3/7, health monitor
wa-intelligence/response-analyzer.py ← system prompt riscritto, KB injection, fee fix
wa-intelligence/argos_knowledge_base.md ← 13 sezioni, 293 righe, dati reali
src/cove/vin_verification.py         ← NHTSA + freevindecoder + recalls, testato E2E
src/cove/cove_engine_v4.py           ← NON MODIFICARE
```

## Priorita' S88 — in ordine

### 1. Schema DuckDB — aggiungere colonne VIN verification (CRITICO)
Il detail_enricher_v2 salva vin_verified/vin_verification_data/recall_count nel DB ma le colonne NON ESISTONO ancora in vehicle_listings. Servono:
```sql
ALTER TABLE vehicle_listings ADD COLUMN vin_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE vehicle_listings ADD COLUMN vin_verification_data VARCHAR;
ALTER TABLE vehicle_listings ADD COLUMN recall_count INTEGER DEFAULT 0;
```
DB path: `src/cove/data/cove_tracker.duckdb`

### 2. Test E2E pipeline COMPLETA con veicolo REALE
Prendere uno dei veicoli trovati in S87 (Q5 €25.730 o X3 M Sport €31.500):
- Scrape detail page → extract VIN → VIN verification → enrich → ARGOS GRADE → PDF
- Verificare che il PDF abbia la sezione "VERIFICA ARGOS 100 PUNTI" con dati REALI
- Questo PDF sara' il primo dossier DA MANDARE a un dealer

### 3. Monitorare Day 3 follow-up (30/03)
- Verificare che lo scheduler mandi i messaggi ai 3 TIER0
- Se non funziona: debug e fix
- Se funziona: documentare e procedere con TIER1

### 4. TIER1 outreach
Stesso approccio S87 (presentarsi + esigenze), calibrato per archetipo:
- BD Auto (CE), Top Cars (CS), AutoQuarta (LE), Loforese (TA)
- Autovanny (SA) e FC Luxury (SA) — attenzione, sono piu' grandi
- Aggiungere alla tabella conversations del daemon PRIMA di contattare

### 5. RDW open data NL — integrare in vin_verification.py
API REST gratuita olandese: km/revisioni per targa olandese.
- Endpoint: https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken=XX-999-X
- Costo: €0, no auth
- Utile per auto dall'Olanda (conferma km con fonte governativa)
- Aggiungere come tool opzionale nel VinVerifier

### 6. Car-Pass BE — documentare flusso
Il venditore belga e' OBBLIGATO a fornire il Car-Pass (storico km).
- Non serve API: basta richiederlo nell'email al venditore
- Aggiornare seller_contact.py per richiederlo automaticamente se source = BE

### 7. DAT consumer via Playwright (se tempo)
DAT Orientierungswert e' gratis ma richiede browser (React wizard).
- Gia' abbiamo Playwright MCP
- Serve: navigare wizard → inserire make/model/year/km → estrarre prezzo
- Questo sarebbe il sanity check prezzi definitivo

### 8. Baileys migration (backlog)
Post primo ciclo Day 1-7. WebSocket diretto, zero browser.

## Veicoli pronti per dossier
Dallo scrape S87 (AutoScout24, 27/03):
1. **Audi Q5 35 TDI Advanced** — €25.730, 29.922 km, Stoccarda — margine ~€5.700-7.700
2. **BMW X3 xDrive20d M Sport 2023** — €31.500, 45.863 km, Olanda — margine ~€2.900-4.900
3. **Audi Q5 35 TDI S-tronic** — €28.780, 55.711 km, Wendlingen — margine ~€3.600-5.600

## Infra
```
iMac: ssh gianlucadistasi@192.168.1.2
PM2 restart: source ~/.zshrc && pm2 restart argos-wa-daemon
Cove path iMac: /Users/gianlucadistasi/Documents/app-antigravity-auto/python/cove/
DB DuckDB: src/cove/data/cove_tracker.duckdb
DB daemon: /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite
Business hours: 8-20 lun-sab (time-context.js)
edge-tts: ~/Library/Python/3.9/bin/edge-tts (path assoluto nel daemon)
```

## Regole
- L'agente si chiama LUCA FERRETTI, mai "AMBRA"
- Day 1 = presentarsi + esigenze (MAI veicolo a freddo finche' zero track record)
- Ordine: leggi esistente → ricerca → implementa (B→A→C)
- TUTTO a costo €0 — se serve un dato, scrappalo o trovalo free
- cove_engine_v4.py NON MODIFICARE
- Dati nel dossier devono essere REALI e VERIFICABILI
