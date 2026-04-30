# NEXT SESSION PROMPT — S148 (1 maggio 2026 mattina)

> Copia-incolla questo testo come primo messaggio nella nuova sessione Claude Code.

---

Sessione S148 — fix WA daemon (NO outreach oggi, è 1° maggio).

**Contesto**: il Day 1 a Stile Car del 30/04 16:44 è risultato falso positivo. Daemon logga "INVIATO via HTTP" senza ack delivery. Marker test + Day 1 entrambi NON consegnati. Rollback DB già eseguito (commit `94645b5`). Stile Car ora di nuovo PENDING/COLD/outbound=0, mai realmente contattato.

**Diagnosi confermata** (screenshot Luke 30/04 17:12, telefono ARGOS Business 3281536308):
- Sessione "argos" ATTIVA su WA → ult. attività 16:44 (momento invio falso)
- Anche sessioni "imac" e "macbook" presenti (3 di 4 slot WA Web usati)
- Quindi NON è sessione persa → è bug libreria `whatsapp-web.js` (errore costante: `chat.sendPresenceUpdate is not a function`)

**Letture obbligatorie** (in ordine):
1. `prompts/s148_debug_wa_daemon.md` (piano completo — salta step 1.1-1.2, sessione esiste, vai diretto a 1.3 lib upgrade + patch)
2. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` entry "2026-04-30 17:00 — S147 BUG CRITICO DAEMON"
3. `HANDOFF.md` sezione "S147 OUTCOME CORRETTO"
4. `wa-intelligence/wa-daemon.js` (su iMac via SSH) — cercare chiamate a `sendPresenceUpdate` + funzione send + gestione ack

**Pre-flight**:
- IP iMac: `192.168.1.2` (regress da `.12` post-reboot 28/04)
- `bash .claude/scripts/session_start.sh`
- WA daemon su `http://192.168.1.2:9191/status` (mostra `wa_status:connected` ma è cached, NON fidarsi)

**Modalità CTO**: agisci autonomamente sui fix tecnici. Chiedi conferma SOLO per:
- restart daemon (interrompe sessione brevemente)
- modifiche a `wa-daemon.js` (file critico, leggi tutto prima)
- prima del re-invio Day 1 Stile Car (mai automatico)

**Sequenza operativa proposta**:

1. **Verifica versione attuale lib** (`npm ls whatsapp-web.js` su iMac)
2. **Leggi `wa-daemon.js`** integralmente: capire dove sta `simulateTyping`, dove la chiamata `sendPresenceUpdate`, dove la funzione send, se c'è gestione ack
3. **Decidi strategia fix**:
   - (A) Upgrade `whatsapp-web.js@latest` + restart
   - (B) Patch chirurgica: guard `typeof chat.sendPresenceUpdate === 'function'` prima della chiamata
   - (C) Aggiungere ack listener (`message_ack`) per delivery confirmation reale
   - Idealmente: A o B per fix immediato + C per hardening
4. **Test marker su TEST_FOUNDER** (393314928901): invio + Luke conferma manualmente sul suo telefono entro 30 secondi
   - Se NO → debug più profondo, NON procedere
   - Se SÌ → daemon verde, log "DELIVERED" deve apparire post-send
5. **Hardening daemon** (post-fix):
   - Sostituire log `INVIATO via HTTP` con `QUEUED via HTTP`
   - Endpoint `/send` deve aspettare ack o restituire `{"status":"queued","ack_pending":true}` invece di `"sent"`
   - Aggiungere endpoint `/messages/<msg_id>/status` per poll delivery
6. **Commit fix daemon** + push
7. **Aggiorna MEMORY/HANDOFF** con outcome fix
8. **Crea prompt S149** = invio Day 1 Stile Car sabato 2/5 mattina ore 11:00 (NON oggi 1/5 — RELAZIONALE non manda WA in giorno di festa)

**Vincoli S148**:
- ✋ NESSUN messaggio reale (a Stile Car o altri dealer) finché test 4 non passa con conferma manuale
- ✋ NON aggiornare `conversations.current_step` con DAY1_SENT senza conferma delivery REALE
- ✋ NON fidarsi di `wa_status:connected` nel JSON `/status` (cached)
- ✋ NON inviare il 1° maggio (oggi) — Stile Car è RELAZIONALE, festa nazionale dilata ricezione + segnale "lavoro anche di festa" controproducente
- ✋ Modifiche a `wa-daemon.js`: leggi tutto il file prima, niente bricolage

**Ultima sessione funzionante daemon verificata**: 15/04 (Enzo Car ha risposto "Nulla" al Day 1). Punto di rottura ignoto fra 15/04 e 30/04 — possibile causa: aggiornamento WhatsApp app sul telefono Business + lib whatsapp-web.js outdated.

**Target di fine S148**: daemon che invia + conferma delivery via ack, marker test arrivato sul telefono Luke, prompt S149 pronto per invio Day 1 Stile Car sabato 2/5.
