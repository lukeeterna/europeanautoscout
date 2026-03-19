"""
ARGOS Automotive — Market Intelligence Scrapers
CoVe 2026 | Enterprise Grade

Moduli:
  config              Veicoli target, portali, rate limits, schedule
  models              Dataclass Listing, ScraperRun, PriceChange, MarketTrend, MarketInsight
  db                  Layer SQLite per market_listings, price_changes, scraper_runs, trends
  base_scraper        Classe base astratta con anti-bot, retry, rate limiting
  autoscout_scraper   AutoScout24 multi-country (DE, NL, BE, AT, FR, SE, IT)
  mobile_de_scraper   Scraper Mobile.de (DE) — curl_cffi + ID numerici reali
"""

from .config import PORTALS, get_portal, TARGET_VEHICLES
from .models import Listing, ScraperRun, PriceChange, MarketTrend, MarketInsight
from .base_scraper import BaseScraper
from .mobile_de_scraper import MobileDeScraper

__all__ = [
    "PORTALS",
    "get_portal",
    "TARGET_VEHICLES",
    "Listing",
    "ScraperRun",
    "PriceChange",
    "MarketTrend",
    "MarketInsight",
    "BaseScraper",
    "MobileDeScraper",
]
