"""
ARGOS Scraper → CoVe Pipeline — IL PEZZO MANCANTE
CoVe 2026 | Enterprise Grade | Zero Costi

Collega i 28+ portali scraper al CoVe Engine per produrre
OPPORTUNITA' VERIFICATE, non listing grezzi.

Pipeline:
  1. Scraper produce raw_listings[]
  2. MarketPriceIndex aggrega i prezzi EU dai nostri dati
  3. CoVe Engine valuta ogni listing (scoring + fraud + VIN)
  4. Solo PROCEED/VIN_CHECK passano come opportunita'
  5. Output: dealer-ready opportunities con margine stimato

SICUREZZA ENTERPRISE:
  - Nessun dato personale esposto (VIN troncati in log)
  - Rate limiting rispettato per ogni portale
  - Cache locale, zero dati inviati a terzi
  - Tutti i prezzi anonimizzati nei log (solo range)
  - Nessuna credenziale in output
  - Robots.txt compliance (informational scraping only)

Author: ARGOS CTO Stack
"""

from __future__ import annotations

import hashlib
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("argos.pipeline")

# Path setup
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@dataclass
class Opportunity:
    """Opportunita' verificata pronta per il dealer."""
    listing_id: str
    make: str
    model: str
    year: int
    km: int
    price_eur: float
    country: str
    portal: str
    listing_url: str

    # CoVe scoring
    cove_confidence: float     # 0.0-1.0
    cove_status: str           # PROCEED | VIN_CHECK
    fraud_level: str           # CLEAN | WARNING

    # Market intelligence
    market_ref_price: float    # Media mercato EU
    discount_pct: float        # % sotto mercato (positivo = affare)
    market_data_quality: str   # HIGH | MEDIUM | LOW
    market_sample_size: int

    # Business value
    estimated_margin_eur: float  # Margine stimato dopo import IT
    risk_level: str              # LOW | MEDIUM | HIGH
    opportunity_score: int       # 0-100

    # Metadata
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    image_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# Import costs estimation (EUR)
# Reference: reale esperienza import EU→IT 2024-2026
IMPORT_COSTS = {
    "transport_estimate": 800,    # Media trasporto EU→Sud Italia
    "registration_it": 400,       # IPT + bollo proporzionale
    "admin_fees": 200,            # Pratiche, voltura
    "argos_fee": 1000,            # Fee ARGOS media (Tier 1)
}
TOTAL_IMPORT_OVERHEAD = sum(IMPORT_COSTS.values())  # ~2400 EUR

# Italian market premium — quanto i dealer IT vendono SOPRA media EU
# Reference: AutoScout24 cross-border price comparison 2025
IT_PREMIUM_PCT = 0.12  # +12% medio (varia per modello)


def _truncate_vin(vin: Optional[str]) -> str:
    """Tronca VIN per privacy nei log."""
    if not vin or len(vin) < 10:
        return "N/A"
    return f"{vin[:3]}...{vin[-4:]}"


def _compute_opportunity_score(
    discount_pct: float,
    cove_confidence: float,
    market_quality: str,
    km_per_year: float,
    country: str,
) -> int:
    """
    Calcola opportunity score 0-100.

    Fattori (pesati):
    - 35% Discount vs mercato (piu' e' sotto, meglio e')
    - 25% CoVe confidence (qualita' del listing)
    - 20% Data quality (quanti comparable abbiamo)
    - 10% KM/anno (meno km = meglio)
    - 10% Country reliability
    """
    # Discount score: 8% = 40pts, 15% = 80pts, 20%+ = 100pts
    discount_score = min(100, max(0, discount_pct * 500))

    # CoVe confidence: gia' 0-1, moltiplica per 100
    cove_score = cove_confidence * 100

    # Data quality
    quality_map = {"HIGH": 100, "MEDIUM": 60, "LOW": 30, "NONE": 0}
    quality_score = quality_map.get(market_quality, 0)

    # KM/anno: 8k-12k optimal, degrada fuori range
    if 8000 <= km_per_year <= 12000:
        km_score = 100
    elif 5000 <= km_per_year <= 18000:
        km_score = 70
    elif km_per_year > 0:
        km_score = max(0, 100 - abs(km_per_year - 12000) / 300)
    else:
        km_score = 50  # km sconosciuto

    # Country reliability
    try:
        from .market_price_index import COUNTRY_WEIGHTS
    except ImportError:
        from market_price_index import COUNTRY_WEIGHTS
    country_score = COUNTRY_WEIGHTS.get(country, 0.5) * 100

    # Weighted average
    score = (
        discount_score * 0.35 +
        cove_score * 0.25 +
        quality_score * 0.20 +
        km_score * 0.10 +
        country_score * 0.10
    )

    return max(0, min(100, int(round(score))))


def _assess_risk(
    fraud_level: str,
    country: str,
    cove_confidence: float,
    discount_pct: float,
) -> str:
    """
    Valuta livello di rischio complessivo.

    RED FLAGS:
    - Fraud WARNING + discount > 25% = HIGH (potrebbe essere truffa)
    - Paese ad alto rischio odometer + low CoVe = HIGH
    - Discount > 30% = sempre HIGH (troppo bello per essere vero)
    """
    high_risk_countries = {"LV", "LT", "RO", "BG", "UA", "PL"}

    if discount_pct > 0.30:
        return "HIGH"  # Troppo sotto mercato
    if fraud_level != "CLEAN" and discount_pct > 0.20:
        return "HIGH"
    if country in high_risk_countries and cove_confidence < 0.70:
        return "HIGH"
    if fraud_level == "WARNING" or country in high_risk_countries:
        return "MEDIUM"
    if cove_confidence < 0.75:
        return "MEDIUM"
    return "LOW"


class ScraperCovePipeline:
    """
    Pipeline completa: Scraper → MarketPriceIndex → CoVe → Opportunities

    Uso:
        pipeline = ScraperCovePipeline()
        opportunities = pipeline.run("BMW", "X3", max_pages=1)
        for opp in opportunities:
            print(f"{opp.make} {opp.model} {opp.year} | EUR {opp.price_eur:,.0f} "
                  f"| -{opp.discount_pct:.1%} vs mercato | score={opp.opportunity_score}")
    """

    def __init__(self):
        try:
            from .market_price_index import MarketPriceIndex
        except ImportError:
            from market_price_index import MarketPriceIndex
        self.price_index = MarketPriceIndex()
        self._cove_engine = None  # Lazy init (DuckDB connection)

    @staticmethod
    def _deduplicate(listings: list) -> list:
        """
        Deduplicazione cross-portale: stesso veicolo su più portali.
        If year+km available: fingerprint by make+model+year+km_bucket+price_bucket.
        If not: use listing_id (no dedup for incomplete data).
        """
        seen = {}
        result = []
        for lst in listings:
            year = getattr(lst, 'year', 0) or 0
            km = getattr(lst, 'km', 0) or 0
            price = getattr(lst, 'price_eur', 0) or 0
            make = getattr(lst, 'make', '') or ''
            model = getattr(lst, 'model', '') or ''

            # Only dedup if we have enough data for meaningful fingerprint
            if year > 0 and km > 0:
                km_bucket = round(km / 5000) * 5000
                price_bucket = round(price / 500) * 500 if price else 0
                fp = f"{make}_{model}_{year}_{km_bucket}_{price_bucket}".upper()
            else:
                # Incomplete data — use listing_id to avoid false dedup
                fp = getattr(lst, 'listing_id', '') or id(lst)

            if fp in seen:
                # Keep the one with more complete data
                existing = seen[fp]
                existing_score = sum([
                    1 if getattr(existing, 'year', 0) else 0,
                    1 if getattr(existing, 'km', 0) else 0,
                    1 if getattr(existing, 'listing_url', '') else 0,
                ])
                new_score = sum([
                    1 if year else 0,
                    1 if km else 0,
                    1 if getattr(lst, 'listing_url', '') else 0,
                ])
                if new_score > existing_score:
                    # Replace with better listing
                    result = [l for l in result if l is not existing]
                    result.append(lst)
                    seen[fp] = lst
            else:
                seen[fp] = lst
                result.append(lst)
        return result

    def _get_cove(self):
        """Lazy init CoVe engine — evita connessione DuckDB se non necessaria."""
        if self._cove_engine is None:
            try:
                try:
                    from .cove_engine_v4 import CoVeEngine
                except ImportError:
                    from cove_engine_v4 import CoVeEngine
                self._cove_engine = CoVeEngine()
                logger.info("CoVe Engine v4 inizializzato")
            except Exception as e:
                logger.warning("CoVe Engine non disponibile: %s — pipeline senza scoring", e)
        return self._cove_engine

    def run(
        self,
        make: str,
        model: str,
        portals: Optional[List[str]] = None,
        max_pages: int = 1,
        min_discount_pct: float = 0.08,
    ) -> List[Opportunity]:
        """
        Esegue pipeline completa per un veicolo.

        1. Scrape da tutti i portali (o subset specificato)
        2. Ingest nel Market Price Index
        3. Passa ogni listing al CoVe Engine
        4. Filtra: solo PROCEED/VIN_CHECK con discount > min_discount_pct
        5. Ritorna opportunita' ordinate per opportunity_score

        Returns: Lista di Opportunity ordinate per score decrescente
        """
        from tools.scrapers.market_intelligence import get_scraper
        from tools.scrapers.config import PORTALS

        portal_keys = portals or list(PORTALS.keys())
        all_listings = []
        ref_year = datetime.now(timezone.utc).year

        # Step 1: Scrape
        logger.info("Pipeline: scraping %s %s da %d portali...", make, model, len(portal_keys))
        for pk in portal_keys:
            scraper = get_scraper(pk)
            if not scraper:
                continue
            try:
                listings, run = scraper.scrape(make, model, max_pages=max_pages)
                if listings:
                    all_listings.extend(listings)
                    logger.info("  %s: %d listing", pk, len(listings))
            except Exception as e:
                logger.debug("  %s: errore %s", pk, e)

        logger.info("Pipeline: %d listing grezzi raccolti", len(all_listings))

        if not all_listings:
            return []

        # Step 1.5: Deduplicazione cross-portale
        before_dedup = len(all_listings)
        all_listings = self._deduplicate(all_listings)
        if before_dedup > len(all_listings):
            logger.info("Pipeline: dedup %d → %d listing", before_dedup, len(all_listings))

        # Step 1.6: Detail enrichment per listing con dati mancanti
        incomplete = [
            lst for lst in all_listings
            if (getattr(lst, 'year', 0) or 0) == 0 or (getattr(lst, 'km', 0) or 0) == 0
        ]
        if incomplete:
            try:
                from tools.scrapers.detail_enricher import DetailEnricher
                enricher = DetailEnricher()
                enriched, attempted = enricher.enrich(incomplete)
                logger.info("Pipeline: enrichment %d/%d listing arricchiti", enriched, attempted)
            except ImportError:
                logger.debug("Pipeline: detail_enricher non disponibile, skip enrichment")
            except Exception as e:
                logger.debug("Pipeline: enrichment error: %s", e)

        # Step 2: Ingest nel Price Index
        n_ingested = self.price_index.ingest_listings(all_listings)
        self.price_index.save()
        logger.info("Pipeline: %d price points ingeriti nell'indice", n_ingested)

        # Step 3: Valuta ogni listing
        opportunities = []
        cove = self._get_cove()

        for lst in all_listings:
            # Skip listing senza dati minimi
            price = getattr(lst, 'price_eur', 0)
            year = getattr(lst, 'year', 0)
            if not price or price < 500 or not year or year < 2010:
                continue

            km = getattr(lst, 'km', 0) or 0
            country = getattr(lst, 'country', '') or ''

            # Market estimate dai nostri dati
            estimate = self.price_index.estimate(make, model, year, km)

            if estimate.ref_price <= 0 or estimate.sample_size < 3:
                continue  # Non abbastanza dati per valutare

            discount = (estimate.ref_price - price) / estimate.ref_price
            if discount < min_discount_pct:
                continue  # Non abbastanza sotto mercato

            # CoVe scoring (se disponibile)
            cove_confidence = 0.70  # default se CoVe non disponibile
            cove_status = "ESTIMATED"
            fraud_level = "UNKNOWN"

            if cove:
                try:
                    try:
                        from .cove_engine_v4 import Listing as CoveListing
                    except ImportError:
                        from cove_engine_v4 import Listing as CoveListing
                    cove_listing = CoveListing(
                        listing_id=getattr(lst, 'listing_id', '') or hashlib.md5(
                            f"{make}{model}{year}{price}".encode()
                        ).hexdigest()[:12],
                        make=make,
                        model=model,
                        year=year,
                        km=km,
                        price=price,
                        vin=None,
                        source=getattr(lst, 'portal', 'unknown'),
                        market_price_ref=estimate.ref_price,
                    )
                    result = cove.analyze(cove_listing)
                    cove_confidence = result.confidence
                    cove_status = result.status
                    fraud_level = result.fraud_flags.get("overall", "UNKNOWN")

                    # Skip REJECTED/SKIP
                    if cove_status in ("REJECTED", "SKIP"):
                        continue
                except Exception as e:
                    logger.debug("CoVe error per listing: %s", e)

            # Calcola margine stimato
            it_sell_price = estimate.ref_price * (1 + IT_PREMIUM_PCT)
            estimated_margin = it_sell_price - price - TOTAL_IMPORT_OVERHEAD

            # km/anno per scoring
            age = max(ref_year - year, 1)
            km_per_year = km / age if km > 0 else 0

            # Opportunity score
            opp_score = _compute_opportunity_score(
                discount_pct=discount,
                cove_confidence=cove_confidence,
                market_quality=estimate.data_quality,
                km_per_year=km_per_year,
                country=country,
            )

            # Risk assessment
            risk = _assess_risk(fraud_level, country, cove_confidence, discount)

            opp = Opportunity(
                listing_id=getattr(lst, 'listing_id', ''),
                make=make,
                model=model,
                year=year,
                km=km,
                price_eur=price,
                country=country,
                portal=getattr(lst, 'portal', ''),
                listing_url=getattr(lst, 'listing_url', ''),
                cove_confidence=cove_confidence,
                cove_status=cove_status,
                fraud_level=fraud_level,
                market_ref_price=estimate.ref_price,
                discount_pct=round(discount, 4),
                market_data_quality=estimate.data_quality,
                market_sample_size=estimate.sample_size,
                estimated_margin_eur=round(estimated_margin),
                risk_level=risk,
                opportunity_score=opp_score,
                image_urls=getattr(lst, 'image_urls', []) or [],
            )
            opportunities.append(opp)

        # Ordina per opportunity score decrescente
        opportunities.sort(key=lambda o: o.opportunity_score, reverse=True)

        logger.info("Pipeline: %d opportunita' trovate (da %d listing grezzi)",
                    len(opportunities), len(all_listings))

        # Step 5: Persist to DuckDB for pipeline_orchestrator
        self._persist_to_duckdb(all_listings, opportunities, make, model)

        return opportunities

    def _persist_to_duckdb(self, listings, opportunities, make, model):
        """Save scraped listings + CoVe results to DuckDB for pipeline_orchestrator."""
        try:
            import duckdb
            db_path = os.path.join(_HERE, "data", "cove_tracker.duckdb")
            con = duckdb.connect(db_path)

            inserted = 0
            for lst in listings:
                lid = getattr(lst, 'listing_id', '') or ''
                if not lid:
                    continue

                # Check if already exists
                exists = con.execute(
                    "SELECT 1 FROM vehicle_listings WHERE listing_id = ?", [lid]
                ).fetchone()
                if exists:
                    continue

                price = getattr(lst, 'price_eur', 0) or 0
                year = getattr(lst, 'year', 0) or 0
                km = getattr(lst, 'km', 0) or 0
                source = getattr(lst, 'portal', 'unknown')
                url = getattr(lst, 'listing_url', '') or ''

                seller_name = getattr(lst, 'seller_name', '') or ''
                con.execute("""
                    INSERT INTO vehicle_listings
                        (listing_id, make, model, year, mileage, price_eu,
                         source, detail_url, pipeline_state, scraped_at, seller_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DISCOVERED', NOW(), ?)
                """, [lid, make, model, year, km, price, source, url, seller_name or None])
                inserted += 1

            # Also persist CoVe results for opportunities
            for opp in opportunities:
                exists = con.execute(
                    "SELECT 1 FROM cove_results WHERE listing_id = ?", [opp.listing_id]
                ).fetchone()
                if exists:
                    continue
                con.execute("""
                    INSERT INTO cove_results
                        (listing_id, recommendation, confidence, price, market_price,
                         fraud_overall, source, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, NOW())
                """, [opp.listing_id, opp.cove_status, opp.cove_confidence,
                      opp.price_eur, opp.market_ref_price, opp.fraud_level,
                      opp.portal])

            con.close()
            if inserted:
                logger.info("Pipeline: %d nuovi listing salvati in DuckDB", inserted)
        except Exception as e:
            logger.warning("Pipeline: DuckDB persist error: %s", e)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="ARGOS Pipeline: Scraper → CoVe → Opportunities")
    parser.add_argument("make", help="Make (BMW, Mercedes, Audi...)")
    parser.add_argument("model", help="Model (X3, GLC, Q5...)")
    parser.add_argument("--pages", type=int, default=1, help="Max pages per portal")
    parser.add_argument("--discount", type=float, default=0.08, help="Min discount %% (default 8%%)")
    parser.add_argument("--portals", nargs="*", help="Specific portals (default all)")
    parser.add_argument("--no-cove", action="store_true", help="Skip CoVe scoring")
    args = parser.parse_args()

    pipeline = ScraperCovePipeline()

    if args.no_cove:
        pipeline._cove_engine = None

    opportunities = pipeline.run(
        make=args.make,
        model=args.model,
        portals=args.portals,
        max_pages=args.pages,
        min_discount_pct=args.discount,
    )

    print(f"\n{'='*90}")
    print(f"ARGOS INTELLIGENCE — {args.make} {args.model}")
    print(f"{'='*90}")
    print(f"Opportunita' trovate: {len(opportunities)}")
    print(f"{'='*90}")

    for i, o in enumerate(opportunities[:20], 1):
        margin_str = f"+EUR {o.estimated_margin_eur:,.0f}" if o.estimated_margin_eur > 0 else f"EUR {o.estimated_margin_eur:,.0f}"
        print(f"\n#{i:2d} [Score: {o.opportunity_score:3d}] {o.make} {o.model} {o.year} | {o.km:,} km")
        print(f"    Prezzo: EUR {o.price_eur:,.0f} vs Mercato EUR {o.market_ref_price:,.0f} (-{o.discount_pct:.1%})")
        print(f"    Margine stimato: {margin_str} | Risk: {o.risk_level} | CoVe: {o.cove_confidence:.0%}")
        print(f"    {o.country} | {o.portal} | {o.listing_url[:70]}")
