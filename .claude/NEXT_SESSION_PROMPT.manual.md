# S226 — Ripartenza (riscritto a mano da CC, supersede stub auto-gen + handoff S225)

**Branch**: `s210/audit-master-plan` · **Generato**: 2026-06-02 · **Last commit**: `f63a1ee` (locale, NON deployato)
Questo file riscrive lo stub auto-generato. Fonte ricca precedente: `.claude/NEXT_SESSION_PROMPT.manual.md` (S225) — qui consolidata e corretta con la governance decisa il 2026-06-02.

---

## ⏹ S229 — ESITO (2026-06-02): C-WA-SEND-SPLIT FIXATO + DEPLOYATO → #9 ora BLOCKED-ON Luke fisico
**Fix applicato (delega devops-automator, code-verified):** il path `/approva` non spawna più `send_message.js` standalone (auth dir inesistente). Ora `cmd_approva` invia via **daemon connesso** POST `http://127.0.0.1:9191/send` + `X-API-Key` (single-writer S173). Edit chirurgico in `telegram-handler.py`:
- `task` dict (righe 237-246): `wa_id`/`wa_sender`/`client_id` → `phone`+`daemon_url`+`api_key`+`force`.
- `send_script` (righe 252-289): **guard HITL re-check `approved` post-sleep INTATTO** (anello #9 verificato); sostituito SOLO il blocco invio `node` con POST urllib; `[ABORT]/[ERROR]/[SENT]` preservati; `UPDATE sent=1` preservato. `py_compile` OK.
- **3 decisioni design:** (1) NON passo `dealer_id`/`template_id` → evito `runOutboundGuard` S106 (bloccherebbe la reply) + bump `current_step`; reply va come send "manual", tracking autoritativo = `pending_replies.sent=1`; (2) `force=true` (Luke approva esplicitamente, annulla precheck24h duplicato daemon); (3) business-hours gate introdotto da `/send` ma TEST_FOUNDER 393314928901 lo bypassa (`wa-daemon.js:799-805`).

**Deploy iMac (devops-automator):** file → `releases/20260527_083951/wa-intelligence/telegram-handler.py` (backup `.bak-pre-s229`). Restart SOLO `argos-tg-bot` (PID 91112 online); `argos-wa-daemon` NON toccato, `wa_status: connected`. **Preconditions verificate:** `ARGOS_API_KEY` presente su tg-bot (no 401), `TEST_FOUNDER_PHONE=393314928901` presente sul daemon (no business-hours block).

**#9 RICLASSIFICATO:** resta **PENDING-GATE**, ora **BLOCKED-ON Luke fisico** (NON più fix codice — C-WA-SEND-SPLIT chiuso code+deploy). **VERIFIED resta 2/9** → sale a 3/9 SOLO a gate fisico passato. La fix è ora RAGGIUNGIBILE (deployata) — vietato re-validarla staticamente (vincolo #1b).

**GATE PACKET #9 v2 — pronto per Luke (esegui il blocco "GATE PACKET #9 — v2" più sotto):** SEED dalla SIM 393314928901 → `/approva <reply_id>` → atteso log iMac `/tmp/argos-tg-send.log`: `[SENT] Reply <id> inviata via daemon msg_id=<id>` + msg ARRIVA sulla SIM (Scenario A). Scenario B: `/approva` poi subito `/rifiuta` → `[ABORT]` + nessun msg + `approved=0`.

---

## ⏹ S228 — ESITO (2026-06-02): GATE #9 ESEGUITO → guard OK, E2E send BLOCCATO da split sessione WA (NUOVO: C-WA-SEND-SPLIT)
**Gate fisico eseguito con Luke.** SEED reale dalla SIM TEST_FOUNDER `393314928901` → `reply_d18d7dc6` (`approved=NULL` PRE = P1 runtime confermato). Luke `/approva reply_d18d7dc6` da TG (niente precheck-block).
- **Guard HITL CORRETTO:** `approved=NULL→1`, tentato invio post-sleep, invio fallito (`node sender rc=1`), `sent` **giustamente NON marcato** (`sent=0` onesto, niente latent bug su questo path/evento).
- **Window-integrity OK (non-VOID):** `uptime_sec` PRE=2719 → POST=4370, nessun restart daemon nei ~12 min.
- **❌ NUOVO BLOCKER — C-WA-SEND-SPLIT:** log daemon `/tmp/argos-tg-send.log` → `❌ Sessione non trovata: ~/.wwebjs_auth/session-argos-business`. Il path `/approva` NON invia via daemon connesso: spawna standalone `~/Documents/app-antigravity-auto/wa-sender/send_message.js` (CLIENT_ID `argos-business`, `telegram-handler.py:45-47`) che cerca auth in `~/.wwebjs_auth/session-argos-business` (INESISTENTE). Daemon connesso usa auth dir diversa (`wa-intelligence/.wwebjs_auth`). Due client whatsapp-web.js → uno solo autenticato → invio path-TG fallisce SEMPRE.
- **NO business-hours gate** sul send path (`cmd_approva` non controlla orario — verificato): il fallimento è solo la sessione mancante, non l'orario.

**#9 RICLASSIFICATO:** resta **PENDING-GATE**, ora **BLOCKED-ON fix codice C-WA-SEND-SPLIT** (NON più Luke fisico: il SEED fisico è stato dato e ha funzionato). **VERIFIED resta 2/9.**

**NEXT (S229) — fix C-WA-SEND-SPLIT (delega devops-automator, time-boxed):** instradare l'invio del path Telegram attraverso il **daemon connesso** (single-writer già autenticato, principio bridge S173) invece di spawnare `send_message.js` standalone. Aggancia backlog "migrare path legacy TG al bridge canonico". Opzioni da valutare in apertura: (a) POST al daemon `:9191/send` con X-API-Key; (b) far puntare `send_message.js` alla stessa auth dir del daemon — SCARTATA a priori se i due client girano simultaneamente (LocalAuth lock whatsapp-web.js). Dopo il fix: ri-eseguire GATE PACKET #9 v2 (SEED già provato raggiungibile) → Scenario A msg ARRIVA sulla SIM + `[SENT]` → #9 VERIFIED 3/9. Scenario B (rifiuta durante sleep → `[ABORT]`) resta da provare.

**Scenario B NON eseguito** (bloccato a monte dal send split): da fare in S229 dopo il fix.

---

## ⏹ S227 — ESITO (2026-06-02): FONDAMENTA C-DB-SPLIT-001/C-DB-ENV-001 CHIUSA VERDE
**FATTO (runtime-verified via devops-automator, R1):** stack iMac ora gira sul DB CANONICO ROOT.
- **Root cause vera ≠ diagnosi S226.** Non era `dump.pm2` (già=ROOT). Era: `wa-intelligence/ecosystem.config.js` calcola `ARGOS_DB_PATH=path.join(BASE,'dealer_network.sqlite')` con BASE=`dirname(__dirname)` → dentro una release punta al DB della release; e **`deploy/sync.sh` linkava `.env` ma NON il DB** (rsync esclude `*.sqlite`) → ogni release nasceva senza DB e SQLite ne auto-creava uno VUOTO → split.
- **Fix permanente (repo):** `deploy/sync.sh` step [4/6] ora linka il DB canonico nella release (`ln -sfn $REMOTE_BASE/dealer_network.sqlite $RELEASE_DIR/dealer_network.sqlite`, pattern Capistrano linked-file). Previene la ricaduta.
- **Fix one-time (iMac):** `releases/20260527_083951/dealer_network.sqlite` (vuoto) → backup `.empty-bak-20260602_193153` + symlink `→ ../../dealer_network.sqlite` (ROOT). I 4 processi condividono quella stringa env → un solo symlink li redirige tutti su ROOT. Restart 4 proc + `pm2 save`.
- **Verifica runtime:** wa_status `connected` PRE/POST (sessione WA INTATTA), lsof daemon→ROOT, stack legge `pending_replies=21` + TEST_FOUNDER `DOSSIER_SENT`.
- **Step 5 "WA session fuori da releases" GIÀ soddisfatto:** auth a `wa-intelligence/.wwebjs_auth` (livello BASE).
- **Rollback manuale (se servisse):** `ssh imac 'cd ~/Documents/app-antigravity-auto/releases/20260527_083951 && pm2 stop argos-wa-daemon argos-tg-bot argos-cf-monitor argos-dashboard && rm dealer_network.sqlite && mv dealer_network.sqlite.empty-bak-20260602_193153 dealer_network.sqlite && pm2 start argos-wa-daemon argos-tg-bot argos-cf-monitor argos-dashboard'`

**#9 RICLASSIFICATO:** non più `BLOCKED-ON C-DB-ENV-001` (risolto). Ora **BLOCKED-ON Luke fisico** (SEED inbound dalla SIM TEST_FOUNDER). VERIFIED resta 2/9 → sale a 3/9 al gate fisico.

**NEXT (S228):** eseguire GATE PACKET #9 v2 (sotto, invariato) con Luke. PRE già fatto (deploy f63a1ee LIVE + stack su ROOT). Serve solo: Luke manda WA dalla SIM → reply_id → Scenario A/B. Verità di PASS = msg fisico sulla SIM (sent è TAINTED). Chiusura: #9→VERIFIED 3/9 o handoff.

---

## ▶ APERTURA (storico S227 — fondamenta ora CHIUSA, vedi ESITO sopra)
Sei CC che apre S227 su ARGOS. Internalizza R1–R4 + budget-rule (più sotto) e applicali. Stato: P0 deploy `f63a1ee` GIÀ LIVE su iMac; anello #9 = PENDING-GATE **BLOCKED-ON C-DB-ENV-001** (NON Luke fisico). VERIFIED 2/9. Il gate #9 è irraggiungibile finché lo stack gira sul DB sbagliato.
**Questa sessione fa UNA cosa: la fondamenta C-DB-ENV-001/C-DB-SPLIT-001 (R3, time-boxed 1 sessione), poi se avanza budget rieseguи il GATE PACKET #9 v2.** Delega a `devops-automator`. Esegui i 5 step del blocco "NEXT (S227)" qui sotto, in ordine, fermandoti se uno non passa. NON flippare l'env senza riconciliare i dati (R4 — è ciò che ha bloccato S226). Verità #9 = msg fisico sulla SIM (sent TAINTED). Chiusura: #9→VERIFIED 3/9 o handoff PENDING-GATE; mai chiusura silenziosa al budget.

---

## ⏹ S226 — ESITO (2026-06-02, chiusura ordinata al 59% budget)

**FATTO (runtime-verified, R1):**
- **P0 deploy `f63a1ee` su iMac = LIVE.** md5 locale==iMac sui 2 file in entrambi i path (root daemon + release tg-bot), healthcheck `:9191` HTTP 200, `wa_status: connected`. Backup `.bak-pre-f63a1ee` su 4 file → rollback 10s.
- **C-WA-RESTART window-integrity = PRONTO.** Campo PRE/POST = `pm2_env.restart_time` (valore 50 su `argos-wa-daemon`). Meccanismo gate disponibile.

**ROOT-CAUSE SCOPERTA (vero deliverable S226):** il gate #9 NON era raggiungibile, e NON per "Luke fisico". Inbound reale TEST_FOUNDER `393314928901` → daemon lo SCARTA "non in pipeline" (`wa-daemon.js:577-588` `lookupDealer` SELECT su `conversations`). Causa: **tutti e 4 i processi PM2 girano sul DB RELEASE sbagliato** (`releases/20260527_083951/dealer_network.sqlite`, 28KB, schema base 15 col, 0 `pending_replies`), via `ARGOS_DB_PATH` settato in **`~/.pm2/dump.pm2`** (NON in `sync.sh`). Il DB ROOT autoritativo (`~/Documents/app-antigravity-auto/dealer_network.sqlite`, 389KB, schema 30 col post-S201/S202, riga TEST_FOUNDER `current_step=DOSSIER_SENT opt_out=0`) è scavalcato. → **C-DB-ENV-001 + C-DB-SPLIT-001 VIVI = root cause strutturale di C-E2E-ZERO.**

**PERCHÉ NON HO FLIPPATO L'ENV (R4, challenge Luke corretto):** né ROOT né RELEASE è "il buono" pulito.
- ROOT: schema mantenuto + TEST_FOUNDER, MA dati congelati al 2026-05-16 (`conversations` max `state_updated_at`=16/05, 7 righe).
- RELEASE: DB runtime live, MA schema base (manca col `state_updated_at` ⇒ ALTER S201/S202 mai applicati) + quasi vuoto.
Env-flip secco = abbandona scritture RELEASE + schemi disallineati = violazione R4 (stato su dato non riconciliato). Serve sessione-fondamenta, non coda a 59%.

**#9 RICLASSIFICATO:** PENDING-GATE, `BLOCKED-ON: C-DB-ENV-001` (non più "Luke fisico"). **VERIFIED resta 2/9.** `UNVERIFIED-RUNTIME`: inbound→pending_reply · `/approva` runtime · Scenari A/B (tutti bloccati a monte dal DB sbagliato — non testabili finché lo stack gira su RELEASE).

**NEXT (S227) — fondamenta C-DB-ENV-001/C-DB-SPLIT-001, TIME-BOXED 1 sessione (delega devops-automator):**
1. DB canonico = **ROOT** (contratto riga 92 + default codice `telegram-handler.py:42` + schema mantenuto).
2. Riconciliare: verificare se RELEASE ha inbound/conversations post-16/05 da salvare → migrare su ROOT. Confermare schema ROOT completo per daemon Node (better-sqlite3 SELECT *).
3. Correggere `ARGOS_DB_PATH` dei 4 processi in `~/.pm2/dump.pm2` → ROOT · `pm2 save` · restart · verificare `pm2 jlist` DB=ROOT su tutti e 4.
4. Confermare `deploy/sync.sh` non re-introduca lo split (non setta ARGOS_DB_PATH — verificato; controllare che non copi un DB dentro release/).
5. SOLO DOPO: rieseguire GATE PACKET #9 v2 (invariato, sotto) → #9 VERIFIED 3/9. Setup WA session in `wa-intelligence/../wa-sender` + `.wwebjs_auth` (NON sotto releases → restart non perde QR).

---

## ▶ PROMPT DI APERTURA S226 — incolla/leggi questo, poi ESEGUI (non descrivere)

Sei CC che apre S226 su ARGOS. **Internalizza il contratto operativo R1–R4 + budget-rule (sotto) e applicalo**, non riassumerlo. Questa sessione fa **UNA cosa** sul percorso canonico `scrape→CoVe→PDF→WA→reply→sign→paid`; finché **C-E2E-ZERO è OPEN, VIETATO aprire file/feature fuori dal percorso** (R2).

Lo stato: anello #9 (HITL guard, commit `f63a1ee`) è **PENDING-GATE non DONE** — code-verified, MAI eseguito a runtime; il fix è su MacBook, **iMac gira la versione vecchia**. VERIFIED 2/9.

**Formato gate (vincolo #1b):** #9 → `TERMINAL_FACT = "msg fisicamente arrivato (o NON arrivato) sulla SIM TEST_FOUNDER nello scenario corretto"` · `BLOCKED-ON = Luke fisico sul gate`. È irraggiungibile-in-sessione → **NON ri-validarlo staticamente** (py_compile/simulazione = vietato come prova di chiusura). L'unico lavoro lecito = **renderlo raggiungibile** (P0 deploy + P1 runtime + packet pronto) o escalare. Stessa firma di C-SAN-001/C-E2E-ZERO che si avvitavano: non ricaderci.

**Esegui in quest'ordine, una cosa alla volta, fermandoti se un gate non passa:**
1. **C-WA-RESTART-001, time-boxed 1 sessione** (delega `devops-automator`). Criterio misurabile: "stabile" = 0 restart non-pianificati in 6h. Se la root-cause non emerge nel time-box → **fallback = window-integrity check** (leggi `restart_time` da `pm2 jlist` PRE/POST finestra test; se cambia → VOID+retry). NON inseguire la root-cause a oltranza (anti S159/S166).
2. **P0 — deploy `f63a1ee` su iMac** (`devops-automator`, rsync atomico + healthcheck). Senza, testi il bug non la fix.
3. **P1 — verifica runtime su iMac**: quale DB ospita `pending_replies` · un inbound da TEST_FOUNDER genera davvero riga `approved=NULL` · `/approva` accettato come testo. (R1: esecuzione reale, non py_compile.)
4. **Consegna il GATE PACKET v2 a Luke** (sotto) ed esegui il gate fisico su TEST_FOUNDER 393314928901.

**Verità di PASS (R4): `sent` è TAINTED** → la verità primaria dello Scenario A è "msg fisicamente arrivato sulla SIM" + log `[SENT]`; `sent=1` è solo conferma attesa. Divergenza (msg arrivato ma sent=0) = **finding** (latent bug storico vivo, aggancia S224-1), NON fail del guard.

**Condizione di chiusura S226 (budget-rule):** o #9 → **VERIFIED 3/9** (gate fisico passato + Luke "soddisfatto"), o handoff `PENDING-GATE` con packet già pronto + tag `UNVERIFIED-RUNTIME` su ciò che non hai provato a runtime. **Mai chiusura silenziosa al budget come `f63a1ee`.** Aggiorna QUESTO file (`.manual.md`, il hook auto-close NON lo clobbera) a fine sessione.

---

## DIAGNOSI (condivisa, ancorata ai dati) — il meta-bug è la CONDIZIONE DI CHIUSURA
~130 sessioni (S94→S225), superficie enorme, **E2E integrato = 0**, **VERIFIED 2/9** anelli, e un campo
di stato auto-riportato (`sent` sul path Telegram) si è rivelato **falso**. Pattern reale: ottimismo in
build-mode → audit reattivo che bonifica. La bonifica è ottima ma è governance, non prevenzione.
Tre problemi: (1) costruisce componenti, non chiude la catena; (2) chiude al limite di budget non di
verifica (es. `f63a1ee`: fix di un path verificato-rotto, committato senza ri-review per "chiusura budget");
(3) verifica lo strato sbagliato (py_compile/simulazione, non runtime) → il bug quoting `cmd_approva`
ha tenuto `UPDATE sent=1` MAI eseguita per tempo ignoto, runtime silenziosamente rotto.

## 5 REGOLE OPERATIVE (estensione, NON sostituzione dei meccanismi che già funzionano)
Tieni: evidence path:riga su ogni claim · separazione code-verified vs E2E reale · scope-fence per sessione · self-audit con de-idratazione overclaim.

- **R1 — Chiusura a due binari.**
  • *Runtime-verificabile* (lo provi da solo): DONE solo dopo **esecuzione reale del path** (output reale, non "compila"/simulazione).
  • *Human-gated* (HITL / E2E founder / dealer reale): **MAI VERIFIED**. Commit `PENDING-GATE` + produci **GATE PACKET** pronto (comando esatto, scenario A/B, durata, cosa osservare, criterio pass) così Luke chiude in <10 min. La latenza del gate umano è il vero collo di C-E2E-ZERO: riducila preparando il packet, non aspettando.
- **R2 — Catena prima della superficie.** Percorso canonico unico: `scrape → CoVe → PDF → WA → reply → sign → paid`. Finché C-E2E-ZERO è OPEN: VIETATO aprire file/feature fuori dal percorso. Ogni sessione muove UN anello verso VERIFIED o consolida una fondamenta che lo blocca (R3). Niente espansione laterale (anti S159/S166).
- **R3 — Fondamenta = prerequisito, non feature.** Prima dell'E2E reale: (a) DB autoritativo unico (C-DB-SPLIT-001 + C-DB-ENV-001); (b) daemon stabile (C-WA-RESTART-001). **Time-box obbligatorio** (vedi sotto) o R3 diventa il buco-senza-fondo che vuole prevenire.
- **R4 — Niente stato su dato non riconciliato.** Dopo un bug che corrompe un campo, quel campo è **TAINTED** finché non riconcili. Concreto: `sent` su path TG inaffidabile → NON usarlo come verità. Reconcile = backlog **S224-1**.
- **Budget-rule (il meta-bug).** Se il context finisce PRIMA della verifica runtime R1: NON committare come DONE. Commit su branch + tag `UNVERIFIED-RUNTIME` + handoff dichiara "manca verifica runtime: <cosa>". Mai più una chiusura silenziosa al budget come `f63a1ee`.

## STATO ANELLO #9 (HITL guard) — riclassificato R1
**PENDING-GATE, non DONE.** `f63a1ee` è *code-verified only* (py_compile + simulazione). **VERIFIED resta 2/9** (#1, #6). Sale a 3/9 solo a gate fisico passato. Il fix è su MacBook; **l'iMac gira la versione vecchia** → senza deploy (P0) testi il bug, non la fix.

Comando reale (`wa-intelligence/telegram-handler.py:10-12,171-347`): `/approva <reply_id>`, `/rifiuta <reply_id>`.
Sleep anti-ban **random 90–720s** (`SLEEP_MIN,SLEEP_MAX = 90,720`, riga 52 — NON 90s fisso). Segnale indipendente da `sent`: log `[SENT]`/`[ERROR] rc=`/`[ABORT]` dal send_script (righe 262-277).

## GATE PACKET #9 — v2 (corretto: sent TAINTED + window-integrity)
```
PRE (CC): P0 deploy f63a1ee su iMac (rsync atomico + healthcheck — via devops-automator)
          P1 verifica runtime su iMac: DB di pending_replies · inbound TEST_FOUNDER genera
             riga approved=NULL · /approva accettato come testo (non solo inline button)

SEED (Luke ~1min): WA da SIM TEST_FOUNDER 393314928901 → numero ARGOS Business → annota reply_id da notifica TG

SCENARIO A — invio consentito:
  pm2 jlist → annota restart_time PRE
  /approva <reply_id> · attendi 90–720s
  PASS A (verità primaria) = msg ARRIVATO sulla SIM (osservazione Luke) + log [SENT]
  CONFERMA attesa (tertiaria, TAINTED, non decide) = sent=1
  DIVERGENZA (msg arrivato MA sent=0) = NON FAIL del guard → prova viva del latent bug storico → FINDING, aggancia S224-1
  pm2 jlist → restart_time POST; se ≠ PRE → VOID, retry

SCENARIO B — revoca durante sleep (nuovo reply_id2):
  pm2 jlist → restart_time PRE
  /approva <reply_id2> · SUBITO (<60s) /rifiuta <reply_id2>
  PASS B = NESSUN msg sulla SIM + log [ABORT] + sent=0 + approved=0
  pm2 jlist → restart_time POST; se ≠ PRE → VOID, retry (NON interpretare "no msg" come PASS)

EVIDENCE: osservazione fisica Luke (A+B) | log daemon [SENT]/[ABORT]/[ERROR] |
          SELECT id,approved,sent FROM pending_replies WHERE id IN (r1,r2) | restart_time PRE/POST
CHIUSURA: Luke "soddisfatto" → #9 DONE, VERIFIED 3/9.
```
Nota window-integrity: il gate **non** richiede C-WA-RESTART chiuso, richiede di SAPERE se il daemon è ripartito nei ~12 min del test. Il check `restart_time` PRE/POST (`pm2 jlist` → confermare nome campo sulla versione iMac) rende lo Scenario B interpretabile senza prima stabilizzare del tutto il daemon.

## ORDINE ESECUZIONE S226 (una cosa alla volta, sul percorso canonico)
1. **C-WA-RESTART-001 — time-boxed**: "daemon stabile" = 0 restart non-pianificati in finestra 6h (criterio misurabile, NON "root-cause trovata"). Root-cause time-box = 1 sessione; se non emerge → fallback = window-integrity check nel packet (sufficiente a rendere B interpretabile). Foundation completa resta task R3, **fuori dal critical-path del gate**.
2. **P0 deploy `f63a1ee`** su iMac (devops-automator). NB: codice solo su MacBook ora.
3. **P1 verifica runtime** su iMac (i 3 punti del PRE).
4. **Consegna GATE PACKET v2 a Luke** ed esegui il gate.

## VINCOLI / NON TOCCARE
- TEST_FOUNDER 393314928901 prima di qualsiasi dealer reale. **Domenica = OFF Luke** (no scadenze domenicali).
- `image_sanitizer.py` + scope partner-unico (landing/Gemini/trasporto) **CONGELATO**. No deploy landing/PDF.
- Day 1 Stile Car blocker invarianti: C-SAN-001, **C-E2E-ZERO**, C-COMM-INTEL-001, C-GATE-FONTE-001.
- Fondi di verità: `PLAN.md` (carte C-DB-SPLIT:178, C-WA-RESTART:179, C-E2E-ZERO:182). DB iMac autoritativo = `~/Documents/app-antigravity-auto/dealer_network.sqlite`.

## BACKLOG (non scope S226 salvo R4)
- **[S224-1]** Reconcile path TG: quante righe `pending_replies` con `approved=1 AND sent=0` ma msg realmente inviato (dati `sent` storici inaffidabili). Prerequisito R4 per fidarsi di metriche di invio su path TG.
- Migrare path legacy multi-msg + Telegram al **bridge canonico** (single-writer S173) → elimina la classe di bug.
- Verifica anelli #2..#5, #7, #8 per salire VERIFIED oltre 3/9.
