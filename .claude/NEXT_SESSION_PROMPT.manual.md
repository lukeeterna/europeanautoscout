# S241 — Ripartenza

## ✅ S240 — ESITO (2026-06-06): #9 Scenario B test fisico → BLOCKED-ON infra (NON codice). Chiusa HANDOFF pulito.

### COSA È SUCCESSO
- Test fisico reject eseguito: Luke ha mandato WA da SIM TEST_FOUNDER `393314928901` → analyzer ha inserito `reply_f4a419e8` + notifica TG con 3 bottoni → Luke ha tappato **🚫**.
- Risultato DB: `approved=NULL, sent=0` (NON `approved=0` atteso). **`cmd_rifiuta` non è mai partito.**
- **Root cause = INFRA, non logica HITL**: il polling del tg-bot (`telegram-handler.py:993-999`) usa long-poll `getUpdates {timeout:30}`. Da ~05/06 ogni chiamata fallisce `read operation timed out` (log `argos-tg-bot`). `curl https://api.telegram.org` riesce in 0.16s → rete OK, ma la connessione tenuta aperta 30s droppa (sospetto wifi/NAT idle iMac 2012). `getUpdates` non ritorna mai → callback bottoni MAI processati → `approved` resta NULL. Restart bot (↺27→28) NON risolve. Offset (`:1002`, `/tmp/argos-tg-offset.txt`) non avanza → tap in coda ma irraggiungibile.
- **Codice reject SANO**: confermato S239 + funzionava il 03-04/06 (log `Callback ricevuto: rifiuta:reply_ec6bdb52` ecc.). Guard `cmd_rifiuta` :422-434 + branch :1021-1022 verificati.

### NEXT (S241) — DIAGNOSI-FIRST del transport polling, NIENTE patch speculativa

> **⚠️ PRIMA AZIONE OBBLIGATORIA (REGOLA #0 — lezione S240)**: l'intera diagnosi che segue va DELEGATA a `Task(subagent_type=agent-ops)` in context dedicato — NON eseguita inline con Bash/Read nel main context. Motivo: S240 ha bruciato il budget (chiusura forzata al 60%) facendo la diagnosi inline; i ~10 round-trip ssh + output verboso (pm2/log/lsof) vanno nel context del subagent, che ritorna solo il verdetto (~200 parole: root cause + fix proposto + evidenze). Il main context si riserva alla DECISIONE sul fix, non all'esecuzione della diagnosi.
**Ipotesi "bug logico timeout" REFUTATA con dati (S240)**: `tg_post` riga 133 = `urlopen(timeout=40)`; long-poll riga 997 = `timeout:30`. Client 40s > long-poll 30s → config CORRETTA, nessun mismatch. Un poll sano ritorna ≤30s. Quindi `timeout:30→10` NON è un fix di logica, è una pezza di rete speculativa → NON applicarla a freddo.

**Cosa dicono i dati**: `read timed out` a 40s = la connessione tenuta aperta stalla >40s a livello rete (GET veloci passano in 0.16s). MA il loop polling è stato letto (`:993-1047`) e refuta il backoff:

**Ipotesi "backoff lungo" REFUTATA (S240, lettura :1026-1047)**: `tg_post` (:125-137) inghiotte la propria eccezione e ritorna `{}` sul timeout. Quindi nel loop il timeout dà `result.get('result',[])=[]`, nessuna eccezione propagata, retry IMMEDIATO. `time.sleep(5)` (:1047) scatta SOLO su eccezione nel branch processing, NON sul timeout getUpdates. → nessun backoff.

**CONTRADDIZIONE APERTA = vero punto S241**: se ci fosse retry immediato su timeout vedremmo "TG error" ogni ~40s; invece sono radi (1 ogni 30min-2h) → la maggior parte dei poll RIESCE. Ma allora perché il tap su `reply_f4a419e8` non è MAI loggato `Callback ricevuto`? Polling per-lo-più-vivo + tap mai ricevuto NON torna col solo timeout di rete.

**SOSPETTO PRIMARIO spostato da rete → OFFSET**: `/tmp/argos-tg-offset.txt` potrebbe essere AVANTI rispetto all'`update_id` del tap (offset persistito oltre il tap, o update perso in un long-poll scaduto e mai ri-richiesto correttamente) → Telegram non ri-consegna mai quell'update. **Diagnostico decisivo S241**: leggere valore `/tmp/argos-tg-offset.txt` su iMac e confrontarlo con gli update_id pendenti (`getUpdates` con offset basso/negativo per ispezione). Root cause ANCORA NON provata: scegliere tra (a) offset ahead, (b) update perso in stall, (c) transport — DAI dati, non a priori.

**Procedura S241 (delega ad `agent-ops`, context isolato — REGOLA #0)**:
1. **Leggi** `telegram-handler.py` da riga 1026 in poi: come gestisce l'eccezione getUpdates (sleep/backoff?). Questo spiega gli errori radi e se il loop si auto-strozza.
2. **Probe live**: `agent-ops` esegue su iMac un `getUpdates {timeout:30}` cronometrato, ripetuto 3-4 volte. Misura: stalla sistematicamente? a quale soglia (10/20/30s)? Solo QUI si decide il fix con dati — non prima.
3. **Verifica anti-conflitto**: `getWebhookInfo` (se webhook impostato → getUpdates 409, ma vediamo timeout non 409) + nessun secondo poller sullo stesso token.
4. Fix deciso DAI dati della probe (potrebbe essere: ridurre held-connection SE la probe mostra soglia di drop; oppure retry/keepalive; oppure altro). Deploy 2-path (`reference_imac_deploy_paths.md`) + restart.
5. **Liveness check** anti silent-death: pm2 diceva "online" con polling morto 24h+ → aggiungere assert che getUpdates ritorni entro timeout, altrimenti alert.

**Chiusura #9B a costo zero per Luke**: il tap di oggi su `reply_f4a419e8` è in coda Telegram (<24h, offset non avanzato riga 1002). Appena il polling torna vivo → pescato → `cmd_rifiuta` → DB `approved=0` → #9B VERIFIED 4/9 SENZA nuovo tap fisico. Verifica: log `Callback ricevuto: rifiuta:reply_f4a419e8` + DB. (Se >24h scaduto: ri-test fisico SIM TEST_FOUNDER → WA POSITIVE → tap 🚫.) Window-integrity: `argos-wa-daemon` ↺50 invariato.

### STATO PULITO LASCIATO
- `reply_f4a419e8`: `approved=NULL, sent=0` = **SAFE** (HOLD path, nessun Popen schedulato, guard `WHERE approved=1` impedisce invio accidentale). Non toccare.
- `argos-wa-daemon` ↺50 (pid 78295) invariato. `argos-tg-bot` riavviato ↺28 (pid 46659).
- DB canonico pending_replies = **ROOT** `~/Documents/app-antigravity-auto/dealer_network.sqlite` (daemon ce l'ha aperto; quello in `wa-intelligence/` è 0 byte morto).

### Memorie aggiornate S240
- `s240_gate9B_blocked_tg_getupdates.md` (nuova, finding completo).
- `reference_imac_deploy_paths.md` (aggiunta: invocazione pm2 = `export PATH=/usr/local/bin:$PATH; ~/.npm-global/bin/pm2 ...`; node `/usr/local/bin/node`; DB canonico pending_replies).

### Mappa anelli E2E (autoritativa)
| # | Anello | Stato |
|---|---|---|
| 1 | invio Day1 WA | VERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED (S202) |
| 9A | approve → send | VERIFIED (S230) |
| 9B | reject → abort | codice SANO; **test BLOCKED-ON polling tg-bot** ← NEXT |
| 5/6/7 | dossier→approve→invio PDF | parziali |
| 8 | contract → sign_url | BLOCKED |

### Vincoli S241: TEST_FOUNDER 393314928901 prima di dealer reali · `image_sanitizer`(D-32)/landing CONGELATI · iMac clock +2h · deploy 2-path · consultare `reference_imac_deploy_paths.md` per OGNI path iMac.
