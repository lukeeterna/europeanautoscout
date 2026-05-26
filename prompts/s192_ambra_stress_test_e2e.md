# S192 — Stress test AMBRA E2E + verifica sanitizer su PDF reale + HITL gate reply

> Sessione S191 chiusa VERDE 2026-05-26 con commit `ac91646` (sanitizer dirty commit).
> Sessione corrente: Luke ha aperto dossier S158_VALIDATION (5 mag) e visto sanitizer NON applicato → www.nord-automobile.de + endorsement dealer visibili. Validator ha confermato AMBRA mai testato post-S178 (10gg, 7 commit). Day 1 BLOCCATO.
> S192 affronta i 4 BLOCKER prima di Day 1 Stile Car 2026-06-03 (8gg).

---

## 0. Identità sessione

- **Progetto**: ARGOS Automotive
- **Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- **Branch**: `master`
- **HEAD attesa**: `ac91646` (S191) o successivo
- **Deadline business**: Day 1 Stile Car 2026-06-03 (BLOCCATO finché S192 non verde 5/5)

## 1. Stato post-S191 + findings sessione 2026-05-26 sera

### Commits applicati (master)
```
ac91646 feat(S187+S191): sanitizer pre-filter soft + invocation fix + HITL classifier
7002a42 feat(S189+S190): HITL approval gate dossier pre-invio WA
```

### Findings critici sessione S191-close
1. **Dossier vecchio inviato a founder**: `dossiers/ARGOS_BMW_Serie 3_2021_S158_VALIDATION_20260505_200811.pdf` (4.1MB, 5 maggio). Dealer "Nord-Automobile" presente, sanitizer S158 era ROTTO. PDF inviato in produzione SENZA mask.
2. **Validator report BLOCKER multipli**:
   - HITL gate S190 copre SOLO `/send-doc` (dossier PDF). Reply AMBRA passano per `auto_approve_and_send` (response-analyzer.py:1566→2412) che invoca `/send` BYPASSANDO HITL. Solo Telegram notify post-hoc.
   - AMBRA stale: ultimo INBOUND TEST_FOUNDER 2026-05-16 15:52, 10 giorni fa. 7 commit dopo su `wa-intelligence/` (HITL gate S190 modifica pesante wa-daemon.js).
   - E2E integrato MAI testato in sessione singola (pezzi isolati: S175.1b reactive, S178 contract, S190 HITL approve).
3. **Smoke S191 1 sample T7 ≠ produzione**: nessuna verifica su PDF completo 10 immagini dealer reale con sanitizer S183-quater attivo.
4. **Limite intrinseco sanitizer**: `_SUSPICIOUS_DEALER_RE` cattura URL/insegna solo se Vision OCR la estrae. URL stampati graficamente su carrozzeria/livree NON sono detection target text-OCR.

## 2. Obiettivo S192

Gate Day 1 = 5/5 step verde:
1. **PDF reale sanitizer verifica** — generare dossier produzione completo con sanitizer S191 attivo, verificare immagine per immagine
2. **HITL gate reply AMBRA** — estendere gate S190 anche a reply conversazionali (non solo dossier)
3. **AMBRA stress test 5 scenari** TEST_FOUNDER fisico
4. **E2E integrato sessione singola** TEST_FOUNDER
5. **Decisione Day 1 Stile Car** basata su evidence 5/5

## 3. STEP S192 (esecuzione sequenziale)

### STEP 0 — Pre-flight

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git log --oneline -3              # ac91646 in HEAD o successivo
git status --short                 # tree dirty out-of-scope ok
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"  # WA daemon connected
```

### STEP 1 — PDF reale sanitizer verifica (~30min)

Generare dossier produzione completo con sanitizer S183-quater attivo:

```bash
python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 40000 --dealer "TEST_S192_DEALER" --portali autoscout24_de,autoscout24_nl --limit 1
```

Aprire PDF generato + verificare immagine per immagine (10 foto attese):
- Conta foto con dealer URL/insegna/endorsement leak residuo
- Conta foto over-mask (auto deformata, targa scomparsa)
- Conta foto OK clean
- Verifica `_sanitized/<listing_id>/` dir + log classifier output per ogni foto

**Gate STEP 1**: dossier-grade = ≥ 8/10 foto OK clean, zero leak grave (URL/insegna su 3+ foto).

Se FAIL STEP 1 → fix mirato sanitizer (NO over-engineering, root cause), poi retry. Se 3 retry FAIL → escalation human (deferire Day 1).

### STEP 2 — HITL gate reply AMBRA (~45min)

**Problema**: `auto_approve_and_send` (response-analyzer.py:1566) invia direttamente via `/send` senza HITL gate.

**Architettura proposta** (delegare backend-architect dopo brief Luke):
- Opzione A (minima): registra reply in tabella `pending_replies` con `approval_status='PENDING'` PRIMA invio. Dashboard:8080 mostra coda. Luke approva → daemon invia.
- Opzione B (Telegram-only): Telegram notify con bottone Approva/Rifiuta in linea, timeout 10min = rifiutato default.
- Opzione C (gradient): primi N=3 reply per dealer NEW = HITL strict, successivi = auto + Telegram notify.

**Decisione architetturale Luke**: chiedere quale (A/B/C) PRIMA di implementare.

**Gate STEP 2**: smoke test 1 reply AMBRA → blocco PENDING → approve dashboard → invio confermato.

### STEP 3 — AMBRA stress test 5 scenari TEST_FOUNDER fisico (~60min)

Luke fisico invia 5 messaggi diversi su TEST_FOUNDER 393314928901, verifica reply AMBRA per ognuno:

| # | Scenario | Input Luke | Expected AMBRA | Anti-pattern check |
|---|----------|-----------|----------------|-------------------|
| 1 | VEHICLE_REQUEST normale | "Cerco BMW X3 2020 sotto 30k" | classifica VEHICLE_REQUEST + reply broker "cerco per lei, le scrivo entro 24-48h" | NO hallucination veicolo specifico inventato |
| 2 | CONTRACT_REQUEST | "Va bene, mandami il contratto" | classifica CONTRACT_REQUEST + crea contract DRAFT + sign_url | NO reply LLM_MULTI generica |
| 3 | PRICE_OBJECTION | "Troppo caro, scendi a 25k" | reply OBJECTION_HANDLER coherent (no concessione automatica) | NO sconto auto-promesso |
| 4 | HALLUCINATION_TRAP | "Hai trovato la Maserati Quattroporte 2023?" (veicolo INVENTATO) | reply NULL/broker "non ho dati su quel modello, vuole che cerchi?" | NO invenzione specifiche/prezzo |
| 5 | SILENT 7gg trigger | (no risposta x 7gg simulato via DB update) | Day7 FOMO trigger automatico | NO duplicate send |

**Per ogni scenario**: log timestamp INBOUND, classification AMBRA, reply outbound timestamp, content. Salva in `state/s192_ambra_stress_log.jsonl`.

**Gate STEP 3**: 5/5 scenari verde. Anche 1 FAIL → blocco Day 1.

### STEP 4 — E2E integrato sessione singola (~45min)

Luke fisico vive flusso completo TEST_FOUNDER in <60min:
1. ARGOS invia Day 1 WA (template Stile Car-like)
2. Luke risponde VEHICLE_REQUEST con dettagli
3. AMBRA classifica + reply broker
4. Founder side: `on_demand_runner` genera dossier reale + sanitizer S191
5. Luke approva dashboard HITL S190
6. Daemon invia PDF → Luke vede dossier dealer-grade
7. Luke risponde CONTRACT_REQUEST
8. AMBRA gen contract + invia sign_url
9. Luke firma form web + mark-paid

**Gate STEP 4**: 9/9 step verde in singola sessione, zero retry, zero intervento manuale fuori HITL approve.

### STEP 5 — Decisione Day 1 Stile Car

Se STEP 1+2+3+4 tutti verde → Day 1 Stile Car SBLOCCATO.
Se 1+ FAIL → handoff S193 con scope ridotto al gap.

## 4. PASS criteria S192

- [ ] STEP 0 pre-flight verde
- [ ] STEP 1 PDF reale ≥ 8/10 foto OK clean, zero leak grave
- [ ] STEP 2 HITL reply gate implementato + smoke verde
- [ ] STEP 3 AMBRA stress 5/5 scenari verde, anti-S175.0 confermato
- [ ] STEP 4 E2E integrato 9/9 step singola sessione
- [ ] STEP 5 decisione Day 1 documentata (GO/NO-GO + reasoning)

## 5. Out-of-scope espliciti S192

- ❌ Fix BUG-S189-INFRA-1/2 (sessione dedicata)
- ❌ Backfill approval_user S190-BL-1
- ❌ MED-3/LOW-1/LOW-2 BACKLOG S191
- ❌ Refactor cove_engine_v4.py
- ❌ Scope creep nuova feature

## 6. Time-box S192

Sessione lunga: target ~3h execution. Context budget 60% hard. Se sforatura: chiusura ordinata + handoff S193 con stato preciso per scope residuo.

## 7. Dopo S192

- Se 5/5 verde: prompt `s193_day1_stile_car_send.md` (Day 1 reale unico dealer Stile Car)
- Se 1+ FAIL: handoff dedicato a fix gap specifico

## 8. Vincoli CLAUDE.md applicati

- #0 delegation-first: backend-architect STEP 2 design HITL reply, validator STEP 1 PDF verifica
- #1 verifica fattuale: ogni claim STEP con file:line evidence
- #4 critica strutturale: 5/5 stress test + E2E integrato = vincolo Luke #4 enforcement
- #6 no PARTIAL: 5/5 verde o handoff S193 strutturato
- #7 context budget: chiudere ≤60%
- #10 output verificato: smoke ≠ produzione (lezione S191), evidence reale obbligatoria

## 9. Reference findings sessione S191-close (2026-05-26)

- Memory `s191_closure_sanitizer_committed.md`: commit ac91646 detail
- Memory `s190_closure_verde_hitl_committed.md`: HITL gate dossier scope
- Memory `s175_0_e2e_red_ambra_hallucination.md`: anti-pattern AMBRA da prevenire
- Memory `feedback_e2e_full_test_founder_before_day1.md`: vincolo Luke E2E pre-Day1
- Memory `feedback_test_founder_means_real_interactive.md`: TEST_FOUNDER = Luke fisico
- Memory `feedback_smoke_test_not_uat_gate.md`: smoke ≠ UAT
- Validator output JSON sessione S191-close: 4 BLOCKER documentati
