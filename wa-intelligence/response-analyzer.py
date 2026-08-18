#!/usr/bin/env python3
"""ARGOS Azzurra response analyzer — deterministic S292 production runtime.

The analyzer receives a persisted inbound message from ``wa-daemon.js`` and
performs only deterministic, auditable operations:

1. classify conversation intent;
2. capture dealer vehicle criteria without inventing missing values;
3. advance conversational state;
4. create MANDATE_CONFIRMED only for an explicit, traceable dealer instruction;
5. select a fixed evidence-safe template;
6. run the final outbound guard before enqueuing the bridge row;
7. persist exact ``template_id`` + ``inbound_msg_id`` for the single-writer
   WhatsApp transport.

An LLM may be added later as a non-authoritative drafting aid, but it is not an
authority in this production path and cannot create a mandate, economics, or a
business fact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from demand_capture import VehicleRequestCapture, capture_vehicle_request  # noqa: E402
from outbound_guard import evaluate as evaluate_outbound  # noqa: E402
from state_machine import (  # noqa: E402
    ensure_state_columns,
    get_dealer_state,
    is_post_handoff,
    process_inbound,
    record_verified_mandate,
    update_state,
)
from templates import fill_template, select_template  # noqa: E402


INTENT_VEHICLE_REQUEST = "VEHICLE_REQUEST"
INTENT_CURIOSITY = "CURIOSITY"
INTENT_POSITIVE = "POSITIVE"
INTENT_NEGATIVE = "NEGATIVE"
INTENT_OBJECTION = "OBJECTION"
INTENT_UNKNOWN = "UNKNOWN"
INTENT_OPT_OUT = "OPT_OUT"

_NEGATIVE = (
    r"\bnon\s+(?:mi\s+)?interessa\b",
    r"\bnon\s+serve\b",
    r"\bno\s+grazie\b",
    r"\bnon\s+fa\s+per\s+noi\b",
    r"\bnon\s+fa\s+per\s+me\b",
)
_OPT_OUT = (
    r"\bnon\s+(?:mi\s+)?contatt",
    r"\bcancell(?:a|ami|ate)\b",
    r"\brimuov(?:i|etemi)\b",
    r"\bstop\b",
    r"\bnon\s+scriv(?:ermi|etemi)\b",
)
_CURIOSITY = (
    r"\bchi\s+(?:siete|sei)\b",
    r"\bcos['’]?e\b",
    r"\bcome\s+funziona\b",
    r"\bdi\s+cosa\s+si\s+tratta\b",
    r"\bspiegami\b",
)
_POSITIVE = (
    r"\binteressante\b",
    r"\bmi\s+interessa\b",
    r"\bva\s+bene\b",
    r"\bok\b",
    r"\bsi\b",
    r"\bsì\b",
    r"\bparliamone\b",
)
_OBJECTION_FEE = (
    r"\bquanto\s+costa\b",
    r"\bfee\b",
    r"\bcommissione\b",
    r"\bprezzo\s+del\s+servizio\b",
)
_OBJECTION_TRUST = (
    r"\bmi\s+fido\b",
    r"\bgaranz",
    r"\bsicuro\b",
    r"\btruff",
    r"\baffidabil",
)
_OBJECTION_TIMING = (
    r"\bnon\s+ora\b",
    r"\bpiu\s+avanti\b",
    r"\bpiù\s+avanti\b",
    r"\bricontatt",
    r"\bsettimana\s+prossima\b",
)
_OBJECTION_SOURCING = (
    r"\bda\s+dove\b",
    r"\bprovenienza\b",
    r"\bgermania\b",
    r"\beuropa\b",
    r"\bcome\s+verificat",
)


@dataclass(frozen=True)
class Classification:
    intent: str
    confidence: float
    objection_code: Optional[str] = None
    vehicle_capture: Optional[VehicleRequestCapture] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "objection_code": self.objection_code,
            "vehicle_capture": (
                {
                    "criteria": dict(self.vehicle_capture.criteria),
                    "explicit_commission": self.vehicle_capture.explicit_commission,
                    "authorization_ready": self.vehicle_capture.authorization_ready,
                    "summary": self.vehicle_capture.summary,
                    "missing_for_search": list(self.vehicle_capture.missing_for_search),
                }
                if self.vehicle_capture
                else None
            ),
        }


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _matches(text: str, patterns: Sequence[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def classify_message(message_id: str, body: str) -> Classification:
    """Deterministic intent router; vehicle capture takes precedence over sentiment."""
    normalized = _norm(body)
    capture = capture_vehicle_request(message_id, body)

    if _matches(normalized, _OPT_OUT):
        return Classification(INTENT_OPT_OUT, 0.99, vehicle_capture=capture)
    if capture.is_vehicle_request:
        confidence = 0.99 if capture.explicit_commission else 0.94
        return Classification(INTENT_VEHICLE_REQUEST, confidence, vehicle_capture=capture)
    if _matches(normalized, _OBJECTION_FEE):
        return Classification(INTENT_OBJECTION, 0.95, "OBJ-2", capture)
    if _matches(normalized, _OBJECTION_TRUST):
        return Classification(INTENT_OBJECTION, 0.90, "OBJ-4", capture)
    if _matches(normalized, _OBJECTION_TIMING):
        return Classification(INTENT_OBJECTION, 0.90, "OBJ-3", capture)
    if _matches(normalized, _OBJECTION_SOURCING):
        return Classification(INTENT_OBJECTION, 0.88, "OBJ-5", capture)
    if _matches(normalized, _NEGATIVE):
        return Classification(INTENT_NEGATIVE, 0.94, vehicle_capture=capture)
    if _matches(normalized, _CURIOSITY):
        return Classification(INTENT_CURIOSITY, 0.90, vehicle_capture=capture)
    if _matches(normalized, _POSITIVE):
        return Classification(INTENT_POSITIVE, 0.82, vehicle_capture=capture)
    return Classification(INTENT_UNKNOWN, 0.40, vehicle_capture=capture)


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


def ensure_primary_schema(db_path: str) -> None:
    """Add analyzer metadata without replacing the existing CRM schema."""
    ensure_state_columns(db_path)
    con = _connect(db_path)
    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS pending_replies (
                id TEXT PRIMARY KEY,
                dealer_id TEXT,
                dealer_name TEXT,
                inbound_msg_id TEXT,
                reply_text TEXT,
                reply_label TEXT,
                cialdini_trigger TEXT,
                approved INTEGER DEFAULT NULL,
                sent INTEGER DEFAULT 0,
                scheduled_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                event_type TEXT,
                dealer_id TEXT,
                payload TEXT,
                timestamp_it TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        pending_cols = _columns(con, "pending_replies")
        for name, sql_type in {
            "template_id": "TEXT",
            "intent": "TEXT",
            "auto_approved": "INTEGER DEFAULT 0",
            "guard_reason": "TEXT",
        }.items():
            if name not in pending_cols:
                con.execute(f'ALTER TABLE pending_replies ADD COLUMN "{name}" {sql_type}')

        msg_cols = _columns(con, "messages")
        for name, sql_type in {
            "classifier_intent": "TEXT",
            "classifier_confidence": "REAL",
        }.items():
            if msg_cols and name not in msg_cols:
                con.execute(f'ALTER TABLE messages ADD COLUMN "{name}" {sql_type}')
        con.commit()
    finally:
        con.close()


def ensure_bridge_schema(bridge_path: str) -> None:
    """Migrate bridge rows so the transport always has an exact template ID."""
    if not bridge_path:
        return
    Path(bridge_path).parent.mkdir(parents=True, exist_ok=True)
    con = _connect(bridge_path)
    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS bridge_outbound (
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
            );
            """
        )
        columns = _columns(con, "bridge_outbound")
        for name, sql_type in {
            "template_id": "TEXT",
            "inbound_msg_id": "TEXT",
            "guard_status": "TEXT",
            "guard_reason": "TEXT",
        }.items():
            if name not in columns:
                con.execute(f'ALTER TABLE bridge_outbound ADD COLUMN "{name}" {sql_type}')
        con.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS uq_s292_outbound_inbound_template
               ON bridge_outbound(deal_id, target_phone, inbound_msg_id, template_id)
               WHERE inbound_msg_id IS NOT NULL AND template_id IS NOT NULL"""
        )
        con.commit()
    finally:
        con.close()


def _audit(db_path: str, dealer_id: str, event_type: str, payload: Mapping[str, Any]) -> None:
    event_id = "audit_" + hashlib.sha256(
        f"{dealer_id}|{event_type}|{json.dumps(payload, sort_keys=True, default=str)}".encode("utf-8")
    ).hexdigest()[:24]
    con = _connect(db_path)
    try:
        con.execute(
            """INSERT OR IGNORE INTO audit_log
               (id, event_type, dealer_id, payload, timestamp_it)
               VALUES (?, ?, ?, ?, ?)""",
            [
                event_id,
                event_type,
                dealer_id,
                json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
                datetime.now(timezone.utc).isoformat(),
            ],
        )
        con.commit()
    finally:
        con.close()


def _update_message_classification(
    db_path: str,
    message_id: str,
    classification: Classification,
) -> None:
    con = _connect(db_path)
    try:
        columns = _columns(con, "messages")
        if {"id", "classifier_intent", "classifier_confidence"}.issubset(columns):
            con.execute(
                """UPDATE messages
                   SET classifier_intent = ?, classifier_confidence = ?, processed = 1
                   WHERE id = ?""",
                [classification.intent, classification.confidence, message_id],
            )
        con.commit()
    finally:
        con.close()


def _dealer_phone(db_path: str, dealer_id: str) -> Optional[str]:
    con = _connect(db_path)
    try:
        columns = _columns(con, "conversations")
        if not {"dealer_id", "phone_number"}.issubset(columns):
            return None
        row = con.execute(
            "SELECT phone_number FROM conversations WHERE dealer_id = ? LIMIT 1",
            [dealer_id],
        ).fetchone()
        if not row or not row[0]:
            return None
        digits = re.sub(r"\D", "", str(row[0]))
        return digits or None
    finally:
        con.close()


def _reply_data(
    *,
    classification: Classification,
    dealer_name: str,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "dealer_name": dealer_name,
        "source": "contatto pubblico della sua attività",
    }
    capture = classification.vehicle_capture
    if capture and capture.is_vehicle_request:
        data["request_summary"] = capture.summary or "richiesta veicolo"
        if capture.missing_for_search:
            readable = {
                "year_range": "anno/intervallo anni",
                "budget_max_eur": "budget massimo",
                "km_max": "chilometraggio massimo",
                "make_model": "marca/modello",
            }
            fields = [readable.get(item, item) for item in capture.missing_for_search]
            data["missing_question"] = "Per completare i criteri mi manca: " + ", ".join(fields) + "."
        else:
            data["missing_question"] = "I criteri principali risultano completi."
    return data


def _select_response(
    classification: Classification,
    state: str,
    dealer_name: str,
) -> tuple[Optional[str], str]:
    if classification.intent in {INTENT_UNKNOWN, INTENT_OPT_OUT}:
        return None, ""

    lookup_intent = classification.objection_code or classification.intent
    template_id = select_template(lookup_intent, state)

    # A generic positive response after the first engagement should continue
    # demand discovery instead of inventing a vehicle or a fee.
    if not template_id and classification.intent == INTENT_POSITIVE and state == "ENGAGED":
        template_id = "DEMAND_DISCOVERY_PROMPT"

    if not template_id:
        return None, ""
    message = fill_template(
        template_id,
        _reply_data(classification=classification, dealer_name=dealer_name),
    )
    return template_id, message


def _persist_pending(
    *,
    db_path: str,
    dealer_id: str,
    dealer_name: str,
    inbound_msg_id: str,
    classification: Classification,
    template_id: str,
    message: str,
    approved: Optional[int],
    guard_reason: str,
) -> str:
    reply_id = "reply_" + hashlib.sha256(
        f"{dealer_id}|{inbound_msg_id}|{template_id}|{message}".encode("utf-8")
    ).hexdigest()[:24]
    con = _connect(db_path)
    try:
        con.execute(
            """INSERT OR IGNORE INTO pending_replies
               (id, dealer_id, dealer_name, inbound_msg_id, reply_text,
                reply_label, approved, sent, scheduled_at, template_id,
                intent, auto_approved, guard_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, datetime('now'), ?, ?, ?, ?)""",
            [
                reply_id,
                dealer_id,
                dealer_name,
                inbound_msg_id,
                message,
                f"S292_{classification.intent}",
                approved,
                template_id,
                classification.intent,
                1 if approved == 1 else 0,
                guard_reason,
            ],
        )
        con.commit()
    finally:
        con.close()
    return reply_id


def _enqueue_bridge(
    *,
    bridge_path: str,
    dealer_id: str,
    phone: str,
    inbound_msg_id: str,
    state: str,
    template_id: str,
    message: str,
) -> tuple[bool, str]:
    if not bridge_path:
        return False, "BRIDGE_DB_PATH_NOT_CONFIGURED"
    ensure_bridge_schema(bridge_path)
    row_id = "out_" + hashlib.sha256(
        f"{dealer_id}|{phone}|{inbound_msg_id}|{template_id}".encode("utf-8")
    ).hexdigest()[:24]
    now = int(time.time())
    con = _connect(bridge_path)
    try:
        cur = con.execute(
            """INSERT OR IGNORE INTO bridge_outbound
               (id, deal_id, target_role, target_phone, template_phase,
                template_lang, body, state_at_send, created_ts, approved_ts,
                action_type, template_id, inbound_msg_id, guard_status, guard_reason)
               VALUES (?, ?, 'dealer', ?, ?, 'it', ?, ?, ?, ?, 'agent_auto',
                       ?, ?, 'PASS', 'pre_enqueue_guard_ok')""",
            [
                row_id,
                dealer_id,
                phone,
                template_id.lower(),
                message,
                state,
                now,
                now,
                template_id,
                inbound_msg_id,
            ],
        )
        con.commit()
        return cur.rowcount == 1, row_id
    finally:
        con.close()


def analyze_and_route(
    *,
    msg_id: str,
    msg_body: str,
    dealer_id: str,
    dealer_name: str,
    db_path: str,
    bridge_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Production transaction boundary for one inbound message/buffer."""
    ensure_primary_schema(db_path)
    classification = classify_message(msg_id, msg_body)
    _update_message_classification(db_path, msg_id, classification)

    before = get_dealer_state(db_path, dealer_id)
    if not before:
        result = {
            "ok": False,
            "reason": "DEALER_NOT_FOUND",
            "dealer_id": dealer_id,
            "classification": classification.to_dict(),
        }
        _audit(db_path, dealer_id, "ANALYZER_BLOCKED", result)
        return result

    if classification.intent == INTENT_OPT_OUT:
        update_state(db_path, dealer_id, "ARCHIVED")
        result = {
            "ok": True,
            "dealer_id": dealer_id,
            "classification": classification.to_dict(),
            "state": "ARCHIVED",
            "outbound": "NONE",
            "reason": "explicit_opt_out",
        }
        _audit(db_path, dealer_id, "DEALER_OPT_OUT", result)
        return result

    state_intent = (
        INTENT_OBJECTION
        if classification.intent == INTENT_OBJECTION
        else classification.intent
    )
    state = process_inbound(db_path, dealer_id, state_intent)

    mandate_recorded = False
    capture = classification.vehicle_capture
    if (
        classification.intent == INTENT_VEHICLE_REQUEST
        and capture is not None
        and capture.authorization_ready
    ):
        # An established conversation/referral is the credibility precondition;
        # the clear commission verb + original inbound message is the mandate.
        credibility = bool(
            str(before.get("conversation_state") or "COLD") != "COLD"
            or is_post_handoff(before)
        )
        evidence = capture.to_evidence(
            dealer_id=dealer_id,
            credibility_established=credibility,
        )
        if evidence.sourcing_authorized:
            record_verified_mandate(db_path, dealer_id, evidence)
            state = "MANDATE_CONFIRMED"
            mandate_recorded = True
        else:
            _audit(
                db_path,
                dealer_id,
                "MANDATE_NOT_AUTHORIZED",
                {
                    "evidence_id": evidence.evidence_id,
                    "credibility_established": evidence.credibility_established,
                    "authorization_ready": capture.authorization_ready,
                },
            )

    template_id, message = _select_response(
        classification,
        state,
        dealer_name,
    )
    if not template_id or not message:
        result = {
            "ok": True,
            "dealer_id": dealer_id,
            "classification": classification.to_dict(),
            "state": state,
            "mandate_recorded": mandate_recorded,
            "outbound": "NONE",
            "reason": "no_safe_template",
        }
        _audit(db_path, dealer_id, "ANALYZER_NO_OUTBOUND", result)
        return result

    guard = evaluate_outbound(
        db_path=db_path,
        dealer_id=dealer_id,
        template_id=template_id,
        message=message,
    )
    approved = 1 if guard.get("ok") else None
    reply_id = _persist_pending(
        db_path=db_path,
        dealer_id=dealer_id,
        dealer_name=dealer_name,
        inbound_msg_id=msg_id,
        classification=classification,
        template_id=template_id,
        message=message,
        approved=approved,
        guard_reason=str(guard.get("reason") or "UNKNOWN"),
    )

    queued = False
    bridge_row_id = None
    phone = _dealer_phone(db_path, dealer_id)
    if guard.get("ok") and phone:
        queued, bridge_row_id = _enqueue_bridge(
            bridge_path=bridge_path or os.environ.get("BRIDGE_DB_PATH", ""),
            dealer_id=dealer_id,
            phone=phone,
            inbound_msg_id=msg_id,
            state=state,
            template_id=template_id,
            message=message,
        )

    result = {
        "ok": bool(guard.get("ok")),
        "dealer_id": dealer_id,
        "classification": classification.to_dict(),
        "state": state,
        "mandate_recorded": mandate_recorded,
        "template_id": template_id,
        "reply_id": reply_id,
        "guard": guard,
        "bridge_queued": queued,
        "bridge_row_id": bridge_row_id,
        "outbound": "QUEUED" if queued else "PENDING",
    }
    _audit(db_path, dealer_id, "ANALYZER_DECISION", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARGOS S292 response analyzer")
    parser.add_argument("--msg-id", required=True)
    parser.add_argument("--msg-body", required=True)
    parser.add_argument("--dealer-id", required=True)
    parser.add_argument("--dealer-name", required=True)
    parser.add_argument("--persona", default="")  # accepted for legacy daemon CLI compatibility
    parser.add_argument("--step", default="")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--time-ctx", default="{}")
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--bridge-db-path", default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = analyze_and_route(
            msg_id=args.msg_id,
            msg_body=args.msg_body,
            dealer_id=args.dealer_id,
            dealer_name=args.dealer_name,
            db_path=args.db_path,
            bridge_path=args.bridge_db_path,
        )
    except Exception as exc:
        result = {
            "ok": False,
            "error": type(exc).__name__,
            "reason": str(exc),
            "dealer_id": args.dealer_id,
            "msg_id": args.msg_id,
        }
        try:
            _audit(args.db_path, args.dealer_id, "ANALYZER_EXCEPTION", result)
        except Exception:
            pass
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("ok") or result.get("outbound") in {"NONE", "PENDING"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
