#!/usr/bin/env bash
set -euo pipefail

EXPECTED_SHA="${1:-${GITHUB_SHA:-}}"
[[ "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]] || { echo 'CUTOVER=BLOCKED_BAD_SHA' >&2; exit 64; }

IMAC_HOST="${ARGOS_IMAC_HOST:-iMac-di-gianluca.local}"
IMAC_USER="${ARGOS_IMAC_USER:-gianlucadistasi}"
TARGET="${IMAC_USER}@${IMAC_HOST}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=yes -o ServerAliveInterval=5 -o ServerAliveCountMax=2)

echo "CUTOVER=BEGIN"
echo "EXPECTED_SHA=$EXPECTED_SHA"
echo "OUTBOUND_ACTION=NONE"
echo "TARGET_RUNTIME_STATUS=PAUSED"
echo "TARGET_AUTOMATION_ENABLED=0"

ssh "${SSH_OPTS[@]}" "$TARGET" "bash -s -- '$EXPECTED_SHA'" <<'REMOTE'
set -euo pipefail

SHA="$1"
SHORT="${SHA:0:12}"
HOME_DIR="$HOME"
RELEASE="$HOME_DIR/Documents/argos-c10-release-$SHORT"
CANONICAL_PRIMARY="$HOME_DIR/Documents/app-antigravity-auto/dealer_network.sqlite"
CANONICAL_BRIDGE="$HOME_DIR/Documents/app-antigravity-auto/comm-broker/bridge.sqlite"
# Preserve the production LocalAuth identity exactly as the live writer uses it:
# dataPath=wa-sender + clientId=argos-business -> wa-sender/session-argos-business.
SESSION_DIR="$HOME_DIR/Documents/app-antigravity-auto/wa-sender"
CLIENT_ID="argos-business"
PM2="$HOME_DIR/.npm-global/bin/pm2"
PY313="/usr/local/bin/python3.13"
CHROME_FALLBACK="$HOME_DIR/.cache/puppeteer/chrome/mac-148.0.7778.97/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
OLD_CWD=""
OLD_ROOT=""
OLD_SHA=""
MUTATED=0
BACKUP_DIR=""

export PATH="$HOME_DIR/.npm-global/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

fail() { echo "CUTOVER_BLOCKED=$*" >&2; exit 20; }

[[ -x "$PM2" ]] || fail "PM2_MISSING"
[[ -x "$PY313" ]] || fail "PYTHON313_MISSING"
command -v git >/dev/null || fail "GIT_MISSING"
command -v node >/dev/null || fail "NODE_MISSING"
command -v npm >/dev/null || fail "NPM_MISSING"
[[ -f "$CANONICAL_PRIMARY" ]] || fail "PRIMARY_DB_MISSING"
[[ -f "$CANONICAL_BRIDGE" ]] || fail "BRIDGE_DB_MISSING"
[[ -d "$SESSION_DIR/session-$CLIENT_ID" ]] || fail "LOCALAUTH_PROFILE_MISSING"

# Read current writer facts without printing its raw command/environment.
# Keep this compatible with Apple's Bash 3.2: do not use readarray/mapfile.
writer_pids="$(ps -axo pid=,command= | awk '/[w]a-daemon\.js/ && /[n]ode/ {print $1}')"
writer_count="$(printf '%s\n' "$writer_pids" | awk 'NF{n++} END{print n+0}')"
[[ "$writer_count" -eq 1 ]] || fail "PRE_SINGLE_WRITER_COUNT_${writer_count}"
OLD_PID="$(printf '%s\n' "$writer_pids" | awk 'NF{print; exit}')"
OLD_CWD="$(/usr/sbin/lsof -a -p "$OLD_PID" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n1)"
[[ -n "$OLD_CWD" ]] || fail "OLD_CWD_UNKNOWN"
OLD_ROOT="$(cd "$OLD_CWD/.." && pwd -P)"
OLD_SHA="$(git -C "$OLD_ROOT" rev-parse HEAD 2>/dev/null || true)"
[[ "$OLD_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "OLD_SHA_UNKNOWN"
[[ -f "$OLD_CWD/ecosystem.config.js" ]] || fail "OLD_ECOSYSTEM_MISSING"

echo "PRE_WRITER_COUNT=1"
echo "PRE_DEPLOYED_SHA=$OLD_SHA"
PRE_STATE="$("$PY313" - "$CANONICAL_PRIMARY" <<'PY'
import sqlite3,sys
p=sys.argv[1]; c=sqlite3.connect(f'file:{p}?mode=ro',uri=True); r=c.execute("SELECT value FROM argos_runtime_state WHERE key='agent_status'").fetchone(); print((r[0] if r else 'ABSENT').upper()); c.close()
PY
)"
echo "PRE_AGENT_STATUS=$PRE_STATE"
PRE_OUTBOUND="$("$PY313" - "$CANONICAL_PRIMARY" <<'PY'
import sqlite3,sys
p=sys.argv[1]; c=sqlite3.connect(f'file:{p}?mode=ro',uri=True); print(c.execute("SELECT COUNT(*) FROM messages WHERE UPPER(direction)='OUTBOUND'").fetchone()[0]); c.close()
PY
)"
echo "PRE_OUTBOUND_TOTAL=$PRE_OUTBOUND"
[[ "$PRE_OUTBOUND" == "77" ]] || fail "OUTBOUND_BASELINE_NOT_77"
[[ "$PRE_STATE" == "PAUSED" ]] || fail "AGENT_NOT_PAUSED"

# Prepare immutable exact-SHA release before any production process mutation.
if [[ -e "$RELEASE" ]]; then
  [[ -d "$RELEASE/.git" ]] || fail "RELEASE_PATH_COLLISION"
  [[ "$(git -C "$RELEASE" rev-parse HEAD 2>/dev/null || true)" == "$SHA" ]] || fail "EXISTING_RELEASE_WRONG_SHA"
else
  mkdir -p "$RELEASE"
  git init -q "$RELEASE"
  git -C "$RELEASE" remote add origin https://github.com/lukeeterna/europeanautoscout.git
  git -C "$RELEASE" -c protocol.version=2 fetch --no-tags --depth=1 origin "$SHA"
  git -C "$RELEASE" checkout --detach --force FETCH_HEAD
fi
[[ "$(git -C "$RELEASE" rev-parse HEAD)" == "$SHA" ]] || fail "RELEASE_EXACT_SHA_MISMATCH"

# Copy existing local secrets without exposing them. Prefer the live release's
# private .env; fall back to the canonical historical runtime .env.
ENV_SRC=""
for candidate in "$OLD_CWD/.env" "$HOME_DIR/Documents/app-antigravity-auto/wa-intelligence/.env"; do
  if [[ -f "$candidate" ]]; then ENV_SRC="$candidate"; break; fi
done
[[ -n "$ENV_SRC" ]] || fail "ENV_SOURCE_MISSING"
cp -p "$ENV_SRC" "$RELEASE/wa-intelligence/.env"
chmod 600 "$RELEASE/wa-intelligence/.env"

# Reuse the currently proven browser executable if still present.
CHROME="$CHROME_FALLBACK"
[[ -x "$CHROME" ]] || fail "CHROME_EXECUTABLE_MISSING"

# Update only non-secret operational keys. All unrelated secret values remain
# from the local .env copy and are never printed.
"$PY313" - "$RELEASE/wa-intelligence/.env" "$CANONICAL_PRIMARY" "$CANONICAL_BRIDGE" "$SESSION_DIR" "$CLIENT_ID" "$CHROME" <<'PY'
from pathlib import Path
import os,sys
path=Path(sys.argv[1])
updates={
 'ARGOS_DB_PATH':sys.argv[2],
 'BRIDGE_DB_PATH':sys.argv[3],
 'ARGOS_WA_SESSION_DIR':sys.argv[4],
 'ARGOS_WA_CLIENT_ID':sys.argv[5],
 'CHROME_EXECUTABLE_PATH':sys.argv[6],
 'ARGOS_WA_TRANSPORT':'wwebjs',
 'ARGOS_AUTOMATION_ENABLED':'0',
 'ARGOS_PYTHON':'/usr/local/bin/python3.13',
}
lines=path.read_text(encoding='utf-8').splitlines()
out=[]; seen=set()
for line in lines:
    stripped=line.strip()
    if stripped and not stripped.startswith('#') and '=' in stripped:
        key=stripped.split('=',1)[0].strip()
        if key in updates:
            out.append(f'{key}={updates[key]}'); seen.add(key); continue
    out.append(line)
for key,val in updates.items():
    if key not in seen: out.append(f'{key}={val}')
path.write_text('\n'.join(out)+'\n',encoding='utf-8')
os.chmod(path,0o600)
PY

# Locked runtime, including the optional production wwebjs adapter.
npm ci --prefix "$RELEASE/wa-intelligence" --include=optional --no-audit --no-fund
npm --prefix "$RELEASE/wa-intelligence" run verify:runtime-deps
node - "$RELEASE/wa-intelligence" <<'NODE'
const path=require('path');
const root=process.argv[2];
const p=require(path.join(root,'node_modules/whatsapp-web.js/package.json'));
if(p.version!=='1.34.7') throw new Error(`WWEBJS_VERSION=${p.version}`);
require(path.join(root,'node_modules/whatsapp-web.js'));
console.log('WWEBJS_VERSION=1.34.7');
console.log('WWEBJS_LOAD=PASS');
NODE

# Back up both canonical databases before any PM2 mutation.
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="$HOME_DIR/Documents/argos-c10-backups/${STAMP}-${SHORT}"
mkdir -m 700 -p "$BACKUP_DIR"
"$PY313" - "$CANONICAL_PRIMARY" "$BACKUP_DIR/dealer_network.sqlite" "$CANONICAL_BRIDGE" "$BACKUP_DIR/bridge.sqlite" <<'PY'
import sqlite3,sys
for src,dst in ((sys.argv[1],sys.argv[2]),(sys.argv[3],sys.argv[4])):
    s=sqlite3.connect(f'file:{src}?mode=ro',uri=True); d=sqlite3.connect(dst)
    s.backup(d); d.close(); s.close()
    c=sqlite3.connect(f'file:{dst}?mode=ro',uri=True); q=c.execute('PRAGMA quick_check').fetchone()[0]; c.close()
    if q!='ok': raise SystemExit(f'backup quick_check={q}')
print('DB_BACKUP=PASS')
PY

# Full predeploy smoke must be GREEN before touching PM2.
"$PY313" "$RELEASE/tools/scripts/argos_c10_smoke.py" \
  --mode predeploy --repo-root "$RELEASE" --expected-head "$SHA" --pretty

echo "PREDEPLOY=GREEN"

rollback() {
  rc="$?"
  if [[ "$MUTATED" == "1" ]]; then
    echo "ROLLBACK=BEGIN" >&2
    "$PM2" stop argos-outreach-scheduler argos-wa-daemon >/dev/null 2>&1 || true
    "$PM2" delete argos-outreach-scheduler argos-wa-daemon >/dev/null 2>&1 || true
    if [[ -f "$OLD_CWD/ecosystem.config.js" ]]; then
      (cd "$OLD_CWD" && "$PM2" start ecosystem.config.js --only argos-wa-daemon,argos-outreach-scheduler --update-env) >/dev/null 2>&1 || true
    fi
    sleep 5
    rb_out="$("$PY313" - "$CANONICAL_PRIMARY" <<'PY'
import sqlite3,sys
c=sqlite3.connect(f'file:{sys.argv[1]}?mode=ro',uri=True); print(c.execute("SELECT COUNT(*) FROM messages WHERE UPPER(direction)='OUTBOUND'").fetchone()[0]); c.close()
PY
)"
    rb_state="$("$PY313" - "$CANONICAL_PRIMARY" <<'PY'
import sqlite3,sys
c=sqlite3.connect(f'file:{sys.argv[1]}?mode=ro',uri=True); r=c.execute("SELECT value FROM argos_runtime_state WHERE key='agent_status'").fetchone(); print((r[0] if r else 'ABSENT').upper()); c.close()
PY
)"
    echo "ROLLBACK_OUTBOUND_TOTAL=$rb_out" >&2
    echo "ROLLBACK_AGENT_STATUS=$rb_state" >&2
    if [[ "$rb_out" == "77" && "$rb_state" == "PAUSED" ]]; then echo "ROLLBACK=PASS" >&2; else echo "ROLLBACK=DEGRADED" >&2; fi
  fi
  exit "$rc"
}
trap rollback ERR

# Cut over only the canonical pair. The scheduler is stopped first; no unrelated
# PM2 process is restarted. Never call /resume.
MUTATED=1
"$PM2" stop argos-outreach-scheduler argos-wa-daemon >/dev/null
"$PM2" delete argos-outreach-scheduler argos-wa-daemon >/dev/null

# Do not force-kill LocalAuth browser children. Wait for clean shutdown; fail and
# rollback rather than risking profile corruption.
for _ in $(seq 1 20); do
  if ! ps -axo command= | grep -F "$SESSION_DIR" | grep -i '[c]hrome' >/dev/null; then break; fi
  sleep 1
done
if ps -axo command= | grep -F "$SESSION_DIR" | grep -i '[c]hrome' >/dev/null; then
  echo "LOCALAUTH_BROWSER_SHUTDOWN=TIMEOUT" >&2
  false
fi
echo "LOCALAUTH_BROWSER_SHUTDOWN=PASS"

(cd "$RELEASE/wa-intelligence" && "$PM2" start ecosystem.config.js --only argos-wa-daemon,argos-outreach-scheduler --update-env) >/dev/null

# Wait bounded for health and wwebjs ready. No outbound endpoint is called.
CONNECTED=0
for _ in $(seq 1 60); do
  health="$(curl --silent --max-time 2 http://127.0.0.1:9191/health || true)"
  if [[ -n "$health" ]]; then
    verdict="$("$PY313" - "$health" <<'PY'
import json,sys
try: h=json.loads(sys.argv[1])
except Exception: print('WAIT'); raise SystemExit
ok=(h.get('runtime')=='argos-s292-single-writer' and h.get('transport')=='wwebjs' and h.get('agent_status')=='PAUSED' and h.get('bridge_enabled') is True)
if ok and h.get('connected') is True: print('CONNECTED')
elif ok: print('READY_NOT_CONNECTED')
else: print('WAIT')
PY
)"
    if [[ "$verdict" == "CONNECTED" ]]; then CONNECTED=1; break; fi
  fi
  sleep 2
done
[[ "$CONNECTED" == "1" ]] || { echo "WWEBJS_CONNECTED=NO" >&2; false; }
echo "WWEBJS_CONNECTED=YES"

# Postdeploy smoke and independent process/DB assertions.
"$PY313" "$RELEASE/tools/scripts/argos_c10_smoke.py" \
  --mode postdeploy --repo-root "$RELEASE" --expected-head "$SHA" --require-connected --pretty

after_out="$("$PY313" - "$CANONICAL_PRIMARY" <<'PY'
import sqlite3,sys
c=sqlite3.connect(f'file:{sys.argv[1]}?mode=ro',uri=True); print(c.execute("SELECT COUNT(*) FROM messages WHERE UPPER(direction)='OUTBOUND'").fetchone()[0]); c.close()
PY
)"
after_state="$("$PY313" - "$CANONICAL_PRIMARY" <<'PY'
import sqlite3,sys
c=sqlite3.connect(f'file:{sys.argv[1]}?mode=ro',uri=True); r=c.execute("SELECT value FROM argos_runtime_state WHERE key='agent_status'").fetchone(); print((r[0] if r else 'ABSENT').upper()); c.close()
PY
)"
writer_count="$(ps -axo command= | awk '/[w]a-daemon\.js/ && /[n]ode/ {n++} END {print n+0}')"
listener_count="$(/usr/sbin/lsof -nP -iTCP:9191 -sTCP:LISTEN -t 2>/dev/null | sort -u | wc -l | tr -d ' ')"
[[ "$after_out" == "77" ]] || false
[[ "$after_state" == "PAUSED" ]] || false
[[ "$writer_count" == "1" ]] || false
[[ "$listener_count" == "1" ]] || false
[[ "$(git -C "$RELEASE" rev-parse HEAD)" == "$SHA" ]] || false

echo "POST_OUTBOUND_TOTAL=$after_out"
echo "POST_OUTBOUND_DELTA=$((after_out-PRE_OUTBOUND))"
echo "POST_AGENT_STATUS=$after_state"
echo "POST_SINGLE_WRITER=PASS"
echo "POST_PORT_9191_SINGLE_LISTENER=PASS"

"$PM2" save >/dev/null
MUTATED=0
trap - ERR

echo "PM2_SAVE=PASS"
echo "CUTOVER=GREEN"
echo "EXACT_SHA=$SHA"
echo "TRANSPORT=wwebjs"
echo "RUNTIME_STATUS=PAUSED"
echo "ARGOS_AUTOMATION_ENABLED=0"
echo "OUTBOUND_TOTAL=$after_out"
echo "OUTBOUND_DELTA=$((after_out-PRE_OUTBOUND))"
REMOTE

echo "CUTOVER=END"
