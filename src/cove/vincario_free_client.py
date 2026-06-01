"""
VincarioFreeClient — Stub per CoVe Engine v4 compatibility
CoVe 2026 | Enterprise Grade

Vincario offre VIN check ma richiede crediti a pagamento.
Questo stub implementa l'interfaccia minima per non crashare il CoVe.
Quando/se avremo crediti free, qui si implementa il vero client.

Author: ARGOS CTO Stack
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("argos.vincario")


class VincarioPaidEndpointError(Exception):
    """Raised quando si tenta di usare un endpoint a pagamento."""
    pass


@dataclass
class VincarioBalance:
    credits_remaining: int = 0
    plan: str = "FREE"


class VincarioFreeClient:
    """
    Client Vincario — stub free.
    Non fa chiamate reali, solo placeholder per CoVe Engine.
    """

    def get_balance(self) -> VincarioBalance:
        """Ritorna sempre 0 crediti — nessun account attivo."""
        return VincarioBalance(credits_remaining=0, plan="STUB")

    def check_vin(self, vin: str) -> dict:
        """Stub — non fa nulla, ritorna dati vuoti."""
        logger.debug("VincarioFreeClient.check_vin(%s) — stub, nessun check reale", vin[:6] if vin else "N/A")
        return {"status": "NOT_CHECKED", "reason": "no_credits"}
