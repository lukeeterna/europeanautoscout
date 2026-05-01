# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S149 fine — 2026-05-01 09:50 (daemon FIXATO, validato E2E ack=2 reale, fix committato)

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
