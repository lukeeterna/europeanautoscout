#!/usr/bin/env bash
set -euo pipefail

EXPECTED_SHA="${1:-${GITHUB_SHA:-}}"
[[ "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]] || { echo 'DIAG=BLOCKED_BAD_SHA'; exit 64; }

HOST="${ARGOS_IMAC_HOST:-iMac-di-gianluca.local}"
USER="${ARGOS_IMAC_USER:-gianlucadistasi}"
ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=yes \
  -o ServerAliveInterval=5 -o ServerAliveCountMax=2 "$USER@$HOST" python3 <<'PY'
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess

home = Path.home()
canonical_primary = home / 'Documents/app-antigravity-auto/dealer_network.sqlite'
canonical_bridge = home / 'Documents/app-antigravity-auto/comm-broker/bridge.sqlite'


def run(args, timeout=10):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def proc_rows():
    out = run(['ps', '-axo', 'pid=,command=']).stdout
    rows = []
    for line in out.splitlines():
        m = re.match(r'^\s*(\d+)\s+(.*)$', line)
        if m:
            rows.append((int(m.group(1)), m.group(2)))
    return rows


def selected_env(pid, keys):
    r = run(['ps', 'eww', '-p', str(pid), '-o', 'command='])
    text = r.stdout if r.returncode == 0 else ''
    values = {}
    for key in keys:
        m = re.search(r'(?:^|\s)' + re.escape(key) + r'=([^\s]+)', text)
        if m:
            values[key] = m.group(1)
    return values


def db_facts(label, path):
    p = Path(path).expanduser()
    present = p.is_file()
    real = str(p.resolve()) if present else 'ABSENT'
    print(f'{label}_PRESENT={str(present).upper()}')
    print(f'{label}_REALPATH={real}')
    if not present:
        return
    con = sqlite3.connect(f'file:{p}?mode=ro', uri=True, timeout=5)
    try:
        quick = con.execute('PRAGMA quick_check').fetchone()[0]
        tables = {str(row[0]) for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        print(f'{label}_QUICK_CHECK={quick}')
        if 'argos_runtime_state' in tables:
            state = con.execute("SELECT value FROM argos_runtime_state WHERE key='agent_status' LIMIT 1").fetchone()
            print(f'{label}_AGENT_STATUS={(state[0] if state else "ABSENT")}')
        else:
            print(f'{label}_AGENT_STATUS=NOT_APPLICABLE')
        if 'messages' in tables:
            outbound = con.execute("SELECT COUNT(*) FROM messages WHERE UPPER(direction)='OUTBOUND'").fetchone()[0]
            print(f'{label}_OUTBOUND_TOTAL={outbound}')
        else:
            print(f'{label}_OUTBOUND_TOTAL=NOT_APPLICABLE')
        if 'bridge_outbound' in tables:
            cols = {str(row[1]) for row in con.execute("PRAGMA table_info('bridge_outbound')").fetchall()}
            if {'approved_ts', 'sent_ts'}.issubset(cols):
                condition = 'approved_ts IS NOT NULL AND sent_ts IS NULL'
                if 'template_id' in cols:
                    condition += ' AND template_id IS NOT NULL'
                pending = con.execute(f'SELECT COUNT(*) FROM bridge_outbound WHERE {condition}').fetchone()[0]
                print(f'{label}_PENDING_APPROVED={pending}')
        print(f'{label}_SIZE={p.stat().st_size}')
    finally:
        con.close()


rows = proc_rows()
writers = [(pid, cmd) for pid, cmd in rows if 'wa-daemon.js' in cmd and 'node' in cmd.lower()]
print(f'DIAG_WRITER_COUNT={len(writers)}')
if len(writers) != 1:
    print('DIAG=BLOCKED_WRITER_COUNT')
    raise SystemExit(20)

pid, _ = writers[0]
env = selected_env(pid, (
    'ARGOS_DB_PATH', 'BRIDGE_DB_PATH', 'ARGOS_WA_SESSION_DIR',
    'ARGOS_WA_CLIENT_ID', 'CHROME_EXECUTABLE_PATH', 'ARGOS_WA_TRANSPORT',
    'ARGOS_AUTOMATION_ENABLED',
))
writer_primary = Path(env.get('ARGOS_DB_PATH') or canonical_primary)
writer_bridge = Path(env.get('BRIDGE_DB_PATH') or canonical_bridge)
print(f'DIAG_WRITER_DB_PATH={writer_primary}')
print(f'DIAG_WRITER_BRIDGE_PATH={writer_bridge}')
print(f'DIAG_SESSION_DIR={env.get("ARGOS_WA_SESSION_DIR", "UNKNOWN")}')
print(f'DIAG_CLIENT_ID={env.get("ARGOS_WA_CLIENT_ID", "UNKNOWN")}')
print(f'DIAG_CHROME_ENV={env.get("CHROME_EXECUTABLE_PATH", "UNKNOWN")}')
print(f'DIAG_TRANSPORT_ENV={env.get("ARGOS_WA_TRANSPORT", "UNKNOWN")}')
print(f'DIAG_AUTOMATION_ENV={env.get("ARGOS_AUTOMATION_ENABLED", "UNKNOWN")}')

db_facts('WRITER_PRIMARY_DB', writer_primary)
db_facts('CANONICAL_PRIMARY_DB', canonical_primary)
db_facts('WRITER_BRIDGE_DB', writer_bridge)
db_facts('CANONICAL_BRIDGE_DB', canonical_bridge)

try:
    print(f'PRIMARY_DB_SAME_FILE={str(os.path.samefile(writer_primary, canonical_primary)).upper()}')
except OSError:
    print('PRIMARY_DB_SAME_FILE=FALSE')
try:
    print(f'BRIDGE_DB_SAME_FILE={str(os.path.samefile(writer_bridge, canonical_bridge)).upper()}')
except OSError:
    print('BRIDGE_DB_SAME_FILE=FALSE')

# Resolve the browser executable from the live process that owns the selected
# LocalAuth user-data directory. Only the executable path is emitted.
session = env.get('ARGOS_WA_SESSION_DIR') or ''
chrome_pids = [pid for pid, cmd in rows if session and session in cmd and 'chrome' in cmd.lower()]
print(f'DIAG_SESSION_CHROME_PROCESS_COUNT={len(chrome_pids)}')
chrome_exec = 'UNKNOWN'
for cpid in chrome_pids:
    r = run(['/usr/sbin/lsof', '-a', '-p', str(cpid), '-d', 'txt', '-Fn'])
    for line in r.stdout.splitlines():
        if line.startswith('n/') and ('Chrome' in line or 'chrome' in line):
            chrome_exec = line[1:]
            break
    if chrome_exec != 'UNKNOWN':
        break
print(f'DIAG_CHROME_EXECUTABLE={chrome_exec}')

# PM2 is installed under the user's npm-global prefix on this machine. Read
# only the daemon entry and emit allowlisted non-secret fields.
pm2 = home / '.npm-global/bin/pm2'
if pm2.is_file():
    r = run([str(pm2), 'jlist'])
    if r.returncode == 0:
        try:
            apps = json.loads(r.stdout)
        except json.JSONDecodeError:
            apps = []
        app = next((a for a in apps if a.get('name') == 'argos-wa-daemon'), None)
        pe = (app or {}).get('pm2_env') or {}
        print(f'DIAG_PM2_STATUS={pe.get("status", "UNKNOWN")}')
        print(f'DIAG_PM2_OUT_LOG={pe.get("pm_out_log_path", "UNKNOWN")}')
        print(f'DIAG_PM2_ERR_LOG={pe.get("pm_err_log_path", "UNKNOWN")}')
    else:
        print('DIAG_PM2_STATUS=JLIST_FAILED')
else:
    print('DIAG_PM2_STATUS=CLI_ABSENT')

print('DIAG=PASS_READ_ONLY')
PY
