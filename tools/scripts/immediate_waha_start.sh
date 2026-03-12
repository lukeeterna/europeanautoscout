#!/bin/bash
# IMMEDIATE WAHA SMARTPHONE COMMANDS
# Run directly on smartphone Termux while setting up SSH

echo "🚀 IMMEDIATE WAHA STARTUP — SMARTPHONE TERMUX"
echo "=============================================="

# Quick check if already installed
if [ -d "~/waha" ]; then
    echo "📁 WAHA directory exists - starting server..."
    cd ~/waha
    export WHATSAPP_DEFAULT_ENGINE=NOWEB
    export WAHA_API_HOSTNAME=0.0.0.0
    npm start
else
    echo "📦 Fresh WAHA installation..."

    # Quick install sequence
    pkg update && pkg install nodejs git curl -y

    # Clone and setup
    cd ~
    git clone https://github.com/devlikeapro/waha
    cd waha
    npm install --production

    # Environment config
    export WHATSAPP_DEFAULT_ENGINE=NOWEB
    export WAHA_API_HOSTNAME=0.0.0.0
    export WAHA_API_PORT=3000

    # Start server
    echo "🚀 Starting WAHA server..."
    npm start &

    # Wait for startup
    sleep 10

    # Create Mario session
    curl -X POST http://localhost:3000/api/sessions/start \
      -H "Content-Type: application/json" \
      -d '{"name": "mario-session"}'

    # Get QR code
    echo "📷 QR Code for WhatsApp pairing:"
    curl http://localhost:3000/api/sessions/mario-session/auth/qr

    echo ""
    echo "✅ WAHA READY!"
    echo "🔗 API endpoint: http://100.100.104.104:3000"
    echo "📱 Scan QR code with WhatsApp to pair"
fi