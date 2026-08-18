#!/usr/bin/env python3
"""ARGOS conversation state machine — S292 demand-side semantics.

A language classifier may detect interest or a vehicle request, but it cannot
create a mandate.  ``VEHICLE_REQUEST`` therefore enters DEMAND_DISCOVERY.  The
MANDATE_CONFIRMED state is reachable only through ``record_verified_mandate``
with a traceable DemandEvidence satisfying the canonical sourcing gate.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from src.cove.demand_contract import (  # noqa: E402
    DemandEvidence,
    require_sourcing_authorization,
)


STATES = {
    "COLD": {
        "allowed_templates": ["DAY1_INTRO", "DAY1_PREMIUM", "DAY1_MIXED", "DAY1_GENERALIST"],
        "max_outbound": 1,
        "requires_inbound": False,
    },
    "CONTACTED": {
        "allowed_templates": ["IDENTITY_RESPONSE", "DAY7_RECOVERY", "DAY12_FINAL"],
        "max_outbound": 3,
        "requires_inbound": False,
    },
    "ENGAGED": {
        "allowed_templates": [
            "IDENTITY_RESPONSE",
            "OBJ_1_NO_INTEREST",
            "OBJ_2_FEE",
            "OBJ_3_TRUST",
            "OBJ_4_TIMING",
            "OBJ_5_SOURCING",
        ],
        "max_outbound": None,
        "requires_inbound": True,
    },
    "DEMAND_DISCOVERY": {
        "allowed_templates": [
            "IDENTITY_RESPONSE",
            "OBJ_2_FEE",
            "OBJ_3_TRUST",
            "OBJ_5_SOURCING",
            # Legacy IDs retained for renderer compatibility. They may be used
            # only as request-confirmation copy, never as unsolicited offers.
            "VEHICLE_PROPOSAL",
            "VEHICLE_DETAILS",
        ],
        "max_outbound": None,
        "requires_inbound": True,
    },
    "MANDATE_CONFIRMED": {
        "allowed_templates": [
            "IDENTITY_RESPONSE",
            "VEHICLE_PROPOSAL",
            "VEHICLE_DETAILS",
            "CLOSING_PUSH",
            "OBJ_2_FEE",
        ],
        "max_outbound": None,
        "requires_inbound": True,
    },
    "CONVERTING": {
        "allowed_templates": ["VEHICLE_DETAILS", "CLOSING_PUSH", "OBJ_2_FEE"],
        "max_outbound": None,
        "requires_inbound": True,
    },
    "CLOSED_WON": {"allowed_templates": [], "max_outbound": 0, "requires_inbound": False},
    "CLOSED_LOST": {"allowed_templates": [], "max_outbound": 0, "requires_inbound": False},
    "ARCHIVED": {"allowed_templates": [], "max_outbound": 0, "requires_inbound": False},
}

# A classifier can advance conversational discovery, never the mandate gate.
TRANSITIONS = {
    ("COLD", "OUTBOUND_SENT"): "CONTACTED",
    ("CONTACTED", "POSITIVE"): "ENGAGED",
    ("CONTACTED", "CURIOSITY"): "ENGAGED",
    ("CONTACTED", "OBJECTION"): "ENGAGED",
    ("CONTACTED", "NEGATIVE"): "CONTACTED",
    ("CONTACTED", "VEHICLE_REQUEST"): "DEMAND_DISCOVERY",
    ("ENGAGED", "POSITIVE"): "ENGAGED",
    ("ENGAGED", "VEHICLE_REQUEST"): "DEMAND_DISCOVERY",
    ("ENGAGED", "CURIOSITY"): "ENGAGED",
    ("ENGAGED", "OBJECTION"): "ENGAGED",
    ("ENGAGED", "NEGATIVE"): "ENGAGED",
    ("DEMAND_DISCOVERY", "VEHICLE_REQUEST"): "DEMAND_DISCOVERY",
    ("DEMAND_DISCOVERY", "POSITIVE"): "DEMAND_DISCOVERY",
    ("DEMAND_DISCOVERY", "CURIOSITY"): "DEMAND_DISCOVERY",
    ("DEMAND_DISCOVERY", "OBJECTION"): "DEMAND_DISCOVERY",
    ("DEMAND_DISCOVERY", "NEGATIVE"): "ENGAGED",
    ("MANDATE_CONFIRMED", "POSITIVE"): "MANDATE_CONFIRMED",
    ("MANDATE_CONFIRMED", "VEHICLE_REQUEST"): "MANDATE_CONFIRMED",
    ("MANDATE_CONFIRMED", "NEGATIVE"): "DEMAND_DISCOVERY",
}


def get_transition(current_state: str, intent: str) -> str:
    return TRANSITIONS.get((current_state, intent), current_state)


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    return con


def ensure_state_columns(db_path: str) -> None:
    """Idempotently add conversation and S292 evidence columns."""
    con = _connect(db_path)
    migrations = [
        "ALTER TABLE conversations ADD COLUMN conversation_state TEXT DEFAULT 'COLD'",
        "ALTER TABLE conversations ADD COLUMN outbound_count INTEGER DEFAULT 0",
        "ALTER TABLE conversations ADD COLUMN inbound_count INTEGER DEFAULT 0",
        "ALTER TABLE conversations ADD COLUMN last_inbound_at TEXT",
        "ALTER TABLE conversations ADD COLUMN state_updated_at TEXT",
        "ALTER TABLE conversations ADD COLUMN escalation_flag INTEGER DEFAULT 0",
        # Kept for schema compatibility; deceptive synthetic handoff values are
        # no longer accepted by set_handoff_source().
        "ALTER TABLE conversations ADD COLUMN handoff_source TEXT DEFAULT 'cold'",
        "ALTER TABLE conversations ADD COLUMN is_micro_dealer INTEGER DEFAULT 0",
        "ALTER TABLE conversations ADD COLUMN demand_evidence_json TEXT",
        "ALTER TABLE conversations ADD COLUMN demand_evidence_id TEXT",
        "ALTER TABLE conversations ADD COLUMN demand_evidence_source TEXT",
        "ALTER TABLE conversations ADD COLUMN mandate_verified_at TEXT",
    ]
    try:
        for sql in migrations:
            try:
                con.execute(sql)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        con.commit()
    finally:
        con.close()


VALID_HANDOFF_SOURCES = ("cold", "referral", "direct", "organic")


def is_post_handoff(dealer: Mapping[str, Any]) -> bool:
    """True only for a real, recorded referral/direct handoff."""
    source = str(dealer.get("handoff_source") or "cold").strip().lower()
    return source in {"referral", "direct", "organic"}


def set_handoff_source(db_path: str, dealer_id: str, source: str) -> bool:
    source = str(source or "").strip().lower()
    if source not in VALID_HANDOFF_SOURCES:
        return False
    con = _connect(db_path)
    try:
        con.execute(
            "UPDATE conversations SET handoff_source = ? WHERE dealer_id = ?",
            [source, dealer_id],
        )
        con.commit()
    finally:
        con.close()
    return True


def set_is_micro_dealer(db_path: str, dealer_id: str, value: bool) -> None:
    con = _connect(db_path)
    try:
        con.execute(
            "UPDATE conversations SET is_micro_dealer = ? WHERE dealer_id = ?",
            [1 if value else 0, dealer_id],
        )
        con.commit()
    finally:
        con.close()


def get_dealer_state(db_path: str, dealer_id: str) -> dict:
    con = _connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT * FROM conversations WHERE dealer_id = ?", [dealer_id]
        ).fetchone()
        return dict(row) if row else {}
    finally:
        con.close()


def update_state(db_path: str, dealer_id: str, new_state: str) -> None:
    if new_state not in STATES:
        raise ValueError(f"unknown conversation state: {new_state}")
    con = _connect(db_path)
    try:
        con.execute(
            """UPDATE conversations
               SET conversation_state = ?, state_updated_at = ?
               WHERE dealer_id = ?""",
            [new_state, datetime.now(timezone.utc).isoformat(), dealer_id],
        )
        con.commit()
    finally:
        con.close()


def increment_outbound(db_path: str, dealer_id: str) -> None:
    con = _connect(db_path)
    try:
        con.execute(
            "UPDATE conversations SET outbound_count = COALESCE(outbound_count, 0) + 1 WHERE dealer_id = ?",
            [dealer_id],
        )
        con.commit()
    finally:
        con.close()


def record_inbound(db_path: str, dealer_id: str) -> None:
    con = _connect(db_path)
    try:
        con.execute(
            """UPDATE conversations
               SET inbound_count = COALESCE(inbound_count, 0) + 1,
                   last_inbound_at = ?
               WHERE dealer_id = ?""",
            [datetime.now(timezone.utc).isoformat(), dealer_id],
        )
        con.commit()
    finally:
        con.close()


def record_verified_mandate(
    db_path: str,
    dealer_id: str,
    evidence: DemandEvidence | Mapping[str, Any],
) -> DemandEvidence:
    """Persist the only transition that may create MANDATE_CONFIRMED.

    The write is transactional and refuses dealer mismatch, inferred evidence,
    an empty vehicle request, or an untraceable source/evidence id.
    """
    ensure_state_columns(db_path)
    parsed = evidence if isinstance(evidence, DemandEvidence) else DemandEvidence.from_mapping(evidence)
    authorized = require_sourcing_authorization(parsed)
    if authorized.dealer_id != str(dealer_id):
        raise PermissionError("S292_GATE: dealer_id/evidence mismatch")

    serialized = json.dumps(authorized.to_dict(), ensure_ascii=False, sort_keys=True)
    now = datetime.now(timezone.utc).isoformat()
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT dealer_id FROM conversations WHERE dealer_id = ?", [dealer_id]
        ).fetchone()
        if not row:
            raise LookupError(f"dealer {dealer_id} not found in conversations")
        con.execute("BEGIN IMMEDIATE")
        con.execute(
            """UPDATE conversations
               SET demand_evidence_json = ?,
                   demand_evidence_id = ?,
                   demand_evidence_source = ?,
                   mandate_verified_at = ?,
                   conversation_state = 'MANDATE_CONFIRMED',
                   state_updated_at = ?
               WHERE dealer_id = ?""",
            [
                serialized,
                authorized.evidence_id,
                authorized.source,
                now,
                now,
                dealer_id,
            ],
        )
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return authorized


def get_verified_mandate(db_path: str, dealer_id: str) -> Optional[DemandEvidence]:
    """Load persisted mandate and re-run the S292 gate on every read."""
    ensure_state_columns(db_path)
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT demand_evidence_json FROM conversations WHERE dealer_id = ?",
            [dealer_id],
        ).fetchone()
    finally:
        con.close()
    if not row or not row[0]:
        return None
    try:
        raw = json.loads(row[0])
        # to_dict nests claims; from_mapping supports that shape.
        evidence = DemandEvidence.from_mapping(raw)
        return require_sourcing_authorization(evidence)
    except (json.JSONDecodeError, TypeError, ValueError, PermissionError):
        # Corrupt/stale evidence never silently authorizes sourcing.
        return None


def can_send(db_path: str, dealer_id: str, template_id: str) -> tuple[bool, str]:
    dealer = get_dealer_state(db_path, dealer_id)
    if not dealer:
        return False, "DEALER_NOT_FOUND"
    state = dealer.get("conversation_state") or "COLD"
    rules = STATES.get(state)
    if not rules:
        return False, f"UNKNOWN_STATE: {state}"
    if template_id not in rules["allowed_templates"]:
        return False, f"TEMPLATE_NOT_ALLOWED: {template_id} in state {state}"

    max_out = rules["max_outbound"]
    current_out = int(dealer.get("outbound_count") or 0)
    if max_out is not None and current_out >= max_out:
        return False, f"CAP_REACHED: {current_out}/{max_out} in state {state}"

    if rules["requires_inbound"]:
        inbound_count = int(dealer.get("inbound_count") or 0)
        if inbound_count == 0:
            return False, f"REQUIRES_INBOUND: state {state} needs dealer response first"
        if current_out > 0 and current_out >= inbound_count:
            return False, f"WAIT_FOR_INBOUND: {current_out} out >= {inbound_count} in"

    if state in {"ARCHIVED", "CLOSED_WON", "CLOSED_LOST"}:
        return False, f"DEALER_{state}"
    return True, "OK"


def is_duplicate(db_path: str, dealer_id: str, message_text: str, hours: int = 24) -> bool:
    msg_hash = hashlib.sha256(message_text.strip().lower().encode("utf-8")).hexdigest()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    con = _connect(db_path)
    try:
        recent = con.execute(
            """SELECT body FROM messages
               WHERE dealer_id = ? AND direction = 'OUTBOUND' AND created_at > ?
               ORDER BY created_at DESC LIMIT 10""",
            [dealer_id, cutoff],
        ).fetchall()
    finally:
        con.close()
    for (body,) in recent:
        if body and hashlib.sha256(body.strip().lower().encode("utf-8")).hexdigest() == msg_hash:
            return True
    return False


def process_inbound(db_path: str, dealer_id: str, intent: str) -> str:
    """Record inbound and apply conversational transition only.

    Critical invariant: even ``VEHICLE_REQUEST`` cannot set
    MANDATE_CONFIRMED; only record_verified_mandate() can do that.
    """
    record_inbound(db_path, dealer_id)
    dealer = get_dealer_state(db_path, dealer_id)
    current_state = dealer.get("conversation_state") or "COLD"
    new_state = get_transition(current_state, str(intent or "UNKNOWN").upper())
    if new_state != current_state:
        update_state(db_path, dealer_id, new_state)
    return new_state


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ensure_state_columns(sys.argv[1])
        print(f"State machine columns ensured on {sys.argv[1]}")
    else:
        print("Usage: python state_machine.py <db_path>")
