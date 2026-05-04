# S155 — Cloudflare Tunnel daemon WA + smoke E2E re-run

**Sessione**: S155 (clean context start)
**Data**: 2026-05-04 (post S154-ter PARTIAL)
**Scope**: setup `cloudflared tunnel` su iMac → re-run smoke E2E step 6+7 → verificare WA delivery → autorizzare Day 1 reale (S156)
**Tempo stimato**: ~1h-1h30 (tunnel setup 30 min + secret update 5 min + smoke re-run 20 min + docs 15 min + prompts/s156 15 min)

---

## 0. Pre-condizioni S155 — TUTTE devono essere ✅

| Pre-condizione | Verifica |
|----------------|----------|
| Worker LIVE | `curl -s https://argos-proxy.gianlucanewtech.workers.dev/health \| jq .status` → `"ok"` |
| iMac up | `ping -c 1 192.168.1.2` |
| WA daemon online | `ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status \| jq .wa_status"` → `"connected"` |
| `cloudflared` installato iMac | `ssh gianlucadistasi@192.168.1.2 "which cloudflared"` (se manca: `brew install cloudflared`) |
| CF account ID + zone | `grep CLOUDFLARE_ACCOUNT_ID .env` |
| Daily WA budget OK | `daily_remaining >= 5` (ne servono 2 per re-run + margine) |

---

## 1. Stato S154-ter PARTIAL — cosa è già confermato

✅ Phone-format fix `wa-daemon.ts` deployed (commit `ab938c4`, version `70958730-...`)
✅ Rate-limit middleware production-ready (75/150 = 429 sotto burst, retry-after header)
✅ Smoke E2E 6/8 step verde: HEALTH/CREATE/GET/SIGN/R2/ADMIN-LIST
✅ D1 audit_log integro (4/4 row CREATE/SIGN/SEND_IBAN/MARK_PAID)

🐛 **Blocker S155**: CF Workers → LAN daemon unreachable. `WA_DAEMON_URL=http://192.168.1.2:9191` (RFC1918) bloccato da CF gateway con error 1003. Soluzione: CF Tunnel.

---

## 2. Phase 1 — Setup `cloudflared tunnel` (~30 min)

### 2.1 Auth + create tunnel

```bash
# Su iMac (SSH)
ssh gianlucadistasi@192.168.1.2 << 'EOF'
cloudflared tunnel login          # browser opens, auth con CF account
cloudflared tunnel create argos-wa-daemon
# Output: Tunnel ID (UUID) + credentials file ~/.cloudflared/<UUID>.json
EOF
```

### 2.2 Config tunnel

```bash
ssh gianlucadistasi@192.168.1.2 'cat > ~/.cloudflared/config.yml << EOF
tunnel: <UUID-from-step-2.1>
credentials-file: /Users/gianlucadistasi/.cloudflared/<UUID>.json

ingress:
  - hostname: wa-daemon.gianlucanewtech.com
    service: http://localhost:9191
  - service: http_status:404
EOF'
```

### 2.3 DNS route

```bash
ssh gianlucadistasi@192.168.1.2 "cloudflared tunnel route dns argos-wa-daemon wa-daemon.gianlucanewtech.com"
```

### 2.4 Run tunnel via PM2 (persistente)

```bash
ssh gianlucadistasi@192.168.1.2 << 'EOF'
cd ~/Documents/app-antigravity-auto/wa-intelligence
# Aggiungi app a ecosystem.config.js (o crea nuovo file pm2 dedicato)
pm2 start cloudflared --name argos-cf-tunnel -- tunnel run argos-wa-daemon
pm2 save
EOF
```

### 2.5 Smoke test tunnel

```bash
# Da MacBook (LAN diversa o tetherata su 4G per simulare external)
curl -s https://wa-daemon.gianlucanewtech.com/status | jq .
# Atteso: same response del LAN endpoint
```

---

## 3. Phase 2 — Update secret Worker (~5 min)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise/argos-proxy
set -a && source ../.env && set +a
echo "https://wa-daemon.gianlucanewtech.com" | npx wrangler secret put WA_DAEMON_URL
# Verifica:
npx wrangler secret list | grep WA_DAEMON_URL
```

Il Worker rilegge il secret a ogni request (no redeploy necessario).

---

## 4. Phase 3 — Re-run smoke E2E step 6+7 (~20 min)

### 4.1 Crea fresh contract + sign + send-iban

```bash
URL="https://argos-proxy.gianlucanewtech.workers.dev"
ADMIN=$(grep "^ARGOS_ADMIN_SECRET=" .env | cut -d= -f2-)

# Create
RESP=$(curl -s -X POST "$URL/api/v1/contract/create" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"dealer_id":"DEALER_TEST_FOUNDER_S155","dealer_name":"Test Founder S155","dealer_phone":"+393314928901","dealer_email":"gianlucadistasi81@gmail.com","fee_cents":80000}')
ID=$(echo "$RESP" | jq -r .contract_id)
TOK=$(echo "$RESP" | jq -r .signature_token)

# Sign
curl -s -X POST "$URL/api/v1/contract/sign" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOK\",\"signer_name\":\"Test Founder S155\",\"signature_font\":\"great-vibes\",\"consent_fes\":true}" | jq .

# Send IBAN — questo è il test critico
curl -s -X POST "$URL/api/v1/contract/$ID/send-iban" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" -d '{}' | jq .
# ATTESO POST-FIX: wa_sent: TRUE
```

### 4.2 Verifiche delivery

```bash
# WA daemon log iMac
ssh gianlucadistasi@192.168.1.2 "tail -30 /tmp/argos-wa-daemon.log | grep -E 'send|393314928901'"
# ATTESO: 1 entry SEND a 393314928901 con body IBAN

# WhatsApp Business app (Luke visual): conferma ricezione messaggio IBAN
```

### 4.3 Mark paid + verifica 2nd WA

```bash
curl -s -X POST "$URL/api/v1/contract/$ID/mark-paid" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"paid_amount_cents":80000,"payment_bank":"Revolut Test","payment_reference":"ARGOS-S155"}' | jq .
# ATTESO: wa_sent: TRUE (PAYMENT_RECEIVED template)

# Luke visual: conferma 2nd WhatsApp message PAYMENT_RECEIVED
```

---

## 5. Phase 4 — Documentation + commit (~15 min)

- [ ] Aggiorna `.planning/E2E-SIM-RESULTS.md` con sezione S155 (tunnel deploy + smoke 8/8 verde)
- [ ] Aggiorna `HANDOFF.md` STATO CORRENTE → S155 CHIUSO VERDE
- [ ] Aggiorna `MEMORY.md` con entry "S155 CF Tunnel deployed + smoke E2E 8/8 verde"
- [ ] Aggiorna `BACKLOG.md`: marca "CF Workers → LAN daemon unreachable" come **FIXED S155 via Cloudflare Tunnel**
- [ ] Commit `feat(s155): cloudflared tunnel + WA delivery production-ready`

---

## 6. Phase 5 — Crea prompt S156 Day 1 reale (~15 min)

SOLO se Phase 3 verde (wa_sent:true confermato + Luke visual app delivery):

- [ ] Crea `prompts/s156_day1_real_dealer.md`:
  - Target: Stile Car (dealer reale Day 1)
  - Phone: TBD da `dealer_network.sqlite`
  - Veicolo concreto Day 1: BMW X3 2022 da scegliere su CoVe DuckDB
  - Sequenza Day 1 + follow-up Day 3/7/14/21/30 (vedi `.claude/rules/communication.md`)
  - Vincoli: max 1 msg/giorno, MAI menzionare "Germania"/"import", linguaggio archetipo (NARCISO/BARONE/...)

---

## 7. Vincoli S155

- ✋ Re-run smoke usa SOLO `+393314928901` (TEST_FOUNDER). NO dealer reale finché S156.
- ✋ Tunnel è critico: se setup fallisce, STOP, debug, NO procedere a Phase 4. Aggiornare BACKLOG con root cause.
- ✋ JWT/auth tunnel: usare `cloudflared` access policy "Service Token" se Luke vuole estra protezione su `wa-daemon.*` URL public. Altrimenti `WA_DAEMON_API_KEY` X-API-Key check già presente è sufficiente.
- ✋ Daily WA limit: 15. Re-run consuma 2. Lasciare margine 10+ per Day 1 reale S156.

---

## 8. Out of scope S155

- Day 1 reale (S156)
- Apertura P.IVA (defer)
- Stripe / Fintecture / Revolut Business (rimossi)
- Custom domain Worker proxy (M3+)
- Drift legacy↔current iMac (BACKLOG)
- Migrate rate-limit a Durable Objects (BACKLOG)

---

## 9. Target di fine S155

✅ `cloudflared tunnel argos-wa-daemon` LIVE iMac, persistente via PM2
✅ Public URL `https://wa-daemon.gianlucanewtech.com` raggiungibile da Worker
✅ Worker secret `WA_DAEMON_URL` aggiornato
✅ Smoke E2E 8/8 verde con `wa_sent: true` su step 6 + 7
✅ Luke conferma 2 WhatsApp message ricevuti su 393314928901 (IBAN_SEND + PAYMENT_RECEIVED)
✅ `prompts/s156_day1_real_dealer.md` pronto per autorizzazione Luke
✅ BACKLOG aggiornato: blocker CF→LAN marked FIXED

❌ NON in S155: Day 1 reale, P.IVA, Stripe, custom domain Worker
