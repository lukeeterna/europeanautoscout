# S177 — Implementazione intent CONTRACT_REQUEST end-to-end + retry STEP 7-9

**Precondizione**: S176-finalize ROSSO 6/9 chiuso (vedi `data/s176_finalize_report.md` + memory `s176_finalize_red_contract_intent_missing.md`). INBOUND TEST_FOUNDER `"Va bene , mi mandi il contratto"` (msg_id `msg_1778946767736_b0a4v`, ingested 17:52:47 2026-05-16) preservato in DB. `reply_e9be3ac6` BLOCKED `approved=0`.

**Scope**: implementare intent `CONTRACT_REQUEST` in classifier AMBRA + handler che genera URL signature via Cloudflare Worker + state transition `DAY1_SENT → DOSSIER_SENT → CONTRACT_REQUESTED`. Retry STEP 7-9 reactive su TEST_FOUNDER → primo deal E2E VERDE 9/9.

**Tempo stimato**: 90-150min (regex+handler 30min, worker call wiring 30min, state transition 20min, replay+verify STEP 7 15min, STEP 8-9 fisici Luke 30min).

## UX GOTCHA — direzione TEST_FOUNDER reactive

**MAI invertire**:
- TEST_FOUNDER (dealer simulato): SIM `<TEST_FOUNDER_NUM>` → ARGOS Business `3281536308` ✓
- ARGOS → TEST_FOUNDER = OUTBOUND auto-eco filtrato dal daemon ✗

In S176-finalize Luke ha invertito 1 volta = 15min persi. Verifica direzione PRIMA di ogni "Luke ha inviato".

## Pre-flight (~3min)

```bash
# 1. Daemon + state
ssh imac "export PATH=\$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin; pm2 status | grep -E 'argos-wa-daemon|argos-cf-monitor|argos-dashboard'"

# 2. INBOUND preservato + reply blocked
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT datetime(created_at,'localtime'), direction, substr(body,1,80) FROM messages WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 3;\""
# Atteso: top row = 2026-05-16 17:52:47 INBOUND 'Va bene , mi mandi il contratto'

ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, reply_label, approved, sent FROM pending_replies WHERE id='reply_e9be3ac6';\""
# Atteso: reply_e9be3ac6|LLM_MULTI|0|0

# 3. Cloudflare Worker contract endpoint health
curl -s https://argos-automotive.pages.dev/sign?id=test 2>&1 | head -10
curl -s -X POST https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/create -H "Content-Type: application/json" -H "X-API-Key: $ARGOS_API_KEY" -d '{"dealer_id":"TEST_PROBE","vehicle_ref":"probe","fee":800}' 2>&1 | head -5
# Atteso: 200 con contract_id + sign_url. Se 404/500 → fix Worker prima di implementare classifier (Worker già operativo S164 ma verify)
```

## STEP 1 — Analyzer classifier patch (~30min)

File: `~/Documents/app-antigravity-auto/wa-intelligence/response-analyzer.py` (su iMac, modifica via SSH+sed o git+sync)

### 1a. Aggiungi pattern dict CONTRACT_REQUEST

Posizionare PRIMA del routing VEHICLE_REQUEST (priorità più alta), AFTER opt-out/STOP detection:

```python
CONTRACT_REQUEST_PATTERNS = [
    r'\b(mi mandi|mandami|inviami|mandate?mi|spediscimi).{0,30}(contratto|contract|firma|signature|sign)\b',
    r'\b(ok|va bene|perfetto|d\'accordo|certo)\b.{0,40}\b(contratto|procedo|proseguo|firmo|firma)\b',
    r'\b(facciamo|procediamo|facciamolo|chiudiamo)\b.{0,20}\b(contratto|deal|cosi|operazione)\b',
    r'^\s*(ok|si|sì|va bene|d\'accordo|perfetto)\.?\s*$',  # conferma secca POST dossier — gate su current_step
]

def _matches_contract_request(text: str, current_step: str) -> bool:
    """True solo se siamo in DOSSIER_SENT/DAY3_SENT E text matcha contract intent."""
    if current_step not in ('DOSSIER_SENT', 'DAY3_SENT'):
        return False
    t = (text or '').lower().strip()
    return any(re.search(p, t) for p in CONTRACT_REQUEST_PATTERNS)
```

### 1b. Routing — chiamare prima di VEHICLE_REQUEST

Nel main classifier function (cerca dove viene assegnato `reply_label`), inserire:

```python
# CONTRACT_REQUEST priority routing (gated by current_step)
if _matches_contract_request(inbound_text, conv_row['current_step']):
    reply_label = 'CONTRACT_REQUEST'
    reply_payload = _handle_contract_request(dealer_id, conv_row)
    # _handle_contract_request ritorna dict {reply_text, sign_url, contract_id}
    # crea pending_replies row con approved=NULL (HITL D-07)
    return reply_label, reply_payload
```

## STEP 2 — Handler contract creation (~30min)

```python
def _handle_contract_request(dealer_id: str, conv_row: dict) -> dict:
    """Crea contract row via Cloudflare Worker + ritorna reply con URL signature."""
    import requests, os
    api_key = os.environ.get('ARGOS_API_KEY')
    worker_url = 'https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/create'
    
    # Recupera vehicle_ref dal dossier inviato (query dossier_log o conversations.notes)
    vehicle_ref = _last_dossier_vehicle(dealer_id) or 'BMW_X1_2022'  # fallback
    
    try:
        r = requests.post(worker_url, json={
            'dealer_id': dealer_id,
            'vehicle_ref': vehicle_ref,
            'fee': 800,
        }, headers={'X-API-Key': api_key}, timeout=15)
        r.raise_for_status()
        data = r.json()  # {contract_id, sign_url, status}
    except Exception as e:
        logger.error(f"contract create failed: {e}")
        # Fallback: template safe senza URL
        return {
            'reply_text': "perfetto. le invio il link contratto a brevissimo, un attimo. Luca",
            'sign_url': None,
            'contract_id': None,
            'fallback': True,
        }
    
    sign_url = data['sign_url']
    reply_text = (
        f"perfetto. firmiamo qui: {sign_url}\n"
        f"appena firmato le mando IBAN per il bonifico di 800. Luca"
    )
    return {
        'reply_text': reply_text,
        'sign_url': sign_url,
        'contract_id': data['contract_id'],
        'fallback': False,
    }


def _last_dossier_vehicle(dealer_id: str) -> str | None:
    """Recupera vehicle_ref ultimo dossier inviato. Fonte: log daemon o tabella dossier_sent."""
    # Implementazione minima: parse filename PDF da daemon log o tabella dedicata
    # Per TEST_FOUNDER S177 replay: hardcoded "BMW_X1_2022" è OK
    ...
```

## STEP 3 — State transition `DOSSIER_SENT` (~20min)

Daemon `wa-daemon.js` callback post `/send-doc` deve aggiornare `conversations.current_step`:

```javascript
// In wa-daemon.js dopo successful sendMessage tipo doc:
if (msgType === 'doc' && contract.indexOf('.pdf') > -1) {
  db.prepare(`
    UPDATE conversations 
    SET current_step='DOSSIER_SENT', state_updated_at=datetime('now') 
    WHERE dealer_id=?
  `).run(dealerId);
  logger.info(`State→DOSSIER_SENT: ${dealerId}`);
}
```

Inoltre `_handle_contract_request` success → `UPDATE conversations SET current_step='CONTRACT_REQUESTED'`.

## STEP 4 — Replay STEP 7 su TEST_FOUNDER (~15min, no fisico)

```bash
# 1. Reset state per simulare DOSSIER_SENT (PDF S176 già inviato 16:17, current_step non aggiornato)
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"UPDATE conversations SET current_step='DOSSIER_SENT', state_updated_at=datetime('now') WHERE dealer_id='TEST_FOUNDER';\""

# 2. Restart daemon per caricare modifiche
ssh imac "export PATH=\$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin; pm2 restart argos-wa-daemon && sleep 3 && pm2 status | grep argos-wa-daemon"

# 3. Force re-analyze inbound preservato msg_1778946767736_b0a4v
# Tool: trigger analyzer su msg già esistente
ssh imac "cd ~/Documents/app-antigravity-auto && python3 -c \"
from wa_intelligence.response_analyzer import analyze_pending_inbounds
analyze_pending_inbounds(force_msg_id='msg_1778946767736_b0a4v')
\""

# 4. Verify nuova pending_replies row
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, datetime(created_at,'localtime'), reply_label, approved, sent, substr(reply_text,1,200) FROM pending_replies WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 2;\""
# Atteso: top row reply_label=CONTRACT_REQUEST, approved=NULL (HITL), reply_text contiene 'argos-automotive.pages.dev/sign?id='
```

**Gate verde STEP 7**: pending_replies top row con `reply_label='CONTRACT_REQUEST'` + reply_text contiene URL signature.

## STEP 5 — HITL approva + STEP 8 sign fisico (~15min Luke)

1. Luke apre dashboard `http://192.168.1.2:8080` → sezione pending_replies → trova `CONTRACT_REQUEST` → click "Approva e invia"
2. AMBRA spedisce reply con URL al telefono TEST_FOUNDER
3. Luke (dal telefono `<TEST_FOUNDER_NUM>`) apre link, compila form (nome test, firma touch, submit)
4. Verifica DB:
   ```bash
   ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, dealer_id, status, datetime(created_at,'localtime') FROM contracts WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 2;\""
   ```
   Atteso: nuovo contract row `status` evoluto `DRAFT → AWAITING_DELIVERY → IBAN_SENT`.

## STEP 6 — Mark-paid + delivery (~5min Luke)

1. Dashboard:8080 → contract TEST_FOUNDER → click "Mark as PAID" → `paid_amount=800`, `ref=S177-CONTRACT-INTENT-VERIFY-001`
2. Verify:
   ```bash
   ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, status, paid_amount, datetime(paid_at,'localtime'), ref FROM contracts WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 1;\""
   ```
   Atteso: `status=PAID, paid_amount=800.0`.

## Verdict S177

- **VERDE 9/9** (STEP 1-6 tutti pass) → primo deal E2E reactive UFFICIALMENTE chiuso. Trigger immediato: **S178 sanitizer refactor D-32** (ex S176-bis) → poi Day 1 reale Stile Car.
- **GIALLO 7-8/9** → patch mirato in S177-bis su step ROSSO singolo
- **ROSSO ≤6/9** → root cause analysis profondo (probabile bug Worker contract endpoint o classifier regex too strict/loose)

## Output attesi sessione S177

1. `data/s177_contract_intent_report.md` — esecuzione + verdict
2. Modifiche commit pushed su `response-analyzer.py` + `wa-daemon.js`
3. Contract TEST_FOUNDER in DB con `status=PAID`
4. Memory entry close S177 9/9 verde
5. Conditional handoff: **S178 sanitizer refactor D-32**

## Context budget S177

Pre-flight 3% + STEP 1-3 implementation 30% + STEP 4 replay 10% + STEP 5-6 verify 10% + report 7% = ~60%. **Sessione tight**, prepararsi a closure forzata se sfora 55% senza completare. Se context >55% prima di STEP 4 → split: chiudere implementation VERDE in S177a, replay+STEP 5-6 in S177b.

## Decisioni applicate

- **D-07** HITL strutturale primi 20 dealer reali (pending_replies approved=NULL per CONTRACT_REQUEST)
- **D-11** Test pipeline 5-step TEST_FOUNDER prima dealer reale
- **D-15** Founder HITL 100% primi 1-3 deal
- **D-21** Workflow info-broker → communication-broker-garante eBay-style (CONTRACT_REQUEST = step 5/8 workflow)
- **D-OPEN-Q2** P.IVA timing — pagamento cash a consegna €800-1.200
- **D-OPEN-Q5** Pricing €800 fee in conversation

## Findings da NON aprire in S177 (BACKLOG/handoff)

1. **D-32 sanitizer regression** — handoff S178 (post-S177 verde)
2. **D-31 dossier 12 sezioni** — handoff S179+
3. **D-30 foto venditore EU** — backlog conditional
4. **Bug substring `passat` in `passato`** — backlog S174 invariato
5. **iMac branch divergence** `main` HEAD vs `origin/master` — backlog

Sprint scope-lock S177 = classifier+handler+state transition+retry STEP 7-9. NESSUN refactor sanitizer in S177.
