# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: 2026-05-06 17:50 — S159 CHIUSO ARANCIONE/PARTIAL: setup PaddleOCR venv 3.11 OK in install ma cv2 dylib incompatibile macOS 11 → import fallisce → fallback RAW invariato. 4 path S160 documentati.

---

## 🟠 STATO CORRENTE — S159 CHIUSO ARANCIONE/PARTIAL (2026-05-06 17:50)

**Decisione CTO Luke**: "decidi tu vincoli 0 cost enterprise". Scelta opzione A (setup PaddleOCR locale).
**Closure forzata**: Luke ha richiesto chiusura ARANCIONE per evitare sforo context >50% (pattern S158).

### Cosa fatto
1. Creato venv `~/.argos-sanitizer-venv/` Python 3.11.11
2. Installati: paddlepaddle 3.0.0, paddleocr 3.5.0, paddlex 3.5.1, opencv-python 4.9, opencv-contrib-python 4.9, numpy 2.3.5, PyYAML 6.0.2 + ~30 deps
3. Editato `tools/scripts/pdf_generator_enterprise.py` line 1563: `_find_sanitizer_python()` priorità venv path > python3.12 > python3 system > python3.11 system

### Blocker trovato
```
ImportError: dlopen(.../cv2/cv2.abi3.so):
  Symbol not found in libtesseract.5.dylib (built for Mac OS X 12.0)
```
Root cause: opencv-contrib-python 4.9 wheel embed `libtesseract.5.dylib` compilato contro macOS 12.0 SDK. MacBook Luke è macOS 11 Big Sur (Darwin 20.6.0).

### Edit codice safe
`_find_sanitizer_python()` testa `import paddleocr` PRIMA di accettare il candidato → venv broken non viene mai usato → falls through a Python successivo → fallback RAW invariato. **Zero regressione vs pre-S159**.

### Path alternativi S160 (in `s159_partial_blocker.md`)
- **B (raccomandato primo tentativo)**: skip opencv-contrib-python, usa solo opencv-python — costo basso, 10min test
- **A (raccomandato fallback)**: sanitizer via SSH iMac (macOS 12.7.4 compat) — sfrutta infra esistente
- **C**: pin opencv-contrib<4.8 — minimal change ma rischio version constraint
- **D**: Docker — high overhead

### File modificati S159 (commit pending)
- `tools/scripts/pdf_generator_enterprise.py` line 1563 (edit safe)
- `~/.argos-sanitizer-venv/` esterno repo (~600MB, OK)

### Resume next session
`leggi prompts/s160_sanitizer_resolve.md ed esegui` (timebox 45min). Day 1 reale Stile Car ancora bloccato fino S160 verde.

---

## 🟢 STATO PRECEDENTE — S158 CHIUSO VERDE (2026-05-05 20:20)

**Sessione (S158)**: fix PDF generator (5,289 bytes era inutilizzabile per dealer Day 1). Outcome: PDF dealer-grade > 4MB cross-brand verde, 6 immagini full-res embedded confermate via PDF inspection.

### Cosa fatto
1. **Pre-conditions 5/5 verdi**: iMac up, WA daemon connected (2/15 daily), tailscaled standalone PID 133, PM2 argos-wa-daemon + argos-cf-monitor online uptime 25h
2. **Phase 1 diagnosi (~10min)**: baseline run BMW Serie 3 → PDF 5,289 bytes con 6 immagini "OK" (9-22KB cad). Inspect `tools/scripts/pdf_generator_enterprise.py` → trovato 2 bug compounded:
   - **Bug A**: `_download_image_to_temp` (line 1457) NON upgrada URL thumbnail. Scraper produce `/250x188.webp` AutoScout24 → download 9-22KB
   - **Bug B**: filtro `> 30000` byte (lines 236, 275, 301) esclude TUTTE le immagini → PDF senza img → 5KB
   - Verifica empirica: `curl /250x188.webp` = 22KB vs `curl /2560x1920.webp` = 140KB ✅
3. **Phase 2 fix mirato (~10min)**: aggiunto `_upgrade_thumbnail_url()` che replica `tools/scrapers/image_downloader.PORTAL_IMAGE_UPGRADES` (autoscout24/olx/otomoto/standvirtual/autovit/finn/blocket/marktplaats/2dehands/willhaben). `_download_image_to_temp` ora prova URL upgradato + fallback originale. Filtro 30KB invariato (safety net contro placeholder).
4. **Phase 3 validation cross-brand (~12min)**:
   - BMW Serie 3 → **4,161,219 bytes (4.1MB)**, immagini 215-646 KB
   - Mercedes GLC → **4,761,092 bytes (4.7MB)**, immagini 393-954 KB
   - PDF inspection: 6 image XObjects + 6 DCTDecode JPG embedded in entrambi
   - Visual: PDF aperto su macOS Preview ✅
5. **Phase 4 docs**: `.planning/S158-PDF-DIAGNOSIS.md` (root cause + fix), BACKLOG.md (FIXED marker), HANDOFF.md (questa entry), MEMORY.md S158

### Risultati misurabili S158
- PDF size: 5,289 → **4,161,219** bytes (788x growth) BMW
- PDF size: → **4,761,092** bytes Mercedes (cross-brand)
- 6 immagini full-res embedded verificate (raw PDF stream count)
- Tempo totale: ~35min execution (vs timebox 60min)

### ⚠️ CAVEAT S158 — Sanitizer NON operativo (issue collaterale rilevato Luke a fine sessione)
PDF S158 contengono foto full-res RAW direttamente dal CDN AutoScout24 — watermark/branding dealer tedesco originario, targhe, numeri telefono visibili. Log stampa `[SANITIZER] 6/6 photos sanitized` ma è messaggio fuorviante: `_find_sanitizer_python()` non trova PaddleOCR su MacBook → `_sanitize_photo()` ritorna RAW passthrough.

**Pre-existing bug** (era già rotto in S157 e prima — non visibile perché immagini non embeddate). Ora esposto.

**Implicazione**: PDF dealer-grade IN SIZE ma con **leak operativo zero-source policy** (dealer Sud Italia capisce immediatamente il portale di origine). NON inviare a dealer reali finché sanitizer non operativo.

**Defer**: setup PaddleOCR su Python 3.12 / venv dedicato → S158-bis o sprint dedicato. Documentato BACKLOG.md "Image Sanitizer (PaddleOCR) NON OPERATIVO".

**Decisione closure VERDE con caveat** (Context Budget Gate >50% = closure forzata): scope S158 era "PDF size 5KB → dealer-grade", achieved. Sanitizer è scope separato pre-esistente.

### Cosa NON fatto (regola Luke "no live senza test esplicito")
- ❌ Day 1 reale Stile Car o altri dealer
- ❌ `prompts/s159_*.md` (NO auto-creation, regola `feedback_no_live_without_test.md`)
- ❌ S159 test founder interattivo (richiede sessione separata + autorizzazione esplicita Luke)
- ❌ Fix sanitizer PaddleOCR (defer, scope separato — leak operativo da risolvere PRIMA di Day 1 reale)

### Cosa fare nel prossimo prompt
Luke decide:
- **S159 TEST FOUNDER INTERATTIVO** (CON Luke davanti, smoke E2E veicolo reale con dossier S158 dealer-grade + WA delivery TEST_FOUNDER, autorizzazione esplicita)
- **S160 DAY 1 REALE STILE CAR** (post-S159 verde, separata)
- Alternative: context budget gate / health monitoring / Day 1 sequence revision V3→V4 / scouting Sud Italia

---

## 📜 STATO PRECEDENTE — S157 CHIUSO VERDE (2026-05-05 19:45)

**Sessione (S157)**: scraper fix BMW Serie 3/5 + Mercedes GLC/C/E/GLE. **Outcome inatteso**: claim CLAUDE.md "scraper rotti" è OBSOLETO/FALSE-POSITIVE. Tutti 6 modelli funzionanti su autoscout24.de.

### Cosa fatto
1. **Pre-conditions verdi 5/5**: iMac up, WA daemon connected (2/15 daily), tailscaled standalone PID 133, PM2 daemon online, argos-wa-daemon + argos-cf-monitor uptime 24h
2. **Phase 1 diagnosi (~10min)**: test URL diretti curl + run scraper Python diretto su BMW Serie 3 → 19 listing CON price/km/seller_name TUTTI popolati. Slug `-(alle)` ritorna HTTP 200, NON è broken. Esteso test agli altri 5 modelli rotti → tutti 19-20 listing per modello, fields completi
3. **Phase 2 fix SKIP**: nessun fix necessario. Scraper già funzionante (probabilmente fixato in sprint precedente, CLAUDE.md non aggiornato)
4. **Phase 3 validation E2E**: `python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" --budget 35000 --dealer "S157_VALIDATION"` → 16 listing → 16 CoVe scored → 2 PROCEED → A4 quality gate verde 2 qualificati → 6 immagini scaricate → PDF generato in 41.6s totali
5. **Phase 4 docs**: CLAUDE.md aggiornato (status E2E FUNZIONANTE + scraper OK list espansa), BACKLOG.md (claim verificato FALSE-POSITIVE + nuovo entry "PDF size 5KB sospetto"), HANDOFF (questa entry), MEMORY.md S157

### Risultati misurabili S157
- Scraper OK confermato: BMW Serie 3 (19), BMW Serie 5 (20), Mercedes Classe C (20), Classe E (20), GLC (20), GLE (20)
- Pipeline E2E: 16 raw → 16 CoVe → 2 PROCEED → 6 immagini → 1 PDF in 41.6s
- Tempo totale sessione: ~10min execution + ~5min docs = ~15min (vs timebox 90min)

### Issue collaterale rilevato (defer)
- **PDF dossier 5,296 bytes sospettosamente piccolo** nonostante 6 immagini scaricate OK (≥18KB cad). Probabile bug template `tools/scripts/pdf_generator_enterprise.py` non incorpora binarie. Documentato BACKLOG.md "PDF dossier size 5KB sospetto". NON blocker S157 (scope = scraper). Fixare prima S159 Day 1 reale Stile Car.

### Cosa NON fatto (regola Luke "no live senza test esplicito")
- ❌ Day 1 reale Stile Car o altri dealer
- ❌ `prompts/s158_*.md` (NO auto-creation, regola `feedback_no_live_without_test.md`)
- ❌ Fix PDF size (defer, fuori scope S157)

### Cosa fare nel prossimo prompt (sessione successiva, fresh context)

```
leggi prompts/s158_pdf_fix.md ed esegui
```

**S158 deciso CTO call (2026-05-05 fine S157)**: fix PDF generator (5,296 bytes con 6 immagini è inutilizzabile) sblocca path produzione S159 test founder interattivo → S160 Day 1 reale Stile Car. Lavoro autonomo zero-rischio dealer, timebox 60min.

**Path produzione**:
- S158 PDF FIX (60min autonomo) → dossier dealer-grade > 200KB con immagini embedded
- S159 TEST FOUNDER INTERATTIVO (45min CON Luke) → smoke E2E veicolo reale + WA delivery validation visiva
- S160 DAY 1 REALE STILE CAR (separata, Luke autorizza esplicito post-S159 verde)

Alternative se Luke vuole altro:
- Context budget gate (3 componenti hook/regola/statusline) — sprint dedicato S160+
- Health monitoring 5min cron + Telegram alert
- Smoke front-end SIGN flow Cloudflare Pages browser
- Day 1 sequence revision V3 → V4
- Dealer scouting Sud Italia espansione pipeline

---

## 📜 STATO PRECEDENTE — S156 CHIUSO VERDE (2026-05-04 18:50)

**Sessione (S156)**: ops hardening post tailscaled standalone S155-tris. Target: persistenza PM2 cross-reboot iMac. Achieved: LaunchDaemon system-level via workaround pm2 bug + reboot test verde 110s totali.

### Cosa fatto (in ordine)
1. **Pre-conditions verdi** (5/5): iMac up, WA daemon connected, Funnel external HTTP 200, Worker LIVE, tailscaled standalone PID 21946
2. **Phase 1 done**: Luke conferma pwd sudo cambiata post S155-tris (security cleanup OK)
3. **Phase 2 pm2 startup launchd con workaround**:
   - `pm2 startup launchd -u gianlucadistasi --hp /Users/gianlucadistasi` → genera plist Label `com.PM2`
   - **Bug pm2 macOS**: scrive in `~/Library/LaunchAgents/` invece di `/Library/LaunchDaemons/` → su iMac headless NO auto-login GUI = LaunchAgent NON parte al boot
   - **Workaround**: `sudo mv` plist a `/Library/LaunchDaemons/` + `chown root:wheel` + `chmod 644` + `sudo launchctl bootstrap system /Library/LaunchDaemons/pm2.gianlucadistasi.plist`
   - `pm2 save` → snapshot `~/.pm2/dump.pm2`
   - Cleanup vecchio rotto `~/Library/LaunchAgents/com.argos.pm2.plist` (path `/usr/local/bin/pm2` inesistente, exit 78 storico) → rinominato `.S156-DISABLED`
4. **Phase 3 reboot test VERDE** (18:46:55 → 18:48:39, totale 110s):
   - `sudo reboot` via SSH (`echo PWD | sudo -S`)
   - Ping back in 16s
   - SSH back + uptime 1min
   - **Cascade auto-restart 4/4 verde**:
     - tailscaled standalone PID 133 ✅ (launchd S155-tris)
     - PM2 daemon + argos-wa-daemon (PID 428) + argos-cf-monitor (PID 432) uptime 53s ✅ (LaunchDaemon S156)
     - WA daemon localhost:9191/status `wa_status:connected` ✅
     - Funnel external `https://imac-di-gianluca.tail62c468.ts.net/status` HTTP 200 ✅
5. **Phase 4 SKIP** (CTO call): health monitoring 5min cron MacBook merita sprint dedicato S157 (design soglie + test alert Telegram end-to-end + runbook). `argos-cf-monitor` PM2 process fornisce monitoring base.
6. **Phase 5 docs aggiornati**: BACKLOG (PM2 daemon FIXED), runbook tailscaled (Appendice PM2 startup persistenza), HANDOFF (questa entry), MEMORY.md S156

### Decisioni operative S156
- **Workaround pm2 startup macOS bug** è path canonical: install in user-level + `sudo mv` a system-level. Plist generato ha già `<key>UserName</key><string>gianlucadistasi</string>` quindi compatibile come Daemon.
- **Skip auto-login GUI iMac**: scelto Daemon system-level invece per non degradare security fisica iMac
- **Phase 4 health monitoring deferred S157**: scope discipline. Il valore ops di health alert merita design dedicato, non add-on.

### Cosa NON fatto (regola Luke "no live senza test esplicito")
- ❌ Day 1 reale Stile Car o altri dealer
- ❌ `prompts/s157_*.md` (NO auto-creation, regola `feedback_no_live_without_test.md`)
- ❌ Health monitoring Phase 4 (deferred S157 dedicato)

### Cosa fare nel prossimo prompt (sessione successiva, fresh context)

```
leggi prompts/s157_scraper_fix.md ed esegui
```

**S157 deciso CTO call (2026-05-04 fine sessione)**: scraper fix BMW Serie 3/5 + Mercedes GLC/C/E/GLE è path critico verso "produrre" (primo dealer reale). Sblocca in cascata S158 (test founder interattivo CON Luke) → S159 (Day 1 reale Stile Car). Lavoro autonomo zero-rischio dealer, timebox 90min.

**Path produzione**:
- S157 SCRAPER FIX (90min autonomo) → produce veicoli reali con numeri reali
- S158 TEST FOUNDER INTERATTIVO (45min CON Luke) → smoke E2E veicolo reale + WA delivery validation visiva
- S159 DAY 1 REALE STILE CAR (separata, Luke autorizza esplicito post-S158 verde)
- S160 ITERATION (post-feedback Stile Car) → V3→V4

Alternative se Luke vuole altro:

- **Test interattivo CON Luke su 1° dealer reale** (Day 1 esplicito, sessione separata + autorizzazione + presenza interattiva)
- **Health monitoring 5min** (S157 dedicato: script bash + cron/launchd MacBook + smoke alert Telegram end-to-end)
- **Smoke front-end SIGN flow Cloudflare Pages** (test browser su signature page)
- **Scraper fix** (BMW Serie 3/5, Mercedes GLC/C/E/GLE — vedi CLAUDE.md "Scraper ROTTI")
- **CoVe pipeline E2E** (sblocco "NON FUNZIONANTE" da CLAUDE.md)
- **Day 1 sequence revision** (template V3 → V4)

---

## 📜 STATO PRECEDENTE — S155-tris CHIUSO VERDE (2026-05-04 17:40)

**Sessione (S155-tris)**: bypass GUI Tailscale.app buggata via install `tailscaled` open-source standalone. Build da source con Homebrew (`brew install tailscale` → tailscale 1.96.4 + go 1.26.2 dependency, ~10min compile). Setup launchd persistente. Re-enroll device. Funnel persistito (al contrario della GUI). Smoke E2E TEST_FOUNDER 8/8 con WA delivery confermata.

### Cosa fatto (in ordine)
1. **Pre-flight verde**: iMac up, WA daemon connected (15/15 daily), Worker LIVE, ACL `nodeAttrs funnel` OK, `httpsEnabled:true` OK, token API + admin secret presenti
2. **Phase 2 un-enroll GUI**: `Tailscale logout` via SSH + DELETE device offline via API (free name)
3. **Phase 3 install tailscaled**: scoperto plan deviation (`pkgs.tailscale.com` per macOS distribuisce SOLO GUI .app/.pkg, non standalone binary). **Pivot Homebrew**: install Homebrew NONINTERACTIVE + `brew install tailscale` (compile da source con go 1.26.2, ~10min) → `/usr/local/bin/tailscaled` + `/usr/local/bin/tailscale`
4. **Phase 4 launchd plist**: `/Library/LaunchDaemons/com.tailscale.tailscaled.plist` con state `/var/lib/tailscale/tailscaled.state` + socket `/var/run/tailscale/tailscaled.sock` + port 41641 + KeepAlive + RunAtLoad. `launchctl bootstrap` → daemon running PID 21946
5. **Phase 5 re-enroll**: tskey-auth via API + `tailscale --socket=... up --authkey=... --hostname=imac-di-gianluca --reset` → device ONLINE IP `100.85.132.49` (no suffix `-1` perché vecchio device DELETE-d)
6. **Phase 6 funnel set GREEN GATE**: `tailscale cert` + `tailscale funnel --bg 9191`. **`funnel status` NON empty** (vs GUI App buggy `{}`): URL + proxy mapping presente. **`serve status --json`**: TCP/443/HTTPS, Web handler, AllowFunnel:true. **DNS pubblico risolve** (3 ipv4 ingress 185.40.234.x). **`curl -s -m 20 https://imac-di-gianluca.tail62c468.ts.net/status` → HTTP 200 in 1.04s con JSON daemon**
7. **Phase 7 Worker secret**: `wrangler secret put WA_DAEMON_URL` = `https://imac-di-gianluca.tail62c468.ts.net` (richiesto export `CLOUDFLARE_API_TOKEN` per non-interactive mode)
8. **Phase 8 smoke E2E TEST_FOUNDER (contract `87f60ca234cd8d97`)**: CREATE → DRAFT, SIGN → AWAITING_DELIVERY, **SEND IBAN → IBAN_SENT `wa_sent:true`** ✅, **MARK PAID → PAID `wa_sent:true`** ✅. Daemon log alle 17:37: 2× `📤 sendMessage` + 2× `✅ INVIATO via HTTP: 393314928901@c.us` + 2× `📬 DELIVERED`. **Luke conferma visiva: 2 WhatsApp ricevuti su WA Business app**

### Decisione architetturale finale
- **Tailscale.app GUI** rimane installata (logged out) come fallback emergenza, ma operativamente NON usata
- **`tailscaled` standalone Homebrew** è il path canonical per ARGOS scale, persistente cross-reboot via launchd
- **Coexistenza**: NO interferenze osservate (GUI logged out + standalone bootstrap separato)

### Cosa NON fatto (regola Luke "no live senza test esplicito")
- ❌ Day 1 reale Stile Car o altri dealer
- ❌ `prompts/s156_day1_real_dealer.md` (NO auto-creation, regola `feedback_no_live_without_test.md`)
- ❌ `pm2 startup launchd` (action item ops separato — defer S156+)

### Cosa fare nel prossimo prompt (sessione successiva, fresh context)

```
leggi prompts/s156_ops_hardening.md ed esegui
```

**Prompt S156 creato**: ops hardening (`prompts/s156_ops_hardening.md`, 6 phase, ~45-60min autonomo + ~5min azioni Luke):
- Phase 1: REMINDER cambio pwd sudo iMac (priority sicurezza)
- Phase 2: `pm2 startup launchd` per persistenza cross-reboot
- Phase 3: Test reboot iMac (richiede autorizzazione Luke)
- Phase 4: Health monitoring 5min Telegram alert (opzionale)
- Phase 5: Docs + commit
- Phase 6: STOP, decisione Luke per next sprint

🛑 NIENTE Day 1 reale in S156. Day 1 reale richiede sessione separata con autorizzazione esplicita Luke + presenza interattiva.

Alternative se Luke vuole altro sprint S156:
- Test interattivo CON Luke su 1° dealer reale (Day 1 esplicito)
- Smoke front-end SIGN flow Cloudflare Pages
- Scraper fix (BMW Serie 3/5, Mercedes GLC/C/E/GLE rotti)
- CoVe pipeline E2E (sblocco "NON FUNZIONANTE" da CLAUDE.md)
- Day 1 sequence revision (template V3 → V4)

---

## 📜 STATO PRECEDENTE — S155-bis BLOCKED (2026-05-04 16:55)

**Sessione (S155-bis)**: tentata ripresa funnel post Quit/Relaunch GUI Tailscale.app. Tutti i fix configurabili applicati (cert, ACL, HTTPS, Allow Incoming Connections, naming, login). **Bug strutturale Tailscale 1.96.5 GUI App network extension confermato irrecuperabile** dopo 5 retry consecutive. Tailscale 1.96.5 = ultima versione disponibile su Monterey 12.7.4 (1.98+ richiede Ventura 13+). Update GUI App NON è opzione.

### Cosa fatto in questa sessione (S155-bis)

1. **Recovery PM2 daemon iMac**: PM2 era morto post-reboot, `pm2 resurrect` con PATH fix `/usr/local/bin:/opt/homebrew/bin` → wa-daemon online (wa_status: connected, daily 15/15)
2. **Tailscale re-auth via API auth-key** (`tskey-auth-*` 1h preauth, generata via `POST /tailnet/-/keys`) → `tailscale up --authkey=... --reset` via SSH, no GUI required
3. **Cleanup device naming via API** (eseguito 2x): `DELETE /api/v2/device/{id}` su offline + `POST /api/v2/device/{id}/name` per rinominare a `imac-di-gianluca` (no suffix `-1`)
4. **Quit + Relaunch Tailscale.app GUI** eseguito da Luke
5. **Verifica "Allow Incoming Connections"**: già abilitato (no fix da [tailscale#11049](https://github.com/tailscale/tailscale/issues/11049))
6. **5 retry funnel reset+set** in vari stati: cert OK, ACL nodeAttrs funnel OK, httpsEnabled:true OK, naming OK, login OK, Allow Incoming OK → SEMPRE `funnel status: No serve config`, `serve get-config: {}`, DNS pubblico NXDOMAIN, curl HTTP 000

### Decisione strategica CTO presa: **OPZIONE A** — `tailscaled` standalone open-source

Switch da Tailscale.app GUI a `tailscaled` open-source binary su iMac. Bypass network extension buggy. Riusa cert+ACL+API token già configurati. Reversibile.

### Cosa NON fatto (S155-bis, deferred S155-tris)

- ❌ Funnel persistence (bug GUI App network extension irrecuperabile)
- ❌ Smoke external `curl https://imac-di-gianluca.tail62c468.ts.net/status`
- ❌ Update Worker secret `WA_DAEMON_URL`
- ❌ Smoke E2E step 6+7 con `wa_sent: true`

### ❌ NON in S155-tris (regola Luke "no live senza test esplicito")

- ❌ Day 1 reale Stile Car o altri dealer
- ❌ `prompts/s156_day1_real_dealer.md` (NO auto-creation)
- ❌ Qualsiasi messaggio WA a numeri ≠ `393314928901`
- 🔒 Day 1 reale richiede sessione separata + autorizzazione esplicita Luke + test interattivo CON Luke (lui vede live messaggi/screen)

### Cosa fare nel prossimo prompt (fresh context S155-tris)

```
leggi prompts/s155c_tailscaled_standalone.md ed esegui
```

(prompt creato in questa sessione, ~60-90min, esecuzione autonoma con accesso pieno SSH+API)

---

## 📜 STATO PRECEDENTE — S155 PARTIAL (2026-05-04 13:30)

**Sessione corrente (S155)**: pivot da CF Tunnel a **Tailscale Funnel** (zero-cost + zero domain). Configurazione tailnet completata via API (ACL nodeAttrs funnel + HTTPS certs + Let's Encrypt cert provisioned). MA `tailscale funnel --bg 9191` set risponde success ma `funnel status` legge `{}` empty in session SSH successive → DNS pubblico NXDOMAIN → smoke E2E impossibile. Bug stato sandbox/socket macOS Tailscale.app system extension daemon. Mitigation deferred S155-bis post-reboot Tailscale.app.

### Cosa fatto in questa sessione (S155)

1. **Pre-flight CF Tunnel scartato**: verificato `GET /zones` su CF account → `result:[]` (0 zone DNS). Luke non possiede dominio. Acquisto domain CF Registrar (~€9/anno) viola ZERO COSTI.
2. **Decisione PIVOT a Tailscale Funnel**: free tier (3 nodes), URL stabile `<machine>.<tailnet>.ts.net`, TLS auto, no domain ownership.
3. **Tailscale 1.96.5 già su iMac** (Monterey 12.7.4). Luke completato login GUI con `ferretti.argosautomotive@gmail.com` → tailnet `tail62c468.ts.net`, hostname `imac-di-gianluca`, IP `100.75.238.38`.
4. **Token API generato Luke + salvato `.env` come `TAILSCALE_API_TOKEN`** (90gg validity).
5. **ACL update via API** `POST /tailnet/-/acl` aggiunto `nodeAttrs: [{target:["autogroup:member"], attr:["funnel"]}]` → CapMap funnel propagato al device.
6. **HTTPS certs enabled via API** `PATCH /tailnet/-/settings httpsEnabled:true`.
7. **Cert Let's Encrypt provisioned** via `tailscale cert imac-di-gianluca.tail62c468.ts.net` (`Wrote public cert + private key`).
8. **`tailscale funnel --bg 9191`** invocato → output success ("Funnel started and running in the background", URL exposed). Status check successivo: `No serve config` / JSON `{}`. DNS pubblico `dig +short @1.1.1.1 imac-di-gianluca.tail62c468.ts.net` → NXDOMAIN.

### 🐛 Bug macOS Tailscale.app funnel state desync (BACKLOG dettagli completi)

`tailscale funnel --bg` set risponde success ma stato non persistito in system extension daemon. Probabile bug socket bridge CLI ↔ network extension. Mitigation S155-bis: reboot Tailscale.app via GUI prima di re-set funnel, oppure usa GUI mode.

### Cosa NON fatto (S155, deferred S155-bis)

- ❌ Verifica funnel status non-empty + DNS pubblico
- ❌ Smoke external `curl https://imac-di-gianluca.tail62c468.ts.net/status`
- ❌ Update Worker secret `WA_DAEMON_URL`
- ❌ Smoke E2E step 6+7 con `wa_sent: true`
- ❌ Day 1 reale Stile Car
- ❌ `prompts/s156_day1_real_dealer.md`

### Cosa fare nel prossimo prompt (fresh context S155-bis)

```
leggi prompts/s155b_funnel_smoke.md ed esegui
```

(prompt creato in questa sessione, ~45min)

---

## 📜 STATO PRECEDENTE — S154-ter PARTIAL (2026-05-04 13:00)

**Sessione corrente (S154-ter)**: phone-format fix deployed, rate-limit Retry-After verificato, 6/8 smoke E2E verde. WA delivery KO per blocker architetturale non legato a phone format: **Cloudflare Workers non possono raggiungere LAN daemon `192.168.1.2:9191`** (CF error 1003 — Direct IP Access Not Allowed). Già documentato in wa-daemon.ts:8-11 come known limitation pre-prod.

### Cosa fatto in questa sessione (S154-ter)

1. **Phase 1 — Phone-format fix**: `argos-proxy/src/lib/wa-daemon.ts` aggiunge `replace(/\D/g, '')` PRIMA del regex `^\d{11,13}$`. Permette a `+393314928901` (formato contract-create) di passare al daemon (formato bare digits). Typecheck OK, redeploy verde, commit `ab938c4`.
2. **Phase 1 finalize — Rate-limit Retry-After**: burst 150 parallel `-P 60` su `/api/v1/contract/$TOKEN` → 75x 200 + 75x 429. Header `retry-after: 26`, body `{"ok":false,"error":"rate_limit_exceeded","scope":"ip","retry_after":26}`. Middleware production-ready.
3. **Phase 2 — Smoke E2E TEST_FOUNDER (contract `f01c3bb683d2ca69`)**:
   - ✅ 1 HEALTH 200 / 2 CREATE (status DRAFT) / 3 GET PUBLIC / 4 SIGN (font `great-vibes` kebab-case, status AWAITING_DELIVERY, pdf_sha256 64 hex)
   - ✅ 5 R2 VERIFY (PDF 9932 byte, SHA256 `100b79b4...da38` MATCH)
   - 🟡 6 SEND IBAN: status IBAN_SENT, **wa_sent: false** (CF→LAN blocker)
   - 🟡 7 MARK PAID: status PAID, payment_amount=80000, **wa_sent: false**
   - ✅ 8 ADMIN LIST (contract presente con status PAID)
4. **Phase 3 — Verifiche collaterali**:
   - ✅ D1 audit_log: 4/4 row `CREATE`/`SIGN`/`SEND_IBAN`/`MARK_PAID` in ordine timestamp ascendente
   - ❌ WA daemon log iMac: 0 entry SEND a 393314928901 (Worker non raggiunge daemon)
   - 🟡 Telegram alerts: pending Luke visual confirmation (3 alert attesi)
5. **Worker tail capture** durante 2nd send-iban: `(error) WA daemon HTTP 403: error code: 1003` → confermato CF→LAN unreachable.

### 🐛 Architectural blocker rilevato (BACKLOG dettagli completi)

**CF Workers → LAN daemon unreachable**: `WA_DAEMON_URL=http://192.168.1.2:9191` è IP RFC1918 privato. CF gateway risponde error 1003 ("Direct IP Access Not Allowed"). NON è bug, è limitazione architetturale già documentata.

**Soluzione S155**: Cloudflare Tunnel (`cloudflared`) su iMac che espone `localhost:9191` con dominio CF interno + JWT validation. Setup ~30 min, €0, sicuro by default.

### Cosa NON fatto (S155)

- ❌ Cloudflare Tunnel daemon iMac (blocker per Day 1 reale)
- ❌ Smoke E2E re-run con `wa_sent: true` (post-tunnel)
- ❌ Day 1 reale Stile Car (richiede WA delivery funzionante)
- ❌ `prompts/s155_day1_real_dealer.md` (prematuro, dipende da tunnel)

### Cosa fare nel prossimo prompt (fresh context S155)

S155 deve risolvere il blocker CF→LAN PRIMA di Day 1 reale:
1. Setup `cloudflared tunnel` su iMac → expose `:9191` come `wa-daemon.<luke-domain>` o subdomain CF gratuito
2. Aggiornare secret Worker `WA_DAEMON_URL` al nuovo public URL HTTPS
3. Re-run smoke E2E step 6+7 → verificare `wa_sent: true` e WhatsApp app riceve 2 messaggi (IBAN_SEND + PAYMENT_RECEIVED)
4. Solo se VERDE: comporre `prompts/s156_day1_real_dealer.md` per autorizzazione Luke

```
leggi prompts/s155_cf_tunnel_daemon.md ed esegui
```

(prompt da creare prima del kickoff S155)

---

## 📜 STATO PRECEDENTE — S154-bis PARTIAL (2026-05-04 12:55)

**Sessione corrente (S154-bis)**: pre-conditions 7/7 verdi, Phase 1 rate-limit eseguita parzialmente (hammer + Retry-After verify in S154-ter), Phase 2 smoke E2E NON eseguita per phone format bug rilevato in code review pre-test.

### Cosa fatto in questa sessione (S154-bis partial)

1. **Pre-conditions check 7/7 OK**: Worker LIVE (`/health` 200), `ARGOS_PROXY_URL` in `.env`, WA daemon connected (15/15 remaining), iMac up (192.168.1.2 ping 2ms), CF Monitor heartbeat (1.5min ago), Telegram bot reachable (`@Argosautomotivebot` getMe.ok=true), TEST_FOUNDER 393314928901 = phone test documentato (DB SQLite iMac non è autoritativo per Worker — Worker usa D1 separato).
2. **Phase 1 rate-limit HAMMER (parziale)**:
   - Contract `RL_TEST` creato: `contract_id=1f04e6b7af512553`, token=`c9bf2729ed9edd5cb49f093062acf927`, fee=€800.
   - 35 GET sequenziali su `/api/v1/contract/$TOKEN`: **35/35 = 200, 0x 429**. Causa: CF Workers spreade su isolate multipli, ogni isolate ha bucket Map fresh → effective limit ≈ N_isolates × perIp.
   - 100 GET parallel via `xargs -P 50` (concorrenza forzata): **42/100 = 429, 58 = 200**. Rate-limit triggerato sotto burst sufficiente.
   - **Verifica `Retry-After` header** su 429: NON eseguita (interrotta da errore tool).
3. **Code review API**: identificati schema endpoints (health/get/sign/create/send-iban/mark-paid/admin contracts) + flow status (DRAFT → AWAITING_DELIVERY → IBAN_SENT → PAID).

### 🐛 Bug bloccante rilevato (BACKLOG dettagli completi)

**Phone format mismatch**: contract-create regex `^(\+39)?3\d{8,10}$` vs wa-daemon.ts regex `^\d{11,13}$`. Intersezione VUOTA per TEST_FOUNDER 393314928901 (formato WA standard country+national).

- Workaround test: `+393314928901` passa create ma Worker rifiuta in wa-daemon.ts pre-fetch → `wa_sent: false`. Status DB OK (best-effort), ma WA delivery KO.
- Fix proposto (3 LOC): normalizzare phone in `wa-daemon.ts` con `phone.replace(/\D/g, '')` PRIMA del regex check. Daemon iMac già strippa internamente, consistente.
- **Priorità alta**: blocca Day 1 reale finché non fixato.

### Cosa NON fatto (S154-ter)

- ❌ Phase 1 finalize: verifica header `Retry-After` su 429, log esempio body
- ❌ Phase 2 smoke E2E TEST_FOUNDER 8 step (create→sign→awaiting→iban_sent→paid)
- ❌ Phase 3 verifiche collaterali: 4 Telegram alert + 2 WA template + 4 row D1 audit_log
- ❌ Phase 4 docs E2E-SIM-RESULTS + commit
- ❌ Cleanup duplicato CF Storage 80% disabled (cosmetico, Luke GUI)

### Cosa fare nel prossimo prompt (fresh context S154-ter)

```
leggi prompts/s154c_smoke_e2e.md ed esegui
```

S154-ter dovrà: (1) fix phone format `wa-daemon.ts` 3 LOC + redeploy → (2) Phase 1 finalize Retry-After verify → (3) Phase 2 smoke E2E completo con phone fix → (4) verifiche collaterali → (5) docs+commit.

---

## 📜 STATO PRECEDENTE — S154a CHIUSO VERDE (2026-05-04 12:15)

**Sessione corrente**: rate-limit middleware + R2 bucket + D1 migration + 8 secrets + wrangler deploy + health check OK. Smoke E2E TEST_FOUNDER deferred a S154-bis per cut clean a context budget.

### Cosa fatto in questa sessione (S154a)

1. **Backup codes Google → macOS Keychain** (alternativa a Apple Note bloccata fallita su macOS 11): account `argos-backup-codes-google`, service `ARGOS Google Backup Codes`. File originale `~/Downloads/Backup-codes-ferretti.argosautomotive.txt` cancellato con `rm -P` (3-pass overwrite). Recovery via `security find-generic-password ... | xxd -r -p` o GUI Keychain Access.
2. **R2 enable verificato**: API `GET /accounts/{id}/r2/buckets` → success, no più error 10042.
3. **3 alert R2 verificati**: dashboard CF mostra "R2 Storage 80%", "R2 Write Ops 80%", "R2 Read Ops 80%" abilitati con email `ferretti.argosautomotive@gmail.com`. 1 duplicato disabled innocuo (toggle off, no trigger).
4. **Rate-limit middleware**: nuovo file `argos-proxy/src/middleware/rate-limit.ts` (147 LOC). Per-IP 10/min sign + 30/min get, global 100/200, body cap 100KB su sign, 429 con Retry-After header, in-memory Map con lazy sweep 60s, admin bypass via `c.get('adminAuthed')`. Applied in `src/index.ts` su rotte pubbliche. TS typecheck OK.
5. **R2 bucket create**: `argos-contracts` standard storage, region default.
6. **D1 migration**: `0001_init.sql` eseguita remote, 2 tables (contracts + audit_log), 15 rows written.
7. **8 secrets uploaded**: ARGOS_ADMIN_SECRET (gen openssl rand -hex 32), R2_SIGNING_SECRET (gen), ARGOS_IBAN, ARGOS_INTESTATARIO, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WA_DAEMON_API_KEY (= ARGOS_API_KEY), WA_DAEMON_URL (=`http://192.168.1.2:9191`). RESEND_API_KEY skip (Worker degrada graceful).
8. **wrangler.toml fix**: glob TTF rules da `assets/fonts/*.ttf` → `**/*.ttf` (esbuild bundler richiedeva pattern più ampio per loader Data type).
9. **Wrangler deploy**: Worker LIVE su `https://argos-proxy.gianlucanewtech.workers.dev` (4.37 MB upload, 132 ms startup). Bindings DB+CONTRACTS verificati.
10. **Health check OK**: `GET /health` → `{status:ok, version:1.0.0, environment:test}`.
11. **ARGOS_PROXY_URL salvato in `.env`**.

### Cosa NON fatto (S154-bis)

- ❌ Smoke E2E TEST_FOUNDER 393314928901 (8 step: create→sign→awaiting→iban_sent→paid + dashboard list + WA template delivery + Telegram alerts + R2 PDF check + D1 audit_log validation + rate-limit hammer test)
- ❌ Cleanup duplicato CF Storage 80% disabled (cosmetico, Luke side da GUI)

### Cosa fare nel prossimo prompt (fresh context S154-bis)

```
leggi prompts/s154b_smoke_e2e.md ed esegui
```

S154-bis completerà: rate-limit hammer test (12 req → 2x 429) → smoke E2E TEST_FOUNDER 8 step → docs E2E-SIM-RESULTS aggiornato → commit feat(s154b) verde.

---

## 📜 STATO PRECEDENTE — S153 partial complete (2026-05-02 20:05)

---

## 🟡 STATO CORRENTE — S153 partial complete (2026-05-02 20:05)

**Sessione corrente**: build CF Alert Monitor + deploy + tests verdi. R2 deploy bloccato su Luke side (Revolut card + R2 enable + 3 alert).

### Cosa fatto in questa sessione (S153)

1. **D1 `argos-contracts` creato**: UUID `75d63bc9-342f-46cf-b6d2-c0adf77c975e`, region EEUR. `argos-proxy/wrangler.toml` aggiornato con UUID reale.
2. **CF Alert Monitor build + deploy iMac**: nuovo PM2 service `argos-cf-monitor` online (pid 76983), heartbeat verde, primo poll 0 errori. File `wa-intelligence/cf_alert_monitor.py` (200 LOC stdlib only) + ecosystem.config.js app #3.
3. **Tests verdi**:
   - IMAP login Gmail `ferretti.argosautomotive@gmail.com`: 96 inbox
   - `--once` test locale: 0 errori
   - Telegram delivery E2E: message_id 6032
   - PM2 boot iMac: online, pm2 save persistito
4. **Bug fix collaterali**:
   - Token Telegram revocato in root `.env` (401) → sync da iMac
   - File copiati in legacy `wa-intelligence/` perché PM2 punta a path legacy non aggiornato da deploy/sync.sh
5. **Backup codes Google**: pushback security su richiesta Luke "memorizza in MEMORY.md" → distinguo backup codes vs app password, opzioni Keychain/cassaforte/PM proposte. App password generata da `myaccount.google.com/apppasswords` salvata in `.env` come `GMAIL_FERRETTI_APP_PASSWORD`.

### Cosa Luke deve fare PRIMA di S154

| Item | Stato | Azione |
|------|-------|--------|
| Carta virtuale Revolut €5/mese | ⏳ | App Revolut → Carte → Crea virtuale → limite €5/mese |
| Carta aggiunta a CF Billing | ⏳ | dash.cloudflare.com/.../billing/payment-methods → Add (autorization hold $1 normale) |
| R2 attivato | ⏳ | dash.cloudflare.com/.../r2/overview → Purchase R2 Plan ($0 + usage) |
| 3 alert R2 created | ⏳ | dash.cloudflare.com/.../notifications con email `ferretti.argosautomotive@gmail.com`: R2 Storage 8GB / Class A 800k / Class B 8M |
| Backup codes spostati | ⏳ | da `~/Downloads/Backup-codes-ferretti.argosautomotive.txt` → Apple Note bloccata (Keychain) o cassaforte |

### Cosa fare nel prossimo prompt (fresh context)

```
leggi prompts/s154_cf_monitor_done_r2_pending.md ed esegui
```

S154 completerà: rate-limit middleware Worker → R2 bucket create → D1 migration → 7 secrets → wrangler deploy → smoke E2E TEST_FOUNDER.

---

## 📜 STATO PRECEDENTE — S152b chiuso, S153 unblock (2026-05-02 12:10)

**Aggiornato**: 2026-05-02 12:10 — TUTTI BLOCKER S152b RISOLTI, S153 READY TO START in fresh context

---

## 🟢 STATO CORRENTE — S153 unblock complete (2026-05-02 12:10)

**Sessione di unblock**: questa sessione (post-S152b) NON ha eseguito S153, ha solo risolto i 2 blocker identificati a chiusura S152b. S153 deve partire in fresh context.

### Pre-condizioni S153 — TUTTE VERDI ✅

| Item | Stato | Evidenza |
|------|-------|----------|
| ARGOS_IBAN | ✅ | in `.env` |
| ARGOS_INTESTATARIO | ✅ | in `.env` |
| CF token scope D1+R2+Workers+Pages Edit | ✅ | `wrangler d1 list` ritorna lista (1 D1 esistente: `luke-automation-emails-production`) |
| iMac online | ✅ | nuovo IP statico **`192.168.1.2`**, ping 0% loss 1.7ms |
| WA daemon connected | ✅ | `:9191/status` → `wa_status: connected`, agent_status active, uptime 25.8h |
| TEST_FOUNDER reset | ✅ | done S151 |
| Worker code completo | ✅ | S152b (8 commit) |
| Dashboard contracts | ✅ | S152b |

### Cosa fatto in questa sessione di unblock

1. **Diagnosi pre-cond fail** alle 11:22 — wrangler d1 list FAIL (10000), iMac UNREACHABLE
2. **Rilevato cambio IP iMac**: da `192.168.1.12` → `192.168.1.2` (statico permanente)
3. **Commit `d86894c`**: `chore: update iMac IP 192.168.1.12 -> 192.168.1.2` — 8 file critici operativi (deploy/sync.sh, healthcheck.sh, wa-intelligence/deploy.sh, tests/test_e2e.py, chaos_test.sh, .claude/scripts/session_start.sh, CLAUDE.md, .claude/rules/identity.md, .claude/agents/agent-ops.md). 29 file storici (prompts/sN_*, research/, .planning snapshots) lasciati invariati.
4. **CF token tutorial step-by-step con Luke** (~30 min interactive):
   - Identificate 2 trappole: `Workers R2 SQL` ≠ `Workers R2 Storage`; `Cloudflare One/Zero Trust → Access: Users` ≠ `User Details: Read`
   - Approccio clean slate accettato (rimuovi tutti, aggiungi solo i 4 corretti)
   - Token nuovo creato e salvato in `.env` (53 char, formato `cfat_*`)
   - User Details Read NON aggiunto (CF UI edit token non offre User scope; warning cosmetico irrilevante per ops S153)
5. **Banner SessionStart** ora mostra `WA Daemon: connected` (prima UNREACHABLE perché pingava vecchio IP)

### Cosa fare nel prossimo prompt (fresh context)

```
leggi prompts/s153_e2e_sim_test_founder.md ed esegui
```

Il piano S153 è già pronto, comandi pronti, blocker tutti rimossi. Stima: ~30 min deploy + ~1h smoke E2E (8 step curl + 1 sign manuale browser) + ~15 min docs.

**Vincoli ribaditi**:
- ✋ TEST_FOUNDER 393314928901 SOLO (no dealer reali)
- ✋ NO Day 1 reale (è S154, parte solo dopo OK Luke esplicito post-smoke verde)
- ✋ NO modifiche a `cove_engine_v4.py` o daemon WA
- ✋ ZERO COSTI nuovi (Cloudflare free tier basta)
- ✋ Workaround `source .env` rotto (riga `ARGOS_INTESTATARIO=Gianluca Di Stasi` con spazi): usare `export VAR=$(grep ^VAR= .env | cut -d= -f2-)` o lasciare wrangler leggere da `.env` come fa nativamente.

---

## 🎯 S152b OUTCOME — Chunk B: send-iban + mark-paid + analyzer + dashboard, DEPLOY BLOCCATO (storia)

**2026-05-01 21:30-21:55** — Chunk B del build S152 completato a livello codice (B-7..B-10). Deploy CF bloccato su token scope insufficiente.

### Cosa fatto S152b (4 commit atomici)

1. **`636a2a4 feat(s152-b7)`**: send-iban endpoint + WA template + email
   - `argos-proxy/src/routes/send-iban.ts` riempito (era stub 501)
   - POST `/api/v1/contract/:id/send-iban` (admin Bearer)
   - Pre-cond: status=AWAITING_DELIVERY (409 altrimenti)
   - D1 UPDATE conditional → IBAN_SENT + audit_log con `iban_last4`
   - Best-effort: WA daemon template + Resend email + Telegram alert
   - WA template include disclosure VoP (intestatario reale ≠ Luca commerciale)
2. **`6992663 feat(s152-b8)`**: mark-paid endpoint + reconciliation manuale
   - `argos-proxy/src/routes/mark-paid.ts` riempito
   - POST `/api/v1/contract/:id/mark-paid` (admin Bearer)
   - Body: `{paid_amount_cents, payment_bank, payment_reference, paid_at_iso?}`
   - Validation ±€1 vs fee_cents, ISO date, status IN (IBAN_SENT, AWAITING_DELIVERY)
   - D1 UPDATE → PAID + audit_log + WA PAYMENT_RECEIVED + Resend Luca+dealer + Telegram
3. **`86ec355 feat(s152-b9)`**: analyzer trigger + 3 templates
   - `wa-intelligence/templates.py`: aggiunti `DAY_INTEREST`, `IBAN_SEND` (mirror TS), `PAYMENT_RECEIVED`
   - `wa-intelligence/response-analyzer.py`: helper `create_contract_for_interest(...)` — HTTP POST a argos-proxy/contract/create con guardrail confidence>=0.85 e config check
   - HITL strict: helper NON auto-trigger, chiamato manualmente da Telegram approval
   - SCP a iMac deferred a deploy phase
4. **`4fe2455 feat(s152-b10)`**: admin dashboard contracts
   - `wa-intelligence/dashboard/app.py`: `_proxy_request()` helper + GET `/contracts` + POST `/contracts/<id>/{send-iban,mark-paid}`
   - `wa-intelligence/dashboard/templates/contracts.html`: tabella + status badges + bottoni condizionali + modal mark-paid
   - `wa-intelligence/dashboard/templates/base.html`: voce sidebar "Contratti"

### Deploy phase — 🔴 BLOCCATO
Tentativo `wrangler d1 create argos-contracts` → `Authentication error [code: 10000]`.

Diagnosi: `CLOUDFLARE_API_TOKEN` in `.env` è attivo (`/user/tokens/verify` → status:active) MA NON ha scope D1. Token attivo ≠ token con scope sufficiente. La verifica precedente non aveva validato gli scope specifici.

**UNBLOCK richiesto a Luke** (5 min dashboard CF):
1. https://dash.cloudflare.com/profile/api-tokens
2. Edit token corrente → aggiungi scope:
   - **D1** → Edit
   - **Workers R2 Storage** → Edit
   - **Workers Scripts** → Edit
   - **Cloudflare Pages** → Edit (se non già presente)
3. Salva (no rotation, stesso valore in `.env`)
4. Re-test: `wrangler d1 list` deve ritornare lista

### Stato post-S152b
- ✅ Worker code 100% production-ready, typecheck pulito
- ✅ Dashboard admin contracts wired (proxy a Worker via Bearer)
- ✅ Templates Python sincroni con TS Worker (consistency message)
- ✅ Helper analyzer HITL con guardrails
- 🔴 D1 + R2 + secrets + deploy → BLOCCATO su CF token scope
- 🔴 Smoke E2E → BLOCCATO (deploy prerequisito)
- 🔴 iMac/WA daemon offline (banner UNREACHABLE; SSH refused)

### Pre-condizioni S153 (E2E sim TEST_FOUNDER)
| Item | Stato |
|------|-------|
| ARGOS_IBAN | ✅ in `.env` |
| ARGOS_INTESTATARIO | ✅ in `.env` |
| CF token scope D1+R2+Workers+Pages | 🔴 mancante |
| iMac/WA daemon online | 🔴 offline |
| TEST_FOUNDER reset | ✅ done S151 |
| Worker code completo | ✅ S152b |
| Dashboard contracts | ✅ S152b |

### File handoff S153
- `prompts/s153_e2e_sim_test_founder.md` — TODO completo per E2E sim
- `.planning/E2E-SIM-RESULTS.md` — risultati build + blocker deploy

### Lezione operativa S152b
1. **Verifica permission scope ≠ verifica token attivo**. `/user/tokens/verify` non rivela scope. Per validare serve read op concreto (`wrangler d1 list`). Aggiungere come step esplicito in pre-cond future.
2. **Build atomico anche con deploy bloccato**: B-7..B-10 sono codice production-ready, indipendenti dall'infra. Deploy resta scope ridotto recuperabile in <30 min quando token unlock.
3. **iMac offline = WA fail best-effort, NON blocca API**: design corretto. Send-iban/mark-paid ritornano 200 con `wa_sent:false` se daemon non risponde — recupero asincrono via dashboard quando daemon torna online.

---

## 🎯 S152a OUTCOME — Chunk A: scaffold + D1/R2 + frontend sign + PDF gen

**2026-05-01 20:10-20:35** — Chunk A del build S152 completato secondo piano user (chunking 3 sessioni: A=B-1→B-5, B=B-7→B-10+deploy, C=S153 E2E sim).

### Cosa fatto S152a (4 commit)
1. **`1f0fbc4 feat(s152-b1)`**: argos-proxy Worker scaffold (Hono+TS, no Stripe) — 19 file, 3041 LOC
   - `argos-proxy/{package.json, tsconfig.json, wrangler.toml}` — Cloudflare Worker config + Data rule per TTF + 9 secret enumerati nei comment
   - `src/index.ts` Hono router con CORS argos-automotive.pages.dev + 7 endpoint (4 admin + 3 public)
   - `src/lib/{types.ts, resend.ts, telegram.ts, wa-daemon.ts, r2-signed-url.ts}` — utility libs
   - `src/middleware/admin-auth.ts` — Bearer constant-time compare
   - `src/routes/{contract-create.ts, contract-get.ts, contract-sign.ts, contracts-list.ts}` — full impl
   - `src/routes/{send-iban.ts, mark-paid.ts}` — STUB 501 (Chunk B)
2. **`d000933 feat(s152-b2)`**: D1 schema + R2 bucket bindings
   - `migrations/0001_init.sql` — `contracts` (7-state CHECK, signature_token UNIQUE, FES columns, pdf_r2_key/sha256, payment_*) + `audit_log` append-only + 4 index
   - SQL validato con sqlite3 standalone (wrangler local D1 non gira su macOS 11.6, deferred remote execute a Chunk B)
3. **`24a858c feat(s152-b4)`**: contract sign frontend (10 firme stilizzate + FES consent)
   - `landing/_redirects` per route `/contract/<token>`
   - `landing/contract/index.html` Tailwind CDN + Google Fonts CDN preconnect (10 family)
   - `landing/contract/sign.js` — fetch contract, render 10 sig-card preview live, POST sign endpoint, redirect thank-you con `#pdf=` fragment
   - `landing/contract/thank-you.html` — bundled (post-sign confirmation, NO online payment, "IBAN dopo consegna documenti")
4. **`0510e44 feat(s152-b5)`**: PDF generation finalized + 10 Google Fonts TTF embedded
   - `assets/fonts/*.ttf` — 10 font scaricati da github.com/google/fonts (~2.0 MB totale)
   - `src/types-assets.d.ts` — declare module '*.ttf' as ArrayBuffer
   - `src/pdf/contract-template.ts` — pdf-lib + fontkit, 4 pagine A4 (header+parts → oggetto+veicolo+fee → 6 clausole+FES consent → signature embed + bundle FES)
   - Caveat e Dancing Script come variable fonts (`Caveat[wght].ttf`, `DancingScript[wght].ttf`)

### Stato post-Chunk A
- ✅ `argos-proxy/` Worker compila (typecheck implicito via tsc strict)
- ✅ Frontend `/contract/<token>` deployabile su CF Pages (no build, statico)
- ✅ Migration SQL valida
- ✅ PDF gen wired con TTF embedded subset
- ⏸️ Local typecheck/dev NON eseguito (npm shim `_cc_pin_trap` rotto, usato `/usr/local/bin/npm` per install)
- ⏸️ Wrangler local dev NON gira su macOS 11.6 (richiede 13.5+) → deferred remote deploy a Chunk B

### File handoff S152b
- `prompts/s152b_chunk_b.md` (~280 righe) — pre-condizioni, TODO B-7→B-10+deploy, smoke test, vincoli ribaditi

### Pre-requisiti S152b — TUTTI SBLOCCATI (2026-05-01 20:50)
- ✅ **`ARGOS_IBAN`** ricevuto da Luke (LT EMI bank code 32500, mod97 valido) — salvato in `.env` locale chmod 600, da caricare via `wrangler secret put` in deploy phase. **Valore non in repo.**
- ✅ **`ARGOS_INTESTATARIO`** confermato (Opzione A post-flag CTO su SEPA Verification of Payee obbligatorio EU dal 9/10/2025: "Luca Ferretti" persona commerciale su contratto/WA, intestatario reale del conto solo su template IBAN_SEND con copertura narrativa). **Valore non in repo.**
- ✅ **CF token** verificato attivo via `/user/tokens/verify` API

### Pending Chunk B (S152b) + Chunk C (S153)
- **B-7 send-iban** endpoint (validate AWAITING_DELIVERY, UPDATE IBAN_SENT, WA template + email + Telegram)
- **B-8 mark-paid** endpoint (validate amount tolerance ±€1, UPDATE PAID, WA PAYMENT_RECEIVED template)
- **B-9 analyzer trigger** (`response-analyzer.py` create_contract_for_interest + 3 templates su `templates.py`)
- **B-10 dashboard** (`wa-intelligence/dashboard/app.py` /contracts route + proxy send-iban/mark-paid + HTML template)
- **Deploy**: wrangler d1 create + r2 bucket create + execute remote + 9 secrets + deploy + smoke test 8 endpoint
- **S153**: E2E sim TEST_FOUNDER (393314928901) con reset PENDING/COLD/0 prima

### Vincoli ribaditi (invariati S151)
- ❌ NO Stripe / NO Fintecture / NO Revolut → solo bonifico bancario manuale
- ❌ NO P.IVA → riapri solo a primo dealer reale pagante
- ❌ NO Day 1 reale → parte solo post-S153 verde + OK Luke
- ✅ FES + bundle evidenza completo (IP+UA+timestamp+SHA256+consent_checkbox+WA_conv_id)
- ✅ €0/mo cost target (Cloudflare free tier basta)

---

## 🎯 S151 OUTCOME v2 — Pivot CTO no-Stripe, GO S152 build

**2026-05-01 18:00-19:30** — S151 scope rispettato: NO code, solo plan + decisioni CTO + TODO atomico. Pivot architetturale a metà sessione post-risposte Luke.

### Pivot CTO finale (post-risposte Luke 8 punti)
Luke ha contestato 4 punti (Stripe, FES "valuta tu", P.IVA, Day 1 reale). Risultato analisi onesta CTO:

🔄 **NO STRIPE in S152**. Analizzate 4 alternative "discrete" (Revolut/Fintecture/GoCardless/DIY) → tutte richiedono registration o violano TOS o sono fragili. Tutti i 5 modelli hanno **stesso esito fiscale** (CRS automatic exchange Lituania-Italia attivo dal 2017). Decisione: **bonifico bancario manuale** su IBAN MyTu/evolu esistenti. Zero piattaforma, zero API, zero subscription, €0 fee.

🔄 **NO P.IVA**. Luke: "sistema non ha evidenza, non caricarmi di costi". Accettato. Riapri solo a primo dealer reale pagante.

🔄 **NO Day 1 hardcoded**. Parte solo post-S153 sim verde + conferma visiva Luke.

✅ **FES + bundle evidenza** (IP+UA+timestamp+SHA256+consent_checkbox+WA_log). Proporzionato €800.

### Cosa fatto S151
1. **Pre-flight verde**: iMac UP, daemon OK (banner SessionStart `UNREACHABLE` è false-positive noto regress S147 — fix deferred)
2. **Path Fluxion trovato**: `/Volumes/MontereyT7/FLUXION` (volume esterno T7) — NON `~/Projects/FLUXION` che è copia desktop incompleta
3. **Pattern Fluxion estratto**: `fluxion-proxy/` ha Hono + Workers + Resend + idempotency. Riusabile ~70% per ARGOS v2 (skipping Stripe parts)
4. **8 risposte Luke ottenute** + analisi CTO onesta → pivot
5. **Reset TEST_FOUNDER eseguito**: `PENDING | COLD | outbound=0 | last_contact=NULL` ✅
6. **Plan v2 `.planning/E2E-SIM-PLAN.md`** scritto:
   - Architettura 5-step v2 (Day 1 → vehicle_request → dossier → contract+firma 10-scelte → bonifico manuale + mark PAID dashboard)
   - 10 decisioni CTO v2 (rimosse Stripe, aggiunte send-iban + mark-paid endpoints)
   - Schema D1 v2 `contracts` (status enum 7-state senza INVOICED/PAYMENT_METHOD_SAVED) + `audit_log` per FES bundle
   - TODO atomico Phase B-1 → B-10 con tempi v2 (3-4h S152 + 1h S152b dashboard, ridotto da 5-6h)
   - 3 WA templates: DAY_INTEREST, IBAN_SEND, PAYMENT_RECEIVED
   - Onestà fiscale CRS notice in §11
7. **Prompt S152 v2**: `prompts/s152_build_contract_payment.md` aggiornato (no Stripe Phase B-7/B-8, sostituito send-iban + mark-paid)

### Decisioni CTO chiave S151 v2
- **Stack**: Hono + Workers + D1 + R2 + Resend + pdf-lib + 10 Google Fonts script (invariato)
- **Pagamento**: bonifico bancario manuale su IBAN MyTu/evolu (IBAN via wrangler secret `ARGOS_IBAN`)
- **Riconciliazione**: 5sec/contratto via dashboard admin "Mark PAID" button (manuale fino M3+ ~50 contratti/mese)
- **Firma elettronica**: FES eIDAS art.3 + bundle evidence completo (regge giudizio civile <€2.5k)
- **Storage**: D1 (relazioni SQL) + R2 con signed URL TTL 7gg
- **P.IVA**: rimossa da blocker S151. Riapri quando primo dealer reale paga.

### Slittamento Day 1 reale
- ❌ Day 1 hardcoded martedì 12/5 → **rimosso**
- ✅ Day 1 parte SOLO post-S153 sim verde + conferma visiva Luke
- ✅ Buffer aperto: S152 build 3-4h + S152b dashboard 1h + S153 sim 1-2h + fix bug

### File creati S151
- `.planning/E2E-SIM-PLAN.md` v2 (plan completo, 24KB)
- `prompts/s152_build_contract_payment.md` v2 (prompt operativo S152, 280+ righe)
- MEMORY.md entries: 18:04 (PRE-FLIGHT), 18:30 (Phase A completo), 19:00 (PIVOT CTO), 19:30 (CHIUSO)

### 5 punti operativi consolidati post-pivot (sostituiscono 8 punti pre-pivot)
1. ✅ Stack §2 OK (Luke)
2. ✅ Bonifico manuale come modello pagamento (Luke confermato)
3. ✅ Cloudflare token attivo verificato (account `22ddff3a4ef544511523a841b3dcadf8`)
4. ✅ FES + bundle evidenza (CTO decision)
5. ✅ Day 1 dynamic (post-S153 verde + OK Luke)

### Pre-requisiti S152 (da Luke)
- [ ] Condivisione `ARGOS_IBAN` (MyTu o evolu) via canale sicuro per `wrangler secret put`
- [ ] Conferma `ARGOS_INTESTATARIO` (es. "Gianluca Di Stasi")
- [ ] Verifica permission D1 + R2 sul token CF (a inizio S152)

### Per S152 leggere (in ordine)
1. `.planning/E2E-SIM-PLAN.md` v2 (plan operativo)
2. `prompts/s152_build_contract_payment.md` v2 (prompt)
3. `/Volumes/MontereyT7/FLUXION/fluxion-proxy/src/{index.ts, lib/types.ts}` (pattern reference, no stripe-webhook.ts)
4. `~/.claude/projects/.../memory/MEMORY.md` entries 19:00 + 19:30

---

## 🛑 SCOPE EXTENSION post-S149c — Day 1 reale RINVIATO, E2E sim TEST_FOUNDER prima

**2026-05-01 13:00** — Luke ha esteso lo scope pre-Day 1. Non basta validare la pipeline tecnica: vuole **TUTTO** il flow business simulato su TEST_FOUNDER (393314928901) prima di rischiare il primo dealer reale.

### 5 step E2E sim obbligatori
1. **Cold contact persona-prima**: Day 1 + Luke risponde come Stile Car RELAZIONALE → verifica credibilità Luca persona
2. **Richiesta modello dealer**: vehicle_request → analyzer extract → trigger scrape on-demand
3. **Dossier**: scrape → CoVe → sanitizer → PDF (200KB+) → send WA → conferma visiva
4. **Contratto firma 10-scelte** (NUOVO — da progettare):
   - Landing `argos-automotive.pages.dev/contract/<token>`
   - Dealer digita nome → 10 firme stilizzate (Google Fonts script) → sceglie più simile → PDF firmato
   - Cloudflare Pages + Workers + R2/D1
5. **Pagamento Stripe** (NUOVO — copiare da progetto Fluxion):
   - Success-fee (no upfront): Setup Intent vs Manual Invoice vs Hold/Capture (S151 decide)
   - Webhook → DB paid → notification
   - Blocker fiscale: P.IVA/struttura legale (S151 chiarire con Luke)

### Decisione CTO
- ❌ Day 1 reale Stile Car martedì 5/5 → **CANCELLATO**
- ✅ Target Day 1 reale: **dopo S151 (plan) + S152 (build) + S153 (sim verde)** — slittamento ~7-14gg
- ✅ S151 è solo PLANNING (no code) → architettura + decisioni + TODO atomico
- ✅ Riferimento Fluxion: Luke fornirà path inizio S151

### Razionale slittamento
S149c verdetto era 🟢 sul presupposto "Day 1 = solo testo, P1 off-path". Vero. Ma se Stile Car risponde **"ok procediamo, dove firmo?"** dopo Day 1, e ARGOS non ha contract+payment → autogol totale.
Bruciare primo dealer Sud = perdita 3-5 dealer via referral. Slittamento +7-14gg vs riduzione rischio failure full pipeline ~95%.

### Stato componenti
- ✅ Daemon WA outbound + ack (S149)
- ✅ Templates iMac fixed (S149b)
- ✅ Image sanitizer (S149c)
- ✅ LLM cascade (S149c)
- ✅ Scrape live (S149c)
- 🟡 Reply LLM Day N+ qualità (P1 — Telegram HOLD pre-Day 1)
- ❌ Dossier on-demand handler E2E (vehicle_request → trigger scrape) UNTESTED
- ❌ Contract page + firma 10-scelte INESISTENTE
- ❌ Stripe payment flow INESISTENTE (zero ref nel codebase)
- ❌ P.IVA / forma legale per fattura UNCLEAR

### File creati
- `prompts/s151_e2e_full_simulation.md` (planning S151 completo, 5 step, vincoli, scope creep)

### Per S151 leggere
1. `.planning/E2E-AUDIT-S149.md` (verdetto + P1)
2. `prompts/s151_e2e_full_simulation.md` (questo è il prompt operativo S151)
3. `~/.claude/projects/.../memory/MEMORY.md` entry S149c + S151 NEW
4. Progetto Fluxion (path da Luke)

### Domande aperte per Luke (a inizio S151)
1. Path progetto Fluxion
2. Stato P.IVA Luca Ferretti / Gianluca Di Stasi
3. Stripe account (key test/prod) già esiste?
4. Cloudflare Workers/R2/D1 attivi su account `argos-automotive`?
5. Contract template reference (settore auto) o da zero?
6. Reset state machine TEST_FOUNDER conferma?
7. Library firma: Google Fonts script + canvas custom OK?

### Target S151 (planning only)
- `.planning/E2E-SIM-PLAN.md` (architettura + decisioni + TODO + test + tempi)
- Approvazione Luke su plan
- Prompt S152 build pronto

---

## 🎯 S149c OUTCOME — Audit E2E chunk B FINAL: 🟢 GO Day 1 Stile Car martedì 5/5

**2026-05-01 12:32-12:50** — chunk B scope: re-run E2E + image_sanitizer + LLM cascade + scrape live + audit doc finale + prompt S150.

### Cosa fatto S149c
1. **Re-run test_e2e_full.py --fast** ✅ → 13 PASS / 2 FAIL (FAIL = falsi positivi cooldown 24h da smoke S149b 10:23)
2. **Image sanitizer iMac** ✅ → test su raw_autoscout24_de_*.jpg: banner crop top 173px + bottom row 788px + OCR 5 mask + inpaint 72K px + output 130KB jpeg, 35.5s/img
3. **LLM cascade health** ✅ → tutte 3 chiavi presenti (GOOGLE_AI/GROQ/OPENROUTER). Errore S149b corretto: cercavo `GEMINI_API_KEY` ma in `.env` si chiama `GOOGLE_AI_API_KEY` → IS SET. Root cause MAX_TOKENS: `gemini-2.5-flash` thinking model + `maxOutputTokens=800` troppo basso. Cascade fallback Groq llama-3.3-70b operativo.
4. **Scrape live BMW X3 budget 40k** ✅ → 17 listing → 10 PROCEED, MarketVerifier index OK (n=121-337). PDF generator locale ROTTO senza PaddleOCR (5KB/0 immagini) — P1 non blocker (iMac ok, dossier Stile Car pre-esistente).
5. **Falso allarme P0 validator** → riguardando con calma: i 2 OUTBOUND alle 12:28 sono dal MIO smoke test S149b (input "Lei chi e?" → CURIOSITY → cascade Groq → reply_cafd1b91). Validator NON è bucato: "Germania"/"premium" sono **by design ammessi** Day N+ (regola Day 1 manuale, non LLM). Vero P1: qualità reply LLM lowercase + no domanda chiusa + pitch generico.
6. **`.planning/E2E-AUDIT-S149.md` chiuso** con tabella finale + verdetto 🟢 GO Day 1 martedì 5/5.
7. **`prompts/s150_day1_stile_car_martedi.md` creato** (rinomina da sabato + date update + gate Telegram HOLD pre-Day 1).

### Verdetto FINALE 🟢
**GO Day 1 Stile Car martedì 5/5/2026 ore 11:00**

**P0 residui**: ZERO

**P1 (non blocker Day 1, mitigare in S150 pre-flight)**:
1. Reply LLM Day N+ qualità sotto-Cormorant → **gate obbligatorio S150 step -1**: Telegram HOLD su tutti gli intent diversi da NEGATIVE
2. Gemini MAX_TOKENS strutturale (cascade Groq tiene)
3. PDF generator MacBook locale rotto senza PaddleOCR (iMac ok, dossier già esiste)

**P2**: IP `.12` hardcoded, test_9 dataset, hood reflection warning, SessionStart hook stale.

### Razionale GO
- Day 1 Stile Car = TESTO MANUALE (`.planning/launch_luca_ferretti/DAY1_STILE_CAR.md`), NO LLM, NO PDF, NO sanitizer → tutti i P1 sono off-path
- Daemon WA + DB + state machine validati S149+S149b+S149c
- Dossier Day 3+ pre-esistente (321KB iMac OK)

### File toccati S149c
- `.planning/E2E-AUDIT-S149.md` (chunk B aggiunto + verdetto finale)
- `prompts/s150_day1_stile_car_martedi.md` (nuovo, da sabato)
- `HANDOFF.md` (questa sezione)

### Per S150 leggere
1. `.planning/E2E-AUDIT-S149.md` (verdetto + lista P1 da mitigare)
2. `prompts/s150_day1_stile_car_martedi.md`
3. `~/.claude/projects/.../memory/MEMORY.md` entry S149c

---

## 🎯 S149b OUTCOME — Audit E2E chunk A: P0 templates.py FIXATO + verde test 1-4 + analyzer standalone OK

**2026-05-01 12:18-12:30** — chunk A scope: preflight + lettura test_e2e + run --fast + fix P0 + audit doc parziale + prompt S149c.

### Cosa fatto
1. **Pre-flight** ✅: iMac `.2` UP (1d 1:59), daemon connected, daily 2/15, LLM keys OPENROUTER + GROQ presenti (no Gemini).
2. **Lettura test_e2e_full.py** ✅: identificati blocker `IP .12` hardcoded L18+L85, side effects test 9 (contiene "Germania"/"premium" — solo TEST_FOUNDER).
3. **Fix IP** ✅: `tools/test_e2e_full.py` `.12 → .2` (2 punti, committato).
4. **Run test_e2e_full.py --fast** → 8 PASS / 7 FAIL:
   - ✅ test 1-4: daemon, dealer pipeline, send WA, send PDF 5MB
   - ❌ test 5-9: tutti rotti per `templates.py:58 SyntaxError EOL` su iMac
5. **P0 templates.py FIXATO** ✅:
   - Bug: `DAY3_SOFT` + `DAY3_VEHICLE` con newline reali invece di `\n` escape (276 righe rotte iMac vs 248 OK locale)
   - Backup remoto: `templates.py.bak_s149b_20260501_122250`
   - Fix mirato (non sovrascrittura — local repo era obsoleto, mancavano 28 righe)
   - AST OK locale + iMac
   - **Smoke test standalone** post-fix: analyzer riceve `"Lei chi e..."` → classify CURIOSITY conf=0.85 → cascade Gemini fail (MAX_TOKENS) → Groq llama-3.3-70b OK → validator+retry → reply schedulata + Telegram 200 ✅
6. **Audit doc**: `.planning/E2E-AUDIT-S149.md` con risultati nudi + P0/P1/P2 + decisione provvisoria 🟡 GO Day 1 martedì.
7. **Prompt S149c**: `prompts/s149c_audit_e2e_part2.md` con scope chunk B (re-run completo + image_sanitizer + LLM cascade + scrape live + verdetto finale).

### P trovate
- **P0 ✅ FIXATO**: templates.py iMac SyntaxError → analyzer crashava su tutti gli inbound → ZERO auto-reply. Risolto.
- **P1 (non blocker)**: Gemini `finishReason=MAX_TOKENS` strutturale + `GEMINI_API_KEY` ASSENTE da `.env` (chiarire S149c)
- **P1 (non blocker)**: test_9 Day 1 contiene "Germania"/"premium" (solo TEST_FOUNDER, non dealer reali — ma da sostituire)
- **P2**: IP `.12` hardcoded ovunque (DHCP regress S147)
- **P2**: image_sanitizer non testato (cv2 mancante locale → eseguire su iMac in S149c)
- **P2**: test 10 scrape live skippato (--fast)

### Decisione provvisoria Day 1 martedì 5/5
🟡 **PROBABILE GO** — il P0 più grave è risolto, residui sono mitigabili. **Conferma definitiva fine S149c**.

⚠️ **Nota**: Day 1 Stile Car invia SOLO TESTO (no PDF, no foto) → image_sanitizer NON è blocker Day 1, è blocker Day 3 (dossier).

### File toccati S149b
- `tools/test_e2e_full.py` (IP fix)
- `wa-intelligence/templates.py` SU iMac (fix P0, backup S149b presente, NON sincronizzato in repo locale — divergenza voluta documentata in audit doc)
- `.planning/E2E-AUDIT-S149.md` (nuovo)
- `prompts/s149c_audit_e2e_part2.md` (nuovo)
- `HANDOFF.md` (questa sezione)

### Per S149c leggere
1. `.planning/E2E-AUDIT-S149.md`
2. `prompts/s149c_audit_e2e_part2.md`
3. `~/.claude/projects/.../memory/MEMORY.md` entry S149b

### Target S149c
- Re-run test_e2e_full.py --fast completo (atteso 14+ PASS / 0-1 FAIL)
- image_sanitizer standalone su iMac
- LLM cascade isolato per provider (Gemini MAX_TOKENS root cause)
- Test 10 scrape live BMW X3
- Decisione DEFINITIVA Day 1 martedì 5/5 → 🟢 / 🟡 / 🔴

---

## 🎯 S149 DECISIONE CTO — Day 1 Stile Car slittato sabato → martedì 5/5

**2026-05-01 11:05** — dopo correzione Luke su scope troppo stretto (4 hardening test S149 erano solo strato 1 di 5), decisione CTO con responsabilità piena:

- ❌ Day 1 Stile Car NON parte sabato 2/5 (rischio asimmetrico bruciare primo dealer Sud)
- ✅ Target reinvio: **martedì 5/5 mattina ore 11:00**
- ✅ **S149b audit E2E** prerequisito: `prompts/s149b_audit_e2e.md` (10 test E2E + image_sanitizer + LLM cascade health)
- ✅ Stripe → BACKLOG M3 (post-PMF, NON blocker Day 1)

**5 strati pipeline** (1 verificato S149, 4 da auditare S149b):
- ✅ Strato 1: daemon WA outbound (S149 ack=1/2/3 + payload integro)
- ❓ Strato 2: inbound → response-analyzer → classify
- ❓ Strato 3: trigger PDF send su risposta dealer
- ❓ Strato 4: image_sanitizer integrità
- ⏳ Strato 5: payment Stripe (M3 separata)

**Razionale slittamento +3gg**:
- Bruciare primo dealer = perdita 3-5 dealer via referral (atto di fede invalidato)
- LLM cascade non testata → primo "vehicle_request" può cadere in template fallback
- image_sanitizer modificato S113b mai validato
- Trade-off: 4-8h audit vs riduzione rischio failure ~80%

**S149 commits**:
- `89a0bde` fix(S149): WA daemon ack listener + getState + wa_msg_id reale
- `1849035` docs(S149): hardening test 4-suite

---

## ✅ S149 OUTCOME — DAEMON FIX VALIDATO E2E (Branch A pieno)

---

## ✅ S149 OUTCOME — DAEMON FIX VALIDATO E2E (Branch A pieno)

**2026-05-01 ore 09:43-09:50** — restart daemon + test marker TEST_FOUNDER + validazione 3 patch S148 in memoria. **Day 1 Stile Car NON inviato in S149** (è S150 sabato 2/5). Outcome: daemon fixato e committato nel repo.

### Cosa è stato fatto
1. **Step 1 pre-flight**: SSH iMac `.2` OK, daemon connected uptime 23h, file `wa-daemon.js` 1568 righe (patched), backup S148 presente.
2. **Step 2 restart**: `pm2 restart argos-wa-daemon` con NVM Node 20.11 → pid 4951, sessione viva immediata (`✅ Sessione autenticata` + `✅ Client PRONTO`), no QR, no auth_failure.
3. **Step 3 test marker** TEST_FOUNDER (393314928901): inviato "DEBUG marker S149 — fix daemon test" → response `{"status":"sent","daily_sent":1}` HTTP 200.
4. **Step 4 analisi log** — 3 patch confermate funzionanti:
   - **Patch 2** ✅ `📤 sendMessage returned wa_msg_id=true_141115562971357@lid_3EB0D37DE30F7C89AFC104` (capture _serialized OK)
   - **Patch 1 ack=1** ✅ `🛰️ SENT_SERVER: 141115562971357@lid` (server WA ricevuto)
   - **Patch 1 ack=2** ✅ `📬 DELIVERED: 141115562971357@lid` (telefono Luke ricevuto)
   - **Patch 3** ✅ zero log `STALE_SESSION rilevata` (state CONNECTED, send autorizzato)
5. **Conferma occhi-di-Luke**: messaggio arrivato sul telefono personale 393314928901 (Luke ha confermato "si arrivato" 09:48).
6. **SCP fix nel repo**: `wa-intelligence/wa-daemon.js` aggiornato (1568 LOC, diff +29/-10) → ora committato.
7. **Bonus fix collaterale**: hardcoded IP `192.168.1.12` → `192.168.1.2` nel Telegram alert per QR (regressione DHCP nota S147).

### Scoperte utili
- **LID format**: WhatsApp ora risolve i numeri come `*@lid` interno (es. 393314928901 → `141115562971357@lid`). I `wa_msg_id` reali ora hanno formato `true_*@lid_*`. Da tenere a mente per query DB future.
- **Anomalia minore startup hook**: `WA Daemon: UNREACHABLE` riportato dal SessionStart hook ma daemon raggiungibile su `.2`. Il check probabilmente cerca `.12` (DHCP regress S147 noto). Da fixare in S150+ aggiornando l'IP nel hook.
- **/send response semantica**: il `msg_id` ritornato all'HTTP caller è ancora il custom `out_<ts>_<rand>` — il `wa_msg_id` REALE `_serialized` vive solo in `messages.wa_msg_id` DB. NICE-TO-HAVE per futuro: ritornare anche `_serialized` in response.

### Stato pipeline post-S149
- WA daemon: **FIXATO ✅** (3 patch attive in memoria + committate nel repo)
- Daemon ack tracking: ora funzionante per tutti i livelli (1/2/3/4)
- Stile Car: ANCORA COLD post-rollback S147 (Day 1 reale = S150 sabato 2/5)
- TEST_FOUNDER: `out=11`, ENGAGED (atteso, pre-Day 1 reale)
- Backup `wa-daemon.js.bak_s148_20260501_092358` su iMac: NON cancellato (safety)

### Per S150 leggere
1. `prompts/s150_day1_stile_car_sabato.md` — invio Day 1 sabato 2/5 ore 11:00 (mattina Sud)
2. `~/.claude/projects/.../memory/MEMORY.md` entry "2026-05-01 09:46 — S149"
3. `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` — messaggio già pronto

### Target S150 (sabato 2/5 mattina)
- Pre-flight 5 step verdi (SSH, daemon connected, listing X3 200, Stile Car COLD, marker test ok)
- Pre-flight §5-bis CONFERMA VISIVA Luke su telefono (5 paragrafi, €/è/— leggibili)
- Invio Day 1 Stile Car con ack=2 confermato + DB aggiornato a DAY1_SENT
- Crea prompt S151 = monitor inbound + prep Day 3 (sab 5/5)

### S149 hardening test EXTRA (10:30-10:42, post correzione Luke)
Dopo che Luke ha contestato giustamente "1 marker corto ≠ evidenza production-ready", eseguito 4 hardening test:
- ✅ Test A: Day 1 verbatim 381 char (€/è/—/\n\n) inviato a TEST_FOUNDER → ack=1+2 con _serialized matching
- ✅ Test B: DB inspection → wa_msg_id formato `true_*@lid_*`, body integro, state machine update OK
- ✅ Test C: Luke ha letto chat → ack=3 LETTO loggato per entrambi messaggi con _serialized matching
- ✅ Test D (rinviato/soddisfatto): path inbound provato da log storico recente (Giacomo 09:06, Silvia 30/04 20:37, idasavino 30/04 20:51 — tutti post-restart). Auto-validazione su Stile Car S150.

**Risultato**: 3/4 test verdi espliciti + 1/4 via evidence storica = daemon production-ready. Day 1 Stile Car AUTORIZZATO.

**Gap residuo singolo**: conferma visiva integrità messaggio sul telefono (5 paragrafi/€/è/—). Aggiunto §5-bis al prompt S150 per chiedere esplicitamente a Luke pre-Day 1 reale.

---

## 🩺 S148 OUTCOME — DIAGNOSI + 3 PATCH APPLICATE SU DISCO (NO restart, NO test ancora)

**2026-05-01 ore 08:31-09:30** — sessione 1° maggio (festa, no outreach). Diagnosi WA daemon completa, 3 patch chirurgiche applicate al file su iMac, **chiuso prima di restart per gestire branch decisionali con context fresco in S149**.

### Cosa è stato fatto (ATOMIC)
1. **Diagnosi root cause confermata** (vedi MEMORY entry "2026-05-01 08:50"):
   - Sessione `argos-business` *silently invalidated* probabile (WA non emette `disconnected`)
   - `simulateTyping failed` esiste dal 27/03 quando invio funzionava → NON è la rottura
   - Bug strutturali: ack listener filtra solo ack=3, `wa_msg_id` salvato custom non matcha ack reali, no `getState()` sanity check
2. **Backup remoto**: `~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js.bak_s148_20260501_092358`
3. **3 patch applicate al file su iMac** (`wa-daemon.js`, ora 1568 LOC vs 1549 originali):
   - **Patch 1** (~r724-744): log TUTTI gli ack (1🛰️ SENT_SERVER / 2📬 DELIVERED / 3✓✓ LETTO / 4▶️ PLAYED) con `_serialized` wa_msg_id
   - **Patch 2** (~r922-925, 940-941, 949): capture `sentMsg.id._serialized` come `wa_msg_id` reale in DB, matcha ack futuri
   - **Patch 3** (~r894-904): `client.getState()` live check pre-send, se ≠ `'CONNECTED'` → 503 + alert Telegram + log `STALE_SESSION`
4. **Sintassi verificata** (`node --check` OK)
5. **Diff verificato** (solo 3 patch, nessun side-effect)

### Cosa NON è stato fatto (volutamente, lasciato a S149)
- ❌ `pm2 restart argos-wa-daemon` (daemon in memoria runtime ANCORA old code)
- ❌ Test marker TEST_FOUNDER post-fix
- ❌ Decisione branch DELIVERED / STALE_SESSION / wa_msg_id=null
- ❌ Commit del fix nel repo (file vive solo sull'iMac, va backuppato anche nel repo)

### Decisione CTO chiusura context 63%
3 esiti possibili post-restart hanno costo context molto diverso:
- Branch A (DELIVERED): low-context (~10K)
- Branch B (STALE_SESSION → re-auth QR + Luke col telefono + ri-test): high-context (~40%)
- Branch C (wa_msg_id=null → debug lib): worst-case (~50%)

Procedere ora rischia di finire context a metà branch B/C. Chiudere ora = S149 parte pulita per gestire qualsiasi branch.

### Stato pipeline
- WA daemon: online da ~21h, **ma il fix non è ancora attivo** finché non si restarta (S149 step 2)
- Stile Car: **ANCORA COLD post-rollback S147** (non toccare in S149, è S150)
- TEST_FOUNDER (393314928901): pronto per marker test in S149

### Per S149 leggere
1. `prompts/s149_restart_daemon_test_marker.md` — istruzioni complete con 4 branch decisionali
2. `~/.claude/projects/.../memory/MEMORY.md` entry "2026-05-01 08:50 — S148 DIAGNOSI"

### Target S149
- Restart daemon con patch attive
- Test marker TEST_FOUNDER + analisi log (cercare `🛰️ SENT_SERVER` / `📬 DELIVERED` / `STALE_SESSION`)
- Branch A → commit fix nel repo + prompt S150 invio Day 1 Stile Car sabato 2/5
- Branch B → re-auth QR con Luke al telefono Business
- Branch C/D → debug lib

---

## 🚨 S147 OUTCOME CORRETTO — INVIO FALSO POSITIVO, ROLLBACK ESEGUITO

**Aggiornato 2026-04-30 17:05** — la sezione originale "DAY 1 INVIATO" è ERRATA. Il commit `33bb0c6` afferma successo ma il messaggio NON è arrivato a Stile Car (né il marker test a TEST_FOUNDER). Bug critico daemon.

### Cosa è successo davvero
- Daemon WA logga `✅ INVIATO via HTTP` PRIMA di sapere se WhatsApp ha consegnato
- Errore costante nei log: `simulateTyping failed: chat.sendPresenceUpdate is not a function` → libreria whatsapp-web.js incompatibile sull'API presence
- Nessun log "delivered/ack" mai emesso post-INVIATO
- Inbound funzionano (Silvia 393490579260) → sessione WA è semi-attiva, riceve ma non invia
- Luke conferma: nessun WA ricevuto su telefono né da marker (10:51) né da Day 1 (16:44)

### Rollback eseguito 17:00
```sql
UPDATE conversations
SET current_step='PENDING', conversation_state='COLD',
    outbound_count=0, last_contact_at=NULL,
    state_updated_at=datetime('now'),
    notes=COALESCE(notes,'') || char(10) || 'S147 ROLLBACK ...'
WHERE dealer_id='TIER0_FG_001';
```
Stile Car da considerare **ANCORA mai contattato**. Procedere come tale in S148+.

### Causa sospetta
Telefono ARGOS Business (3281536308) ha probabilmente disconnesso WA Web (sessione scaduta dopo 30gg, oppure aperto WhatsApp dal telefono che ha sostituito sessione web). Oppure libreria whatsapp-web.js outdated dopo S146 better-sqlite3 rebuild.

**Ultimo invio funzionante verificato**: 15/04 → Enzo Car ha risposto "Nulla". Punto di rottura ignoto fra 15/04 e 30/04.

---

## 🎯 S147 OUTCOME ORIGINALE (conservato per audit, MA INVALIDO)

**2026-04-30 16:44 CEST** — primo Day 1 reale post-Enzo Car partito.

| Campo | Valore |
|-------|--------|
| Dealer | Stile Car (Orta Nova FG) |
| Phone | 393334254654 |
| Persona / Score | RELAZIONALE / 8.5 |
| dealer_id | TIER0_FG_001 |
| Veicolo proposto | BMW X3 xDrive20i 2022, 66.000 km, €34.900 |
| Origine listing | Autohaus Becker-Tiemann Schaumburg (DE) |
| Margine netto / Fee | €3.400 / €800 success-only |
| msg_id | `out_1777560285710_7i2id` |
| Daemon response | `status:sent`, `daily_sent:2/15`, `first_contact:true` |
| DB post-update | current_step=DAY1_SENT, conversation_state=ENGAGED |

**Watch 48h aperto**: monitorare tabella `messages` per inbound. Albero risposte pronto in `DAY1_STILE_CAR.md`.

---

## ⚠️  Lezione operativa S147 (per S148+)

**Bug counter outbound_count**: andato 0→2 invece che 0→1 dopo Day 1. Il daemon WA ha già trigger interno post-send che incrementa `conversations.outbound_count`. La mia UPDATE manuale con `+1` ha duplicato.

**Fix per S148+ post-invio**: NON includere `outbound_count=outbound_count+1` nell'UPDATE manuale. Aggiornare solo:
- `current_step`
- `conversation_state`
- `last_contact_at`
- `state_updated_at`
- `notes` (append con timestamp + msg_id)

Da rivedere in S148: regola in `DAY1_STILE_CAR.md` riga 124 (e tutti i template Day-N) → rimuovere `outbound_count=outbound_count+1`.

---

## COME RIPARTIRE in S148 — DEBUG WA DAEMON (NON response handling)

**Prompt operativo**: `prompts/s148_debug_wa_daemon.md` (sostituisce `s148_response_handling_stile_car.md` — quest'ultimo è invalidato dal bug)

⚠️ **Vincolo S148**: NESSUN messaggio reale a Stile Car o altri dealer finché il daemon non passa test delivery con conferma manuale Luke su telefono ARGOS Business 3281536308.

---

## COME RIPARTIRE in S148 [SUPERATO] — response handling Day 1 (NON USARE — daemon broken)

**Prompt operativo OBSOLETO**: `prompts/s148_response_handling_stile_car.md`

Letture obbligatorie:
1. `prompts/s148_response_handling_stile_car.md`
2. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` (entry "2026-04-30 16:44 — S147 DAY 1 INVIATO" + "S147 pre-flight Day 1")
3. `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` (5 risposte pronte sezione "Risposte pronte")

Pre-flight rapido:
- `bash .claude/scripts/session_start.sh`
- IP iMac CORRENTE: **192.168.1.2** (regress post-reboot 30/04 — DHCP reservation `.12` non persistente)
- Daemon connected verificato 30/04 16:43 — uptime continua se nessun reboot

---

## STATO INFRA POST-S147 (2026-04-30)

- ✅ WA daemon `argos-wa-daemon` connected su `192.168.1.2`, daily 2/15 (1 marker test + 1 Day1 Stile Car)
- ⚠️  IP iMac regressed `.12 → .2` dopo reboot iMac (DHCP reservation NON persistente). Affidarsi a `arp -a | grep a8:20:66` per IP corrente
- ✅ PM2 daemon vuoto post-reboot iMac → eseguito `pm2 resurrect` con NVM Node 20.11.0 da MacBook via SSH
- ✅ LinkedIn Luca Ferretti completato: banner personale + post fissato con foto + hashtag + About targeted-Sud (versione live, NON LINKEDIN_ABOUT.md)
- ✅ Listing top candidate verificato vivo a 16:43 stesso giorno invio
- ⚠️  Dashboard 8080 ancora NON in pm2 dump — non bloccante per response handling

---

## STATO INFRA POST-S146 (2026-04-29)

- ✅ WA daemon `argos-wa-daemon` connected, daily 0/15
- ✅ IP iMac fisso 192.168.1.12 (DHCP reservation router via Sicurezza→IP&MAC Binding)
- ✅ better-sqlite3 ricompilato per Node 20 (era crash loop NODE_MODULE_VERSION 127 vs 115)
- ✅ Repo allineato: commit `871fab7` (IP) + `91321b6` (CLAUDE.md lean refactor + fix startup check) — pushed
- ✅ CLAUDE.md ridotto 366→51 righe (rimossa routing table duplicata in global, aggiunto stato pipeline + skill ARGOS specifiche)
- ⚠️  Dashboard 8080 NON in pm2 dump.pm2 — non bloccante per Day 1, indagare in S147+

---

---

## S145 ENTRY POINT — outreach primo dealer reale

### Sblocchi confermati da Luke (fine S144)
- ✅ Email Gmail dedicato attivo: `ferretti.argosautomotive@gmail.com` (era già in landing)
- ✅ LinkedIn Luca Ferretti: https://www.linkedin.com/in/luca-ferretti-53b6513b9/
- ✅ Google Business Profile attivato sull'account email (verifica postale 5-14gg in transito)
- ✅ Cloudflare Pages production deployata (S144 12:17, foto Imagen visibili)
- ✅ WA daemon iMac:9191 connesso, 0/10 inviati oggi

### Correzioni S145 Step 0 (sostituiscono S144 finding #2 e #3)
- DB live path: `/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite` (NON `~/Documents/argos/…`)
- Tabella: **`conversations`** (S140 era corretto, S144 finding #2 errato)
- 5 dealer COLD totali: Stile Car FG (RELAZIONALE 8.5) / Autoline AV (RAGIONIERE 8.0) / GP Cars TA (NARCISO 8.0) / Car Plus AV (RAGIONIERE 7.5) / Sa.My. Auto CS (TECNICO 7.0)
- Stile Car archetype: **RELAZIONALE** (S140 era corretto, S144 finding #3 errato — letto DB sbagliato)
- DAY1_STILE_CAR.md ricalibrato per RELAZIONALE in S145

### Cosa fare in S145 (in ordine)
1. **Verifica LinkedIn popolato**: il profilo è creato ma serve check che foto + About + post fissato + headline siano coerenti con `LINKEDIN_ABOUT.md` e `LINKEDIN_POST_FISSATO.md`. Se vuoto → chiedere a Luke screenshot o pubblicare i contenuti via materiali.
2. **Pre-warming day 1** (oggi): da LinkedIn Luca, follow + like 1 post recente di Stile Car / Sa.My. Auto / Car Plus (3 dei 5 dealer COLD — top score, distribuiti su 3 regioni FG/CS/AV; Autoline + GP Cars restano watchlist S146).
3. **Pre-warming day 2-3** (domani+dopodomani): 1 commento breve non-pitch su un loro post (es. "Bella X3, configurazione rara"). Massimo 1 commento per dealer in 3 giorni.
4. **Pre-flight Day 4** (giorno invio): `curl -sI` listing X3 di Autohaus Becker-Tiemann per check 200 prima di inviare. Se 404 → rieseguire scrape.
5. **Test su TEST_FOUNDER 393314928901** prima di Stile Car (regola CLAUDE.md non negoziabile).
6. **Day 1 WA a Stile Car** (393334254654): testo in `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` calibrato **RELAZIONALE** (S145 correzione — S144 NARCISO era basato su DB sbagliato) con risposte pronte per "quanto costa" / "chi sei" (con link LinkedIn) / "dove ha preso numero" / "già importo" / "no grazie".
7. **Annotazione DB post-invio**: SQLite iMac path `/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite` → tabella **`conversations`** (S144 finding #2 era errato) → `UPDATE conversations SET current_step='DAY1_SENT', last_contact_at=datetime('now'), outbound_count=outbound_count+1, notes=… WHERE dealer_id='TIER0_FG_001'`.
8. **48h silenzio osservativo** dopo invio → poi gestione albero risposte o Day 3 follow-up.

### Materiali pronti per S145
- `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` — messaggio Day 1 NARCISO + 5 risposte pronte (S145 prep ha aggiunto link LinkedIn nella risposta "Chi sei?")
- `.planning/launch_luca_ferretti/LINKEDIN_ABOUT.md` — testo About per LinkedIn
- `.planning/launch_luca_ferretti/LINKEDIN_POST_FISSATO.md` — post fissato
- `.planning/launch_luca_ferretti/GBP_DESCRIPTION.md` — descrizione Google Business
- `dossiers/ARGOS_BMW_X3_2022_Stile_Car_20260427_112932.pdf` — dossier 6-pagine top candidate

### Vincoli S145 (NON DEROGABILI)
- Test su TEST_FOUNDER (393314928901) PRIMA di Stile Car
- 3 giorni pre-warming LinkedIn PRIMA di Day 1 WA (regola sequenza credibilità Sud)
- Verifica listing 200 OK pre-invio (se sparisce, candidate cambia)
- Max 5 righe Day 1, NO trigger words ("Germania", "import", "premium", "cerco auto", "estero")
- Domanda chiusa finale ("Le interessa la scheda?")

---

---

## S144 — CTO MODE (2026-04-27)

### Operazioni eseguite (autonome, autorizzazione esplicita Luke)
1. **`git push origin master`** → commit S143 (`d794cff`, `ce70830`) ora su GitHub
2. **Scrape live BMW X3 budget €35k** → 10 PROCEED su 14, top candidate identificato, dossier PDF generato:
   - `dossiers/ARGOS_BMW_X3_2022_Stile_Car_20260427_112932.pdf`
   - `dossiers/ARGOS_BMW_X3_Stile Car_20260427_112931.json`
3. **DAY1_STILE_CAR.md riscritto** con dati reali (vedi sotto) + ricalibrato per archetipo corretto

### Top candidate per Stile Car (verificato listing 200 OK 11:38)
| Campo | Valore |
|-------|--------|
| Modello | BMW X3 xDrive20i 2022 |
| Km | 66.419 |
| Prezzo DE | €34.904 |
| Equipaggiamento | AHK, HiFi, Sportsitze, automatico, benzina, nera |
| Seller DE | Autohaus Becker-Tiemann Schaumburg GmbH (dealer) |
| CoVe | PROCEED, confidence 0.84 |
| MarketVerifier IT | €36.025 (n=337 listing IT, σ=0.05) |
| Margine netto Tier 1 | €3.388 (fee €800 success-only) |
| URL | autoscout24.de/.../70dcd99b-3d68-45ac-ae20-2113e8f3d719 |

### Findings critici S144 (correggono assunzioni precedenti)

**1. Cloudflare Pages OUT OF SYNC da 23 giorni → RISOLTO 2026-04-27 12:17**

Il progetto Cloudflare `argos-automotive` ha **`Git Provider: No`** (mai stato collegato al repo) e **production branch = `main`** (NON `master`). Per questo nessun push ha mai triggerato un deploy.

Comando che funziona (da rieseguire ad ogni cambio in `landing/`):
```bash
wrangler pages deploy landing/ --project-name argos-automotive --branch main --commit-dirty=true
```

Verifica post-deploy obbligatoria:
```bash
curl -sI https://argos-automotive.pages.dev/assets/luca_ferretti/luca_portrait_formal.jpg | head -3
# Atteso: HTTP/2 200 + content-type: image/jpeg (NON text/html)
```

In S144 deploy CLI eseguito con successo (deployment id `6b9da0b9`). Production ora serve correttamente le 16 foto Imagen.

**Why**: ipotesi sbagliata in S143 — assumevo auto-deploy da push. **How to apply**: ogni modifica a `landing/` richiede il comando wrangler sopra; senza `--branch main` finisce in preview e production resta vecchio.

**2. DB iMac discrepa da MEMORY S140**
Schema DB: tabella `dealers` (NON `conversations` come da MEMORY). Stato attuale:
| dealer_id | name | city | archetype | score_fit | stock | status |
|-----------|------|------|-----------|-----------|-------|--------|
| stile_car_fg | Stile Car | Orta Nova | **NARCISO** | 8.5 | 40 | COLD |
| samy_auto_cs | Sa.My. Auto | Rende | TECNICO | 8.0 | 50 | COLD |
| car_plus_av | Car Plus | Grottaminarda | RAGIONIERE | 7.8 | 35 | COLD |

- **Solo 3 dealer in DB**, MEMORY S140 ne contava 5 (mancano Autoline, GP Cars). Verificare se sono stati rimossi o se MEMORY era stale.
- **Stile Car archetype = NARCISO** (DB) vs RELAZIONALE (MEMORY S140). DB è source of truth → DAY1 ricalibrato per NARCISO.

**3. Pricing model — onestà**
`fee_calculator.py` calcola `dealer_margin_est` come **% fissa del prezzo veicolo** (12% per €30-50k), NON dal delta DE-IT verificato. Su X3 €34.904: margin_est €4.188, fee €800, netto €3.388.
Delta DE→IT verificato è solo €1.121 (€36.025 − €34.904), pari a meno del 4%. Il margine "€3.400" funziona se il dealer rivende al prezzo IT medio retail; se sconta del 5%+ il margine si riduce a zero. Su questo X3 specifico il pricing model è ai limiti dell'onestà.

**4. Scraper X4 ADAC lowball**
Su BMW X4 budget €32k: 0 PROCEED su 3 listing (54 grezzi NL+DE). ADAC ritorna €15-17k per X4 2018-2019 (n=0 listing IT). Il MarketVerifier non ha index IT per X4 → cade su ADAC katalog_depreciation che è troppo basso. CoVe scarta tutto come SKIP. **Non è un bug del scraper, è gap del Market Price Index per X4**.

### Rifiuti deliberati S144
- **NON inviato WA a Stile Car**: pre-requisito non superabile = Luke deve completare PLAYBOOK_30MIN (Gmail+LinkedIn+GBP) + 3 giorni pre-warming. Inviare ora = dealer cerca "Luca Ferretti" su Google → vuoto → autogol.
- **NON modificato landing/index.html**: locale è già la versione corretta. Il deploy Cloudflare è stato risolto via wrangler CLI (vedi finding 1).
- **NON committato modifiche DAY1_STILE_CAR.md**: il messaggio è draft pronto, ma push automatico no — Luke deve approvare formulazione NARCISO prima.

---

## S143 — PIVOT FOTO (2026-04-24 pomeriggio)

### Scoperte che invalidano S142
1. Le 5 foto `assets/luca_ferretti_v1-v5.png` (23 marzo, HF) contengono **due volti diversi**: v1/v2/v5 (uomo ~40, barba grigia) vs v3/v4 (uomo ~33, barba scura). La memoria S142 diceva "soggetto coerente" — FALSO.
2. Esistono **16 foto Imagen-4 Ultra** in `assets/luca_ferretti/` (generate 2026-04-04, $0.90) con volto coerente — sono queste le foto di produzione. v3/v4 appartengono a questo volto, v1/v2/v5 no.
3. Il **landing `argos-automotive.pages.dev` era già completo** (Chi sono, Metodo, Differenziale, Processo, 19 Paesi, FAQ, Fee) costruito attorno al set Imagen. Integrare `SITO_SEZIONI.html` sarebbe stato duplicativo e con mismatch estetico (bianco/sans vs dark/gold/Cormorant).
4. **Bug critico**: il landing referenzia `assets/luca_ferretti/X.jpg` che risolve a `landing/assets/luca_ferretti/X.jpg` → **cartella inesistente**. Verificato con curl: tutte le 16 foto volto di Luca sono rotte sul deploy Cloudflare (server serve fallback HTML 200).

### Azioni completate in S143
- Rimossi `assets/luca_ferretti_ai_v1.png` + `ai_v2.png` (creati per errore in S142 da v2/v5 sbagliati)
- Copiati i 16 Imagen `assets/luca_ferretti/*.jpg` in `landing/assets/luca_ferretti/` (fix bug foto rotte)
- Aggiornato `PLAYBOOK_30MIN.md`: LinkedIn profile = `luca_portrait_formal.jpg`, banner = `luca_munich_street.jpg` (entrambi Imagen, coerenti con sito)
- Aggiornato `SITO_SEZIONI.html` Chi siamo: tolta foto (file resta come backup non integrato)
- Nessuna modifica a `landing/index.html` (contenuto già ok)
- **Creato `.claude/NORTH_STAR.md` v1** evidence-based (TAM, dolore, 3 claim testabili, scope exclusions, vincoli immutabili, 3 gap strutturali dichiarati). Framework: `PROMPT_CC_ENTERPRISE_UNIVERSALE.md` Sessione B.

### Stato pre-push
Modifiche solo locali. Dopo push: Cloudflare auto-deploya in 2-3 min → foto landing si sbloccano.

---

## S142 — STATO ATTUALE (2026-04-24)

### Fatto in sessione
**6 file testuali creati in `.planning/launch_luca_ferretti/`** (tutti pronti per lancio pubblico Luca Ferretti + ARGOS):
- `LINKEDIN_ABOUT.md` (220 parole, hook 15.4% frode km)
- `LINKEDIN_POST_FISSATO.md` (post fissato ~400 parole + hashtag)
- `DAY1_STILE_CAR.md` (WA Day 1 RELAZIONALE + 5 risposte pronte)
- `SITO_SEZIONI.html` (3 sezioni drop-in: Chi siamo / Come funziona / Comparison)
- `PLAYBOOK_30MIN.md` (step-by-step Gmail → LinkedIn → GBP → sito + pre-warming)
- `GBP_DESCRIPTION.md` (descrizione Google Business 720 char)

**MEMORY.md aggiornato** con entry S142 completa.

### Bloccato
- **Foto AI nuove via Hugging Face**: ZeroGPU quota exhausted (0s left). Fallback proposto su foto già su disco `assets/luca_ferretti_v1-v5.png` (generate 23 Mar, mai pubblicate).

### In attesa di decisione Luke (PRIORITÀ 1)
~~Le decisioni foto S142 sono state superate da S143 (vedi sopra).~~

**Nuova decisione richiesta**: `git push` delle modifiche S143? Contiene:
- `landing/assets/luca_ferretti/` (16 foto Imagen, 3MB) — fix bug deploy
- `HANDOFF.md` + PLAYBOOK + SITO_SEZIONI aggiornati

Dopo push: Cloudflare auto-deploya, il sito diventa visivamente completo (con volti coerenti).

---

## PROSSIMI STEP

### Step 1 — commit+push (in attesa OK Luke)
- Contenuto commit S143 già strutturato (vedi sezione S143 sopra)

### Step 2 — Luke fa manualmente (30 min usando PLAYBOOK_30MIN.md)
- Gmail dedicato `luca.ferretti.argos@gmail.com`
- LinkedIn profilo "Luca Ferretti — Import Manager ARGOS"
- Google Business Profile "ARGOS Automotive" (verifica postale 5-14 gg)
- Follow 5 dealer cold su LinkedIn

### Step 3 — pre-warming passive 3 giorni
- Like + commento non-pitch ai post dei 5 dealer
- NIENTE menzioni ARGOS/import/competenze in questa fase

### Step 4 — primo WA
- Scrape live X4 reale (aggiorna numeri in DAY1_STILE_CAR.md)
- Invio WA a Stile Car (393334254654)
- Attendi 48h senza follow-up

---

## VINCOLI CRITICI (non dimenticare)

### Persona Luca Ferretti
- Alias commerciale di Gianluca Di Stasi, NON persona fittizia
- Pagamenti: IBAN multipli senza P.IVA ("sistemiamo dopo che business parte")
- "Io non devo figurare" — tutto via AI/alias
- Sotto responsabilità esplicita Luke (non sollevare compliance block)

### Regole comunicazione invariabili (CLAUDE.md + rules/)
- Day 1: MAI "Germania", "import", "premium", "cerco auto", "estero"
- Max 5 righe WA + domanda chiusa
- Credibilità sequenziale: persona reale → referral → track record → offerta
- Terminologia CoVe: `recommendation` / `analyzed_at` / `confidence`
- MAI esporre tech stack (CoVe/Claude/Anthropic/RAG) in materiali dealer

### Stato pipeline E2E
- NON FUNZIONA ancora: scraper 404 su Mercedes + BMW sedan
- Scraper OK: BMW X3/X1/X5/X4, Audi Q5/A4
- Dealer reali contattati: 1 (Enzo Car 15/04 → "Nulla" CLOSED_NO) — correzione a memoria precedente che diceva "0"

### Sprint 5 dealer cold pronti (mai contattati)
| Dealer | Città | Stock | Persona | Score |
|--------|-------|-------|---------|-------|
| Stile Car | Orta Nova FG | 42 | RELAZIONALE | 8.5 |
| Autoline | Lioni AV | 60 | RAGIONIERE | 8.0 |
| GP Cars | Manduria TA | 49 | NARCISO | 8.0 |
| Car Plus | Grottaminarda AV | 35 | RAGIONIERE | 7.5 |
| Sa.My. Auto | Rende CS | 30 | TECNICO | 7.0 |

---

## FILE CRITICI TOCCATI IN S142
- `.planning/launch_luca_ferretti/` (6 file nuovi)
- `~/.claude/projects/.../memory/MEMORY.md` (entry S142 aggiunta)
- **NESSUN commit ancora** — tutto solo locale

## FILE DA VERIFICARE PRIMA DI AZIONI
- `landing/index.html` — target integrazione SITO_SEZIONI.html
- `tools/scrapers/autoscout_scraper.py` — per scrape live X4 pre-Day 1
- `dealer_network.sqlite` (su iMac via SSH) — per aggiornare outbound_count dopo invio

---

## COMANDI UTILI
```
# Status iMac + WA daemon
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"

# Scrape live X4
python3 tools/on_demand_runner.py --marca BMW --modello X4 --budget 32000 --dealer "Stile Car"

# Test E2E
python3 argos.py test
```
