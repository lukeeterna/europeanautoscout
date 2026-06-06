# S242 — Ripartenza

## 🔴 PRIORITÀ #0 S242 (decisa da Luke S241, NON ri-discutere) — CONSOLIDARE I FILE DI STATO
**Problema root (quantificato S241)**: 7+ file rispondono a "stato + cosa faccio dopo" e si contraddicono → ogni sessione riparte da zero, riscrive un handoff (spesso sbagliato, vedi S240) e ne aggiunge un altro. #9B ha richiesto 7 sessioni.
**Decisione presa**: UN solo source-of-truth = `STATE.md` a root con SOLO: (1) tabella anelli E2E + stato, (2) task corrente, (3) prossimi 3 step.
**Azioni S242 (fai PRIMA di toccare gli anelli)**:
1. Crea `STATE.md` a root (contenuto sotto: la mappa anelli + NEXT è già la roadmap).
2. Archivia in `archive/` o elimina: `HANDOFF.md`, `AUDIT_E2E.md`, `.claude/NEXT_SESSION_PROMPT.manual.md`, i 58 file `prompts/`.
3. **Disattiva l'hook auto-close** che rigenera `.claude/NEXT_SESSION_PROMPT.md` (usa skill `update-config`; è co-causa della proliferazione).
4. `PLAN.md` + `BACKLOG.md` restano ma referenziati da STATE.md (non duplicare lo stato lì).
5. MEMORY.md (cross-sessione) resta: scopo diverso. Ma valuta compattazione (2717 righe/256KB).
Done-condition: esiste `STATE.md`, gli altri handoff sono spariti, l'hook non rigenera più. Solo DOPO → anelli 5/6/7.

## ✅ S241 — CHIUSA VERDE (2026-06-06): Anello #9B VERIFIED. Diagnosi S240 era FALSA. Bot tg sano.

### ESITO #9B (reject → abort) — VERIFIED 4/9
Test fisico: WA *"Ok mi interessa"* da SIM TEST_FOUNDER `393314928901` (18:40) → analyzer crea `reply_94678456` + notifica TG con 3 bottoni → Luke tappa **🚫 Rifiuta** (18:51).
**Evidenza**: log `18:51:04 Callback ricevuto: rifiuta:reply_94678456` + DB `reply_94678456 | approved=0 | sent=0` (= reject corretto, nessun invio). Codice reject già SANO da S239. **#9B chiuso.**

### LEZIONE CRITICA S241 — la diagnosi S240 era interamente sbagliata
S240 concluse "polling morto 24h / token revocato / BLOCKED-ON infra". **Tutto falso**, provato in S241:
1. `getMe` → `ok:true` (`@Argosautomotivebot`). Token **VALIDO**.
2. `/help` processato (`Comando ricevuto: /help`). Bot **vivo**.
3. `409 Conflict` su probe getUpdates concorrente = bot **stava pollando**.
4. Il "tap mai ricevuto" di S240 = **semplicemente Luke non aveva tappato** (confermato S241: "non ho fatto il tap"). Nessun bug.
5. I `read operation timed out` sono ~1% dei poll (fastidio minore di rete iMac 2012, NON perde update perché offset avanza solo su poll riuscito).

**Lezione delega (REGOLA #0)**: agent-ops ha ritornato verdetto FALSO — ha scambiato un `409 Conflict` per "token revocato 404" e ha inventato la narrativa. Delegare per non bruciare budget va bene, MA il main context DEVE verificare il fatto terminale (`getMe`, probe `409`, log reale) prima di accettare il summary del subagent. Mai fidarsi del verdetto non verificato.

### RESIDUO MINORE (opzionale, NON blocca nulla)
~1% di `getUpdates` va in `read operation timed out` (wifi/NAT iMac 2012 droppa connessioni held). Impatto reale = zero (Telegram ri-consegna). **SE** si volesse hardening: watchdog liveness (assert giro loop < N s → `sys.exit(1)` → PM2 autorestart) o restart periodico tg-bot via cron. Bassa priorità. NON applicare patch timeout speculative (già refutate S240).

### Mappa anelli E2E (autoritativa)
| # | Anello | Stato |
|---|---|---|
| 1 | invio Day1 WA | VERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED (S202) |
| 9A | approve → send | VERIFIED (S230) |
| 9B | reject → abort | **VERIFIED (S241)** |
| 5/6/7 | dossier→approve→invio PDF | parziali ← prossimo focus |
| 8 | contract → sign_url | BLOCKED |

### NEXT (S242) — anelli 5/6/7 (dossier → approve → invio PDF)
Con #9A+#9B chiusi, il prossimo gap E2E sono gli anelli **5/6/7**: generazione dossier → approvazione HITL → invio PDF al dealer. Verificare stato reale su codice (non doc) prima di pianificare. Anello #8 (contract→sign_url) resta BLOCKED (dipende da Luke fisico / terzo).

### STATO PULITO
- `reply_94678456`: `approved=0, sent=0` = reject completato, SAFE. `reply_f4a419e8` (S240): `approved=NULL` SAFE (HOLD, mai consumato).
- Bot tg pid 46659 ↺28, sano. wa-daemon invariato. Nessun riavvio fatto in S241.
- DB canonico pending_replies = `~/Documents/app-antigravity-auto/dealer_network.sqlite` (ROOT). Schema: PK=`id`, colonne `approved/sent/reply_label/created_at`. Token in `current/wa-intelligence/.env` var `ARGOS_TELEGRAM_TOKEN`.

### PROBE UTILI (token mai stampato)
```
# getMe (validità token)
ssh imac 'T=$(grep -E "^ARGOS_TELEGRAM_TOKEN=" ~/Documents/app-antigravity-auto/current/wa-intelligence/.env|head -1|cut -d= -f2-|tr -d " \t\r\n"); curl -s -m10 "https://api.telegram.org/bot$T/getMe"; echo'
# log + stato reply
ssh imac 'tail -n 8 /tmp/argos-tg-bot-out.log; sqlite3 -header ~/Documents/app-antigravity-auto/dealer_network.sqlite "SELECT id,approved,sent FROM pending_replies ORDER BY created_at DESC LIMIT 3;"'
```

### Memorie da aggiornare in S242
- `s240_gate9B_blocked_tg_getupdates.md` → **CORREGGERE/SUPERSEDED**: conclusione "BLOCKED-ON infra / polling morto" FALSA. #9B VERIFIED S241, bot sano, root cause apparente = tap mai eseguito. Lezione delega: agent-ops allucina 409→"token revocato".

### Vincoli S242: TEST_FOUNDER 393314928901 prima di dealer reali · `image_sanitizer`(D-32)/landing CONGELATI · iMac clock skew DB `created_at` ~-2h vs wa-daemon log · deploy 2-path · consultare `reference_imac_deploy_paths.md` per OGNI path iMac.
