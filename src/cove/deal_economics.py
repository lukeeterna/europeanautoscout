"""ARGOS deal-economics evidence contract.

No historical/fixed logistics cost and no percentage uplift may be used as a
production fallback.  A deal verdict is available only when the caller supplies
traceable values for acquisition, expected resale/reference value and every
cost category that applies to the calculation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from src.cove.demand_contract import NOT_AVAILABLE, NO_VERDICT


DEFAULT_REQUIRED_COSTS = (
    "transport_eur",
    "registration_eur",
    "argos_fee_eur",
)


def _money(value: Any, name: str) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{name} is required")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if parsed < 0:
        raise ValueError(f"{name} cannot be negative")
    return parsed


@dataclass(frozen=True)
class MoneyEvidence:
    amount_eur: float
    source: str
    evidence_id: str

    def __post_init__(self) -> None:
        amount = _money(self.amount_eur, "amount_eur")
        source = str(self.source or "").strip()
        evidence_id = str(self.evidence_id or "").strip()
        if not source or not evidence_id:
            raise ValueError("money evidence requires source and evidence_id")
        object.__setattr__(self, "amount_eur", amount)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "evidence_id", evidence_id)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "MoneyEvidence":
        return cls(
            amount_eur=value.get("amount_eur"),
            source=str(value.get("source") or ""),
            evidence_id=str(value.get("evidence_id") or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount_eur": self.amount_eur,
            "source": self.source,
            "evidence_id": self.evidence_id,
        }


@dataclass(frozen=True)
class DealEconomics:
    acquisition: MoneyEvidence
    market_reference: MoneyEvidence
    costs: Mapping[str, MoneyEvidence]
    required_costs: tuple[str, ...] = DEFAULT_REQUIRED_COSTS
    min_margin_eur: Optional[float] = None
    market_confidence: Optional[float] = None

    def __post_init__(self) -> None:
        if self.market_confidence is not None:
            confidence = float(self.market_confidence)
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("market_confidence must be between 0 and 1 or None")
        if self.min_margin_eur is not None:
            object.__setattr__(self, "min_margin_eur", _money(self.min_margin_eur, "min_margin_eur"))
        missing = [name for name in self.required_costs if name not in self.costs]
        if missing:
            raise ValueError(f"missing required evidenced costs: {', '.join(missing)}")
        for name, evidence in self.costs.items():
            if not isinstance(evidence, MoneyEvidence):
                raise TypeError(f"cost {name} must be MoneyEvidence")

    @property
    def total_costs_eur(self) -> float:
        return sum(item.amount_eur for item in self.costs.values())

    @property
    def net_margin_eur(self) -> float:
        return self.market_reference.amount_eur - self.acquisition.amount_eur - self.total_costs_eur

    @property
    def margin_ratio(self) -> Optional[float]:
        if self.market_reference.amount_eur <= 0:
            return None
        return self.net_margin_eur / self.market_reference.amount_eur

    @property
    def verdict(self) -> str:
        if self.min_margin_eur is None:
            # Without a declared business threshold ARGOS can expose arithmetic,
            # but must not invent a PROCEED/REJECT business decision.
            return NO_VERDICT
        return "PROCEED" if self.net_margin_eur >= self.min_margin_eur else "REJECT"

    @property
    def deal_economics_score(self) -> Optional[float]:
        """Bounded dimension only when both threshold and market confidence exist."""
        if self.min_margin_eur is None or self.market_confidence is None:
            return None
        if self.min_margin_eur == 0:
            base = 1.0 if self.net_margin_eur >= 0 else 0.0
        else:
            base = max(0.0, min(1.0, self.net_margin_eur / self.min_margin_eur))
        return round(base * float(self.market_confidence), 6)

    def to_dict(self) -> Dict[str, Any]:
        evidence_ids = {
            "acquisition": self.acquisition.evidence_id,
            "market_reference": self.market_reference.evidence_id,
            **{name: value.evidence_id for name, value in self.costs.items()},
        }
        return {
            "acquisition_eur": self.acquisition.amount_eur,
            "market_reference_eur": self.market_reference.amount_eur,
            "costs_eur": {name: value.amount_eur for name, value in self.costs.items()},
            "total_costs_eur": self.total_costs_eur,
            "net_margin_eur": self.net_margin_eur,
            "min_margin_eur": self.min_margin_eur if self.min_margin_eur is not None else NOT_AVAILABLE,
            "margin_ratio": self.margin_ratio if self.margin_ratio is not None else NOT_AVAILABLE,
            "market_confidence": self.market_confidence if self.market_confidence is not None else NOT_AVAILABLE,
            "deal_economics": self.deal_economics_score if self.deal_economics_score is not None else NOT_AVAILABLE,
            "verdict": self.verdict,
            "source": "argos.deal_economics.evidence-v1",
            "evidence_id": ";".join(f"{key}={value}" for key, value in sorted(evidence_ids.items())),
            "evidence": {
                "acquisition": self.acquisition.to_dict(),
                "market_reference": self.market_reference.to_dict(),
                "costs": {name: value.to_dict() for name, value in self.costs.items()},
            },
        }


def build_deal_economics(
    *,
    acquisition: Mapping[str, Any],
    market_reference: Mapping[str, Any],
    costs: Mapping[str, Mapping[str, Any]],
    min_margin_eur: Optional[float] = None,
    market_confidence: Optional[float] = None,
    required_costs: tuple[str, ...] = DEFAULT_REQUIRED_COSTS,
) -> DealEconomics:
    """Boundary adapter for JSON/DB payloads; raises on missing evidence."""
    return DealEconomics(
        acquisition=MoneyEvidence.from_mapping(acquisition),
        market_reference=MoneyEvidence.from_mapping(market_reference),
        costs={name: MoneyEvidence.from_mapping(value) for name, value in costs.items()},
        required_costs=required_costs,
        min_margin_eur=min_margin_eur,
        market_confidence=market_confidence,
    )
