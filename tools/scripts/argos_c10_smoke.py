#!/usr/bin/env python3
"""ARGOS C10 production smoke gate — read-only, no outreach.

This command is designed to run ON the iMac release tree immediately before
and after PM2 startup. It never changes Git, SQLite, PM2 or WhatsApp state.

PREDEPLOY proves that starting the reviewed runtime cannot accidentally contact
real dealers:
- expected Git HEAD and clean worktree;
- Python 3.13, Node and PM2 available;
- production JS syntax valid;
- primary DB, bridge DB and existing WhatsApp LocalAuth directory present;
- ARGOS_API_KEY configured;
- ARGOS_AUTOMATION_ENABLED != 1;
- no already-authorized dealer and no approved/pending bridge row unless an
  explicit command-line override is supplied;
- persisted runtime state, if present, is not ACTIVE.

POSTDEPLOY additionally reads local ``/health`` and PM2 metadata. The daemon
must be the S292 single-writer and must remain PAUSED. Use ``--require-connected``
only after QR/session authentication is expected to be complete.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional


@dataclass
class SmokeReport:
    mode: str
    ok: bool = True
    checks: list[dict[str, Any]] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: Any = None, *, required: bool = True) -> None:
        self.checks.append(
            {"name": name, "ok": bool(ok), "required": bool(required), "detail": detail}
        )
        if required and not ok:
            self.ok = False

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "mode": self.mode, "checks": self.checks}


def _load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _run(args: list[str], *, cwd: Path, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def _sqlite_columns(path: Path, table: str) -> set[str]:
    uri = f"file:{path}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        return {str(row[1]) for row in con.execute(f"PRAGMA table_info('{table}')").fetchall()}
    finally:
        con.close()


def _sqlite_scalar(path: Path, sql: str, params: tuple[Any, ...] = ()) -> Any:
    uri = f"file:{path}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        row = con.execute(sql, params).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def _http_health(port: int) -> tuple[Optional[Mapping[str, Any]], str]:
    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload if isinstance(payload, Mapping) else None, ""
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
        return None, str(exc)


def _pm2_apps(repo_root: Path) -> tuple[dict[str, Mapping[str, Any]], str]:
    pm2 = shutil.which("pm2")
    if not pm2:
        return {}, "pm2 not found"
    result = _run([pm2, "jlist"], cwd=repo_root)
    if result.returncode != 0:
        return {}, result.stderr.strip() or result.stdout.strip()
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {}, f"invalid pm2 jlist JSON: {exc}"
    apps: dict[str, Mapping[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, Mapping) and row.get("name"):
            apps[str(row["name"])] = row
    return apps, ""


def predeploy_checks(
    *,
    repo_root: Path,
    expected_head: Optional[str],
    allow_authorized_dealers: bool,
    allow_pending_bridge: bool,
) -> tuple[SmokeReport, dict[str, Any]]:
    report = SmokeReport("predeploy")
    root = repo_root.resolve()
    intel = root / "wa-intelligence"
    env_file = intel / ".env"
    env = _load_env(env_file)

    required_files = [
        intel / "wa-daemon.js",
        intel / "runtime_entrypoint.py",
        intel / "outreach_scheduler.py",
        intel / "ecosystem.config.js",
        root / "tools" / "scripts" / "argos_dealer_delivery.py",
    ]
    missing = [str(path.relative_to(root)) for path in required_files if not path.is_file()]
    report.add("required_runtime_files", not missing, missing or "present")

    git = shutil.which("git")
    report.add("git_available", bool(git), git or "not found")
    actual_head = None
    if git:
        head = _run([git, "rev-parse", "HEAD"], cwd=root)
        actual_head = head.stdout.strip() if head.returncode == 0 else None
        report.add("git_head_readable", bool(actual_head), actual_head or head.stderr.strip())
        if expected_head:
            report.add("expected_head", actual_head == expected_head, {"expected": expected_head, "actual": actual_head})
        status = _run([git, "status", "--porcelain=v1"], cwd=root)
        dirty = [line for line in status.stdout.splitlines() if line.strip()]
        report.add("worktree_clean", status.returncode == 0 and not dirty, dirty[:20] or "clean")

    python_path = Path("/usr/local/bin/python3.13")
    report.add("python_3_13", python_path.is_file(), str(python_path))
    if python_path.is_file():
        py = _run([str(python_path), "--version"], cwd=root)
        report.add("python_version_exec", py.returncode == 0, (py.stdout or py.stderr).strip())

    node = shutil.which("node")
    pm2 = shutil.which("pm2")
    report.add("node_available", bool(node), node or "not found")
    report.add("pm2_available", bool(pm2), pm2 or "not found")
    if node:
        for rel in ("wa-intelligence/wa-daemon.js", "wa-intelligence/ecosystem.config.js"):
            result = _run([node, "--check", rel], cwd=root)
            report.add(f"node_check:{rel}", result.returncode == 0, result.stderr.strip() or "PASS")

    report.add("env_file_present", env_file.is_file(), str(env_file))
    api_key = env.get("ARGOS_API_KEY") or env.get("WA_API_KEY") or ""
    report.add("api_key_configured", bool(api_key.strip()), "configured" if api_key.strip() else "missing")
    automation = (env.get("ARGOS_AUTOMATION_ENABLED") or "0").strip()
    report.add("automation_disabled", automation != "1", f"ARGOS_AUTOMATION_ENABLED={automation}")

    primary_db = root / "dealer_network.sqlite"
    report.add("primary_db_present", primary_db.is_file(), str(primary_db))

    bridge_raw = (env.get("BRIDGE_DB_PATH") or "").strip()
    bridge_db = Path(os.path.expanduser(bridge_raw)).resolve() if bridge_raw else None
    report.add("bridge_path_configured", bool(bridge_raw), bridge_raw or "missing")
    report.add("bridge_db_present", bool(bridge_db and bridge_db.is_file()), str(bridge_db) if bridge_db else "missing")

    session_raw = (env.get("ARGOS_WA_SESSION_DIR") or "").strip()
    session_dir = Path(os.path.expanduser(session_raw)).resolve() if session_raw else (root / "wa-sender")
    session_nonempty = session_dir.is_dir() and any(session_dir.iterdir())
    report.add("existing_wa_session", session_nonempty, str(session_dir))

    if primary_db.is_file():
        try:
            conv_cols = _sqlite_columns(primary_db, "conversations")
            report.add("conversations_table", bool(conv_cols), sorted(conv_cols)[:30])
            if "outreach_authorized" in conv_cols:
                authorized_count = int(
                    _sqlite_scalar(
                        primary_db,
                        "SELECT COUNT(*) FROM conversations WHERE COALESCE(outreach_authorized,0)=1",
                    )
                    or 0
                )
                report.add(
                    "no_authorized_dealers_during_c10",
                    authorized_count == 0 or allow_authorized_dealers,
                    authorized_count,
                )
            state_cols = _sqlite_columns(primary_db, "argos_runtime_state")
            if state_cols:
                state = _sqlite_scalar(
                    primary_db,
                    "SELECT value FROM argos_runtime_state WHERE key='agent_status' LIMIT 1",
                )
                report.add("runtime_not_active_predeploy", str(state or "PAUSED").upper() != "ACTIVE", state or "absent")
            else:
                report.add("runtime_not_active_predeploy", True, "state row absent -> entrypoint will seed PAUSED")
        except sqlite3.Error as exc:
            report.add("primary_db_readable", False, str(exc))

    if bridge_db and bridge_db.is_file():
        try:
            cols = _sqlite_columns(bridge_db, "bridge_outbound")
            report.add("bridge_outbound_table", bool(cols), sorted(cols)[:30])
            required = {"approved_ts", "sent_ts"}
            if required.issubset(cols):
                condition = "approved_ts IS NOT NULL AND sent_ts IS NULL"
                if "template_id" in cols:
                    condition += " AND template_id IS NOT NULL"
                pending = int(_sqlite_scalar(bridge_db, f"SELECT COUNT(*) FROM bridge_outbound WHERE {condition}") or 0)
                report.add("no_pending_approved_bridge", pending == 0 or allow_pending_bridge, pending)
        except sqlite3.Error as exc:
            report.add("bridge_db_readable", False, str(exc))

    context = {
        "repo_root": str(root),
        "actual_head": actual_head,
        "primary_db": str(primary_db),
        "bridge_db": str(bridge_db) if bridge_db else None,
        "session_dir": str(session_dir),
        "env_file": str(env_file),
        "port": int(env.get("ARGOS_WA_PORT") or 9191),
    }
    return report, context


def postdeploy_checks(
    *,
    repo_root: Path,
    expected_head: Optional[str],
    require_connected: bool,
    allow_authorized_dealers: bool,
    allow_pending_bridge: bool,
) -> SmokeReport:
    pre, context = predeploy_checks(
        repo_root=repo_root,
        expected_head=expected_head,
        allow_authorized_dealers=allow_authorized_dealers,
        allow_pending_bridge=allow_pending_bridge,
    )
    report = SmokeReport("postdeploy", ok=pre.ok, checks=list(pre.checks))

    apps, pm2_error = _pm2_apps(repo_root.resolve())
    report.add("pm2_jlist", not pm2_error, pm2_error or sorted(apps))
    for name in ("argos-wa-daemon", "argos-outreach-scheduler"):
        app = apps.get(name)
        status = str(((app or {}).get("pm2_env") or {}).get("status") or "missing")
        report.add(f"pm2_online:{name}", status == "online", status)

    health, error = _http_health(int(context["port"]))
    report.add("local_health_reachable", health is not None, error or health)
    if health is not None:
        report.add("health_runtime", health.get("runtime") == "argos-s292-single-writer", health.get("runtime"))
        report.add("health_agent_paused", health.get("agent_status") == "PAUSED", health.get("agent_status"))
        report.add("health_bridge_enabled", health.get("bridge_enabled") is True, health.get("bridge_enabled"))
        if require_connected:
            report.add("whatsapp_connected", health.get("connected") is True, health.get("connected"))
        else:
            report.add("whatsapp_connected", True, health.get("connected"), required=False)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARGOS C10 read-only no-outreach smoke gate")
    parser.add_argument("--mode", choices=("predeploy", "postdeploy"), required=True)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--expected-head")
    parser.add_argument("--require-connected", action="store_true")
    parser.add_argument("--allow-authorized-dealers", action="store_true")
    parser.add_argument("--allow-pending-bridge", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.repo_root)
    if args.mode == "predeploy":
        report, _ = predeploy_checks(
            repo_root=root,
            expected_head=args.expected_head,
            allow_authorized_dealers=args.allow_authorized_dealers,
            allow_pending_bridge=args.allow_pending_bridge,
        )
    else:
        report = postdeploy_checks(
            repo_root=root,
            expected_head=args.expected_head,
            require_connected=args.require_connected,
            allow_authorized_dealers=args.allow_authorized_dealers,
            allow_pending_bridge=args.allow_pending_bridge,
        )
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
