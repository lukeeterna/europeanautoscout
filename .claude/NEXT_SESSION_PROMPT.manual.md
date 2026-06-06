# S242 — Ripartenza

## ✅ S241 — ESITO (2026-06-06): diagnosi S240 SMENTITA dai fatti. Bot tg VIVO, token VALIDO. Anello #9B ancora NON verificato ma la root cause è cambiata. Chiusura ordinata a 60% context.

### COSA HO PROVATO (con evidenza, non a priori)
1. **Token Telegram VALIDO** — `getMe` → `{"ok":true,...,"username":"Argosautomotivebot","id":8691360619}`. → La diagnosi S240/agent-ops **"token revocato / HTTP 404" è FALSA (allucinata)**.
2. **Nessun webhook, nessun conflitto strutturale** — `getWebhookInfo` → `url:""`, `pending_update_count:0`.
3. **Istanza singola** — `ps aux|grep telegram-handler` = 1 processo (pid 46659, release `20260527_083951`). Nessun poller duplicato.
4. **Bot processa i MESSAGE update** — `/help` mandato da Luke alle 17:55:21 → log `Comando ricevuto: /help` + risposta con sottomenu ricevuta. Transport+processing per *message* PROVATO VIVO.
5. **Bot stava pollando alle 17:52** — mia probe `getUpdates` concorrente → `409 Conflict` (= prova che il bot long-pollava). Anche agent-ops ha ricevuto questo **409** e l'ha riportato come "token invalido": ecco la radice dell'allucinazione.
6. **I read-timeout sono RARI** — ~30 `read operation timed out` in 24h su ~2880 poll/giorno = **~1%**. Il polling NON era "morto 24h" (conclusione S240 troppo forte). Su timeout `tg_post` (:125-137) inghiotte l'eccezione, ritorna `{}`, offset NON avanza (`save_offset` solo su update iterato, :1002-1003) → Telegram **ri-consegna** → un timeout da solo NON perde l'update.

### ⚠️ ANELLO #9B ANCORA ROSSO — nuovo quadro, nuova ipotesi
Test #9B eseguito: WA *"Ok mi interessa"* da SIM TEST_FOUNDER `393314928901` alle 18:40:13 → wa-daemon log `MESSAGGIO IN ARRIVO` + `Telegram alert dispatched` + analyzer triggato 18:40:28 → **nuovo reply creato `reply_94678456`** (approved=NULL, sent=0, reply_label=LLM_MULTI). Luke **conferma di aver ricevuto la notifica con i bottoni sul bot TG**.
MA: **nessun `Callback ricevuto` nel log tg-bot** dopo `/help` (17:55). `reply_94678456` resta `approved=NULL`. Stesso sintomo S240 riprodotto.

**CONTRADDIZIONE CHIAVE (vero punto S242)**: un *message* (`/help`) viene processato, un *callback_query* (tap 🚫) NO — stesso loop `run_daemon()` (:993-1047), stesso `allowed_updates=['message','callback_query']`. Perché solo i callback spariscono?

**SEGNALE NUOVO (fine S241)**: dopo `/help` (17:55) il log tg-bot è **completamente muto ~50min** (né timeout né callback né 409). E la mia ultima probe `getUpdates?offset=-1&timeout=0` ha dato **`{"ok":true,"result":[]}` (NON 409)** → al momento della probe il bot **non era in mid-poll** + coda Telegram **vuota**. → **IPOTESI PRIMARIA S242: il loop tg-bot si è STALLATO dopo aver processato `/help`** (bloccato dentro un'iterazione, p.es. `send()`/`cmd_*` o un `urlopen` appeso senza che il timeout=40 scatti), quindi NON polla più → nessun callback raccolto. Il 409 alle 17:52 + `/help` 17:55 sono le ULTIME prove di vita; dopo, silenzio.

### NEXT (S242) — DIAGNOSI-FIRST sullo stallo del loop (REGOLA #0: delega ad agent-ops, MA verifica l'output — S241 ha mostrato che agent-ops allucina su questo task)
> **Lezione S241 sulla delega**: agent-ops ha ritornato diagnosi FALSA ("token revocato 404") perché ha scambiato un 409 per token-invalido. Delega pure in context isolato per non bruciare budget, MA il main context DEVE verificare il fatto terminale (`getMe`, `409` probe, log reale) prima di accettare il verdetto. Non fidarsi del summary del subagent.

1. **Il bot è ancora vivo/iterante ADESSO?** Probe `getUpdates` con `timeout=1`: se **409** → polla (vivo); se **`ok:true result:[]`** ripetuto → NON polla = **stallo confermato**. Ripeti 2-3 volte a distanza di ~5s per distinguere "tra un poll e l'altro" da "fermo".
2. Se stallo → **dove è bloccato**: `sample`/`spindump` del pid (macOS) o controlla CPU `ps`. Cerca se è dentro `urlopen` (connessione appesa) o dentro `send()`/`cmd_*`. Il `/help` ha risposto, quindi lo stallo è DOPO — sospetto: un `urlopen` di `getUpdates` che si appende SENZA far scattare il timeout=40 (connessione half-open su wifi iMac), oppure `answerCallbackQuery`/`send` bloccante.
3. **Fix probabile (decidere DAI dati, non a freddo)**: (a) aggiungere `socket.setdefaulttimeout()` o assicurare che TUTTI gli `urlopen` abbiano timeout effettivo; (b) **liveness/watchdog**: assert che il loop completi un giro entro N secondi, altrimenti log `STALL` + `sys.exit(1)` → PM2 riavvia (autorestart attivo). Questo trasforma uno stallo silenzioso in auto-recovery. (c) valutare riavvio periodico tg-bot via PM2 cron come cerotto se la causa rete è irriducibile su iMac 2012.
4. **Chiusura #9B**: `reply_94678456` è già in DB (approved=NULL, SAFE). Dopo il fix + restart, ri-test: WA POSITIVE da SIM → tap 🚫 → atteso log `Callback ricevuto: rifiuta:reply_xxx` + DB `approved=0` → **#9B VERIFIED 4/9**. Il reply vecchio si può anche solo ri-tappare se la notifica è ancora viva (<48h).

### STATO PULITO LASCIATO
- `reply_94678456` (nuovo, S241) e `reply_f4a419e8` (vecchio, S240): entrambi `approved=NULL, sent=0` = **SAFE** (guard `WHERE approved=1` impedisce invio accidentale). Non toccare.
- Bot tg riavviato in S240 ↺28 (pid 46659). NON l'ho riavviato in S241 (per non perdere lo stato di stallo da diagnosticare in S242). **Se vuoi sbloccare subito #9B prima della diagnosi: `pm2 restart argos-tg-bot` e ri-tappa** — ma così perdi la prova dello stallo.
- DB canonico pending_replies = `~/Documents/app-antigravity-auto/dealer_network.sqlite` (ROOT). Schema reale: PK=`id` (NON reply_id), colonne `approved/sent/reply_label/created_at`. `.env` token in `current/wa-intelligence/.env` var `ARGOS_TELEGRAM_TOKEN`.
- `argos-wa-daemon` invariato.

### PROBE UTILI (copia-incolla, token mai stampato)
```
# getMe (validità token)
ssh imac 'T=$(grep -E "^ARGOS_TELEGRAM_TOKEN=" ~/Documents/app-antigravity-auto/current/wa-intelligence/.env|head -1|cut -d= -f2-|tr -d " \t\r\n"); curl -s -m10 "https://api.telegram.org/bot$T/getMe"; echo'
# liveness (409=vivo / ok:true=non in poll)
ssh imac 'T=$(grep -E "^ARGOS_TELEGRAM_TOKEN=" ~/Documents/app-antigravity-auto/current/wa-intelligence/.env|head -1|cut -d= -f2-|tr -d " \t\r\n"); curl -s -m6 "https://api.telegram.org/bot$T/getUpdates?offset=-1&timeout=1"; echo'
# log + stato reply
ssh imac 'tail -n 8 /tmp/argos-tg-bot-out.log; sqlite3 -header ~/Documents/app-antigravity-auto/dealer_network.sqlite "SELECT id,approved,sent FROM pending_replies ORDER BY created_at DESC LIMIT 3;"'
```

### Mappa anelli E2E (autoritativa)
| # | Anello | Stato |
|---|---|---|
| 1 | invio Day1 WA | VERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED (S202) |
| 9A | approve → send | VERIFIED (S230) |
| 9B | reject → abort | codice SANO (S239); transport message OK (/help); **callback NON raccolto — ipotesi stallo loop tg-bot** ← NEXT |
| 5/6/7 | dossier→approve→invio PDF | parziali |
| 8 | contract → sign_url | BLOCKED |

### Memorie da aggiornare in S242 (NON fatto in S241 per budget)
- `s240_gate9B_blocked_tg_getupdates.md` → **CORREGGERE**: la conclusione "polling morto / BLOCKED-ON infra" è smentita. Token valido, bot processa /help, ipotesi reale = stallo loop post-iterazione. Lezione delega: agent-ops allucina 409→"token revocato".

### Vincoli S242: TEST_FOUNDER 393314928901 prima di dealer reali · `image_sanitizer`(D-32)/landing CONGELATI · iMac clock skew (DB `created_at` ~-2h vs wa-daemon log) · deploy 2-path · consultare `reference_imac_deploy_paths.md` per OGNI path iMac.
