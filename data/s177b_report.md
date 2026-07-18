# S177b — Report Classifier CONTRACT_REQUEST + handler + replay

**Data**: 2026-05-16 18:33 IT
**Commit chain**: `0476df6` → `20de638` → `c3c98a9` (master, pushed)
**Verdict**: VERDE 3/5 (STEP 0-3) + GATING fisico Luke (STEP 4-5)

## Esecuzione

### STEP 0 — Worker auth (~10min reale, 20min budget) — VERDE
**Finding strutturale**: Worker NON era broken. Il probe iniziale documentato in S176-finalize/S177a usava header sbagliato (`X-API-Key` invece di `Authorization: Bearer`) + body sbagliato (`vehicle_ref` invece di `dealer_name+dealer_phone+vehicle{}`). Probe corretto:
```bash
curl -X POST '<worker>/api/v1/contract/create' \
  -H "Authorization: Bearer $ARGOS_ADMIN_SECRET" \
  -H 'Content-Type: application/json' \
  -d '{"dealer_id":"X","dealer_name":"Y","dealer_phone":"+393...","fee_cents":80000,"vehicle":{...}}'
```
→ HTTP 201, contract creato. Auth Bearer + body completo = OK.

Conseguenza: piano S177b STEP 2 semplificato — riuso helper esistente `create_contract_for_interest()` (response-analyzer.py:121) invece di scrivere `_handle_contract_request` nuovo.

### STEP 1 — Classifier patch (~15min) — VERDE
File `wa-intelligence/response-analyzer.py`:
- Aggiunto `CONTRACT_REQUEST_PATTERNS` (4 regex) + `matches_contract_request(text, current_step)` con gating su `current_step in (DOSSIER_SENT, DAY3_SENT)`
- `classify_message()` accetta kwarg `current_step=''` (backward-compat); priority CONTRACT_REQUEST > MEDIA > POSITIVE/CURIOSITY
- Test offline: 14/14 cases passed (incluso 4 false-positive negative: stati sbagliati, brand mention senza confirm)

### STEP 2 — Handler nel main (~15min) — VERDE
Branch CONTRACT_REQUEST dopo `classification = classify_message(...)` (linea 1891):
- Chiama `create_contract_for_interest()` con confidence=0.92 (>= 0.85 threshold)
- Fallback vehicle: BMW X1 2020 €18000 (TODO post-S177b: lookup dossier_sent table)
- Normalizza dealer_phone: `39<TEST_FOUNDER_NUM>` → `+39<TEST_FOUNDER_NUM>` (Worker regex `^(\+39)?3\d{8,10}$`)
- Reply template **D-OPEN-Q2 cash a consegna NO IBAN hardcode**:
  ```
  perfetto. firmiamo qui: {sign_url}

  appena firmato ci sentiamo per consegna e saldo. Luca
  ```
- `save_pending_reply(approved=NULL)` (HITL D-07 strict)
- `send_telegram_hold(...)` per approve manuale
- `return` early (skip LLM flow, anti-spam bypass)

### STEP 3 — Replay TEST_FOUNDER (~20min, incluso debug) — VERDE
Esecuzione finale:
```
Classificazione: {'type': 'CONTRACT_REQUEST', 'confidence': 0.92, 'method': 'state_gated_pattern', 'matched': ['contract_request']}
[16/05/2026 18:33:38] CONTRACT_REQUEST — creo contratto via argos-proxy
[INFO] Telegram hold inviata
[16/05/2026 18:33:39] CONTRACT_REQUEST handled — reply_id=reply_f674d884 contract=52bc66c9feb4771d
```

DB verification:
```
reply_f674d884 | 2026-05-16 18:33:38 | CONTRACT_REQUEST | approved=NULL | sent=0
text: "perfetto. firmiamo qui: https://argos-automotive.pages.dev/contract/612b16944d82d75e639b92c060e74197
       appena firmato ci sentiamo per consegna e saldo. Luca"
contract_id=52bc66c9feb4771d, signature_token=612b16944d82d75e639b92c060e74197
```

**Issue intermedi risolti in STEP 3**:
1. iMac `.env` mancava `ARGOS_PROXY_URL` + `ARGOS_ADMIN_SECRET` → appended (chmod 600), backup `.env.s177b_bak`
2. Phone format `39<TEST_FOUNDER_NUM>` (12 digits no +) failed Worker regex → normalize handler
3. **Cloudflare WAF error 1010** (banned by browser signature) blocked default `Python-urllib/X.Y` UA → patched helper con `User-Agent: argos-analyzer/1.0` header

### STEP 4 — HITL approve + sign fisico — PENDING LUKE
Azione richiesta:
1. Apri dashboard `http://192.168.1.2:8080`
2. Sezione pending_replies → cerca `reply_f674d884` → review testo → click "Approva"
3. WA arriverà sul SIM TEST_FOUNDER (<TEST_FOUNDER_NUM>): aprire il link `https://argos-automotive.pages.dev/contract/612b16944d82d75e639b92c060e74197`
4. Firma + submit → status contract dovrebbe evolvere `DRAFT → AWAITING_DELIVERY`

### STEP 5 — Mark-paid fisico — PENDING LUKE
Dopo STEP 4: dashboard:8080 → contracts → `52bc66c9feb4771d` → Mark PAID, ref `S177B-CONTRACT-INTENT-VERIFY-001`, amount €800.

## Patch summary

Files modified:
- `wa-intelligence/response-analyzer.py` (+103 / -3 vs HEAD pre-S177b)
  - patterns + matcher: linee 226-249
  - classify_message signature + early-return: linee 1380-1389
  - handler branch: linee 1894-1952
  - urllib UA header: linea 207

iMac side:
- `wa-intelligence/.env` → appended `ARGOS_PROXY_URL` + `ARGOS_ADMIN_SECRET` (backup `.env.s177b_bak`)

Backup files:
- MacBook: `wa-intelligence/response-analyzer.py.s177b_bak` (pre-patch)
- iMac: `wa-intelligence/response-analyzer.py.s177b_bak` + `.env.s177b_bak`

## Decisioni applicate
- D-07 HITL strict (approved=NULL su pending_reply)
- D-11 test pipeline TEST_FOUNDER prima dealer reale
- D-15 founder HITL 100%
- D-21 workflow eBay-style (contract creation prima del template messaggio)
- **D-OPEN-Q2 cash a consegna**: reply template NO IBAN hardcode
- D-OPEN-Q5 €800 fee (in conversation, default Worker fee_cents=80000)

## Critica strutturale (vincolo #4)
1. **Assunzione vehicle BMW X1 hardcoded** — solo per scenario S177b TEST_FOUNDER. In produzione real dealer servirebbe lookup dossier_sent table (nessuna oggi). Rompe al primo deal reale con veicolo diverso. → BACKLOG HIGH.
2. **No retry su Worker 5xx** — helper esistente non retries. Se Worker giù → HOLD Telegram silenzioso, Luca deve diagnosticare manualmente. Per TEST_FOUNDER ok, per produzione serve retry+backoff.
3. **Pattern "ok" gating** — protetto da state DOSSIER_SENT ma dipende da S177a fix transition. Se daemon `/send-doc` regredisce (no state update), "ok" tornerebbe POSITIVE → AMBRA fallback "ti aggiorno 24-48h" loop. State machine va monitorata.
4. **WAF UA fix locale** — User-Agent `argos-analyzer/1.0` è solo per `create_contract_for_interest`. Altri endpoint argos-proxy chiamati da Python con default UA → stesso 1010. → BACKLOG: applicare UA globalmente a urllib.request in tutto response-analyzer.py.

## Findings parcheggiati (BACKLOG)
- Vehicle ref lookup dossier_sent (P1 HIGH, blocker primo deal reale post-test)
- Retry+backoff per Worker call (P2 MEDIUM)
- UA header globale per urllib (P2 MEDIUM)
- HITL LLM_MULTI bypass S177c (parcheggiato S177a, ancora aperto)
- D-32 sanitizer refactor Pillow-only S178 (DEFERRED a post-S177b)
- D-31 dossier 12 sezioni S179 (DEFERRED)
- iMac repo divergent (P6 backlog)

## Gating Day 1 reale Stile Car
**NON sbloccato** fino a STEP 4-5 VERDE + S178 sanitizer fix + S179 dossier struttura (vedi `feedback_e2e_full_test_founder_before_day1.md`).

Sequenza prossime sessioni: **S177b-finalize** (Luke sign+paid fisico) → **S178** (sanitizer D-32 Pillow refactor) → Day 1 reale.
