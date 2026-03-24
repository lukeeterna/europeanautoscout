"""
ARGOS Automotive — DuckDB Schema: vehicle_listings + vehicle_images
Phase 02 — Schema DB + Detail Enricher

Creates two tables alongside cove_results (DO NOT MODIFY cove_results):
  - vehicle_listings: enriched listing data with VIN, URLs, detail fields
  - vehicle_images:   image URLs linked to listings, with local-path tracking

Usage:
    python3 src/cove/db_schema.py
    # or import and call:
    from src.cove.db_schema import create_tables, seed_from_cove_results
"""

from __future__ import annotations

import os

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

VEHICLE_LISTINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicle_listings (
    listing_id        VARCHAR PRIMARY KEY,
    vin               VARCHAR,
    make              VARCHAR,
    model             VARCHAR,
    year              INTEGER,
    mileage           INTEGER,
    price_eu          DOUBLE,
    price_it_estimate DOUBLE,
    source            VARCHAR,
    url               VARCHAR,
    detail_url        VARCHAR,
    scraped_at        TIMESTAMP DEFAULT NOW(),
    fuel_type         VARCHAR,
    transmission      VARCHAR,
    power_kw          INTEGER,
    color             VARCHAR,
    image_count       INTEGER DEFAULT 0
)
"""

VEHICLE_IMAGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicle_images (
    id           INTEGER PRIMARY KEY DEFAULT nextval('vehicle_images_id_seq'),
    listing_id   VARCHAR NOT NULL,
    image_url    VARCHAR NOT NULL,
    image_type   VARCHAR DEFAULT 'listing',
    downloaded   BOOLEAN DEFAULT FALSE,
    local_path   VARCHAR
)
"""

_VEHICLE_IMAGES_SEQ = """
CREATE SEQUENCE IF NOT EXISTS vehicle_images_id_seq START 1
"""


# ─────────────────────────────────────────────────────────────────────────────
# URL CONSTRUCTION
# ─────────────────────────────────────────────────────────────────────────────

def _build_urls(listing_id: str, source: str) -> tuple[str | None, str | None]:
    """Build listing URL and detail URL from listing_id and source."""
    if source == "autoscout24_de":
        hash_part = listing_id.replace("autoscout24_de_", "")
        url = f"https://www.autoscout24.de/angebote/{hash_part}"
        detail_url = url
    elif source == "autoscout24_nl":
        hash_part = listing_id.replace("autoscout24_nl_", "")
        url = f"https://www.autoscout24.nl/aanbod/{hash_part}"
        detail_url = url
    elif source == "autoscout24_fr":
        hash_part = listing_id.replace("autoscout24_fr_", "")
        url = f"https://www.autoscout24.fr/annonces/{hash_part}"
        detail_url = url
    elif source == "autoscout24_it":
        hash_part = listing_id.replace("autoscout24_it_", "")
        url = f"https://www.autoscout24.it/annunci/{hash_part}"
        detail_url = url
    elif source == "otomoto_pl":
        url = f"https://www.otomoto.pl/osobowe/oferta/{listing_id}"
        detail_url = url
    elif source == "finn_no":
        hash_part = listing_id.replace("finn_no_", "")
        url = f"https://www.finn.no/car/used/ad.html?finnkode={hash_part}"
        detail_url = url
    else:
        url = None
        detail_url = None
    return url, detail_url


# ─────────────────────────────────────────────────────────────────────────────
# TABLE CREATION
# ─────────────────────────────────────────────────────────────────────────────

def create_tables(con) -> None:
    """Create vehicle_listings and vehicle_images tables idempotently.

    Safe to call multiple times — uses IF NOT EXISTS throughout.
    Does NOT modify cove_results.

    Args:
        con: DuckDB connection object
    """
    print("Creating sequence vehicle_images_id_seq ...")
    con.execute(_VEHICLE_IMAGES_SEQ)
    print("  OK — sequence ready")

    print("Creating table vehicle_listings ...")
    con.execute(VEHICLE_LISTINGS_SCHEMA)
    print("  OK — vehicle_listings ready")

    print("Creating table vehicle_images ...")
    con.execute(VEHICLE_IMAGES_SCHEMA)
    print("  OK — vehicle_images ready")


# ─────────────────────────────────────────────────────────────────────────────
# SEEDING FROM cove_results
# ─────────────────────────────────────────────────────────────────────────────

def seed_from_cove_results(con) -> tuple[int, int]:
    """Seed vehicle_listings with all PROCEED listings from cove_results.

    Reads PROCEED listings from cove_results, constructs URLs for each,
    and inserts into vehicle_listings — skipping any that already exist.

    Does NOT modify cove_results.

    Args:
        con: DuckDB connection object

    Returns:
        (inserted_count, total_proceed_count) tuple
    """
    rows = con.execute(
        """
        SELECT listing_id, make, model, year, km, price, market_price, source
        FROM cove_results
        WHERE recommendation = 'PROCEED'
          AND listing_id NOT IN (SELECT listing_id FROM vehicle_listings)
        """
    ).fetchall()

    total_proceed = con.execute(
        "SELECT COUNT(*) FROM cove_results WHERE recommendation = 'PROCEED'"
    ).fetchone()[0]

    inserted = 0
    for row in rows:
        listing_id, make, model, year, km, price, market_price, source = row
        url, detail_url = _build_urls(listing_id, source)

        con.execute(
            """
            INSERT INTO vehicle_listings
                (listing_id, make, model, year, mileage, price_eu, price_it_estimate,
                 source, url, detail_url, scraped_at)
            SELECT
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW()
            WHERE ? NOT IN (SELECT listing_id FROM vehicle_listings)
            """,
            [listing_id, make, model, year, km, price, market_price,
             source, url, detail_url, listing_id],
        )
        inserted += 1

    print(f"Seeded {inserted}/{total_proceed} PROCEED listings into vehicle_listings")
    return inserted, total_proceed


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import duckdb

    db_path = os.path.join(os.path.dirname(__file__), "data", "cove_tracker.duckdb")
    print(f"Connecting to DuckDB at: {db_path}")

    con = duckdb.connect(db_path)
    create_tables(con)
    inserted, total = seed_from_cove_results(con)
    print(f"Done: {inserted} inserted, {total} total PROCEED listings")
    con.close()
