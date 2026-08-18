"""ARGOS Automotive — evidence-safe dossier readiness contract.

The dossier is a delivery gate, not a marketing score.  It may summarise facts
that are present in CoVe/vehicle data, but it must never fabricate economics,
turn a contact attempt into seller confirmation, or treat a raw photo count as
proof that required views exist.

S292 business authority: docs/ROADMAP.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

try:
    from src.cove.demand_contract import (
        DemandEvidence,
        NOT_AVAILABLE,
        NO_VERDICT,
        require_listing_authorization,
    )
except ModuleNotFoundError:  # CLI compatibility when executed from src/cove
    from demand_contract import (  # type: ignore
        DemandEvidence,
        NOT_AVAILABLE,
        NO_VERDICT,
        require_listing_authorization,
    )


class ReadinessLevel(Enum):
    NOT_READY = "NOT_READY"
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    DEALER_READY = "DEALER_READY"


MANDATORY = {
    "make_model_year": "Marca, modello e anno presenti",
    "price_eu": "Prezzo di acquisizione osservato",
    "mileage": "Chilometraggio osservato",
    "photo_views": "Copertura semantica delle viste foto obbligatorie",
    "argos_grade": "ARGOS Vehicle Grade disponibile come dimensione separata",
    "deal_economics": "Economica deal supportata da evidenza, senza costi/fallback inventati",
    "no_fraud_flags": "Nessun fraud flag bloccante",
    "demand_authorized": "Mandato/richiesta dealer S292 autorizzata",
}

IMPORTANT = {
    "vin_verified": "VIN verificato",
    "seller_confirmed_available": "Disponibilita' confermata esplicitamente dal venditore",
    "service_history": "Storico manutenzione documentato",
    "hu_date": "Data/referenza ultima revisione HU/TUV",
    "accident_history": "Storico incidenti/danni dichiarato",
    "previous_owners": "Numero proprietari precedenti",
}

OPTIONAL = {
    "underbody_photos": "Foto sottoscocca",
    "tire_condition": "Condizione pneumatici",
    "equipment_list": "Lista optional",
    "num_keys": "Numero chiavi",
    "next_service_due": "Prossimo tagliando",
    "transport_quote": "Preventivo trasporto documentato",
}

PHOTO_VIEWS_MANDATORY = (
    "front",
    "rear",
    "side_left",
    "side_right",
    "front_three_quarter",
    "rear_three_quarter",
    "interior_front",
    "dashboard",
)
PHOTO_VIEWS_DEALER_READY = PHOTO_VIEWS_MANDATORY + (
    "interior_rear",
    "trunk",
    "engine",
    "wheels_front",
)

BLOCKING_FRAUD_VALUES = {
    "WARNING",
    "SUSPICIOUS",
    "HIGH",
    "CRITICAL",
    "BLOCK",
    "BLOCKED",
    "FAIL",
}


def _known(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() not in {NOT_AVAILABLE, NO_VERDICT, "DA_VERIFICARE"}
    return True


def _truthy_db(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "si", "sì", "verified", "confirmed"}
    return bool(value)


def _safe_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _table_columns(con: Any, table: str) -> Set[str]:
    try:
        rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    except Exception:
        return set()
    return {str(row[1]) for row in rows if len(row) > 1}


def _fetch_row_as_dict(con: Any, table: str, listing_id: str) -> Dict[str, Any]:
    columns = _table_columns(con, table)
    if not columns or "listing_id" not in columns:
        return {}
    ordered = sorted(columns)
    select_cols = ", ".join(f'"{name}"' for name in ordered)
    row = con.execute(
        f'SELECT {select_cols} FROM "{table}" WHERE listing_id = ? LIMIT 1',
        [listing_id],
    ).fetchone()
    return dict(zip(ordered, row)) if row else {}


def _first_known(mapping: Mapping[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name in mapping and _known(mapping[name]):
            return mapping[name]
    return None


def _extract_photo_views(con: Any, listing_id: str) -> tuple[int, Set[str], bool]:
    """Return (count, semantic views, semantics_available).

    Older rows use image_type='listing', which proves only that an image exists.
    It must not be promoted to a front/rear/interior observation.  Semantic
    coverage becomes available only when a recognised view label is persisted.
    """
    columns = _table_columns(con, "vehicle_images")
    if not columns or "listing_id" not in columns:
        return 0, set(), False

    label_column = next(
        (name for name in ("view", "view_type", "photo_view", "semantic_view", "image_type") if name in columns),
        None,
    )
    if not label_column:
        count = con.execute(
            "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?", [listing_id]
        ).fetchone()[0]
        return int(count or 0), set(), False

    rows = con.execute(
        f'SELECT "{label_column}" FROM vehicle_images WHERE listing_id = ?', [listing_id]
    ).fetchall()
    count = len(rows)
    allowed = set(PHOTO_VIEWS_DEALER_READY) | {"underbody", "wheels_rear", "service_book", "hu_report", "damage_detail", "infotainment"}
    views = {
        str(row[0]).strip().lower()
        for row in rows
        if row and _known(row[0]) and str(row[0]).strip().lower() in allowed
    }
    return count, views, bool(views)


def _extract_argos_grade(cove: Mapping[str, Any], listing: Mapping[str, Any]) -> Optional[str]:
    value = _first_known(
        {**dict(cove), **dict(listing)},
        ("argos_grade", "vehicle_grade", "grade"),
    )
    if value is None:
        return None
    grade = str(value).strip().upper()
    return grade if grade in {"A", "B", "C", "D", "E"} else None


def _extract_confirmed_availability(listing: Mapping[str, Any]) -> bool:
    """A sent message is never evidence of availability."""
    for key in (
        "seller_confirmed_available",
        "availability_confirmed",
        "seller_availability_confirmed",
    ):
        if key in listing:
            return _truthy_db(listing[key])
    status = _first_known(listing, ("availability_status", "seller_availability"))
    return str(status or "").strip().upper() in {"AVAILABLE_CONFIRMED", "CONFIRMED_AVAILABLE"}


def _extract_evidence_flags(listing: Mapping[str, Any]) -> Dict[str, bool]:
    aliases = {
        "vin_verified": ("vin_verified",),
        "service_history": ("service_history_verified", "service_history_present"),
        "hu_date": ("hu_date", "tuv_date", "inspection_date"),
        "accident_history": ("accident_history", "accident_history_verified", "accident_free_confirmed"),
        "previous_owners": ("previous_owners", "owner_count"),
        "tire_condition": ("tire_condition", "tire_type_condition"),
        "equipment_list": ("equipment_list", "equipment"),
        "num_keys": ("num_keys", "keys_count"),
        "next_service_due": ("next_service_due",),
        "transport_quote": ("transport_quote", "transport_quote_eur"),
    }
    result: Dict[str, bool] = {}
    for target, candidates in aliases.items():
        value = _first_known(listing, candidates)
        if target == "vin_verified":
            result[target] = _truthy_db(value)
        else:
            result[target] = _known(value)
    return result


def _normalise_economics(economics: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Accept only explicit, traceable economics supplied by the economics layer."""
    if not economics:
        return {
            "verdict": NO_VERDICT,
            "net_margin_eur": None,
            "evidence_id": NOT_AVAILABLE,
            "source": NOT_AVAILABLE,
        }
    source = str(economics.get("source") or "").strip()
    evidence_id = str(economics.get("evidence_id") or "").strip()
    margin = _safe_float(economics.get("net_margin_eur"))
    if not source or not evidence_id or margin is None:
        return {
            "verdict": NO_VERDICT,
            "net_margin_eur": None,
            "evidence_id": evidence_id or NOT_AVAILABLE,
            "source": source or NOT_AVAILABLE,
        }
    verdict = str(economics.get("verdict") or "").strip().upper()
    if verdict not in {"PROCEED", "REVIEW", "REJECT"}:
        verdict = "PROCEED" if margin > 0 else "REJECT"
    return {
        "verdict": verdict,
        "net_margin_eur": margin,
        "evidence_id": evidence_id,
        "source": source,
    }


@dataclass
class DossierReadiness:
    listing_id: str
    level: ReadinessLevel
    dossier_readiness: Optional[float]
    ready: bool
    missing_mandatory: List[str] = field(default_factory=list)
    missing_important: List[str] = field(default_factory=list)
    missing_optional: List[str] = field(default_factory=list)
    photo_count: int = 0
    observed_photo_views: List[str] = field(default_factory=list)
    missing_photo_views: List[str] = field(default_factory=list)
    net_margin_eur: Optional[float] = None
    economics_verdict: str = NO_VERDICT
    next_action: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def score(self) -> Optional[int]:
        """Compatibility view: dossier completeness only, never a global ARGOS score."""
        if self.dossier_readiness is None:
            return None
        return int(round(self.dossier_readiness * 100))

    @property
    def margin_net(self) -> Optional[float]:
        """Compatibility alias without fabricating a zero when economics is unknown."""
        return self.net_margin_eur

    def as_dict(self) -> Dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "level": self.level.value,
            "ready": self.ready,
            "dossier_readiness": self.dossier_readiness,
            "score_semantics": "dossier_readiness_only",
            "missing_mandatory": list(self.missing_mandatory),
            "missing_important": list(self.missing_important),
            "missing_optional": list(self.missing_optional),
            "photo_count": self.photo_count,
            "observed_photo_views": list(self.observed_photo_views),
            "missing_photo_views": list(self.missing_photo_views),
            "net_margin_eur": self.net_margin_eur if self.net_margin_eur is not None else NOT_AVAILABLE,
            "economics_verdict": self.economics_verdict,
            "next_action": self.next_action,
            "details": dict(self.details),
        }


def check_dossier_readiness(
    listing_id: str,
    db_path: Optional[str] = None,
    *,
    demand_evidence: Optional[DemandEvidence] = None,
    economics: Optional[Mapping[str, Any]] = None,
) -> DossierReadiness:
    """Evaluate dealer-delivery readiness with fail-closed evidence semantics.

    The function is intentionally useful before a dossier is ready: callers may
    inspect ``missing_*`` without satisfying the demand gate.  ``ready=True`` is
    impossible, however, until S292 authorization is present.
    """
    import duckdb

    listing_id = str(listing_id or "").strip()
    if not listing_id:
        raise ValueError("listing_id is required")
    if db_path is None:
        db_path = str(Path(__file__).parent / "data" / "cove_tracker.duckdb")

    con = duckdb.connect(db_path, read_only=True)
    try:
        cove = _fetch_row_as_dict(con, "cove_results", listing_id)
        listing = _fetch_row_as_dict(con, "vehicle_listings", listing_id)
        photo_count, photo_views, semantics_available = _extract_photo_views(con, listing_id)
    finally:
        con.close()

    if not cove:
        return DossierReadiness(
            listing_id=listing_id,
            level=ReadinessLevel.NOT_READY,
            dossier_readiness=0.0,
            ready=False,
            missing_mandatory=["listing_not_found"],
            next_action="Eseguire CoVe sul listing prima del dossier",
        )

    merged = {**cove, **listing}
    make = _first_known(merged, ("make",))
    model = _first_known(merged, ("model",))
    year = _first_known(merged, ("year",))
    km = _first_known(merged, ("km", "mileage"))
    price = _safe_float(_first_known(merged, ("price", "price_eu")))
    vin = _first_known(merged, ("vin",))
    fraud = _first_known(cove, ("fraud_overall", "fraud_status"))
    cove_confidence = _safe_float(_first_known(cove, ("confidence", "cove_confidence")))
    grade = _extract_argos_grade(cove, listing)
    flags = _extract_evidence_flags(listing)
    confirmed_available = _extract_confirmed_availability(listing)
    economics_data = _normalise_economics(economics)

    missing_mandatory: List[str] = []
    if not (make and model and year):
        missing_mandatory.append("make_model_year")
    if price is None or price <= 0:
        missing_mandatory.append("price_eu")
    if _safe_float(km) is None or float(km) < 0:
        missing_mandatory.append("mileage")

    required_views = set(PHOTO_VIEWS_MANDATORY)
    missing_views = sorted(required_views - photo_views)
    if not semantics_available or missing_views:
        missing_mandatory.append("photo_views")

    if grade is None:
        missing_mandatory.append("argos_grade")

    if economics_data["verdict"] == NO_VERDICT:
        missing_mandatory.append("deal_economics")
    elif economics_data["verdict"] == "REJECT":
        missing_mandatory.append("deal_economics")

    if str(fraud or "").strip().upper() in BLOCKING_FRAUD_VALUES:
        missing_mandatory.append("no_fraud_flags")

    demand_authorized = False
    demand_error = NOT_AVAILABLE
    try:
        require_listing_authorization(demand_evidence, listing_id)
        demand_authorized = True
    except (PermissionError, TypeError, ValueError) as exc:
        demand_error = str(exc)
        missing_mandatory.append("demand_authorized")

    missing_important: List[str] = []
    if not flags["vin_verified"]:
        missing_important.append("vin_verified")
    if not confirmed_available:
        missing_important.append("seller_confirmed_available")
    for key in ("service_history", "hu_date", "accident_history", "previous_owners"):
        if not flags[key]:
            missing_important.append(key)

    missing_optional: List[str] = []
    if "underbody" not in photo_views:
        missing_optional.append("underbody_photos")
    for key in ("tire_condition", "equipment_list", "num_keys", "next_service_due", "transport_quote"):
        if not flags[key]:
            missing_optional.append(key)

    # Readiness is a transparent checklist ratio, not a blended business score.
    all_checks = list(MANDATORY) + list(IMPORTANT)
    failed = len(set(missing_mandatory)) + len(set(missing_important))
    readiness = max(0.0, min(1.0, (len(all_checks) - failed) / len(all_checks)))

    if missing_mandatory:
        level = ReadinessLevel.NOT_READY
    elif missing_important:
        level = ReadinessLevel.REVIEW
    else:
        level = ReadinessLevel.DEALER_READY

    if "demand_authorized" in missing_mandatory:
        next_action = "Ottenere/registrare commissione dealer S292 verificabile"
    elif "deal_economics" in missing_mandatory:
        next_action = "Calcolare deal economics da costi e riferimenti documentati"
    elif "photo_views" in missing_mandatory:
        next_action = "Acquisire e classificare le viste foto mancanti"
    elif "argos_grade" in missing_mandatory:
        next_action = "Calcolare e persistere ARGOS Vehicle Grade"
    elif missing_mandatory:
        next_action = f"Risolvere: {missing_mandatory[0]}"
    elif missing_important:
        next_action = f"Ottenere evidenza: {IMPORTANT[missing_important[0]]}"
    else:
        next_action = "Dossier pronto per generazione artefatto dealer"

    return DossierReadiness(
        listing_id=listing_id,
        level=level,
        dossier_readiness=readiness,
        ready=(level == ReadinessLevel.DEALER_READY and demand_authorized),
        missing_mandatory=list(dict.fromkeys(missing_mandatory)),
        missing_important=list(dict.fromkeys(missing_important)),
        missing_optional=list(dict.fromkeys(missing_optional)),
        photo_count=photo_count,
        observed_photo_views=sorted(photo_views),
        missing_photo_views=missing_views if semantics_available else list(PHOTO_VIEWS_MANDATORY),
        net_margin_eur=economics_data["net_margin_eur"],
        economics_verdict=economics_data["verdict"],
        next_action=next_action,
        details={
            "make": make or NOT_AVAILABLE,
            "model": model or NOT_AVAILABLE,
            "year": year if _known(year) else NOT_AVAILABLE,
            "km": km if _known(km) else NOT_AVAILABLE,
            "price_eu": price if price is not None else NOT_AVAILABLE,
            "vin": vin or NOT_AVAILABLE,
            "vin_verified": flags["vin_verified"],
            "seller_confirmed_available": confirmed_available,
            "argos_grade": grade or NOT_AVAILABLE,
            "cove_confidence": cove_confidence if cove_confidence is not None else NOT_AVAILABLE,
            "fraud_overall": fraud or NOT_AVAILABLE,
            "photo_semantics_available": semantics_available,
            "demand_authorized": demand_authorized,
            "demand_gate_error": demand_error,
            "economics_source": economics_data["source"],
            "economics_evidence_id": economics_data["evidence_id"],
        },
    )


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 src/cove/dossier_standard.py <listing_id>")
        print("CLI is read-only and cannot mark a dossier dealer-ready without S292 evidence.")
        sys.exit(1)

    result = check_dossier_readiness(sys.argv[1])
    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False, default=str))
    # A CLI check without demand/economics evidence is expected to be non-ready.
    sys.exit(0)
