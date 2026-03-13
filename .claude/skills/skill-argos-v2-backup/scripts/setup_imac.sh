#!/bin/bash
# setup_imac.sh — ARGOS™ CoVe 2026
# Setup prima installazione su iMac via SSH
# Esegui UNA SOLA VOLTA dal MacBook

set -e
IMAC="gianlucadistasi@192.168.1.12"
BASE="$HOME/Documents/app-antigravity-auto"

echo "[ARGOS] ▶ Setup iMac — ARGOS™ Outreach Automation"
echo "[ARGOS] Target: $IMAC"
echo ""

# ── Test connessione ─────────────────────────────────────────
echo "[ARGOS] 1/5 Test SSH..."
ssh "$IMAC" "echo '  ✅ SSH OK'" || { echo "❌ SSH fallito"; exit 1; }

# ── Node.js ──────────────────────────────────────────────────
echo "[ARGOS] 2/5 Verifica Node.js..."
ssh "$IMAC" "
  if command -v node &>/dev/null; then
    echo '  ✅ Node.js:' \$(node --version)
  else
    echo '  ⚠ Node.js non trovato — installo via Homebrew...'
    brew install node
    echo '  ✅ Node.js installato:' \$(node --version)
  fi
"

# ── Directory struttura ──────────────────────────────────────
echo "[ARGOS] 3/5 Struttura directory..."
ssh "$IMAC" "
  mkdir -p $BASE/wa-sender
  mkdir -p $BASE/.chromadb
  echo '  ✅ Directory OK'
"

# ── NPM deps wa-sender ───────────────────────────────────────
echo "[ARGOS] 4/5 Dipendenze npm..."
ssh "$IMAC" "
  cd $BASE/wa-sender
  if [ ! -d node_modules/whatsapp-web.js ]; then
    npm init -y 2>/dev/null
    npm install whatsapp-web.js qrcode 2>&1 | grep -E 'added|warn|error' | tail -5
    echo '  ✅ npm deps installati'
  else
    echo '  ✅ npm deps già presenti'
  fi
"

# ── Python deps ──────────────────────────────────────────────
echo "[ARGOS] 5/5 Python deps..."
ssh "$IMAC" "
  python3 -c 'import duckdb' 2>/dev/null && echo '  ✅ duckdb OK' || \
    (pip3 install duckdb 2>&1 | tail -2 && echo '  ✅ duckdb installato')
"

echo ""
echo "[ARGOS] ✅ Setup completato"
echo "[ARGOS] Prossimo: bash scripts/deploy_qr_server.sh '393XXXXXXXXX' 'testo'"
