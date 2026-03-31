#!/usr/bin/env python3
"""
ARGOS Dealer Discovery — Subito.it Scraper
Trova dealer professionisti per provincia, estrae profilo, classifica "su commissione".

Strategia:
  1. Scrappa listings auto per provincia da Subito.it
  2. Estrae seller unici dal __NEXT_DATA__ JSON
  3. Per ogni seller PRO: conta annunci, analizza marche, cerca keyword commissione
  4. Produce lista dealer con commission_score

Usage:
  python3 tools/dealer_discovery/subito_dealer_scraper.py --province foggia
  python3 tools/dealer_discovery/subito_dealer_scraper.py --province foggia,cosenza,caserta
  python3 tools/dealer_discovery/subito_dealer_scraper.py --all-priority 1
"""

import json
import logging
import os
import random
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict
from urllib.parse import quote_plus

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.dealer_discovery.config import (
    PROVINCE_TARGET, COMMISSION_KEYWORDS, PREMIUM_BRANDS,
    COMMISSION_SCORING, RATE_LIMIT,
)

logger = logging.getLogger("argos.dealer_discovery.subito")

# ── Data classes ──────────────────────────────────────────────

@dataclass
class SubitoListing:
    listing_id: str
    title: str
    price: Optional[int] = None
    brand: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    seller_id: Optional[str] = None
    seller_name: Optional[str] = None
    seller_type: Optional[str] = None  # "private" / "professional"
    url: Optional[str] = None


@dataclass
class DiscoveredDealer:
    name: str
    province: str
    region: str
    source: str = "subito.it"
    seller_id: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    listing_count: int = 0
    brands: List[str] = field(default_factory=list)
    brand_diversity: int = 0
    premium_brands: List[str] = field(default_factory=list)
    premium_pct: float = 0.0
    has_commission_keywords: bool = False
    matched_keywords: List[str] = field(default_factory=list)
    shop_url: Optional[str] = None
    source_url: Optional[str] = None
    commission_score: float = 0.0
    fit_score: float = 0.0


# ── Fetcher ───────────────────────────────────────────────────

def _get_fetcher():
    """Get ResilientFetcher or fall back to curl_cffi/requests."""
    try:
        from tools.scrapers.resilient_fetcher import ResilientFetcher
        fetcher = ResilientFetcher()
        def _resilient_fetch(url, **kwargs):
            result = fetcher.fetch(url)
            if result and hasattr(result, 'text'):
                return result.text
            return result
        return _resilient_fetch
    except ImportError:
        pass

    # Fallback: curl_cffi (best for bypassing anti-bot)
    try:
        from curl_cffi import requests as curl_requests
        def _curl_fetch(url, **kwargs):
            resp = curl_requests.get(url, impersonate="chrome", timeout=30)
            resp.raise_for_status()
            return resp.text
        return _curl_fetch
    except ImportError:
        pass

    # Last resort: standard requests
    import requests
    def _simple_fetch(url, **kwargs):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "it-IT,it;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text
    return _simple_fetch


def _rate_limit():
    delay = random.uniform(RATE_LIMIT["subito_delay_min"], RATE_LIMIT["subito_delay_max"])
    time.sleep(delay)


# ── Parser ────────────────────────────────────────────────────

def _extract_next_data(html: str) -> Optional[dict]:
    """Extract __NEXT_DATA__ JSON from Subito.it HTML."""
    match = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        logger.warning("Failed to parse __NEXT_DATA__ JSON")
        return None


def _extract_listings_from_next_data(data: dict, province: str) -> List[SubitoListing]:
    """Extract listings from Subito.it __NEXT_DATA__."""
    listings = []

    # Navigate: props.pageProps.initialState.items.list
    try:
        items = data["props"]["pageProps"]["initialState"]["items"]["list"]
    except (KeyError, TypeError):
        items = []

    for wrapper in items:
        if not isinstance(wrapper, dict):
            continue

        # Subito wraps items: {"before":..., "item":{...}, "after":..., "kind":"DecoratedItem"}
        item = wrapper.get("item", wrapper)
        if not isinstance(item, dict):
            continue

        listing_id = str(item.get("urn", item.get("id", "")))
        title = item.get("subject", item.get("title", ""))

        # Price from features
        price = None
        features = item.get("features", {})
        if isinstance(features, dict):
            price_feat = features.get("/price", {})
            if isinstance(price_feat, dict):
                values = price_feat.get("values", [])
                if values and isinstance(values[0], dict):
                    price_str = values[0].get("key", values[0].get("value", ""))
                    try:
                        price = int(re.sub(r'[^\d]', '', str(price_str)))
                    except (ValueError, TypeError):
                        pass

        # Brand extraction from title
        brand = None
        title_upper = title.upper() if title else ""
        for b in PREMIUM_BRANDS + ["FIAT", "VOLKSWAGEN", "OPEL", "FORD", "PEUGEOT",
                                     "RENAULT", "CITROEN", "SEAT", "SKODA", "TOYOTA",
                                     "HYUNDAI", "KIA", "NISSAN", "SUZUKI", "DACIA"]:
            if b.upper() in title_upper:
                brand = b
                break

        # Seller info — Subito uses "advertiser" with company/shopId/shopName
        adv = item.get("advertiser", {})
        if not isinstance(adv, dict):
            adv = {}

        seller_id = str(adv.get("shopId", adv.get("userId", "")))
        seller_name = adv.get("shopName", adv.get("name", ""))
        is_company = adv.get("company", False)
        adv_type = adv.get("type", 0)
        seller_type = "professional" if (is_company or adv_type == 1 or adv.get("shopId")) else "private"

        # City from geo
        geo = item.get("geo", {})
        city = ""
        if isinstance(geo, dict):
            town = geo.get("town", {})
            if isinstance(town, dict):
                city = town.get("value", "")
            if not city:
                city_obj = geo.get("city", {})
                if isinstance(city_obj, dict):
                    city = city_obj.get("shortName", city_obj.get("value", ""))

        url = ""
        urls = item.get("urls", {})
        if isinstance(urls, dict):
            url = urls.get("default", "")

        listings.append(SubitoListing(
            listing_id=listing_id,
            title=title,
            price=price,
            brand=brand,
            city=city,
            province=province,
            seller_id=seller_id,
            seller_name=seller_name,
            seller_type=seller_type,
            url=url,
        ))

    return listings


# ── Aggregation ───────────────────────────────────────────────

def _aggregate_sellers(listings: List[SubitoListing], province: str, region: str) -> List[DiscoveredDealer]:
    """Aggregate listings by seller to build dealer profiles."""
    sellers: Dict[str, List[SubitoListing]] = defaultdict(list)

    for listing in listings:
        if listing.seller_type == "professional" and listing.seller_name:
            key = listing.seller_id or listing.seller_name
            sellers[key].append(listing)

    dealers = []
    for seller_key, seller_listings in sellers.items():
        name = seller_listings[0].seller_name
        city = seller_listings[0].city or ""
        seller_id = seller_listings[0].seller_id

        # Brand analysis
        brands = list(set(l.brand for l in seller_listings if l.brand))
        premium = [b for b in brands if b.upper() in [p.upper() for p in PREMIUM_BRANDS]]

        dealer = DiscoveredDealer(
            name=name,
            province=province,
            region=region,
            seller_id=seller_id,
            city=city,
            listing_count=len(seller_listings),
            brands=brands,
            brand_diversity=len(brands),
            premium_brands=premium,
            premium_pct=len(premium) / max(len(brands), 1),
        )
        dealers.append(dealer)

    return dealers


# ── Commission scoring ────────────────────────────────────────

def score_commission(dealer: DiscoveredDealer) -> float:
    """Score how likely a dealer works 'su commissione'. Higher = more likely."""
    score = 0.0
    cfg = COMMISSION_SCORING

    # Few listings (3-15) = strong signal
    if cfg["few_listings_min"] <= dealer.listing_count <= cfg["few_listings_max"]:
        score += cfg["few_listings_weight"]
    elif dealer.listing_count < cfg["few_listings_min"]:
        score += cfg["few_listings_weight"] * 0.5  # very few = maybe inactive
    # >15 listings = less likely commission, but not zero
    elif dealer.listing_count <= 25:
        score += cfg["few_listings_weight"] * 0.3

    # Brand diversity (>= 4 diverse brands = eterogeneo = commissione)
    if dealer.brand_diversity >= cfg["brand_diversity_min"]:
        score += cfg["brand_diversity_weight"]
    elif dealer.brand_diversity >= 3:
        score += cfg["brand_diversity_weight"] * 0.5

    # Commission keywords in matched_keywords
    if dealer.has_commission_keywords:
        score += cfg["keyword_match_weight"]

    # Premium presence (has at least 1 premium brand)
    if dealer.premium_brands:
        score += cfg["premium_presence_weight"]

    return round(score, 2)


def score_fit_argos(dealer: DiscoveredDealer) -> float:
    """Score overall fit for ARGOS targeting. Combines commission + premium + size."""
    score = dealer.commission_score

    # Premium percentage bonus
    if dealer.premium_pct >= 0.3:
        score += 2.0
    elif dealer.premium_pct >= 0.15:
        score += 1.0

    # Sweet spot: 5-20 listings
    if 5 <= dealer.listing_count <= 20:
        score += 1.0

    return round(score, 2)


# ── Main scraper ──────────────────────────────────────────────

def scrape_province(province: str, region: str, max_pages: int = 3) -> List[DiscoveredDealer]:
    """Scrape Subito.it for professional dealers in a province."""
    fetch = _get_fetcher()
    all_listings = []

    for page in range(1, max_pages + 1):
        # Build URL
        if page == 1:
            url = f"https://www.subito.it/annunci-{region}/vendita/auto/{province}/"
        else:
            url = f"https://www.subito.it/annunci-{region}/vendita/auto/{province}/?o={page}"

        logger.info(f"Scraping Subito.it: {province} page {page}")
        try:
            html = fetch(url)
            if not html:
                logger.warning(f"Empty response for {url}")
                break
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            break

        data = _extract_next_data(html)
        if not data:
            logger.warning(f"No __NEXT_DATA__ found for {url}")
            break

        listings = _extract_listings_from_next_data(data, province)
        logger.info(f"  Found {len(listings)} listings (page {page})")

        if not listings:
            break

        all_listings.extend(listings)
        _rate_limit()

    # Aggregate by seller
    dealers = _aggregate_sellers(all_listings, province, region)
    logger.info(f"  {len(dealers)} professional sellers found in {province}")

    # Score each dealer
    for dealer in dealers:
        dealer.commission_score = score_commission(dealer)
        dealer.fit_score = score_fit_argos(dealer)

    # Sort by fit_score descending
    dealers.sort(key=lambda d: d.fit_score, reverse=True)

    return dealers


def scrape_provinces(provinces: List[dict], max_pages: int = 3) -> List[DiscoveredDealer]:
    """Scrape multiple provinces."""
    all_dealers = []
    for prov in provinces:
        dealers = scrape_province(prov["province"], prov["region"], max_pages)
        all_dealers.extend(dealers)
        if prov != provinces[-1]:
            # Extra delay between provinces
            time.sleep(random.uniform(10, 20))
    return all_dealers


# ── Output ────────────────────────────────────────────────────

def print_results(dealers: List[DiscoveredDealer], top_n: int = 30):
    """Print dealer discovery results."""
    print(f"\n{'='*80}")
    print(f"ARGOS DEALER DISCOVERY — {len(dealers)} dealer trovati")
    print(f"{'='*80}\n")

    # Filter and show top results
    commission_dealers = [d for d in dealers if d.commission_score >= COMMISSION_SCORING["threshold_commission"]]
    fit_dealers = [d for d in dealers if d.fit_score >= COMMISSION_SCORING["threshold_fit_argos"]]

    print(f"Dealer con segnali 'su commissione': {len(commission_dealers)}")
    print(f"Dealer con fit ARGOS alto:           {len(fit_dealers)}")
    print()

    for i, d in enumerate(dealers[:top_n], 1):
        comm_tag = " [COMMISSIONE]" if d.commission_score >= COMMISSION_SCORING["threshold_commission"] else ""
        fit_tag = " [FIT ARGOS]" if d.fit_score >= COMMISSION_SCORING["threshold_fit_argos"] else ""
        premium_str = ", ".join(d.premium_brands) if d.premium_brands else "none"

        print(f"#{i:2d} {d.name:<35s} {d.city}, {d.province.upper()}")
        print(f"    Annunci: {d.listing_count:3d} | Marche: {d.brand_diversity} | Premium: {premium_str}")
        print(f"    Commission: {d.commission_score:.1f} | Fit: {d.fit_score:.1f}{comm_tag}{fit_tag}")
        print()


def export_json(dealers: List[DiscoveredDealer], output_path: str):
    """Export results to JSON."""
    data = [asdict(d) for d in dealers]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Exported {len(dealers)} dealers to {output_path}")


# ── CLI ───────────────────────────────────────────────────────

def main():
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    parser = argparse.ArgumentParser(description="ARGOS Dealer Discovery — Subito.it")
    parser.add_argument("--province", type=str, help="Comma-separated provinces (e.g., foggia,cosenza)")
    parser.add_argument("--all-priority", type=int, help="Scrape all provinces with this priority or higher")
    parser.add_argument("--pages", type=int, default=3, help="Max pages per province (default: 3)")
    parser.add_argument("--output", type=str, help="Export JSON to file")
    parser.add_argument("--top", type=int, default=30, help="Show top N results")

    args = parser.parse_args()

    if args.province:
        province_names = [p.strip().lower() for p in args.province.split(",")]
        provinces = [p for p in PROVINCE_TARGET if p["province"] in province_names]
        if not provinces:
            print(f"Province non trovate: {province_names}")
            print(f"Disponibili: {[p['province'] for p in PROVINCE_TARGET]}")
            sys.exit(1)
    elif args.all_priority:
        provinces = [p for p in PROVINCE_TARGET if p["priority"] <= args.all_priority]
    else:
        # Default: priority 1
        provinces = [p for p in PROVINCE_TARGET if p["priority"] == 1]

    print(f"Province da scrappare: {[p['province'] for p in provinces]}")
    dealers = scrape_provinces(provinces, max_pages=args.pages)

    print_results(dealers, top_n=args.top)

    if args.output:
        export_json(dealers, args.output)

    # Summary
    commission = [d for d in dealers if d.commission_score >= COMMISSION_SCORING["threshold_commission"]]
    fit = [d for d in dealers if d.fit_score >= COMMISSION_SCORING["threshold_fit_argos"]]
    print(f"\n{'='*80}")
    print(f"RIEPILOGO: {len(dealers)} dealer | {len(commission)} commissione | {len(fit)} fit ARGOS")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
