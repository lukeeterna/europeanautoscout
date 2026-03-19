"""
models.py -- ARGOS Market Intelligence Data Models
CoVe 2026 | Enterprise Grade

Dataclass per listing, run, price changes, trend, insight.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"
    ELECTRIC = "electric"
    LPG = "lpg"
    CNG = "cng"
    UNKNOWN = "unknown"


class Transmission(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    UNKNOWN = "unknown"


class SellerType(str, Enum):
    DEALER = "dealer"
    PRIVATE = "private"
    UNKNOWN = "unknown"


class InsightType(str, Enum):
    PRICE_DROP = "PRICE_DROP"
    NEW_LISTING = "NEW_LISTING"
    DEAL_ALERT = "DEAL_ALERT"
    TREND_CHANGE = "TREND_CHANGE"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


# ---------------------------------------------------------------------------
# Core Listing
# ---------------------------------------------------------------------------
@dataclass
class Listing:
    """Singolo annuncio veicolo da un portale europeo."""
    listing_id: str                    # ID univoco portale (es. autoscout24_de_123456)
    portal: str                        # chiave portale (es. autoscout24_de)
    country: str                       # ISO 2 (DE, NL, BE, AT, FR, SE, IT)
    make: str                          # BMW, Mercedes, Audi, ...
    model: str                         # Serie 3, Classe C, A4, ...
    variant: str = ""                  # 320d, C220d AMG, ...
    year: int = 0
    km: int = 0
    fuel_type: FuelType = FuelType.UNKNOWN
    transmission: Transmission = Transmission.UNKNOWN
    power_hp: int = 0
    price_eur: float = 0.0            # prezzo convertito in EUR
    currency_original: str = "EUR"     # valuta originale (SEK, CZK, ...)
    seller_type: SellerType = SellerType.UNKNOWN
    seller_name: str = ""
    seller_location: str = ""          # citta/regione venditore
    listing_url: str = ""
    image_urls: List[str] = field(default_factory=list)
    first_seen_at: str = ""            # ISO 8601
    last_seen_at: str = ""             # ISO 8601
    price_current: float = 0.0        # ultimo prezzo visto (puo differire da price_eur iniziale)
    is_active: bool = True
    cove_score: Optional[float] = None  # 0.0-1.0 se valutato da CoVe
    fraud_flags: List[str] = field(default_factory=list)
    extra_data: Dict[str, Any] = field(default_factory=dict)
    vin: str = ""

    def __post_init__(self) -> None:
        now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        if not self.first_seen_at:
            self.first_seen_at = now_iso
        if not self.last_seen_at:
            self.last_seen_at = now_iso
        if self.price_current == 0.0 and self.price_eur > 0:
            self.price_current = self.price_eur

    @property
    def composite_id(self) -> str:
        """ID composto portale + listing_id per dedup cross-portal."""
        return f"{self.portal}_{self.listing_id}"

    def price_changed(self, new_price: float, tolerance_eur: float = 50.0) -> bool:
        """True se il prezzo e' cambiato oltre la tolleranza."""
        return abs(self.price_current - new_price) > tolerance_eur

    def to_dict(self) -> Dict[str, Any]:
        """Serializzazione per DB/JSON."""
        return {
            "listing_id": self.listing_id,
            "portal": self.portal,
            "country": self.country,
            "make": self.make,
            "model": self.model,
            "variant": self.variant,
            "year": self.year,
            "km": self.km,
            "fuel_type": self.fuel_type.value,
            "transmission": self.transmission.value,
            "power_hp": self.power_hp,
            "price_eur": self.price_eur,
            "currency_original": self.currency_original,
            "seller_type": self.seller_type.value,
            "seller_name": self.seller_name,
            "seller_location": self.seller_location,
            "listing_url": self.listing_url,
            "image_urls": ",".join(self.image_urls) if self.image_urls else "",
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "price_current": self.price_current,
            "is_active": int(self.is_active),
            "cove_score": self.cove_score,
            "fraud_flags": ",".join(self.fraud_flags) if self.fraud_flags else "",
            "extra_data": str(self.extra_data) if self.extra_data else "",
            "vin": self.vin,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> Listing:
        """Ricostruisci da riga DB (sqlite3.Row o dict)."""
        img = row.get("image_urls", "")
        flags = row.get("fraud_flags", "")
        return cls(
            listing_id=row["listing_id"],
            portal=row["portal"],
            country=row["country"],
            make=row["make"],
            model=row["model"],
            variant=row.get("variant", ""),
            year=int(row.get("year", 0)),
            km=int(row.get("km", 0)),
            fuel_type=FuelType(row.get("fuel_type", "unknown")),
            transmission=Transmission(row.get("transmission", "unknown")),
            power_hp=int(row.get("power_hp", 0)),
            price_eur=float(row.get("price_eur", 0)),
            currency_original=row.get("currency_original", "EUR"),
            seller_type=SellerType(row.get("seller_type", "unknown")),
            seller_name=row.get("seller_name", ""),
            seller_location=row.get("seller_location", ""),
            listing_url=row.get("listing_url", ""),
            image_urls=img.split(",") if img else [],
            first_seen_at=row.get("first_seen_at", ""),
            last_seen_at=row.get("last_seen_at", ""),
            price_current=float(row.get("price_current", 0)),
            is_active=bool(row.get("is_active", 1)),
            cove_score=row.get("cove_score"),
            fraud_flags=flags.split(",") if flags else [],
            extra_data={},
            vin=row.get("vin", ""),
        )


# ---------------------------------------------------------------------------
# Scraper Run tracking
# ---------------------------------------------------------------------------
@dataclass
class ScraperRun:
    """Tracciamento di una singola esecuzione scraper."""
    run_id: int = 0                    # auto-increment DB
    portal: str = ""
    country: str = ""
    started_at: str = ""               # ISO 8601
    finished_at: str = ""              # ISO 8601
    status: RunStatus = RunStatus.RUNNING
    listings_found: int = 0
    listings_new: int = 0
    listings_updated: int = 0
    price_changes: int = 0
    pages_scraped: int = 0
    errors: List[str] = field(default_factory=list)

    def duration_seconds(self) -> float:
        """Durata del run in secondi, o 0 se non completato."""
        if not self.started_at or not self.finished_at:
            return 0.0
        try:
            t0 = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(self.finished_at.replace("Z", "+00:00"))
            return (t1 - t0).total_seconds()
        except (ValueError, TypeError):
            return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "portal": self.portal,
            "country": self.country,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status.value,
            "listings_found": self.listings_found,
            "listings_new": self.listings_new,
            "listings_updated": self.listings_updated,
            "price_changes": self.price_changes,
            "pages_scraped": self.pages_scraped,
            "errors": "|".join(self.errors) if self.errors else "",
        }


# ---------------------------------------------------------------------------
# Price Change
# ---------------------------------------------------------------------------
@dataclass
class PriceChange:
    """Variazione prezzo rilevata su un listing."""
    listing_id: str
    portal: str = ""
    old_price: float = 0.0
    new_price: float = 0.0
    change_pct: float = 0.0
    recorded_at: str = ""              # ISO 8601

    def __post_init__(self) -> None:
        if not self.recorded_at:
            self.recorded_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        if self.old_price > 0 and self.change_pct == 0.0:
            self.change_pct = round(
                ((self.new_price - self.old_price) / self.old_price) * 100, 2
            )

    @property
    def is_drop(self) -> bool:
        return self.new_price < self.old_price

    @property
    def abs_change(self) -> float:
        return abs(self.new_price - self.old_price)


# ---------------------------------------------------------------------------
# Market Trend (aggregato giornaliero)
# ---------------------------------------------------------------------------
@dataclass
class MarketTrend:
    """Trend giornaliero aggregato per make/model/country."""
    date: str                          # YYYY-MM-DD
    make: str
    model: str
    country: str
    avg_price: float = 0.0
    median_price: float = 0.0
    min_price: float = 0.0
    max_price: float = 0.0
    count_active: int = 0
    avg_km: float = 0.0
    avg_year: float = 0.0
    new_listings: int = 0
    removed_listings: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "make": self.make,
            "model": self.model,
            "country": self.country,
            "avg_price": self.avg_price,
            "median_price": self.median_price,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "count_active": self.count_active,
            "avg_km": self.avg_km,
            "avg_year": self.avg_year,
            "new_listings": self.new_listings,
            "removed_listings": self.removed_listings,
        }


# ---------------------------------------------------------------------------
# Market Insight (alert/segnalazione)
# ---------------------------------------------------------------------------
@dataclass
class MarketInsight:
    """Segnalazione generata dal sistema di intelligence."""
    insight_type: InsightType
    severity: Severity = Severity.MEDIUM
    make: str = ""
    model: str = ""
    country: str = ""
    listing_id: str = ""
    summary: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_type": self.insight_type.value,
            "severity": self.severity.value,
            "make": self.make,
            "model": self.model,
            "country": self.country,
            "listing_id": self.listing_id,
            "summary": self.summary,
            "data": str(self.data),
            "created_at": self.created_at,
        }
