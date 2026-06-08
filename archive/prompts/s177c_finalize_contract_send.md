# S177c — Finalize S177b: send sign_url + sign + mark PAID + fix 3 BACKLOG HIGH

> **Quando eseguire**: prima sessione utile lun-sab in fascia 9-19 IT (daemon anti-ban). Domenica = OFF Luke (lavapiatti, memory `user_luke_finanzia_canone_lavapiatti_domenica.md`).


**Precondizioni S177b code-VERDE 3.5/5** (commit chain pushato master `0476df6 → 20de638 → c3c98a9 → 315d751`):
- ✅ Classifier `CONTRACT_REQUEST` state-gated funzionante (test 14/14)
- ✅ Handler riusa `create_contract_for_interest()` → Worker auth OK (Bearer + body completo)
- ✅ Contract `52bc66c9feb4771d` creato D1 status=DRAFT, sign_url:
  ```
  https://argos-automotive.pages.dev/contract/612b16944d82d75e639b92c060e74197
  ```
- ✅ `reply_f674d884` salvato pending_replies, **approved=1 (forzato SQL)**, sent=0
- ❌ Daemon WA `/send` rifiuta: `{"error":"outside business hours"}` HTTP 403 (orario serale 18:33 IT)
- ❌ Dashboard 8080 button "Approva" NON aggiorna DB (UPDATE manuale necessario)
- ❌ Daemon NON polla `pending_replies WHERE approved=1 AND sent=0`

**Scope**: chiudere S177b 5/5 + diagnosticare 3 bug HIGH emersi.
**Tempo stimato**: 30-60min. **Context preventivo**: start <30%.

## Decisioni applicate
D-07 HITL strict, D-11 test pipeline TEST_FOUNDER, D-15 founder HITL 100%, **D-OPEN-Q2 cash a consegna NO IBAN** (reply già conforme), D-OPEN-Q5 €800 fee, D-21 workflow eBay-style.

## STEP 0 — Stato preflight verifica (~3min)

```bash
# 1. Reply ancora approved+unsent?
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, approved, sent FROM pending_replies WHERE id='reply_f674d884';\""
# Expected: reply_f674d884|1|0

# 2. Contract ancora DRAFT?
ssh imac "source ~/Documents/app-antigravity-auto/wa-intelligence/.env && curl -sS 'https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/52bc66c9feb4771d' -H \"Authorization: Bearer \$ARGOS_ADMIN_SECRET\" -H 'User-Agent: argos-analyzer/1.0'"
# Expected: status=DRAFT

# 3. Daemon online?
ssh imac "source ~/Documents/app-antigravity-auto/wa-intelligence/.env && curl -sS http://localhost:9191/status -H \"X-API-Key: \$ARGOS_API_KEY\""
# Expected: connected:true
```

Se step 1 mostra `sent=1` → invio già avvenuto durante la notte (polling daemon ciclico), salta STEP 1, vai STEP 2.

## STEP 1 — Invia sign_url al TEST_FOUNDER (~10min, ORARIO BUSINESS)

**Esegui SOLO in fascia 9:00-19:00 IT** (anti-ban hardcoded daemon — vedi BACKLOG #3 sotto).

**Path A — riusa pending_reply esistente (preferito)**: il daemon dovrebbe pollare da solo se approved=1+sent=0. Verifica 2min:
```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, sent FROM pending_replies WHERE id='reply_f674d884';\""
```
Se ancora `sent=0` dopo 2min, daemon non polla → Path B.

**Path B — invio diretto /send daemon** (fallback):
```bash
ssh imac "source ~/Documents/app-antigravity-auto/wa-intelligence/.env && curl -sS -X POST 'http://localhost:9191/send' -H \"X-API-Key: \$ARGOS_API_KEY\" -H 'Content-Type: application/json' -d '{\"phone\":\"393314928901\",\"message\":\"perfetto. firmiamo qui: https://argos-automotive.pages.dev/contract/612b16944d82d75e639b92c060e74197\\n\\nappena firmato ci sentiamo per consegna e saldo. Luca\"}'"
```
Se ancora `outside business hours`: orario fuori range, attendi o vedi BACKLOG #3.

**Path C — manuale fallback** (se daemon irrecuperabile): WhatsApp app dal SIM 3281536308 → chat con 3314928901 → incolla il testo sopra → invia.

**Verifica arrivo**: WA sulla SIM TEST_FOUNDER (3314928901) riceve messaggio con link.

## STEP 2 — Firma contratto fisica (~3min, Luke fisico)

1. Sul telefono SIM 3314928901 → clicca link `https://argos-automotive.pages.dev/contract/612b16944d82d75e639b92c060e74197`
2. Pagina firma su Cloudflare Pages → compila campi (nome dealer, conferma, eventuale firma) → submit
3. Verifica transition DRAFT → AWAITING_DELIVERY:
   ```bash
   ssh imac "source ~/Documents/app-antigravity-auto/wa-intelligence/.env && curl -sS 'https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/52bc66c9feb4771d' -H \"Authorization: Bearer \$ARGOS_ADMIN_SECRET\" -H 'User-Agent: argos-analyzer/1.0'"
   ```

## STEP 3 — Mark PAID (~3min)

**Path preferito — endpoint Worker** (verifica nome esatto endpoint in `argos-proxy/src/routes/`):
```bash
ssh imac "source ~/Documents/app-antigravity-auto/wa-intelligence/.env && curl -sS -X POST 'https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/mark-paid' -H \"Authorization: Bearer \$ARGOS_ADMIN_SECRET\" -H 'Content-Type: application/json' -H 'User-Agent: argos-analyzer/1.0' -d '{\"contract_id\":\"52bc66c9feb4771d\",\"paid_amount_eu_cents\":80000,\"paid_ref\":\"S177B-CONTRACT-INTENT-VERIFY-001\"}'"
```
Se endpoint diverso (404), grep in repo:
```bash
grep -rn "mark.*paid\|paid_amount" /Users/macbook/Documents/combaretrovamiauto-enterprise/argos-proxy/src/routes/
```

**Path fallback — dashboard 8080** sezione contracts (se mark-paid endpoint funziona da UI a differenza di "Approva" button → vedi BACKLOG #1).

**Gate VERDE 5/5**: contract status=PAID + paid_at popolato.

## STEP 4 — Fix 3 BACKLOG HIGH emersi S177b

### BUG-1 — Dashboard "Approva" button non aggiorna DB
**Sintomo**: click "Approva" su `reply_f674d884` (label CONTRACT_REQUEST) — UI non dà errore visibile ma `approved` resta NULL nel DB.
**Debug**:
```bash
ssh imac "tail -100 ~/Documents/app-antigravity-auto/wa-intelligence/dashboard/dashboard.log 2>/dev/null"
grep -n "@app.post.*approve\|def approve_reply\|approva" /Users/macbook/Documents/combaretrovamiauto-enterprise/wa-intelligence/dashboard/app.py
```
Ipotesi: endpoint richiede CSRF token, oppure label CONTRACT_REQUEST non gestita (template dashboard mostra il bottone per ogni label ma il backend whitelist solo LLM_*/POSITIVE_*).

### BUG-2 — Daemon non polla pending_replies approved=1
**Sintomo**: dopo UPDATE manuale `approved=1`, `sent` resta 0 indefinitamente.
**Debug**:
```bash
grep -n "pollOutbound\|pollPending\|pending_replies\|SELECT.*approved" /Users/macbook/Documents/combaretrovamiauto-enterprise/wa-intelligence/wa-daemon.js | head -20
ssh imac "pm2 logs argos-wa-daemon --lines 50 --nostream" # se pm2 disponibile in PATH
```
Ipotesi: daemon polla solo `bridge_outbound` table, non `pending_replies`. Dashboard "Approva" doveva INSERT in `bridge_outbound` ma BUG-1 lo impedisce → catena spezzata. Fix unico per BUG-1+BUG-2.

### BUG-3 — Anti-ban "outside business hours" hardcoded
**Sintomo**: `/send` HTTP 403 fuori range orario.
**Debug**:
```bash
grep -nE "business.?hours|workingHours|cooldown.*hour|hour.*reject" /Users/macbook/Documents/combaretrovamiauto-enterprise/wa-intelligence/wa-daemon.js
```
Ipotesi: range 9:00-19:00 IT hardcoded. Per TEST_FOUNDER serve bypass (whitelist phone 393314928901). Aggiungi check `if (phone == TEST_FOUNDER_PHONE) skip business_hours_check`.

**Tempo budget**: BUG-1+2 fix ~30min (test su MacBook + push + reload daemon iMac), BUG-3 fix ~10min.

## Verdict S177c

- **VERDE 5/5** (STEP 1-3 done + ≥1 BACKLOG fix) → primo deal E2E reactive UFFICIALMENTE chiuso → trigger **S178 sanitizer D-32** Pillow refactor → **Day 1 reale Stile Car** dopo S178 VERDE
- **GIALLO 3-4/5** (STEP 1-3 done ma 0 BACKLOG fix) → close VERDE su S177b business outcome, BACKLOG resta aperto, comunque trigger S178
- **ROSSO ≤2/5** → root cause analysis su daemon/dashboard, S178 differito

## UX gotcha invariata
**MAI invertire direzione TEST_FOUNDER**: SIM `3314928901` (TEST_FOUNDER) ↔ ARGOS `3281536308` (Luca Ferretti). Per STEP 1 invio: from ARGOS `3281536308` to TEST_FOUNDER `3314928901`. Per STEP 2 firma: Luke fisico sul telefono che ha la SIM TEST_FOUNDER.

## Findings parcheggiati S178+ (NON aprire in S177c)
- D-32 sanitizer refactor Pillow-only → S178 post-S177c (BLOCKER Day 1 Stile Car)
- D-31 dossier 12 sezioni → S179
- HITL LLM_MULTI bypass originale S177 (S176-finalize reply_e9be3ac6) → S180
- Vehicle ref hardcoded BMW X1 in handler S177b → lookup dossier_sent table (BLOCKER primo deal reale)
- UA header `argos-analyzer/1.0` solo in create_contract_for_interest, altri endpoint Python urllib → applicare globalmente
- Retry+backoff Worker call
- iMac repo divergent (P6)

## Output attesi S177c
1. `data/s177c_report.md` (STEP 1-3 evidence + diagnosi BUG-1/2/3)
2. Contract `52bc66c9feb4771d` status=PAID nel Worker D1
3. Patch BUG-1 e/o BUG-2 e/o BUG-3 (almeno 1 fix VERDE)
4. Memory entry close S177c con stato finale 5/5 o GIALLO
5. Handoff S178 sanitizer Pillow-only (prompt resume)

## Reference per session start
- Memory S177b code-VERDE: `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s177b_classifier_handler_green.md`
- Report dettagliato: `data/s177b_report.md`
- Patch diff: `git show 0476df6 20de638 c3c98a9` (3 commit S177b)
- Worker source: `argos-proxy/src/routes/contract-create.ts` (Bearer auth + body schema reference)
- Helper Python: `wa-intelligence/response-analyzer.py:121` (`create_contract_for_interest`)
- Dashboard: `wa-intelligence/dashboard/app.py` (BUG-1 investigation)
- Daemon: `wa-intelligence/wa-daemon.js` (BUG-2+3 investigation)

## Credenziali rapide
- Dashboard `http://192.168.1.2:8080/login` password: `1Bwg0bsKrkyDgjhJVczfI-XY_ZCwT91c`
- iMac SSH: `ssh imac`
- DB iMac: `~/Documents/app-antigravity-auto/dealer_network.sqlite`
- .env iMac: `~/Documents/app-antigravity-auto/wa-intelligence/.env` (backup `.env.s177b_bak`)
