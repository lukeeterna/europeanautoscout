"""ARGOS S292 demand-side contract.

This module is the executable boundary for the active demand-side runtime.
It contains no network or persistence code: callers must provide evidence
collected by an authorised channel and ARGOS must never infer a mandate from a
profile, CRM stage, inventory similarity, or a model prediction.

Canonical flow (docs/ROADMAP.md, S292):
    credibility -> demand discovery -> dealer commissions vehicle -> sourcing ->
    CoVe/evidence/grade/economics -> dossier -> deal/retention
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
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

_EMPTY = (None, "", NOT_AVAILABLE, UNKNOWN)


def _known(value: Any) -> bool:
    """Return True only for a value carrying actual information."""
    if value in _EMPTY:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_known(v) for v in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_known(v) for v in value)
    return True


def _clean_mapping(value: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not value:
        return {}
    cleaned: Dict[str, Any] = {}
    for key, item in value.items():
        key_s = str(key).strip()
        if not key_s or not _known(item):
            continue
        if isinstance(item, str):
            cleaned[key_s] = item.strip()
        else:
            cleaned[key_s] = item
    return cleaned


@dataclass(frozen=True)
class DemandEvidence:
    """Evidence about a dealer conversation and, separately, a vehicle mandate.

    ``has_verifiable_evidence`` answers only whether the claims have a traceable
    dealer-originated source. It deliberately does *not* mean that the dealer
    commissioned a vehicle. ``sourcing_authorized`` is the stronger S292 gate
    and requires credibility, traceable evidence, an explicit commission and a
    non-empty vehicle request.
    """

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
    observed_at: str = NOT_AVAILABLE

    def __post_init__(self) -> None:
        dealer_id = str(self.dealer_id or "").strip()
        if not dealer_id:
            raise ValueError("dealer_id is required")
        object.__setattr__(self, "dealer_id", dealer_id)
        object.__setattr__(self, "source", str(self.source or NOT_AVAILABLE).strip() or NOT_AVAILABLE)
        object.__setattr__(
            self,
            "evidence_id",
            str(self.evidence_id or NOT_AVAILABLE).strip() or NOT_AVAILABLE,
        )
        object.__setattr__(self, "vehicle_request", _clean_mapping(self.vehicle_request))
        if self.observed_at not in _EMPTY:
            try:
                datetime.fromisoformat(str(self.observed_at).replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("observed_at must be ISO-8601 or n/d") from exc

    @property
    def has_verifiable_evidence(self) -> bool:
        """Whether this evidence can be traced back to a concrete observation."""
        return self.source not in _EMPTY and self.evidence_id not in _EMPTY

    @property
    def is_direct(self) -> bool:
        """Backward-compatible alias for traceable/direct evidence.

        Older code used ``is_direct`` as if it also meant commissioned. That
        conflation is intentionally removed; callers needing permission to
        source must use ``sourcing_authorized`` / ``require_sourcing_authorization``.
        """
        return self.has_verifiable_evidence

    @property
    def has_vehicle_request(self) -> bool:
        return bool(_clean_mapping(self.vehicle_request))

    @property
    def sourcing_authorized(self) -> bool:
        """Fail closed: no explicit dealer commission, no vehicle sourcing."""
        return bool(
            self.credibility_established
            and self.has_verifiable_evidence
            and self.dealer_commissioned_vehicle
            and self.has_vehicle_request
        )

    def normalized_claims(self) -> Dict[str, Any]:
        """Return claims only when their provenance is traceable.

        A verified dealer reply can establish a claim even when it does not yet
        contain a vehicle commission. Profile-derived guesses never become facts.
        """
        raw = {
            "lavora_su_mandato": self.lavora_su_mandato,
            "accesso_clienti_altospendenti": self.accesso_clienti_altospendenti,
            "segmenti_richiesti": self.segmenti_richiesti,
            "live_demand": self.live_demand,
        }
        if not self.has_verifiable_evidence:
            return {key: UNKNOWN for key in MANDATE_FIELDS}
        return {
            key: (UNKNOWN if not _known(value) else value)
            for key, value in raw.items()
        }

    def to_dict(self, *, display_missing: bool = False) -> Dict[str, Any]:
        missing = NOT_AVAILABLE if display_missing else None
        return {
            "dealer_id": self.dealer_id,
            "credibility_established": self.credibility_established,
            "dealer_commissioned_vehicle": self.dealer_commissioned_vehicle,
            "source": self.source,
            "evidence_id": self.evidence_id,
            "observed_at": self.observed_at,
            "claims": self.normalized_claims(),
            "vehicle_request": dict(self.vehicle_request),
            "has_verifiable_evidence": self.has_verifiable_evidence,
            "sourcing_authorized": self.sourcing_authorized,
            "authorization": "AUTHORIZED" if self.sourcing_authorized else (missing or "BLOCKED"),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DemandEvidence":
        """Strict, side-effect-free adapter for JSON/DB boundaries."""
        claims = value.get("claims") if isinstance(value.get("claims"), Mapping) else value
        request = value.get("vehicle_request")
        if request is None:
            request = {}
        if not isinstance(request, Mapping):
            raise TypeError("vehicle_request must be an object/mapping")
        return cls(
            dealer_id=str(value.get("dealer_id") or ""),
            credibility_established=bool(value.get("credibility_established", False)),
            dealer_commissioned_vehicle=bool(value.get("dealer_commissioned_vehicle", False)),
            live_demand=claims.get("live_demand", UNKNOWN),
            segmenti_richiesti=claims.get("segmenti_richiesti", UNKNOWN),
            lavora_su_mandato=claims.get("lavora_su_mandato", UNKNOWN),
            accesso_clienti_altospendenti=claims.get("accesso_clienti_altospendenti", UNKNOWN),
            source=str(value.get("source") or NOT_AVAILABLE),
            evidence_id=str(value.get("evidence_id") or NOT_AVAILABLE),
            vehicle_request=request,
            observed_at=str(value.get("observed_at") or NOT_AVAILABLE),
        )


@dataclass(frozen=True)
class ArgosScorecard:
    """Independent evidence dimensions; missing never becomes a neutral score."""

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
    """Return a confidence only for the exact S292 authorization fact.

    No arbitrary midpoint is emitted for a reply/profile: either a traceable,
    explicit commission with request exists (1.0), or the mandate confidence
    remains unknown (None). Other response facts live in ``normalized_claims``.
    """
    return 1.0 if evidence.sourcing_authorized else None


def require_sourcing_authorization(evidence: Optional[DemandEvidence]) -> DemandEvidence:
    """Return evidence only when the canonical S292 sourcing gate is satisfied."""
    if evidence is None:
        raise PermissionError("S292_GATE: dealer demand evidence required before sourcing")
    if not isinstance(evidence, DemandEvidence):
        raise TypeError("evidence must be DemandEvidence")
    if not evidence.credibility_established:
        raise PermissionError("S292_GATE: dealer credibility not established")
    if not evidence.has_verifiable_evidence:
        raise PermissionError("S292_GATE: traceable dealer evidence required")
    if not evidence.dealer_commissioned_vehicle:
        raise PermissionError("S292_GATE: dealer has not commissioned a vehicle")
    if not evidence.has_vehicle_request:
        raise PermissionError("S292_GATE: commissioned vehicle request is empty")
    return evidence


def require_listing_authorization(
    evidence: Optional[DemandEvidence],
    listing_id: str,
) -> DemandEvidence:
    """S292 gate plus optional listing binding.

    If the request explicitly carries ``listing_id``, it must match. A request
    expressed only as vehicle criteria is valid for sourcing candidates and is
    therefore not forced to carry a listing id that did not exist when the
    dealer commissioned the search.
    """
    authorized = require_sourcing_authorization(evidence)
    expected = str(authorized.vehicle_request.get("listing_id") or "").strip()
    actual = str(listing_id or "").strip()
    if not actual:
        raise ValueError("listing_id is required")
    if expected and expected != actual:
        raise PermissionError(
            f"S292_GATE: evidence is bound to listing {expected}, not {actual}"
        )
    return authorized
