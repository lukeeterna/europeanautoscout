#!/usr/bin/env python3
"""
post_send_update.py — ARGOS Post-Send State Updater
Called by wa-daemon.js AFTER successful /send to update state machine.

Usage:
    python3 post_send_update.py --db-path DB --dealer-id ID --template-id TPL

Updates: increment_outbound + state transition (COLD→CONTACTED on DAY1).
Returns JSON to stdout:
    {"ok": true, "new_state": "CONTACTED", "outbound_count": 1}
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state_machine import (
    get_dealer_state, increment_outbound, get_transition,
    update_state, ensure_state_columns
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-path', required=True)
    parser.add_argument('--dealer-id', required=True)
    parser.add_argument('--template-id', required=True)
    args = parser.parse_args()

    ensure_state_columns(args.db_path)

    # 1. Increment outbound counter
    increment_outbound(args.db_path, args.dealer_id)

    # 2. State transition for outbound
    dealer = get_dealer_state(args.db_path, args.dealer_id)
    current_state = dealer.get('conversation_state') or 'COLD'
    outbound_count = dealer.get('outbound_count') or 0  # already incremented by step 1

    # DAY1 templates trigger COLD → CONTACTED
    if args.template_id.startswith('DAY1') and current_state == 'COLD':
        new_state = get_transition('COLD', 'OUTBOUND_SENT')
        update_state(args.db_path, args.dealer_id, new_state)
    else:
        new_state = current_state

    print(json.dumps({
        "ok": True,
        "new_state": new_state,
        "outbound_count": outbound_count
    }))


if __name__ == '__main__':
    main()
