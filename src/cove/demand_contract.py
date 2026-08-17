"""ARGOS S292 demand-side contract.

Single source of business invariants for the active CoVe runtime.
This module deliberately contains no network or persistence code: callers must
provide verifiable dealer evidence. Unknown claims remain unknown.

Canonical flow (docs/ROADMAP.md, S292):
    credibility -> mandate/demand discovery -> dealer commissions vehicle ->
    sourcing -> CoVe/evidence/grade/economics -> dossier -> deal/retention
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

UNKNOWN = "DA_VERIFICARE"
NOT_AVAILABLE = "n/d"
NO_VERDICT = "NO-VERDICT"

MANDATE_FIELDS = (
    "lavora_su_mandato",
    "accesso_clienti_altospendenti",
    "segmenti_richiesti",
    "live_demand",
)

SCORE_DIMENSIONS = (
    "dealer_fit",
    "mandate_confidence",
    "cove_confidence",
    "argos_vehicle_grade",
    "deal_economics",
    "market_confidence",
    "dossier_readiness",
)


@dataclass(frozen=True)
class DemandEvidence:
    """Evidence about dealer demand. Only direct/verifiable evidence can open sourcing."""

    dealer_id: str
    credibility_established: bool = False
    dealer_commissioned_vehicle: bool = False
    live_demand: Any = UNKNOWN
    segmenti_richiesti: Any = UNKNOWN
    lavora_su_mandato: Any = UNKNOWN
    accesso_clienti_altospendenti: Any = UNKNOWN
    source: str = NOT_AVAILABLE
    evidence_id: str = NOT_AVAILABLE
    vehicle_request: Mapping[str, Any] = field(default_factory=dict)

    @property
    def is_direct(self) -> bool:
        return bool(
            self.credibility_established
            and self.dealer_commissioned_vehicle
            and self.source not in ("", NOT_AVAILABLE, UNKNOWN)
            and self.evidence_id not in ("", NOT_AVAILABLE, UNKNOWN)
        )

    @property
    def sourcing_authorized(self) -> bool:
        """Fail closed: no direct commission evidence, no sourcing."""
        return self.is_direct and bool(self.vehicle_request)

    def normalized_claims(self) -> Dict[str, Any]:
        raw = {
            "lavora_su_mandato": self.lavora_su_mandato,
            "accesso_clienti_altospendenti": self.accesso_clienti_altospendenti,
            "segmenti_richiesti": self.segmenti_richiesti,
            "live_demand": self.live_demand,
        }
        if not self.is_direct:
            return {key: UNKNOWN for key in MANDATE_FIELDS}
        return {
            key: (UNKNOWN if value in (None, "", NOT_AVAILABLE) else value)
            for key, value in raw.items()
        }


@dataclass(frozen=True)
class ArgosScorecard:
    """Independent dimensions; missing evidence is never converted to a neutral score."""

    dealer_fit: Optional[float] = None
    mandate_confidence: Optional[float] = None
    cove_confidence: Optional[float] = None
    argos_vehicle_grade: Optional[float] = None
    deal_economics: Optional[float] = None
    market_confidence: Optional[float] = None
    dossier_readiness: Optional[float] = None

    def __post_init__(self) -> None:
        for name in SCORE_DIMENSIONS:
            value = getattr(self, name)
            if value is not None and not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1 or None")

    def as_dict(self, display_missing: bool = False) -> Dict[str, Any]:
        missing = NOT_AVAILABLE if display_missing else None
        return {
            name: (missing if getattr(self, name) is None else float(getattr(self, name)))
            for name in SCORE_DIMENSIONS
        }


def mandate_confidence_from_evidence(evidence: DemandEvidence) -> Optional[float]:
    """Confidence is evidence-backed, not inferred from dealer profile/persona."""
    if not evidence.is_direct:
        return None
    if not evidence.vehicle_request:
        return 0.5
    return 1.0


def require_sourcing_authorization(evidence: Optional[DemandEvidence]) -> DemandEvidence:
    """Return evidence only when canonical S292 sourcing gate is satisfied."""
    if evidence is None:
        raise PermissionError("S292_GATE: dealer mandate/demand evidence required before sourcing")
    if not evidence.sourcing_authorized:
        raise PermissionError(
            "S292_GATE: sourcing blocked until credibility + direct dealer commission + vehicle request"
        )
    return evidence
