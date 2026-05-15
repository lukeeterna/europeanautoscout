# S172 ARGOS — Resume P0→P6 da S171 (AMBRA audit completion + pipeline)

**Sessione precedente**: S171 chiusa VERDE via handoff strutturato (vincolo #6) a ~70% context (vincolo #7).
**Stato**: P0 AMBRA audit ~60% completato — findings consolidati nel corpo conversazione S171, MA `wiki/projects/ARGOS/AMBRA-AUDIT.md` NON ancora scritto. P1-P6 pending.

---

## LEGGI PRIMA (canonical, già consultati S171 — re-leggi solo i diff)

**Cross-progetto (VOS canonical)**:
- `/Volumes/MontereyT7/venture-os/wiki/projects/ARGOS/DECISIONS.md` — focus D-26→D-29 (linea 685-823)
- `/Volumes/MontereyT7/venture-os/wiki/projects/ARGOS/COMPILED-STATE.md` (max 200 righe)
- `~/.claude/projects/-Volumes-MontereyT7-venture-os/memory/MEMORY.md` (7 righe index)

**Memory feedback critici S170/S171**:
- `~/.claude/projects/-Volumes-MontereyT7-venture-os/memory/feedback_argos_target_microdealer_commissione.md` — target D-28 micro-dealer commissione P.IVA forfettaria stock<20
- `~/.claude/projects/-Volumes-MontereyT7-venture-os/memory/feedback_wa_daemon_duplicate_sends.md` — bug strutturale già noto (S171 fix in code, verifica pending)
- `~/.claude/projects/-Volumes-MontereyT7-venture-os/memory/feedback_argos_scope_italia.md` — NO geo-anchor in messaggi

**ARGOS plan AMBRA (tutti SUMMARY status: complete 2026-03-27)**:
- `.planning/phases/06-ambra-agent-wa-autonomo/06-01-SUMMARY.md` — multi-msg + typing
- `.planning/phases/06-ambra-agent-wa-autonomo/06-02-SUMMARY.md` — SYSTEM_PROMPT JSON + imperfezioni
- `.planning/phases/06-ambra-agent-wa-autonomo/06-03-SUMMARY.md` — debounce 15s
- `.planning/phases/06-ambra-agent-wa-autonomo/06-04-SUMMARY.md` — KB ARGOS
- `.planning/phases/06-ambra-agent-wa-autonomo/06-05-SUMMARY.md` — anti-ban HumanLike

---

## STATO VERIFICATO S171 (evidenza nel codebase ARGOS)

### AMBRA implementazione (5/5 plan, complete)
- ✅ **wa-daemon.js** (1755 righe) — endpoint `/send-multi` (line 1174), `/send-voice` (line 1283), MessageBuffer debounce (line 627+, `bufferMessage` line 774, `flushBuffer` line 800), HumanLike anti-ban (line 634+: `simulateTyping`/`simulateRecording`/`logNormalDelay`/`checkOnWhatsApp`/`clearPresence`/`isAllowedToSend`), 47 occorrenze pattern.
- ✅ **response-analyzer.py** (2031 righe) — PROMPT_MODULES XML modulari `<IDENTITY>`/`<RULES>`/`<OUTPUT_FORMAT>`/`<TONE>`/`<REGISTER>`/`<ARCHETYPE>` (line 305-353), `build_system_prompt(archetype, cls_type)` (line 356), `_load_knowledge_base()` + `_get_relevant_kb(cls_type, obj_code)` (line 230-289), `parse_llm_responses` JSON multi-fallback (line 797), `auto_approve_and_send` con route /send vs /send-multi (line 1353), `ResponseValidator` 5-check (line 375).
- ✅ **argos_knowledge_base.md** (293 righe) — 7 sezioni: COME FUNZIONA, COSTI, TEMPI, DOCUMENTI, FISCALITA' (TD17 reverse charge), GARANZIA, TRASPORTO + sotto-sezione OBIEZIONI COMUNI (8 obiezioni).
- ✅ **state_machine.py** — FSM COLD → CONTACTED → ENGAGED → INTERESTED → CONVERTING → CLOSED_WON/LOST/ARCHIVED, regole template + max_outbound + requires_inbound per stato.

### wa-daemon duplicate sends fix S171 (Open Q #12) — IN CODICE, verifica pending
**Patch in `wa-daemon.js`**:
- `ensureBridgeOutboundSchemaS171(bdb)` line 270-284 — schema migration additive: `processing_ts INTEGER`, `attempt_count INTEGER DEFAULT 0`
- `isPermanentSendError(errStr)` line 287-289 — regex `/No LID for user|invalid wid|invalid number|not.?registered|forbidden|not.?found/i`
- `BRIDGE_RECLAIM_WINDOW_S = max(120, poll_interval*4/1000)` line 292
- `BRIDGE_MAX_ATTEMPTS = 3` line 293
- `pollBridgeOutbound` line 295-372 — **atomic claim PRE-send** (line 320-326 UPDATE WHERE sent_ts IS NULL AND (processing_ts IS NULL OR processing_ts < ?)) + permanent/transient/capped classification post-error
- Schema migration triggerata da `ensureBridgeOutboundSchemaS171` chiamata in `pollBridgeOutbound` (line 298)

**Schema `bridge_outbound` in `comm-broker/wa_bridge.py`** (line 64-78):
- ⚠️ NO UNIQUE constraint su `(deal_id, target_phone, body_hash)` — fix S171 è SOLO poll-side (previene stessa row processata 2x), NON previene upstream emit 2 rows identiche. Trade-off ragionato S171: atomic claim copre 95% root cause (poll race), upstream dedup è scope creep.

**Test verifica PENDING**:
- ❌ Daemon attivo ma test 3/3 single-send su TEST_FOUNDER richiede founder fisico (A1 S171 confermato test simulato OK ma duplicate-send verification non eseguita ancora).
- ✅ `/status` endpoint risponde OK (curl http://192.168.1.2:9191/status — wa_status: connected, daily 0/20)
- ✅ `/send-multi` accetta payload (curl test dryrun → 400 invalid phone, validation OK)

### Gap-to-D-27 (mystery shopper paradigm, S170-post-close)
**Codice AMBRA progettato per scenario V3 transactional** (carry-over S166→S169 INVALIDATED da D-26→D-27/D-28):
- `<IDENTITY>` module: "Sei tu che hai contattato il dealer PER PRIMO — hai trovato il suo contatto online" → **conflitta con D-27 Layer 3** dove AMBRA gestisce handoff DOPO Layer 2 mystery shopper (dealer ha "sentito parlare" prima)
- `<RULES>` module: hard-coded "ARGOS" banned in messaggi MA in scenario D-27 Layer 3 il dealer ASPETTA contatto da "Argos" → vincolo va invertito (Argos OK ma solo come reaction, mai self-promotion)
- Archetipi NARCISO/RAGIONIERE/BARONE/TECNICO/RELAZIONALE — D-08 OPEN-ipotesi non validata + non target-fit micro-dealer commissione (D-28)
- KB obiezione "Ho gia il mio fornitore" → riformulare per target micro-dealer commissione: "lavoro per commissione, non ho stock" / "il cliente chiede l'auto, non io"

### Gap-to-D-28 (target micro-dealer commissione P.IVA forfettaria)
**KB lessico non calibrato**:
- "il dealer riceve dossier" → target micro NON riceve dossier per stock, lo richiede SU richiesta cliente finale
- "margine €4-7k su premium" → micro-dealer non calcola margine così, calcola commissione % o flat su singola vendita
- "regime IVA ordinaria" sezione FISCALITA' → micro-dealer è P.IVA forfettaria 5-15%, NO reverse charge TD17 (regime forfettario esente)
- Manca lessico micro-dealer: "commissione", "percentuale", "cliente cerca", "non tengo stock", "compro su ordine"

---

## PIANO ESECUZIONE S172 (in ordine)

### P0 completion (~15min) — Scrivi AMBRA-AUDIT.md
Output: `/Volumes/MontereyT7/venture-os/wiki/projects/ARGOS/AMBRA-AUDIT.md`

Struttura obbligatoria:
1. **Stato implementazione 5/5 plan** (estrai da SUMMARY.md verificati)
2. **Architettura verificata** (file + line references concrete)
3. **FSM exam** (state_machine.py STATES, transizioni, requires_inbound)
4. **Gap-to-D-27 mystery shopper** — lista 4-6 punti con file:line da modificare (PROMPT_MODULES identity/rules)
5. **Gap-to-D-28 target micro-dealer** — lista 4-6 punti KB da ricalibrare (FISCALITA', COSTI, OBIEZIONI, lessico)
6. **Retune plan P3** (KB lessico commissione informale + SYSTEM_PROMPT post-mystery-shopper handoff)
7. **Smoke test plan /send-multi** (gated A1 founder fisico — non eseguibile S172 senza founder)
8. **wa-daemon duplicate sends fix S171** — stato (code IN PLACE, verifica pending)
9. **Critica strutturale 4 punti** (vincolo #4 obbligatorio)

### P1 — Research 4-agent blind search (60min cap)
Output: `/Volumes/MontereyT7/venture-os/wiki/projects/ARGOS/RESEARCH-MICRODEALER-COMMISSIONE.md`

Parallelo 4 agent (Agent tool subagent_type=general-purpose o Explore, in single message):
- **Agent 1 — Telegram**: cerca gruppi pubblici "dealer auto Italia commissione", "import auto EU", "auto usato premium" — output canali con conta membri + tipo conversazioni dominanti + signal micro-dealer commissione presence
- **Agent 2 — Facebook Groups**: search "dealer auto usato Italia", "rivenditori auto commissione", "import auto Germania" — output gruppi pubblici + admin activity + signal P.IVA forfettaria target
- **Agent 3 — Google/Reddit/Forum**: r/ItaliaCarOwners, r/automobili, forum settore (Quattroruote forum, AutoScout24 community) — output thread/discussioni dove micro-dealer parlano workflow
- **Agent 4 — Subito.it/AutoScout24.it dealer profile sampling**: pattern recognition profili che vendono 5-15 auto stock con annunci EU origin — output 10 candidati con phone+WA + stock size + business style hint

Output ranked list 10 canali con confidence `[verified]` (joined+observed) vs `[unverified-need-join]` (only metadata public). Timebox HARD 60min — se sforato, deliverable PARTIAL allowed solo se ≥6 canali ranked + nota "Agent X timed out".

### P2 — Verifica fix wa-daemon duplicate sends (gated A1)
**Pre-condizione**: founder fisico online TEST_FOUNDER 3314928901 conferma "pronto a verificare 3/3 single-send".

Test procedura (eseguibile in S172 se founder pronto):
1. SSH iMac: `sqlite3 bridge.sqlite "SELECT name FROM sqlite_master WHERE name='bridge_outbound'"` → schema check
2. Verifica colonne S171: `PRAGMA table_info(bridge_outbound)` → `processing_ts` + `attempt_count` presenti
3. Insert 3 outbound test rows manuali (deal_id S172-DEDUP-001/002/003, body distinto, target 393314928901, approved_ts now)
4. Wait BRIDGE_POLL_INTERVAL_MS (~30s) × 4 = 2min
5. Founder verifica WA: deve ricevere ESATTAMENTE 3 messaggi (uno per row, NO duplicati per row)
6. Query post-test: `SELECT id, sent_ts, sent_status, wa_msg_id, attempt_count FROM bridge_outbound WHERE deal_id LIKE 'S172-DEDUP-%'` → 3 rows con sent_status='ok' + attempt_count=1

Se duplicate observed → escalation: debug Baileys retry layer o aggiungere UNIQUE constraint schema upstream (comm-broker/wa_bridge.py line 64-78).

### P3 — AMBRA re-tune (post-P0 plan, ~45min)
**Modifiche concrete** (file:line da AMBRA-AUDIT.md P0):
- `wa-intelligence/response-analyzer.py` line 305-353 PROMPT_MODULES:
  - `<IDENTITY>`: aggiungere variante `identity_post_handoff` per Layer 3 (dealer ha già sentito di Argos via Layer 2)
  - `<RULES>`: condizionale ban "ARGOS" parola — solo in pre-handoff, OK post-handoff
  - Nuovo modulo `<TARGET_LEXICON>` per micro-dealer commissione (lessico D-28)
- `wa-intelligence/argos_knowledge_base.md`:
  - Sezione COSTI: aggiungere variante "commissione %" / "flat su singola vendita"
  - Sezione FISCALITA': aggiungere "regime forfettario P.IVA 5-15%" + "esenzione reverse charge"
  - Sezione OBIEZIONI: riscrivere "Ho gia fornitore" → "Lavoro su richiesta cliente, non tengo stock"
- Test scenari handoff Layer 2→3 (3 conversation mocks in `tests/test_ambra_layer3.py`)

### P4 — V6 messaggi 3 vs 3 bozze (15min)
Output inline conversazione, founder sceglie:
- 3 bozze **antipattern americano** (CTA-heavy, urgency, formality professionale, sales script)
- 3 bozze **italiano naturale** (intercalari, frase spezzata, no CTA aggressivo, "ho sentito" reactive)
- Founder pick → diventa base V6 msg1 in `research/s172_messaging_v6.md`

### P5 — E2E 15-step TEST_FOUNDER (founder gated A6)
Founder decide auto LIVE: modello + km + prezzo + paese DE/BE/NL/AT.
Scraper deve gestire qualsiasi auto (NON solo BMW 320d) — verifica scraper generic in `tools/scrapers/`.

15 step: Layer 2 mystery shopper inbound (sim) → AMBRA inbound classify → AMBRA outbound multi-msg → founder reply → AMBRA handoff to Luca Ferretti → contract create → sign URL → IBAN flow → mark-paid → audit log.

### P6 — IBAN multipli (deferred post-pipeline-verde)
Layer config IBAN per regione/dealer/scope. Pagamento ufficiale **BONIFICO BANCARIO** (founder explicit S170-post-close).
Trigger: P5 verde end-to-end → P6 attiva.

---

## DECISIONI FOUNDER NON RINEGOZIABILI (canonical)

- **D-26**: V5 cold-lead SUPERSEDED-INVALIDATED (target wrong + paradigm wrong)
- **D-27**: PROPOSED mystery shopper 3-layer (Layer 1 marketing infiltration + Layer 2 mystery shopper WA + Layer 3 AMBRA autonomous). Validation pending P1 research.
- **D-28**: DECIDED target micro-dealer commissione P.IVA forfettaria stock<20. ESCLUDERE stock ≥20.
- **D-29**: DECIDED numero 3314928901 condiviso ARGOS+FLUXION zero-cost pre-revenue. Persona Luca Ferretti / Erica Fluxion solo in CORPO messaggi.
- **A1** (S171): P5 test simulato founder-to-founder su 3314928901 OK
- **A2** (S171): BLIND search 60min cap Telegram+FB+Google ranked 10 canali
- **A5** (S171): 3 bozze antipattern americano vs 3 italiano naturale → founder sceglie
- **A6** (S171): Auto fittizia P5 decisa LIVE da founder
- **Layer 2 mystery shopper REAL su dealer terzi = DEFERRED fino primo revenue**

---

## VINCOLI SESSIONE

- **#5 zero-cost rigoroso** — nessun capex/recurring nuovo
- **#6 mai PARTIAL** — chiusura verde o handoff strutturato con prompt resume
- **#7 context budget** — `/context` ogni 5-10 turni, sopra 60% chiudi
- **#13 pre-action check** — ogni proposta tecnica cita D-XX rif + vincolo founder + fonte dati (skill `pre-action-check` B6 L2 nudge attivo)
- **#4 critica strutturale obbligatoria** — 4 punti autocritica dopo ogni design proposto
- **#1 verifica fattuale** — doc upstream o `--help` reale, mai sintassi inventata
- **#3 mai liste A/B/C/D** su decisioni tecniche — raccomandazione singola motivata

---

## ENTRY POINT S172

Procedi **P0 completion** ora — scrivi `wiki/projects/ARGOS/AMBRA-AUDIT.md` usando i findings consolidati nel corpo del prompt sopra. Una volta scritto + commit, passa a P1 research 4-agent parallel.

Se context sopra 60% durante P1 → chiudi sessione con handoff S173 (vincolo #6 — mai PARTIAL).
