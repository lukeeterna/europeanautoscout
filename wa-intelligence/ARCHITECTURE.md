# ARGOS™ WA Intelligence — Enterprise Architecture
# CoVe 2026 | Event-Driven | Human-in-Loop | Time-Aware

## PROBLEMA DA RISOLVERE

Il sistema attuale è **reattivo-manuale**:
- L'agente non sa che ore sono, che giorno è, da quanto aspetta
- Non rileva quando Mario risponde
- Non genera una risposta oculata in tempo reale
- Dipende da Luke per ogni check

## ARCHITETTURA TARGET

```
iMac 2012 (server sempre acceso)
│
├── wa-daemon.js          [PM2 PERSISTENT]
│   Listener WA eventi in real-time
│   ↓ su ogni messaggio in arrivo
│   → scrive DuckDB (audit trail completo)
│   → chiama response-analyzer.py
│   → invia Telegram alert immediato
│
├── response-analyzer.py  [chiamato da daemon]
│   Carica context: archetipo + storico + objection_library
│   Classifica messaggio: POSITIVE / OBJECTION / NEGATIVE / CURIOSITY
│   Genera 2 candidate replies calibrate su archetipo
│   Valuta timing (orario, giorno, urgenza)
│   Invia a Telegram con bottoni APPROVA / MODIFICA / RIFIUTA
│
├── scheduler.py           [CRON ogni 5 min via launchd]
│   Calcola SEMPRE: ora IT, giorno settimana, business hours
│   Monitora: scadenze Day 7, Day 12, follow-up pendenti
│   Alert proattivi: "Day 7 Mario scade tra 2 ore"
│   Non invia nulla — solo allerta. Invio = umano approva
│
├── telegram-handler.py    [PM2 PERSISTENT]
│   Bot Telegram human-in-loop
│   Bottone APPROVA → schedule invio WA (anti-ban sleep)
│   Bottone MODIFICA → chiede testo manuale
│   Bottone RIFIUTA → log + nessuna azione
│   Bottone POSTICIPA 1H / POSTICIPA 1G → reschedule
│
└── DuckDB [dealer_network.duckdb]
    Tabelle: conversations, messages, pending_replies,
             scheduled_actions, audit_log

MacBook (client sviluppo)
└── Claude Code → SSH → legge DuckDB → suggerisce azioni strategiche
```

## PRINCIPI ENTERPRISE

1. **EVENT-DRIVEN** — non polling. Il daemon reagisce in ms all'arrivo.
2. **HUMAN-IN-LOOP OBBLIGATORIO** — nessun messaggio parte senza approvazione.
3. **AUDIT TRAIL COMPLETO** — ogni evento (arrivo, analisi, approvazione, invio) è loggato con timestamp IT preciso.
4. **FAULT-TOLERANT** — PM2 restarta il daemon se crasha. LaunchAgent lo riavvia al boot.
5. **TIME-AWARE** — ogni azione porta il contesto temporale completo: ora IT, business hours, giorni dall'ultimo contatto, scadenza prossima.
6. **ARCHETIPO-CALIBRATO** — la risposta generata usa il framework Cialdini corretto per l'archetipo identificato.
7. **ZERO API KEYS ESPOSTE** — le credenziali non passano mai per chat.

## STACK

| Componente | Tecnologia | Perché |
|---|---|---|
| WA daemon | Node.js + whatsapp-web.js | nativo, no Docker |
| Process manager | PM2 | no Docker, auto-restart, log |
| Autostart macOS | LaunchAgent plist | persistenza al boot |
| Database | DuckDB | già in uso, zero setup |
| LLM locale | Ollama mistral:7b | no API key, sempre disponibile |
| Alert human | Telegram Bot | già configurato |
| Scheduler | Python + schedule + launchd | leggero, affidabile |
| Timezone | IT = Europe/Rome | hardcoded |
