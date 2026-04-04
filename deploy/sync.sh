#!/bin/bash
set -euo pipefail

# ARGOS — Atomic Deploy via rsync + symlink swap
# Usage: bash deploy/sync.sh [--skip-restart]

IMAC="gianlucadistasi@192.168.1.2"
REMOTE_BASE="/Users/gianlucadistasi/Documents/app-antigravity-auto"
RELEASE_DIR="$REMOTE_BASE/releases/$(date +%Y%m%d_%H%M%S)"
CURRENT_LINK="$REMOTE_BASE/current"
PM2_PATH="\$HOME/.nvm/versions/node/v20.11.0/bin:\$HOME/.npm-global/bin:\$PATH"
SKIP_RESTART="${1:-}"

echo "=== ARGOS Deploy ==="
echo "Release: $RELEASE_DIR"

# 1. Verify SSH connectivity
echo "[1/6] Verifying SSH..."
ssh -o ConnectTimeout=5 "$IMAC" "echo ok" > /dev/null 2>&1 || {
    echo "ERROR: Cannot reach iMac at $IMAC"
    exit 1
}

# 2. Create release directory
echo "[2/6] Creating release directory..."
ssh "$IMAC" "mkdir -p $RELEASE_DIR"

# 3. rsync project files (exclude secrets, data, node_modules)
echo "[3/6] Syncing files..."
rsync -az --delete \
    --exclude='.env' \
    --exclude='node_modules/' \
    --exclude='.wwebjs_auth/' \
    --exclude='.wwebjs_cache/' \
    --exclude='*.sqlite' \
    --exclude='*.sqlite-wal' \
    --exclude='*.sqlite-shm' \
    --exclude='*.duckdb' \
    --exclude='*.duckdb.wal' \
    --exclude='__pycache__/' \
    --exclude='.DS_Store' \
    --exclude='dossiers/*.pdf' \
    --exclude='data/batch_results/' \
    --exclude='.git/' \
    --exclude='.playwright-mcp/' \
    --exclude='assets/' \
    --exclude='s62_*.png' \
    --exclude='fb_captcha.png' \
    --exclude='landing_full_page.png' \
    ./ "$IMAC:$RELEASE_DIR/"

# 4. Symlink .env from persistent location
echo "[4/6] Linking .env..."
ssh "$IMAC" "
    # Ensure persistent .env exists
    [ -f $REMOTE_BASE/wa-intelligence/.env ] || touch $REMOTE_BASE/wa-intelligence/.env
    ln -sf $REMOTE_BASE/wa-intelligence/.env $RELEASE_DIR/wa-intelligence/.env
"

# 5. Rebuild node_modules only if package.json changed
echo "[5/6] Checking node_modules..."
ssh "$IMAC" "
    export PATH=$PM2_PATH
    cd $RELEASE_DIR/wa-intelligence
    # Copy existing node_modules if available (hardlink for speed)
    if [ -d $CURRENT_LINK/wa-intelligence/node_modules ]; then
        cp -al $CURRENT_LINK/wa-intelligence/node_modules $RELEASE_DIR/wa-intelligence/node_modules 2>/dev/null || true
    fi
    npm ci --production 2>&1 | tail -3
"

# 6. Atomic symlink swap
echo "[6/6] Swapping symlink..."
ssh "$IMAC" "ln -sfn $RELEASE_DIR $CURRENT_LINK"

# Restart daemon (unless --skip-restart)
if [ "$SKIP_RESTART" != "--skip-restart" ]; then
    echo ""
    echo "Restarting daemon..."
    ssh "$IMAC" "
        export PATH=$PM2_PATH
        cd $CURRENT_LINK/wa-intelligence
        set -a && source .env 2>/dev/null && set +a
        pm2 restart argos-wa-daemon --update-env 2>&1 | tail -5
    "

    # Wait for daemon to come up
    sleep 15

    # Healthcheck
    echo ""
    echo "Healthcheck..."
    bash "$(dirname "$0")/healthcheck.sh" || {
        echo "WARN: Healthcheck failed — consider rollback"
    }
fi

# Cleanup old releases (keep last 5)
ssh "$IMAC" "ls -dt $REMOTE_BASE/releases/*/ 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true"

echo ""
echo "=== Deploy Complete ==="
echo "Release: $RELEASE_DIR"
echo "Rollback: ssh $IMAC \"ln -sfn PREVIOUS_RELEASE $CURRENT_LINK && pm2 restart argos-wa-daemon\""
