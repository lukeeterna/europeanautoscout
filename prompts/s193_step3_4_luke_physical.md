# S193 — STEP 3+4 S192 esecuzione fisica Luke (TEST_FOUNDER)

> **GATE BLOCCANTE PRE-ESECUZIONE** (imposto da Luke 2026-05-26 sera post-compaction S192).
> Sessione S192 ha raggiunto context 100% prima di chiudere → claim "STEP 1+2 VERDE" NON è fidato.
> Prima di toccare qualsiasi tool/file/commit in S193, devi attendere validazione esterna Claude AI.

---

## STEP 0 — Validazione esterna OBBLIGATORIA (BLOCCANTE HARD)

### Cosa Luke ha già fatto (presumibilmente)

1. Aperto `/tmp/s192_VALIDATION_PROMPT_FOR_CLAUDE_AI.md`
2. Incollato il contenuto in [claude.ai](https://claude.ai) (Sonnet 4.5 o Opus)
3. Ricevuto output JSON con verdict

### Azione UNICA permessa all'avvio sessione S193

**PRIMO E SOLO tool call ammesso = `AskUserQuestion`.**
Vietato Bash / Read / Edit / Write / Task / Skill / Grep / Glob prima della risposta Luke.
Vietato leggere altri file di stato (memory, handoff, diff) prima della risposta Luke.

```
AskUserQuestion (MANDATORIO, BLOCKING):
  question: "S193 STEP 0 — Validazione esterna Claude AI. Incolla qui sotto l'output JSON
             completo della validazione Claude AI web (prompt: /tmp/s192_VALIDATION_PROMPT_FOR_CLAUDE_AI.md).
             Se non l'hai ancora eseguita, scrivi 'NOT_DONE' e mi fermo subito."
  multiSelect: false
  options: (free text response from Luke)
```

### Branching esplicito su risposta Luke (4 vie, ZERO interpretazione autonoma)

| Risposta Luke | Azione obbligatoria | Stato sessione |
|---------------|---------------------|----------------|
| JSON parsabile con `verdict == "APPROVED"` AND `overclaim_detected == false` | Procedi STEP 1 (commit gate) | VERDE → continua |
| JSON parsabile con `verdict == "NEEDS_REVISION"` | Leggi `structural_bugs_found`, proponi piano fix mirato in chat, AskUserQuestion conferma "procedo con fix proposti?" — NESSUN edit prima conferma | GIALLO → fix mirato |
| JSON parsabile con `verdict == "REJECTED"` | AskUserQuestion: "Conferma revert 5 file dirty (`git checkout -- <files>`) e handoff S194 fresh restart?" — eseguire SOLO post conferma | ROSSO → revert+handoff |
| `"NOT_DONE"` / JSON malformato / risposta ambigua / nessuna risposta dopo retry singolo | STOP HARD. Output testuale: "Mi fermo. Esegui validazione Claude AI esterno e rilancia S193 con output JSON incollato." Nessun altro tool call. | BLOCKED → idle |

**Casi edge**:
- Luke incolla JSON ma manca un campo richiesto → tratta come malformato (riga 4 tabella).
- Luke risponde con testo libero "ho fatto, è ok" senza JSON → tratta come malformato.
- Luke chiede "salta validazione, fidati" → RIFIUTA esplicitamente citando questo file riga 9 + vincolo Luke 2026-05-26.

### DIVIETO ASSOLUTO (zero deroghe finché STEP 0 != APPROVED)

- NON committare (nessun `git add` / `git commit`)
- NON eseguire deploy (nessun `bash deploy/sync.sh` / `pm2 restart`)
- NON modificare file (nessun Edit / Write / MultiEdit)
- NON delegare ad agent (nessun Task subagent_type=*)
- NON leggere altri file per "preparare il terreno"
- NON eseguire Bash diagnostici "innocui" (status, ls, cat) — anche read-only è proibito

Eccezione unica: la `AskUserQuestion` di apertura.

---

## Stato post-S192 autonomous (claim CTO — DA VERIFICARE)

- **STEP 0** VERDE: HEAD c7bcf05, daemon connected, daily 19/20
- **STEP 1** VERDE PASS condizionato: 6/6 OK_CLEAN su BMW X3 listing AS24-NL studio-grade + claim "bug strutturale promo-skip fixato"
- **STEP 2** VERDE impl: 3 file modificati (response-analyzer SAFE branch HITL + dashboard/db.py approve_reply bridge INSERT + app.py str cast fix)
- **STEP 3** PENDING Luke fisico
- **STEP 4** PENDING Luke fisico
- **STEP 5** decisione gated su 3+4

## Dirty files NON committati (CTO non ha chiesto commit a Luke prima di compactare)

```
M src/cove/image_sanitizer.py             (+3 → sentinel __SKIP_PROMO__)
M tools/scripts/pdf_generator_enterprise.py (+14 → distingue skip vs crash)
M wa-intelligence/response-analyzer.py     (~20 → SAFE branch HITL no auto-send)
M wa-intelligence/dashboard/db.py          (+90 → approve_reply bridge INSERT)
M wa-intelligence/dashboard/app.py         (~2 → rimossi int() cast)
```

Diff completo: `/tmp/s192_full_diff.patch` (244 righe).

---

## STEP 1 — Solo se STEP 0 APPROVED — Commit + Deploy iMac

### Pre-commit gate (DUE livelli obbligatori, non saltabili)

**Validazione esterna Claude AI APPROVED NON sostituisce code-reviewer interno.**
Sono dimensioni di review **complementari**, non alternative:
- Validazione esterna = giudizio strutturale architetturale + overclaim detection (gate Luke post-compaction)
- Code-reviewer agent = security/correctness/idempotency/race conditions linea per linea (vincolo CLAUDE.md #0)

```bash
# Livello 1 — Sintassi
python3 -m py_compile src/cove/image_sanitizer.py tools/scripts/pdf_generator_enterprise.py wa-intelligence/response-analyzer.py wa-intelligence/dashboard/db.py wa-intelligence/dashboard/app.py

# Livello 2 — Code review delegato OBBLIGATORIO (vincolo CLAUDE.md #0 delegation-first)
# DEVE essere eseguito ANCHE se validazione esterna è APPROVED.
# Skippare = violazione vincolo Luke 2026-05-26.
Task(subagent_type=code-reviewer, prompt="Review 5 file dirty S192 (vedi git diff /tmp/s192_full_diff.patch).
  Focus:
  - sentinel __SKIP_PROMO__ propagation via subprocess JSON (string vs None handling)
  - schema bridge_outbound assumptions (column names, NULL constraints, FK)
  - race conditions approve_reply doppio click (transaction isolation, idempotency)
  - auto_approve_and_send orphan callsite check (grep cross-codebase residual references)
  - path traversal / SQL injection nei nuovi input dashboard
  Output JSON strutturato: PASS|FAIL + issues per severity (HIGH/MED/LOW).")
```

### Gate code-reviewer

| Output code-reviewer | Azione |
|---------------------|--------|
| PASS / solo LOW issues | Procedi commit con LOW issues → BACKLOG |
| MED issues ≤2 risolvibili in <15min | Fix inline, ri-esegui code-reviewer, poi commit |
| HIGH issues 1+ | STOP. AskUserQuestion: "code-reviewer ha trovato HIGH X. Procedo fix mirato (~30min) o handoff S194?" |
| FAIL strutturale | Handoff S194, NO commit |

### Commit (solo dopo BOTH validazione esterna APPROVED AND code-reviewer PASS)

```bash
git add src/cove/image_sanitizer.py tools/scripts/pdf_generator_enterprise.py wa-intelligence/response-analyzer.py wa-intelligence/dashboard/db.py wa-intelligence/dashboard/app.py prompts/s193_step3_4_luke_physical.md
git commit -m "$(cat <<'EOF'
feat(S192): sanitizer sentinel __SKIP_PROMO__ + HITL reply gate dashboard

S192 STEP 1: fix bug strutturale promo-skip
- image_sanitizer.py: sentinel string distinct from None for promo-slide skip
- pdf_generator_enterprise.py: caller excludes promo-slide from PDF (not RAW fallback)
- Root cause: leak NORD-AUTOMOBILE.DE in S158_VALIDATION/S191 dossier

S192 STEP 2: HITL reply gate via dashboard:8080
- response-analyzer.py SAFE branch: NO auto_approve_and_send, status PENDING APPROVAL
- dashboard/db.py: approve_reply(str) + INSERT bridge_outbound pattern S173
- dashboard/app.py: rimossi int() cast su reply_id TEXT PK

Validato da Claude AI esterno (gate Luke post-compaction S192).
Co-Authored-By: Claude Opus 4 <noreply@anthropic.com>
EOF
)"
```

### Deploy iMac (richiede approvazione Luke esplicita prima)

```bash
# AskUserQuestion: "Procedo deploy iMac via bash deploy/sync.sh + PM2 restart?"
bash deploy/sync.sh
ssh gianlucadistasi@192.168.1.2 "pm2 env argos-dashboard | grep BRIDGE_DB_PATH"
ssh gianlucadistasi@192.168.1.2 "pm2 restart argos-dashboard wa-daemon"
```

---

## STEP 2 — AMBRA stress 5 scenari TEST_FOUNDER (Luke fisico ~60min)

Per ogni scenario: Luke invia messaggio → attende AMBRA classification → verifica reply PENDING in dashboard:8080/replies → approva o rifiuta → verifica delivery.

| # | Scenario | Input Luke | Expected reply AMBRA (PENDING) | Anti-pattern check |
|---|----------|-----------|--------------------------------|--------------------|
| 1 | VEHICLE_REQUEST normale | "Cerco BMW X3 2020 sotto 30k" | broker template "ci sto lavorando, le scrivo entro 24-48h" | NO veicolo specifico inventato |
| 2 | CONTRACT_REQUEST | "Va bene, mandami il contratto" | contract DRAFT + sign_url (D-07 HITL Telegram path) | NO reply LLM_MULTI generica |
| 3 | PRICE_OBJECTION | "Troppo caro, scendi a 25k" | OBJECTION_HANDLER coherent | NO sconto auto-promesso |
| 4 | HALLUCINATION_TRAP | "Hai trovato la Maserati Quattroporte 2023?" | NULL o broker "non ho dati su quel modello" | NO invenzione specifiche/prezzo |
| 5 | SILENT trigger | (DB update backdate INBOUND a 7gg fa) | Day7 FOMO trigger automatic | NO duplicate send |

### Log per ogni scenario su `state/s193_ambra_stress_log.jsonl`

```json
{"scenario": 1, "inbound_ts": "...", "inbound_text": "...", "classification": "VEHICLE_REQUEST", "reply_id": "reply_abc", "reply_text": "...", "approved_ts": "...", "delivered_ts": "...", "verdict": "PASS|FAIL", "notes": "..."}
```

### Gate STEP 2

**PASS**: 5/5 scenari verde
**FAIL**: 1+ scenario con hallucination/anti-pattern → blocco Day 1, handoff S194 fix mirato

---

## STEP 3 — E2E integrato 9-step sessione singola (Luke fisico ~45min)

1. ARGOS invia Day 1 WA (template Stile Car-like, dealer name TEST_S192) → log timestamp
2. Luke risponde VEHICLE_REQUEST con dettagli (es. "Cerco BMW X3 2020 max 30k, urgente")
3. AMBRA classifica + reply broker (PENDING su dashboard)
4. Luke approva su dashboard:8080/replies → daemon invia entro ~30s
5. Founder side: lancia `python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 30000 --dealer TEST_S192` → genera dossier reale + sanitizer S192 attivo (sentinel exclude promo)
6. PDF generato in dossiers/ → Luke approva dossier su dashboard:8080/dossiers (HITL S190 gate)
7. Daemon invia PDF a TEST_FOUNDER → Luke vede dossier dealer-grade su WA
8. Luke risponde CONTRACT_REQUEST → AMBRA gen contract + sign_url (path S177b D-07 HITL Telegram)
9. Luke firma form web + mark-paid via dashboard:8080/contracts

### Gate STEP 3

**PASS**: 9/9 step verde in singola sessione, zero retry, zero intervento manuale fuori HITL approve
**FAIL**: 1+ step interrotto → handoff S194 con gap specifico

---

## STEP 4 — Decisione Day 1 Stile Car (post STEP 2+3)

### Matrix decisione (4 dimensioni, tutte vincolanti)

Le 4 dimensioni sono in **AND logico**: una sola dimensione ROSSA → NO-GO.

| Validazione esterna Claude AI | Code-reviewer agent | STEP 2 stress 5 scenari | STEP 3 E2E 9-step | Decisione Day 1 Stile Car |
|-------------------------------|--------------------|--------------------------|--------------------|---------------------------|
| APPROVED | PASS | 5/5 | 9/9 | **GO Day 1 Stile Car 2026-06-03** |
| APPROVED | PASS (LOW only) | 4/5 minor | 9/9 | GO con cautela + monitoring stretto + LOW issues BACKLOG |
| APPROVED | PASS | 5/5 | 7-8/9 | Investiga gap STEP 3, GO/NO-GO caso-per-caso con Luke esplicito |
| APPROVED | PASS | ≤3/5 | qualsiasi | **NO-GO** → handoff S194 fix STEP 2 |
| APPROVED | PASS | qualsiasi | ≤6/9 | **NO-GO** → handoff S194 fix STEP 3 |
| APPROVED | MED/HIGH residui | qualsiasi | qualsiasi | **NO-GO** → fix code-reviewer issues prima |
| NEEDS_REVISION | n/a | n/a | n/a | **NO-GO HARD** → fix mirato S194 prima TEST_FOUNDER |
| REJECTED | n/a | n/a | n/a | **NO-GO HARD** → revert + fresh restart S194 |
| NOT_DONE / risposta ambigua | n/a | n/a | n/a | **BLOCKED** → idle, Luke rilancia con validazione |

**Regola d'oro**: validazione esterna APPROVED da sola NON sblocca Day 1. Tutte e 4 le dimensioni devono essere verdi.

### Output STEP 4

Scrivere `state/s193_day1_decision.md` con:
- Tabella evidence step 0-3 con timestamp + reference
- Decisione GO/NO-GO motivata
- Se GO: prompt `s194_day1_stile_car_send.md` (Day 1 reale unico dealer)
- Se NO-GO: prompt handoff specifico

---

## Vincoli ricordati (non sindacabili)

- `feedback_test_founder_means_real_interactive.md`: TEST_FOUNDER = Luke fisico WA + dashboard click + bonifico vero. NON simulato.
- `feedback_e2e_full_test_founder_before_day1.md`: Day 1 reale BLOCKED fino a E2E full TEST_FOUNDER verde.
- `feedback_smoke_test_not_uat_gate.md`: smoke ≠ gate. STEP 2+3 = gate Day 1.
- `feedback_no_live_without_test.md`: NON auto-prompt Day 1 dealer reale post-STEP 3 senza Luke esplicito.
- CLAUDE.md #6: no PARTIAL/ARANCIONE. STEP 0 NEEDS_REVISION → handoff S194 pulito, NON "procedo con cautela".
- CLAUDE.md #0: delegation-first. code-reviewer + validator agent OBBLIGATORI prima commit.

## Reference

- Validation prompt: `/tmp/s192_VALIDATION_PROMPT_FOR_CLAUDE_AI.md`
- Diff completo: `/tmp/s192_full_diff.patch`
- Memory `s192_step1_step2_close_autonomous.md` (claim CTO da verificare)
- Memory `s175_0_e2e_red_ambra_hallucination.md` — anti-pattern scenario 4
- Memory `s171_daemon_duplicate_sends_fixed.md` — pattern dedup scenario 5
- Memory `s178_contract_e2e_verde.md` — pattern contract scenario 2
- Memory `feedback_smoke_test_not_uat_gate.md` — applicato anche a S192
