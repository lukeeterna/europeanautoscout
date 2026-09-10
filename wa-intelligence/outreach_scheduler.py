#!/usr/bin/env python3
"""ARGOS zero-founder scheduler — queue-only, fail-closed S292 runtime.

The scheduler NEVER sends WhatsApp messages. It only enqueues fixed templates;
``wa-daemon.js`` remains the single writer and re-runs the final guard before
transport.

A dealer is eligible for business-initiated WhatsApp outreach only when BOTH:

* ``outreach_authorized=1`` (ARGOS internal business authorization), and
* traceable WhatsApp opt-in evidence is present.

For the official Cloud API, proactive Day1/Day7/Day12 rows also carry an exact
approved Meta template payload. Free-form text is not used to initiate a Cloud
conversation outside the 24-hour customer-service window.

Cadence:
- COLD/outbound=0 -> credibility-first Day1;
- CONTACTED/outbound=1 and 7 days silent -> Day7 recovery;
- CONTACTED/outbound=2 and 5 more days silent -> Day12 final.

Default runtime is disabled. Set ``ARGOS_AUTOMATION_ENABLED=1`` only at the
separate rollout gate after C10 is fully GREEN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
for candidate in (str(_HERE), str(_REPO)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from outbound_guard import evaluate as evaluate_outbound  # noqa: E402
from state_machine import ensure_state_columns  # noqa: E402
from templates import fill_template  # noqa: E402
from whatsapp_consent import consent_is_valid, ensure_consent_columns  # noqa: E402

DAY7_SECONDS = 7 * 24 * 3600
DAY12_AFTER_DAY7_SECONDS = 5 * 24 * 3600
_META_CONTRACT = json.loads((_HERE / "meta_templates.json").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class ScheduledCandidate:
    dealer_id: str
    phone: str
    template_id: str
    message: str
    state: str
    reason: str
    meta_parameters: tuple[str, ...] = ()
    opt_in_evidence_id: str = ""


def _connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    return con


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {str(row[1]) for row in con.execute(f"PRAGMA table_info('{table}')").fetchall()}
    except sqlite3.Error:
        return set()


def _parse_ts(value: Any) -> Optional[float]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        return None


def ensure_runtime_schema(db_path: str, bridge_path: str) -> None:
    ensure_state_columns(db_path)
    ensure_consent_columns(db_path)
    con = _connect(db_path)
    try:
        con.execute(
            """CREATE TABLE IF NOT EXISTS argos_scheduler_audit (
                   cycle_id TEXT NOT NULL,
                   dealer_id TEXT,
                   template_id TEXT,
                   decision TEXT NOT NULL,
                   reason TEXT,
                   created_at TEXT NOT NULL
               )"""
        )
        con.commit()
    finally:
        con.close()

    Path(bridge_path).parent.mkdir(parents=True, exist_ok=True)
    bcon = _connect(bridge_path)
    try:
        bcon.execute(
            """CREATE TABLE IF NOT EXISTS bridge_outbound (
                   id TEXT PRIMARY KEY,
                   deal_id TEXT NOT NULL,
                   target_role TEXT NOT NULL,
                   target_phone TEXT NOT NULL,
                   template_phase TEXT NOT NULL,
                   template_lang TEXT NOT NULL DEFAULT 'it',
                   body TEXT NOT NULL,
                   state_at_send TEXT,
                   created_ts INTEGER NOT NULL,
                   approved_ts INTEGER,
                   sent_ts INTEGER,
                   sent_status TEXT,
                   wa_msg_id TEXT,
                   processing_ts INTEGER,
                   attempt_count INTEGER DEFAULT 0,
                   action_type TEXT DEFAULT 'agent_auto'
               )"""
        )
        cols = _columns(bcon, "bridge_outbound")
        for name, definition in {
            "template_id": "TEXT",
            "inbound_msg_id": "TEXT",
            "guard_status": "TEXT",
            "guard_reason": "TEXT",
            "next_attempt_ts": "INTEGER",
            "meta_template_json": "TEXT",
            "whatsapp_opt_in_evidence_id": "TEXT",
        }.items():
            if name not in cols:
                bcon.execute(f'ALTER TABLE bridge_outbound ADD COLUMN "{name}" {definition}')
        bcon.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS uq_s292_scheduler_dealer_template
               ON bridge_outbound(deal_id, template_id)
               WHERE action_type = 's292_scheduler'"""
        )
        bcon.commit()
    finally:
        bcon.close()


def _last_message_times(con: sqlite3.Connection, dealer_id: str) -> tuple[Optional[float], Optional[float]]:
    cols = _columns(con, "messages")
    if not {"dealer_id", "direction"}.issubset(cols):
        return None, None
    ts_col = "created_at" if "created_at" in cols else ("received_at" if "received_at" in cols else None)
    if not ts_col:
        return None, None

    def latest(direction: str) -> Optional[float]:
        row = con.execute(
            f"""SELECT {ts_col} FROM messages
                WHERE dealer_id=? AND direction=? AND {ts_col} IS NOT NULL
                ORDER BY {ts_col} DESC LIMIT 1""",
            [dealer_id, direction],
        ).fetchone()
        return _parse_ts(row[0]) if row else None

    return latest("OUTBOUND"), latest("INBOUND")


def _source_for(row: sqlite3.Row) -> str:
    keys = set(row.keys())
    for key in ("public_source", "source", "profile_source"):
        if key in keys and str(row[key] or "").strip():
            return str(row[key]).strip()
    return "il sito/contatto pubblico della sua attività"


def _eligible_rows(con: sqlite3.Connection) -> list[sqlite3.Row]:
    cols = _columns(con, "conversations")
    required = {
        "dealer_id",
        "phone_number",
        "conversation_state",
        "outbound_count",
        "outreach_authorized",
        "whatsapp_opt_in",
        "whatsapp_opt_in_at",
        "whatsapp_opt_in_source",
        "whatsapp_opt_in_evidence_id",
        "whatsapp_opt_out_at",
    }
    if not required.issubset(cols):
        return []
    dealer_name_expr = "dealer_name" if "dealer_name" in cols else "dealer_id AS dealer_name"
    extras = [key for key in ("public_source", "source", "profile_source") if key in cols]
    extra_sql = (", " + ", ".join(extras)) if extras else ""
    return con.execute(
        f"""SELECT dealer_id, phone_number, conversation_state, outbound_count,
                   outreach_authorized, whatsapp_opt_in, whatsapp_opt_in_at,
                   whatsapp_opt_in_source, whatsapp_opt_in_evidence_id,
                   whatsapp_opt_out_at, {dealer_name_expr}{extra_sql}
            FROM conversations
            WHERE outreach_authorized=1
              AND whatsapp_opt_in=1
              AND whatsapp_opt_in_at IS NOT NULL
              AND TRIM(COALESCE(whatsapp_opt_in_source,'')) <> ''
              AND TRIM(COALESCE(whatsapp_opt_in_evidence_id,'')) <> ''
              AND whatsapp_opt_out_at IS NULL
              AND conversation_state IN ('COLD','CONTACTED')"""
    ).fetchall()


def _candidate(con: sqlite3.Connection, row: sqlite3.Row, now_ts: float) -> Optional[ScheduledCandidate]:
    dealer_id = str(row["dealer_id"] or "").strip()
    phone = str(row["phone_number"] or "").strip()
    state = str(row["conversation_state"] or "COLD").upper()
    outbound_count = int(row["outbound_count"] or 0)
    evidence_id = str(row["whatsapp_opt_in_evidence_id"] or "").strip()
    if (
        not dealer_id
        or not phone
        or int(row["outreach_authorized"] or 0) != 1
        or not consent_is_valid(dict(row))
    ):
        return None

    if state == "COLD" and outbound_count == 0:
        source = _source_for(row)
        brand_focus = "auto premium"
        template_id = "DAY1_PREMIUM"
        message = fill_template(template_id, {"source": source, "brand_focus": brand_focus})
        return (
            ScheduledCandidate(
                dealer_id,
                phone,
                template_id,
                message,
                state,
                "authorized_opted_in_day1",
                (source, brand_focus),
                evidence_id,
            )
            if message
            else None
        )

    if state != "CONTACTED" or outbound_count not in {1, 2}:
        return None
    last_outbound, last_inbound = _last_message_times(con, dealer_id)
    if last_outbound is None:
        return None
    if last_inbound is not None and last_inbound > last_outbound:
        return None

    age = max(0.0, now_ts - last_outbound)
    dealer_name = str(row["dealer_name"] or "").strip() or "Buongiorno"
    if outbound_count == 1 and age >= DAY7_SECONDS:
        message = fill_template("DAY7_RECOVERY", {"dealer_name": dealer_name})
        return (
            ScheduledCandidate(
                dealer_id,
                phone,
                "DAY7_RECOVERY",
                message,
                state,
                "authorized_opted_in_day7",
                (dealer_name,),
                evidence_id,
            )
            if message
            else None
        )
    if outbound_count == 2 and age >= DAY12_AFTER_DAY7_SECONDS:
        message = fill_template("DAY12_FINAL", {"dealer_name": dealer_name})
        return (
            ScheduledCandidate(
                dealer_id,
                phone,
                "DAY12_FINAL",
                message,
                state,
                "authorized_opted_in_day12",
                (dealer_name,),
                evidence_id,
            )
            if message
            else None
        )
    return None


def _meta_template_payload(
    candidate: ScheduledCandidate,
    *,
    env: Mapping[str, str],
) -> dict[str, Any]:
    contract = _META_CONTRACT.get(candidate.template_id)
    if not isinstance(contract, Mapping):
        raise ValueError(f"META_TEMPLATE_CONTRACT_MISSING: {candidate.template_id}")
    env_name = str(contract.get("env_name") or "").strip()
    template_name = str(env.get(env_name) or "").strip()
    language = str(env.get("META_WA_TEMPLATE_LANGUAGE") or "it").strip()
    expected_count = len(contract.get("parameters") or [])
    if not env_name or not template_name or not language:
        raise ValueError(f"META_TEMPLATE_CONFIG_MISSING: {candidate.template_id}")
    if len(candidate.meta_parameters) != expected_count or any(not str(value).strip() for value in candidate.meta_parameters):
        raise ValueError(f"META_TEMPLATE_PARAMETERS_INVALID: {candidate.template_id}")
    components: list[dict[str, Any]] = []
    if candidate.meta_parameters:
        components.append(
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": str(value)} for value in candidate.meta_parameters
                ],
            }
        )
    return {
        "name": template_name,
        "language": {"code": language},
        "components": components,
        "internal_template_id": candidate.template_id,
    }


def _audit(con: sqlite3.Connection, cycle_id: str, candidate: ScheduledCandidate, decision: str, reason: str) -> None:
    con.execute(
        """INSERT INTO argos_scheduler_audit
           (cycle_id, dealer_id, template_id, decision, reason, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            cycle_id,
            candidate.dealer_id,
            candidate.template_id,
            decision,
            reason,
            datetime.now(timezone.utc).isoformat(),
        ],
    )


def _enqueue(
    bridge_path: str,
    candidate: ScheduledCandidate,
    now_ts: float,
    *,
    meta_template: Optional[Mapping[str, Any]],
) -> tuple[bool, str]:
    row_id = "sched_" + hashlib.sha256(
        f"{candidate.dealer_id}|{candidate.template_id}".encode("utf-8")
    ).hexdigest()[:24]
    bcon = _connect(bridge_path)
    try:
        cur = bcon.execute(
            """INSERT OR IGNORE INTO bridge_outbound
               (id, deal_id, target_role, target_phone, template_phase,
                template_lang, body, state_at_send, created_ts, approved_ts,
                action_type, template_id, inbound_msg_id, guard_status, guard_reason,
                meta_template_json, whatsapp_opt_in_evidence_id)
               VALUES (?, ?, 'dealer', ?, ?, 'it', ?, ?, ?, ?,
                       's292_scheduler', ?, NULL, 'PASS', ?, ?, ?)""",
            [
                row_id,
                candidate.dealer_id,
                candidate.phone,
                candidate.template_id.lower(),
                candidate.message,
                candidate.state,
                int(now_ts),
                int(now_ts),
                candidate.template_id,
                candidate.reason,
                json.dumps(meta_template, ensure_ascii=False, sort_keys=True) if meta_template else None,
                candidate.opt_in_evidence_id,
            ],
        )
        bcon.commit()
        return cur.rowcount == 1, row_id
    finally:
        bcon.close()


def run_cycle(
    *,
    db_path: str,
    bridge_path: str,
    enabled: bool,
    dry_run: bool = False,
    now_ts: Optional[float] = None,
    transport_mode: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> dict:
    if not db_path or not bridge_path:
        raise ValueError("db_path and bridge_path are required")
    if not Path(db_path).exists():
        raise FileNotFoundError(db_path)
    if not enabled:
        return {"ok": True, "enabled": False, "queued": 0, "blocked": 0, "candidates": 0}

    ensure_runtime_schema(db_path, bridge_path)
    now_value = float(now_ts if now_ts is not None else time.time())
    runtime_env: Mapping[str, str] = env if env is not None else os.environ
    transport = str(transport_mode or runtime_env.get("ARGOS_WA_TRANSPORT") or "wwebjs").strip().lower()
    if transport not in {"wwebjs", "cloud"}:
        raise ValueError(f"unsupported transport: {transport}")

    cycle_id = "cycle_" + hashlib.sha256(f"{int(now_value)}|{db_path}".encode("utf-8")).hexdigest()[:16]
    con = _connect(db_path)
    queued = blocked = candidates = 0
    try:
        for row in _eligible_rows(con):
            candidate = _candidate(con, row, now_value)
            if candidate is None:
                continue
            candidates += 1
            guard = evaluate_outbound(
                db_path=db_path,
                dealer_id=candidate.dealer_id,
                template_id=candidate.template_id,
                message=candidate.message,
            )
            if not guard.get("ok"):
                blocked += 1
                _audit(con, cycle_id, candidate, "BLOCK", str(guard.get("reason") or "UNKNOWN"))
                continue

            meta_template: Optional[Mapping[str, Any]] = None
            if transport == "cloud":
                try:
                    meta_template = _meta_template_payload(candidate, env=runtime_env)
                except ValueError as exc:
                    blocked += 1
                    _audit(con, cycle_id, candidate, "BLOCK", str(exc))
                    continue

            if dry_run:
                _audit(con, cycle_id, candidate, "DRY_RUN", candidate.reason)
                continue
            inserted, row_id = _enqueue(
                bridge_path,
                candidate,
                now_value,
                meta_template=meta_template,
            )
            if inserted:
                queued += 1
            _audit(con, cycle_id, candidate, "QUEUED" if inserted else "DEDUP", f"{candidate.reason}:{row_id}")
        con.commit()
    finally:
        con.close()
    return {
        "ok": True,
        "enabled": True,
        "dry_run": dry_run,
        "transport": transport,
        "cycle_id": cycle_id,
        "candidates": candidates,
        "queued": queued,
        "blocked": blocked,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARGOS S292 queue-only outreach scheduler")
    parser.add_argument("--db-path", default=os.environ.get("ARGOS_DB_PATH", ""))
    parser.add_argument("--bridge-db-path", default=os.environ.get("BRIDGE_DB_PATH", ""))
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--interval", type=int, default=int(os.environ.get("ARGOS_SCHEDULER_INTERVAL_SECONDS", "900")))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    enabled = os.environ.get("ARGOS_AUTOMATION_ENABLED", "0").strip() == "1"
    interval = max(60, int(args.interval))

    def one() -> int:
        try:
            result = run_cycle(
                db_path=args.db_path,
                bridge_path=args.bridge_db_path,
                enabled=enabled,
                dry_run=args.dry_run,
            )
        except Exception as exc:
            result = {"ok": False, "error": type(exc).__name__, "reason": str(exc)}
            print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
            return 2
        print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
        return 0

    if args.once:
        return one()
    while True:
        one()
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
