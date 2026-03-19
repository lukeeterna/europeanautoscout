"""
config.py -- ARGOS Market Intelligence Configuration
CoVe 2026 | Enterprise Grade

Veicoli target, portali europei, rate limits, scheduling.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Categorie veicolo (per soglie km differenziate)
# ---------------------------------------------------------------------------
CATEGORY_SUV = "SUV"
CATEGORY_SUPERCAR = "SUPERCAR"
CATEGORY_STANDARD = "STANDARD"

MODEL_CATEGORIES: Dict[str, Dict[str, str]] = {
    "BMW": {
        "X1": CATEGORY_SUV, "X3": CATEGORY_SUV, "X5": CATEGORY_SUV,
        "Serie 3": CATEGORY_STANDARD, "Serie 5": CATEGORY_STANDARD,
        "M3": CATEGORY_STANDARD, "M4": CATEGORY_STANDARD,
    },
    "Mercedes": {
        "Classe A": CATEGORY_STANDARD, "Classe C": CATEGORY_STANDARD,
        "Classe E": CATEGORY_STANDARD,
        "GLA": CATEGORY_SUV, "GLC": CATEGORY_SUV, "GLE": CATEGORY_SUV,
        "AMG GT": CATEGORY_SUPERCAR,
    },
    "Audi": {
        "A3": CATEGORY_STANDARD, "A4": CATEGORY_STANDARD,
        "A5": CATEGORY_STANDARD, "A6": CATEGORY_STANDARD,
        "Q3": CATEGORY_SUV, "Q5": CATEGORY_SUV, "Q7": CATEGORY_SUV,
        "RS3": CATEGORY_STANDARD, "RS5": CATEGORY_STANDARD,
    },
    "Porsche": {
        "Cayenne": CATEGORY_SUV, "Macan": CATEGORY_SUV,
        "911": CATEGORY_SUPERCAR, "Panamera": CATEGORY_STANDARD,
        "Taycan": CATEGORY_STANDARD,
    },
    "Lamborghini": {
        "Urus": CATEGORY_SUPERCAR, "Huracan": CATEGORY_SUPERCAR,
    },
    "Ferrari": {
        "Roma": CATEGORY_SUPERCAR, "F8": CATEGORY_SUPERCAR,
        "296": CATEGORY_SUPERCAR,
    },
    "McLaren": {
        "720S": CATEGORY_SUPERCAR, "GT": CATEGORY_SUPERCAR,
    },
    "Range Rover": {
        "Sport": CATEGORY_SUV, "Velar": CATEGORY_SUV, "Evoque": CATEGORY_SUV,
    },
}

# ---------------------------------------------------------------------------
# Veicoli target (lista esplicita per iterazione)
# ---------------------------------------------------------------------------
TARGET_VEHICLES: Dict[str, List[str]] = {
    make: list(models.keys()) for make, models in MODEL_CATEGORIES.items()
}

# ---------------------------------------------------------------------------
# Limiti km per categoria
# ---------------------------------------------------------------------------
KM_LIMITS: Dict[str, int] = {
    CATEGORY_STANDARD: 80_000,
    CATEGORY_SUV: 100_000,
    CATEGORY_SUPERCAR: 30_000,
}

# Anni target
YEAR_MIN = 2018
YEAR_MAX = 2025


def km_limit_for(make: str, model: str) -> int:
    """Restituisce il limite km per make/model."""
    cat = MODEL_CATEGORIES.get(make, {}).get(model, CATEGORY_STANDARD)
    return KM_LIMITS[cat]


def category_for(make: str, model: str) -> str:
    """Restituisce la categoria del veicolo."""
    return MODEL_CATEGORIES.get(make, {}).get(model, CATEGORY_STANDARD)


# ---------------------------------------------------------------------------
# Portali e paesi supportati
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PortalConfig:
    """Configurazione per un portale di annunci."""
    name: str
    base_url: str
    countries: List[str]
    results_per_page: int = 20
    max_pages: int = 10
    rate_limit_min_s: float = 3.0      # sleep minimo tra richieste (secondi)
    rate_limit_max_s: float = 8.0      # sleep massimo tra richieste (secondi)
    rate_limit_burst_pause_s: float = 30.0  # pausa dopo burst di pagine
    burst_size: int = 5                 # pagine prima della pausa burst
    daily_request_cap: int = 2000       # cap giornaliero richieste
    headers: Dict[str, str] = field(default_factory=dict)


PORTALS: Dict[str, PortalConfig] = {
    "autoscout24_de": PortalConfig(
        name="AutoScout24 DE",
        base_url="https://www.autoscout24.de",
        countries=["DE"],
        results_per_page=20,
        max_pages=10,
        rate_limit_min_s=4.0,
        rate_limit_max_s=10.0,
    ),
    "autoscout24_nl": PortalConfig(
        name="AutoScout24 NL",
        base_url="https://www.autoscout24.nl",
        countries=["NL"],
        results_per_page=20,
        max_pages=10,
        rate_limit_min_s=4.0,
        rate_limit_max_s=10.0,
    ),
    "autoscout24_be": PortalConfig(
        name="AutoScout24 BE",
        base_url="https://www.autoscout24.be",
        countries=["BE"],
        results_per_page=20,
        max_pages=10,
        rate_limit_min_s=4.0,
        rate_limit_max_s=10.0,
    ),
    "autoscout24_at": PortalConfig(
        name="AutoScout24 AT",
        base_url="https://www.autoscout24.at",
        countries=["AT"],
        results_per_page=20,
        max_pages=10,
        rate_limit_min_s=4.0,
        rate_limit_max_s=10.0,
    ),
    "autoscout24_fr": PortalConfig(
        name="AutoScout24 FR",
        base_url="https://www.autoscout24.fr",
        countries=["FR"],
        results_per_page=20,
        max_pages=10,
        rate_limit_min_s=4.0,
        rate_limit_max_s=10.0,
    ),
    "autoscout24_se": PortalConfig(
        name="AutoScout24 SE",
        base_url="https://www.autoscout24.se",
        countries=["SE"],
        results_per_page=20,
        max_pages=8,
        rate_limit_min_s=5.0,
        rate_limit_max_s=12.0,
    ),
    "autoscout24_it": PortalConfig(
        name="AutoScout24 IT",
        base_url="https://www.autoscout24.it",
        countries=["IT"],
        results_per_page=20,
        max_pages=10,
        rate_limit_min_s=4.0,
        rate_limit_max_s=10.0,
    ),
    "mobile_de": PortalConfig(
        name="mobile.de",
        base_url="https://suchen.mobile.de",
        countries=["DE"],
        results_per_page=20,
        max_pages=10,
        rate_limit_min_s=5.0,
        rate_limit_max_s=12.0,
        burst_size=3,
        rate_limit_burst_pause_s=45.0,
    ),
    "willhaben_at": PortalConfig(
        name="willhaben.at",
        base_url="https://www.willhaben.at",
        countries=["AT"],
        results_per_page=25,
        max_pages=8,
        rate_limit_min_s=4.0,
        rate_limit_max_s=10.0,
    ),
    "leboncoin_fr": PortalConfig(
        name="leboncoin.fr",
        base_url="https://www.leboncoin.fr",
        countries=["FR"],
        results_per_page=20,
        max_pages=8,
        rate_limit_min_s=6.0,
        rate_limit_max_s=15.0,
        burst_size=3,
        rate_limit_burst_pause_s=60.0,
        daily_request_cap=1000,
    ),
}


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
SCRAPER_SCHEDULE = {
    "scrape_cron": "0 5 * * 1-5",    # 05:00 lun-ven
    "digest_cron": "0 8 * * 1-5",    # 08:00 lun-ven (dopo scrape)
    "timezone": "Europe/Rome",
}

# Soglie per alert
PRICE_DROP_ALERT_PCT = 5.0        # % drop minimo per alert
DEAL_ALERT_BELOW_MARKET_PCT = 8.0 # % sotto media per "deal alert"
NEW_LISTING_HOURS = 24            # listing nuovi entro N ore


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def get_portal(portal_key: str) -> PortalConfig:
    """Restituisce la config del portale o ValueError."""
    if portal_key not in PORTALS:
        raise ValueError(f"Portale sconosciuto: {portal_key}. Validi: {list(PORTALS.keys())}")
    return PORTALS[portal_key]


def all_portal_keys() -> List[str]:
    """Lista di tutte le chiavi portale configurate."""
    return list(PORTALS.keys())


def portals_for_country(country: str) -> List[str]:
    """Restituisce le chiavi portale che coprono un paese."""
    return [k for k, p in PORTALS.items() if country in p.countries]
