"""ARGOS comm-broker WA bridge — D-22 F1 integration.

Bridge layer tra wa-daemon esistente (whatsapp-web.js, PM2 managed) e comm-broker
state machine + templates. NON sostituisce wa-daemon. Si integra via SQLite shared.

Architettura (D-21 workflow communication-broker-garante):

  [Dealer IT WA] ↔ wa-daemon.js (whatsapp-web.js) ↔ argos.db (messages, conversations)
                                                            ↑
                                                   [wa_bridge.py]
                                                            ↓
                                                   deal_state_machine + templates
                                                            ↓
                                                   bridge_outbound_queue → wa-daemon polls
                                                            ↓
  [Seller EU WA] ↔ wa-daemon (stesso brand Luca Ferretti +39)

MVP S167: bridge isolato, schema interface chiaro. Integration concreta con
wa-daemon outbound_log esistente → S168 (dopo Luke verifica bridge logic).

Vincoli operativi:
- HITL-friendly (D-07): bridge produce candidate, NON auto-send
- Single brand identity Luca Ferretti +39 328 1536308 (D-04)
- Identity masking bilaterale (D-21 step 4): dealer non vede seller, seller non vede dealer
- Stesso WA business account contatta sia dealer IT che seller EU
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deal_state_machine import Deal, DealStateMachine
from templates.templates_loader import render as render_template


logger = logging.getLogger("argos.wa_bridge")


BRIDGE_SCHEMA = """
-- Bridge inbound queue: messaggi WA in arrivo da wa-daemon, pending bridge processing
CREATE TABLE IF NOT EXISTS bridge_inbound (
    msg_id         TEXT PRIMARY KEY,
    party_role     TEXT NOT NULL CHECK(party_role IN ('dealer', 'seller')),
    party_phone    TEXT NOT NULL,
    party_alias    TEXT,
    body           TEXT NOT NULL,
    received_ts    INTEGER NOT NULL,
    processed_ts   INTEGER,
    deal_id        TEXT,
    intent         TEXT,
    sentiment      TEXT
);

-- Bridge outbound queue: messaggi candidati da bridge, pending HITL approval + wa-daemon send
-- S168 wire-up: wa_msg_id audit trail link a WA message ID reale post-sendMessage
CREATE TABLE IF NOT EXISTS bridge_outbound (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id        TEXT NOT NULL,
    target_role    TEXT NOT NULL CHECK(target_role IN ('dealer', 'seller')),
    target_phone   TEXT NOT NULL,
    template_phase TEXT NOT NULL,
    template_lang  TEXT NOT NULL,
    body           TEXT NOT NULL,
    state_at_send  TEXT NOT NULL,
    created_ts     INTEGER NOT NULL,
    approved_ts    INTEGER,
    sent_ts        INTEGER,
    sent_status    TEXT,
    wa_msg_id      TEXT
);

-- Party registry: mapping phone ↔ alias ↔ deal context
CREATE TABLE IF NOT EXISTS bridge_parties (
    phone          TEXT PRIMARY KEY,
    role           TEXT NOT NULL CHECK(role IN ('dealer', 'seller')),
    alias          TEXT NOT NULL,
    country        TEXT,
    current_deals  TEXT,  -- JSON array deal_ids
    created_ts     INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inbound_unprocessed ON bridge_inbound(processed_ts) WHERE processed_ts IS NULL;
CREATE INDEX IF NOT EXISTS idx_outbound_pending ON bridge_outbound(approved_ts, sent_ts);
"""


@dataclass
class InboundMsg:
    msg_id: str
    party_role: str          # 'dealer' | 'seller'
    party_phone: str
    body: str
    received_ts: int
    party_alias: Optional[str] = None
    deal_id: Optional[str] = None


@dataclass
class OutboundCandidate:
    deal_id: str
    target_role: str          # 'dealer' | 'seller'
    target_phone: str
    template_phase: str       # offer | negotiation | documents | payment | delivery
    template_lang: str        # 'it' | 'en'
    body: str
    state_at_send: str


class WABridge:
    """Bridge orchestratore: inbound → state machine → outbound candidate (HITL approval)."""

    def __init__(self, db_path: str | Path, deals_db_path: str | Path):
        self.db_path = Path(db_path)
        self.deals_db_path = Path(deals_db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(BRIDGE_SCHEMA)
            # S168 wire-up: idempotent ALTER per DB pre-esistenti (CREATE TABLE già aggiornato per nuovi DB)
            cols = {row[1] for row in conn.execute("PRAGMA table_info(bridge_outbound)").fetchall()}
            if "wa_msg_id" not in cols:
                conn.execute("ALTER TABLE bridge_outbound ADD COLUMN wa_msg_id TEXT")
            # S203: action_type per HITL routing (auto-approve whitelist vs HITL required)
            if "action_type" not in cols:
                conn.execute("ALTER TABLE bridge_outbound ADD COLUMN action_type TEXT DEFAULT 'agent_auto'")
            conn.commit()
        finally:
            conn.close()

    def register_party(self, phone: str, role: str, alias: str, country: Optional[str] = None) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO bridge_parties (phone, role, alias, country, current_deals, created_ts)
                VALUES (?, ?, ?, ?, '[]', ?)
                ON CONFLICT(phone) DO UPDATE SET alias = excluded.alias, country = excluded.country
                """,
                (phone, role, alias, country, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()

    def get_party_alias(self, phone: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute("SELECT alias, role FROM bridge_parties WHERE phone = ?", (phone,))
            row = cur.fetchone()
            return f"{row[1]}:{row[0]}" if row else None
        finally:
            conn.close()

    def ingest_inbound(self, msg: InboundMsg) -> None:
        """Chiamato da wa-daemon polling layer quando nuovo msg arriva."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO bridge_inbound (msg_id, party_role, party_phone, party_alias, body, received_ts)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(msg_id) DO NOTHING
                """,
                (msg.msg_id, msg.party_role, msg.party_phone, msg.party_alias, msg.body, msg.received_ts),
            )
            conn.commit()
            logger.info(f"ingest inbound msg_id={msg.msg_id} role={msg.party_role}")
        finally:
            conn.close()

    def pending_inbound(self) -> Iterator[InboundMsg]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT msg_id, party_role, party_phone, party_alias, body, received_ts, deal_id
                FROM bridge_inbound
                WHERE processed_ts IS NULL
                ORDER BY received_ts ASC
                """
            )
            for row in cur.fetchall():
                yield InboundMsg(
                    msg_id=row[0], party_role=row[1], party_phone=row[2],
                    party_alias=row[3], body=row[4], received_ts=row[5], deal_id=row[6],
                )
        finally:
            conn.close()

    def mark_processed(self, msg_id: str, deal_id: Optional[str] = None,
                       intent: Optional[str] = None, sentiment: Optional[str] = None) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                UPDATE bridge_inbound
                SET processed_ts = ?, deal_id = ?, intent = ?, sentiment = ?
                WHERE msg_id = ?
                """,
                (int(time.time()), deal_id, intent, sentiment, msg_id),
            )
            conn.commit()
        finally:
            conn.close()

    def queue_outbound(self, candidate: OutboundCandidate) -> tuple[int, bool]:
        """Inserisce outbound candidate nella coda bridge.

        Usa INSERT OR IGNORE per gestire UNIQUE constraint (uq_outbound_deal_phone_phase)
        introdotto con migrazione S173 senza sollevare eccezioni.

        Returns:
            (row_id, inserted): row_id=lastrowid se inserito (else -1), inserted=True se nuovo record.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO bridge_outbound
                    (deal_id, target_role, target_phone, template_phase, template_lang,
                     body, state_at_send, created_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (candidate.deal_id, candidate.target_role, candidate.target_phone,
                 candidate.template_phase, candidate.template_lang,
                 candidate.body, candidate.state_at_send, int(time.time())),
            )
            conn.commit()
            inserted = cur.rowcount == 1
            row_id = cur.lastrowid if inserted else -1
            if not inserted:
                logger.warning(
                    f"[dedup] INSERT OR IGNORE skipped duplicate: deal={candidate.deal_id} "
                    f"phone={candidate.target_phone} phase={candidate.template_phase}"
                )
            return (row_id, inserted)
        finally:
            conn.close()

    def pending_outbound(self, only_approved: bool = False) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        try:
            where = "WHERE sent_ts IS NULL"
            if only_approved:
                where += " AND approved_ts IS NOT NULL"
            cur = conn.execute(
                f"""
                SELECT id, deal_id, target_role, target_phone, template_phase, template_lang,
                       body, state_at_send, created_ts, approved_ts
                FROM bridge_outbound
                {where}
                ORDER BY created_ts ASC
                """
            )
            cols = ["id", "deal_id", "target_role", "target_phone", "template_phase",
                    "template_lang", "body", "state_at_send", "created_ts", "approved_ts"]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    def approve_outbound(self, outbound_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE bridge_outbound SET approved_ts = ? WHERE id = ?",
                (int(time.time()), outbound_id),
            )
            conn.commit()
        finally:
            conn.close()

    def mark_sent(self, outbound_id: int, status: str = "ok", wa_msg_id: Optional[str] = None) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE bridge_outbound SET sent_ts = ?, sent_status = ?, wa_msg_id = ? WHERE id = ?",
                (int(time.time()), status, wa_msg_id, outbound_id),
            )
            conn.commit()
        finally:
            conn.close()

    # ── Core orchestration logic ────────────────────────────────

    def _open_fsm(self, deal_id: str) -> DealStateMachine:
        """Restore FSM dal deals.sqlite. Assume Deal già creato altrove."""
        conn = sqlite3.connect(self.deals_db_path)
        try:
            cur = conn.execute(
                "SELECT dealer_alias, seller_alias, vehicle_desc, fee_eur, metadata_json FROM deals WHERE deal_id = ?",
                (deal_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"deal not found: {deal_id}")
            metadata = json.loads(row[4]) if row[4] else {}
            deal = Deal(
                deal_id=deal_id,
                dealer_alias=row[0],
                seller_alias=row[1],
                vehicle_desc=row[2],
                fee_eur=row[3],
                metadata=metadata,
            )
            return DealStateMachine(deal, db_path=self.deals_db_path)
        finally:
            conn.close()

    def _phase_for_state(self, state_id: str) -> Optional[str]:
        """Mapping state_machine state → template phase."""
        mapping = {
            "offer_sent": "offer",
            "accepted": "negotiation",
            "docs_shared": "documents",
            "payment_pending": "payment",
            "payment_confirmed": "payment",
            "transport_scheduled": "delivery",
            "in_transit": "delivery",
        }
        return mapping.get(state_id)

    def _phone_for_target(self, deal_id: str, target_role: str) -> Optional[str]:
        """Look up phone da bridge_parties via deal context."""
        conn = sqlite3.connect(self.deals_db_path)
        try:
            cur = conn.execute(
                "SELECT dealer_alias, seller_alias, metadata_json FROM deals WHERE deal_id = ?",
                (deal_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            alias = row[0] if target_role == "dealer" else row[1]
        finally:
            conn.close()

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "SELECT phone FROM bridge_parties WHERE alias = ? AND role = ?",
                (alias, target_role),
            )
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def generate_response(self, deal_id: str, target_role: str, template_vars: dict) -> OutboundCandidate:
        """Genera candidate response basata su stato FSM corrente + template phase mapping.

        target_role: a chi va il messaggio ('dealer' o 'seller')
        template_vars: variabili Jinja2 per render (auto specs, prezzi, dossier_id, ecc)
        """
        fsm = self._open_fsm(deal_id)
        state = fsm.current_state.id
        phase = self._phase_for_state(state)
        if not phase:
            raise ValueError(f"no template phase mapped for state '{state}'")
        lang = "it" if target_role == "dealer" else "en"
        phone = self._phone_for_target(deal_id, target_role)
        if not phone:
            raise ValueError(f"no phone registered for deal_id={deal_id} role={target_role}")

        body = render_template(phase, lang, **template_vars)

        return OutboundCandidate(
            deal_id=deal_id,
            target_role=target_role,
            target_phone=phone,
            template_phase=phase,
            template_lang=lang,
            body=body,
            state_at_send=state,
        )

    def stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        try:
            inb_total = conn.execute("SELECT COUNT(*) FROM bridge_inbound").fetchone()[0]
            inb_pending = conn.execute(
                "SELECT COUNT(*) FROM bridge_inbound WHERE processed_ts IS NULL"
            ).fetchone()[0]
            out_total = conn.execute("SELECT COUNT(*) FROM bridge_outbound").fetchone()[0]
            out_pending = conn.execute(
                "SELECT COUNT(*) FROM bridge_outbound WHERE sent_ts IS NULL"
            ).fetchone()[0]
            out_approved = conn.execute(
                "SELECT COUNT(*) FROM bridge_outbound WHERE approved_ts IS NOT NULL AND sent_ts IS NULL"
            ).fetchone()[0]
            parties = conn.execute("SELECT COUNT(*) FROM bridge_parties").fetchone()[0]
            return {
                "inbound_total": inb_total,
                "inbound_pending": inb_pending,
                "outbound_total": out_total,
                "outbound_pending": out_pending,
                "outbound_approved_unsent": out_approved,
                "parties_registered": parties,
            }
        finally:
            conn.close()
