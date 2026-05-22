#!/usr/bin/env python3
"""
ARGOS Dealer Discovery Engine
Orchestratore che combina Subito.it + Google Maps per trovare dealer su commissione.

Pipeline:
  1. Subito.it → lista dealer PRO per provincia con commission scoring
  2. Google Maps → arricchimento contatti (telefono, recensioni, rating)
  3. Dedup → unifica dealer trovati su piu' fonti
  4. Scoring finale → fit ARGOS
  5. Export → JSON + CRM insert

Usage:
  python3 tools/dealer_discovery/discovery_engine.py --province foggia --dry-run
  python3 tools/dealer_discovery/discovery_engine.py --all-priority 1
  python3 tools/dealer_discovery/discovery_engine.py --all-priority 2 --insert-crm
"""

import json
import logging
import os
import re
import sqlite3
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.dealer_discovery.config import PROVINCE_TARGET, COMMISSION_SCORING
from tools.dealer_discovery.subito_dealer_scraper import (
    scrape_provinces, DiscoveredDealer, print_results, export_json,
)

logger = logging.getLogger("argos.dealer_discovery.engine")

# ── CRM Integration ──────────────────────────────────────────

from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parents[2]
DB_PATH = os.environ.get(
    'ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite')
)
if not os.path.exists(DB_PATH):
    _alt = str(_PROJECT_ROOT / "dealer_network.sqlite")
    if os.path.exists(_alt):
        DB_PATH = _alt


def _normalize_name(name: str) -> str:
    """Normalize dealer name for dedup."""
    name = name.lower().strip()
    # Remove common suffixes
    for suffix in [" srl", " srls", " s.r.l.", " s.r.l.s.", " sas", " snc",
                   " di ", " s.n.c.", " s.a.s.", " autocommercio", " auto"]:
        name = name.replace(suffix, "")
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def dedup_dealers(dealers: List[DiscoveredDealer]) -> List[DiscoveredDealer]:
    """Remove duplicate dealers based on normalized name + province."""
    seen = {}
    deduped = []
    for d in dealers:
        key = f"{_normalize_name(d.name)}|{d.province}"
        if key not in seen:
            seen[key] = d
            deduped.append(d)
        else:
            # Merge: keep the one with higher fit_score
            existing = seen[key]
            if d.fit_score > existing.fit_score:
                seen[key] = d
                deduped = [d if _normalize_name(x.name) + "|" + x.province == key else x for x in deduped]
    return deduped


def check_existing_in_crm(dealers: List[DiscoveredDealer]) -> List[DiscoveredDealer]:
    """Mark dealers already in CRM."""
    if not os.path.exists(DB_PATH):
        return dealers

    try:
        con = sqlite3.connect(DB_PATH, timeout=5)
        con.row_factory = sqlite3.Row
        existing = con.execute("SELECT name, province FROM dealers").fetchall()
        con.close()

        existing_keys = {f"{_normalize_name(r['name'])}|{(r['province'] or '').lower()}" for r in existing}

        new_dealers = []
        for d in dealers:
            key = f"{_normalize_name(d.name)}|{d.province}"
            if key in existing_keys:
                logger.info(f"  Gia' nel CRM: {d.name} ({d.province})")
            else:
                new_dealers.append(d)

        logger.info(f"  {len(dealers) - len(new_dealers)} gia' nel CRM, {len(new_dealers)} nuovi")
        return new_dealers
    except Exception as e:
        logger.warning(f"CRM check failed: {e}")
        return dealers


def insert_into_crm(dealers: List[DiscoveredDealer]):
    """Insert discovered dealers into CRM as NEW with target_type COMMISSION."""
    if not os.path.exists(DB_PATH):
        logger.error(f"CRM DB not found: {DB_PATH}")
        return

    con = sqlite3.connect(DB_PATH, timeout=10)
    inserted = 0

    for d in dealers:
        dealer_id = f"disc_{d.province}_{_normalize_name(d.name).replace(' ', '_')[:30]}"

        try:
            con.execute("""
                INSERT OR IGNORE INTO dealers (
                    dealer_id, name, city, province, region,
                    stock_size, brands, premium_pct,
                    target_type, tier, score_fit,
                    source_url, pipeline_status, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dealer_id,
                d.name,
                d.city,
                d.province.upper(),
                d.region.upper(),
                d.listing_count,
                json.dumps(d.brands),
                d.premium_pct,
                "COMMISSION",
                "TIER_NEW",
                d.fit_score,
                d.shop_url or d.source_url or f"subito.it/{d.province}",
                "NEW",
                f"Discovery auto: commission_score={d.commission_score}, "
                f"fit={d.fit_score}, brands={','.join(d.brands[:5])}, "
                f"premium={','.join(d.premium_brands[:3])}",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            logger.debug(f"  Already exists: {dealer_id}")

    con.commit()
    con.close()
    logger.info(f"Inserted {inserted} new dealers into CRM")


# ── Main engine ───────────────────────────────────────────────

def run_discovery(
    provinces: List[dict],
    max_pages: int = 3,
    insert_crm: bool = False,
    output_json: Optional[str] = None,
    dry_run: bool = False,
) -> List[DiscoveredDealer]:
    """Run full discovery pipeline."""
    logger.info(f"Starting discovery for {len(provinces)} provinces")

    # Step 1: Scrape Subito.it
    logger.info("Step 1: Scraping Subito.it...")
    dealers = scrape_provinces(provinces, max_pages=max_pages)
    logger.info(f"  Found {len(dealers)} professional dealers")

    # Step 2: Dedup
    logger.info("Step 2: Deduplication...")
    dealers = dedup_dealers(dealers)
    logger.info(f"  After dedup: {len(dealers)} dealers")

    # Step 3: Filter commission-likely
    commission = [d for d in dealers if d.commission_score >= COMMISSION_SCORING["threshold_commission"]]
    fit = [d for d in dealers if d.fit_score >= COMMISSION_SCORING["threshold_fit_argos"]]
    logger.info(f"  Commission signal: {len(commission)} | Fit ARGOS: {len(fit)}")

    # Step 4: Check existing CRM
    if not dry_run:
        logger.info("Step 3: Checking CRM for existing dealers...")
        new_dealers = check_existing_in_crm(dealers)
    else:
        new_dealers = dealers

    # Step 5: Insert into CRM
    if insert_crm and not dry_run and new_dealers:
        logger.info("Step 4: Inserting into CRM...")
        # Only insert high-fit dealers
        to_insert = [d for d in new_dealers if d.fit_score >= COMMISSION_SCORING["threshold_commission"]]
        if to_insert:
            insert_into_crm(to_insert)

    # Step 6: Export
    if output_json:
        export_json(dealers, output_json)

    return dealers


# ── CLI ───────────────────────────────────────────────────────

def main():
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    parser = argparse.ArgumentParser(description="ARGOS Dealer Discovery Engine")
    parser.add_argument("--province", type=str, help="Comma-separated provinces")
    parser.add_argument("--all-priority", type=int, help="All provinces with priority <= N")
    parser.add_argument("--pages", type=int, default=3, help="Max pages per province")
    parser.add_argument("--insert-crm", action="store_true", help="Insert into CRM database")
    parser.add_argument("--output", type=str, help="Export JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to CRM")
    parser.add_argument("--top", type=int, default=30, help="Show top N results")

    args = parser.parse_args()

    if args.province:
        province_names = [p.strip().lower() for p in args.province.split(",")]
        provinces = [p for p in PROVINCE_TARGET if p["province"] in province_names]
    elif args.all_priority:
        provinces = [p for p in PROVINCE_TARGET if p["priority"] <= args.all_priority]
    else:
        provinces = [p for p in PROVINCE_TARGET if p["priority"] == 1]

    print(f"\nARGOS DEALER DISCOVERY ENGINE")
    print(f"Province: {[p['province'] for p in provinces]}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    dealers = run_discovery(
        provinces=provinces,
        max_pages=args.pages,
        insert_crm=args.insert_crm,
        output_json=args.output,
        dry_run=args.dry_run,
    )

    print_results(dealers, top_n=args.top)


if __name__ == "__main__":
    main()
