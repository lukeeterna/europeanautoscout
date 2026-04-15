# Gotchas ARGOS — Errori da non ripetere

<!-- FORMATO:
## [DATA] — [TIPO ERRORE]
Cosa è successo:
Causa root:
Come fixato:
Regola derivata:
-->

## 2026-03-13 — DIRECTION BUG WA
Cosa è successo: messaggi outbound loggati come inbound nel DB
Causa root: `msg.fromMe ? 'outbound' : 'inbound'` invertito in wa-daemon.js
Come fixato: invertita la condizione
Regola derivata: sempre verificare direction prima di loggare eventi WA

## 2026-03-13 — STATO ENGAGED FALSO POSITIVO
Cosa è successo: Car Plus marcata ENGAGED da broadcast noise, non risposta reale
Causa root: nessun filtro su messaggi broadcast
Regola derivata: mai cambiare stato dealer senza risposta diretta verificata
