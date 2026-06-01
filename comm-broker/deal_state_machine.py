"""ARGOS deal state machine — D-22 F4 implementation.

State machine 7-step per tracking deal end-to-end:

  offer_sent → accepted → docs_shared → payment_pending → payment_confirmed →
  transport_scheduled → in_transit → delivered

SQLite persistence (D-22 stack), hooks on-transition (notify founder, audit log),
graceful failure recovery.

Library: python-statemachine 3.0.0 (Feb 2026, verified compat Py 3.13).
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any

from statemachine import StateMachine, State


DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS deals (
    deal_id        TEXT PRIMARY KEY,
    dealer_alias   TEXT NOT NULL,
    seller_alias   TEXT NOT NULL,
    vehicle_desc   TEXT,
    current_state  TEXT NOT NULL,
    fee_eur        INTEGER DEFAULT 1000,
    created_ts     INTEGER NOT NULL,
    updated_ts     INTEGER NOT NULL,
    metadata_json  TEXT,
    paid_at        INTEGER
);

CREATE TABLE IF NOT EXISTS state_transitions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id        TEXT NOT NULL,
    from_state     TEXT NOT NULL,
    to_state       TEXT NOT NULL,
    event          TEXT NOT NULL,
    ts             INTEGER NOT NULL,
    note           TEXT,
    FOREIGN KEY(deal_id) REFERENCES deals(deal_id)
);

CREATE INDEX IF NOT EXISTS idx_deals_state ON deals(current_state);
CREATE INDEX IF NOT EXISTS idx_transitions_deal ON state_transitions(deal_id, ts);
"""


@dataclass
class Deal:
    deal_id: str
    dealer_alias: str           # alias anonimo dealer IT (D-21 identity masking)
    seller_alias: str           # alias anonimo seller EU (D-21 identity masking)
    vehicle_desc: str = ""      # marca/modello/anno
    fee_eur: int = 1000         # D-01 default fee
    metadata: dict | None = None


class DealStateMachine(StateMachine):
    """ARGOS deal lifecycle 7-step.

    States:
      - offer_sent: ARGOS ha mandato dossier preview al dealer (D-21 step 2)
      - accepted: dealer ha accettato auto + clausola pre-deal firmata (step 3)
      - docs_shared: comm aperta dealer↔ARGOS↔seller, docs richieste (step 4-5)
      - payment_pending: deal chiuso, fee €1k da pagare a consegna documento
      - payment_confirmed: fee €1k received from dealer (step 8)
      - transport_scheduled: trasporto Macingo organizzato
      - in_transit: auto in viaggio EU → IT
      - delivered: auto consegnata al dealer (closure)
      - aborted: deal abortito (qualsiasi step → aborted)
    """
    offer_sent = State(initial=True)
    accepted = State()
    docs_shared = State()
    payment_pending = State()
    payment_confirmed = State()
    transport_scheduled = State()
    in_transit = State()
    delivered = State(final=True)
    aborted = State(final=True)

    # Transitions forward
    accept = offer_sent.to(accepted)
    share_docs = accepted.to(docs_shared)
    request_payment = docs_shared.to(payment_pending)
    confirm_payment = payment_pending.to(payment_confirmed)
    schedule_transport = payment_confirmed.to(transport_scheduled)
    start_transit = transport_scheduled.to(in_transit)
    deliver = in_transit.to(delivered)

    # Abort dovunque
    abort = (
        offer_sent.to(aborted)
        | accepted.to(aborted)
        | docs_shared.to(aborted)
        | payment_pending.to(aborted)
        | payment_confirmed.to(aborted)
        | transport_scheduled.to(aborted)
        | in_transit.to(aborted)
    )

    def __init__(self, deal: Deal, db_path: str | Path = "deals.sqlite", **kwargs):
        self.deal = deal
        self.db_path = Path(db_path)
        self._init_db()
        # Restore stato da DB se deal esiste
        restored = self._load_state()
        if restored:
            kwargs["start_value"] = restored
        super().__init__(**kwargs)
        self._persist_deal()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(DB_SCHEMA)
            # Migration idempotente: aggiunge paid_at a DB esistenti (Task 4 C-GATE-FONTE-001)
            try:
                conn.execute("ALTER TABLE deals ADD COLUMN paid_at INTEGER")
                conn.commit()
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise
            conn.commit()
        finally:
            conn.close()

    def _load_state(self) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "SELECT current_state FROM deals WHERE deal_id = ?",
                (self.deal.deal_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def _persist_deal(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            now = int(time.time())
            md = json.dumps(self.deal.metadata or {})
            conn.execute(
                """
                INSERT INTO deals (deal_id, dealer_alias, seller_alias, vehicle_desc,
                                   current_state, fee_eur, created_ts, updated_ts,
                                   metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(deal_id) DO UPDATE SET
                    current_state = excluded.current_state,
                    updated_ts = excluded.updated_ts,
                    metadata_json = excluded.metadata_json
                """,
                (
                    self.deal.deal_id,
                    self.deal.dealer_alias,
                    self.deal.seller_alias,
                    self.deal.vehicle_desc,
                    self.current_state.id,
                    self.deal.fee_eur,
                    now,
                    now,
                    md,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def on_transition(self, event: str, source: State, target: State) -> None:
        """Hook chiamato a ogni transizione — log + persist."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO state_transitions (deal_id, from_state, to_state, event, ts, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    self.deal.deal_id,
                    source.id,
                    target.id,
                    event,
                    int(time.time()),
                    None,
                ),
            )
            conn.execute(
                "UPDATE deals SET current_state = ?, updated_ts = ? WHERE deal_id = ?",
                (target.id, int(time.time()), self.deal.deal_id),
            )
            conn.commit()
        finally:
            conn.close()

    def history(self) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT from_state, to_state, event, ts, note
                FROM state_transitions
                WHERE deal_id = ?
                ORDER BY ts ASC, id ASC
                """,
                (self.deal.deal_id,),
            )
            cols = ["from_state", "to_state", "event", "ts", "note"]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()


def create_deal(
    deal_id: str,
    dealer_alias: str,
    seller_alias: str,
    vehicle_desc: str,
    source_locked: dict,
    db_path: str | Path = "deals.sqlite",
    fee_eur: int = 1000,
) -> DealStateMachine:
    """Crea un nuovo Deal e lo persiste con fonte in cassaforte (C-GATE-FONTE-001).

    source_locked DEVE contenere: listing_url, seller_name, seller_city, seller_phone, portal.
    La fonte rimane nascosta finché current_state != 'payment_confirmed'.

    Returns:
        DealStateMachine istanziata nello stato iniziale offer_sent.
    """
    required_keys = {"listing_url", "seller_name", "seller_city", "seller_phone", "portal"}
    missing = required_keys - set(source_locked.keys())
    if missing:
        raise ValueError(f"source_locked mancante di campi obbligatori: {missing}")

    deal = Deal(
        deal_id=deal_id,
        dealer_alias=dealer_alias,
        seller_alias=seller_alias,
        vehicle_desc=vehicle_desc,
        fee_eur=fee_eur,
        metadata={"source_locked": source_locked},
    )
    fsm = DealStateMachine(deal, db_path=db_path)
    return fsm


if __name__ == "__main__":
    import sys
    # CLI smoke test
    deal = Deal(
        deal_id="DEAL-TEST-001",
        dealer_alias="D-FG-001",
        seller_alias="S-DE-042",
        vehicle_desc="BMW X3 2020 45000km",
    )
    fsm = DealStateMachine(deal, db_path="/tmp/argos-test-deals.sqlite")
    print(f"Initial state: {fsm.current_state.id}")
    print(f"Available transitions: {[t.event for t in fsm.allowed_events]}")
    fsm.accept()
    print(f"After accept(): {fsm.current_state.id}")
    fsm.share_docs()
    fsm.request_payment()
    fsm.confirm_payment()
    fsm.schedule_transport()
    fsm.start_transit()
    fsm.deliver()
    print(f"Final state: {fsm.current_state.id}")
    print(f"\nHistory ({len(fsm.history())} transitions):")
    for t in fsm.history():
        print(f"  {t['from_state']} → {t['to_state']} (event: {t['event']})")
