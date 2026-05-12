# S164 — E2E Full Pipeline Test su TEST_FOUNDER (gate Day 1 Stile Car)

## Contesto
S163 ha chiuso verde: sanitizer Apple Vision Framework operativo, 2 commit pushati master (`70de02c..23d120a`). Backup `src/cove/image_sanitizer.py.bak_s163` esiste.

**Vincolo Luke (2026-05-12 18:35, memory `feedback_e2e_full_test_founder_before_day1.md`)**: NESSUN Day 1 reale a Stile Car finché la pipeline COMPLETA contatto → dossier → pagamento non gira verde end-to-end su TEST_FOUNDER `393314928901`. UAT visivo sanitizer da solo NON sblocca.

## Goal sessione
Smoke E2E full su TEST_FOUNDER, 4 step:
1. **Contatto**: Day 1 WA delivered + risposta dealer simulata + classificazione analyzer + Day 3 schedulato
2. **Dossier**: PDF enterprise generato con S163 sanitizer attivo (immagini sanitized = Vision Framework) + delivery via WA
3. **Fattura**: emissione TD17/18/19 corretto su listing test (verifica solo, no invio reale)
4. **IBAN flow**: send-iban + mark-paid worker Cloudflare end-to-end + wa_sent:true conferma

Tutto su numero **393314928901**, zero dealer reali.

## Pre-conditions verificare prima di iniziare
```bash
# 1. WA daemon online iMac
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"

# 2. Sanitizer S163 attivo (vision_ocr lazy-load + pyobjc presente MacBook)
python3 -c "from src.cove.vision_ocr import detect_text_regions; print('OK')"

# 3. 23 imgs S163 ancora presenti
ls /tmp/argos_s163_e2e/ | wc -l   # atteso: 23

# 4. Cloudflare Worker tail funzionante per step 4
# (URL e secret in argos-proxy/wrangler.toml + tail con `wrangler tail`)
```

Se qualcosa rosso → STOP, riporta in memory, NON procedere.

## Step operativi

### Step 1 — Esegui test_e2e_full.py esistente (verifica baseline)
```bash
python3 tools/test_e2e_full.py 2>&1 | tee /tmp/s164_e2e.log
```
Atteso: 10 test, mix PASS/FAIL noti. Annota quali FAIL su `/tmp/s164_e2e.log`. NON tentare fix retroattivi qui — annota in BACKLOG se nuovi, fix solo se bloccano step 2-4.

### Step 2 — Verifica sanitizer S163 nel PDF generato
Il PDF in `test_4_send_pdf` usa `ARGOS_BMW_X3_2022_Stile_Car_ee60eed0.pdf` pre-generato. Per testare S163:
```bash
python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 40000 --dealer "TEST_FOUNDER"
```
Verifica:
- Nuovo PDF in `dossiers/` ha immagini con S163 sanitizer (no watermark dealer DE residuo)
- File size PDF > 1MB (no fallback RAW dovuto a sanitizer fail come S158 caveat)
- Log mostra `Vision OCR (Apple Framework) initialized` (lazy-load triggerato)

### Step 3 — Test fattura TD17/18/19 (verify-only)
ARGOS regime fiscale per import EU: TD17 (reverse charge servizi UE), TD18 (acquisti intracomunitari beni), TD19 (acquisti UE con IVA italiana). Verifica:
```bash
# Cerca tool fattura/fee_calculator
grep -rn "TD17\|TD18\|TD19\|reverse_charge\|fattura" tools/ src/ --include="*.py" | head -20
```
Se tool fattura esiste → run dry-run su TEST_FOUNDER (output XML/PDF in `/tmp/`, NO invio). Se tool NON esiste → annota gap critico in BACKLOG (vincolo Luke richiede step 4 verde, fattura è prerequisito).

### Step 4 — IBAN flow su Cloudflare Worker
```bash
# Da S155-tris infrastruttura funnel Tailscale OK + S156 PM2 launchd OK.
# Verifica worker proxy → daemon iMac via Tailscale Funnel
curl -X POST https://argos-proxy.workers.dev/send-iban \
  -H "Authorization: Bearer $ARGOS_API_KEY" \
  -d '{"phone":"393314928901","amount":"800","listing_id":"TEST_S164"}'

# Atteso JSON: { wa_sent: true, msg_id: "..." }
# Tail worker: wrangler tail argos-proxy
```
Se `wa_sent: false` → guarda errori (HTTP 403/timeout/Tailscale cert exp). Annota.

Poi:
```bash
curl -X POST https://argos-proxy.workers.dev/mark-paid \
  -H "Authorization: Bearer $ARGOS_API_KEY" \
  -d '{"listing_id":"TEST_S164","amount":"800"}'

# Atteso: wa_sent: true (conferma "pagamento ricevuto, dossier in arrivo")
```

## Closure criteria

**VERDE** sblocca Day 1 Stile Car:
- Step 1: ≥9/10 test PASS in `test_e2e_full.py`
- Step 2: PDF nuovo > 1MB con sanitizer S163 attivo (log `Vision OCR ... initialized`)
- Step 3: tool fattura esistente E dry-run pulito O gap documentato chiaramente (Luke decide se gap = blocker)
- Step 4: `send-iban` + `mark-paid` entrambi `wa_sent: true` con WA delivered su TEST_FOUNDER (2 messaggi visibili)

**Aggiorna memory**: `s164_e2e_full_test_founder_green.md` con prove (log path, msg_id WA, PDF path).

**ARANCIONE/PARTIAL vietato** (vincolo 6 CLAUDE.md): se non chiude verde → HANDOFF strutturato con prompt resume `s165_*.md` E **Day 1 Stile Car resta gated**.

## Vincoli sessione

- **NON inviare a dealer reali** (Stile Car o altri): blocked finché S164 non verde
- **Context budget**: `/context` ogni 5-10 turni, sopra 60% chiusura ordinata
- **Verifica fattuale**: ogni claim ("PASS", "wa_sent:true") deve avere prova grep-able nel log
- **Zero cost**: nessuna nuova lib, nessun nuovo servizio paid
- **Pattern recognition S159-S162**: se step 3 (fattura) o step 4 (worker) hanno dependency hell ML → STOP, NO workaround locale, document gap e propor offload service esistente

## File chiave
- `tools/test_e2e_full.py` — script E2E esistente (10 test, da estendere step 4)
- `tools/on_demand_runner.py` — scrape→CoVe→PDF con sanitizer S163
- `src/cove/image_sanitizer.py` + `src/cove/vision_ocr.py` — S163 sanitizer
- `argos-proxy/` — Cloudflare Worker (send-iban, mark-paid)
- `wa-intelligence/response-analyzer.py` — classificazione risposta dealer
- `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` — target Day 1 (post-gate)

## Memory da leggere prima di iniziare
- `feedback_e2e_full_test_founder_before_day1.md` (vincolo hard Luke)
- `feedback_no_live_without_test.md` (no prompt Day 1 auto-eseguibile)
- `feedback_context_budget_gate.md` (context >50% no nuovo scope)
- `feedback_false_positive_lazy_import.md` (gate = istanza+call reale, no import top-level)
- `s163_closure_vision_framework.md` (stato sanitizer)

## Out-of-scope (defer)
- Send dealer reale qualsiasi
- UAT visivo S163 (rimane gate parallelo Luke, indipendente da S164)
- Nuove feature, refactor, scope discovery
- Estensione test analyzer oltre i 4 step pipeline
