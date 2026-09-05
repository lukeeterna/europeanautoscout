#!/usr/bin/env python3
"""Read-only ARGOS post-C11 production readiness gate.

This gate is intended to run after the single controlled C11 pilot and, when a
pre-reboot boot epoch is supplied, after a real host reboot.  It never resumes
outreach, sends a message, edits the production databases, or modifies the
LocalAuth session.  The restore drill uses temporary SQLite backups only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import tempfile
import urllib.request

EXPECTED_RUNTIME = "argos-s292-single-writer"


def _check(checks, name, ok, detail=None):
    item = {"name": name, "ok": bool(ok)}
    if detail is not None:
        item["detail"] = detail
    checks.append(item)


def _read_env(path):
    values = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _git_head(repo_root):
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _git_tracked_clean(repo_root):
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=no"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    return proc.returncode == 0 and not proc.stdout.strip()


def _ro_connect(path):
    return sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=5)


def _scalar(path, sql, args=()):
    con = _ro_connect(path)
    try:
        row = con.execute(sql, args).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def _columns(path, table):
    con = _ro_connect(path)
    try:
        return {str(row[1]) for row in con.execute("PRAGMA table_info('%s')" % table)}
    finally:
        con.close()


def _sqlite_restore_drill(path, scalar_queries):
    """Back up a live DB into a temporary DB and verify equivalent safe scalars."""
    with tempfile.TemporaryDirectory(prefix="argos-restore-drill-") as td:
        target = Path(td) / "restored.sqlite"
        src = _ro_connect(path)
        dst = sqlite3.connect(str(target), timeout=5)
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
            src.close()

        restored = sqlite3.connect(str(target), timeout=5)
        original = _ro_connect(path)
        try:
            if restored.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                return False
            for sql, args in scalar_queries:
                a = original.execute(sql, args).fetchone()
                b = restored.execute(sql, args).fetchone()
                if a != b:
                    return False
        finally:
            original.close()
            restored.close()
    return True


def _current_boot_epoch():
    # macOS first; Linux fallback keeps offline/unit use portable.
    try:
        proc = subprocess.run(
            ["sysctl", "-n", "kern.boottime"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0:
            match = re.search(r"sec\s*=\s*(\d+)", proc.stdout)
            if match:
                return int(match.group(1))
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines():
            if line.startswith("btime "):
                return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return None


def _fetch_health(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def run_gate(
    repo_root,
    db_path,
    bridge_db_path,
    env_path,
    expected_head,
    expected_outbound_total=78,
    health_payload=None,
    pre_reboot_boot_epoch=None,
    current_boot_epoch=None,
):
    repo_root = Path(repo_root)
    db_path = Path(db_path)
    bridge_db_path = Path(bridge_db_path)
    env_path = Path(env_path)
    checks = []

    _check(checks, "repo_present", (repo_root / ".git").exists())
    head = _git_head(repo_root) if (repo_root / ".git").exists() else ""
    _check(checks, "expected_head", head == expected_head, {"match": head == expected_head})
    _check(checks, "tracked_worktree_clean", _git_tracked_clean(repo_root) if head else False)

    env = {}
    env_private = False
    if env_path.is_file():
        env = _read_env(env_path)
        mode = stat.S_IMODE(env_path.stat().st_mode)
        env_private = (mode & 0o077) == 0
    _check(checks, "env_present", env_path.is_file())
    _check(checks, "env_private", env_private)
    _check(checks, "automation_disabled", str(env.get("ARGOS_AUTOMATION_ENABLED", "")).strip() == "0")
    _check(checks, "transport_wwebjs", str(env.get("ARGOS_WA_TRANSPORT", "")).strip().lower() == "wwebjs")
    bind_host = str(env.get("ARGOS_BIND_HOST", "127.0.0.1")).strip().lower()
    _check(checks, "loopback_bind", bind_host in {"127.0.0.1", "localhost", "::1"})

    session_raw = str(env.get("ARGOS_WA_SESSION_DIR", "")).strip()
    session_path = Path(session_raw).expanduser() if session_raw else None
    session_ok = bool(session_path and session_path.is_dir())
    session_files = 0
    if session_ok:
        try:
            session_files = sum(1 for p in session_path.rglob("*") if p.is_file())
        except OSError:
            session_files = 0
    _check(checks, "localauth_session_present", session_ok and session_files > 0, {"file_count_positive": session_files > 0})

    primary_ok = db_path.is_file()
    bridge_ok = bridge_db_path.is_file()
    _check(checks, "primary_db_present", primary_ok)
    _check(checks, "bridge_db_present", bridge_ok)

    outbound_total = None
    authorized = None
    primary_quick = None
    if primary_ok:
        try:
            primary_quick = _scalar(db_path, "PRAGMA quick_check")
            outbound_total = int(_scalar(db_path, "SELECT COUNT(*) FROM messages WHERE UPPER(direction)='OUTBOUND'") or 0)
            authorized = int(_scalar(db_path, "SELECT COUNT(*) FROM conversations WHERE COALESCE(outreach_authorized,0)=1") or 0)
        except (sqlite3.Error, TypeError, ValueError):
            pass
    _check(checks, "primary_db_quick_check", primary_quick == "ok")
    _check(
        checks,
        "postpilot_outbound_total",
        outbound_total == int(expected_outbound_total),
        {"expected": int(expected_outbound_total), "actual": outbound_total},
    )
    _check(checks, "authorized_recipients_zero", authorized == 0, {"actual": authorized})

    bridge_quick = None
    bridge_pending = None
    bridge_cols = set()
    if bridge_ok:
        try:
            bridge_quick = _scalar(bridge_db_path, "PRAGMA quick_check")
            bridge_cols = _columns(bridge_db_path, "bridge_outbound")
            if {"approved_ts", "sent_ts"}.issubset(bridge_cols):
                condition = "approved_ts IS NOT NULL AND sent_ts IS NULL"
                if "template_id" in bridge_cols:
                    condition += " AND template_id IS NOT NULL"
                bridge_pending = int(_scalar(bridge_db_path, "SELECT COUNT(*) FROM bridge_outbound WHERE %s" % condition) or 0)
        except (sqlite3.Error, TypeError, ValueError):
            pass
    _check(checks, "bridge_db_quick_check", bridge_quick == "ok")
    _check(checks, "bridge_pending_approved_zero", bridge_pending == 0, {"actual": bridge_pending})

    restore_primary = False
    restore_bridge = False
    if primary_ok and primary_quick == "ok":
        try:
            restore_primary = _sqlite_restore_drill(
                db_path,
                [
                    ("SELECT COUNT(*) FROM messages WHERE UPPER(direction)='OUTBOUND'", ()),
                    ("SELECT COUNT(*) FROM conversations WHERE COALESCE(outreach_authorized,0)=1", ()),
                ],
            )
        except sqlite3.Error:
            restore_primary = False
    if bridge_ok and bridge_quick == "ok":
        try:
            bridge_queries = []
            if {"approved_ts", "sent_ts"}.issubset(bridge_cols):
                condition = "approved_ts IS NOT NULL AND sent_ts IS NULL"
                if "template_id" in bridge_cols:
                    condition += " AND template_id IS NOT NULL"
                bridge_queries.append(("SELECT COUNT(*) FROM bridge_outbound WHERE %s" % condition, ()))
            restore_bridge = _sqlite_restore_drill(bridge_db_path, bridge_queries)
        except sqlite3.Error:
            restore_bridge = False
    _check(checks, "primary_restore_drill", restore_primary)
    _check(checks, "bridge_restore_drill", restore_bridge)

    health = health_payload
    if health is None:
        try:
            health = _fetch_health("http://127.0.0.1:9191/health")
        except Exception:
            health = {}
    _check(checks, "runtime_single_writer", str(health.get("runtime", "")) == EXPECTED_RUNTIME)
    _check(checks, "health_connected", health.get("connected") is True)
    _check(checks, "health_transport_wwebjs", str(health.get("transport", "")).lower() == "wwebjs")
    _check(checks, "runtime_paused", str(health.get("agent_status", "")).upper() == "PAUSED")
    _check(checks, "health_pending_bridge_zero", int(health.get("pending_bridge", -1)) == 0)
    try:
        recent = int(health.get("global_outbound_24h", -1))
    except (TypeError, ValueError):
        recent = -1
    _check(checks, "health_recent_outbound_bounded", recent in (0, 1), {"actual": recent})

    if current_boot_epoch is None:
        current_boot_epoch = _current_boot_epoch()
    _check(checks, "boot_epoch_readable", isinstance(current_boot_epoch, int) and current_boot_epoch > 0)
    if pre_reboot_boot_epoch is not None:
        _check(
            checks,
            "reboot_proven",
            isinstance(current_boot_epoch, int) and current_boot_epoch > int(pre_reboot_boot_epoch),
            {"advanced": isinstance(current_boot_epoch, int) and current_boot_epoch > int(pre_reboot_boot_epoch)},
        )

    ok = all(item["ok"] for item in checks)
    return {
        "gate": "ARGOS_POSTPILOT_READINESS",
        "ok": ok,
        "expected_head": expected_head,
        "expected_outbound_total": int(expected_outbound_total),
        "checks": checks,
        "safety": {
            "production_db_mutation": "NONE",
            "outbound_action": "NONE",
            "localauth_mutation": "NONE",
            "restore_target": "TEMPORARY_ONLY",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--bridge-db-path", required=True)
    parser.add_argument("--env-path", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-outbound-total", type=int, default=78)
    parser.add_argument("--pre-reboot-boot-epoch", type=int)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_head):
        raise SystemExit("expected exact SHA is required")
    report = run_gate(
        repo_root=args.repo_root,
        db_path=args.db_path,
        bridge_db_path=args.bridge_db_path,
        env_path=args.env_path,
        expected_head=args.expected_head,
        expected_outbound_total=args.expected_outbound_total,
        pre_reboot_boot_epoch=args.pre_reboot_boot_epoch,
    )
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
