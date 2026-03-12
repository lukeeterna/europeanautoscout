#!/bin/bash
# MARIO COLLECTION MESSAGE — IMMEDIATE SEND
# Run on smartphone after QR pairing

curl -X POST http://localhost:3000/api/sendText \
  -H "Content-Type: application/json" \
  -d '{
    "session": "mario-session",
    "chatId": "393336142544@c.us",
    "text": "🚗 Mario, aggiornamento BMW 330i:\n\n✅ Km verificati: 45.200 (correzione tecnica)\n💰 Prezzo confermato: €27.800\n📋 Documentazione EU preparata\n\n**MODALITÀ SEMPLIFICATA FISCALE**:\n€800 fee success-only → evita oneri TD17 (~€200)\nChiavi in mano Napoli senza complicazioni\n\nProcediamo con BMW o valutiamo alternative?\n\n*ARGOS™ Automotive | Luca Ferretti*\n*Competenza automotive + consulenza fiscale integrata*"
  }'

echo "✅ Mario collection message SENT!"
echo "💰 Target: €800 revenue"
echo "⏰ Window: 44h remaining"
echo ""
echo "🔍 Monitor responses with:"
echo "curl http://localhost:3000/api/sessions/mario-session/chats/393336142544@c.us/messages?limit=5"