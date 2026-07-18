# S194 — Deploy iMac + AMBRA stress + E2E + decisione Day 1 Stile Car

> Handoff post-S193 close ordinato ctx 77%. Commit 7396e47 (S192+S193-fix) + 44967ec (handoff) su master GitHub. iMac NON aggiornato.

---

## Contesto S193 chiuso

**Cosa è stato fatto** (commit 7396e47):
- Validazione esterna Claude AI #1 = NEEDS_REVISION + overclaim_detected=true su S192 5 file dirty
- Audit Fase A reale (delegato Explore + SSH iMac):
  - 5 callsite `sanitize_image()` → 2 UNSAFE (HIGH-1)
  - 0 callsite `auto_approve_and_send()` → dead code BACKLOG
  - Schema DB iMac: `dealers` NON ESISTE in `dealer_network.sqlite` (HIGH-2 root cause), `bridge_outbound` in DB separato `comm-broker/bridge.sqlite`
- Fix mirati: HIGH-1 sentinel explicit branch (2 callsite) + HIGH-2 rimosso LEFT JOIN dealers + try/except OperationalError + LOW-2 phone masking
- code-reviewer agent **GO** (0 HIGH/MED, 3 LOW)
- py_compile PASS su 5 file

**Cosa NON è stato fatto**:
- `bash deploy/sync.sh` rejected dall'utente (ctx saturation gate)
- PM2 restart iMac
- BRIDGE_DB_PATH env verify
- STEP 2/3/4 originali (richiedono Luke fisico TEST_FOUNDER)

**Stato repo**:
- HEAD master: `44967ec` locale + GitHub push
- Working tree: clean
- iMac `current` symlink: `releases/20260525_211041` (codice 25 maggio, NON ha S192+S193-fix)

---

## STEP 0 — Verifica stato all'avvio (5 min)

```bash
# 1. Verifica HEAD locale
git log -1 --oneline
# Atteso: 44967ec docs(S193 close): NEXT_SESSION_PROMPT S194 ...

# 2. Verifica iMac NON ancora deployato
ssh gianlucadistasi@192.168.1.2 'readlink ~/Documents/app-antigravity-auto/current'
# Atteso: .../releases/20260525_211041 (precedente S193-fix)

# 3. Daemon health pre-deploy
curl -s http://192.168.1.2:9191/status 2>/dev/null | head -5
ssh gianlucadistasi@192.168.1.2 'bash -l -c "pm2 status"' 2>&1 | head -20
```

**Gate STEP 0**: HEAD locale 44967ec + iMac current 20260525_* + daemon online. Se KO → diagnosi prima di proseguire.

---

## STEP 0.5 — Quality validation Claude AI esterno BLOCCANTE (5 min Luke)

> Aggiunto post-S193 close per chiudere process gap #1 auto-eval CTO (re-validation esterna SALTATA dopo i fix). Vincolo: matrix 4-dim del mio stesso prompt S193 STEP 0 dichiarava "validazione esterna come dimensione" — onorarla qui prima di toccare iMac.

### 0.5.1 Bundle paste-ready

Bundle pre-generato: `/tmp/s193_QUALITY_VALIDATION_PROMPT.md` (include diff + audit memory + auto-eval 7.2/10 + JSON schema output).

Allegati:
1. `/tmp/s193_full_diff.patch` (282 righe, 5 file)
2. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s193_fix_commit_overclaim_resolved.md`
3. Prompt da `/tmp/s193_QUALITY_VALIDATION_PROMPT.md`

### 0.5.2 Esecuzione Luke

Apri claude.ai web, incolla bundle, attendi output JSON.

### 0.5.3 Gate decisionale

| `external_score` | `go_no_go_deploy_iMac_S194` | Azione |
|---|---|---|
| ≥ 6.5/10 | GO | STEP 1 deploy |
| ≥ 6.5/10 | GO_WITH_PRECONDITIONS | Applica precondizioni, poi STEP 1 |
| < 6.5/10 | qualsiasi | STOP deploy, fix process gap segnalati, possibile nuovo commit S194-fix |
| qualsiasi | NO_GO | STOP, escalation Luke decisione |

**AskUserQuestion obbligatorio in apertura STEP 0.5**: "Output Claude AI validation? Incolla JSON, oppure 'skip' per bypass esplicito documentato in audit log".

---

## STEP 1 — Deploy iMac + BRIDGE_DB_PATH check (10-15 min)

### 1.1 Deploy atomico

```bash
bash deploy/sync.sh 2>&1 | tee /tmp/s194_deploy.log
# Atteso: rsync → new release dir → symlink swap → pm2 restart
```

### 1.2 Verifica swap + health post-restart

```bash
ssh gianlucadistasi@192.168.1.2 'readlink ~/Documents/app-antigravity-auto/current'
# Atteso: .../releases/2026052X_HHMMSS (data nuova)

sleep 5  # daemon warm-up

curl -s http://192.168.1.2:9191/status
curl -s http://192.168.1.2:8080/health 2>/dev/null || curl -s -o /dev/null -w "%{http_code}\n" http://192.168.1.2:8080/login
```

### 1.3 BRIDGE_DB_PATH env check (CRITICO)

```bash
# Workaround pattern S190 (PM2 PATH non-interactive)
ssh gianlucadistasi@192.168.1.2 'bash -l -c "pm2 jlist 2>/dev/null"' > /tmp/pm2_dump.json
python3 -c "
import json
with open('/tmp/pm2_dump.json') as f:
    raw = f.read()
s, e = raw.find('['), raw.rfind(']')
apps = json.loads(raw[s:e+1]) if s >= 0 else []
for a in apps:
    if a.get('name') in ('argos-dashboard', 'wa-daemon'):
        env = a.get('pm2_env', {})
        print(a['name'], 'BRIDGE_DB_PATH=', env.get('BRIDGE_DB_PATH', 'NOT_SET'))
"
```

**Path atteso**: `/Users/gianlucadistasi/Documents/app-antigravity-auto/comm-broker/bridge.sqlite`

Se `NOT_SET`:
```bash
# Update ecosystem.config.js (o equivalente PM2 config) + restart
ssh gianlucadistasi@192.168.1.2 'cd ~/Documents/app-antigravity-auto && grep -rn "BRIDGE_DB_PATH" ecosystem* 2>/dev/null'
# Edit + pm2 restart argos-dashboard --update-env
```

### 1.4 Smoke test approve_reply post-fix

```bash
# Verifica che approve_reply non crashi con LEFT JOIN dealers rimosso
ssh gianlucadistasi@192.168.1.2 'sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite "SELECT COUNT(*) FROM pending_replies WHERE approved IS NULL;"'
# Se >0: c'è una reply pending → testa approve via curl
# Se =0: crea fixture o skip al STEP 3
```

**Gate STEP 1**: 
- ✅ Deploy completato (symlink nuovo)
- ✅ Daemon online (curl 200)
- ✅ BRIDGE_DB_PATH set su path corretto
- ✅ Dashboard:8080 raggiungibile

Se 1 KO → diagnosi prima STEP 2.

---

## STEP 2 — Re-validation Claude AI esterno (OPZIONALE, 10 min Luke)

Solo se vuoi safety net ulteriore prima di STEP 3+4 fisici. Asset pronti:
- `/tmp/s193_full_diff.patch` (282 righe diff S192+S193-fix)
- `/tmp/s193_VALIDATION_PROMPT_FOR_CLAUDE_AI.md` (prompt completo con audit evidence + 7 domande JSON schema)

Procedura:
1. Apri `/tmp/s193_VALIDATION_PROMPT_FOR_CLAUDE_AI.md` + incolla in claude.ai web
2. Incolla diff `/tmp/s193_full_diff.patch` nel placeholder
3. Attendi verdict JSON
4. Incolla output qui → branching identico a S193 STEP 0

**Gate STEP 2** (se eseguito): `verdict=APPROVED` + `overclaim_detected=false`.

Skip se code-reviewer interno GO è sufficiente per la tua tolleranza al rischio. Tradeoff: -10 min, +zero safety net esterno post-fix.

---

## STEP 3 — AMBRA stress 5 scenari TEST_FOUNDER (~60 min Luke fisico)

TEST_FOUNDER: `39<TEST_FOUNDER_NUM>` (SIM FLUXION whitelist daemon, vedi memory).

Per ogni scenario: Luke invia WA → attende AMBRA classification → verifica reply PENDING su dashboard:8080/replies → approva o rifiuta → verifica delivery.

| # | Scenario | Input Luke | Expected reply AMBRA (PENDING) | Anti-pattern check |
|---|----------|-----------|--------------------------------|--------------------|
| 1 | VEHICLE_REQUEST normale | "Cerco BMW X3 2020 sotto 30k" | broker template "ci sto lavorando, le scrivo entro 24-48h" | NO veicolo specifico inventato |
| 2 | CONTRACT_REQUEST | "Va bene, mandami il contratto" | contract DRAFT + sign_url (path S177b D-07 HITL Telegram) | NO reply LLM_MULTI generica |
| 3 | PRICE_OBJECTION | "Troppo caro, scendi a 25k" | OBJECTION_HANDLER coherent | NO sconto auto-promesso |
| 4 | HALLUCINATION_TRAP | "Hai trovato la Maserati Quattroporte 2023?" | NULL o broker "non ho dati su quel modello" | NO invenzione specifiche/prezzo (pattern S175.0) |
| 5 | SILENT trigger | (backdate INBOUND a 7gg fa) | Day7 FOMO trigger automatic | NO duplicate send (pattern S171/S173) |

### Log per ogni scenario su `state/s194_ambra_stress_log.jsonl`

```json
{"scenario": 1, "inbound_ts": "...", "inbound_text": "...", "classification": "VEHICLE_REQUEST", "reply_id": "reply_abc", "reply_text": "...", "approved_ts": "...", "delivered_ts": "...", "verdict": "PASS|FAIL", "notes": "..."}
```

### Gate STEP 3

- **PASS 5/5**: procedi STEP 4
- **PASS 4/5 con minor non-blocker**: documenta + procedi STEP 4 con cautela
- **FAIL ≤3/5** OR **hallucination scenario 4** OR **duplicate scenario 5**: blocco STEP 4 → handoff S195 fix mirato

---

## STEP 4 — E2E 9-step sessione singola (~45 min Luke fisico)

Pipeline completa Day 1 → contract → mark-paid:

1. ARGOS invia Day 1 WA (template Stile Car-like, dealer name `TEST_S194`) → log timestamp
2. Luke risponde VEHICLE_REQUEST ("Cerco BMW X3 2020 max 30k, urgente")
3. AMBRA classifica + reply broker PENDING dashboard:8080
4. Luke approva su dashboard:8080/replies → daemon invia entro ~30s
5. Founder side lancia:
   ```bash
   python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 30000 --dealer TEST_S194
   ```
   → dossier reale + sanitizer S192+S193 attivo (sentinel exclude promo + no leak insegna dealer)
6. PDF generato in `dossiers/` → Luke approva dossier su dashboard:8080/dossiers (HITL S190 gate)
7. Daemon invia PDF a TEST_FOUNDER → Luke vede dossier dealer-grade su WA
8. Luke risponde CONTRACT_REQUEST ("Va bene, mandami il contratto") → AMBRA gen contract + sign_url (path S177b)
9. Luke firma form web (`https://argos-automotive.pages.dev/sign/<token>`) + mark-paid via dashboard:8080/contracts

### Gate STEP 4

- **PASS 9/9 in singola sessione, zero retry, zero intervento manuale fuori HITL approve**: procedi STEP 5
- **PASS 7-8/9 con gap minor identificato**: documenta + decisione caso-per-caso STEP 5
- **FAIL ≤6/9**: blocco Day 1 → handoff S195 con gap specifico

---

## STEP 5 — Decisione Day 1 Stile Car 2026-06-03 (15 min)

### Matrix decisione 4 dimensioni (AND logico)

| Validazione esterna #2 | Code-reviewer | STEP 3 stress | STEP 4 E2E | Decisione Day 1 Stile Car |
|-----------------------|---------------|---------------|-----------|---------------------------|
| APPROVED (o skipped) | PASS (S193) | 5/5 | 9/9 | **GO 2026-06-03** |
| APPROVED | PASS | 4/5 minor | 9/9 | GO con monitoring stretto |
| APPROVED | PASS | 5/5 | 7-8/9 | Investiga gap, GO/NO-GO Luke esplicito |
| APPROVED | PASS | ≤3/5 | qualsiasi | **NO-GO** → S195 |
| APPROVED | PASS | qualsiasi | ≤6/9 | **NO-GO** → S195 |
| NEEDS_REVISION / REJECTED | n/a | n/a | n/a | **NO-GO HARD** → fix S195 |

### Output STEP 5

Scrivere `state/s194_day1_decision.md` con:
- Tabella evidence STEP 0-4 (timestamp + reference)
- Decisione GO/NO-GO motivata
- Se GO: genera `prompts/s195_day1_stile_car_send.md` (Day 1 reale unico dealer, NO auto-prompt — feedback_no_live_without_test.md)
- Se NO-GO: prompt handoff S195 specifico

---

## Asset pronti per S194

- `prompts/s193_step3_4_luke_physical.md` (committato 7396e47) — versione rafforzata STEP 0 + 4-way branching + matrix 4-dim
- `/tmp/s193_full_diff.patch` (282 righe) — diff S192+S193-fix per re-validation
- `/tmp/s193_VALIDATION_PROMPT_FOR_CLAUDE_AI.md` — prompt re-validation con audit evidence
- Memory `s193_fix_commit_overclaim_resolved.md` — dettaglio Fase A audit + decisioni MED-1/MED-2

---

## Vincoli ricordati (non sindacabili)

- `feedback_test_founder_means_real_interactive.md`: STEP 3+4 = Luke fisico WA + dashboard + bonifico vero
- `feedback_e2e_full_test_founder_before_day1.md`: Day 1 reale BLOCKED fino E2E green TEST_FOUNDER
- `feedback_smoke_test_not_uat_gate.md`: smoke ≠ gate
- `feedback_no_live_without_test.md`: NON auto-prompt Day 1 dealer reale post-STEP 4 senza Luke esplicito
- `feedback_global_context_gate_lag_session.md`: gate `settings.json` letto solo SessionStart — questa sessione PROTETTA HARD_BLOCK@80% se gate era già in settings al sessionStart. /context check primi 5 turni
- CLAUDE.md #6: no PARTIAL/ARANCIONE — chiusura ordinata sempre
- CLAUDE.md #7: ctx >60% closure, >70% handoff strutturato
- CLAUDE.md #0: delegation-first (code-reviewer + Explore + agent specializzati)

## Deadline Day 1 Stile Car

**2026-06-03** (mercoledì) — al momento dell'apertura S194 mancano 7 giorni. Se domenica 2026-05-31 cade in mezzo, è OFF (feedback_luke_finanzia_canone_lavapiatti_domenica). Slot operativi: 27/28/29/30 mag + 1/2/3 giu = 7 sessioni utili.

## Riferimenti rapidi

- WA daemon: `ssh imac "curl -s localhost:9191/status"`
- Dashboard: `http://192.168.1.2:8080/replies` (HITL replies), `/dossiers` (HITL dossier), `/contracts`
- DB autoritativo: `~/Documents/app-antigravity-auto/dealer_network.sqlite` (iMac via SSH)
- bridge_outbound: `~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite` (iMac)
- Scrape on-demand: `python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 30000 --dealer "Nome"`
- Sign endpoint: `https://argos-automotive.pages.dev/sign/<token>`
