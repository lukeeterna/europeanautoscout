"""
ARGOS Automotive — Detail Enricher V2
Phase 02 — Schema DB + Detail Enricher

Reads PROCEED listings from vehicle_listings, fetches detail pages,
extracts VIN + images + specs, writes to vehicle_listings + vehicle_images.

Does NOT modify cove_results or cove_engine_v4.py.

Usage:
    python3 src/cove/detail_enricher_v2.py --limit 5 --dry-run
    python3 src/cove/detail_enricher_v2.py --limit 10 --source autoscout24_de
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("argos.detail_enricher_v2")

# VIN character set — excludes I, O, Q per ISO 3779
_VIN_RE = re.compile(r'\b([A-HJ-NPR-Z0-9]{17})\b')


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def extract_vin_from_html(html: str) -> Optional[str]:
    """
    Extract 17-char VIN from detail page HTML.
    Tries 4 layers in priority order:
      1. JSON-LD vehicleIdentificationNumber
      2. <meta name="vin"> content
      3. data-vin attribute anywhere in HTML
      4. Text pattern "FIN: XXXX" or "VIN: XXXX"
    Returns first valid 17-char VIN found, or None.
    """
    # Layer 1: JSON-LD
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         html, re.DOTALL | re.IGNORECASE):
        try:
            data = json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            vin_raw = item.get("vehicleIdentificationNumber") or item.get("vin") or ""
            if vin_raw:
                vin_match = _VIN_RE.search(str(vin_raw).upper())
                if vin_match:
                    return vin_match.group(1)

    # Layer 2: meta name="vin"
    m = re.search(r'<meta[^>]+name=["\']vin["\'][^>]+content=["\']([^"\']+)["\']',
                  html, re.IGNORECASE)
    if m:
        vin_match = _VIN_RE.search(m.group(1).upper())
        if vin_match:
            return vin_match.group(1)

    # Layer 3: data-vin attribute
    m = re.search(r'data-vin=["\']([A-HJ-NPR-Z0-9]{17})["\']', html, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # Layer 4: text patterns near "FIN" / "VIN" / "Fahrzeugidentifikationsnummer"
    for pattern in [
        r'(?:FIN|VIN|Fahrzeugidentifikation(?:snummer)?)\s*:?\s*([A-HJ-NPR-Z0-9]{17})',
        r'(?:FIN|VIN)\b[^A-Z0-9]{0,10}([A-HJ-NPR-Z0-9]{17})',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return m.group(1).upper()

    return None


def extract_images_from_html(html: str, source: str) -> List[str]:
    """
    Extract all unique image URLs from a detail page.
    Returns list of full HTTPS URLs. Deduplicates. Filters thumbnails.
    """
    found: List[str] = []
    seen: set = set()

    def add_url(url: str) -> None:
        url = url.strip()
        if not url.startswith("http"):
            return
        if any(skip in url.lower() for skip in ["1x1", "pixel", "tracking", "logo", "icon"]):
            return
        if url not in seen:
            seen.add(url)
            found.append(url)

    # Layer 1: JSON-LD "image" field (array or string)
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         html, re.DOTALL | re.IGNORECASE):
        try:
            data = json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            img = item.get("image")
            if isinstance(img, list):
                for url in img:
                    if isinstance(url, str):
                        add_url(url)
                    elif isinstance(url, dict):
                        add_url(url.get("url", ""))
            elif isinstance(img, str):
                add_url(img)

    # Layer 2: data-image-url attributes (AS24 gallery)
    for m in re.finditer(r'data-(?:image-url|src|lazy-src)=["\']([^"\']+)["\']', html, re.IGNORECASE):
        add_url(m.group(1))

    # Layer 3: <img src> for CDN images
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
        url = m.group(1)
        if any(cdn in url.lower() for cdn in ["cdn", "img.", "images.", "foto", "photo", "bild"]):
            add_url(url)

    return found[:20]


def extract_specs_from_html(html: str) -> Dict[str, Any]:
    """
    Extract fuel_type, transmission, power_kw, color from JSON-LD.
    All fields nullable — returns empty dict if nothing found.
    """
    specs: Dict[str, Any] = {}

    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         html, re.DOTALL | re.IGNORECASE):
        try:
            data = json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if "fuelType" in item:
                specs["fuel_type"] = str(item["fuelType"])
            if "vehicleTransmission" in item:
                specs["transmission"] = str(item["vehicleTransmission"])
            if "color" in item:
                specs["color"] = str(item["color"])
            engine = item.get("vehicleEngine", {})
            if isinstance(engine, dict):
                ep = engine.get("enginePower", {})
                if isinstance(ep, dict):
                    unit = ep.get("unitCode", "KWT").upper()
                    val = ep.get("value", 0)
                    try:
                        kw = int(float(val))
                        if unit in ("PS", "CV", "HP"):
                            kw = int(kw * 0.7355)
                        specs["power_kw"] = kw
                    except (ValueError, TypeError):
                        pass

    return specs


# ─────────────────────────────────────────────────────────────────────────────
# DETAIL ENRICHER V2 CLASS
# ─────────────────────────────────────────────────────────────────────────────

class DetailEnricherV2:
    """
    Enriches vehicle_listings records with VIN, images, and specs
    by fetching detail pages for PROCEED listings.

    Reads from:  vehicle_listings (detail_url column)
    Writes to:   vehicle_listings (vin, fuel_type, transmission, power_kw, color, image_count)
                 vehicle_images (listing_id, image_url, image_type)

    Does NOT modify cove_results.
    Does NOT modify cove_engine_v4.py.
    """

    def __init__(self, db_path: str, delay: float = 3.0, max_404: int = 5):
        self.db_path = db_path
        self.delay = delay
        self.max_404 = max_404
        self._last_request: dict = {}
        self._consecutive_404 = 0

        # Import ResilientFetcher — resolve path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from tools.scrapers.resilient_fetcher import ResilientFetcher
        self._fetcher = ResilientFetcher(timeout=25, max_retries=2)

    def _rate_limit(self, domain: str) -> None:
        last = self._last_request.get(domain, 0)
        elapsed = time.time() - last
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request[domain] = time.time()

    def _get_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc
        except Exception:
            return ""

    def enrich_listing(self, listing_id: str, detail_url: str, source: str, dry_run: bool = False) -> dict:
        """
        Enrich a single listing. Returns result dict with keys:
          status: 'enriched' | '404' | 'no_vin' | 'error' | 'no_url'
          vin: str or None
          image_count: int
          fields_updated: list[str]
        """
        import duckdb

        result = {"status": "error", "vin": None, "image_count": 0, "fields_updated": []}

        if not detail_url:
            result["status"] = "no_url"
            return result

        domain = self._get_domain(detail_url)
        self._rate_limit(domain)

        try:
            accept_lang = "de-DE,de;q=0.9,en;q=0.5" if ".de" in detail_url else "en-US,en;q=0.9"
            html = self._fetcher.fetch(detail_url, accept_language=accept_lang)
        except Exception as e:
            msg = str(e).lower()
            if "404" in msg or "not found" in msg:
                result["status"] = "404"
                self._consecutive_404 += 1
            else:
                result["status"] = "error"
                logger.warning("[enricher_v2] Fetch failed %s: %s", listing_id, e)
            return result

        self._consecutive_404 = 0  # reset on success

        # Empty or tiny response = listing sold/removed (ResilientFetcher returns "" for 404)
        if not html or len(html) < 500:
            result["status"] = "404"
            self._consecutive_404 += 1
            return result

        # Extract data
        vin = extract_vin_from_html(html)
        images = extract_images_from_html(html, source)
        specs = extract_specs_from_html(html)

        result["vin"] = vin
        result["image_count"] = len(images)

        # ── VIN VERIFICATION (€0 — NHTSA + freevindecoder) ────────
        vin_verification = None
        if vin and len(vin) == 17:
            try:
                from src.cove.vin_verification import VinVerifier
                # Prendi make/model/year dal listing per consistency check
                listing_make = specs.get("make", "")
                listing_model = specs.get("model", "")
                listing_year = int(specs.get("year", 0) or 0)
                vin_verification = VinVerifier.full_check(
                    vin=vin,
                    listing_make=listing_make,
                    listing_model=listing_model,
                    listing_year=listing_year,
                )
                result["vin_verified"] = vin_verification.vin_verified
                result["vin_alerts"] = vin_verification.alerts
                result["recall_count"] = vin_verification.recall_count
                logger.info("[enricher_v2] VIN verified=%s, tools=%d/%d, recalls=%d, alerts=%s",
                            vin_verification.vin_verified,
                            vin_verification.total_tools_ok,
                            vin_verification.total_tools_tried,
                            vin_verification.recall_count,
                            vin_verification.alerts)
            except Exception as e:
                logger.warning("[enricher_v2] VIN verification failed (non-blocking): %s", e)
                vin_verification = None

        if dry_run:
            result["status"] = "enriched" if (vin or images) else "no_vin"
            logger.info("[enricher_v2] DRY RUN %s: vin=%s images=%d specs=%s",
                        listing_id, vin, len(images), specs)
            return result

        # Write to DuckDB
        con = duckdb.connect(self.db_path)
        try:
            # Update vehicle_listings
            updates = []
            params = []
            if vin:
                updates.append("vin = ?")
                params.append(vin)
                result["fields_updated"].append("vin")
            # Salva verifica VIN nel DB
            if vin_verification:
                updates.append("vin_verified = ?")
                params.append(vin_verification.vin_verified)
                updates.append("vin_verification_data = ?")
                params.append(vin_verification.to_json())
                updates.append("recall_count = ?")
                params.append(vin_verification.recall_count)
                result["fields_updated"].extend(["vin_verified", "vin_verification_data", "recall_count"])
            for field in ("fuel_type", "transmission", "power_kw", "color"):
                if field in specs:
                    updates.append(f"{field} = ?")
                    params.append(specs[field])
                    result["fields_updated"].append(field)
            updates.append("image_count = ?")
            params.append(len(images))
            updates.append("scraped_at = NOW()")
            params.append(listing_id)

            if updates:
                sql = f"UPDATE vehicle_listings SET {', '.join(updates)} WHERE listing_id = ?"
                con.execute(sql, params)

            # Insert vehicle_images (skip if already populated for this listing)
            existing = con.execute(
                "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?", [listing_id]
            ).fetchone()[0]

            if existing == 0 and images:
                for img_url in images:
                    con.execute(
                        "INSERT INTO vehicle_images (listing_id, image_url, image_type) VALUES (?, ?, ?)",
                        [listing_id, img_url, "listing"]
                    )

            con.commit()
        finally:
            con.close()

        result["status"] = "enriched" if (vin or images) else "no_vin"
        logger.info("[enricher_v2] %s: vin=%s images=%d specs=%s",
                    listing_id, vin, len(images), specs)
        return result

    def close(self):
        try:
            self._fetcher.close()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# RUNNER FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def enrich_proceed_listings(
    db_path: str,
    limit: int = 10,
    dry_run: bool = False,
    source_filter: str = "autoscout24_de"
) -> dict:
    """
    Standalone runner: enriches up to `limit` PROCEED listings from vehicle_listings.
    Priority: listings without VIN first, ordered by price_it_estimate DESC.
    """
    import duckdb

    con = duckdb.connect(db_path)
    where_clause = "WHERE vin IS NULL"
    params = []
    if source_filter:
        where_clause += " AND source = ?"
        params.append(source_filter)

    rows = con.execute(
        f"""
        SELECT listing_id, detail_url, source
        FROM vehicle_listings
        {where_clause}
        ORDER BY price_it_estimate DESC NULLS LAST
        LIMIT ?
        """,
        params + [limit]
    ).fetchall()
    con.close()

    if not rows:
        print(f"No listings to enrich (filter: source={source_filter}, vin IS NULL)")
        return {"total_attempted": 0, "enriched": 0, "not_found_404": 0, "no_vin": 0, "errors": 0, "vins_found": []}

    enricher = DetailEnricherV2(db_path)
    stats = {"total_attempted": 0, "enriched": 0, "not_found_404": 0, "no_vin": 0, "errors": 0, "vins_found": []}

    try:
        for listing_id, detail_url, source in rows:
            if enricher._consecutive_404 >= enricher.max_404:
                print(f"[enricher_v2] Stopping: {enricher.max_404} consecutive 404s (listings sold)")
                break

            print(f"[enricher_v2] Processing {listing_id} ({source}) — {detail_url}")
            result = enricher.enrich_listing(listing_id, detail_url, source, dry_run=dry_run)
            stats["total_attempted"] += 1

            if result["status"] == "enriched":
                stats["enriched"] += 1
                if result["vin"]:
                    stats["vins_found"].append({"listing_id": listing_id, "vin": result["vin"]})
                print(f"  -> ENRICHED: vin={result['vin']} images={result['image_count']}")
            elif result["status"] == "404":
                stats["not_found_404"] += 1
                print(f"  -> 404 (listing sold or URL changed)")
            elif result["status"] == "no_vin":
                stats["no_vin"] += 1
                print(f"  -> Fetched OK but no VIN found (images={result['image_count']})")
            else:
                stats["errors"] += 1
                print(f"  -> ERROR: {result['status']}")

    finally:
        enricher.close()

    print(f"\n[enricher_v2] Summary: attempted={stats['total_attempted']} "
          f"enriched={stats['enriched']} 404s={stats['not_found_404']} "
          f"no_vin={stats['no_vin']} errors={stats['errors']}")
    print(f"[enricher_v2] VINs found: {stats['vins_found']}")

    return stats


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="ARGOS Detail Enricher V2")
    parser.add_argument("--db", default=None, help="Path to DuckDB file")
    parser.add_argument("--limit", type=int, default=5, help="Max listings to attempt")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not write to DB")
    parser.add_argument("--source", default="autoscout24_de", help="Filter by source (default: autoscout24_de)")
    parser.add_argument("--all-sources", action="store_true", help="Process all sources")
    args = parser.parse_args()

    if args.db is None:
        args.db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cove_tracker.duckdb")

    source = None if args.all_sources else args.source
    stats = enrich_proceed_listings(args.db, limit=args.limit, dry_run=args.dry_run, source_filter=source)
    sys.exit(0 if stats["errors"] == 0 else 1)
