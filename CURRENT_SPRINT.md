# Sprint S152 — argos-proxy build (contract + bonifico manuale)

**Pivot CTO S151**: NO Stripe / NO P.IVA / NO Day 1 hardcoded → bonifico bancario manuale + FES.

Chunking 3 sessioni: S152a (B-1→B-5) → S152b (B-7→B-10+deploy) → S153 (E2E sim).

---

## ✅ S152a — CHIUSO 2026-05-01 20:55 (Chunk A)

**4 commit atomici su master**:
- `1f0fbc4` B-1 scaffold Hono+TS (19 file, 3041 LOC, 7 endpoint)
- `d000933` B-2 D1 schema (contracts 7-state + audit_log + 4 index)
- `24a858c` B-4 frontend sign (10 firme + FES consent)
- `0510e44` B-5 PDF gen (pdf-lib + 10 Google Fonts TTF embedded ~2MB)
- `7518017` docs(s152a) chunk A complete + handoff S152b
- `ab79f92` docs(s152b) unblock pre-requisites

**Stato tecnico**:
- ✅ Worker compila (tsc strict)
- ✅ Frontend deployabile su CF Pages (no build, statico)
- ✅ Migration SQL valida
- ✅ PDF gen wired con TTF subset
- ⏸️ Wrangler local NON gira su macOS 11.6 (richiede 13.5+) → remote deploy in S152b

**Pre-requisiti S152b — TUTTI SBLOCCATI**:
- ✅ `ARGOS_IBAN` in `.env` (LT EMI, mod97 valido) — wrangler secret put in deploy
- ✅ `ARGOS_INTESTATARIO` in `.env` (Opzione A post-flag CTO SEPA Verification of Payee)
- ✅ CF token verificato attivo (`/user/tokens/verify`)

---

## ⏸️ S152b — PENDING (clean context start)

**Leggere prima**: `prompts/s152b_chunk_b.md`

**TODO**:
- B-7 send-iban endpoint (validate AWAITING_DELIVERY → IBAN_SENT, WA template + email + Telegram)
- B-8 mark-paid endpoint (validate amount tolerance ±€1 → PAID, WA PAYMENT_RECEIVED)
- B-9 analyzer trigger (`response-analyzer.py` create_contract_for_interest + 3 templates su `templates.py`)
- B-10 dashboard (`wa-intelligence/dashboard/app.py` /contracts route + proxy + HTML)
- Deploy: wrangler d1 create + r2 bucket + execute remote + 9 secrets + deploy + smoke 8 endpoint
- Handoff S153

**Tempo stimato**: 3h

---

## ⏸️ S153 — E2E sim TEST_FOUNDER (post-S152b)

- Reset TEST_FOUNDER: `PENDING | COLD | outbound=0 | last_contact=NULL`
- Simulazione completa: Day 1 → vehicle_request → dossier → contract+firma → bonifico manuale + mark PAID
- Verifica visiva Luke prima di Day 1 reale

**Tempo stimato**: 1-2h

---

## Vincoli invariati (da S151 pivot)

- ❌ NO Stripe / NO Fintecture / NO Revolut → solo bonifico bancario manuale
- ❌ NO P.IVA → riapri solo a primo dealer reale pagante
- ❌ NO Day 1 reale → parte solo post-S153 verde + OK Luke
- ✅ FES + bundle evidenza completo (IP+UA+timestamp+SHA256+consent_checkbox+WA_conv_id)
- ✅ €0/mo cost target (Cloudflare free tier)
- ✅ Test su TEST_FOUNDER (393314928901) prima di qualsiasi dealer reale
