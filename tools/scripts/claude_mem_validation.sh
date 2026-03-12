#!/bin/bash

echo "🧪 CLAUDE-MEM VALIDATION PROTOCOL"
echo "================================="
echo

# Wait for service startup
echo "⏳ Waiting for service startup..."
sleep 5

# Health check
if curl -s http://localhost:37777/api/health >/dev/null 2>&1; then
    echo "✅ HTTP API: OPERATIONAL"

    # Extract MCP ready status
    MCP_STATUS=$(curl -s http://localhost:37777/api/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('✅ CONNECTED' if data.get('mcpReady', False) else '❌ DISCONNECTED')
except:
    print('❌ PARSE ERROR')
")

    echo "🔗 MCP Connection: $MCP_STATUS"

    # Service details
    echo
    echo "📊 Service Status:"
    curl -s http://localhost:37777/api/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'   Version: {data.get(\"version\", \"unknown\")}')
    print(f'   Uptime: {data.get(\"uptime\", 0)} seconds')
    print(f'   Platform: {data.get(\"platform\", \"unknown\")}')
    print(f'   Initialized: {data.get(\"initialized\", False)}')
except:
    print('   Unable to parse status')
"

else
    echo "❌ HTTP API: NOT RESPONDING"
    echo "   Check Claude Code restart completion"
fi

echo
echo "================================="
if [ "$MCP_STATUS" = "✅ CONNECTED" ]; then
    echo "🏆 ENTERPRISE DEPLOYMENT SUCCESSFUL"
    echo "   claude-mem is ready for production use"
else
    echo "⚠️  Additional troubleshooting may be required"
    echo "   Verify Claude Code has been fully restarted"
fi
echo "================================="
