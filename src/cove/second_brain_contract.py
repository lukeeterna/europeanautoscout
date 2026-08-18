"""ARGOS Second Brain -> S292 runtime boundary.

Second Brain describes a dealer from permitted observations.  It is useful for
credible communication, but a profile is not demand.  This adapter is the only
supported bridge from ``tools/second_brain.py`` artifacts into the demand-side
runtime and keeps profile hints physically separated from dealer-originated
DemandEvidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from src.cove.demand_contract import (
    DemandEvidence,
    MANDATE_FIELDS,
    NOT_AVAILABLE,
    UNKNOWN,
)


@dataclass(frozen=True)
class SecondBrainContext:
    dealer_id: str
    profile_observations: Mapping[str, Any]
    communication: Mapping[str, Any]
    non_authoritative_search_hint: Mapping[str, Any]
    demand_claims: Mapping[str, Any]
    sourcing_authorized: bool
    demand_evidence_id: str = NOT_AVAILABLE
    demand_source: str = NOT_AVAILABLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dealer_id": self.dealer_id,
            "profile_observations": dict(self.profile_observations),
            "communication": dict(self.communication),
            "non_authoritative_search_hint": dict(self.non_authoritative_search_hint),
            "demand": {
                "claims": dict(self.demand_claims),
                "sourcing_authorized": self.sourcing_authorized,
                "evidence_id": self.demand_evidence_id,
                "source": self.demand_source,
            },
            "contract": (
                "Second Brain profile observations may tune communication; "
                "they never authorize sourcing or become live demand."
            ),
        }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _field_value(value: Any) -> Any:
    """Read SourcedField-shaped values without dropping provenance containers."""
    if isinstance(value, Mapping) and "value" in value:
        return value.get("value", NOT_AVAILABLE)
    return value if value not in (None, "") else NOT_AVAILABLE


def _dealer_id(artifact: Mapping[str, Any]) -> str:
    compatibility = _mapping(artifact.get("compatibility"))
    crm = _mapping(compatibility.get("dealer_crm"))
    dealer_id = str(crm.get("dealer_id") or "").strip()
    if not dealer_id:
        raise ValueError("Second Brain artifact missing compatibility.dealer_crm.dealer_id")
    return dealer_id


def build_second_brain_context(
    artifact: Mapping[str, Any],
    *,
    demand_evidence: Optional[DemandEvidence] = None,
) -> SecondBrainContext:
    """Build runtime context without promoting profile observations to demand."""
    if not isinstance(artifact, Mapping):
        raise TypeError("Second Brain artifact must be a mapping")
    schema = str(artifact.get("schema_version") or "").strip()
    if schema and not schema.startswith("second-brain."):
        raise ValueError(f"unsupported Second Brain schema: {schema}")

    dealer_id = _dealer_id(artifact)
    synthesis = _mapping(artifact.get("synthesis"))
    compatibility = _mapping(artifact.get("compatibility"))

    profile_observations = {
        "specializzazione_reale": _field_value(synthesis.get("specializzazione_reale")),
        "marche": _field_value(synthesis.get("marche")),
        "segmenti": _field_value(synthesis.get("segmenti")),
        "fascia_prezzo": _field_value(synthesis.get("fascia_prezzo")),
    }
    communication = {
        "registro_comunicativo": _mapping(synthesis.get("registro_comunicativo")),
        "aggancio_specifico": _mapping(synthesis.get("aggancio_specifico")),
    }

    # Preserve the legacy hint for diagnostics/backward compatibility but label
    # it explicitly non-authoritative.  No value from here is copied into demand.
    legacy_hint = dict(_mapping(compatibility.get("on_demand_runner_search_params")))

    if demand_evidence is None:
        claims = {name: UNKNOWN for name in MANDATE_FIELDS}
        return SecondBrainContext(
            dealer_id=dealer_id,
            profile_observations=profile_observations,
            communication=communication,
            non_authoritative_search_hint=legacy_hint,
            demand_claims=claims,
            sourcing_authorized=False,
        )

    if not isinstance(demand_evidence, DemandEvidence):
        raise TypeError("demand_evidence must be DemandEvidence or None")
    if demand_evidence.dealer_id != dealer_id:
        raise PermissionError("Second Brain dealer_id does not match DemandEvidence dealer_id")

    return SecondBrainContext(
        dealer_id=dealer_id,
        profile_observations=profile_observations,
        communication=communication,
        non_authoritative_search_hint=legacy_hint,
        demand_claims=demand_evidence.normalized_claims(),
        sourcing_authorized=demand_evidence.sourcing_authorized,
        demand_evidence_id=(
            demand_evidence.evidence_id
            if demand_evidence.has_verifiable_evidence
            else NOT_AVAILABLE
        ),
        demand_source=(
            demand_evidence.source
            if demand_evidence.has_verifiable_evidence
            else NOT_AVAILABLE
        ),
    )
