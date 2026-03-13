---
name: argos-outreach-automation
description: >
  Skill enterprise per automazione completa outreach dealer COMBARETROVAMIAUTO/ARGOS™.
  Copre OGNI task di automazione commerciale: WhatsApp auth+invio, email, sequenze
  multi-step, gestione stato dealer, anti-ban, persona detection, objection handling.
  TRIGGER OBBLIGATORIO su qualsiasi di questi pattern: "invia whatsapp", "messaggio mario",
  "sequenza outreach", "contatta dealer", "follow-up", "email day 7", "wa day 12",
  "stato dealer", "obiezione", "persona classifier", "argosautomotive", "wa sender",
  "autentica whatsapp", "QR whatsapp", "sessione whatsapp", "dealer pipeline",
  "automazione commerciale", "outreach automatico".
  MAI procedere senza leggere questa skill. MAI usare QR nel terminale SSH.
version: 2.0.0
allowed-tools: Bash, Read, Write
---

# ARGOS™ Outreach Automation — Skill Enterprise CoVe 2026

## HARDWARE MAP (immutabile)

| Macchina | Ruolo | IP |
|---|---|---|
| iMac 2012 Intel i5 | Server sempre acceso, esecuzione processi | 192.168.1.12 |
| MacBook | Client sviluppo, portabile | locale |
| Redmi Note 9 Pro | Android con SIM Very Mobile IT | fisico |
| Connessione | SSH via Tailscale | `ssh gianlucadistasi@192.168.1.12` |

**REGOLA ASSOLUTA:** iMac = NO Docker. Tutto gira con Node.js nativo.

---

## ERRORI NOTI — NON RIPETERE

| Errore | Causa | Fix |
|---|---|---|
| QR nel terminale SSH | SSH non interattivo | Servire QR via HTTP porta 8765 |
| "messaggio inviato" falso | `~/.wwebjs_auth/` assente | Verificare sessione PRIMA di dichiarare successo |
| WAHA su iMac | Richiede Docker | Usare whatsapp-web.js nativo |
| `verdict` nel DB | Campo errato | Usare `recommendation` |
| `created_at` nel DB | Campo errato | Usare `analyzed_at` |
| km BMW diversi da 45.200 | Dato non locked | 45.200 è IMMUTABILE |

---

## WORKFLOW DECISIONALE

```
TASK RICEVUTO
     │
     ├─ WhatsApp (auth/invio) ──────→ [A] WA PROTOCOL
     ├─ Email outreach ─────────────→ [B] EMAIL PROTOCOL  
     ├─ Sequenza multi-step ────────→ [C] SEQUENCE PROTOCOL
     ├─ Stato dealer / DuckDB ──────→ [D] STATE PROTOCOL
     ├─ Persona / obiezione ────────→ [E] PERSONA PROTOCOL
     └─ Setup infrastruttura ───────→ [F] SETUP PROTOCOL
```

---

## [A] WA PROTOCOL — WhatsApp Auth + Invio

### A0 — Prerequisiti (esegui SEMPRE prima)

```bash
# 1. Tailscale + SSH
ssh gianlucadistasi@192.168.1.12 "echo OK && node --version && npm --version"

# 2. Dipendenze iMac
ssh gianlucadistasi@192.168.1.12 "
  cd ~/Documents/app-antigravity-auto/wa-sender 2>/dev/null ||
  (mkdir -p ~/Documents/app-antigravity-auto/wa-sender &&
   cd ~/Documents/app-antigravity-auto/wa-sender &&
   npm init -y && npm install whatsapp-web.js qrcode)
"

# 3. Sessione esistente? (se sì → salta A1, vai ad A2)
# LocalAuth salva in path relativo alla dir progetto, NON in ~/
ssh gianlucadistasi@192.168.1.12 \
  "ls ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/session-argosautomotive/ 2>/dev/null && echo SESSIONE_OK || echo SESSIONE_ASSENTE"
```

### A1 — Prima autenticazione (solo se sessione assente)

**REGOLA CRITICA: Il QR NON va nel terminale SSH. Va servito via HTTP.**

```bash
# Deploy QR server su iMac
bash .claude/skills/argos-outreach-automation/scripts/deploy_qr_server.sh \
  "NUMERO_TARGET_39XXXXXXXXXX" \
  "TESTO_MESSAGGIO"

# Avvia in background su iMac
ssh gianlucadistasi@192.168.1.12 "
  pkill -f 'node.*send_qr' 2>/dev/null || true
  cd ~/Documents/app-antigravity-auto/wa-sender
  nohup node send_qr_server.js > /tmp/wa_log.txt 2>&1 &
  sleep 5 && cat /tmp/wa_log.txt
"

# Apri QR nel browser MacBook
open http://192.168.1.12:8765
```

**→ HUMAN ACTION RICHIESTA (30 secondi):**
Android → WhatsApp → Menu ⋮ → Dispositivi collegati → Collega dispositivo → Scansiona QR dal browser

```bash
# Verifica proof-of-send (esegui dopo scansione)
# LocalAuth path = RELATIVO alla dir progetto, NON ~/
ssh gianlucadistasi@192.168.1.12 "
  ls -la ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/session-argosautomotive/ 2>&1 | head -3
  echo '---LOG---'
  tail -5 /tmp/wa_log.txt
"
# OUTPUT ATTESO: cartella con file + '[ARGOS] INVIATO'
# OUTPUT FALSO: 'No such file or directory' = QR non scansionato
```

### A2 — Invio successivo (sessione già attiva)

```bash
ssh gianlucadistasi@192.168.1.12 "
  cd ~/Documents/app-antigravity-auto/wa-sender
  node send_message.js '39XXXXXXXXXX@c.us' 'TESTO'
"
```

Script: `scripts/send_message.js` — anti-ban sleep 90-720s integrato.

### A3 — Anti-ban rules (IMMUTABILI)

```
DAILY_LIMIT  = 30 msg/giorno (hard limit, non business ceiling)
SLEEP        = random(90, 720) secondi tra invii
SIM          = Very Mobile IT (personale, non bulk)
SESSION      = LocalAuth persistente (argosautomotive)
MAX_NEW/DAY  = 5 nuovi contatti/giorno
```

---

## [B] EMAIL PROTOCOL — Outreach email

### Template Day 7 Mario Orefice (RAGIONIERE)

```python
# Esegui su iMac
ssh gianlucadistasi@192.168.1.12 "
  cd ~/Documents/app-antigravity-auto
  python3 email_agent.py \
    --to 'mario.orefice@mariauto.it' \
    --persona RAGIONIERE \
    --veicolo 'BMW 330i G20' \
    --km 45200 \
    --prezzo_de 27800 \
    --margine 3100 \
    --day 7
"
```

Se email_agent.py non risponde → usa template statico in `references/email_templates.md`.

---

## [C] SEQUENCE PROTOCOL — Gestione sequenza multi-step

### Calendario Mario Orefice (LOCKED)

| Step | Data | Canale | Azione |
|---|---|---|---|
| Day 1 | 2026-03-10 | WhatsApp | ✅ INVIATO |
| Day 7 | 2026-03-17 | Email | Inviare se no risposta |
| Day 12 | 2026-03-22 | WhatsApp | Follow-up finale |

### State machine invio

```bash
# Leggi stato corrente da DuckDB
ssh gianlucadistasi@192.168.1.12 "
  cd ~/Documents/app-antigravity-auto
  python3 -c \"
import duckdb
con = duckdb.connect('dealer_network.duckdb')
r = con.execute(\\\"
  SELECT dealer_name, current_step, last_contact_at, recommendation
  FROM conversations
  WHERE dealer_name = 'Mario Orefice'
  ORDER BY last_contact_at DESC LIMIT 1
\\\").fetchone()
print(r)
\"
"
```

### Trigger matrix risposta Mario

| Risposta ricevuta | Azione |
|---|---|
| "Ok, andiamo avanti" | → Contratto pilot €400, onboarding |
| Silenzio >48h | → Email Day 7 (2026-03-17) |
| OBJ-1..5 nota | → [E] PERSONA PROTOCOL objection handler |
| Obiezione sconosciuta | → Telegram alert + HUMAN_NEEDED + STOP |
| "Non mi interessa" | → Log CLOSED_NO, nessun recontact |

---

## [D] STATE PROTOCOL — DuckDB / stato dealer

### Schema DuckDB (campi LOCKED)

```sql
-- CORRETTO           ← MAI usare nomi errati
recommendation        -- NON verdict
analyzed_at           -- NON created_at

-- Query stato dealer
SELECT dealer_name, current_step, persona_type,
       recommendation, analyzed_at
FROM conversations
WHERE dealer_id = 'MARIO_001'
ORDER BY analyzed_at DESC LIMIT 1;
```

### Update stato dopo invio

```python
# Esegui via SSH dopo ogni invio
ssh gianlucadistasi@192.168.1.12 "python3 -c \"
import duckdb, datetime
con = duckdb.connect('/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.duckdb')
con.execute('''
  UPDATE conversations
  SET current_step = 'WA_DAY1_SENT',
      last_contact_at = CURRENT_TIMESTAMP,
      recommendation = 'IN_PROGRESS',
      analyzed_at = CURRENT_TIMESTAMP
  WHERE dealer_name = 'Mario Orefice'
''')
con.close()
print('✅ Stato aggiornato')
\""
```

---

## [E] PERSONA PROTOCOL — Detector + Objection Handler

### 5 Archetipi dealer (da references/persona_matrix.md)

| Persona | Trigger | Leva | MAI dire |
|---|---|---|---|
| BARONE (55-70) | Tono paternalistico | Margine € netto | "sistema", "AI", "algoritmo" |
| RAGIONIERE (45-60) ← Mario | Chiede documenti | Dati verificabili | "circa", "verifico dopo" |
| PERFORMANTE (35-45) | ROI, velocità | KPI misurabili | "siamo agli inizi" |
| NARCISO (30-40) | Social media attivo | Esclusività | "lavoro con tutti" |
| TECNICO (ex-meccanico) | Dettagli tecnici | Competenza reale | "circa", "più o meno" |

**Fallback:** confidence < 0.50 → RAGIONIERE

### Mario Orefice = RAGIONIERE (confidence 0.85) — regole attive

```
✅ USA: dati precisi, documenti, certificazioni, numeri esatti
✅ USA: "km verificati 45.200", "Vincario report", "ARGOS™ Score 89/100"
❌ MAI: stime vaghe, promesse senza prova, linguaggio entusiasta
❌ MAI: deviare da km=45.200 (LOCKED)
```

### Objection handler

Leggi: `references/objection_library.md`

```
OBJ-1: "Ho già fornitori tedeschi" → RISPOSTA: differenziazione su verifica km + CoVe
OBJ-2: "Il prezzo non mi convince" → RISPOSTA: breakdown margine €3.100 netto
OBJ-3: "Non ho tempo" → RISPOSTA: processo 48h, zero burocrazia sua
OBJ-4: "Come funziona il pagamento?" → RISPOSTA: success-fee €400 pilot, nessun anticipo
OBJ-5: "Devo sentire il titolare" → RISPOSTA: coinvolgimento titolare come opportunità

Obiezione NON in lista → Telegram alert → attendi human override → STOP outreach
```

---

## [F] SETUP PROTOCOL — Prima installazione su iMac

```bash
# Esegui una volta sola dal MacBook
bash .claude/skills/argos-outreach-automation/scripts/setup_imac.sh
```

Script verifica e installa: Node.js, npm deps, DuckDB, struttura directory.

---

## VEICOLO ATTIVO — DATI LOCKED (mai modificare)

```
BMW 330i G20 2020
km verificati:  45.200   ← IMMUTABILE
Prezzo DE:      €27.800 franco
Costo totale:   €29.400 (incluso trasporto)
Prezzo IT:      €33.500+
Margine dealer: €3.100 (dopo fee €800)
ARGOS™ Score:   89/100 CERTIFICATO™
Prima imm.:     15/06/2020
```

---

## PROOF-OF-EXECUTION CHECKLIST

**Prima di dichiarare qualsiasi task completato:**

```bash
# WhatsApp inviato?
# NOTA: LocalAuth salva in path RELATIVO alla dir del progetto, NON in ~/
ssh gianlucadistasi@192.168.1.12 \
  "ls ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/session-argosautomotive/ && tail -3 /tmp/wa_log.txt"

# DB aggiornato?
ssh gianlucadistasi@192.168.1.12 "python3 -c \"
import duckdb
con = duckdb.connect('/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.duckdb')
print(con.execute('SELECT dealer_name,current_step,analyzed_at FROM conversations ORDER BY analyzed_at DESC LIMIT 3').fetchall())
\""

# Log pulito (no errori)?
ssh gianlucadistasi@192.168.1.12 "grep -i 'error\|fail\|exception' /tmp/wa_log.txt || echo 'NO ERRORS'"
```

**Output accettabile = tutti e 3 i check verdi.**
**Output parziale = task NON completato. Ripeti dal punto di fallimento.**

---

## TROUBLESHOOTING RAPIDO

| Sintomo | Fix |
|---|---|
| `Connection refused` porta 3000 | WAHA non serve → usa whatsapp-web.js nativo |
| `command not found: docker` | iMac non ha Docker → architettura corretta è Node.js nativo |
| `~/.wwebjs_auth/` assente | QR non scansionato → ripeti A1 |
| Chromium crash iMac 2012 | Aggiungi `--disable-gpu`, `--disable-dev-shm-usage` |
| Porta 8765 occupata | `ssh imac "lsof -ti:8765 \| xargs kill -9"` |
| Sessione scaduta | `ssh imac "rm -rf ~/.wwebjs_auth/session-argosautomotive/"` poi A1 |
| `npm: command not found` | `ssh imac "brew install node"` |
