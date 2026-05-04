# S155-bis — Tailscale Funnel persistence + smoke E2E re-run

**Sessione**: S155-bis (clean context start)
**Data**: 2026-05-04 (post S155 PARTIAL)
**Scope**: ripristinare Tailscale Funnel persistence (bug status `{}`) → smoke E2E step 6+7 → autorizzare Day 1 reale (S156)
**Tempo stimato**: ~45min (reboot Tailscale.app 5min + funnel setup 5min + smoke E2E 20min + docs 10min + prompts/s156 5min)

---

## 0. Pre-condizioni S155-bis — TUTTE devono essere ✅

| Pre-condizione | Verifica |
|----------------|----------|
| Worker LIVE | `curl -s https://argos-proxy.gianlucanewtech.workers.dev/health \| python3 -c "import sys,json; print(json.load(sys.stdin).get('status'))"` → `ok` |
| iMac up | `ping -c 1 192.168.1.2` |
| WA daemon online | `ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"` → `wa_status: connected` |
| Tailscale logged in | `ssh gianlucadistasi@192.168.1.2 "/Applications/Tailscale.app/Contents/MacOS/Tailscale status"` → mostra `imac-di-gianluca` |
| Token API in `.env` | `grep TAILSCALE_API_TOKEN .env` → presente |
| Daily WA budget | `daily_remaining >= 5` |

---

## 1. Stato S155 PARTIAL — cosa è già configurato

✅ Tailnet `tail62c468.ts.net`, hostname `imac-di-gianluca`, account `ferretti.argosautomotive@gmail.com`
✅ ACL nodeAttrs funnel applicato (CapMap `funnel` + `funnel-ports?ports=443,8443,10000` propagati)
✅ HTTPS certs enabled tailnet-wide (`httpsEnabled: true` in `/tailnet/-/settings`)
✅ Cert Let's Encrypt provisioned per `imac-di-gianluca.tail62c468.ts.net`
✅ Token API `tskey-api-...` salvato in `.env` come `TAILSCALE_API_TOKEN` (90gg validity)

🐛 **Blocker S155-bis**: `tailscale funnel --bg 9191` set OK ma `funnel status` empty `{}`. DNS pubblico NXDOMAIN. State non persistito in system extension daemon macOS App.

---

## 2. Phase 1 — Reset Tailscale.app + re-set funnel (~10min)

### 2.1 Quit + relaunch Tailscale.app (Luke action richiesta)

Sull'iMac (via VNC/Screen Sharing o Luke fisico):
1. Click icona Tailscale menu bar → **Quit Tailscale**
2. Aspetta 5 secondi
3. Apri `/Applications/Tailscale.app` (doppio click in Finder)
4. Verifica icona menu bar torna verde + connected

**Conferma**: `ssh gianlucadistasi@192.168.1.2 "/Applications/Tailscale.app/Contents/MacOS/Tailscale status | head -3"` → `imac-di-gianluca` online

### 2.2 Re-set funnel + verifica persistence

```bash
ssh gianlucadistasi@192.168.1.2 'TS=/Applications/Tailscale.app/Contents/MacOS/Tailscale
# Reset eventuali config legacy
$TS funnel reset 2>&1
$TS serve reset 2>&1
sleep 2

# Set funnel
$TS funnel --bg 9191

# Verifica persistence (CRITICAL — se ancora `{}` empty, bug NON risolto)
sleep 2
echo "=== status check ==="
$TS funnel status
echo "=== JSON ==="
$TS funnel status --json'
```

**Verifiche obbligatorie**:
- `funnel status` mostra `https://imac-di-gianluca.tail62c468.ts.net/` → proxy `http://127.0.0.1:9191` ✅
- JSON non vuoto, contiene `AllowFunnel` + `TCP` o `Web` config ✅

### 2.3 Smoke external DNS + curl

```bash
# DNS pubblico
echo "=== DNS pubblico ==="
dig +short @1.1.1.1 imac-di-gianluca.tail62c468.ts.net
# ATTESO: ipv4 (Funnel ingress IP, NON 100.x.x.x interno)

# External curl
echo "=== external curl ==="
curl -s -m 15 https://imac-di-gianluca.tail62c468.ts.net/status
# ATTESO: JSON daemon con `wa_status: connected`
```

🛑 **Se 2.2 o 2.3 falliscono**: STOP, NON procedere. Aggiornare BACKLOG con root cause e aggiornare HANDOFF a S155-ter PARTIAL. Considerare alternative:
- Upgrade Tailscale 1.97+ via brew o homepage download
- Set funnel via GUI mode (tailscale serve via menu bar) invece di CLI
- Switch a `tailscaled` standalone (open-source) invece di Tailscale.app system extension

### 2.4 Persist funnel via launchd (post-fix)

Tailscale macOS app dovrebbe persistere funnel across reboot. Verifica con `pkill -KILL` test optional:

```bash
ssh gianlucadistasi@192.168.1.2 'TS=/Applications/Tailscale.app/Contents/MacOS/Tailscale; $TS funnel status'
# Atteso: persistente
```

---

## 3. Phase 2 — Update Worker secret (~5min)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise/argos-proxy
echo "https://imac-di-gianluca.tail62c468.ts.net" | npx wrangler secret put WA_DAEMON_URL

# Verifica
npx wrangler secret list | grep WA_DAEMON_URL
```

Worker rilegge il secret a ogni request (no redeploy necessario).

---

## 4. Phase 3 — Re-run smoke E2E step 6+7 (~20min)

### 4.1 Crea fresh contract + sign + send-iban

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
URL="https://argos-proxy.gianlucanewtech.workers.dev"
ADMIN=$(grep "^ARGOS_ADMIN_SECRET=" .env | cut -d= -f2- | tr -d '"')

# Create
RESP=$(curl -s -X POST "$URL/api/v1/contract/create" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"dealer_id":"DEALER_TEST_FOUNDER_S155b","dealer_name":"Test Founder S155b","dealer_phone":"+393314928901","dealer_email":"gianlucadistasi81@gmail.com","fee_cents":80000}')
ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['contract_id'])")
TOK=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['signature_token'])")

echo "contract_id=$ID"
echo "signature_token=$TOK"

# Sign
curl -s -X POST "$URL/api/v1/contract/sign" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOK\",\"signer_name\":\"Test Founder S155b\",\"signature_font\":\"great-vibes\",\"consent_fes\":true}"

# Send IBAN — CRITICAL TEST
curl -s -X POST "$URL/api/v1/contract/$ID/send-iban" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" -d '{}'
# ATTESO POST-FIX: wa_sent: TRUE
```

### 4.2 Verifiche delivery

```bash
# WA daemon log iMac (entry SEND a 393314928901)
ssh gianlucadistasi@192.168.1.2 'tail -30 /tmp/argos-wa-daemon.log 2>/dev/null | grep -E "send|393314928901"'

# WhatsApp Business app (Luke visual): conferma ricezione messaggio IBAN
```

### 4.3 Mark paid + verifica 2nd WA

```bash
curl -s -X POST "$URL/api/v1/contract/$ID/mark-paid" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"paid_amount_cents":80000,"payment_bank":"Revolut Test","payment_reference":"ARGOS-S155b"}'
# ATTESO: wa_sent: TRUE (PAYMENT_RECEIVED template)

# Luke visual: conferma 2nd WhatsApp message PAYMENT_RECEIVED
```

---

## 5. Phase 4 — Documentation + commit (~10min)

- [ ] Aggiorna `.planning/E2E-SIM-RESULTS.md` con sezione S155-bis (smoke 8/8 verde via Tailscale Funnel)
- [ ] Aggiorna `HANDOFF.md` STATO CORRENTE → S155-bis CHIUSO VERDE
- [ ] Aggiorna `MEMORY.md` con entry "S155-bis Tailscale Funnel deployed + smoke E2E 8/8 verde"
- [ ] Aggiorna `BACKLOG.md`: marca **CF Workers → LAN daemon unreachable** come **FIXED S155-bis via Tailscale Funnel** + marca **Tailscale Funnel `--bg` macOS bug** come **FIXED via reboot Tailscale.app** (con root cause documentato)
- [ ] Commit `feat(s155-bis): tailscale funnel persistente + WA delivery production-ready`

---

## 6. Phase 5 — Crea prompt S156 Day 1 reale (~5min)

SOLO se Phase 3 verde (wa_sent:true confermato + Luke visual app delivery):

- [ ] Crea `prompts/s156_day1_real_dealer.md`:
  - Target: Stile Car (dealer reale Day 1)
  - Phone: TBD da `dealer_network.sqlite`
  - Veicolo concreto Day 1: BMW X3 2022 da scegliere su CoVe DuckDB
  - Sequenza Day 1 + follow-up Day 3/7/14/21/30 (vedi `.claude/rules/communication.md`)
  - Vincoli: max 1 msg/giorno, MAI menzionare "Germania"/"import", linguaggio archetipo

---

## 7. Vincoli S155-bis

- ✋ Re-run smoke usa SOLO `+393314928901` (TEST_FOUNDER). NO dealer reale finché S156.
- ✋ Tailscale funnel persistence è critico: se Phase 1 fallisce, STOP, debug, NO procedere a Phase 2-3. Aggiornare BACKLOG con root cause.
- ✋ Daily WA limit: 15. Re-run consuma 2. Lasciare margine 10+ per Day 1 reale S156.

---

## 8. Out of scope S155-bis

- Day 1 reale (S156)
- Apertura P.IVA (defer)
- Stripe / Fintecture / Revolut Business (rimossi)
- Custom domain Worker proxy (M3+)

---

## 9. Target di fine S155-bis

✅ Tailscale Funnel persistente iMac, status non-empty, DNS pubblico risolve
✅ Worker secret `WA_DAEMON_URL` aggiornato a `https://imac-di-gianluca.tail62c468.ts.net`
✅ Smoke E2E 8/8 verde con `wa_sent: true` su step 6 + 7
✅ Luke conferma 2 WhatsApp message ricevuti su 393314928901 (IBAN_SEND + PAYMENT_RECEIVED)
✅ `prompts/s156_day1_real_dealer.md` pronto per autorizzazione Luke
✅ BACKLOG aggiornato: CF→LAN + Funnel bug entrambi marked FIXED

❌ NON in S155-bis: Day 1 reale, P.IVA, Stripe, custom domain Worker
