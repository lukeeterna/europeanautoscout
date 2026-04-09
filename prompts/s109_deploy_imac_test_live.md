# S109 — Deploy iMac + Test E2E Live

## Contesto

S108 ha completato la Settimana 0: contratto con Art. 5-bis, requirements.txt, DAY1_MIXED fix,
case study template, formazione kit, verifica AS24 di 16 dealer (13 VALIDATI).
Enrichment dei 13 dealer in corso (email, website, social).

**Prerequisito S109:** iMac ONLINE e raggiungibile via SSH.

---

## BLOCCO 1 — Deploy S106 su iMac (BLOCCANTE)

**Skill:** `/devops-automator`
**Agent:** `agent-ops`

### 1.1 Sync codice
```bash
# Da MacBook
rsync -avz --delete \
  --exclude '.git' --exclude '__pycache__' --exclude '.env' \
  wa-intelligence/ gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/wa-intelligence/
```

### 1.2 Install requirements
```bash
ssh gianlucadistasi@192.168.1.2 "cd ~/Documents/app-antigravity-auto/wa-intelligence && pip3 install -r requirements.txt"
```

### 1.3 Restart PM2
```bash
ssh gianlucadistasi@192.168.1.2 "pm2 restart wa-daemon && pm2 save"
```

### 1.4 Health check
```bash
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"
```

---

## BLOCCO 2 — Import dealer profilati nel DB iMac

**Agent:** `agent-ops`

### 2.1 Sync file dealer
```bash
rsync -avz research/s106_dealer_profiled_30.json research/s108_dealer_enriched_final.json \
  tools/import_profiled_dealers.py \
  gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/
```

### 2.2 Import in SQLite
```bash
ssh gianlucadistasi@192.168.1.2 "cd ~/Documents/app-antigravity-auto && python3 tools/import_profiled_dealers.py"
```

### 2.3 Verifica DB
```bash
ssh gianlucadistasi@192.168.1.2 "cd ~/Documents/app-antigravity-auto && sqlite3 dealer_network.sqlite 'SELECT COUNT(*) FROM dealers WHERE archetype IS NOT NULL'"
```

---

## BLOCCO 3 — Migrazione scheduler.py DuckDB → SQLite

**Skill:** `/backend-architect`

`wa-intelligence/scheduler.py` usa `duckdb.connect()` per leggere `conversations`.
Tutto il resto del pipeline usa `sqlite3` con `dealer_network.sqlite`.

### 3.1 Modificare scheduler.py
- Sostituire `import duckdb` con `import sqlite3`
- Cambiare `duckdb.connect(DB_PATH)` → `sqlite3.connect(DB_PATH)`
- Aggiornare `DB_PATH` default a `dealer_network.sqlite`
- Verificare che la query SQL sia compatibile sqlite3

### 3.2 Test locale
```bash
python3 wa-intelligence/scheduler.py
```

---

## BLOCCO 4 — Test E2E Live con Daemon

**Skill:** `/api-tester`

### 4.1 Test outbound guard
```bash
ssh gianlucadistasi@192.168.1.2 "curl -s -X POST localhost:9191/send \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: [API_KEY]' \
  -d '{\"phone\": \"393314928901\", \"message\": \"Test E2E S109\", \"dry_run\": true}'"
```

### 4.2 Test inbound classification
Inviare messaggio test al numero WA business e verificare:
- classify() categorizza correttamente
- select_template() trova il template giusto
- validate() non blocca il messaggio
- Telegram riceve notifica human-in-loop

### 4.3 Test full cycle
```
COLD dealer → /send DAY1 → risposta simulata → classify → template → validate → risposta
```

---

## BLOCCO 5 — Primo outreach VERO (se test E2E passano)

**Skill:** `/skill-argos`
**Agent:** `agent-sales`

### 5.1 Selezionare 3-5 dealer dal TOP 8
Criteri: email trovata, WA confermato, annunci >= 25

### 5.2 Generare messaggio DAY1 personalizzato
Per ogni dealer:
- Usare DAY1_PREMIUM con source e brand_focus reali
- Allegare dossier veicolo specifico per il brand del dealer (se disponibile in CoVe DB)

### 5.3 Invio con guardrails
```bash
# Invio singolo con dry_run=false
curl -X POST localhost:9191/send \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: [API_KEY]' \
  -d '{"phone": "[PHONE]", "message": "[MSG]", "dry_run": false}'
```

### 5.4 Monitorare risposte
- Telegram alert per ogni risposta
- Classificazione automatica
- Nessun auto-reply senza approvazione umana per i primi 5

---

## BLOCCO 6 — Materiali deployment

### 6.1 Sync materiali su iMac
```bash
rsync -avz tools/materiali/ gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/tools/materiali/
```

### 6.2 Generare PDF contratto
```bash
# Da Chrome headless su iMac
google-chrome --headless --print-to-pdf=contratto_argos.pdf tools/materiali/contratto_incarico_scouting.html
```

---

## File chiave S109

```
Verifica dealer:     research/s108_dealer_as24_verification.md
Enrichment finale:   research/s108_dealer_enriched_final.json
Contratto:           tools/materiali/contratto_incarico_scouting.html (con Art.5-bis)
Case study:          tools/materiali/case_study_template.html
Formazione:          tools/materiali/formazione_dealer_kit.md
Scheduler:           wa-intelligence/scheduler.py (da migrare)
```

## Regole S109

- Test E2E DEVE passare PRIMA di qualsiasi outreach reale
- Primo outreach: max 3-5 dealer, con approvazione umana per ogni risposta
- Nessun auto-reply autonomo per i primi 5 dealer
- Commit dopo ogni blocco completato
