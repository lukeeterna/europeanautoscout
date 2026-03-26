"""
dealer_matcher.py — ARGOS Dealer-Vehicle Matching Engine
CoVe 2026 | Enterprise Grade

Matches DOSSIER_READY vehicles to the best dealer from CRM based on:
  30% Brand affinity (dealer already sells this make)
  25% Price range fit (vehicle price vs dealer's stock bracket)
  20% Margin potential (higher margin → higher priority)
  15% Geographic relevance (model popularity in dealer's region)
  10% Relationship stage (TIER0 > TIER1 > TIER2)

Usage:
  from src.cove.dealer_matcher import match_vehicle_to_dealers

  matches = match_vehicle_to_dealers(listing_id, db_path, crm_db_path)
  # Returns sorted list: [{"dealer_id": ..., "score": 0.85, "reasons": [...]}, ...]

CLI:
  python3 src/cove/dealer_matcher.py <listing_id>
  python3 src/cove/dealer_matcher.py --all-ready   # Match all DOSSIER_READY vehicles
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DUCKDB_PATH = str(SCRIPT_DIR / "data" / "cove_tracker.duckdb")
CRM_DB_PATH = os.environ.get(
    'ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite')
)
# Fallback: check project root
if not os.path.exists(CRM_DB_PATH):
    alt = str(PROJECT_ROOT / "dealer_network.sqlite")
    if os.path.exists(alt):
        CRM_DB_PATH = alt

# Weights
W_BRAND = 0.30
W_PRICE = 0.25
W_MARGIN = 0.20
W_GEO = 0.15
W_TIER = 0.10

TIER_SCORES = {"TIER0": 1.0, "TIER1": 0.6, "TIER2": 0.3}
PIPELINE_ACTIVE = {"NEW", "CONTACTED", "REPLIED", "INTERESTED", "NEGOTIATION"}


def get_active_dealers(crm_path: str = CRM_DB_PATH) -> List[Dict]:
    """Get all dealers from CRM that are in active pipeline status."""
    if not os.path.exists(crm_path):
        return []

    con = sqlite3.connect(crm_path)
    con.row_factory = sqlite3.Row
    try:
        # Ensure tables exist
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        if "dealers" not in tables:
            return []

        rows = con.execute("""
            SELECT dealer_id, name, city, province, region, brands, stock_size,
                   premium_pct, tier, archetype, pipeline_status, score_fit
            FROM dealers
            WHERE pipeline_status IN ('NEW','CONTACTED','REPLIED','INTERESTED','NEGOTIATION')
            ORDER BY tier ASC, score_fit DESC
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        con.close()


def get_vehicle_data(listing_id: str, db_path: str = DUCKDB_PATH) -> Optional[Dict]:
    """Get vehicle data for matching."""
    import duckdb
    con = duckdb.connect(db_path, read_only=True)
    try:
        row = con.execute("""
            SELECT cr.listing_id, cr.make, cr.model, cr.year, cr.km, cr.price,
                   cr.market_price, cr.confidence, cr.fraud_overall,
                   vl.fuel_type, vl.color
            FROM cove_results cr
            LEFT JOIN vehicle_listings vl ON cr.listing_id = vl.listing_id
            WHERE cr.listing_id = ?
        """, [listing_id]).fetchone()
        if not row:
            return None
        return {
            "listing_id": row[0], "make": row[1], "model": row[2],
            "year": row[3], "km": row[4], "price_eu": float(row[5]),
            "market_price_it": float(row[6]) if row[6] else float(row[5]) * 1.10,
            "confidence": float(row[7]), "fraud": row[8],
            "fuel_type": row[9], "color": row[10],
        }
    finally:
        con.close()


def compute_match_score(vehicle: Dict, dealer: Dict) -> Dict:
    """
    Compute match score 0.0-1.0 between a vehicle and a dealer.
    Returns dict with score, component scores, and reasoning.
    """
    reasons = []

    # ── Brand Affinity (30%) ──
    brand_score = 0.5  # neutral default
    dealer_brands_raw = dealer.get("brands", "[]")
    try:
        dealer_brands = json.loads(dealer_brands_raw) if dealer_brands_raw else []
    except (json.JSONDecodeError, TypeError):
        dealer_brands = []

    vehicle_make = (vehicle.get("make") or "").upper()
    dealer_brands_upper = [b.upper() for b in dealer_brands]

    if vehicle_make in dealer_brands_upper:
        brand_score = 1.0
        reasons.append(f"brand match: {vehicle_make} in stock")
    elif dealer_brands:
        brand_score = 0.3
        reasons.append(f"brand mismatch: {vehicle_make} not in {dealer_brands}")
    else:
        brand_score = 0.5
        reasons.append("no brand data for dealer")

    # ── Price Range Fit (25%) ──
    price_eu = vehicle.get("price_eu", 0)
    stock_size = dealer.get("stock_size") or 30
    premium_pct = dealer.get("premium_pct") or 0.5

    # Estimate dealer's price bracket from premium %
    if premium_pct >= 0.7:
        # High-premium dealer → comfortable with €25-50k
        ideal_min, ideal_max = 25000, 55000
    elif premium_pct >= 0.4:
        ideal_min, ideal_max = 18000, 40000
    else:
        ideal_min, ideal_max = 10000, 30000

    if ideal_min <= price_eu <= ideal_max:
        price_score = 1.0
        reasons.append(f"price EUR {price_eu:,.0f} fits dealer range")
    elif price_eu < ideal_min:
        price_score = max(0.3, 1.0 - (ideal_min - price_eu) / ideal_min)
        reasons.append(f"price below dealer's range ({ideal_min:,.0f}-{ideal_max:,.0f})")
    else:
        price_score = max(0.2, 1.0 - (price_eu - ideal_max) / ideal_max)
        reasons.append(f"price above dealer's range ({ideal_min:,.0f}-{ideal_max:,.0f})")

    # ── Margin Potential (20%) ──
    margin = vehicle.get("market_price_it", 0) - price_eu - 1200 - 430 - 900
    if margin >= 4000:
        margin_score = 1.0
        reasons.append(f"excellent margin EUR {margin:,.0f}")
    elif margin >= 2500:
        margin_score = 0.7
        reasons.append(f"good margin EUR {margin:,.0f}")
    elif margin >= 1500:
        margin_score = 0.4
        reasons.append(f"thin margin EUR {margin:,.0f}")
    else:
        margin_score = 0.1
        reasons.append(f"insufficient margin EUR {margin:,.0f}")

    # ── Geographic Relevance (15%) ──
    # At current scale: all dealers are Sud Italia, all vehicles are premium
    # Simple heuristic: BMW/Mercedes/Audi are universally popular
    popular_brands = {"BMW", "MERCEDES", "MERCEDES-BENZ", "AUDI", "PORSCHE"}
    if vehicle_make in popular_brands:
        geo_score = 0.8
        reasons.append("popular premium brand in Sud Italia")
    else:
        geo_score = 0.5
        reasons.append("less common brand in region")

    # ── Relationship Stage (10%) ──
    tier = dealer.get("tier", "TIER2")
    tier_score = TIER_SCORES.get(tier, 0.3)
    reasons.append(f"tier={tier}")

    # ── Weighted Score ──
    total = (
        W_BRAND * brand_score +
        W_PRICE * price_score +
        W_MARGIN * margin_score +
        W_GEO * geo_score +
        W_TIER * tier_score
    )

    return {
        "dealer_id": dealer["dealer_id"],
        "dealer_name": dealer["name"],
        "city": dealer.get("city", ""),
        "tier": tier,
        "score": round(total, 3),
        "components": {
            "brand": round(brand_score, 2),
            "price": round(price_score, 2),
            "margin": round(margin_score, 2),
            "geo": round(geo_score, 2),
            "tier": round(tier_score, 2),
        },
        "margin_eur": round(margin),
        "reasons": reasons,
    }


def match_vehicle_to_dealers(
    listing_id: str,
    db_path: str = DUCKDB_PATH,
    crm_path: str = CRM_DB_PATH,
    min_score: float = 0.4,
) -> List[Dict]:
    """
    Match a vehicle to all active dealers, return sorted by score.
    Only returns dealers above min_score.
    """
    vehicle = get_vehicle_data(listing_id, db_path)
    if not vehicle:
        return []

    dealers = get_active_dealers(crm_path)
    if not dealers:
        return []

    matches = []
    for dealer in dealers:
        result = compute_match_score(vehicle, dealer)
        if result["score"] >= min_score:
            matches.append(result)

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


def freshness_check(listing_id: str, db_path: str = DUCKDB_PATH) -> Dict:
    """
    Verify a listing is still live on the source portal.
    HEAD request on detail_url: 200 = live, 404/410 = sold.

    Returns: {"available": True/False/None, "status_code": int, "checked_at": str}
    """
    import duckdb
    from datetime import datetime, timezone

    con = duckdb.connect(db_path, read_only=True)
    try:
        row = con.execute(
            "SELECT detail_url FROM vehicle_listings WHERE listing_id = ?",
            [listing_id]
        ).fetchone()
    finally:
        con.close()

    if not row or not row[0]:
        return {"available": None, "reason": "no_detail_url"}

    url = row[0]
    try:
        import requests
        resp = requests.head(url, timeout=10, allow_redirects=True, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
        available = resp.status_code == 200
        return {
            "available": available,
            "status_code": resp.status_code,
            "url": url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"available": None, "error": str(e)}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 src/cove/dealer_matcher.py <listing_id>     # Match to dealers")
        print("  python3 src/cove/dealer_matcher.py --fresh <id>     # Freshness check")
        sys.exit(1)

    if sys.argv[1] == "--fresh" and len(sys.argv) >= 3:
        result = freshness_check(sys.argv[2])
        status = "LIVE" if result.get("available") else "SOLD/GONE" if result.get("available") is False else "UNKNOWN"
        print(f"\n  Freshness: {sys.argv[2]} → {status}")
        print(f"  {result}")
    else:
        listing_id = sys.argv[1]
        matches = match_vehicle_to_dealers(listing_id)
        vehicle = get_vehicle_data(listing_id)
        if vehicle:
            print(f"\n  === Matching: {vehicle['make']} {vehicle['model']} {vehicle['year']} ===")
            print(f"  Price EU: EUR {vehicle['price_eu']:,.0f}")
            print(f"  Market IT: EUR {vehicle['market_price_it']:,.0f}")
        if not matches:
            print("  No matching dealers found (check CRM DB path)")
        else:
            print(f"\n  {len(matches)} dealers matched:\n")
            for i, m in enumerate(matches, 1):
                print(f"  {i}. {m['dealer_name']} ({m['city']}) — score {m['score']:.2f} | margin EUR {m['margin_eur']:,}")
                print(f"     {m['tier']} | brand={m['components']['brand']} price={m['components']['price']} margin={m['components']['margin']}")
                print(f"     {', '.join(m['reasons'][:3])}")
