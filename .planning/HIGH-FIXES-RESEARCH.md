# HIGH Security Fixes — Enterprise Research Report

**Date:** 2026-04-10 | **System:** ARGOS Automotive (iMac server, PM2-managed)
**Stack:** Node.js (wa-daemon :9191) + Python (Flask dashboard :8080, tg-bot, scheduler, response-analyzer) + SQLite WAL

---

## Finding 1: Dashboard Default Password + No Startup Assertion

### Current State

`auth.py` line 18: `DASHBOARD_PASSWORD = os.environ.get('ARGOS_DASHBOARD_PASSWORD', 'argos2026')` — hardcoded fallback. `wa-daemon.js` line 646: `const API_KEY = process.env.ARGOS_API_KEY || ''` — empty string fallback means `if (API_KEY && ...)` guard is bypassed when env var is missing, leaving all endpoints unauthenticated.

### Enterprise-Grade Solution

**A. Replace plaintext comparison with Argon2id hashing**

Argon2id is the 2025-2026 gold standard (OWASP recommendation). Use `argon2-cffi` for Python.

```bash
pip install argon2-cffi
```

**Generate hash once (CLI or setup script):**

```python
from argon2 import PasswordHasher
ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)  # OWASP minimum
hash = ph.hash("your-strong-password-here")
print(hash)  # Store this in .env as ARGOS_DASHBOARD_PASSWORD_HASH
```

**Updated `auth.py`:**

```python
import sys
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)

# ── Fail-fast: refuse to start without password hash ──
DASHBOARD_PASSWORD_HASH = os.environ.get('ARGOS_DASHBOARD_PASSWORD_HASH')
if not DASHBOARD_PASSWORD_HASH:
    print("FATAL: ARGOS_DASHBOARD_PASSWORD_HASH not set in .env. "
          "Dashboard refuses to start with default password.", file=sys.stderr)
    sys.exit(1)

SECRET_KEY = os.environ.get('ARGOS_SECRET_KEY')
if not SECRET_KEY:
    print("FATAL: ARGOS_SECRET_KEY not set in .env. "
          "Session cookies would be predictable.", file=sys.stderr)
    sys.exit(1)

def verify_password(password: str) -> bool:
    """Argon2id verification (timing-safe by design)."""
    try:
        return ph.verify(DASHBOARD_PASSWORD_HASH, password)
    except VerifyMismatchError:
        return False
```

**B. Fail-fast startup assertion for wa-daemon.js:**

```javascript
// ── Top of wa-daemon.js, BEFORE http.createServer ──
const REQUIRED_ENV = ['ARGOS_API_KEY', 'DB_PATH'];
const missing = REQUIRED_ENV.filter(k => !process.env[k]);
if (missing.length > 0) {
    console.error(`FATAL: Missing required env vars: ${missing.join(', ')}`);
    console.error('Port 9191 would be unauthenticated. Refusing to start.');
    process.exit(1);
}
```

**C. Optional: macOS Keychain integration for secrets**

The `keyring` Python library integrates with macOS Keychain natively:

```bash
pip install keyring
```

```python
import keyring
# Store once: keyring.set_password("argos", "dashboard", "<hash>")
# Retrieve:  keyring.get_password("argos", "dashboard")
```

This avoids secrets in `.env` files entirely. However, for PM2-managed processes, `.env` with `chmod 600` is simpler and equally secure on a single-user server. Keychain integration adds complexity (Keychain Access prompts, PM2 service user context) without proportional benefit for this setup.

**Recommendation:** Use `.env` with `chmod 600` + Argon2id hash + fail-fast assertions. Skip Keychain.

### Libraries/Tools

| Library | Purpose | License |
|---------|---------|---------|
| `argon2-cffi` | Argon2id password hashing (Python) | MIT |
| `keyring` | macOS Keychain integration (optional) | MIT |

### Estimated Implementation Time

2 hours (generate hash, update auth.py, update wa-daemon.js, update .env on iMac, test, deploy)

### Risk If Not Fixed

**CRITICAL.** Dashboard is accessible with known default password `argos2026` (visible in public-turned-private repo history). If `ARGOS_API_KEY` env var is lost during PM2 restart, all WA daemon endpoints become unauthenticated — anyone on the LAN can send WhatsApp messages as Luca Ferretti.

---

## Finding 2: Missing `busy_timeout` in 4 SQLite Connections

### Current State

`state_machine.py` and `dashboard/db.py` correctly set WAL + busy_timeout=10000. But:
- `telegram-handler.py` `db_query()` (line 93): `sqlite3.connect(DB_PATH)` — **no timeout, no WAL**
- `telegram-handler.py` `db_exec()` (line 107): `sqlite3.connect(DB_PATH, timeout=10)` — has timeout but **no WAL pragma**
- `scheduler.py` `load_active_dealers()` (line 103): `sqlite3.connect(DB_PATH)` — **no timeout, no WAL**
- `response-analyzer.py` (lines 767, 1145, 1540, 1584): mixed — some have WAL+timeout, some have only timeout, line 767 has timeout but no WAL

4 concurrent writers: wa-daemon (better-sqlite3), tg-bot, scheduler, response-analyzer.

### Enterprise-Grade Solution

**Create a shared `db_utils.py` module** — single source of truth for all SQLite connections:

```python
# wa-intelligence/db_utils.py
"""
db_utils.py — ARGOS SQLite Connection Factory
Single source of truth for all SQLite connection configuration.
All Python processes MUST use get_connection() instead of sqlite3.connect().
"""

import sqlite3
import os
import sys

DB_PATH = os.environ.get(
    'ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite')
)

# ── Production PRAGMAs (applied to EVERY connection) ──
_PRAGMAS = [
    ('journal_mode', 'WAL'),       # concurrent reads during writes
    ('busy_timeout', '10000'),     # 10s wait on SQLITE_BUSY (not 0!)
    ('synchronous', 'NORMAL'),     # safe with WAL, 2x faster than FULL
    ('foreign_keys', 'ON'),        # enforce FK constraints
    ('cache_size', '-8000'),       # 8MB page cache (negative = KB)
]


def get_connection(db_path: str = None, row_factory=None) -> sqlite3.Connection:
    """
    Returns a configured SQLite connection with all production PRAGMAs.

    Usage:
        from db_utils import get_connection
        con = get_connection()
        # ... use con ...
        con.close()

    Or as context manager:
        with get_connection() as con:
            con.execute("INSERT ...")
    """
    path = db_path or DB_PATH
    con = sqlite3.connect(path, timeout=10)

    if row_factory:
        con.row_factory = row_factory

    for pragma, value in _PRAGMAS:
        con.execute(f'PRAGMA {pragma} = {value}')

    return con


def get_row_connection(db_path: str = None) -> sqlite3.Connection:
    """Convenience: connection with sqlite3.Row factory."""
    return get_connection(db_path=db_path, row_factory=sqlite3.Row)
```

**Update all consumers:**

```python
# telegram-handler.py — BEFORE
def db_query(sql, params=None):
    con = sqlite3.connect(DB_PATH)        # NO timeout, NO WAL
    ...

# telegram-handler.py — AFTER
from db_utils import get_connection

def db_query(sql, params=None):
    try:
        con = get_connection()
        con.row_factory = sqlite3.Row  # or use get_row_connection()
        ...
```

```python
# scheduler.py — BEFORE
con = sqlite3.connect(DB_PATH)            # NO timeout, NO WAL

# scheduler.py — AFTER
from db_utils import get_connection
con = get_connection(row_factory=sqlite3.Row)
```

**Node.js side (better-sqlite3) — already correct:**

```javascript
// wa-daemon.js line 77-79 — ALREADY has correct config:
_db = new Database(CONFIG.DB_PATH, { timeout: 10000 });
_db.pragma('journal_mode = WAL');
_db.pragma('busy_timeout = 10000');
```

better-sqlite3 `timeout` option is the Node equivalent of `busy_timeout`. The wa-daemon is correctly configured.

**Transaction strategy — use BEGIN IMMEDIATE:**

For write transactions with multiple concurrent writers, always use `BEGIN IMMEDIATE` to avoid deadlock-induced SQLITE_BUSY errors that bypass busy_timeout:

```python
def db_exec(sql: str, params: list = None, db_path: str = None):
    """Execute a write query with retry and BEGIN IMMEDIATE."""
    for attempt in range(3):
        try:
            con = get_connection(db_path=db_path)
            con.execute('BEGIN IMMEDIATE')
            con.execute(sql, params or [])
            con.commit()
            con.close()
            return True
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise
    return False
```

### Libraries/Tools

No additional libraries needed. `sqlite3` is stdlib. `better-sqlite3` is already installed.

### Estimated Implementation Time

3 hours (create db_utils.py, update 4 files, test concurrent writes, deploy)

### Risk If Not Fixed

**HIGH.** Without `busy_timeout`, any write contention between the 4 processes causes an immediate `SQLITE_BUSY` exception instead of waiting. The tg-bot `db_query()` (no timeout at all) is the worst offender — a single concurrent write from wa-daemon will crash the query. Without WAL pragma on some connections, those connections may not benefit from WAL concurrency (SQLite sets journal mode per-database, but the pragma must be issued to confirm/enable it). Missing `synchronous=NORMAL` means unnecessary fsync overhead.

---

## Finding 3: DB File Permissions chmod 644 on iMac

### Current State

`dealer_network.sqlite` and `cove_tracker.duckdb` are world-readable (644 = `rw-r--r--`) on iMac. Any local user or process can read the entire database including phone numbers, dealer data, and conversation history.

### Enterprise-Grade Solution

**Set restrictive permissions:**

```bash
# On iMac — run once after deploy
chmod 600 ~/Documents/app-antigravity-auto/dealer_network.sqlite
chmod 600 ~/Documents/app-antigravity-auto/dealer_network.sqlite-wal
chmod 600 ~/Documents/app-antigravity-auto/dealer_network.sqlite-shm
chmod 600 ~/Documents/app-antigravity-auto/src/cove/data/cove_tracker.duckdb

# Directory permissions (prevent listing)
chmod 700 ~/Documents/app-antigravity-auto/
```

**Does 600 affect PM2?** No. PM2 runs as the same user (`gianlucadistasi`) on iMac. All processes (wa-daemon, tg-bot, scheduler, dashboard) run under this user. `chmod 600` means owner read/write — exactly what's needed.

**Verify PM2 user:**

```bash
pm2 list  # shows user
ps aux | grep wa-daemon  # confirms process owner
```

**Add to deploy script (`deploy/sync.sh`):**

```bash
# ── Post-deploy: lock down DB files ──
echo "[deploy] Setting DB permissions to 600..."
chmod 600 "$HOME/Documents/app-antigravity-auto/dealer_network.sqlite"*
chmod 600 "$HOME/Documents/app-antigravity-auto/src/cove/data/cove_tracker.duckdb"*
```

**Add to monitoring script (verify permissions haven't drifted):**

```python
# In tools/monitoring.py — add permission check
import stat

def check_db_permissions(db_path):
    mode = os.stat(db_path).st_mode
    if mode & (stat.S_IRGRP | stat.S_IROTH):  # group or other readable
        alert_telegram(f"DB {db_path} has insecure permissions: {oct(mode)}")
        os.chmod(db_path, 0o600)  # auto-fix
```

**macOS-specific notes:**
- macOS respects POSIX permissions. No ACL complications for single-user PM2.
- If using Time Machine, backups inherit permissions — no special handling needed.
- The `-wal` and `-shm` files MUST also be 600 (SQLite creates them with default umask).

**Set umask for PM2 processes:**

```bash
# In ecosystem.config.js or PM2 startup
# Ensures new files created by PM2 processes are 600
umask 077
```

### Libraries/Tools

None needed. Standard POSIX permissions.

### Estimated Implementation Time

30 minutes (chmod on iMac, update deploy script, add monitoring check)

### Risk If Not Fixed

**HIGH.** Any process or user on the iMac can read the full database including: dealer phone numbers (GDPR PII), conversation content, API keys stored in config tables, business intelligence data. On a multi-user macOS system this would be critical; on a single-user iMac the risk is lower but still violates defense-in-depth and GDPR best practices.

---

## Finding 4: macOS Firewall Disabled on iMac

### Current State

macOS Application Firewall is OFF. Ports 9191 (WA daemon) and 8080 (dashboard) are bound to `0.0.0.0` (all interfaces), meaning any device on the LAN (or WAN if router port-forwards) can access them.

### Enterprise-Grade Solution

There are three layers to address, in order of priority:

**Layer 1 (Simplest, do FIRST): Bind to 127.0.0.1**

This is the single most effective change — no firewall configuration needed:

```javascript
// wa-daemon.js — change server.listen
server.listen(9191, '127.0.0.1', () => {
    log('INFO', 'HTTP server on 127.0.0.1:9191 (localhost only)');
});
```

```python
# dashboard/run_dashboard.py or app.py — bind to localhost
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8080)
```

After this change, ports are only accessible from the iMac itself. MacBook access requires a tunnel (Layer 3).

**Layer 2: Enable `pf` packet filter**

macOS Application Firewall is application-level only (allow/deny per app). For port-level control, use `pf` (packet filter, inherited from OpenBSD):

```bash
# /etc/pf.anchors/argos.rules
# Allow loopback
pass quick on lo0 all

# Allow established connections
pass in quick proto tcp from any to any flags A/A

# Allow LAN access to ARGOS ports ONLY from MacBook
# (replace 192.168.1.X with MacBook's static LAN IP)
pass in quick on en0 proto tcp from 192.168.1.0/24 to any port { 8080, 9191 }

# Block all other inbound to ARGOS ports
block in quick on en0 proto tcp from any to any port { 8080, 9191 }
```

```bash
# /etc/pf.conf — add at the end (before any existing anchors)
anchor "argos"
load anchor "argos" from "/etc/pf.anchors/argos.rules"
```

```bash
# Enable and test
sudo pfctl -vnf /etc/pf.conf    # validate syntax (dry run)
sudo pfctl -ef /etc/pf.conf     # enable
sudo pfctl -sr                   # show active rules
```

**Important macOS caveat:** macOS upgrades may revert `/etc/pf.conf`. Keep a backup of your rules in the project and re-apply after upgrades.

**Create a LaunchDaemon to persist pf rules across reboots:**

```xml
<!-- /Library/LaunchDaemons/com.argos.pf.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.argos.pf</string>
    <key>ProgramArguments</key>
    <array>
        <string>/sbin/pfctl</string>
        <string>-ef</string>
        <string>/etc/pf.conf</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

**Layer 3: Tailscale for remote MacBook access (recommended)**

If you bind to 127.0.0.1 (Layer 1), the MacBook needs a way to access the dashboard remotely. Two options:

**Option A — SSH tunnel (zero cost, already works):**

```bash
# From MacBook — forward local 8080 to iMac's localhost:8080
ssh -L 8080:127.0.0.1:8080 -L 9191:127.0.0.1:9191 gianlucadistasi@192.168.1.2
# Then access http://localhost:8080 on MacBook
```

**Option B — Tailscale (recommended, free tier, zero config NAT traversal):**

```bash
# Install on both iMac and MacBook
brew install tailscale

# On iMac: bind services to Tailscale interface
# wa-daemon listens on 100.x.x.x:9191 (Tailscale IP) + 127.0.0.1:9191
# dashboard listens on 100.x.x.x:8080 + 127.0.0.1:8080

# From MacBook: access via Tailscale hostname
# http://imac.tail12345.ts.net:8080
```

Tailscale free tier: 3 users, 100 devices. WireGuard-encrypted, zero port forwarding, works from anywhere (not just LAN). **This is the enterprise recommendation** — SSH tunnels are fragile and require the tunnel to be active.

### Recommendation

1. **Immediately:** Bind to `127.0.0.1` (30 min, zero risk)
2. **This week:** Set up Tailscale on both machines (1 hour)
3. **Optional:** Configure `pf` rules as defense-in-depth (1 hour)
4. **Skip:** macOS Application Firewall (it's per-app, not per-port — less useful here)

### Libraries/Tools

| Tool | Purpose | Cost |
|------|---------|------|
| `pf` (built-in) | Packet filter firewall | Free (macOS built-in) |
| Tailscale | Encrypted mesh VPN | Free tier (3 users, 100 devices) |
| SSH | Tunnel for remote access | Free (built-in) |

### Estimated Implementation Time

- Bind to 127.0.0.1: 30 minutes
- Tailscale setup: 1 hour
- pf configuration: 1 hour
- Total: 2.5 hours

### Risk If Not Fixed

**HIGH.** Any device on the same LAN (WiFi guests, compromised IoT devices, other household members) can:
- Access the dashboard (with the known default password `argos2026`)
- Send WhatsApp messages via the unauthenticated API (if API key is missing)
- Read all dealer data, conversation history, and business intelligence
- Combined with Finding 1 (default password), this is effectively **unauthenticated remote access to the entire system**

---

## Finding 5: No Automated DB Backup (6h Schedule)

### Current State

One manual backup exists: `dealer_network.sqlite.bak_20260402`. The `security.md` policy requires automated 6h backups using `sqlite3 .backup`. No automation is in place.

### Enterprise-Grade Solution

**A. Backup script:**

```bash
#!/bin/bash
# ~/scripts/argos_backup.sh — ARGOS SQLite Automated Backup
# Runs every 6h via LaunchAgent. Uses sqlite3 .backup (safe for WAL mode).

set -euo pipefail

# ── Config ──
DB_PATH="$HOME/Documents/app-antigravity-auto/dealer_network.sqlite"
DUCKDB_PATH="$HOME/Documents/app-antigravity-auto/src/cove/data/cove_tracker.duckdb"
BACKUP_DIR="$HOME/backups/argos"
RETENTION_DAYS=14        # keep 14 days = 56 backups (every 6h)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="$BACKUP_DIR/backup.log"

# ── Setup ──
mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

alert_telegram() {
    local TOKEN=$(grep ARGOS_TELEGRAM_TOKEN "$HOME/Documents/app-antigravity-auto/wa-intelligence/.env" 2>/dev/null | cut -d= -f2)
    local CHAT=$(grep ARGOS_TELEGRAM_CHAT_ID "$HOME/Documents/app-antigravity-auto/wa-intelligence/.env" 2>/dev/null | cut -d= -f2)
    if [ -n "$TOKEN" ] && [ -n "$CHAT" ]; then
        curl -s "https://api.telegram.org/bot${TOKEN}/sendMessage" \
            -d chat_id="$CHAT" \
            -d text="$1" \
            -d parse_mode=Markdown >/dev/null 2>&1 || true
    fi
}

# ── SQLite Backup (safe for WAL — uses backup API) ──
SQLITE_BACKUP="$BACKUP_DIR/dealer_network_${TIMESTAMP}.sqlite"
log "Starting SQLite backup..."

if sqlite3 "$DB_PATH" ".backup '$SQLITE_BACKUP'"; then
    BACKUP_SIZE=$(stat -f%z "$SQLITE_BACKUP" 2>/dev/null || stat -c%s "$SQLITE_BACKUP")
    log "SQLite backup OK: $SQLITE_BACKUP (${BACKUP_SIZE} bytes)"
else
    log "ERROR: SQLite backup FAILED"
    alert_telegram "ARGOS BACKUP FAILED: sqlite3 .backup returned error"
    exit 1
fi

# ── Integrity check on backup ──
log "Running integrity check on backup..."
INTEGRITY=$(sqlite3 "$SQLITE_BACKUP" "PRAGMA integrity_check;" 2>&1)
if [ "$INTEGRITY" = "ok" ]; then
    log "Integrity check PASSED"
else
    log "ERROR: Integrity check FAILED: $INTEGRITY"
    alert_telegram "ARGOS BACKUP INTEGRITY FAILED: $INTEGRITY"
    # Keep the backup anyway for forensics, but alert
fi

# ── DuckDB backup (simple copy — DuckDB handles its own WAL) ──
if [ -f "$DUCKDB_PATH" ]; then
    DUCK_BACKUP="$BACKUP_DIR/cove_tracker_${TIMESTAMP}.duckdb"
    cp "$DUCKDB_PATH" "$DUCK_BACKUP"
    log "DuckDB backup OK: $DUCK_BACKUP"
fi

# ── Rotation: delete backups older than RETENTION_DAYS ──
DELETED=$(find "$BACKUP_DIR" -name "*.sqlite" -o -name "*.duckdb" | \
    while read f; do
        FAGE=$(( ($(date +%s) - $(stat -f%m "$f" 2>/dev/null || stat -c%Y "$f")) / 86400 ))
        if [ "$FAGE" -gt "$RETENTION_DAYS" ]; then
            rm "$f"
            echo "$f"
        fi
    done | wc -l)
log "Rotation: deleted $DELETED old backups (retention: ${RETENTION_DAYS}d)"

# ── Permissions ──
chmod 600 "$BACKUP_DIR"/*.sqlite 2>/dev/null || true
chmod 600 "$BACKUP_DIR"/*.duckdb 2>/dev/null || true

log "Backup complete."
```

**B. `.backup` vs `VACUUM INTO` comparison:**

| Feature | `sqlite3 .backup` | `VACUUM INTO` |
|---------|-------------------|---------------|
| Safe during writes | Yes (uses backup API) | Yes (snapshot) |
| WAL-aware | Yes (includes WAL content) | Yes (creates clean DB) |
| Speed | Fast (page copy) | Slower (rebuilds + compacts) |
| Output size | Same as source | Compacted (smaller) |
| CPU/IO impact | Low | Higher |
| Recommended for | Frequent automated backups | Weekly maintenance |

**Recommendation:** Use `.backup` for the 6h automated cycle. Run `VACUUM INTO` weekly during off-peak hours for a compacted archive.

**C. LaunchAgent for macOS scheduling:**

```xml
<!-- ~/Library/LaunchAgents/com.argos.backup.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.argos.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/gianlucadistasi/scripts/argos_backup.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>21600</integer>  <!-- 6 hours = 21600 seconds -->
    <key>StandardOutPath</key>
    <string>/tmp/argos-backup-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/argos-backup-stderr.log</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

```bash
# Install and load
launchctl load ~/Library/LaunchAgents/com.argos.backup.plist
launchctl list | grep argos.backup  # verify
```

**Why LaunchAgent over cron or PM2 cron:**
- `cron`: Works but no macOS integration, no automatic restart after reboot if user not logged in
- `PM2 cron`: PM2 `cron_restart` restarts the process, not runs a script — wrong tool
- `LaunchAgent`: macOS-native, runs even if terminal is closed, proper logging, survives reboots

**D. Offsite backup (zero cost):**

```bash
# Install rclone
brew install rclone

# Configure Google Drive remote (one-time interactive setup)
rclone config
# → New remote → name: gdrive → type: drive → default options → authorize

# Sync backups to Google Drive (add to end of argos_backup.sh)
if command -v rclone &>/dev/null; then
    log "Syncing to Google Drive..."
    rclone sync "$BACKUP_DIR" gdrive:argos-backups/ \
        --transfers 1 \
        --bwlimit 1M \
        --log-level ERROR 2>>"$LOG"
    log "Offsite sync complete"
fi
```

**Cost:** Google Drive free tier = 15 GB. SQLite DB is ~5-10 MB. Even with 56 retained backups, total is ~500 MB. Effectively infinite free storage for this use case.

**Optional encryption before upload:**

```bash
# rclone crypt wraps the remote — files encrypted before upload
rclone config
# → New remote → name: gdrive-crypt → type: crypt → remote: gdrive:argos-backups/
# → filename_encryption: standard → directory_name_encryption: true → password: <generate>
```

### Libraries/Tools

| Tool | Purpose | Cost |
|------|---------|------|
| `sqlite3` (built-in) | `.backup` command | Free |
| `launchctl` (built-in) | macOS job scheduler | Free |
| `rclone` | Offsite sync to Google Drive | Free (OSS, Apache 2.0) |
| Google Drive | Offsite storage | Free (15 GB) |

### Estimated Implementation Time

- Backup script + LaunchAgent: 2 hours
- rclone offsite setup: 1 hour
- Total: 3 hours

### Risk If Not Fixed

**HIGH.** A single `rm`, corruption event, or disk failure destroys ALL dealer data, conversation history, and business intelligence with no recovery path. The existing manual backup is 8 days old (`bak_20260402`). The security policy explicitly requires 6h automated backups — this is a compliance violation of the project's own security gates.

---

## Implementation Priority

| # | Finding | Severity | Effort | Priority |
|---|---------|----------|--------|----------|
| 1 | Default password + no startup assertion | CRITICAL | 2h | **P0 — Do NOW** |
| 4 | Firewall disabled + bind 0.0.0.0 | HIGH | 30min (bind fix) | **P0 — Do NOW** |
| 2 | Missing busy_timeout in 4 connections | HIGH | 3h | **P1 — This week** |
| 5 | No automated backup | HIGH | 3h | **P1 — This week** |
| 3 | DB permissions 644 | HIGH | 30min | **P1 — This week** |

**Total estimated effort: 9 hours**

Findings 1 and 4 should be fixed together in a single deploy session — they compound each other (default password + open firewall = unauthenticated access from any LAN device).

---

## Sources

- [SQLite WAL Documentation](https://www.sqlite.org/wal.html)
- [SQLite Busy Timeout and Locking](https://berthub.eu/articles/posts/a-brief-post-on-sqlite3-database-locked-despite-timeout/)
- [SQLite Concurrent Writes](https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/)
- [SQLite Production Setup 2026](https://oneuptime.com/blog/post/2026-02-02-sqlite-production-setup/view)
- [Password Hashing Guide 2025: Argon2 vs Bcrypt](https://guptadeepak.com/the-complete-guide-to-password-hashing-argon2-vs-bcrypt-vs-scrypt-vs-pbkdf2-2026/)
- [argon2-cffi PyPI](https://pypi.org/project/argon2-cffi/)
- [OWASP Argon2id Recommendations](https://hackernoon.com/argon2-in-practice-how-to-implement-secure-password-hashing-in-your-application)
- [macOS pf Firewall Configuration](https://iyanmv.medium.com/setting-up-correctly-packet-filter-pf-firewall-on-any-macos-from-sierra-to-big-sur-47e70e062a0e)
- [pf Firewall Rules on macOS](https://blog.neilsabol.site/post/quickly-easily-adding-pf-packet-filter-firewall-rules-macos-osx/)
- [macOS pf Restrict Network Access](https://inventivehq.com/knowledge-base/macos/how-to-configure-macos-firewall-pf)
- [Tailscale SSH Docs](https://tailscale.com/docs/features/tailscale-ssh)
- [Tailscale SSH Setup Guide 2026](https://oneuptime.com/blog/post/2026-01-27-tailscale-ssh/view)
- [From SSH Tunnels to Tailscale](https://medium.com/israeli-tech-radar/from-ssh-tunnels-to-tailscale-e391ddb3cf18)
- [SQLite Backup API](https://sqlite.org/backup.html)
- [keyring PyPI — macOS Keychain](https://pypi.org/project/keyring/)
- [Node.js Env Variable Validation](https://medium.com/@davidminaya04/validating-environment-variables-in-node-js-c1c917a45d66)
- [Node.js Env Var Best Practices](https://reintech.io/blog/nodejs-environment-variables-best-practices-security)
- [rclone — Cloud Storage Sync](https://rclone.org/)
- [rclone Google Drive Setup](https://rclone.org/drive/)
- [Free Backup with rclone + Google Drive](https://forum.rclone.org/t/howto-guide-get-free-backup-service-for-your-database-and-storage-files/19833)
