# S154 — Resume R2 deploy + smoke E2E TEST_FOUNDER (post S153 partial)

**Sessione**: S154 (clean context start)
**Data**: TBD (dopo Luke completa Revolut card + R2 enable + 3 alert R2)
**Scope**: completare deploy argos-proxy (R2 bucket + D1 migration + secrets + wrangler deploy + rate-limit middleware) e smoke E2E TEST_FOUNDER
**Tempo stimato**: ~2-2.5h (rate-limit code 30 min + deploy 30 min + smoke E2E 1h + docs 15 min)

---

## 0. Pre-condizioni S154 — TUTTE devono essere ✅

Prima di iniziare, verifica con Luke che TUTTI questi siano fatti:

| Pre-condizione | Verifica |
|----------------|----------|
| Carta Revolut virtuale €5/mese su CF | `https://dash.cloudflare.com/.../billing/payment-methods` mostra carta |
| R2 attivato sull'account | `wrangler r2 bucket list` ritorna lista vuota `[]` (NO error 10042) |
| 3 alert R2 creati | dashboard CF Notifications mostra 3 entry attive (R2 Storage 8GB, Class A 800k, Class B 8M) — tutti con email `ferretti.argosautomotive@gmail.com` |
| Backup codes Google in posto sicuro | NON in `~/Downloads/` (è file Keychain Note bloccata o cassaforte fisica) |
| CF Alert Monitor PM2 online | `ssh iMac "pm2 list \| grep argos-cf-monitor"` → status `online` |
| WA daemon connected | banner SessionStart |

**Se UNA fallisce**: STOP, return a Luke. NO improvisation, NO deploy parziali.

---

## 1. Stato S153 partial — cosa è già fatto

✅ D1 `argos-contracts` creato — UUID `75d63bc9-342f-46cf-b6d2-c0adf77c975e` in `argos-proxy/wrangler.toml`
✅ CF Alert Monitor deployed su iMac PM2 — `argos-cf-monitor` online (vedi MEMORY 2026-05-02 19:55)
✅ Telegram delivery validato end-to-end (test message_id 6032)
✅ Token Telegram local↔iMac sync ricomposta
✅ App Password Gmail in `.env` come `GMAIL_FERRETTI_APP_PASSWORD`

❌ R2 bucket `argos-contracts` NON creato (bloccato da R2 disabled, ora unblock-ready)
❌ D1 migration `0001_init.sql` NON eseguita remote
❌ 7 secrets `wrangler secret put` NON eseguiti
❌ Rate-limit middleware Worker NON scritto
❌ `wrangler deploy` NON eseguito
❌ Smoke E2E TEST_FOUNDER NON eseguito

---

## 2. Phase Rate-limit middleware (~30 min, FAI PRIMA del deploy)

Decisione architettura: rate-limit per protezione costi R2 da abuse esterno.

**File da creare**: `argos-proxy/src/middleware/rate-limit.ts`

Specifiche:
- Approccio: in-memory Map con TTL (no Durable Objects, troppa overhead per scale ARGOS)
- 2 layer:
  1. **Per-IP** (estratto da `c.req.header('CF-Connecting-IP')`): max **10 req/min** su `/api/v1/contract/:token/sign`
  2. **Global** (counter unico): max **100 req/min** total su tutti gli endpoint pubblici (sign + get-by-token)
- Body size cap: max **100KB** su POST sign (header `Content-Length` check before body parse)
- Risposta 429: `{"ok":false,"error":"rate_limit_exceeded","retry_after":<sec>}`
- Bypass automatico per Bearer admin endpoints (no rate-limit su admin)
- TTL cleanup: ogni 60s purge entries scaduti per evitare memory leak

**Apply nel router** (`src/index.ts`):
```typescript
import { rateLimit } from './middleware/rate-limit';
app.post('/api/v1/contract/:token/sign', rateLimit({ perIp: 10, global: 100, maxBody: 102400 }), signHandler);
app.get('/api/v1/contract/:token', rateLimit({ perIp: 30, global: 200 }), getContractHandler);
```

**Test locale**: NO disponibile (wrangler dev non gira su macOS 11.6). Test in staging via curl post-deploy: invio 12 req in 60s, attendo 2x 429.

**Commit atomico**: `feat(s154): rate-limit middleware Worker — protezione costi R2`

---

## 3. Phase Deploy R2 + Migration + Secrets + Worker (~30 min)

Esegui in ordine, da `argos-proxy/`:

### 3.1 R2 bucket
```bash
cd argos-proxy
export CLOUDFLARE_API_TOKEN=$(grep ^CLOUDFLARE_API_TOKEN= ../.env | cut -d= -f2-)
export CLOUDFLARE_ACCOUNT_ID=$(grep ^CLOUDFLARE_ACCOUNT_ID= ../.env | cut -d= -f2-)
./node_modules/.bin/wrangler r2 bucket create argos-contracts
# Expected: "Created bucket 'argos-contracts'"
```

### 3.2 D1 migration remote
```bash
./node_modules/.bin/wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --remote
# Expected: "X queries executed" (X >= 6 per CREATE TABLE + indexes)
```

### 3.3 7 secrets
```bash
ADMIN_SECRET=$(openssl rand -hex 32)
SIGN_SECRET=$(openssl rand -hex 32)

# Save in .env first (idempotent: skip se già presenti)
grep -q '^ARGOS_ADMIN_SECRET=' ../.env || echo "ARGOS_ADMIN_SECRET=$ADMIN_SECRET" >> ../.env
grep -q '^R2_SIGNING_SECRET=' ../.env || echo "R2_SIGNING_SECRET=$SIGN_SECRET" >> ../.env

# Reload da .env (in caso siano già presenti da run precedente)
ADMIN_SECRET=$(grep ^ARGOS_ADMIN_SECRET= ../.env | cut -d= -f2-)
SIGN_SECRET=$(grep ^R2_SIGNING_SECRET= ../.env | cut -d= -f2-)

echo "$ADMIN_SECRET" | ./node_modules/.bin/wrangler secret put ARGOS_ADMIN_SECRET
echo "$SIGN_SECRET" | ./node_modules/.bin/wrangler secret put R2_SIGNING_SECRET
grep ARGOS_IBAN ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put ARGOS_IBAN
grep ARGOS_INTESTATARIO ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put ARGOS_INTESTATARIO
grep TELEGRAM_BOT_TOKEN ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put TELEGRAM_BOT_TOKEN
grep TELEGRAM_CHAT_ID ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put TELEGRAM_CHAT_ID
grep ARGOS_API_KEY ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put WA_DAEMON_API_KEY
echo "http://192.168.1.2:9191" | ./node_modules/.bin/wrangler secret put WA_DAEMON_URL
# RESEND_API_KEY: skip se Luke non ha account Resend (Worker degrada graceful)
```

### 3.4 Worker deploy
```bash
./node_modules/.bin/wrangler deploy
# → URL stampato, es: https://argos-proxy.<account>.workers.dev
echo "ARGOS_PROXY_URL=https://argos-proxy.<account>.workers.dev" >> ../.env
```

---

## 4. Phase Smoke E2E TEST_FOUNDER (~1h)

Vedi sezione 3 di `prompts/s153_e2e_sim_test_founder.md` (8 step da 3.1 health a 3.8 dashboard test). Esegui identico, sostituendo:
- `393314928901` ovunque chiede phone
- `URL=$(grep ARGOS_PROXY_URL ../.env | cut -d= -f2-)`

⚠️ **Nuovo step 3.0 prima dei smoke**: test rate-limit
```bash
ADMIN=$(grep ARGOS_ADMIN_SECRET ../.env | cut -d= -f2-)
# Crea 1 contract per avere token
TOKEN=$(curl -s -X POST "$URL/api/v1/contract/create" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"dealer_id":"RL_TEST","dealer_name":"RateLimit","dealer_phone":"393314928901","fee_cents":80000,"vehicle":{"make":"BMW","model":"X3","year":2022,"price_eu_cents":3410000}}' | jq -r .sign_url | sed 's|.*/contract/||')

# Hammer 12 GET in <60s — attesi 2x 429
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "req $i: %{http_code}\n" "$URL/api/v1/contract/$TOKEN"
done | tail -5
# Expected: ultime 2 richieste mostrano 429
```

---

## 5. Phase Documentation (~15 min)

- [ ] Aggiorna `.planning/E2E-SIM-RESULTS.md` con tutti i smoke step PASS/FAIL
- [ ] Aggiorna `HANDOFF.md` sezione S154 OUTCOME
- [ ] Aggiorna `MEMORY.md` con entry "S154 R2 deploy + smoke E2E VERDE"
- [ ] Crea `prompts/s155_day1_real_dealer.md` SOLO se tutti smoke verdi
- [ ] Commit finale: `feat(s154): R2 deploy + rate-limit + smoke E2E TEST_FOUNDER verde`

---

## 6. Vincoli S154 (ribaditi)

- ✋ TEST_FOUNDER 393314928901 SOLO. Mai dealer reale in S154.
- ✋ Rate-limit DEVE essere deployato PRIMA di Worker (è la difesa anti-abuse, non opzionale)
- ✋ Se uno dei 3 alert R2 NON ha email `ferretti.argosautomotive@gmail.com` → STOP, fallirebbe la catena alert→Telegram (visto che CF Alert Monitor è hard-coded a quella inbox)
- ✋ Day 1 reale (Stile Car) parte SOLO dopo S154 verde + OK Luke esplicito (sarà S155)

---

## 7. Out of scope S154

- Apertura P.IVA (defer)
- Stripe / Fintecture / Revolut Business (rimossi da S151)
- Day 1 reale (S155)
- Drift legacy↔current iMac directory (BACKLOG)
- Drift secrets local↔iMac unification (BACKLOG)
- Custom domain Worker (M3+)

---

## 8. Target di fine S154

✅ Rate-limit middleware deployato e testato
✅ argos-proxy deployed funzionante
✅ E2E TEST_FOUNDER: create→sign→awaiting→iban_sent→paid VERDE
✅ Dashboard contracts riceve correttamente list + actions
✅ WA daemon riceve template IBAN_SEND + PAYMENT_RECEIVED
✅ Telegram riceve alert su tutte le state transition
✅ R2 contiene PDF firmato con SHA256 hashed
✅ D1 audit_log contiene 4 row (CREATE, SIGN, SEND_IBAN, MARK_PAID)
✅ Rate-limit 429 funzionante post 10 req/min/IP
✅ `prompts/s155_day1_real_dealer.md` pronto

❌ NON in S154: Day 1 reale, P.IVA, Stripe
