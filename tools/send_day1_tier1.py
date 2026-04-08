#!/usr/bin/env python3
"""
send_day1_tier1.py — Primo contatto V3 (CHI-PERCHE'-CHIEDI) a Enzo Car e Dream Car
Eseguire SOLO DOPO: GBP live + Facebook page creata + LinkedIn già OK

REGOLA: Day 1 = presentazione + domanda. ZERO veicoli, ZERO numeri, ZERO fee.
Il veicolo arriva nel Day 3 (dopo che il dealer sa chi sei).

Uso: python3 tools/send_day1_tier1.py [--dry-run]
"""

import os
import sys
import json
import time
import sqlite3
import urllib.request
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WA_DAEMON = "http://192.168.1.2:9191"
DB_PATH = os.path.join(PROJECT_ROOT, "dealer_network.sqlite")

MESSAGES = {
    "enzo_car_fg": {
        "wa": "393398835656",
        "name": "Enzo Car",
        "titolare": "Enzo Cordisco",
        "archetype": "NARCISO",
        "text": (
            "Buongiorno Enzo, sono Luca Ferretti — cerco auto premium "
            "in Germania per concessionari del Sud.\n\n"
            "Ho visto il suo stock, tratta anche Porsche e Mercedes. "
            "Le capita di cercare questi modelli all'estero?\n\n"
            "Luca"
        ),
    },
    # Dream Car (Cerignola) ESCLUSO su richiesta founder
}


def check_daemon():
    try:
        resp = urllib.request.urlopen(f"{WA_DAEMON}/status", timeout=5)
        data = json.loads(resp.read())
        if data.get("wa_status") != "connected":
            print("[ERROR] WA not connected")
            return False
        remaining = data.get("daily_remaining", 0)
        if remaining < 2:
            print(f"[WARN] Only {remaining} messages remaining today")
            return False
        print(f"[OK] WA daemon connected, {remaining} remaining")
        return True
    except Exception as e:
        print(f"[ERROR] Daemon unreachable: {e}")
        return False


def send_message(wa_number, text):
    payload = {"to": wa_number, "text": text}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{WA_DAEMON}/send",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result.get("status") == "sent"
    except Exception as e:
        print(f"[ERROR] Send failed: {e}")
        return False


def update_crm(dealer_id, wa_number):
    """Update CRM after sending Day 1."""
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now()
    day3_at = (now + timedelta(days=2)).replace(hour=9, minute=0, second=0).isoformat()

    conn.execute("""
        UPDATE dealers SET
            pipeline_status = 'CONTACTED',
            first_contact_at = ?,
            last_contact_at = ?,
            next_action_type = 'DAY3_FOLLOWUP',
            next_action_at = ?,
            updated_at = ?
        WHERE dealer_id = ?
    """, [now.isoformat(), now.isoformat(), day3_at, now.isoformat(), dealer_id])
    conn.commit()
    conn.close()
    print(f"  [CRM] Updated {dealer_id} → CONTACTED, Day 3 at {day3_at}")


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("ARGOS — Day 1 V3 TIER1 (Enzo Car + Dream Car)")
    print("Framework: CHI-PERCHE'-CHIEDI")
    print("=" * 60)

    if not dry_run:
        if not check_daemon():
            print("\n[ABORT] Fix daemon issues before sending.")
            sys.exit(1)

    for dealer_id, msg in MESSAGES.items():
        print(f"\n--- {msg['name']} ({msg['titolare']}) [{msg['archetype']}] ---")
        print(f"  WA: {msg['wa']}")
        print(f"  Messaggio ({len(msg['text'])} chars):")
        for line in msg["text"].split("\n"):
            print(f"    {line}")

        if dry_run:
            print("  [DRY RUN] Would send message")
        else:
            ok = send_message(msg["wa"], msg["text"])
            if ok:
                print(f"  [SENT] Day 1 message")
                update_crm(dealer_id, msg["wa"])
                time.sleep(8)  # Anti-ban delay between dealers
            else:
                print(f"  [FAIL] Message not sent")

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN complete. Run without --dry-run to send.")
    else:
        print("Day 1 outreach complete. Day 3 scheduled automatically.")


if __name__ == "__main__":
    main()
