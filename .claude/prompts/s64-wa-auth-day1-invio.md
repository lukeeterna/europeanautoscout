Sessione 64 — TEST PIPELINE LIVE + fix dbExec + sequenza multi-step.

CONTESTO RAPIDO:
- Dashboard ARGOS Command Center LIVE su iMac:8080 (F1-F5 + WA Auth card)
- WA Business: SESSIONE ATTIVA (auth S63 18:30), numero 328-1536308
- PM2: argos-dashboard ONLINE, tg-bot ONLINE, wa-daemon ONLINE (85MB, porta 9191)
- wa-daemon ha /send + /send-voice endpoints
- edge-tts 7.2.7 su iMac, voce it-IT-DiegoNeural testata e funzionante
- Day 1 INVIATO a SALERNO_001 (Autovanny, NARCISO) e SALERNO_002 (FC Luxury, BARONE)
- GUARDRAIL: wa-daemon processa SOLO numeri presenti in conversations DB
- CF Quick Tunnel potrebbe essere scaduto — rilanciare: cloudflared tunnel --config /dev/null --url http://localhost:8080
  MAI TOCCARE ~/.cloudflared/config.yml (FLUXION!)
- iMac SSH: ssh gianlucadistasi@192.168.1.2 (node: /usr/local/bin/node, pm2: ~/.npm-global/bin/pm2)

TASK S64 — TEST PIPELINE END-TO-END:

1. SETUP DEALER TEST (per founder che si finge dealer):
   - Il founder usera' il numero 328-1536308 per inviare messaggi come "dealer"
   - PROBLEMA POSSIBILE: e' lo stesso numero del WA Business che invia.
     whatsapp-web.js potrebbe non ricevere self-messages come inbound.
   - SE NON FUNZIONA: creare un dealer test con un numero alternativo del founder
     oppure usare un secondo telefono
   - Inserire in DB: INSERT INTO conversations con phone_number del founder test
   - Il dealer test deve avere un archetipo assegnato (es. RAGIONIERE per test numeri/ROI)

2. TEST LIVE REAL-TIME:
   - Founder invia messaggio WA come dealer (es. "Buongiorno, ho visto il vostro messaggio. Che margini ci sono su una BMW X3?")
   - VERIFICARE che wa-daemon:
     a) Riceve il messaggio (log "MESSAGGIO IN ARRIVO")
     b) lookupDealer trova il dealer test nel DB
     c) persistInboundMessage logga su SQLite
     d) Invia a response-analyzer
     e) response-analyzer genera risposta calibrata sull'archetipo
     f) Risposta viene auto-inviata al "dealer" via WA
     g) Notifica Telegram al founder con suggerimento/risposta
   - NOTA: Il protocollo temporale (Day 1, Day 3, Day 7) resta INVARIATO per i dealer reali.
     Il test e' in real-time solo perche' il founder simula, non perche' cambiamo il protocollo.

3. FIX dbExec (PRIORITA' ALTA):
   - BUG: dbExec usa python3 -c via shell exec. Parentesi e apici nei messaggi rompono lo shell escape.
   - CAUSA: il body del messaggio viene interpolato direttamente nella stringa python3.
   - FIX: Passare il body come argomento stdin o base64, oppure usare node-sqlite3 nativo.
   - OPZIONE MIGLIORE: sostituire dbExec con better-sqlite3 (npm) — zero shell, tutto in-process.
   - Se better-sqlite3 non compila su iMac: usare sql.js (SQLite in WASM, zero compilazione)

4. SEQUENZA MULTI-STEP AUTOMATICA:
   - Implementare scheduler per Day 3 e Day 7 automatici
   - Day 3: WA testo follow-up (se current_step = DAY1_SENT e last_contact_at > 3 giorni)
   - Day 7: WA voice note (edge-tts DiegoNeural, 40sec, personalizzato per archetipo)
   - Lo scheduler gira nel wa-daemon o come processo PM2 separato
   - Aggiorna current_step: DAY3_SENT, DAY7_VOICE_SENT

5. VOICE NOTE PER ARCHETIPO:
   - Preparare testi voice note Day 7 per ogni archetipo:
     * NARCISO: esclusivita, "ho riservato questa opportunita per lei"
     * BARONE: rispetto, "mi permetto di ricontattarla con calma"
     * RAGIONIERE: numeri, "le invio i margini aggiornati"
     * TECNICO: documentazione, "ho il report DAT pronto"
     * RELAZIONALE: calore, "ci tenevo a risentirla"
     * CONSERVATORE: sicurezza, "nessun rischio, tutto documentato"
     * DELEGATORE: semplicita, "gestisco tutto io, le serve solo dire si"
     * PERFORMANTE: velocita, "ho un veicolo disponibile subito"
     * OPPORTUNISTA: margine, "i numeri sono interessanti"
   - Generare con edge-tts e salvare in /tmp/argos_voice_DAY7_ARCHETIPO.mp3

PERSONA: Luca Ferretti, ARGOS Automotive
REGOLA: Tutto gira su iMac. Mai lanciare processi WA/dashboard su MacBook.
REGOLA: MAI menzionare CoVe/Claude/AI/Anthropic nei messaggi dealer.
REGOLA: MAI toccare config Fluxion (~/.cloudflared/config.yml).
REGOLA: wa-daemon processa SOLO numeri in pipeline DB (guardrail fondamentale).
Procedi autonomamente. Sei il CTO.
