#!/usr/bin/env python3
"""ARGOS post-send state updater — idempotent S292 production boundary.

Called only after the WhatsApp transport has returned and the outbound message
has been persisted. ``event_id`` is normally the real WA message id. During a
rolling upgrade an older daemon may omit it; in that case this module resolves
the newest persisted outbound ``wa_msg_id`` for the same dealer/template and
still fails closed if no traceable event can be found.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state_machine import STATES, ensure_state_columns  # noqa: E402


STEP_BY_TEMPLATE = {
    "DAY1_INTRO": "DAY1_SENT",
    "DAY1_PREMIUM": "DAY1_SENT",
    "DAY1_MIXED": "DAY1_SENT",
    "DAY1_GENERALIST": "DAY1_SENT",
    "DAY7_RECOVERY": "DAY7_SENT",
    "DAY12_FINAL": "DAY12_SENT",
    "IDENTITY_RESPONSE": "IDENTITY_SENT",
    "DEMAND_DISCOVERY_PROMPT": "DEMAND_DISCOVERY_SENT",
    "VEHICLE_REQUEST_ACK": "REQUEST_ACK_SENT",
    "VEHICLE_PROPOSAL": "VEHICLE_PROPOSAL_SENT",
    "VEHICLE_DETAILS": "VEHICLE_DETAILS_SENT",
    "CLOSING_PUSH": "CLOSING_SENT",
}


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    return con


def _ensure_event_table(con: sqlite3.Connection) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS argos_post_send_events (
               event_id TEXT PRIMARY KEY,
               dealer_id TEXT NOT NULL,
               template_id TEXT NOT NULL,
               state_before TEXT NOT NULL,
               state_after TEXT NOT NULL,
               applied_at TEXT NOT NULL
           )"""
    )


def _next_state(current_state: str, template_id: str) -> str:
    state = str(current_state or "COLD").upper()
    template = str(template_id or "").upper()
    if state not in STATES:
        raise ValueError(f"unknown conversation state: {state}")
    if state == "COLD" and template.startswith("DAY1"):
        return "CONTACTED"
    if state == "MANDATE_CONFIRMED" and template in {"VEHICLE_PROPOSAL", "VEHICLE_DETAILS"}:
        return "CONVERTING"
    return state


def _resolve_event_id(
    con: sqlite3.Connection,
    *,
    dealer_id: str,
    template_id: str,
    event_id: str | None,
) -> str:
    explicit = str(event_id or "").strip()
    if explicit:
        return explicit
    columns = {
        str(row[1]) for row in con.execute("PRAGMA table_info('messages')").fetchall()
    }
    required = {"dealer_id", "direction", "wa_msg_id", "template_id"}
    if not required.issubset(columns):
        raise ValueError("event_id required: messages table cannot resolve wa_msg_id")
    order_column = "created_at" if "created_at" in columns else "rowid"
    row = con.execute(
        f"""SELECT wa_msg_id FROM messages
            WHERE dealer_id = ? AND direction = 'OUTBOUND'
              AND template_id = ? AND wa_msg_id IS NOT NULL
            ORDER BY {order_column} DESC LIMIT 1""",
        [dealer_id, template_id],
    ).fetchone()
    if not row or not row[0]:
        raise ValueError("event_id required: no persisted outbound wa_msg_id found")
    return str(row[0])


def apply_post_send(
    *,
    db_path: str,
    dealer_id: str,
    template_id: str,
    event_id: str | None = None,
) -> dict:
    dealer_id = str(dealer_id or "").strip()
    template_id = str(template_id or "").strip().upper()
    if not dealer_id or not template_id:
        raise ValueError("dealer_id and template_id are required")

    ensure_state_columns(db_path)
    con = _connect(db_path)
    try:
        _ensure_event_table(con)
        resolved_event_id = _resolve_event_id(
            con,
            dealer_id=dealer_id,
            template_id=template_id,
            event_id=event_id,
        )
        con.execute("BEGIN IMMEDIATE")

        existing = con.execute(
            "SELECT state_before, state_after FROM argos_post_send_events WHERE event_id = ?",
            [resolved_event_id],
        ).fetchone()
        if existing:
            dealer = con.execute(
                "SELECT conversation_state, outbound_count FROM conversations WHERE dealer_id = ?",
                [dealer_id],
            ).fetchone()
            con.commit()
            return {
                "ok": True,
                "idempotent": True,
                "event_id": resolved_event_id,
                "new_state": dealer["conversation_state"] if dealer else existing["state_after"],
                "outbound_count": int((dealer["outbound_count"] if dealer else 0) or 0),
            }

        dealer = con.execute(
            "SELECT conversation_state, outbound_count FROM conversations WHERE dealer_id = ?",
            [dealer_id],
        ).fetchone()
        if not dealer:
            raise LookupError(f"dealer not found: {dealer_id}")

        state_before = str(dealer["conversation_state"] or "COLD").upper()
        state_after = _next_state(state_before, template_id)
        outbound_count = int(dealer["outbound_count"] or 0) + 1
        now = datetime.now(timezone.utc).isoformat()
        step = STEP_BY_TEMPLATE.get(template_id, f"{template_id}_SENT")

        columns = {
            str(row[1])
            for row in con.execute("PRAGMA table_info('conversations')").fetchall()
        }
        if "current_step" in columns:
            con.execute(
                """UPDATE conversations
                   SET outbound_count = ?, conversation_state = ?, state_updated_at = ?,
                       current_step = ?
                   WHERE dealer_id = ?""",
                [outbound_count, state_after, now, step, dealer_id],
            )
        else:
            con.execute(
                """UPDATE conversations
                   SET outbound_count = ?, conversation_state = ?, state_updated_at = ?
                   WHERE dealer_id = ?""",
                [outbound_count, state_after, now, dealer_id],
            )

        con.execute(
            """INSERT INTO argos_post_send_events
               (event_id, dealer_id, template_id, state_before, state_after, applied_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [resolved_event_id, dealer_id, template_id, state_before, state_after, now],
        )
        con.commit()
        return {
            "ok": True,
            "idempotent": False,
            "event_id": resolved_event_id,
            "new_state": state_after,
            "outbound_count": outbound_count,
        }
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARGOS idempotent post-send updater")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--dealer-id", required=True)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--event-id", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = apply_post_send(
            db_path=args.db_path,
            dealer_id=args.dealer_id,
            template_id=args.template_id,
            event_id=args.event_id,
        )
    except Exception as exc:
        result = {"ok": False, "error": type(exc).__name__, "reason": str(exc)}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
