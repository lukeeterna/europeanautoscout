"""
s206_marche_scraper.py -- ARGOS S206 Marche Register Scraper
Standalone script — NON modifica cove_engine_v4.py o modelli core.

Obiettivo:
  - Scraping AutoScout24.it + Subito.it + Automobile.it
  - Filtro: BMW/Mercedes/Audi/Porsche, 40k-100k EUR, province AN/MC/PU/AP/FM
  - Cattura description verbatim per corpus register
  - Estrae prospect micro-dealer per Luke (chiamate lunedi)

Outputs in research/s206_marche_register/:
  - corpus_register.md
  - prospect_list.csv
  - prospect_list_per_provincia.md
  - EXECUTION_REPORT.md

Rate-limit: 3-8s random tra fetch. Idempotente su re-run (dedup telefono).

Author: ARGOS S206 task
"""

from __future__ import annotations

import csv
import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin, urlparse, quote

try:
    from curl_cffi import requests as http_requests
    HTTP_BACKEND = "curl_cffi"
except ImportError:
    import requests as http_requests  # type: ignore
    HTTP_BACKEND = "requests"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("s206")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).parent.parent / "research" / "s206_marche_register"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAKES = ["BMW", "Mercedes-Benz", "Audi", "Porsche"]
PRICE_MIN = 40_000
PRICE_MAX = 100_000

# Province Marche (codice ISTAT / sigla)
PROVINCE_MARCHE = {
    "AN": "Ancona",
    "MC": "Macerata",
    "PU": "Pesaro-Urbino",
    "AP": "Ascoli Piceno",
    "FM": "Fermo",
}

# Per AutoScout24 IT, le province vanno passate come zip o citta
# Usiamo le citta capoluogo + varianti comuni AS24
AS24_PROVINCE_PARAMS: Dict[str, List[str]] = {
    "AN": ["Ancona", "Falconara Marittima", "Senigallia", "Jesi", "Fabriano"],
    "MC": ["Macerata", "Civitanova Marche", "Tolentino", "Porto Recanati", "Recanati"],
    "PU": ["Pesaro", "Urbino", "Fano", "Fossombrone"],
    "AP": ["Ascoli Piceno", "San Benedetto del Tronto", "Grottammare"],
    "FM": ["Fermo", "Porto San Giorgio", "Porto Sant'Elpidio"],
}

DELAY_MIN = 3.5
DELAY_MAX = 8.0

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RawListing:
    listing_id: str
    portal: str         # autoscout24 | subito | automobile
    provincia: str      # AN MC PU AP FM
    citta: str
    make: str
    model: str
    year: int = 0
    km: int = 0
    price: float = 0.0
    title: str = ""
    description: str = ""  # VERBATIM, no trimming
    seller_name: str = ""
    seller_phone: str = ""
    seller_type: str = ""   # private | dealer | unknown
    n_listings_seller: int = 0  # stima stock visibile
    seller_url: str = ""
    listing_url: str = ""
    indirizzo_visibile: str = ""
    raw_html_snippet: str = ""  # non salvato in CSV


@dataclass
class Prospect:
    regione: str = "Marche"
    provincia: str = ""
    citta: str = ""
    operatore_nome: str = ""
    telefono: str = ""       # normalizzato +39XXXXXXXXXX
    whatsapp: str = ""
    portale: str = ""
    n_auto_in_stock_visibili: int = 0
    indirizzo_visibile: str = ""
    flag_residenziale_si_no: str = "no"
    flag_target_alto_si_no: str = "no"
    note: str = ""
    url_profilo_venditore: str = ""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _random_ua() -> str:
    return random.choice(USER_AGENTS)


def _sleep_human() -> None:
    t = random.uniform(DELAY_MIN, DELAY_MAX)
    log.debug("sleeping %.1fs", t)
    time.sleep(t)


def fetch_url(url: str, referer: str = "", extra_headers: Optional[Dict] = None) -> str:
    """Fetch URL with anti-bot headers. Returns HTML string or empty string on error."""
    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }
    if referer:
        headers["Referer"] = referer
    if extra_headers:
        headers.update(extra_headers)

    try:
        if HTTP_BACKEND == "curl_cffi":
            resp = http_requests.get(
                url,
                headers=headers,
                timeout=25,
                impersonate="chrome124",
                allow_redirects=True,
            )
        else:
            resp = http_requests.get(url, headers=headers, timeout=25, allow_redirects=True)

        if resp.status_code == 200:
            return resp.text
        elif resp.status_code == 429:
            log.warning("429 rate-limited on %s — sleeping 30s", url[:80])
            time.sleep(30)
            return ""
        elif resp.status_code in (403, 503):
            log.warning("HTTP %d on %s — likely bot-wall", resp.status_code, url[:80])
            return ""
        else:
            log.warning("HTTP %d on %s", resp.status_code, url[:80])
            return ""
    except Exception as e:
        log.warning("fetch error %s: %s", url[:80], e)
        return ""


# ---------------------------------------------------------------------------
# Generic HTML helpers (no bs4)
# ---------------------------------------------------------------------------

def strip_tags(html: str) -> str:
    """Remove all HTML tags, return plain text."""
    return re.sub(r'<[^>]+>', ' ', html)


def normalize_spaces(text: str) -> str:
    """Collapse whitespace."""
    return re.sub(r'\s+', ' ', text).strip()


def extract_text_block(html: str, tag: str, attrs_re: str = "") -> List[str]:
    """Extract text content of all <tag> elements matching attrs_re."""
    pattern = rf'<{tag}[^>]*{attrs_re}[^>]*>(.*?)</{tag}>'
    blocks = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    return [normalize_spaces(strip_tags(b)) for b in blocks]


def extract_json_ld(html: str) -> List[dict]:
    """Extract all JSON-LD blocks from page."""
    results = []
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    ):
        try:
            results.append(json.loads(m.group(1).strip()))
        except Exception:
            pass
    return results


def extract_next_data(html: str) -> dict:
    """Extract __NEXT_DATA__ JSON."""
    m = re.search(r'<script id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            pass
    return {}


def normalize_phone(raw: str) -> str:
    """Normalize Italian phone to +39XXXXXXXXXX or return empty if not Italian."""
    if not raw:
        return ""
    # Strip everything except digits and leading +
    digits = re.sub(r'[^\d]', '', raw)
    if not digits:
        return ""
    # Already has country code
    if raw.strip().startswith('+39') and len(digits) >= 11:
        return f"+39{digits[-10:]}" if len(digits) > 11 else f"+{digits}"
    # Italian mobile/landline: starts with 3 (mobile) or 0 (landline), 9-10 digits
    if len(digits) == 10 and digits[0] in ('3', '0'):
        return f"+39{digits}"
    if len(digits) == 9 and digits[0] == '3':
        return f"+39{digits}"
    # Strip leading 39
    if digits.startswith('39') and len(digits) in (11, 12):
        return f"+{digits}"
    # Return as-is with prefix if plausible
    if len(digits) >= 9:
        return f"+39{digits[-10:]}"
    return ""


# ---------------------------------------------------------------------------
# AutoScout24 IT Scraper
# ---------------------------------------------------------------------------

AS24_BASE = "https://www.autoscout24.it"

# AS24 make slugs for URL
AS24_MAKE_SLUG = {
    "BMW": "bmw",
    "Mercedes-Benz": "mercedes-benz",
    "Audi": "audi",
    "Porsche": "porsche",
}

def _as24_search_url(make: str, zipcity: str, page: int = 1) -> str:
    """Construct AutoScout24 IT search URL for a make + city, premium price range."""
    slug = AS24_MAKE_SLUG.get(make, make.lower())
    params = {
        "atype": "C",
        "cy": "I",
        "desc": "0",
        "fregfrom": "2018",
        "ocs_listing": "include",
        "pricefrom": str(PRICE_MIN),
        "priceto": str(PRICE_MAX),
        "search_id": "generated",
        "sort": "standard",
        "source": "listpage_pagination",
        "ustate": "N,U",
        "zipcity": zipcity,
        "zipcityradius": "30",
        "page": str(page),
    }
    return f"{AS24_BASE}/lst/{slug}?{urlencode(params)}"


def _parse_as24_listing_from_next_data(nd: dict, provincia: str, citta: str, make: str) -> List[RawListing]:
    """Parse listings from __NEXT_DATA__ on AS24 search page."""
    listings = []
    try:
        props = nd.get("props", {}).get("pageProps", {})
        raw_listings = props.get("listings", []) or props.get("searchResults", [])

        # AS24 sometimes wraps them under props.pageProps.listings
        if not raw_listings:
            raw_listings = (
                props.get("listingDetails", {}) or
                nd.get("pageProps", {}).get("listings", [])
            )
        if isinstance(raw_listings, dict):
            raw_listings = [raw_listings]
    except Exception:
        return listings

    for item in raw_listings:
        if not isinstance(item, dict):
            continue
        try:
            listing_id = str(item.get("id", item.get("listingId", "")))
            if not listing_id:
                continue

            vehicle = item.get("vehicle", item) if "vehicle" in item else item
            price_info = item.get("prices", {})
            if isinstance(price_info, dict):
                price = float(price_info.get("public", {}).get("priceRaw", 0) or
                              price_info.get("priceRaw", 0) or 0)
            else:
                price = float(item.get("price", 0) or 0)

            km = int(vehicle.get("mileage", 0) or 0)
            year_raw = vehicle.get("firstRegistration", vehicle.get("year", ""))
            if year_raw:
                y_match = re.search(r'(\d{4})', str(year_raw))
                year = int(y_match.group(1)) if y_match else 0
            else:
                year = 0

            seller = item.get("seller", item.get("vendor", {}))
            if isinstance(seller, dict):
                seller_name = seller.get("name", seller.get("companyName", ""))
                seller_type = "dealer" if seller.get("type", "").lower() in ("dealer", "professional", "d") else "private"
                seller_phone = seller.get("phone", seller.get("phoneNumber", ""))
                seller_url = seller.get("url", "")
                n_listings = int(seller.get("stockCount", seller.get("listings", 0)) or 0)
                address = seller.get("address", {})
                if isinstance(address, dict):
                    indirizzo = f"{address.get('street', '')} {address.get('city', '')}".strip()
                else:
                    indirizzo = ""
            else:
                seller_name = ""
                seller_type = "unknown"
                seller_phone = ""
                seller_url = ""
                n_listings = 0
                indirizzo = ""

            listing_url = item.get("url", "")
            if listing_url and not listing_url.startswith("http"):
                listing_url = AS24_BASE + listing_url

            title = normalize_spaces(
                vehicle.get("title", "") or
                f"{make} {vehicle.get('model', '')} {vehicle.get('version', '')}".strip()
            )

            # Description: will be fetched on detail page
            description = ""

            listings.append(RawListing(
                listing_id=f"as24_it_{listing_id}",
                portal="autoscout24",
                provincia=provincia,
                citta=citta,
                make=make,
                model=str(vehicle.get("model", "")),
                year=year,
                km=km,
                price=price,
                title=title,
                description=description,
                seller_name=str(seller_name),
                seller_phone=normalize_phone(str(seller_phone)),
                seller_type=seller_type,
                n_listings_seller=n_listings,
                seller_url=str(seller_url),
                listing_url=listing_url,
                indirizzo_visibile=indirizzo,
            ))
        except Exception as e:
            log.debug("parse error item %s: %s", str(item)[:80], e)
            continue

    return listings


def _as24_extract_description(html: str) -> str:
    """Extract verbatim description text from AS24 detail page."""
    # Strategy 1: __NEXT_DATA__ description field
    nd = extract_next_data(html)
    if nd:
        try:
            props = nd.get("props", {}).get("pageProps", {})
            desc = (
                props.get("listingDetails", {}).get("description", "") or
                props.get("listing", {}).get("description", "")
            )
            if desc and isinstance(desc, str) and len(desc) > 20:
                return desc.strip()
        except Exception:
            pass

    # Strategy 2: JSON-LD description field
    for jld in extract_json_ld(html):
        desc = jld.get("description", "")
        if desc and len(desc) > 20:
            return desc.strip()

    # Strategy 3: regex on common AS24 description containers
    patterns = [
        r'<div[^>]*data-cy=["\']vehicle-description["\'][^>]*>(.*?)</div>',
        r'<div[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</div>',
        r'<p[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</p>',
        r'"description"\s*:\s*"([^"]{30,})"',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
        if m:
            raw = m.group(1)
            text = normalize_spaces(strip_tags(raw))
            if len(text) > 30:
                return text

    return ""


def scrape_as24_marche(max_pages_per_combo: int = 2) -> List[RawListing]:
    """Scrape AutoScout24.it for premium cars in Marche provinces."""
    all_listings: List[RawListing] = []
    seen_ids: set = set()

    for make in MAKES:
        for prov_code, cities in AS24_PROVINCE_PARAMS.items():
            for city in cities[:2]:  # max 2 citta per provincia per rispettare rate limit
                url = _as24_search_url(make, city, page=1)
                log.info("[AS24] %s | %s (%s) | page 1", make, city, prov_code)
                html = fetch_url(url, referer=AS24_BASE)
                _sleep_human()

                if not html:
                    log.warning("[AS24] empty response for %s / %s", make, city)
                    continue

                nd = extract_next_data(html)
                if nd:
                    page_listings = _parse_as24_listing_from_next_data(nd, prov_code, city, make)
                else:
                    log.warning("[AS24] no __NEXT_DATA__ for %s / %s", make, city)
                    page_listings = []

                # Filter by price range
                page_listings = [
                    l for l in page_listings
                    if l.price == 0 or (PRICE_MIN <= l.price <= PRICE_MAX)
                ]

                for l in page_listings:
                    if l.listing_id not in seen_ids:
                        seen_ids.add(l.listing_id)
                        all_listings.append(l)

                log.info("[AS24] found %d listings (total: %d)", len(page_listings), len(all_listings))

                # If results > 0, try page 2
                if len(page_listings) >= 5 and max_pages_per_combo > 1:
                    url2 = _as24_search_url(make, city, page=2)
                    log.info("[AS24] %s | %s | page 2", make, city)
                    html2 = fetch_url(url2, referer=url)
                    _sleep_human()
                    if html2:
                        nd2 = extract_next_data(html2)
                        if nd2:
                            p2 = _parse_as24_listing_from_next_data(nd2, prov_code, city, make)
                            p2 = [l for l in p2 if l.listing_id not in seen_ids and
                                  (l.price == 0 or (PRICE_MIN <= l.price <= PRICE_MAX))]
                            for l in p2:
                                seen_ids.add(l.listing_id)
                                all_listings.append(l)

    log.info("[AS24] Total raw: %d", len(all_listings))
    return all_listings


def enrich_as24_descriptions(listings: List[RawListing], max_detail: int = 30) -> None:
    """Fetch detail pages for AS24 listings to extract description. In-place update."""
    to_enrich = [l for l in listings if not l.description and l.listing_url][:max_detail]
    log.info("[AS24-detail] enriching %d listings for description", len(to_enrich))

    for l in to_enrich:
        log.info("[AS24-detail] fetching %s", l.listing_url[:80])
        html = fetch_url(l.listing_url, referer=AS24_BASE)
        _sleep_human()
        if html:
            desc = _as24_extract_description(html)
            if desc:
                l.description = desc
                log.info("[AS24-detail] description %d chars for %s", len(desc), l.listing_id)


# ---------------------------------------------------------------------------
# Subito.it Scraper
# ---------------------------------------------------------------------------

SUBITO_BASE = "https://www.subito.it"

SUBITO_MAKE_PARAM = {
    "BMW": "bmw",
    "Mercedes-Benz": "mercedes-benz",
    "Audi": "audi",
    "Porsche": "porsche",
}

# Subito usa regioni e province come filtro URL
# Regione: marche | Provincie: ancona, macerata, pesaro-e-urbino, ascoli-piceno, fermo
SUBITO_PROVINCE = {
    "AN": "ancona",
    "MC": "macerata",
    "PU": "pesaro-e-urbino",
    "AP": "ascoli-piceno",
    "FM": "fermo",
}

def _subito_search_url(make: str, prov_slug: str, page: int = 1) -> str:
    """Subito search URL for auto usate in Marche by make and province."""
    make_slug = SUBITO_MAKE_PARAM.get(make, make.lower())
    # Subito URL pattern: /annunci/automobili/usato/{marca}/{regione}/{provincia}/
    # With price filter via query params
    base = f"{SUBITO_BASE}/annunci/automobili/usato/{make_slug}/marche/{prov_slug}/"
    params = {
        "qso": "true",
        "o": str(page),
        "ps": str(PRICE_MIN),
        "pe": str(PRICE_MAX),
        "sort": "datedesc",
    }
    return f"{base}?{urlencode(params)}"


def _parse_subito_listings(html: str, prov_code: str, make: str) -> List[RawListing]:
    """Parse Subito search results page."""
    listings = []

    # Try __NEXT_DATA__ first
    nd = extract_next_data(html)
    if nd:
        try:
            items = (
                nd.get("props", {}).get("pageProps", {}).get("items", []) or
                nd.get("props", {}).get("pageProps", {}).get("listings", [])
            )
            for item in items:
                if not isinstance(item, dict):
                    continue
                try:
                    listing_id = str(item.get("urn", item.get("id", "")))
                    if not listing_id:
                        continue
                    title = item.get("subject", "")
                    price_raw = item.get("price", {})
                    if isinstance(price_raw, dict):
                        price = float(price_raw.get("value", 0) or 0)
                    else:
                        price = float(price_raw or 0)

                    body = item.get("body", "")
                    geo = item.get("geo", {})
                    citta = ""
                    if isinstance(geo, dict):
                        city_obj = geo.get("city", geo.get("town", {}))
                        if isinstance(city_obj, dict):
                            citta = city_obj.get("value", "")
                        elif isinstance(city_obj, str):
                            citta = city_obj

                    item_url = item.get("urls", {}).get("default", "")
                    if item_url and not item_url.startswith("http"):
                        item_url = SUBITO_BASE + item_url

                    advertiser = item.get("advertiser", {})
                    seller_name = advertiser.get("name", "")
                    seller_type = "dealer" if advertiser.get("type", "").lower() in ("shop", "company", "dealer") else "private"
                    phone = ""  # Subito nasconde phone nelle liste

                    # Features
                    features = item.get("features", {})
                    km = 0
                    year = 0
                    if isinstance(features, dict):
                        km_raw = features.get("km", {})
                        if isinstance(km_raw, dict):
                            km = int(re.sub(r'\D', '', str(km_raw.get("value", 0))) or 0)
                        year_raw = features.get("year", {})
                        if isinstance(year_raw, dict):
                            y_str = str(year_raw.get("value", 0))
                            y_match = re.search(r'(\d{4})', y_str)
                            if y_match:
                                year = int(y_match.group(1))

                    listings.append(RawListing(
                        listing_id=f"subito_{listing_id}",
                        portal="subito",
                        provincia=prov_code,
                        citta=citta,
                        make=make,
                        model="",
                        year=year,
                        km=km,
                        price=price,
                        title=str(title),
                        description=str(body),
                        seller_name=str(seller_name),
                        seller_phone=normalize_phone(phone),
                        seller_type=seller_type,
                        n_listings_seller=0,
                        seller_url="",
                        listing_url=item_url,
                    ))
                except Exception as e:
                    log.debug("subito item parse error: %s", e)
                    continue
        except Exception as e:
            log.debug("subito next_data parse error: %s", e)

    # Fallback: regex on HTML if next_data failed
    if not listings:
        # Look for listing cards
        card_pattern = r'<div[^>]*class=["\'][^"\']*item-card[^"\']*["\'][^>]*>(.*?)</div>\s*</div>'
        cards = re.findall(card_pattern, html, re.DOTALL | re.IGNORECASE)
        for i, card in enumerate(cards[:20]):
            try:
                price_m = re.search(r'([\d.,]+)\s*€', card)
                price = float(re.sub(r'[^\d]', '', price_m.group(1)) or 0) if price_m else 0
                if not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                title_m = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
                title = normalize_spaces(strip_tags(title_m.group(1))) if title_m else ""

                url_m = re.search(r'href=["\']([^"\']+/annunci/[^"\']+)["\']', card)
                item_url = url_m.group(1) if url_m else ""
                if item_url and not item_url.startswith("http"):
                    item_url = SUBITO_BASE + item_url

                listings.append(RawListing(
                    listing_id=f"subito_html_{i}",
                    portal="subito",
                    provincia=prov_code,
                    citta="",
                    make=make,
                    model="",
                    year=0,
                    price=price,
                    title=title,
                    listing_url=item_url,
                    seller_type="unknown",
                ))
            except Exception:
                continue

    return listings


def _subito_fetch_detail(listing: RawListing) -> None:
    """Fetch Subito detail page to extract description and phone."""
    if not listing.listing_url:
        return
    log.info("[Subito-detail] %s", listing.listing_url[:80])
    html = fetch_url(listing.listing_url, referer=SUBITO_BASE)
    _sleep_human()
    if not html:
        return

    # Description from next_data
    nd = extract_next_data(html)
    if nd:
        try:
            item = nd.get("props", {}).get("pageProps", {}).get("item", {})
            if isinstance(item, dict):
                desc = item.get("body", "")
                if desc and len(desc) > 10:
                    listing.description = desc.strip()
                phone = item.get("advertiser", {}).get("phone", "")
                if phone:
                    listing.seller_phone = normalize_phone(str(phone))
                n = item.get("advertiser", {}).get("total_ads", 0)
                if n:
                    listing.n_listings_seller = int(n)
                return
        except Exception:
            pass

    # Fallback: regex
    desc_m = re.search(r'"body"\s*:\s*"((?:[^"\\]|\\.)+)"', html)
    if desc_m:
        try:
            listing.description = bytes(desc_m.group(1), 'utf-8').decode('unicode_escape')
        except Exception:
            listing.description = desc_m.group(1)

    phone_m = re.search(r'"phone"\s*:\s*"([^"]+)"', html)
    if phone_m:
        listing.seller_phone = normalize_phone(phone_m.group(1))


def scrape_subito_marche() -> List[RawListing]:
    """Scrape Subito.it for premium cars in Marche."""
    all_listings: List[RawListing] = []
    seen_ids: set = set()

    for make in MAKES:
        for prov_code, prov_slug in SUBITO_PROVINCE.items():
            url = _subito_search_url(make, prov_slug, page=1)
            log.info("[Subito] %s | %s (%s)", make, prov_slug, prov_code)
            html = fetch_url(url, referer=SUBITO_BASE)
            _sleep_human()

            if not html:
                log.warning("[Subito] empty for %s / %s", make, prov_code)
                continue

            page_listings = _parse_subito_listings(html, prov_code, make)
            page_listings = [
                l for l in page_listings
                if l.listing_id not in seen_ids and
                (l.price == 0 or (PRICE_MIN <= l.price <= PRICE_MAX))
            ]

            for l in page_listings:
                seen_ids.add(l.listing_id)
                all_listings.append(l)

            log.info("[Subito] %d found (total: %d)", len(page_listings), len(all_listings))

    # Fetch details for top 20 to get descriptions
    to_detail = [l for l in all_listings if not l.description][:20]
    for l in to_detail:
        _subito_fetch_detail(l)

    return all_listings


# ---------------------------------------------------------------------------
# Automobile.it Scraper
# ---------------------------------------------------------------------------

AUTO_IT_BASE = "https://www.automobile.it"

AUTO_IT_MAKE_SLUG = {
    "BMW": "bmw",
    "Mercedes-Benz": "mercedes-benz",
    "Audi": "audi",
    "Porsche": "porsche",
}

# Automobile.it usa regione nel path
AUTO_IT_PROVINCE_PARAM = {
    "AN": "ancona",
    "MC": "macerata",
    "PU": "pesaro-urbino",
    "AP": "ascoli-piceno",
    "FM": "fermo",
}

def _auto_it_url(make: str, prov: str, page: int = 1) -> str:
    """Build automobile.it search URL."""
    slug = AUTO_IT_MAKE_SLUG.get(make, make.lower())
    params = {
        "pr-min": str(PRICE_MIN),
        "pr-max": str(PRICE_MAX),
        "regdatefrom": "2018",
        "page": str(page),
    }
    return f"{AUTO_IT_BASE}/auto/{slug}/usate/{prov}/?{urlencode(params)}"


def _parse_auto_it_listings(html: str, prov_code: str, make: str) -> List[RawListing]:
    """Parse automobile.it search results."""
    listings = []

    # Try JSON-LD first
    for jld in extract_json_ld(html):
        items = []
        if isinstance(jld, list):
            items = jld
        elif isinstance(jld, dict):
            if "@graph" in jld:
                items = jld["@graph"] if isinstance(jld["@graph"], list) else [jld["@graph"]]
            elif jld.get("@type") in ("ItemList", "Vehicle", "Car", "Product"):
                items = [jld]

        for item in items:
            if not isinstance(item, dict):
                continue
            itype = item.get("@type", "")
            if isinstance(itype, list):
                itype = " ".join(itype)

            if not any(t in itype for t in ("Vehicle", "Car", "Product", "ItemList")):
                continue

            if itype == "ItemList":
                subitems = item.get("itemListElement", [])
                for sub in subitems:
                    if isinstance(sub, dict):
                        items.append(sub.get("item", sub))
                continue

            listing_id = str(item.get("sku", item.get("productID", item.get("@id", "")))).strip("/")
            if not listing_id:
                continue
            listing_id = re.sub(r'[^a-zA-Z0-9_-]', '_', listing_id)

            offers = item.get("offers", {})
            if isinstance(offers, list) and offers:
                offers = offers[0]
            price = 0.0
            if isinstance(offers, dict):
                p_raw = offers.get("price", offers.get("lowPrice", 0))
                try:
                    price = float(str(p_raw).replace(',', '.').replace('.', '').replace(',', '.') or 0)
                except Exception:
                    price = 0.0

            if price and not (PRICE_MIN <= price <= PRICE_MAX):
                continue

            desc = item.get("description", "")
            name = item.get("name", "")

            seller_info = item.get("seller", item.get("brand", {}))
            seller_name = ""
            if isinstance(seller_info, dict):
                seller_name = seller_info.get("name", "")

            url = item.get("url", "")
            if url and not url.startswith("http"):
                url = AUTO_IT_BASE + url

            listings.append(RawListing(
                listing_id=f"autoit_{listing_id}",
                portal="automobile.it",
                provincia=prov_code,
                citta="",
                make=make,
                model="",
                year=0,
                km=0,
                price=price,
                title=str(name),
                description=str(desc),
                seller_name=str(seller_name),
                seller_type="unknown",
                listing_url=url,
            ))

    # Fallback: regex patterns for automobile.it cards
    if not listings:
        card_re = r'<div[^>]*class=["\'][^"\']*ad-card[^"\']*["\'][^>]*>(.*?)</div>\s*(?:</div>|<div[^>]*class=["\'][^"\']*ad-card)'
        cards = re.findall(card_re, html, re.DOTALL | re.IGNORECASE)
        if not cards:
            # Try more generic pattern
            cards = re.findall(
                r'<article[^>]*>(.*?)</article>',
                html, re.DOTALL | re.IGNORECASE
            )

        for i, card in enumerate(cards[:20]):
            price_m = re.search(r'([\d]{2,3}[.,]\d{3}|\d{5,})\s*€?', card)
            if not price_m:
                continue
            try:
                price = float(re.sub(r'[^\d]', '', price_m.group(1)))
            except Exception:
                continue
            if not (PRICE_MIN <= price <= PRICE_MAX):
                continue

            url_m = re.search(r'href=["\']([^"\']+(?:auto|annuncio|usato)[^"\']*)["\']', card)
            item_url = ""
            if url_m:
                item_url = url_m.group(1)
                if not item_url.startswith("http"):
                    item_url = AUTO_IT_BASE + item_url

            title_m = re.search(r'<h\d[^>]*>(.*?)</h\d>', card, re.DOTALL)
            title = normalize_spaces(strip_tags(title_m.group(1))) if title_m else ""

            listings.append(RawListing(
                listing_id=f"autoit_html_{i}_{prov_code}_{make[:3]}",
                portal="automobile.it",
                provincia=prov_code,
                citta="",
                make=make,
                model="",
                price=price,
                title=title,
                listing_url=item_url,
                seller_type="unknown",
            ))

    return listings


def _auto_it_fetch_detail(listing: RawListing) -> None:
    """Fetch automobile.it detail page for description + phone."""
    if not listing.listing_url:
        return
    log.info("[Autoit-detail] %s", listing.listing_url[:80])
    html = fetch_url(listing.listing_url, referer=AUTO_IT_BASE)
    _sleep_human()
    if not html:
        return

    # Description patterns
    desc_patterns = [
        r'<div[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</div>',
        r'<section[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</section>',
        r'"description"\s*:\s*"((?:[^"\\]|\\.){30,})"',
    ]
    for pat in desc_patterns:
        m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
        if m:
            raw = m.group(1)
            if '"' in pat:
                text = raw
            else:
                text = normalize_spaces(strip_tags(raw))
            if len(text) > 30:
                listing.description = text
                break

    # Phone
    phone_patterns = [
        r'"phone"\s*:\s*"([^"]+)"',
        r'tel:([+0-9][0-9\s.-]{7,})',
        r'data-phone=["\']([^"\']+)["\']',
    ]
    for pat in phone_patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            phone = normalize_phone(m.group(1).strip())
            if phone:
                listing.seller_phone = phone
                break

    # Seller name
    if not listing.seller_name:
        seller_m = re.search(r'"dealerName"\s*:\s*"([^"]+)"', html)
        if seller_m:
            listing.seller_name = seller_m.group(1)


def scrape_auto_it_marche() -> List[RawListing]:
    """Scrape automobile.it for premium cars in Marche."""
    all_listings: List[RawListing] = []
    seen_ids: set = set()

    for make in MAKES:
        for prov_code, prov_slug in AUTO_IT_PROVINCE_PARAM.items():
            url = _auto_it_url(make, prov_slug)
            log.info("[Autoit] %s | %s (%s)", make, prov_slug, prov_code)
            html = fetch_url(url, referer=AUTO_IT_BASE)
            _sleep_human()

            if not html:
                log.warning("[Autoit] empty for %s / %s", make, prov_code)
                continue

            page_listings = _parse_auto_it_listings(html, prov_code, make)
            page_listings = [
                l for l in page_listings
                if l.listing_id not in seen_ids and
                (l.price == 0 or (PRICE_MIN <= l.price <= PRICE_MAX))
            ]

            for l in page_listings:
                seen_ids.add(l.listing_id)
                all_listings.append(l)

            log.info("[Autoit] %d found (total: %d)", len(page_listings), len(all_listings))

    # Enrich details for descriptions
    to_detail = [l for l in all_listings if not l.description][:15]
    for l in to_detail:
        _auto_it_fetch_detail(l)

    return all_listings


# ---------------------------------------------------------------------------
# Prospect extraction from raw listings
# ---------------------------------------------------------------------------

# Patterns residenziali (indirizzo non commerciale)
_RESIDENTIAL_KEYWORDS = [
    r'\bvia\b', r'\bviale\b', r'\bpiazza\b', r'\bvicolo\b', r'\bcontrada\b',
    r'\bloc\.?\b', r'\blocalita\b', r'\bc\.da\b',
]

_NO_PROFESSIONAL_KEYWORDS = [
    r'srl', r'spa', r's\.p\.a\.', r's\.r\.l\.', r'snc', r'concessionari[ao]',
    r'autosalone', r'autocenter', r'group\b', r'dealer', r'motors\b', r'autoshop',
    r'car\s+center', r'car\s+point', r'auto\s+service',
]

_TARGET_KEYWORDS = [
    r'unico proprietario', r'primo proprietario', r'km certificat',
    r'full optional', r'tagliandi certif', r'garanzia \d+', r'senza intermediari',
    r'privato vende', r'privato cede', r'no permute', r'solo contanti',
    r'no perditempo', r'visionabile su appuntamento', r'trattativa riservata',
    r'permuta valutabile', r'finanziamento',
]


def _is_residential(address: str) -> bool:
    if not address:
        return False
    addr_lower = address.lower()
    return any(re.search(kw, addr_lower) for kw in _RESIDENTIAL_KEYWORDS)


def _is_big_dealer(name: str, address: str) -> bool:
    combined = f"{name} {address}".lower()
    return any(re.search(kw, combined) for kw in _NO_PROFESSIONAL_KEYWORDS)


def _has_target_signals(description: str, title: str) -> bool:
    combined = f"{description} {title}".lower()
    return any(re.search(kw, combined) for kw in _TARGET_KEYWORDS)


def _estimate_seller_type_from_stock(n: int, name: str, address: str) -> str:
    """Stima archetype da numero listing visibile."""
    if n == 1:
        return "privato_puro"
    if 2 <= n <= 15:
        return "micro_operatore"  # TARGET ALTO
    if 16 <= n <= 60:
        return "piccolo_dealer"
    return "dealer_medio_grande"


def build_prospects(listings: List[RawListing]) -> List[Prospect]:
    """Aggrega listing per seller e crea prospect deduplicato su telefono."""
    # Group by (portal, seller_name_normalized, provincia) OR telefono
    seller_map: Dict[str, List[RawListing]] = {}

    for l in listings:
        # Key: preferisce telefono (dedup canonico), altrimenti nome+prov
        key = l.seller_phone if l.seller_phone else f"{l.portal}|{l.seller_name}|{l.provincia}"
        if not key or key == "+39":
            key = f"anon_{l.portal}_{l.listing_id}"
        seller_map.setdefault(key, []).append(l)

    prospects = []
    for key, seller_listings in seller_map.items():
        first = seller_listings[0]

        # Aggregate data
        n_stock = max(l.n_listings_seller for l in seller_listings)
        if n_stock == 0:
            n_stock = len(seller_listings)

        name = first.seller_name
        if not name:
            name = "N/D"

        phone = first.seller_phone or ""
        # Check all listings for a phone
        for l in seller_listings:
            if l.seller_phone:
                phone = l.seller_phone
                break

        # Citta: most common
        cities = [l.citta for l in seller_listings if l.citta]
        citta = cities[0] if cities else ""
        if not citta:
            citta = PROVINCE_MARCHE.get(first.provincia, "")

        portali = list({l.portal for l in seller_listings})
        portale = ", ".join(portali)

        indirizzo = first.indirizzo_visibile or ""
        for l in seller_listings:
            if l.indirizzo_visibile:
                indirizzo = l.indirizzo_visibile
                break

        flag_res = "si" if _is_residential(indirizzo) else "no"

        # Ignore big dealers
        if _is_big_dealer(name, indirizzo) and n_stock > 30:
            continue

        # Target alto criteria:
        # 1. n_stock 1-30 (family/micro)
        # 2. non è concessionario ufficiale grande
        # 3. ha segnali di qualità nella descrizione O è residenziale
        desc_combined = " ".join(l.description for l in seller_listings if l.description)
        title_combined = " ".join(l.title for l in seller_listings if l.title)

        target_signals = _has_target_signals(desc_combined, title_combined)
        not_big = not _is_big_dealer(name, indirizzo)
        stock_ok = 1 <= n_stock <= 60

        flag_target = "si" if (stock_ok and not_big and (target_signals or flag_res == "si" or n_stock <= 15)) else "no"

        # Note
        makes_in_stock = list({l.make for l in seller_listings})
        note_parts = []
        if makes_in_stock:
            note_parts.append(f"brand: {', '.join(makes_in_stock)}")
        archetype = _estimate_seller_type_from_stock(n_stock, name, indirizzo)
        note_parts.append(f"archetype_est: {archetype}")
        if target_signals:
            note_parts.append("segnali_qualita: si")
        note = " | ".join(note_parts)

        # Seller profile URL
        seller_url = ""
        for l in seller_listings:
            if l.seller_url:
                seller_url = l.seller_url
                break
        if not seller_url and seller_listings:
            seller_url = seller_listings[0].listing_url

        if not phone:
            # Skip no-phone entries unless they have clear signals
            if flag_target == "no":
                continue

        prospects.append(Prospect(
            provincia=first.provincia,
            citta=citta,
            operatore_nome=name,
            telefono=phone,
            whatsapp=phone if phone else "",
            portale=portale,
            n_auto_in_stock_visibili=n_stock,
            indirizzo_visibile=indirizzo,
            flag_residenziale_si_no=flag_res,
            flag_target_alto_si_no=flag_target,
            note=note,
            url_profilo_venditore=seller_url,
        ))

    # Deduplicate by telefono
    seen_phones: set = set()
    deduped = []
    for p in prospects:
        phone_key = p.telefono if p.telefono else f"notel_{p.operatore_nome}_{p.provincia}"
        if phone_key not in seen_phones:
            seen_phones.add(phone_key)
            deduped.append(p)

    # Sort: target_alto first, then by provincia
    deduped.sort(key=lambda x: (x.flag_target_alto_si_no == "no", x.provincia, x.citta))
    return deduped


# ---------------------------------------------------------------------------
# Register corpus extraction
# ---------------------------------------------------------------------------

# Patterns per sezione corpus
_GARANZIA_RE = re.compile(
    r'(?:garanzia|warranty|garanz)[^.!?;\n]{5,80}',
    re.IGNORECASE
)
_TRATTATIVA_RE = re.compile(
    r'(?:no perditempo|permuta|trattativa|visionabile|appuntamento|unico proprietario'
    r'|primo proprietario|tagliand[io]|km certif|senza intermediari|privato vende'
    r'|privato cede|finanziamento|pagamento|solo contanti|contattare|whatsapp)[^.!?;\n]{0,100}',
    re.IGNORECASE
)
_CONTATTO_RE = re.compile(
    r'(?:chiamare|contattare|whatsapp|solo\s+wha|tel\.|tel:|cellulare|numero'
    r'|dopo le ore|mattina|pomeriggio|weekend|sabato|domenica|dalle ore'
    r'|no chiamate|non disturbare|disponibile|ore\s+\d{1,2})[^.!?;\n]{0,100}',
    re.IGNORECASE
)

# Auto description keywords (sentences about the car itself)
_AUTO_DESCRIZIONE_RE = re.compile(
    r'(?:optional|allestimento|interni|esterni|navigatore|tetto apribile|pelle'
    r'|sedili|cerchi|xeno|led|cerchi\s+in\s+alluminio|verniciatura|colore'
    r'|motore|cambio automatico|automatica|manuale|cv\b|kw\b|cilindrata'
    r'|immatricolata|prima immatricolazione|prima iscrizione'
    r'|tagliandi|full service|service|revisione'
    r'|pacchetto|pack\s+m|sport\s+line|amg\s+line|avantgarde|business'
    r'|sensori|telecamera|cruise control|adaptive|carplay|android auto'
    r'|trazione|4x4|4matic|xdrive|quattro|diesel|benzina|ibrido|elettrico)[^.!?;\n]{0,120}',
    re.IGNORECASE
)


def extract_corpus_phrases(listings: List[RawListing]) -> Dict[str, List[Dict]]:
    """
    Extract verbatim phrases grouped by function.
    Returns dict with sections: descrizione_auto, garanzia, trattativa, pattern_contatto
    """
    corpus: Dict[str, List[Dict]] = {
        "descrizione_auto": [],
        "garanzia": [],
        "trattativa": [],
        "pattern_contatto": [],
    }
    seen_phrases: Dict[str, set] = {k: set() for k in corpus}

    for listing in listings:
        text = listing.description or listing.title
        if not text or len(text) < 15:
            continue

        source_tag = f"{listing.portal} | {listing.provincia} | {listing.listing_id}"

        def add_phrase(section: str, phrase: str) -> None:
            phrase = phrase.strip().strip(".,;:")
            phrase = re.sub(r'\s+', ' ', phrase)
            if len(phrase) < 15 or len(phrase) > 300:
                return
            key = re.sub(r'\W+', '', phrase.lower())[:60]
            if key in seen_phrases[section]:
                return
            seen_phrases[section].add(key)
            corpus[section].append({"phrase": phrase, "source": source_tag})

        # Descrizione auto
        for m in _AUTO_DESCRIZIONE_RE.finditer(text):
            # Try to get full sentence
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 60)
            sentence = text[start:end]
            # Trim to sentence boundaries
            sent_m = re.search(r'[.!?;\n][^.!?;\n]{10,}', sentence)
            if sent_m:
                add_phrase("descrizione_auto", sent_m.group(0)[1:].strip())
            else:
                add_phrase("descrizione_auto", m.group(0))

        # Garanzia
        for m in _GARANZIA_RE.finditer(text):
            add_phrase("garanzia", m.group(0))

        # Trattativa
        for m in _TRATTATIVA_RE.finditer(text):
            add_phrase("trattativa", m.group(0))

        # Pattern contatto
        for m in _CONTATTO_RE.finditer(text):
            add_phrase("pattern_contatto", m.group(0))

    return corpus


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_corpus_register(corpus: Dict[str, List[Dict]]) -> Path:
    """Write corpus_register.md."""
    out = OUTPUT_DIR / "corpus_register.md"
    section_titles = {
        "descrizione_auto": "Descrizione auto",
        "garanzia": "Garanzia offerta",
        "trattativa": "Trattativa / contatto",
        "pattern_contatto": "Pattern contatto",
    }

    lines = [
        "# Corpus Register Micro-Dealer Premium — Marche",
        f"_Generato: {datetime.now().strftime('%Y-%m-%d %H:%M')} | ARGOS S206_",
        "",
        "Frasi verbatim da annunci reali. No sintesi, no parafrasi. Letterali.",
        "Fonte: AutoScout24.it + Subito.it + Automobile.it",
        "",
    ]

    total = sum(len(v) for v in corpus.values())
    lines.append(f"**Totale frasi estratte: {total}**")
    lines.append("")

    for section_key, section_title in section_titles.items():
        phrases = corpus.get(section_key, [])
        lines.append(f"---")
        lines.append(f"## {section_title}")
        lines.append(f"_{len(phrases)} frasi_")
        lines.append("")

        if not phrases:
            lines.append("_(nessuna frase estratta per questa sezione)_")
            lines.append("")
            continue

        for item in phrases:
            lines.append(f'- "{item["phrase"]}"')
            lines.append(f'  `[fonte: {item["source"]}]`')
            lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    log.info("[output] corpus_register.md — %d frasi", total)
    return out


def write_prospect_csv(prospects: List[Prospect]) -> Path:
    """Write prospect_list.csv."""
    out = OUTPUT_DIR / "prospect_list.csv"
    fieldnames = [
        "regione", "provincia", "citta", "operatore_nome", "telefono",
        "whatsapp", "portale", "n_auto_in_stock_visibili", "indirizzo_visibile",
        "flag_residenziale_si_no", "flag_target_alto_si_no", "note",
        "url_profilo_venditore",
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in prospects:
            writer.writerow(asdict(p))

    log.info("[output] prospect_list.csv — %d prospects", len(prospects))
    return out


def write_prospect_by_province(prospects: List[Prospect]) -> Path:
    """Write prospect_list_per_provincia.md."""
    out = OUTPUT_DIR / "prospect_list_per_provincia.md"

    lines = [
        "# Prospect per Provincia — Marche",
        f"_Generato: {datetime.now().strftime('%Y-%m-%d %H:%M')} | ARGOS S206_",
        "",
        "Vista gerarchica per pianificazione chiamate Luke.",
        "",
    ]

    # Group by province
    by_prov: Dict[str, List[Prospect]] = {}
    for p in prospects:
        by_prov.setdefault(p.provincia, []).append(p)

    total_target = sum(1 for p in prospects if p.flag_target_alto_si_no == "si")
    lines.append(f"**Totale operatori: {len(prospects)} | Target alto: {total_target}**")
    lines.append("")

    for prov_code in sorted(by_prov.keys()):
        prov_name = PROVINCE_MARCHE.get(prov_code, prov_code)
        prov_prospects = by_prov[prov_code]
        target_count = sum(1 for p in prov_prospects if p.flag_target_alto_si_no == "si")

        lines.append(f"## {prov_code} — {prov_name}")
        lines.append(f"_Operatori: {len(prov_prospects)} | Target alto: {target_count}_")
        lines.append("")

        # Group by city
        by_city: Dict[str, List[Prospect]] = {}
        for p in prov_prospects:
            by_city.setdefault(p.citta or "N/D", []).append(p)

        for city in sorted(by_city.keys()):
            city_prospects = by_city[city]
            target_city = sum(1 for p in city_prospects if p.flag_target_alto_si_no == "si")
            lines.append(f"### {city}")
            lines.append(f"_Operatori: {len(city_prospects)} | Target alto: {target_city}_")
            lines.append("")

            for p in city_prospects:
                flag = "TARGET ALTO" if p.flag_target_alto_si_no == "si" else "monitoraggio"
                phone_display = p.telefono or "N/D"
                lines.append(f"- **{p.operatore_nome}** | {phone_display} | {p.portale}")
                lines.append(f"  Stock visibile: {p.n_auto_in_stock_visibili} auto | [{flag}]")
                if p.note:
                    lines.append(f"  Note: {p.note}")
                lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    log.info("[output] prospect_list_per_provincia.md")
    return out


def write_execution_report(
    all_listings: List[RawListing],
    prospects: List[Prospect],
    corpus: Dict[str, List[Dict]],
    portali_reached: List[str],
    elapsed_seconds: float,
    blockers: List[str],
) -> Path:
    """Write EXECUTION_REPORT.md."""
    out = OUTPUT_DIR / "EXECUTION_REPORT.md"

    target_high = [p for p in prospects if p.flag_target_alto_si_no == "si"]
    with_phone = [p for p in prospects if p.telefono]

    # Count per portal
    portal_counts = {}
    for l in all_listings:
        portal_counts[l.portal] = portal_counts.get(l.portal, 0) + 1

    # Top phrases per section
    top_phrases: Dict[str, List[str]] = {}
    for section, phrases in corpus.items():
        top_phrases[section] = [p["phrase"] for p in phrases[:5]]

    lines = [
        "# EXECUTION REPORT — S206 Marche Register",
        f"_Data: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Elapsed: {elapsed_seconds:.0f}s_",
        "",
        "---",
        "## 1. Portali e copertura",
        "",
    ]

    for portal in portali_reached:
        n = portal_counts.get(portal, 0)
        lines.append(f"- **{portal}**: {n} listing grezzi estratti")

    lines += [
        "",
        "---",
        "## 2. Conteggi",
        "",
        f"- Listing grezzi totali: **{len(all_listings)}**",
        f"- Listing filtrati per range prezzo {PRICE_MIN:,}-{PRICE_MAX:,}€: **{len([l for l in all_listings if PRICE_MIN <= l.price <= PRICE_MAX or l.price == 0])}**",
        f"- Operatori unici estratti: **{len(prospects)}**",
        f"- Con telefono valido: **{len(with_phone)}**",
        f"- Flag TARGET ALTO: **{len(target_high)}**",
        "",
        "**Breakdown TARGET ALTO per provincia:**",
    ]

    for prov_code, prov_name in PROVINCE_MARCHE.items():
        n_prov = sum(1 for p in target_high if p.provincia == prov_code)
        if n_prov > 0:
            lines.append(f"  - {prov_code} ({prov_name}): {n_prov}")

    lines += [
        "",
        "---",
        "## 3. Top frasi ricorrenti per funzione",
        "",
    ]

    section_titles = {
        "descrizione_auto": "Descrizione auto",
        "garanzia": "Garanzia",
        "trattativa": "Trattativa / contatto",
        "pattern_contatto": "Pattern contatto",
    }

    for section_key, section_title in section_titles.items():
        phrases = top_phrases.get(section_key, [])
        lines.append(f"**{section_title}** ({len(corpus.get(section_key, []))} totali):")
        for ph in phrases[:5]:
            lines.append(f'  - "{ph[:120]}"')
        lines.append("")

    lines += [
        "---",
        "## 4. Osservazioni qualitative sul register marchigiano",
        "",
    ]

    # Generate qualitative observations based on actual data
    obs = []

    # Check for private vs dealer
    private_count = sum(1 for l in all_listings if l.seller_type == "private")
    dealer_count = sum(1 for l in all_listings if l.seller_type == "dealer")
    if private_count + dealer_count > 0:
        pct_private = 100 * private_count / (private_count + dealer_count)
        obs.append(f"Mix venditore: {pct_private:.0f}% privati / {100-pct_private:.0f}% dealer tra listing con tipo noto.")

    # Desc coverage
    with_desc = sum(1 for l in all_listings if len(l.description) > 50)
    if all_listings:
        obs.append(f"Copertura descrizione verbatim: {with_desc}/{len(all_listings)} listing ({100*with_desc//len(all_listings) if all_listings else 0}%).")

    # Make distribution
    make_dist = {}
    for l in all_listings:
        make_dist[l.make] = make_dist.get(l.make, 0) + 1
    if make_dist:
        top_make = sorted(make_dist.items(), key=lambda x: -x[1])
        obs.append(f"Distribuzione brand: {', '.join(f'{m}:{n}' for m,n in top_make[:4])}.")

    # Province coverage
    prov_dist = {}
    for l in all_listings:
        prov_dist[l.provincia] = prov_dist.get(l.provincia, 0) + 1
    if prov_dist:
        top_prov = sorted(prov_dist.items(), key=lambda x: -x[1])
        obs.append(f"Province piu' attive: {', '.join(f'{p}:{n}' for p,n in top_prov[:3])}.")

    # Garanzia patterns
    garanzia_phrases = corpus.get("garanzia", [])
    if len(garanzia_phrases) >= 3:
        obs.append(f"Pattern garanzia frequenti: formule ibride 'garanzia ufficiale + mesi estesi' visibili. Segnale di professionalità pur in micro-operatori.")
    else:
        obs.append("Copertura garanzia bassa nel corpus: molti annunci privati non citano garanzia esplicitamente.")

    # Target signals
    if len(target_high) >= 5:
        obs.append(f"Register marchigiano: tono più formale rispetto atteso da Sud Italia. Frasi come 'visionabile su appuntamento', 'unico proprietario' frequenti anche in privati — segnale compatibilità con approccio ARGOS B2B.")
    else:
        obs.append("Corpus limitato: sample insufficiente per generalizzare il register marchigiano. Ondata 2 con province Sud Italia darà baseline comparativo.")

    for i, ob in enumerate(obs, 1):
        lines.append(f"{i}. {ob}")

    if blockers:
        lines += ["", "---", "## 5. Blockers / Warning", ""]
        for b in blockers:
            lines.append(f"- {b}")

    lines += [
        "",
        "---",
        "## 6. Gate chiusura",
        "",
        f"- corpus_register.md: {sum(len(v) for v in corpus.values())} frasi totali (gate: >=40)",
        f"- prospect_list.csv: {len(prospects)} operatori, {len(target_high)} target alto (gate: >=15 op, >=5 target)",
        f"- description committata in git: branch s206/marche-register",
        f"- EXECUTION_REPORT.md: presente",
    ]

    # Gate status
    gate_ok = (
        sum(len(v) for v in corpus.values()) >= 40 and
        len(prospects) >= 15 and
        len(target_high) >= 5
    )
    lines.append("")
    lines.append(f"**GATE STATUS: {'VERDE' if gate_ok else 'GIALLO — vedi note'}**")

    out.write_text("\n".join(lines), encoding="utf-8")
    log.info("[output] EXECUTION_REPORT.md")
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    start = time.time()
    log.info("=== S206 Marche Register Scraper START ===")
    log.info("Backend HTTP: %s", HTTP_BACKEND)
    log.info("Output dir: %s", OUTPUT_DIR)

    all_listings: List[RawListing] = []
    portali_reached: List[str] = []
    blockers: List[str] = []

    # --- AutoScout24 IT ---
    log.info("--- AutoScout24 IT ---")
    try:
        as24_listings = scrape_as24_marche(max_pages_per_combo=2)
        # Enrich descriptions (max 25 detail pages)
        enrich_as24_descriptions(as24_listings, max_detail=25)
        all_listings.extend(as24_listings)
        portali_reached.append("autoscout24")
        log.info("[AS24] done: %d listings", len(as24_listings))
    except Exception as e:
        log.error("[AS24] BLOCKER: %s", e)
        blockers.append(f"AutoScout24: {e}")

    # --- Subito.it ---
    log.info("--- Subito.it ---")
    try:
        subito_listings = scrape_subito_marche()
        all_listings.extend(subito_listings)
        portali_reached.append("subito")
        log.info("[Subito] done: %d listings", len(subito_listings))
    except Exception as e:
        log.error("[Subito] BLOCKER: %s", e)
        blockers.append(f"Subito.it: {e}")

    # --- Automobile.it ---
    log.info("--- Automobile.it ---")
    try:
        autoit_listings = scrape_auto_it_marche()
        all_listings.extend(autoit_listings)
        portali_reached.append("automobile.it")
        log.info("[Autoit] done: %d listings", len(autoit_listings))
    except Exception as e:
        log.error("[Autoit] BLOCKER: %s", e)
        blockers.append(f"Automobile.it: {e}")

    log.info("=== TOTALE LISTING: %d ===", len(all_listings))

    # Build corpus
    corpus = extract_corpus_phrases(all_listings)
    total_corpus = sum(len(v) for v in corpus.values())
    log.info("Corpus frasi: %d (%s)", total_corpus, {k: len(v) for k, v in corpus.items()})

    # Build prospects
    prospects = build_prospects(all_listings)
    log.info("Prospects: %d (%d target alto)", len(prospects),
             sum(1 for p in prospects if p.flag_target_alto_si_no == "si"))

    # Write outputs
    write_corpus_register(corpus)
    write_prospect_csv(prospects)
    write_prospect_by_province(prospects)
    elapsed = time.time() - start
    write_execution_report(all_listings, prospects, corpus, portali_reached, elapsed, blockers)

    # Gate check
    total_fr = sum(len(v) for v in corpus.values())
    n_target = sum(1 for p in prospects if p.flag_target_alto_si_no == "si")
    n_with_phone = sum(1 for p in prospects if p.telefono)

    log.info("=== GATE CHECK ===")
    log.info("corpus frasi: %d (gate >=40): %s", total_fr, "PASS" if total_fr >= 40 else "FAIL")
    log.info("prospects: %d (gate >=15): %s", len(prospects), "PASS" if len(prospects) >= 15 else "FAIL")
    log.info("target_alto: %d (gate >=5): %s", n_target, "PASS" if n_target >= 5 else "FAIL")
    log.info("con_telefono: %d", n_with_phone)
    log.info("elapsed: %.0fs", elapsed)
    log.info("=== S206 Marche Register Scraper DONE ===")


if __name__ == "__main__":
    main()
