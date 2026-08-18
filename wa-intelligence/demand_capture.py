#!/usr/bin/env python3
"""Deterministic capture of dealer-originated vehicle demand.

The module converts an inbound WhatsApp message into structured *discovery*
criteria.  It may mark a commission explicit only when the dealer uses a clear
commission verb and names at least a make/model.  Ambiguous interest remains
DEMAND_DISCOVERY and never authorizes sourcing.

No LLM decision is allowed to create a mandate.  The original inbound message
ID is the evidence ID; downstream code can always trace the decision back to
what the dealer actually wrote.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from src.cove.demand_contract import DemandEvidence, UNKNOWN


KNOWN_MAKES = (
    "Alfa Romeo", "Audi", "BMW", "Citroen", "Cupra", "Dacia", "Fiat",
    "Ford", "Honda", "Hyundai", "Jaguar", "Jeep", "Kia", "Land Rover",
    "Lexus", "Mazda", "Mercedes-Benz", "Mercedes", "Mini", "Nissan",
    "Opel", "Peugeot", "Porsche", "Renault", "Seat", "Skoda", "Smart",
    "Suzuki", "Tesla", "Toyota", "Volkswagen", "Volvo",
)

_COMMISSION_PATTERNS = (
    r"\bcercami\b",
    r"\btrovami\b",
    r"\bprova\s+a\s+trovarmi\b",
    r"\bpuoi\s+cercar(?:e|mi)\b",
    r"\bpuoi\s+trovar(?:e|mi)\b",
    r"\bprocedi\s+(?:pure\s+)?con\s+la\s+ricerca\b",
    r"\bprocedi\s+(?:pure\s+)?a\s+cercar",
    r"\bvai\s+(?:pure\s+)?avanti\s+con\s+la\s+ricerca\b",
    r"\bti\s+incarico\b",
    r"\bvi\s+incarico\b",
    r"\bdo\s+(?:il\s+)?mandato\b",
    r"\baffido\s+(?:a\s+voi\s+)?la\s+ricerca\b",
    r"\bmi\s+serve\b.{0,80}\b(?:cercala|cercalo|trovala|trovalo)\b",
)

_REQUEST_PATTERNS = (
    r"\bcerco\b",
    r"\bsto\s+cercando\b",
    r"\bavrei\s+bisogno\b",
    r"\bmi\s+serve\b",
    r"\bmi\s+servirebbe\b",
    r"\bhai\s+(?:una|un)\b",
    r"\bavete\s+(?:una|un)\b",
    r"\bpotresti\s+trovar",
    r"\bpotreste\s+trovar",
) + _COMMISSION_PATTERNS

_NEGATION_PATTERNS = (
    r"\bnon\s+(?:mi\s+)?serve\b",
    r"\bnon\s+cerco\b",
    r"\bnon\s+sto\s+cercando\b",
    r"\bnon\s+mi\s+interessa\b",
    r"\bnessuna\s+ricerca\b",
)

_FUEL = {
    "diesel": "diesel",
    "benzina": "benzina",
    "ibrida": "ibrido",
    "ibrido": "ibrido",
    "plug in": "plug-in hybrid",
    "plug-in": "plug-in hybrid",
    "elettrica": "elettrico",
    "elettrico": "elettrico",
}

_TRANSMISSION = {
    "automatico": "automatico",
    "automatica": "automatico",
    "manuale": "manuale",
}


def _ascii_lower(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in value if not unicodedata.combining(ch)).lower()


def _compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _money_value(raw_number: str, suffix: str = "") -> Optional[int]:
    value = raw_number.strip().lower().replace("€", "").replace("eur", "")
    value = value.replace(" ", "")
    suffix = suffix.lower().strip()
    try:
        if "," in value and "." in value:
            # Italian thousands + decimal, e.g. 45.000,00
            value = value.replace(".", "").replace(",", ".")
        elif value.count(".") >= 1:
            parts = value.split(".")
            if all(len(part) == 3 for part in parts[1:]):
                value = "".join(parts)
        elif value.count(",") == 1:
            before, after = value.split(",")
            if len(after) == 3:
                value = before + after
            else:
                value = before + "." + after
        number = float(value)
    except ValueError:
        return None
    if suffix in {"k", "mila", "mille"}:
        number *= 1000
    amount = int(round(number))
    return amount if 1000 <= amount <= 2_000_000 else None


def _km_value(raw_number: str, suffix: str = "") -> Optional[int]:
    value = _money_value(raw_number, suffix)
    if value is not None:
        return value if value <= 500_000 else None
    # _money_value rejects small explicit values such as "900"; allow them for km.
    try:
        normalized = raw_number.replace(".", "").replace(",", "").strip()
        number = int(normalized)
    except ValueError:
        return None
    if suffix.lower().strip() in {"k", "mila", "mille"}:
        number *= 1000
    return number if 0 <= number <= 500_000 else None


def _extract_make(text: str) -> Optional[str]:
    lowered = _ascii_lower(text)
    # Longest first so Mercedes-Benz wins over Mercedes.
    for make in sorted(KNOWN_MAKES, key=len, reverse=True):
        needle = _ascii_lower(make)
        if re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", lowered):
            return "Mercedes-Benz" if make in {"Mercedes", "Mercedes-Benz"} else make
    return None


def _extract_model(text: str, make: Optional[str]) -> Optional[str]:
    """Conservative model extraction around a recognised make or common model token."""
    cleaned = _compact_spaces(text)
    if make:
        make_pattern = r"mercedes(?:-benz)?" if make == "Mercedes-Benz" else re.escape(make)
        match = re.search(
            rf"\b{make_pattern}\b\s+([A-Za-z0-9][A-Za-z0-9+\-]{{0,14}}(?:\s+[A-Za-z0-9][A-Za-z0-9+\-]{{0,12}})?)",
            cleaned,
            flags=re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip(" ,.;:-")
            # Stop words frequently follow the make and are not models.
            candidate = re.split(
                r"\b(?:dal|dall|del|anno|con|max|massimo|budget|sotto|entro|diesel|benzina|automatic[oa]|manuale)\b",
                candidate,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip(" ,.;:-")
            if candidate:
                return candidate

    # Common premium model families where the make is often omitted.
    model_match = re.search(
        r"\b(X[1-7]|Q[2-8]|GL[ABCES]|GLE|GLS|Macan|Cayenne|Tiguan|Touareg|XC(?:40|60|90)|Range\s+Rover(?:\s+Sport)?|Evoque)\b",
        cleaned,
        flags=re.IGNORECASE,
    )
    return model_match.group(1) if model_match else None


def _extract_years(text: str) -> tuple[Optional[int], Optional[int]]:
    years = [int(value) for value in re.findall(r"\b(20(?:1[0-9]|2[0-9]|3[0-5]))\b", text)]
    if not years:
        return None, None
    return min(years), max(years)


def _extract_budget(text: str) -> Optional[int]:
    normalized = _ascii_lower(text)
    patterns = (
        r"(?:budget|max(?:\.|imo)?|massimo|fino\s+a|entro|sotto)\s*(?:di\s*)?(?:eur|€)?\s*([0-9][0-9.,]*)\s*(k|mila|mille)?",
        r"(?:eur|€)\s*([0-9][0-9.,]*)\s*(k|mila|mille)?\s*(?:max|massimo)?",
        r"([0-9][0-9.,]*)\s*(k|mila|mille)\s*(?:eur|€)?\s*(?:max|massimo|di budget)?",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            amount = _money_value(match.group(1), match.group(2) or "")
            if amount is not None:
                return amount
    return None


def _extract_km_max(text: str) -> Optional[int]:
    normalized = _ascii_lower(text)
    patterns = (
        r"(?:max(?:\.|imo)?|massimo|fino\s+a|entro|sotto)\s*([0-9][0-9.,]*)\s*(k|mila|mille)?\s*km\b",
        r"([0-9][0-9.,]*)\s*(k|mila|mille)?\s*km\s*(?:max|massimo)?",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            value = _km_value(match.group(1), match.group(2) or "")
            if value is not None:
                return value
    return None


def _extract_keyword(text: str, mapping: Mapping[str, str]) -> Optional[str]:
    normalized = _ascii_lower(text).replace("-", " ")
    for needle, value in mapping.items():
        if re.search(rf"\b{re.escape(_ascii_lower(needle).replace('-', ' '))}\b", normalized):
            return value
    return None


def _contains_any(text: str, patterns: Sequence[str]) -> bool:
    normalized = _ascii_lower(text)
    return any(re.search(pattern, normalized, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


@dataclass(frozen=True)
class VehicleRequestCapture:
    message_id: str
    criteria: Mapping[str, Any]
    is_vehicle_request: bool
    explicit_commission: bool
    summary: str
    missing_for_search: tuple[str, ...] = field(default_factory=tuple)

    @property
    def authorization_ready(self) -> bool:
        """True only for clear commission + a concrete vehicle identity."""
        return bool(
            self.explicit_commission
            and (self.criteria.get("make") or self.criteria.get("model"))
        )

    def to_evidence(
        self,
        *,
        dealer_id: str,
        credibility_established: bool,
        observed_at: Optional[str] = None,
    ) -> DemandEvidence:
        """Create traceable evidence; only authorization_ready becomes commissioned."""
        return DemandEvidence(
            dealer_id=dealer_id,
            credibility_established=bool(credibility_established),
            dealer_commissioned_vehicle=self.authorization_ready,
            live_demand=True if self.is_vehicle_request else UNKNOWN,
            segmenti_richiesti=[self.summary] if self.summary else UNKNOWN,
            lavora_su_mandato=UNKNOWN,
            accesso_clienti_altospendenti=UNKNOWN,
            source="whatsapp_inbound",
            evidence_id=self.message_id,
            vehicle_request=dict(self.criteria) if self.authorization_ready else {},
            observed_at=observed_at or datetime.now(timezone.utc).isoformat(),
        )


def capture_vehicle_request(message_id: str, body: str) -> VehicleRequestCapture:
    message_id = str(message_id or "").strip()
    if not message_id:
        raise ValueError("message_id is required")
    body = _compact_spaces(body)
    if not body:
        raise ValueError("inbound body is empty")

    negated = _contains_any(body, _NEGATION_PATTERNS)
    make = _extract_make(body)
    model = _extract_model(body, make)
    year_min, year_max = _extract_years(body)
    budget = _extract_budget(body)
    km_max = _extract_km_max(body)
    fuel = _extract_keyword(body, _FUEL)
    transmission = _extract_keyword(body, _TRANSMISSION)

    request_language = _contains_any(body, _REQUEST_PATTERNS)
    commission_language = _contains_any(body, _COMMISSION_PATTERNS)
    concrete_vehicle = bool(make or model)
    is_vehicle_request = bool(not negated and (request_language or concrete_vehicle) and concrete_vehicle)
    explicit_commission = bool(is_vehicle_request and commission_language)

    criteria: Dict[str, Any] = {}
    if make:
        criteria["make"] = make
    if model:
        criteria["model"] = model
    if year_min is not None:
        criteria["year_min"] = year_min
        criteria["year_max"] = year_max
    if budget is not None:
        criteria["budget_max_eur"] = budget
    if km_max is not None:
        criteria["km_max"] = km_max
    if fuel:
        criteria["fuel_type"] = fuel
    if transmission:
        criteria["transmission"] = transmission

    missing: list[str] = []
    if is_vehicle_request:
        if not make and not model:
            missing.append("make_model")
        if year_min is None:
            missing.append("year_range")
        if budget is None:
            missing.append("budget_max_eur")
        if km_max is None:
            missing.append("km_max")

    summary_parts: list[str] = []
    if make:
        summary_parts.append(make)
    if model:
        summary_parts.append(model)
    if year_min is not None:
        summary_parts.append(str(year_min) if year_min == year_max else f"{year_min}-{year_max}")
    if budget is not None:
        summary_parts.append(f"budget max EUR {budget:,}".replace(",", "."))
    if km_max is not None:
        summary_parts.append(f"max {km_max:,} km".replace(",", "."))
    if fuel:
        summary_parts.append(fuel)
    if transmission:
        summary_parts.append(transmission)

    return VehicleRequestCapture(
        message_id=message_id,
        criteria=criteria,
        is_vehicle_request=is_vehicle_request,
        explicit_commission=explicit_commission,
        summary=", ".join(summary_parts),
        missing_for_search=tuple(missing),
    )
