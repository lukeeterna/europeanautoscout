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
    """Converte un Listing object in dict per CoVe/PDF.
    Usa Listing.to_dict() se disponibile, altrimenti estrae manualmente
    con .value per gli Enum (mai str(Enum) che produce 'FuelType.DIESEL')."""
    if hasattr(lst, 'to_dict'):
        d = lst.to_dict()
        # Normalize image_urls from comma-string to list for downstream
        if isinstance(d.get('image_urls'), str) and d['image_urls']:
            d['image_urls'] = d['image_urls'].split(',')
        elif not d.get('image_urls'):
            d['image_urls'] = []
        return d

    # Fallback manuale (non dovrebbe servire)
    def _enum_val(v):
        return v.value if hasattr(v, 'value') else str(v)

    return {
        'listing_id': getattr(lst, 'listing_id', ''),
        'portal': getattr(lst, 'portal', ''),
        'make': getattr(lst, 'make', ''),
        'model': getattr(lst, 'model', ''),
        'price_eur': getattr(lst, 'price_eur', 0),
        'year': getattr(lst, 'year', 0),
        'km': getattr(lst, 'km', 0),
        'fuel_type': _enum_val(getattr(lst, 'fuel_type', 'unknown')),
        'transmission': _enum_val(getattr(lst, 'transmission', 'unknown')),
        'seller_type': _enum_val(getattr(lst, 'seller_type', 'unknown')),
        'variant': getattr(lst, 'variant', ''),
        'power_hp': getattr(lst, 'power_hp', 0),
        'vin': getattr(lst, 'vin', ''),
        'listing_url': getattr(lst, 'listing_url', ''),
        'image_urls': list(getattr(lst, 'image_urls', [])),
        'country': getattr(lst, 'country', ''),
        'seller_name': getattr(lst, 'seller_name', ''),
        'seller_location': getattr(lst, 'seller_location', ''),
    }


def enrich_listings(listing_dicts, max_enrich=30):
    """Enrich listing dicts with missing data via detail page fetching.
    Converts dicts to Listing objects, runs enricher, merges ALL enriched fields back."""
    try:
        from tools.scrapers.models import Listing as ScraperListing, FuelType, Transmission, SellerType
        from tools.scrapers.detail_enricher import DetailEnricher

        # Convert dicts to full Listing objects (preserve all fields)
        listings = []
        for d in listing_dicts:
            # Parse fuel_type from string value
            ft = FuelType.UNKNOWN
            fuel_raw = d.get('fuel_type', d.get('fuel', 'unknown'))
            if isinstance(fuel_raw, str):
                try:
                    ft = FuelType(fuel_raw.lower().strip())
                except ValueError:
                    ft = FuelType.UNKNOWN

            # Parse transmission
            tr = Transmission.UNKNOWN
            tr_raw = d.get('transmission', 'unknown')
            if isinstance(tr_raw, str):
                try:
                    tr = Transmission(tr_raw.lower().strip())
                except ValueError:
                    tr = Transmission.UNKNOWN

            # Parse seller_type
            st = SellerType.UNKNOWN
            st_raw = d.get('seller_type', 'unknown')
            if isinstance(st_raw, str):
                try:
                    st = SellerType(st_raw.lower().strip())
                except ValueError:
                    st = SellerType.UNKNOWN

            # Parse image_urls
            img_urls = d.get('image_urls', [])
            if isinstance(img_urls, str):
                img_urls = [u.strip() for u in img_urls.split(',') if u.strip()]

            lst = ScraperListing(
                listing_id=d.get('listing_id', ''),
                portal=d.get('portal', ''),
                country=d.get('country', 'DE'),
                make=d.get('make', ''),
                model=d.get('model', ''),
                variant=d.get('variant', ''),
                year=d.get('year', 0),
                km=d.get('km', 0),
                price_eur=d.get('price_eur', 0),
                fuel_type=ft,
                transmission=tr,
                power_hp=d.get('power_hp', 0),
                seller_type=st,
                seller_name=d.get('seller_name', ''),
                seller_location=d.get('seller_location', ''),
                listing_url=d.get('listing_url', ''),
                image_urls=img_urls,
                vin=d.get('vin', ''),
            )
            listings.append(lst)

        # Limit enrichment to avoid rate-limiting
        enricher = DetailEnricher(delay_seconds=2.0, max_failures_per_portal=3)
        enriched, attempted = enricher.enrich(listings[:max_enrich])
        logger.info(f'Enrichment: {enriched}/{attempted} listing arricchiti')

        # Merge ALL enriched data back to dicts
        for i, lst in enumerate(listings):
            if i < len(listing_dicts):
                if lst.year > 0:
                    listing_dicts[i]['year'] = lst.year
                if lst.km > 0:
                    listing_dicts[i]['km'] = lst.km
                if lst.price_eur > 0:
                    listing_dicts[i]['price_eur'] = lst.price_eur
                if lst.fuel_type != FuelType.UNKNOWN:
                    listing_dicts[i]['fuel_type'] = lst.fuel_type.value
                if lst.transmission != Transmission.UNKNOWN:
                    listing_dicts[i]['transmission'] = lst.transmission.value
                if lst.image_urls:
                    listing_dicts[i]['image_urls'] = list(lst.image_urls)
                if lst.seller_name:
                    listing_dicts[i]['seller_name'] = lst.seller_name
                if lst.seller_location:
                    listing_dicts[i]['seller_location'] = lst.seller_location
                if lst.power_hp > 0:
                    listing_dicts[i]['power_hp'] = lst.power_hp
                if lst.variant:
                    listing_dicts[i]['variant'] = lst.variant
                # Color from extra_data (enricher stores it there)
                if lst.extra_data.get('color'):
                    listing_dicts[i]['color'] = lst.extra_data['color']

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

        # Strategy 1 (PRIMARY): --data mode with enriched JSON (has ALL fields)
        # This is the primary strategy because the enriched dict has price, fuel,
        # color, images — DuckDB only has CoVe scoring fields.
        try:
            data_dict = {
                'vehicles': top_vehicles[:5],
                'search_params': params,
                'generated_at': datetime.now().isoformat(),
            }
            data = json.dumps(data_dict, default=str)
            # Save JSON alongside PDF for evidence/audit
            json_path = DOSSIER_DIR / f"ARGOS_{params.get('make','X')}_{params.get('model','X')}_{dealer_name or 'Dealer'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_path, 'w') as jf:
                json.dump(data_dict, jf, indent=2, default=str)
            logger.info(f'JSON saved: {json_path}')
            result = subprocess.run(
                [sys.executable, str(gen_script),
                 '--data', data,
                 '--dealer', dealer_name or 'Dealer',
                 '--output', str(DOSSIER_DIR)],
                capture_output=True, text=True, timeout=360
            )
            # Log full subprocess output for debugging image pipeline
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    logger.info(f'PDF> {line}')
            if result.stderr:
                logger.info(f'PDF subprocess stderr: {result.stderr[-200:]}')
            if result.returncode == 0:
                out_line = result.stdout.strip().split('\n')[-1]
                if 'PDF at:' in out_line:
                    out_path = out_line.split('PDF at:')[-1].strip()
                    if os.path.exists(out_path):
                        pdf_size = os.path.getsize(out_path)
                        logger.info(f'PDF generated: {out_path} ({pdf_size:,} bytes)')
                        return out_path
            logger.warning(f'PDF --data mode fallback: {result.stderr[:300]}')
        except Exception as e:
            logger.warning(f'PDF --data mode errore: {e}')

        # Strategy 2 (FALLBACK): --listing mode from DuckDB
        best = top_vehicles[0]
        listing_id = best.get('listing_id', '')
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

    # Step 1c: A0 — Data completeness gate (SKIP_INCOMPLETE before CoVe)
    complete = []
    skipped = 0
    for r in all_results:
        price = r.get('price_eur', 0) or 0
        km = r.get('km', 0) or 0
        year = r.get('year', 0) or 0
        if price <= 0 or km <= 0 or year < 2015:
            skipped += 1
            continue
        complete.append(r)
    if skipped > 0:
        logger.info(f'A0 completeness gate: {skipped} SKIP_INCOMPLETE (price=0/km=0/year<2015), {len(complete)} passano')
    if not complete:
        logger.warning('Zero listing completi dopo A0 gate — pipeline terminata')
        return None
    all_results = complete

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

    # Step 2b: A4 — Quality gate (GRADE >= C, images >= 3)
    MIN_CONFIDENCE = 0.60  # GRADE C threshold
    MIN_IMAGES = 3
    qualified = []
    for v in top:
        conf = v.get('_cove_confidence', 0)
        imgs = len(v.get('image_urls', []))
        if conf < MIN_CONFIDENCE:
            logger.info(f'A4 quality gate: SKIP {v.get("listing_id", "?")} — confidence {conf:.2f} < {MIN_CONFIDENCE}')
            continue
        if imgs < MIN_IMAGES:
            logger.info(f'A4 quality gate: SKIP {v.get("listing_id", "?")} — images {imgs} < {MIN_IMAGES}')
            continue
        qualified.append(v)

    if qualified:
        top = qualified
        logger.info(f'A4 quality gate: {len(top)} veicoli qualificati (GRADE >= C, images >= {MIN_IMAGES})')
    else:
        # Relax image requirement if no vehicles qualify — confidence is hard gate
        conf_only = [v for v in top if v.get('_cove_confidence', 0) >= MIN_CONFIDENCE]
        if conf_only:
            top = conf_only
            logger.warning(f'A4 quality gate: relaxed image requirement — {len(top)} veicoli con GRADE >= C ma < {MIN_IMAGES} foto')
        else:
            logger.warning(f'A4 quality gate: zero veicoli con GRADE >= C — usando top {len(top)} comunque')

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
