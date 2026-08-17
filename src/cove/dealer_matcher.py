"""ARGOS dealer/vehicle fit adapter — S292 demand-side runtime.

This module is intentionally *not* a vehicle-first decision engine anymore.
A dealer must first establish credibility and directly commission a vehicle.
Only then may this compatibility API rank dealer/vehicle fit.

Business authority: docs/ROADMAP.md, S292.
"""

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from src.cove.demand_contract import (
        ArgosScorecard,
        DemandEvidence,
        mandate_confidence_from_evidence,
        require_sourcing_authorization,
    )
except ModuleNotFoundError:  # CLI compatibility when executed from src/cove
    from demand_contract import (  # type: ignore
        ArgosScorecard,
        DemandEvidence,
        mandate_confidence_from_evidence,
        require_sourcing_authorization,
    )

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DUCKDB_PATH = str(SCRIPT_DIR / "data" / "cove_tracker.duckdb")
CRM_DB_PATH = os.environ.get(
    "ARGOS_DB_PATH",
    os.path.expanduser("~/Documents/app-antigravity-auto/dealer_network.sqlite"),
)
if not os.path.exists(CRM_DB_PATH):
    alt = str(PROJECT_ROOT / "dealer_network.sqlite")
    if os.path.exists(alt):
        CRM_DB_PATH = alt

PIPELINE_ACTIVE = {"NEW", "CONTACTED", "REPLIED", "INTERESTED", "NEGOTIATION"}


def get_active_dealers(crm_path: str = CRM_DB_PATH) -> List[Dict]:
    """Read active dealers without inferring mandate or demand from CRM stage."""
    if not os.path.exists(crm_path):
        return []

    con = sqlite3.connect(crm_path)
    con.row_factory = sqlite3.Row
    try:
        tables = [
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        if "dealers" not in tables:
            return []
        rows = con.execute(
            """
            SELECT dealer_id, name, city, province, region, brands, stock_size,
                   premium_pct, tier, archetype, pipeline_status, score_fit
            FROM dealers
            WHERE pipeline_status IN ('NEW','CONTACTED','REPLIED','INTERESTED','NEGOTIATION')
            ORDER BY tier ASC, score_fit DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []
    finally:
        con.close()


def get_vehicle_data(listing_id: str, db_path: str = DUCKDB_PATH) -> Optional[Dict]:
    """Return observed/derived vehicle data. Missing market price stays missing."""
    import duckdb

    con = duckdb.connect(db_path, read_only=True)
    try:
        row = con.execute(
            """
            SELECT cr.listing_id, cr.make, cr.model, cr.year, cr.km, cr.price,
                   cr.market_price, cr.confidence, cr.fraud_overall,
                   vl.fuel_type, vl.color
            FROM cove_results cr
            LEFT JOIN vehicle_listings vl ON cr.listing_id = vl.listing_id
            WHERE cr.listing_id = ?
            """,
            [listing_id],
        ).fetchone()
        if not row:
            return None
        return {
            "listing_id": row[0],
            "make": row[1],
            "model": row[2],
            "year": row[3],
            "km": row[4],
            "price_eu": float(row[5]) if row[5] is not None else None,
            "market_price_it": float(row[6]) if row[6] is not None else None,
            "confidence": float(row[7]) if row[7] is not None else None,
            "fraud": row[8],
            "fuel_type": row[9],
            "color": row[10],
        }
    finally:
        con.close()


def _dealer_brands(dealer: Dict) -> List[str]:
    raw = dealer.get("brands", "[]")
    try:
        values = json.loads(raw) if isinstance(raw, str) else (raw or [])
    except (json.JSONDecodeError, TypeError):
        values = []
    return [str(value).strip().upper() for value in values if str(value).strip()]


def _brand_fit(vehicle: Dict, dealer: Dict) -> Optional[float]:
    make = str(vehicle.get("make") or "").strip().upper()
    brands = _dealer_brands(dealer)
    if not make or not brands:
        return None
    return 1.0 if make in brands else 0.0


def _deal_economics(vehicle: Dict) -> Optional[float]:
    """Evidence-safe economics signal; returns None when a market reference is absent.

    It intentionally does not inject historical fixed logistics costs or a fabricated
    market-price uplift. Full deal economics belong to the CoVe economics layer.
    """
    acquisition = vehicle.get("price_eu")
    market = vehicle.get("market_price_it")
    if acquisition is None or market is None or market <= 0:
        return None
    spread_pct = (market - acquisition) / market
    return max(0.0, min(1.0, spread_pct / 0.20))


def compute_match_score(
    vehicle: Dict,
    dealer: Dict,
    evidence: DemandEvidence,
) -> Dict:
    """Compute dealer fit *after* S292 mandate authorization.

    Legacy key ``score`` is retained for compatibility, but it is only dealer_fit.
    Independent confidence/economics dimensions are exposed in ``scorecard`` and are
    never silently merged into a single truth score.
    """
    require_sourcing_authorization(evidence)

    brand_fit = _brand_fit(vehicle, dealer)
    dealer_fit = brand_fit
    economics = _deal_economics(vehicle)
    cove_confidence = vehicle.get("confidence")
    if cove_confidence is not None:
        cove_confidence = max(0.0, min(1.0, float(cove_confidence)))

    scorecard = ArgosScorecard(
        dealer_fit=dealer_fit,
        mandate_confidence=mandate_confidence_from_evidence(evidence),
        cove_confidence=cove_confidence,
        deal_economics=economics,
    )

    reasons: List[str] = []
    if brand_fit is None:
        reasons.append("brand fit n/d: dealer or vehicle brand evidence missing")
    elif brand_fit == 1.0:
        reasons.append("observed brand is present in dealer stock profile")
    else:
        reasons.append("observed brand is not present in dealer stock profile")
    reasons.append("sourcing authorized by direct dealer commission evidence")

    return {
        "dealer_id": dealer["dealer_id"],
        "dealer_name": dealer.get("name") or "n/d",
        "city": dealer.get("city") or "n/d",
        "score": dealer_fit,
        "score_semantics": "dealer_fit_only",
        "scorecard": scorecard.as_dict(display_missing=True),
        "evidence_id": evidence.evidence_id,
        "reasons": reasons,
    }


def match_vehicle_to_dealers(
    listing_id: str,
    db_path: str = DUCKDB_PATH,
    crm_path: str = CRM_DB_PATH,
    min_score: float = 0.0,
    evidence: Optional[DemandEvidence] = None,
) -> List[Dict]:
    """Compatibility API, now fail-closed on the S292 demand gate.

    ``evidence`` is mandatory in practice. Keeping it optional in the signature avoids
    import-time breakage for older callers while making old vehicle-first execution
    fail closed with PermissionError instead of silently sourcing.
    """
    authorized = require_sourcing_authorization(evidence)
    vehicle = get_vehicle_data(listing_id, db_path)
    if not vehicle:
        return []

    dealers = [
        dealer
        for dealer in get_active_dealers(crm_path)
        if str(dealer.get("dealer_id")) == str(authorized.dealer_id)
    ]
    if not dealers:
        return []

    matches = []
    for dealer in dealers:
        result = compute_match_score(vehicle, dealer, authorized)
        score = result["score"]
        if score is None or score >= min_score:
            matches.append(result)

    # Unknown dealer_fit is not converted to a neutral numeric score.
    matches.sort(key=lambda item: item["score"] if item["score"] is not None else -1.0, reverse=True)
    return matches


def freshness_check(listing_id: str, db_path: str = DUCKDB_PATH) -> Dict:
    """Check listing freshness without treating request failure as sold."""
    import duckdb
    from datetime import datetime, timezone

    con = duckdb.connect(db_path, read_only=True)
    try:
        row = con.execute(
            "SELECT detail_url FROM vehicle_listings WHERE listing_id = ?", [listing_id]
        ).fetchone()
    finally:
        con.close()

    if not row or not row[0]:
        return {"available": None, "reason": "no_detail_url"}

    url = row[0]
    try:
        import requests

        response = requests.head(
            url,
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
        )
        if response.status_code == 200:
            available: Optional[bool] = True
        elif response.status_code in (404, 410):
            available = False
        else:
            available = None
        return {
            "available": available,
            "status_code": response.status_code,
            "url": url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        return {"available": None, "error": str(exc)}


if __name__ == "__main__":
    print(
        "dealer_matcher.py is no longer a vehicle-first CLI. "
        "Use the demand-side orchestrator with direct dealer mandate evidence."
    )
    sys.exit(2)
