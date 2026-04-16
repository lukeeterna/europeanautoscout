# S129 — Shadow Mode: Primo Dealer Reale

## Contesto

S128 ha completato Phase 2 minima:
- 37/37 validator tests PASS
- 6/6 E2E checkpoint su TEST_FOUNDER PASS
- Digest Telegram inviato, Luke ha visto il messaggio generato

**Phase 2 è pronta. S129 è il primo shadow mode su dealer reale.**

Source of truth: `memory/MEMORY.md` + `HANDOFF.md`

---

## Prerequisiti (verifica all'avvio)

```bash
# 1. iMac online
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"

# 2. Dealer candidati da DB
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  'SELECT dealer_id, dealer_name, city, persona_type, score FROM conversations \
   WHERE dealer_id != \"TEST_FOUNDER\" AND current_step IN (\"PENDING\",\"COLD\") \
   AND outbound_count = 0 ORDER BY score DESC LIMIT 5'"
```

---

## Step 1 — Scegliere dealer + ottenere signal reale

Candidati prioritari (score > 7.5):
- `TIER0_AV_001` Car Plus (Grottaminarda AV) — RAGIONIERE — score 7.5
- `TIER0_FG_001` Stile Car (Orta Nova FG) — RELAZIONALE — score 8.5
- `TIER0_CS_001` Sa.My. Auto (Rende CS) — TECNICO — score 7.0

**FONDATORE decide quale dealer avviare. Non procedere senza esplicita autorizzazione.**

Una volta scelto il dealer:
```bash
# Scrape on-demand per signal reale
python3 tools/on_demand_runner.py --dealer "Car Plus" --budget 50000 --marca BMW
# Output: listing con days_on_market reali da AutoScout24
```

---

## Step 2 — Stock reale per GATE-ICP-001

```python
# Query cove_tracker.duckdb per stock del dealer
import duckdb
con = duckdb.connect("src/cove/data/cove_tracker.duckdb", read_only=True)
rows = con.execute("SELECT make, COUNT(*) FROM vehicle_listings WHERE dealer_id=? GROUP BY make", ["dealer_id"]).fetchall()
```

Se DuckDB non ha dati: scrape stock dal sito del dealer o usa stima conservativa.

---

## Step 3 — Genera candidato via batch_generator

```bash
# DRY RUN prima (obbligatorio)
python3 .claude/skills/human-first-outreach/scripts/batch_generator.py \
  --test-founder --dry-run --mode shadow

# Se dry-run OK, genera candidato reale
python3 .claude/skills/human-first-outreach/scripts/batch_generator.py \
  --mode shadow  # senza --test-founder
```

**batch_generator invia digest Telegram a Luke con:**
- Nome dealer, archetipo, ICP tier
- Messaggio generato (con days_on_market ESATTO)
- rule_id log del validator

---

## Step 4 — Luke approva via Telegram

**NON inviare prima che Luke risponda al digest con approvazione esplicita.**

La risposta di approvazione attesa: "OK" o "OK dealer_id"

---

## Step 5 — Invio WA via daemon

Solo dopo approvazione founder:
```bash
# Via curl a wa-daemon su iMac
ssh gianlucadistasi@192.168.1.2 "curl -s -X POST http://localhost:9191/send \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: h_65WFGPMtlgROInLfZtU5TM8hFlVLfYLrn8vSV6kko' \
  -d '{\"phone\":\"<numero>\",\"message\":\"<testo>\",\"dealer_id\":\"<id>\"}'"
```

---

## 3 metriche da tracciare dopo shadow mode (30 messaggi)

1. Reply rate assoluto (quanti hanno risposto)
2. Dei non-risposti: premium_concentration < 30% vs >= 30% (valida GATE-ICP)
3. Messaggi bloccati dal validator: per quale rule_id (valida HARD rules)

---

## Definition of Done S129

- Almeno 1 messaggio inviato a dealer reale in shadow mode
- validation_log ha entry reale con rule_id per quel dealer
- Nessuna risposta dealer → registrata come "silenzio Day 1" (normal)
- Luke ha visto il digest e approvato prima dell'invio
