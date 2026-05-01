# S152 — BUILD argos-proxy Worker + Contract Sign + Bonifico Manuale (v2 post-pivot)

**Sessione**: S152 (clean context start, post-S151 plan v2 approvato)
**Data**: TBD (post-GO Luke S151 v2)
**Scope**: implementare componenti NUOVI Step 4 (contract+firma) e Step 5 (bonifico bancario manuale) della pipeline E2E sim
**Tempo stimato**: 3-4h (Phase B-1 → B-9, ridotto da 5-6h post-pivot no-Stripe)

---

## 0. Pre-requisiti (verificare prima di avviare)

- [x] Luke ha approvato `.planning/E2E-SIM-PLAN.md` v2 (5 punti operativi)
- [x] Bonifico bancario manuale come modello pagamento confermato (no Stripe S152)
- [x] Cloudflare token ARGOS attivo (`CLOUDFLARE_API_TOKEN` in `.env`, account `22ddff3a4ef544511523a841b3dcadf8`)
- [ ] Verificare permission D1 + R2 sul token (a inizio S152)
- [ ] iMac UP + daemon WA online (`ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"`)
- [ ] IBAN MyTu o evolu confermato da Luke per `ARGOS_IBAN` env var (mai in commit)

---

## 1. Letture obbligatorie (10 min)

1. `.planning/E2E-SIM-PLAN.md` v2 — plan completo (architettura + decisioni + TODO)
2. `/Volumes/MontereyT7/FLUXION/fluxion-proxy/src/{index.ts, lib/types.ts}` — pattern Hono + Resend reference (skippare stripe-webhook.ts/refund.ts, non riutilizzati in v2)
3. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` entry "2026-05-01 19:00 — S151 PIVOT CTO"
4. `.claude/rules/{security.md, communication.md}` — vincoli comunicazione + security gates

---

## 2. TODO atomico S152 v2 (replicato da E2E-SIM-PLAN §3 v2)

Eseguire in ordine. Commit dopo ogni Phase B-* (granularità intermedia, rollback safety).

### Phase B-1: Worker scaffold (~30 min)
- [ ] `mkdir argos-proxy && cd argos-proxy`
- [ ] `npm init -y`
- [ ] `npm i hono pdf-lib @pdf-lib/fontkit`
- [ ] `npm i -D wrangler typescript @cloudflare/workers-types @types/node`
- [ ] Copia `wrangler.toml` da `/Volumes/MontereyT7/FLUXION/fluxion-proxy/wrangler.toml` → adatta `name = "argos-proxy"`, rimuovi binding KV `LICENSE_CACHE`
- [ ] Copia `tsconfig.json` da Fluxion mirror
- [ ] Crea `src/lib/types.ts` con interface `Env` v2 ARGOS:
  ```ts
  interface Env {
    DB: D1Database;
    CONTRACTS: R2Bucket;
    RESEND_API_KEY: string;
    ARGOS_ADMIN_SECRET: string;
    R2_SIGNING_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    TELEGRAM_CHAT_ID: string;
    ARGOS_IBAN: string;          // IBAN MyTu/evolu (es. LT...)
    ARGOS_INTESTATARIO: string;  // "Gianluca Di Stasi" o nome conto
    ENVIRONMENT: 'test' | 'production';
  }
  ```
- [ ] Copia skeleton `src/index.ts` Hono router con CORS + health + middleware admin-auth
- [ ] **Commit**: `feat(s152-b1): argos-proxy scaffold (Hono+Workers+TS, no Stripe)`

### Phase B-2: D1 + R2 setup (~20 min)
- [ ] `wrangler d1 create argos-contracts` → annota `database_id` UUID
- [ ] Aggiungi binding D1 in `wrangler.toml`
- [ ] Crea `migrations/0001_init.sql` con schema da `E2E-SIM-PLAN §2.2 v2` (tabella `contracts` con status enum 7-state: DRAFT/SIGNED/AWAITING_DELIVERY/IBAN_SENT/PAID/CANCELLED/REFUNDED + tabella `audit_log` per FES evidence bundle)
- [ ] `wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --local` (test locale)
- [ ] `wrangler r2 bucket create argos-contracts`
- [ ] Aggiungi binding R2 in `wrangler.toml`
- [ ] **Commit**: `feat(s152-b2): D1 schema v2 + R2 bucket + bindings`

### Phase B-3: Contract creation endpoint (~30 min)
- [ ] `src/middleware/admin-auth.ts`: Bearer `ARGOS_ADMIN_SECRET` validator
- [ ] `src/routes/contract-create.ts`: POST `/api/v1/contract/create` (admin auth)
- [ ] Body schema validation (zod o manual): dealer_id, dealer_name, vehicle_data, fee_eur
- [ ] Genera `id` (nanoid 16) + `signature_token` (random 32 hex via crypto.subtle)
- [ ] D1 INSERT con status=DRAFT
- [ ] `audit_log`: action='CREATE', metadata IP+UA+timestamp
- [ ] Return `{contract_id, sign_url: "https://argos-automotive.pages.dev/contract/<token>"}`
- [ ] Test locale via `wrangler dev` + curl
- [ ] **Commit**: `feat(s152-b3): contract creation endpoint + audit log`

### Phase B-4: Contract sign frontend (~1h)
- [ ] `landing/contract/index.html`: template (Tailwind CDN, no build)
- [ ] Header dinamico: dati contratto fetched via `/api/v1/contract/<token>` (GET no auth, ritorna solo dati pubblici)
- [ ] `src/routes/contract-get.ts`: GET endpoint (ritorna recap senza dati interni: dealer_name, vehicle, fee, status)
- [ ] Form: input Nome + Cognome (required, min 2 char ognuno)
- [ ] 10 canvas pre-rendered con i 10 font Google Fonts + nome digitato (live update)
- [ ] Click su canvas = seleziona firma (highlight border)
- [ ] Submit button disabled finché Nome+Cognome+Firma scelta
- [ ] **Clausola consenso esplicito FES** (checkbox required prima submit):
  > "Confermo che la firma elettronica scelta ha valore legale ai sensi dell'art. 20 CAD / eIDAS art. 25 e art. 3 (FES). Ho letto i termini contrattuali."
- [ ] POST `/api/v1/contract/sign` con `{token, signer_name, signature_font, consent_fes:true}`
- [ ] Loading state + redirect a `/contract/thank-you.html?token=` (ricevuta firma + "le invieremo IBAN dopo consegna documenti veicolo")
- [ ] **Commit**: `feat(s152-b4): contract sign UI + 10 firme stilizzate + consenso FES`

### Phase B-5: Sign endpoint + PDF generation (~1h)
- [ ] Scarica 10 font TTF da Google Fonts → `argos-proxy/assets/fonts/*.ttf` (Allura, Great Vibes, Pacifico, Dancing Script, Sacramento, Tangerine, Yellowtail, Kaushan Script, Satisfy, Caveat)
- [ ] `src/pdf/contract-template.ts`: helper pdf-lib per rendering 4 pagine (header + clausole + firma embed + bundle FES evidence pag 4)
- [ ] `src/routes/contract-sign.ts`: POST `/api/v1/contract/sign`
  - [ ] Validate token + status=DRAFT + consent_fes=true
  - [ ] Embed font TTF da assets via @pdf-lib/fontkit
  - [ ] Render PDF 4 pagine
  - [ ] SHA256 PDF bytes
  - [ ] R2 put `contracts/<id>.pdf`
  - [ ] D1 UPDATE status=SIGNED + signature_name + signature_font + signed_at + pdf_sha256 + signer_ip + signer_ua + email_match
  - [ ] `audit_log`: action='SIGN', metadata bundle FES (IP+UA+timestamp+font+SHA256+consent=true)
  - [ ] Resend email Luca + dealer (signed URL R2 7gg)
  - [ ] Telegram alert Luke "📝 Contratto FIRMATO {{dealer_name}} — €{{fee}}"
  - [ ] Return `{ok, contract_id}`
- [ ] Helper `src/lib/r2-signed-url.ts`: HMAC-SHA256 signed URL TTL 7gg
- [ ] Helper `src/lib/resend.ts`: clone pattern Fluxion, 2 templates HTML (firma_dealer, firma_luca)
- [ ] Helper `src/lib/telegram.ts`: send alert
- [ ] **Commit**: `feat(s152-b5): contract signing + PDF gen + R2 + audit FES bundle`

### Phase B-6: Post-firma "delivery pending" frontend (~20 min)
- [ ] `landing/contract/thank-you.html`: pagina ricevuta firma
- [ ] Messaggio: "✅ Contratto firmato. Le invieremo i dati per il bonifico **dopo la consegna del veicolo**. Riceverà email e WhatsApp con IBAN e importo."
- [ ] Recap: dealer + veicolo + fee + numero contratto + data firma
- [ ] Link download PDF firmato (signed URL R2 7gg)
- [ ] Status badge: "AWAITING_DELIVERY"
- [ ] **NESSUN selettore track A/B Stripe** (rimosso post-pivot)
- [ ] **Commit**: `feat(s152-b6): post-sign confirmation page (no payment selector)`

### Phase B-7: Send-IBAN endpoint + WA template (~30 min)
- [ ] `src/routes/send-iban.ts`: POST `/api/v1/contract/<id>/send-iban` (admin auth)
  - [ ] D1 SELECT contract WHERE id=<id> AND status='AWAITING_DELIVERY'
  - [ ] D1 UPDATE status='IBAN_SENT', iban_sent_at=now
  - [ ] `audit_log`: action='SEND_IBAN'
  - [ ] HTTP POST to iMac WA daemon `http://192.168.1.2:9191/send` con template `IBAN_SEND`:
    ```
    IBAN_SEND = "Pronto per il bonifico {{dealer_name}}.\n\nIBAN: {{ARGOS_IBAN}}\nIntestatario: {{ARGOS_INTESTATARIO}}\nImporto: €{{fee}}\nCausale: ARGOS-{{contract_id}}\n\nMi invii ricevuta quando fatto. Grazie."
    ```
  - [ ] Resend email a dealer con stessi dati (canale ridondante)
  - [ ] Telegram alert Luke "📨 IBAN inviato a {{dealer_name}} — attendere bonifico"
  - [ ] Return `{ok, status:'IBAN_SENT', iban_sent_at}`
- [ ] **Commit**: `feat(s152-b7): send-iban endpoint + WA template IBAN_SEND`

### Phase B-8: Mark-paid endpoint + reconciliation manuale (~30 min)
- [ ] `src/routes/mark-paid.ts`: POST `/api/v1/contract/<id>/mark-paid` (admin auth)
  - [ ] Body: `{paid_amount_eur, paid_at_iso, bank_reference}`
  - [ ] D1 SELECT contract WHERE id=<id> AND status='IBAN_SENT'
  - [ ] Validate `paid_amount_eur >= contract.fee_eur` (tolleranza ±€1 per arrotondamenti)
  - [ ] D1 UPDATE status='PAID', paid_at, paid_amount_eur, bank_reference
  - [ ] `audit_log`: action='MARK_PAID', metadata bank_reference
  - [ ] HTTP POST WA daemon template `PAYMENT_RECEIVED`:
    ```
    PAYMENT_RECEIVED = "Bonifico ricevuto {{dealer_name}}, grazie. Operazione conclusa.\n\nA presto per il prossimo veicolo. 🚗"
    ```
  - [ ] Resend email "Pagamento ricevuto" a dealer + Luca
  - [ ] Telegram alert Luke "✅ PAGATO €{{amount}} {{dealer_name}} — contratto chiuso"
  - [ ] Return `{ok, status:'PAID', paid_at}`
- [ ] **NESSUN webhook esterno** (no Stripe in v2). Riconciliazione 100% manuale via dashboard admin.
- [ ] **Commit**: `feat(s152-b8): mark-paid endpoint + WA template PAYMENT_RECEIVED`

### Phase B-9: Trigger integration ARGOS analyzer (~30 min)
- [ ] Modifica `wa-intelligence/response-analyzer.py`:
  - [ ] Helper `create_contract_for_interest(intent, dealer_id, vehicle_data)`
  - [ ] Trigger su INTEREST conf≥0.85 + Telegram approval Luke (NON auto)
  - [ ] HTTP POST `argos-proxy/api/v1/contract/create` con Bearer ARGOS_ADMIN_SECRET
  - [ ] Return `{contract_id, sign_url}`
- [ ] Aggiungi 3 template in `wa-intelligence/templates.py`:
  ```python
  DAY_INTEREST = "Perfetto {{dealer_name}}, le mando il contratto. Compila qui: {{sign_url}}\n\nFirma e ci occupiamo di tutto. Pagherà solo dopo aver ricevuto il veicolo."

  IBAN_SEND = "Pronto per il bonifico {{dealer_name}}.\n\nIBAN: {{ARGOS_IBAN}}\nIntestatario: {{ARGOS_INTESTATARIO}}\nImporto: €{{fee}}\nCausale: ARGOS-{{contract_id}}\n\nMi invii ricevuta quando fatto. Grazie."

  PAYMENT_RECEIVED = "Bonifico ricevuto {{dealer_name}}, grazie. Operazione conclusa.\n\nA presto per il prossimo veicolo."
  ```
- [ ] Sync templates.py iMac via SCP (mantenere divergenza S149b documentata risolta)
- [ ] **Commit**: `feat(s152-b9): ARGOS analyzer trigger contract on INTEREST + 3 templates v2`

### Phase B-10 (S152b se time): Dashboard Luca admin (~1h)
- [ ] Estensione `wa-intelligence/dashboard/app.py`:
  - [ ] Route GET `/contracts` → fetch GET `argos-proxy/api/v1/admin/contracts` (admin auth)
  - [ ] Route POST `/contracts/<id>/send-iban` → proxy a Worker
  - [ ] Route POST `/contracts/<id>/mark-paid` → form modal con campi paid_amount, paid_at, bank_reference → proxy a Worker
- [ ] Template HTML: tabella contratti + bottoni:
  - [ ] "📨 Invia IBAN" (visibile se status=AWAITING_DELIVERY)
  - [ ] "✅ Mark PAID" (visibile se status=IBAN_SENT, apre modal)
  - [ ] Status badges colorati (DRAFT gray / SIGNED yellow / AWAITING blue / IBAN_SENT orange / PAID green)
- [ ] **Commit**: `feat(s152b-b10): admin dashboard contracts + send-iban + mark-paid buttons`

---

## 3. Deploy + test (fine S152, ~30 min)

- [ ] `wrangler secret put RESEND_API_KEY`
- [ ] `wrangler secret put ARGOS_ADMIN_SECRET` (genera `openssl rand -hex 32`)
- [ ] `wrangler secret put R2_SIGNING_SECRET` (`openssl rand -hex 32`)
- [ ] `wrangler secret put TELEGRAM_BOT_TOKEN` (riusa esistente)
- [ ] `wrangler secret put TELEGRAM_CHAT_ID`
- [ ] `wrangler secret put ARGOS_IBAN` (IBAN MyTu o evolu — Luke condivide canale sicuro)
- [ ] `wrangler secret put ARGOS_INTESTATARIO` (es. "Gianluca Di Stasi")
- [ ] **NESSUN secret Stripe** (rimosso v2)
- [ ] `wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --remote` (production D1)
- [ ] `wrangler deploy`
- [ ] Test smoke endpoint:
  - [ ] curl `/health` → 200
  - [ ] curl POST `/api/v1/contract/create` con dati fittizi + admin auth → 200 + token
  - [ ] open contract URL → render OK + 10 canvas firme visibili + checkbox FES
  - [ ] curl POST `/api/v1/contract/sign` mock → SIGNED + PDF in R2
  - [ ] curl POST `/api/v1/contract/<id>/send-iban` → IBAN_SENT + WA daemon hit
  - [ ] curl POST `/api/v1/contract/<id>/mark-paid` → PAID + Telegram
- [ ] **Commit**: `chore(s152): deploy argos-proxy v2 (bonifico manuale, no Stripe)`

---

## 4. Vincoli S152

- ✋ Day 1 reale Stile Car NON parte in S152 (solo build)
- ✋ NESSUNA piattaforma pagamento esterna (no Stripe / no Fintecture / no Revolut / no GoCardless)
- ✋ NO P.IVA finché primo dealer reale paga davvero (rule Luke 7/5)
- ✋ Tutti i secret via `wrangler secret put`, MAI in commit (incluso `ARGOS_IBAN`)
- ✋ Zero modifiche al daemon WA esistente (S149 fix solido)
- ✋ Zero modifiche a `cove_engine_v4.py` (rule .claude/rules/cove.md)
- ✋ Se context >75% in S152 e Phase B-5 non finita → STOP, S152b clean restart
- ✋ Test contract reale solo su TEST_FOUNDER (393314928901), non su dealer reali (è S153)
- ✋ Documentare bug rilevati in `.planning/E2E-SIM-RESULTS.md` (NUOVO)
- ✋ FES bundle evidence (IP+UA+timestamp+SHA256+consent) deve essere in `audit_log` per ogni firma

---

## 5. Scope creep da rifiutare

- Apertura P.IVA (rimossa post-pivot, non in S152)
- Integrazione Stripe / Fintecture / Revolut (rimosse post-pivot)
- Acquisto dominio `argos-automotive.com` per email custom Resend
- Custom domain Worker `api.argos-automotive.com`
- Logo ARGOS finale embedded in PDF (placeholder bastante per S153)
- SPID o firma qualificata FEQ (FES + bundle evidence è proporzionata €800 transazione)
- Dashboard estesa con grafici/analytics
- Reconciliation automatica via OpenBanking (è M3+ con Fintecture, NON S152)
- Refactor `cove_engine_v4.py`
- Fix `pdf_generator_enterprise.py` MacBook locale (iMac OK)
- Test reali con dealer reali (sono S153/S154)

---

## 6. Target di fine S152 v2

✅ Worker `argos-proxy` deployed su Cloudflare (test mode logico, no env Stripe)
✅ D1 `argos-contracts` schema applicato + bindings OK + audit_log table
✅ R2 bucket `argos-contracts` ready
✅ 8 endpoint funzionanti: `create / get / sign / send-iban / mark-paid / admin-list / health` (era 10, ridotto -2 stripe)
✅ Frontend `landing/contract/` deployed con 10 firme stilizzate + consenso FES + thank-you page
✅ Trigger ARGOS analyzer integrato (3 templates: DAY_INTEREST + IBAN_SEND + PAYMENT_RECEIVED)
✅ Resend email pipeline working (2 templates: firma_dealer, firma_luca)
✅ Telegram alerts working (firma + iban_sent + paid)
✅ Dashboard admin minima per send-iban + mark-paid (S152b)
✅ Smoke test verde: contract create → sign → PDF in R2 → send-iban → mark-paid

❌ NON in S152: E2E completo TEST_FOUNDER (è S153)
❌ NON in S152: production deploy
❌ NON in S152: Day 1 reale
❌ NON in S152: Stripe / piattaforma pagamento (è M3+ se mai)

---

## 7. Output S152

- `argos-proxy/` directory completa
- `landing/contract/` directory completa (index.html + thank-you.html)
- `.planning/E2E-SIM-RESULTS.md` (NUOVO, log build + smoke test)
- `prompts/s153_e2e_sim_test_founder.md` (NUOVO, plan E2E sim su TEST_FOUNDER)
- `HANDOFF.md` aggiornato sezione S152
- MEMORY.md entry "S152 BUILD"

---

## 8. Decisione CTO ereditata

S151 plan v2 approvato → S152 build esecutivo. NO discussioni architetturali in S152 (sono in S151). Solo execute + commit + smoke test.

Pivot consolidato: **bonifico bancario manuale**, riconciliazione 5sec/contratto via dashboard admin. Quando volume >50 contratti/mese (M3+) si valuta automation Fintecture/SDD. Fino ad allora: zero piattaforme, zero subscription, €0/mo target rispettato.

Se durante S152 emergono ambiguità:
- Se piccola → decisione CTO + log in `.planning/E2E-SIM-RESULTS.md`
- Se grande → STOP, ritorna a Luke per chiarimento, no improvisation

**Onestà fiscale ribadita**: Luke informato del CRS automatic exchange Lituania-Italia. Decisione operativa = sua. Mio compito CTO = build clean, scalabile, reversibile (P.IVA + Stripe attivabili in 1 sprint quando necessario).
