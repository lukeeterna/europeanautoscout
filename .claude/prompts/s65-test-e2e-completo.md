Sessione 65 — TEST E2E COMPLETO + fix analyzer + cleanup + Day 3 automatico.

CONTESTO RAPIDO:
- wa-daemon v3 ONLINE su iMac (better-sqlite3 nativo, scheduler Day3/Day7 integrato)
- WA Business: SESSIONE ATTIVA, numero 328-1536308
- PM2: argos-dashboard ONLINE, tg-bot ONLINE, wa-daemon ONLINE (77MB, porta 9191)
- OpenRouter: key RIATTIVATA, ~$4.98 credito, Haiku 4.5
- Dealer TEST_FOUNDER (380-7769822, RAGIONIERE) in DB, Day 1 inviato
- SALERNO_001 (NARCISO) e SALERNO_002 (BARONE): Day 1 inviato il 18/03, Day 3 previsto il 21/03
- iMac SSH: ssh gianlucadistasi@192.168.1.2 (node: /usr/local/bin/node, pm2: ~/.npm-global/bin/pm2)
- better-sqlite3 installato in wa-intelligence/node_modules/

TASK S65 — IN ORDINE DI PRIORITA':

1. FIX ANALYZER STDIO (5 min):
   - wa-daemon.js: triggerAnalyzer() usa `stdio: 'ignore'` → impossibile debuggare
   - Cambiare a log file: stdio: ['ignore', fs.openSync('/tmp/argos-analyzer.log', 'a'), fs.openSync('/tmp/argos-analyzer.log', 'a')]
   - Verificare che il log si popoli al prossimo messaggio

2. TEST E2E COMPLETO (priorita' massima):
   - Founder invia messaggio WA dal 380-7769822 al 328-1536308
   - VERIFICARE OGNI STEP:
     a) wa-daemon riceve (log "MESSAGGIO IN ARRIVO") ← VERIFICATO S64
     b) lookupDealer trova TEST_FOUNDER ← VERIFICATO S64
     c) persistInboundMessage logga su SQLite ← VERIFICATO S64
     d) triggerAnalyzer parte ← VERIFICATO S64
     e) response-analyzer genera risposta LLM ← VERIFICATO S64 (manuale)
     f) auto_approve_and_send schedula invio ← DA VERIFICARE
     g) Dopo 2-12 min: risposta arriva al 380-7769822 via WA ← DA VERIFICARE
     h) Notifica Telegram al founder ← DA VERIFICARE
   - Se step f/g non funzionano: auto_approve_and_send usa send_message.js (vecchio sender)
     Potrebbe non funzionare perche' la sessione WA e' nel wa-daemon, non in send_message.js
     FIX: usare POST http://127.0.0.1:9191/send dal analyzer invece di send_message.js

3. FIX AUTO-INVIO (se necessario):
   - response-analyzer.py auto_approve_and_send() usa:
     `subprocess.Popen(['bash', '-c', f'sleep {sleep_s} && node {wa_sender} "{wa_id}" "{safe_text}"'])`
   - Questo chiama send_message.js che ha la SUA sessione WA (potrebbe essere diversa dal daemon)
   - FIX MIGLIORE: sostituire con curl POST a http://127.0.0.1:9191/send
     `subprocess.Popen(['bash', '-c', f'sleep {sleep_s} && curl -s -X POST http://127.0.0.1:9191/send -H "Content-Type: application/json" -d \'{{...}}\''])`
   - Questo usa la sessione WA del daemon (quella autenticata e funzionante)

4. CLEANUP DB:
   - Rimuovere pending_replies orfane (dealer_id = 'UNKNOWN')
   - Rimuovere messaggi test vecchi

5. FIX TELEGRAM MARKDOWN:
   - response-analyzer.py: le notifiche Markdown falliscono → aggiungere sanitize degli underscore/asterischi
   - Oppure inviare sempre in plain text (piu' affidabile)

6. VERIFICARE SCHEDULER Day 3:
   - Il 21 marzo scatta il Day 3 per SALERNO_001 e SALERNO_002
   - Verificare che lo scheduler li trovi (query: DAY1_SENT + 3 giorni)
   - Se i template sono corretti per NARCISO e BARONE
   - Lo scheduler gira solo in orario business (9-18)

7. CF TUNNEL PERMANENTE (se tempo):
   - Quick tunnel scade → named tunnel
   - MAI TOCCARE ~/.cloudflared/config.yml (FLUXION!)
   - Usare config separata per ARGOS

PERSONA: Luca Ferretti, ARGOS Automotive
REGOLA: Tutto gira su iMac. Mai lanciare processi WA/dashboard su MacBook.
REGOLA: MAI menzionare CoVe/Claude/AI/Anthropic nei messaggi dealer.
REGOLA: MAI toccare config Fluxion (~/.cloudflared/config.yml).
REGOLA: wa-daemon processa SOLO numeri in pipeline DB (guardrail fondamentale).
REGOLA: OpenRouter key nel .env iMac — verificare che sia attiva prima di testare.
Procedi autonomamente. Sei il CTO.
