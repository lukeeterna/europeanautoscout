---
name: cove-engine
description: >
  Skill enterprise per il motore CoVe 2026 (Confidence of Vehicle Evaluation).
  Copre: verifica schema DuckDB, esecuzione scoring dealer/veicolo, aggiornamento pipeline,
  analisi confidence, query advanced, manutenzione DB.
  TRIGGER su: "cove score", "cove engine", "confidence dealer", "scoring veicolo",
  "aggiorna pipeline cove", "query duckdb", "verifica schema", "recommendation",
  "analyzed_at", "cove_tracker", "dealer_network.duckdb", "cove v4", "bayesian",
  "recommendation proceed skip", "vin check threshold", "dealer premium threshold".
  MAI modificare cove_engine_v4.py — solo leggere e invocare.
version: 1.0.0
allowed-tools: Bash, Read, Grep
---

# ARGOS™ CoVe Engine 2026 — Skill Enterprise

## REGOLE ASSOLUTE (NON DEROGABILI)

```
✅ CORRETTO          ❌ SBAGLIATO
recommendation       verdict
analyzed_at          created_at
confidence 0.0-1.0   confidence %

THRESHOLDS IMMUTABILI:
  DEALER_PREMIUM_THRESHOLD = 0.75
  VIN_CHECK_THRESHOLD      = 0.60

HARD LIMITS:
  sleep(15) | Semaphore(5) | DAILY_LIMIT=30

FIELD recommendation VALUES:
  'PROCEED' | 'SKIP' | 'VIN_CHECK'

FILE:
  NON MODIFICARE: python/cove/cove_engine_v4.py
  DB principale:  python/cove/data/cove_tracker.duckdb
  DB dealer:      ~/Documents/app-antigravity-auto/dealer_network.duckdb (iMac)
```

---

## WORKFLOW DECISIONALE

```
TASK RICEVUTO
     │
     ├─ Score dealer / veicolo     ──→ [A] SCORING PROTOCOL
     ├─ Query / read DB            ──→ [B] QUERY PROTOCOL
     ├─ Update stato pipeline      ──→ [C] UPDATE PROTOCOL
     ├─ Verifica schema            ──→ [D] SCHEMA PROTOCOL
     └─ Manutenzione / backup      ──→ [E] MAINTENANCE PROTOCOL
```

---

## [A] SCORING PROTOCOL — Valutazione dealer/veicolo

### A1 — Invocare CoVe Engine v4

```bash
# Dal MacBook (path enterprise)
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
python3 python/cove/cove_engine_v4.py \
  --dealer-id "DEALER_ID" \
  --dealer-name "Nome Dealer" \
  --provincia "NA" \
  --stock-size 45 \
  --years-active 12

# OUTPUT ATTESO:
# {
#   "recommendation": "PROCEED",   ← MAI "verdict"
#   "confidence": 0.82,
#   "analyzed_at": "2026-03-13T16:00:00+01:00",  ← MAI "created_at"
#   "factors": {...}
# }
```

### A2 — Interpretazione risultato

```
confidence >= 0.75  → PROCEED        → Aggiungi a pipeline outreach
0.60 <= c < 0.75   → VIN_CHECK       → Deep research veicolo + dealer
confidence < 0.60  → SKIP            → Non contattare (log motivo)
```

### A3 — Salva score in DB

```python
import duckdb, datetime

DB = 'python/cove/data/cove_tracker.duckdb'
con = duckdb.connect(DB)

con.execute("""
  INSERT OR REPLACE INTO vehicle_analyses (
    dealer_id, dealer_name, recommendation, confidence,
    analyzed_at, province, stock_size
  ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", [
    dealer_id,
    dealer_name,
    result['recommendation'],     # 'PROCEED' | 'SKIP' | 'VIN_CHECK'
    result['confidence'],         # float 0.0-1.0
    datetime.datetime.now(datetime.timezone.utc).isoformat(),  # analyzed_at
    provincia,
    stock_size
])
con.commit()
con.close()
```

---

## [B] QUERY PROTOCOL — Lettura stato pipeline

### B1 — Query standard

```python
import duckdb
con = duckdb.connect('python/cove/data/cove_tracker.duckdb')

# Pipeline attiva
con.execute("""
  SELECT dealer_name, recommendation, confidence, analyzed_at
  FROM vehicle_analyses
  WHERE recommendation = 'PROCEED'
    AND confidence >= 0.75
  ORDER BY confidence DESC, analyzed_at DESC
  LIMIT 20
""").fetchdf()

# Stato dealer Mario
con.execute("""
  SELECT dealer_name, current_step, recommendation, analyzed_at
  FROM conversations
  WHERE dealer_name = 'Mario Orefice'
  ORDER BY analyzed_at DESC LIMIT 1
""").fetchone()

# Statistiche pipeline
con.execute("""
  SELECT recommendation, COUNT(*) as n, ROUND(AVG(confidence),2) as avg_conf
  FROM vehicle_analyses
  GROUP BY recommendation
""").fetchdf()
```

### B2 — Query dealer_network.duckdb (iMac)

```bash
# Via SSH iMac
ssh gianlucadistasi@192.168.1.12 "python3 -c \"
import duckdb
DB = '/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.duckdb'
con = duckdb.connect(DB)
# tabelle disponibili
print(con.execute('SHOW TABLES').fetchdf())
\""
```

---

## [C] UPDATE PROTOCOL — Aggiornamento stato pipeline

### C1 — Aggiorna stato dealer dopo contatto

```python
import duckdb, datetime

con = duckdb.connect('python/cove/data/cove_tracker.duckdb')

con.execute("""
  UPDATE conversations
  SET current_step        = ?,
      last_contact_at     = ?,
      recommendation      = ?,    -- MAI verdict
      analyzed_at         = ?     -- MAI created_at
  WHERE dealer_name = ?
""", [
    'WA_DAY1_SENT',
    datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'IN_PROGRESS',
    datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'Mario Orefice'
])
con.commit()
```

### C2 — Registra risposta dealer

```python
# Risposta positiva → registra opportunità
con.execute("""
  INSERT INTO opportunities (
    dealer_id, dealer_name, veicolo, prezzo_de, fee,
    recommendation, confidence, analyzed_at
  ) VALUES (?, ?, ?, ?, ?, 'PROCEED', 0.90, ?)
""", [
    'MARIO_001', 'Mario Orefice',
    'BMW 330i G20 2020 45200km',
    27800.0, 800.0,
    datetime.datetime.now(datetime.timezone.utc).isoformat()
])
```

### C3 — Chiudi dealer (no response / rifiuto)

```python
con.execute("""
  UPDATE conversations
  SET recommendation = 'SKIP',
      current_step   = 'CLOSED_NO',
      analyzed_at    = CURRENT_TIMESTAMP
  WHERE dealer_name = ?
""", ['Nome Dealer'])
```

---

## [D] SCHEMA PROTOCOL — Verifica e debug schema

### D1 — Verifica schema corretto

```python
import duckdb
con = duckdb.connect('python/cove/data/cove_tracker.duckdb')

# Elenca tabelle
print("TABLES:", con.execute("SHOW TABLES").fetchdf())

# Schema conversations
print("SCHEMA:", con.execute("DESCRIBE conversations").fetchdf())

# Controlla che NON esistano campi sbagliati
cols = [r[0] for r in con.execute("DESCRIBE conversations").fetchall()]
assert 'verdict' not in cols,     "❌ ERRORE: campo 'verdict' trovato — usare 'recommendation'"
assert 'created_at' not in cols,  "❌ ERRORE: campo 'created_at' trovato — usare 'analyzed_at'"
assert 'recommendation' in cols,  "❌ ERRORE: campo 'recommendation' mancante"
assert 'analyzed_at' in cols,     "❌ ERRORE: campo 'analyzed_at' mancante"
print("✅ Schema CoVe 2026 verificato")
```

### D2 — Migration se schema legacy

```python
# SOLO se trovati campi legacy — mai se schema è corretto
# con.execute("ALTER TABLE conversations RENAME COLUMN verdict TO recommendation")
# con.execute("ALTER TABLE conversations RENAME COLUMN created_at TO analyzed_at")
# Verificare SEMPRE prima di eseguire
```

---

## [E] MAINTENANCE PROTOCOL — Backup e manutenzione

### E1 — Backup DB prima di modifiche

```bash
# MacBook
cp python/cove/data/cove_tracker.duckdb \
   python/cove/data/cove_tracker_backup_$(date +%Y%m%d_%H%M%S).duckdb

# iMac (via SSH)
ssh gianlucadistasi@192.168.1.12 "
  cp ~/Documents/app-antigravity-auto/dealer_network.duckdb \
     ~/Documents/app-antigravity-auto/dealer_network_backup_\$(date +%Y%m%d_%H%M%S).duckdb
  echo '✅ Backup creato'
"
```

### E2 — Verifica integrità DB

```python
import duckdb
con = duckdb.connect('python/cove/data/cove_tracker.duckdb')

# Check record count
tables = con.execute("SHOW TABLES").fetchall()
for (table,) in tables:
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count} records")

# Check recommendation values validi
invalid = con.execute("""
  SELECT COUNT(*) FROM vehicle_analyses
  WHERE recommendation NOT IN ('PROCEED', 'SKIP', 'VIN_CHECK')
""").fetchone()[0]
print(f"  Record con recommendation non valida: {invalid}")
```

---

## ANTI-PATTERN — NON FARE MAI

```
❌ Modificare cove_engine_v4.py → IMMUTABILE
❌ Usare 'verdict' al posto di 'recommendation'
❌ Usare 'created_at' al posto di 'analyzed_at'
❌ Skippare CoVe score → contattare dealer senza confidence ≥ 0.60
❌ Hardcode credenziali in query → solo .env
❌ Cancellare record da DB senza backup
❌ Scrivere 'CoVe', 'RAG', 'AI', 'Claude' nei messaggi ai dealer
```

---

## PATH CRITICI

```
CoVe Engine v4 (IMMUTABILE):  python/cove/cove_engine_v4.py
DB MacBook:                   python/cove/data/cove_tracker.duckdb
DB iMac (dealer network):     ~/Documents/app-antigravity-auto/dealer_network.duckdb
Personality engine:           src/marketing/dealer_personality_engine.py
Objection handler:            src/marketing/objection_handler.py
Fee calculator:               tools/fee_calculator.py
```
