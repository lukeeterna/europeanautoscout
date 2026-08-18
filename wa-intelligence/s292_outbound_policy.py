#!/usr/bin/env python3
"""Fail-closed S292 policy applied immediately before WhatsApp send.

This is intentionally independent from the LLM/template generator.  Whatever
produces a message, the final send boundary rejects vehicle-push before a
verified mandate and known legacy deceptive/unsupported claims.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


VEHICLE_SPECIFIC_TEMPLATES = {
    "VEHICLE_PROPOSAL",
    "VEHICLE_DETAILS",
    "CLOSING_PUSH",
    "DAY_INTEREST",
    "IBAN_SEND",
}

DEPRECATED_TEMPLATE_IDS = {"DAY1_VEHICLE_FIRST"}

# Claims that the historical runtime could emit without corresponding evidence.
# They are blocked at the send boundary rather than trusted because an LLM or
# old template produced them.
_UNSUPPORTED_CLAIM_PATTERNS = (
    (r"\bcliente\s+fittizio\b", "FALSE_HANDOFF"),
    (r"\bmystery\s*shopper\b", "FALSE_HANDOFF"),
    (r"\bil\s+cliente\s+che\s+(?:e['’]?\s+)?passato\s+da\s+lei\b", "FALSE_HANDOFF"),
    (r"\bkm\s+certificati\s+(?:dalla\s+)?(?:revisione\s+)?t[uü]v\b", "UNVERIFIED_CERTAINTY"),
    (r"\btagliandi\s+certificati\b", "UNVERIFIED_CERTAINTY"),
    (r"\bgaranzia\s+costruttore\s+valida\s+in\s+italia\b", "UNVERIFIED_CERTAINTY"),
    (r"\bte\s+la\s+trovo\s+in\s+48\s*ore\b", "UNSUPPORTED_PROMISE"),
    (r"\bce\s+l['’]?ho\b", "UNSUPPORTED_AVAILABILITY"),
    (r"\bauto\s+pronta\s+per\s+la\s+vetrina\b", "UNSUPPORTED_AVAILABILITY"),
    (r"\bprezzi?\s+sotto\s+il\s+mercato\s+italiano\b", "UNSUPPORTED_MARKET_CLAIM"),
    (r"\bstessa\s+auto\s+parte\s+da\s+eur\b", "UNSUPPORTED_MARKET_CLAIM"),
)


@dataclass(frozen=True)
class OutboundPolicyResult:
    ok: bool
    reason: str
    check: str = "s292_policy"

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "reason": self.reason, "check": self.check}


def evaluate_outbound_policy(
    *,
    dealer_state: Mapping[str, Any],
    template_id: str,
    message: str,
) -> OutboundPolicyResult:
    state = str(dealer_state.get("conversation_state") or "COLD").upper()
    handoff = str(dealer_state.get("handoff_source") or "cold").lower()
    template_id = str(template_id or "").upper()
    message = str(message or "")

    if template_id in DEPRECATED_TEMPLATE_IDS:
        return OutboundPolicyResult(False, f"DEPRECATED_TEMPLATE: {template_id}")

    # Old database values may still contain the retired synthetic handoff.  No
    # message leaves the system until an operator replaces it with a real source.
    if handoff == "mystery_shopper":
        return OutboundPolicyResult(False, "UNVERIFIED_HANDOFF_SOURCE: mystery_shopper")

    if template_id in VEHICLE_SPECIFIC_TEMPLATES and state not in {"MANDATE_CONFIRMED", "CONVERTING"}:
        return OutboundPolicyResult(
            False,
            f"S292_GATE: {template_id} requires verified mandate, state={state}",
        )

    # Demand discovery can acknowledge criteria, but cannot become a vehicle
    # offer through a manually selected legacy template.
    if state == "DEMAND_DISCOVERY" and template_id not in {
        "VEHICLE_REQUEST_ACK",
        "IDENTITY_RESPONSE",
        "OBJ_1_NO_INTEREST",
        "OBJ_2_FEE",
        "OBJ_3_TRUST",
        "OBJ_4_TIMING",
        "OBJ_5_SOURCING",
    }:
        return OutboundPolicyResult(False, f"DEMAND_DISCOVERY_TEMPLATE_NOT_ALLOWED: {template_id}")

    normalized = " ".join(message.split())
    for pattern, reason in _UNSUPPORTED_CLAIM_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return OutboundPolicyResult(False, reason)

    if not normalized:
        return OutboundPolicyResult(False, "EMPTY_MESSAGE")

    return OutboundPolicyResult(True, "OK")
