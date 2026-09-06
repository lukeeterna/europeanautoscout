#!/usr/bin/env python3
"""ARGOS C11 controlled-pilot preflight — read-only and zero-outbound.

This gate is intentionally safe to prepare before WhatsApp device pairing. It
never calls /resume, /send or /send-doc and never writes SQLite, Git, PM2 or
LocalAuth state. After pairing, C11 may proceed only when this preflight proves
that the exact deployed release is connected while still PAUSED, that its exact
LocalAuth profile is persistently present, and that the only internally
authorized recipient is the explicitly named controlled test record with
traceable WhatsApp opt-in evidence.

The controlled recipient must be a fresh COLD record with outbound_count=0 and
zero historical OUTBOUND rows, so the pilot cannot accidentally reuse a real or
previously contacted dealer. The normal production business-hours policy remains
mandatory even for C11. No phone number, API key, consent evidence id or other
secret is emitted.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional


@dataclass
class Report:
    ok: bool = True
    checks: list[dict[str, Any]] = field(default_factory=list)
    outbound_baseline: Optional[int] = None

    def add(self, name: str, ok: bool, detail: Any = None) -> None:
        self.checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            self.ok = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "gate": "C11_PREFLIGHT",
            "outbound_baseline": self.outbound_baseline,
            "checks": self.checks,
        }


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
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _ro_connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def _quick_check(path: Path) -> str:
    con = _ro_connect(path)
    try:
        row = con.execute("PRAGMA quick_check").fetchone()
        return str(row[0] if row else "missing")
    finally:
        con.close()


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in con.execute(f"PRAGMA table_info('{table}')").fetchall()}


def _health(url: str) -> tuple[Optional[Mapping[str, Any]], str]:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, Mapping):
            return None, "health payload is not an object"
        return payload, ""
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__


def _git_head(repo_root: Path) -> tuple[Optional[str], str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, type(exc).__name__
    head = proc.stdout.strip() if proc.returncode == 0 else ""
    return (head or None), (proc.stderr.strip() if proc.returncode else "")


def _consent_valid(row: Mapping[str, Any]) -> bool:
    return (
        int(row.get("whatsapp_opt_in") or 0) == 1
        and bool(str(row.get("whatsapp_opt_in_at") or "").strip())
        and bool(str(row.get("whatsapp_opt_in_source") or "").strip())
        and bool(str(row.get("whatsapp_opt_in_evidence_id") or "").strip())
        and not bool(str(row.get("whatsapp_opt_out_at") or "").strip())
    )


def _localauth_profile_status(env: Mapping[str, str]) -> dict[str, bool]:
    session_raw = str(env.get("ARGOS_WA_SESSION_DIR") or "").strip()
    client_id = str(env.get("ARGOS_WA_CLIENT_ID") or "").strip()
    root = Path(session_raw).expanduser() if session_raw else None
    root_ok = bool(root and root.is_dir())
    profile = root / f"session-{client_id}" if root and client_id else None
    profile_ok = bool(profile and profile.is_dir())
    file_count_positive = False
    if profile_ok:
        try:
            file_count_positive = any(p.is_file() for p in profile.rglob("*"))
        except OSError:
            file_count_positive = False
    return {
        "client_id_configured": bool(client_id),
        "session_root_present": root_ok,
        "profile_directory_present": profile_ok,
        "file_count_positive": file_count_positive,
    }


def run_preflight(
    *,
    repo_root: Path,
    db_path: Path,
    bridge_db_path: Path,
    expected_head: str,
    test_dealer_id: str,
    expected_outbound_baseline: int = 77,
    health_payload: Optional[Mapping[str, Any]] = None,
    health_url: str = "http://127.0.0.1:9191/health",
) -> Report:
    report = Report()
    root = repo_root.resolve()
    primary = db_path.expanduser().resolve()
    bridge = bridge_db_path.expanduser().resolve()
    dealer_id = str(test_dealer_id or "").strip()

    report.add("test_dealer_id_supplied", bool(dealer_id), "configured" if dealer_id else "missing")
    report.add("primary_db_present", primary.is_file(), str(primary))
    report.add("bridge_db_present", bridge.is_file(), str(bridge))
    if not primary.is_file() or not bridge.is_file() or not dealer_id:
        return report

    try:
        quick = _quick_check(primary)
        report.add("primary_db_quick_check", quick == "ok", quick)
    except sqlite3.Error as exc:
        report.add("primary_db_quick_check", False, type(exc).__name__)
    try:
        quick = _quick_check(bridge)
        report.add("bridge_db_quick_check", quick == "ok", quick)
    except sqlite3.Error as exc:
        report.add("bridge_db_quick_check", False, type(exc).__name__)

    head, head_error = _git_head(root)
    report.add("git_head_readable", bool(head), head_error or "readable")
    report.add(
        "expected_head",
        bool(expected_head) and head == expected_head,
        {"matches": bool(expected_head) and head == expected_head},
    )

    env_path = root / "wa-intelligence" / ".env"
    env = _load_env(env_path)
    report.add("private_env_present", env_path.is_file(), "present" if env_path.is_file() else "missing")
    if env_path.is_file():
        try:
            mode = env_path.stat().st_mode & 0o777
            report.add("private_env_mode", mode & 0o077 == 0, oct(mode))
        except OSError as exc:
            report.add("private_env_mode", False, type(exc).__name__)
    report.add(
        "automation_disabled",
        str(env.get("ARGOS_AUTOMATION_ENABLED") or "0").strip() != "1",
        "disabled" if str(env.get("ARGOS_AUTOMATION_ENABLED") or "0").strip() != "1" else "enabled",
    )
    report.add(
        "env_transport_wwebjs",
        str(env.get("ARGOS_WA_TRANSPORT") or "wwebjs").strip().lower() == "wwebjs",
        str(env.get("ARGOS_WA_TRANSPORT") or "wwebjs").strip().lower(),
    )
    report.add(
        "api_key_configured",
        bool(str(env.get("ARGOS_API_KEY") or "").strip()),
        "configured" if str(env.get("ARGOS_API_KEY") or "").strip() else "missing",
    )
    report.add(
        "loopback_bind",
        str(env.get("ARGOS_BIND_HOST") or "127.0.0.1").strip() in {"127.0.0.1", "localhost"},
        str(env.get("ARGOS_BIND_HOST") or "127.0.0.1").strip(),
    )
    localauth = _localauth_profile_status(env)
    report.add("localauth_client_id_present", localauth["client_id_configured"])
    report.add(
        "localauth_profile_persistent",
        all(localauth.values()),
        localauth,
    )

    health = health_payload
    health_error = ""
    if health is None:
        health, health_error = _health(health_url)
    report.add("health_readable", isinstance(health, Mapping), health_error or "readable")
    if isinstance(health, Mapping):
        report.add("health_runtime", health.get("runtime") == "argos-s292-single-writer", str(health.get("runtime")))
        report.add("connected", health.get("connected") is True, bool(health.get("connected")))
        report.add("transport_wwebjs", str(health.get("transport") or "").lower() == "wwebjs", str(health.get("transport")))
        report.add("runtime_paused", str(health.get("agent_status") or "").upper() == "PAUSED", str(health.get("agent_status")))
        report.add("business_hours", health.get("business_hours") is True, bool(health.get("business_hours")))
        report.add("bridge_enabled", health.get("bridge_enabled") is True, bool(health.get("bridge_enabled")))
        try:
            pending_health = int(health.get("pending_bridge") or 0)
        except (TypeError, ValueError):
            pending_health = -1
        report.add("health_pending_bridge_zero", pending_health == 0, pending_health)
        try:
            recent_health = int(health.get("global_outbound_24h") or 0)
        except (TypeError, ValueError):
            recent_health = -1
        report.add("health_outbound_24h_zero", recent_health == 0, recent_health)

    try:
        con = _ro_connect(primary)
        try:
            cols = _columns(con, "conversations")
            required = {
                "dealer_id",
                "phone_number",
                "outreach_authorized",
                "conversation_state",
                "outbound_count",
                "whatsapp_opt_in",
                "whatsapp_opt_in_at",
                "whatsapp_opt_in_source",
                "whatsapp_opt_in_evidence_id",
                "whatsapp_opt_out_at",
            }
            report.add("consent_schema", required.issubset(cols), "present" if required.issubset(cols) else "incomplete")
            selected: dict[str, Any] = {}
            if required.issubset(cols):
                rows = con.execute(
                    """SELECT dealer_id, phone_number, outreach_authorized,
                              conversation_state, outbound_count,
                              whatsapp_opt_in, whatsapp_opt_in_at,
                              whatsapp_opt_in_source, whatsapp_opt_in_evidence_id,
                              whatsapp_opt_out_at
                         FROM conversations
                        WHERE COALESCE(outreach_authorized,0)=1"""
                ).fetchall()
                report.add("exactly_one_authorized_recipient", len(rows) == 1, len(rows))
                selected = dict(rows[0]) if len(rows) == 1 else {}
                is_controlled = bool(selected) and str(selected.get("dealer_id") or "") == dealer_id
                report.add(
                    "authorized_recipient_is_controlled_test",
                    is_controlled,
                    "match" if is_controlled else "mismatch",
                )
                phone_present = bool(str(selected.get("phone_number") or "").strip())
                report.add("controlled_test_phone_present", phone_present, "present" if phone_present else "missing")
                valid_consent = bool(selected) and _consent_valid(selected)
                report.add("controlled_test_whatsapp_opt_in", valid_consent, "valid" if valid_consent else "invalid")
                state = str(selected.get("conversation_state") or "COLD").upper() if selected else ""
                report.add("controlled_test_state_cold", state == "COLD", state or "missing")
                outbound_count = int(selected.get("outbound_count") or 0) if selected else -1
                report.add("controlled_test_outbound_count_zero", outbound_count == 0, outbound_count)

            msg_cols = _columns(con, "messages")
            if "direction" in msg_cols:
                row = con.execute("SELECT COUNT(*) FROM messages WHERE UPPER(direction)='OUTBOUND'").fetchone()
                report.outbound_baseline = int(row[0] if row else 0)
                report.add("outbound_baseline_readable", True, report.outbound_baseline)
                report.add(
                    "outbound_baseline_expected",
                    report.outbound_baseline == int(expected_outbound_baseline),
                    {"expected": int(expected_outbound_baseline), "actual": report.outbound_baseline},
                )
                if "dealer_id" in msg_cols:
                    row = con.execute(
                        "SELECT COUNT(*) FROM messages WHERE dealer_id=? AND UPPER(direction)='OUTBOUND'",
                        [dealer_id],
                    ).fetchone()
                    prior = int(row[0] if row else 0)
                    report.add("controlled_test_historical_outbound_zero", prior == 0, prior)
                else:
                    report.add("controlled_test_historical_outbound_zero", False, "messages.dealer_id missing")
            else:
                report.add("outbound_baseline_readable", False, "messages.direction missing")
                report.add("controlled_test_historical_outbound_zero", False, "messages.direction missing")
        finally:
            con.close()
    except sqlite3.Error as exc:
        report.add("primary_policy_read", False, type(exc).__name__)

    try:
        con = _ro_connect(bridge)
        try:
            cols = _columns(con, "bridge_outbound")
            required = {"approved_ts", "sent_ts"}
            report.add("bridge_outbound_schema", required.issubset(cols), "present" if required.issubset(cols) else "incomplete")
            if required.issubset(cols):
                row = con.execute(
                    "SELECT COUNT(*) FROM bridge_outbound WHERE approved_ts IS NOT NULL AND sent_ts IS NULL"
                ).fetchone()
                pending = int(row[0] if row else 0)
                report.add("bridge_pending_approved_zero", pending == 0, pending)
        finally:
            con.close()
    except sqlite3.Error as exc:
        report.add("bridge_policy_read", False, type(exc).__name__)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only ARGOS C11 controlled-pilot preflight")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--bridge-db-path", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--test-dealer-id", required=True)
    parser.add_argument("--expected-outbound-baseline", type=int, default=77)
    parser.add_argument("--health-url", default="http://127.0.0.1:9191/health")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = run_preflight(
        repo_root=Path(args.repo_root),
        db_path=Path(args.db_path),
        bridge_db_path=Path(args.bridge_db_path),
        expected_head=str(args.expected_head),
        test_dealer_id=str(args.test_dealer_id),
        expected_outbound_baseline=int(args.expected_outbound_baseline),
        health_url=str(args.health_url),
    )
    print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True, indent=2 if args.pretty else None))
    return 0 if report.ok else 20


if __name__ == "__main__":
    raise SystemExit(main())
