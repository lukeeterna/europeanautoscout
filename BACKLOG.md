# Backlog — problemi trovati ma non nel sprint corrente

<!-- Aggiungi qui durante lo sprint. Non risolvere ora. -->

## S176-finalize 2026-05-16 — Findings collaterali (priorità ordinata)

### 🔴 PRIORITÀ 1 — S177 contract intent (BLOCKER primo deal E2E)
Classifier AMBRA non gestisce intent CONTRACT_REQUEST. Pipeline reactive si ferma a info-broker loop dopo dossier accept. Resume: `prompts/s177_contract_intent_implementation.md`. **PRIMA di S178 sanitizer**.

### 🟠 PRIORITÀ 2 — S178 sanitizer refactor D-32 (BLOCKER Day 1 reale)
LaMa→Pillow rectangle solid (D-25 violazione). Targa scomparsa + paraurti deformato in regression test S176. Senza fix = primo dealer reale vede foto distorte = trust kill. **Dopo S177 verde**.

### 🟡 PRIORITÀ 3 — UX direzione TEST_FOUNDER reactive
In tutti prompt futuri esplicitare: TEST_FOUNDER reactive = SIM `3314928901` → SIM `3281536308`. Direzione invertita = daemon filtra come auto-eco. S176-finalize ha perso 15min su questo.

### ✅ PRIORITÀ 4 — `current_step` non si aggiorna dopo PDF send (RISOLTO S177a 2026-05-16)
Daemon `wa-daemon.js` `/send-doc` patch in-place iMac: post-send UPDATE `conversations.current_step='DOSSIER_SENT'` se era `DAY1_SENT`/`DAY3_SENT`. Backup `wa-daemon.js.s177a_bak`. Restart pulito 18:11. Smoke test fisico differito S177b primo `/send-doc` reale.

### 🔴 PRIORITÀ 4-bis NUOVA — HITL LLM_MULTI bypass strutturale (D-07 violation)
`pending_replies.reply_e9be3ac6` ha `approved=0` MA `sent=1` con 2 OUTBOUND messaggi delivered TEST_FOUNDER 17:57:44/48 (reply hallucinata mai approvata). Schema NON ha `approved_ts` né `sent_at` (solo `approved`, `sent`). `wa-daemon.js pollBridgeOutbound` legge da `bridge_outbound` (table diversa) con `approved_ts IS NOT NULL` — quindi reply LLM_MULTI NON viene da quella pipeline. Sospetti path auto-send: (a) `telegram-handler.py:171` esegue UPDATE sent=1 post Telegram approve, (b) embedded subprocess in response-analyzer.py:1684 `c.execute('UPDATE pending_replies SET sent=1 WHERE id=?', [task['reply_id']])`. Per dealer reale = un dealer riceve hallucination senza HITL gate. **FIX URGENTE pre-Day 1 reale Stile Car**. Audit completo path subprocess in S177b o S177-bis-hitl.

### 🟠 PRIORITÀ 4-ter NUOVA — Worker `/api/v1/contract/create` 401 INVALID_TOKEN
Endpoint Cloudflare `https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/create` rifiuta `X-API-Key: $ARGOS_API_KEY` (token presente in `.env` iMac). Test S164 aveva creato contract via questo path → o token ruotato o auth method cambiato. Verifica `wrangler.toml` Worker env binding + path autenticazione (Bearer?). Necessario per S177b classifier handler che chiama questo endpoint.

### ⚪ PRIORITÀ 5 — D-31 dossier 12 sezioni
PDF S176 = 3 pagine vs D-18 12 sezioni. Gap analysis deferred S179+.

### ⚪ PRIORITÀ 6 — iMac branch divergence
`main` HEAD `fd35965e` history-rewrite vs `origin/master`. Risolvere prima di prossimo deploy esteso.



## S174 — Classifier substring bug (false-positive `passat` in `passato`)

`wa-intelligence/response-analyzer.py` line 1136 — keyword list VEHICLE_REQUEST contiene `passat` come exact match ma classifier usa substring scan (line 1306 area `keyword_mixed_intent`). Messaggio "il cliente che è passato da me" → matcha `passat` → routato VEHICLE_REQUEST → template VEHICLE_PROPOSAL servito → LLM bypassed.

Impatto: dealer Layer 3 post-handoff che racconta storia cliente (vocabolario naturale "passato/è venuto/è stato qui") finiscono in template invece di LLM identity_post_handoff. Risposta scriptata BMW/Mercedes/Audi.

Fix candidato: word boundary regex `\bpassat\b` invece di substring, OR sostituire `passat` con `vw passat`/`volkswagen passat` per disambiguare. Stessa famiglia tutti gli "exact" keyword di VEHICLE_REQUEST con frammenti corti (`golf`, `t-roc`).

Defer: non blocca S175 mystery shopper (test parlerà di auto specifiche, non storie cliente). Da affrontare post primo deal.

## ✅ FIXED S171 — wa-daemon duplicate sends + retry loop su permanent error

**Risolto 2026-05-15**: `wa-intelligence/wa-daemon.js` `pollBridgeOutbound()` patch atomica.

**Root cause (cumulativa)**:
- (Bug A) Error path linea 305 aggiornava `sent_status` ma NON `sent_ts` → row con errore permanente (es. Auto Carfora "No LID for user") re-pollato ogni 30s → 41+ retry confermati nei log iMac 21:05-21:25.
- (Bug B) Poll-then-send-then-update senza lock atomico: `setInterval` può lanciare poll #2 mentre await `sendMessage` di poll #1 ancora in flight → race window duplicate.

**Fix applicato**:
1. Schema migration additive (`processing_ts INTEGER`, `attempt_count INTEGER DEFAULT 0`) idempotente a startup
2. Atomic claim pre-send: UPDATE `processing_ts=now, attempt_count++` WHERE `sent_ts IS NULL AND (processing_ts IS NULL OR processing_ts < now-RECLAIM)` → se `changes===0` skip (concurrent poll)
3. Poll query filtra stale processing + cap attempt_count<3
4. Error path classifica permanent (regex `/No LID|invalid|forbidden|not.found/i`) vs transient → permanent o cap-3 → set `sent_ts=now` terminal (escape loop)
5. Stale reclaim window = max(120s, poll_interval*4)

**Cleanup eseguito**:
- Backup DB e source su iMac (`*.bak_s171`)
- id=5 Auto Carfora marcato `sent_ts=now, sent_status='error_permanent_S171: No LID for user (frozen)'` per fermare retry loop attivo
- better-sqlite3 rebuilt per node 22 (era contro node 20, pm2 --update-env aveva switchato versione)

**Verifica fix**:
- Daemon ONLINE post-restart, schema migration confermata via `.schema bridge_outbound`
- Smoke 3/3 single-send su TEST_FOUNDER → **pending Luke fisico** (vincolo `feedback_test_founder_means_real_interactive.md`)

## fatturazione TD17/18/19: nessun tool emissione (S164 gap critico)

**Trovato S164 2026-05-12**: grep `TD17|TD18|TD19|reverse_charge|fattura|invoice` in tutto codebase → solo menzioni marketing copy (`tools/fee_calculator.py`, `tools/import_checklist.py`, dataset training) e KB session test (`mario_kb_test_session40.py`). **Nessun tool che emette XML SDI / PDF fattura su transazione reale**. `argos-proxy/src/routes/` ha `mark-paid.ts` ma è notifica WA conferma pagamento, NON emissione fattura.

**Implicazione vincolo Luke (`feedback_e2e_full_test_founder_before_day1.md` step 4 "Pagamento: fattura emessa TD17/18/19 corretto")**: step 4 E2E pipeline non chiudibile finché non esiste tool fattura O processo manuale documentato (commercialista che riceve trigger post `mark-paid` e emette fattura entro 15gg per reverse charge intracomunitario).

**Decisione richiesta a Luke**: (a) tool fattura va costruito dentro ARGOS (Fatture in Cloud API / fattura PA XML SDI generator) E2E digitale, oppure (b) processo manuale via commercialista (`mark-paid` worker invia notifica TG + email a commercialista con dati transazione → fattura emessa offline) → gap step 4 risolto a livello processo, non a livello tool.

**File coinvolti se opzione (a)**: nuovo `argos-proxy/src/routes/invoice-emit.ts` o `tools/invoice_generator.py`. Se (b): solo nuovo handler in `mark-paid.ts` o telegram alert dedicato.

## scraper(autoscout24): filtrare slide marketing PRIMA del DB insert (S163.1 follow-up)

Filtra slide marketing AS24 (Premium Selection, Garantie, Wartungsfreiheit, Inzahlungnahme, Finanzierung) PRIMA del DB insert in `vehicle_images`. Fix economico upstream; sanitizer S163.1 è safety net non solution.

**Pattern detect**:
- `image_url` contiene marketing-asset path (es. `/promo/`, `/banner/`, hash AS24 noti per slide stock)
- OR primo OCR Vision restituisce >5 region testo tedesco senza targa/badge BMW
- OR aspect ratio + dominant color → slide bianca con solo overlay testuale

**Razionale**: oggi S163.1 guard salta JPEG <20% size originale post-sanitize, ma è reattivo (richiede full pipeline run + inpaint + ricompress per scartare). Filtro upstream a scraping time = zero cost downstream + DB pulito (no rows da skippare).

**File coinvolti**: `tools/scrapers/autoscout_scraper.py`, `vehicle_images` table.

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

## Scraper "ROTTI" BMW Serie 3/5 + Mercedes GLC/C/E/GLE (CLAUDE.md, ✅ VERIFICATO FALSE-POSITIVE S157)
**Status**: ✅ NON ROTTI — claim CLAUDE.md obsoleto. Verificato S157 (2026-05-05): tutti 6 modelli producono 19-20 listing/run su autoscout24.de con `price_eur`, `km`, `seller_name` tutti popolati. Slug `-(alle)` ritorna HTTP 200. Pipeline E2E BMW Serie 3 → CoVe → PDF in 41s, 2 PROCEED su 16. CLAUDE.md aggiornato a "E2E FUNZIONANTE".

## PDF dossier size 5KB sospetto (rilevato S157, ✅ FIXED S158)
**Status**: ✅ FIXED S158 (2026-05-05). Root cause: `_download_image_to_temp` in `pdf_generator_enterprise.py` non upgradava URL thumbnail AutoScout24 (`/250x188.webp`) a full-res (`/2560x1920.webp`); il filtro `> 30000` byte poi escludeva tutte le immagini 9-22KB. Fix: aggiunto `_upgrade_thumbnail_url()` (replica `image_downloader.PORTAL_IMAGE_UPGRADES`) prima del download. Verifica: BMW Serie 3 PDF 5,289 → **4,161,219 bytes** (4.1MB), Mercedes GLC PDF **4,761,092 bytes** (4.7MB), 6 image XObjects + 6 DCTDecode JPG embedded confermati via raw PDF inspection. Diagnosi completa in `.planning/S158-PDF-DIAGNOSIS.md`.

## Image Sanitizer (PaddleOCR) NON OPERATIVO — leak foto dealer originario (rilevato S158, defer)
**Status**: 🟢 STACK-FIXED S160 (2026-05-11) — combo `opencv-python==4.7.0.72 + numpy<2 + paddleocr 3.5` operativa in `~/.argos-sanitizer-venv/`. `_find_sanitizer_python()` timeout 30s. **Smoke E2E + visual inspection deferred S161** (`prompts/s161_sanitizer_smoke.md`). Day 1 reale Stile Car bloccato fino S161 verde. Dettagli: `.planning/s160_path_c_working_combo.md`.

**Sintomo**: Il PDF generato S158 contiene foto full-res direttamente dal CDN AutoScout24 con watermark/branding del dealer tedesco originario visibili (targhe, numeri telefono, loghi concessionario). Violazione zero-source policy ARGOS — un dealer Sud Italia capisce subito da quale portale arriva l'opportunità.

**Root cause** (nel codice già prima S158):
- `_find_sanitizer_python()` cerca Python con PaddleOCR su `/usr/local/bin/python3.12`, `/usr/bin/python3`, `/usr/local/bin/python3.11` — nessuno lo ha installato sul MacBook
- Quando non trovato, `_sanitize_photo()` (line 1531-1538) ritorna `image_path` (l'immagine RAW originale) senza modifiche
- Il log stampa `[SANITIZER] 6/6 photos sanitized` ma il count include anche le immagini RAW non realmente sanitized → **messaggio fuorviante**

**Pre-esistente**: il bug era già presente in S157 e prima — non visibile perché le immagini non venivano embeddate (Bug S158 sopra). Ora che le full-res vengono embedded correttamente, il problema sanitizer è esposto.

**Cosa fare (defer S158-bis o S159+)**:
1. Setup PaddleOCR: `python3.12 -m pip install paddleocr` o creare venv `~/.argos-sanitizer-venv/`
2. Verificare path candidates in `_find_sanitizer_python()` includano il venv dedicato
3. Smoke re-run: log deve mostrare `[SANITIZER] Using /path (has PaddleOCR)` invece di "No Python with PaddleOCR found"
4. Visual inspection PDF post-fix: targhe blur + watermark dealer originale rimossi
5. **Bonus fix log**: `_sanitize_photo()` deve distinguere "RAW (passthrough)" da "sanitized"; messaggio finale deve riportare numeri reali (es. `0/6 sanitized (PaddleOCR missing) — photos RAW`)

**Implicazione operativa Day 1**: NON inviare PDF S158 a dealer reali finché sanitizer non operativo. PDF dealer-grade in size, ma leak operativo non risolto.
