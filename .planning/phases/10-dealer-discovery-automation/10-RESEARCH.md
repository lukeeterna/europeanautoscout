# Phase 10: Automazione Identificazione Dealer su Commissione — Research

**Researched:** 2026-03-31
**Domain:** Web scraping, dealer identification, lead generation Italia Sud
**Confidence:** MEDIUM

## Summary

La ricerca copre 5 piattaforme target per identificare automaticamente i piccoli dealer/salonisti che lavorano su commissione nel Sud Italia: Subito.it, AutoScout24.it, Google Maps, PagineGialle.it, e Facebook. L'infrastruttura ARGOS esistente (resilient_fetcher, generic_scraper, portal_profiles, dealer_crm) fornisce una base solida su cui costruire il sistema di discovery.

Il pattern "su commissione" e' identificabile da segnali concreti: pochi annunci (3-15), marche eterogenee, alta rotazione, descrizioni tipo "cerchiamo per voi", foto da cellulare. La pipeline deve scrappare, classificare, e qualificare questi operatori automaticamente, producendo una lista ordinata per fit ARGOS.

**Primary recommendation:** Partire da Subito.it (impresapiu shops + __NEXT_DATA__ parsing) come fonte primaria — e' il portale con la migliore granularita' sul tipo di venditore e la provincia. Seconda fonte: AutoScout24.it/concessionari per cross-reference. Terza: Google Maps per dati di contatto e recensioni.

## Project Constraints (from CLAUDE.md)

- **ZERO COSTI** — tutto deve essere gratuito o gia' pagato. Nessuna API a pagamento (Apify, SerpAPI, Bright Data = NO)
- **Scraper PERSISTENTI** — MAI CSS selectors, SOLO dati strutturati (__NEXT_DATA__, JSON-LD, regex stabili)
- **Enterprise Grade** — nessun limite su approccio, creativita', aggressivita'. Se funziona e costa zero, fallo
- **Usare asset esistenti** — resilient_fetcher.py, generic_scraper.py, dealer_crm.py, dealer_scouting_playbook.py
- **Pipeline completa > componente singolo** — il discovery deve alimentare il CRM e lo scoring
- **MAI credenziali hardcoded** — solo .env
- **Infra**: iMac (ssh 192.168.1.2) + MacBook locale. Python 3.13, Node v22
- **DB**: dealer_network.sqlite (CRM), DuckDB (CoVe)
- **Target**: concessionari family-business Sud Italia, 10-40 auto, premium

## Standard Stack

### Core (gia' esistente — RIUSARE)

| Library | Purpose | Path |
|---------|---------|------|
| resilient_fetcher.py | HTTP multi-backend anti-bot (curl_cffi + cloudscraper + undetected-chromedriver) | tools/scrapers/resilient_fetcher.py |
| generic_scraper.py | Parser configurabile (__NEXT_DATA__, JSON-LD, regex) | tools/scrapers/generic_scraper.py |
| portal_profiles.py | SearchProfile per portale (URL template, encoding, regex) | tools/scrapers/portal_profiles.py |
| dealer_crm.py | CRM SQLite con anagrafica dealer completa | tools/dealer_crm.py |
| dealer_scouting_playbook.py | Scoring dealer (stock fit, premium %, import signal) | tools/dealer_scouting_playbook.py |
| models.py | Dataclass SellerType, Listing | tools/scrapers/models.py |

### Da aggiungere

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| playwright | (gia' installato per sanitizer) | Google Maps scrolling + FB se necessario | Gia' usato nel progetto, anti-detection con stealth |
| duckdb | (gia' installato) | Storage dealer discovery con dedup e analytics | Gia' nel progetto |
| sqlite3 | stdlib | CRM dealer_network.sqlite | Gia' in uso |

### NON usare (costo > 0)

| Servizio | Perche' NO |
|----------|-----------|
| Apify (qualsiasi actor) | Subscription a pagamento |
| SerpAPI | API a pagamento |
| Bright Data | Proxy a pagamento |
| Google Places API | $17/1000 requests dopo free tier |
| Outscraper | Pagamento dopo free tier |
| Carapis | API a pagamento |

## Architecture Patterns

### Struttura progetto consigliata

```
tools/
├── dealer_discovery/
│   ├── __init__.py
│   ├── discovery_engine.py        # Orchestratore principale
│   ├── subito_dealer_scraper.py   # Scraper shop Subito.it
│   ├── as24_dealer_scraper.py     # Scraper concessionari AS24.it
│   ├── google_maps_scraper.py     # Scraper Google Maps (playwright)
│   ├── paginegialle_scraper.py    # Scraper PagineGialle.it
│   ├── commission_classifier.py   # Classificatore "su commissione"
│   ├── dealer_scorer.py           # Scoring fit ARGOS
│   └── config.py                  # Province target, soglie, pattern
├── dealer_crm.py                  # GIA' ESISTENTE — arricchire
└── dealer_scouting_playbook.py    # GIA' ESISTENTE — invocare
```

### Pattern 1: Discovery Pipeline

```
Subito.it shops → Extract dealer list per provincia
                 ↓
AS24.it concessionari → Cross-reference + arricchimento
                 ↓
Google Maps → Contatti + recensioni + rating
                 ↓
Commission Classifier → Analizza pattern stock (eterogeneo? pochi? rotazione?)
                 ↓
Dealer Scorer → Score fit ARGOS (stock, premium %, age, import signal)
                 ↓
dealer_crm.py → Inserisce come NEW + tier calcolato
```

### Pattern 2: Commission Detection Heuristics

```python
# Segnali "su commissione" — score cumulativo
COMMISSION_SIGNALS = {
    "few_listings": (3, 15),        # 3-15 annunci attivi
    "brand_diversity": 4,           # >= 4 marche diverse
    "description_keywords": [       # Keywords nelle descrizioni
        "su richiesta", "cerchiamo", "troviamo",
        "su ordinazione", "a richiesta",
        "ricerchiamo per voi", "il veicolo che cerchi",
        "custom order", "ricerca personalizzata",
    ],
    "photo_quality_low": True,      # Foto cellulare (no studio)
    "high_turnover": 0.5,           # >50% stock cambia in 30gg
    "no_website": True,             # Nessun sito web strutturato
    "social_only": True,            # Solo Facebook/Instagram
}
```

### Anti-Pattern da evitare

- **Scraping aggressivo senza rate limiting**: blocco IP permanente. Usare resilient_fetcher con sleep 8-18s
- **CSS selectors fragili**: Subito/AS24 cambiano HTML spesso. Usare __NEXT_DATA__ JSON o JSON-LD
- **Parsing senza dedup**: stesso dealer su Subito + AS24 + GMaps = 3 record. Dedup su nome normalizzato + provincia
- **Discovery senza scoring**: lista grezza di 500 dealer = inutile. Lo scoring deve produrre top-20 ordinata

## Piattaforme — Analisi Tecnica Dettagliata

### 1. Subito.it — FONTE PRIMARIA

**Confidence: MEDIUM-HIGH**

**URL Patterns verificati:**

| Tipo | URL | Note |
|------|-----|------|
| Listing auto per provincia | `https://www.subito.it/annunci-puglia/vendita/auto/foggia/` | Regione + provincia nell'URL |
| Shop professionista | `https://impresapiu.subito.it/shops/{id}-{slug}` | Es: `/shops/38485-imperauto-foggia` |
| Directory shops | `https://impresapiu.subito.it/shops` | 403 con fetch diretto |
| Ricerca auto | `https://www.subito.it/annunci-italia/vendita/auto/?q={query}` | Con __NEXT_DATA__ |

**Parsing strategy:**

Subito.it usa Next.js con `__NEXT_DATA__` JSON embedded nel HTML. Il path dei dati e':
```python
json_data['props']['pageProps']['initialState']['items']['list']
```

Ogni item contiene:
- `urn` — ID univoco
- `subject` — titolo annuncio
- `geo.town.value` / `geo.city.shortName` — localita'
- `features./price.values[0].key` — prezzo
- Seller info — tipo venditore (privato vs professionista)

**Come distinguere privato da professionista:**
- Su Subito Motori esiste il filtro "privato/azienda" nella UI
- I professionisti hanno lo shop su `impresapiu.subito.it`
- Le pagine shop mostrano: logo, contatti, orari, elenco annunci
- I venditori "Pro" hanno certificazione e negozio virtuale personalizzabile

**Strategia di scraping:**

```python
# 1. Scrappare listings auto per provincia (Sud Italia)
provinces = ["foggia", "cosenza", "caserta", "lecce", "taranto", "salerno", "catanzaro",
             "bari", "avellino", "benevento", "potenza", "crotone", "reggio-calabria"]
regions = {"foggia": "puglia", "cosenza": "calabria", "caserta": "campania", ...}

# URL: https://www.subito.it/annunci-{regione}/vendita/auto/{provincia}/
# 2. Da __NEXT_DATA__ estrarre tutti i seller unici
# 3. Per ogni seller con tipo "azienda": visitare shop page
# 4. Dalla shop page estrarre: num annunci, marche, range prezzo
```

**Anti-bot:**
- Subito.it ha protezione moderata — curl_cffi con impersonate Chrome funziona
- Rate limit: 5-10s tra richieste
- impresapiu.subito.it restituisce 403 su fetch diretto (serve browser reale o cookie session)

**Dealer trovabili per provincia (stima):**
- Province grandi (Bari, Napoli): 50-100 dealer professionisti su Subito
- Province medie (Foggia, Cosenza, Salerno): 20-50 dealer
- Province piccole (Crotone, Potenza): 5-15 dealer
- **Di cui "su commissione" stimati: 20-30%** = 5-15 per provincia media

### 2. AutoScout24.it — CROSS-REFERENCE

**Confidence: MEDIUM**

**URL Patterns:**

| Tipo | URL | Note |
|------|-----|------|
| Directory concessionari | `https://www.autoscout24.it/concessionari/` | Carica dinamicamente con JS |
| Dealer page | `https://www.autoscout24.it/concessionari/{slug}/recensioni` | Con dati dealer |
| Listing con dealer | `https://www.autoscout24.it/lst/{make}?atype=C&cy=I&...` | cy=I per Italia |

**Problema:** La pagina /concessionari/ carica dealer via JavaScript (React app). Serve Playwright per renderizzare.

**Dati estraibili per dealer:**
- Nome dealer, citta', provincia
- Numero auto in stock
- Rating e numero recensioni
- Marche trattate (dal loro inventario)
- Telefono, sito web

**Strategia:**
```python
# AS24 non ha un endpoint diretto per lista dealer per provincia
# Approccio: scrappare listings auto IT per provincia e aggregare per seller
# URL: https://www.autoscout24.it/lst?cy=I&...
# Dalla listing page: estrarre seller_name + seller_url
# Aggregare: {seller_name: count_listings, brands: [...], location: "..."}
# Filtrare: seller con 3-15 listing e brand eterogenei = potenziale commissione
```

**Anti-bot:** Akamai protection. Serve curl_cffi o undetected-chromedriver. Rate limit: 5-10s minimo. Proxy rotation consigliata ma non obbligatoria per volumi bassi.

### 3. Google Maps — CONTATTI E RECENSIONI

**Confidence: MEDIUM**

**Approccio ZERO COSTI:**

Google Maps non ha API gratuita per volume, ma si puo' scrappare con Playwright:

```python
# Query: "autosalone {provincia}" OR "concessionaria {provincia}" OR "auto usate {provincia}"
# Per ogni provincia Sud Italia
queries = [
    "autosalone Foggia",
    "concessionaria auto usate Foggia",
    "salone auto Foggia",
    "vendita auto usate Foggia",
]
# Playwright: apri Google Maps, scrolla risultati, estrai per ogni business:
# - nome, indirizzo, telefono, rating, num_recensioni, sito_web, orari
```

**Tool consigliato:** `HasData/google-maps-scraper` (GitHub, open source) — usa Playwright con stealth mode. Estrae: name, rating, review_count, category, address, phone, website.

**Installazione:**
```bash
pip install selenium pandas playwright playwright-stealth
playwright install
```

**Limiti:** Google blocca dopo ~200-300 query da stesso IP. Serve rotazione IP o batch piccoli distribuiti nel tempo.

**Valore specifico:** Solo Google Maps ha il rating e numero recensioni reale — dati fondamentali per il dealer scoring ARGOS.

### 4. PagineGialle.it — ANAGRAFICA BASE

**Confidence: HIGH**

**API non ufficiale disponibile:** GitHub `chiccomagnus/PGAPI` — wrapper PHP/Python per PagineGialle.

**Endpoint:**
```
/category/[codice_categoria]/place/[citta_o_provincia]
```

**Response JSON:**
```json
{
  "result": [{
    "name": "Auto Srl",
    "place": {"address": "Via...", "locality": "Foggia", "region": "Puglia"},
    "telephone": "0881...",
    "website": "...",
    "category": "Autosaloni"
  }],
  "status": "OK",
  "length": 42
}
```

**Categorie rilevanti:**
- "Autosaloni" — salone auto usate
- "Autoveicoli usati - commercio" — ATECO 45.11
- "Concessionarie auto" — concessionari ufficiali (meno interessante)

**Limite noto:** PagineGialle mostra max 200 risultati per ricerca. Workaround: cercare per singolo comune o CAP.

**Valore:** Copertura completa delle attivita' registrate. Ma NON distingue chi lavora su commissione — serve cross-reference con Subito/AS24.

### 5. Facebook — BASSA PRIORITA'

**Confidence: LOW**

**Stato Graph API 2026:** Facebook NON ha API pubblica per cercare pagine business o Marketplace listings. Il Graph API richiede app review e non supporta ricerca Marketplace.

**Scraping:** Possibile con Playwright ma estremamente fragile (DOM cambia continuamente, A/B testing, class names dinamiche). Facebook blocca aggressivamente.

**Raccomandazione:** NON prioritizzare Facebook. Usare solo come cross-reference manuale per dealer gia' identificati su Subito/AS24 (cercare "{dealer name} {citta}" su Facebook per trovare pagina).

### 6. Camera di Commercio / RegistroImprese.it

**Confidence: MEDIUM**

**ATECO rilevanti:**
- 45.11.01 — Commercio all'ingrosso e al dettaglio di autovetture e autoveicoli leggeri
- 45.11.02 — Intermediari del commercio di autovetture e autoveicoli leggeri (QUESTO E' IL CODICE COMMISSIONE)

**Accesso:**
- registroimprese.it — ricerca gratuita per nome azienda, restituisce ATECO
- Elenchi personalizzati (per ATECO + provincia): costo minimo €5 + €0.02/record
- NON scrappabile gratuitamente in bulk

**Valore:** ATECO 45.11.02 identifica ESATTAMENTE chi lavora come intermediario/commissionario. Ma il costo (anche se basso) e la difficolta' di accesso bulk lo rendono uno strumento di verifica, non di discovery primaria.

**Strategia:** Usare come VERIFICA dopo discovery su Subito/AS24. Per ogni dealer trovato: cercare su registroimprese.it per confermare ATECO.

## Don't Hand-Roll

| Problema | Don't Build | Usa Invece | Perche' |
|----------|-------------|-----------|---------|
| HTTP anti-bot | Nuovo fetcher | resilient_fetcher.py | 4 backend, persistent cache, gia' testato su 28 portali |
| Parser HTML | Parser custom | generic_scraper.py con SearchProfile | __NEXT_DATA__ + JSON-LD + regex, configurabile |
| CRM dealer | Nuovo DB schema | dealer_crm.py | Schema completo con pipeline_status, archetype, scoring |
| Scoring dealer | Nuovo algoritmo | dealer_scouting_playbook.py | Pesi calibrati, 7 dimensioni, soglie ARGOS |
| Google Maps scraping | Selenium custom | HasData/google-maps-scraper | Open source, Playwright stealth, testato |
| Dedup dealer | String matching custom | fuzzywuzzy/thefuzz | Normalizzazione nomi business + Levenshtein |

## Common Pitfalls

### Pitfall 1: Scraping troppo aggressivo = ban IP
**What goes wrong:** Subito/AS24/Google bloccano l'IP dopo troppe richieste veloci
**Why it happens:** Rate limit non rispettato, pattern riconoscibile
**How to avoid:** Sleep 8-18s random tra richieste. Max 100 pagine/sessione. Distribuire su piu' giorni. Usare curl_cffi impersonate.
**Warning signs:** HTTP 403, 429, CAPTCHA page restituita

### Pitfall 2: False positive "su commissione"
**What goes wrong:** Dealer con poco stock classificato come commissionario, ma e' solo piccolo
**Why it happens:** Il solo numero annunci non basta — anche un micro-dealer con 5 BMW e' stock-based
**How to avoid:** Score cumulativo: pochi annunci + marche diverse + keywords + no sito web. Serve >= 3 segnali su 5.
**Warning signs:** Tutti i dealer di una provincia classificati come commissionari

### Pitfall 3: Dati duplicati cross-piattaforma
**What goes wrong:** Stesso dealer su Subito, AS24, Google Maps = 3 record separati
**Why it happens:** Nome scritto diversamente ("Auto Srl" vs "AUTO SRL" vs "Auto S.r.l.")
**How to avoid:** Normalizzazione aggressiva (lowercase, remove "srl/snc/sas", strip spaces) + match su provincia + fuzzy match nome
**Warning signs:** Lista finale con dealer count >> dealer reali

### Pitfall 4: impresapiu.subito.it blocca fetch diretto
**What goes wrong:** Le shop page restituiscono 403 con requests/curl_cffi
**Why it happens:** Protezione anti-bot piu' aggressiva sulla sezione business
**How to avoid:** Usare undetected-chromedriver o Playwright come fallback. Oppure: estrarre dati dealer dalle listing pages standard (non dalle shop page)
**Warning signs:** Tutte le shop page restituiscono 403

### Pitfall 5: Compliance GDPR contatto WA
**What goes wrong:** Dealer si lamenta o segnala a Garante Privacy
**Why it happens:** In Italia, anche contatto B2B richiede base giuridica (non basta "dato pubblico")
**How to avoid:** Contatto personalizzato, NON massivo. Un singolo messaggio business-to-business rilevante al destinatario rientra nel pre-contractual legitimate interest. Mai blast. Mai piu' di 5 nuovi contatti/giorno. Sempre possibilita' di opt-out.
**Warning signs:** Messaggio percepito come spam (generico, non personalizzato)

## Compliance GDPR — Analisi Dettagliata

### Quadro normativo Italia

L'Italia ha un regime PIU' RESTRITTIVO della media EU per il marketing B2B:

1. **Art. 130 Codice Privacy:** richiede consenso anche per comunicazioni a persone giuridiche
2. **Soft opt-in:** consentito SOLO per clienti esistenti, su prodotti/servizi simili
3. **Legitimate interest:** accettato per contatto B2B personalizzato e rilevante, ma non per mass outreach
4. **Dati pubblici da annunci:** il telefono in un annuncio e' pubblicato per essere contattato per QUEL annuncio. Contattare per altro scopo (vendere servizio) e' area grigia.

### Cosa e' sicuro fare

| Azione | Rischio | Note |
|--------|---------|------|
| Scraping dati pubblici (annunci, pagine business) | BASSO | Informazioni pubblicate per essere trovate |
| Un singolo messaggio WA personalizzato, business-relevant | BASSO | Pre-contractual B2B communication |
| Mantenere database di contatti business pubblici | BASSO | Se dati provengono da fonti pubbliche e uso e' B2B |
| Opt-out rispettato immediatamente | OBBLIGATORIO | Qualsiasi "non interessato" = stop immediato |

### Cosa NON fare MAI

| Azione | Rischio | Note |
|--------|---------|------|
| Mass messaging a lista scrappata | ALTO | Spam = sanzione Garante |
| Contattare tramite email nominativa senza consenso | ALTO | Art. 130 — serve consenso per email nominativa |
| Ignorare richiesta di opt-out | CRITICO | Sanzione certa |
| Usare numero privato (non da annuncio) | ALTO | Violazione privacy |

### Raccomandazione ARGOS

Il modello attuale (max 5 nuovi contatti/giorno, messaggio ultra-personalizzato, veicolo reale come gancio) e' CONFORME perche':
- Ogni messaggio e' genuinamente rilevante per il business del dealer
- Non e' percepito come spam ma come proposta commerciale B2B
- Il numero viene da annuncio pubblico (pubblicato per essere contattato)
- Opt-out immediato rispettato
- Volume minimo (non mass outreach)

## Code Examples

### Scraper Subito.it — Dealer Discovery

```python
# Source: Analisi __NEXT_DATA__ Subito.it + morrolinux/subito-it-searcher
import json
import re
from tools.scrapers.resilient_fetcher import fetch_url

PROVINCES_SUD = {
    "foggia": "puglia", "bari": "puglia", "lecce": "puglia", "taranto": "puglia",
    "cosenza": "calabria", "catanzaro": "calabria", "reggio-calabria": "calabria", "crotone": "calabria",
    "caserta": "campania", "salerno": "campania", "avellino": "campania", "benevento": "campania",
    "potenza": "basilicata", "matera": "basilicata",
}

def scrape_subito_dealers(province: str, region: str) -> list[dict]:
    """Scrappa listing auto su Subito per provincia, estrae seller unici."""
    url = f"https://www.subito.it/annunci-{region}/vendita/auto/{province}/"
    html = fetch_url(url)

    # Estrarre __NEXT_DATA__
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not match:
        return []

    data = json.loads(match.group(1))
    items = data.get('props', {}).get('pageProps', {}).get('initialState', {}).get('items', {}).get('list', [])

    # Aggregare per seller
    sellers = {}
    for item in items:
        advertiser = item.get('advertiser', {})
        if advertiser.get('type') == 'company':  # Solo professionisti
            seller_id = advertiser.get('userId', '')
            if seller_id not in sellers:
                sellers[seller_id] = {
                    'name': advertiser.get('name', ''),
                    'shop_url': advertiser.get('shopUrl', ''),
                    'province': province,
                    'region': region,
                    'listings': [],
                    'brands': set(),
                }
            listing_title = item.get('subject', '')
            sellers[seller_id]['listings'].append(listing_title)
            # Estrai marca dal titolo
            for brand in ['BMW', 'Mercedes', 'Audi', 'Fiat', 'Volkswagen', 'Opel', 'Peugeot', 'Renault', 'Toyota']:
                if brand.lower() in listing_title.lower():
                    sellers[seller_id]['brands'].add(brand)

    return list(sellers.values())
```

### Classificatore "Su Commissione"

```python
def classify_commission_dealer(dealer: dict) -> tuple[bool, float, list[str]]:
    """
    Classifica se un dealer lavora su commissione.
    Returns: (is_commission, confidence, signals_found)
    """
    signals = []
    score = 0.0

    n_listings = len(dealer.get('listings', []))
    n_brands = len(dealer.get('brands', set()))

    # Segnale 1: Pochi annunci (3-15)
    if 3 <= n_listings <= 15:
        score += 0.25
        signals.append(f"few_listings={n_listings}")

    # Segnale 2: Marche eterogenee (>= 4 diverse)
    if n_brands >= 4:
        score += 0.25
        signals.append(f"brand_diversity={n_brands}")
    elif n_brands >= 3 and n_listings <= 10:
        score += 0.15
        signals.append(f"brand_moderate_diversity={n_brands}")

    # Segnale 3: Keywords nelle descrizioni
    commission_keywords = [
        "su richiesta", "cerchiamo", "troviamo", "su ordinazione",
        "a richiesta", "ricerchiamo", "il veicolo che cerchi",
        "ricerca personalizzata", "su commissione",
    ]
    descriptions = ' '.join(dealer.get('listings', [])).lower()
    found_kw = [kw for kw in commission_keywords if kw in descriptions]
    if found_kw:
        score += 0.30
        signals.append(f"keywords={found_kw}")

    # Segnale 4: Nessun sito web
    if not dealer.get('website'):
        score += 0.10
        signals.append("no_website")

    # Segnale 5: Solo social (FB/IG ma no sito)
    if dealer.get('facebook') or dealer.get('instagram'):
        if not dealer.get('website'):
            score += 0.10
            signals.append("social_only")

    is_commission = score >= 0.50 and len(signals) >= 3
    return is_commission, min(score, 1.0), signals
```

### Google Maps Scraper (Playwright)

```python
# Source: HasData/google-maps-scraper pattern
from playwright.sync_api import sync_playwright
import time, random

def scrape_google_maps_dealers(query: str, max_results: int = 30) -> list[dict]:
    """Scrappa Google Maps per query tipo 'autosalone Foggia'."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.google.com/maps/search/{query}")
        page.wait_for_selector('[role="feed"]', timeout=10000)

        # Scroll per caricare risultati
        feed = page.query_selector('[role="feed"]')
        for _ in range(max_results // 5):
            feed.evaluate('el => el.scrollTop = el.scrollHeight')
            time.sleep(random.uniform(1.5, 3.0))

        # Estrarre dati da ogni risultato
        items = page.query_selector_all('[role="feed"] > div > div > a')
        for item in items[:max_results]:
            name = item.get_attribute('aria-label') or ''
            href = item.get_attribute('href') or ''
            results.append({'name': name, 'maps_url': href, 'query': query})

        browser.close()
    return results
```

## Pipeline Automatica — Architettura

### Flusso completo

```
FASE 1: DISCOVERY (settimanale)
  Per ogni provincia target:
    1. Subito.it → lista dealer professionisti + num annunci + marche
    2. AS24.it → lista dealer + stock size (aggregando listing)
    3. Google Maps → "autosalone {prov}" → nome, telefono, rating, recensioni
    4. PagineGialle → "autosaloni {prov}" → nome, telefono, indirizzo

FASE 2: MERGE + DEDUP
    5. Normalizzare nomi (lowercase, strip SRL/SAS/SNC, fuzzy match)
    6. Merge per nome+provincia: unificare dati da tutte le fonti
    7. Arricchire: telefono da PG/GMaps, rating da GMaps, stock da Subito/AS24

FASE 3: CLASSIFY
    8. Per ogni dealer: classify_commission_dealer()
    9. Per ogni dealer: score_fit_argos() (da dealer_scouting_playbook.py)
    10. Ordinare per: commission_confidence * fit_score DESC

FASE 4: EXPORT
    11. Top 20-30 dealer → dealer_crm.py (insert come NEW, tier calcolato)
    12. Report Telegram: "Trovati {N} nuovi dealer potenziali in {province}"
    13. Log completo in DuckDB per analytics
```

### Frequenza consigliata

| Azione | Frequenza | Perche' |
|--------|-----------|---------|
| Discovery completo | Settimanale (domenica notte) | Stock dealer cambia lentamente |
| Verifica rotazione stock | Ogni 2 settimane | Per confermare pattern commissione |
| Google Maps refresh | Mensile | Rating/recensioni cambiano raramente |

### Stime di volume per provincia

| Provincia | Dealer su Subito (stima) | Di cui "commissione" (stima) | Fit ARGOS (stima) |
|-----------|--------------------------|------------------------------|-------------------|
| Foggia | 25-40 | 6-12 | 3-5 |
| Cosenza | 20-35 | 5-10 | 2-4 |
| Caserta | 30-50 | 8-15 | 4-6 |
| Salerno | 25-40 | 6-12 | 3-5 |
| Lecce | 20-35 | 5-10 | 2-4 |
| Taranto | 15-25 | 4-8 | 2-3 |
| Bari | 40-60 | 10-18 | 5-8 |
| Catanzaro | 10-20 | 3-6 | 1-3 |
| **TOTALE Sud** | **~250-400** | **~60-100** | **~25-40** |

## State of the Art

| Vecchio approccio | Approccio corrente | Impatto |
|-------------------|--------------------|---------|
| Ricerca manuale Google | Scraping automatico multi-piattaforma | Da 2-3 dealer/ora a 50+/ora |
| Solo AS24 per dealer list | Subito.it __NEXT_DATA__ + AS24 + GMaps cross-ref | 3x piu' dealer trovati |
| Nessun filtro "commissione" | Classificatore heuristico 5 segnali | Target chirurgico vs lista generica |
| Excel dealer list | dealer_crm.py SQLite con pipeline status | Pipeline automatizzata |

## Open Questions

1. **impresapiu.subito.it accessibility**
   - What we know: le shop page individuali (es. `/shops/38485-imperauto-foggia`) potrebbero restituire 403
   - What's unclear: se il blocco e' solo su directory listing o anche su singole pagine
   - Recommendation: testare con curl_cffi e undetected-chromedriver. Se bloccato, estratrre dati dealer dalle listing page standard (non dalla shop page)

2. **AutoScout24.it /concessionari/ JS rendering**
   - What we know: la pagina carica dealer via JavaScript (React)
   - What's unclear: se esiste un endpoint JSON sottostante (tipo `/api/dealers?region=puglia`)
   - Recommendation: ispezionare network tab con Playwright per intercettare le XHR/fetch calls

3. **Volume stimato "su commissione"**
   - What we know: il 20-30% dei piccoli dealer nel Sud lavora su commissione (stima da ricerca S73)
   - What's unclear: se la stima e' accurata — nessun dato ufficiale
   - Recommendation: validare con primo batch (5 province) e calibrare percentuali

4. **ATECO 45.11.02 come filtro**
   - What we know: registroimprese.it classifica intermediari auto con ATECO specifico
   - What's unclear: quanti dealer "su commissione" sono registrati con 45.11.02 vs 45.11.01
   - Recommendation: per primo batch, NON usare ATECO come discovery (costa tempo). Usare come verifica post-discovery.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | Tutto | OK | 3.13 | — |
| curl_cffi | resilient_fetcher | OK | Installato | cloudscraper |
| playwright | Google Maps scraper | OK | Installato (sanitizer) | selenium |
| sqlite3 | dealer_crm | OK | stdlib | — |
| duckdb | analytics | OK | Installato | SQLite |
| fuzzywuzzy/thefuzz | dedup nomi dealer | Da verificare | — | difflib.SequenceMatcher (stdlib) |

**Missing dependencies with fallback:**
- thefuzz: se non installato, usare difflib.SequenceMatcher dalla stdlib Python (sufficiente per dedup nomi)

## Sources

### Primary (HIGH confidence)
- Subito.it __NEXT_DATA__ structure — verificato via morrolinux/subito-it-searcher + alebrandi/Subito.it-API
- PagineGialle API — verificato via chiccomagnus/PGAPI su GitHub
- ARGOS existing codebase — resilient_fetcher.py, dealer_crm.py, dealer_scouting_playbook.py

### Secondary (MEDIUM confidence)
- [Subito.it shop URLs](https://impresapiu.subito.it/shops/38485-imperauto-foggia) — URL pattern verificato da search results
- [AutoScout24.it concessionari](https://www.autoscout24.it/concessionari/) — directory verificata ma JS-rendered
- [HasData/google-maps-scraper](https://github.com/HasData/google-maps-scraper) — open source Playwright scraper
- [GDPR B2B Italy](https://consulente-gdpr.it/domande-e-risposte/marketing-b2b-e-gdpr/) — Art. 130 Codice Privacy
- [GDPR Soft Spam Italy](https://www.dgrs.it/lapplicazione-in-italia-della-disciplina-del-soft-spam-e-linterpretazione-dei-paesi-europei-unanalisi-comparata/) — analisi comparata
- [Scraping AutoScout24](https://scrapfly.io/blog/posts/how-to-scrape-autoscout24) — Akamai protection details

### Tertiary (LOW confidence)
- Stime volume dealer per provincia — basate su ricerca S73 + extrapolazione, NON verificate
- Facebook scraping feasibility — sconsigliato, info da fonti terze

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — basato su codebase ARGOS esistente
- Piattaforme Subito/PG: MEDIUM-HIGH — URL pattern e parsing verificati
- Piattaforme AS24/GMaps: MEDIUM — anti-bot e JS-rendering aggiungono incertezza
- Compliance GDPR: MEDIUM — interpretazione legale, non consulenza legale
- Stime volume: LOW — extrapolazioni da campione limitato

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (30 giorni — piattaforme cambiano lentamente)
