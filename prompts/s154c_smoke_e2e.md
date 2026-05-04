# S154-ter — Smoke E2E TEST_FOUNDER post phone-format fix

**Sessione**: S154-ter (clean context start)
**Data**: 2026-05-04 (post S154-bis partial)
**Scope**: fix phone format bug + smoke E2E TEST_FOUNDER 8 step + verifiche collaterali
**Tempo stimato**: ~1h-1h30 (fix+redeploy 15 min + Phase 1 finalize 10 min + smoke E2E 45 min + docs 15 min)

---

## 0. Pre-condizioni S154-ter — TUTTE devono essere ✅

| Pre-condizione | Verifica |
|----------------|----------|
| Worker LIVE | `curl -s https://argos-proxy.gianlucanewtech.workers.dev/health \| jq .status` → `"ok"` |
| ARGOS_PROXY_URL in .env | `grep ARGOS_PROXY_URL .env` → URL Workers |
| WA daemon connected | `ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status \| jq .wa_status"` → `"connected"` |
| iMac up | `ping -c 1 192.168.1.2` |
| CF Alert Monitor live | `ssh gianlucadistasi@192.168.1.2 "cat /tmp/argos-cf-monitor-heartbeat.txt"` → timestamp <10 min |
| Telegram bot reachable | `curl -s "https://api.telegram.org/bot$(grep TELEGRAM_BOT_TOKEN .env \| cut -d= -f2-)/getMe" \| jq .ok` → `true` |
| Daily WA budget OK | status response `daily_remaining >= 5` (ne servono 2 in smoke E2E + margine) |

---

## 1. Stato S154-bis partial — cosa è già confermato

✅ Worker LIVE: `https://argos-proxy.gianlucanewtech.workers.dev`
✅ R2 bucket `argos-contracts` created, D1 migrated, 8 secrets uploaded
✅ Rate-limit middleware deployed (verificato in Phase 1: 100 parallel = 42x 429 — funziona sotto burst)
✅ CF Alert Monitor LIVE iMac, backup codes Google in macOS Keychain

🐛 **Bug rilevato S154-bis (FIX in Phase 1 di questo sprint)**:
- Phone format mismatch: `contract-create.ts` regex `^(\+39)?3\d{8,10}$` vs `wa-daemon.ts` regex `^\d{11,13}$`. Intersezione vuota per TEST_FOUNDER `393314928901`.
- Soluzione minima: in `argos-proxy/src/lib/wa-daemon.ts:27`, normalizzare phone con `replace(/\D/g, '')` PRIMA del regex check, passare valore pulito a fetch body.

❌ Smoke E2E TEST_FOUNDER non eseguito (deferred per bug sopra)

---

## 2. Phase 1 — Fix phone format + redeploy (~15 min)

### 2.1 Fix `wa-daemon.ts`

```ts
// argos-proxy/src/lib/wa-daemon.ts
export async function sendWa(env, params) {
  if (!env.WA_DAEMON_URL) return { ok: false, error: 'WA_DAEMON_URL missing' };

  // FIX S154-ter: normalize phone (strip + and non-digits) before validation.
  // Necessary because contract-create accepts +39... format but daemon
  // requires bare digits. Daemon already strips internally, kept consistent.
  const cleanedPhone = (params.phone ?? '').replace(/\D/g, '');
  if (!/^\d{11,13}$/.test(cleanedPhone)) {
    return { ok: false, error: 'invalid phone format' };
  }
  if (!params.body || params.body.length === 0 || params.body.length > 4096) {
    return { ok: false, error: 'invalid body length' };
  }

  try {
    const res = await fetch(`${env.WA_DAEMON_URL}/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(env.WA_DAEMON_API_KEY ? { 'X-API-Key': env.WA_DAEMON_API_KEY } : {}),
      },
      body: JSON.stringify({ phone: cleanedPhone, message: params.body }),
    });
    // ... resto invariato
  }
}
```

### 2.2 Typecheck + redeploy

```bash
cd argos-proxy
npx tsc --noEmit               # type check
npx wrangler deploy            # redeploy
curl -s https://argos-proxy.gianlucanewtech.workers.dev/health | jq .timestamp   # verify fresh deploy
```

### 2.3 Commit fix

```bash
git add argos-proxy/src/lib/wa-daemon.ts BACKLOG.md
git commit -m "fix(s154c): normalize phone in wa-daemon.ts (strip non-digits before validation)

Resolves intersection-empty bug between contract-create regex (^(\\+39)?3\\d{8,10}\$)
and wa-daemon regex (^\\d{11,13}\$): TEST_FOUNDER 393314928901 had no string passing both.
Daemon iMac already strips internally — Worker now consistent."
```

---

## 3. Phase 1 finalize — Rate-limit Retry-After verify (~10 min)

```bash
URL=$(grep ^ARGOS_PROXY_URL= .env | cut -d= -f2-)
ADMIN=$(grep ^ARGOS_ADMIN_SECRET= .env | cut -d= -f2-)

# Crea contract dummy (RL_TEST già usato in S154-bis, ne basta uno nuovo)
RESP=$(curl -s -X POST "$URL/api/v1/contract/create" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"dealer_id":"RL_TEST_2","dealer_name":"RateLimit Test 2","dealer_phone":"+393314928901","fee_cents":80000}')
TOKEN=$(echo "$RESP" | jq -r .signature_token)

# Burst parallel per forzare same-isolate (dimostrato in S154-bis: 50+ concurrent)
seq 1 80 | xargs -P 40 -I{} curl -s -D /tmp/h_{}.txt -o /tmp/b_{}.txt \
  -w "%{http_code}\n" "$URL/api/v1/contract/$TOKEN" | sort | uniq -c

# Pesca un 429 e verifica header + body
for f in /tmp/h_*.txt; do
  code=$(head -1 "$f" | awk '{print $2}')
  if [ "$code" = "429" ]; then
    echo "=== Headers 429 ==="
    head -15 "$f"
    echo ""
    echo "=== Body 429 ==="
    cat "/tmp/b_$(basename "$f" .txt | sed 's/h_//').txt"
    break
  fi
done
rm -f /tmp/h_*.txt /tmp/b_*.txt
```

**PASS criteria**:
- ✅ Output mostra mix `200` + `429` (rate-limit triggered)
- ✅ Header 429 contiene `retry-after: <N>` (1-60)
- ✅ Body 429 contiene `{"ok":false,"error":"rate_limit_exceeded","scope":"ip","retry_after":N}`

Se 0x 429 con burst 80 parallel → bug regression, STOP, debug.

---

## 4. Phase 2 — Smoke E2E TEST_FOUNDER (~45 min)

**Phone test**: usa `+393314928901` (passa contract-create regex; wa-daemon.ts normalizzato lo strippa per daemon).

**8 step sequenziali (STOP al primo fail)**:

```bash
URL=$(grep ^ARGOS_PROXY_URL= .env | cut -d= -f2-)
ADMIN=$(grep ^ARGOS_ADMIN_SECRET= .env | cut -d= -f2-)

# 1. HEALTH
curl -s "$URL/health" | jq .

# 2. CREATE
RESP=$(curl -s -X POST "$URL/api/v1/contract/create" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"dealer_id":"DEALER_TEST_FOUNDER","dealer_name":"Test Founder","dealer_phone":"+393314928901","dealer_email":"gianlucadistasi81@gmail.com","fee_cents":80000,"vehicle":{"vin":"WBAJB7C57KB123456","make":"BMW","model":"X3","year":2022,"price_eu_cents":3410000}}')
echo "$RESP" | jq .
ID=$(echo "$RESP" | jq -r .contract_id)
TOKEN=$(echo "$RESP" | jq -r .signature_token)
echo "ID=$ID  TOKEN=$TOKEN"

# 3. GET PUBLIC (anonymous)
curl -s "$URL/api/v1/contract/$TOKEN" | jq .

# 4. SIGN (anonymous)
curl -s -X POST "$URL/api/v1/contract/sign" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOKEN\",\"signer_name\":\"Test Founder\",\"signature_font\":\"GreatVibes\",\"consent_fes\":true}" | jq .
# ATTESO: status=AWAITING_DELIVERY, pdf_sha256, post_sign_url

# 5. VERIFY R2 (admin only via wrangler)
cd argos-proxy && npx wrangler r2 object get "argos-contracts/contracts/$ID.pdf" --remote --file=/tmp/${ID}.pdf
ls -la /tmp/${ID}.pdf
shasum -a 256 /tmp/${ID}.pdf  # confronta con pdf_sha256 da step 4
cd ..

# 6. SEND IBAN (admin)
curl -s -X POST "$URL/api/v1/contract/$ID/send-iban" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" -d '{}' | jq .
# ATTESO: status=IBAN_SENT, wa_sent:true (post-fix S154-ter Phase 1)

# 7. MARK PAID (admin)
curl -s -X POST "$URL/api/v1/contract/$ID/mark-paid" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"paid_amount_cents":80000,"payment_bank":"Revolut Test","payment_reference":"ARGOS-'$ID'"}' | jq .
# ATTESO: status=PAID, wa_sent:true

# 8. ADMIN LIST
curl -s "$URL/api/v1/admin/contracts" -H "Authorization: Bearer $ADMIN" | jq '.[] | select(.id=="'$ID'")'
```

**PASS criteria per step**:
1. health 200
2. create 201, contract_id 16 hex, signature_token 32 hex, status DRAFT
3. get 200, ContractPublicDto, status DRAFT
4. sign 200, status AWAITING_DELIVERY, pdf_sha256 64 hex, post_sign_url
5. PDF in R2, SHA256 match
6. send-iban 200, status IBAN_SENT, wa_sent:true (post-fix), iban_sent_at
7. mark-paid 200, status PAID, payment_amount_cents=80000, wa_sent:true
8. admin list 200, contract presente con status=PAID

---

## 5. Phase 3 — Verifiche collaterali (~10 min, parallel a Phase 2)

### 5.1 Telegram alerts (4 attesi)

Su Telegram chat ARGOS verificare che siano arrivati 4 alert dopo gli step 4/6/7:
- 📝 Contratto FIRMATO (post step 4)
- 📨 IBAN inviato (post step 6, WA: ✅, Email: ✅ se RESEND_API_KEY)
- ✅ PAGATO €800 (post step 7)
- (3 attesi minimum, "CONTRACT_CREATED" Telegram NON inviato dal Worker — solo email Luca on sign)

### 5.2 WA template delivery (2 attesi)

```bash
ssh gianlucadistasi@192.168.1.2 "tail -50 /tmp/argos-wa-daemon.log | grep -E 'send|393314928901'"
```

Cerca 2 entry SEND a 393314928901 (IBAN_SEND template + PAYMENT_RECEIVED template).
Verifica anche su WhatsApp Business app (Luke) numero 393314928901: 2 messaggi ricevuti contenenti rispettivamente IBAN + ringraziamento.

### 5.3 D1 audit_log (4 row attese: CREATE, SIGN, SEND_IBAN, MARK_PAID)

```bash
cd argos-proxy && npx wrangler d1 execute argos-contracts --remote \
  --command="SELECT contract_id, action, actor, at FROM audit_log WHERE contract_id='$ID' ORDER BY at"
cd ..
```

Atteso: 4 row in ordine CREATE/SIGN/SEND_IBAN/MARK_PAID con timestamp ascendenti.

---

## 6. Phase 4 — Documentation + commit (~15 min)

- [ ] Aggiorna `.planning/E2E-SIM-RESULTS.md` con tabella 8 step PASS/FAIL + screenshot Telegram (3 alert) + screenshot WA (2 messaggi) + R2 SHA256 match + audit_log 4 row
- [ ] Aggiorna `HANDOFF.md` sezione S154-ter OUTCOME (verde/red)
- [ ] Aggiorna `MEMORY.md` con entry "S154-ter smoke E2E [VERDE/RED]"
- [ ] Crea `prompts/s155_day1_real_dealer.md` SOLO se tutti smoke verdi (target dealer reale Stile Car)
- [ ] Commit finale: `feat(s154c): smoke E2E TEST_FOUNDER verde — Worker production-ready`

---

## 7. Vincoli S154-ter

- ✋ Phone test: SOLO `+393314928901` (TEST_FOUNDER). Mai dealer reale finché S155 non autorizzato.
- ✋ Se uno step fallisce: STOP, debug, NO continuare. Aggiorna BACKLOG con root cause.
- ✋ Day 1 reale (Stile Car) parte SOLO dopo S154-ter verde + OK Luke esplicito (sarà S155).
- ✋ Daily WA limit: 15. Smoke E2E consuma 2. Lasciare margine 5+.

---

## 8. Out of scope S154-ter

- Apertura P.IVA (defer)
- Stripe / Fintecture / Revolut Business (rimossi da S151)
- Day 1 reale (S155)
- Custom domain Worker (M3+)
- Drift legacy↔current iMac (BACKLOG)
- Migrate rate-limit a Durable Objects (BACKLOG, scale dependent)

---

## 9. Target di fine S154-ter

✅ Phone format normalization fixed in wa-daemon.ts + redeploy
✅ Rate-limit 429 con `Retry-After` header verificato
✅ E2E TEST_FOUNDER: create→sign→awaiting→iban_sent→paid VERDE 8/8 step
✅ Dashboard contracts list mostra il contract con status=PAID
✅ WA daemon riceve template IBAN_SEND + PAYMENT_RECEIVED su 393314928901
✅ Telegram riceve 3 alert su tutte le state transition
✅ R2 contiene PDF firmato con SHA256 hashed
✅ D1 audit_log contiene 4 row (CREATE/SIGN/SEND_IBAN/MARK_PAID)
✅ `prompts/s155_day1_real_dealer.md` pronto per autorizzazione Luke

❌ NON in S154-ter: Day 1 reale, P.IVA, Stripe, custom domain
