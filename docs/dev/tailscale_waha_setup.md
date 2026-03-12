# TAILSCALE + WAHA SETUP — IMMEDIATE DEPLOYMENT

## 🚀 REDMI NOTE 9 PRO — WAHA + TAILSCALE

### Su Android (Termux):

```bash
# 1. Verifica Tailscale esistente
tailscale status

# 2. Installa Node.js se non presente
pkg update && pkg upgrade -y
pkg install nodejs git wget -y

# 3. Clone WAHA (lightweight version)
git clone https://github.com/devlikeapro/waha
cd waha

# 4. Install dependencies (production only)
npm install --production

# 5. Configure WAHA per Tailscale
export WHATSAPP_DEFAULT_ENGINE=NOWEB
export WAHA_API_HOSTNAME=0.0.0.0
export WAHA_API_PORT=3000
export WAHA_WEBHOOK_URL=http://imac-tailscale-ip:5678/webhook/waha

# 6. Start WAHA server
npm start
```

### Tailscale Configuration:

```bash
# Get Redmi Tailscale IP
tailscale ip -4

# Example output: 100.64.x.x (note this IP)
```

---

## 🖥️ iMac 2012 — SSH ROUTING + TAILSCALE

### SSH Setup:

```bash
# SSH dal MacBook al iMac
ssh user@imac-local-ip

# Su iMac - Verifica Tailscale
tailscale status
tailscale ip -4  # Note iMac Tailscale IP

# Setup port forwarding (iMac → Redmi)
# Forward local :3000 to Redmi WAHA
ssh -L 3000:redmi-tailscale-ip:3000 -N &

# Test connection
curl http://localhost:3000/api/status
```

---

## 💻 MacBook — N8N INTEGRATION

### n8n Workflow Setup:

```bash
# n8n HTTP Request node configuration:
URL: http://imac-local-ip:3000/api/sendText
Method: POST
Headers: Content-Type: application/json
Body: {
  "session": "dealer-session",
  "chatId": "phone@c.us",
  "text": "{{$json.message}}"
}
```

### WAHA Session Management:

```bash
# Create WhatsApp session via iMac tunnel
curl -X POST http://imac-local-ip:3000/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"name": "dealer-session"}'

# Get QR code for pairing
curl http://imac-local-ip:3000/api/sessions/dealer-session/auth/qr

# Scan QR with primary WhatsApp phone
```

---

## 📱 WHATSAPP AUTOMATION — CONTATTI CALDI

### Mario Collection Immediate:

```bash
# Send enhanced Mario message via WAHA
curl -X POST http://imac-local-ip:3000/api/sendText \
  -H "Content-Type: application/json" \
  -d '{
    "session": "dealer-session",
    "chatId": "393336142544@c.us",
    "text": "🚗 Mario, aggiornamento BMW 330i:\n\n✅ Km verificati: 45.200\n💰 €27.800 confermato\n📋 Documentazione pronta\n\n€800 success-fee + risparmio fiscale €150\n\nProcediamo? *ARGOS™ | Luca Ferretti*"
  }'
```

### Dealer Prospects Automation:

```javascript
// n8n Workflow: Dealer WhatsApp Automation
{
  "nodes": [
    {
      "name": "Get Hot Prospects",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "query": "SELECT * FROM dealer_contacts WHERE whatsapp_opt_in = true AND automation_stage = 'READY' LIMIT 5"
      }
    },
    {
      "name": "Send WhatsApp",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://imac-local-ip:3000/api/sendText",
        "method": "POST",
        "body": {
          "session": "dealer-session",
          "chatId": "{{$json.phone_number}}@c.us",
          "text": "🚗 **Veicolo premium disponibile**\n\nCiao {{$json.contact_name}},\n\nBMW 330i 2020 - €27.800 Germania\nDocumentazione EU verificata ARGOS™\n\nInteressato? Rispondi 'SÌ' per dettagli completi.\n\n*Luca Ferretti | ARGOS™ Automotive*"
        }
      }
    }
  ]
}
```

---

## 🔧 TROUBLESHOOTING

### Connection Issues:

```bash
# Test Tailscale connectivity
ping redmi-tailscale-ip
ping imac-tailscale-ip

# Test WAHA API
curl http://redmi-tailscale-ip:3000/api/status

# Test SSH tunnel
ssh -v user@imac-local-ip
```

### Port Conflicts:

```bash
# Check port usage
netstat -tulpn | grep :3000
netstat -tulpn | grep :5678

# Kill conflicting processes if needed
sudo killall -9 node
```

---

## 📊 MONITORING & AUTOMATION

### Response Tracking:

```bash
# Monitor WhatsApp responses
curl http://imac-local-ip:3000/api/sessions/dealer-session/chats

# Parse responses for keywords
grep -i "sì\|ok\|interessato\|bene" response.json
```

### Auto-notification:

```bash
# Webhook for positive responses → n8n
curl -X POST http://localhost:5678/webhook/positive-response \
  -H "Content-Type: application/json" \
  -d '{"contact": "Mario", "response": "Sì, procediamo", "timestamp": "'$(date)'"}'
```

---

**COSTO TOTALE**: €0 (usa hardware esistente + Tailscale + WAHA open source)

**TEMPO SETUP**: 30-60 minuti

**TARGET**: Mario collection immediate + dealer automation scaling