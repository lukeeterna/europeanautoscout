# S157 — Scraper fix BMW Serie 3/5 + Mercedes GLC/C/E/GLE (sblocco pipeline E2E)

**Sessione**: S157 (clean context start)
**Scope**: ripristinare scraper E2E "NON FUNZIONANTE" da CLAUDE.md. Diagnosi 404 + fix MODEL_SLUG/selector/API change. Validation: ≥1 listing per modello con `seller_name` non-NULL + CoVe scoring verde.
**Tempo stimato**: ~90min autonomo (timebox)
**Rischio dealer**: ZERO — nessun outreach, nessun messaggio, no go-live.
**Path critico**: sblocca S158 (test founder interattivo CON Luke) → S159 (Day 1 reale Stile Car).

---

## Pre-condizioni S157

| Check | Verifica |
|-------|----------|
| iMac up | `ping -c 1 192.168.1.2` |
| WA daemon online | `ssh ... "curl -s localhost:9191/status"` → `connected` |
| tailscaled standalone | `ssh ... "ps aux \| grep tailscaled \| grep -v grep"` mostra PID |
| PM2 daemons | `ssh ... "pm2 list"` → argos-wa-daemon + argos-cf-monitor online |

🛑 Se KO: recovery via `docs/ops/tailscaled-runbook.md` PRIMA, poi S157.

---

## Phase 1 — Diagnosi 404 (~20min)

### 1.1 Scraper layout & MODEL_SLUG attuali
```bash
# File scraper principale
cat tools/scrapers/autoscout_scraper.py | head -80
# Mapping MODEL_SLUG (cercare struttura)
grep -nE "MODEL_SLUG|model_slug|brand|model" tools/scrapers/autoscout_scraper.py | head -30
# Models attualmente OK vs ROTTI (da CLAUDE.md):
# OK: BMW X3/X1/X5, Audi Q5/A4
# ROTTI: BMW Serie 3/5, Mercedes GLC/C/E/GLE
```

### 1.2 Test scraper diretto su 1 modello rotto
```bash
# BMW Serie 3 budget 30k
python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" --budget 30000 --dealer "DEBUG_S157" 2>&1 | tee /tmp/s157_bmw3_debug.log | tail -50
# Cattura: URL costruita, HTTP status, response body se 404, error trace
grep -E "url|404|ERROR|exception" /tmp/s157_bmw3_debug.log | head -20
```

### 1.3 Manual fetch URL costruita per ispezione
```bash
# Estrai URL dal log + curl manuale con headers browser-like
URL=$(grep -oE 'https://[^[:space:]]+autoscout[^[:space:]]+' /tmp/s157_bmw3_debug.log | head -1)
echo "URL costruita: $URL"
# Test con headers reali
curl -s -o /tmp/s157_response.html -w "HTTP:%{http_code}\nTIME:%{time_total}\n" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept-Language: it-IT,it;q=0.9,en;q=0.8" \
  -m 15 "$URL"
# Se 404: il path è cambiato lato AS24
# Se 200 ma HTML diverso: selector/parser breaking
head -100 /tmp/s157_response.html
```

### 1.4 Confronto con modello OK (BMW X3 baseline)
```bash
python3 tools/on_demand_runner.py --marca BMW --modello "X3" --budget 40000 --dealer "DEBUG_X3" 2>&1 | tail -20
# Compara URL pattern + selectors usati. Differenza tra OK e ROTTO è il fix path.
```

### 1.5 Documenta findings
Crea `.planning/S157-DIAGNOSIS.md` con:
- URL pattern OK vs ROTTO
- HTTP response code & body sample
- Root cause hypothesis: (a) MODEL_SLUG mapping errato, (b) selector CSS cambiato, (c) URL path AS24 nuovo, (d) geo-block, (e) altro

---

## Phase 2 — Fix mirato (~40min)

In base alla diagnosi:

### Caso A: MODEL_SLUG errato
```bash
# Cerca mapping nel file scraper
grep -nB2 -A5 "MODEL_SLUG\|series\|serie" tools/scrapers/autoscout_scraper.py
# Verifica slug AS24 corretto navigando autoscout24.it manualmente:
# BMW Serie 3 → slug atteso: "serie-3" o "3-series" o "3er"
# Aggiorna mapping con slug corretto
```

### Caso B: Selector CSS cambiato (parser breaking)
```bash
# Estrai selectors usati
grep -nE "css|select|find|xpath" tools/scrapers/autoscout_scraper.py | head -20
# Ispeziona /tmp/s157_response.html per nuovi selectors
# Fix BeautifulSoup/Playwright selectors
```

### Caso C: URL path cambiato AS24
```bash
# Aggiorna URL builder
grep -nE "BASE_URL|build_url|search_url" tools/scrapers/autoscout_scraper.py
# Test con nuovo path
```

### Caso D: Geo-block / rate limit
```bash
# Verifica se response è Cloudflare challenge / 429
grep -E "captcha|rate|blocked|challenge" /tmp/s157_response.html
# Mitigation: rotation User-Agent + delay tra requests + Tailscale exit-node se serve geo-IT
```

### Caso E: Altro (fallback)
- Documenta in BACKLOG, propone alternative (Mobile.de scraping, AutoScout24 API ufficiale a pagamento NON ammesso, scraping da search Google CSE, etc)

---

## Phase 3 — Validation (~20min)

### 3.1 Test ogni modello rotto
```bash
for MODEL in "Serie 3" "Serie 5"; do
  echo "=== BMW $MODEL ==="
  python3 tools/on_demand_runner.py --marca BMW --modello "$MODEL" --budget 35000 --dealer "S157_VALIDATION" 2>&1 | tail -10
done
for MODEL in "Classe C" "Classe E" "GLC" "GLE"; do
  echo "=== Mercedes $MODEL ==="
  python3 tools/on_demand_runner.py --marca Mercedes --modello "$MODEL" --budget 45000 --dealer "S157_VALIDATION" 2>&1 | tail -10
done
```

### 3.2 Verifica DuckDB cove_results
```bash
ssh gianlucadistasi@192.168.1.2 'duckdb /path/to/cove_tracker.duckdb "SELECT brand, model, COUNT(*) FROM cove_results WHERE analyzed_at > now() - INTERVAL 1 HOUR GROUP BY 1,2"'
# Deve mostrare ≥1 row per ogni modello fixato
```

### 3.3 Verifica seller_name non-NULL
```bash
# Era issue noto AS24.it (CLAUDE.md "seller_name NULL su AS24.it")
ssh gianlucadistasi@192.168.1.2 'duckdb /path/to/cove_tracker.duckdb "SELECT brand, model, seller_name FROM cove_results WHERE analyzed_at > now() - INTERVAL 1 HOUR LIMIT 10"'
# Se seller_name NULL: secondo bug da fixare (estrazione dealer name dal listing)
```

### 3.4 GREEN GATE
- ≥1 listing per modello (Serie 3, Serie 5, Classe C, Classe E, GLC, GLE)
- `seller_name` not NULL
- CoVe scoring eseguito (`recommendation` field popolato)

🔴 Se non green: documenta in `.planning/S157-PARTIAL.md` con dettaglio per modello + hypothesis fix S158-bis.

---

## Phase 4 — Docs + commit (~10min)

- [ ] `.planning/S157-DIAGNOSIS.md`: findings completi (root cause + fix applicato)
- [ ] `BACKLOG.md`: marca "scraper 404 BMW Serie 3/5 + Mercedes GLC/C/E/GLE" → ✅ FIXED S157 (o PARTIAL se non tutti modelli)
- [ ] `BACKLOG.md`: marca "seller_name NULL su AS24.it" → FIXED se applicabile
- [ ] `HANDOFF.md`: STATO CORRENTE → S157 CHIUSO VERDE/PARTIAL
- [ ] Memory MEMORY.md entry S157
- [ ] Commit: `fix(s157): scraper BMW Serie 3/5 + Mercedes GLC/C/E/GLE` o variant
- [ ] Push

---

## Phase 5 — STOP (regola feedback_no_live_without_test.md)

🛑 NESSUN prompt S158 auto-creato. Luke deciderà next sprint:
- **S158 TEST FOUNDER INTERATTIVO** (CON Luke davanti, smoke E2E con veicolo reale prodotto S157)
- **Iteration scraper** (se PARTIAL S157)
- **Altro sprint**

---

## Vincoli S157

- ✋ NO outreach dealer reale
- ✋ NO messaggi WA a numeri ≠ TEST_FOUNDER (in S157 idealmente NESSUN messaggio WA — è scraper)
- ✋ NO modificare `src/cove/cove_engine_v4.py` (rule cove.md)
- ✋ NO Tailscale.app GUI ops (usa `tailscaled` standalone se serve)
- ✋ Timebox 90min — se non risolto, documenta PARTIAL e ferma

---

## Out of scope S157

- Test founder interattivo → S158
- Day 1 dealer reale → S159
- CoVe engine refactor → defer
- Health monitoring → defer
- Day 1 sequence revision V4 → defer

---

## Target di fine S157

✅ ≥1 listing per ogni modello rotto (BMW Serie 3, Serie 5; Mercedes Classe C, E, GLC, GLE)
✅ `seller_name` not NULL nei risultati
✅ CoVe scoring eseguito su listing nuovi
✅ Diagnosis + fix documentati
✅ Commit pushato
✅ S157 CHIUSO VERDE/PARTIAL in HANDOFF + MEMORY

❌ NON in S157: outreach, Day 1, founder test, V4 messaggi

---

## Skill ARGOS da caricare

`/scraper-ops` quando entri in fix scraper (è skill dedicata).

---

## Riferimenti

- CLAUDE.md "Scraper ROTTI": BMW Serie 3/5, Mercedes GLC/C/E/GLE
- CLAUDE.md "Scraper OK": BMW X3/X1/X5, Audi Q5/A4 (baseline confronto)
- File principale: `tools/scrapers/autoscout_scraper.py`
- Runner: `tools/on_demand_runner.py`
- DB: `src/cove/data/cove_tracker.duckdb` (DuckDB) on iMac via SSH
- Skill: `/scraper-ops`

---

## Resume path se compaction

Stato tracciato in TaskCreate da Phase 1. Se compaction:
1. Leggi questa entry + ultima MEMORY.md S157
2. Verifica diagnosis salvata `.planning/S157-DIAGNOSIS.md`
3. Riprendi da Phase 2 (fix) o Phase 3 (validation) in base a stato
