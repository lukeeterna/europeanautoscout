#!/usr/bin/env bash
set -euo pipefail

EXPECTED_SHA="${1:-${GITHUB_SHA:-}}"
if [[ ! "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo "BLOCKED: expected exact SHA is required" >&2
  exit 64
fi

IMAC_HOST="${ARGOS_IMAC_HOST:-iMac-di-gianluca.local}"
IMAC_USER="${ARGOS_IMAC_USER:-gianlucadistasi}"
TARGET="${IMAC_USER}@${IMAC_HOST}"
SSH_OPTS=(
  -o BatchMode=yes
  -o ConnectTimeout=10
  -o StrictHostKeyChecking=yes
  -o ServerAliveInterval=5
  -o ServerAliveCountMax=2
)

echo "C10_MACHINE_PROBE=BEGIN"
echo "EXPECTED_SHA=$EXPECTED_SHA"
echo "TRANSPORT_PATH=macbook_self_hosted_to_imac_ssh"
echo "PRODUCTION_MUTATION=NONE"
echo "OUTBOUND_ACTION=NONE"

ssh "${SSH_OPTS[@]}" "$TARGET" "python3 - '$EXPECTED_SHA'" <<'PY'
import datetime as dt
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import urllib.request

expected_sha = sys.argv[1]
os.environ["PATH"] = "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:" + os.environ.get("PATH", "")
home = Path.home()
primary_db = home / "Documents/app-antigravity-auto/dealer_network.sqlite"
bridge_db = home / "Documents/app-antigravity-auto/comm-broker/bridge.sqlite"
session_root = home / "Documents/app-antigravity-auto/wa-sender"
legacy_auth = home / "Documents/app-antigravity-auto/wa-intelligence/.wwebjs_auth"


def run(args, timeout=15):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def one_line(value):
    return str(value if value is not None else "").replace("\n", " ").replace("\r", " ")


def ro_connect(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)


def db_scalar(path, sql):
    if not path.is_file():
        return None
    con = ro_connect(path)
    try:
        row = con.execute(sql).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def db_table_columns(path, table):
    if not path.is_file():
        return set()
    con = ro_connect(path)
    try:
        return {str(row[1]) for row in con.execute(f"PRAGMA table_info('{table}')").fetchall()}
    finally:
        con.close()


def git_head_from(app):
    env = app.get("pm2_env") or {}
    candidates = []
    for raw in (env.get("pm_cwd"), env.get("pm_exec_path")):
        if not raw:
            continue
        p = Path(str(raw)).expanduser()
        candidates.extend([p, p.parent, p.parent.parent])
    seen = set()
    for p in candidates:
        try:
            p = p.resolve()
        except Exception:
            continue
        if str(p) in seen:
            continue
        seen.add(str(p))
        r = run(["git", "-C", str(p), "rev-parse", "HEAD"])
        if r.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", r.stdout.strip()):
            return r.stdout.strip(), str(p)
    return "UNKNOWN", "UNKNOWN"

pm2_cmd = run(["pm2", "jlist"])
if pm2_cmd.returncode != 0:
    print("PM2_JLIST=FAIL")
    print("C10_MACHINE=RED")
    print("BLOCKERS=PM2_JLIST_UNAVAILABLE")
    raise SystemExit(20)

try:
    apps = json.loads(pm2_cmd.stdout)
except json.JSONDecodeError:
    print("PM2_JLIST=UNPARSEABLE")
    print("C10_MACHINE=RED")
    print("BLOCKERS=PM2_JLIST_UNPARSEABLE")
    raise SystemExit(20)

writers = [a for a in apps if a.get("name") == "argos-wa-daemon" and (a.get("pm2_env") or {}).get("status") == "online"]
schedulers = [a for a in apps if a.get("name") == "argos-outreach-scheduler"]
print("PM2_JLIST=PASS")
print(f"WRITER_ONLINE_COUNT={len(writers)}")

writer = writers[0] if len(writers) == 1 else None
writer_env = (writer or {}).get("pm2_env") or {}
writer_pid = (writer or {}).get("pid")
writer_cwd = writer_env.get("pm_cwd") or "UNKNOWN"
writer_script = writer_env.get("pm_exec_path") or "UNKNOWN"
transport = str(writer_env.get("ARGOS_WA_TRANSPORT") or "UNKNOWN").lower()
automation = str(writer_env.get("ARGOS_AUTOMATION_ENABLED") or "UNKNOWN")

print(f"WRITER_PID={one_line(writer_pid)}")
print(f"WRITER_CWD={one_line(writer_cwd)}")
print(f"WRITER_SCRIPT={one_line(writer_script)}")
print(f"WRITER_TRANSPORT={one_line(transport)}")
print(f"WRITER_AUTOMATION_ENABLED={one_line(automation)}")

deployed_sha, deployed_root = git_head_from(writer) if writer else ("UNKNOWN", "UNKNOWN")
print(f"DEPLOYED_SHA={deployed_sha}")
print(f"DEPLOYED_GIT_ROOT={deployed_root}")

if schedulers:
    scheduler = schedulers[0]
    se = scheduler.get("pm2_env") or {}
    print(f"SCHEDULER_STATUS={one_line(se.get('status') or 'UNKNOWN')}")
    print(f"SCHEDULER_CWD={one_line(se.get('pm_cwd') or 'UNKNOWN')}")
else:
    print("SCHEDULER_STATUS=ABSENT")
    print("SCHEDULER_CWD=ABSENT")

listeners = run(["lsof", "-nP", "-iTCP:9191", "-sTCP:LISTEN", "-t"])
listener_pids = sorted({line.strip() for line in listeners.stdout.splitlines() if line.strip()})
print(f"PORT_9191_LISTENER_COUNT={len(listener_pids)}")
print("PORT_9191_PIDS=" + (",".join(listener_pids) if listener_pids else "NONE"))

health = {}
try:
    with urllib.request.urlopen("http://127.0.0.1:9191/health", timeout=3) as response:
        health = json.loads(response.read().decode("utf-8"))
    print("HEALTH_HTTP=200")
except Exception as exc:
    print(f"HEALTH_HTTP=UNAVAILABLE:{type(exc).__name__}")

for key in ("runtime", "transport", "connected", "agent_status", "bridge_enabled", "pending_bridge", "global_outbound_24h"):
    print(f"HEALTH_{key.upper()}={one_line(health.get(key, 'UNKNOWN'))}")

agent_status = db_scalar(primary_db, "SELECT value FROM argos_runtime_state WHERE key='agent_status' LIMIT 1")
outbound_total = db_scalar(primary_db, "SELECT COUNT(*) FROM messages WHERE UPPER(direction)='OUTBOUND'")
primary_integrity = db_scalar(primary_db, "PRAGMA quick_check")
print(f"PRIMARY_DB_PRESENT={str(primary_db.is_file()).upper()}")
print(f"PRIMARY_DB_QUICK_CHECK={one_line(primary_integrity or 'UNKNOWN')}")
print(f"DB_AGENT_STATUS={one_line(agent_status or 'UNKNOWN')}")
print(f"OUTBOUND_TOTAL={one_line(outbound_total if outbound_total is not None else 'UNKNOWN')}")

bridge_integrity = db_scalar(bridge_db, "PRAGMA quick_check")
bridge_cols = db_table_columns(bridge_db, "bridge_outbound")
pending_bridge = None
if {"approved_ts", "sent_ts"}.issubset(bridge_cols):
    condition = "approved_ts IS NOT NULL AND sent_ts IS NULL"
    if "template_id" in bridge_cols:
        condition += " AND template_id IS NOT NULL"
    pending_bridge = db_scalar(bridge_db, f"SELECT COUNT(*) FROM bridge_outbound WHERE {condition}")
print(f"BRIDGE_DB_PRESENT={str(bridge_db.is_file()).upper()}")
print(f"BRIDGE_DB_QUICK_CHECK={one_line(bridge_integrity or 'UNKNOWN')}")
print(f"BRIDGE_PENDING_APPROVED={one_line(pending_bridge if pending_bridge is not None else 'UNKNOWN')}")


def describe_auth_root(label, root):
    print(f"{label}_PRESENT={str(root.is_dir()).upper()}")
    if not root.is_dir():
        return
    dirs = sorted(p.name for p in root.iterdir() if p.is_dir())
    file_count = 0
    latest = 0.0
    locklike = 0
    for p in root.rglob("*"):
        try:
            if p.is_file():
                file_count += 1
                latest = max(latest, p.stat().st_mtime)
                if any(x in p.name.lower() for x in ("lock", "singleton")):
                    locklike += 1
        except OSError:
            pass
    latest_iso = dt.datetime.fromtimestamp(latest, dt.timezone.utc).isoformat() if latest else "NONE"
    print(f"{label}_PROFILES=" + (",".join(dirs) if dirs else "NONE"))
    print(f"{label}_FILE_COUNT={file_count}")
    print(f"{label}_LATEST_MTIME_UTC={latest_iso}")
    print(f"{label}_LOCKLIKE_COUNT={locklike}")


describe_auth_root("WA_SENDER_AUTH", session_root)
describe_auth_root("LEGACY_WWEBJS_AUTH", legacy_auth)

if writer:
    safe_keywords = ("consent_schema", "initial_agent_status", "transport=", "qr", "connected", "disconnected", "auth_failure", "ready")
    print("RECENT_DAEMON_SAFE_EVENTS_BEGIN")
    for log_key in ("pm_out_log_path", "pm_err_log_path"):
        raw_path = writer_env.get(log_key)
        if not raw_path:
            continue
        path = Path(str(raw_path))
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-800:]
        except OSError:
            continue
        for line in lines:
            lower = line.lower()
            if not ("23/08/2026" in line or "2026-08-23" in line):
                continue
            if not any(k in lower for k in safe_keywords):
                continue
            line = re.sub(r"\b\d{7,}\b", "[NUMBER]", line)
            line = re.sub(r"\b[A-Za-z0-9_-]{32,}\b", "[REDACTED]", line)
            print(line[:500])
    print("RECENT_DAEMON_SAFE_EVENTS_END")

blockers = []
if len(writers) != 1:
    blockers.append("SINGLE_WRITER")
if len(listener_pids) != 1:
    blockers.append("PORT_9191_SINGLE_LISTENER")
if str(agent_status or "").upper() != "PAUSED":
    blockers.append("AGENT_NOT_PAUSED")
if automation != "0":
    blockers.append("AUTOMATION_NOT_DISABLED")
if transport != "wwebjs":
    blockers.append("TRANSPORT_NOT_WWEBJS")
if outbound_total != 77:
    blockers.append("OUTBOUND_BASELINE_CHANGED")
if health.get("bridge_enabled") is not True:
    blockers.append("BRIDGE_NOT_ENABLED")
if health.get("connected") is not True:
    blockers.append("WWEBJS_NOT_CONNECTED")
if deployed_sha != expected_sha:
    blockers.append("EXACT_SHA_NOT_DEPLOYED")
if primary_integrity != "ok":
    blockers.append("PRIMARY_DB_INTEGRITY")
if bridge_integrity != "ok":
    blockers.append("BRIDGE_DB_INTEGRITY")

if blockers:
    print("C10_MACHINE=RED")
    print("BLOCKERS=" + ",".join(blockers))
    raise SystemExit(20)

print("C10_MACHINE=GREEN")
print("BLOCKERS=NONE")
PY
rc=$?

echo "C10_MACHINE_PROBE=END"
exit "$rc"
