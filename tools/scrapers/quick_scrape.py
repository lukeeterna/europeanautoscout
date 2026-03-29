#!/usr/bin/env python3
"""
ARGOS Quick Scrape — Targeted scrape for priority models.
Scrapes specific make/model combinations and stores in DuckDB.

Usage:
  python3 tools/scrapers/quick_scrape.py                    # Default priority models
  python3 tools/scrapers/quick_scrape.py --dry-run           # Preview only
"""

import sys
import os
import time
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.scrapers.config import YEAR_MIN, YEAR_MAX, km_limit_for
from tools.scrapers.db import ensure_market_schema, upsert_listing

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('quick_scrape')

# Priority targets for immediate pipeline
PRIORITY_TARGETS = [
    ("BMW", "X3"),
    ("Mercedes", "GLC"),
    ("Audi", "Q5"),
    ("Porsche", "Macan"),
]

# Portals to scrape (most results)
PORTALS = ["autoscout24_de", "autoscout24_nl", "autoscout24_at", "mobile_de"]


def get_scraper(portal_name: str):
    scraper_type = portal_name.split('_')[0] if '_' in portal_name else portal_name
    if scraper_type == 'autoscout24':
        from tools.scrapers.autoscout_scraper import AutoScoutScraper
        return AutoScoutScraper(portal_key=portal_name)
    elif scraper_type == 'mobile':
        from tools.scrapers.mobile_de_scraper import MobileDeScraper
        return MobileDeScraper()
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    ensure_market_schema()

    total_found = 0
    total_new = 0

    for portal_name in PORTALS:
        scraper = get_scraper(portal_name)
        if not scraper:
            log.warning(f"Skip {portal_name}: no scraper")
            continue

        for make, model in PRIORITY_TARGETS:
            km_max = km_limit_for(make, model)
            log.info(f"━━━ {portal_name} | {make} {model} ━━━")

            try:
                listings = scraper.scrape_model(
                    make=make,
                    model=model,
                    year_min=YEAR_MIN,
                    year_max=YEAR_MAX,
                    km_max=km_max,
                )

                if listings:
                    total_found += len(listings)
                    log.info(f"  Found: {len(listings)} listings")

                    if not args.dry_run:
                        for listing in listings:
                            result = upsert_listing(listing)
                            if result == 'new':
                                total_new += 1
                else:
                    log.info(f"  No listings found")

            except Exception as e:
                log.error(f"  ERROR: {e}")

    log.info(f"━━━ DONE: {total_found} found, {total_new} new ━━━")


if __name__ == "__main__":
    main()
