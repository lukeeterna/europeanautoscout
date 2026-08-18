"""ARGOS Automotive — DuckDB vehicle evidence schema.

Creates/migrates vehicle_listings + vehicle_images alongside cove_results.
The schema is additive and idempotent.  In particular, photo semantics are
stored separately from raw image presence so a gallery count can never stand in
for front/rear/interior coverage.
"""
from __future__ import annotations

import os
from typing import Any


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
    id                   INTEGER PRIMARY KEY DEFAULT nextval('vehicle_images_id_seq'),
    listing_id           VARCHAR NOT NULL,
    image_url            VARCHAR NOT NULL,
    image_type           VARCHAR DEFAULT 'listing',
    downloaded           BOOLEAN DEFAULT FALSE,
    local_path           VARCHAR,
    semantic_view        VARCHAR,
    semantic_confidence  DOUBLE,
    semantic_source      VARCHAR,
    semantic_evidence_id VARCHAR
)
"""

_VEHICLE_IMAGES_SEQ = """
CREATE SEQUENCE IF NOT EXISTS vehicle_images_id_seq START 1
"""


# Explicitly deprecated legacy column: retained only for database compatibility.
# New production code must not write an invented Italian market uplift here.
DEPRECATED_VEHICLE_LISTING_COLUMNS = {"price_it_estimate"}


def _build_urls(listing_id: str, source: str) -> tuple[str | None, str | None]:
    """Build source listing URL only for known source identifiers."""
    if source == "autoscout24_de":
        value = listing_id.replace("autoscout24_de_", "")
        url = f"https://www.autoscout24.de/angebote/{value}"
    elif source == "autoscout24_nl":
        value = listing_id.replace("autoscout24_nl_", "")
        url = f"https://www.autoscout24.nl/aanbod/{value}"
    elif source == "autoscout24_fr":
        value = listing_id.replace("autoscout24_fr_", "")
        url = f"https://www.autoscout24.fr/annonces/{value}"
    elif source == "autoscout24_it":
        value = listing_id.replace("autoscout24_it_", "")
        url = f"https://www.autoscout24.it/annunci/{value}"
    elif source == "otomoto_pl":
        url = f"https://www.otomoto.pl/osobowe/oferta/{listing_id}"
    elif source == "finn_no":
        value = listing_id.replace("finn_no_", "")
        url = f"https://www.finn.no/car/used/ad.html?finnkode={value}"
    else:
        return None, None
    return url, url


def _table_columns(con: Any, table: str) -> set[str]:
    try:
        rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    except Exception:
        return set()
    return {str(row[1]) for row in rows if len(row) > 1}


def _ensure_vehicle_listing_columns(con: Any) -> None:
    """Add evidence fields used by current seller/dossier runtime when absent."""
    columns = _table_columns(con, "vehicle_listings")
    migrations = {
        "seller_name": "VARCHAR",
        "seller_email": "VARCHAR",
        "seller_phone": "VARCHAR",
        "seller_contact_sent_at": "TIMESTAMP",
        "seller_contact_evidence_id": "VARCHAR",
        "seller_confirmed_available": "BOOLEAN",
        "availability_status": "VARCHAR",
        "vin_verified": "BOOLEAN",
        "service_history": "VARCHAR",
        "hu_date": "VARCHAR",
        "previous_owners": "INTEGER",
        "accident_history": "VARCHAR",
        "equipment_list": "VARCHAR",
        "num_keys": "INTEGER",
        "next_service_due": "VARCHAR",
        "outstanding_finance": "VARCHAR",
        "interior_color_material": "VARCHAR",
        "tire_type_condition": "VARCHAR",
        "available_from": "VARCHAR",
        "transport_quote_eur": "DOUBLE",
        "argos_grade": "VARCHAR",
    }
    for name, sql_type in migrations.items():
        if name not in columns:
            con.execute(f'ALTER TABLE vehicle_listings ADD COLUMN "{name}" {sql_type}')


def create_tables(con: Any) -> None:
    """Create/migrate evidence tables idempotently without touching cove_results."""
    con.execute(_VEHICLE_IMAGES_SEQ)
    con.execute(VEHICLE_LISTINGS_SCHEMA)
    con.execute(VEHICLE_IMAGES_SCHEMA)
    _ensure_vehicle_listing_columns(con)

    # Centralized photo semantics migration. Import after tables exist to avoid
    # import-time DuckDB dependency and circular schema construction.
    try:
        from src.cove.photo_coverage import ensure_photo_semantic_columns
    except ModuleNotFoundError:
        from photo_coverage import ensure_photo_semantic_columns  # type: ignore
    ensure_photo_semantic_columns(con)


def seed_from_cove_results(con: Any) -> tuple[int, int]:
    """Seed observed listing facts from PROCEED CoVe rows.

    Historical code copied cove_results.market_price into a column named
    ``price_it_estimate``.  That conflated an upstream market reference with an
    Italian resale estimate.  New rows leave the deprecated column NULL; deal
    economics must come from the evidence-backed economics layer.
    """
    rows = con.execute(
        """
        SELECT listing_id, make, model, year, km, price, source
        FROM cove_results
        WHERE recommendation = 'PROCEED'
          AND listing_id NOT IN (SELECT listing_id FROM vehicle_listings)
        """
    ).fetchall()
    total_proceed = con.execute(
        "SELECT COUNT(*) FROM cove_results WHERE recommendation = 'PROCEED'"
    ).fetchone()[0]

    inserted = 0
    for listing_id, make, model, year, km, price, source in rows:
        url, detail_url = _build_urls(str(listing_id), str(source or ""))
        con.execute(
            """
            INSERT INTO vehicle_listings
                (listing_id, make, model, year, mileage, price_eu,
                 price_it_estimate, source, url, detail_url, scraped_at)
            SELECT ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, NOW()
            WHERE ? NOT IN (SELECT listing_id FROM vehicle_listings)
            """,
            [
                listing_id,
                make,
                model,
                year,
                km,
                price,
                source,
                url,
                detail_url,
                listing_id,
            ],
        )
        inserted += 1
    return inserted, int(total_proceed or 0)


if __name__ == "__main__":
    import duckdb

    db_path = os.path.join(os.path.dirname(__file__), "data", "cove_tracker.duckdb")
    with duckdb.connect(db_path) as connection:
        create_tables(connection)
        inserted, total = seed_from_cove_results(connection)
    print(f"Evidence schema ready: {inserted} new rows, {total} PROCEED rows observed")
