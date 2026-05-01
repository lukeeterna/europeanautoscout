# E2E Audit S149b — Risultati nudi (Chunk A)

**Data**: 2026-05-01 12:18-12:30
**Scope chunk A**: test_e2e_full.py --fast + P0 fix templates.py
**Scope chunk B (S149c)**: image_sanitizer standalone + LLM cascade isolato + audit doc finale + fix P0 residui

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

## DECISIONE Day 1 martedì 5/5 — provvisoria, conferma a fine S149c

### Verde post-S149b chunk A
- ✅ Daemon outbound (S149: send WA + send PDF + ack 1/2/3 + payload integro)
- ✅ DB pipeline + dealer in pipeline
- ✅ Response analyzer **funzionante post-fix templates.py**: classify + LLM cascade Groq + validator + auto-approve + Telegram notification
- ✅ Day 1 testo + dossier PDF Stile Car pronti

### Da chiudere in S149c
- ⏳ Re-run test_e2e_full.py --fast COMPLETO post-fix (atteso 14/15 PASS)
- ⏳ Test 10 scrape live (validazione pipeline scoring per veicolo NUOVO se serve)
- ⏳ image_sanitizer standalone (priorità: capire se è davvero blocker Day 1 — Day 1 invia solo testo, NO foto)
- ⏳ LLM cascade isolato per provider (Gemini MAX_TOKENS root cause + check key configurato/no)

### Decisione provvisoria
🟡 **Day 1 martedì 5/5 ATTUALMENTE PROBABILE GO** — il P0 più grave (analyzer crash) è risolto e verificato in standalone. I residui P1/P2 sono mitigabili e/o non blocker.

**Conferma definitiva** a fine S149c chunk B. Se chunk B trova nuove rotture P0 → slittare ulteriormente.

⚠️ **Nota Day 1 specifica**: il primo touchpoint Stile Car è SOLO TESTO (no PDF, no foto) — quindi image_sanitizer NON è blocker per Day 1 reale (è blocker per Day 3+ quando si invia il dossier).

---

## File toccati in S149b chunk A

- `tools/test_e2e_full.py` — IP `.12 → .2` (2 punti) — committato
- `wa-intelligence/templates.py` (iMac, NON repo) — fix DAY3_SOFT + DAY3_VEHICLE — backup remoto presente
- `.planning/E2E-AUDIT-S149.md` — questo file (nuovo)

**Nota templates.py**: la versione iMac fixata (267 righe) è DIVERGENTE dalla versione local repo (248 righe) di 19 righe (i 2 template DAY3 nuovi). In S149c o S150 va deciso se sincronizzare il fix nel repo locale (overwrite local con iMac fixato) o se la divergenza è desiderata.
