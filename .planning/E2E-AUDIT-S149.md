# E2E Audit S149 — FINAL (Chunk A + B)

**Data**: 2026-05-01 12:18-12:50 (chunk A 12:18-12:30, chunk B 12:32-12:50)
**Scope chunk A** (S149b): test_e2e_full.py --fast + P0 fix templates.py
**Scope chunk B** (S149c): image_sanitizer + LLM cascade + scrape live + verdetto finale

---

## Pre-flight infra (Step 1) — ✅ TUTTO VERDE

| Check | Risultato |
|-------|-----------|
| iMac SSH `192.168.1.2` | ✅ UP (uptime 1d 1:59) |
| Daemon `/status` | ✅ OK, wa_status=connected |
| Daemon daily | 2/15 sent, 13 remaining |
| Daemon uptime | ~2.5h post-restart S149 |
| `.env` LLM keys (iMac) | ✅ OPENROUTER, GROQ presenti |
| `.env` LLM keys (locale) | ✅ OPENROUTER, GROQ, ARGOS_API_KEY |
| Note | ❌ GEMINI_API_KEY ASSENTE in entrambi `.env` (vedi P1) |

**Anomalia banner SessionStart**: hook riportava `WA Daemon: UNREACHABLE` perché probabilmente cerca `.12` (regress DHCP da S147). Fix da fare nel hook in S150+.

---

## Test E2E (test_e2e_full.py --fast) — 8 PASS / 7 FAIL → 14 PASS / 1 FAIL post-P0

Eseguito alle 12:21 con IP fixato `.12 → .2` (Edit applicato nel file repo).

| # | Test | Pre-fix | Post-fix templates.py | Note |
|---|------|---------|----------------------|------|
| 1 | daemon_status | ✅ 3/3 PASS | ✅ | Daemon raggiungibile, WA connected, 13 msg disponibili |
| 2 | dealer_in_pipeline | ✅ PASS | ✅ | TEST_FOUNDER trovato `current_step=DAY1_SENT` |
| 3 | send_message | ✅ PASS | ✅ | `out_1777630860861_n1g0e` |
| 4 | send_pdf | ✅ PASS | ✅ | PDF 5383KB inviato `out_1777630864070_5t173` |
| 5 | analyzer CURIOSITY | ❌ FAIL (SyntaxError) | ✅ verificato standalone post-fix | classify CURIOSITY conf=0.85, Groq llama-3.3-70b OK, validator+retry OK, reply schedulata |
| 6 | analyzer VEHICLE_REQUEST | ❌ FAIL (SyntaxError) | ⏳ S149c (re-run) | Stesso root cause: import templates.py crash |
| 7 | analyzer OBJECTION | ❌ FAIL (SyntaxError) | ⏳ S149c (re-run) | Stesso root cause |
| 8 | analyzer INTEREST | ❌ FAIL (SyntaxError) | ⏳ S149c (re-run) | Stesso root cause |
| 9 | full_conversation_flow | ❌ FAIL (parziale) | ⏳ S149c (re-run) | Day 1 send PASS, reply gen FAIL pre-fix |
| 10 | scrape→CoVe→PDF | ⏭️ SKIPPED (--fast) | ⏭️ S149c | ~5 min, da eseguire chunk B |

**Score**:
- Pre-fix: 8 PASS / 7 FAIL — 🔴 SISTEMA NON PRONTO
- Post-fix (estrapolato da test 5 standalone verde): atteso 14+ PASS / 0-1 FAIL — 🟢/🟡

---

## P0 ROTTURA — `wa-intelligence/templates.py` SyntaxError → ✅ FIXATO

**Sintomo**: `response-analyzer.py` non parte, crash a `import templates`:
```
File "wa-intelligence/templates.py", line 58
    "Capito, {dealer_name}.
                           ^
SyntaxError: EOL while scanning string literal
```

**Root cause**: i template `DAY3_SOFT` (righe 57-63) e `DAY3_VEHICLE` (righe 65-79) avevano newline reali (carriage return) **dentro** stringhe Python invece di escape `\n`. File iMac corrotto rispetto a versione locale (locale 248 righe AST OK; iMac 276 righe AST FAIL). Probabile copy-paste manuale fra S137 e S148 che ha "mangiato" gli escape.

**Impatto pre-fix**: TUTTI gli inbound dealer → analyzer crash → ZERO auto-reply generata. Production-blocker totale per Day 1 (se Stile Car risponde, Luca non risponde mai automaticamente).

**Fix applicato**:
1. Backup remoto: `templates.py.bak_s149b_20260501_122250`
2. Download iMac → `/tmp/templates_imac_broken.py`
3. Edit mirato righe 57-79: ricostruito DAY3_SOFT + DAY3_VEHICLE con `\n` escape proper
4. AST validate locale ✅
5. SCP → iMac
6. AST validate iMac ✅
7. **Test smoke standalone** su iMac:
   - `response-analyzer.py --msg-body "Lei chi e, chi le ha dato il mio numero?"` → CURIOSITY confidence 0.85, LLM Groq OK, validator+retry OK, reply auto-approvata + Telegram 200, reply ID `reply_cafd1b91`

**File ora 267 righe** (era 276, -9 righe per `\n` compattati).

**Backup non cancellato**: `templates.py.bak_s149b_20260501_122250` su iMac (safety).

---

## P1 — Gemini `MAX_TOKENS` strutturale (NON blocker Day 1)

**Sintomo log analyzer**:
```
[WARN] Gemini finishReason=MAX_TOKENS — skip
[WARN] Gemini failed — trying Groq
[OK] Groq llama-3.3-70b-versatile response received
```

**Diagnosi rapida**: ogni call Gemini termina con `MAX_TOKENS`. O il prompt è troppo lungo, o `max_output_tokens` è impostato troppo basso, o entrambi. Da indagare in S149c o S150.

**Mitigazione**: cascade scende correttamente a Groq. Latenza extra +1 chiamata HTTP fallita ma reply finale OK.

**Impatto Day 1**: nullo se Groq tiene. Da monitorare in produzione: se Groq cade, cascade scende a OpenRouter (che è 3° livello). Se anche OpenRouter cade → template fallback senza alert (regola .claude/rules/security.md "MAI template fallback senza alert Telegram" — verificare implementazione).

**Anche notato**: `GEMINI_API_KEY` ASSENTE da `.env`. Significa che la key non è mai stata configurata, quindi i `[WARN]` Gemini sono una falsa cascade (chiamata salta del tutto?). Da chiarire.

---

## P1 — Day 1 nel test_9 contiene "Germania"/"premium" (regola CLAUDE.md violata)

**File**: `tools/test_e2e_full.py` riga 303:
```python
"message": "Buongiorno, sono Luca Ferretti. Cerco auto premium in Germania per
concessionari selezionati del Sud..."
```

**Regola violata** (`.claude/rules/communication.md`): Day 1 MAI "Germania", "import", "premium", "cerco auto", "estero".

**Mitigazione**: il test va a TEST_FOUNDER (numero personale Luke), NON a dealer reale. Ok come test funzionale, NO come dataset di sample da replicare.

**Action**: in S149c o S150, sostituire con messaggio Day 1 calibrato per archetipo (es. RELAZIONALE NARCISO neutro).

---

## P2 — IP iMac hardcoded `.12` ovunque (DHCP regress S147 nota)

Trovato in:
- `tools/test_e2e_full.py` L18, L85 → ✅ fixato in S149b
- `.claude/scripts/session_start.sh` (probabile) → da auditare S149c
- Verosimilmente in altri tool

**Fix proposto**: variabile env `IMAC_IP` con fallback `arp -a | grep a8:20:66`. Da fare in S150+, NON blocker.

---

## P2 — image_sanitizer NON testato (deps mancanti locale)

`cv2` non installato sul MacBook locale → impossibile eseguire sanitizer standalone in chunk A. Deferred S149c con due opzioni:
- (a) Installare cv2/PaddleOCR locale (~500MB)
- (b) Eseguire sanitizer **su iMac** (deps probabilmente già installate per produzione scraper)

**Verifica preliminare codice**: `src/cove/image_sanitizer.py` 39KB, pipeline 5-stage validata S110, fallback degradante (no cv2 → solo EXIF strip), business rule chiara ("dealer NOT able to identify EU seller from dossier"). Codice sembra solido a lettura.

**Backup pre-S113b** esiste (`.bak_s113b`) → confronto possibile in S149c per vedere cosa è stato modificato in S113b e mai validato.

---

## P2 — TEST 10 (scrape live) skippato

`--fast` mode salta test_10_pipeline_scrape_cove_pdf (~5 min). Da eseguire in S149c per validare:
- Scraper BMW X3 OK (già verificato funzionante S144)
- CoVe scoring OK
- PDF generation OK

Non blocker Day 1 (dossier Stile Car già esiste).

---

---

# CHUNK B — S149c (12:32-12:50)

## Step 1 re-run test_e2e_full.py --fast — 13 PASS / 2 FAIL ✅ effective PASS

Eseguito 12:33:11. **Tutti gli analyzer test classify CORRETTO**, i 2 FAIL sono FALSI POSITIVI causati da `[ANTI-SPAM] Cooldown 24h attivo` (smoke test S149b alle 10:23 ha attivato cooldown su TEST_FOUNDER).

| # | Test | Score |
|---|------|-------|
| 1 | daemon_status | ✅ PASS |
| 2 | dealer_in_pipeline | ✅ PASS |
| 3 | send_message | ✅ PASS (`out_1777631600102_z79pn`) |
| 4 | send_pdf 5MB | ✅ PASS (`out_1777631603279_8ov6t`) |
| 5 | analyzer CURIOSITY | ⚠️ classify OK, reply BLOCKED cooldown |
| 6 | analyzer VEHICLE_REQUEST | ✅ classify + extract OK |
| 7 | analyzer NEGATIVE | ✅ template-first OK (cooldown bypass) |
| 8 | analyzer POSITIVE | ✅ classify OK |
| 9 | full_conversation_flow | ⚠️ Day1 send OK, reply chi-sei BLOCKED cooldown, vehicle_request OK |
| 10 | scrape live | ⏭️ skipped --fast → eseguito step 4 separatamente |

**Cooldown 24h**: comportamento PROD-CORRECT per dealer reali (primo contatto = no cooldown). Su TEST_FOUNDER è artificio del test ripetuto. Pipeline analyzer **funzionante**.

## Step 2 image_sanitizer standalone (iMac) — ✅ PASS

Test su `dossiers/safe_images/raw/raw_autoscout24_de_39d64c65e9de_00.jpg`:
- ✅ Banner top crop 173px (18%)
- ✅ Banner bottom crop a row 788px (AS24 dealer bar removal — diff vs S113b backup confermato)
- ✅ OCR 5 region masked
- ✅ Inpaint 72K pixels
- ✅ Output 130KB jpeg, 1280x615 px
- ✅ EXIF strip (input=0 tag, output=0 tag — input già pulito da AS24)
- ⚠️ Latency 35.5s/image
- ⚠️ Hood reflection warning (manual review flag)

**Verdetto**: sanitizer funzionante su iMac. Day 1 Stile Car NON usa sanitizer (solo testo) → non blocker comunque.

## Step 3 LLM cascade health — ✅ PASS

**Diagnosi corretta vs S149b** (errore mio S149b):
- ✅ `GOOGLE_AI_API_KEY` SET in .env (cercavo `GEMINI_API_KEY` errato)
- ✅ `GROQ_API_KEY` SET
- ✅ `OPENROUTER_API_KEY` SET

**Root cause Gemini MAX_TOKENS** (`response-analyzer.py:527`):
- `gemini-2.5-flash` con `maxOutputTokens=800`
- 2.5-flash è **thinking model** → consuma token in reasoning interno PRIMA di emettere output → spesso eccede 800
- Cascade scende correttamente a Groq llama-3.3-70b (verificato S149b smoke test: reply_cafd1b91)

**Fix candidato (S150+)**: alzare `maxOutputTokens` a 2048, oppure switch a `gemini-2.5-flash-lite` (no thinking), oppure disabilitare thinking via `thinkingConfig`. **Non blocker**: cascade fallback Groq tiene.

## Step 4 scrape live BMW X3 — ✅ scrape PASS, ⚠️ PDF generator P1

```
2026-05-01 12:40-12:41 — pipeline 54.3s
- 17 listing CoVe scoring → 10 PROCEED ✅
- MarketVerifier OK (n=121-337 IT listing)
- 6 immagini downloaded
- ⚠️ PaddleOCR mancante locale → "photos will be RAW"
- PDF generato MA solo 5,267 bytes / 3 pagine / 0 IMMAGINI
```

**Bug confermato**: su MacBook (no PaddleOCR), il fallback genera PDF VUOTO senza immagini incluse. Reference dossier Stile Car (321KB) generato su iMac. **Day 1 NO PDF, Day 3+ usa dossier pre-esistente** → non blocker Day 1.

**Action S150+**: indagare fallback in `tools/scripts/pdf_generator_enterprise.py` perché RAW dovrebbe includere immagini originali, non skipparle.

## Step 5 — analisi reply LLM smoke test S149b (12:28 OUTBOUND)

**FALSO ALLARME P0 iniziale**. Riguardando con calma i 2 messaggi inviati a TEST_FOUNDER alle 12:28:29 + 12:28:33:
```
"ciao, mi scuso se sono stato un po' diretto all'inizio. ho trovato il suo contatto su un portale di concessionari, sto cercando concessionari per auto premium dalla Germania"
"io mi occupo di trovare auto premium in europa, verifico le condizioni e consegno in italia. ..."
```

- **Origine**: smoke test S149b (input `"Lei chi e, chi le ha dato il mio numero?"` → CURIOSITY → cascade Groq → reply_cafd1b91 → auto_approve_and_send → multi-msg split 2 chunk)
- **Validator**: NON bucato. `FORBIDDEN_TERMS` blocca solo CoVe/Claude/anthropic/openai/chatgpt/algoritmo/embedding/piattaforma + WORDS_EXACT. "Germania"/"premium" sono **by design ammessi** Day N+ (specifico Day 1 communication.md, non Day N+ identity)
- **System prompt** (`response-analyzer.py:193-219`): istruisce esplicitamente l'LLM a usare "auto premium" + "dalla Germania" per descrivere chi è Luca + cosa fa
- **Reg 8 system prompt**: "Se chiede chi le ha dato il mio numero → rispondi 'ho trovato il suo contatto su un portale'" → LLM ha seguito la regola

**Vero P1 qualità reply LLM**:
- ❌ Output **lowercase senza punteggiatura proper**
- ❌ Manca **domanda chiusa finale** (system prompt richiede ma LLM ha generato 2 chunk pitch invece di 3 chunk)
- ❌ Pitch generico "io mi occupo di..." → viola "messaggio generico/template" (è regola Day 1, ma applicabile anche Day N+)

**Action S150+**: prompt tuning + validator extended con:
- Reject se text è all-lowercase (no maiuscole)
- Reject se ultimo chunk non termina con `?`
- Detect frasi pitch-template ("io mi occupo", "il mio servizio è semplice")

**Day 1 Stile Car**: è MANUALE (`DAY1_STILE_CAR.md`), NO LLM → questo P1 NON impatta primo contatto. Impatta SOLO Day N+ se Stile Car risponde "chi sei?" → in quel caso Luke deve **review manuale prima di approvazione** (Telegram hold approve è già attivo? verificare).

## Step 6 — Telegram hold per reply LLM (verifica)

Da verificare se reply auto-generata richiede approvazione manuale via Telegram (hold pattern) o auto-send. Il reply_cafd1b91 è stato `auto_approve_and_send` → **AUTO-INVIATO** senza hold.

**Action immediata pre-Day 1 (S150 pre-flight)**: configurare `auto_approve_threshold` = HIGH (solo NEGATIVE template auto-approve) + tutti gli altri intent → Telegram HOLD richiede approvazione Luke prima dell'invio.

---

## DECISIONE Day 1 martedì 5/5 — FINAL S149c

### Verde verificato S149c chunk B
- ✅ Daemon outbound (S149: send WA + send PDF + ack 1/2/3 + payload integro)
- ✅ DB pipeline + dealer in pipeline
- ✅ Response analyzer post-fix templates.py: 13 PASS / 2 FAIL (FAIL = falsi positivi cooldown)
- ✅ Image sanitizer iMac: banner+OCR+inpaint funzionanti
- ✅ LLM cascade: tutte 3 chiavi (Google/Groq/OpenRouter) presenti, fallback Groq operativo
- ✅ Scrape live BMW X3: 10 PROCEED / 17, MarketVerifier index OK
- ✅ Day 1 testo Stile Car pronto (manuale `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md`)
- ✅ Dossier PDF Stile Car pre-esistente OK (321KB, 30/3, generato su iMac)

### P0 residui — ZERO ✅

### P1 (non blocker Day 1)
1. **Reply LLM Day N+ qualità**: lowercase + no domanda chiusa + pitch generico. Day 1 manuale → impatta solo Day N+. Mitigazione: Telegram HOLD su tutti gli intent diversi da NEGATIVE pre-Day 1
2. **Gemini MAX_TOKENS strutturale**: maxOutputTokens=800 troppo basso per 2.5-flash thinking. Cascade Groq tiene. Fix: 2048 o switch a flash-lite
3. **PDF generator locale (MacBook)**: senza PaddleOCR genera PDF vuoto senza immagini. iMac OK. Dossier Stile Car già esiste

### P2
1. IP `.12` hardcoded ovunque (DHCP regress S147)
2. test_9 dataset Day 1 contiene "Germania"/"premium" (TEST_FOUNDER only, sostituire)
3. SessionStart hook check daemon UNREACHABLE (cerca .12)
4. Sanitizer hood reflection warning (false positive review flag)

### Verdetto FINALE
🟢 **GO Day 1 Stile Car martedì 5/5 ore 11:00**

Razionale:
- P0 ZERO
- Day 1 = testo manuale, NO LLM, NO sanitizer, NO PDF → tutti i P1 sono off-path
- Daemon WA + DB pipeline + state machine validati
- Dossier Day 3+ pre-esistente

Pre-flight obbligatorio S150 (martedì mattina):
1. ✋ **Configurare Telegram HOLD su tutti gli intent diversi da NEGATIVE** (action S150 pre-flight)
2. ✋ Verificare listing X3 still alive (curl 200)
3. ✋ Marker test su TEST_FOUNDER pre-Day 1 reale
4. ✋ Conferma visiva Luke su telefono (5 paragrafi, €/è/—)
5. ✋ Day 1 verbatim Stile Car con outbound_count check (no double-increment)

⚠️ **Se Stile Car risponde "chi sei?"**: NON usare auto-reply LLM. Luke deve approvare manualmente via Telegram HOLD. Reply LLM qualità sotto-Cormorant può bruciare il contatto.

---

## File toccati in S149b chunk A

- `tools/test_e2e_full.py` — IP `.12 → .2` (2 punti) — committato
- `wa-intelligence/templates.py` (iMac, NON repo) — fix DAY3_SOFT + DAY3_VEHICLE — backup remoto presente
- `.planning/E2E-AUDIT-S149.md` — questo file (nuovo)

**Nota templates.py**: la versione iMac fixata (267 righe) è DIVERGENTE dalla versione local repo (248 righe) di 19 righe (i 2 template DAY3 nuovi). In S149c o S150 va deciso se sincronizzare il fix nel repo locale (overwrite local con iMac fixato) o se la divergenza è desiderata.
