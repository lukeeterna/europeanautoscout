# S178 — Pages redeploy + STEP 2 firma + STEP 3 mark-paid + BUG-1/2 diag

> Prerequisito: leggi memory `s177c_giallo_pages_blocker.md` + `s177b_classifier_handler_green.md` per contesto completo.
> Quando eseguire: prima sessione utile lun-sab 9-19 IT (anti-ban daemon; per TEST_FOUNDER ora bypassato whitelist ma resta best practice).

## Stato ereditato S177c GIALLO 3/5

- ✅ BUG-3 fix daemon whitelist TEST_FOUNDER (commits `a97dd07`, `78f9700`)
- ✅ STEP 1 send `out_1778958263596_ob4sr` consegnato (sign_url su SIM 3314928901)
- ❌ BUG-4 emerso: Pages NON auto-deploy GitHub, `/contract/*` serve landing root
- ⏳ STEP 2 firma BLOCKED (Pages routing rotto)
- ⏳ STEP 3 mark-paid BLOCKED (richiede AWAITING_DELIVERY)
- ⏳ BUG-1/2 dashboard Approva + daemon poll pending_replies non diagnosticati

## STEP 1 — Pages redeploy (Luke fisico, ~30s)

Vai su `https://dash.cloudflare.com` → Workers & Pages → progetto `argos-automotive` → **Deployments** → ultima riga → click **"Retry deployment"** OPPURE **"Create deployment"** branch=master.

Attendi build (~1-3min). Verifica:
```bash
curl -sS 'https://argos-automotive.pages.dev/contract/sign.js' | head -3
# Expected: JavaScript reale (non <!DOCTYPE html>)
curl -sS 'https://argos-automotive.pages.dev/contract/612b16944d82d75e639b92c060e74197' | grep -o '<title>[^<]*</title>'
# Expected: <title>Firma contratto ...</title> (non "ARGOS Automotive — Scouting...")
```

Se ancora rotto dopo retry: alternativa wrangler CLI:
```bash
export CLOUDFLARE_API_TOKEN=<token con scope "Account: Cloudflare Pages: Edit">
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
npx wrangler pages deploy landing/ --project-name=argos-automotive --branch=master
```

## STEP 2 — Firma fisica TEST_FOUNDER (Luke, ~3min)

1. Sul telefono SIM 3314928901 → tap link `https://argos-automotive.pages.dev/contract/612b16944d82d75e639b92c060e74197` (link già consegnato da S177c STEP 1)
2. Pagina sign su Pages → compila form (nome, firma stilizzata, FES consent) → submit
3. Verifica transition:
```bash
curl -sS 'https://argos-automotive.pages.dev/api/v1/contract/612b16944d82d75e639b92c060e74197' -H 'User-Agent: argos-analyzer/1.0'
# Expected: "status":"AWAITING_DELIVERY", "signed_at":"<ISO>"
```

NB: se devi rinviare il sign_url (es. messaggio perso), riusa daemon `/send` con TEST_FOUNDER whitelist (no business hours check).

## STEP 3 — Mark PAID (Claude, ~2min)

```bash
ssh imac "set -a; source ~/Documents/app-antigravity-auto/wa-intelligence/.env; set +a; \
  curl -sS -X POST 'https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/52bc66c9feb4771d/mark-paid' \
  -H \"Authorization: Bearer \$ARGOS_ADMIN_SECRET\" \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: argos-analyzer/1.0' \
  -d '{\"paid_amount_cents\":80000,\"payment_bank\":\"Test Bank S178\",\"payment_reference\":\"S178-CONTRACT-INTENT-001\"}'"
```

Verifica `status:PAID + paid_at` popolato. Gate VERDE 5/5 S177c (closure retroattiva).

## STEP 4 — BUG-1/2 diagnosi (~30min, opzionale per VERDE 5/5)

### BUG-1 Dashboard "Approva" button no DB update
```bash
ssh imac "tail -100 /tmp/argos-dashboard-err.log 2>/dev/null; tail -100 /tmp/argos-dashboard-out.log 2>/dev/null"
grep -nE '@app.post.*approve|def approve_reply|approva|/api/approve' wa-intelligence/dashboard/app.py
```
Ipotesi: endpoint backend whitelist solo label `LLM_*` / `POSITIVE_*`, label `CONTRACT_REQUEST` non gestita → click frontend riceve 400/422 silente. Fix: estendere whitelist.

### BUG-2 Daemon non polla pending_replies approved=1
```bash
grep -nE 'pollOutbound|pollPending|pending_replies|SELECT.*approved' wa-intelligence/wa-daemon.js | head -20
```
Ipotesi: daemon polla solo `bridge_outbound` (S171 logic), non `pending_replies` (dashboard table). Fix unico per BUG-1+BUG-2: dashboard Approva → INSERT in `bridge_outbound` invece di solo UPDATE `pending_replies`.

## STEP 5 — Aggiorna BACKLOG.md

Aggiungi entry HIGH:
- `BUG-4 Pages auto-deploy GitHub mancante` — root cause: connector CF→GitHub non config'd; mitigation: retry manuale dashboard ogni cambio landing
- `SSH .env sourcing pattern` — sempre `set -a; source; set +a` per env vars in script SSH

## STEP 6 — Memory + handoff

Se VERDE 5/5: nuova memory `s178_contract_e2e_verde.md` close S177b+c, trigger S179 sanitizer D-32 Pillow refactor (blocker Day 1 Stile Car), poi Day 1 reale.
Se GIALLO/ROSSO: handoff S179 con stato preciso + prompt resume.

## Reference rapide

- TEST_FOUNDER SIM: 3314928901 (numero Luke, NO rischio ban)
- ARGOS WA daemon: 3281536308 (Luca Ferretti persona)
- Contract id: `52bc66c9feb4771d` | signature_token: `612b16944d82d75e639b92c060e74197`
- iMac SSH: `ssh imac` | .env path: `~/Documents/app-antigravity-auto/wa-intelligence/.env`
- Dashboard `http://192.168.1.2:8080/login` pwd: `1Bwg0bsKrkyDgjhJVczfI-XY_ZCwT91c`
- Worker base: `https://argos-proxy.gianlucanewtech.workers.dev`
- Commit chain S177c: `a97dd07 → 78f9700 → 739384e` (master pushato)
- D-OPEN-Q2 cash a consegna: NO IBAN, reply S177b conforme (memory S175.1b)
- D-32 sanitizer Pillow-only: blocker Day 1 reale, gated post-S178 VERDE
