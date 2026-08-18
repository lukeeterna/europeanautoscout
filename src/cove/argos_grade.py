"""ARGOS Vehicle Grade — evidence-aware A-E grade.

The vehicle grade is one independent S292 dimension.  It is *not* dealer fit,
mandate confidence, deal economics, market confidence, or dossier readiness.
Unknown evidence never receives a neutral numeric value.  A grade is emitted
only when the minimum evidence contract is satisfied; otherwise the result is
``NO-VERDICT`` with explicit missing evidence.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

import duckdb
import requests

from src.cove.demand_contract import NOT_AVAILABLE, NO_VERDICT
from src.cove.photo_coverage import load_photo_coverage

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(_HERE, "data", "cove_tracker.duckdb")
WARRANTY_STATUS = "richiedere al venditore"

COMPONENT_WEIGHTS: Dict[str, float] = {
    "cove_confidence": 0.35,
    "fraud": 0.20,
    "data_completeness": 0.15,
    "photo_semantics": 0.15,
    "recall_evidence": 0.10,
    "km_history": 0.05,
}

COMPLETENESS_FIELDS = (
    "vin",
    "fuel_type",
    "transmission",
    "power_kw",
    "color",
    "mileage",
    "price_eu",
)

GRADE_THRESHOLDS = (
    ("A", 0.85),
    ("B", 0.75),
    ("C", 0.65),
    ("D", 0.55),
    ("E", 0.00),
)

BLOCKING_FRAUD_VALUES = {"SUSPICIOUS", "HIGH", "CRITICAL", "BLOCK", "BLOCKED", "REJECTED"}


def _known(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        return bool(stripped) and stripped not in {NOT_AVAILABLE, NO_VERDICT, "DA_VERIFICARE", "UNKNOWN"}
    if isinstance(value, (int, float)):
        return value != 0
    return True


def _bounded(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not 0.0 <= result <= 1.0:
        return None
    return result


def _score_to_grade(score: float) -> str:
    for grade, threshold in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "E"


def get_nhtsa_recalls(make: str, model: str, year: int) -> dict:
    """Query NHTSA without fabricating a zero-recall result on failures.

    NHTSA is a US-market source and therefore supporting evidence only.  Its
    absence is represented as unknown, not as a clean recall record.
    """
    if not _known(make) or not _known(model) or not year:
        return {
            "recall_count": None,
            "recalls": [],
            "source": "NHTSA",
            "error": "missing_make_model_year",
        }
    url = "https://api.nhtsa.gov/recalls/recallsByVehicle"
    try:
        response = requests.get(
            url,
            params={"make": make, "model": model, "modelYear": int(year)},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results")
        if not isinstance(results, list):
            return {
                "recall_count": None,
                "recalls": [],
                "source": "NHTSA",
                "error": "invalid_response_shape",
            }
        return {
            "recall_count": len(results),
            "recalls": [
                {
                    "component": item.get("component", ""),
                    "summary": item.get("summary", ""),
                    "consequence": item.get("consequence", ""),
                    "remedy": item.get("remedy", ""),
                    "nhtsaId": item.get("nhtsaId", ""),
                }
                for item in results
                if isinstance(item, Mapping)
            ],
            "source": "NHTSA_US_MARKET",
            "scope": "supporting evidence; not proof of EU recall clearance",
        }
    except requests.exceptions.Timeout:
        return {
            "recall_count": None,
            "recalls": [],
            "source": "NHTSA",
            "error": "timeout",
        }
    except (requests.exceptions.RequestException, ValueError) as exc:
        return {
            "recall_count": None,
            "recalls": [],
            "source": "NHTSA",
            "error": type(exc).__name__,
        }


def _score_fraud(value: Any) -> Optional[float]:
    if not _known(value):
        return None
    normalized = str(value).strip().upper()
    if normalized in {"CLEAN", "PASS", "OK", "NONE"}:
        return 1.0
    if normalized in {"WARNING", "REVIEW", "MEDIUM"}:
        return 0.5
    if normalized in BLOCKING_FRAUD_VALUES:
        return 0.0
    return None


def _score_completeness(listing: Mapping[str, Any]) -> Optional[float]:
    if not listing:
        return None
    known = sum(1 for field in COMPLETENESS_FIELDS if _known(listing.get(field)))
    return known / len(COMPLETENESS_FIELDS)


def _score_photo_semantics(photo_coverage: Mapping[str, Any]) -> Optional[float]:
    """Use semantic required-view coverage; raw image count is irrelevant."""
    if not photo_coverage.get("semantics_available"):
        return None
    missing = photo_coverage.get("missing_mandatory")
    if not isinstance(missing, (list, tuple)):
        return None
    mandatory_total = int(photo_coverage.get("mandatory_total") or 0)
    if mandatory_total <= 0:
        return None
    covered = mandatory_total - len(missing)
    return max(0.0, min(1.0, covered / mandatory_total))


def _score_recalls(recall_data: Mapping[str, Any]) -> Optional[float]:
    if recall_data.get("error"):
        return None
    count = recall_data.get("recall_count")
    if count is None:
        return None
    try:
        count_i = int(count)
    except (TypeError, ValueError):
        return None
    if count_i < 0:
        return None
    if count_i == 0:
        return 1.0
    if count_i <= 3:
        return 0.7
    return 0.4


def _score_km_history(vin_verified: Any, vin_consistent: Any) -> Optional[float]:
    """No static 0.5 for missing VIN evidence."""
    if not bool(vin_verified):
        return None
    if vin_consistent is True:
        return 1.0
    if vin_consistent is False:
        return 0.0
    return None


@dataclass(frozen=True)
class VehicleGradeResult:
    grade: str
    score: Optional[float]
    evidence_coverage: float
    components: Mapping[str, Mapping[str, Any]]
    missing_evidence: tuple[str, ...]
    blocking_reasons: tuple[str, ...]

    @property
    def has_verdict(self) -> bool:
        return self.grade != NO_VERDICT and self.score is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade,
            "score": self.score if self.score is not None else NOT_AVAILABLE,
            "evidence_coverage": self.evidence_coverage,
            "components": {key: dict(value) for key, value in self.components.items()},
            "missing_evidence": list(self.missing_evidence),
            "blocking_reasons": list(self.blocking_reasons),
            "has_verdict": self.has_verdict,
        }


def compute_vehicle_grade_from_evidence(
    *,
    cove_confidence: Any,
    fraud_overall: Any,
    listing_data: Mapping[str, Any],
    photo_coverage: Mapping[str, Any],
    recall_data: Mapping[str, Any],
    vin_verified: Any = False,
    vin_consistent: Any = None,
    min_evidence_coverage: float = 0.70,
) -> VehicleGradeResult:
    """Pure evidence aggregation for the independent vehicle-grade dimension.

    Required gates:
      * CoVe confidence known
      * fraud state known and non-blocking
      * semantic photo coverage available
      * at least ``min_evidence_coverage`` of weighted evidence known

    Unknown optional dimensions are omitted and known weights are renormalised;
    they are never filled with a neutral midpoint.
    """
    if not 0.0 <= float(min_evidence_coverage) <= 1.0:
        raise ValueError("min_evidence_coverage must be between 0 and 1")

    scores: Dict[str, Optional[float]] = {
        "cove_confidence": _bounded(cove_confidence),
        "fraud": _score_fraud(fraud_overall),
        "data_completeness": _score_completeness(listing_data),
        "photo_semantics": _score_photo_semantics(photo_coverage),
        "recall_evidence": _score_recalls(recall_data),
        "km_history": _score_km_history(vin_verified, vin_consistent),
    }

    missing = tuple(name for name, value in scores.items() if value is None)
    known_weight = sum(
        COMPONENT_WEIGHTS[name]
        for name, value in scores.items()
        if value is not None
    )
    total_weight = sum(COMPONENT_WEIGHTS.values())
    coverage = round(known_weight / total_weight, 6) if total_weight else 0.0

    blocking: list[str] = []
    if scores["cove_confidence"] is None:
        blocking.append("cove_confidence_missing")
    if scores["fraud"] is None:
        blocking.append("fraud_evidence_missing")
    elif scores["fraud"] == 0.0:
        blocking.append("fraud_blocking")
    if scores["photo_semantics"] is None:
        blocking.append("photo_semantics_missing")
    if coverage < min_evidence_coverage:
        blocking.append("insufficient_evidence_coverage")

    components: Dict[str, Dict[str, Any]] = {}
    for name, score in scores.items():
        components[name] = {
            "weight": COMPONENT_WEIGHTS[name],
            "score": score if score is not None else NOT_AVAILABLE,
            "known": score is not None,
        }

    if blocking:
        return VehicleGradeResult(
            grade=NO_VERDICT,
            score=None,
            evidence_coverage=coverage,
            components=components,
            missing_evidence=missing,
            blocking_reasons=tuple(blocking),
        )

    weighted_sum = sum(
        COMPONENT_WEIGHTS[name] * float(score)
        for name, score in scores.items()
        if score is not None
    )
    normalized_score = round(weighted_sum / known_weight, 4)
    grade = _score_to_grade(normalized_score)
    return VehicleGradeResult(
        grade=grade,
        score=normalized_score,
        evidence_coverage=coverage,
        components=components,
        missing_evidence=missing,
        blocking_reasons=(),
    )


def _table_columns(con: Any, table: str) -> set[str]:
    try:
        rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    except Exception:
        return set()
    return {str(row[1]) for row in rows if len(row) > 1}


def _latest_cove(con: Any, listing_id: str) -> Dict[str, Any]:
    columns = _table_columns(con, "cove_results")
    required = {"listing_id", "make", "model", "year", "confidence", "fraud_overall"}
    if not required.issubset(columns):
        return {}
    requested = [
        name for name in (
            "listing_id", "make", "model", "year", "km", "price", "source",
            "recommendation", "confidence", "fraud_overall", "analyzed_at",
        ) if name in columns
    ]
    order = " ORDER BY analyzed_at DESC" if "analyzed_at" in columns else ""
    projection = ", ".join(f'"{name}"' for name in requested)
    row = con.execute(
        f"SELECT {projection} FROM cove_results WHERE listing_id = ?{order} LIMIT 1",
        [listing_id],
    ).fetchone()
    return dict(zip(requested, row)) if row else {}


def _listing_row(con: Any, listing_id: str, cove: Mapping[str, Any]) -> Dict[str, Any]:
    columns = _table_columns(con, "vehicle_listings")
    if "listing_id" not in columns:
        return {
            "vin": None,
            "fuel_type": None,
            "transmission": None,
            "power_kw": None,
            "color": None,
            "mileage": cove.get("km"),
            "price_eu": cove.get("price"),
        }
    wanted = [
        name for name in (
            "vin", "fuel_type", "transmission", "power_kw", "color", "mileage",
            "price_eu", "vin_verified", "vin_verification_data", "recall_count",
        ) if name in columns
    ]
    projection = ", ".join(f'"{name}"' for name in wanted)
    row = con.execute(
        f"SELECT {projection} FROM vehicle_listings WHERE listing_id = ? LIMIT 1",
        [listing_id],
    ).fetchone()
    if row:
        result = dict(zip(wanted, row))
    else:
        result = {}
    result.setdefault("mileage", cove.get("km"))
    result.setdefault("price_eu", cove.get("price"))
    for key in COMPLETENESS_FIELDS:
        result.setdefault(key, None)
    return result


def _vin_evidence(listing: Mapping[str, Any]) -> tuple[bool, Optional[bool], Optional[Mapping[str, Any]]]:
    verified = bool(listing.get("vin_verified"))
    raw = listing.get("vin_verification_data")
    data: Optional[Mapping[str, Any]] = None
    if isinstance(raw, Mapping):
        data = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            decoded = json.loads(raw)
            data = decoded if isinstance(decoded, Mapping) else None
        except json.JSONDecodeError:
            data = None
    consistency: Optional[bool] = None
    if data:
        consistency_obj = data.get("consistency")
        if isinstance(consistency_obj, Mapping) and isinstance(consistency_obj.get("is_consistent"), bool):
            consistency = consistency_obj["is_consistent"]
    return verified, consistency, data


def compute_argos_grade(
    listing_id: str,
    db_path: str = DEFAULT_DB_PATH,
    *,
    recall_fetcher: Callable[[str, str, int], Mapping[str, Any]] = get_nhtsa_recalls,
) -> dict:
    """Compute evidence-aware ARGOS Vehicle Grade for one listing."""
    listing_id = str(listing_id or "").strip()
    analyzed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if not listing_id:
        return {"listing_id": NOT_AVAILABLE, "error": "listing_id is required", "analyzed_at": analyzed_at}

    con = duckdb.connect(db_path, read_only=True)
    try:
        cove = _latest_cove(con, listing_id)
        if not cove:
            return {
                "listing_id": listing_id,
                "error": f"Listing '{listing_id}' not found or CoVe schema incomplete",
                "analyzed_at": analyzed_at,
            }
        listing = _listing_row(con, listing_id, cove)
        coverage = load_photo_coverage(con, listing_id)
    finally:
        con.close()

    vin_verified, vin_consistent, vin_data = _vin_evidence(listing)
    db_recall_count = listing.get("recall_count")
    if db_recall_count is not None:
        recall_data: Mapping[str, Any] = {
            "recall_count": db_recall_count,
            "recalls": [],
            "source": "vehicle_listings.recall_count",
        }
        if vin_data:
            stored = vin_data.get("nhtsa_recalls")
            if isinstance(stored, Mapping):
                recall_data = {
                    "recall_count": stored.get("recall_count", db_recall_count),
                    "recalls": stored.get("recalls", []),
                    "source": "vin_verification_data.nhtsa_recalls",
                }
    else:
        recall_data = recall_fetcher(
            str(cove.get("make") or ""),
            str(cove.get("model") or ""),
            int(cove.get("year") or 0),
        )

    coverage_payload = coverage.to_dict()
    coverage_payload["mandatory_total"] = len(coverage.missing_mandatory) + (
        len(set(coverage.observed_views).intersection(set(
            ("front", "rear", "side_left", "side_right", "front_three_quarter",
             "rear_three_quarter", "interior_front", "dashboard")
        )))
    )
    # The invariant is eight mandatory views; keep the calculation explicit for
    # callers while avoiding dependence on raw image count.
    coverage_payload["mandatory_total"] = 8

    grade_result = compute_vehicle_grade_from_evidence(
        cove_confidence=cove.get("confidence"),
        fraud_overall=cove.get("fraud_overall"),
        listing_data=listing,
        photo_coverage=coverage_payload,
        recall_data=recall_data,
        vin_verified=vin_verified,
        vin_consistent=vin_consistent,
    )
    result = grade_result.to_dict()
    result.update(
        {
            "listing_id": listing_id,
            "make": cove.get("make") or NOT_AVAILABLE,
            "model": cove.get("model") or NOT_AVAILABLE,
            "year": cove.get("year") if cove.get("year") is not None else NOT_AVAILABLE,
            "photo_coverage": coverage.to_dict(),
            "recall_count": recall_data.get("recall_count", NOT_AVAILABLE),
            "recalls": recall_data.get("recalls", []),
            "recall_source": recall_data.get("source", NOT_AVAILABLE),
            "recall_scope": recall_data.get("scope", NOT_AVAILABLE),
            "vin_verified": vin_verified,
            "vin_consistency": vin_consistent if vin_consistent is not None else NOT_AVAILABLE,
            "warranty_status": WARRANTY_STATUS,
            "cove_recommendation": cove.get("recommendation") or NOT_AVAILABLE,
            "analyzed_at": analyzed_at,
            "score_semantics": "argos_vehicle_grade_only",
        }
    )
    return result


def persist_argos_grade(listing_id: str, result: Mapping[str, Any], db_path: str = DEFAULT_DB_PATH) -> None:
    """Persist only a real A-E verdict; NO-VERDICT is never stored as a grade."""
    grade = str(result.get("grade") or "")
    if grade not in {"A", "B", "C", "D", "E"}:
        raise ValueError("only A-E ARGOS Vehicle Grade verdicts may be persisted")
    with duckdb.connect(db_path) as con:
        columns = _table_columns(con, "vehicle_listings")
        if "argos_grade" not in columns:
            con.execute("ALTER TABLE vehicle_listings ADD COLUMN argos_grade VARCHAR")
        con.execute(
            "UPDATE vehicle_listings SET argos_grade = ? WHERE listing_id = ?",
            [grade, listing_id],
        )


def _print_result(result: Mapping[str, Any]) -> None:
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return
    print("=" * 60)
    print(f"ARGOS Vehicle Grade: {result.get('grade', NO_VERDICT)}")
    print(f"Score: {result.get('score', NOT_AVAILABLE)}")
    print(f"Evidence coverage: {result.get('evidence_coverage', 0):.0%}")
    print(f"Vehicle: {result.get('make', NOT_AVAILABLE)} {result.get('model', NOT_AVAILABLE)} {result.get('year', NOT_AVAILABLE)}")
    if result.get("blocking_reasons"):
        print("Blocked by: " + ", ".join(result["blocking_reasons"]))
    if result.get("missing_evidence"):
        print("Missing: " + ", ".join(result["missing_evidence"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute evidence-aware ARGOS Vehicle Grade A-E.")
    parser.add_argument("listing_id")
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--persist", action="store_true", help="persist A-E verdict to vehicle_listings")
    args = parser.parse_args()
    result = compute_argos_grade(args.listing_id, db_path=args.db)
    if args.persist:
        try:
            persist_argos_grade(args.listing_id, result, db_path=args.db)
        except ValueError as exc:
            print(f"NOT PERSISTED: {exc}")
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        _print_result(result)


if __name__ == "__main__":
    main()
