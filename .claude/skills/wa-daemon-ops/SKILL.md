---
name: wa-daemon-ops
description: >
  Operazioni WA daemon su iMac. Carica quando Luke dice "verifica daemon",
  "invia messaggio WA", "stato WhatsApp", "daemon offline", "debug connessione",
  "porta 9191", o quando devi inviare o verificare un messaggio WhatsApp
  via wa-daemon.js. NON caricare per generare il testo del messaggio (usa outreach-day1).
---

# WA Daemon Ops — Protocollo operativo

## Status check
```bash
ssh gianlucadistasi@192.168.1.12 "curl -s localhost:9191/status"
# Risposta attesa: {"status":"connected","uptime":...}
```

## Invio messaggio
```bash
ssh gianlucadistasi@192.168.1.12 "curl -s -X POST localhost:9191/send \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: $WA_API_KEY' \
  -d '{\"phone\":\"393314928901\",\"message\":\"testo\",\"dealer_id\":\"test\"}'"
```

## Checklist pre-invio — OBBLIGATORIA
```
[ ] daemon status = "connected" (non solo "online")
[ ] outbound_count del dealer < cap corrente
[ ] validate() restituisce PASS (non solo log)
[ ] Nessun duplicato nelle ultime 24h
[ ] Numero destinatario: TEST_FOUNDER (393314928901) per test
```

## Verifica risposta dealer (query obbligatoria)
```sql
-- Su dealer_network.sqlite (iMac)
SELECT direction, body, timestamp_it FROM messages
WHERE dealer_id = '<id>' ORDER BY timestamp_it;
-- inbound_count > 0 + righe direction='inbound' = risposta reale
-- current_step != prova di risposta reale
```

## File daemon
- `wa-intelligence/wa-daemon.js` — processo principale (PM2: wa-daemon)
- `wa-intelligence/dashboard/app.py` — dashboard :8080
- `dealer_network.sqlite` — DB messaggi + dealer queue

## PM2 su iMac
```bash
ssh gianlucadistasi@192.168.1.12 "pm2 status"
ssh gianlucadistasi@192.168.1.12 "pm2 logs wa-daemon --lines 50"
ssh gianlucadistasi@192.168.1.12 "pm2 restart wa-daemon"
```

## Regole sicurezza
- Porta 9191 richiede X-API-Key header — mai chiamare senza
- MAX 1 messaggio Day 1 per numero — non inviare se outbound_count > 0
- TEST_FOUNDER = 393314928901 — unico numero autorizzato per test
- Dealer reali: autorizzazione esplicita del founder prima di qualsiasi invio
