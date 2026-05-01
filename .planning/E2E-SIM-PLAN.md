# E2E SIM PLAN v2 — ARGOS Phase A (S151)

**Sessione**: S151 Phase A — pivot CTO post-risposte Luke
**Data**: 2026-05-01 19:10 (v2 dopo pivot)
**Scope**: progettare 5-step E2E sim su TEST_FOUNDER prima del Day 1 reale Stile Car
**Decisioni CTO finali**: stack firma, **bonifico bancario manuale (no Stripe)**, FES con bundle evidenza, deploy strategy
**Vincolo**: NO CODE in S151. Solo plan + decisioni + TODO atomico per S152.
**Cost target**: €0/mo (Cloudflare free tier + Resend free tier + IBAN MyTu/evolu esistenti)

---

## 0. Risposte Luke (input Phase A) — POST PIVOT

| # | Domanda | Risposta finale | Decisione operativa v2 |
|---|---------|-----------------|------------------------|
| 1 | Stack §2 | ✅ OK | Hono + Workers + D1 + R2 + Resend + pdf-lib + 10 Google Fonts |
| 2 | Stripe / pagamento | 🔄 No piattaforma — analisi Revolut/Fintecture/GoCardless rifiutate | **Bonifico bancario manuale** su IBAN MyTu/evolu esistenti. Mark PAID via dashboard. €0 fee, zero API, zero registrazione |
| 3 | Dual-track | ✅ OK | Ridefinito: Track A bonifico (S152), Track B automation (M3+) |
| 4 | FES | "Valuta tu" → CTO PROCEED | FES + bundle evidenza (IP+UA+timestamp+WA log+SHA256+clausola consenso) |
| 5 | Stripe nuovo account | ❌ Non serve più | Skippato |
| 6 | Cloudflare token | ✅ Verificato attivo (`CLOUDFLARE_API_TOKEN` in `.env`, account `22ddff3a4ef544511523a841b3dcadf8`) | Verifico permission D1+R2 a inizio S152 |
| 7 | P.IVA | 🛑 "Nessuna p iva per ora" | Rimosso da blocker S151. Riapri solo a primo dealer reale pagante |
| 8 | Day 1 reale | 🛑 "No se non completiamo tutto con numero test" | Nessuna data hardcoded. Day 1 parte solo post-S153 verde |

---

## 1. Architettura E2E v2 (5 step)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ARGOS — pipeline post-Day 1 (v2 NO Stripe)                          │
│                                                                     │
│ STEP 1  Cold contact persona-prima                                  │
│   Day 1 testo manuale → WA daemon (existing) → ack 1/2/3            │
│                                                                     │
│ STEP 2  vehicle_request                                             │
│   Inbound → response-analyzer → classify VEHICLE_REQUEST            │
│   → extract {make, model, year, budget, opts}                       │
│   → Telegram HOLD approval Luca → trigger scrape on-demand          │
│                                                                     │
│ STEP 3  Dossier consegnato                                          │
│   tools/on_demand_runner.py (existing) →                            │
│   AS24 scrape → CoVe scoring → top candidate →                      │
│   image_sanitizer (iMac) → pdf_generator_enterprise →               │
│   send PDF via daemon → ack=2 + LETTO + visual confirm Luke         │
│                                                                     │
│ STEP 4  ─── NUOVO ───  Contratto firmato                            │
│   Dealer dice "ok procediamo" → analyzer INTEREST                   │
│   → Telegram HOLD → Luke approva                                    │
│   → POST argos-proxy/api/v1/contract/create                         │
│   → backend genera contract_id + signature_token                    │
│   → invio WA template DAY_INTEREST con sign_url                     │
│   → dealer apre argos-automotive.pages.dev/contract/<token>         │
│   → form nome+cognome → 10 firme stilizzate Google Fonts            │
│   → dealer sceglie firma → POST /api/v1/contract/sign               │
│   → Worker: render PDF firmato (pdf-lib) + bundle evidenza          │
│      (IP + UA + timestamp + SHA256 + WA conv_id + email)            │
│   → R2 store contratto + D1 status=SIGNED                           │
│   → Resend email Luca + dealer (signed URL R2 7gg)                  │
│   → contract page redirect /post-sign                               │
│                                                                     │
│ STEP 5  ─── NUOVO v2 ───  Bonifico bancario manuale                 │
│   Post-firma contract page mostra:                                  │
│     "Quando consegniamo i documenti auto:                           │
│      - Le invio IBAN MyTu per bonifico €800                         │
│      - Causale: Contratto ARGOS-{id}                                │
│      - Marco contratto come pagato a ricezione bonifico"            │
│   D1 status=AWAITING_DELIVERY                                       │
│                                                                     │
│   Post-consegna documenti (Luke verifica):                          │
│     Luke su dashboard click "SEND IBAN" →                           │
│     POST /api/v1/contract/<id>/send-iban                            │
│     → Worker: invia template WA al dealer con IBAN + causale        │
│     → D1 status=IBAN_SENT, iban_sent_at                             │
│                                                                     │
│   Dealer paga bonifico (Luke vede in MyTu/evolu app):               │
│     Luke su dashboard click "MARK PAID" →                           │
│     POST /api/v1/contract/<id>/mark-paid                            │
│     Body: {amount_received, bank, reference}                        │
│     → D1 status=PAID, paid_at, payment_method='bank_transfer'       │
│     → Telegram alert + Resend email Luca                            │
│     → WA notification dealer "Bonifico ricevuto, contratto chiuso"  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stack tecnologico (decisioni CTO v2)

### 2.1 Backend Worker — `argos-proxy`
- **Framework**: Hono (clone pattern fluxion-proxy)
- **Runtime**: Cloudflare Workers (compat date 2025-03-19, nodejs_compat)
- **Deploy**: `wrangler deploy` da `argos-proxy/` directory
- **Domain**: `argos-proxy.<account>.workers.dev` per S152 dev

### 2.2 State storage — Cloudflare D1
Schema `argos-contracts.db`:
```sql
CREATE TABLE contracts (
  id TEXT PRIMARY KEY,
  dealer_id TEXT NOT NULL,
  dealer_name TEXT NOT NULL,
  dealer_phone TEXT NOT NULL,
  vehicle_vin TEXT,
  vehicle_make TEXT,
  vehicle_model TEXT,
  vehicle_year INTEGER,
  vehicle_price_eu_cents INTEGER,
  fee_cents INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'DRAFT',
  -- DRAFT, SIGNED, AWAITING_DELIVERY, IBAN_SENT, PAID, CANCELLED, REFUNDED
  signature_token TEXT UNIQUE NOT NULL,
  signature_font TEXT,
  signature_signer_name TEXT,
  signature_ip TEXT,
  signature_ua TEXT,
  signature_at TEXT,
  signature_wa_conv_id TEXT,
  signature_email_match TEXT,
  pdf_r2_key TEXT,
  pdf_sha256 TEXT,
  iban_sent_at TEXT,
  iban_sent_iban TEXT,
  paid_at TEXT,
  payment_amount_cents INTEGER,
  payment_bank TEXT,
  payment_reference TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_dealer ON contracts(dealer_id);
CREATE INDEX idx_contracts_token ON contracts(signature_token);

CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contract_id TEXT NOT NULL,
  action TEXT NOT NULL,
  actor TEXT NOT NULL,
  details TEXT,
  ip TEXT,
  ua TEXT,
  at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (contract_id) REFERENCES contracts(id)
);
```

### 2.3 PDF storage — Cloudflare R2
- Bucket: `argos-contracts`
- Path: `contracts/<contract_id>.pdf`
- Access: privato + signed URL HMAC TTL 7gg

### 2.4 Frontend contract page — Cloudflare Pages
- Path: `argos-automotive.pages.dev/contract/<token>`
- Tech: HTML statico + Tailwind CDN (no build) + Vanilla JS modulare
- File:
  - `landing/contract/index.html` (sign page)
  - `landing/contract/sign.js` (logica firma 10-canvas)
  - `landing/contract/post-sign.html` (recap + IBAN info text)

### 2.5 Firma 10-scelte stilizzate
- 10 Google Fonts CDN script:
  Allura, Great Vibes, Pacifico, Dancing Script, Sacramento, Tangerine, Yellowtail, Kaushan Script, Satisfy, Caveat
- Frontend: 10 canvas 400x80px live render del nome digitato
- Backend: TTF embedded via pdf-lib + fontkit
- Assets: `argos-proxy/assets/fonts/<name>.ttf` (10 file, ~500KB)

### 2.6 PDF generation — pdf-lib
- Library: `pdf-lib` 1.17+ + `@pdf-lib/fontkit` (Workers nativo)
- Layout: 4 pagine (header+parti / oggetto+veicolo+fee / clausole+FES consent / firma+SHA256)
- Output: PDF binary

### 2.7 Email — Resend
- Free tier: 3000/mese
- From: `onboarding@resend.dev` (fallback) o dominio custom (futuro)
- Templates HTML:
  - `contract_signed_dealer.html`
  - `contract_signed_luca.html`
  - `iban_sent_dealer.html`
  - `payment_received_luca.html`
  - `payment_received_dealer.html`

### 2.8 Pagamento — BONIFICO BANCARIO MANUALE
**Decisione CTO v2**: nessuna piattaforma pagamento (no Stripe, no Fintecture, no Revolut, no GoCardless).

**Flow operativo**:
1. Post-firma → contract page mostra recap + "Le invieremo IBAN dopo consegna documenti auto"
2. D1 status = AWAITING_DELIVERY
3. Luca consegna documenti auto al dealer (offline)
4. Luca su dashboard click "SEND IBAN" → Worker invia WA template al dealer:
   ```
   Bonifico €800 — Contratto ARGOS-{id}
   IBAN: {IBAN_MYTU}
   Intestatario: Gianluca Di Stasi
   Causale: ARGOS-{id}
   ```
5. D1 status = IBAN_SENT
6. Dealer fa bonifico (vede "MyTu" o "evolu" in estratto, neutrale)
7. Luca verifica bonifico ricevuto su app MyTu/evolu (manualmente)
8. Luca su dashboard click "MARK PAID" → Worker:
   - D1 UPDATE status=PAID, paid_at, payment_amount_cents, payment_bank, payment_reference
   - Audit log entry
   - Telegram alert
   - Resend email Luca + dealer
   - WA template al dealer "Bonifico ricevuto, contratto chiuso"

**IBAN MyTu/evolu**: configurato in Worker env `ARGOS_IBAN` + `ARGOS_INTESTATARIO`. Switch tra MyTu / evolu via env var (Luke decide quale conto usare).

**Pro**:
- €0 fee piattaforma
- Zero registrazione
- Estratto conto pulito (nome banca neutrale)
- Compatibile con conti esistenti
- Dealer Sud RELAZIONALE preferisce bonifico
- Implementazione semplice (3 endpoint vs 6 Stripe)

**Contro accettati**:
- Reconciliation manuale (~5 sec/contratto, ok fino 50/mese)
- No webhook automation (mark PAID manuale)
- No chargeback protection (per €800 B2B non serve)

**Trigger upgrade automation**: M3+ post 10° dealer pagante, valutare Fintecture PIS.

### 2.9 Auth & security
- Worker auth:
  - Routes pubbliche (sign, contract-get, health) — no auth
  - Routes admin (create, send-iban, mark-paid, contracts-list) — Bearer `ARGOS_ADMIN_SECRET`
- Signed URL R2 — HMAC + TTL 7gg
- CORS — whitelist `argos-automotive.pages.dev`
- Secrets Worker: `ARGOS_ADMIN_SECRET, R2_SIGNING_SECRET, RESEND_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ARGOS_IBAN, ARGOS_INTESTATARIO`
- ❌ NO Stripe secrets (rimosso)

### 2.10 Trigger flow (analyzer → contract creation)
**Modifica MINIMA `wa-intelligence/response-analyzer.py`** (~10 righe):
- INTEREST conf≥0.85 → Telegram HOLD per Luke approval
- Su approve → POST `argos-proxy/api/v1/contract/create` con `{dealer_id, vehicle_data}`
- Ritorna `{contract_id, sign_url}`
- Auto-genera template DAY_INTEREST con `{sign_url}` → invia via daemon

**Aggiungi template** in `wa-intelligence/templates.py` (sia local che iMac):
```python
DAY_INTEREST = """Perfetto {dealer_name}, le mando il contratto.
Compila e firma qui: {sign_url}

Dopo la firma, le invio i documenti dell'auto.
Tutto chiaro?"""

IBAN_SEND = """{dealer_name}, ecco i dati per il bonifico:

IBAN: {iban}
Intestatario: {intestatario}
Importo: €800
Causale: ARGOS-{contract_id}

Quando vede il bonifico, mi conferma."""

PAYMENT_RECEIVED = """{dealer_name}, ricevuto il bonifico €800.
Contratto chiuso. Buon lavoro!"""
```

---

## 3. TODO atomico S152 (build, ~3-4h totale)

### Phase B-1: Worker scaffold (~30 min)
- [ ] `mkdir argos-proxy && cd argos-proxy && npm init -y`
- [ ] `npm i hono pdf-lib @pdf-lib/fontkit`
- [ ] `npm i -D wrangler typescript @cloudflare/workers-types`
- [ ] Copia `wrangler.toml` da fluxion-proxy → adatta name e bindings
- [ ] Copia `tsconfig.json` mirror
- [ ] Crea `src/lib/types.ts` con interface `Env` ARGOS-specific
- [ ] Crea `src/index.ts` Hono router + CORS + health
- [ ] Commit: `feat(s152-b1): argos-proxy scaffold`

### Phase B-2: D1 + R2 setup (~20 min)
- [ ] `wrangler d1 create argos-contracts` → annota database_id
- [ ] Aggiungi binding D1 in wrangler.toml
- [ ] Crea `migrations/0001_init.sql` (schema §2.2)
- [ ] `wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --local`
- [ ] `wrangler r2 bucket create argos-contracts`
- [ ] Aggiungi binding R2 in wrangler.toml
- [ ] **Verifica permessi token CF**: D1 admin + R2 admin + Workers admin (dal dash CF se mancano)
- [ ] Commit: `feat(s152-b2): D1 schema + R2 bucket + bindings`

### Phase B-3: Contract creation endpoint (~30 min)
- [ ] `src/middleware/admin-auth.ts`: Bearer ARGOS_ADMIN_SECRET
- [ ] `src/routes/contract-create.ts`: POST `/api/v1/contract/create` (admin)
- [ ] Body validation + INSERT D1 status=DRAFT
- [ ] Return `{contract_id, sign_url}`
- [ ] Test via wrangler dev + curl
- [ ] Commit: `feat(s152-b3): contract creation endpoint`

### Phase B-4: Contract sign frontend (~1h)
- [ ] `src/routes/contract-get.ts`: GET `/api/v1/contract/<token>` (no auth, dati pubblici only)
- [ ] `landing/contract/index.html`: Tailwind CDN + form nome+cognome
- [ ] 10 canvas con 10 font Google Fonts + nome live update
- [ ] Click canvas = seleziona firma
- [ ] Submit → POST `/api/v1/contract/sign`
- [ ] `landing/contract/sign.js`: logica + canvas rendering
- [ ] Commit: `feat(s152-b4): contract sign UI 10-firme`

### Phase B-5: Sign endpoint + PDF generation (~1h)
- [ ] Scarica 10 TTF Google Fonts → `argos-proxy/assets/fonts/`
- [ ] `src/pdf/contract-template.ts`: pdf-lib renderer 4 pagine + clausola FES
- [ ] `src/routes/contract-sign.ts`: POST `/api/v1/contract/sign`
  - Validate token + status=DRAFT + signer_name ≥ 3 char + font in whitelist
  - Render PDF + SHA256 + R2 put
  - Bundle evidenza: capture IP (CF-Connecting-IP), UA, timestamp, signature_at
  - D1 UPDATE status=SIGNED + signature_*
  - Resend email Luca + dealer (signed URL)
  - Audit log entry
  - Return `{ok, contract_id, post_sign_url}`
- [ ] `src/lib/r2-signed-url.ts`: HMAC signed URL TTL 7gg
- [ ] `src/lib/resend.ts`: clone pattern Fluxion + 4 templates
- [ ] Commit: `feat(s152-b5): contract signing + PDF + R2 + email`

### Phase B-6: Post-sign frontend (~20 min)
- [ ] `landing/contract/post-sign.html`: recap firma + testo informativo bonifico
  - "Quando consegniamo i documenti auto, le invieremo IBAN per bonifico €800"
  - No form, no action richiesta dealer
- [ ] Commit: `feat(s152-b6): post-sign info page`

### Phase B-7: Send IBAN endpoint (~30 min)
- [ ] `src/routes/send-iban.ts`: POST `/api/v1/contract/<id>/send-iban` (admin)
- [ ] Validate status=AWAITING_DELIVERY
- [ ] Build template IBAN_SEND con {iban, intestatario, contract_id}
- [ ] HTTP POST a daemon WA `localhost:9191/send` con phone dealer + body
- [ ] D1 UPDATE status=IBAN_SENT, iban_sent_at, iban_sent_iban
- [ ] Resend email dealer copia testo
- [ ] Audit log
- [ ] Commit: `feat(s152-b7): send IBAN endpoint`

### Phase B-8: Mark Paid endpoint (~30 min)
- [ ] `src/routes/mark-paid.ts`: POST `/api/v1/contract/<id>/mark-paid` (admin)
- [ ] Body: `{amount_received_cents, bank, reference}`
- [ ] Validate status in (IBAN_SENT, AWAITING_DELIVERY)
- [ ] D1 UPDATE status=PAID, paid_at, payment_*
- [ ] Telegram alert "💰 Pagamento ricevuto contratto {id}"
- [ ] Resend email Luca + dealer
- [ ] WA template PAYMENT_RECEIVED al dealer
- [ ] Audit log
- [ ] Commit: `feat(s152-b8): mark paid endpoint`

### Phase B-9: Trigger integration ARGOS (~30 min)
- [ ] Modifica `wa-intelligence/response-analyzer.py` ~10 righe
  - Helper `create_contract_for_interest(...)`
  - Trigger su INTEREST conf≥0.85 + Telegram HOLD approval
  - HTTP POST argos-proxy con Bearer
- [ ] Aggiungi template `DAY_INTEREST`, `IBAN_SEND`, `PAYMENT_RECEIVED` in `templates.py`
- [ ] Sync `templates.py` iMac via SCP (chiudi divergenza S149b)
- [ ] Commit: `feat(s152-b9): analyzer trigger contract on INTEREST`

### Phase B-10 (S152b se time): Dashboard Luca admin (~45 min)
- [ ] Estensione `wa-intelligence/dashboard/app.py`:
  - GET `/contracts` → fetch list da Worker
  - POST `/contracts/<id>/send-iban` → proxy
  - POST `/contracts/<id>/mark-paid` (con form: amount, bank, reference)
- [ ] Template HTML: tabella + bottoni per status:
  - SIGNED → bottone "MARK AWAITING_DELIVERY" (auto su confirm)
  - AWAITING_DELIVERY → bottone "SEND IBAN"
  - IBAN_SENT → form "MARK PAID" (amount, bank, reference)
  - PAID → badge ✅
- [ ] Commit: `feat(s152b-b10): admin dashboard contracts`

---

## 4. Test plan S153 sim (E2E TEST_FOUNDER)

**Pre**: TEST_FOUNDER reset OK ✅ (eseguito S151 18:10), Worker deployed test, IBAN MyTu test configurato

### Step 1 sim
- Day 1 testo manuale a TEST_FOUNDER → ack=2/3 + visual confirm

### Step 2 sim
- Luke risponde "buongiorno mi serve BMW X3 2022 sotto 35k automatica"
- Analyzer classify VEHICLE_REQUEST conf≥0.85 → extract → Telegram HOLD → approve
- Pass: parametri estratti + scrape triggered

### Step 3 sim
- Pipeline scrape→CoVe→sanitize→PDF→send WA
- Pass: PDF ≥200KB + 6 pagine + ack=2 + LETTO + visual confirm

### Step 4 sim
- Luke risponde "ok mi piace, procediamo"
- Analyzer INTEREST conf≥0.85 → Telegram HOLD → approve
- Worker create contract → D1 row + sign_url
- Daemon invia DAY_INTEREST con sign_url
- Luke apre link mobile → compila nome+cognome → vede 10 firme → sceglie → submit
- Worker render PDF + R2 store + email Luke + WA notification
- Pass: PDF firmato apre OK + 10 font visibili + email ricevuta + D1 SIGNED + bundle evidenza completo

### Step 5 sim — bonifico flow
- Luke su dashboard click "SEND IBAN"
- Worker invia template IBAN_SEND al dealer (TEST_FOUNDER)
- Pass: WA ricevuto + D1 IBAN_SENT
- Luke simula bonifico ricevuto (no soldi reali, è sim)
- Luke su dashboard click "MARK PAID" form (amount=80000, bank=MyTu, reference=test123)
- Worker: D1 PAID + Telegram + email + WA PAYMENT_RECEIVED
- Pass: tutti i side effect avvengono + dashboard mostra ✅

### Cronometraggio + bug log
- File `.planning/E2E-SIM-RESULTS.md` con time + pass/fail + bug + decisione GO Day 1 reale o iter

---

## 5. Stima tempi v2

| Phase | Tempo | Sessione |
|-------|-------|----------|
| A — Plan v2 (questo) | 1.5h | S151 (DONE) |
| B-1 → B-9 build core | ~3.5h | S152 |
| B-10 dashboard | ~45 min | S152b |
| C — E2E sim | ~1-2h | S153 |
| Buffer fix bug | ~1-2h | S153b |
| **Totale** | **~7-9h** | **S151+S152+S152b+S153(+b)** |

**Risparmio vs v1**: -2h (rimosso tutto blocco Stripe).

---

## 6. Rischi residui v2

### 6.1 P.IVA blocker production (DEFERRED)
- Rimosso da blocker S151. Test mode E2E sim non genera reddito → zero esposizione fiscale ora
- Riapri solo quando dealer reale firma e sta per fare bonifico
- **CRS automatic exchange Lituania-Italia attivo dal 2017** — segnalato a Luke. Founder decide.

### 6.2 Validità legale FES (FIRMA ELETTRONICA SEMPLICE)
- eIDAS art.3 — ammessa libero foro, regge se non contestata
- Bundle evidenza in D1 + audit_log = bundle plurale per giudizio civile <€2.5k
- Implication: dealer disputa improbabile per €800 B2B con consenso esplicito clausola
- Mitigazione long-term M3+: SPID Sign o DocuSign EU Advanced per Tier-1

### 6.3 Reconciliation manuale bonifico
- Luke deve verificare bonifico in app MyTu/evolu poi click "MARK PAID"
- Rischio: dimenticanza → status non aggiornato → no notification dealer
- Mitigazione: Telegram daily reminder "X contratti IBAN_SENT da N giorni, verifica bonifico"

### 6.4 R2 signed URL leak
- TTL 7gg + access log in audit_log + email solo dealer + Luca

### 6.5 Daemon WA downtime durante send-iban / payment-received
- Worker tenta retry 3x → fallback Telegram alert "WA send failed contract X"
- Luke manda manualmente

---

## 7. File da creare/modificare in S152

```
combaretrovamiauto-enterprise/
├── argos-proxy/                          (NUOVO — Cloudflare Worker)
│   ├── package.json
│   ├── tsconfig.json
│   ├── wrangler.toml
│   ├── migrations/0001_init.sql
│   ├── assets/fonts/                     (10 .ttf)
│   └── src/
│       ├── index.ts
│       ├── lib/
│       │   ├── types.ts
│       │   ├── r2-signed-url.ts
│       │   ├── resend.ts
│       │   ├── telegram.ts
│       │   └── wa-daemon.ts              (HTTP client to localhost:9191)
│       ├── pdf/
│       │   └── contract-template.ts
│       ├── middleware/
│       │   └── admin-auth.ts
│       └── routes/
│           ├── health.ts
│           ├── contract-create.ts
│           ├── contract-get.ts
│           ├── contract-sign.ts
│           ├── send-iban.ts
│           ├── mark-paid.ts
│           └── contracts-list.ts        (admin, list contracts per dashboard)
├── landing/contract/                     (NUOVO — frontend)
│   ├── index.html                        (sign page)
│   ├── sign.js
│   └── post-sign.html
├── wa-intelligence/
│   ├── response-analyzer.py              (modifica ~10 righe trigger INTEREST)
│   ├── templates.py                      (aggiungi 3 template)
│   └── dashboard/app.py                  (estensione contracts CRUD)
└── .planning/
    ├── E2E-SIM-PLAN.md                   (v2, questo doc)
    ├── E2E-SIM-CONTRACTS.md              (clausole legali contratto, S152)
    └── E2E-SIM-RESULTS.md                (risultati S153)
```

---

## 8. Domande residue (NON-blocking S152)

1. Logo ARGOS embedded in PDF: usare `assets/ARGOS_logo_sobrio_horizontal.png`?
2. Clausole contratto legali: template Luke o standard ANIASA B2B auto?
3. IBAN per S152 sim: usare quale tra MyTu o evolu? (configurazione env Worker)
4. Worker custom domain (M3+): `api.argos-automotive.com`?

---

## 9. Approvazione richiesta a Luke prima di S152 (v2 — 5 punti)

✅ Stack tecnologico §2 (Hono+Workers+D1+R2+Resend+pdf-lib+10 Google Fonts) — CONFERMATO
✅ Pagamento bonifico bancario manuale (no Stripe/Fintecture/Revolut) — CONFERMATO
✅ FES con bundle evidenza (proporzionata €800 B2B) — CTO PROCEED
✅ P.IVA defer (riapri a primo dealer reale pagante) — CONFERMATO
✅ Day 1 reale senza data hardcoded (parte solo post-S153 verde) — CONFERMATO

→ TUTTI 5 PUNTI APPROVATI. **GO S152 build**.

---

## 10. Onestà fiscale (CTO duty notice)

Segnalato a Luke una volta in modo chiaro:
- Lituania ha CRS automatic exchange con Italia dal 2017 — Agenzia Entrate vede ogni IBAN lituano riconducibile a residente fiscale italiano
- €800 × N dealer su qualsiasi conto (IT/LT/Stripe/Fintecture/Revolut/MyTu) senza P.IVA = stesso reddito non dichiarato
- Differenza fiscale tra le 5 modalità = ZERO
- Mio ruolo CTO: segnalo, non blocco. Luke decide.
- P.IVA forfettaria €0/anno fino €85k → attivare quando primo dealer paga davvero, non prima
- Test mode E2E sim S152+S153 NON genera reddito → zero esposizione fiscale ora

Notice persistito anche in MEMORY.md (entry 2026-05-01 19:00 — S151 PIVOT CTO).
