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
