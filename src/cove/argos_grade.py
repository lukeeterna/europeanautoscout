"""
ARGOS Automotive — ARGOS GRADE A-E Calculator
Phase 03 — ARGOS GRADE + NHTSA Recall Integration

Computes a single letter grade (A-E) for a vehicle listing based on:
  35% CoVe confidence (from cove_results table)
  20% Fraud flags (CLEAN=1.0, WARNING=0.5, SUSPICIOUS=0.0)
  15% Data completeness (7 key fields in vehicle_listings)
  15% Photo count (vehicle_images table)
  10% Recall status (NHTSA API)
   5% KM history (static 0.5 — no free DE API)

Warranty: always "richiedere al venditore" — Phase 1 confirmed no free OEM API.

Usage:
    python3 src/cove/argos_grade.py fresh_84aec3405b5d
    python3 src/cove/argos_grade.py fresh_84aec3405b5d --db /path/to/cove_tracker.duckdb
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Optional

import duckdb
import requests

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# Grade weights (must sum to 1.0)
WEIGHT_COVE_CONFIDENCE: float = 0.35
WEIGHT_FRAUD:           float = 0.20
WEIGHT_COMPLETENESS:    float = 0.15
WEIGHT_PHOTOS:          float = 0.15
WEIGHT_RECALLS:         float = 0.10
WEIGHT_KM_HISTORY:      float = 0.05

# Completeness: these 7 fields are checked in vehicle_listings
COMPLETENESS_FIELDS = ["vin", "fuel_type", "transmission", "power_kw", "color", "mileage", "price_eu"]

# Grade thresholds
GRADE_THRESHOLDS = [
    ("A", 0.85),
    ("B", 0.75),
    ("C", 0.65),
    ("D", 0.55),
    ("E", 0.00),
]

# Default DB path (relative to this file)
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(_HERE, "data", "cove_tracker.duckdb")

# Warranty is always documented as this — no free OEM API exists (Phase 1 confirmed)
WARRANTY_STATUS = "richiedere al venditore"


# ─────────────────────────────────────────────────────────────────────────────
# NHTSA RECALL INTEGRATION (copied from TOOL_VALIDATION.md appendix — confirmed working)
# ─────────────────────────────────────────────────────────────────────────────

def get_nhtsa_recalls(make: str, model: str, year: int) -> dict:
    """Get recall data from NHTSA for a given make/model/year.

    Free REST API, no auth, no rate limits.
    Works for EU models sold in US market (BMW, Mercedes, Audi, Porsche, VW).
    Phase 1 confirmed: 7 recalls for BMW X3 2022.

    Args:
        make: Vehicle make, e.g. "BMW"
        model: Vehicle model, e.g. "X3"
        year: Model year as integer, e.g. 2022

    Returns:
        dict with keys:
            recall_count (int): number of open recalls
            recalls (list): list of recall dicts with component/summary/consequence/remedy/nhtsaId
            source (str): "NHTSA"
            error (str, optional): error message if request failed
    """
    url = "https://api.nhtsa.gov/recalls/recallsByVehicle"
    params = {"make": make, "model": model, "modelYear": year}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return {
            "recall_count": len(results),
            "recalls": [
                {
                    "component": r.get("component", ""),
                    "summary": r.get("summary", ""),
                    "consequence": r.get("consequence", ""),
                    "remedy": r.get("remedy", ""),
                    "nhtsaId": r.get("nhtsaId", ""),
                }
                for r in results
            ],
            "source": "NHTSA",
        }
    except requests.exceptions.Timeout:
        return {"recall_count": 0, "recalls": [], "source": "NHTSA", "error": "timeout"}
    except requests.exceptions.RequestException as exc:
        return {"recall_count": 0, "recalls": [], "source": "NHTSA", "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# SCORE COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def _score_cove_confidence(confidence: float) -> float:
    """Return confidence directly (already in 0.0-1.0 range)."""
    return max(0.0, min(1.0, float(confidence)))


def _score_fraud(fraud_overall: str) -> float:
    """Map fraud flag to score component."""
    mapping = {
        "CLEAN":      1.0,
        "WARNING":    0.5,
        "SUSPICIOUS": 0.0,
    }
    return mapping.get(str(fraud_overall).upper(), 0.5)


def _score_completeness(listing_row: dict) -> float:
    """Compute data completeness score based on 7 key fields."""
    filled = sum(
        1 for field in COMPLETENESS_FIELDS
        if listing_row.get(field) is not None and listing_row.get(field) != 0
    )
    return filled / len(COMPLETENESS_FIELDS)


def _score_photos(photo_count: int) -> float:
    """Score based on photo count."""
    if photo_count == 0:
        return 0.0
    elif photo_count <= 3:
        return 0.5
    else:
        return 1.0


def _score_recalls(recall_count: int) -> float:
    """Score based on NHTSA recall count (fewer = better)."""
    if recall_count == 0:
        return 1.0
    elif recall_count <= 3:
        return 0.7
    else:
        return 0.4


def _score_km_history(vin_verified: bool = False, vin_consistency: bool = True) -> float:
    """KM history score — boosted by VIN verification.

    If VIN verified + consistent: 0.8 (we confirmed the car is what it says)
    If VIN verified but inconsistent: 0.2 (RED FLAG)
    If VIN not verified: 0.5 (unknown — same as before)
    """
    if vin_verified and vin_consistency:
        return 0.8
    elif vin_verified and not vin_consistency:
        return 0.2  # VIN mismatch = likely fraud
    return 0.5


# ─────────────────────────────────────────────────────────────────────────────
# GRADE MAPPING
# ─────────────────────────────────────────────────────────────────────────────

def _score_to_grade(score: float) -> str:
    """Map weighted score (0.0-1.0) to letter grade A-E."""
    for grade, threshold in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "E"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN COMPUTE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def compute_argos_grade(listing_id: str, db_path: str = DEFAULT_DB_PATH) -> dict:
    """Compute ARGOS GRADE A-E for a listing.

    Fetches data from DuckDB (cove_results + vehicle_listings + vehicle_images)
    and calls NHTSA recall API. Returns a structured dict with grade, score,
    components, recall data, and warranty status.

    Weights:
      35% CoVe confidence (cove_results.confidence)
      20% Fraud flags (CLEAN=1.0, WARNING=0.5, SUSPICIOUS=0.0)
      15% Data completeness (7 key fields in vehicle_listings)
      15% Photo count (vehicle_images count)
      10% Recall status (NHTSA — 0=1.0, 1-3=0.7, 4+=0.4)
       5% KM history (static 0.5 — no free DE API)

    Grade mapping:
      A: score >= 0.85
      B: score >= 0.75
      C: score >= 0.65
      D: score >= 0.55
      E: score < 0.55

    Args:
        listing_id: Listing ID (e.g., "fresh_84aec3405b5d")
        db_path: Path to cove_tracker.duckdb

    Returns:
        dict with:
            grade (str): A-E letter grade
            score (float): Weighted composite score 0.0-1.0
            components (dict): Per-component scores and weights
            recall_count (int): NHTSA recall count
            recalls (list): NHTSA recall detail records
            warranty_status (str): Always "richiedere al venditore"
            listing_id (str): Input listing_id
            make, model, year (from DB)
            analyzed_at (str): ISO timestamp
            error (str, optional): If listing not found
    """
    analyzed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    con = duckdb.connect(db_path, read_only=True)
    try:
        # ── 1. Fetch cove_results row ─────────────────────────────────────────
        cove_row = con.execute(
            """
            SELECT listing_id, make, model, year, km, price, market_price,
                   source, recommendation, confidence, fraud_overall
            FROM cove_results
            WHERE listing_id = ?
            """,
            [listing_id],
        ).fetchone()

        if cove_row is None:
            return {
                "listing_id": listing_id,
                "error": f"Listing '{listing_id}' not found in cove_results",
                "analyzed_at": analyzed_at,
            }

        (db_listing_id, make, model, year, km, price, market_price,
         source, recommendation, confidence, fraud_overall) = cove_row

        # ── 2. Fetch vehicle_listings row ─────────────────────────────────────
        # Check if vin_verified column exists (S87+ schema)
        _has_vin_cols = False
        try:
            con.execute("SELECT vin_verified FROM vehicle_listings LIMIT 0")
            _has_vin_cols = True
        except Exception:
            pass

        if _has_vin_cols:
            vl_row = con.execute(
                """
                SELECT vin, fuel_type, transmission, power_kw, color, mileage, price_eu,
                       vin_verified, vin_verification_data, recall_count
                FROM vehicle_listings
                WHERE listing_id = ?
                """,
                [listing_id],
            ).fetchone()
        else:
            vl_row = con.execute(
                """
                SELECT vin, fuel_type, transmission, power_kw, color, mileage, price_eu
                FROM vehicle_listings
                WHERE listing_id = ?
                """,
                [listing_id],
            ).fetchone()

        vin_verified = False
        vin_verification_data = None
        vin_consistency = True
        db_recall_count = None

        if vl_row is not None:
            listing_data = {
                "vin": vl_row[0],
                "fuel_type": vl_row[1],
                "transmission": vl_row[2],
                "power_kw": vl_row[3],
                "color": vl_row[4],
                "mileage": vl_row[5],
                "price_eu": vl_row[6],
            }
            if _has_vin_cols and len(vl_row) > 7:
                vin_verified = bool(vl_row[7])
                if vl_row[8]:
                    try:
                        vin_verification_data = json.loads(vl_row[8]) if isinstance(vl_row[8], str) else vl_row[8]
                        # Check consistency from stored data
                        cons = vin_verification_data.get("consistency", {})
                        vin_consistency = cons.get("is_consistent", True)
                    except (json.JSONDecodeError, AttributeError):
                        pass
                if vl_row[9] is not None:
                    db_recall_count = int(vl_row[9])
        else:
            listing_data = {
                "vin": None,
                "fuel_type": None,
                "transmission": None,
                "power_kw": None,
                "color": None,
                "mileage": km,
                "price_eu": price,
            }

        # ── 3. Fetch photo count ──────────────────────────────────────────────
        photo_count_row = con.execute(
            "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?",
            [listing_id],
        ).fetchone()
        photo_count = photo_count_row[0] if photo_count_row else 0

    finally:
        con.close()

    # ── 4. NHTSA recalls ──────────────────────────────────────────────────────
    # Usa recall_count dal DB (salvato dall'enricher) se disponibile, altrimenti chiama API
    if db_recall_count is not None:
        recall_count = db_recall_count
        recall_data = {"recall_count": recall_count, "recalls": [], "source": "DB (vin_verification)"}
        # Estrai recall details dal vin_verification_data se disponibile
        if vin_verification_data:
            nhtsa_recalls = vin_verification_data.get("nhtsa_recalls") or {}
            recall_data["recalls"] = nhtsa_recalls.get("recalls", [])
    else:
        recall_data = get_nhtsa_recalls(make or "BMW", model or "X3", year or 2022)
        recall_count = recall_data.get("recall_count", 0)

    # ── 5. Compute component scores ───────────────────────────────────────────
    s_cove    = _score_cove_confidence(confidence)
    s_fraud   = _score_fraud(fraud_overall)
    s_compl   = _score_completeness(listing_data)
    s_photos  = _score_photos(photo_count)
    s_recalls = _score_recalls(recall_count)
    s_km      = _score_km_history(vin_verified=vin_verified, vin_consistency=vin_consistency)

    # ── 6. Weighted composite score ───────────────────────────────────────────
    total_score = (
        WEIGHT_COVE_CONFIDENCE * s_cove +
        WEIGHT_FRAUD           * s_fraud +
        WEIGHT_COMPLETENESS    * s_compl +
        WEIGHT_PHOTOS          * s_photos +
        WEIGHT_RECALLS         * s_recalls +
        WEIGHT_KM_HISTORY      * s_km
    )
    total_score = round(total_score, 4)

    # ── 7. Letter grade ───────────────────────────────────────────────────────
    grade = _score_to_grade(total_score)

    return {
        "listing_id": listing_id,
        "make": make,
        "model": model,
        "year": year,
        "grade": grade,
        "score": total_score,
        "components": {
            "cove_confidence": {
                "weight": WEIGHT_COVE_CONFIDENCE,
                "raw_value": round(float(confidence), 4),
                "score": round(s_cove, 4),
                "weighted": round(WEIGHT_COVE_CONFIDENCE * s_cove, 4),
            },
            "fraud_flags": {
                "weight": WEIGHT_FRAUD,
                "raw_value": str(fraud_overall),
                "score": round(s_fraud, 4),
                "weighted": round(WEIGHT_FRAUD * s_fraud, 4),
            },
            "data_completeness": {
                "weight": WEIGHT_COMPLETENESS,
                "raw_value": f"{int(s_compl * len(COMPLETENESS_FIELDS))}/{len(COMPLETENESS_FIELDS)} fields",
                "score": round(s_compl, 4),
                "weighted": round(WEIGHT_COMPLETENESS * s_compl, 4),
            },
            "photo_count": {
                "weight": WEIGHT_PHOTOS,
                "raw_value": photo_count,
                "score": round(s_photos, 4),
                "weighted": round(WEIGHT_PHOTOS * s_photos, 4),
            },
            "recall_status": {
                "weight": WEIGHT_RECALLS,
                "raw_value": f"{recall_count} recalls (NHTSA)",
                "score": round(s_recalls, 4),
                "weighted": round(WEIGHT_RECALLS * s_recalls, 4),
            },
            "km_history": {
                "weight": WEIGHT_KM_HISTORY,
                "raw_value": f"vin_verified={vin_verified}, consistent={vin_consistency}",
                "score": round(s_km, 4),
                "weighted": round(WEIGHT_KM_HISTORY * s_km, 4),
            },
        },
        "recall_count": recall_count,
        "recalls": recall_data.get("recalls", []),
        "recall_source": recall_data.get("source", "NHTSA"),
        "vin_verified": vin_verified,
        "vin_consistency": vin_consistency,
        "vin_verification": {
            "verified": vin_verified,
            "consistent": vin_consistency,
            "alerts": (vin_verification_data or {}).get("alerts", []),
            "nhtsa_decode": {
                "make": ((vin_verification_data or {}).get("nhtsa_decode") or {}).get("make", ""),
                "model": ((vin_verification_data or {}).get("nhtsa_decode") or {}).get("model", ""),
                "year": ((vin_verification_data or {}).get("nhtsa_decode") or {}).get("year", 0),
                "fuel_type": ((vin_verification_data or {}).get("nhtsa_decode") or {}).get("fuel_type", ""),
                "body_type": ((vin_verification_data or {}).get("nhtsa_decode") or {}).get("body_type", ""),
            } if vin_verification_data else None,
            "freevindecoder": {
                "manufacturer": ((vin_verification_data or {}).get("freevindecoder") or {}).get("make", ""),
            } if vin_verification_data else None,
        },
        "warranty_status": WARRANTY_STATUS,
        "recommendation": recommendation,
        "analyzed_at": analyzed_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def _print_result(result: dict) -> None:
    """Print ARGOS GRADE result in human-readable format."""
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    grade = result["grade"]
    score = result["score"]
    make  = result.get("make", "?")
    model = result.get("model", "?")
    year  = result.get("year", "?")

    print("=" * 60)
    print(f"  ARGOS GRADE: {grade}  (score: {score:.4f})")
    print(f"  Vehicle: {make} {model} {year}")
    print(f"  Listing: {result['listing_id']}")
    print("=" * 60)
    print()
    print("Score breakdown:")
    for key, comp in result["components"].items():
        label = key.replace("_", " ").title()
        print(
            f"  {label:20s}  weight={comp['weight']:.0%}  "
            f"score={comp['score']:.2f}  "
            f"weighted={comp['weighted']:.4f}  "
            f"({comp['raw_value']})"
        )
    print()
    print(f"  Recalls: {result['recall_count']} (source: {result['recall_source']})")
    if result["recalls"]:
        for i, r in enumerate(result["recalls"][:3], 1):
            comp = r.get("component", "—")[:60]
            print(f"    {i}. {comp}")
        if len(result["recalls"]) > 3:
            print(f"    ... and {len(result['recalls']) - 3} more")
    print()
    print(f"  Warranty: {result['warranty_status']}")
    print(f"  CoVe recommendation: {result.get('recommendation', '?')}")
    print(f"  Analyzed at: {result['analyzed_at']}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute ARGOS GRADE A-E for a vehicle listing."
    )
    parser.add_argument(
        "listing_id",
        help="Listing ID from cove_results (e.g. fresh_84aec3405b5d)",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_PATH,
        help=f"Path to cove_tracker.duckdb (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of human-readable format",
    )
    args = parser.parse_args()

    result = compute_argos_grade(args.listing_id, db_path=args.db)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_result(result)


if __name__ == "__main__":
    main()
