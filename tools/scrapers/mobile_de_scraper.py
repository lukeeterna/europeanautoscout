"""
mobile_de_scraper.py -- ARGOS Market Intelligence: Mobile.de Scraper
CoVe 2026 | Enterprise Grade

Scraper per Mobile.de (secondo marketplace auto piu' grande d'Europa, solo Germania).
Anti-bot aggressivo: richiede curl_cffi con impersonate Chrome + rate limiting conservativo.

Usa ID numerici reali di Mobile.de per make/model.
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from .base_scraper import BaseScraper
from .models import Listing, FuelType, Transmission, SellerType
from .config import PORTALS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mobile.de ID Mappings (REALI)
# ---------------------------------------------------------------------------
# Formato: ms={make_id} oppure ms={make_id};{model_id}

MAKE_IDS: Dict[str, int] = {
    "BMW": 3500,
    "Mercedes-Benz": 17200,
    "Mercedes": 17200,
    "Audi": 1900,
    "Porsche": 20100,
    "Lamborghini": 15600,
    "Ferrari": 8600,
    "McLaren": 25100,
    "Land Rover": 15400,
    "Range Rover": 15400,
}

MODEL_IDS: Dict[str, Dict[str, int]] = {
    "BMW": {
        "Serie 1": 3501,
        "1er": 3501,
        "Serie 3": 3503,
        "3er": 3503,
        "Serie 5": 3505,
        "5er": 3505,
        "X1": 41,
        "X3": 11,
        "X5": 15,
        "M3": 10,
        "M4": 43,
    },
    "Mercedes-Benz": {
        "Classe A": 21,
        "A-Klasse": 21,
        "Classe C": 4,
        "C-Klasse": 4,
        "Classe E": 6,
        "E-Klasse": 6,
        "GLA": 47,
        "GLC": 48,
        "GLE": 49,
        "AMG GT": 44,
    },
    "Mercedes": {
        "Classe A": 21,
        "A-Klasse": 21,
        "Classe C": 4,
        "C-Klasse": 4,
        "Classe E": 6,
        "E-Klasse": 6,
        "GLA": 47,
        "GLC": 48,
        "GLE": 49,
        "AMG GT": 44,
    },
    "Audi": {
        "A3": 2,
        "A4": 3,
        "A5": 30,
        "A6": 5,
        "Q3": 38,
        "Q5": 27,
        "Q7": 14,
        "RS3": 36,
    },
    "Porsche": {
        "911": 3,
        "Cayenne": 11,
        "Macan": 17,
        "Panamera": 16,
        "Taycan": 22,
    },
    "Lamborghini": {
        "Urus": 10,
        "Huracan": 8,
        "Hurac\u00e1n": 8,
    },
    "Ferrari": {
        "Roma": 32,
        "F8": 31,
        "296": 33,
    },
    "McLaren": {
        "720S": 4,
        "GT": 6,
    },
    "Land Rover": {
        "Range Rover Sport": 10,
        "Sport": 10,
        "Range Rover Velar": 14,
        "Velar": 14,
        "Range Rover Evoque": 12,
        "Evoque": 12,
    },
    "Range Rover": {
        "Sport": 10,
        "Range Rover Sport": 10,
        "Velar": 14,
        "Range Rover Velar": 14,
        "Evoque": 12,
        "Range Rover Evoque": 12,
    },
}

# Mappatura fuel per parametro ft di Mobile.de
FUEL_MAP: Dict[str, List[str]] = {
    "diesel": ["DIESEL"],
    "petrol": ["GASOLINE"],
    "gasoline": ["GASOLINE"],
    "benzin": ["GASOLINE"],
    "hybrid": ["HYBRID"],
    "plugin_hybrid": ["PLUGIN_HYBRID"],
    "electric": ["ELECTRIC"],
    "elettrico": ["ELECTRIC"],
    "all": ["DIESEL", "GASOLINE"],
}

# Mappatura inversa fuel da testo tedesco in pagina
FUEL_TEXT_MAP: Dict[str, FuelType] = {
    "diesel": FuelType.DIESEL,
    "benzin": FuelType.PETROL,
    "super": FuelType.PETROL,
    "super plus": FuelType.PETROL,
    "hybrid": FuelType.HYBRID,
    "plug-in-hybrid": FuelType.PLUGIN_HYBRID,
    "plug-in hybrid": FuelType.PLUGIN_HYBRID,
    "elektro": FuelType.ELECTRIC,
    "elektrisch": FuelType.ELECTRIC,
    "autogas (lpg)": FuelType.LPG,
    "erdgas (cng)": FuelType.CNG,
}


class MobileDeScraper(BaseScraper):
    """
    Scraper per Mobile.de — il piu' grande marketplace auto tedesco.

    Caratteristiche:
    - URL search con parametri numerici (make/model ID)
    - Anti-bot aggressivo: curl_cffi obbligatorio, rate limit 10-25s
    - Parsing HTML con fallback JSON embedded
    - Max 8 pagine per ricerca
    """

    IMPERSONATE_BROWSER = "chrome120"

    SEARCH_BASE = "https://suchen.mobile.de/fahrzeuge/search.html"

    # Rate limit piu' conservativo di default per Mobile.de
    DEFAULT_RATE_MIN_S = 10.0
    DEFAULT_RATE_MAX_S = 25.0

    # Max pagine per singola ricerca
    MAX_PAGES_MOBILE = 8

    # Backoff specifici per Mobile.de
    BACKOFF_403_MIN_S = 60.0
    BACKOFF_403_MAX_S = 120.0
    BACKOFF_429_S = 300.0  # 5 minuti

    def __init__(self, **kwargs):
        super().__init__(
            portal_key="mobile_de",
            rate_limit_min_s=kwargs.pop("rate_limit_min_s", self.DEFAULT_RATE_MIN_S),
            rate_limit_max_s=kwargs.pop("rate_limit_max_s", self.DEFAULT_RATE_MAX_S),
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Override fetch per headers specifici Mobile.de
    # ------------------------------------------------------------------
    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
        """Fetch con headers specifici per Mobile.de e backoff aggressivo."""
        mobile_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.7,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.mobile.de/",
            "Cache-Control": "no-cache",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }
        if headers:
            mobile_headers.update(headers)

        return super().fetch(url, headers=mobile_headers)

    # ------------------------------------------------------------------
    # Override rate_limit_sleep per Mobile.de (piu' conservativo)
    # ------------------------------------------------------------------
    def rate_limit_sleep(self) -> None:
        """Sleep conservativo per Mobile.de: 10-25 secondi base."""
        if (
            self._request_count > 0
            and self._request_count % self.portal.burst_size == 0
        ):
            burst_sleep = self.portal.rate_limit_burst_pause_s + random.uniform(10, 30)
            logger.info(
                "[mobile.de] Burst pause dopo %d richieste — %.0fs",
                self._request_count, burst_sleep,
            )
            time.sleep(burst_sleep)
        else:
            sleep_s = random.uniform(self.rate_limit_min, self.rate_limit_max)
            logger.debug("[mobile.de] Rate limit sleep: %.1fs", sleep_s)
            time.sleep(sleep_s)

    # ------------------------------------------------------------------
    # URL BUILDER
    # ------------------------------------------------------------------
    def build_search_url(
        self,
        make: str,
        model: str,
        page: int = 1,
        **kwargs,
    ) -> str:
        """
        Costruisce URL di ricerca Mobile.de.

        Parametri kwargs accettati:
            year_min, year_max, km_max, fuel, sort
        """
        year_min: int = kwargs.get("year_min", 0)
        year_max: int = kwargs.get("year_max", 0)
        km_max: int = kwargs.get("km_max", 0)
        fuel: Optional[str] = kwargs.get("fuel", None)
        sort: str = kwargs.get("sort", "newest")

        # Costruisci il parametro ms (make;model)
        ms_value = self._resolve_ms(make, model)

        # Parametri base
        params: List[Tuple[str, str]] = [
            ("isSearchRequest", "true"),
            ("ms", ms_value),
            ("damageUnrepaired", "NO_DAMAGE_UNREPAIRED"),
            ("scopeId", "C"),
        ]

        # Anno
        if year_min > 0:
            params.append(("fr", f"{year_min}:"))
        if year_max > 0:
            params.append(("to", f"{year_max}:"))

        # Chilometraggio massimo
        if km_max > 0:
            params.append(("ml", f":{km_max}"))

        # Fuel type
        if fuel:
            fuel_lower = fuel.lower().strip()
            fuel_codes = FUEL_MAP.get(fuel_lower, [])
            for fc in fuel_codes:
                params.append(("ft", fc))

        # Ordinamento
        params.append(("s", "Car"))
        if sort == "newest":
            params.append(("sb", "doc"))
            params.append(("sd", "d"))
        elif sort == "cheapest":
            params.append(("sb", "p"))
            params.append(("sd", "a"))
        elif sort == "expensive":
            params.append(("sb", "p"))
            params.append(("sd", "d"))
        elif sort == "km_asc":
            params.append(("sb", "m"))
            params.append(("sd", "a"))
        else:
            # Default: newest
            params.append(("sb", "doc"))
            params.append(("sd", "d"))

        # Pagina
        if page > 1:
            params.append(("pageNumber", str(page)))

        # Costruisci URL
        query_string = urlencode(params)
        url = f"{self.SEARCH_BASE}?{query_string}"
        return url

    def _resolve_ms(self, make: str, model: str) -> str:
        """
        Risolve il parametro ms= per Mobile.de.

        Prova prima il nome esatto, poi varianti comuni.
        Se il modello non e' mappato, usa solo il make ID.
        """
        # Trova make ID
        make_id = MAKE_IDS.get(make)
        if make_id is None:
            # Prova case-insensitive
            for k, v in MAKE_IDS.items():
                if k.lower() == make.lower():
                    make_id = v
                    break
        if make_id is None:
            logger.warning(
                "[mobile.de] Make non mappato: '%s' — usa ricerca testuale",
                make,
            )
            return str(make)

        # Trova model ID
        model_ids = MODEL_IDS.get(make, {})
        if not model_ids:
            # Cerca con case-insensitive su chiave primaria
            for k, v in MODEL_IDS.items():
                if k.lower() == make.lower():
                    model_ids = v
                    break

        model_id = model_ids.get(model) if model_ids else None
        if model_id is None and model_ids:
            # Prova case-insensitive
            for k, v in model_ids.items():
                if k.lower() == model.lower():
                    model_id = v
                    break

        if model_id is not None:
            return f"{make_id};{model_id}"
        else:
            logger.warning(
                "[mobile.de] Modello non mappato: '%s' '%s' — solo make ID",
                make, model,
            )
            return str(make_id)

    # ------------------------------------------------------------------
    # PARSING
    # ------------------------------------------------------------------
    def parse_listings(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """
        Parsa la pagina risultati Mobile.de ed estrae i listing.

        Strategia multi-layer:
        1. Cerca JSON embedded (__NEXT_DATA__, carcutter, window.__INITIAL_STATE__)
        2. Fallback: parsing regex su HTML
        """
        listings: List[Listing] = []

        # ------ Strategia 1: JSON embedded ------
        json_listings = self._try_parse_json_embedded(html)
        if json_listings:
            for jl in json_listings:
                listing = self._json_to_listing(jl, country, make, model)
                if listing is not None:
                    listings.append(listing)
            if listings:
                logger.debug(
                    "[mobile.de] Parsed %d listings via JSON embedded", len(listings)
                )
                return listings

        # ------ Strategia 2: Regex su HTML ------
        listings = self._parse_html_regex(html, country, make, model)
        if listings:
            logger.debug(
                "[mobile.de] Parsed %d listings via HTML regex", len(listings)
            )
        else:
            logger.warning(
                "[mobile.de] Zero listings parsed per %s %s — pagina potrebbe "
                "essere vuota o struttura cambiata",
                make, model,
            )

        return listings

    def _try_parse_json_embedded(self, html: str) -> List[dict]:
        """Prova a estrarre listing da JSON embedded nella pagina."""
        results: List[dict] = []

        # Pattern 1: __NEXT_DATA__
        m = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*({.+?})\s*</script>',
            html,
            re.DOTALL,
        )
        if m:
            try:
                data = json.loads(m.group(1))
                # Naviga la struttura __NEXT_DATA__ per estrarre i risultati
                search_results = self._extract_from_next_data(data)
                if search_results:
                    return search_results
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug("[mobile.de] __NEXT_DATA__ parse failed: %s", e)

        # Pattern 2: window.__INITIAL_STATE__
        m = re.search(
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});\s*</script>',
            html,
            re.DOTALL,
        )
        if m:
            try:
                data = json.loads(m.group(1))
                search_results = self._extract_from_initial_state(data)
                if search_results:
                    return search_results
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug("[mobile.de] __INITIAL_STATE__ parse failed: %s", e)

        # Pattern 3: JSON-LD
        for m in re.finditer(
            r'<script\s+type="application/ld\+json">\s*({.+?})\s*</script>',
            html,
            re.DOTALL,
        ):
            try:
                data = json.loads(m.group(1))
                if data.get("@type") == "ItemList" and "itemListElement" in data:
                    for item in data["itemListElement"]:
                        if "item" in item:
                            results.append(item["item"])
                        elif "@type" in item and item["@type"] in ("Car", "Vehicle", "Product"):
                            results.append(item)
            except (json.JSONDecodeError, KeyError):
                continue

        return results

    def _extract_from_next_data(self, data: dict) -> List[dict]:
        """Estrae listing dalla struttura __NEXT_DATA__."""
        results = []
        # Naviga props > pageProps > searchResult > ads
        try:
            page_props = data.get("props", {}).get("pageProps", {})
            # Prova vari percorsi
            for key in ("searchResult", "searchResults", "data", "result"):
                sr = page_props.get(key, {})
                if isinstance(sr, dict):
                    for ads_key in ("ads", "items", "results", "listings"):
                        ads = sr.get(ads_key, [])
                        if isinstance(ads, list) and ads:
                            return ads
            # Prova un livello piu' profondo
            for val in page_props.values():
                if isinstance(val, dict):
                    for ads_key in ("ads", "items", "results", "listings"):
                        ads = val.get(ads_key, [])
                        if isinstance(ads, list) and len(ads) > 2:
                            return ads
        except (AttributeError, TypeError):
            pass
        return results

    def _extract_from_initial_state(self, data: dict) -> List[dict]:
        """Estrae listing da window.__INITIAL_STATE__."""
        results = []
        try:
            # Mobile.de potrebbe avere struttura search > results > data
            for key in ("search", "searchResults", "results"):
                section = data.get(key, {})
                if isinstance(section, dict):
                    for ads_key in ("ads", "items", "data", "listings"):
                        ads = section.get(ads_key, [])
                        if isinstance(ads, list) and ads:
                            return ads
        except (AttributeError, TypeError):
            pass
        return results

    def _json_to_listing(
        self, jl: dict, country: str, make: str, model: str
    ) -> Optional[Listing]:
        """Converte un oggetto JSON listing in un Listing dataclass."""
        try:
            # Estrai ID
            listing_id_raw = (
                jl.get("id")
                or jl.get("adId")
                or jl.get("offerId")
                or ""
            )
            listing_id = str(listing_id_raw)
            if not listing_id:
                return None

            # URL
            url = jl.get("url", "") or jl.get("detailUrl", "") or jl.get("pdpUrl", "")
            if url and not url.startswith("http"):
                url = f"https://suchen.mobile.de{url}"

            # Titolo
            title = jl.get("title", "") or jl.get("headline", "") or f"{make} {model}"

            # Prezzo
            price_eur = self._extract_price_from_json(jl)

            # Km
            km = self._extract_km_from_json(jl)

            # Anno
            year = self._extract_year_from_json(jl)

            # Fuel
            fuel_type = self._extract_fuel_from_json(jl)

            # Transmission
            transmission = self._extract_transmission_from_json(jl)

            # Power
            power_hp = self._extract_power_from_json(jl)

            # Seller
            seller_name, seller_location, seller_type = self._extract_seller_from_json(jl)

            # Variant (sottotitolo o sub-headline)
            variant = jl.get("subTitle", "") or jl.get("subHeadline", "") or ""

            # Immagini
            image_urls: List[str] = []
            img = jl.get("image", {})
            if isinstance(img, dict) and img.get("src"):
                image_urls.append(img["src"])
            elif isinstance(img, str) and img:
                image_urls.append(img)
            imgs = jl.get("images", [])
            if isinstance(imgs, list):
                for i in imgs[:5]:
                    src = i.get("src", "") if isinstance(i, dict) else str(i)
                    if src and src not in image_urls:
                        image_urls.append(src)

            return Listing(
                listing_id=f"mobile_de_{listing_id}",
                portal="mobile_de",
                country=country,
                make=make,
                model=model,
                variant=variant,
                year=year,
                km=km,
                fuel_type=fuel_type,
                transmission=transmission,
                power_hp=power_hp,
                price_eur=float(price_eur) if price_eur else 0.0,
                currency_original="EUR",
                seller_type=seller_type,
                seller_name=seller_name,
                seller_location=seller_location,
                listing_url=url,
                image_urls=image_urls,
            )

        except Exception as e:
            logger.warning("[mobile.de] Failed to parse JSON listing: %s", e)
            return None

    def _extract_price_from_json(self, jl: dict) -> int:
        """Estrae prezzo da un oggetto JSON listing."""
        # Prova campi diretti
        for key in ("price", "priceGross", "grossPrice", "priceRaw"):
            val = jl.get(key)
            if isinstance(val, (int, float)) and val > 0:
                return int(val)
            if isinstance(val, str):
                cleaned = self._clean_price_string(val)
                if cleaned > 0:
                    return cleaned

        # Prova oggetto price nested
        price_obj = jl.get("price", {})
        if isinstance(price_obj, dict):
            for key in ("amount", "value", "gross", "grossPrice"):
                val = price_obj.get(key)
                if isinstance(val, (int, float)) and val > 0:
                    return int(val)
                if isinstance(val, str):
                    cleaned = self._clean_price_string(val)
                    if cleaned > 0:
                        return cleaned

        # Prova nel testo formattato
        price_text = jl.get("priceFormatted", "") or jl.get("priceLabel", "")
        if price_text:
            cleaned = self._clean_price_string(price_text)
            if cleaned > 0:
                return cleaned

        return 0

    def _extract_km_from_json(self, jl: dict) -> int:
        """Estrae chilometraggio da un oggetto JSON listing."""
        for key in ("mileage", "km", "mileageKm"):
            val = jl.get(key)
            if isinstance(val, (int, float)) and val > 0:
                return int(val)
            if isinstance(val, str):
                cleaned = self._clean_number_string(val)
                if cleaned > 0:
                    return cleaned

        # Nested
        attrs = jl.get("attributes", {})
        if isinstance(attrs, dict):
            for key in ("mileage", "km"):
                val = attrs.get(key)
                if isinstance(val, (int, float)) and val > 0:
                    return int(val)
                if isinstance(val, str):
                    cleaned = self._clean_number_string(val)
                    if cleaned > 0:
                        return cleaned

        # Lista attributi
        if isinstance(attrs, list):
            for attr in attrs:
                if isinstance(attr, str) and "km" in attr.lower():
                    cleaned = self._clean_number_string(attr)
                    if cleaned > 0:
                        return cleaned

        return 0

    def _extract_year_from_json(self, jl: dict) -> int:
        """Estrae anno immatricolazione da JSON listing."""
        for key in ("year", "firstRegistration", "registrationDate", "ez"):
            val = jl.get(key)
            if isinstance(val, int) and 1990 < val < 2030:
                return val
            if isinstance(val, str):
                # Pattern MM/YYYY o YYYY
                ym = re.search(r'(\d{4})', val)
                if ym:
                    y = int(ym.group(1))
                    if 1990 < y < 2030:
                        return y

        # Nested attributes
        attrs = jl.get("attributes", {})
        if isinstance(attrs, dict):
            for key in ("firstRegistration", "year", "ez"):
                val = attrs.get(key)
                if isinstance(val, int) and 1990 < val < 2030:
                    return val
                if isinstance(val, str):
                    ym = re.search(r'(\d{4})', val)
                    if ym:
                        y = int(ym.group(1))
                        if 1990 < y < 2030:
                            return y

        return 0

    def _extract_fuel_from_json(self, jl: dict) -> FuelType:
        """Estrae tipo carburante da JSON listing."""
        for key in ("fuel", "fuelType", "fuelCategory"):
            val = jl.get(key)
            if isinstance(val, str):
                ft = self._map_fuel_text(val)
                if ft != FuelType.UNKNOWN:
                    return ft

        attrs = jl.get("attributes", {})
        if isinstance(attrs, dict):
            for key in ("fuel", "fuelType"):
                val = attrs.get(key)
                if isinstance(val, str):
                    ft = self._map_fuel_text(val)
                    if ft != FuelType.UNKNOWN:
                        return ft

        if isinstance(attrs, list):
            for attr in attrs:
                if isinstance(attr, str):
                    ft = self._map_fuel_text(attr)
                    if ft != FuelType.UNKNOWN:
                        return ft

        return FuelType.UNKNOWN

    def _extract_transmission_from_json(self, jl: dict) -> Transmission:
        """Estrae tipo trasmissione da JSON listing."""
        for key in ("transmission", "gearbox", "gearboxType"):
            val = jl.get(key)
            if isinstance(val, str):
                return self._map_transmission_text(val)

        attrs = jl.get("attributes", {})
        if isinstance(attrs, dict):
            for key in ("transmission", "gearbox"):
                val = attrs.get(key)
                if isinstance(val, str):
                    return self._map_transmission_text(val)

        return Transmission.UNKNOWN

    def _extract_power_from_json(self, jl: dict) -> int:
        """Estrae potenza in HP da JSON listing."""
        for key in ("powerHp", "power", "hp", "ps"):
            val = jl.get(key)
            if isinstance(val, (int, float)) and val > 0:
                return int(val)

        # Prova powerKw e converti
        for key in ("powerKw", "kw"):
            val = jl.get(key)
            if isinstance(val, (int, float)) and val > 0:
                return int(val * 1.36)  # 1 kW = 1.36 PS

        attrs = jl.get("attributes", {})
        if isinstance(attrs, dict):
            for key in ("power", "powerHp", "ps"):
                val = attrs.get(key)
                if isinstance(val, (int, float)) and val > 0:
                    return int(val)
                if isinstance(val, str):
                    # Pattern "150 PS" o "110 kW (150 PS)"
                    pm = re.search(r'(\d+)\s*(?:PS|hp|CV)', val, re.IGNORECASE)
                    if pm:
                        return int(pm.group(1))
                    pm = re.search(r'(\d+)\s*kW', val, re.IGNORECASE)
                    if pm:
                        return int(int(pm.group(1)) * 1.36)

        return 0

    def _extract_seller_from_json(self, jl: dict) -> Tuple[str, str, SellerType]:
        """Estrae info venditore da JSON listing."""
        seller_name = ""
        seller_location = ""
        seller_type = SellerType.UNKNOWN

        seller = jl.get("seller", {})
        if isinstance(seller, dict):
            seller_name = seller.get("name", "") or seller.get("companyName", "")
            seller_location = seller.get("location", "") or seller.get("city", "")
            s_type = seller.get("type", "").lower()
            if s_type in ("dealer", "haendler", "commercial"):
                seller_type = SellerType.DEALER
            elif s_type in ("private", "privat"):
                seller_type = SellerType.PRIVATE

        if not seller_name:
            seller_name = jl.get("sellerName", "") or jl.get("dealerName", "")
        if not seller_location:
            seller_location = jl.get("location", "") or jl.get("city", "")

        # Se ha dealer name, assume dealer
        if seller_name and seller_type == SellerType.UNKNOWN:
            seller_type = SellerType.DEALER

        return seller_name, seller_location, seller_type

    # ------------------------------------------------------------------
    # HTML Regex parsing (fallback)
    # ------------------------------------------------------------------
    def _parse_html_regex(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """
        Parsing fallback via regex su HTML.
        Mobile.de usa classi CSS variabili, quindi cerchiamo pattern strutturali.
        """
        listings: List[Listing] = []

        # Cerca blocchi listing: pattern su link a dettaglio annuncio
        # Mobile.de listing links: /fahrzeuge/details.html?id=XXXXXXX
        listing_blocks = re.findall(
            r'<a[^>]+href="(/fahrzeuge/details\.html\?id=(\d+)[^"]*)"[^>]*>'
            r'(.*?)</a>',
            html,
            re.DOTALL,
        )

        # Dedup per ID (stesso listing puo' apparire piu' volte nella pagina)
        seen_ids: set = set()

        for href, listing_id_raw, block_html in listing_blocks:
            if listing_id_raw in seen_ids:
                continue
            seen_ids.add(listing_id_raw)

            url = f"https://suchen.mobile.de{href}"
            listing = self._parse_single_html_block(
                listing_id_raw, url, block_html, html, country, make, model
            )
            if listing is not None:
                listings.append(listing)

        # Se il pattern sopra non funziona, prova pattern alternativo
        if not listings:
            listings = self._parse_html_alternative(html, country, make, model)

        return listings

    def _parse_single_html_block(
        self,
        listing_id_raw: str,
        url: str,
        block_html: str,
        full_html: str,
        country: str,
        make: str,
        model: str,
    ) -> Optional[Listing]:
        """Parsa un singolo blocco listing dall'HTML."""
        try:
            # Cerca il contesto piu' ampio intorno a questo listing
            # Trova la sezione che contiene questo ID
            context_match = re.search(
                rf'(?:class="[^"]*(?:result-item|listing|cBox)[^"]*"[^>]*>)'
                rf'(.*?href="/fahrzeuge/details\.html\?id={re.escape(listing_id_raw)}.*?)'
                rf'(?:</(?:div|article|section)>\s*<(?:div|article|section))',
                full_html,
                re.DOTALL,
            )
            context = context_match.group(1) if context_match else block_html

            # Prova anche un contesto piu' ampio: 3000 caratteri intorno al link
            idx = full_html.find(f"id={listing_id_raw}")
            if idx > 0:
                wide_context = full_html[max(0, idx - 1500):idx + 1500]
            else:
                wide_context = context

            # Prezzo: pattern "XX.XXX EUR" o "EUR XX.XXX" o "XX.XXX"
            price = self._extract_price_from_text(wide_context)

            # Km: pattern "XX.XXX km"
            km = self._extract_km_from_text(wide_context)

            # Anno: pattern "EZ MM/YYYY" o "MM/YYYY"
            year = self._extract_year_from_text(wide_context)

            # Fuel
            fuel_type = self._extract_fuel_from_text(wide_context)

            # Transmission
            transmission = self._extract_transmission_from_text(wide_context)

            # Power: pattern "XXX PS" o "XXX kW"
            power_hp = self._extract_power_from_text(wide_context)

            # Titolo: primo testo significativo nel blocco
            title_match = re.search(r'<(?:h2|h3|span)[^>]*class="[^"]*(?:title|headline)[^"]*"[^>]*>([^<]+)</(?:h2|h3|span)>', wide_context)
            title = title_match.group(1).strip() if title_match else f"{make} {model}"

            # Seller info
            seller_name = ""
            seller_location = ""
            seller_match = re.search(r'<(?:span|div)[^>]*class="[^"]*(?:seller|dealer)[^"]*"[^>]*>([^<]+)', wide_context)
            if seller_match:
                seller_name = seller_match.group(1).strip()
            loc_match = re.search(r'<(?:span|div)[^>]*class="[^"]*(?:location|city|address)[^"]*"[^>]*>([^<]+)', wide_context)
            if loc_match:
                seller_location = loc_match.group(1).strip()

            # Immagine
            image_urls: List[str] = []
            img_match = re.search(r'<img[^>]+src="(https?://[^"]+mobile\.de[^"]*)"', wide_context)
            if img_match:
                image_urls.append(img_match.group(1))
            else:
                img_match = re.search(r'<img[^>]+data-src="(https?://[^"]+)"', wide_context)
                if img_match:
                    image_urls.append(img_match.group(1))

            # Se non abbiamo ne' prezzo ne' km, il blocco probabilmente non e' un listing
            if price == 0 and km == 0 and year == 0:
                return None

            return Listing(
                listing_id=f"mobile_de_{listing_id_raw}",
                portal="mobile_de",
                country=country,
                make=make,
                model=model,
                variant="",
                year=year,
                km=km,
                fuel_type=fuel_type,
                transmission=transmission,
                power_hp=power_hp,
                price_eur=float(price) if price else 0.0,
                currency_original="EUR",
                seller_type=SellerType.DEALER if seller_name else SellerType.UNKNOWN,
                seller_name=seller_name,
                seller_location=seller_location,
                listing_url=url,
                image_urls=image_urls,
            )

        except Exception as e:
            logger.warning(
                "[mobile.de] Failed to parse HTML block for ID %s: %s",
                listing_id_raw, e,
            )
            return None

    def _parse_html_alternative(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """
        Parsing alternativo: cerca pattern data-* attributes o strutture div
        usate da Mobile.de per i risultati di ricerca.
        """
        listings: List[Listing] = []
        seen_ids: set = set()

        # Pattern: data-ad-id="XXXXXXX" o data-listing-id="XXXXXXX"
        for m in re.finditer(
            r'data-(?:ad-id|listing-id|testid="result-listing-)\s*[=:]\s*"?(\d{5,12})"?',
            html,
        ):
            ad_id = m.group(1)
            if ad_id in seen_ids:
                continue
            seen_ids.add(ad_id)

            # Estrai contesto: 2000 caratteri dopo il match
            start = max(0, m.start() - 500)
            end = min(len(html), m.end() + 2000)
            context = html[start:end]

            url = f"https://suchen.mobile.de/fahrzeuge/details.html?id={ad_id}"
            price = self._extract_price_from_text(context)
            km = self._extract_km_from_text(context)
            year = self._extract_year_from_text(context)
            fuel_type = self._extract_fuel_from_text(context)
            power_hp = self._extract_power_from_text(context)

            if price == 0 and km == 0 and year == 0:
                continue

            listings.append(Listing(
                listing_id=f"mobile_de_{ad_id}",
                portal="mobile_de",
                country=country,
                make=make,
                model=model,
                year=year,
                km=km,
                fuel_type=fuel_type,
                power_hp=power_hp,
                price_eur=float(price) if price else 0.0,
                currency_original="EUR",
                listing_url=url,
            ))

        return listings

    # ------------------------------------------------------------------
    # Text extraction helpers
    # ------------------------------------------------------------------
    def _extract_price_from_text(self, text: str) -> int:
        """Estrae prezzo da testo HTML. Pattern Mobile.de: 'EUR 27.800' o '27.800 EUR'."""
        # Pattern 1: EUR XX.XXX o XX.XXX EUR
        patterns = [
            r'EUR\s*(\d{1,3}(?:\.\d{3})+)',            # EUR 27.800
            r'(\d{1,3}(?:\.\d{3})+)\s*(?:EUR|\u20ac)',  # 27.800 EUR o 27.800 euro sign
            r'\u20ac\s*(\d{1,3}(?:\.\d{3})+)',           # euro sign 27.800
            r'"price"[:\s]*"?(\d[\d.]+)"?',              # JSON-like "price": "27800"
            r'(\d{1,3}(?:\.\d{3})+)\s*,-',               # 27.800,- (formato tedesco)
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                cleaned = self._clean_price_string(m.group(1))
                if 500 < cleaned < 1_000_000:
                    return cleaned

        # Fallback: cerca qualsiasi numero grande che potrebbe essere un prezzo
        m = re.search(r'(\d{2,3}\.\d{3})', text)
        if m:
            cleaned = self._clean_price_string(m.group(1))
            if 1_000 < cleaned < 500_000:
                return cleaned

        return 0

    def _extract_km_from_text(self, text: str) -> int:
        """Estrae chilometraggio da testo. Pattern: 'XX.XXX km'."""
        patterns = [
            r'(\d{1,3}(?:\.\d{3})+)\s*km',              # 45.000 km
            r'(\d{4,6})\s*km',                           # 45000 km (senza punto)
            r'"mileage"[:\s]*"?(\d[\d.]+)"?',            # JSON-like
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                cleaned = self._clean_number_string(m.group(1))
                if 0 < cleaned < 1_000_000:
                    return cleaned
        return 0

    def _extract_year_from_text(self, text: str) -> int:
        """Estrae anno immatricolazione. Pattern: 'EZ MM/YYYY' o 'MM/YYYY'."""
        patterns = [
            r'EZ\s*(\d{2})/(\d{4})',                     # EZ 03/2021
            r'Erstzulassung\s*(\d{2})/(\d{4})',          # Erstzulassung 03/2021
            r'(\d{2})/(\d{4})',                           # 03/2021
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                year = int(m.group(2)) if len(m.groups()) >= 2 else int(m.group(1))
                if 1990 < year < 2030:
                    return year

        # Fallback: anno isolato
        m = re.search(r'\b(20[12]\d)\b', text)
        if m:
            return int(m.group(1))

        return 0

    def _extract_fuel_from_text(self, text: str) -> FuelType:
        """Estrae tipo carburante da testo tedesco."""
        text_lower = text.lower()
        for keyword, fuel_type in FUEL_TEXT_MAP.items():
            if keyword in text_lower:
                return fuel_type
        return FuelType.UNKNOWN

    def _extract_transmission_from_text(self, text: str) -> Transmission:
        """Estrae tipo trasmissione da testo tedesco."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ("automatik", "automatic", "dsg", "tiptronic", "s-tronic", "dct", "pdk")):
            return Transmission.AUTOMATIC
        if any(kw in text_lower for kw in ("schaltgetriebe", "manuell", "manual")):
            return Transmission.MANUAL
        return Transmission.UNKNOWN

    def _extract_power_from_text(self, text: str) -> int:
        """Estrae potenza in HP da testo. Pattern: 'XXX PS' o 'XXX kW (YYY PS)'."""
        # PS diretto
        m = re.search(r'(\d{2,4})\s*PS', text)
        if m:
            return int(m.group(1))

        # kW con conversione
        m = re.search(r'(\d{2,4})\s*kW', text)
        if m:
            return int(int(m.group(1)) * 1.36)

        # HP/CV
        m = re.search(r'(\d{2,4})\s*(?:hp|CV)', text, re.IGNORECASE)
        if m:
            return int(m.group(1))

        return 0

    # ------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------
    def has_next_page(self, html: str, current_page: int) -> bool:
        """
        Verifica se esiste una pagina successiva.
        Rispetta il limite MAX_PAGES_MOBILE (8 pagine).
        """
        if current_page >= self.MAX_PAGES_MOBILE:
            logger.info(
                "[mobile.de] Raggiunto limite max pagine (%d)",
                self.MAX_PAGES_MOBILE,
            )
            return False

        # Cerca link alla pagina successiva
        next_page = current_page + 1

        # Pattern 1: pageNumber=N nel link
        if f"pageNumber={next_page}" in html:
            return True

        # Pattern 2: aria-label o class con "next"
        if re.search(
            r'(?:aria-label|class)\s*=\s*"[^"]*(?:next|weiter|nachste)[^"]*"',
            html,
            re.IGNORECASE,
        ):
            return True

        # Pattern 3: pagination con numero pagina successivo
        if re.search(
            rf'<(?:a|button|li)[^>]*>\s*{next_page}\s*</(?:a|button|li)>',
            html,
        ):
            return True

        return False

    # ------------------------------------------------------------------
    # Override scrape per cap a 8 pagine
    # ------------------------------------------------------------------
    def scrape(
        self,
        make: str,
        model: str,
        max_pages: Optional[int] = None,
        **search_kwargs,
    ) -> Tuple[List[Listing], ...]:
        """Scrape con cap a 8 pagine per Mobile.de."""
        effective_max = min(
            max_pages or self.MAX_PAGES_MOBILE,
            self.MAX_PAGES_MOBILE,
        )
        return super().scrape(make, model, max_pages=effective_max, **search_kwargs)

    # ------------------------------------------------------------------
    # Utility statiche
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_price_string(s: str) -> int:
        """Pulisce una stringa prezzo tedesca e ritorna intero."""
        # Rimuovi tutto tranne cifre (il '.' tedesco e' separatore migliaia)
        cleaned = re.sub(r'[^\d]', '', s)
        try:
            val = int(cleaned)
            return val
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _clean_number_string(s: str) -> int:
        """Pulisce una stringa numerica tedesca e ritorna intero."""
        cleaned = re.sub(r'[^\d]', '', s)
        try:
            return int(cleaned)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _map_fuel_text(text: str) -> FuelType:
        """Mappa testo carburante (DE/EN) a FuelType enum."""
        text_lower = text.lower().strip()
        for keyword, ft in FUEL_TEXT_MAP.items():
            if keyword in text_lower:
                return ft
        # Mappatura codici Mobile.de
        code_map = {
            "diesel": FuelType.DIESEL,
            "gasoline": FuelType.PETROL,
            "petrol": FuelType.PETROL,
            "hybrid": FuelType.HYBRID,
            "plugin_hybrid": FuelType.PLUGIN_HYBRID,
            "electric": FuelType.ELECTRIC,
            "lpg": FuelType.LPG,
            "cng": FuelType.CNG,
        }
        return code_map.get(text_lower, FuelType.UNKNOWN)

    @staticmethod
    def _map_transmission_text(text: str) -> Transmission:
        """Mappa testo trasmissione a Transmission enum."""
        text_lower = text.lower().strip()
        auto_kw = ("automatic", "automatik", "dsg", "tiptronic", "s-tronic", "dct", "pdk", "cvt")
        manual_kw = ("manual", "manuell", "schaltgetriebe")
        if any(kw in text_lower for kw in auto_kw):
            return Transmission.AUTOMATIC
        if any(kw in text_lower for kw in manual_kw):
            return Transmission.MANUAL
        return Transmission.UNKNOWN

    # ------------------------------------------------------------------
    # Convenience: ricerca rapida
    # ------------------------------------------------------------------
    def search_quick(
        self,
        make: str,
        model: str,
        year_min: int = 2018,
        year_max: int = 2025,
        km_max: int = 80_000,
        fuel: Optional[str] = None,
        max_pages: int = 3,
    ) -> List[Listing]:
        """
        Ricerca rapida con parametri ARGOS standard.
        Ritorna solo la lista di listing (senza ScraperRun).
        """
        listings, run = self.scrape(
            make=make,
            model=model,
            max_pages=max_pages,
            year_min=year_min,
            year_max=year_max,
            km_max=km_max,
            fuel=fuel,
            sort="newest",
        )
        return listings

    @classmethod
    def supported_makes(cls) -> List[str]:
        """Ritorna lista dei make supportati con ID Mobile.de."""
        return list(MAKE_IDS.keys())

    @classmethod
    def supported_models(cls, make: str) -> List[str]:
        """Ritorna lista dei modelli supportati per un make."""
        models = MODEL_IDS.get(make, {})
        if not models:
            for k, v in MODEL_IDS.items():
                if k.lower() == make.lower():
                    return list(v.keys())
        return list(models.keys())

    @classmethod
    def get_ms_param(cls, make: str, model: Optional[str] = None) -> Optional[str]:
        """Ritorna il parametro ms= per un make/model, o None se non mappato."""
        make_id = MAKE_IDS.get(make)
        if make_id is None:
            return None
        if model is None:
            return str(make_id)
        model_ids = MODEL_IDS.get(make, {})
        model_id = model_ids.get(model)
        if model_id is None:
            return str(make_id)
        return f"{make_id};{model_id}"


# ---------------------------------------------------------------------------
# STANDALONE TEST
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    print("=" * 60)
    print("ARGOS Automotive — Mobile.de Scraper Test")
    print("=" * 60)

    scraper = MobileDeScraper()

    # Test URL builder
    print("\n--- URL Builder Test ---")
    test_cases = [
        ("BMW", "Serie 3", {"year_min": 2020, "km_max": 60000, "fuel": "diesel"}),
        ("Mercedes-Benz", "GLC", {"year_min": 2019, "sort": "cheapest"}),
        ("Audi", "Q5", {"year_min": 2018, "year_max": 2023, "km_max": 80000}),
        ("Porsche", "911", {"fuel": "petrol", "sort": "newest"}),
        ("Lamborghini", "Urus", {}),
    ]

    for make, model, kwargs in test_cases:
        url = scraper.build_search_url(make, model, page=1, **kwargs)
        print(f"  {make} {model}: {url}")

    # Test ms= resolution
    print("\n--- MS Parameter Test ---")
    ms_tests = [
        ("BMW", "X3"),
        ("Mercedes-Benz", "Classe C"),
        ("Audi", "RS3"),
        ("Porsche", "Taycan"),
        ("Ferrari", "Roma"),
        ("Land Rover", "Range Rover Sport"),
    ]
    for make, model in ms_tests:
        ms = MobileDeScraper.get_ms_param(make, model)
        print(f"  {make} {model} -> ms={ms}")

    print("\n--- Supported Makes ---")
    print(f"  {MobileDeScraper.supported_makes()}")

    print("\n--- Supported BMW Models ---")
    print(f"  {MobileDeScraper.supported_models('BMW')}")

    print("\nDone. Per scraping reale: scraper.scrape('BMW', 'Serie 3', year_min=2020)")
