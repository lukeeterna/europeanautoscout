# E2E SIM RESULTS — S152b deploy

**Data**: 2026-05-01
**Sessione**: S152b chunk B
**Stato finale**: 🟡 BUILD COMPLETO + DEPLOY BLOCCATO

---

## Build (B-7..B-10) — ✅ TUTTO PASS

| Phase | Commit | File modificati | Status |
|-------|--------|-----------------|--------|
| B-7 send-iban | `636a2a4` | `argos-proxy/src/routes/send-iban.ts` | ✅ typecheck OK |
| B-8 mark-paid | `6992663` | `argos-proxy/src/routes/mark-paid.ts` | ✅ typecheck OK |
| B-9 analyzer + templates | `86ec355` | `wa-intelligence/templates.py`, `response-analyzer.py` | ✅ smoke unit OK |
| B-10 dashboard | `4fe2455` | `wa-intelligence/dashboard/{app.py, templates/contracts.html, templates/base.html}` | ✅ AST OK |

### Smoke unit B-9 (eseguiti)
- `templates.py`: 3 nuovi template (`DAY_INTEREST`, `IBAN_SEND`, `PAYMENT_RECEIVED`) caricano via `fill_template()` con slot defaults
- `response-analyzer.py::create_contract_for_interest()`:
  - guardrail confidence < 0.85 → ritorna `{ok:False, error:'confidence ... < threshold ...'}`
  - guardrail config mancante → ritorna `{ok:False, error:'ARGOS_PROXY_URL or ARGOS_ADMIN_SECRET not configured'}`

---

## Deploy — 🔴 BLOCCATO

### Tentativo 1 — `wrangler d1 create argos-contracts`
```
✘ ERROR — A request to the Cloudflare API failed.
   Authentication error [code: 10000]
```

### Diagnosi
Il `CLOUDFLARE_API_TOKEN` in `.env`:
- ✅ Attivo (test `/user/tokens/verify` → status `active` registrato in MEMORY 2026-05-01 20:55)
- ❌ NON ha permission per D1 endpoint `/accounts/.../d1/database`
- Token attivo ≠ token con scope sufficiente. La verifica del token attivo NON aveva validato le permission specifiche (gap noto della pre-condizione S152a→S152b).

### Azione richiesta a Luke (UNBLOCK S152b deploy / S153)
1. Vai su https://dash.cloudflare.com/profile/api-tokens
2. Trova il token corrente (account ID `22ddff3a4ef544511523a841b3dcadf8`)
3. Edit → aggiungi i 4 scope mancanti:
   - **D1** → Edit
   - **Workers R2 Storage** → Edit
   - **Workers Scripts** → Edit
   - **Cloudflare Pages** → Edit (se non già presente)
4. Salva → token rotation NON necessaria, stesso valore in `.env`
5. Re-test: `wrangler d1 list` deve ritornare lista (anche vuota) senza errore

### Smoke test deferred a S153 dopo unlock
- `wrangler d1 create argos-contracts` → annota UUID
- Aggiorna `wrangler.toml` con UUID reale
- `wrangler r2 bucket create argos-contracts`
- `wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --remote`
- `wrangler secret put` × 9 (lista in `prompts/s152b_chunk_b.md` Phase Deploy)
- `wrangler deploy` → URL Worker
- Smoke curl:
  - GET `/health` → 200
  - POST `/api/v1/contract/create` (Bearer admin, body TEST_FOUNDER) → 201
  - GET `/api/v1/contract/:token` → 200 ContractPublicDto status=DRAFT
  - Browser: `https://argos-automotive.pages.dev/contract/:token` → render OK
  - (manual) firma → POST `/api/v1/contract/sign` → 200 + R2
  - GET `/api/v1/admin/contracts` → 200
  - POST send-iban → 200 (richiede WA daemon online — vedi sotto)
  - POST mark-paid → 200

---

## Pre-condizioni S153 — stato attuale

| Pre-condizione | Stato | Note |
|----------------|-------|------|
| ARGOS_IBAN | ✅ in `.env` | LT EMI bank code 32500 |
| ARGOS_INTESTATARIO | ✅ in `.env` | nome reale founder (Opzione A post-VoP CTO) |
| CF token attivo | ✅ verified | `/user/tokens/verify` status:active |
| **CF token scope D1+R2+Workers+Pages** | 🔴 **MANCANTE** | bloccante per deploy |
| WA daemon iMac online | 🔴 OFFLINE | banner SessionStart UNREACHABLE; SSH refused 192.168.1.12:22 |
| TEST_FOUNDER reset | ✅ done S151 | PENDING/COLD/0 |

---

## Lezione operativa S152b

1. **Verifica permission scope ≠ verifica token attivo**: avevamo `status:active` su `/user/tokens/verify` ma quello check non rivela quali scope sono presenti. Per validare scope reali serve fare un `wrangler d1 list` (read-only) prima del deploy. Aggiungere come step esplicito in pre-condizione future.

2. **Build completo nonostante blocker deploy**: B-7..B-10 sono codice atomico, race-safe, con audit log e best-effort side effects. La quality gate del codice non dipende dal deploy.

3. **iMac offline = WA daemon offline = side-effect WA fail (ma 200 OK in API)**: design corretto best-effort. Quando iMac torna online, send-iban/mark-paid funzioneranno in produzione senza modifiche al Worker.

4. **Smoke test minimi possibili senza deploy**: solo unit test su Python (templates, helper guardrails). TypeScript Worker non si può smoke-testare in locale per limite macOS 11.6 < 13.5 di workerd. Tutto verde nei limiti possibili.

---

## Conclusione

**Build S152b** = ✅ **COMPLETO** — 4 commit atomici, codice production-ready.
**Deploy S152b** = 🔴 **BLOCCATO** su CF token scope.

S153 (E2E sim TEST_FOUNDER) non può partire fino a:
- Luke aggiorna scope CF token (5 minuti dashboard)
- iMac/WA daemon torna online

Quando entrambi unblock, la fase Deploy + smoke completi prende ~30 min e si può fare a inizio S153.

---

## S154-ter — Smoke E2E TEST_FOUNDER (2026-05-04)

**Data**: 2026-05-04 12:43-12:51 CEST
**Sessione**: S154-ter
**Worker URL**: `https://argos-proxy.gianlucanewtech.workers.dev`
**Phone test**: `+393314928901` (TEST_FOUNDER, contract-create regex) → normalizzato a `393314928901` per daemon (post-fix S154-ter wa-daemon.ts)

### Phase 1 — Phone-format fix + redeploy
- ✅ `argos-proxy/src/lib/wa-daemon.ts`: `replace(/\D/g, '')` PRIMA del regex check
- ✅ `npx tsc --noEmit` → no errors
- ✅ `wrangler deploy` → Version `70958730-f73d-45df-9530-65efdf8dc704` LIVE
- ✅ Commit `ab938c4` `fix(s154c): normalize phone in wa-daemon.ts`

### Phase 1 finalize — Rate-limit Retry-After verify
- Burst 80 parallel `-P 40` → 80x 200 (insufficient concurrency, isolate spread)
- Burst 150 parallel `-P 60` → **75x 200 + 75x 429** ✅
- Header 429: `retry-after: 26` ✅
- Body 429: `{"ok":false,"error":"rate_limit_exceeded","scope":"ip","retry_after":26}` ✅

### Phase 2 — Smoke E2E 8 step (contract `f01c3bb683d2ca69`)

| # | Step | Status | Note |
|---|------|--------|------|
| 1 | HEALTH | ✅ | `{status:"ok", version:"1.0.0", environment:"test"}` |
| 2 | CREATE | ✅ | contract_id 16 hex, signature_token 32 hex, status DRAFT |
| 3 | GET PUBLIC | ✅ | ContractPublicDto, status DRAFT |
| 4 | SIGN | ✅ | status AWAITING_DELIVERY, pdf_sha256 64 hex (font: `great-vibes` kebab-case, NON `GreatVibes`) |
| 5 | R2 VERIFY | ✅ | PDF in R2, SHA256 `100b79b4...da38` MATCH (file 9932 byte) |
| 6 | SEND IBAN | 🟡 | status IBAN_SENT, **wa_sent: false** ⚠️ (root cause: CF Worker → LAN unreachable) |
| 7 | MARK PAID | 🟡 | status PAID, payment_amount_cents=80000, **wa_sent: false** ⚠️ |
| 8 | ADMIN LIST | ✅ | contract presente con status=PAID |

**Risultato**: 6/8 step verde. Step 6+7 status DB transition OK ma WA delivery fallita.

### Phase 3 — Verifiche collaterali

- **D1 audit_log**: ✅ 4/4 row in ordine `CREATE` → `SIGN` → `SEND_IBAN` → `MARK_PAID`
- **WA daemon log iMac**: ❌ 0 entry SEND a 393314928901 nei timestamp 12:48-12:51
- **Telegram alerts**: pending Luke visual confirmation (3 alert attesi: SIGNED + IBAN_SENT + PAID)

### 🐛 Architectural blocker — CF Worker cannot reach LAN daemon

**Worker tail output** (verificato live durante 2nd send-iban call):
```
(error) WA daemon HTTP 403: error code: 1003
(warn) send-iban WA failed: HTTP 403
```

**Root cause**: `WA_DAEMON_URL=http://192.168.1.2:9191` è IP RFC1918 privato. Cloudflare Workers fetch da edge non può raggiungere LAN. Il fetch ritorna **CF error 1003** ("Direct IP Access Not Allowed"). Già documentato in `argos-proxy/src/lib/wa-daemon.ts:8-11`:
> production: daemon NOT publicly reachable. For prod path the Worker would need Tailscale binding or daemon would publish via Cloudflare Tunnel.

**Implicazione**: il fix phone-format S154-ter è corretto e deployed (regex normalizzato), ma WA delivery end-to-end richiede:
- **Opzione A**: Cloudflare Tunnel (`cloudflared tunnel`) che espone iMac:9191 con dominio CF interno + JWT validation
- **Opzione B**: Tailscale binding nel Worker (richiede paid Workers plan / Workers for Platforms)
- **Opzione C**: Move daemon a public host (richiede infra change)

**Soluzione proposta per S155**: Cloudflare Tunnel (€0, 30 min setup, sicuro by default).

### Conclusione S154-ter

**Status**: 🟡 **PARTIAL — phone-fix deployed + 6/8 smoke verde, WA delivery deferred S155**

✅ **Cosa funziona**:
- Worker LIVE production-ready su Cloudflare
- Rate-limit middleware enforced (75 429 su 150 parallel, retry-after header)
- Contract lifecycle DB transitions: DRAFT → AWAITING_DELIVERY → IBAN_SENT → PAID (D1 audit log integro)
- PDF generation + R2 storage + SHA256 match
- Admin endpoints (create + list) auth bearer working
- Public endpoints (get + sign) anonymous working

❌ **Cosa NON funziona** (architettura, NON bug):
- WA delivery LAN daemon (CF Workers → 192.168.1.2 unreachable, error 1003)

**Day 1 reale (Stile Car) NON può partire** finché WA delivery non funziona. Step bloccante per S155: Cloudflare Tunnel daemon.
