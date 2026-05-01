# S149c — AUDIT E2E chunk B (continua S149b)

**Sessione**: S149c (chunk B di audit E2E pre-Day 1 Stile Car martedì 5/5)
**Trigger**: S149b chunk A ha chiuso a context ~80% con P0 templates.py risolto. Restano image_sanitizer, LLM cascade isolato, re-run completo test E2E, scrape live, finalizzazione audit doc, decisione GO/NO-GO definitiva.
**Context**: aprire fresh, S149b ha consumato ~80%.

---

## 0. Letture obbligatorie (10 min)

1. `.planning/E2E-AUDIT-S149.md` — risultati S149b chunk A (P0 templates.py FIXATO, P1 Gemini, P2 image_sanitizer/test10/IP)
2. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` entry S149b
3. `HANDOFF.md` sezione S149b OUTCOME

**NON ri-leggere** test_e2e_full.py, response-analyzer.py, image_sanitizer.py se hai già il riassunto: vai direttamente all'esecuzione.

---

## 1. Stato pre-S149c

**Verde verificato S149b**:
- ✅ Daemon WA outbound (S149)
- ✅ Pipeline DB + TEST_FOUNDER ready
- ✅ test_e2e_full.py test 1-4 PASS
- ✅ Response analyzer post-fix `templates.py` → standalone test verde (CURIOSITY classify + Groq llama-3.3-70b OK + validator + reply schedulata + Telegram 200)
- ✅ IP fix `.12 → .2` in test_e2e_full.py committato

**Da chiudere S149c**:
- ⏳ Re-run test_e2e_full.py --fast completo per capture verde test 5-9 post-fix
- ⏳ Test 10 (scrape live BMW X3, ~5 min)
- ⏳ image_sanitizer standalone test
- ⏳ LLM cascade isolato per provider
- ⏳ Decisione DEFINITIVA GO/NO-GO Day 1 martedì

---

## 2. Sequenza S149c (3-5h stimati)

### Step 1 — re-run test_e2e_full.py --fast (15 min)
```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
python3 tools/test_e2e_full.py --fast 2>&1 | tee /tmp/s149c_e2e_run.log
```
Atteso: 14+ PASS / 0-1 FAIL.
Se test 5-9 ancora rossi → ROOT CAUSE ANALYSIS analyzer (può essere altro bug oltre templates.py).
Se verdi → procedere step 2.

⚠️ Quota WA daily: stimato consumo ~5-10 sends a TEST_FOUNDER. Verificare `daily_remaining` prima:
```bash
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status | grep daily_remaining"
```
Se `daily_remaining < 8` → SKIP re-run completo, fare solo test 5 standalone:
```bash
ssh gianlucadistasi@192.168.1.2 'cd ~/Documents/app-antigravity-auto/wa-intelligence && export $(grep -v "^#" .env | xargs) 2>/dev/null && python3 response-analyzer.py --msg-id smoke_$(date +%s) --msg-body "Si mi interessa, cerco un BMW X3 budget 35mila" --dealer-id TEST_FOUNDER --dealer-name "Test" --persona NARCISO --step CONTACTED --db-path /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite 2>&1 | tail -25'
```

### Step 2 — image_sanitizer standalone (45 min)

**Decisione preliminare**: Day 1 Stile Car invia SOLO TESTO (no PDF, no foto). Quindi image_sanitizer NON è blocker Day 1, è blocker Day 3+ (quando arriva richiesta dossier dal dealer).

Fare il test comunque per chiudere il gap, ma con priorità ridotta: se trova rotture, NON slittare Day 1 — schedulare fix in S151+ prima del Day 3 send.

```bash
# Su iMac (deps installate per produzione)
ssh gianlucadistasi@192.168.1.2 << 'EOF'
cd ~/Documents/app-antigravity-auto
ls -la src/cove/image_sanitizer.py src/cove/image_sanitizer.py.bak_s113b
diff src/cove/image_sanitizer.py src/cove/image_sanitizer.py.bak_s113b | head -50
EOF
```
Identificare cosa è cambiato in S113b vs backup.

Poi test funzionale su immagine reale:
```bash
ssh gianlucadistasi@192.168.1.2 << 'EOF'
cd ~/Documents/app-antigravity-auto
ls dossiers/safe_images/raw/*.jpg | head -3
# Pick one
TEST_IMG=$(ls dossiers/safe_images/raw/*.jpg | head -1)
python3 -c "
import sys; sys.path.insert(0, 'src/cove')
from image_sanitizer import sanitize_image
result = sanitize_image('$TEST_IMG', output_dir='/tmp/test_sanitize/')
print(f'Result: {result}')
"
ls -la /tmp/test_sanitize/
EOF
```
Verificare:
- File output esiste
- Confronto exiftool input vs output (EXIF strip)
- Ispezione visiva (banner sparito? watermark sparito?)

Documentare nudo: `image_sanitizer ✅/❌`.

### Step 3 — LLM cascade health isolato (30 min)

```bash
ssh gianlucadistasi@192.168.1.2 << 'EOF'
cd ~/Documents/app-antigravity-auto/wa-intelligence
export $(grep -v "^#" .env | xargs)
# Check chiavi disponibili
echo "GEMINI: ${GEMINI_API_KEY:0:8}... (${#GEMINI_API_KEY} char)"
echo "GROQ: ${GROQ_API_KEY:0:8}... (${#GROQ_API_KEY} char)"
echo "OPENROUTER: ${OPENROUTER_API_KEY:0:8}... (${#OPENROUTER_API_KEY} char)"
EOF
```

Poi grep `response-analyzer.py` per capire come `call_gemini` / `call_groq` / `call_openrouter` sono implementati, e capire se Gemini `MAX_TOKENS` è bug `max_output_tokens` troppo basso o prompt troppo lungo. Fix se trovato.

### Step 4 — test 10 scrape live BMW X3 (5-6 min)
```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
timeout 360 python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 40000 --dealer 'Test E2E S149c' 2>&1 | tail -30
```
Atteso: ≥1 PROCEED + PDF generato.
Se 0 PROCEED → scraper rotto → P1 (non blocker Day 1 perché dossier Stile Car esiste già).

### Step 5 — finalizza .planning/E2E-AUDIT-S149.md (30 min)

Aggiornare sezione "DECISIONE Day 1 martedì 5/5":
- Tabella finale test E2E (tutti 10 test)
- image_sanitizer status definitivo
- LLM cascade health per provider con stato/latenza
- Lista P0 residui (se zero → Day 1 GO)
- Lista P1/P2 da BACKLOG

Chiudere con verdetto **DEFINITIVO**:
- (a) 🟢 GO Day 1 martedì 5/5 ore 11:00 — P0=0
- (b) 🟡 GO con riserva — P0=0 ma P1 critici monitorare
- (c) 🔴 SLITTARE — P0>0, audit chunk C necessario

### Step 6 — prompt S150 Day 1 Stile Car (se GO)

Creare/aggiornare `prompts/s150_day1_stile_car_martedi.md` (rinomina da `s150_day1_stile_car_sabato.md` con date update).

---

## 3. Vincoli S149c (ereditati S149b)

- ✋ NO invio WA a dealer reali (solo TEST_FOUNDER 393314928901)
- ✋ NO modifica daemon WA (S149 fix solido)
- ✋ NO Stripe (BACKLOG M3)
- ✋ Documentare TUTTO in `.planning/E2E-AUDIT-S149.md` finale
- ✋ Se context >80% e audit non finito → S149d (NO Day 1 senza audit completo)
- ✋ Se trovi P0 nuovi non fixabili in <4h → reportare, non saltare

---

## 4. Pre-flight rapido S149c

```bash
# 1. iMac up
ssh -o ConnectTimeout=5 gianlucadistasi@192.168.1.2 "uptime && curl -s localhost:9191/status | grep -E 'wa_status|daily'"

# 2. templates.py iMac AST OK (dovrebbe essere fixato S149b)
ssh gianlucadistasi@192.168.1.2 'python3 -c "import ast; ast.parse(open(\"/Users/gianlucadistasi/Documents/app-antigravity-auto/wa-intelligence/templates.py\").read()); print(\"AST OK\")"'

# 3. Backup S149b presente (safety)
ssh gianlucadistasi@192.168.1.2 "ls -la ~/Documents/app-antigravity-auto/wa-intelligence/templates.py.bak_s149b_*"
```

---

## 5. Target di fine S149c

✅ Tutti 10 test E2E eseguiti, risultati nudi
✅ image_sanitizer validato (o flagged broken non-blocker)
✅ LLM cascade health verificato per provider
✅ `.planning/E2E-AUDIT-S149.md` chiuso con decisione finale
✅ Lista P0/P1/P2 priorizzata
✅ Decisione GO/NO-GO Day 1 martedì 5/5 — committata su HANDOFF.md
✅ (Se GO) prompts/s150_day1_stile_car_martedi.md aggiornato

---

## 6. Riferimenti rapidi

- iMac IP: `192.168.1.2`
- Daemon: `http://192.168.1.2:9191`
- TEST_FOUNDER (unico WA test): `393314928901`
- Stile Car (NO touch): `393334254654`
- DB iMac: `/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite`
- Test E2E: `tools/test_e2e_full.py` (10 test, IP fixato S149b)
- Analyzer: `wa-intelligence/response-analyzer.py` (83KB)
- Sanitizer: `src/cove/image_sanitizer.py` (39KB) + `.bak_s113b`
- Templates fixed: `wa-intelligence/templates.py` su iMac (267 righe, AST OK) + backup S149b

---

## 7. Decisione CTO ereditata S149

**Day 1 Stile Car target: martedì 5/5 mattina ore 11:00.**
Sabato 2/5: NO INVIO. Stripe: BACKLOG M3.

S149c può confermare (GO) o slittare ulteriormente se P0 nuovi.
