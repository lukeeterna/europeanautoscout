# Phase 11: Automazione Comunicazione Dealer - Research

**Researched:** 2026-03-31
**Domain:** WhatsApp automation, dealer CRM, on-demand vehicle scouting, TTS voice generation
**Confidence:** HIGH

## Summary

Il sistema ARGOS ha gia' una infrastruttura robusta: wa-daemon.js (whatsapp-web.js su PM2), response-analyzer.py (LLM via OpenRouter + Haiku), outreach_scheduler.py (sequenza Day 3/7/10/14/21/30), dealer_crm.py (SQLite schema completo), e pipeline CoVe (scraper 28 portali -> scoring -> dossier). Mancano 4 pezzi per l'automazione completa: (1) generazione primo messaggio personalizzato automatico dal profilo dealer, (2) parsing richieste on-demand dal dealer, (3) matching veicolo-dealer intelligente, (4) vocali TTS per Day 10.

**Primary recommendation:** Estendere il sistema esistente senza riscritture. Aggiungere un modulo `message_generator.py` che combina profilo dealer + stock scrappato + opportunita' CoVe per generare il Day 1 personalizzato. Per il flusso on-demand, aggiungere un classifier nel response-analyzer.py che detecta richieste veicolo e triggera lo scraper con filtri estratti. Per i vocali, usare `edge-tts` (gratuito, qualita' Microsoft Neural TTS). MAI migrare a WhatsApp Business API — costa troppo e viola REGOLA ZERO COSTI.

## Standard Stack

### Core (GIA' ESISTENTE - da estendere)
| Componente | Path | Scopo | Stato |
|-----------|------|-------|-------|
| wa-daemon.js | wa-intelligence/wa-daemon.js | Sessione WA + invio/ricezione + anti-ban | OPERATIVO |
| response-analyzer.py | wa-intelligence/response-analyzer.py | LLM response + classification + Telegram approval | OPERATIVO |
| outreach_scheduler.py | tools/outreach_scheduler.py | Sequenza touchpoint automatica | OPERATIVO |
| dealer_crm.py | tools/dealer_crm.py | Schema CRM completo (dealers, interactions, vehicles_proposed) | OPERATIVO |
| pipeline_orchestrator.py | src/cove/pipeline_orchestrator.py | Scrape -> CoVe -> Enrich -> Dossier | OPERATIVO (cron 4h) |
| scraper_cove_pipeline.py | src/cove/scraper_cove_pipeline.py | Scraper -> CoVe scoring E2E | OPERATIVO |
| autoscout_scraper.py | tools/scrapers/autoscout_scraper.py | Scraper AS24 multi-country | OPERATIVO |
| argos_knowledge_base.md | wa-intelligence/argos_knowledge_base.md | KB per risposte LLM calibrate | OPERATIVO |

### Nuovi moduli da creare
| Modulo | Scopo | Dipende da |
|--------|-------|-----------|
| `tools/message_generator.py` | Genera Day 1 personalizzato per archetipo + stock dealer | dealer_crm.py, DuckDB opportunita' |
| `tools/vehicle_matcher.py` | Matcha opportunita' CoVe con profilo dealer | cove_tracker.duckdb, dealer_crm.py |
| `tools/request_parser.py` | Estrae marca/modello/anno/budget da messaggio WA testo libero | regex + normalizzazione |
| `tools/voice_generator.py` | Genera vocale WA Day 10 con edge-tts | edge-tts (pip install) |

### Dipendenze nuove
| Pacchetto | Versione | Scopo | Costo |
|----------|---------|-------|-------|
| edge-tts | 6.1+ | TTS Microsoft Neural (italiano) | GRATIS |

**Installazione:**
```bash
pip install edge-tts
```

## Architecture Patterns

### Flusso Completo Comunicazione Automatizzata

```
                                    OUTBOUND (proattivo)
                                    =====================
dealer_crm.py (profilo)  ─┐
                           ├─> message_generator.py ─> wa-daemon POST /send
vehicle_matcher.py (top3) ─┘         |
                                     v
                           outreach_scheduler.py (Day 3/7/10...)
                                     |
                                     v (Day 10)
                           voice_generator.py ─> wa-daemon POST /send-media


                                    INBOUND (on-demand)
                                    ====================
dealer scrive WA ─> wa-daemon (message_create)
                        |
                        v
                  response-analyzer.py
                        |
                  ┌─────┴─────┐
                  |           |
            VEHICLE_REQUEST   ALTRO (curiosity/objection/positive...)
                  |                    |
                  v                    v
            request_parser.py    LLM genera risposta (come oggi)
                  |
                  v
            scraper_cove_pipeline.py (filtri specifici)
                  |
                  v
            shortlist 3 veicoli ─> formatta WA ─> pending_replies ─> Telegram approval
```

### Pattern 1: Message Generator (Day 1 Personalizzato)

**What:** Genera il primo messaggio WA partendo dal profilo dealer e dalle opportunita' CoVe disponibili.

**Input:** dealer_id dal CRM
**Output:** messaggio WA pronto (testo, max 5 righe)

```python
# tools/message_generator.py

import sqlite3
import json
import duckdb
from typing import Optional, Dict, List

# Template per archetipo — basati su research/s73_messaging_v2.md
TEMPLATES = {
    "NARCISO": {
        "day1": (
            "Buongiorno, ho trovato una {vehicle} {year}, {km} km,\n"
            "a {city_source} — {price_eu}. In {region_dealer} gli stessi esemplari partono da {price_it}.\n\n"
            "Sto cercando 2-3 concessionari della zona per questo tipo di auto.\n"
            "Ho visto il suo stock su AutoScout24 — tratta questa fascia.\n\n"
            "Le mando la scheda completa?\n\n"
            "Luca Ferretti"
        ),
    },
    "RAGIONIERE": {
        "day1": (
            "Buongiorno, ho trovato una {vehicle} {year}, {km} km\n"
            "a {price_eu} in {country_source}.\n\n"
            "In Italia la stessa auto sta a {price_it}.\n"
            "Trasporto {region_dealer}: {transport_cost}. Fee mia: {fee}.\n"
            "Margine netto per lei: circa {margin}.\n\n"
            "Le interessa?\n\n"
            "Luca Ferretti"
        ),
    },
    "BARONE": {
        "day1": (
            "Buongiorno, ho una {vehicle} {year}, {km} km,\n"
            "certificata — {price_eu} in {country_source}.\n\n"
            "Su AutoScout24 Italia la stessa auto sta a {price_it}.\n"
            "Km verificati prima di proporla.\n\n"
            "Ha interesse per questa fascia?\n\n"
            "Luca Ferretti"
        ),
    },
    "TECNICO": {
        "day1": (
            "Buongiorno, ho trovato una {vehicle} {year}, {km} km,\n"
            "{optional_features}— {price_eu} in {country_source}.\n\n"
            "Allestimento completo e VIN check gia' fatto.\n"
            "Posso mandarle la scheda tecnica con tutti i dettagli?\n\n"
            "Luca Ferretti"
        ),
    },
    "RELAZIONALE": {
        "day1": (
            "Buongiorno, sono Luca — lavoro con concessionari\n"
            "della zona {city_dealer} per trovare auto dalla Germania.\n\n"
            "Ho visto le sue {reviews} recensioni — pochi in {region_dealer}\n"
            "hanno quel livello di fiducia dai clienti.\n\n"
            "Posso chiamarla 2 minuti per presentarmi?\n\n"
            "Luca"
        ),
    },
}

# Fallback per archetipi non mappati (CONSERVATORE, DELEGATORE, PERFORMANTE, OPPORTUNISTA)
DEFAULT_TEMPLATE = TEMPLATES["RAGIONIERE"]


def load_dealer(db_path: str, dealer_id: str) -> dict:
    """Carica profilo dealer dal CRM."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM dealers WHERE dealer_id = ?", [dealer_id]).fetchone()
    con.close()
    return dict(row) if row else {}


def find_best_vehicle(duckdb_path: str, dealer: dict) -> Optional[dict]:
    """
    Trova il miglior veicolo DOSSIER_READY da proporre al dealer.
    Criteri:
    1. Marchio nel range del dealer (brands JSON array)
    2. CoVe confidence >= 0.75
    3. Margine stimato > €2000
    4. Ordinato per opportunity_score DESC
    """
    brands = json.loads(dealer.get("brands", "[]"))
    if not brands:
        brands = ["BMW", "Mercedes", "Audi"]  # default premium

    con = duckdb.connect(duckdb_path, read_only=True)
    # Query per veicoli pronti che matchano i brand del dealer
    placeholders = ",".join(["?" for _ in brands])
    rows = con.execute(f"""
        SELECT *
        FROM vehicles
        WHERE state IN ('DOSSIER_READY', 'DATA_COMPLETE')
          AND make IN ({placeholders})
          AND cove_confidence >= 0.75
          AND estimated_margin > 2000
        ORDER BY opportunity_score DESC
        LIMIT 5
    """, brands).fetchall()
    con.close()

    if not rows:
        return None

    # Evita veicoli gia' proposti a questo dealer
    # (check vehicles_proposed in SQLite)
    # ... [implementation]

    return dict(zip([col[0] for col in con.description], rows[0])) if rows else None


def generate_day1(dealer: dict, vehicle: dict) -> str:
    """Genera messaggio Day 1 personalizzato."""
    archetype = dealer.get("archetype", "RAGIONIERE")
    template = TEMPLATES.get(archetype, DEFAULT_TEMPLATE)["day1"]

    # Mappa citta' source da country code
    country_names = {
        "DE": "Germania", "NL": "Olanda", "BE": "Belgio",
        "AT": "Austria", "FR": "Francia", "SE": "Svezia",
    }
    city_source_map = {
        "DE": "Monaco", "NL": "Amsterdam", "BE": "Bruxelles",
        "AT": "Vienna", "FR": "Parigi", "SE": "Stoccolma",
    }

    country = vehicle.get("country", "DE")
    margin = vehicle.get("estimated_margin", 0)
    transport = 650 if country in ("AT", "DE") else 800  # stima semplificata

    params = {
        "vehicle": f"{vehicle.get('make', '')} {vehicle.get('model', '')} {vehicle.get('variant', '')}".strip(),
        "year": vehicle.get("year", ""),
        "km": f"{vehicle.get('km', 0):,}".replace(",", "."),
        "price_eu": f"EUR{vehicle.get('price', 0):,.0f}".replace(",", "."),
        "price_it": f"EUR{vehicle.get('market_ref_price', 0):,.0f}".replace(",", "."),
        "city_source": city_source_map.get(country, "Germania"),
        "country_source": country_names.get(country, "Germania"),
        "region_dealer": dealer.get("region", "Sud Italia"),
        "city_dealer": dealer.get("city", ""),
        "transport_cost": f"EUR{transport}",
        "fee": "EUR900",
        "margin": f"EUR{margin - transport - 900:,.0f}".replace(",", "."),
        "reviews": dealer.get("reviews", ""),
        "optional_features": "",  # da enricher
    }

    return template.format(**params)
```

### Pattern 2: Request Parser (On-Demand)

**What:** Estrae marca/modello/anno/budget/specifiche dal messaggio WA del dealer in testo libero.

```python
# tools/request_parser.py

import re
from typing import Optional, Dict

# Normalizzazione brand
BRAND_ALIASES = {
    "bmw": "BMW", "bimmer": "BMW",
    "mercedes": "Mercedes", "merc": "Mercedes", "benz": "Mercedes",
    "audi": "Audi",
    "porsche": "Porsche",
    "range rover": "Range Rover", "range": "Range Rover",
    "lambo": "Lamborghini", "lamborghini": "Lamborghini",
    "ferrari": "Ferrari",
}

# Normalizzazione modello
MODEL_ALIASES = {
    "x3": "X3", "x5": "X5", "x1": "X1",
    "glc": "GLC", "gle": "GLE", "gla": "GLA",
    "classe c": "Classe C", "classe e": "Classe E", "classe a": "Classe A",
    "q3": "Q3", "q5": "Q5", "q7": "Q7",
    "a3": "A3", "a4": "A4", "a5": "A5", "a6": "A6",
    "macan": "Macan", "cayenne": "Cayenne",
    "serie 3": "Serie 3", "serie 5": "Serie 5",
    "911": "911", "panamera": "Panamera",
}

# Varianti motore comuni
VARIANT_PATTERNS = [
    r"(x[Dd]rive\d{2}[deiDEI]?)",
    r"(\d{3}[deiDEI]\b)",          # 220d, 320i
    r"(M\s?Sport)",
    r"([AMGS]\s?\d{2,3})",
    r"(S\s?line)",
]

def parse_request(text: str) -> Dict:
    """
    Estrae parametri di ricerca da testo libero WA.

    Esempi input:
    - "mi serve una X3 2022 sotto 38k, colore scuro"
    - "hai una mercedes GLC 220d 2021 max 35mila?"
    - "cerco una tedesca buona sotto 40k"
    - "bmw x3 20d 2022 max 35000 nero o grigio"
    - "mi trovi un q5 recente?"

    Output: {
        "make": "BMW" | None,
        "model": "X3" | None,
        "variant": "xDrive20d" | None,
        "year_min": 2022 | None,
        "year_max": 2022 | None,
        "budget_max": 38000 | None,
        "color": "scuro" | None,
        "km_max": None,
        "fuel": None,
        "confidence": 0.0-1.0,
        "raw_text": "...",
        "missing": ["make", ...]  # campi non trovati
    }
    """
    text_lower = text.lower().strip()
    result = {
        "make": None, "model": None, "variant": None,
        "year_min": None, "year_max": None,
        "budget_max": None, "color": None,
        "km_max": None, "fuel": None,
        "confidence": 0.0, "raw_text": text,
        "missing": [],
    }

    # 1. Estrai brand
    for alias, brand in BRAND_ALIASES.items():
        if alias in text_lower:
            result["make"] = brand
            break

    # Fallback: "tedesca" = BMW/Mercedes/Audi (generico)
    if not result["make"]:
        if "tedesca" in text_lower or "germania" in text_lower:
            result["make"] = "GERMAN_ANY"  # il matcher espandera'

    # 2. Estrai modello
    for alias, model in MODEL_ALIASES.items():
        if alias in text_lower:
            result["model"] = model
            break

    # 3. Estrai anno
    year_match = re.search(r"\b(20[12][0-9])\b", text_lower)
    if year_match:
        year = int(year_match.group(1))
        result["year_min"] = year
        result["year_max"] = year

    # "recente" = 2022+
    if "recente" in text_lower or "nuova" in text_lower:
        result["year_min"] = result["year_min"] or 2022

    # 4. Estrai budget
    # Pattern: "sotto 38k", "max 35mila", "max 35000", "35.000 euro", "budget 40k"
    budget_patterns = [
        r"(?:sotto|max|massimo|budget|entro)\s*(?:i\s*)?(\d{2,3})\s*(?:k|mila)",
        r"(?:sotto|max|massimo|budget|entro)\s*(?:i\s*)?(\d{4,6})",
        r"(\d{2,3})\s*(?:k|mila)\s*(?:euro|eur)?",
        r"(\d{2})[\.\s]?(\d{3})\s*(?:euro|eur)?",
    ]
    for pattern in budget_patterns:
        m = re.search(pattern, text_lower)
        if m:
            groups = m.groups()
            if len(groups) == 2 and groups[1]:
                result["budget_max"] = int(groups[0]) * 1000 + int(groups[1])
            elif int(groups[0]) < 200:  # "38k" = 38000
                result["budget_max"] = int(groups[0]) * 1000
            else:
                result["budget_max"] = int(groups[0])
            break

    # 5. Estrai colore
    colors = {
        "nero": "nero", "nera": "nero", "black": "nero",
        "bianco": "bianco", "bianca": "bianco", "white": "bianco",
        "grigio": "grigio", "grigia": "grigio", "grey": "grigio", "gray": "grigio",
        "blu": "blu", "blue": "blu",
        "scuro": "scuro",  # generico = nero/grigio/blu
    }
    for color_key, color_val in colors.items():
        if color_key in text_lower:
            result["color"] = color_val
            break

    # 6. Estrai km max
    km_match = re.search(r"(?:max|sotto|meno di)\s*(\d{2,3})\s*(?:\.?000)?\s*km", text_lower)
    if km_match:
        km_val = int(km_match.group(1))
        result["km_max"] = km_val * 1000 if km_val < 200 else km_val

    # 7. Estrai variante motore
    for pattern in VARIANT_PATTERNS:
        vm = re.search(pattern, text, re.IGNORECASE)
        if vm:
            result["variant"] = vm.group(1)
            break

    # 8. Calcola confidence
    filled = sum(1 for k in ["make", "model", "year_min", "budget_max"] if result[k])
    result["confidence"] = filled / 4.0

    # 9. Campi mancanti
    for field in ["make", "model", "year_min", "budget_max"]:
        if not result[field]:
            result["missing"].append(field)

    return result


def build_search_queries(parsed: dict) -> list:
    """
    Traduce la richiesta parsata in query per gli scraper.
    Gestisce varianti (X3 = xDrive20d, xDrive30d, ecc.)
    """
    queries = []

    makes = [parsed["make"]] if parsed["make"] and parsed["make"] != "GERMAN_ANY" else ["BMW", "Mercedes", "Audi"]

    for make in makes:
        q = {
            "make": make,
            "model": parsed.get("model"),
            "year_min": parsed.get("year_min", 2020),
            "year_max": parsed.get("year_max", 2025),
            "price_max": parsed.get("budget_max"),
            "km_max": parsed.get("km_max", 80000),
            "countries": ["DE", "NL", "BE", "AT"],  # mercati principali
        }
        queries.append(q)

    return queries
```

### Pattern 3: Vehicle Matcher (Proattivo)

**What:** Sceglie il veicolo MIGLIORE da proporre a ciascun dealer basandosi sul profilo.

```python
# tools/vehicle_matcher.py — Pseudocodice logica matching

def match_vehicle_to_dealer(dealer: dict, opportunities: list) -> dict:
    """
    Scoring per match veicolo-dealer.

    Fattori:
    1. Brand match: il dealer tratta quel marchio? (+30 punti)
    2. Fascia prezzo: coerente col positioning? (+20 punti)
    3. Margine: piu' alto = meglio per il Ragioniere (+20 punti)
    4. Rarita': veicolo raro = meglio per il Narciso (+15 punti)
    5. Qualita' dati: CoVe score alto = piu' credibile (+15 punti)

    Il peso dei fattori cambia per archetipo:
    - NARCISO: rarita' x2, margine x0.5
    - RAGIONIERE: margine x2, rarita' x0.5
    - BARONE: qualita' x2, brand_match x1.5
    - TECNICO: qualita' x2, allestimento dettagliato x1.5
    """
    dealer_brands = json.loads(dealer.get("brands", "[]"))
    dealer_stock_avg_price = estimate_avg_price(dealer)  # dalla fascia stock
    archetype = dealer.get("archetype", "RAGIONIERE")

    scored = []
    for v in opportunities:
        score = 0

        # Brand match
        if v["make"] in dealer_brands:
            score += 30
        elif v["make"] in ["BMW", "Mercedes", "Audi"]:
            score += 10  # premium generico

        # Fascia prezzo coerente
        price_ratio = v["price"] / dealer_stock_avg_price if dealer_stock_avg_price else 1
        if 0.7 <= price_ratio <= 1.5:
            score += 20

        # Margine
        margin_score = min(20, v.get("estimated_margin", 0) / 250)
        score += margin_score

        # CoVe quality
        score += v.get("cove_confidence", 0) * 15

        # Archetype weight adjustments
        if archetype == "NARCISO":
            if v.get("make") in ["Porsche", "Lamborghini", "Ferrari"]:
                score += 20
        elif archetype == "RAGIONIERE":
            score += margin_score  # double weight
        elif archetype == "BARONE":
            score += v.get("cove_confidence", 0) * 15  # double weight

        scored.append((score, v))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None
```

### Pattern 4: Integrazione On-Demand nel Response Analyzer

**What:** Nuovo classification type `VEHICLE_REQUEST` nel response-analyzer.py.

```python
# Aggiunta a response-analyzer.py PATTERNS dict

'VEHICLE_REQUEST': {
    'exact': [
        'mi serve', 'mi trovi', 'cerco', 'sto cercando',
        'hai una', 'hai disponibile', 'avete', 'mi procuri',
        'mi puoi trovare', 'puoi cercare', 'cerca una',
        'mi interessa una', 'ho bisogno di', 'mi occorre',
        'per un cliente', 'un cliente cerca', 'cliente vuole',
        'ho un cliente che', 'ci serve', 'ci servirebbe',
    ],
    'weight': 0.90,  # alta priorita' — e' una richiesta di business
},
```

Quando classificato come VEHICLE_REQUEST:
1. ACK immediato: "Ricevuto, cerco sui portali europei. Domani mattina le mando 2-3 opzioni con numeri."
2. Trigger `request_parser.py` per estrarre parametri
3. Se parametri insufficienti (confidence < 0.5): chiedere chiarimento ("Che marca/modello? Budget massimo?")
4. Se parametri OK: trigger scraper con filtri -> CoVe -> shortlist top 3
5. Formatta shortlist WA-friendly -> pending_replies -> Telegram approval

### Pattern 5: Shortlist WA-Friendly

**What:** Formato compatto per presentare 3 opzioni via WhatsApp.

```
Msg 1 (ACK):
"ricevuto, cerco subito sui portali europei"

Msg 2 (risultati, 24h dopo):
"guarda, ho trovato 3 opzioni per la X3 2022:

1. BMW X3 20d M Sport — 41.000 km
   Germania — EUR28.400
   Margine netto: ~EUR4.200

2. BMW X3 30d xLine — 38.000 km
   Olanda — EUR31.200
   Margine netto: ~EUR3.800

3. BMW X3 20d — 52.000 km
   Belgio — EUR26.100
   Margine netto: ~EUR5.100

quale le interessa? le mando il dossier completo"
```

### Pattern 6: Voice Generator (Day 10)

```python
# tools/voice_generator.py

import asyncio
import edge_tts
import os

VOICE_IT = "it-IT-DiegoNeural"  # voce maschile italiana naturale
OUTPUT_DIR = "/tmp/argos-voices"

async def generate_voice(text: str, dealer_id: str) -> str:
    """
    Genera vocale WA con edge-tts.
    Ritorna path al file .ogg (formato WA voice note).
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"voice_{dealer_id}.mp3")

    communicate = edge_tts.Communicate(text, VOICE_IT, rate="-5%")  # leggermente lento = piu' naturale
    await communicate.save(output_path)

    # Converti in ogg/opus per WA voice note
    ogg_path = output_path.replace(".mp3", ".ogg")
    os.system(f'ffmpeg -i {output_path} -c:a libopus -b:a 32k {ogg_path} -y 2>/dev/null')

    return ogg_path


def generate_day10_voice(dealer: dict) -> str:
    """
    Genera vocale Day 10 personalizzato.
    Max 20 secondi (~50 parole italiane).
    """
    archetype = dealer.get("archetype", "RAGIONIERE")
    name = dealer.get("titolare_name", "")

    scripts = {
        "NARCISO": (
            f"Buongiorno {name}, sono Luca. Le avevo mandato due auto dalla Germania "
            f"la settimana scorsa. Ho appena trovato un esemplare raro, "
            f"se ha due minuti le mando i dettagli. Buona giornata."
        ),
        "RAGIONIERE": (
            f"Buongiorno {name}, sono Luca Ferretti. Le avevo mandato i numeri "
            f"su una BMW e una Mercedes dalla Germania. Se ha un momento, "
            f"mi faccia sapere se la fascia di prezzo e' giusta. Grazie."
        ),
        "BARONE": (
            f"Buongiorno, sono Luca. Volevo solo dirle che sono a disposizione "
            f"se in futuro le serve un veicolo dall'estero. Nessuna fretta, "
            f"quando vuole mi scriva pure. Buona giornata."
        ),
        "TECNICO": (
            f"Buongiorno {name}, sono Luca. Le avevo mandato la scheda tecnica "
            f"di una BMW con allestimento completo. Se vuole posso mandarle "
            f"anche il VIN check dettagliato. Mi faccia sapere."
        ),
        "RELAZIONALE": (
            f"Ciao {name}, sono Luca. Le avevo scritto la settimana scorsa. "
            f"Se ha due minuti mi piacerebbe sentirci a voce per presentarmi "
            f"meglio. Quando le fa comodo mi chiami pure. A presto."
        ),
    }

    script = scripts.get(archetype, scripts["RAGIONIERE"])

    return asyncio.run(generate_voice(script, dealer.get("dealer_id", "unknown")))
```

### Invio vocale via wa-daemon

Il wa-daemon ha gia' il supporto per `sendAudioAsVoice`:

```javascript
// Dentro wa-daemon.js POST /send-media (da aggiungere)
const media = MessageMedia.fromFilePath(filePath);
await client.sendMessage(chatId, media, { sendAudioAsVoice: true });
```

### Anti-Pattern da Evitare

- **MAI creare un chatbot autonomo**: SEMPRE human-in-the-loop via Telegram approval (gia' implementato nel response-analyzer)
- **MAI rispondere automaticamente a VEHICLE_REQUEST senza conferma umana**: la shortlist va in pending_replies
- **MAI inviare vocali TTS senza review del founder**: il vocale generato va in Telegram per approvazione
- **MAI usare LLM per generare Day 1**: il primo messaggio e' TEMPLATE con dati reali, non LLM-generated (evita allucinazioni)
- **MAI inviare veicoli che non sono DOSSIER_READY**: solo veicoli con CoVe >= 0.75 e pipeline state >= DATA_COMPLETE

## Don't Hand-Roll

| Problema | Non Costruire | Usa Invece | Perche' |
|---------|-------------|-----------|--------|
| TTS vocali italiani | Modello TTS custom | edge-tts (Microsoft Neural TTS) | Qualita' nativa, gratis, 0 training |
| NLP parsing richieste | LLM per ogni parsing | Regex + normalizzazione + LLM fallback | LLM ha costo (OpenRouter), regex e' gratis e veloce per 90% dei casi |
| Sessione WhatsApp | WhatsApp Business API | whatsapp-web.js (gia' operativo) | Costo zero, gia' configurato, volume < 30 msg/day |
| Template engine | Jinja2 / template engine complesso | Python f-string con dict | Max 5 template per archetipo, complessita' non giustificata |
| Scheduler | Cron job custom | outreach_scheduler.py (gia' operativo) | Gia' gestisce Day 3/7/10/14/21/30 |
| CRM | Nuovo sistema CRM | dealer_crm.py + dealer_network.sqlite (gia' operativo) | Schema completo con interactions, vehicles_proposed |

## Common Pitfalls

### Pitfall 1: WhatsApp Ban per Volume
**What goes wrong:** Invio di troppi messaggi a numeri nuovi -> ban account WA.
**Why it happens:** WhatsApp detecta pattern automatici: troppi messaggi a numeri non in rubrica, intervalli regolari, messaggi identici.
**How to avoid:**
- Max 10-15 nuovi contatti/giorno (gia' CONFIG.DAILY_LIMIT=30, ma abbassare per primi contatti)
- Intervalli log-normali (gia' implementato in HumanLike)
- Simulare typing (gia' implementato)
- Business hours only 8-20 (gia' implementato)
- Variare leggermente i messaggi (il template + dati reali crea varianza naturale)
**Warning signs:** Account temporaneamente limitato, QR da riscansionare spesso.

### Pitfall 2: LLM Hallucination nel Flusso On-Demand
**What goes wrong:** LLM inventa veicoli/prezzi nella risposta al dealer.
**Why it happens:** Il dealer chiede "hai una X3?" e l'LLM risponde "si, ne ho 3" inventando i dettagli.
**How to avoid:**
- Per risposte on-demand: MAI lasciare l'LLM inventare veicoli
- Il flusso corretto: parser estrae parametri -> scraper trova veicoli REALI -> formatta risultati -> umano approva
- L'LLM genera SOLO l'ACK ("ricevuto, cerco subito") e le risposte conversazionali
**Warning signs:** Prezzi troppo tondi (es. EUR30.000 esatti), veicoli senza listing_id.

### Pitfall 3: Vocale TTS Riconosciuto come Artificiale
**What goes wrong:** Il dealer capisce che il vocale e' generato da TTS -> perde fiducia.
**Why it happens:** Le voci TTS, per quanto buone, hanno prosodia leggermente diversa da un umano.
**How to avoid:**
- edge-tts con voce it-IT-DiegoNeural e' gia' molto naturale
- Rate leggermente ridotto (-5%) per sembrare piu' pensieroso
- Contenuto BREVE (max 20 secondi) riduce esposizione
- Alternativa: il founder registra 5-6 vocali template a mano (20 sec ciascuno)
- **RACCOMANDAZIONE:** Fase 1 = vocali manuali del founder. Fase 2 = TTS come backup quando scala.
**Warning signs:** Dealer chiede "ma e' una registrazione automatica?"

### Pitfall 4: Request Parser Non Capisce Dialetto/Abbreviazioni
**What goes wrong:** Il dealer scrive "m serv n x3 2022 stt 38" e il parser non estrae nulla.
**Why it happens:** Testo libero WA con abbreviazioni, errori, dialetto.
**How to avoid:**
- Fallback LLM: se confidence < 0.5, passa il messaggio a Haiku per extraction
- Normalizzazione pre-processing: rimuovi abbreviazioni comuni ("m serv" -> "mi serve", "stt" -> "sotto")
- Se ancora insufficiente: rispondi con domanda chiusa ("che marca e modello? e budget massimo?")
**Warning signs:** Troppi messaggi classificati come UNKNOWN.

### Pitfall 5: Dealer Risponde e il Sistema Continua la Sequenza Automatica
**What goes wrong:** Day 3 va automaticamente anche se il dealer ha gia' risposto.
**Why it happens:** outreach_scheduler.py avanza la sequenza su timer, senza controllare se c'e' stata risposta.
**How to avoid:**
- Quando wa-daemon riceve risposta -> update pipeline_status a 'REPLIED'
- outreach_scheduler.py: skip dealer con pipeline_status IN ('REPLIED', 'INTERESTED', 'NEGOTIATION')
- Il passaggio REPLIED -> sequenza custom va gestito dal founder via Telegram
**Warning signs:** Dealer riceve Day 7 dopo aver gia' detto "si, mi interessa".

## WhatsApp: whatsapp-web.js vs Business API

### Confronto Completo

| Aspetto | whatsapp-web.js (attuale) | WA Business Cloud API |
|---------|--------------------------|----------------------|
| **Costo** | GRATIS | EUR0.05-0.10/msg marketing (IT), EUR0.03/msg utility |
| **Volume ARGOS (10-50 msg/day)** | OK con anti-ban | ~EUR1.50-5.00/giorno = EUR45-150/mese |
| **Rischio ban** | MEDIO (mitigato da HumanLike) | ZERO (ufficiale) |
| **Setup** | GIA' OPERATIVO | Richiede Business Manager Meta, verifica azienda, 2-4 settimane |
| **Template messages** | N/A (testo libero) | Necessari per primo contatto (approvazione Meta) |
| **Messaggi in entrata** | Webhook via message_create | Webhook HTTPS (serve endpoint pubblico) |
| **Voice notes** | sendAudioAsVoice: true | Media upload + send |
| **Allegati/PDF** | MessageMedia.fromFilePath | Media upload API |
| **Affidabilita'** | 95%+ (QR disconnect ogni 2-4 settimane) | 99.9% SLA |
| **Adatto per ARGOS ora** | SI | NO (costo + setup + overkill) |

### Raccomandazione

**USARE whatsapp-web.js** (gia' operativo). Motivi:
1. ZERO COSTI (Regola #6 CLAUDE.md)
2. Gia' configurato e funzionante su iMac PM2
3. Volume ARGOS (10-50 msg/day) e' ben sotto il threshold ban
4. Anti-ban gia' implementato (HumanLike, business hours, daily limit)
5. Human-in-the-loop gia' implementato (Telegram approval)

**Quando migrare a Business API:**
- Volume > 100 msg/day
- Primo ban account (segnale che serve ufficiale)
- Revenue > EUR5.000/mese (puo' assorbire costo API)
- Necessita' di template messages pre-approvati

## Schema DB per Tracking On-Demand

### Nuova tabella: dealer_requests

```sql
CREATE TABLE IF NOT EXISTS dealer_requests (
    id                  TEXT PRIMARY KEY,
    dealer_id           TEXT NOT NULL,
    request_text        TEXT NOT NULL,        -- messaggio originale dealer
    parsed_make         TEXT,
    parsed_model        TEXT,
    parsed_year_min     INTEGER,
    parsed_year_max     INTEGER,
    parsed_budget_max   REAL,
    parsed_color        TEXT,
    parsed_km_max       INTEGER,
    parse_confidence    REAL,                 -- 0.0-1.0
    status              TEXT DEFAULT 'RECEIVED',
    -- RECEIVED/PARSING/SEARCHING/SHORTLISTED/SENT/CLOSED
    shortlist_count     INTEGER DEFAULT 0,
    shortlist_sent_at   TEXT,
    dealer_choice       TEXT,                 -- vehicle_id scelto
    created_at          TEXT DEFAULT (datetime('now')),
    updated_at          TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dealer_id) REFERENCES dealers(dealer_id)
);

CREATE TABLE IF NOT EXISTS shortlist_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id          TEXT NOT NULL,
    vehicle_id          TEXT,                 -- from DuckDB vehicles
    make                TEXT,
    model               TEXT,
    year                INTEGER,
    km                  INTEGER,
    price_eu            REAL,
    price_it_ref        REAL,
    margin_estimated    REAL,
    cove_score          REAL,
    country             TEXT,
    listing_url         TEXT,
    rank                INTEGER,              -- 1, 2, 3
    status              TEXT DEFAULT 'PROPOSED',
    -- PROPOSED/INTERESTED/APPROVED/PURCHASED/REJECTED
    FOREIGN KEY (request_id) REFERENCES dealer_requests(id)
);
```

### Estensione dashboard per il founder

Vista a colpo d'occhio:
```
ARGOS Dashboard — CRM Overview

Dealer Pipeline:
  TIER0:  3 dealer (1 REPLIED, 2 CONTACTED)
  TIER1:  6 dealer (3 NEW, 3 CONTACTED)
  TIER2:  3 dealer (3 NEW)

Richieste On-Demand Attive:
  Stile Car FG: "X3 2022 sotto 38k" — SEARCHING (2 risultati)
  Car Plus AV: nessuna richiesta

Prossime Azioni (oggi):
  09:00 — Day 7 Stile Car (FOMO/uscita)
  10:00 — Day 3 Car Plus (foto HD + 2o veicolo)

Messaggi Pendenti Approvazione: 2
```

## Sequenza Automatica Ripensata

### Flusso Decisionale per Ogni Step

```
Day 1:  message_generator.py → veicolo concreto basato su stock dealer + domanda chiusa
        Inviato via: wa-daemon POST /send
        Trigger: manuale o scheduler

Day 3:  SE silenzio → secondo veicolo (brand diverso) + intro on-demand
        "ho trovato anche questa — {veicolo2}. se ha un cliente che cerca qualcosa
         di specifico, mi scriva pure e cerco sui portali europei"
        SE ha risposto → conversazione umana (esce da sequenza)

Day 7:  SE silenzio → PDF allegato + FOMO lieve
        "la {vehicle} che le avevo segnalato e' stata presa.
         ne ho trovata un'altra simile — le allego il dossier completo"
        + PDF via wa-daemon POST /send-media

Day 10: SE silenzio → vocale personalizzato (TTS o manuale)
        20 sec max, calibrato su archetipo

Day 14: SE silenzio → referral o case study
        "un concessionario di {citta_vicina} ha preso 2 auto il mese scorso.
         se vuole le mando i numeri di come e' andata"

Day 21: SE silenzio → break-up gentile
        "non e' il momento giusto? nessun problema, sono qui quando le serve.
         mi scriva pure quando cerca qualcosa dall'estero"

Day 30: Telefonata/visita fisica (MANUALE — alert Telegram)
```

### Come Gestire il Dealer che Risponde

```
risposta dealer → wa-daemon (message_create)
                      |
                      v
                response-analyzer.py classifica
                      |
    ┌─────────────────┼──────────────────┐
    |                 |                  |
POSITIVE          CURIOSITY         VEHICLE_REQUEST
    |                 |                  |
    v                 v                  v
pipeline_status   LLM risponde      request_parser
= REPLIED         (come oggi)       + scraper trigger
    |                                    |
    v                                    v
STOP sequenza    continua in         shortlist → approval
automatica       pending_replies
    |
    v
founder gestisce
via Telegram
```

## TTS per Vocali WhatsApp — Dettaglio

### edge-tts: Raccomandazione Primaria

| Proprieta' | Valore |
|-----------|-------|
| Pacchetto | `edge-tts` (pip install edge-tts) |
| Voce italiana | `it-IT-DiegoNeural` (maschile), `it-IT-ElsaNeural` (femminile), `it-IT-IsabellaNeural` (femminile 2) |
| Qualita' | Microsoft Neural TTS — molto naturale, prosodia italiana corretta |
| Costo | GRATIS (usa API Microsoft Edge read-aloud) |
| Rate limit | Non documentato, ma uso moderato (5-10 vocali/giorno) non ha problemi |
| Output | MP3, convertibile in OGG/Opus per WA |
| Dipendenza extra | ffmpeg per conversione MP3 -> OGG (gia' su macOS: `brew install ffmpeg`) |

### Alternativa: Vocali Manuali del Founder

Per la fase iniziale (3-12 dealer), il founder potrebbe registrare 6 vocali template:
1. Day 10 NARCISO (20 sec)
2. Day 10 RAGIONIERE (20 sec)
3. Day 10 BARONE (20 sec)
4. Day 10 TECNICO (20 sec)
5. Day 10 RELAZIONALE (20 sec)
6. Day 10 GENERICO (20 sec)

**Vantaggio:** Voce vera di Luca Ferretti = massima credibilita'
**Svantaggio:** Non personalizzabili con nome dealer

**RACCOMANDAZIONE FINALE:** Iniziare con vocali manuali. Passare a edge-tts quando il volume sale sopra 10 dealer attivi.

## Cosa Implementare SUBITO vs DOPO

### FASE 1 — Implementare ORA (S94-S95)

| Componente | Effort | Impatto | Dipende da |
|-----------|--------|---------|-----------|
| `message_generator.py` (Day 1 personalizzato) | 2-3h | ALTO — automatizza primo contatto | dealer_crm.py, DuckDB |
| `vehicle_matcher.py` (scelta veicolo) | 2h | ALTO — elimina scelta manuale | DuckDB opportunita' |
| Classificatore VEHICLE_REQUEST in response-analyzer | 1h | MEDIO — abilita on-demand | response-analyzer.py |
| ACK automatico per richieste | 30min | MEDIO — feedback immediato dealer | wa-daemon.js |
| Fix outreach_scheduler per REPLIED | 1h | CRITICO — evita messaggi post-risposta | outreach_scheduler.py |

### FASE 2 — Implementare DOPO (S96-S97)

| Componente | Effort | Impatto | Dipende da |
|-----------|--------|---------|-----------|
| `request_parser.py` completo | 3-4h | ALTO — parsing richieste dealer | Fase 1 classifier |
| Shortlist generation + formato WA | 3h | ALTO — risposta on-demand completa | request_parser, scraper |
| Schema `dealer_requests` + `shortlist_items` | 1h | MEDIO — tracking richieste | SQLite |
| `voice_generator.py` con edge-tts | 2h | BASSO — solo Day 10 | edge-tts, ffmpeg |
| Dashboard estesa CRM | 4-6h | MEDIO — visibilita' founder | wa-intelligence/dashboard |

### FASE 3 — Implementare QUANDO SCALA (S100+)

| Componente | Effort | Impatto | Trigger |
|-----------|--------|---------|---------|
| Migrazione WA Business API | 2 settimane | ALTO — zero ban risk | Volume > 100 msg/day O primo ban |
| Multi-lingua template (DE/NL per seller) | 1 settimana | MEDIO — contatto seller EU | Quando ARGOS contatta seller direttamente |
| Dashboard dealer self-service | 2 settimane | ALTO — il dealer vede le sue proposte | Quando > 20 dealer attivi |

## Open Questions

1. **ffmpeg su iMac**
   - What we know: Necessario per convertire MP3 -> OGG per voice notes WA
   - What's unclear: ffmpeg e' installato su iMac? (macOS + Homebrew probabile)
   - Recommendation: Verificare con `ssh gianlucadistasi@192.168.1.2 which ffmpeg`

2. **OpenRouter costo per on-demand parsing**
   - What we know: Haiku costa ~$0.80/MTok input. Per parsing richiesta: ~500 tokens = $0.0004/richiesta
   - What's unclear: Volume atteso di richieste on-demand (probabilmente basso inizialmente)
   - Recommendation: Regex first, LLM fallback. Costo trascurabile per volume ARGOS.

3. **DuckDB schema campo `vehicles`**
   - What we know: `cove_tracker.duckdb` contiene listing, ma lo schema esatto dei campi per il matching non e' stato verificato
   - What's unclear: Campi esatti disponibili per query matching (make, model, price, state, etc.)
   - Recommendation: Verificare schema con `duckdb.connect('cove_tracker.duckdb').execute("DESCRIBE vehicles")`

## Sources

### Primary (HIGH confidence)
- Codebase ARGOS: wa-daemon.js, response-analyzer.py, outreach_scheduler.py, dealer_crm.py, pipeline_orchestrator.py
- research/s73_messaging_v2.md — template V2 completi per archetipo
- research/s73_dealer_persona.md — profili archetipi dettagliati
- wa-intelligence/argos_knowledge_base.md — KB per risposte LLM

### Secondary (MEDIUM confidence)
- [edge-tts GitHub](https://github.com/rany2/edge-tts) — Microsoft Neural TTS gratuito per Python
- [whatsapp-web.js Issue #160](https://github.com/pedroslopez/whatsapp-web.js/issues/160) — sendAudioAsVoice PTT
- [WhatsApp Business API Pricing](https://business.whatsapp.com/products/platform-pricing) — pricing per-message 2026
- [WhatsApp Business API Pricing Guide 2026](https://www.flowcall.co/blog/whatsapp-business-api-pricing-2026) — rate card IT
- [whatsapp-web.js ban risk](https://github.com/pedroslopez/whatsapp-web.js/issues/532) — account ban patterns

### Tertiary (LOW confidence)
- [WA AI Terms 2026](https://green-api.com/en/blog/2025/AI-Changes-to-WhatsApp-terms/) — nuove restrizioni AI su WA Business API
- Pricing WA Business API per Italia: ~EUR0.05-0.10/msg marketing (non verificato direttamente su rate card Meta)

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — tutto basato su codebase esistente, verificato direttamente
- Architecture: HIGH — estensione pattern gia' validati (response-analyzer, outreach_scheduler)
- Pitfalls: HIGH — basato su esperienza codebase (anti-ban gia' implementato, hallucination gia' gestita)
- WA API pricing: MEDIUM — range verificato ma EUR esatti per Italia non confermati
- TTS quality: MEDIUM — edge-tts verificato come libreria, qualita' voce italiana non testata direttamente

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stack stabile, pricing WA puo' cambiare)
