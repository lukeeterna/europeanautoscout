#!/bin/bash
# IMMEDIATE WAHA SETUP — SMARTPHONE DIRECT EXECUTION
# Copy/paste these commands on smartphone Termux

echo "🚀 WAHA SETUP — MARIO COLLECTION IMMEDIATE"
echo "==========================================="

# 1. Environment setup
echo "📦 Installing dependencies..."
pkg update && pkg install nodejs git curl -y

# 2. Clone WAHA
echo "📥 Cloning WAHA repository..."
cd ~
git clone https://github.com/devlikeapro/waha
cd waha

# 3. Install dependencies
echo "🔧 Installing WAHA dependencies..."
npm install --production

# 4. Environment configuration
echo "⚙️ Configuring WAHA environment..."
export WHATSAPP_DEFAULT_ENGINE=NOWEB
export WAHA_API_HOSTNAME=0.0.0.0
export WAHA_API_PORT=3000
export WAHA_WEBHOOK_URL=http://192.168.1.12:5678/webhook/waha

# 5. Start WAHA server
echo "🚀 Starting WAHA server..."
nohup npm start > waha.log 2>&1 &

# Wait for startup
echo "⏳ Waiting for WAHA to start..."
sleep 15

# 6. Test WAHA API
echo "🔍 Testing WAHA API..."
curl -s http://localhost:3000/api/status || echo "❌ WAHA not ready yet"

# 7. Create Mario WhatsApp session
echo "📱 Creating Mario WhatsApp session..."
curl -X POST http://localhost:3000/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"name": "mario-session"}'

# 8. Get QR code for pairing
echo "📷 Getting QR code for WhatsApp pairing..."
echo "Scan this QR code with WhatsApp on your primary phone:"
curl http://localhost:3000/api/sessions/mario-session/auth/qr

echo ""
echo "✅ SETUP COMPLETE!"
echo "📱 Scan QR code above with WhatsApp"
echo "🔗 API endpoint: http://100.100.104.104:3000"
echo ""
echo "🎯 READY FOR MARIO COLLECTION MESSAGE!"