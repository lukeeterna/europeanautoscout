#!/usr/bin/env python3
"""
on_demand_runner.py — ARGOS On-Demand Pipeline Runner
Thin wrapper: scraper esistenti -> CoVe scoring -> PDF dossier

Chiamato quando un dealer chiede un veicolo specifico.
Input: marca, budget, [modello, anno, km]
Output: path del PDF dossier su stdout

Uso:
  python3 tools/on_demand_runner.py --marca BMW --budget 35000
  python3 tools/on_demand_runner.py --marca Mercedes --modello GLC --budget 40000 --anno-min 2020

Componenti usati (ZERO nuovi moduli):
  - tools/scrapers/market_intelligence.py -> get_scraper() factory
  - src/cove/cove_engine_v4.py -> scoring (invocato, MAI modificato)
  - tools/scripts/pdf_generator_enterprise.py -> PDF output
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('on_demand_runner')

DOSSIER_DIR = PROJECT_ROOT / 'dossiers'
DOSSIER_DIR.mkdir(exist_ok=True)


def scrape_portal(portal_name, params):
    """Scrape un singolo portale usando l'interfaccia BaseScraper.scrape_model().
    Ritorna lista di dict (listing serializzati)."""
    try:
        from tools.scrapers.market_intelligence import get_scraper
        scraper = get_scraper(portal_name)
        if not scraper:
            return []

        make = params['make']
        model = params.get('model', '')
        year_min = params.get('year_min', 2018)
        year_max = params.get('year_max', 2025)
        km_max = params.get('mileage_max', 100000)

        # BaseScraper.scrape_model() -> List[Listing]
        listings = scraper.scrape_model(
            make=make,
            model=model,
            year_min=year_min,
            year_max=year_max,
            km_max=km_max,
        )

        # Filtra per budget (scrape_model non ha price filter)
        # Se price_eur=0 il parser non ha estratto il prezzo — includi comunque,
        # il CoVe scoring gestirà la qualità dati
        price_max = params.get('price_max', 999999)
        price_min = int(price_max * 0.60)
        results = []
        for lst in (listings or []):
            price = getattr(lst, 'price_eur', 0) or 0
            if price == 0 or (price_min <= price <= price_max):
                results.append(listing_to_dict(lst))

        logger.info(f'{portal_name}: {len(results)} risultati (di {len(listings or [])} totali)')
        return results
    except Exception as e:
        logger.warning(f'Scraper {portal_name} errore: {e}')
        return []


def listing_to_dict(lst) -> dict:
    """Converte un Listing object in dict per CoVe/PDF."""
    return {
        'listing_id': getattr(lst, 'listing_id', ''),
        'portal': getattr(lst, 'portal', ''),
        'make': getattr(lst, 'make', ''),
        'model': getattr(lst, 'model', ''),
        'price_eur': getattr(lst, 'price_eur', 0),
        'year': getattr(lst, 'year', 0),
        'km': getattr(lst, 'km', 0),
        'fuel': str(getattr(lst, 'fuel', '')),
        'transmission': str(getattr(lst, 'transmission', '')),
        'color': getattr(lst, 'color', ''),
        'vin': getattr(lst, 'vin', ''),
        'listing_url': getattr(lst, 'listing_url', ''),
        'image_url': getattr(lst, 'image_url', ''),
        'country': getattr(lst, 'country', ''),
        'seller_type': str(getattr(lst, 'seller_type', '')),
        'title': getattr(lst, 'title', ''),
    }


def enrich_listings(listing_dicts, max_enrich=30):
    """Enrich listing dicts with missing data via detail page fetching.
    Converts dicts to Listing objects, runs enricher, converts back."""
    try:
        from tools.scrapers.models import Listing as ScraperListing
        from tools.scrapers.detail_enricher import DetailEnricher

        # Convert dicts to Listing objects for the enricher
        listings = []
        for d in listing_dicts:
            lst = ScraperListing(
                listing_id=d.get('listing_id', ''),
                portal=d.get('portal', ''),
                country=d.get('country', 'DE'),
                make=d.get('make', ''),
                model=d.get('model', ''),
                year=d.get('year', 0),
                km=d.get('km', 0),
                price_eur=d.get('price_eur', 0),
                listing_url=d.get('listing_url', ''),
                vin=d.get('vin', ''),
            )
            listings.append(lst)

        # Limit enrichment to avoid rate-limiting
        enricher = DetailEnricher(delay_seconds=2.0, max_failures_per_portal=3)
        enriched, attempted = enricher.enrich(listings[:max_enrich])
        logger.info(f'Enrichment: {enriched}/{attempted} listing arricchiti')

        # Convert back to dicts, merging enriched data
        for i, lst in enumerate(listings):
            if i < len(listing_dicts):
                if lst.year > 0:
                    listing_dicts[i]['year'] = lst.year
                if lst.km > 0:
                    listing_dicts[i]['km'] = lst.km
                if lst.price_eur > 0:
                    listing_dicts[i]['price_eur'] = lst.price_eur

        return listing_dicts
    except Exception as e:
        logger.warning(f'Enrichment errore: {e}')
        return listing_dicts


def score_vehicles(listings):
    """Applica CoVe Engine v4 ai listing. Ritorna lista ordinata per score."""
    cove_path = PROJECT_ROOT / 'src' / 'cove' / 'cove_engine_v4.py'
    if not cove_path.exists():
        logger.warning('CoVe Engine v4 non trovato — skip scoring')
        return listings

    try:
        # Add src/cove to path for CoVe imports (fraud_flags, market_verifier, etc.)
        cove_dir = str(PROJECT_ROOT / 'src' / 'cove')
        if cove_dir not in sys.path:
            sys.path.insert(0, cove_dir)

        from cove_engine_v4 import CoVeEngine, Listing as CoveListing

        engine = CoVeEngine()
        scored = []
        for listing_dict in listings:
            try:
                # Convert scraper dict to CoVe Listing dataclass
                cove_listing = CoveListing(
                    listing_id=listing_dict.get('listing_id', ''),
                    make=listing_dict.get('make', ''),
                    model=listing_dict.get('model', ''),
                    year=listing_dict.get('year', 0),
                    km=listing_dict.get('km', 0),
                    price=listing_dict.get('price_eur', 0),
                    vin=listing_dict.get('vin') or None,
                    source=listing_dict.get('portal', 'autoscout24'),
                )
                result = engine.analyze(cove_listing)
                listing_dict['_cove_score'] = result.confidence
                listing_dict['_cove_recommendation'] = result.recommendation
                listing_dict['_cove_confidence'] = result.confidence
                scored.append(listing_dict)
            except Exception as e:
                logger.debug(f'CoVe scoring errore per {listing_dict.get("listing_id")}: {e}')
                listing_dict['_cove_score'] = 0
                listing_dict['_cove_recommendation'] = 'SKIP'
                scored.append(listing_dict)

        scored.sort(key=lambda x: x.get('_cove_score', 0), reverse=True)
        proceed_count = sum(1 for s in scored if s.get('_cove_recommendation') == 'PROCEED')
        logger.info(f'CoVe scoring completato: {proceed_count} PROCEED su {len(scored)} totali')
        return scored
    except Exception as e:
        logger.warning(f'CoVe import errore: {e}')
        return listings


def generate_dossier(top_vehicles, params, dealer_name=None):
    """Genera PDF dossier con pdf_generator_enterprise.py.

    La CLI del PDF generator richiede --listing <id> --dealer <name> --output <dir>
    e cerca i dati in DuckDB. Se non disponibile, usa fallback JSON con dati inline.
    """
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    marca = params['make']
    modello = params.get('model', '')
    name_part = f'_{dealer_name.replace(" ", "_")}' if dealer_name else ''
    pdf_name = f'ARGOS_{marca}_{modello}{name_part}_{ts}.pdf'
    pdf_path = DOSSIER_DIR / pdf_name

    gen_script = PROJECT_ROOT / 'tools' / 'scripts' / 'pdf_generator_enterprise.py'
    if gen_script.exists() and top_vehicles:
        import subprocess
        best = top_vehicles[0]
        listing_id = best.get('listing_id', '')

        # Strategy 1: Try --listing mode (listing in DuckDB after CoVe scoring)
        if listing_id and dealer_name:
            try:
                result = subprocess.run(
                    [sys.executable, str(gen_script),
                     '--listing', listing_id,
                     '--dealer', dealer_name,
                     '--output', str(DOSSIER_DIR)],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    out_line = result.stdout.strip().split('\n')[-1]
                    if 'PDF at:' in out_line:
                        out_path = out_line.split('PDF at:')[-1].strip()
                        if os.path.exists(out_path):
                            return out_path
                logger.info(f'PDF --listing mode fallback: {result.stderr[:200]}')
            except Exception as e:
                logger.info(f'PDF --listing mode errore: {e}')

        # Strategy 2: Try --data mode (inline JSON, no DB needed)
        try:
            data = json.dumps({
                'vehicles': top_vehicles[:5],
                'search_params': params,
                'generated_at': datetime.now().isoformat(),
            })
            result = subprocess.run(
                [sys.executable, str(gen_script),
                 '--data', data,
                 '--dealer', dealer_name or 'Dealer',
                 '--output', str(DOSSIER_DIR)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                out_line = result.stdout.strip().split('\n')[-1]
                if 'PDF at:' in out_line:
                    out_path = out_line.split('PDF at:')[-1].strip()
                    if os.path.exists(out_path):
                        return out_path
            logger.warning(f'PDF --data mode: {result.stderr[:300]}')
        except Exception as e:
            logger.warning(f'PDF --data mode errore: {e}')

    # Fallback: generate standalone dossier JSON (for manual PDF later)
    json_path = pdf_path.with_suffix('.json')
    json_path.write_text(json.dumps({
        'vehicles': top_vehicles[:5],
        'params': params,
        'dealer': dealer_name,
        'generated_at': datetime.now().isoformat(),
    }, indent=2, ensure_ascii=False))
    logger.info(f'Dossier JSON salvato: {json_path}')
    return str(json_path)


def run(marca, budget, modello=None, anno_min=None, km_max=None, dealer_name=None):
    """Entry point pipeline on-demand."""
    t0 = time.time()
    logger.info(f'Pipeline: {marca} {modello or ""} budget={budget}')

    params = {
        'make': marca,
        'price_max': budget,
        'model': modello,
        'year_min': anno_min or 2018,
        'mileage_max': km_max or 100000,
    }

    # Step 1: Scrape in parallelo (max 3 portali)
    portals = ['autoscout24_de', 'mobile_de']
    if marca.upper() in ('BMW', 'MERCEDES', 'AUDI'):
        portals.append('autoscout24_nl')

    all_results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scrape_portal, p, params): p for p in portals}
        for future in as_completed(futures, timeout=120):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                logger.warning(f'Scraper timeout/error: {e}')

    logger.info(f'Totale listing grezzi: {len(all_results)}')

    if not all_results:
        logger.warning('Zero risultati — pipeline terminata')
        return None

    # Step 1b: Enrich listings with missing price/km/year via detail pages
    zero_data = sum(1 for r in all_results if r.get('price_eur', 0) == 0 or r.get('km', 0) == 0)
    if zero_data > 0:
        logger.info(f'{zero_data}/{len(all_results)} listing con dati mancanti — avvio enrichment')
        all_results = enrich_listings(all_results, max_enrich=30)

    # Step 2: CoVe scoring
    scored = score_vehicles(all_results)

    # Filtra solo PROCEED e VIN_CHECK (MAI usare "verdict" — regola CoVe immutabile)
    top = [v for v in scored if v.get('_cove_recommendation') in ('PROCEED', 'VIN_CHECK')][:5]
    if not top:
        # Distingui: CoVe non ha scorato (errore tecnico) vs ha scorato tutto SKIP
        has_any_score = any(v.get('_cove_score', 0) > 0 for v in scored)
        if has_any_score:
            logger.warning('Zero veicoli PROCEED/VIN_CHECK — tutti SKIP, nessun dossier generato')
            return None
        else:
            logger.warning('CoVe non ha scorato (lock/errore) — uso top per prezzo come fallback')
            top = sorted(scored, key=lambda x: x.get('price_eur', 0))[:5]

    logger.info(f'Top {len(top)} veicoli selezionati')

    # Step 3: PDF
    pdf_path = generate_dossier(top, params, dealer_name)

    elapsed = round(time.time() - t0, 1)
    logger.info(f'Pipeline completata in {elapsed}s — {pdf_path}')
    return pdf_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ARGOS On-Demand Pipeline Runner')
    parser.add_argument('--marca', required=True)
    parser.add_argument('--budget', type=int, required=True)
    parser.add_argument('--modello', default=None)
    parser.add_argument('--anno-min', type=int, default=None)
    parser.add_argument('--km-max', type=int, default=None)
    parser.add_argument('--dealer', default=None, help='Nome dealer per il PDF')
    args = parser.parse_args()

    result = run(args.marca, args.budget, args.modello, args.anno_min, args.km_max, args.dealer)
    if result:
        print(result)  # stdout = path PDF (letto da wa_incoming_listener)
    else:
        sys.exit(1)
