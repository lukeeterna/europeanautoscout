"""
autoscout_scraper.py -- ARGOS AutoScout24 Multi-Country Scraper
CoVe 2026 | Enterprise Grade

Scraper production-grade per AutoScout24 su tutti i mercati EU target:
DE, NL, BE, AT, FR, SE, IT.

Parsing: JSON-LD preferenziale, fallback HTML card regex.
Anti-bot: curl_cffi impersonate chrome120 + Accept-Language per paese.
Rate limiting: 8-18s tra richieste (configurabile), burst pause.

Author: ARGOS Automotive CTO Stack
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from .base_scraper import BaseScraper
from .config import PORTALS, TARGET_VEHICLES, YEAR_MIN, YEAR_MAX, km_limit_for
from .models import Listing, FuelType, Transmission, SellerType, ScraperRun

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# MAPPATURE AUTOSCOUT24
# ─────────────────────────────────────────────────────────────────────────────

# TLD per paese
COUNTRY_TLD: Dict[str, str] = {
    "DE": "de",
    "NL": "nl",
    "BE": "be",
    "AT": "at",
    "FR": "fr",
    "SE": "se",
    "IT": "it",
}

# Accept-Language per paese
COUNTRY_ACCEPT_LANG: Dict[str, str] = {
    "DE": "de-DE,de;q=0.9,en;q=0.8",
    "NL": "nl-NL,nl;q=0.9,en;q=0.8",
    "BE": "nl-BE,nl;q=0.9,fr-BE;q=0.8,en;q=0.7",
    "AT": "de-AT,de;q=0.9,en;q=0.8",
    "FR": "fr-FR,fr;q=0.9,en;q=0.8",
    "SE": "sv-SE,sv;q=0.9,en;q=0.8",
    "IT": "it-IT,it;q=0.9,en;q=0.8",
}

# Country code per URL param (cy=D per DE, cy=NL per NL, ecc.)
COUNTRY_CY_PARAM: Dict[str, str] = {
    "DE": "D",
    "NL": "NL",
    "BE": "B",
    "AT": "A",
    "FR": "F",
    "SE": "S",
    "IT": "I",
}

# Make slug per URL AutoScout24
MAKE_SLUG: Dict[str, str] = {
    "BMW": "bmw",
    "Mercedes-Benz": "mercedes-benz",
    "Mercedes": "mercedes-benz",
    "Audi": "audi",
    "Porsche": "porsche",
    "Lamborghini": "lamborghini",
    "Ferrari": "ferrari",
    "McLaren": "mclaren",
    "Land Rover": "land-rover",
    "Range Rover": "land-rover",
    "Volkswagen": "volkswagen",
    "Volvo": "volvo",
    "Peugeot": "peugeot",
    "Renault": "renault",
    "Fiat": "fiat",
    "Alfa Romeo": "alfa-romeo",
    "Maserati": "maserati",
}

# Model slug per paese — key: model generico, value: {country: slug}
# Se il country non e' presente, usa "universal" come fallback.
MODEL_SLUG: Dict[str, Dict[str, str]] = {
    # BMW
    "Serie 3": {
        "DE": "3er-reihe", "AT": "3er-reihe",
        "NL": "3-reeks", "BE": "3-reeks",
        "FR": "serie-3", "IT": "serie-3",
        "SE": "3-serie",
        "universal": "3er-reihe",
    },
    "Serie 5": {
        "DE": "5er-reihe", "AT": "5er-reihe",
        "NL": "5-reeks", "BE": "5-reeks",
        "FR": "serie-5", "IT": "serie-5",
        "SE": "5-serie",
        "universal": "5er-reihe",
    },
    "X1": {"universal": "x1"},
    "X3": {"universal": "x3"},
    "X5": {"universal": "x5"},
    "X6": {"universal": "x6"},
    "M3": {"universal": "m3"},
    "M4": {"universal": "m4"},
    # Mercedes-Benz
    "Classe A": {
        "DE": "a-klasse", "AT": "a-klasse",
        "NL": "a-klasse", "BE": "a-klasse",
        "FR": "classe-a", "IT": "classe-a",
        "SE": "a-klass",
        "universal": "a-klasse",
    },
    "Classe C": {
        "DE": "c-klasse", "AT": "c-klasse",
        "NL": "c-klasse", "BE": "c-klasse",
        "FR": "classe-c", "IT": "classe-c",
        "SE": "c-klass",
        "universal": "c-klasse",
    },
    "Classe E": {
        "DE": "e-klasse", "AT": "e-klasse",
        "NL": "e-klasse", "BE": "e-klasse",
        "FR": "classe-e", "IT": "classe-e",
        "SE": "e-klass",
        "universal": "e-klasse",
    },
    "GLA": {"universal": "gla"},
    "GLB": {"universal": "glb"},
    "GLC": {"universal": "glc"},
    "GLE": {"universal": "gle"},
    "CLA": {"universal": "cla"},
    "AMG GT": {"universal": "amg-gt"},
    # Audi
    "A3": {"universal": "a3"},
    "A4": {"universal": "a4"},
    "A5": {"universal": "a5"},
    "A6": {"universal": "a6"},
    "Q3": {"universal": "q3"},
    "Q5": {"universal": "q5"},
    "Q7": {"universal": "q7"},
    "Q8": {"universal": "q8"},
    "RS3": {"universal": "rs3"},
    "RS5": {"universal": "rs5"},
    # Porsche
    "Cayenne": {"universal": "cayenne"},
    "Macan": {"universal": "macan"},
    "911": {"universal": "911"},
    "Panamera": {"universal": "panamera"},
    "Taycan": {"universal": "taycan"},
    # Lamborghini
    "Urus": {"universal": "urus"},
    "Huracan": {"universal": "huracan"},
    # Ferrari
    "Roma": {"universal": "roma"},
    "F8": {"universal": "f8"},
    "296": {"universal": "296"},
    # McLaren
    "720S": {"universal": "720s"},
    "GT": {"universal": "gt"},
    # Range Rover / Land Rover
    "Sport": {"universal": "range-rover-sport"},
    "Velar": {"universal": "range-rover-velar"},
    "Evoque": {"universal": "range-rover-evoque"},
}

# Mappatura fuel type AutoScout24 → FuelType enum
_FUEL_MAP: Dict[str, FuelType] = {
    "petrol": FuelType.PETROL,
    "gasoline": FuelType.PETROL,
    "benzin": FuelType.PETROL,
    "benzine": FuelType.PETROL,
    "essence": FuelType.PETROL,
    "bensin": FuelType.PETROL,
    "diesel": FuelType.DIESEL,
    "hybrid": FuelType.HYBRID,
    "hybride": FuelType.HYBRID,
    "plug-in hybrid": FuelType.PLUGIN_HYBRID,
    "plugin hybrid": FuelType.PLUGIN_HYBRID,
    "electric": FuelType.ELECTRIC,
    "elektro": FuelType.ELECTRIC,
    "electrique": FuelType.ELECTRIC,
    "elettrica": FuelType.ELECTRIC,
    "lpg": FuelType.LPG,
    "cng": FuelType.CNG,
    "erdgas": FuelType.CNG,
}

# Mappatura transmission
_TRANS_MAP: Dict[str, Transmission] = {
    "automatic": Transmission.AUTOMATIC,
    "automatik": Transmission.AUTOMATIC,
    "automatique": Transmission.AUTOMATIC,
    "automatico": Transmission.AUTOMATIC,
    "automatisch": Transmission.AUTOMATIC,
    "manual": Transmission.MANUAL,
    "manuell": Transmission.MANUAL,
    "manuelle": Transmission.MANUAL,
    "manuale": Transmission.MANUAL,
    "handgeschakeld": Transmission.MANUAL,
}


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_make_slug(make: str) -> str:
    """Risolve il make in slug URL AutoScout24."""
    slug = MAKE_SLUG.get(make)
    if slug:
        return slug
    # Fallback: lowercase e dash per spazi
    return make.lower().replace(" ", "-")


def _resolve_model_slug(model: str, country: str) -> str:
    """Risolve il model in slug URL per uno specifico paese."""
    mapping = MODEL_SLUG.get(model)
    if not mapping:
        # Fallback: lowercase, dash per spazi
        return model.lower().replace(" ", "-")
    return mapping.get(country, mapping.get("universal", model.lower().replace(" ", "-")))


def _parse_fuel(raw: str) -> FuelType:
    """Parsa fuel type da stringa raw multilingua."""
    if not raw:
        return FuelType.UNKNOWN
    low = raw.strip().lower()
    for key, ft in _FUEL_MAP.items():
        if key in low:
            return ft
    return FuelType.UNKNOWN


def _parse_transmission(raw: str) -> Transmission:
    """Parsa transmission da stringa raw multilingua."""
    if not raw:
        return Transmission.UNKNOWN
    low = raw.strip().lower()
    for key, tr in _TRANS_MAP.items():
        if key in low:
            return tr
    return Transmission.UNKNOWN


def _parse_price(raw: str) -> Optional[float]:
    """
    Parsa un prezzo da stringa: '27.800', '27,800', '27800', '€ 27.800,-'
    Restituisce float in EUR, oppure None.
    """
    if not raw:
        return None
    # Rimuovi tutto tranne cifre, punti e virgole
    cleaned = re.sub(r"[^\d.,]", "", raw.strip())
    if not cleaned:
        return None

    # Determina separatore decimale vs migliaia
    # AutoScout24: '27.800' = 27800 EUR (punto = migliaia), '27.800,00' = 27800 EUR
    # Formato olandese/belga: '27.800,-' = 27800
    # Formato svedese: '279 000 kr' gia' pulito sopra
    if "," in cleaned and "." in cleaned:
        # Entrambi presenti: l'ultimo e' il decimale
        if cleaned.rindex(",") > cleaned.rindex("."):
            # 27.800,50 → punto=migliaia, virgola=decimale
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # 27,800.50 → virgola=migliaia, punto=decimale
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Solo virgola: se dopo ci sono esattamente 3 cifre, e' migliaia
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) == 3:
            cleaned = cleaned.replace(",", "")
        elif len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            # Multipli: 27,800,000
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) == 2 and len(parts[1]) == 3:
            # 27.800 → migliaia
            cleaned = cleaned.replace(".", "")
        elif len(parts) > 2:
            # 27.800.000
            cleaned = cleaned.replace(".", "")
        # else: 27.50 → decimale, lascio com'e'

    try:
        val = float(cleaned)
        # Sanity: un prezzo auto deve essere > 500 e < 5.000.000
        if val < 500 or val > 5_000_000:
            return None
        return val
    except ValueError:
        return None


def _parse_km(raw: str) -> Optional[int]:
    """Parsa chilometraggio: '45.200 km', '45200', '45,200 km'."""
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.,]", "", raw.strip())
    if not cleaned:
        return None
    cleaned = cleaned.replace(".", "").replace(",", "")
    try:
        val = int(cleaned)
        if val < 0 or val > 999_999:
            return None
        return val
    except ValueError:
        return None


def _parse_year(raw: str) -> Optional[int]:
    """Parsa anno: '2020', '03/2020', '2020-03'."""
    if not raw:
        return None
    # Cerca 4 cifre che iniziano con 19 o 20
    match = re.search(r"((?:19|20)\d{2})", raw)
    if match:
        y = int(match.group(1))
        if 1990 <= y <= 2030:
            return y
    return None


def _extract_seller_type(raw: str) -> SellerType:
    """Determina seller type da stringa o contesto."""
    if not raw:
        return SellerType.UNKNOWN
    low = raw.strip().lower()
    dealer_keywords = [
        "dealer", "handler", "concessionnaire", "concessionario",
        "handelaar", "handlare", "gewerblich", "professionnel",
        "professionista", "bedrijf",
    ]
    private_keywords = [
        "private", "privat", "particulier", "privato", "prive",
    ]
    for kw in dealer_keywords:
        if kw in low:
            return SellerType.DEALER
    for kw in private_keywords:
        if kw in low:
            return SellerType.PRIVATE
    return SellerType.UNKNOWN


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

class AutoScoutScraper(BaseScraper):
    """
    Scraper concreto per AutoScout24 multi-country.

    Supporta: DE, NL, BE, AT, FR, SE, IT.

    Parsing strategy:
      1. JSON-LD (<script type="application/ld+json">) — dati strutturati, preferiti
      2. __NEXT_DATA__ JSON blob — dati React/Next.js hydration
      3. HTML card regex — fallback robusto

    Usage:
        scraper = AutoScoutScraper("autoscout24_de")
        listings, run = scraper.scrape("BMW", "Serie 3", year_min=2019, km_max=80000)
    """

    MAX_PAGES = 20
    RESULTS_PER_PAGE = 20

    def __init__(
        self,
        portal_key: str,
        *,
        rate_limit_min_s: float = 8.0,
        rate_limit_max_s: float = 18.0,
        max_retries: int = 3,
        backoff_base_s: float = 30.0,
        request_timeout_s: int = 25,
    ):
        super().__init__(
            portal_key,
            max_retries=max_retries,
            backoff_base_s=backoff_base_s,
            request_timeout_s=request_timeout_s,
        )
        # Determina il paese dal portal_key (es. "autoscout24_de" → "DE")
        self._country = self._resolve_country()
        self._tld = COUNTRY_TLD.get(self._country, "de")
        self._accept_lang = COUNTRY_ACCEPT_LANG.get(self._country, "en;q=0.9")
        self._cy_param = COUNTRY_CY_PARAM.get(self._country, "D")

    def _resolve_country(self) -> str:
        """Determina il country code dal portal_key."""
        # portal_key format: autoscout24_XX
        parts = self.portal_key.split("_")
        if len(parts) >= 2:
            code = parts[-1].upper()
            if code in COUNTRY_TLD:
                return code
        # Fallback da config
        if self.portal.countries:
            return self.portal.countries[0]
        return "DE"

    # ─────────────────────────────────────────────────────────
    # URL BUILDING
    # ─────────────────────────────────────────────────────────

    def build_search_url(
        self,
        make: str,
        model: str,
        page: int = 1,
        *,
        year_min: int = YEAR_MIN,
        year_max: int = YEAR_MAX,
        km_max: Optional[int] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        fuel_types: Optional[List[str]] = None,
        sort: str = "standard",
        **kwargs,
    ) -> str:
        """
        Costruisce l'URL di ricerca AutoScout24.

        Formato:
        https://www.autoscout24.{tld}/lst/{make_slug}/{model_slug}?atype=C&cy={cy}&...

        Args:
            make: "BMW", "Mercedes-Benz", "Audi", ...
            model: "Serie 3", "Classe C", "A4", ...
            page: Numero pagina (1-based)
            year_min: Anno minimo immatricolazione
            year_max: Anno massimo immatricolazione
            km_max: Chilometraggio massimo
            price_min: Prezzo minimo EUR
            price_max: Prezzo massimo EUR
            fuel_types: Lista fuel type codes (D=Diesel, G=Gasoline, E=Electric, ecc.)
            sort: Ordinamento (standard, price_asc, price_desc)
        """
        make_slug = _resolve_make_slug(make)
        model_slug = _resolve_model_slug(model, self._country)

        if km_max is None:
            km_max = km_limit_for(make, model)

        params: Dict[str, str] = {
            "atype": "C",
            "cy": self._cy_param,
            "damaged_listing": "exclude",
            "fregfrom": str(year_min),
            "fregto": str(year_max),
            "kmto": str(km_max),
            "sort": sort,
            "ustate": "N,U",
        }

        if page > 1:
            params["page"] = str(page)

        if price_min is not None:
            params["pricefrom"] = str(price_min)
        if price_max is not None:
            params["priceto"] = str(price_max)

        # Fuel types: powertype=D&powertype=G
        if fuel_types is None:
            fuel_types = ["D", "G"]

        # Costruisci query string manualmente per duplicati powertype
        base = f"https://www.autoscout24.{self._tld}/lst/{make_slug}/{model_slug}"
        qs_parts = []
        for k, v in params.items():
            qs_parts.append(f"{k}={quote(v, safe=',')}")
        for ft in fuel_types:
            qs_parts.append(f"powertype={quote(ft)}")

        url = f"{base}?{'&'.join(qs_parts)}"
        return url

    # ─────────────────────────────────────────────────────────
    # FETCH OVERRIDE — aggiunge Accept-Language per paese
    # ─────────────────────────────────────────────────────────

    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
        """Override fetch per aggiungere Accept-Language per paese."""
        country_headers = {
            "Accept-Language": self._accept_lang,
        }
        if headers:
            country_headers.update(headers)
        return super().fetch(url, headers=country_headers)

    # ─────────────────────────────────────────────────────────
    # PARSING — strategia 3-livelli
    # ─────────────────────────────────────────────────────────

    def parse_search_results(self, html: str) -> List[Listing]:
        """Wrapper per compatibilità con BaseScraper (usa parse_listings con defaults)."""
        return self.parse_listings(html, country='DE', make='', model='')

    def parse_listings(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """
        Parsa listings dalla pagina di ricerca AutoScout24.

        Strategia:
          1. JSON-LD — dati strutturati (<script type="application/ld+json">)
          2. __NEXT_DATA__ — dati React hydration
          3. HTML card regex — fallback
        """
        if not html or len(html) < 200:
            logger.warning("[%s] HTML troppo corto (%d bytes) — skip", self.portal_key, len(html))
            return []

        # Strategia 1: JSON-LD
        listings = self._parse_json_ld(html, country, make, model)
        if listings:
            logger.debug("[%s] Parsed %d listings via JSON-LD", self.portal_key, len(listings))
            return listings

        # Strategia 2: __NEXT_DATA__
        listings = self._parse_next_data(html, country, make, model)
        if listings:
            logger.debug("[%s] Parsed %d listings via __NEXT_DATA__", self.portal_key, len(listings))
            return listings

        # Strategia 3: HTML card regex
        listings = self._parse_html_cards(html, country, make, model)
        if listings:
            logger.debug("[%s] Parsed %d listings via HTML regex", self.portal_key, len(listings))
            return listings

        logger.warning("[%s] No listings parsed from any strategy", self.portal_key)
        return []

    # ─── Strategia 1: JSON-LD ────────────────────────────────

    def _parse_json_ld(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """Parsa JSON-LD <script type="application/ld+json">."""
        listings: List[Listing] = []

        pattern = re.compile(
            r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
            re.DOTALL,
        )

        for match in pattern.finditer(html):
            raw_json = match.group(1).strip()
            if not raw_json:
                continue
            try:
                data = json.loads(raw_json)
            except (json.JSONDecodeError, ValueError):
                continue

            # JSON-LD puo' essere un singolo oggetto o una lista
            items: List[Dict[str, Any]] = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # Potrebbe essere un ItemList con itemListElement
                if data.get("@type") == "ItemList":
                    for elem in data.get("itemListElement", []):
                        item = elem.get("item", elem)
                        if isinstance(item, dict):
                            items.append(item)
                elif data.get("@type") in ("Car", "Vehicle", "Product", "Offer"):
                    items.append(data)

            for item in items:
                listing = self._json_ld_to_listing(item, country, make, model)
                if listing:
                    listings.append(listing)

        return listings

    def _json_ld_to_listing(
        self, item: Dict[str, Any], country: str, make: str, model: str
    ) -> Optional[Listing]:
        """Converte un singolo oggetto JSON-LD in Listing."""
        item_type = item.get("@type", "")
        if item_type not in ("Car", "Vehicle", "Product", "Offer", ""):
            return None

        # URL
        listing_url = item.get("url", item.get("@id", ""))
        if not listing_url:
            return None

        # Listing ID
        lid = self.generate_listing_id(self.portal_key, listing_url)

        # Prezzo
        price_raw = None
        offers = item.get("offers", item.get("offer", {}))
        if isinstance(offers, dict):
            price_raw = offers.get("price", offers.get("lowPrice"))
        elif isinstance(offers, list) and offers:
            price_raw = offers[0].get("price", offers[0].get("lowPrice"))
        if price_raw is None:
            price_raw = item.get("price")

        price = None
        if price_raw is not None:
            if isinstance(price_raw, (int, float)):
                price = float(price_raw)
            else:
                price = _parse_price(str(price_raw))

        # Nome / variant
        name = item.get("name", "")
        variant = item.get("vehicleConfiguration", item.get("model", ""))
        if isinstance(variant, dict):
            variant = variant.get("name", "")

        # Anno
        year_raw = item.get("vehicleModelDate", item.get("productionDate", ""))
        year = _parse_year(str(year_raw)) if year_raw else None

        # Km
        km_raw = item.get("mileageFromOdometer", {})
        if isinstance(km_raw, dict):
            km_val = km_raw.get("value", "")
        else:
            km_val = km_raw
        km = _parse_km(str(km_val)) if km_val else None

        # Fuel
        fuel_raw = item.get("fuelType", item.get("vehicleEngine", {}).get("fuelType", ""))
        if isinstance(fuel_raw, dict):
            fuel_raw = fuel_raw.get("name", "")
        fuel_type = _parse_fuel(str(fuel_raw))

        # Transmission
        trans_raw = item.get("vehicleTransmission", "")
        if isinstance(trans_raw, dict):
            trans_raw = trans_raw.get("name", "")
        transmission = _parse_transmission(str(trans_raw))

        # Immagini
        images: List[str] = []
        img_data = item.get("image", [])
        if isinstance(img_data, str):
            images = [img_data]
        elif isinstance(img_data, list):
            for im in img_data[:10]:
                if isinstance(im, str):
                    images.append(im)
                elif isinstance(im, dict):
                    images.append(im.get("contentUrl", im.get("url", "")))

        # Seller
        seller_data = item.get("seller", item.get("offeredBy", {}))
        seller_name = ""
        seller_type = SellerType.UNKNOWN
        if isinstance(seller_data, dict):
            seller_name = seller_data.get("name", "")
            st_raw = seller_data.get("@type", "")
            if "auto" in st_raw.lower() or "dealer" in st_raw.lower():
                seller_type = SellerType.DEALER
            elif "person" in st_raw.lower():
                seller_type = SellerType.PRIVATE
            else:
                seller_type = _extract_seller_type(st_raw)

        # Power
        power_hp = 0
        engine = item.get("vehicleEngine", {})
        if isinstance(engine, dict):
            power_raw = engine.get("enginePower", {})
            if isinstance(power_raw, dict):
                pv = power_raw.get("value", 0)
                try:
                    power_hp = int(pv)
                except (ValueError, TypeError):
                    pass

        return Listing(
            listing_id=lid,
            portal=self.portal_key,
            country=country,
            make=make,
            model=model,
            variant=str(variant)[:200] if variant else name[:200] if name else "",
            year=year or 0,
            km=km or 0,
            fuel_type=fuel_type,
            transmission=transmission,
            power_hp=power_hp,
            price_eur=price or 0.0,
            currency_original="SEK" if country == "SE" else "EUR",
            seller_type=seller_type,
            seller_name=seller_name,
            listing_url=listing_url,
            image_urls=images,
        )

    # ─── Strategia 2: __NEXT_DATA__ ─────────────────────────

    def _parse_next_data(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """Parsa il blob JSON __NEXT_DATA__ (React/Next.js hydration)."""
        listings: List[Listing] = []

        pattern = re.compile(
            r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            re.DOTALL,
        )
        match = pattern.search(html)
        if not match:
            return []

        try:
            next_data = json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            logger.debug("[%s] Failed to parse __NEXT_DATA__ JSON", self.portal_key)
            return []

        # Naviga nella struttura Next.js per trovare i listing
        # AutoScout24 struttura: props.pageProps.listings[] o props.pageProps.searchResult.listings[]
        page_props = next_data.get("props", {}).get("pageProps", {})

        listing_items = (
            page_props.get("listings", [])
            or page_props.get("searchResult", {}).get("listings", [])
            or page_props.get("listingsData", {}).get("listings", [])
        )

        if not listing_items:
            # Cerca ricorsivamente chiavi con "listing" nel nome
            listing_items = self._find_listings_in_dict(page_props)

        for item in listing_items:
            listing = self._next_data_item_to_listing(item, country, make, model)
            if listing:
                listings.append(listing)

        return listings

    def _find_listings_in_dict(self, d: Any, depth: int = 0) -> List[Dict]:
        """Cerca ricorsivamente liste di listing nel dict Next.js."""
        if depth > 5 or not isinstance(d, dict):
            return []
        for key, val in d.items():
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                # Euristica: una lista di dict con 'id' o 'price' o 'url' sono listing
                sample = val[0]
                if any(k in sample for k in ("id", "price", "url", "tracking", "listingId")):
                    return val
            if isinstance(val, dict):
                result = self._find_listings_in_dict(val, depth + 1)
                if result:
                    return result
        return []

    def _next_data_item_to_listing(
        self, item: Dict[str, Any], country: str, make: str, model: str
    ) -> Optional[Listing]:
        """Converte un item __NEXT_DATA__ in Listing."""
        if not isinstance(item, dict):
            return None

        # URL
        listing_url = item.get("url", item.get("detailUrl", ""))
        if listing_url and not listing_url.startswith("http"):
            listing_url = f"https://www.autoscout24.{self._tld}{listing_url}"

        if not listing_url:
            # Costruisci dall'ID
            item_id = item.get("id", item.get("listingId", ""))
            if item_id:
                listing_url = f"https://www.autoscout24.{self._tld}/angebote/{item_id}"
            else:
                return None

        lid = self.generate_listing_id(self.portal_key, listing_url)

        # Prezzo
        price = None
        price_raw = item.get("price", item.get("rawPrice", item.get("priceRaw", "")))
        if isinstance(price_raw, dict):
            price = _parse_price(str(price_raw.get("value", price_raw.get("amount", ""))))
        elif isinstance(price_raw, (int, float)):
            price = float(price_raw)
        elif isinstance(price_raw, str):
            price = _parse_price(price_raw)

        # Dati veicolo
        vehicle = item.get("vehicle", item)
        variant = vehicle.get("modelVersionInput", vehicle.get("version", vehicle.get("variant", "")))
        if isinstance(variant, dict):
            variant = variant.get("raw", "")

        year_raw = vehicle.get("firstRegistration", vehicle.get("year", vehicle.get("yearOfRegistration", "")))
        year = _parse_year(str(year_raw)) if year_raw else None

        km_raw = vehicle.get("mileage", vehicle.get("km", vehicle.get("mileageInKmRaw", "")))
        if isinstance(km_raw, dict):
            km_raw = km_raw.get("value", km_raw.get("raw", ""))
        km = _parse_km(str(km_raw)) if km_raw else None

        fuel_raw = vehicle.get("fuelType", vehicle.get("fuel", ""))
        if isinstance(fuel_raw, dict):
            fuel_raw = fuel_raw.get("label", fuel_raw.get("value", ""))
        fuel_type = _parse_fuel(str(fuel_raw))

        trans_raw = vehicle.get("transmissionType", vehicle.get("transmission", ""))
        if isinstance(trans_raw, dict):
            trans_raw = trans_raw.get("label", trans_raw.get("value", ""))
        transmission = _parse_transmission(str(trans_raw))

        power_hp = 0
        power_raw = vehicle.get("power", vehicle.get("powerInHp", vehicle.get("hp", 0)))
        if isinstance(power_raw, dict):
            power_raw = power_raw.get("hp", power_raw.get("value", 0))
        try:
            power_hp = int(power_raw)
        except (ValueError, TypeError):
            pass

        # Immagini
        images: List[str] = []
        img_data = item.get("images", item.get("image", item.get("imageUrls", [])))
        if isinstance(img_data, list):
            for im in img_data[:10]:
                if isinstance(im, str):
                    images.append(im)
                elif isinstance(im, dict):
                    images.append(im.get("url", im.get("src", "")))
        elif isinstance(img_data, str):
            images = [img_data]

        # Seller
        seller_data = item.get("seller", {})
        seller_name = ""
        seller_type = SellerType.UNKNOWN
        if isinstance(seller_data, dict):
            seller_name = seller_data.get("name", seller_data.get("companyName", ""))
            st = seller_data.get("type", seller_data.get("sellerType", ""))
            seller_type = _extract_seller_type(str(st))

        return Listing(
            listing_id=lid,
            portal=self.portal_key,
            country=country,
            make=make,
            model=model,
            variant=str(variant)[:200] if variant else "",
            year=year or 0,
            km=km or 0,
            fuel_type=fuel_type,
            transmission=transmission,
            power_hp=power_hp,
            price_eur=price or 0.0,
            currency_original="SEK" if country == "SE" else "EUR",
            seller_type=seller_type,
            seller_name=seller_name,
            listing_url=listing_url,
            image_urls=[img for img in images if img],
        )

    # ─── Strategia 3: HTML Card Regex ────────────────────────

    def _parse_html_cards(
        self, html: str, country: str, make: str, model: str
    ) -> List[Listing]:
        """Fallback: parsa le card HTML con regex."""
        listings: List[Listing] = []

        # Pattern per trovare le card degli annunci
        # AutoScout24 usa <article> o <div> con data-* attributes, oppure link a /angebote/ o /annunci/
        card_patterns = [
            # Pattern 1: <article> con link
            re.compile(
                r'<article[^>]*?>(.*?)</article>',
                re.DOTALL | re.IGNORECASE,
            ),
            # Pattern 2: div con classe listing-card
            re.compile(
                r'<div[^>]*?class="[^"]*?(?:listing|result|vehicle)[^"]*?"[^>]*?>(.*?)</div>\s*</div>\s*</div>',
                re.DOTALL | re.IGNORECASE,
            ),
        ]

        cards: List[str] = []
        for pat in card_patterns:
            found = pat.findall(html)
            if found and len(found) >= 3:
                cards = found
                break

        if not cards:
            # Fallback: cerca tutti i link ad annunci individuali
            link_pattern = re.compile(
                r'href="(/(?:angebote|offerte|annonces|aanbod|annonser)/[^"]+)"',
                re.IGNORECASE,
            )
            links = list(set(link_pattern.findall(html)))
            if links:
                # Per ogni link, crea un listing minimale
                for link in links[:self.RESULTS_PER_PAGE]:
                    full_url = f"https://www.autoscout24.{self._tld}{link}"
                    lid = self.generate_listing_id(self.portal_key, full_url)
                    listing = self._extract_card_data_from_surrounding_html(
                        html, link, lid, country, make, model
                    )
                    if listing:
                        listings.append(listing)
                return listings
            return []

        for card_html in cards:
            listing = self._parse_single_card(card_html, country, make, model)
            if listing:
                listings.append(listing)

        return listings

    def _extract_card_data_from_surrounding_html(
        self, html: str, link: str, lid: str, country: str, make: str, model: str
    ) -> Optional[Listing]:
        """Estrai dati dal contesto HTML attorno a un link listing."""
        full_url = f"https://www.autoscout24.{self._tld}{link}"

        # Trova la posizione del link nel HTML e prendi un chunk attorno
        pos = html.find(link)
        if pos < 0:
            return Listing(
                listing_id=lid,
                portal=self.portal_key,
                country=country,
                make=make,
                model=model,
                listing_url=full_url,
            )

        start = max(0, pos - 2000)
        end = min(len(html), pos + 2000)
        chunk = html[start:end]

        # Prezzo
        price = None
        price_patterns = [
            re.compile(r'(\d{1,3}(?:[.\s]\d{3})+)\s*(?:EUR|€)', re.IGNORECASE),
            re.compile(r'(?:EUR|€)\s*(\d{1,3}(?:[.\s]\d{3})+)', re.IGNORECASE),
            re.compile(r'"price"[^}]*?"value":\s*["\']?(\d[\d.,]+)', re.IGNORECASE),
            re.compile(r'data-price="(\d+)"'),
        ]
        for pp in price_patterns:
            m = pp.search(chunk)
            if m:
                price = _parse_price(m.group(1))
                if price:
                    break

        # Km
        km = None
        km_patterns = [
            re.compile(r'(\d{1,3}(?:[.\s]\d{3})*)\s*km', re.IGNORECASE),
            re.compile(r'"mileage"[^}]*?"value":\s*["\']?(\d[\d.,]+)', re.IGNORECASE),
        ]
        for kp in km_patterns:
            m = kp.search(chunk)
            if m:
                km = _parse_km(m.group(1))
                if km:
                    break

        # Anno
        year = None
        year_patterns = [
            re.compile(r'(\d{2})/(\d{4})'),  # MM/YYYY
            re.compile(r'(20[12]\d)'),
        ]
        for yp in year_patterns:
            m = yp.search(chunk)
            if m:
                groups = m.groups()
                if len(groups) == 2 and len(groups[1]) == 4:
                    year = int(groups[1])
                elif len(groups) == 1:
                    year = _parse_year(groups[0])
                if year:
                    break

        # Fuel
        fuel_type = FuelType.UNKNOWN
        fuel_re = re.compile(
            r'(diesel|benzin|petrol|gasoline|hybrid|electric|elektro|essence|benzine)',
            re.IGNORECASE,
        )
        fm = fuel_re.search(chunk)
        if fm:
            fuel_type = _parse_fuel(fm.group(1))

        # Transmission
        transmission = Transmission.UNKNOWN
        trans_re = re.compile(
            r'(automat\w*|manual\w*|manuell\w*|handgeschakeld)',
            re.IGNORECASE,
        )
        tm = trans_re.search(chunk)
        if tm:
            transmission = _parse_transmission(tm.group(1))

        return Listing(
            listing_id=lid,
            portal=self.portal_key,
            country=country,
            make=make,
            model=model,
            year=year or 0,
            km=km or 0,
            fuel_type=fuel_type,
            transmission=transmission,
            price_eur=price or 0.0,
            currency_original="SEK" if country == "SE" else "EUR",
            listing_url=full_url,
        )

    def _parse_single_card(
        self, card_html: str, country: str, make: str, model: str
    ) -> Optional[Listing]:
        """Parsa una singola card HTML."""
        # URL
        url_match = re.search(
            r'href="(/(?:angebote|offerte|annonces|aanbod|annonser)/[^"]+)"',
            card_html,
            re.IGNORECASE,
        )
        if not url_match:
            url_match = re.search(r'href="(https://www\.autoscout24\.[^"]+/[^"]+)"', card_html)
        if not url_match:
            return None

        raw_url = url_match.group(1)
        if raw_url.startswith("/"):
            listing_url = f"https://www.autoscout24.{self._tld}{raw_url}"
        else:
            listing_url = raw_url

        lid = self.generate_listing_id(self.portal_key, listing_url)

        # Prezzo
        price = None
        price_patterns = [
            re.compile(r'(\d{1,3}(?:[.\s]\d{3})+)\s*(?:EUR|€)', re.IGNORECASE),
            re.compile(r'(?:EUR|€)\s*(\d{1,3}(?:[.\s]\d{3})+)', re.IGNORECASE),
            re.compile(r'"price"[^}]*?["\'](\d[\d.,]+)["\']', re.IGNORECASE),
        ]
        for pp in price_patterns:
            m = pp.search(card_html)
            if m:
                price = _parse_price(m.group(1))
                if price:
                    break

        # Km
        km = None
        km_match = re.search(r'(\d{1,3}(?:[.\s]\d{3})*)\s*km', card_html, re.IGNORECASE)
        if km_match:
            km = _parse_km(km_match.group(1))

        # Anno
        year = None
        year_match = re.search(r'(\d{2})/(\d{4})', card_html)
        if year_match:
            year = int(year_match.group(2))
        else:
            year_match = re.search(r'(20[12]\d)', card_html)
            if year_match:
                year = _parse_year(year_match.group(1))

        # Variant (titolo della card)
        variant = ""
        title_match = re.search(
            r'(?:title|aria-label)="([^"]*)"',
            card_html,
            re.IGNORECASE,
        )
        if title_match:
            variant = title_match.group(1).strip()[:200]

        # Fuel
        fuel_type = FuelType.UNKNOWN
        fuel_match = re.search(
            r'(diesel|benzin|petrol|gasoline|hybrid|electric|elektro|essence|benzine)',
            card_html,
            re.IGNORECASE,
        )
        if fuel_match:
            fuel_type = _parse_fuel(fuel_match.group(1))

        # Transmission
        transmission = Transmission.UNKNOWN
        trans_match = re.search(
            r'(automat\w*|manual\w*|manuell\w*|handgeschakeld)',
            card_html,
            re.IGNORECASE,
        )
        if trans_match:
            transmission = _parse_transmission(trans_match.group(1))

        # Power
        power_hp = 0
        power_match = re.search(r'(\d{2,4})\s*(?:hp|ps|cv|pk|hk)', card_html, re.IGNORECASE)
        if power_match:
            try:
                power_hp = int(power_match.group(1))
                if power_hp > 2000:
                    power_hp = 0
            except ValueError:
                pass

        # Immagini
        images: List[str] = []
        img_matches = re.findall(r'<img[^>]*?src="(https://[^"]*?autoscout[^"]*?)"', card_html)
        images = img_matches[:5]

        # Seller type
        seller_type = SellerType.UNKNOWN
        if re.search(r'(?:dealer|handler|concession|profession|gewerblich|bedrijf)', card_html, re.IGNORECASE):
            seller_type = SellerType.DEALER
        elif re.search(r'(?:privat|particulier|prive)', card_html, re.IGNORECASE):
            seller_type = SellerType.PRIVATE

        return Listing(
            listing_id=lid,
            portal=self.portal_key,
            country=country,
            make=make,
            model=model,
            variant=variant,
            year=year or 0,
            km=km or 0,
            fuel_type=fuel_type,
            transmission=transmission,
            power_hp=power_hp,
            price_eur=price or 0.0,
            currency_original="SEK" if country == "SE" else "EUR",
            seller_type=seller_type,
            listing_url=listing_url,
            image_urls=images,
        )

    # ─────────────────────────────────────────────────────────
    # PAGINAZIONE
    # ─────────────────────────────────────────────────────────

    def has_next_page(self, html: str, current_page: int) -> bool:
        """Determina se esiste una pagina successiva."""
        if current_page >= self.MAX_PAGES:
            return False

        # Metodo 1: cerca link alla pagina successiva
        next_page = current_page + 1
        if f"page={next_page}" in html:
            return True

        # Metodo 2: cerca pulsante "next" o ">" o "Nachste" / "Volgende" / "Suivant" / "Successivo"
        next_patterns = [
            r'aria-label="[^"]*(?:next|nachste|volgende|suivant|successiv|nasta)[^"]*"',
            r'class="[^"]*pagination[^"]*next[^"]*"',
            r'rel="next"',
        ]
        for pat in next_patterns:
            if re.search(pat, html, re.IGNORECASE):
                return True

        # Metodo 3: se ci sono RESULTS_PER_PAGE listing, probabilmente c'e' una pagina dopo
        # Conta i link ad annunci
        link_count = len(re.findall(
            r'href="[^"]*(?:angebote|offerte|annonces|aanbod|annonser)/[^"]+',
            html,
            re.IGNORECASE,
        ))
        if link_count >= self.RESULTS_PER_PAGE - 2:
            return True

        return False

    # ─────────────────────────────────────────────────────────
    # SCRAPE OVERRIDE — passa kwargs extra
    # ─────────────────────────────────────────────────────────

    def scrape(
        self,
        make: str,
        model: str,
        max_pages: Optional[int] = None,
        *,
        year_min: int = YEAR_MIN,
        year_max: int = YEAR_MAX,
        km_max: Optional[int] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        fuel_types: Optional[List[str]] = None,
        **kwargs,
    ) -> Tuple[List[Listing], ScraperRun]:
        """
        Scrape AutoScout24 per un make/model specifico.

        Args:
            make: "BMW", "Mercedes-Benz", "Audi", ...
            model: "Serie 3", "Classe C", "A4", ...
            max_pages: Limite pagine (default: config portale)
            year_min: Anno minimo
            year_max: Anno massimo
            km_max: Km massimo (default: da config per categoria)
            price_min: Prezzo minimo EUR
            price_max: Prezzo massimo EUR
            fuel_types: Lista codici fuel (D, G, E, ...)
        """
        return super().scrape(
            make,
            model,
            max_pages=max_pages or min(self.portal.max_pages, self.MAX_PAGES),
            year_min=year_min,
            year_max=year_max,
            km_max=km_max,
            price_min=price_min,
            price_max=price_max,
            fuel_types=fuel_types,
            **kwargs,
        )

    # ─────────────────────────────────────────────────────────
    # MULTI-COUNTRY CONVENIENCE
    # ─────────────────────────────────────────────────────────

    @classmethod
    def scrape_all_countries(
        cls,
        make: str,
        model: str,
        countries: Optional[List[str]] = None,
        max_pages_per_country: int = 5,
        **search_kwargs,
    ) -> Tuple[List[Listing], List[ScraperRun]]:
        """
        Scrape lo stesso make/model su tutti i paesi configurati.

        Args:
            make: "BMW"
            model: "Serie 3"
            countries: Lista paesi (default: tutti)
            max_pages_per_country: Pagine per paese
            **search_kwargs: Passati a scrape() (year_min, km_max, ecc.)

        Returns:
            (all_listings, all_runs)
        """
        if countries is None:
            countries = list(COUNTRY_TLD.keys())

        all_listings: List[Listing] = []
        all_runs: List[ScraperRun] = []

        for country in countries:
            portal_key = f"autoscout24_{country.lower()}"
            if portal_key not in PORTALS:
                logger.warning("Portal %s non configurato — skip %s", portal_key, country)
                continue

            logger.info(
                "Scraping %s %s on %s (%s)",
                make, model, portal_key, country,
            )
            try:
                scraper = cls(portal_key)
                listings, run = scraper.scrape(
                    make, model,
                    max_pages=max_pages_per_country,
                    **search_kwargs,
                )
                all_listings.extend(listings)
                all_runs.append(run)
                logger.info(
                    "%s: %d listings in %.0fs",
                    country, len(listings), run.duration_seconds(),
                )
            except Exception as exc:
                logger.error("Failed scraping %s: %s", portal_key, exc)
                failed_run = ScraperRun(
                    portal=portal_key,
                    country=country,
                    started_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    finished_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    status="FAILED",
                    errors=[str(exc)],
                )
                all_runs.append(failed_run)

        logger.info(
            "Multi-country scrape complete: %d total listings from %d countries",
            len(all_listings), len(countries),
        )
        return (all_listings, all_runs)


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """CLI per test rapido dello scraper."""
    import argparse
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="ARGOS AutoScout24 Multi-Country Scraper",
    )
    parser.add_argument("--make", default="BMW", help="Make (default: BMW)")
    parser.add_argument("--model", default="Serie 3", help="Model (default: Serie 3)")
    parser.add_argument("--country", default="DE", help="Country code (default: DE)")
    parser.add_argument("--pages", type=int, default=2, help="Max pages (default: 2)")
    parser.add_argument("--year-min", type=int, default=YEAR_MIN, help=f"Year min (default: {YEAR_MIN})")
    parser.add_argument("--year-max", type=int, default=YEAR_MAX, help=f"Year max (default: {YEAR_MAX})")
    parser.add_argument("--km-max", type=int, default=None, help="Max km (default: auto)")
    parser.add_argument("--all-countries", action="store_true", help="Scrape all countries")
    parser.add_argument("--url-only", action="store_true", help="Only print search URL, no scraping")
    args = parser.parse_args()

    if args.all_countries:
        print(f"=== ARGOS AutoScout24 Multi-Country Scraper ===")
        print(f"Make: {args.make} | Model: {args.model}")
        print(f"Year: {args.year_min}-{args.year_max} | Pages/country: {args.pages}")
        print()

        listings, runs = AutoScoutScraper.scrape_all_countries(
            args.make,
            args.model,
            max_pages_per_country=args.pages,
            year_min=args.year_min,
            year_max=args.year_max,
            km_max=args.km_max,
        )

        print(f"\n{'='*60}")
        print(f"RISULTATI TOTALI: {len(listings)} listings")
        for run in runs:
            print(f"  {run.country}: {run.listings_found} listings, {run.pages_scraped} pages, {run.status.value if hasattr(run.status, 'value') else run.status}")
        print()

        for lst in listings[:10]:
            print(f"  [{lst.country}] {lst.make} {lst.model} {lst.variant} | {lst.year} | {lst.km:,} km | EUR {lst.price_eur:,.0f} | {lst.fuel_type.value} | {lst.listing_url}")
        if len(listings) > 10:
            print(f"  ... e altri {len(listings) - 10} listing")

        sys.exit(0)

    portal_key = f"autoscout24_{args.country.lower()}"
    scraper = AutoScoutScraper(portal_key)

    if args.url_only:
        url = scraper.build_search_url(
            args.make,
            args.model,
            page=1,
            year_min=args.year_min,
            year_max=args.year_max,
            km_max=args.km_max,
        )
        print(url)
        sys.exit(0)

    print(f"=== ARGOS AutoScout24 Scraper ===")
    print(f"Portal: {portal_key} | Make: {args.make} | Model: {args.model}")
    print(f"Year: {args.year_min}-{args.year_max} | Max pages: {args.pages}")
    print()

    listings, run = scraper.scrape(
        args.make,
        args.model,
        max_pages=args.pages,
        year_min=args.year_min,
        year_max=args.year_max,
        km_max=args.km_max,
    )

    print(f"\n{'='*60}")
    print(f"Run: {run.status.value} | {run.listings_found} listings | {run.pages_scraped} pages | {run.duration_seconds():.0f}s")
    if run.errors:
        print(f"Errors: {run.errors}")
    print()

    for lst in listings[:20]:
        print(f"  {lst.make} {lst.model} {lst.variant} | {lst.year} | {lst.km:,} km | EUR {lst.price_eur:,.0f} | {lst.fuel_type.value} | {lst.listing_url}")

    if len(listings) > 20:
        print(f"  ... e altri {len(listings) - 20} listing")


if __name__ == "__main__":
    main()
