#!/usr/bin/env python3
"""ARGOS C10 production smoke gate — read-only, transport-aware, no outreach.

Runs on the production release tree before/after PM2 startup. It never changes
Git, SQLite, PM2, WhatsApp or Meta state. Both supported transports are checked:

* ``wwebjs`` requires the exact persisted LocalAuth ``session-<client_id>``.
* ``cloud`` requires the official Meta Cloud API configuration plus a public
  HTTPS webhook URL and the exact approved proactive template names. Predeploy
  performs no Graph API request. On the final ``--require-connected`` postdeploy
  gate, the script also performs a harmless GET webhook verification challenge
  against that public URL so inbound routing is proven end-to-end without
  sending any WhatsApp message.

In every mode C10 remains fail-closed: automation disabled, runtime not ACTIVE,
no authorized dealer/pending approved bridge row unless explicitly overridden.
Production release trees must point explicitly to the existing external SQLite
state via ``ARGOS_DB_PATH`` and ``BRIDGE_DB_PATH``.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional


CLOUD_REQUIRED_ENV = (
    "META_WA_ACCESS_TOKEN",
    "META_WA_PHONE_NUMBER_ID",
    "META_WA_WABA_ID",
    "META_WA_WEBHOOK_VERIFY_TOKEN",
    "META_APP_SECRET",
    "ARGOS_WA_WEBHOOK_PUBLIC_URL",
    "META_WA_TEMPLATE_DAY1_NAME",
    "META_WA_TEMPLATE_DAY7_NAME",
    "META_WA_TEMPLATE_DAY12_NAME",
)
SUPPORTED_TRANSPORTS = {"wwebjs", "cloud"}


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


def _public_webhook_verify(public_url: str, verify_token: str) -> tuple[bool, str]:
    """Verify the deployed HTTPS route using the same side-effect-free GET Meta uses."""
    try:
        parsed = urllib.parse.urlsplit(public_url)
        if parsed.scheme != "https" or not parsed.netloc:
            return False, "public webhook URL must be absolute HTTPS"
        query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        challenge = "argos-c10-webhook-ok"
        query.extend(
            [
                ("hub.mode", "subscribe"),
                ("hub.verify_token", verify_token),
                ("hub.challenge", challenge),
            ]
        )
        target = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
        )
        request = urllib.request.Request(target, method="GET")
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read(1024).decode("utf-8")
            status = int(response.status)
        return status == 200 and body == challenge, f"HTTP {status}, challenge_match={body == challenge}"
    except (OSError, urllib.error.URLError, ValueError) as exc:
        return False, f"webhook verification failed: {type(exc).__name__}"


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


def _profile_nonempty(session_dir: Path, client_id: str) -> tuple[bool, bool]:
    profile = session_dir / f"session-{client_id}" if client_id else None
    profile_ok = bool(profile and profile.is_dir())
    if not profile_ok:
        return False, False
    try:
        return True, any(p.is_file() for p in profile.rglob("*"))
    except OSError:
        return True, False


def _transport_checks(report: SmokeReport, env: Mapping[str, str], root: Path) -> tuple[str, Path]:
    transport = str(env.get("ARGOS_WA_TRANSPORT") or "wwebjs").strip().lower()
    report.add("transport_supported", transport in SUPPORTED_TRANSPORTS, transport)

    session_raw = str(env.get("ARGOS_WA_SESSION_DIR") or "").strip()
    session_dir = Path(os.path.expanduser(session_raw)).resolve() if session_raw else (root / "wa-sender")

    if transport == "cloud":
        missing = [name for name in CLOUD_REQUIRED_ENV if not str(env.get(name) or "").strip()]
        report.add("cloud_required_env", not missing, missing or "configured")
        graph_version = str(env.get("META_GRAPH_API_VERSION") or "v25.0").strip()
        report.add("cloud_graph_version", bool(graph_version), graph_version)
        template_language = str(env.get("META_WA_TEMPLATE_LANGUAGE") or "it").strip()
        report.add("cloud_template_language", bool(template_language), template_language)
        public_url = str(env.get("ARGOS_WA_WEBHOOK_PUBLIC_URL") or "").strip()
        parsed = urllib.parse.urlsplit(public_url) if public_url else None
        report.add(
            "cloud_public_webhook_https",
            bool(parsed and parsed.scheme == "https" and parsed.netloc),
            "configured" if public_url else "missing",
        )
        report.add(
            "existing_wa_session",
            True,
            "not required for official Cloud API transport",
            required=False,
        )
    elif transport == "wwebjs":
        client_id = str(env.get("ARGOS_WA_CLIENT_ID") or "").strip()
        root_ok = session_dir.is_dir()
        profile_ok, files_ok = _profile_nonempty(session_dir, client_id)
        report.add("wwebjs_client_id_configured", bool(client_id), "configured" if client_id else "missing")
        report.add(
            "existing_wa_session",
            bool(root_ok and profile_ok and files_ok),
            {
                "session_root_present": root_ok,
                "profile_directory_present": profile_ok,
                "profile_files_positive": files_ok,
            },
        )
    else:
        report.add("existing_wa_session", False, f"unsupported transport: {transport}")

    return transport, session_dir


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
        intel / "whatsapp_consent.py",
        intel / "meta_templates.json",
        intel / "ecosystem.config.js",
        intel / "package.json",
        intel / "package-lock.json",
        intel / "transport" / "index.js",
        intel / "transport" / "errors.js",
        intel / "transport" / "cloud_api_transport.js",
        intel / "transport" / "cloud_policy_transport.js",
        intel / "transport" / "wwebjs_transport.js",
        intel / "transport" / "webhook.js",
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
            report.add(
                "expected_head",
                actual_head == expected_head,
                {"expected": expected_head, "actual": actual_head},
            )
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
        node_files = (
            "wa-intelligence/wa-daemon.js",
            "wa-intelligence/ecosystem.config.js",
            "wa-intelligence/transport/index.js",
            "wa-intelligence/transport/errors.js",
            "wa-intelligence/transport/cloud_api_transport.js",
            "wa-intelligence/transport/cloud_policy_transport.js",
            "wa-intelligence/transport/wwebjs_transport.js",
            "wa-intelligence/transport/webhook.js",
        )
        for rel in node_files:
            result = _run([node, "--check", rel], cwd=root)
            report.add(f"node_check:{rel}", result.returncode == 0, result.stderr.strip() or "PASS")
        runtime_deps = _run(
            [
                node,
                "-e",
                "const Database=require('better-sqlite3'); const db=new Database(':memory:'); db.prepare('SELECT 1').get(); db.close(); require('qrcode');",
            ],
            cwd=intel,
        )
        report.add(
            "node_runtime_dependencies",
            runtime_deps.returncode == 0,
            runtime_deps.stderr.strip() or "better-sqlite3+qrcode PASS",
        )

    report.add("env_file_present", env_file.is_file(), str(env_file))
    if env_file.is_file():
        try:
            mode = env_file.stat().st_mode & 0o777
            report.add("env_file_private", mode & 0o077 == 0, oct(mode))
        except OSError as exc:
            report.add("env_file_private", False, type(exc).__name__)
    api_key = str(env.get("ARGOS_API_KEY") or env.get("WA_API_KEY") or "")
    report.add("api_key_configured", bool(api_key.strip()), "configured" if api_key.strip() else "missing")
    automation = str(env.get("ARGOS_AUTOMATION_ENABLED") or "0").strip()
    report.add("automation_disabled", automation != "1", f"ARGOS_AUTOMATION_ENABLED={automation}")

    transport, session_dir = _transport_checks(report, env, root)

    primary_raw = str(env.get("ARGOS_DB_PATH") or "").strip()
    primary_db = Path(os.path.expanduser(primary_raw)).resolve() if primary_raw else (root / "dealer_network.sqlite")
    report.add("primary_path_configured", bool(primary_raw), primary_raw or "missing")
    report.add("primary_db_present", primary_db.is_file(), str(primary_db))

    bridge_raw = str(env.get("BRIDGE_DB_PATH") or "").strip()
    bridge_db = Path(os.path.expanduser(bridge_raw)).resolve() if bridge_raw else None
    report.add("bridge_path_configured", bool(bridge_raw), bridge_raw or "missing")
    report.add("bridge_db_present", bool(bridge_db and bridge_db.is_file()), str(bridge_db) if bridge_db else "missing")

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
                report.add(
                    "runtime_not_active_predeploy",
                    str(state or "PAUSED").upper() != "ACTIVE",
                    state or "absent",
                )
            else:
                report.add(
                    "runtime_not_active_predeploy",
                    True,
                    "state row absent -> entrypoint will seed PAUSED",
                )
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
        "transport": transport,
        "webhook_public_url": str(env.get("ARGOS_WA_WEBHOOK_PUBLIC_URL") or "").strip(),
        "webhook_verify_token": str(env.get("META_WA_WEBHOOK_VERIFY_TOKEN") or "").strip(),
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
        report.add("health_transport", health.get("transport") == context["transport"], health.get("transport"))
        if require_connected:
            report.add("whatsapp_connected", health.get("connected") is True, health.get("connected"))
        else:
            report.add("whatsapp_connected", True, health.get("connected"), required=False)

    if context["transport"] == "cloud" and require_connected:
        webhook_ok, webhook_detail = _public_webhook_verify(
            context["webhook_public_url"], context["webhook_verify_token"]
        )
        report.add("cloud_public_webhook_verified", webhook_ok, webhook_detail)
    else:
        report.add(
            "cloud_public_webhook_verified",
            True,
            "not required for this transport/gate",
            required=False,
        )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARGOS C10 read-only transport-aware no-outreach smoke gate")
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
