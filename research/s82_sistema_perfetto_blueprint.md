# ARGOS SISTEMA PERFETTO — BLUEPRINT ARCHITETTURALE
## Da "intelligence engine" a "deal machine"

---

## IL PROBLEMA IN UNA FRASE

Il sistema oggi TROVA le opportunita ma NON le CONFEZIONA.
Un dealer vuole: foto reali, dati completi, margine che regge, PDF che puo mostrare al cliente.
Oggi gli diamo: una tabella con numeri.

---

## FLUSSO TARGET (come deve funzionare)

```
INPUT: "BMW X3 2022, sotto 50.000 km"
                    |
    [1. HARVEST]    |  Scraper raccoglie da 28+ portali
                    |  Output: 200-500 listing grezzi
                    v
    [2. STORE]      |  Ogni listing salvato COMPLETO nel DB
                    |  listing_url, image_urls, description, equipment, seller
                    v
    [3. SCORE]      |  CoVe Engine (gia funziona)
                    |  Output: PROCEED / VIN_CHECK / SKIP con confidence
                    v
    [4. ENRICH]     |  Detail page scraping per i soli PROCEED
                    |  Scarica: foto HD, VIN, allestimento, descrizione
                    v
    [5. SELECT]     |  Filtro dealer-ready:
                    |  - Margine netto dealer >= EUR 3.000 (dopo fee ARGOS)
                    |  - Almeno 3 foto HD disponibili
                    |  - Dati completi (anno, km, prezzo verificati)
                    v
    [6. PACKAGE]    |  PDF Enterprise con foto reali
                    |  Watermark dealer, zero source, brand ARGOS
                    v
    [7. DELIVER]    |  WA + PDF allegato (o email)
                    |  Messaggio calibrato per archetipo
                    v
    [8. TRACK]      |  CRM aggiorna stato
                    |  Sequenza Day 1-30 parte automatica
```

---

## MODULO 1 — HARVEST (Scraper)

### Stato attuale
- 28 portali configurati, generic_scraper funziona
- Estrae: make, model, year, km, price, fuel, transmission, image_urls, listing_url
- 8 layer parsing (JSON-LD, __NEXT_DATA__, regex, etc.)

### Cosa manca
- I dati estratti (image_urls, listing_url) NON vengono salvati nel DB
- Non estrae: VIN, description, equipment, seller_name, seller_type

### Fix necessario
```
generic_scraper.py → gia estrae listing_url e image_urls nel Listing object
Il problema e che scraper_cove_pipeline NON li persiste nel DB
```

### Priorita: ALTA — senza listing_url non possiamo tornare all'annuncio

---

## MODULO 2 — STORE (Schema DB)

### Stato attuale — Schema cove_results
```sql
listing_id, make, model, year, km, price, vin, source,
status, confidence, uncertainty, fraud_overall,
market_price, price_delta, recommendation, actual_outcome, analyzed_at
```

### Schema TARGET — vehicle_listings (NUOVA TABELLA)
```sql
CREATE TABLE vehicle_listings (
    -- Identita
    listing_id      VARCHAR PRIMARY KEY,
    source_portal   VARCHAR NOT NULL,      -- "autoscout24_de", "finn_no"
    listing_url     VARCHAR,               -- URL annuncio originale

    -- Veicolo base
    make            VARCHAR NOT NULL,
    model           VARCHAR NOT NULL,
    variant         VARCHAR,               -- "xDrive20d", "M Sport"
    year            INTEGER,
    km              INTEGER,
    price_eur       DOUBLE NOT NULL,
    currency_orig   VARCHAR,               -- "NOK", "SEK", "PLN"
    price_orig      DOUBLE,                -- prezzo in valuta originale

    -- Dettagli tecnici
    fuel_type       VARCHAR,
    transmission    VARCHAR,
    power_hp        INTEGER,
    color           VARCHAR,
    doors           INTEGER,

    -- VIN e storia
    vin             VARCHAR,
    first_registration VARCHAR,            -- "03/2022"
    previous_owners INTEGER,

    -- Contenuto ricco
    description     TEXT,                  -- descrizione venditore
    equipment       TEXT,                  -- lista optional (JSON array)
    image_urls      TEXT,                  -- JSON array di URL immagini
    image_count     INTEGER DEFAULT 0,

    -- Venditore
    seller_name     VARCHAR,
    seller_type     VARCHAR,               -- "dealer" | "private"
    seller_location VARCHAR,               -- citta/regione
    country         VARCHAR,               -- "DE", "NL", "NO"

    -- Metadata
    scraped_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    detail_enriched BOOLEAN DEFAULT FALSE, -- detail page visitata?
    images_cached   BOOLEAN DEFAULT FALSE, -- foto scaricate in locale?

    -- Status pipeline
    cove_scored     BOOLEAN DEFAULT FALSE,
    cove_result_id  VARCHAR,               -- FK a cove_results
    dealer_ready    BOOLEAN DEFAULT FALSE  -- passato tutti i filtri?
);
```

### Schema TARGET — vehicle_images (NUOVA TABELLA)
```sql
CREATE TABLE vehicle_images (
    listing_id      VARCHAR NOT NULL,
    image_index     INTEGER NOT NULL,      -- 0, 1, 2, ...
    url_original    VARCHAR NOT NULL,      -- URL thumbnail
    url_hd          VARCHAR,               -- URL HD (dopo upgrade CDN)
    local_path      VARCHAR,               -- path locale cached
    watermarked_path VARCHAR,              -- path con watermark ARGOS
    width           INTEGER,
    height          INTEGER,
    downloaded_at   TIMESTAMP,
    PRIMARY KEY (listing_id, image_index)
);
```

### Perche due tabelle
- vehicle_listings: dati strutturati, query veloci per filtri
- vehicle_images: dati binari pesanti, gestiti separatamente
- cove_results: resta com'e (scoring puro, non tocchiamo)

### Priorita: CRITICA — e la fondazione di tutto

---

## MODULO 3 — SCORE (CoVe Engine)

### Stato attuale: FUNZIONA
- Bayesian scoring, fraud detection, 4 VQ isolati
- Scrive in cove_results
- NON TOCCARE (regola CLAUDE.md)

### Unica modifica necessaria
```
Dopo scoring, aggiornare vehicle_listings:
  SET cove_scored = TRUE, cove_result_id = listing_id
```

### Priorita: BASSA — funziona, serve solo il collegamento

---

## MODULO 4 — ENRICH (Detail Page Scraping)

### Stato attuale
- detail_enricher.py esiste ma fa SOLO year/km mancanti
- image_downloader.py fa SOLO URL upgrade (non scarica)

### Target: DetailEnricherV2
```python
class DetailEnricherV2:
    """Arricchisce listing PROCEED con dati dalla detail page"""

    def enrich(self, listing_id: str) -> EnrichedData:
        """
        1. Legge listing_url da vehicle_listings
        2. Fetch detail page (ResilientFetcher)
        3. Estrae:
           - VIN (da JSON-LD, meta tags, testo pagina)
           - Equipment/optional (lista strutturata)
           - Description (testo venditore)
           - Seller info (nome, tipo, location)
           - Image URLs HD (tutti, non solo primi 3)
           - First registration date
           - Previous owners count
           - Color
           - Power HP
        4. Aggiorna vehicle_listings con dati arricchiti
        5. Scarica immagini HD (prime 6)
        6. Applica watermark ARGOS
        7. Salva in vehicle_images
        8. SET detail_enriched = TRUE, images_cached = TRUE
        """
```

### Strategie estrazione per campo

**VIN** (nuovo):
```
Layer 1: JSON-LD → vehicle.vehicleIdentificationNumber
Layer 2: Meta tags → og:vin, data-vin attribute
Layer 3: Regex → pattern [A-HJ-NPR-Z0-9]{17} nel body
Layer 4: Structured data → class="vin", id="vin-number"
Nota: molti portali lo nascondono — non bloccante se manca
```

**Equipment** (nuovo):
```
Layer 1: JSON-LD → vehicle.vehicleSpecialUsage, additionalProperty[]
Layer 2: HTML → lista con class="features", "equipment", "options"
Layer 3: Regex → pattern "Optional:", "Ausstattung:", "Uitrusting:"
Output: JSON array ["LED Matrix", "Navi Pro", "Pelle Vernasca", ...]
```

**Immagini HD** (upgrade da image_downloader esistente):
```
1. Legge image_urls da listing
2. Applica regole CDN upgrade (gia in image_downloader.py)
3. Scarica prime 6 immagini in locale
4. Applica watermark ARGOS semi-trasparente
5. Salva in /data/images/{listing_id}/
6. Registra in vehicle_images
```

### Quando arricchire
- SOLO listing con recommendation = PROCEED
- SOLO listing con confidence >= 0.75
- SOLO listing con margine stimato >= EUR 3.000
- Questo riduce il volume da centinaia a 10-30 listing da arricchire

### Priorita: ALTA — senza questo non abbiamo foto ne dati completi

---

## MODULO 5 — SELECT (Filtro Dealer-Ready)

### Criteri per passare a "dealer_ready = TRUE"

```python
def is_dealer_ready(listing) -> bool:
    """Un veicolo e dealer-ready quando il dealer puo agire subito"""

    checks = [
        # Dati base completi
        listing.year > 0,
        listing.km > 0,
        listing.price_eur > 0,
        listing.fuel_type is not None,

        # CoVe superato
        listing.cove_scored == True,
        listing.cove_confidence >= 0.75,
        listing.cove_fraud == 'CLEAN',

        # Margine sufficiente
        listing.net_dealer_margin >= 3000,  # DOPO fee ARGOS

        # Contenuto disponibile
        listing.image_count >= 3,           # almeno 3 foto
        listing.images_cached == True,      # foto scaricate
        listing.detail_enriched == True,    # detail page visitata

        # Annuncio ancora attivo (< 7 giorni)
        listing.scraped_at > now() - 7 days,
    ]

    return all(checks)
```

### Formula margine netto dealer
```
margine_netto_dealer = prezzo_mercato_IT
                     - prezzo_acquisto_EU
                     - trasporto (stima per paese)
                     - immatricolazione (EUR 430 fisso)
                     - fee_ARGOS (EUR 900 media)

SOGLIA MINIMA: EUR 3.000 netti per il dealer
Sotto questa soglia, non proponiamo il veicolo.
```

### Stima trasporto per paese (tabella reference)
```
DE → IT Sud:  EUR 700-900    (~1.500-1.900 km)
NL → IT Sud:  EUR 800-1.000  (~1.800-2.100 km)
BE → IT Sud:  EUR 750-950    (~1.700-2.000 km)
AT → IT Sud:  EUR 600-800    (~1.200-1.500 km)
FR → IT Sud:  EUR 700-900    (~1.400-1.800 km)
NO → IT Sud:  EUR 1.200-1.500 (~3.000-3.500 km)
SE → IT Sud:  EUR 1.100-1.400 (~2.800-3.200 km)
PL → IT Sud:  EUR 800-1.000  (~1.800-2.100 km)
```

### Priorita: MEDIA — logica semplice, dipende dai moduli precedenti

---

## MODULO 6 — PACKAGE (PDF Enterprise)

### Stato attuale: FUNZIONA (appena redesignato)
- Logo ARGOS, badge APPROVED, palette nero/oro
- Layout a due colonne, tabelle pulite
- Zero source, watermark dealer

### Upgrade necessario
```
1. Inserire FOTO REALI del veicolo (da vehicle_images)
   - 1 foto grande (hero) + 2-3 foto piccole (gallery)
   - Watermark ARGOS gia applicato

2. Inserire ALLESTIMENTO reale (da vehicle_listings.equipment)
   - Lista optional in formato leggibile
   - Evidenziare optional premium (LED Matrix, HUD, pelle, etc.)

3. Margine REALE calcolato con transport_estimator
   - Non piu stima fissa EUR 700
   - Calcolo specifico per paese → citta dealer

4. Sezione "Prossimi Passi"
   - "Confermi interesse? Blocchiamo il veicolo in 24h"
   - "Trasporto 10-14 gg, pratiche incluse"
   - "Paga SOLO a veicolo consegnato"
```

### Priorita: MEDIA — il generatore c'e, serve collegargli i dati

---

## MODULO 7 — DELIVER (Invio)

### Stato attuale
- WA daemon su iMac:9191 (quando WA funziona)
- Template messaggi per archetipo (s73_messaging_v2.md)

### Target
```
1. Invio WA con PDF allegato
   POST /send-media {number, file_path, caption}

2. Fallback email se WA non disponibile
   ferretti.argosautomotive@gmail.com → dealer email

3. Messaggio auto-generato da:
   - Archetipo dealer (NARCISO/RAGIONIERE/TECNICO/etc.)
   - Dati veicolo reali
   - Margine in EUR netti
```

### Priorita: BASSA — funziona, dipende da WA availability

---

## MODULO 8 — TRACK (CRM)

### Stato attuale: FUNZIONA
- dealer_network.sqlite con stato dealer
- Sequencer Day 1-30
- Dashboard iMac:8080

### Upgrade necessario
```
Collegare vehicle_assignments:
- Quale veicolo proposto a quale dealer
- Stato: PROPOSED → INTERESTED → NEGOTIATING → DEAL_CLOSED / REJECTED
- Feedback loop: actual_outcome in cove_results per calibrazione
```

### Priorita: BASSA — funziona, il feedback loop serve dopo i primi deal

---

## ORDINE DI IMPLEMENTAZIONE

```
SESSIONE 1 (S83): Schema DB + Store
  - Creare vehicle_listings e vehicle_images in DuckDB
  - Modificare scraper_cove_pipeline per salvare listing_url e image_urls
  - Test: run pipeline → verificare che URL e immagini siano nel DB

SESSIONE 2 (S84): Enrich V2
  - DetailEnricherV2: estrazione VIN, equipment, description, images HD
  - Image downloader: scarica e cacha foto con watermark
  - Test: prendere 5 listing PROCEED → arricchire → verificare foto salvate

SESSIONE 3 (S85): Select + Package
  - Filtro dealer_ready con soglia margine EUR 3.000
  - Collegare PDF generator a vehicle_images per foto reali
  - Test: generare PDF con foto reali per un veicolo dealer_ready

SESSIONE 4 (S86): Deliver + Track
  - Collegare PDF → WA send con allegato
  - Vehicle assignment tracking nel CRM
  - Test: E2E — scrape → score → enrich → PDF → send → CRM update
```

---

## METRICHE DI SUCCESSO

```
Il sistema e "perfetto" quando:

1. TEMPO: da "cerco BMW X3" a "PDF con foto pronto" < 2 ore
2. QUALITA: ogni PDF ha almeno 3 foto HD reali del veicolo
3. MARGINE: ogni veicolo proposto ha margine dealer >= EUR 3.000
4. COMPLETEZZA: anno, km, prezzo, fuel, transmission sempre presenti
5. ZERO LEAK: nessun URL portale, nessun riferimento tech nel PDF
6. DEALER TEST: "questa informazione non la trovo da nessun'altra parte" = SI
```

---

## NOTA SUL MARGINE

```
Il veicolo BMW X3 2022 a EUR 34.140 con margine EUR 1.818 NON sarebbe mai
arrivato al dealer con il filtro dealer_ready attivo (soglia EUR 3.000).

Il sistema perfetto lo avrebbe scartato automaticamente e proposto invece
la BMW X3 2022 dalla Norvegia a EUR 30.951 con margine netto ~EUR 4.300.

Questo e il valore del filtro: il dealer riceve SOLO veicoli su cui guadagna.
```
