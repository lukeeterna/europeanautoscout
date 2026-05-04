# S155-tris — Switch a tailscaled standalone + smoke E2E

**Sessione**: S155-tris (clean context start)
**Data**: 2026-05-04 (post S155-bis BLOCKED)
**Scope**: bypass Tailscale.app GUI buggy → install `tailscaled` open-source standalone su iMac → re-set funnel → smoke E2E TEST_FOUNDER → docs+commit. **NIENTE Day 1 reale** (richiede sessione separata con autorizzazione esplicita Luke + test interattivo).
**Tempo stimato**: ~55-85min (un-enroll GUI 5min + install standalone 15min + launchd plist 10min + re-enroll 5min + funnel set 5min + smoke E2E 20min + docs 15min)
**Esecuzione**: AUTONOMA — Claude ha accesso SSH iMac + API token Tailscale + admin secret Worker. Luke approverà solo lo switch architetturale all'inizio.

---

## 0. Pre-condizioni S155-tris — verificare PRIMA

| Pre-condizione | Verifica |
|----------------|----------|
| iMac up | `ping -c 1 192.168.1.2` |
| WA daemon online | `ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"` → `wa_status: connected` |
| PM2 vivo | `ssh gianlucadistasi@192.168.1.2 "PATH=/usr/local/bin:/opt/homebrew/bin:\$PATH /Users/gianlucadistasi/.npm-global/bin/pm2 list"` mostra wa-daemon online |
| Worker LIVE | `curl -s https://argos-proxy.gianlucanewtech.workers.dev/health` → status:ok |
| Token API Tailscale `.env` | `grep TAILSCALE_API_TOKEN .env` presente |
| Admin Worker secret `.env` | `grep ARGOS_ADMIN_SECRET .env` presente |
| ACL+HTTPS già configurati | (S155 PARTIAL) verificare: `curl -s "https://api.tailscale.com/api/v2/tailnet/-/acl" -u "$TS_TOKEN:" | python3 -m json.tool | grep funnel` deve mostrare `funnel` attr |
| Tailnet nome | `tail62c468.ts.net` (hardcoded S155-tris) |
| Hostname target | `imac-di-gianluca` (mantenere consistente, cert valido) |

🛑 **Se WA daemon UNREACHABLE**: eseguire `ssh gianlucadistasi@192.168.1.2 "PATH=/usr/local/bin:/opt/homebrew/bin:\$PATH /Users/gianlucadistasi/.npm-global/bin/pm2 resurrect"` e attendere ~15s.

---

## 1. Stato S155-bis — cosa è già configurato (non rifare)

✅ Tailnet `tail62c468.ts.net`, account `ferretti.argosautomotive@gmail.com`
✅ ACL `nodeAttrs autogroup:member → funnel` applicato
✅ Settings `httpsEnabled: true`
✅ Cert Let's Encrypt provisioned per `imac-di-gianluca.tail62c468.ts.net` (riusa)
✅ Token API `tskey-api-...` 90gg validity in `.env`
✅ Device `imac-di-gianluca` IP 100.76.180.78 ONLINE su Tailscale.app GUI

🐛 **Bug irrecuperabile S155-bis**: GUI Tailscale.app network extension non persiste serve/funnel config dal CLI socket. Versione 1.96.5 capped per Monterey 12.7.4. Soluzione: bypass GUI, usa `tailscaled` open-source standalone.

---

## 2. Phase 1 — Decisione esplicita switch architettura (~2min)

**AskUserQuestion** a Luke (one-shot conferma):

> "Confermi switch architetturale: disinstallare Tailscale.app GUI dall'iMac e installare `tailscaled` open-source standalone come launchd daemon? Setup ~60min autonomo, reversibile (re-install GUI app possibile). Procedo? [Sì / No / Pause]"

🛑 Se "No" o "Pause" → STOP, aggiorna HANDOFF, exit.

---

## 3. Phase 2 — Un-enroll GUI Tailscale.app (~5min)

Approccio NON distruttivo: prima logout pulito, poi eventualmente quit. Mantenere `.app` installato come fallback.

```bash
ssh gianlucadistasi@192.168.1.2 'TS=/Applications/Tailscale.app/Contents/MacOS/Tailscale
echo "=== status pre ==="
$TS status 2>&1 | head -3

echo "=== logout ==="
$TS logout 2>&1
sleep 3

echo "=== status post-logout ==="
$TS status 2>&1 | head -3'
```

✅ Atteso: device `imac-di-gianluca` rimosso da tailnet attivi (verifica via API).

```bash
TS_TOKEN=$(grep ^TAILSCALE_API_TOKEN .env | cut -d= -f2- | tr -d '"')
curl -s "https://api.tailscale.com/api/v2/tailnet/-/devices" -u "${TS_TOKEN}:" | \
  python3 -c "import sys,json; [print(d['name'], d.get('lastSeen','?')[:19]) for d in json.load(sys.stdin)['devices'] if 'imac' in d['name'].lower()]"
```

Se device offline (lastSeen più di 1m fa) → eliminare via API per evitare suffix `-1` al re-enroll:

```bash
DEV_ID=$(curl -s "https://api.tailscale.com/api/v2/tailnet/-/devices" -u "${TS_TOKEN}:" | \
  python3 -c "import sys,json; [print(d['id']) for d in json.load(sys.stdin)['devices'] if d['name'].startswith('imac-di-gianluca')]" | head -1)
echo "Deleting device: $DEV_ID"
curl -s -w "HTTP %{http_code}\n" -X DELETE "https://api.tailscale.com/api/v2/device/$DEV_ID" -u "${TS_TOKEN}:"
```

---

## 4. Phase 3 — Install tailscaled open-source binary (~15min)

### 4.1 Download binari ufficiali da pkgs.tailscale.com

Tailscale fornisce binari static-linked per macOS amd64 (Monterey supportato).

```bash
ssh gianlucadistasi@192.168.1.2 '
cd /tmp
# Latest stable per Monterey (1.96.x line)
TSVER="1.96.5"
ARCH="amd64"  # iMac Intel; se M1/M2 usa "arm64"
echo "Detecting arch..."
uname -m
# Adjust ARCH se uname -m mostra arm64

curl -fsSLO "https://pkgs.tailscale.com/stable/tailscale_${TSVER}_${ARCH}.tgz"
ls -lh tailscale_${TSVER}_${ARCH}.tgz
tar -xzf tailscale_${TSVER}_${ARCH}.tgz
ls tailscale_${TSVER}_${ARCH}/
'
```

✅ Atteso: directory `/tmp/tailscale_1.96.5_amd64/` con `tailscale` (CLI) + `tailscaled` (daemon) + `systemd/` configs.

### 4.2 Install binari in /usr/local/bin

```bash
ssh gianlucadistasi@192.168.1.2 '
TSVER="1.96.5"
ARCH="amd64"
sudo cp /tmp/tailscale_${TSVER}_${ARCH}/tailscale /usr/local/bin/tailscale-oss
sudo cp /tmp/tailscale_${TSVER}_${ARCH}/tailscaled /usr/local/bin/tailscaled
sudo chmod +x /usr/local/bin/tailscale-oss /usr/local/bin/tailscaled
ls -lh /usr/local/bin/tailscale-oss /usr/local/bin/tailscaled
/usr/local/bin/tailscale-oss version
'
```

⚠️ Nota: rinomino CLI a `tailscale-oss` per non collidere con `/Applications/Tailscale.app/Contents/MacOS/Tailscale` (GUI app fallback).

🔐 **Sudo password**: Luke deve fornirla. Se SSH richiede password interattiva, usare `AskUserQuestion` per chiederla a Luke o configurare sudoers per `gianlucadistasi` su questi 2 path.

---

## 5. Phase 4 — Setup launchd plist per tailscaled (~10min)

### 5.1 Crea state dir

```bash
ssh gianlucadistasi@192.168.1.2 '
sudo mkdir -p /var/lib/tailscale
sudo mkdir -p /var/run/tailscale
sudo chown root:wheel /var/lib/tailscale /var/run/tailscale
sudo chmod 700 /var/lib/tailscale
'
```

### 5.2 Crea launchd plist `/Library/LaunchDaemons/com.tailscale.tailscaled.plist`

```bash
ssh gianlucadistasi@192.168.1.2 'sudo tee /Library/LaunchDaemons/com.tailscale.tailscaled.plist > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tailscale.tailscaled</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/tailscaled</string>
        <string>--state=/var/lib/tailscale/tailscaled.state</string>
        <string>--socket=/var/run/tailscale/tailscaled.sock</string>
        <string>--port=41641</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/tailscaled.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/tailscaled.err.log</string>
</dict>
</plist>
EOF
sudo chown root:wheel /Library/LaunchDaemons/com.tailscale.tailscaled.plist
sudo chmod 644 /Library/LaunchDaemons/com.tailscale.tailscaled.plist
'
```

### 5.3 Load + start daemon

```bash
ssh gianlucadistasi@192.168.1.2 '
sudo launchctl bootstrap system /Library/LaunchDaemons/com.tailscale.tailscaled.plist
sleep 3
sudo launchctl print system/com.tailscale.tailscaled | head -20
ps aux | grep tailscaled | grep -v grep
ls -l /var/run/tailscale/tailscaled.sock
'
```

✅ Atteso: tailscaled running, socket `/var/run/tailscale/tailscaled.sock` esistente.

⚠️ **Coexistenza GUI App**: GUI App ha la sua network extension separata. Se entrambi attivi, possono interferire. Strategia: Quit Tailscale.app dal menu bar (Luke action OR `osascript -e 'tell application "Tailscale" to quit'` via SSH se permesso).

---

## 6. Phase 5 — Re-enroll device via tailscale-oss + auth-key (~5min)

### 6.1 Genera fresh auth-key via API (preauthorized, 1h validity)

```bash
TS_TOKEN=$(grep ^TAILSCALE_API_TOKEN .env | cut -d= -f2- | tr -d '"')
AUTH_KEY=$(curl -s -X POST "https://api.tailscale.com/api/v2/tailnet/-/keys" \
  -u "${TS_TOKEN}:" \
  -H "Content-Type: application/json" \
  -d '{"capabilities":{"devices":{"create":{"reusable":false,"ephemeral":false,"preauthorized":true}}},"expirySeconds":3600,"description":"S155-tris tailscaled standalone"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['key'])")
echo "AUTH_KEY=$AUTH_KEY"
```

### 6.2 Login con tailscaled standalone

```bash
ssh gianlucadistasi@192.168.1.2 "
sudo /usr/local/bin/tailscale-oss --socket=/var/run/tailscale/tailscaled.sock up \
  --authkey=$AUTH_KEY \
  --hostname=imac-di-gianluca \
  --reset
sleep 5
sudo /usr/local/bin/tailscale-oss --socket=/var/run/tailscale/tailscaled.sock status | head -5
"
```

✅ Atteso: device `imac-di-gianluca` ONLINE con IP 100.x.x.x. Verificare nome via API non abbia suffix `-1` (se sì → cleanup naming come fatto S155-bis).

---

## 7. Phase 6 — Set funnel via tailscaled standalone (~5min)

### 7.1 Genera cert (riusa Let's Encrypt esistente o ne emette nuovo)

```bash
ssh gianlucadistasi@192.168.1.2 '
sudo /usr/local/bin/tailscale-oss --socket=/var/run/tailscale/tailscaled.sock cert imac-di-gianluca.tail62c468.ts.net 2>&1 | tail -5
'
```

### 7.2 Set funnel + verifica persistence

```bash
ssh gianlucadistasi@192.168.1.2 '
sudo /usr/local/bin/tailscale-oss --socket=/var/run/tailscale/tailscaled.sock funnel --bg 9191 2>&1
sleep 3
echo "=== status ==="
sudo /usr/local/bin/tailscale-oss --socket=/var/run/tailscale/tailscaled.sock funnel status 2>&1
echo "=== json ==="
sudo /usr/local/bin/tailscale-oss --socket=/var/run/tailscale/tailscaled.sock funnel status --json 2>&1
'
```

✅ **CRITICAL**: status NON deve essere empty `{}`. Deve mostrare `https://imac-di-gianluca.tail62c468.ts.net/ → http://127.0.0.1:9191`.

### 7.3 Smoke external definitivo

```bash
echo "=== DNS @1.1.1.1 ==="
dig +short @1.1.1.1 imac-di-gianluca.tail62c468.ts.net
echo "=== DNS @8.8.8.8 ==="
dig +short @8.8.8.8 imac-di-gianluca.tail62c468.ts.net
echo "=== external curl (THE TEST) ==="
curl -s -m 15 -w "\nHTTP %{http_code}\n" https://imac-di-gianluca.tail62c468.ts.net/status
```

✅ **GREEN GATE**: DNS risolve a ipv4 + curl HTTP 200 con JSON `wa_status: connected` → procedi Phase 7.
🔴 **RED GATE**: STOP. Documenta in BACKLOG. Considera Opzione B (cloudflared) come fallback.

---

## 8. Phase 7 — Update Worker secret (~5min)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise/argos-proxy
echo "https://imac-di-gianluca.tail62c468.ts.net" | npx wrangler secret put WA_DAEMON_URL
npx wrangler secret list | grep WA_DAEMON_URL
```

Worker rilegge il secret a ogni request (no redeploy).

---

## 9. Phase 8 — Smoke E2E step 6+7 fresh contract (~20min)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
URL="https://argos-proxy.gianlucanewtech.workers.dev"
ADMIN=$(grep "^ARGOS_ADMIN_SECRET=" .env | cut -d= -f2- | tr -d '"')

# 1. CREATE
RESP=$(curl -s -X POST "$URL/api/v1/contract/create" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"dealer_id":"DEALER_TEST_FOUNDER_S155c","dealer_name":"Test Founder S155c","dealer_phone":"+393314928901","dealer_email":"gianlucadistasi81@gmail.com","fee_cents":80000}')
ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['contract_id'])")
TOK=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['signature_token'])")
echo "contract_id=$ID token=$TOK"

# 2. SIGN
curl -s -X POST "$URL/api/v1/contract/sign" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOK\",\"signer_name\":\"Test Founder S155c\",\"signature_font\":\"great-vibes\",\"consent_fes\":true}"

# 3. SEND IBAN — GREEN GATE
curl -s -X POST "$URL/api/v1/contract/$ID/send-iban" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" -d '{}'
# ATTESO: wa_sent: TRUE

# 4. MARK PAID
curl -s -X POST "$URL/api/v1/contract/$ID/mark-paid" \
  -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
  -d '{"paid_amount_cents":80000,"payment_bank":"Revolut Test","payment_reference":"ARGOS-S155c"}'
# ATTESO: wa_sent: TRUE
```

### 9.1 Verifiche delivery

```bash
# WA daemon log (entry SEND a 393314928901)
ssh gianlucadistasi@192.168.1.2 'tail -30 /tmp/argos-wa-daemon.log 2>/dev/null | grep -E "send|393314928901"'

# AskUserQuestion a Luke: "Confermi 2 WhatsApp ricevuti su WA Business app (IBAN_SEND + PAYMENT_RECEIVED)?"
```

---

## 10. Phase 9 — Documentation + commit (~15min)

- [ ] Aggiorna `.planning/E2E-SIM-RESULTS.md` con sezione S155-tris (smoke 8/8 verde via tailscaled standalone)
- [ ] Aggiorna `HANDOFF.md` STATO CORRENTE → S155-tris CHIUSO VERDE
- [ ] Aggiorna `MEMORY.md` entry "S155-tris tailscaled standalone deployed + smoke E2E 8/8 verde"
- [ ] Aggiorna `BACKLOG.md`:
  - Marca **CF Workers → LAN daemon unreachable** = FIXED S155-tris via tailscaled standalone funnel
  - Marca **Tailscale.app GUI funnel bug** = WORKAROUND tailscaled standalone (root cause non risolto, ma bypass production-ready)
- [ ] Aggiungi sezione **"Ops checklist tailscaled iMac"** a CLAUDE.md o nuovo file `docs/ops/tailscaled-runbook.md`:
  - launchctl bootstrap/bootout
  - log path `/var/log/tailscaled.log`
  - state path `/var/lib/tailscale/tailscaled.state`
  - socket path `/var/run/tailscale/tailscaled.sock`
  - re-auth procedura via API auth-key
- [ ] Commit `feat(s155-tris): tailscaled standalone iMac + WA delivery production-ready via funnel`

---

## 11. Phase 10 — STOP, attendi autorizzazione esplicita Luke per Day 1 reale (NO auto-creation prompt S156)

🛑 **REGOLA FERMA** (memory `feedback_no_live_without_test.md`): smoke E2E TEST_FOUNDER verde NON è trigger automatico per Day 1 reale. NON creare `prompts/s156_*.md` Day 1 dealer reale come step auto-eseguibile.

Day 1 reale (Stile Car o altri) richiede:
1. Sessione separata avviata da Luke con approvazione esplicita ("ora andiamo live con X dealer")
2. Test interattivo CON Luke (Luke vede live messaggi + screen) — smoke E2E TEST_FOUNDER simulato NON sostituisce questo passo
3. Daily WA budget verificato disponibile (>=10 messaggi liberi)

**Action S155-tris fine**: chiusura prompt qui. Niente prompt S156 Day 1 reale auto-generato. Luke deciderà sessione successiva quale prossimo step (test interattivo dealer, smoke aggiuntivi, o altro sprint).

---

## 12. Vincoli S155-tris

- ✋ Smoke usa SOLO `+393314928901` (TEST_FOUNDER). NO dealer reale **MAI** in questa sessione.
- ✋ Tailscaled funnel persistence è gate critico: se Phase 6 fallisce, STOP, fallback Opzione B.
- ✋ Daily WA limit: 15. Smoke consuma 2.
- ✋ Sudo richiesto: se SSH non ha sudoers, AskUserQuestion a Luke per password OR escalation manuale.
- ✋ Coexistenza Tailscale.app GUI: Quit prima di tailscaled startup (evita doppio routing).
- ✋ **NO Day 1 reale**: niente messaggi a numeri ≠ `393314928901`, niente prompt auto-generato `s156_day1_*`.

---

## 13. Out of scope S155-tris

- Day 1 reale (richiede sessione successiva con autorizzazione esplicita Luke)
- Generazione prompt S156 Day 1 dealer reale (NO auto-creation)
- Apertura P.IVA (defer)
- Stripe / Fintecture / Revolut Business (rimossi)
- Custom domain Worker proxy (M3+)
- Update macOS Monterey → Ventura/Sonoma (defer, evaluate impact PM2/wa-daemon/Python/Node prima)

---

## 14. Target di fine S155-tris

✅ `tailscaled` open-source standalone running su iMac via launchd persistente
✅ Funnel attivo, `funnel status` non-empty, DNS pubblico risolve, curl esterno HTTP 200
✅ Worker secret `WA_DAEMON_URL` aggiornato
✅ Smoke E2E 8/8 verde con `wa_sent: true` su step 6 + 7
✅ Luke conferma 2 WhatsApp ricevuti (IBAN_SEND + PAYMENT_RECEIVED)
✅ Docs aggiornati: HANDOFF, MEMORY, BACKLOG, E2E-SIM-RESULTS, runbook tailscaled
✅ Commit `feat(s155-tris)` pushato
✅ HANDOFF segnala "S155-tris CHIUSO VERDE — in attesa decisione Luke per next sprint (test interattivo dealer / altro)"

❌ NON in S155-tris: Day 1 reale, prompt S156 auto-generato, P.IVA, Stripe, custom domain Worker, OS upgrade

---

## 15. Risk register S155-tris

| Risk | Probabilità | Impact | Mitigation |
|------|-------------|--------|------------|
| Sudo password non disponibile via SSH | Media | Alta | AskUserQuestion a Luke per pwd OR `sudo visudo` config NOPASSWD per binari Tailscale |
| Coexistenza GUI App + standalone causa routing duplicato | Media | Media | Quit Tailscale.app prima del bootstrap launchd; opzionale `mv /Applications/Tailscale.app /Applications/Tailscale.app.disabled` |
| Cert Let's Encrypt re-emit fallisce (rate limit) | Bassa | Media | Cert già provisioned in S155 PARTIAL, riusa esistente. Se nuovo: rate limit 50/week/domain (ampio margine) |
| Tailscaled binary download fallisce | Bassa | Bassa | URL `pkgs.tailscale.com` stabile da anni; fallback download manuale + scp |
| Funnel ANCHE su tailscaled non funziona | Bassa | Alta | Allora bug è control plane Tailscale lato account/tailnet → fallback Opzione B cloudflared |
| Worker secret update fallisce auth wrangler | Bassa | Bassa | Re-auth `npx wrangler login` se token expired |

---

## 16. Resume path se compaction durante S155-tris

Stato sarà tracciato in tasks Claude (TaskCreate da Phase 1). Se compaction:
1. Leggi questa entry + ultima entry MEMORY.md S155-tris
2. Verifica fase corrente con `ssh gianlucadistasi@192.168.1.2 "ps aux | grep tailscaled | grep -v grep"` (running?)
3. Se daemon attivo + funnel set → procedi Phase 7+ (Worker secret + smoke E2E)
4. Se daemon NOT attivo → riprendi da Phase 4 (launchd plist)
