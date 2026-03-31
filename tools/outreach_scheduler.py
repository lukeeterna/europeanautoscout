#!/usr/bin/env python3
"""
outreach_scheduler.py — ARGOS Dealer Outreach Scheduler
Checks CRM for pending follow-ups and sends Telegram alerts.

Run via cron every hour on iMac:
  0 * * * * cd ~/Documents/app-antigravity-auto && python3 tools/outreach_scheduler.py

Reads dealer_network.sqlite, checks next_action_at, sends Telegram notifications.
"""

import os
import sys
import sqlite3
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

# Config
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "dealer_network.sqlite")
STATE_FILE = "/tmp/argos-outreach-scheduler-state.json"

# Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_IDS", "931063621")

# Load token from .env if not in environment
if not TELEGRAM_TOKEN:
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    TELEGRAM_TOKEN = line.strip().split("=", 1)[1]

# Sequenza touchpoint completa
SEQUENCE = {
    "DAY3_FOLLOWUP": {
        "label": "Day 3 — Foto HD + secondo veicolo",
        "next": "DAY7_FOLLOWUP",
        "next_days": 4,
    },
    "DAY7_FOLLOWUP": {
        "label": "Day 7 — FOMO lieve / uscita dignitosa",
        "next": "DAY10_VOCALE",
        "next_days": 3,
    },
    "DAY10_VOCALE": {
        "label": "Day 10 — Vocale 20 sec",
        "next": "DAY14_REFERRAL",
        "next_days": 4,
    },
    "DAY14_REFERRAL": {
        "label": "Day 14 — Referral o case study",
        "next": "DAY21_BREAKUP",
        "next_days": 7,
    },
    "DAY21_BREAKUP": {
        "label": "Day 21 — Break-up gentile",
        "next": "DAY30_CALL",
        "next_days": 9,
    },
    "DAY30_CALL": {
        "label": "Day 30 — Telefonata o visita fisica",
        "next": None,
        "next_days": 0,
    },
}


def send_telegram(msg: str):
    if not TELEGRAM_TOKEN:
        print(f"[WARN] No Telegram token — would send: {msg}")
        return
    try:
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data,
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"[TG] Sent: {msg[:80]}...")
    except Exception as e:
        print(f"[ERROR] Telegram failed: {e}")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def check_due_actions():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] DB not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    now = datetime.now()

    # Find dealers with pending actions due today or overdue
    rows = conn.execute("""
        SELECT dealer_id, name, wa, pipeline_status, tier, archetype,
               next_action_at, next_action_type, titolare_name
        FROM dealers
        WHERE next_action_at IS NOT NULL
          AND next_action_at <= ?
          AND pipeline_status NOT IN ('CLOSED', 'DEAD', 'CONVERTED')
        ORDER BY next_action_at ASC
    """, [now.isoformat()]).fetchall()

    state = load_state()
    actions_due = []

    for row in rows:
        dealer_id = row["dealer_id"]
        action_type = row["next_action_type"]
        state_key = f"{dealer_id}_{action_type}"

        # Skip if already notified today
        if state.get(state_key) == now.strftime("%Y-%m-%d"):
            continue

        seq_info = SEQUENCE.get(action_type, {})
        label = seq_info.get("label", action_type)
        titolare = row["titolare_name"] or row["name"]
        archetype = row["archetype"] or "?"

        actions_due.append({
            "dealer_id": dealer_id,
            "name": row["name"],
            "titolare": titolare,
            "wa": row["wa"],
            "action": action_type,
            "label": label,
            "archetype": archetype,
            "tier": row["tier"],
        })

        # Mark as notified
        state[state_key] = now.strftime("%Y-%m-%d")

    if actions_due:
        # Build summary message
        lines = ["<b>ARGOS Outreach Scheduler</b>\n"]
        for a in actions_due:
            lines.append(
                f"  {a['name']} ({a['archetype']})\n"
                f"  <b>{a['label']}</b>\n"
                f"  WA: {a['wa']}\n"
            )
        lines.append(f"\n{len(actions_due)} azioni da fare ORA.")
        send_telegram("\n".join(lines))

        # Advance each dealer to next sequence step (prevents re-sending)
        for a in actions_due:
            seq_info = SEQUENCE.get(a["action"], {})
            next_action = seq_info.get("next")
            next_days = seq_info.get("next_days", 7)
            if next_action:
                next_at = (now + timedelta(days=next_days)).replace(
                    hour=9, minute=0, second=0, microsecond=0
                ).isoformat()
                conn.execute("""
                    UPDATE dealers SET next_action_type = ?, next_action_at = ?
                    WHERE dealer_id = ?
                """, [next_action, next_at, a["dealer_id"]])
                print(f"  [{a['dealer_id']}] Advanced: {a['action']} → {next_action} at {next_at}")
            else:
                # End of sequence — mark as COLD
                conn.execute("""
                    UPDATE dealers SET next_action_type = NULL, next_action_at = NULL,
                    pipeline_status = 'COLD'
                    WHERE dealer_id = ?
                """, [a["dealer_id"]])
                print(f"  [{a['dealer_id']}] Sequence complete → COLD")
        conn.commit()

        save_state(state)
        print(f"[OK] {len(actions_due)} actions due, notification sent, dealers advanced")
    else:
        print(f"[OK] No actions due right now")

    # Also report upcoming (next 24h)
    upcoming = conn.execute("""
        SELECT name, next_action_type, next_action_at
        FROM dealers
        WHERE next_action_at > ? AND next_action_at <= ?
          AND pipeline_status NOT IN ('CLOSED', 'DEAD', 'CONVERTED')
    """, [now.isoformat(), (now + timedelta(hours=24)).isoformat()]).fetchall()

    if upcoming:
        print(f"[INFO] {len(upcoming)} actions coming in next 24h:")
        for r in upcoming:
            print(f"  - {r['name']}: {r['next_action_type']} at {r['next_action_at']}")

    conn.close()


if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] ARGOS Outreach Scheduler run")
    check_due_actions()
