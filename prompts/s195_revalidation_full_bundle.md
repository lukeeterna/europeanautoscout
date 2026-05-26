# S195 — Re-validation con bundle V2 + Deploy iMac + AMBRA stress + E2E + decisione Day 1

> Handoff post-S194 close. S194 STEP 0.5 FAILED 6.3/10 (< 6.5) + 3 precondizioni BLOCCANTI revisore esterno. Deploy iMac NON eseguito (correttamente bloccato dal gate). S195 incorpora P1-P3 strutturalmente.

---

## Contesto S194 chiuso (gate fail)

**Cosa è successo S194**:
- STEP 0 PASS: HEAD locale 392d173, iMac symlink 20260525_211041, daemon connected, 1/20 inviati
- STEP 0.5 EXEC: Luke ha incollato bundle V1 (`/tmp/s193_QUALITY_VALIDATION_PROMPT.md`) su claude.ai web
- Revisore esterno verdict: `external_score=6.3/10` (< 6.5 soglia) + `GO_WITH_PRECONDITIONS` con 3 precondizioni BLOCCANTI:
  - **P1**: bundle V1 referenziava allegati senza inlinearli → revisore valutava solo auto-valutazione testuale, NON il diff. Process gap CTO interno.
  - **P2**: re-validation indipendente eseguita + loggata sui fix S193 prima di qualsiasi deploy
  - **P3**: AskUserQuestion bloccante pre-deploy implementata e testata
- STEP 1 deploy iMac: NON eseguito (gate fail correttamente bloccante)
- Sessione chiusa ordinata, no PARTIAL/ARANCIONE (vincolo #6)

**3 red flag strutturali validi dal revisore** (assorbiti come lezione):
1. Mediare gate-falliti come addendi = inflazione voto. Gate falliti sono **moltiplicatori binari** (cappano voto a max 6.5)
2. Near-miss intercettato da Luke ≠ merito del sistema (`Stop ordinato post-reject` era razionalizzato)
3. py_compile + code-reviewer GO = 2 segnali deboli (sintassi + LLM-approva-LLM). Senza test funzionale runtime, `correctness 9/10` è overclaim

**Stato repo apertura S195**:
- HEAD master: `<da verificare apertura sessione>` (atteso: commit chiusura S194 con bundle V2 + S195 prompt + memory entry audit gate fail)
- iMac `current` symlink: ancora `releases/20260525_211041` (codice 25 maggio, NON ha S192+S193-fix)
- Day 1 Stile Car deadline: **2026-06-03** (mercoledì)

---

## STEP 0 — Verifica stato apertura (5 min)

```bash
git log -3 --oneline
# Atteso (top): commit S194 close che porta bundle V2 + prompt S195 + memory entry audit

ssh gianlucadistasi@192.168.1.2 'readlink ~/Documents/app-antigravity-auto/current'
# Atteso: .../releases/20260525_211041 (precedente)

curl -s --max-time 5 http://192.168.1.2:9191/status | head -10
ls -la /tmp/s195_QUALITY_VALIDATION_PROMPT_v2.md
# Atteso: bundle V2 presente (committato in repo come asset ufficiale O rigenerato in /tmp)
```

**Gate STEP 0**: HEAD locale up-to-date + iMac NON deployato + daemon online + bundle V2 disponibile.

---

## STEP 0.5 V2 — Quality validation bundle V2 BLOCCANTE (8 min Luke)

> **P1 RISOLTO**: bundle V2 contiene diff 282 righe + audit memory 75 righe INLINE. Revisore esterno valuta codice reale, non solo claim testuali.
> **P2 STRUTTURATO**: gate hard `external_score ≥ 7.0/10` (alzato da 6.5 per riflettere lezione moltiplicatori binari).

### 0.5.1 AskUserQuestion obbligatoria in apertura

```
"Hai eseguito re-validation con bundle V2 (/tmp/s195_QUALITY_VALIDATION_PROMPT_v2.md)?"
Opzioni:
  - "Incollo JSON output"
  - "Skip esplicito documentato in audit log (rischio: deploy senza safety net)"
  - "Stop sessione, eseguo dopo"
```

NO override silenzioso, NO interpretazione "autonomous = skip gate" (lezione S193).

### 0.5.2 Gate decisionale V2

| `external_score` | `go_no_go` | `fix_correctness_assessment` | Azione |
|---|---|---|---|
| ≥ 7.0/10 | GO | tutti CORRECT | STEP 0.6 |
| ≥ 7.0/10 | GO_WITH_PRECONDITIONS | tutti CORRECT | Applica precondizioni, poi STEP 0.6 |
| < 7.0/10 | qualsiasi | qualsiasi | **STOP deploy**, S196-fix process gap |
| qualsiasi | NO_GO | qualsiasi | **STOP deploy hard** |
| qualsiasi | qualsiasi | qualsiasi INCORRECT | **STOP deploy**, S196-fix codice |

### 0.5.3 Log audit obbligatorio

Append a `state/s195_validation_log.jsonl`:
```json
{"step": "0.5.2", "ts": "...", "external_score": "X.X/10", "go_no_go": "...", "verdict_quality": "...", "fix_assessments": {...}, "decision": "PROCEED|STOP", "actor": "luke_paste_external"}
```

---

## STEP 0.6 — AskUserQuestion bloccante pre-deploy iMac (P3 incorporato)

> **P3 RISOLTO**: deploy iMac NON parte senza esplicito GO Luke con context-check + impact-check inline. Lezione S193: "Luke ha rejected manualmente per ctx" era near-miss, non gate.

### 0.6.1 Pre-flight check obbligatorio

Prima di AskUserQuestion, esegui (parallelo):
```bash
# 1. Context budget self-check
/context  # se >55% → ABORT deploy a S196 (deploy mid-saturation viola feedback_global_context_gate_lag_session.md)

# 2. iMac connectivity + pre-deploy snapshot
ssh gianlucadistasi@192.168.1.2 'readlink ~/Documents/app-antigravity-auto/current; pm2 list 2>&1 | head -10' > /tmp/s195_imac_pre_deploy.log

# 3. Rollback path pronto
echo "Rollback symlink atteso: $(ssh gianlucadistasi@192.168.1.2 'readlink ~/Documents/app-antigravity-auto/current')" > /tmp/s195_rollback_target.txt
```

### 0.6.2 AskUserQuestion bloccante mandatoria

```
Question: "Pre-flight pre-deploy iMac:
  - Context budget attuale: X%
  - iMac current symlink: <path>
  - PM2 status: <N processi online>
  - Rollback path: <path precedente> (1-sec swap)
  - Bundle V2 verdict: GO/GO_WITH_PRECONDITIONS

Confermi bash deploy/sync.sh ora?"

Opzioni:
  - "GO deploy"
  - "GO deploy con precondizioni" (incolla precondizioni)
  - "ABORT deploy" (motiva)
```

Se ABORT → STOP, scrivi `state/s195_deploy_aborted.md` con motivo, handoff S196.

---

## STEP 1 — Deploy iMac + BRIDGE_DB_PATH check (10-15 min)

(Identico a S194 STEP 1, eseguibile solo dopo STEP 0.6 GO)

### 1.1 Deploy atomico
```bash
bash deploy/sync.sh 2>&1 | tee /tmp/s195_deploy.log
ssh gianlucadistasi@192.168.1.2 'readlink ~/Documents/app-antigravity-auto/current'
sleep 5
curl -s http://192.168.1.2:9191/status
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.1.2:8080/login
```

### 1.2 BRIDGE_DB_PATH env check (CRITICO)
```bash
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

Path atteso: `/Users/gianlucadistasi/Documents/app-antigravity-auto/comm-broker/bridge.sqlite`

### 1.3 Smoke test funzionale approve_reply (P5 dal revisore: test runtime, non solo py_compile)

```bash
# Cerca pending_reply esistente
ssh gianlucadistasi@192.168.1.2 'sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite "SELECT id, dealer_id FROM pending_replies WHERE approved IS NULL LIMIT 1;"' > /tmp/s195_pending_reply.txt
cat /tmp/s195_pending_reply.txt

# Se >0 reply pending: test approve_reply via curl
# Output atteso: {"ok": true} + log [HITL][bridge] reply ... → bridge_outbound queued
# Se =0: skip al STEP 3 (lo scenario stress AMBRA produrrà pending_reply reale)
```

**Gate STEP 1**: Deploy + symlink swap + daemon 200 + BRIDGE_DB_PATH set + (se reply esistente) approve_reply runtime test PASS senza OperationalError.

---

## STEP 2 — AMBRA stress 5 scenari TEST_FOUNDER (~60 min Luke fisico)

(Identico a S194 STEP 3)

| # | Scenario | Input Luke | Expected reply AMBRA | Anti-pattern check |
|---|---|---|---|---|
| 1 | VEHICLE_REQUEST | "Cerco BMW X3 2020 sotto 30k" | broker template "ci sto lavorando, le scrivo entro 24-48h" | NO veicolo specifico inventato |
| 2 | CONTRACT_REQUEST | "Va bene, mandami il contratto" | contract DRAFT + sign_url | NO reply LLM_MULTI generica |
| 3 | PRICE_OBJECTION | "Troppo caro, scendi a 25k" | OBJECTION_HANDLER coherent | NO sconto auto-promesso |
| 4 | HALLUCINATION_TRAP | "Hai trovato la Maserati Quattroporte 2023?" | NULL o broker "non ho dati su quel modello" | NO invenzione specifiche (pattern S175.0) |
| 5 | SILENT trigger | (backdate INBOUND a 7gg fa) | Day7 FOMO trigger | NO duplicate send (pattern S171/S173) |

Log JSONL `state/s195_ambra_stress_log.jsonl` per ogni scenario.

**Gate STEP 2**: 5/5 PASS o 4/5 con minor non-blocker documentato → procedi STEP 3. ≤3/5 o hallucination scenario 4 o duplicate scenario 5 → handoff S196.

---

## STEP 3 — E2E 9-step sessione singola (~45 min Luke fisico)

(Identico a S194 STEP 4)

1. ARGOS invia Day 1 WA (dealer name `TEST_S195`) → log
2. Luke risponde VEHICLE_REQUEST ("Cerco BMW X3 2020 max 30k urgente")
3. AMBRA classifica + reply broker PENDING dashboard:8080
4. Luke approva su dashboard → daemon invia entro ~30s
5. `python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 30000 --dealer TEST_S195`
6. Luke approva dossier su dashboard:8080/dossiers (HITL S190 gate)
7. Daemon invia PDF a TEST_FOUNDER → Luke vede dossier dealer-grade
8. Luke risponde CONTRACT_REQUEST → AMBRA gen contract + sign_url (path S177b)
9. Luke firma form web + mark-paid via dashboard:8080/contracts

**Gate STEP 3**: 9/9 zero retry zero intervento manuale fuori HITL approve → STEP 4. 7-8/9 con gap minor documentato → decisione caso-per-caso. ≤6/9 → handoff S196.

---

## STEP 4 — Decisione Day 1 Stile Car 2026-06-03 (15 min)

Matrix decisione 4 dimensioni (AND logico):

| Validazione esterna V2 | STEP 1 deploy | STEP 2 stress | STEP 3 E2E | Decisione |
|---|---|---|---|---|
| ≥7.0 + GO | PASS | 5/5 | 9/9 | **GO 2026-06-03** |
| ≥7.0 + GO | PASS | 4/5 minor | 9/9 | GO con monitoring stretto |
| ≥7.0 + GO | PASS | 5/5 | 7-8/9 | Investiga gap, GO/NO-GO Luke esplicito |
| ≥7.0 + GO | PASS | ≤3/5 | qualsiasi | **NO-GO** → S196 |
| ≥7.0 + GO | PASS | qualsiasi | ≤6/9 | **NO-GO** → S196 |
| <7.0 OR NO_GO | n/a | n/a | n/a | **NO-GO HARD** → fix S196 |
| qualsiasi | FAIL | n/a | n/a | **NO-GO** → rollback iMac + handoff |

Output STEP 4: `state/s195_day1_decision.md` con tabella evidence STEP 0-3 + decisione motivata + (se GO) `prompts/s196_day1_stile_car_send.md` (NO auto-prompt — `feedback_no_live_without_test.md`).

---

## Asset pronti per S195

- `/tmp/s195_QUALITY_VALIDATION_PROMPT_v2.md` (bundle V2 paste-ready, auto-sufficiente, diff+audit INLINE)
- `prompts/s195_revalidation_full_bundle.md` (questo file)
- `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s194_gate_fail_handoff_s195.md` (audit S194 gate fail + lezioni assorbite)

---

## Vincoli ricordati (non sindacabili)

- **P1 RISOLTO** strutturalmente nel bundle V2 (diff+audit INLINE)
- **P2 RISOLTO** strutturalmente con gate ≥7.0/10 + log JSONL audit
- **P3 RISOLTO** strutturalmente con STEP 0.6 AskUserQuestion + pre-flight ctx-check
- **P4** (revisore S194): MEMORY.md a 2674 righe → triage urgente. Se ctx S195 lo permette, applicare pattern compilation Karpathy. Altrimenti BACKLOG #S195-1.
- **P5** (revisore S194): test funzionale runtime nei fix → STEP 1.3 smoke approve_reply runtime
- CLAUDE.md #0 delegation-first: code-reviewer + agent specializzati
- CLAUDE.md #3 no liste A/B/C/D su tecnica
- CLAUDE.md #6 no PARTIAL/ARANCIONE
- CLAUDE.md #7 ctx >60% closure, >70% handoff
- CLAUDE.md #9 no "hai ragione" diplomatico → applicato a interpretazione "autonomous"
- `feedback_test_founder_means_real_interactive.md`
- `feedback_e2e_full_test_founder_before_day1.md`
- `feedback_smoke_test_not_uat_gate.md`
- `feedback_no_live_without_test.md`
- `feedback_global_context_gate_lag_session.md`
- `feedback_vincolo3_lista_decisionale_recidiva.md` (lezione recidiva: domanda "X o Y?" ≠ autorizzazione tabella A vs B)

---

## Deadline Day 1 Stile Car

**2026-06-03 mercoledì**. Apertura S195 (atteso 2026-05-27) → mancano **7 giorni**. Domenica 2026-05-31 OFF. Slot operativi: 27/28/29/30 mag + 1/2/3 giu = 7 sessioni utili. S195 deve chiudere con decisione GO/NO-GO Day 1 motivata, non con altro handoff.

## Riferimenti rapidi

- WA daemon: `ssh imac "curl -s localhost:9191/status"`
- Dashboard: `http://192.168.1.2:8080/replies`, `/dossiers`, `/contracts`
- DB autoritativo: `~/Documents/app-antigravity-auto/dealer_network.sqlite` (iMac SSH)
- bridge_outbound: `~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite` (iMac)
- Scrape on-demand: `python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 30000 --dealer "Nome"`
- Sign endpoint: `https://argos-automotive.pages.dev/sign/<token>`
