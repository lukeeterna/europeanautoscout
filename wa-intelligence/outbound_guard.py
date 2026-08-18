#!/usr/bin/env python3
"""ARGOS pre-send guardrail.

Called by wa-daemon.js before every /send.  The order is deliberate:
conversation/state gate -> S292 business policy -> dedup -> legacy content
validator.  Any unavailable/corrupt state fails closed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from s292_outbound_policy import evaluate_outbound_policy
from state_machine import can_send, get_dealer_state, is_duplicate
from validator import validate


def evaluate(
    *,
    db_path: str,
    dealer_id: str,
    template_id: str,
    message: str,
) -> dict:
    """Pure-ish callable boundary used by CLI/tests; never sends a message."""
    ok, reason = can_send(db_path, dealer_id, template_id)
    if not ok:
        return {"ok": False, "reason": reason, "check": "can_send"}

    dealer = get_dealer_state(db_path, dealer_id)
    if not dealer:
        return {"ok": False, "reason": "DEALER_NOT_FOUND", "check": "state"}

    policy = evaluate_outbound_policy(
        dealer_state=dealer,
        template_id=template_id,
        message=message,
    )
    if not policy.ok:
        return policy.to_dict()

    if is_duplicate(db_path, dealer_id, message):
        return {"ok": False, "reason": "DUPLICATE_MESSAGE", "check": "dedup"}

    result = validate(message, template_id, {})
    if result.get("result") == "BLOCK":
        return {
            "ok": False,
            "reason": f"{result.get('check_failed', 'validator')}: {result.get('reason', 'blocked')}",
            "check": "validate",
        }

    return {"ok": True, "reason": "OK", "check": "all"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--dealer-id", required=True)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--message", required=True)
    args = parser.parse_args()
    try:
        result = evaluate(
            db_path=args.db_path,
            dealer_id=args.dealer_id,
            template_id=args.template_id,
            message=args.message,
        )
    except Exception as exc:
        result = {
            "ok": False,
            "reason": f"GUARD_ERROR: {type(exc).__name__}",
            "check": "guard_exception",
        }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
