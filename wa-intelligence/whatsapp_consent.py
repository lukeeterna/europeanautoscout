#!/usr/bin/env python3
"""Traceable WhatsApp opt-in evidence for ARGOS.

Platform/business-initiated WhatsApp outreach is never inferred from a public
phone number or from ARGOS' internal ``outreach_authorized`` flag.  A grant is
recorded only with an explicit source and evidence identifier; revocation clears
that authorization fail-closed.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Mapping


CONSENT_COLUMNS = {
    "whatsapp_opt_in": "INTEGER DEFAULT 0",
    "whatsapp_opt_in_at": "TEXT",
    "whatsapp_opt_in_source": "TEXT",
    "whatsapp_opt_in_evidence_id": "TEXT",
    "whatsapp_opt_out_at": "TEXT",
}


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    return con


def ensure_consent_columns(db_path: str) -> None:
    con = _connect(db_path)
    try:
        columns = {str(row[1]) for row in con.execute("PRAGMA table_info('conversations')").fetchall()}
        if not columns:
            raise RuntimeError("conversations table missing")
        for name, definition in CONSENT_COLUMNS.items():
            if name not in columns:
                con.execute(f'ALTER TABLE conversations ADD COLUMN "{name}" {definition}')
        con.commit()
    finally:
        con.close()


def consent_is_valid(dealer: Mapping[str, Any]) -> bool:
    return (
        int(dealer.get("whatsapp_opt_in") or 0) == 1
        and bool(str(dealer.get("whatsapp_opt_in_at") or "").strip())
        and bool(str(dealer.get("whatsapp_opt_in_source") or "").strip())
        and bool(str(dealer.get("whatsapp_opt_in_evidence_id") or "").strip())
        and not bool(str(dealer.get("whatsapp_opt_out_at") or "").strip())
    )


def grant_consent(
    *,
    db_path: str,
    dealer_id: str,
    source: str,
    evidence_id: str,
    granted_at: str | None = None,
) -> dict[str, Any]:
    source = str(source or "").strip()
    evidence_id = str(evidence_id or "").strip()
    dealer_id = str(dealer_id or "").strip()
    if not dealer_id or not source or not evidence_id:
        raise ValueError("dealer_id, source and evidence_id are required")
    ensure_consent_columns(db_path)
    timestamp = granted_at or datetime.now(timezone.utc).isoformat()
    con = _connect(db_path)
    try:
        result = con.execute(
            """UPDATE conversations
               SET whatsapp_opt_in=1,
                   whatsapp_opt_in_at=?,
                   whatsapp_opt_in_source=?,
                   whatsapp_opt_in_evidence_id=?,
                   whatsapp_opt_out_at=NULL
               WHERE dealer_id=?""",
            [timestamp, source, evidence_id, dealer_id],
        )
        if result.rowcount != 1:
            raise LookupError(f"dealer not found: {dealer_id}")
        con.commit()
    finally:
        con.close()
    return {
        "ok": True,
        "dealer_id": dealer_id,
        "whatsapp_opt_in": 1,
        "whatsapp_opt_in_at": timestamp,
        "source": source,
        "evidence_id": evidence_id,
    }


def revoke_consent(*, db_path: str, dealer_id: str, revoked_at: str | None = None) -> dict[str, Any]:
    dealer_id = str(dealer_id or "").strip()
    if not dealer_id:
        raise ValueError("dealer_id is required")
    ensure_consent_columns(db_path)
    timestamp = revoked_at or datetime.now(timezone.utc).isoformat()
    con = _connect(db_path)
    try:
        result = con.execute(
            """UPDATE conversations
               SET whatsapp_opt_in=0, whatsapp_opt_out_at=?
               WHERE dealer_id=?""",
            [timestamp, dealer_id],
        )
        if result.rowcount != 1:
            raise LookupError(f"dealer not found: {dealer_id}")
        con.commit()
    finally:
        con.close()
    return {"ok": True, "dealer_id": dealer_id, "whatsapp_opt_in": 0, "whatsapp_opt_out_at": timestamp}


def main() -> int:
    parser = argparse.ArgumentParser(description="Record or revoke traceable WhatsApp consent evidence")
    parser.add_argument("action", choices=("grant", "revoke"))
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--dealer-id", required=True)
    parser.add_argument("--source")
    parser.add_argument("--evidence-id")
    args = parser.parse_args()
    try:
        if args.action == "grant":
            result = grant_consent(
                db_path=args.db_path,
                dealer_id=args.dealer_id,
                source=str(args.source or ""),
                evidence_id=str(args.evidence_id or ""),
            )
        else:
            result = revoke_consent(db_path=args.db_path, dealer_id=args.dealer_id)
    except Exception as exc:
        result = {"ok": False, "error": type(exc).__name__, "reason": str(exc)}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
