# S152b — Chunk B: complete contract+payment Worker (post-S152a)

**Sessione**: S152b (clean context start)
**Data**: TBD (post-S152a chunk A completato 2026-05-01)
**Scope**: completare argos-proxy Worker (B-7..B-10) + deploy + smoke test
**Tempo stimato**: ~2.5-3h

---

## 0. Stato post-Chunk A (S152a) — già fatto

✅ **B-1 commit `1f0fbc4`** — Worker scaffold (Hono+TS, no Stripe), 19 file
- `argos-proxy/{package.json, tsconfig.json, wrangler.toml, .gitignore}`
- `src/{index.ts, lib/{types.ts, r2-signed-url.ts, resend.ts, telegram.ts, wa-daemon.ts}, middleware/admin-auth.ts, pdf/contract-template.ts, routes/*}`
- 68 npm packages installati, typecheck pulito

✅ **B-2 commit `d000933`** — D1 schema + R2 bucket bindings
- `migrations/0001_init.sql` con 7-state status enum + audit_log + 4 indexes
- `wrangler.toml` D1+R2 uncommented (database_id placeholder per local)
- SQL validato con sqlite3 standalone (workerd non gira su macOS 11.6)

✅ **B-3 bundled in B-1** — admin-auth + contract-create endpoint completi
- Bearer ARGOS_ADMIN_SECRET constant-time compare
- POST `/api/v1/contract/create`: validation + INSERT D1 status=DRAFT + audit_log

✅ **B-4 commit `24a858c`** — frontend sign 10 firme + FES consent
- `landing/_redirects`: `/contract/* → /contract/index.html` (200 rewrite)
- `landing/contract/index.html`: Tailwind CDN + 10 Google Fonts CDN preview
- `landing/contract/sign.js`: vanilla JS, fetch contract-get, build 10 cards, submit sign
- `landing/contract/thank-you.html`: post-sign con flow bonifico esplicito

✅ **B-5 commit `0510e44`** — PDF generation completo + 10 TTF embedded
- `assets/fonts/*.ttf` (10 file, 2.0 MB totali) da github.com/google/fonts
- `src/types-assets.d.ts`: `declare module '*.ttf' { ... ArrayBuffer }`
- `src/pdf/contract-template.ts`: 10 import statici + FONT_BUFFERS map + remove fallback
- 4 pagine PDF (header/parti, oggetto/veicolo/fee, clausole/FES, sottoscrizione/bundle)

✅ **B-6 bundled in B-4** — thank-you page già scritta

✅ **Pre-condizioni Chunk A → Chunk B (TUTTE SBLOCCATE 2026-05-01 20:50)**
- `ARGOS_IBAN` ricevuto (LT EMI bank code 32500, mod97 valido) → in `.env` locale (chmod 600), da `wrangler secret put` in deploy. **Valore non in repo.**
- `ARGOS_INTESTATARIO` confermato (Opzione A post-flag VoP CTO: "Luca Ferretti" resta solo persona commerciale su contratto/WA, intestatario reale del conto solo nel template IBAN_SEND con copertura narrativa "il bonifico va al titolare del conto"). **Valore non in repo.**
- Permission CF token: ✅ verificato attivo (`/user/tokens/verify` → status active)

---

## 1. Letture obbligatorie (10 min)

1. `.planning/E2E-SIM-PLAN.md` v2 §3 (TODO atomico) e §4 (test plan)
2. `prompts/s152_build_contract_payment.md` v2 (parent prompt)
3. `argos-proxy/src/index.ts` — vedere route map
4. `argos-proxy/src/routes/{send-iban.ts, mark-paid.ts}` — sono STUB 501, da implementare
5. MEMORY.md entry "2026-05-01 20:30 — S152a Chunk A COMPLETO" (questa sessione)

---

## 2. TODO atomico Chunk B

### Phase B-7: Send-IBAN endpoint (~30 min)

File: `argos-proxy/src/routes/send-iban.ts` (sostituire stub 501)

- [ ] POST `/api/v1/contract/:id/send-iban` (admin auth — già wired in `index.ts`)
- [ ] D1 SELECT contract WHERE id=:id (404 se manca)
- [ ] Validate `status === 'AWAITING_DELIVERY'` (409 altrimenti, errore include `current_status`)
- [ ] D1 UPDATE status='IBAN_SENT', iban_sent_at=now, iban_sent_iban=ARGOS_IBAN
- [ ] Audit log row: action='SEND_IBAN', actor='admin', details={iban_masked: last4}
- [ ] Build template `IBAN_SEND` (vedi templates.py B-9 per testo finale):
  ```
  Pronto per il bonifico {{dealer_name}}.

  IBAN: {{ARGOS_IBAN}}
  Intestatario: {{ARGOS_INTESTATARIO}}
  Importo: €{{fee}}
  Causale: ARGOS-{{contract_id}}

  Mi invii ricevuta quando fatto. Grazie.
  ```
- [ ] HTTP POST `WA_DAEMON_URL/send` via `lib/wa-daemon.ts:sendWa()` con `phone=row.dealer_phone, body=template`
- [ ] Resend email dealer (se `dealer_email`) con stessi dati IBAN (canale ridondante)
- [ ] Telegram alert "📨 IBAN inviato a {{dealer_name}} — attendere bonifico"
- [ ] Side effects = best-effort (non far fallire response su WA fail; loga warning)
- [ ] Return `{ok, status: 'IBAN_SENT', iban_sent_at, wa_sent: bool, email_sent: bool}`
- [ ] **Commit**: `feat(s152-b7): send-iban endpoint + WA template + email`

### Phase B-8: Mark-paid endpoint (~30 min)

File: `argos-proxy/src/routes/mark-paid.ts` (sostituire stub 501)

- [ ] POST `/api/v1/contract/:id/mark-paid` (admin auth)
- [ ] Body: `{paid_amount_cents: number, paid_at_iso?: string, payment_bank: string, payment_reference: string}`
- [ ] Validate paid_amount_cents >= row.fee_cents - 100 (tolleranza ±€1 arrotondamento)
- [ ] Validate status in ('IBAN_SENT', 'AWAITING_DELIVERY') — 409 altrimenti
- [ ] D1 UPDATE status='PAID', paid_at, payment_amount_cents, payment_bank, payment_reference
- [ ] Audit log: action='MARK_PAID', details={amount, bank, reference}
- [ ] Build template `PAYMENT_RECEIVED`:
  ```
  Bonifico ricevuto {{dealer_name}}, grazie. Operazione conclusa.

  A presto per il prossimo veicolo.
  ```
- [ ] HTTP POST WA daemon con phone=row.dealer_phone, body=template
- [ ] Resend email "Pagamento ricevuto" a Luca + dealer (se email)
- [ ] Telegram alert "✅ PAGATO €{{amount}} {{dealer_name}} — contratto chiuso"
- [ ] Return `{ok, status: 'PAID', paid_at}`
- [ ] **Commit**: `feat(s152-b8): mark-paid endpoint + reconciliation manuale`

### Phase B-9: Analyzer trigger + 3 templates (~30 min)

File: `wa-intelligence/response-analyzer.py` + `wa-intelligence/templates.py`

- [ ] Aggiungi 3 template a `templates.py` (locale + iMac via SCP a fine):
  - `DAY_INTEREST` — copia da §2.10 di `.planning/E2E-SIM-PLAN.md`
  - `IBAN_SEND` — copia identico a quello del Worker (consistenza messaggio)
  - `PAYMENT_RECEIVED`
- [ ] In `response-analyzer.py` aggiungi helper `create_contract_for_interest(intent, dealer_id, vehicle_data, conv_id)`:
  - Trigger SOLO su `INTEREST` con `confidence >= 0.85`
  - SOLO post Telegram HOLD approval (NON automatico)
  - HTTP POST `argos-proxy/api/v1/contract/create` con Bearer ARGOS_ADMIN_SECRET
  - Body: `{dealer_id, dealer_name, dealer_phone, dealer_email, vehicle, fee_cents, wa_conv_id}`
  - Return `{contract_id, sign_url}`
  - On success: invia template DAY_INTEREST via daemon WA con `{sign_url}`
- [ ] Sync `templates.py` su iMac via SCP (chiude divergenza S149b documentata)
- [ ] Test unitario: helper non chiama Worker se conf<0.85 o Telegram non approva
- [ ] **Commit**: `feat(s152-b9): analyzer trigger + 3 templates DAY_INTEREST/IBAN_SEND/PAYMENT_RECEIVED`

### Phase B-10: Dashboard admin (~1h, S152b/c se time)

File: `wa-intelligence/dashboard/app.py` + template HTML

- [ ] Route GET `/contracts` → fetch `argos-proxy/api/v1/admin/contracts?limit=50` (Bearer)
- [ ] Route POST `/contracts/<id>/send-iban` → proxy admin a Worker
- [ ] Route POST `/contracts/<id>/mark-paid` → form modal (amount, bank, reference) → proxy a Worker
- [ ] Template `templates/contracts.html`:
  - Tabella contratti (id, dealer, vehicle, fee, status, created_at)
  - Status badges colorati (DRAFT gray / SIGNED yellow / AWAITING blue / IBAN_SENT orange / PAID green)
  - Bottoni condizionali per status:
    - `AWAITING_DELIVERY` → "📨 Invia IBAN"
    - `IBAN_SENT` → "✅ Mark PAID" (modal con form)
- [ ] **Commit**: `feat(s152-b10): admin dashboard contracts + send-iban + mark-paid`

### Phase Deploy + Smoke Tests (~30 min)

**Pre-requisiti**: ✅ tutti sbloccati. ARGOS_IBAN + ARGOS_INTESTATARIO in `.env` locale (chmod 600), CF token verificato attivo.

- [ ] `cd argos-proxy && wrangler d1 create argos-contracts` → annota UUID
- [ ] Aggiorna `wrangler.toml` con UUID reale (replace `00000000-0000-0000-0000-000000000000`)
- [ ] `wrangler r2 bucket create argos-contracts`
- [ ] `wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --remote`
- [ ] Set 9 secrets via `wrangler secret put`:
  - `RESEND_API_KEY`
  - `ARGOS_ADMIN_SECRET` (`openssl rand -hex 32`)
  - `R2_SIGNING_SECRET` (`openssl rand -hex 32`)
  - `TELEGRAM_BOT_TOKEN` (riusa esistente da `.env`)
  - `TELEGRAM_CHAT_ID` (riusa esistente)
  - `ARGOS_IBAN` ✅ sbloccato — in `.env` locale (`grep ARGOS_IBAN .env | cut -d= -f2- | wrangler secret put ARGOS_IBAN`)
  - `ARGOS_INTESTATARIO` ✅ sbloccato — in `.env` locale (`grep ARGOS_INTESTATARIO .env | cut -d= -f2- | wrangler secret put ARGOS_INTESTATARIO`)
  - `WA_DAEMON_URL` (`http://192.168.1.2:9191` — testing LAN; production via Tailscale)
  - `WA_DAEMON_API_KEY` (verificare/generare per `.claude/rules/security.md` compliance)
- [ ] `wrangler deploy` → URL `argos-proxy.<account>.workers.dev`
- [ ] Smoke tests via curl (in ordine):
  - [ ] GET `/health` → 200 status:ok
  - [ ] POST `/api/v1/contract/create` (Bearer admin) con body fittizio TEST_FOUNDER → 201 + token
  - [ ] GET `/api/v1/contract/:token` → 200 ContractPublicDto status=DRAFT
  - [ ] open `https://argos-automotive.pages.dev/contract/:token` in browser → render OK + 10 firme + checkbox FES
  - [ ] (manual) compila form, submit → POST `/api/v1/contract/sign` → 200 + status=AWAITING_DELIVERY + PDF in R2
  - [ ] GET `/api/v1/admin/contracts` (Bearer) → 200 con il contratto creato
  - [ ] POST `/api/v1/contract/:id/send-iban` (Bearer) → 200 + WA daemon ricevuto + IBAN_SENT
  - [ ] POST `/api/v1/contract/:id/mark-paid` (Bearer) → 200 + status=PAID + Telegram + WA
- [ ] Crea `.planning/E2E-SIM-RESULTS.md` (NUOVO) con time + pass/fail + bug log
- [ ] **Commit**: `chore(s152): deploy argos-proxy v2 + smoke tests`

### Phase Handoff S153

- [ ] Crea `prompts/s153_e2e_sim_test_founder.md` (copia template + parametri reset TEST_FOUNDER)
- [ ] Aggiorna `HANDOFF.md` sezione S152 OUTCOME completo
- [ ] Aggiorna MEMORY.md con entry "S152 BUILD COMPLETO"
- [ ] **Commit**: `docs(S152): handoff S153 + memory update`

---

## 3. Vincoli S152b (post-S151 pivot ribaditi)

- ✋ **NESSUN secret in commit** — tutti via `wrangler secret put` (incluso ARGOS_IBAN)
- ✋ **NO Stripe / Fintecture / Revolut** — solo bonifico bancario manuale (ribadito)
- ✋ **NO P.IVA** — defer fino a primo dealer reale pagante
- ✋ **NO Day 1 reale** — SOLO TEST_FOUNDER (393314928901), è S153
- ✋ **NO modifiche a `cove_engine_v4.py`** o daemon WA esistente
- ✋ Se context >75% prima di B-9 → STOP, S152c clean restart per dashboard
- ✋ Test smoke su TEST_FOUNDER, NON dealer reali
- ✋ FES bundle evidence sempre in audit_log per ogni firma
- ✋ HMAC R2 signed URL TTL massimo 7gg

---

## 4. Scope creep da rifiutare (ripeto)

- Apertura P.IVA (rimossa da S151)
- Stripe / Fintecture / Revolut / GoCardless (tutti rimossi da S151)
- Custom domain Worker o Pages
- Acquisto dominio per Resend custom from
- Logo ARGOS finale embedded in PDF (placeholder OK fino S153)
- SPID Sign / FEQ (FES + bundle è proporzionata €800)
- Dashboard analytics/grafici (solo CRUD essenziale)
- OpenBanking automation (è M3+, non ora)
- Refactor cove_engine_v4.py
- Test reali dealer reali (S153/S154)

---

## 5. Target di fine S152b

✅ Worker `argos-proxy` deployed + 8 endpoint live (health, contract-get, contract-sign, contract-create, send-iban, mark-paid, admin/contracts + 404)
✅ D1 `argos-contracts` schema applicato remote + R2 bucket pronto
✅ Dashboard admin funzionante con send-iban + mark-paid
✅ Trigger ARGOS analyzer integrato (DAY_INTEREST con sign_url)
✅ Smoke test verde end-to-end su TEST_FOUNDER
✅ `prompts/s153_e2e_sim_test_founder.md` pronto

❌ NON in S152b: E2E sim completo TEST_FOUNDER (è S153)
❌ NON in S152b: Day 1 reale (è S154)

---

## 6. Decisione CTO ereditata

S151 plan v2 + S152a chunk A → S152b chunk B esecutivo.

NO discussioni architetturali in S152b (decise in S151). Solo execute + commit + smoke test.

Pivot consolidato: **bonifico bancario manuale**, riconciliazione 5sec/contratto via dashboard admin. Quando volume >50 contratti/mese (M3+) si valuta automation Fintecture/SDD.

Se durante S152b emergono ambiguità:
- Piccola → decisione CTO + log in `E2E-SIM-RESULTS.md`
- Grande → STOP, ritorna a Luke per chiarimento, no improvisation

**Onestà fiscale ribadita**: Luke informato CRS Lituania-Italia. Decisione operativa = sua. Mio compito CTO = build clean, scalabile, reversibile.
