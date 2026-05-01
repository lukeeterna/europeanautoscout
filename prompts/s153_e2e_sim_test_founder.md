# S153 — E2E SIM TEST_FOUNDER (post S152b deploy unblock)

**Sessione**: S153 (clean context start)
**Data**: TBD (dopo unblock CF token + iMac online)
**Scope**: deploy argos-proxy + smoke test E2E completo su TEST_FOUNDER (393314928901)
**Tempo stimato**: ~2-2.5h (deploy 30min + smoke E2E 1h + analisi/fix 30min)

---

## 0. Pre-condizioni S153 — TUTTE devono essere ✅

| Pre-condizione | Verifica |
|----------------|----------|
| CF token scope D1+R2+Workers+Pages | `wrangler d1 list` deve ritornare lista (anche vuota) |
| iMac online | `ssh -o ConnectTimeout=3 gianlucadistasi@192.168.1.12 echo OK` |
| WA daemon iMac | `ssh gianlucadistasi@192.168.1.12 "curl -s localhost:9191/status"` → JSON connected |
| ARGOS_IBAN in `.env` | `grep ARGOS_IBAN .env` |
| ARGOS_INTESTATARIO in `.env` | `grep ARGOS_INTESTATARIO .env` |
| TEST_FOUNDER stato | `dealer_id` 393314928901 in PENDING/COLD su `dealer_network.sqlite` |

**Se UNA fallisce**: STOP, return a Luke, NO improvisation.

---

## 1. Letture obbligatorie (10 min)

1. `HANDOFF.md` sezione S152b OUTCOME
2. `.planning/E2E-SIM-RESULTS.md` (stato build + blocker deploy)
3. `prompts/s152b_chunk_b.md` Phase Deploy (lista 9 secrets + step ordinati)
4. `argos-proxy/wrangler.toml` (placeholder UUID da sostituire)
5. MEMORY.md entry "2026-05-01 21:55 — S152b CHIUSO"

---

## 2. Phase Deploy (~30 min)

### 2.1 Crea CF resources
```bash
cd argos-proxy
export $(grep -E "^(CLOUDFLARE_API_TOKEN|CLOUDFLARE_ACCOUNT_ID)=" ../.env | xargs)

# D1
./node_modules/.bin/wrangler d1 create argos-contracts
# → annota UUID, sostituisci 00000000-... in wrangler.toml

# R2
./node_modules/.bin/wrangler r2 bucket create argos-contracts

# Migration remote
./node_modules/.bin/wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --remote
# → conferma "X queries executed" (X >= 6 per CREATE TABLE + indexes)
```

### 2.2 Set 9 secrets
```bash
# Genera ARGOS_ADMIN_SECRET + R2_SIGNING_SECRET fresh
ADMIN_SECRET=$(openssl rand -hex 32)
SIGN_SECRET=$(openssl rand -hex 32)
echo "ARGOS_ADMIN_SECRET=$ADMIN_SECRET" >> ../.env       # save for dashboard config
echo "R2_SIGNING_SECRET=$SIGN_SECRET" >> ../.env

echo "$ADMIN_SECRET"           | ./node_modules/.bin/wrangler secret put ARGOS_ADMIN_SECRET
echo "$SIGN_SECRET"            | ./node_modules/.bin/wrangler secret put R2_SIGNING_SECRET
grep ARGOS_IBAN ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put ARGOS_IBAN
grep ARGOS_INTESTATARIO ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put ARGOS_INTESTATARIO
grep TELEGRAM_BOT_TOKEN ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put TELEGRAM_BOT_TOKEN
grep TELEGRAM_CHAT_ID ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put TELEGRAM_CHAT_ID
grep ARGOS_API_KEY ../.env | cut -d= -f2- | tr -d '"' | ./node_modules/.bin/wrangler secret put WA_DAEMON_API_KEY
echo "http://192.168.1.12:9191" | ./node_modules/.bin/wrangler secret put WA_DAEMON_URL

# RESEND_API_KEY: optional. If Luke ha account Resend, genera key e:
# echo "re_xxxxx" | wrangler secret put RESEND_API_KEY
# Se manca, Worker skippa email gracefully (vedere src/routes/contract-sign.ts:202).
```

### 2.3 Deploy + verify
```bash
./node_modules/.bin/wrangler deploy
# → URL stampato, es: https://argos-proxy.<account>.workers.dev
# Salva URL in ../.env come ARGOS_PROXY_URL=https://...
echo "ARGOS_PROXY_URL=https://argos-proxy.<account>.workers.dev" >> ../.env
```

### 2.4 Frontend deploy (CF Pages — se non già attivo)
Verificare che `https://argos-automotive.pages.dev/contract/` route funzioni con `_redirects`.

---

## 3. Phase Smoke (~1h)

### 3.1 Health check (no auth)
```bash
URL=$(grep ARGOS_PROXY_URL ../.env | cut -d= -f2-)
curl -s "$URL/health" | jq .
# Expected: {"status":"ok","service":"argos-proxy","version":"1.0.0",...}
```

### 3.2 Contract create (admin)
```bash
ADMIN=$(grep ARGOS_ADMIN_SECRET ../.env | cut -d= -f2-)
curl -s -X POST "$URL/api/v1/contract/create" \
  -H "Authorization: Bearer $ADMIN" \
  -H "Content-Type: application/json" \
  -d '{
    "dealer_id":"TEST_FOUNDER",
    "dealer_name":"Founder Test",
    "dealer_phone":"393314928901",
    "fee_cents":80000,
    "vehicle":{"make":"BMW","model":"X3 xDrive20d","year":2022,"price_eu_cents":3410000}
  }' | jq .
# Expected: {"ok":true,"contract_id":"<16hex>","sign_url":"https://argos-automotive.pages.dev/contract/<32hex>",...}
# Salva CONTRACT_ID e TOKEN
```

### 3.3 Contract get (public)
```bash
TOKEN=<dal step 3.2>
curl -s "$URL/api/v1/contract/$TOKEN" | jq .
# Expected: ContractPublicDto status=DRAFT, dealer_name, vehicle_*, fee_eur=800
```

### 3.4 Frontend render manual
- Apri `https://argos-automotive.pages.dev/contract/$TOKEN` in browser
- Verifica: 10 sig-card preview, checkbox FES, form firmatario
- Compila e submit
- Expected redirect: thank-you.html?id=<contract_id> + PDF in R2

### 3.5 Admin list
```bash
curl -s -H "Authorization: Bearer $ADMIN" "$URL/api/v1/admin/contracts?limit=10" | jq .
# Expected: {"ok":true,"count":1,"contracts":[{...status:"AWAITING_DELIVERY"}]}
```

### 3.6 Send IBAN
```bash
CID=<dal step 3.2>
curl -s -X POST "$URL/api/v1/contract/$CID/send-iban" \
  -H "Authorization: Bearer $ADMIN" -d '{}' | jq .
# Expected: {"ok":true,"status":"IBAN_SENT","wa_sent":true,"email_sent":<bool>}
# WhatsApp TEST_FOUNDER deve ricevere template IBAN_SEND con IBAN+intestatario+causale
# Telegram deve ricevere alert "📨 IBAN inviato"
```

### 3.7 Mark PAID
```bash
curl -s -X POST "$URL/api/v1/contract/$CID/mark-paid" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"paid_amount_cents":80000,"payment_bank":"MyTu","payment_reference":"ARGOS-TEST"}' | jq .
# Expected: {"ok":true,"status":"PAID","wa_sent":true}
# WhatsApp TEST_FOUNDER deve ricevere PAYMENT_RECEIVED
# Telegram alert "✅ PAGATO €800"
```

### 3.8 Dashboard test (manuale)
- Apri `http://localhost:8080/contracts`
- Verifica tabella mostra contratto TEST con badge PAID verde
- Tabella mostra correttamente importo + banca

---

## 4. Phase Documentation (~15 min)

- [ ] Aggiorna `.planning/E2E-SIM-RESULTS.md` con tutti gli step PASS/FAIL
- [ ] Aggiorna `HANDOFF.md` sezione S153 OUTCOME
- [ ] Aggiorna `MEMORY.md` con entry "S153 E2E sim TEST_FOUNDER VERDE"
- [ ] Crea `prompts/s154_day1_real_dealer.md` (Day 1 reale Stile Car) **SOLO** se tutti smoke verdi
- [ ] **Commit finale**: `chore(s153): E2E sim verde + handoff S154`

---

## 5. Vincoli S153 (ribaditi)

- ✋ TEST_FOUNDER 393314928901 SOLO. Mai dealer reale in S153.
- ✋ Se WA daemon offline durante smoke → STOP, return a Luke.
- ✋ Se step manuale 3.4 (browser sign) richiede modifiche frontend → BACKLOG, S153b.
- ✋ Se mark-paid o send-iban falliscono per bug → debug + commit fix + rerun smoke. NON skip.
- ✋ Day 1 reale (Stile Car) parte SOLO dopo smoke verde TUTTO + OK Luke esplicito.

---

## 6. Out of scope S153

- Apertura P.IVA (defer fino primo dealer reale pagante)
- Stripe / Fintecture / Revolut (rimossi da S151)
- Day 1 reale (è S154)
- Refactor frontend sign (è S155+ se needed)
- Custom domain Worker (M3+)
- Resend custom from domain (richiede DNS verification, M3+)

---

## 7. Target di fine S153

✅ argos-proxy deployed funzionante
✅ E2E TEST_FOUNDER: create→sign→awaiting→iban_sent→paid VERDE
✅ Dashboard contracts riceve correttamente list + actions
✅ WA daemon riceve template IBAN_SEND + PAYMENT_RECEIVED
✅ Telegram riceve alert su tutte le state transition
✅ R2 contiene PDF firmato con SHA256 hashed
✅ D1 audit_log contiene 4 row (CREATE, SIGN, SEND_IBAN, MARK_PAID)
✅ `prompts/s154_day1_real_dealer.md` pronto

❌ NON in S153: Day 1 reale, P.IVA, Stripe
