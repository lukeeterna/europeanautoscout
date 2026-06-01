# S69 — API e Fonti Dati REALI per Prezzi Auto Usate EU

**Data**: 2026-03-20
**Obiettivo**: Censimento verificato di tutte le API e fonti dati disponibili per prezzi di mercato auto usate in Europa
**Metodo**: Web research live + verifica diretta pagine pricing + incrocio con integrazione CoVe esistente

---

## SOMMARIO EXECUTIVE

| Categoria | Fonti trovate | Usabili ARGOS (<100 EUR/mese) | Gia' integrate |
|-----------|--------------|-------------------------------|----------------|
| API gratuite | 6 | 4 | 2 (auto.dev, Vincario FREE) |
| API pagamento <100 EUR | 5 | 3 | 0 |
| Dataset pubblici/open | 5 | 5 | 0 |
| Fonti alternative | 6 | 3 | 0 |
| **Scraper nostri (gia' operativi)** | **22 portali** | **22** | **22** |

**VERDETTO**: La fonte piu' affidabile e gratuita per ARGOS sono i **nostri scraper** (22 portali E2E in 15 paesi). Le API commerciali per valuation EU sono tutte enterprise (>500 EUR/mese). Le API gratuite coprono solo specs/VIN, NON prezzi di mercato EU.

---

## 1. API GRATUITE

### 1.1 auto.dev (GIA' INTEGRATA in CoVe)

| Campo | Valore |
|-------|--------|
| **URL** | https://www.auto.dev |
| **Pricing** | Starter FREE: 1.000 call/mese, poi $0.002/call listings |
| **Rate limit** | 5 req/sec (Starter), 10 (Growth $299/mo), 50 (Scale $599/mo) |
| **Coverage** | **SOLO USA** — listing da dealer fisici e online US |
| **Accuracy EU** | **ZERO** — non copre Europa |
| **Formato** | REST JSON |
| **Integrazione ARGOS** | `cove_engine_v4.py` riga 91-93, `MarketPriceFetcher` |

**PROBLEMA CRITICO**: auto.dev copre SOLO il mercato USA. I prezzi che restituisce per BMW/Mercedes NON sono riferimenti validi per il mercato EU. La nostra integrazione attuale in CoVe usa questi dati come "market_price_ref" ma sono fuorvianti per veicoli EU.

**AZIONE**: Sostituire auto.dev con dati dai nostri scraper EU come fonte primaria per `MarketPriceFetcher`.

---

### 1.2 Vincario FREE (GIA' INTEGRATA in CoVe)

| Campo | Valore |
|-------|--------|
| **URL** | https://vincario.com |
| **Free tier** | 3 report/mese + 20 lookup API per test |
| **VIN Decode** | Da 100 lookup: 0.49 EUR/req; 1.000 lookup: 0.249 EUR/req |
| **Market Value** | Da 100 lookup: 1.99 EUR/req; 1.000 lookup: 0.999 EUR/req |
| **Stolen Check** | Da 100 lookup: 1.99 EUR/req |
| **Coverage** | EU + internazionale, ML-based decode |
| **Formato** | REST JSON |
| **Integrazione ARGOS** | `cove_engine_v4.py` riga 38, `VincarioFreeClient` — solo balance check |

**NOTA**: Il tier Market Value a 100 lookup/mese = ~200 EUR/mese. Troppo caro per volume ARGOS attuale. I 3 report free sono sufficienti per test ma non per produzione.

**Piano Vincario ragionevole**: 100 VIN Decode/mese = 49 EUR/mese. Utile per validazione VIN, NON per prezzi di mercato.

---

### 1.3 NHTSA vPIC (USA ONLY — gratuita)

| Campo | Valore |
|-------|--------|
| **URL** | https://vpic.nhtsa.dot.gov/api/ |
| **Costo** | 100% gratuita, no registrazione, no limiti |
| **Coverage** | **SOLO USA** — veicoli venduti/importati negli Stati Uniti |
| **Dati** | VIN decode: make, model, year, body, engine, safety |
| **NO prezzi** | Non fornisce valutazioni o prezzi |

**Utilita' ARGOS**: ZERO per prezzi. Potenzialmente utile per decode VIN di veicoli US-spec importati in EU (raro nel nostro segmento).

---

### 1.4 RDW Open Data (Olanda — gratuita)

| Campo | Valore |
|-------|--------|
| **URL** | https://opendata.rdw.nl/ |
| **Costo** | 100% gratuito, no API key necessaria |
| **API** | Socrata SODA API |
| **Dati** | Registrazioni veicoli NL: specs tecniche, emissioni, prima immatricolazione, colore, porte, peso |
| **NO prezzi** | NON include prezzi di vendita o valutazioni |
| **Volume** | Milioni di record (tutti i veicoli targati NL) |

**Utilita' ARGOS**: Verifica specs tecniche e prima immatricolazione per veicoli NL. Utile come cross-check per listing da Marktplaats/AutoTrack. NO prezzi.

---

### 1.5 KBA Open Data (Germania)

| Campo | Valore |
|-------|--------|
| **URL** | https://www.kba.de/DE/Service/OpenData/opendata_node.html |
| **Costo** | Gratuito (download), no API REST pubblica diretta |
| **Dati** | Immatricolazioni per marca/modello, CoC data, dati tipo veicolo |
| **NO prezzi** | Statistiche aggregate, NON prezzi singoli veicoli |
| **Formato** | Download file (non REST API) |

**Utilita' ARGOS**: Statistiche macro su volumi immatricolazione DE (utile per pitch: "In DE sono state immatricolate 120.000 BMW Serie 3 nel 2024"). NO prezzi.

---

### 1.6 License Plate Lookup Vincario (gratuita)

| Campo | Valore |
|-------|--------|
| **URL** | https://vincario.com (endpoint targa) |
| **Costo** | Completamente gratuito, nessun limite |
| **Dati** | Lookup targa → VIN (coverage limitata, non tutti i paesi) |

**Utilita' ARGOS**: Marginale. Potrebbe servire per convertire targa → VIN su veicoli specifici.

---

## 2. API A PAGAMENTO ACCESSIBILI (<100 EUR/mese)

### 2.1 Vincario VIN Decode (PAID)

| Campo | Valore |
|-------|--------|
| **URL** | https://vincario.com/pricing/ |
| **100 lookup/mese** | 49 EUR/mese (0.49 EUR/req) |
| **500 lookup/mese** | 149 EUR/mese (0.298 EUR/req) |
| **Rate limit** | 60 VIN/minuto |
| **Coverage** | EU completa, 120+ parametri decoded |
| **Accuracy** | Alta per VIN decode; ML-trained su database nazionali |

**Verdetto ARGOS**: CONSIGLIATO a 49 EUR/mese (100 lookup). Sufficiente per fase iniziale: ~3-4 veicoli/giorno da validare via VIN.

---

### 2.2 Vincario Market Value (PAID)

| Campo | Valore |
|-------|--------|
| **100 lookup/mese** | 199 EUR/mese (1.99 EUR/req) |
| **500 lookup/mese** | 599 EUR/mese (1.198 EUR/req) |
| **Dati** | Prezzo stimato basato su VIN structure + make/model/year/transmission/engine |

**Verdetto ARGOS**: TROPPO CARO per fase attuale. A 199 EUR/mese non giustificato quando i nostri scraper coprono 22 portali gratis. Valutare in futuro se serve valuation automatica per PDF dossier.

---

### 2.3 Vindecoder.eu / Vincario (alternativa)

| Campo | Valore |
|-------|--------|
| **URL** | https://vindecoder.eu/api/ |
| **Free** | 20 lookup gratis |
| **200 lookup** | $50/mese |
| **1.000 lookup** | $200/mese |
| **Coverage** | EU + Nord America |

**NOTA**: Vindecoder.eu ora reindirizza a Vincario. Stesso servizio.

---

### 2.4 Zyla Labs — Europe Used Cars Prices Database API

| Campo | Valore |
|-------|--------|
| **URL** | https://zylalabs.com/api-marketplace/data/europe+used+cars+prices+database+api/2324 |
| **Free trial** | 7 giorni, 50 API call |
| **Dati** | Make, model, year, price, mileage — mercato EU |
| **Fonte dati** | NON DICHIARATA (probabilmente scraping aggregato) |
| **Accuracy** | SCONOSCIUTA — nessun benchmark pubblicato |
| **Pricing paid** | Non pubblicato (subscription-based) |

**Verdetto ARGOS**: DA TESTARE con 50 call free. Sospetto sia un wrapper su dati scraped da AutoScout24/Mobile.de — se cosi', i nostri scraper sono superiori.

---

### 2.5 Apify Scrapers (AutoScout24 / Mobile.de)

| Campo | Valore |
|-------|--------|
| **URL** | https://apify.com/3x1t/autoscout24-scraper |
| **Modello** | Pay-per-result OPPURE rental |
| **Costo** | Non pubblicato chiaramente (tipicamente $5-25/1000 risultati su Apify) |
| **Dati** | Listing completi: prezzo, km, specs, dealer, foto |
| **Coverage** | AutoScout24 18 paesi EU; Mobile.de Germania |

**Verdetto ARGOS**: INUTILE — abbiamo gia' i nostri scraper per AutoScout24 (5 paesi) e un parser generico per 22 portali totali. Apify costerebbe di piu' e darebbe meno controllo.

---

## 3. API ENTERPRISE (>100 EUR/mese — fuori budget attuale)

### 3.1 DAT/SilverDAT (Germania — standard de facto)

| Campo | Valore |
|-------|--------|
| **URL** | https://www.datgroup.com/products/silverdat-3/ |
| **Costo** | Da 274 EUR/mese (base, 1 utente, 15 valutazioni) |
| **Coverage** | DE, AT, CZ, FR, GR, IT, RO, SK, ES |
| **Dati** | Valutazione dealer (vendita + acquisto), basata su transazioni reali |
| **Accuracy** | GOLD STANDARD per dealer tedeschi |
| **Contatto API** | joachim.elsaesser@schwacke.de |

**Verdetto ARGOS**: Il piu' autorevole ma FUORI BUDGET (274+ EUR/mese). Da considerare quando ARGOS genera revenue costante. Nota: copre anche IT.

---

### 3.2 Autovista Group / Eurotax

| Campo | Valore |
|-------|--------|
| **URL** | https://autovista.com/product/autovista-api/ |
| **Costo** | Enterprise — contattare sales (stimato 500+ EUR/mese) |
| **Coverage** | Pan-EU (tutti i mercati principali) |
| **Dati** | Valutazione, specs, residual value forecast, depreciation |
| **API** | REST + SOAP (legacy) |

**Verdetto ARGOS**: Standard per leasing/OEM. Completamente fuori portata attuale.

---

### 3.3 Indicata (by Autorola)

| Campo | Valore |
|-------|--------|
| **URL** | https://indicata.com/ |
| **Costo** | Enterprise — contattare sales |
| **Coverage** | 16 paesi EU |
| **Dati** | Market intelligence: pricing trends, supply/demand, stock turn per make/model |
| **Target** | OEM, dealer groups, fleet |

**Verdetto ARGOS**: Interessante come benchmark competitivo ma fuori portata.

---

### 3.4 auto-api.com (AutoScout24 + Mobile.de feeds)

| Campo | Valore |
|-------|--------|
| **URL** | https://auto-api.com/autoscout24 e https://auto-api.com/mobile-de |
| **Costo** | "Contact for pricing" — non pubblicato |
| **Dati** | Feed real-time listing AS24 (18 paesi) + Mobile.de: prezzo, VIN, specs, foto, seller |
| **Latenza** | Nuovi listing entro 60 secondi |
| **SDK** | PHP, Node.js, Python, Go, C#, Java, Ruby, Rust |

**Verdetto ARGOS**: Potenzialmente utile in futuro per feed real-time. Ma i nostri scraper gia' coprono AS24 e il costo e' presumibilmente 200-500+ EUR/mese.

---

### 3.5 Carapis

| Campo | Valore |
|-------|--------|
| **URL** | https://carapis.com/ |
| **Free tier** | Disponibile (limiti non specificati), no carta credito |
| **Portali** | 25+ mercati: Mobile.de, AutoScout24, CarGurus, Encar, Che168, etc. |
| **Dati** | Listing, pricing, specs, seller info, market analytics |
| **Latenza** | <2 sec response |
| **Pricing paid** | Non pubblicato — contact sales |

**Verdetto ARGOS**: DA TESTARE free tier. Se il free tier da' 50-100 call/giorno, potrebbe integrare i nostri scraper per portali che non copriamo (es. Mobile.de).

---

### 3.6 Brego (UK only)

| Campo | Valore |
|-------|--------|
| **URL** | https://brego.io/products/api |
| **Costo** | Contact sales (free trial disponibile) |
| **Coverage** | **SOLO UK** |
| **Dati** | Valutazione, depreciation 96 mesi, AI-powered |

**Verdetto ARGOS**: INUTILE — solo UK, noi operiamo EU continentale.

---

## 4. DATASET PUBBLICI / OPEN

### 4.1 AUTO1 Group Price Index (GRATUITO)

| Campo | Valore |
|-------|--------|
| **URL** | https://www.auto1-group.com/index/ |
| **Costo** | GRATUITO — download mensile |
| **Dati** | Indice prezzi wholesale EU, base gennaio 2015 = 100 |
| **Granularita'** | Per classi veicolo, fuel type, km range (NON per singolo modello) |
| **Fonte** | 5.8 milioni di transazioni wholesale AUTO1 |
| **Aggiornamento** | Mensile (ultimo: febbraio 2026) |

**Utilita' ARGOS**: ECCELLENTE per pitch dealer ("I prezzi wholesale EU sono calati dell'1.3% nel Q3 2025 — fonte AUTO1 su 5.8M transazioni"). NON utile per pricing singolo veicolo.

---

### 4.2 Kaggle — Used Car Database in Europe

| Campo | Valore |
|-------|--------|
| **URL** | https://www.kaggle.com/datasets/nestorwinamo/used-car-database-in-europe |
| **Dimensione** | 92.5 MB |
| **Campi** | Maker, model, mileage, year, engine, body, color, transmission, fuel, price EUR |
| **Data** | Ultimo aggiornamento marzo 2023 |
| **Paesi** | "Europa" — non specificati singolarmente |
| **Download** | 187 (basso engagement) |

**Utilita' ARGOS**: DATATO (2023). Potenzialmente utile per training modello ML di stima prezzo, ma i prezzi 2023 non sono reference validi per 2026.

---

### 4.3 Kaggle — Germany Used Cars Dataset 2023

| Campo | Valore |
|-------|--------|
| **URL** | https://www.kaggle.com/datasets/wspirat/germany-used-cars-dataset-2023 |
| **Focus** | Auto usate Germania |
| **Data** | 2023 |

**Utilita' ARGOS**: Stessa limitazione — datato. Utile solo per analisi storica o training ML.

---

### 4.4 ADAC Gebrauchtwagenpreise (Germania — gratuito)

| Campo | Valore |
|-------|--------|
| **URL** | https://www.adac.de/rund-ums-fahrzeug/auto-kaufen-verkaufen/gebrauchtwagenkauf/gebrauchtwagenpreise/ |
| **Costo** | GRATUITO |
| **Coverage** | Germania — veicoli ultimi 10 anni |
| **Dati** | Valutazione base (meno dettagliata di Schwacke) |
| **Formato** | Web — NO API |
| **Scraping** | Possibile ma non automatizzato |

**Utilita' ARGOS**: Buono come quick-check manuale per singolo veicolo DE. Non automatizzabile facilmente. Un articolo Medium documenta scraping ADAC per analisi prezzi (https://kirillstrelkov.medium.com/analysis-of-used-car-price-using-adac-c793ec4890e9).

---

### 4.5 auto-data.net (Specs tecniche — NO prezzi)

| Campo | Valore |
|-------|--------|
| **URL** | https://api.auto-data.net/ |
| **Database** | 55.000+ specs, 3.500 modelli, 10.000+ generazioni |
| **Coverage EU** | >50% del database e' veicoli europei |
| **Lingue** | 14 (incluso IT, DE, FR, ES, PL, RO) |
| **Costo** | Custom quote — modulare (paghi solo categorie necessarie) |
| **Dati** | 120+ parametri tecnici. **NO PREZZI** |

**Utilita' ARGOS**: Potenzialmente utile per arricchire dossier con specs tecniche (consumo, emissioni, dimensioni). Ma non per pricing.

---

## 5. FONTI ALTERNATIVE / CREATIVE

### 5.1 I NOSTRI SCRAPER (FONTE PRIMARIA ARGOS)

| Campo | Valore |
|-------|--------|
| **Portali E2E** | 22 portali in 15 paesi |
| **Costo** | EUR 0 (infrastruttura propria) |
| **Dati** | Prezzo reale di vendita, km, anno, specs, seller, link, foto |
| **Accuracy** | MASSIMA — sono i prezzi EFFETTIVI pubblicati dai dealer |
| **Aggiornamento** | Real-time (ogni esecuzione scraper) |
| **Formato** | JSON standardizzato via `GenericClassifiedScraper` |

**QUESTA E' LA FONTE PIU' PREZIOSA DI ARGOS**. Nessuna API commerciale batte 22 portali in 15 paesi con dati real-time a costo zero.

---

### 5.2 AUTO1 Group — Wholesale Transaction Data (accesso dealer)

| Campo | Valore |
|-------|--------|
| **URL** | https://www.auto1.com/en/home/sell |
| **Accesso** | Solo dealer registrati (serve P.IVA + ATECO 45.11.01) |
| **Dati** | Prezzi reali wholesale, bid/ask, 30.000+ auto ispezionate |
| **60.000 dealer** | In 30+ paesi |

**Utilita' ARGOS**: Quando avremo P.IVA EU, registrarsi come buyer su AUTO1 darebbe accesso a prezzi wholesale REALI. Benchmark definitivo.

---

### 5.3 carVertical (Report storico veicolo)

| Campo | Valore |
|-------|--------|
| **URL** | https://www.carvertical.com/en/business/api |
| **Consumer** | 29.99 EUR/report |
| **Business API** | >73% sconto (contattare sales — stimato ~8 EUR/report) |
| **Dati** | Damage history, odometer rollback, theft, ownership, price estimate |
| **Coverage** | 45+ paesi, 1.000+ database |

**Utilita' ARGOS**: GIA' referenziato in `fraud_flags.py` per statistiche odometer fraud. API business a ~8 EUR/report potrebbe servire per dossier premium (Tier 3 fee 1.200 EUR). ROI positivo se incluso nel servizio.

---

### 5.4 MyCarSpecs Price Calculator (Germania — gratuito)

| Campo | Valore |
|-------|--------|
| **URL** | https://www.mycarspecs.com/de-eur/car-price-calculator |
| **Costo** | Gratuito |
| **Dati** | Stima prezzo basata su year/make/model/mileage |
| **Coverage** | Germania |

**Utilita' ARGOS**: Quick-check gratuito. Da testare accuracy vs nostri scraper.

---

### 5.5 Orange Book Value (globale)

| Campo | Valore |
|-------|--------|
| **URL** | https://orangebookvalue.com/global-de |
| **Costo** | Gratuito |
| **Coverage** | Asia, Europa, ANZ |
| **Dati** | Fair market price basato su category/make/model/year/condition/km |

**Utilita' ARGOS**: DA TESTARE per Europa. Se accuracy e' decente, potrebbe essere un quick-check gratuito.

---

### 5.6 TUV Rheinland Online Vehicle Appraisal

| Campo | Valore |
|-------|--------|
| **URL** | https://www.tuv.com/world/en/online-vehicle-appraisal.html |
| **Costo** | Non specificato (probabilmente a pagamento) |
| **Dati** | Valutazione veicolo online |

**Utilita' ARGOS**: Marginale. Brand TUV e' forte per credibilita' ma non per pricing bulk.

---

## 6. MATRICE DECISIONALE ARGOS

### Priorita' IMMEDIATE (S69-S72)

| Priorita' | Azione | Costo | Impatto |
|-----------|--------|-------|---------|
| **P0** | Sostituire auto.dev (US-only) con aggregazione scraper EU in `MarketPriceFetcher` | 0 EUR | CRITICO — fix dato errato |
| **P1** | Testare Zyla Labs free trial (50 call) | 0 EUR | Validare se utile |
| **P2** | Testare Carapis free tier | 0 EUR | Coprire gap Mobile.de |
| **P3** | Integrare AUTO1 Price Index per pitch | 0 EUR | Sales ammunition |
| **P4** | Upgrade Vincario a 100 VIN Decode/mese | 49 EUR/mese | VIN validation produzione |

### Priorita' FUTURE (quando revenue >3K EUR/mese)

| Priorita' | Azione | Costo | Impatto |
|-----------|--------|-------|---------|
| **F1** | DAT/SilverDAT API | 274+ EUR/mese | Gold standard valuation DE/IT |
| **F2** | carVertical Business API | ~8 EUR/report | Dossier premium Tier 3 |
| **F3** | Registrazione AUTO1 come buyer | P.IVA EU necessaria | Prezzi wholesale reali |
| **F4** | auto-api.com per feed real-time AS24/Mobile.de | 200-500 EUR/mese | Listing detection <60 sec |

---

## 7. ARCHITETTURA CONSIGLIATA — MarketPriceFetcher v2

```python
class MarketPriceFetcherV2:
    """
    Sostituisce auto.dev (US-only) con aggregazione multi-source EU.

    Cascata di fonti:
    1. Scraper EU propri (22 portali) → prezzo mediano listing attivi
    2. Vincario Market Value API (se budget disponibile)
    3. ADAC/MyCarSpecs scraping (fallback DE)
    4. auto.dev (SOLO per veicoli US-spec, raro)

    Output: (price_estimate, sigma, source, n_samples)
    """

    def fetch_eu_market_price(self, make, model, year, fuel=None, km=None):
        # Step 1: Query nostro DB scraper results
        # SELECT AVG(price), COUNT(*), STDDEV(price)
        # FROM scraped_listings
        # WHERE make=? AND model=? AND year BETWEEN ?-1 AND ?+1
        # AND scraped_at > NOW() - INTERVAL '7 days'

        # Step 2: Se n_samples >= 10 → sigma basso (0.10-0.15)
        # Step 3: Se n_samples < 10 → Vincario fallback
        # Step 4: Se tutto fallisce → sigma=0.40 [UNKNOWN]
        pass
```

---

## 8. FONTI VERIFICATE

- [auto.dev Pricing](https://www.auto.dev/pricing)
- [Vincario Pricing](https://vincario.com/pricing/)
- [Vincario VIN Decoder API Pricing Comparison](https://vincario.com/blog/vin-decoder-api-pricing/)
- [AutoScout24 Listing Creation API](https://listing-creation.api.autoscout24.com/docs)
- [auto-api.com AutoScout24](https://auto-api.com/autoscout24)
- [auto-api.com Mobile.de](https://auto-api.com/mobile-de)
- [DAT SilverDAT 3](https://www.datgroup.com/products/silverdat-3/)
- [Autovista API](https://autovista.com/product/autovista-api/)
- [Indicata](https://indicata.com/)
- [AUTO1 Group Price Index](https://www.auto1-group.com/index/)
- [RDW Open Data NL](https://opendata.rdw.nl/)
- [KBA Open Data DE](https://www.kba.de/DE/Service/OpenData/opendata_node.html)
- [NHTSA vPIC API](https://vpic.nhtsa.dot.gov/api/)
- [Carapis](https://carapis.com/)
- [Brego API](https://brego.io/products/api)
- [auto-data.net API](https://api.auto-data.net/)
- [carVertical Business API](https://www.carvertical.com/en/business/api)
- [Kaggle EU Used Cars](https://www.kaggle.com/datasets/nestorwinamo/used-car-database-in-europe)
- [ADAC Gebrauchtwagenpreise](https://www.adac.de/rund-ums-fahrzeug/auto-kaufen-verkaufen/gebrauchtwagenkauf/gebrauchtwagenpreise/)
- [Zyla Labs Europe Cars API](https://zylalabs.com/api-marketplace/data/europe+used+cars+prices+database+api/2324)
- [MarketCheck API](https://www.marketcheck.com/apis/pricing/)
- [Apify AutoScout24 Scraper](https://apify.com/3x1t/autoscout24-scraper)
- [Orange Book Value](https://orangebookvalue.com/global-de)
- [MyCarSpecs DE](https://www.mycarspecs.com/de-eur/car-price-calculator)
