# S175.0 ARGOS — E2E reactive pipeline TEST_FOUNDER HITL-driven (gate pre-mystery-shopper)

**Precondition strutturale**: S174 chiuso GIALLO 2.5/3 + S175 SOSPESO post-discussione 2026-05-15. Pipeline reactive NON mai testata realmente E2E. S164 retract (12 maggio) ha invalidato "verde" precedente perché simulato (admin API, classifier stub, mark-paid finto). Questo prompt è gate prima Path A mystery shopper LUCKY CARS reale.

**Riferimenti vincolanti**:
- `feedback_e2e_full_test_founder_before_day1.md` — E2E full pipeline TEST_FOUNDER green PRIMA Day 1 dealer reale
- `feedback_test_founder_means_real_interactive.md` — "test_founder = Luke fisicamente reagisce realmente, NO response stubs"
- D-15 founder HITL 100% primi 1-3 dealer (Luke decides manual launch per ogni step)
- D-21 workflow info-broker → communication-broker-garante 8-step
- S164 retract Luke verbatim: "tutto deve avvenire realmente. no green light"

---

## SCOPE S175.0

Verificare 9 step E2E pipeline reactive funzionano REALMENTE su TEST_FOUNDER (39<TEST_FOUNDER_NUM>). Output = gap report con fix singolo per gap. NO simulation, NO admin API, NO classifier stub. Solo `on_demand_runner.py` è manual (D-15 HITL).

---

## STATO FATTUALE VERIFICATO (2026-05-15 sera, pre-execution)

Verifiche eseguite in-session prima della scrittura di questo prompt — fatti accertati:

| Componente | Stato | Note operative |
|------------|-------|----------------|
| iMac SSH (alias `imac`) | ✓ alive | `imac.local` non risolve, usa alias `imac` |
| DB iMac path | ✓ `~/Documents/app-antigravity-auto/dealer_network.sqlite` | NON ~/argos (vuoto), NON dealer_network senza prefix |
| DB schema | ✓ tabella `conversations` (NON `dealers`) | Col phone = `phone_number` (NON `phone`) |
| `handoff_source` + `is_micro_dealer` | ✓ presenti | S173 migration confermata |
| TEST_FOUNDER row | ✓ presente | dealer_id=`TEST_FOUNDER`, current_step=`DAY3_SENT`, handoff_source=`cold` |
| wa-daemon HTTP | ✓ 200 su localhost:9191 (iMac) | PM2 `argos-wa-daemon` online |
| `argos-cf-monitor` PM2 | ✓ online | |
| **`argos-dashboard` PM2** | ✗ **NON ATTIVO** | porta 8080 unreachable — **blocker step 9 mark-paid web form** |
| argos-proxy worker | ⚠ alive ma `/api/v1/health` 404 | Worker risponde formato error standard — endpoint `/api/v1/contract/create` da testare |
| `MODEL_SLUG` BMW Serie 1 | ✗ **MANCANTE** | swap a **BMW X1** (presente, profilo dealer micro Sud realistic) |
| Auto-bridge PDF MacBook→iMac | ✗ NON ESISTE | step 6 richiede scp manuale (1-liner deterministico fornito) |
| `response-analyzer.py:1144` `extract_vehicle_request()` | ✓ LLM-based | marca/modello/budget/anno/km estratti |
| `response-analyzer.py:1910-1922` Telegram alert HITL | ✓ con comando ready | NO auto-trigger (D-15 compliance) |
| `wa-daemon.js:1333` `/send-doc` | ✓ endpoint | richiede file_path on iMac (gap PDF transfer) |
| `response-analyzer.py:111-200` `create_contract()` | ✓ integration | POST argos-proxy `/api/v1/contract/create` |
| `dashboard/app.py:542` `/contracts/{id}/mark-paid` | ✓ web form | path corretto Luke (NO admin API S164) |
| `dashboard/templates/contracts.html:77` form HTML | ✓ presente | submit POST mark-paid |

**Fix preventivi pre-execution next session**:
- Step 0 includerà `pm2 start argos-dashboard` (o discovery ecosystem config)
- Vehicle test = BMW X1 2020 budget €18000 (era Serie 1)
- Step 6 include scp 1-liner inline (no manual decision-making Luke)

---

## 9 STEP CON GATE VERIFICA FATTUALE

### STEP 0 — Pre-conditions check + fix preventivi (Claude in-session, ~10min)

```bash
# 0.1 SSH iMac reachable (alias `imac`, NON `imac.local`)
ssh imac "echo OK_$(hostname)" 2>&1 | grep -q OK_ && echo "STEP0.1 SSH VERDE" || echo "STEP0.1 GAP — SSH down"

# 0.2 wa-daemon connected
ssh imac "curl -s localhost:9191/status" | python3 -c "import sys,json; d=json.load(sys.stdin); print('STEP0.2 WA VERDE' if d.get('connected') else 'STEP0.2 GAP — daemon offline')"

# 0.3 PM2 status check + start dashboard se down (FIX preventivo GAP-A)
ssh imac "export PATH=\$PATH:/opt/homebrew/bin:/usr/local/bin; pm2 jlist 2>/dev/null | python3 -c 'import json,sys; data=json.load(sys.stdin); names=[p[\"name\"] for p in data if p[\"pm2_env\"][\"status\"]==\"online\"]; print(\"online:\", names)'"
# Se argos-dashboard NON in lista:
ssh imac "export PATH=\$PATH:/opt/homebrew/bin:/usr/local/bin; cd ~/Documents/app-antigravity-auto && pm2 start ecosystem.config.js --only argos-dashboard 2>&1 | tail -10"
# Verifica post-start:
ssh imac "curl -s -o /dev/null -w 'STEP0.3 dashboard: %{http_code}\n' http://localhost:8080/"
# Expected 200 / 401 / 302. Se 000 → GAP-A confermato blocker step 9.

# 0.4 TEST_FOUNDER row presente
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT dealer_id, dealer_name, phone_number, current_step, handoff_source, is_micro_dealer FROM conversations WHERE dealer_id='TEST_FOUNDER';\""
# Expected: TEST_FOUNDER|Test Concessionaria Founder|39<TEST_FOUNDER_NUM>|<step>|<source>|<flag>

# 0.5 argos-proxy worker contract endpoint reale (NON /health che è 404)
curl -s -X OPTIONS https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/create \
  -H "Origin: https://argos-automotive.pages.dev" \
  -w "\nSTEP0.5 contract-create OPTIONS: %{http_code}\n" 2>&1 | tail -3
# Expected: 200/204 CORS preflight OK. Se 404 → GAP-B worker route broken.

# 0.6 LLM API key disponibile (almeno 1)
ssh imac "grep -c 'GROQ_API_KEY=.\\|GOOGLE_AI_API_KEY=.\\|OPENROUTER_API_KEY=.' ~/Documents/app-antigravity-auto/.env 2>&1"
# Expected: ≥1

# 0.7 MODEL_SLUG BMW X1 conferma (anti-regressione)
grep -n '"X1"' tools/scrapers/autoscout_scraper.py | head -1
# Expected: line 99 "X1": {"universal": "x1"}

# 0.8 Telegram bot credentials presenti
ssh imac "grep -c 'TELEGRAM_BOT_TOKEN=.\\|TELEGRAM_CHAT_ID=.' ~/Documents/app-antigravity-auto/.env"
# Expected: 2 (token + chat_id)

# 0.9 dossiers/ directory + space MacBook
df -h dossiers/ 2>/dev/null | tail -1
ls dossiers/ 2>/dev/null | wc -l
```

**GATE STEP 0**: 0.1, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9 VERDE obbligatorio. 0.3 GAP-A (dashboard offline) e 0.5 GAP-B (worker route) sono blocker hard step 9/8 — fix prima di procedere a step 1+. NO procedere con gap-0 aperti.

### STEP 1 — Handoff mystery_shopper context (Claude, ~5min)

Simula stato dealer SEEDED da Layer 2 (situazione post Path A reale).

```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite <<SQL
UPDATE conversations 
SET handoff_source='mystery_shopper', 
    is_micro_dealer=1,
    current_step='HANDOFF_LAYER3',
    state_updated_at=datetime('now')
WHERE dealer_id='TEST_FOUNDER';
SELECT dealer_id, phone_number, handoff_source, is_micro_dealer, current_step 
FROM conversations WHERE dealer_id='TEST_FOUNDER';
SQL"
```

**GATE STEP 1**: 1 row UPDATE, fields = `mystery_shopper|1|HANDOFF_LAYER3`. Output di SELECT mostra valori corretti.

### STEP 2 — Day 1 AMBRA Layer 3 post-handoff (Luke phone, ~3min)

**LUKE ACTION (phone TEST_FOUNDER → invia WA ad ARGOS WA Business 3281536308)**:
> "Buonasera, ho parlato con un cliente che mi ha menzionato Argos. Lei cerca auto in Germania?"

Questo simula dealer SEEDED post-Layer-2 che richiama. AMBRA Layer 3 deve gestire come inbound + handoff_source='mystery_shopper'.

**GATE STEP 2**: AMBRA risponde entro 90s, rispetta:
- Identity Luca Ferretti (D-OPEN-Q1) — verifica nome citato
- Ban "Argos brand" come opener (D-20) — verifica NO "ARGOS Automotive" formal
- Tono reactive post-handoff (NON cold outbound pitch)
- D-07 max 5 righe + domanda chiusa

Verifica DB inbound + outbound:
```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
SELECT direction, body, created_at 
FROM messages 
WHERE dealer_id='TEST_FOUNDER' 
ORDER BY created_at DESC LIMIT 4;
\""
```

GAP-2.X se: nessuna risposta entro 120s (LLM cascade fail) | tone cold pitch | menziona Argos brand opener | >5 righe.

### STEP 3 — VEHICLE_REQUEST (Luke phone, ~5min)

**LUKE ACTION**:
> "Mi serve una BMW X1 del 2020, budget sui 18000. La trova?"

(NB: BMW X1 NON Serie 1 — Serie 1 manca da MODEL_SLUG, swap fatto per evitare scraper fallback silenzioso)

**GATE STEP 3**:
- AMBRA risponde conferma testuale (NON inventa veicolo specifico — D-21 rule "info-broker non inventa")
- Telegram alert HITL arriva entro 60s con comando `python3 tools/on_demand_runner.py --marca BMW --modello "X1" --budget 18000` pronto (verifica visiva Luke su Telegram)
- `extract_vehicle_request()` LLM-based estrae: marca=BMW, modello=X1, budget=18000, anno=2020

Verifica DB extracted:
```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
SELECT direction, body, created_at 
FROM messages 
WHERE dealer_id='TEST_FOUNDER' 
ORDER BY created_at DESC LIMIT 2;
\""
# Cerca classification + extracted fields in lia_log:
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
SELECT * FROM lia_log WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 1;
\""
```

GAP-3.X se: Telegram alert assente | extracted incompleto | AMBRA inventa veicolo specifico vs conferma ricerca | timing >2min.

### STEP 4 — Manual on_demand_runner (Luke CTO, ~2min wall, ~30-90s exec)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
time python3 tools/on_demand_runner.py --marca BMW --modello "X1" --budget 18000 --dealer "TEST_FOUNDER" 2>&1 | tee /tmp/s175_0_run.log
```

**GATE STEP 4**:
- Exit code 0
- Tempo exec <120s (atteso 30-90s, simile S157 Serie 3 41s)
- PDF generato: `ls -lt dossiers/ARGOS_BMW_X1*.pdf | head -1` → file >1MB
- Log mostra: scrape N≥10 listing → CoVe scored → ≥1 PROCEED → PDF written

GAP-4.X se: 0 listing scraped (scraper X1 broken) | 0 PROCEED (price index calibration off) | PDF <500KB (sanitizer fallback RAW visibility leak) | exit !=0.

### STEP 5 — Visual UAT sanitizer S163 + dossier review (Luke CTO, ~10min)

```bash
PDF=$(ls -t dossiers/ARGOS_BMW_X1*.pdf | head -1)
open "$PDF"
```

**LUKE visual checklist** (chiude anche UAT S163 pending dal 12 maggio):
1. ☐ 12 sezioni D-18 presenti (cover, summary, 5+ veicoli, comparison, CoVe rationale, market data, disclaimer)
2. ☐ Immagini 5+ embedded (no placeholder gray)
3. ☐ Watermark dealer tedesco originario REMOVED (Vision OCR S163)
4. ☐ Targhe RIMOSSE/BLURRED
5. ☐ Banner marketing "Premium Selection / Garantie / Inzahlungnahme" filtered (S158 caveat)
6. ☐ Numeri prezzo/km verosimili (NO €1.234.567 hallucination)

**GATE STEP 5**:
- 6/6 PASS = VERDE (chiude S163 UAT)
- 5/6 con leak minore = GIALLO + BACKLOG
- ≤4/6 = ROSSO blocker step 6

### STEP 6 — PDF transfer + WA delivery (Claude, ~2min)

```bash
# Auto-bridge MacBook→iMac (gap atteso, scriptato deterministicamente)
PDF=$(ls -t dossiers/ARGOS_BMW_X1*.pdf | head -1)
BASENAME=$(basename "$PDF")
scp "$PDF" imac:/tmp/"$BASENAME"

# WA daemon /send-doc
ssh imac "WA_API_KEY=\$(grep -E '^WA_DAEMON_API_KEY=' ~/Documents/app-antigravity-auto/.env | cut -d= -f2); curl -s -X POST http://localhost:9191/send-doc \
  -H 'Content-Type: application/json' \
  -H \"X-API-Key: \$WA_API_KEY\" \
  -d '{
    \"phone\": \"39<TEST_FOUNDER_NUM>\",
    \"file_path\": \"/tmp/$BASENAME\",
    \"caption\": \"BMW X1 2020 — dossier ARGOS\",
    \"dealer_id\": \"TEST_FOUNDER\"
  }' | python3 -m json.tool"
```

**GATE STEP 6**:
- scp exit 0, file presente `/tmp/$BASENAME` su iMac (verifica `ssh imac "ls -la /tmp/$BASENAME"`)
- /send-doc HTTP 200, JSON success
- Luke riceve PDF su TEST_FOUNDER phone entro 30s
- PDF apribile da phone

GAP-6.X se: scp fail (network) | /send-doc 4xx (api_key wrong, file path resolution, daily limit) | PDF arriva corrotto | apertura fail su phone.

### STEP 7 — Cost question + target_lexicon test (Luke phone, ~5min)

**LUKE ACTION**:
> "Bella macchina. Quanto costa il vostro servizio?"

Questo testa esplicitamente target_lexicon GIALLO finding S174.

**GATE STEP 7**:
- AMBRA risponde con D-OPEN-Q5 framing: "€800-1.200 cash a consegna" o equivalente + money-back DEKRA
- Lessico target: "ci guadagna", "macchina", "su ordine", "Germania/Belgio/Olanda"
- NON usa: ROI, percentuali, "pipeline", "fee", "platform", "scout"
- Day 1 rule: prezzo NON nel primo messaggio outbound (qui è reactive post-question, prezzo OK)

GAP-7.X se: AMBRA cost-deflect totale evita prezzo (hard_rules over-dominate target_lexicon — S174 finding confirmed) | usa lessico premium/ROI/pipeline | percentuali invece di numeri EUR netti.

Output funzionale: ground-truth utterance dealer-Luke + AMBRA reply = primo data point reale per S175.5 target_lexicon calibration.

### STEP 8 — Contract flow web form REAL (Luke phone, ~10min)

**LUKE ACTION (phone)**:
> "Ok mi interessa, come procediamo?"

**GATE STEP 8**:
- AMBRA innesca `create_contract()` → POST argos-proxy `/api/v1/contract/create`
- AMBRA invia WA con `sign_url` reale (link cliccabile)
- Luke clicca link da phone → form apre
- Luke compila + sign (NO admin API)
- DB contract row: status DRAFT → AWAITING_DELIVERY

Verifica post-sign:
```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
SELECT * FROM agent_state WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 1;
\""
# NOTA: contracts table potrebbe non esistere in DB iMac — contracts vivono su worker D1 cloudflare.
# Verifica worker side:
curl -s "https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/list?dealer_phone=39<TEST_FOUNDER_NUM>" \
  -H "Authorization: Bearer \$(grep ARGOS_PROXY_ADMIN_TOKEN ~/Documents/app-antigravity-auto/.env | cut -d= -f2)" \
  | python3 -m json.tool 2>&1 | head -30
```

GAP-8.X se: create_contract HTTP 4xx/5xx | sign_url 404 | form non submit | contract row non transition.

### STEP 9 — Mark-paid web form REAL (Luke phone, ~5min)

**Distinzione vs S164**: PATH = dashboard iMac `http://192.168.1.2:8080/contracts/{id}/mark-paid` form HTML (verificato `dashboard/templates/contracts.html:77`), NON admin API.

**LUKE ACTION**:
1. Apre `http://192.168.1.2:8080/contracts` da phone (network locale o Tailscale)
2. Trova contract TEST_FOUNDER row
3. Clicca "Mark Paid" → form POST con paid_amount €1 test simbolico + bank_name "TEST"

Verifica post:
```bash
curl -s "https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/list?dealer_phone=39<TEST_FOUNDER_NUM>" \
  -H "Authorization: Bearer \$TOKEN" | python3 -m json.tool
# Expected: status=PAID, paid_amount=1, paid_at populated
```

**GATE STEP 9**:
- Form submit success (no 5xx)
- Contract DB transitions a PAID
- AMBRA invia conferma WA TEST_FOUNDER ("ricevuto, contratto chiuso") — verifica delivery
- paid_amount = 1.0 (test simbolico)

GAP-9.X se: dashboard 8080 unreachable (GAP-A non risolto step 0.3) | mark-paid form 5xx | DB transition fail | AMBRA no conferma post-paid.

---

## OUTPUT REPORT FINALE (Claude, ~15min post-step-9)

File `data/s175_0_e2e_real_report.md`:

```markdown
## S175.0 E2E Reactive Pipeline Report — TEST_FOUNDER HITL-driven

**Data**: 2026-MM-DD
**Durata totale**: X min wall (target <120min)
**Operatore Luke**: phone TEST_FOUNDER + laptop CTO

### Step results
| # | Step | Stato | Tempo | Evidence/Note |
|---|------|-------|-------|---------------|
| 0 | Pre-conditions | VERDE/GAP-A/GAP-B | Xmin | dashboard status, worker route |
| 1 | SQL handoff | VERDE | Xmin | UPDATE 1 row, fields verified |
| 2 | Day 1 AMBRA | VERDE/GAP | Xmin | identity check, 5-line check |
| 3 | VEHICLE_REQUEST | VERDE/GAP | Xmin | extracted fields, TG alert |
| 4 | on_demand_runner | VERDE/GAP | Xmin | PDF size MB, exit code |
| 5 | UAT sanitizer | VERDE/GAP | Xmin | 6/6 visual checks |
| 6 | PDF delivery WA | VERDE/GAP | Xmin | scp + send-doc 200 |
| 7 | cost question | VERDE/GAP | Xmin | target_lexicon outcome |
| 8 | contract form | VERDE/GAP | Xmin | sign_url, DB transition |
| 9 | mark-paid form | VERDE/GAP | Xmin | dashboard 8080 reachable |

### Gap identificati (priorità decrescente)
**GAP-X.Y — [titolo]**
- Sintomo verbatim
- Root cause
- Fix singolo motivato (vincolo #3)
- Costo fix stimato
- Blocker mystery shopper reale: SI/NO

### Verdict S175.0
- VERDE: 9/9 pass → S175 Path A LUCKY CARS mystery shopper unblocked
- GIALLO: 1-2 gap medi → fix dedicato prima Path A
- ROSSO: ≥3 gap o blocker hard → ripensare D-21 workflow

### Handoff conditional
- VERDE → `prompts/s176_mystery_shopper_path_a_lucky_cars.md`
- GIALLO → `prompts/s175_0_fix_<priority>.md`
- ROSSO → `prompts/s175_strategic_rethink.md`
```

---

## AUTOCRITICA STRUTTURALE PROMPT (vincolo #4)

1. **Assunzione nascosta**: presumo `pm2 start argos-dashboard` step 0.3 abbia ecosystem entry per dashboard. Se ecosystem.config.js NON include argos-dashboard, comando fallisce. Mitigation: prima `pm2 start` esegui `ssh imac "cat ~/Documents/app-antigravity-auto/ecosystem.config.js | grep -c argos-dashboard"`; se 0, dashboard va avviato standalone con `pm2 start /path/to/app.py --name argos-dashboard`.

2. **Cosa rompe a 30/60gg**: dashboard 8080 mai reso persistente cross-reboot via PM2 — possibile che S156 (pm2 startup launchd) abbia coperto solo wa-daemon+monitor. Mitigation: post-test S175.0, aggiornare `~/.pm2/dump.pm2` (`pm2 save`) per persistenza cross-reboot.

3. **Pattern errore noto**: ogni step Luke action richiede conferma esplicita "ricevuto" / "PDF aperto" / "form compilato" prima next step. Claude NON deve assumere completion da DB state alone (lezione S164 — DB row update può venire da admin API path bypass). Mitigation: ogni gate include double-check Luke phone + DB.

4. **Sovradimensiono**: 9 step in 1 sessione → context budget rischio sforo. Stima: step 0-3 ~25% context (verify + dialog), 4-6 ~25% (on_demand_runner output verbose + PDF analysis), 7-9 ~25%, gap report ~15%. Tot ~90% — sopra limite #7. Mitigation: split possibile S175.0 step 0-5 + S175.0-bis step 6-9 se context >55% post-step-5.

---

## VINCOLI ESECUZIONE NEXT SESSION

- **Luke fisico richiesto** — step 2, 3, 5 (visual UAT), 7, 8, 9 partial
- **NO simulation** — vincolo S164 retract: nessun admin API, nessun classifier stub, nessun mark-paid finto
- **Vincolo #1 verifica fattuale** — ogni claim "step X VERDE" richiede evidence (DB row, log line, screenshot phone, file size, HTTP code) — NON assumption
- **Vincolo #3 raccomandazione singola** — per ogni gap, 1 fix motivato, NO opzioni
- **Vincolo #9 no diplomazia** — se 0/9 pass, dichiarare reactive pipeline NON operativa
- **Vincolo #11 pattern recognition** — gap simile S159-S162 (dep) o S164 (mock) = root cause strutturale
- **Context budget** — `/context` post-step 3 e post-step 6. >55% post-5 = split S175.0-bis

---

## OUTPUT ATTESI

1. `data/s175_0_e2e_real_report.md` — 10-row table + gap list + verdict
2. Commit + push (Claude decide stato, no scope question Luke)
3. Prompt handoff:
   - VERDE → `prompts/s176_mystery_shopper_path_a_lucky_cars.md`
   - GIALLO → `prompts/s175_0_fix_*.md`
   - ROSSO → `prompts/s175_strategic_rethink.md`

## CHIUSURA S175.0

VERDE | GIALLO | ROSSO. Nessun PARTIAL/ARANCIONE (vincolo #6).
