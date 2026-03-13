#!/usr/bin/env bash
# deploy.sh — ARGOS™ WA Intelligence Stack
# CoVe 2026 | Eseguire dal MacBook via SSH
#
# PREREQUISITI:
#   1. SSH verso iMac funzionante: ssh gianlucadistasi@192.168.1.12
#   2. Node.js v22+ su iMac: node --version
#   3. PM2 installato globalmente: npm install -g pm2
#   4. Python3 + duckdb + requests: pip3 install duckdb requests
#   5. File .env con ARGOS_TELEGRAM_TOKEN configurato
#
# ESECUZIONE:
#   bash deploy.sh
#
# COSA FA:
#   1. Copia tutti i file su iMac
#   2. Installa dipendenze npm
#   3. Copia LaunchAgents
#   4. Avvia PM2 stack
#   5. Installa scheduler LaunchAgent
#   6. Verifica health

set -euo pipefail

# ── Config ────────────────────────────────────────────────────
IMAC="gianlucadistasi@192.168.1.12"
REMOTE_BASE="/Users/gianlucadistasi/Documents/app-antigravity-auto"
IMAC_PATH="export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH"
REMOTE_INTEL="$REMOTE_BASE/wa-intelligence"
LOCAL_INTEL="$(cd "$(dirname "$0")" && pwd)"

echo "═══════════════════════════════════════════"
echo " ARGOS™ WA Intelligence — Deploy"
echo " Destinazione: $IMAC"
echo " Path remoto:  $REMOTE_INTEL"
echo "═══════════════════════════════════════════"

# ── 1. Connettività ──────────────────────────────────────────
echo ""
echo "▶ [1/7] Verifica connessione iMac..."
ssh "$IMAC" "$IMAC_PATH && echo '✅ SSH OK' && node --version && python3 --version && pm2 --version" \
  || { echo "❌ Prerequisiti mancanti su iMac. Verifica SSH, Node.js, PM2."; exit 1; }

# ── 2. Copia file ───────────────────────────────────────────
echo ""
echo "▶ [2/7] Copia file su iMac..."
ssh "$IMAC" "mkdir -p $REMOTE_INTEL/launchd"

scp "$LOCAL_INTEL/time-context.js"         "$IMAC:$REMOTE_INTEL/"
scp "$LOCAL_INTEL/wa-daemon.js"            "$IMAC:$REMOTE_INTEL/"
scp "$LOCAL_INTEL/response-analyzer.py"   "$IMAC:$REMOTE_INTEL/"
scp "$LOCAL_INTEL/scheduler.py"           "$IMAC:$REMOTE_INTEL/"
scp "$LOCAL_INTEL/telegram-handler.py"    "$IMAC:$REMOTE_INTEL/"
scp "$LOCAL_INTEL/ecosystem.config.js"    "$IMAC:$REMOTE_INTEL/"
scp "$LOCAL_INTEL/launchd/"*.plist        "$IMAC:$REMOTE_INTEL/launchd/"

echo "  ✅ File copiati"

# ── 3. Dipendenze npm ────────────────────────────────────────
echo ""
echo "▶ [3/7] Installazione dipendenze npm..."
ssh "$IMAC" "
  $IMAC_PATH
  set -e
  cd $REMOTE_BASE/wa-sender 2>/dev/null || mkdir -p $REMOTE_BASE/wa-sender
  cd $REMOTE_BASE/wa-sender
  if [ ! -f package.json ]; then npm init -y; fi
  npm install --save whatsapp-web.js qrcode 2>&1 | tail -5
  echo '  ✅ npm deps OK'
"

# ── 4. Dipendenze Python ─────────────────────────────────────
echo ""
echo "▶ [4/7] Dipendenze Python..."
ssh "$IMAC" "
  python3 -c 'import duckdb' 2>/dev/null || pip3 install duckdb --break-system-packages
  python3 -c 'import zoneinfo' 2>/dev/null && echo '  ✅ zoneinfo OK'
  echo '  ✅ Python deps OK'
"

# ── 5. Configura .env ────────────────────────────────────────
echo ""
echo "▶ [5/7] Configurazione .env..."
ssh "$IMAC" "
  ENV_FILE=$REMOTE_INTEL/.env
  if [ ! -f \"\$ENV_FILE\" ]; then
    echo 'ARGOS_TELEGRAM_TOKEN=INSERISCI_IL_TOKEN_QUI' > \"\$ENV_FILE\"
    echo 'ARGOS_TELEGRAM_CHAT_ID=931063621'            >> \"\$ENV_FILE\"
    echo 'ARGOS_DB_PATH=$REMOTE_BASE/dealer_network.duckdb' >> \"\$ENV_FILE\"
    chmod 600 \"\$ENV_FILE\"
    echo '  ⚠️  .env creato — EDIT REQUIRED: $REMOTE_INTEL/.env'
  else
    echo '  ✅ .env già presente'
  fi
"

# ── 6. PM2 start ─────────────────────────────────────────────
echo ""
echo "▶ [6/7] Avvio PM2 stack..."
ssh "$IMAC" "
  $IMAC_PATH
  set -e
  cd $REMOTE_INTEL
  # Carica token da .env se esiste
  if [ -f .env ]; then
    export \$(grep -v '^#' .env | xargs)
  fi

  # Stop eventuali processi precedenti
  pm2 stop argos-wa-daemon 2>/dev/null || true
  pm2 stop argos-tg-bot    2>/dev/null || true
  pm2 delete argos-wa-daemon 2>/dev/null || true
  pm2 delete argos-tg-bot    2>/dev/null || true

  # Avvia stack
  pm2 start ecosystem.config.js
  pm2 save

  echo '  ✅ PM2 stack avviato'
  pm2 list
"

# ── 7. LaunchAgent scheduler ─────────────────────────────────
echo ""
echo "▶ [7/7] Installazione LaunchAgent scheduler..."
ssh "$IMAC" "
  PLIST_SRC=$REMOTE_INTEL/launchd/com.argos.scheduler.plist
  PLIST_DST=~/Library/LaunchAgents/com.argos.scheduler.plist
  PM2_PLIST_SRC=$REMOTE_INTEL/launchd/com.argos.pm2.plist
  PM2_PLIST_DST=~/Library/LaunchAgents/com.argos.pm2.plist

  # Scheduler
  cp \"\$PLIST_SRC\" \"\$PLIST_DST\"
  launchctl unload \"\$PLIST_DST\" 2>/dev/null || true
  launchctl load   \"\$PLIST_DST\"
  echo '  ✅ Scheduler LaunchAgent attivo (ogni 5 min)'

  # PM2 resurrect al boot
  cp \"\$PM2_PLIST_SRC\" \"\$PM2_PLIST_DST\"
  launchctl unload \"\$PM2_PLIST_DST\" 2>/dev/null || true
  launchctl load   \"\$PM2_PLIST_DST\"
  echo '  ✅ PM2 resurrect al boot attivo'
"

# ── Health check finale ──────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo " HEALTH CHECK"
echo "═══════════════════════════════════════════"
ssh "$IMAC" "
  $IMAC_PATH
  echo '--- PM2 Status ---'
  pm2 list

  echo ''
  echo '--- WA Daemon Health ---'
  curl -s http://127.0.0.1:9191 2>/dev/null | python3 -m json.tool || echo '  ⚠️  Daemon non ancora pronto (attendi 30s)'

  echo ''
  echo '--- Scheduler LaunchAgent ---'
  launchctl list | grep argos || echo '  ⚠️  LaunchAgent non trovato'

  echo ''
  echo '--- Ultimi log daemon ---'
  tail -5 /tmp/argos-wa-daemon.log 2>/dev/null || echo '  (nessun log ancora)'
"

echo ""
echo "═══════════════════════════════════════════"
echo " DEPLOY COMPLETATO"
echo ""
echo " ⚠️  AZIONE RICHIESTA:"
echo "    Verifica e aggiorna ARGOS_TELEGRAM_TOKEN in:"
echo "    $REMOTE_INTEL/.env"
echo ""
echo " MONITORING:"
echo "    pm2 logs argos-wa-daemon"
echo "    pm2 logs argos-tg-bot"
echo "    curl http://192.168.1.12:9191   (health check)"
echo "    tail -f /tmp/argos-scheduler.log"
echo "═══════════════════════════════════════════"
