# S177b — Classifier CONTRACT_REQUEST + handler + replay STEP 7-9

**Precondizioni S177a VERDE (commit `b345d05` pushato master)**:
- ✅ `wa-daemon.js` patch state transition `DOSSIER_SENT` post `/send-doc` (in-place iMac, backup `.s177a_bak`)
- ✅ TEST_FOUNDER `current_step=DOSSIER_SENT` (backfilled)
- ✅ daemon pm2 healthy pid 38788
- ✅ INBOUND `msg_1778946767736_b0a4v` preservato per replay
- ❌ Worker `/api/v1/contract/create` 401 INVALID_TOKEN (BLOCKER STEP 2, fix prima di tutto)
- ⚠️ HITL LLM_MULTI bypass NON risolto (S177c separato, per TEST_FOUNDER sandbox safe)

**Scope**: implementare classifier intent + handler + replay → primo deal E2E VERDE 9/9.
**Tempo stimato**: 75-120min. **Context preventivo richiesto**: start <30%.

## STEP 0 — Fix Worker auth (~20min, BLOCKER)

Cloudflare repo separato. Tentativo curl:
```bash
curl -X POST 'https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/create' \
  -H "X-API-Key: $ARGOS_API_KEY" \
  -d '{"dealer_id":"PROBE","vehicle_ref":"BMW_X1_2022","fee":800}'
# → {"error":"Unauthorized","code":"INVALID_TOKEN"}
```

**Path debug** (in ordine):
1. Trova repo Worker (probabile `~/Documents/argos-proxy/` o subdir `argos-automotive`)
2. Leggi `wrangler.toml` env binding nome variabile (es. `API_TOKEN` vs `ARGOS_API_KEY`)
3. Leggi `_worker.js` o `src/index.js` per auth header expected (X-API-Key vs Authorization Bearer)
4. Verifica `wrangler secret list` se token ruotato
5. Test con header corretto + token corretto

**Fallback se irriparabile in 30min**: hardcode contract creation lato Python su DB iMac (skip Worker), genera `sign_url` template `https://argos-automotive.pages.dev/sign?id={contract_id}` con contract_id UUID locale. Worker fix → S177c.

## STEP 1 — Classifier patch response-analyzer.py (~20min)

File: `/Users/gianlucadistasi/Documents/app-antigravity-auto/wa-intelligence/response-analyzer.py` (iMac, edit via SSH+Python heredoc come S177a).

Cerca routing main classifier (`reply_label =` assignments). Inserisci PRIMA del routing VEHICLE_REQUEST:

```python
CONTRACT_REQUEST_PATTERNS = [
    r'\b(mi\s+mandi|mandami|inviami|mandate?mi|spediscimi)\b.{0,30}\b(contratto|contract|firma|sign)\b',
    r'\b(ok|va\s+bene|perfetto|d\'accordo|certo)\b.{0,40}\b(contratto|procedo|proseguo|firmo|firma|mandi)\b',
    r'\b(facciamo|procediamo|facciamolo|chiudiamo)\b.{0,20}\b(contratto|deal|operazione)\b',
    r'^\s*(ok|si|sì|va\s+bene|d\'accordo|perfetto)\.?\s*$',  # conferma secca gated by state
]

def _matches_contract_request(text: str, current_step: str) -> bool:
    if current_step not in ('DOSSIER_SENT', 'DAY3_SENT'):
        return False
    t = (text or '').lower().strip()
    return any(re.search(p, t) for p in CONTRACT_REQUEST_PATTERNS)
```

Routing (priorità ALTA, prima VEHICLE_REQUEST):
```python
if _matches_contract_request(inbound_text, conv_row.get('current_step', '')):
    reply_label = 'CONTRACT_REQUEST'
    reply_payload = _handle_contract_request(dealer_id, conv_row)
    # ... continua con insert pending_replies approved=NULL (HITL D-07)
```

## STEP 2 — Handler `_handle_contract_request` (~25min)

**Template reply CRITICO**: NO "IBAN bonifico" hardcode (D-OPEN-Q2 violation). Default cash a consegna:
```python
reply_text = (
    f"perfetto. firmiamo qui: {sign_url}\n"
    f"appena firmato ci sentiamo per consegna e saldo. Luca"
)
# Variante se Luke vuole IBAN-opzionale: aggiungere logic dealer.has_partita_iva + chiedere
```

Handler skeleton:
```python
def _handle_contract_request(dealer_id: str, conv_row: dict) -> dict:
    import requests, os, uuid
    api_key = os.environ.get('ARGOS_API_KEY', '')
    worker_url = 'https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/create'
    vehicle_ref = _last_dossier_vehicle(dealer_id) or 'BMW_X1_2022'

    try:
        r = requests.post(worker_url, json={'dealer_id': dealer_id, 'vehicle_ref': vehicle_ref, 'fee': 800},
                          headers={'X-API-Key': api_key}, timeout=15)
        r.raise_for_status()
        data = r.json()
        sign_url, contract_id = data['sign_url'], data['contract_id']
        fallback = False
    except Exception as e:
        logger.error(f"contract create failed: {e}")
        # Fallback locale se Worker down
        contract_id = uuid.uuid4().hex[:16]
        sign_url = f"https://argos-automotive.pages.dev/sign?id={contract_id}"
        # INSERT contract DB locale (schema contracts su iMac DB)
        _insert_local_contract(contract_id, dealer_id, vehicle_ref, fee=800)
        fallback = True

    reply_text = (f"perfetto. firmiamo qui: {sign_url}\n"
                  f"appena firmato ci sentiamo per consegna e saldo. Luca")
    return {'reply_text': reply_text, 'sign_url': sign_url,
            'contract_id': contract_id, 'fallback': fallback}
```

## STEP 3 — Replay STEP 7 (~15min)

```bash
ssh imac "export PATH=\$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin; pm2 restart argos-wa-daemon && sleep 3"
ssh imac "cd ~/Documents/app-antigravity-auto && python3 -c \"
from wa_intelligence.response_analyzer import analyze_pending_inbounds
analyze_pending_inbounds(force_msg_id='msg_1778946767736_b0a4v')
\""
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, datetime(created_at,'localtime'), reply_label, approved, sent, substr(reply_text,1,200) FROM pending_replies WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 2;\""
```

**Gate VERDE STEP 7**: top row `reply_label='CONTRACT_REQUEST'`, `approved=NULL` (HITL), reply_text contiene URL `sign?id=`.

## STEP 4 — HITL approve + sign fisico Luke (~15min, fisico)

1. Dashboard `http://192.168.1.2:8080` → pending_replies → approve CONTRACT_REQUEST
2. SIM TEST_FOUNDER (`<TEST_FOUNDER_NUM>`) riceve link → apre, firma, submit
3. Verify `SELECT * FROM contracts WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 1;` → status evolve `DRAFT → AWAITING_DELIVERY`

## STEP 5 — Mark-paid (~5min, fisico)

Dashboard:8080 → contract → Mark PAID, ref `S177B-CONTRACT-INTENT-VERIFY-001`, amount 800.
Verify status=PAID + paid_at.

## Verdict S177b

- VERDE 5/5 → primo deal E2E reactive UFFICIALMENTE chiuso → trigger **S178 sanitizer D-32** (refactor Pillow-only) → **Day 1 reale Stile Car** dopo S178 VERDE
- GIALLO step parziale → S177b-bis su singolo step ROSSO
- ROSSO ≤2/5 → root cause analysis

## UX gotcha invariata
**MAI invertire direzione TEST_FOUNDER reactive**: SIM `<TEST_FOUNDER_NUM>` → ARGOS `3281536308` ✓. Inverso = daemon filtra auto-eco. S176-finalize ha perso 15min su questo.

## Findings da NON aprire (BACKLOG)
- HITL LLM_MULTI bypass (P4-bis) → S177c dedicato post-S177b
- D-32 sanitizer → S178 post-S177b
- D-31 dossier 12 sezioni → S179
- iMac repo divergent → P6 backlog

## Decisioni applicate
D-07 HITL, D-11 test pipeline TEST_FOUNDER, D-15 founder HITL 100%, D-21 workflow eBay-style, **D-OPEN-Q2 cash a consegna NO IBAN hardcode** (template reply chiave), D-OPEN-Q5 €800 fee in conversation.

## Output attesi S177b
1. `data/s177b_report.md`
2. Patch in-place iMac response-analyzer.py + backup `.s177b_bak`
3. Worker fix commit (repo Cloudflare separato) OR fallback locale documentato
4. Contract TEST_FOUNDER status=PAID
5. Memory entry close S177b 5/5
6. Handoff S178 sanitizer
