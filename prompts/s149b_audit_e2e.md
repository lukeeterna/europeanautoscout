# S149b — AUDIT E2E completo (blocker per Day 1 Stile Car martedì 5/5)

**Sessione**: S149b (extension di S149)
**Trigger**: decisione CTO 11:05 → Day 1 Stile Car slittato sabato 2/5 → martedì 5/5. Pre-Day 1 serve audit E2E reale (5 strati pipeline), non solo daemon outbound (1/5 strato fatto in S149).
**Context**: aprire fresh con questa sessione, S149 ha chiuso a 77% context.

---

## 0. Letture obbligatorie (10 min, prima di toccare codice)

1. `~/.claude/projects/.../memory/MEMORY.md` entry "2026-05-01 11:05 — S149 DECISIONE CTO" + "10:55 — CORREZIONE 2"
2. `HANDOFF.md` sezione S149 OUTCOME + S149-extension
3. `tools/test_e2e_full.py` — leggere SOLO per capire cosa testano i 10 test (NON eseguire ancora)
4. `wa-intelligence/response-analyzer.py` — leggere `class ResponseValidator`, `classify_message`, `auto_approve_and_send`, `call_llm` (cascade)
5. `src/cove/image_sanitizer.py` — leggere top-level + funzioni principali

---

## 1. Stato pre-S149b

**Cosa funziona (verificato S149)**:
- ✅ Daemon WA outbound: ack=1/2/3 con `_serialized` matching, payload integro €/è/—/\n\n
- ✅ Day 1 testo `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` pronto
- ✅ Dossier PDF `dossiers/ARGOS_BMW_X3_2022_Stile_Car_20260427_112932.pdf` esiste

**Cosa è incognito (audit in S149b)**:
- ❓ Strato 2: inbound → response-analyzer → classify (LLM cascade health)
- ❓ Strato 3: trigger PDF send su risposta dealer
- ❓ Strato 4: image_sanitizer integrità PDF/foto
- ❓ State machine multi-step DAY1_SENT → DAY3 → DAY7

**Cosa NON esiste (audit confermato)**:
- ❌ Stripe / payment pipeline → BACKLOG M3 (post-PMF)

---

## 2. Sequenza audit S149b (4-8h stimati)

### Step 1 — preflight infra (15 min)
```bash
ssh -o ConnectTimeout=5 gianlucadistasi@192.168.1.2 "uptime && curl -s http://localhost:9191/status"
# Atteso: daemon connected, daily_sent ridotto (counter quotidiano)
```
Verifica `.env` LLM API keys non scadute:
```bash
ssh gianlucadistasi@192.168.1.2 "grep -E 'GEMINI|GROQ|OPENROUTER' ~/Documents/app-antigravity-auto/wa-intelligence/.env | wc -l"
# Atteso: ≥3 chiavi presenti
```

### Step 2 — leggi test_e2e_full.py (30 min)
```
Read tools/test_e2e_full.py
```
Per ogni test (1-10), nota:
- Cosa fa esattamente
- Quali servizi tocca (daemon, analyzer, DB, LLM, scraper)
- Come misura PASS/FAIL
- Side effects (manda WA reali? a chi? TEST_FOUNDER ok, altri NO)

⚠️ **NON ESEGUIRE** test che mandino WA a numeri ≠ TEST_FOUNDER (393314928901). Se il test usa numeri reali → SKIP o modificare prima.

### Step 3 — esegui test_e2e_full.py CON SICUREZZA (60-90 min)
```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
python3 tools/test_e2e_full.py 2>&1 | tee /tmp/s149b_e2e_run.log
```
Per ogni test annotare:
- ✅ PASS / ❌ FAIL / ⏭️ SKIP (con motivo)
- Se FAIL: stack trace + ipotesi root cause
- Se test_4 (send PDF): verificare DB `messages` direzione OUTBOUND con file allegato + image_sanitizer fired
- Se test_5-8 (analyzer): verificare LLM call andata + classify output coerente
- Se test_9 (full conversation): è il test più importante — verificare end-to-end

### Step 4 — image_sanitizer standalone test (30 min)
```bash
# Trovare immagine test
ls assets/post_*.png | head -3
# Eseguire sanitizer su un'immagine reale
python3 -c "
from src.cove.image_sanitizer import sanitize_image  # adattare import name reale
result = sanitize_image('assets/post_1_bmw_x3.png', output='/tmp/sanitized_test.png')
print(result)
"
# Confronto: exiftool /tmp/sanitized_test.png vs exiftool assets/post_1_bmw_x3.png
# Verificare: EXIF rimosso, watermark rimosso, source obfuscated
```
Documentare cosa il sanitizer fa effettivamente vs cosa promette.

### Step 5 — LLM cascade health check (30 min)
```bash
# Test ogni provider della cascade
python3 -c "
import os
from wa_intelligence.response_analyzer import call_gemini  # adattare
result = call_gemini('You are helpful', 'Say only OK')
print(result)
"
# Ripetere per Groq, OpenRouter, Gemini Lite, Ollama
# Tutti devono rispondere o circuit breaker triggerare correttamente
```

### Step 6 — scrivere E2E-AUDIT-S149.md (45 min)
Crea `.planning/E2E-AUDIT-S149.md` con:
```markdown
# E2E Audit S149 — Risultati nudi

## Test E2E (test_e2e_full.py)
| Test | Risultato | Note |
|------|-----------|------|
| 1 daemon_status | ✅/❌ | ... |
| 2 dealer_in_pipeline | ... | ... |
...

## Image sanitizer
Stato: ✅/❌
Cosa fa: ...
Cosa NON fa: ...

## LLM cascade
| Provider | Stato | Latenza | Note |
| Gemini | ... | ... | ... |
...

## Rotture priorizzate (P0/P1/P2)
P0 (blocker Day 1):
- ...
P1 (blocker Day 3):
- ...
P2 (nice-to-have):
- ...

## Decisione finale
- (a) Day 1 martedì 5/5 OK perché P0 è chiuso → procedere
- (b) Day 1 slitta ulteriormente perché P0 ha N rotture → fixare prima
```

### Step 7 — fix P0 rotture (variable)
Fixare solo P0 (blocker Day 1). P1/P2 vanno in BACKLOG. Test post-fix.

---

## 3. Vincoli S149b

- ✋ **NO invio WA a dealer reali** (Stile Car, Sa.My, Car Plus, etc) durante audit
- ✋ **NO modifica daemon WA** (S149 fix è solido, non toccare)
- ✋ **NO Stripe / payment** (backlog M3, fuori scope)
- ✋ **Documentare TUTTO** in `.planning/E2E-AUDIT-S149.md` — niente claim non supportato
- ✋ Se context >80% e audit non finito → STOP e crea S149c (no slittamento ulteriore Day 1, ma audit completo prima di Day 1)
- ✋ Se trovi rotture P0 troppo profonde da fixare in <8h → reportare a Luke per decisione (slittare Day 1 oltre martedì OPPURE accettare rischio mitigato)

---

## 4. Pre-flight rapido S149b

```bash
# 1. SSH iMac
ssh -o ConnectTimeout=5 gianlucadistasi@192.168.1.2 "uptime"

# 2. Daemon online (è nightly da S149)
ssh gianlucadistasi@192.168.1.2 "curl -s http://localhost:9191/status"

# 3. Test file esiste
ls -la tools/test_e2e_full.py

# 4. Sanitizer file esiste
ls -la src/cove/image_sanitizer.py
```

---

## 5. Target di fine S149b

- ✅ 10 test E2E eseguiti, risultati nudi documentati
- ✅ image_sanitizer validato (o flagged broken)
- ✅ LLM cascade health verificata
- ✅ `.planning/E2E-AUDIT-S149.md` scritto e committato
- ✅ Lista P0/P1/P2 rotture priorizzata
- ✅ Decisione su Day 1 martedì 5/5: GO o slittare

OPPURE

- ✅ Audit parziale + S149c per finire prima di martedì
- ✅ Day 1 ricalibrato a data realistica con tutto verde

---

## 6. Riferimenti rapidi

- iMac IP: `192.168.1.2`
- Daemon: `http://192.168.1.2:9191`
- TEST_FOUNDER (unico numero permesso per send WA test): `393314928901`
- Stile Car (NO touch): `393334254654`
- Test E2E: `tools/test_e2e_full.py` (10 test)
- Analyzer: `wa-intelligence/response-analyzer.py` (83KB)
- Sanitizer: `src/cove/image_sanitizer.py` (39KB)
- Daemon (fixato S149): `wa-intelligence/wa-daemon.js`
- Backup sanitizer pre-S113b: `src/cove/image_sanitizer.py.bak_s113b`

---

## 7. Decisione CTO presa S149 (immutabile salvo Luke override)

**Day 1 Stile Car target: martedì 5/5 mattina ore 11:00.**
**Sabato 2/5: NO INVIO.**
**Stripe: BACKLOG M3 post-PMF.**

Responsabilità di questa decisione: presa S149 11:05 dopo richiesta esplicita Luke "consiglio cto che si prende la piena responsabilità".
