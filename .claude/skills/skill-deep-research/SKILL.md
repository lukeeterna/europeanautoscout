---
name: deep-research
description: >
  Skill enterprise per ricerca approfondita (deep research) su qualsiasi topic ARGOS:
  dealer target, mercati veicoli EU, prezzi, competitor, normative import, aree geografiche IT.
  TRIGGER su: "ricerca dealer", "deep research", "analisi mercato", "cerca concessionari",
  "trova lead", "competitor analysis", "prezzi veicoli", "normativa import", "analisi territorio",
  "dealer sud italia", "scouting lead", "market intelligence", "research autoscout",
  "carapis ricerca", "trova target", "analisi area".
  Usa Agent Explore + WebSearch + WebFetch per ricerca strutturata multi-source.
version: 1.0.0
allowed-tools: Bash, Read, Write, WebSearch, WebFetch, Agent, Grep, Glob
---

# ARGOS™ Deep Research — Skill Enterprise CoVe 2026

## PRINCIPIO

Deep research = ricerca strutturata multi-source con validazione incrociata.
MAI rispondere da memoria su dati di mercato — sempre verificare live.
Output sempre in formato strutturato con fonti citate.

---

## WORKFLOW DECISIONALE

```
RESEARCH REQUEST
     │
     ├─ Dealer target (nome/area)  ──→ [A] DEALER RESEARCH
     ├─ Mercato veicoli EU/IT       ──→ [B] MARKET RESEARCH
     ├─ Competitor / benchmark      ──→ [C] COMPETITOR RESEARCH
     ├─ Normativa / compliance      ──→ [D] REGULATORY RESEARCH
     └─ Lead generation (bulk)      ──→ [E] LEAD GENERATION
```

---

## [A] DEALER RESEARCH — Analisi singolo dealer

### A1 — Identifica dealer

```
Target input: nome / città / provincia / P.IVA
```

**Fonti da ricercare in ordine:**
1. Google Business + Maps (presenza, recensioni, orari)
2. Autoscout24.it → cerca il dealer come venditore
3. Subito.it / Automobile.it (presenza stock)
4. LinkedIn (dealership profile, titolare)
5. Facebook Business (engagement, post recenti)
6. CoVe DB interno: `SELECT * FROM dealers WHERE ...`

### A2 — Profilo da estrarre

```
OBBLIGATORIO:
- Ragione sociale + P.IVA se disponibile
- Indirizzo + provincia
- Telefono + WhatsApp (se presente)
- Email diretta o form contatto
- Stock stimato (n. auto in vendita)
- Marchi trattati (multi-brand vs mono)
- Anni di attività (fondazione)
- Presenza online (sito, social, marketplace)

OPZIONALE (se trovato):
- Nome titolare / responsabile acquisti
- Fatturato stimato (da info pubbliche)
- Notizie recenti (espansioni, partnership)
- Presenza in fiere (Automotoretrò, Bologna Motor Show)
```

### A3 — CoVe Scoring (dopo raccolta dati)

```python
# Esegui su MacBook o iMac
python3 python/cove/cove_engine_v4.py \
  --dealer-name "NOME" \
  --provincia "XX" \
  --stock-size N \
  --years-active N
# OUTPUT: recommendation (PROCEED/SKIP/VIN_CHECK) + confidence 0.0-1.0
```

**Threshold decision:**
- `confidence >= 0.75` → DEALER_PREMIUM → aggiungi a pipeline
- `0.60 <= confidence < 0.75` → VIN_CHECK → ricerca approfondita
- `confidence < 0.60` → SKIP → non contattare

---

## [B] MARKET RESEARCH — Prezzi e mercato veicoli EU

### B1 — Fonti prezzi veicoli (in ordine di affidabilità)

```
1. Mobile.de (DE)       → prezzi di riferimento Germania
2. AutoScout24.de       → prezzi EU benchmark
3. AutoScout24.it       → prezzi IT per margine
4. Autovit.ro (RO)      → mercato est Europa
5. Otomoto.pl (PL)      → mercato Polonia
6. BCA Group (aste)     → prezzi wholesale reali
```

### B2 — Template analisi prezzo

```
VEICOLO: [marca] [modello] [anno] [km]
─────────────────────────────────────
Prezzo DE (Mobile.de):    €XX.XXX
Prezzo IT equivalente:    €XX.XXX
Delta potenziale:         €X.XXX
Fee ARGOS (success):      €800-1.200
Margine dealer netto:     €X.XXX
ROI dealer:               XXX%
─────────────────────────────────────
ARGOS™ Score: XX/100 CERTIFICATO™
Prima imm.: XX/XX/20XX
km verificati: XX.XXX (LOCKED)
```

### B3 — Query CoVe per analisi mercato

```python
import duckdb
con = duckdb.connect('python/cove/data/cove_tracker.duckdb')

# Trend prezzi ultimi 90 giorni
con.execute("""
  SELECT make, model, AVG(price_de) as avg_de,
         AVG(price_it_potential) as avg_it,
         AVG(confidence) as avg_confidence
  FROM vehicle_analyses
  WHERE analyzed_at >= NOW() - INTERVAL '90 days'
  GROUP BY make, model
  ORDER BY avg_confidence DESC
""").fetchdf()
```

---

## [C] COMPETITOR RESEARCH — Analisi competitor

### Competitor diretti ARGOS

```
1. AutoEurope / EuroAutoImport → scouting EU→IT
2. Marchetti Import → dealer import professionali
3. AutoScout24 dealer IT con import EU
4. Broker veicoli tedeschi (Heycar, mobile.de Händler)
```

### Template analisi competitor

```
COMPETITOR: [nome]
Servizi offerti: ...
Fee struttura: ...
Target clienti: ...
Punti deboli: ...
Leva ARGOS (come differenziarsi): ...
```

---

## [D] REGULATORY RESEARCH — Normativa import EU→IT

### Documenti standard per import veicolo DE→IT

```
1. Certificato di conformità (CoC) → obbligatorio immatricolazione IT
2. Fattura di acquisto (con reverse charge)
3. Documento di trasporto (CMR)
4. Libretto del veicolo tedesco (Fahrzeugbrief/Zulassung)
5. Dichiarazione doganale (se extra-UE, non applicabile DE→IT)
6. Perizia preventiva (facoltativa ma consigliata)
```

**TD fiscale corretto**: TD17 (acquisto servizi), TD18 (acquisto beni intra-UE), TD19 (acquisto beni in IT da soggetto estero)

**Risparmio reverse charge**: €150-200 vs importazione ordinaria

---

## [E] LEAD GENERATION — Ricerca bulk dealer target

### Criteri target primari

```
✅ Provincia: Sud Italia (NA, SA, CE, BA, BR, LE, TA, RC, CZ, PA, CT, ME)
✅ Stock: 30-80 auto
✅ Marchi: multi-brand o focus premium (BMW/Mercedes/Audi)
✅ Anni attività: >5 anni (stabilità)
✅ Presenza: sito o social attivo
✅ Titolare: accesso diretto (no grandi gruppi)

❌ ESCLUDERE: Grandi gruppi (Autotorino, Class Auto, Leasys)
❌ ESCLUDERE: Solo elettrico / flotte aziendali
❌ ESCLUDERE: Mono-brand ufficiale (concessionari autorizzati)
```

### Fonti lead generation

```bash
# AutoScout24 — cerca dealer per provincia
# URL pattern: autoscout24.it/offerte/?...&zip=CODICE&zipr=50

# Carapis API (se configurata)
curl -H "X-Api-Key: $CARAPIS_API_KEY" \
  "https://api.carapis.com/v1/dealers?country=it&region=campania"

# Pagine Gialle — ricerca "concessionari auto usate"
# Google Maps → "concessionari auto usata [città]"
```

### Output lead generation (formato DuckDB)

```python
# Inserisci lead in DB dopo research
import duckdb
con = duckdb.connect('python/cove/data/cove_tracker.duckdb')
con.execute("""
  INSERT INTO dealers (dealer_id, dealer_name, province, phone, email,
                       stock_size, brands, source, analyzed_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
""", [id, name, prov, phone, email, stock, brands, 'deep_research'])
```

---

## ANTI-PATTERN — NON FARE MAI

```
❌ Inventare dati → sempre fonte verificata
❌ Usare prezzi >30 giorni senza ricontrollare
❌ Assumere km senza fonte → MAI deviare da km LOCKED (45.200 per BMW Mario)
❌ Contattare dealer senza CoVe score ≥ 0.60
❌ Research senza output strutturato in DB
```

---

## OUTPUT STANDARD

Ogni deep research deve produrre:
1. **Scheda dealer** (se dealer research) — salvata in DB
2. **CoVe Score** — recommendation + confidence
3. **Pipeline action** — cosa fare con questo lead
4. **Next step** — data e canale contatto
