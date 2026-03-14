---
name: skill-data-official
description: >
  Plugin ufficiale Anthropic Data adattato per ARGOS. Genera SQL ottimizzato per DuckDB,
  analisi pipeline dealer, validazione dati CoVe, dashboard HTML interattive.
  TRIGGER su: "scrivi query DuckDB", "analisi dati pipeline", "dashboard dealer",
  "sql cove_tracker", "valida dati", "report statistico", "visualizzazione", "esporta CSV".
version: 1.0.0
allowed-tools: Bash, Read, Write
---

# ARGOS Data Intelligence — Official Plugin Layer

> **Fonte**: github.com/anthropics/knowledge-work-plugins/data (Apache 2.0)
> **Target DB**: DuckDB `data/db/cove_tracker.duckdb` (read-only default)
> **Adattamento**: ARGOS Automotive dealer pipeline analytics

---

## COMANDI DISPONIBILI

### /write-query — Genera SQL DuckDB
Genera SQL ottimizzato per DuckDB dialect. Sempre read-only (SELECT).

**Input**: descrizione in italiano di cosa si vuole analizzare
**Output**: query SQL pronta, commentata, con spiegazione

**Regole DuckDB** (differenze da PostgreSQL/MySQL):
```sql
-- Timestamp: NOW() o CURRENT_TIMESTAMP
-- Intervalli: INTERVAL '30 days' (non INTERVAL 30 DAY)
-- String agg: STRING_AGG(col, ', ')
-- Type cast: col::VARCHAR, col::FLOAT
-- Date diff: DATE_DIFF('day', start_date, end_date)
-- Read-only connection: duckdb.connect(path, read_only=True)
```

### /analyze — Analisi dati pipeline
Risponde a domande sui dati esistenti.

**Pattern di analisi**:
- Quanti dealer per recommendation?
- Trend confidence nel tempo
- Dealer mai contattati con PROCEED
- Conversione per archetipo

### /validate — QA prima di decisioni
Verifica coerenza dati prima di azioni commerciali.

**Check list**:
- recommendation in ('PROCEED', 'SKIP', 'VIN_CHECK')
- confidence tra 0.0 e 1.0
- analyzed_at non nel futuro
- dealer_name non null
- duplicati su chiave primaria

### /build-dashboard — Dashboard HTML interattiva
Genera HTML con Chart.js per visualizzazione pipeline.

**Template base**:
```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>body{font-family:sans-serif;padding:20px;background:#f5f5f5}</style>
</head>
<body>
  <h1>ARGOS Pipeline Dashboard</h1>
  <canvas id="pipeline" width="400" height="200"></canvas>
  <script>
    const ctx = document.getElementById('pipeline');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['PROCEED', 'VIN_CHECK', 'SKIP'],
        datasets: [{
          label: 'Dealer per recommendation',
          data: [/* da DuckDB */],
          backgroundColor: ['#22c55e', '#f59e0b', '#ef4444']
        }]
      }
    });
  </script>
</body>
</html>
```

---

## SCHEMA COVE_TRACKER (reference)

```sql
-- Campi certificati (NON modificare nomi)
recommendation  VARCHAR   -- 'PROCEED' | 'SKIP' | 'VIN_CHECK'  ← NON verdict
analyzed_at     TIMESTAMPTZ  -- ← NON created_at
confidence      FLOAT     -- 0.0 – 1.0
dealer_name     VARCHAR
vehicle_info    VARCHAR   -- JSON o stringa
persona_type    VARCHAR   -- archetipo ARGOS (se popolato)

-- THRESHOLDS (immutabili):
-- PROCEED:    confidence >= 0.75
-- VIN_CHECK:  confidence >= 0.60 AND < 0.75
-- SKIP:       confidence < 0.60
```

---

## QUERY LIBRARY (pronte all'uso)

```sql
-- 1. Pipeline summary
SELECT recommendation, COUNT(*) as n, ROUND(AVG(confidence),3) as avg_conf
FROM cove_tracker GROUP BY 1 ORDER BY 2 DESC;

-- 2. Top PROCEED non contattati (ultimi 30gg)
SELECT dealer_name, confidence, analyzed_at
FROM cove_tracker
WHERE recommendation = 'PROCEED'
  AND analyzed_at > NOW() - INTERVAL '30 days'
ORDER BY confidence DESC LIMIT 10;

-- 3. VIN_CHECK scadenti (> 7gg senza follow-up)
SELECT dealer_name, vehicle_info, analyzed_at,
       DATE_DIFF('day', analyzed_at::DATE, CURRENT_DATE) as giorni
FROM cove_tracker
WHERE recommendation = 'VIN_CHECK'
  AND DATE_DIFF('day', analyzed_at::DATE, CURRENT_DATE) > 7
ORDER BY giorni DESC;

-- 4. Distribuzione per archetipo
SELECT persona_type, COUNT(*) as n, AVG(confidence) as avg_conf
FROM cove_tracker
WHERE persona_type IS NOT NULL
GROUP BY 1 ORDER BY 3 DESC;

-- 5. Health check schema
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'cove_tracker';
```

---

## COME ESEGUIRE

```python
# Locale (MacBook)
import duckdb
conn = duckdb.connect('data/db/cove_tracker.duckdb', read_only=True)
result = conn.execute("""
  SELECT recommendation, COUNT(*) as n FROM cove_tracker GROUP BY 1
""").fetchdf()
print(result)
conn.close()
```

```bash
# Via SSH iMac
ssh gianlucadistasi@192.168.1.12 "
  export PATH=/usr/local/bin:\$PATH
  python3 -c \"
import duckdb
conn = duckdb.connect('/Users/gianlucadistasi/Documents/app-antigravity-auto/data/db/cove_tracker.duckdb', read_only=True)
print(conn.execute('SELECT recommendation, COUNT(*) FROM cove_tracker GROUP BY 1').fetchall())
\"
"
```

---

## NOTE DI AGGIORNAMENTO

**v1.0.0** (S51 — 2026-03-14): Creazione da knowledge-work-plugins/data adattato per DuckDB ARGOS
