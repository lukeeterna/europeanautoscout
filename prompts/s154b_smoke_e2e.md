# S154-bis — Smoke E2E TEST_FOUNDER (post S154a deploy verde)

**Sessione**: S154-bis (clean context start)
**Data**: 2026-05-04 — dopo S154a chiuso verde
**Scope**: validare end-to-end Worker LIVE con TEST_FOUNDER 393314928901 prima di Day 1 reale (S155)
**Tempo stimato**: ~1h-1h30 (rate-limit test 10 min + 8 step E2E 45 min + docs 15 min)

---

## 0. Pre-condizioni S154-bis — TUTTE devono essere ✅

| Pre-condizione | Verifica |
|----------------|----------|
| Worker LIVE | `curl -s https://argos-proxy.gianlucanewtech.workers.dev/health \| jq .status` → `"ok"` |
| ARGOS_PROXY_URL in .env | `grep ARGOS_PROXY_URL .env` → URL Workers |
| WA daemon connected | banner SessionStart `WA Daemon: connected` |
| iMac up | `ping -c 1 192.168.1.2` |
| CF Alert Monitor live | `ssh gianlucadistasi@192.168.1.2 "cat /tmp/argos-cf-monitor-heartbeat.txt"` → timestamp <10 min |
| TEST_FOUNDER in DB | dealer_id `DEALER_TEST_001` phone `393314928901` esiste |
| Telegram bot reachable | `curl -s "https://api.telegram.org/bot$(grep TELEGRAM_BOT_TOKEN .env \| cut -d= -f2-)/getMe" \| jq .ok` → `true` |

**Se UNA fallisce**: STOP, return a Luke. NO improvisation.

---

## 1. Stato S154a — cosa è già live

✅ Worker `argos-proxy` deployed: `https://argos-proxy.gianlucanewtech.workers.dev`
✅ R2 bucket `argos-contracts` created
✅ D1 `argos-contracts` migrated (UUID `75d63bc9-342f-46cf-b6d2-c0adf77c975e`)
✅ 8 secrets uploaded (ARGOS_ADMIN_SECRET, R2_SIGNING_SECRET, IBAN, INTESTATARIO, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WA_DAEMON_API_KEY, WA_DAEMON_URL)
✅ Rate-limit middleware deployed (per-IP 10/min sign, global 100, body 100KB)
✅ Health check 200
✅ CF Alert Monitor LIVE su iMac (3 alert R2 abilitati con email `ferretti.argosautomotive@gmail.com`)
✅ Backup codes Google in macOS Keychain

❌ Smoke E2E NON eseguito (questo sprint)

---

## 2. Phase Rate-Limit Test (~10 min, FAI PRIMA di smoke E2E)

```bash
URL=$(grep ^ARGOS_PROXY_URL= .env | cut -d= -f2-)
ADMIN=$(grep ^ARGOS_ADMIN_SECRET= .env | cut -d= -f2-)

# Crea 1 contract per avere token
RESP=$(curl -s -X POST "$URL/api/v1/contract/create" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"dealer_id":"RL_TEST","dealer_name":"RateLimit Test","dealer_phone":"393314928901","fee_cents":80000,"vehicle":{"make":"BMW","model":"X3","year":2022,"price_eu_cents":3410000}}')
echo "$RESP" | jq .
TOKEN=$(echo "$RESP" | jq -r .signature_token // .sign_url)  # check actual schema response

# Hammer 35 GET in <60s — atteso 5x 429 (limite 30/min per-IP)
echo "=== Hammer test ==="
for i in $(seq 1 35); do
  curl -s -o /dev/null -w "req $i: %{http_code}\n" "$URL/api/v1/contract/$TOKEN"
done | tail -10

# Expected: ultime ~5 richieste mostrano 429
# Verify Retry-After header present su 429
curl -sI "$URL/api/v1/contract/$TOKEN" | grep -i retry-after
```

**PASS criteria**: almeno 1 risposta 429 con header `Retry-After`. Body 100KB cap testato indirettamente (sign endpoint).

---

## 3. Phase Smoke E2E TEST_FOUNDER (~45 min)

Riferimento storico: `prompts/s153_e2e_sim_test_founder.md` sezione 3 (8 step). Esegui identico, sostituendo URL=$ARGOS_PROXY_URL e phone=393314928901.

**8 step da validare** (ordine sequenziale, STOP al primo fail):

1. **Health** `GET /health` → 200 (già OK in S154a, ripeti per consistency)
2. **Create contract** `POST /api/v1/contract/create` con admin Bearer + payload TEST_FOUNDER → 200 + token + sign_url
3. **Get public** `GET /api/v1/contract/:token` (anonymous) → 200 + ContractPublicDto + status DRAFT
4. **Sign** `POST /api/v1/contract/sign` con token + signer_name + font + consent → 200 + status SIGNED + pdf_download_url
5. **Verify R2** PDF in bucket `argos-contracts` con SHA256 hash in DB
6. **Send IBAN** `POST /api/v1/contract/:id/send-iban` admin → 200 + WA template delivered + DB iban_sent_at popolato
7. **Mark paid** `POST /api/v1/contract/:id/mark-paid` admin con bank+ref+amount → 200 + status PAID + payment_* fields
8. **Dashboard list** `GET /api/v1/admin/contracts` admin → 200 + array con il contract appena creato

**Verifiche collaterali** (parallel dopo step 4 e 7):
- Telegram: 4 alert ricevuti (CONTRACT_CREATED, SIGNED, IBAN_SENT, PAYMENT_RECEIVED)
- WA daemon iMac: 2 messaggi inviati a TEST_FOUNDER (IBAN_SEND, PAYMENT_RECEIVED templates)
- D1 audit_log: 4 row (CREATE, SIGN, SEND_IBAN, MARK_PAID) con timestamp + actor

---

## 4. Phase Documentation (~15 min)

- [ ] Aggiorna `.planning/E2E-SIM-RESULTS.md` con tutti gli 8 smoke step PASS/FAIL + screenshot Telegram + screenshot WA
- [ ] Aggiorna `HANDOFF.md` sezione S154-bis OUTCOME (verde/red)
- [ ] Aggiorna `MEMORY.md` con entry "S154-bis smoke E2E [VERDE/RED]"
- [ ] Crea `prompts/s155_day1_real_dealer.md` SOLO se tutti smoke verdi
- [ ] Commit finale: `feat(s154b): smoke E2E TEST_FOUNDER verde — Worker production-ready`

---

## 5. Vincoli S154-bis

- ✋ TEST_FOUNDER 393314928901 SOLO. Mai dealer reale.
- ✋ Se uno step fallisce: STOP, debug, NO continuare. Aggiorna BACKLOG con root cause.
- ✋ Se rate-limit test fallisce (no 429 dopo 35 req): STOP, il middleware è broken, fix prima.
- ✋ Day 1 reale (Stile Car) parte SOLO dopo S154-bis verde + OK Luke esplicito (sarà S155).

---

## 6. Out of scope S154-bis

- Apertura P.IVA (defer)
- Stripe / Fintecture / Revolut Business (rimossi da S151)
- Day 1 reale (S155)
- Custom domain Worker (M3+)
- Drift legacy↔current iMac (BACKLOG)
- Update wrangler 3 → 4 (BACKLOG, warning innocuo per ora)

---

## 7. Target di fine S154-bis

✅ Rate-limit 429 funzionante post 30+ req/min/IP con Retry-After header
✅ E2E TEST_FOUNDER: create→sign→awaiting→iban_sent→paid VERDE 8/8 step
✅ Dashboard contracts riceve correttamente list + actions
✅ WA daemon riceve template IBAN_SEND + PAYMENT_RECEIVED
✅ Telegram riceve 4 alert su tutte le state transition
✅ R2 contiene PDF firmato con SHA256 hashed
✅ D1 audit_log contiene 4 row
✅ `prompts/s155_day1_real_dealer.md` pronto per autorizzazione Luke

❌ NON in S154-bis: Day 1 reale, P.IVA, Stripe, custom domain
