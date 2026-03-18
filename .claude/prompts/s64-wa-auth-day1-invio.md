Sessione 64 — ARGOS WA Auth + Day 1 Invio + CF Tunnel permanente.

CONTESTO RAPIDO:
- Dashboard ARGOS Command Center LIVE su iMac:8080 (F1-F5 + WA Auth card)
- CF Quick Tunnel ATTIVO: https://accomplish-struck-manchester-davidson.trycloudflare.com
  ATTENZIONE: quick tunnel = temporaneo, potrebbe essere scaduto. Rilanciare se necessario.
  Comando: `cloudflared tunnel --config /dev/null --url http://localhost:8080`
  MAI TOCCARE ~/.cloudflared/config.yml (FLUXION!)
- PM2: argos-dashboard ONLINE, tg-bot ONLINE, wa-daemon STOPPED
- WA Business sessione SCADUTA — QR pronto in dashboard System
- 8 dealer Salerno in pipeline, tutti PENDING
- iMac SSH: ssh gianlucadistasi@192.168.1.2 (node: /usr/local/bin/node, pm2: ~/.npm-global/bin/pm2)

TASK S64 (4 track):

1. WA RE-AUTH (dalla dashboard):
   - Apri dashboard http://192.168.1.2:8080 → login argos2026 → System
   - Clicca "Autentica WhatsApp" → aspetta QR (~15s Chromium)
   - Invia QR via Telegram al founder (chat 931063621, bot token in MEMORY)
   - Founder scansiona QR con WA Business dal Redmi (328-1536308)
   - Verifica sessione → se OK: pm2 start argos-wa-daemon

2. DAY 1 INVIO (dopo WA auth):
   - wa-daemon gira su porta 9191 (localhost su iMac)
   - Componi messaggio Day 1 per archetipo:
     * SALERNO_001: Autovanny Group (Eboli), NARCISO, WA 39335-5250129
       Tono: esclusivita, "selezionato", "riservato per la sua area"
     * SALERNO_002: FC Luxury Car Center (S.Egidio MA), BARONE, WA 39342-5036799
       Tono: rispetto, "su misura per lei", esclusivita, mai pressione
   - Invia via: curl -X POST http://localhost:9191/send -H 'Content-Type: application/json' -d '{"phone":"39XXXXXXXXX","message":"...","dealer_id":"SALERNO_00X"}'
   - wa-daemon aggiorna automaticamente SQLite (DAY1_SENT) + notifica Telegram
   - Verifica dalla dashboard Pipeline che step sia DAY1_SENT

3. CLOUDFLARE TUNNEL PERMANENTE:
   - Attuale: quick tunnel (scade, URL random). Serve named tunnel.
   - Opzione A: cloudflared login → crea tunnel "argos-dashboard" → DNS su argos-automotive.pages.dev
   - Opzione B: resta quick tunnel e rilancia ogni sessione
   - MAI modificare ~/.cloudflared/config.yml (FLUXION!)
   - Se named tunnel: creare config separato es. ~/.cloudflared/argos-config.yml

4. MONITORAGGIO RISPOSTE:
   - Dopo invio Day 1, monitorare risposte dealer
   - wa-daemon logga inbound su SQLite automaticamente
   - response-analyzer genera risposte via Haiku 4.5
   - Dashboard Conversations mostra feed real-time

PERSONA: Luca Ferretti, ARGOS Automotive
REGOLA: Tutto gira su iMac. Mai lanciare processi WA/dashboard su MacBook.
REGOLA: MAI menzionare CoVe/Claude/AI/Anthropic nei messaggi dealer.
REGOLA: MAI toccare config Fluxion (~/.cloudflared/config.yml).
Procedi autonomamente. Sei il CTO.
