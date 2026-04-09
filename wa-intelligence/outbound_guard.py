#!/usr/bin/env python3
"""
outbound_guard.py — ARGOS Pre-Send Guardrail
Called by wa-daemon.js BEFORE every /send to enforce state machine + validation.

Usage:
    python3 outbound_guard.py --db-path DB --dealer-id ID --template-id TPL --message "text"

Returns JSON to stdout:
    {"ok": true, "reason": "OK"}
    {"ok": false, "reason": "CAP_REACHED: 1/1 in state COLD", "check": "can_send"}
    {"ok": false, "reason": "FEE_LEAK: ...", "check": "validate"}
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state_machine import can_send, is_duplicate
from validator import validate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-path', required=True)
    parser.add_argument('--dealer-id', required=True)
    parser.add_argument('--template-id', required=True)
    parser.add_argument('--message', required=True)
    args = parser.parse_args()

    # 1. State machine guard: can we send this template to this dealer?
    ok, reason = can_send(args.db_path, args.dealer_id, args.template_id)
    if not ok:
        print(json.dumps({"ok": False, "reason": reason, "check": "can_send"}))
        return

    # 2. Dedup check
    if is_duplicate(args.db_path, args.dealer_id, args.message):
        print(json.dumps({"ok": False, "reason": "DUPLICATE_MESSAGE", "check": "dedup"}))
        return

    # 3. Validator: content safety
    result = validate(args.message, args.template_id, {})
    if result["result"] == "BLOCK":
        print(json.dumps({
            "ok": False,
            "reason": f"{result['check_failed']}: {result['reason']}",
            "check": "validate"
        }))
        return

    print(json.dumps({"ok": True, "reason": "OK"}))


if __name__ == '__main__':
    main()
