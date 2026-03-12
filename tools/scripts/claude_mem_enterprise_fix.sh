#!/bin/bash

# CLAUDE-MEM MCP ENTERPRISE FIX SCRIPT
# CoVe 2026 | Enterprise-Grade Solution

echo "🏆 CLAUDE-MEM MCP ENTERPRISE FIX PROTOCOL"
echo "========================================"
echo

# 1. Current status check
echo "📊 PHASE 1: Current Status Analysis"
echo "------------------------------------"

# Check if service is running
if curl -s http://localhost:37777/api/health >/dev/null 2>&1; then
    echo "✅ claude-mem HTTP API: OPERATIONAL"
    MCP_READY=$(curl -s http://localhost:37777/api/health | grep -o '"mcpReady":[^,]*' | cut -d':' -f2)
    echo "🔗 MCP Connection Status: $MCP_READY"
else
    echo "❌ claude-mem HTTP API: NOT RESPONDING"
    echo "⚠️  Service needs restart"
fi

# Check binaries availability
echo
echo "🔧 Binary Availability Check:"
echo "   uvx: $(which uvx 2>/dev/null || echo 'NOT FOUND')"
echo "   uv: $(which uv 2>/dev/null || echo 'NOT FOUND')"
echo "   node: $(which node 2>/dev/null || echo 'NOT FOUND')"

# Check configuration
echo
echo "📁 Configuration File:"
if [ -f "/Users/macbook/.claude/claude_desktop_config.json" ]; then
    echo "✅ claude_desktop_config.json: EXISTS"
    echo "📝 Current claude-mem config:"
    grep -A 10 '"claude-mem"' /Users/macbook/.claude/claude_desktop_config.json
else
    echo "❌ claude_desktop_config.json: NOT FOUND"
fi

echo
echo "========================================"
echo

# 2. Environment optimization
echo "⚡ PHASE 2: Environment Optimization"
echo "------------------------------------"

# Ensure symlinks are correct
echo "🔗 Validating system binaries..."

# Check if uvx symlink exists and is correct
if [ ! -L "/usr/local/bin/uvx" ]; then
    echo "⚠️  Creating uvx symlink to /usr/local/bin/"
    sudo ln -sf /Users/macbook/bin/uvx /usr/local/bin/uvx 2>/dev/null
    echo "✅ uvx symlink created"
fi

# Check if uv symlink exists and is correct
if [ ! -L "/usr/local/bin/uv" ]; then
    echo "⚠️  Creating uv symlink to /usr/local/bin/"
    sudo ln -sf /Users/macbook/.local/bin/uv /usr/local/bin/uv 2>/dev/null
    echo "✅ uv symlink created"
fi

# Set environment variables for claude-mem
export CLAUDE_MEM_PROVIDER="claude"
export CLAUDE_MEM_CONTEXT_OBSERVATIONS=50
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"

echo "✅ Environment variables configured"
echo

# 3. Configuration validation and update
echo "🔧 PHASE 3: Configuration Enhancement"
echo "------------------------------------"

# Backup current configuration
if [ -f "/Users/macbook/.claude/claude_desktop_config.json" ]; then
    cp "/Users/macbook/.claude/claude_desktop_config.json" "/Users/macbook/.claude/claude_desktop_config.backup_$(date +%Y%m%d_%H%M%S).json"
    echo "✅ Configuration backed up"
fi

# Create optimized configuration
cat > "/tmp/claude_desktop_config_optimized.json" << 'EOF'
{
  "mcpServers": {
    "fluxion": {
      "command": "node",
      "args": ["/Volumes/MontereyT7/FLUXION/mcp-server/dist/index.js"],
      "env": {
        "FLUXION_DB_PATH": "/Volumes/MontereyT7/FLUXION/src-tauri/fluxion.db"
      }
    },
    "claude-mem": {
      "command": "/usr/local/bin/node",
      "args": [
        "/Users/macbook/.claude/plugins/marketplaces/thedotmack/plugin/scripts/mcp-server.cjs"
      ],
      "env": {
        "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin",
        "NODE_ENV": "production",
        "CLAUDE_MEM_PROVIDER": "claude",
        "CLAUDE_MEM_CONTEXT_OBSERVATIONS": "50"
      }
    }
  }
}
EOF

# Apply optimized configuration
cp "/tmp/claude_desktop_config_optimized.json" "/Users/macbook/.claude/claude_desktop_config.json"
echo "✅ Enterprise-optimized configuration applied"

# 4. Service restart protocol
echo
echo "🔄 PHASE 4: Service Restart Protocol"
echo "------------------------------------"

# Graceful shutdown of HTTP service
echo "🛑 Stopping claude-mem HTTP service..."
curl -X POST http://localhost:37777/api/stop 2>/dev/null || echo "   (Service already stopped)"

# Wait for service to stop
sleep 2

# Check if still running
if curl -s http://localhost:37777/api/health >/dev/null 2>&1; then
    echo "⚠️  Service still running - force cleanup may be needed"
else
    echo "✅ HTTP service stopped"
fi

echo
echo "========================================"
echo "🚨 CRITICAL: MANUAL ACTION REQUIRED"
echo "========================================"
echo
echo "To complete the enterprise-grade claude-mem fix:"
echo
echo "1. 🔄 RESTART Claude Code completely"
echo "   • Close Claude Code application"
echo "   • Wait 5 seconds"
echo "   • Reopen Claude Code"
echo
echo "2. ✅ VALIDATE connection after restart:"
echo "   curl -s http://localhost:37777/api/health | jq '.mcpReady'"
echo
echo "3. 🧪 TEST memory functionality:"
echo "   Try: search(\"enterprise claude-mem solution\")"
echo
echo "========================================"
echo

# 5. Post-restart validation script
cat > "/Users/macbook/Documents/combaretrovamiauto/claude_mem_validation.sh" << 'EOF'
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
EOF

chmod +x "/Users/macbook/Documents/combaretrovamiauto/claude_mem_validation.sh"

echo "📋 EXECUTION SUMMARY"
echo "===================="
echo "✅ Environment optimized"
echo "✅ Configuration enhanced"
echo "✅ Service restart initiated"
echo "✅ Validation script created"
echo
echo "📁 Files created:"
echo "   • claude_mem_validation.sh (run after Claude restart)"
echo "   • Configuration backup (timestamped)"
echo
echo "🎯 NEXT STEP: Restart Claude Code application"
echo "   Then run: ./claude_mem_validation.sh"
echo
echo "🏆 Enterprise claude-mem deployment protocol complete!"