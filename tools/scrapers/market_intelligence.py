#!/usr/bin/env python3
"""
ARGOS™ Market Intelligence — Orchestratore Principale
Coordina tutti gli scraper, analizza trend, invia notifiche.

Uso:
    python3 tools/scrapers/market_intelligence.py                    # Run completo
    python3 tools/scrapers/market_intelligence.py --portal autoscout24  # Solo un portale
    python3 tools/scrapers/market_intelligence.py --country DE       # Solo un paese
    python3 tools/scrapers/market_intelligence.py --dry-run          # Solo log, no DB
    python3 tools/scrapers/market_intelligence.py --no-notify        # Skip Telegram

Schedulazione:
    crontab: 0 5 * * 1-5 cd /path/to/enterprise && python3 tools/scrapers/market_intelligence.py
    PM2: vedi ecosystem.market.config.js
"""

import argparse
import logging
import sys
import os
import time
from datetime import datetime

# Aggiungi root progetto al path per import
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.scrapers.config import (
    PORTALS, TARGET_VEHICLES, SCRAPER_SCHEDULE,
    YEAR_MIN, YEAR_MAX, km_limit_for, PortalConfig,
)
from tools.scrapers.db import ensure_market_schema, start_run, finish_run
from tools.scrapers.trend_analyzer import generate_full_digest, format_telegram_digest
from tools.scrapers.notifier import send_market_digest, send_scraper_error, send_scraper_summary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/argos-market-intel.log', mode='a'),
    ]
)
logger = logging.getLogger('market_intelligence')


def get_scraper(portal_type: str):
    """Factory: ritorna l'istanza scraper corretta per il tipo di portale.
    portal_type è il prefisso (autoscout24, mobile, willhaben, leboncoin)."""
    if portal_type.startswith('autoscout24'):
        from tools.scrapers.autoscout_scraper import AutoScoutScraper
        return AutoScoutScraper()
    elif portal_type in ('mobile_de', 'mobile'):
        from tools.scrapers.mobile_de_scraper import MobileDeScraper
        return MobileDeScraper()
    else:
        logger.warning(f'Scraper non implementato per tipo: {portal_type}')
        return None


def run_portal(portal_name: str, portal_config: PortalConfig,
               country_filter: str = None, dry_run: bool = False) -> dict:
    """Esegue lo scraping per un singolo portale. Ritorna stats."""
    # Determina il tipo di scraper dal nome del portale
    scraper_type = portal_name.split('_')[0] if '_' in portal_name else portal_name
    scraper = get_scraper(scraper_type)
    if not scraper:
        return {'error': f'Scraper non disponibile: {portal_name}'}

    countries = portal_config.countries
    if country_filter:
        countries = [c for c in countries if c == country_filter.upper()]

    total_stats = {
        'portal': portal_name,
        'listings_found': 0,
        'listings_new': 0,
        'listings_updated': 0,
        'errors': 0,
        'countries_scraped': 0,
    }

    for country in countries:
        logger.info(f'━━━ {portal_name.upper()} [{country}] ━━━')
        run_id = None
        if not dry_run:
            run_id = start_run(portal_name, country)

        country_found = 0
        country_new = 0
        country_updated = 0
        country_errors = 0
        start_time = time.time()

        # TARGET_VEHICLES è un dict {make: [models]}
        for make, models in TARGET_VEHICLES.items():
            for model in models:
                km_max = km_limit_for(make, model)
                try:
                    logger.info(f'  Scraping {make} {model} [{country}]...')
                    listings = scraper.scrape_model(
                        make=make,
                        model=model,
                        country=country,
                        year_min=YEAR_MIN,
                        year_max=YEAR_MAX,
                        km_max=km_max,
                    )

                    if listings:
                        logger.info(f'    Trovati: {len(listings)} listing')
                        country_found += len(listings)

                        if not dry_run:
                            from tools.scrapers.db import upsert_listing
                            for listing in listings:
                                result = upsert_listing(listing)
                                if result == 'new':
                                    country_new += 1
                                elif result == 'updated':
                                    country_updated += 1
                    else:
                        logger.info(f'    Nessun listing trovato')

                except Exception as e:
                    logger.error(f'    ERRORE {make} {model} [{country}]: {e}')
                    country_errors += 1

        duration = time.time() - start_time

        if not dry_run and run_id:
            finish_run(
                run_id=run_id,
                listings_found=country_found,
                listings_new=country_new,
                listings_updated=country_updated,
                listings_removed=0,
                errors=country_errors,
                duration_sec=duration,
            )

        total_stats['listings_found'] += country_found
        total_stats['listings_new'] += country_new
        total_stats['listings_updated'] += country_updated
        total_stats['errors'] += country_errors
        total_stats['countries_scraped'] += 1

        logger.info(
            f'  {portal_name} [{country}] completato: '
            f'{country_found} trovati, {country_new} nuovi, '
            f'{country_errors} errori, {duration:.0f}s'
        )

    return total_stats


def main():
    parser = argparse.ArgumentParser(description='ARGOS™ Market Intelligence')
    parser.add_argument('--portal', type=str, help='Solo un portale (autoscout24, mobile_de)')
    parser.add_argument('--country', type=str, help='Solo un paese (DE, NL, BE, AT, FR, SE)')
    parser.add_argument('--dry-run', action='store_true', help='Solo log, non salva in DB')
    parser.add_argument('--no-notify', action='store_true', help='Skip notifiche Telegram')
    args = parser.parse_args()

    logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    logger.info('ARGOS™ MARKET INTELLIGENCE — Run avviato')
    logger.info(f'Timestamp: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    logger.info(f'Portali: {args.portal or "TUTTI"}')
    logger.info(f'Paese: {args.country or "TUTTI"}')
    logger.info(f'Dry run: {args.dry_run}')
    logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

    # Assicura schema DB
    if not args.dry_run:
        ensure_market_schema()

    # Seleziona portali
    portals_to_run = {}
    if args.portal:
        if args.portal in PORTALS:
            portals_to_run[args.portal] = PORTALS[args.portal]
        else:
            logger.error(f'Portale sconosciuto: {args.portal}. Disponibili: {list(PORTALS.keys())}')
            sys.exit(1)
    else:
        portals_to_run = PORTALS

    # Esegui scraping
    all_stats = []
    run_start = time.time()

    for portal_name, portal_config in portals_to_run.items():
        try:
            stats = run_portal(
                portal_name=portal_name,
                portal_config=portal_config,
                country_filter=args.country,
                dry_run=args.dry_run,
            )
            all_stats.append(stats)

            if not args.no_notify and not args.dry_run:
                send_scraper_summary(
                    portal=portal_name,
                    total_found=stats['listings_found'],
                    new=stats['listings_new'],
                    updated=stats['listings_updated'],
                    removed=0,
                    duration_sec=time.time() - run_start,
                    errors=stats['errors'],
                )

        except Exception as e:
            logger.error(f'ERRORE FATALE portale {portal_name}: {e}')
            if not args.no_notify:
                send_scraper_error(portal_name, args.country or 'ALL', str(e))

    # Genera e invia digest
    total_duration = time.time() - run_start
    total_found = sum(s.get('listings_found', 0) for s in all_stats)
    total_new = sum(s.get('listings_new', 0) for s in all_stats)
    total_errors = sum(s.get('errors', 0) for s in all_stats)

    logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    logger.info(f'RUN COMPLETATO in {total_duration:.0f}s')
    logger.info(f'Totale: {total_found} listing, {total_new} nuovi, {total_errors} errori')
    logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

    if not args.dry_run:
        # Genera digest con trend
        try:
            digest = generate_full_digest()
            digest_text = format_telegram_digest(digest)
            logger.info(f'\n{digest_text}')

            if not args.no_notify:
                send_market_digest(digest_text)
                logger.info('Digest Telegram inviato')
        except Exception as e:
            logger.error(f'Errore generazione digest: {e}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
