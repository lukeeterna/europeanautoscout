# Backlog — problemi trovati ma non nel sprint corrente

<!-- Aggiungi qui durante lo sprint. Non risolvere ora. -->

## Gap strutturali (da S130)
- `days_on_market` non recuperabile dai search results — richiede click su detail page
- `vehicle_listings.matched_dealer` = NULL — le due tabelle non sono collegate
- PDF E2E con dati CoVe reali mai completato (immagini sanitizzate OK, dati reali no)

## Architettura avanzata (Phase 3 — dopo 30 messaggi reali)
- L5 LLM-as-judge validator
- `mv_market_insights` view materializzata su CoVe
- Geographic routing Nord/Centro/Sud
- `insight_delta` schema
- SEQ-NOEXIT-BEFORE-DAY21 rule
- Batch generation + digest Telegram 08:00
- `persona_evolution_log`
- GATE-ICP-001 con soglie calibrate empiricamente
- Confidence-gated blending archetipi (0.65-0.85 → top-2 blend)

## CF Workers → LAN daemon unreachable (rilevato S154-ter, PIVOT S155 → Tailscale Funnel, ✅ FIXED S155-tris)
**Status**: ✅ FIXED in S155-tris via `tailscaled` open-source standalone + Tailscale Funnel su iMac. Worker secret `WA_DAEMON_URL` aggiornato a `https://imac-di-gianluca.tail62c468.ts.net`. Smoke E2E TEST_FOUNDER 8/8 verde con `wa_sent:true` confermato (2 WhatsApp delivered, log + visual Luke).

- **Sintomo**: `send-iban` + `mark-paid` ritornano `wa_sent: false`. Worker tail mostra:
  ```
  (error) WA daemon HTTP 403: error code: 1003
  (warn) send-iban WA failed: HTTP 403
  ```
- **Root cause**: `WA_DAEMON_URL=http://192.168.1.2:9191` è IP RFC1918 privato. Cloudflare Workers fetch da edge non può raggiungere LAN. CF gateway risponde con error code 1003 ("Direct IP Access Not Allowed").
- **Già documentato** in `argos-proxy/src/lib/wa-daemon.ts:8-11` come known limitation pre-prod.
- **Decisione S155 PIVOT (€0 + zero domain)**: scartata Opzione A (CF Tunnel) perché Luke non possiede dominio e CF account ha 0 zone DNS (verificato `GET /zones` → `result:[]`). Scartato anche acquisto domain CF Registrar (~€9/anno → viola ZERO COSTI). **Pivot a Tailscale Funnel**: URL stabile `<machine>.<tailnet>.ts.net`, TLS auto, free tier 3 nodes, no domain ownership.
- **Status S155 PARTIAL (2026-05-04 13:30)**:
  - ✅ Tailscale 1.96.5 già installato iMac
  - ✅ Login completato (account `ferretti.argosautomotive@gmail.com`, tailnet `tail62c468.ts.net`)
  - ✅ ACL nodeAttrs `funnel` aggiunto via API (commit token in `.env`)
  - ✅ HTTPS Certs abilitati via API `PATCH /tailnet/-/settings httpsEnabled:true`
  - ✅ Cert Let's Encrypt provisioned (`tailscale cert imac-di-gianluca.tail62c468.ts.net`)
  - 🐛 `tailscale funnel --bg 9191` set OK ma `funnel status` legge `{}` empty in session SSH successive — bug stato sandbox/socket macOS App (vedi sezione sotto)
  - 🟡 Smoke E2E + Worker secret update **deferred S155-bis** (post-reboot Tailscale.app o forced GUI restart)
- **Resume path S155-bis**: `prompts/s155b_funnel_smoke.md`. Token API Tailscale 90 giorni in `.env` come `TAILSCALE_API_TOKEN`.

## Tailscale Funnel `--bg` set ma `status` empty su macOS App (rilevato S155 PARTIAL, CONFERMATO IRRECUPERABILE S155-bis, ✅ WORKAROUND DEPLOYED S155-tris)
**Status**: ✅ WORKAROUND DEPLOYED in S155-tris via switch a `tailscaled` open-source standalone (Homebrew build + launchd). Bug GUI App **non risolto upstream** (struttura macOS Tailscale.app 1.96.x network extension), ma **completamente bypassato** in produzione. Funnel persiste, DNS pubblico risolve, curl HTTP 200 confermato.

**Setup canonical S155-tris**:
- `brew install tailscale` → `/usr/local/bin/{tailscale,tailscaled}` (compile from source con go 1.26.2 dependency, ~10min totali)
- launchd plist `/Library/LaunchDaemons/com.tailscale.tailscaled.plist` (KeepAlive + RunAtLoad, sopravvive reboot)
- Socket dedicato `/var/run/tailscale/tailscaled.sock` (separato da GUI App, no interferenze)
- State `/var/lib/tailscale/tailscaled.state`
- CLI invocation: `sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock <cmd>`
- Runbook completo: `docs/ops/tailscaled-runbook.md`


- **Sintomo**: `tailscale funnel --bg 9191` ritorna "Funnel started and running in the background" + URL. Ma `tailscale funnel status` → `No serve config`. JSON: `{}`. DNS pubblico NXDOMAIN. Cert provisioned ma DNS record AAAA non pubblicato presso control plane.
- **Root cause confermato S155-bis**: bug strutturale Tailscale.app GUI macOS network extension 1.96.x. Network extension daemon non persiste serve/funnel config dal CLI socket bridge. Tailscale 1.96.5 = ultima versione disponibile su macOS Monterey 12.7.4 ([1.98+ richiede Ventura 13+](https://tailscale.com/docs/install/mac)). Update GUI App NON è opzione.
- **Mitigation tentativi falliti S155-bis** (5 retry consecutive identici):
  - ✅ Quit + Relaunch Tailscale.app GUI (eseguito Luke)
  - ✅ Verifica "Allow Incoming Connections" abilitato (no fix da [tailscale#11049](https://github.com/tailscale/tailscale/issues/11049))
  - ✅ Re-auth via API auth-key fresh
  - ✅ Cleanup naming via API DELETE/POST `/name` (rimosso suffix `-1`)
  - ✅ Re-emit cert idempotent
  - ✅ Reset + retry funnel + serve separato
  - ✅ Verifica ACL `nodeAttrs autogroup:member → funnel` propagato
  - ✅ Verifica `httpsEnabled: true` settings
  - Tutti success message ma status sempre `{}` empty + DNS NXDOMAIN + curl HTTP 000
- **Mitigation S155-tris (decisione CTO Opzione A)**: switch a `tailscaled` open-source standalone via launchd plist `/Library/LaunchDaemons/com.tailscale.tailscaled.plist`. Bypass GUI App network extension. Riusa cert+ACL+API token già configurati. Reversibile. Plan completo: `prompts/s155c_tailscaled_standalone.md` (10 phase, ~60-90min autonomo).
- **Plan B se anche standalone fallisce**: switch architettura cloudflared tunnel.
- Priorità: **alta** — blocca smoke E2E end-to-end + Day 1 reale.

## PM2 daemon non resurrect post-reboot iMac (rilevato S155-bis, ✅ FIXED S156)
**Status**: ✅ FIXED in S156 via `pm2 startup launchd` + workaround manuale spostamento plist da `~/Library/LaunchAgents/` a `/Library/LaunchDaemons/`. Reboot test verde alle 18:48: PM2 + argos-wa-daemon + argos-cf-monitor + funnel external auto-restart in <1min senza intervento utente.

- **Sintomo (storico)**: SessionStart hook segnala `WA Daemon: UNREACHABLE`. PM2 daemon era morto, dump.pm2 esistente. `pm2 resurrect` con PATH fix ripristina entrambi processi.
- **Root cause**: PM2 startup script non installato. Reboot iMac ferma daemon e non si ricarica.
- **Fix S156**:
  1. `sudo env PATH=$PATH:/usr/local/bin /Users/gianlucadistasi/.npm-global/lib/node_modules/pm2/bin/pm2 startup launchd -u gianlucadistasi --hp /Users/gianlucadistasi` → genera plist (Label `com.PM2`)
  2. **Workaround pm2 bug**: pm2 mette plist in `~/Library/LaunchAgents/` (user-level) invece di `/Library/LaunchDaemons/` (system-level). Su iMac headless senza auto-login GUI, LaunchAgent NON parte al boot. Soluzione: `sudo mv` a `/Library/LaunchDaemons/` + `sudo chown root:wheel + chmod 644` + `sudo launchctl bootstrap system /Library/LaunchDaemons/pm2.gianlucadistasi.plist`
  3. Cleanup vecchio `~/Library/LaunchAgents/com.argos.pm2.plist` (path `/usr/local/bin/pm2` inesistente, exit 78 storico) → rinominato `.S156-DISABLED`
  4. `pm2 save` → snapshot `~/.pm2/dump.pm2` per resurrect
- **Reboot test S156 (18:46:55 → 18:48:39)**: ping back 16s, SSH back 60s, cascade auto-restart verde in 110s totali — nessun intervento manuale richiesto. argos-wa-daemon + argos-cf-monitor uptime 53s post-reboot, WA daemon connected, funnel external HTTP 200.
- Runbook: `docs/ops/tailscaled-runbook.md` sezione "PM2 startup persistenza".

## Phone format mismatch contract-create ↔ wa-daemon.ts (rilevato S154-bis, FIXED S154-ter)
**Status**: ✅ FIXED in commit `ab938c4` `fix(s154c): normalize phone in wa-daemon.ts`. Sezione mantenuta come reference storica.


- `argos-proxy/src/routes/contract-create.ts:46` regex `^(\+39)?3\d{8,10}$` accetta:
  - `+393314928901` ✅ (`+39` + `3` + 9 digits)
  - `3314928901` ✅ (10 digit national)
  - `393314928901` ❌ (11 digits dopo prima `3` → fuori range {8,10})
- `argos-proxy/src/lib/wa-daemon.ts:27` regex `^\d{11,13}$` accetta:
  - `393314928901` ✅ (12 digits puri)
  - `+393314928901` ❌ (presenza `+` invalida)
  - `3314928901` ❌ (10 digits)
- **Intersezione vuota per TEST_FOUNDER 393314928901 (formato WA standard country+national)**
- Side effect: in send-iban / mark-paid Worker valida prima di chiamare daemon → `wa_sent: false`. Status DB transition OK (best-effort), ma dealer non riceve IBAN_SEND/PAYMENT_RECEIVED su WA.
- **Fix proposto** (3 LOC, send-iban + mark-paid + wa-daemon.ts):
  - In `wa-daemon.ts`: normalizzare con `phone.replace(/\D/g, '')` PRIMA del regex check, passare valore pulito a fetch.
  - Daemon iMac già fa stripping interno (`phone.replace(/[^0-9]/g, '')`), quindi consistente.
- Alternativa (più invasiva): contract-create normalizza phone in formato canonical (393...) prima di INSERT.
- Priorità: **alta** — blocca smoke E2E S154-bis (WA delivery KO), blocca Day 1 reale fino a fix.

## Rate-limit middleware soft-limit per CF isolate spread (rilevato S154-bis)
- `argos-proxy/src/middleware/rate-limit.ts` usa `Map` module-level → buckets per-isolate, non globali.
- Smoke test S154-bis evidenza:
  - 35 GET sequenziali (non sleep) tra le richieste → 35x 200, **0x 429** (CF distribuisce su isolate diversi, ognuno bucket fresh).
  - 100 GET parallel via `xargs -P 50` → **42x 429**, 58x 200 (sotto burst, isolate riusati).
- **Diagnosi**: il middleware funziona come "circuit breaker per single isolate" ma NON come "rate-limit globale per IP". Per ARGOS scale (~100 req/giorno) accettabile come anti-flood layer, NON come hard cap.
- **Fix opzionale** (per quando supera 1k req/min): migrare a Durable Objects o KV con atomic INCR (commento già presente in middleware:8).
- Priorità: **bassa** — soft limit sufficiente, but documentare in PR description e ops runbook.

## Drift architetturale deploy iMac (rilevato S153)
- **Directory `~/Documents/app-antigravity-auto/wa-intelligence/` (legacy) NON è symlink** ma directory standalone con codice obsoleto (mtime drift di ore/giorni vs `current/wa-intelligence/`)
- `deploy/sync.sh` aggiorna SOLO `current/` (symlink to fresh release), NON aggiorna legacy
- PM2 apps (wa-daemon, tg-bot, cf-monitor) sono registrati col path legacy → girano su codice OBSOLETO ad ogni deploy
- Workaround attuale (S153): post-deploy `cp current/wa-intelligence/*.{js,py} wa-intelligence/` per file modificati
- **Fix proposto**: o (a) trasformare legacy in symlink a current/wa-intelligence (richiede pm2 stop/start tutti), o (b) deploy/sync.sh aggiunge step "rsync current → legacy" (più sicuro, no PM2 disruption)
- Priorità: media — bug latente, non critico ma causa silent staleness deployment

## Drift secrets local↔iMac (rilevato S153)
- Root `.env` aveva `TELEGRAM_BOT_TOKEN` revocato (401) mentre iMac `wa-intelligence/.env` aveva token valido
- Nessun fail visibile finché qualcuno usa root .env per script ad-hoc
- **Fix proposto**: definire single source of truth (iMac canonical), root `.env` rigenerato post-deploy via `scp iMac:.../wa-intelligence/.env .env.from-imac` per script local

## Security cleanup .env (post-S153)
- **Rimuovere password Gmail/LinkedIn plain text** dopo switch a App Password IMAP per CF Alert Monitor
  - `GMAIL_PWD=...` e `ARGOS_GMAIL_PWD=...` sostituibili da `GMAIL_FERRETTI_APP_PASSWORD` per IMAP
  - Audit script che leggono `GMAIL_PWD` (grep ricorsivo `wa-intelligence/`, `tools/`) prima di rimuovere
  - Mantenere solo se ancora usata da SMTP/login web automation (in tal caso: switchare anche quelli a App Password)
- **`LINKEDIN_PWD` = stessa password `GMAIL_PWD`**: single-point-of-failure. Cambiare LinkedIn con password dedicata + salvare separatamente. Trapela `.env` → perdi entrambi.
- **Rotazione password Gmail post-S153**: la password attuale è già stata in plain text in `.env` da Sx (commit history può averla esposta se per errore committata). Verificare `git log -p -- .env` non sia mai stata pushata. Se sì → rotation immediata + revoca app password.
- **`VOIP_PASSWORD`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_AI_API_KEY`, `CLOUDFLARE_API_TOKEN`**: già in plain text — accettabile per ora (sono token revocabili, non password account), ma considerare migrazione a Cloudflare Workers Secrets / macOS Keychain CLI per ridurre file plain text.
- **Backup codes Google**: salvati in [TODO Luke conferma: Apple Note bloccata / cassaforte fisica / password manager]. NON in `.env`, NON in MEMORY.md, NON in repo.

## Miglioramenti scraper
- Scraping periodico AutoScout24.it → `dealer_inventory_snapshots` in DuckDB
- Signal: aged inventory (>90 giorni senza variazioni) come trigger primario
- `days_on_market` via detail page click (richiede Playwright o delay aggiuntivo)
- `mobile_de`: MobileDeScraper non implementa `parse_search_results` (abstract method) — on_demand_runner skips silenziosamente
- `seller_name` ancora NULL per listing DE/NL già esistenti — solo nuovi insert la salvano (fix S131)
- `vehicle_listings.seller_city` non estratta (disponibile in `item.location` su AS24.it)
