# S241 — Ripartenza

## ✅ S240 — ESITO (2026-06-06): #9 Scenario B test fisico → BLOCKED-ON infra (NON codice). Chiusa HANDOFF pulito.

### COSA È SUCCESSO
- Test fisico reject eseguito: Luke ha mandato WA da SIM TEST_FOUNDER `393314928901` → analyzer ha inserito `reply_f4a419e8` + notifica TG con 3 bottoni → Luke ha tappato **🚫**.
- Risultato DB: `approved=NULL, sent=0` (NON `approved=0` atteso). **`cmd_rifiuta` non è mai partito.**
- **Root cause = INFRA, non logica HITL**: il polling del tg-bot (`telegram-handler.py:993-999`) usa long-poll `getUpdates {timeout:30}`. Da ~05/06 ogni chiamata fallisce `read operation timed out` (log `argos-tg-bot`). `curl https://api.telegram.org` riesce in 0.16s → rete OK, ma la connessione tenuta aperta 30s droppa (sospetto wifi/NAT idle iMac 2012). `getUpdates` non ritorna mai → callback bottoni MAI processati → `approved` resta NULL. Restart bot (↺27→28) NON risolve. Offset (`:1002`, `/tmp/argos-tg-offset.txt`) non avanza → tap in coda ma irraggiungibile.
- **Codice reject SANO**: confermato S239 + funzionava il 03-04/06 (log `Callback ricevuto: rifiuta:reply_ec6bdb52` ecc.). Guard `cmd_rifiuta` :422-434 + branch :1021-1022 verificati.

### NEXT (S241) — PRIMO E UNICO: ripristinare polling tg-bot, poi chiudere #9B
1. **Fix candidato (1 riga, da testare)**: `telegram-handler.py:997` long-poll `timeout:30` → `timeout:10` (o `0` short-poll + sleep nel loop), più robusto su connessione flaky iMac. Verifica anche read-timeout di `tg_post` (urlopen).
2. **Deploy 2-path SEMPRE**: ROOT + `current/` (consulta `reference_imac_deploy_paths.md`). Restart `argos-tg-bot`.
3. **Prova polling vivo**: log mostra `Callback ricevuto:` su un tap di test (il tap di `f4a419e8` potrebbe ancora essere in coda < 24h e venir pescato al primo getUpdates riuscito → controlla DB).
4. **Ri-test fisico #9B** (BLOCKED-ON Luke al telefono): SIM TEST_FOUNDER → WA POSITIVE → tap 🚫 → PROVA = DB `pending_replies.approved=0 AND sent=0`. Window-integrity: `argos-wa-daemon` ↺50 invariato.
5. PASS → anello #9 chiuso (A già VERIFIED S230). VERIFIED → 4/9.

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
