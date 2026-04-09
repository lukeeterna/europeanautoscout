---
name: devops-automator
description: >
  Standard enterprise per DevOps e automazione. Invocare per: shell scripts,
  CI/CD, LaunchAgents macOS, PM2, cron jobs, monitoring, backup, SSH/Tailscale,
  deployment automation. Contiene pattern e checklist che Claude deve applicare
  quando scrive script o configura infrastruttura.
---

## Standard script bash

```bash
#!/bin/bash
set -euo pipefail  # ← SEMPRE, prima riga di ogni script

# Struttura obbligatoria:
usage() {
    echo "Usage: $0 [--dry-run] <arg>"
    echo "  --dry-run  Mostra cosa farebbe senza eseguire"
    exit 1
}

# Logging con timestamp:
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2; }

# Mask secrets nei log:
log "Token: ${TOKEN:0:4}****"
```

**Proprietà obbligatorie di ogni script:**
- Idempotente: eseguire 2 volte = stesso risultato
- Dry-run mode per operazioni distruttive
- `--help` flag documentato
- Exit codes significativi (0=ok, 1=errore, 2=usage error)

## Process management macOS

```bash
# LaunchAgent (user-space daemon):
# Path: ~/Library/LaunchAgents/com.company.service.plist
# Comandi:
launchctl load ~/Library/LaunchAgents/com.company.service.plist
launchctl unload ~/Library/LaunchAgents/com.company.service.plist
launchctl list | grep com.company

# PM2 per Node.js:
pm2 start ecosystem.config.js
pm2 save        # persist after reboot
pm2 startup     # generate startup script
```

## Reliability patterns

- **Retry con backoff esponenziale** su ogni chiamata di rete.
- **Health check** prima E dopo ogni deployment.
- **Rollback procedure** documentata e testata prima del deploy in produzione.
- **Alert on failure**, non solo on recovery.

## Backup (regola 3-2-1)

- 3 copie dei dati
- 2 tipi di storage diversi
- 1 copia offsite/cloud
- Test restore trimestrali — un backup mai ripristinato non è un backup.

## Output obbligatorio per ogni script

Ogni script prodotto deve includere:
1. Lo script stesso
2. Come installarlo/abilitarlo
3. Come verificare che giri
4. Come disabilitarlo/rollback

## Checklist sicurezza script

```
[ ] Nessun secret hardcoded (usare .env)?
[ ] Input validati prima dell'uso in comandi?
[ ] Operazioni distruttive hanno --dry-run?
[ ] Permessi file corretti (600 per secrets, 755 per scripts)?
[ ] Log rotation configurata?
```
