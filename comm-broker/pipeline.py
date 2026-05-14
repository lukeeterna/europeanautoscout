"""ARGOS comm-broker pipeline orchestrator — D-22 glue layer.

Lega: wa_bridge (in/out queue) + message_analyzer (Groq NLU) + deal_state_machine
(7-step lifecycle) + templates (Jinja2 5 fasi IT+EN).

MVP scope (S167): single-pass orchestrator. Production PM2 daemon → S168.

Flow per ogni inbound msg pending:
  1. analyzer.analyze(body, source_lang, target_lang) → intent + sentiment + scam
  2. if scam_flag → alert + transition FSM to aborted
  3. else if intent suggests state transition → FSM transition + outbound candidate
  4. bridge.mark_processed(msg_id, deal_id, intent, sentiment)
  5. bridge.queue_outbound(candidate) for HITL approval

Intent → FSM transition mapping:
  offer (state=offer_sent) → no auto-transition, send dossier
  positive accept (state=offer_sent) → FSM.accept() → render negotiation
  negotiation reply (state=accepted) → FSM.share_docs() → render documents
  docs_provided (state=docs_shared) → FSM.request_payment() → render payment
  payment_confirmed_msg (state=payment_pending) → FSM.confirm_payment() → render delivery
  scam → FSM.abort()

HITL gate (D-07): NO auto-send. Tutti outbound candidate vanno in queue per
founder approval prima di chiamata wa-daemon.
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wa_bridge import WABridge, InboundMsg, OutboundCandidate
from message_analyzer import MessageAnalyzer, AnalysisResult
from deal_state_machine import Deal, DealStateMachine


logger = logging.getLogger("argos.pipeline")


# Mapping: (intent, current_state) → FSM transition method name
INTENT_TO_TRANSITION = {
    # state offer_sent
    ("offer", "offer_sent"): "accept",          # dealer "mi interessa" → accepted
    ("greeting", "offer_sent"): None,            # no transition, send opening
    ("objection", "offer_sent"): None,           # stay, send neg counter
    # state accepted
    ("docs_request", "accepted"): "share_docs",
    ("offer", "accepted"): "share_docs",        # continued interest → docs phase
    ("negotiation", "accepted"): None,           # negotiate, stay
    # state docs_shared
    ("payment", "docs_shared"): "request_payment",
    ("docs_request", "docs_shared"): None,       # additional docs, stay
    # state payment_pending
    ("payment", "payment_pending"): "confirm_payment",
    # state payment_confirmed
    ("delivery", "payment_confirmed"): "schedule_transport",
    # state transport_scheduled
    ("delivery", "transport_scheduled"): "start_transit",
    # state in_transit
    ("delivery", "in_transit"): "deliver",
}


@dataclass
class PipelineResult:
    msg_id: str
    deal_id: str
    intent: str
    sentiment: str
    scam_flag: bool
    fsm_transition: Optional[str]
    state_after: str
    outbound_queued: bool
    outbound_target: Optional[str]
    error: Optional[str] = None


class Pipeline:
    """Single-pass orchestrator: process pending inbound msgs → generate outbound candidates."""

    def __init__(self, bridge: WABridge, analyzer: MessageAnalyzer,
                 default_template_vars: Optional[dict] = None):
        self.bridge = bridge
        self.analyzer = analyzer
        self.template_vars = default_template_vars or {}

    def _resolve_deal_id(self, msg: InboundMsg) -> Optional[str]:
        """Trova deal_id attivo per il sender. MVP: lookup parties.current_deals."""
        if msg.deal_id:
            return msg.deal_id
        import sqlite3, json
        conn = sqlite3.connect(self.bridge.db_path)
        try:
            cur = conn.execute(
                "SELECT current_deals FROM bridge_parties WHERE phone = ?",
                (msg.party_phone,),
            )
            row = cur.fetchone()
            if not row or not row[0]:
                return None
            deals = json.loads(row[0]) if row[0] else []
            return deals[0] if deals else None
        finally:
            conn.close()

    def _attach_deal_to_party(self, phone: str, deal_id: str) -> None:
        """Aggiunge deal_id a parties.current_deals (JSON array)."""
        import sqlite3, json
        conn = sqlite3.connect(self.bridge.db_path)
        try:
            cur = conn.execute(
                "SELECT current_deals FROM bridge_parties WHERE phone = ?", (phone,)
            )
            row = cur.fetchone()
            if not row:
                return
            deals = json.loads(row[0]) if row[0] else []
            if deal_id not in deals:
                deals.append(deal_id)
                conn.execute(
                    "UPDATE bridge_parties SET current_deals = ? WHERE phone = ?",
                    (json.dumps(deals), phone),
                )
                conn.commit()
        finally:
            conn.close()

    def process_one(self, msg: InboundMsg) -> PipelineResult:
        """Process single inbound msg end-to-end."""
        # Determine source/target lang based on party role
        source_lang = "it" if msg.party_role == "dealer" else "en"
        target_lang = "en" if msg.party_role == "dealer" else "it"

        # 1. Analyze
        try:
            analysis = self.analyzer.analyze(msg.body, source_lang, target_lang)
        except Exception as e:
            logger.error(f"analyzer failed for msg {msg.msg_id}: {e}")
            self.bridge.mark_processed(msg.msg_id, intent="parse_error", sentiment="neutral")
            return PipelineResult(
                msg_id=msg.msg_id, deal_id=msg.deal_id or "",
                intent="parse_error", sentiment="neutral", scam_flag=False,
                fsm_transition=None, state_after="unknown",
                outbound_queued=False, outbound_target=None, error=str(e),
            )

        # 2. Resolve deal context
        deal_id = self._resolve_deal_id(msg)
        if not deal_id:
            logger.warning(f"no deal context for msg {msg.msg_id} from {msg.party_phone}")
            self.bridge.mark_processed(
                msg.msg_id, intent=analysis.intent, sentiment=analysis.sentiment
            )
            return PipelineResult(
                msg_id=msg.msg_id, deal_id="",
                intent=analysis.intent, sentiment=analysis.sentiment,
                scam_flag=analysis.scam_flag,
                fsm_transition=None, state_after="no_deal",
                outbound_queued=False, outbound_target=None,
                error="no_deal_context",
            )

        # 3. Open FSM
        try:
            fsm = self.bridge._open_fsm(deal_id)
        except ValueError as e:
            logger.error(f"FSM open failed: {e}")
            self.bridge.mark_processed(
                msg.msg_id, deal_id=deal_id,
                intent=analysis.intent, sentiment=analysis.sentiment,
            )
            return PipelineResult(
                msg_id=msg.msg_id, deal_id=deal_id,
                intent=analysis.intent, sentiment=analysis.sentiment,
                scam_flag=analysis.scam_flag,
                fsm_transition=None, state_after="error",
                outbound_queued=False, outbound_target=None, error=str(e),
            )

        current_state = fsm.current_state.id

        # 4. Scam → abort
        if analysis.scam_flag:
            logger.warning(f"SCAM DETECTED deal={deal_id} msg={msg.msg_id} reason={analysis.scam_reason}")
            try:
                fsm.abort()
            except Exception as e:
                logger.error(f"FSM abort failed: {e}")
            self.bridge.mark_processed(
                msg.msg_id, deal_id=deal_id,
                intent=analysis.intent, sentiment=analysis.sentiment,
            )
            return PipelineResult(
                msg_id=msg.msg_id, deal_id=deal_id,
                intent=analysis.intent, sentiment=analysis.sentiment,
                scam_flag=True,
                fsm_transition="abort", state_after=fsm.current_state.id,
                outbound_queued=False, outbound_target=None,
                error="scam_flag",
            )

        # 5. Determine FSM transition
        transition_name = INTENT_TO_TRANSITION.get((analysis.intent, current_state))
        transition_executed = None
        if transition_name:
            try:
                transition_method = getattr(fsm, transition_name)
                transition_method()
                transition_executed = transition_name
                logger.info(f"deal={deal_id} {current_state} → {fsm.current_state.id} ({transition_name})")
            except Exception as e:
                logger.warning(f"FSM transition '{transition_name}' failed from {current_state}: {e}")

        # 6. Generate outbound candidate (target = opposite party)
        target_role = "seller" if msg.party_role == "dealer" else "dealer"
        outbound_target = None
        outbound_queued = False
        try:
            # Merge default vars + deal-specific
            tvars = dict(self.template_vars)
            tvars.setdefault("dossier_id", deal_id)
            candidate = self.bridge.generate_response(deal_id, target_role, tvars)
            self.bridge.queue_outbound(candidate)
            outbound_target = target_role
            outbound_queued = True
        except (ValueError, Exception) as e:
            logger.warning(f"outbound generation skipped: {e}")

        # 7. Mark processed
        self.bridge.mark_processed(
            msg.msg_id, deal_id=deal_id,
            intent=analysis.intent, sentiment=analysis.sentiment,
        )

        return PipelineResult(
            msg_id=msg.msg_id, deal_id=deal_id,
            intent=analysis.intent, sentiment=analysis.sentiment,
            scam_flag=False,
            fsm_transition=transition_executed,
            state_after=fsm.current_state.id,
            outbound_queued=outbound_queued, outbound_target=outbound_target,
        )

    def process_pending(self, max_iterations: int = 100) -> list[PipelineResult]:
        """Process tutti pending inbound. Cap iterations per safety."""
        results = []
        for i, msg in enumerate(self.bridge.pending_inbound()):
            if i >= max_iterations:
                logger.warning(f"max_iterations {max_iterations} reached")
                break
            r = self.process_one(msg)
            results.append(r)
        return results
