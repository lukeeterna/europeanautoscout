#!/bin/bash
# SSH SMARTPHONE WAHA SETUP — IMMEDIATE DEPLOYMENT
# For zero-cost WhatsApp automation despite compliance risks

echo "🚀 WAHA SMARTPHONE SETUP VIA SSH"
echo "=================================="

# Step 1: SSH into smartphone via Tailscale/iMac
echo "📱 Connecting to smartphone..."

# Commands to run on smartphone via SSH:
cat << 'SMARTPHONE_COMMANDS' > smartphone_setup.sh

# === SMARTPHONE COMMANDS (via SSH) ===

# Termux environment setup
echo "📦 Setting up Termux environment..."
pkg update && pkg upgrade -y
pkg install nodejs git wget curl openssh -y

# Verify Node.js
node --version
npm --version

# WAHA installation
echo "🔧 Installing WAHA..."
cd ~
git clone https://github.com/devlikeapro/waha
cd waha

# Install dependencies (production only for speed)
npm install --production

# Environment configuration
echo "⚙️ Configuring WAHA environment..."
export WHATSAPP_DEFAULT_ENGINE=NOWEB
export WAHA_API_HOSTNAME=0.0.0.0
export WAHA_API_PORT=3000

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4)
echo "📡 Smartphone Tailscale IP: $TAILSCALE_IP"

# Start WAHA server
echo "🚀 Starting WAHA server..."
nohup npm start > waha.log 2>&1 &

# Get PID and verify
WAHA_PID=$!
echo "✅ WAHA running on PID: $WAHA_PID"
echo "📊 API endpoint: http://$TAILSCALE_IP:3000"

# Test API
sleep 5
curl -s http://localhost:3000/api/status || echo "❌ WAHA startup failed"

# Create WhatsApp session for Mario
echo "📱 Creating WhatsApp session..."
curl -X POST http://localhost:3000/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"name": "mario-session"}'

# Get QR code for pairing
echo "📷 Getting QR code for WhatsApp pairing..."
curl http://localhost:3000/api/sessions/mario-session/auth/qr

echo ""
echo "🎯 SETUP COMPLETE!"
echo "Next steps:"
echo "1. Scan QR code with WhatsApp on primary phone"
echo "2. Test Mario message sending"
echo "3. Setup n8n webhook integration"

SMARTPHONE_COMMANDS

# Make executable
chmod +x smartphone_setup.sh

echo ""
echo "📋 TO EXECUTE ON SMARTPHONE:"
echo "1. SSH into smartphone: ssh user@smartphone-ip"
echo "2. Run setup script: bash smartphone_setup.sh"
echo "3. Scan QR code when prompted"
echo ""
echo "🔗 Or execute remotely:"
echo "ssh user@smartphone-ip 'bash -s' < smartphone_setup.sh"