# S147 — Day 1 Stile Car: pre-flight + invio (target 30/04/2026)

**Sessione**: S147
**Data target**: 30/04/2026 mattina
**Obiettivo unico**: invio Day 1 WhatsApp a Stile Car (Orta Nova FG, 393334254654, RELAZIONALE 8.5)

---

## 0. Letture obbligatorie all'avvio (NON skippare)

```
1. ~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md
   → entry "2026-04-28/29 — iMac IP fix + CLAUDE.md refactor lean"
   → entry "S146 esecuzione prompt Day 1"
   → entry "Identità live Luca Ferretti"

2. ~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/imac_network.md

3. HANDOFF.md (sezione S145 ENTRY POINT, ancora valida operativamente)

4. .planning/launch_luca_ferretti/DAY1_STILE_CAR.md
   → testo Day 1 calibrato RELAZIONALE + 5 risposte pronte + SQL UPDATE post-invio
```

---

## 1. Pre-flight checklist (in ordine, NON skippare)

### 1.1 — Startup check
```bash
bash .claude/scripts/session_start.sh
```
**Atteso**: tutto verde — Skills OK / CLAUDE.md OK 51 lines / Rules 5 files / WA Daemon: connected.
Se WA daemon UNREACHABLE → ssh iMac, `pm2 list`, eventuale resurrect (vedi `imac_network.md` per comandi nvm-aware).

### 1.2 — Listing top candidate ancora vivo
```bash
curl -sIm 5 "https://www.autoscout24.de/angebote/bmw-x3-xdrive20i-70dcd99b-3d68-45ac-ae20-2113e8f3d719" | head -3
```
**Atteso**: `HTTP/2 200` + `content-type: text/html`.
Se 404 / 410 / redirect → il listing è sparito. Re-eseguire scrape live e aggiornare DAY1_STILE_CAR.md con nuovo candidato PRIMA di proseguire:
```bash
python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 --dealer "Stile Car"
```

### 1.3 — DB Stile Car ancora COLD
```bash
ssh gianlucadistasi@192.168.1.12 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT dealer_id, dealer_name, persona_type, score, current_step, outbound_count FROM conversations WHERE dealer_name LIKE '%Stile Car%';\""
```
**Atteso**: `TIER0_FG_001 | Stile Car | RELAZIONALE | 8.5 | COLD | 0`.
Se `current_step` ≠ COLD o `outbound_count` ≠ 0 → STOP, già contattato. Indagare cosa è successo prima di re-inviare.

### 1.4 — Test marker su TEST_FOUNDER (NON Stile Car)
Invio test al numero demo `393314928901` con marker testo per verificare daemon end-to-end:
```bash
ssh gianlucadistasi@192.168.1.12 "curl -s -X POST http://localhost:9191/send \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: \$(cat ~/Documents/app-antigravity-auto/wa-intelligence/.env | grep ARGOS_API_KEY | cut -d= -f2)' \
  -d '{\"phone\":\"393314928901\",\"message\":\"S147 marker $(date +%H%M%S)\",\"dealer_id\":\"TEST_FOUNDER\"}'"
```
**Atteso**: `{"success":true,...}`. Se fallisce → debug daemon prima di Stile Car.

### 1.5 — Pre-warming LinkedIn confermato
Domanda diretta a Luke (o ispezione manuale):
- LinkedIn `/in/luca-ferretti-53b6513b9/`: profilo popolato (foto + About + post fissato)?
- Follow fatti su Stile Car / Sa.My. Auto / Car Plus?
- ≥1 like distribuito tra i 3 dealer?

Se **NO** a qualsiasi punto → SLITTAMENTO 1-2 giorni. Non negoziabile (regola sequenziale credibilità Sud, vedi `.claude/rules/communication.md`).

---

## 2. Invio Day 1 (solo se 1.1-1.5 tutti verdi)

### Testo
Da `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` — versione RELAZIONALE.
**Vincoli**: max 5 righe, NO trigger words ("Germania", "import", "premium", "cerco auto", "estero"), domanda chiusa finale.

### Comando
```bash
ssh gianlucadistasi@192.168.1.12 "curl -s -X POST http://localhost:9191/send \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: \$WA_API_KEY' \
  -d '{\"phone\":\"393334254654\",\"message\":\"<TESTO_DA_DAY1_STILE_CAR_MD>\",\"dealer_id\":\"TIER0_FG_001\"}'"
```
**Atteso**: `success: true`, `message_id` valorizzato.

### Post-invio — SQL UPDATE obbligatorio
```sql
UPDATE conversations
SET current_step = 'DAY1_SENT',
    last_contact_at = datetime('now'),
    outbound_count = outbound_count + 1,
    notes = COALESCE(notes,'') || char(10) || 'S147 Day1 inviato $(date +%Y-%m-%d %H:%M)'
WHERE dealer_id = 'TIER0_FG_001';
```

---

## 3. Post-invio — silenzio osservativo 48h

- **NO follow-up automatico per 48h**
- Monitorare `messages` table per inbound:
  ```bash
  ssh gianlucadistasi@192.168.1.12 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT direction, body, timestamp_it FROM messages WHERE dealer_id='TIER0_FG_001' ORDER BY timestamp_it;\""
  ```
- Se inbound arriva → albero risposte da `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` (5 risposte pronte: quanto costa / chi sei / dove hai preso numero / già importo / no grazie)
- Se silenzio 72h+ → Day 3 follow-up (foto HD + secondo veicolo, vedi `.claude/rules/communication.md`)

---

## 4. Vincoli S147 (NON negoziabili)

- ✋ NO invio se uno qualsiasi del 1.1-1.5 fallisce
- ✋ MAI inviare a 393334254654 senza prima il marker su 393314928901
- ✋ MAX 1 messaggio Day 1 per dealer — se outbound_count > 0 → STOP
- ✋ NO modifiche al testo Day 1 senza approvazione esplicita Luke
- ✋ NO push automatico modifiche repo durante S147 — freeze pre-invio

---

## 5. Fine sessione (se invio andato)

1. Aggiorna MEMORY.md con outcome (success/fail + osservazioni dealer behavior)
2. Aggiorna `HANDOFF.md` con stato post-invio + setup Day 3
3. Crea `prompts/s148_day3_followup_o_response_handling.md` (depends on inbound)
4. `git add HANDOFF.md prompts/s148_*.md && git commit -m "docs(S147): outcome Day1 Stile Car" && git push`

---

## 6. Riferimenti rapidi

- IP iMac: **192.168.1.12** (DHCP reservation attiva)
- WA daemon API key: `$(cat ~/Documents/app-antigravity-auto/wa-intelligence/.env | grep ARGOS_API_KEY)` su iMac
- DB live: `/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite`
- TEST_FOUNDER: 393314928901 (unico numero autorizzato per test)
- Stile Car: 393334254654 — RELAZIONALE 8.5 — TIER0_FG_001
- Top candidate verificato S144: BMW X3 xDrive20i 2022, 66.419km, €34.904 (Autohaus Becker-Tiemann), margine €3.388
- Dossier: `dossiers/ARGOS_BMW_X3_2022_Stile_Car_20260427_112932.pdf`
