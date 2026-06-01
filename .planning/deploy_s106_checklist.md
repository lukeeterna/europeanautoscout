# DEPLOY S106 — CHECKLIST ATOMICO

## PRE-REQUISITI
- [ ] SSH iMac raggiungibile
- [ ] Codice S106 testato localmente (36/36 test PASS)
- [ ] requirements.txt esistente con dipendenze
- [ ] Daemon PM2 "argos-wa-daemon" è online

## FASE 1: BACKUP (rollback-safe)
```bash
ssh gianlucadistasi@192.168.1.12 \
  "cp -r ~/Documents/app-antigravity-auto/wa-intelligence \
        ~/Documents/app-antigravity-auto/wa-intelligence.backup.$(date +%Y%m%d_%H%M%S)"
```

## FASE 2: RSYNC wa-intelligence
```bash
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '.env' \
  --exclude 'node_modules' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  /Users/macbook/Documents/combaretrovamiauto-enterprise/wa-intelligence/ \
  gianlucadistasi@192.168.1.12:~/Documents/app-antigravity-auto/wa-intelligence/
```

**File che DEVONO essere sincronizzati:**
- outbound_guard.py (NUOVO)
- post_send_update.py (NUOVO)
- response-analyzer.py (MODIFICATO)
- wa-daemon.js (MODIFICATO)
- templates.py (MODIFICATO)
- requirements.txt (NUOVO)
- state_machine.py
- validator.py
- telegram-handler.py

## FASE 3: INSTALL dipendenze Python
```bash
ssh gianlucadistasi@192.168.1.12 \
  "cd ~/Documents/app-antigravity-auto/wa-intelligence && \
   pip3 install -r requirements.txt"
```

**Expected output:**
- fastapi==0.104.1 installed
- uvicorn[standard]==0.24.0 installed
- itsdangerous==2.1.2 installed

## FASE 4: RESTART daemon con nvm sourcing
```bash
ssh gianlucadistasi@192.168.1.12 \
  "source ~/.nvm/nvm.sh && \
   pm2 restart argos-wa-daemon && \
   pm2 save"
```

## FASE 5: HEALTH CHECK (attendi 10sec startup)
```bash
sleep 10
curl -s http://192.168.1.12:9191/health | python3 -m json.tool
```

**Expected output:**
```json
{
  "status": "ok",
  "wa_connected": true,
  "version": "4.0.0",
  "uptime_seconds": X
}
```

## FASE 6: VERIFY WA still CONNECTED
```bash
ssh gianlucadistasi@192.168.1.12 \
  "source ~/.nvm/nvm.sh && \
   pm2 list | grep argos-wa-daemon"
```

**Expected:** Status `online`, non `errored/crashed`

## FASE 7: CHECK logs per errori
```bash
ssh gianlucadistasi@192.168.1.12 \
  "source ~/.nvm/nvm.sh && \
   pm2 logs argos-wa-daemon --lines 20 --nostream"
```

**RED FLAGS:**
- `SyntaxError` in Python modules
- `Error: Cannot find module` (Node.js dipendenze)
- `EADDRINUSE` (porta 9191 occupata)
- Disconnessioni WA ripetute

## FASE 8: ROLLBACK SE NECESSARIO
Se health check fallisce o WA disconnette:

```bash
ssh gianlucadistasi@192.168.1.12 \
  "rm -rf ~/Documents/app-antigravity-auto/wa-intelligence && \
   mv ~/Documents/app-antigravity-auto/wa-intelligence.backup.* \
      ~/Documents/app-antigravity-auto/wa-intelligence && \
   source ~/.nvm/nvm.sh && \
   pm2 restart argos-wa-daemon"
```

## POST-DEPLOY TASK
1. Test prima uscita (template-first) su 1 dealer
2. Verifica state machine transitions in DB
3. Monitoring: curva heartbeat per 30 min
4. Update MEMORY.md con outcome

---

## FINESTRA DI DEPLOY IDEALE
- Orario: Quando iMac NON ha connessioni dealer attive
- Durata: 2-3 minuti totali
- Risk window: Innesto daemon fino a health OK (circa 10 sec)

## VERDETTO FINALE
Deploy PASS se:
- [ ] rsync completato senza errori
- [ ] requirements installati
- [ ] daemon riavviato e torni ONLINE in PM2
- [ ] /health restituisce 200 + wa_connected: true
- [ ] PM2 logs non contengono errori critici

Deploy FAIL → ROLLBACK IMMEDIATO
