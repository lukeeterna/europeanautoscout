#!/usr/bin/env python3
"""
state_machine.py — ARGOS™ Conversation State Machine
Blueprint approvato S105 | Template-first architecture

Stati: COLD → CONTACTED → ENGAGED → INTERESTED → CONVERTING → CLOSED_WON/CLOSED_LOST/ARCHIVED
Ogni stato ha regole su: template ammessi, max outbound, richiesta inbound prima di continuare.
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta

# ── State definitions ──────────────────────────────────────
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
            "IDENTITY_RESPONSE", "VEHICLE_PROPOSAL",
            "OBJ_1_NO_INTEREST", "OBJ_2_FEE", "OBJ_3_TRUST",
            "OBJ_4_TIMING", "OBJ_5_SOURCING",
        ],
        "max_outbound": None,  # no cap, ma requires_inbound
        "requires_inbound": True,
    },
    "INTERESTED": {
        "allowed_templates": ["VEHICLE_PROPOSAL", "VEHICLE_DETAILS", "CLOSING_PUSH"],
        "max_outbound": None,
        "requires_inbound": True,
    },
    "CONVERTING": {
        "allowed_templates": ["VEHICLE_DETAILS", "CLOSING_PUSH", "OBJ_2_FEE"],
        "max_outbound": None,
        "requires_inbound": True,
    },
    "ARCHIVED": {
        "allowed_templates": [],
        "max_outbound": 0,
        "requires_inbound": False,
    },
}

# ── Transition rules ──────────────────────────────────────
# (current_state, intent) → new_state
TRANSITIONS = {
    ("COLD", "OUTBOUND_SENT"):    "CONTACTED",
    ("CONTACTED", "POSITIVE"):    "ENGAGED",
    ("CONTACTED", "CURIOSITY"):   "ENGAGED",
    ("CONTACTED", "OBJECTION"):   "ENGAGED",
    ("CONTACTED", "NEGATIVE"):    "CONTACTED",  # resta, conta verso archive
    ("CONTACTED", "VEHICLE_REQUEST"): "INTERESTED",
    ("ENGAGED", "POSITIVE"):      "INTERESTED",
    ("ENGAGED", "VEHICLE_REQUEST"): "INTERESTED",
    ("ENGAGED", "CURIOSITY"):     "ENGAGED",
    ("ENGAGED", "OBJECTION"):     "ENGAGED",
    ("ENGAGED", "NEGATIVE"):      "ENGAGED",  # 1 negative non archivia
    ("INTERESTED", "POSITIVE"):   "CONVERTING",
    ("INTERESTED", "VEHICLE_REQUEST"): "CONVERTING",
    ("INTERESTED", "NEGATIVE"):   "ENGAGED",   # torna indietro, non archivia
    ("INTERESTED", "CURIOSITY"):  "INTERESTED",
}


def get_transition(current_state: str, intent: str) -> str:
    """Determina il nuovo stato. Se non c'e' transizione, resta nello stato attuale."""
    return TRANSITIONS.get((current_state, intent), current_state)


# ── DB operations ──────────────────────────────────────────
def ensure_state_columns(db_path: str):
    """Aggiunge colonne state machine se non esistono."""
    con = sqlite3.connect(db_path, timeout=10)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=10000')

    migrations = [
        "ALTER TABLE conversations ADD COLUMN conversation_state TEXT DEFAULT 'COLD'",
        "ALTER TABLE conversations ADD COLUMN outbound_count INTEGER DEFAULT 0",
        "ALTER TABLE conversations ADD COLUMN inbound_count INTEGER DEFAULT 0",
        "ALTER TABLE conversations ADD COLUMN last_inbound_at TEXT",
        "ALTER TABLE conversations ADD COLUMN state_updated_at TEXT",
        "ALTER TABLE conversations ADD COLUMN escalation_flag INTEGER DEFAULT 0",
    ]
    for sql in migrations:
        try:
            con.execute(sql)
        except sqlite3.OperationalError:
            pass  # column already exists
    con.commit()
    con.close()


def get_dealer_state(db_path: str, dealer_id: str) -> dict:
    """Legge stato corrente del dealer."""
    con = sqlite3.connect(db_path, timeout=10)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT * FROM conversations WHERE dealer_id = ?", [dealer_id]
    ).fetchone()
    con.close()
    if not row:
        return {}
    return dict(row)


def update_state(db_path: str, dealer_id: str, new_state: str):
    """Aggiorna lo stato conversazione."""
    con = sqlite3.connect(db_path, timeout=10)
    con.execute(
        """UPDATE conversations
           SET conversation_state = ?, state_updated_at = datetime('now')
           WHERE dealer_id = ?""",
        [new_state, dealer_id]
    )
    con.commit()
    con.close()


def increment_outbound(db_path: str, dealer_id: str):
    """Incrementa contatore outbound dopo invio."""
    con = sqlite3.connect(db_path, timeout=10)
    con.execute(
        "UPDATE conversations SET outbound_count = COALESCE(outbound_count, 0) + 1 WHERE dealer_id = ?",
        [dealer_id]
    )
    con.commit()
    con.close()


def record_inbound(db_path: str, dealer_id: str):
    """Registra messaggio inbound e aggiorna contatore."""
    con = sqlite3.connect(db_path, timeout=10)
    con.execute(
        """UPDATE conversations
           SET inbound_count = COALESCE(inbound_count, 0) + 1,
               last_inbound_at = datetime('now')
           WHERE dealer_id = ?""",
        [dealer_id]
    )
    con.commit()
    con.close()


# ── Pre-send guard ─────────────────────────────────────────
def can_send(db_path: str, dealer_id: str, template_id: str) -> tuple:
    """Guardrail pre-invio. Returns (ok: bool, reason: str)."""
    dealer = get_dealer_state(db_path, dealer_id)
    if not dealer:
        return False, "DEALER_NOT_FOUND"

    state = dealer.get('conversation_state') or 'COLD'
    rules = STATES.get(state)
    if not rules:
        return False, f"UNKNOWN_STATE: {state}"

    # Check 1: template ammesso per questo stato
    if template_id not in rules["allowed_templates"]:
        return False, f"TEMPLATE_NOT_ALLOWED: {template_id} in state {state}"

    # Check 2: cap outbound
    max_out = rules["max_outbound"]
    current_out = dealer.get('outbound_count') or 0
    if max_out is not None and current_out >= max_out:
        return False, f"CAP_REACHED: {current_out}/{max_out} in state {state}"

    # Check 3: richiede inbound prima di continuare
    if rules["requires_inbound"]:
        inbound_count = dealer.get('inbound_count') or 0
        if inbound_count == 0:
            return False, f"REQUIRES_INBOUND: state {state} needs dealer response first"
        # Dopo ogni nostro outbound, serve un nuovo inbound
        if current_out > 0 and current_out >= inbound_count:
            return False, f"WAIT_FOR_INBOUND: {current_out} out >= {inbound_count} in"

    # Check 4: stato archiviato
    if state == "ARCHIVED":
        return False, "DEALER_ARCHIVED"

    return True, "OK"


# ── Dedup ──────────────────────────────────────────────────
def is_duplicate(db_path: str, dealer_id: str, message_text: str, hours: int = 24) -> bool:
    """Controlla se un messaggio simile e' gia' stato inviato nelle ultime N ore."""
    msg_hash = hashlib.md5(message_text.strip().lower().encode()).hexdigest()
    con = sqlite3.connect(db_path, timeout=10)
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    row = con.execute(
        """SELECT COUNT(*) FROM messages
           WHERE dealer_id = ? AND direction = 'OUTBOUND'
           AND created_at > ?""",
        [dealer_id, cutoff]
    ).fetchone()
    # Check hash in recent outbound messages
    recent = con.execute(
        """SELECT body FROM messages
           WHERE dealer_id = ? AND direction = 'OUTBOUND'
           AND created_at > ?
           ORDER BY created_at DESC LIMIT 10""",
        [dealer_id, cutoff]
    ).fetchall()
    con.close()

    for (body,) in recent:
        if body and hashlib.md5(body.strip().lower().encode()).hexdigest() == msg_hash:
            return True
    return False


# ── Process inbound (chiamato dal daemon) ──────────────────
def process_inbound(db_path: str, dealer_id: str, intent: str) -> str:
    """Processa messaggio inbound: aggiorna contatore + transizione stato.
    Ritorna il nuovo stato."""
    record_inbound(db_path, dealer_id)
    dealer = get_dealer_state(db_path, dealer_id)
    current_state = dealer.get('conversation_state') or 'COLD'
    new_state = get_transition(current_state, intent)

    # Regola speciale: 2+ NEGATIVE consecutivi in ENGAGED → ARCHIVED
    if intent == 'NEGATIVE' and current_state == 'ENGAGED':
        # Conta NEGATIVE recenti
        con = sqlite3.connect(db_path, timeout=10)
        neg_count = con.execute(
            """SELECT COUNT(*) FROM messages
               WHERE dealer_id = ? AND direction = 'INBOUND'
               AND body IS NOT NULL
               ORDER BY created_at DESC LIMIT 3""",
            [dealer_id]
        ).fetchone()[0]
        con.close()
        # Semplificato: se gia' in ENGAGED e riceve NEGATIVE, resta.
        # Se riceve 2° NEGATIVE → ARCHIVED (da implementare con tracking)

    if new_state != current_state:
        update_state(db_path, dealer_id, new_state)

    return new_state


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        db = sys.argv[1]
        ensure_state_columns(db)
        print(f'State machine columns ensured on {db}')
    else:
        print('Usage: python state_machine.py <db_path>')
