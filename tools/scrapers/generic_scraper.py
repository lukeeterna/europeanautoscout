"""
generic_scraper.py -- ARGOS Generic Classified Scraper
CoVe 2026 | Enterprise Grade

Scraper generico configurabile per portali classificati europei.
Usa profili di parsing (regex/CSS) per estrarre listing da qualsiasi portale HTML.

Supporta:
- __NEXT_DATA__ (React/Next.js) — parsing automatico
- JSON-LD structured data
- HTML regex patterns configurabili per portale
- URL template system per ricerca parametrica

Author: ARGOS Automotive CTO Stack
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, quote

from .base_scraper import BaseScraper
from .models import Listing, FuelType, Transmission, SellerType
from .config import YEAR_MIN, YEAR_MAX, km_limit_for

logger = logging.getLogger("argos.generic_scraper")


# ---------------------------------------------------------------------------
# Portal Search Profile — come costruire URL e parsare risultati
# ---------------------------------------------------------------------------
@dataclass
class SearchProfile:
    """Profilo di ricerca per un portale generico."""
    # URL template: {base_url}, {make}, {model}, {year_min}, {year_max}, {km_max}, {page}
    url_template: str
    # Encoding: come il portale vuole make/model nell'URL
    make_in_url: str = "lowercase"  # lowercase, titlecase, uppercase, slug, raw
    model_in_url: str = "lowercase"
    # Separator for slug (e.g., "-" for "serie-3")
    slug_separator: str = "-"
    # Pagination
    page_param: str = "page"
    page_start: int = 1  # 0-based or 1-based
    # Extra query params always added
    extra_params: Dict[str, str] = field(default_factory=dict)
    # Accept-Language header
    accept_language: str = "en-US,en;q=0.9"
    # Make/model name mappings (portal-specific names)
    make_map: Dict[str, str] = field(default_factory=dict)
    model_map: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # Parsing hints
    uses_next_data: bool = False
    uses_json_ld: bool = False
    # Listing container regex (fallback)
    listing_block_re: str = ""
    # Field extraction regexes (applied within listing block)
    title_re: str = ""
    price_re: str = ""
    url_re: str = ""
    image_re: str = ""
    km_re: str = ""
    year_re: str = ""
    fuel_re: str = ""
    # Currency
    currency: str = "EUR"
    # Country code
    country: str = ""
    # Results per page (for pagination detection)
    results_per_page: int = 20


# ---------------------------------------------------------------------------
# Common regex patterns
# ---------------------------------------------------------------------------
PRICE_PATTERNS = [
    # "27.800 EUR", "EUR 27.800"
    r'(?:EUR|€)\s*[\s]*([\d.,]+)',
    r'([\d.,]+)\s*(?:EUR|€)',
    # HTML entities: "27 800 &euro;"
    r'([\d\s.,]+)\s*&euro;',
    # "27 800 kr", "27.800 SEK"
    r'([\d\s.,]+)\s*(?:kr|SEK|CZK|PLN|HUF|RON|DKK|NOK|BGN|HRK)',
    # Generic price in data attribute
    r'data-(?:price|amount)["\s:=]+([\d.,]+)',
    r'"price"[:\s]+([\d.,]+)',
    # "Pris: 279 000"
    r'(?:Pris|Prix|Preis|Prezzo|Precio|Cena|Cijena|Hinta|Kaina)[\s:]*(?:€\s*)?([\d\s.,]+)',
]

KM_PATTERNS = [
    r'([\d.,\s]+)\s*km\b',
    r'(?:km|Kilometer|chilometri|kilom)[\s:]*(\d[\d.,\s]*)',
    r'"mileage"[:\s]+([\d]+)',
]

YEAR_PATTERNS = [
    r'\b(20[12]\d)\b',
    r'(?:EZ|Bj|Anno|Year|Jaar|Rok|An)[\s:.]*(\d{1,2}[/.-])?(20[12]\d)',
    r'(\d{1,2})[/.-](20[12]\d)',
]


def _clean_price(text: str) -> Optional[float]:
    """Parse price string to float."""
    if not text:
        return None
    # Remove spaces, non-breaking spaces
    cleaned = re.sub(r'[\s\u00a0]', '', text.strip())
    # Handle both , and . as decimal/thousands
    if ',' in cleaned and '.' in cleaned:
        # "27.800,00" or "27,800.00"
        if cleaned.rindex(',') > cleaned.rindex('.'):
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Could be "27,800" (thousands) or "27,50" (decimal)
        parts = cleaned.split(',')
        if len(parts[-1]) == 3:
            cleaned = cleaned.replace(',', '')
        else:
            cleaned = cleaned.replace(',', '.')
    # Remove currency symbols
    cleaned = re.sub(r'[^\d.]', '', cleaned)
    try:
        val = float(cleaned)
        return val if val > 100 else None  # skip obvious non-prices
    except (ValueError, TypeError):
        return None


def _clean_km(text: str) -> Optional[int]:
    """Parse km string to int."""
    if not text:
        return None
    cleaned = re.sub(r'[^\d]', '', text.strip())
    try:
        val = int(cleaned)
        return val if 0 < val < 1_000_000 else None
    except (ValueError, TypeError):
        return None


def _clean_year(text: str) -> Optional[int]:
    """Parse year string to int."""
    if not text:
        return None
    m = re.search(r'(20[12]\d)', text)
    if m:
        return int(m.group(1))
    return None


def _guess_fuel(text: str) -> FuelType:
    """Guess fuel type from multilingual text."""
    t = text.lower()
    if any(w in t for w in ('elektr', 'electric', 'ev', 'bev')):
        return FuelType.ELECTRIC
    if any(w in t for w in ('plugin', 'plug-in', 'phev')):
        return FuelType.PLUGIN_HYBRID
    if any(w in t for w in ('hybrid', 'ibrido', 'hybride')):
        return FuelType.HYBRID
    if any(w in t for w in ('diesel', 'tdi', 'cdi', 'hdi', 'dci', 'jtd', 'bluehdi')):
        return FuelType.DIESEL
    if any(w in t for w in ('benzin', 'petrol', 'gasoline', 'essence', 'benzina', 'ottomotor', 'tfsi', 'tsi')):
        return FuelType.PETROL
    if any(w in t for w in ('lpg', 'gpl', 'autogas')):
        return FuelType.LPG
    if any(w in t for w in ('cng', 'erdgas', 'metano')):
        return FuelType.CNG
    return FuelType.UNKNOWN


# ---------------------------------------------------------------------------
# Currency conversion (approximate, for non-EUR countries)
# ---------------------------------------------------------------------------
CURRENCY_TO_EUR: Dict[str, float] = {
    "EUR": 1.0,
    "SEK": 0.088,    # ~11.4 SEK/EUR
    "CZK": 0.040,    # ~25 CZK/EUR
    "PLN": 0.233,    # ~4.3 PLN/EUR
    "HUF": 0.0025,   # ~400 HUF/EUR
    "RON": 0.201,    # ~5.0 RON/EUR
    "DKK": 0.134,    # ~7.46 DKK/EUR
    "NOK": 0.086,    # ~11.6 NOK/EUR
    "BGN": 0.511,    # ~1.96 BGN/EUR
    "HRK": 0.133,    # ~7.53 HRK/EUR (legacy, now EUR)
    "GBP": 1.17,     # ~0.85 GBP/EUR
    "CHF": 1.06,     # ~0.94 CHF/EUR
}


def _to_eur(price: float, currency: str) -> float:
    """Convert price to EUR using approximate rates."""
    rate = CURRENCY_TO_EUR.get(currency, 1.0)
    return round(price * rate, 2)


# ---------------------------------------------------------------------------
# GenericClassifiedScraper
# ---------------------------------------------------------------------------
class GenericClassifiedScraper(BaseScraper):
    """
    Scraper generico per portali classificati.
    Configurato tramite SearchProfile per adattarsi a qualsiasi portale.

    RESILIENTE AI CAMBIAMENTI CSS:
    - MAI usa CSS selectors per trovare listing
    - Parsing prioritario via dati strutturati (JSON-LD, __NEXT_DATA__, GraphQL)
    - Fallback via pattern universali (link + prezzo nel contesto)
    - Multi-backend HTTP (curl_cffi -> cloudscraper -> requests)
    """

    def __init__(self, portal_key: str, profile: SearchProfile) -> None:
        super().__init__(portal_key)
        self.profile = profile
        # Initialize resilient fetcher for anti-bot bypass
        try:
            from .resilient_fetcher import ResilientFetcher
            self._resilient = ResilientFetcher(
                timeout=self.timeout,
                max_retries=self.max_retries,
                backoff_base=self.backoff_base,
            )
        except ImportError:
            self._resilient = None

    def _format_make(self, make: str) -> str:
        """Format make name for URL."""
        # Check portal-specific mapping first
        if make in self.profile.make_map:
            return self.profile.make_map[make]
        style = self.profile.make_in_url
        if style == "lowercase":
            return make.lower().replace(" ", self.profile.slug_separator)
        elif style == "titlecase":
            return make.title()
        elif style == "uppercase":
            return make.upper()
        elif style == "slug":
            return quote(make.lower().replace(" ", self.profile.slug_separator))
        return make

    def _format_model(self, make: str, model: str) -> str:
        """Format model name for URL."""
        # Check portal-specific mapping first
        model_maps = self.profile.model_map.get(make, {})
        if model in model_maps:
            return model_maps[model]
        style = self.profile.model_in_url
        if style == "lowercase":
            return model.lower().replace(" ", self.profile.slug_separator)
        elif style == "titlecase":
            return model.title()
        elif style == "slug":
            return quote(model.lower().replace(" ", self.profile.slug_separator))
        return model

    def build_search_url(
        self,
        make: str,
        model: str,
        page: int = 1,
        **kwargs: Any,
    ) -> str:
        year_min = kwargs.get("year_min", YEAR_MIN)
        year_max = kwargs.get("year_max", YEAR_MAX)
        km_max = kwargs.get("km_max") or km_limit_for(make, model)

        fmt_make = self._format_make(make)
        fmt_model = self._format_model(make, model)

        url = self.profile.url_template.format(
            base_url=self.portal.base_url,
            make=fmt_make,
            model=fmt_model,
            year_min=year_min,
            year_max=year_max,
            km_max=km_max,
            page=page + (self.profile.page_start - 1),  # adjust for 0-based pagination
        )

        return url

    def fetch(self, url: str, extra_headers: Optional[Dict[str, str]] = None, retry: int = 0) -> str:
        """
        Override: usa ResilientFetcher (multi-backend) come primo tentativo.
        Fallback a BaseScraper.fetch() se ResilientFetcher non disponibile.
        """
        all_headers = {"Accept-Language": self.profile.accept_language}
        if extra_headers:
            all_headers.update(extra_headers)

        # Try resilient fetcher first (multi-backend: curl_cffi -> cloudscraper -> requests)
        if self._resilient is not None:
            try:
                html = self._resilient.fetch(
                    url,
                    accept_language=self.profile.accept_language,
                    extra_headers=extra_headers,
                )
                self._request_count += 1
                self._daily_count += 1
                return html
            except RuntimeError:
                # All backends failed — fall through to base fetch
                logger.warning(
                    "[%s] ResilientFetcher failed, falling back to base fetch",
                    self.portal_key,
                )

        return super().fetch(url, extra_headers=all_headers, retry=retry)

    def parse_listings(
        self,
        html: str,
        country: str,
        make: str,
        model: str,
    ) -> List[Listing]:
        if not html or len(html) < 200:
            return []

        country = country or self.profile.country

        # Strategy 1: __NEXT_DATA__ (React/Next.js)
        if self.profile.uses_next_data:
            listings = self._parse_next_data(html, country, make, model)
            if listings:
                return listings

        # Strategy 2: JSON-LD
        if self.profile.uses_json_ld:
            listings = self._parse_json_ld(html, country, make, model)
            if listings:
                return listings

        # Strategy 3: Auto-detect __PRERENDERED_STATE__ (OLX group: olx.pl, olx.ro)
        if '__PRERENDERED_STATE__' in html:
            listings = self._parse_prerendered_state(html, country, make, model)
            if listings:
                return listings

        # Strategy 3b: Auto-detect __NEXT_DATA__
        if '__NEXT_DATA__' in html:
            listings = self._parse_next_data(html, country, make, model)
            if listings:
                return listings

        # Strategy 4: Auto-detect JSON-LD
        if 'application/ld+json' in html:
            listings = self._parse_json_ld(html, country, make, model)
            if listings:
                return listings

        # Strategy 5: HTML regex parsing
        listings = self._parse_html_regex(html, country, make, model)
        if listings:
            return listings

        # Strategy 6: Aggressive link extraction
        listings = self._parse_aggressive(html, country, make, model)
        return listings

    # ----- __NEXT_DATA__ parsing -----

    def _parse_next_data(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        pattern = re.compile(
            r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            re.DOTALL,
        )
        match = pattern.search(html)
        if not match:
            return []

        try:
            data = json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            return []

        page_props = data.get("props", {}).get("pageProps", {})

        # Strategy A: GraphQL urqlState (OLX Group: Otomoto, Standvirtual, Autovit)
        urql_state = page_props.get("urqlState", {})
        if urql_state:
            listings = self._parse_urql_state(urql_state, country, make, model)
            if listings:
                return listings

        # Strategy B: React Query dehydratedState (Bilbasen, Finn.no, Blocket, etc.)
        dehydrated = page_props.get("dehydratedState", {})
        if dehydrated:
            listings = self._parse_dehydrated_state(dehydrated, country, make, model)
            if listings:
                return listings

        # Strategy C: Direct listing arrays in pageProps
        items = self._find_listing_arrays(page_props)

        listings = []
        for item in items:
            lst = self._json_item_to_listing(item, country, make, model)
            if lst:
                listings.append(lst)
        return listings

    def _parse_urql_state(
        self, urql_state: Dict, country: str, make: str, model: str
    ) -> List[Listing]:
        """Parse GraphQL urqlState cache (OLX Group pattern: Otomoto, Standvirtual, Autovit)."""
        listings = []
        for _cache_key, cache_val in urql_state.items():
            if not isinstance(cache_val, dict):
                continue
            d = cache_val.get("data", "")
            if isinstance(d, str):
                try:
                    d = json.loads(d)
                except (json.JSONDecodeError, ValueError):
                    continue

            if not isinstance(d, dict):
                continue

            # Find advertSearch or similar top-level query result
            search_result = None
            for key in ("advertSearch", "searchResult", "search", "listing"):
                if key in d:
                    search_result = d[key]
                    break
            if not search_result or not isinstance(search_result, dict):
                continue

            # Extract edges -> node (GraphQL relay pagination)
            edges = search_result.get("edges", [])
            if not edges:
                continue

            for edge in edges:
                if not isinstance(edge, dict):
                    continue
                node = edge.get("node", edge)
                if not isinstance(node, dict):
                    continue

                lst = self._graphql_node_to_listing(node, country, make, model)
                if lst:
                    listings.append(lst)

        return listings

    def _parse_dehydrated_state(
        self, dehydrated: Dict, country: str, make: str, model: str
    ) -> List[Listing]:
        """Parse React Query dehydratedState (Bilbasen, Finn.no, Blocket, modern Nordic portals)."""
        listings = []
        queries = dehydrated.get("queries", [])

        for query in queries:
            state = query.get("state", {})
            state_data = state.get("data", {})
            if not isinstance(state_data, dict):
                continue

            # Find listing arrays in the query data
            items = self._find_listing_arrays(state_data)
            if not items:
                continue

            for item in items:
                lst = self._json_item_to_listing(item, country, make, model)
                if lst:
                    listings.append(lst)

            if listings:
                return listings

        return listings

    def _parse_prerendered_state(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """Parse OLX __PRERENDERED_STATE__ (double-encoded JSON in olx.pl, olx.ro)."""
        # Find the raw JSON-escaped content
        pos = html.find('__PRERENDERED_STATE__')
        if pos < 0:
            return []
        eq_pos = html.find('=', pos)
        q_start = html.find('"', eq_pos)
        script_end = html.find('</script>', q_start)
        if q_start < 0 or script_end < 0:
            return []
        q_end = html.rfind('"', q_start + 1, script_end)
        if q_end <= q_start:
            return []

        raw = html[q_start + 1:q_end]

        # Extract ads via regex from the escaped JSON
        # Pattern: \"id\":{id},\"title\":\"...\",\"description\":\"...\",...
        ad_pattern = re.compile(
            r'\\"id\\":(\d{5,}),\\"title\\":\\"([^\\]*(?:\\.[^\\]*)*?)\\"',
        )

        listings = []
        for m in ad_pattern.finditer(raw):
            ad_id = m.group(1)
            title = m.group(2).replace('\\"', '"')

            # Get chunk after this ad for parsing fields (up to next ad or 10K chars)
            chunk_start = m.start()
            next_ad = ad_pattern.search(raw, m.end() + 100)
            chunk_end = next_ad.start() if next_ad else min(chunk_start + 10000, len(raw))
            chunk = raw[chunk_start:chunk_end]

            # Price: regularPrice\":{\"value\":123456
            price = None
            price_m = re.search(r'\\"regularPrice\\":\{\\"value\\":(\d+)', chunk)
            if price_m:
                price = float(price_m.group(1))
            if not price:
                price_m2 = re.search(r'\\"displayValue\\":\\"([\d\s]+)', chunk)
                if price_m2:
                    price = _clean_price(price_m2.group(1))
            if not price or price < 500:
                continue

            # Currency
            curr_m = re.search(r'\\"currencyCode\\":\\"(\w+)\\"', chunk)
            currency = curr_m.group(1) if curr_m else self.profile.currency
            if currency != "EUR":
                price = _to_eur(price, currency)

            # URL: \"url\":\"https:\u002F\u002F...\"
            url = ""
            url_m = re.search(r'\\"url\\":\\"(https?:[^"]*?)\\"', chunk)
            if url_m:
                url = url_m.group(1).replace('\\u002F', '/').replace('\\"', '"').replace('\\/', '/')

            # Params extraction
            params = {}
            param_pattern = re.compile(
                r'\\"key\\":\\"(\w+)\\".*?\\"normalizedValue\\":\\"([^\\]*)\\"'
            )
            for pm in param_pattern.finditer(chunk):
                params[pm.group(1)] = pm.group(2)

            year = _clean_year(params.get('year', ''))
            km = _clean_km(params.get('milage', params.get('mileage', '')))
            fuel = _guess_fuel(params.get('petrol', ''))

            # Images
            images = []
            img_pattern = re.compile(r'\\"link\\":\\"(https?:[^\\]*?\.(?:jpg|webp|jpeg|png)[^\\]*?)\\"')
            for im in img_pattern.finditer(chunk[:3000]):
                img_url = im.group(1).replace('\\u002F', '/')
                if img_url not in images:
                    images.append(img_url)
                    if len(images) >= 3:
                        break

            lid = f"olx_{ad_id}"
            listings.append(Listing(
                listing_id=lid,
                portal=self.portal_key,
                country=country,
                make=make,
                model=params.get('model', model),
                variant=title[:200],
                year=year or 0,
                km=km or 0,
                fuel_type=fuel,
                price_eur=price,
                currency_original=currency,
                listing_url=url,
                image_urls=images,
            ))

            if len(listings) >= 40:
                break

        return listings

    def _graphql_node_to_listing(
        self, node: Dict[str, Any], country: str, make: str, model: str
    ) -> Optional[Listing]:
        """Convert a GraphQL node (OLX Group format) to Listing."""
        # URL
        url = node.get("url", "")
        if url and not url.startswith("http"):
            url = f"{self.portal.base_url.rstrip('/')}{url}"

        # Price — OLX Group: {"amount": 139900, "currency": "PLN", "displayValue": "139 900 PLN"}
        price_obj = node.get("price", {})
        price = None
        if isinstance(price_obj, dict):
            price = price_obj.get("amount")
            if isinstance(price, dict):
                price = price.get("value") or price.get("amount")
            if price is None:
                dv = price_obj.get("displayValue", price_obj.get("priceFormatted", ""))
                price = _clean_price(str(dv))
            else:
                price = float(price) if price else None
            # Currency conversion
            curr = price_obj.get("currency", self.profile.currency)
            if price and curr != "EUR":
                price = _to_eur(price, curr)
        elif isinstance(price_obj, (int, float)):
            price = float(price_obj)
            if self.profile.currency != "EUR":
                price = _to_eur(price, self.profile.currency)
        elif isinstance(price_obj, str):
            price = _clean_price(price_obj)

        if not price or price < 500:
            return None

        # Parameters array (OLX Group pattern)
        params = {}
        raw_params = node.get("parameters", [])
        if isinstance(raw_params, list):
            for p in raw_params:
                if isinstance(p, dict):
                    key = p.get("key", p.get("label", ""))
                    val = p.get("value", p.get("displayValue", ""))
                    dval = p.get("displayValue", val)
                    params[key] = {"value": val, "display": dval}

        # Make / Model from params
        node_make = params.get("make", {}).get("display", node.get("make", make))
        node_model = params.get("model", {}).get("display", node.get("model", model))

        # Year
        year = None
        year_param = params.get("year", {}).get("value", "")
        if year_param:
            year = _clean_year(str(year_param))
        if not year:
            year = _clean_year(str(node.get("year", node.get("firstRegistration", ""))))

        # KM
        km = None
        km_param = params.get("mileage", {}).get("value", "")
        if km_param:
            km = _clean_km(str(km_param))
        if not km:
            km = _clean_km(str(node.get("mileage", "")))

        # Fuel
        fuel = FuelType.UNKNOWN
        fuel_param = params.get("fuel_type", {}).get("value", "")
        if fuel_param:
            fuel = _guess_fuel(fuel_param)
        if fuel == FuelType.UNKNOWN:
            fuel_param = params.get("fuel_type", {}).get("display", "")
            if fuel_param:
                fuel = _guess_fuel(fuel_param)

        # Transmission
        trans = Transmission.UNKNOWN
        gearbox = params.get("gearbox", {}).get("value", "")
        if "automat" in gearbox.lower():
            trans = Transmission.AUTOMATIC
        elif "manual" in gearbox.lower():
            trans = Transmission.MANUAL

        # Power
        power = 0
        power_param = params.get("engine_power", {}).get("value", "")
        if power_param:
            try:
                power = int(power_param)
            except (ValueError, TypeError):
                pass

        # Images
        images = []
        thumb = node.get("thumbnail", {})
        if isinstance(thumb, dict):
            for ik in ("x2", "x1", "url", "src"):
                if ik in thumb:
                    images.append(thumb[ik])
                    break
        elif isinstance(thumb, str):
            images.append(thumb)

        photos = node.get("photos", node.get("images", []))
        if isinstance(photos, list):
            for ph in photos[:5]:
                if isinstance(ph, str):
                    images.append(ph)
                elif isinstance(ph, dict):
                    img_url = ph.get("url", ph.get("x2", ph.get("src", "")))
                    if img_url:
                        images.append(img_url)

        # Seller
        seller_type = SellerType.UNKNOWN
        seller_name = ""
        seller_obj = node.get("seller", {})
        if isinstance(seller_obj, dict):
            seller_name = seller_obj.get("name", seller_obj.get("companyName", ""))
            stype = seller_obj.get("type", seller_obj.get("__typename", ""))
            if "dealer" in stype.lower() or "business" in stype.lower():
                seller_type = SellerType.DEALER
            elif "private" in stype.lower() or "person" in stype.lower():
                seller_type = SellerType.PRIVATE

        # Location
        location = ""
        loc_obj = node.get("location", {})
        if isinstance(loc_obj, dict):
            city = loc_obj.get("city", loc_obj.get("cityName", ""))
            region = loc_obj.get("region", loc_obj.get("regionName", ""))
            location = f"{city}, {region}" if city and region else (city or region)

        # ID
        lid = str(node.get("id", ""))
        if not lid:
            lid = self.generate_listing_id(self.portal_key, url or str(price))

        title = node.get("title", node.get("shortDescription", ""))

        return Listing(
            listing_id=lid,
            portal=self.portal_key,
            country=country,
            make=str(node_make) or make,
            model=str(node_model) or model,
            variant=str(title)[:200] if title else "",
            year=year or 0,
            km=km or 0,
            fuel_type=fuel,
            transmission=trans,
            power_hp=power,
            price_eur=price,
            currency_original=self.profile.currency,
            seller_type=seller_type,
            seller_name=seller_name,
            seller_location=location,
            listing_url=url,
            image_urls=images,
        )

    def _find_listing_arrays(self, obj: Any, depth: int = 0) -> List[Dict]:
        """
        Recursively find arrays that look like listing data.
        Handles multiple structures:
        - Direct arrays: {listings: [...]}
        - Nested: {advertSummaryList: {advertSummary: [...]}}
        - GraphQL: {edges: [{node: {...}}, ...]}
        """
        if depth > 6:
            return []

        # Keywords that indicate listing arrays (must be word-boundary safe)
        _LISTING_KEYWORDS = (
            'listing', 'result', 'items', 'vehicle', 'advert',
            'offer', 'annonce', 'summary', 'classified', 'inserat',
            'ads', 'cars', 'fahrzeug',
        )

        def _key_matches(key_lower: str) -> bool:
            """Check if key likely refers to listings (not breadcrumbs, etc.)."""
            # Exclude known non-listing arrays
            if any(x in key_lower for x in ('breadcrumb', 'navigator', 'filter', 'facet', 'sort', 'paging', 'link')):
                return False
            return any(k in key_lower for k in _LISTING_KEYWORDS)

        if isinstance(obj, dict):
            for key, val in obj.items():
                key_lower = key.lower()
                # Direct array with listing-like name
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    if _key_matches(key_lower):
                        return val
                # Nested dict with listing array inside
                elif isinstance(val, dict):
                    for k2, v2 in val.items():
                        k2_lower = k2.lower()
                        if isinstance(v2, list) and len(v2) > 0 and isinstance(v2[0], dict):
                            if _key_matches(k2_lower):
                                return v2

            # Recurse into all dict values
            for key, val in obj.items():
                sub = self._find_listing_arrays(val, depth + 1)
                if sub:
                    return sub

        elif isinstance(obj, list) and len(obj) > 0:
            # Check if this list itself contains listing-like dicts
            if isinstance(obj[0], dict) and len(obj[0]) > 3:
                keys_lower = {k.lower() for k in obj[0].keys()}
                if keys_lower & {'price', 'url', 'title', 'id', 'make', 'brand', 'model', 'description', 'selflink'}:
                    return obj

        return []

    def _extract_willhaben_attrs(self, item: Dict) -> Dict[str, str]:
        """Extract Willhaben-style attributes: {attribute: [{name, values}, ...]}."""
        attrs_raw = item.get("attributes", {})
        if isinstance(attrs_raw, dict):
            attr_list = attrs_raw.get("attribute", [])
        elif isinstance(attrs_raw, list):
            attr_list = attrs_raw
        else:
            return {}
        result = {}
        for a in attr_list:
            if isinstance(a, dict):
                name = a.get("name", "")
                values = a.get("values", [])
                if name and values:
                    result[name] = values[0] if len(values) == 1 else str(values)
        return result

    def _json_item_to_listing(
        self, item: Dict[str, Any], country: str, make: str, model: str
    ) -> Optional[Listing]:
        """Convert a JSON item (from __NEXT_DATA__ or JSON-LD) to a Listing."""
        if not isinstance(item, dict):
            return None

        # Check for Willhaben-style attributes
        wh_attrs = self._extract_willhaben_attrs(item)

        # Marktplaats/generic attributes array: [{key, value, values, unit}, ...]
        mp_attrs = {}
        raw_attrs = item.get('attributes', [])
        if isinstance(raw_attrs, list):
            for attr in raw_attrs:
                if isinstance(attr, dict) and 'key' in attr:
                    mp_attrs[attr['key']] = attr.get('value', '')
        # Also check extendedAttributes
        ext_attrs = item.get('extendedAttributes', [])
        if isinstance(ext_attrs, list):
            for attr in ext_attrs:
                if isinstance(attr, dict) and 'key' in attr:
                    mp_attrs[attr['key']] = attr.get('value', '')

        # URL — multiple strategies
        url = ""
        # Strategy 1: Direct URL fields
        for key in ('url', 'uri', 'vipUrl', 'detailUrl', 'pdpUrl', 'link', 'href', 'detailPageUrl', 'seoUrl', 'selfLink'):
            url = item.get(key, "")
            if url:
                break
        # Strategy 2: Nested links/urls
        if not url:
            for sub_key in ('links', 'urls', 'contextLinkList'):
                sub = item.get(sub_key, {})
                if isinstance(sub, dict):
                    # Willhaben: contextLinkList.contextLink[{id, uri}]
                    cl = sub.get('contextLink', [])
                    if isinstance(cl, list):
                        for link in cl:
                            if isinstance(link, dict) and link.get('id') in ('iadAdDetail', 'detail', 'selfLink'):
                                url = link.get('uri', link.get('relativePath', ''))
                                if url:
                                    break
                    if not url:
                        url = sub.get('detail', sub.get('self', sub.get('canonical', '')))
                    if url:
                        break
        # Strategy 3: Willhaben SEO_URL attribute
        if not url and 'SEO_URL' in wh_attrs:
            url = f"{self.portal.base_url}/iad/{wh_attrs['SEO_URL']}"

        if url and not url.startswith('http'):
            url = f"{self.portal.base_url.rstrip('/')}{url}"

        # Price — multiple strategies
        price = None
        # Strategy 1: Direct price field
        price_raw = item.get('price', item.get('priceInfo', item.get('pricing', '')))
        if isinstance(price_raw, dict):
            # Marktplaats: priceCents (divide by 100)
            if 'priceCents' in price_raw:
                try:
                    price = float(price_raw['priceCents']) / 100.0
                except (ValueError, TypeError):
                    pass
            if not price:
                for pk in ('amount', 'value', 'price', 'priceFormatted', 'displayPrice', 'main', 'display', 'raw'):
                    if pk in price_raw:
                        price = _clean_price(str(price_raw[pk]))
                        if price:
                            break
        elif isinstance(price_raw, (int, float)):
            price = float(price_raw)
        elif isinstance(price_raw, str):
            price = _clean_price(price_raw)
        # Strategy 2: JSON-LD offers (Finn.no, Blocket, standard schema.org)
        price_currency = self.profile.currency
        if not price:
            offers = item.get('offers', {})
            if isinstance(offers, dict):
                for pk in ('price', 'lowPrice', 'highPrice'):
                    if pk in offers:
                        price = _clean_price(str(offers[pk]))
                        if price:
                            price_currency = offers.get('priceCurrency', price_currency)
                            break
            elif isinstance(offers, list) and offers:
                o = offers[0]
                if isinstance(o, dict):
                    price = _clean_price(str(o.get('price', '')))
                    if price:
                        price_currency = o.get('priceCurrency', price_currency)
        # Strategy 3: Willhaben-style attribute
        if not price and 'PRICE/AMOUNT' in wh_attrs:
            price = _clean_price(wh_attrs['PRICE/AMOUNT'])

        if not price:
            return None

        # Convert to EUR if needed (use detected currency from offers or profile default)
        effective_currency = price_currency if price_currency != self.profile.currency else self.profile.currency
        if effective_currency != "EUR":
            price = _to_eur(price, effective_currency)

        # Title / Make / Model
        title = item.get('title', item.get('name', item.get('heading', item.get('description', ''))))
        item_make = item.get('make', item.get('brand', item.get('manufacturer', '')))
        if isinstance(item_make, dict):
            item_make = item_make.get('name', '')
        # Willhaben attributes
        if not item_make and 'CAR_MODEL/MAKE' in wh_attrs:
            item_make = wh_attrs['CAR_MODEL/MAKE']
        item_make = item_make or make

        item_model_raw = item.get('model', item.get('modelGroup', ''))
        if isinstance(item_model_raw, dict):
            item_model_raw = item_model_raw.get('name', '')
        if not item_model_raw and 'CAR_MODEL/MODEL' in wh_attrs:
            item_model_raw = wh_attrs['CAR_MODEL/MODEL']
        item_model_raw = item_model_raw or model

        variant = item.get('variant', item.get('version', item.get('modelVersionInput', '')))
        if not variant and 'CAR_MODEL/MODEL_SPECIFICATION' in wh_attrs:
            variant = wh_attrs['CAR_MODEL/MODEL_SPECIFICATION']

        # Year and KM (initialized early — details parsing may set both)
        year = None
        km = None
        for yk in ('year', 'firstRegistration', 'registrationYear', 'modelYear'):
            yr = item.get(yk, '')
            if yr:
                year = _clean_year(str(yr))
                if year:
                    break
        # Try nested vehicle
        vehicle = item.get('vehicle', {})
        if not year and isinstance(vehicle, dict):
            for yk in ('year', 'firstRegistration', 'modelYear'):
                yr = vehicle.get(yk, '')
                if yr:
                    year = _clean_year(str(yr))
                    if year:
                        break
        # Willhaben: YEAR_MODEL attribute
        if not year and 'YEAR_MODEL' in wh_attrs:
            year = _clean_year(wh_attrs['YEAR_MODEL'])
        # Marktplaats/generic: constructionYear attribute
        if not year and 'constructionYear' in mp_attrs:
            year = _clean_year(str(mp_attrs['constructionYear']))
        # Bilbasen/Nordic: properties.firstregistrationdate
        if not year:
            props = item.get('properties', {})
            if isinstance(props, dict):
                for pk in ('firstregistrationdate', 'registrationDate', 'yearModel'):
                    pv = props.get(pk, {})
                    if isinstance(pv, dict):
                        year = _clean_year(pv.get('displayTextShort', pv.get('displayTextLong', '')))
                    elif isinstance(pv, str):
                        year = _clean_year(pv)
                    if year:
                        break
        # Bilbasen/Nordic: details array [{displayText: "8/2020"}, {displayText: "75.000 km"}, ...]
        if not year or not km:
            details = item.get('details', [])
            if isinstance(details, list):
                for d in details:
                    dt = d.get('displayText', '') if isinstance(d, dict) else str(d)
                    if not year:
                        year = _clean_year(dt)
                    if not km and 'km' in dt.lower():
                        km = _clean_km(dt)

        # Year from title/name fallback (e.g., "BMW X3 Diesel (2020)")
        if not year and title:
            year = _clean_year(str(title))

        # Schema.org: vehicleModelDate or dateVehicleFirstRegistered
        if not year:
            for yk in ('vehicleModelDate', 'dateVehicleFirstRegistered', 'productionDate'):
                yr = item.get(yk, '')
                if yr:
                    year = _clean_year(str(yr))
                    if year:
                        break

        # KM — direct fields
        if not km:
            for kk in ('mileage', 'mileageInKm', 'km', 'odometer', 'kilometerstand'):
                kr = item.get(kk, '') or (vehicle.get(kk, '') if isinstance(vehicle, dict) else '')
                if kr:
                    km_val = _clean_km(str(kr))
                    if km_val:
                        km = km_val
                        break
        # Schema.org: mileageFromOdometer {value, unitCode}
        if not km:
            mfo = item.get('mileageFromOdometer', {})
            if isinstance(mfo, dict):
                km_val = mfo.get('value', '')
                if km_val:
                    km = _clean_km(str(km_val))
        # Willhaben: MILEAGE attribute
        if not km and 'MILEAGE' in wh_attrs:
            km = _clean_km(wh_attrs['MILEAGE'])
        # Marktplaats: mileage attribute
        if not km and 'mileage' in mp_attrs:
            km = _clean_km(str(mp_attrs['mileage']))
        # Bilbasen: properties.mileage
        if not km:
            props = item.get('properties', {})
            if isinstance(props, dict):
                mv = props.get('mileage', {})
                if isinstance(mv, dict):
                    km = _clean_km(mv.get('displayTextShort', mv.get('displayTextLong', '')))

        # Fuel
        fuel = FuelType.UNKNOWN
        for fk in ('fuel', 'fuelType', 'fuelCategory', 'powerTrain'):
            fr = item.get(fk, '') or (vehicle.get(fk, '') if isinstance(vehicle, dict) else '')
            if fr:
                fuel = _guess_fuel(str(fr))
                if fuel != FuelType.UNKNOWN:
                    break
        # Bilbasen: details array may have fuel info
        if fuel == FuelType.UNKNOWN:
            details = item.get('details', [])
            if isinstance(details, list):
                for d in details:
                    dt = d.get('displayText', '') if isinstance(d, dict) else str(d)
                    fuel = _guess_fuel(dt)
                    if fuel != FuelType.UNKNOWN:
                        break

        # Fuel — Willhaben attribute
        if fuel == FuelType.UNKNOWN and 'FUEL' in wh_attrs:
            fuel = _guess_fuel(wh_attrs['FUEL'])
        if fuel == FuelType.UNKNOWN and 'ENGINE/FUEL' in wh_attrs:
            fuel = _guess_fuel(wh_attrs['ENGINE/FUEL'])

        # Images
        images = []
        img_raw = item.get('images', item.get('imageUrls', item.get('image', item.get('photos', item.get('media', [])))))
        if isinstance(img_raw, list):
            for img in img_raw[:6]:
                if isinstance(img, str):
                    images.append(img)
                elif isinstance(img, dict):
                    for ik in ('url', 'src', 'uri', 'large', 'medium', 'original', 'selfLink'):
                        if ik in img:
                            images.append(img[ik])
                            break
        elif isinstance(img_raw, str) and img_raw:
            images.append(img_raw)
        # Willhaben: advertImageList.advertImage[{selfLink}]
        if not images:
            img_list = item.get('advertImageList', {})
            if isinstance(img_list, dict):
                for img in img_list.get('advertImage', [])[:6]:
                    if isinstance(img, dict) and 'selfLink' in img:
                        images.append(img['selfLink'])

        # Seller type (bilbasen: "Forhandler"=dealer, "Privat"=private)
        seller_type = SellerType.UNKNOWN
        seller_name = ""
        st_raw = item.get('sellerType', item.get('seller_type', ''))
        if isinstance(st_raw, str) and st_raw:
            stl = st_raw.lower()
            if any(w in stl for w in ('dealer', 'forhandler', 'handler', 'business', 'professionnel', 'händler')):
                seller_type = SellerType.DEALER
            elif any(w in stl for w in ('private', 'privat', 'particulier', 'privato')):
                seller_type = SellerType.PRIVATE
        seller_obj = item.get('seller', {})
        if isinstance(seller_obj, dict):
            seller_name = seller_obj.get('name', seller_obj.get('companyName', ''))
            if seller_type == SellerType.UNKNOWN:
                stype = seller_obj.get('type', seller_obj.get('__typename', ''))
                if 'dealer' in stype.lower() or 'business' in stype.lower():
                    seller_type = SellerType.DEALER
                elif 'private' in stype.lower():
                    seller_type = SellerType.PRIVATE

        # Location
        location = ""
        loc_obj = item.get('location', {})
        if isinstance(loc_obj, dict):
            city = loc_obj.get('city', loc_obj.get('cityName', ''))
            region = loc_obj.get('region', loc_obj.get('regionName', ''))
            location = f"{city}, {region}" if city and region else (city or region)

        # ID
        lid = str(item.get('id', item.get('externalId', item.get('itemId', item.get('adId', item.get('offerId', ''))))))
        if not lid:
            lid = self.generate_listing_id(self.portal_key, url or str(price))

        return Listing(
            listing_id=lid,
            portal=self.portal_key,
            country=country,
            make=str(item_make) or make,
            model=model,
            variant=str(variant)[:200] if variant else "",
            year=year or 0,
            km=km or 0,
            fuel_type=fuel,
            price_eur=price,
            currency_original=self.profile.currency,
            seller_type=seller_type,
            seller_name=seller_name,
            seller_location=location,
            listing_url=url,
            image_urls=images,
        )

    # ----- JSON-LD parsing -----

    def _parse_json_ld(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        listings = []
        pattern = re.compile(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL,
        )
        for match in pattern.finditer(html):
            try:
                data = json.loads(match.group(1))
            except (json.JSONDecodeError, ValueError):
                continue

            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if data.get("@type") in ("Car", "Vehicle", "Product", "Offer"):
                    items = [data]
                elif "itemListElement" in data:
                    items = [
                        el.get("item", el) for el in data.get("itemListElement", [])
                        if isinstance(el, dict)
                    ]
                # CollectionPage -> mainEntity -> itemListElement (Finn.no, Blocket)
                main_entity = data.get("mainEntity", {})
                if isinstance(main_entity, dict) and "itemListElement" in main_entity:
                    items = [
                        el.get("item", el) for el in main_entity.get("itemListElement", [])
                        if isinstance(el, dict)
                    ]

            for item in items:
                lst = self._json_item_to_listing(item, country, make, model)
                if lst:
                    listings.append(lst)

        return listings

    # ----- HTML regex parsing -----

    def _parse_html_regex(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """Parse listings using configured regex patterns."""
        listings = []

        if not self.profile.listing_block_re:
            return []

        block_re = re.compile(self.profile.listing_block_re, re.DOTALL | re.IGNORECASE)
        blocks = block_re.findall(html)

        for block in blocks[:50]:  # cap at 50 per page
            # Extract URL
            url = ""
            if self.profile.url_re:
                m = re.search(self.profile.url_re, block, re.IGNORECASE)
                if m:
                    url = m.group(1)
                    if url and url.startswith('//'):
                        url = f"https:{url}"
                    elif url and not url.startswith('http'):
                        url = f"{self.portal.base_url.rstrip('/')}{url}"

            # Extract price — find ALL prices and pick the LARGEST valid one
            # (handles sites that show both leasing rates and full prices)
            all_prices = []
            if self.profile.price_re:
                for m in re.finditer(self.profile.price_re, block, re.IGNORECASE):
                    p = _clean_price(m.group(1))
                    if p and p > 500:
                        all_prices.append(p)
            if not all_prices:
                for pat in PRICE_PATTERNS:
                    for m in re.finditer(pat, block, re.IGNORECASE):
                        p = _clean_price(m.group(1))
                        if p and p > 500:
                            all_prices.append(p)
                    if all_prices:
                        break

            price = max(all_prices) if all_prices else None
            if not price:
                continue  # Skip listings without price

            if self.profile.currency != "EUR":
                price = _to_eur(price, self.profile.currency)

            # Extract title
            title = ""
            if self.profile.title_re:
                m = re.search(self.profile.title_re, block, re.IGNORECASE)
                if m:
                    title = re.sub(r'<[^>]+>', '', m.group(1)).strip()

            # Extract image
            images = []
            if self.profile.image_re:
                m = re.search(self.profile.image_re, block, re.IGNORECASE)
                if m:
                    images.append(m.group(1))
            if not images:
                # Generic image extraction
                m = re.search(r'<img[^>]+src=["\']([^"\']+(?:jpg|jpeg|png|webp)[^"\']*)["\']', block, re.IGNORECASE)
                if m:
                    img = m.group(1)
                    if not img.startswith('http'):
                        img = f"{self.portal.base_url.rstrip('/')}{img}"
                    images.append(img)

            # Extract km
            km = None
            if self.profile.km_re:
                m = re.search(self.profile.km_re, block, re.IGNORECASE)
                if m:
                    km = _clean_km(m.group(1))
            if not km:
                for pat in KM_PATTERNS:
                    m = re.search(pat, block, re.IGNORECASE)
                    if m:
                        km = _clean_km(m.group(1))
                        if km:
                            break

            # Extract year
            year = None
            if self.profile.year_re:
                m = re.search(self.profile.year_re, block, re.IGNORECASE)
                if m:
                    year = _clean_year(m.group(0))
            if not year:
                for pat in YEAR_PATTERNS:
                    m = re.search(pat, block, re.IGNORECASE)
                    if m:
                        year = _clean_year(m.group(0))
                        if year:
                            break

            # Fuel
            fuel = _guess_fuel(block) if self.profile.fuel_re == "" else FuelType.UNKNOWN

            # Generate ID
            lid = self.generate_listing_id(self.portal_key, url or block[:100])

            listings.append(Listing(
                listing_id=lid,
                portal=self.portal_key,
                country=country,
                make=make,
                model=model,
                variant=title[:200] if title else "",
                year=year or 0,
                km=km or 0,
                fuel_type=fuel,
                price_eur=price,
                currency_original=self.profile.currency,
                listing_url=url,
                image_urls=images,
            ))

        return listings

    # ----- Aggressive fallback -----

    def _parse_aggressive(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """Last resort: find any links that look like vehicle listings with prices nearby."""
        listings = []
        seen_urls = set()

        # Find all links that might be vehicle detail pages
        link_patterns = [
            r'<a[^>]+href=["\']([^"\']*(?:detail|annonce|inserat|oglas|hirdet|anunt|annunci|ilmoitu|oglasen|obiava)[^"\']*)["\']',
            r'<a[^>]+href=["\']([^"\']*(?:auto|car|fahrzeug|voiture|veicol|vozilo|samochod|masina)[^"\']*)["\']',
            r'<a[^>]+href=["\']([^"\']*(?:/d/|/ad/|/listing/|/offer/|/vehicle/|/inzerat/|/skelbimas/)[^"\']*)["\']',
        ]

        for pat in link_patterns:
            for m in re.finditer(pat, html, re.IGNORECASE):
                url = m.group(1)
                if url in seen_urls:
                    continue
                # Filter junk URLs (carfax-proxy fees, API endpoints, etc.)
                if any(junk in url.lower() for junk in [
                    'carfax-proxy', '/api/', '/login', '/register',
                    '/cookie', '/consent', '/privacy',
                ]):
                    continue
                seen_urls.add(url)

                if url.startswith('//'):
                    url = f"https:{url}"
                elif not url.startswith('http'):
                    url = f"{self.portal.base_url.rstrip('/')}{url}"

                # Look at surrounding context (2000 chars before and after)
                start = max(0, m.start() - 2000)
                end = min(len(html), m.end() + 2000)
                context = html[start:end]

                # Find price in context
                price = None
                for ppat in PRICE_PATTERNS:
                    pm = re.search(ppat, context, re.IGNORECASE)
                    if pm:
                        price = _clean_price(pm.group(1))
                        if price and price > 500:
                            break
                        price = None

                if not price:
                    continue

                if self.profile.currency != "EUR":
                    price = _to_eur(price, self.profile.currency)

                # Year
                year = None
                for ypat in YEAR_PATTERNS:
                    ym = re.search(ypat, context)
                    if ym:
                        year = _clean_year(ym.group(0))
                        if year:
                            break

                # KM
                km = None
                for kpat in KM_PATTERNS:
                    km_m = re.search(kpat, context, re.IGNORECASE)
                    if km_m:
                        km = _clean_km(km_m.group(1))
                        if km:
                            break

                lid = self.generate_listing_id(self.portal_key, url)
                listings.append(Listing(
                    listing_id=lid,
                    portal=self.portal_key,
                    country=country,
                    make=make,
                    model=model,
                    year=year or 0,
                    km=km or 0,
                    fuel_type=_guess_fuel(context),
                    price_eur=price,
                    currency_original=self.profile.currency,
                    listing_url=url,
                ))

                if len(listings) >= 30:
                    break
            if len(listings) >= 30:
                break

        return listings
