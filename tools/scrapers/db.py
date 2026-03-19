"""
db.py -- ARGOS Market Intelligence Database Layer
CoVe 2026 | Enterprise Grade

SQLite WAL, prepared statements, transazioni esplicite.
Pattern da wa-intelligence/dashboard/db.py.
"""

from __future__ import annotations
import os
import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    Listing, ScraperRun, PriceChange, MarketTrend, MarketInsight,
    RunStatus, InsightType, Severity,
)
from .config import PRICE_DROP_ALERT_PCT, DEAL_ALERT_BELOW_MARKET_PCT, NEW_LISTING_HOURS

DB_PATH = os.environ.get(
    'ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite')
)


def _connect() -> sqlite3.Connection:
    """Connessione con WAL mode e busy timeout."""
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=10000')
    con.execute('PRAGMA foreign_keys=ON')
    return con


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS market_listings (
    listing_id      TEXT NOT NULL,
    portal          TEXT NOT NULL,
    country         TEXT NOT NULL DEFAULT '',
    make            TEXT NOT NULL DEFAULT '',
    model           TEXT NOT NULL DEFAULT '',
    variant         TEXT DEFAULT '',
    year            INTEGER DEFAULT 0,
    km              INTEGER DEFAULT 0,
    fuel_type       TEXT DEFAULT 'unknown',
    transmission    TEXT DEFAULT 'unknown',
    power_hp        INTEGER DEFAULT 0,
    price_eur       REAL DEFAULT 0,
    currency_original TEXT DEFAULT 'EUR',
    seller_type     TEXT DEFAULT 'unknown',
    seller_name     TEXT DEFAULT '',
    seller_location TEXT DEFAULT '',
    listing_url     TEXT DEFAULT '',
    image_urls      TEXT DEFAULT '',
    first_seen_at   TEXT DEFAULT '',
    last_seen_at    TEXT DEFAULT '',
    price_current   REAL DEFAULT 0,
    is_active       INTEGER DEFAULT 1,
    cove_score      REAL,
    fraud_flags     TEXT DEFAULT '',
    extra_data      TEXT DEFAULT '',
    vin             TEXT DEFAULT '',
    PRIMARY KEY (portal, listing_id)
);

CREATE INDEX IF NOT EXISTS idx_ml_make_model ON market_listings(make, model);
CREATE INDEX IF NOT EXISTS idx_ml_country ON market_listings(country);
CREATE INDEX IF NOT EXISTS idx_ml_price ON market_listings(price_current);
CREATE INDEX IF NOT EXISTS idx_ml_active ON market_listings(is_active);
CREATE INDEX IF NOT EXISTS idx_ml_first_seen ON market_listings(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_ml_last_seen ON market_listings(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_ml_vin ON market_listings(vin) WHERE vin != '';

CREATE TABLE IF NOT EXISTS market_price_changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id      TEXT NOT NULL,
    portal          TEXT NOT NULL DEFAULT '',
    old_price       REAL NOT NULL,
    new_price       REAL NOT NULL,
    change_pct      REAL NOT NULL DEFAULT 0,
    recorded_at     TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_pc_listing ON market_price_changes(listing_id);
CREATE INDEX IF NOT EXISTS idx_pc_recorded ON market_price_changes(recorded_at);
CREATE INDEX IF NOT EXISTS idx_pc_change ON market_price_changes(change_pct);

CREATE TABLE IF NOT EXISTS market_scraper_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    portal          TEXT NOT NULL DEFAULT '',
    country         TEXT NOT NULL DEFAULT '',
    started_at      TEXT NOT NULL DEFAULT '',
    finished_at     TEXT DEFAULT '',
    status          TEXT DEFAULT 'RUNNING',
    listings_found  INTEGER DEFAULT 0,
    listings_new    INTEGER DEFAULT 0,
    listings_updated INTEGER DEFAULT 0,
    price_changes   INTEGER DEFAULT 0,
    pages_scraped   INTEGER DEFAULT 0,
    errors          TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_sr_portal ON market_scraper_runs(portal);
CREATE INDEX IF NOT EXISTS idx_sr_status ON market_scraper_runs(status);

CREATE TABLE IF NOT EXISTS market_daily_trends (
    date            TEXT NOT NULL,
    make            TEXT NOT NULL,
    model           TEXT NOT NULL,
    country         TEXT NOT NULL,
    avg_price       REAL DEFAULT 0,
    median_price    REAL DEFAULT 0,
    min_price       REAL DEFAULT 0,
    max_price       REAL DEFAULT 0,
    count_active    INTEGER DEFAULT 0,
    avg_km          REAL DEFAULT 0,
    avg_year        REAL DEFAULT 0,
    new_listings    INTEGER DEFAULT 0,
    removed_listings INTEGER DEFAULT 0,
    PRIMARY KEY (date, make, model, country)
);

CREATE TABLE IF NOT EXISTS market_insights (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_type    TEXT NOT NULL,
    severity        TEXT DEFAULT 'medium',
    make            TEXT DEFAULT '',
    model           TEXT DEFAULT '',
    country         TEXT DEFAULT '',
    listing_id      TEXT DEFAULT '',
    summary         TEXT DEFAULT '',
    data            TEXT DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_mi_type ON market_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_mi_created ON market_insights(created_at);
"""


def ensure_market_schema() -> None:
    """Crea tutte le tabelle e gli indici per market intelligence."""
    con = _connect()
    try:
        con.executescript(_SCHEMA_SQL)
        con.commit()
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Listings CRUD
# ---------------------------------------------------------------------------
def upsert_listing(listing: Listing) -> Tuple[str, Optional[PriceChange]]:
    """
    Inserisci o aggiorna un listing.
    Ritorna ("new"|"updated"|"unchanged", PriceChange o None).
    """
    con = _connect()
    try:
        existing = con.execute(
            "SELECT price_current, first_seen_at FROM market_listings "
            "WHERE portal=? AND listing_id=?",
            (listing.portal, listing.listing_id)
        ).fetchone()

        price_change: Optional[PriceChange] = None

        if existing is None:
            # Nuovo listing
            d = listing.to_dict()
            cols = ", ".join(d.keys())
            placeholders = ", ".join(["?"] * len(d))
            con.execute(
                f"INSERT INTO market_listings ({cols}) VALUES ({placeholders})",
                list(d.values())
            )
            con.commit()
            return ("new", None)

        # Listing esistente: aggiorna last_seen e verifica prezzo
        old_price = float(existing["price_current"])
        listing.first_seen_at = existing["first_seen_at"]  # preserva data originale

        if listing.price_changed(old_price):
            price_change = PriceChange(
                listing_id=listing.listing_id,
                portal=listing.portal,
                old_price=old_price,
                new_price=listing.price_current,
            )
            _insert_price_change(con, price_change)

        con.execute(
            "UPDATE market_listings SET "
            "last_seen_at=?, price_current=?, is_active=1, "
            "km=?, seller_name=?, seller_location=?, image_urls=?, "
            "variant=?, fuel_type=?, transmission=?, power_hp=?, "
            "extra_data=?, vin=? "
            "WHERE portal=? AND listing_id=?",
            (
                listing.last_seen_at, listing.price_current,
                listing.km, listing.seller_name, listing.seller_location,
                ",".join(listing.image_urls) if listing.image_urls else "",
                listing.variant, listing.fuel_type.value,
                listing.transmission.value, listing.power_hp,
                str(listing.extra_data) if listing.extra_data else "",
                listing.vin,
                listing.portal, listing.listing_id,
            )
        )
        con.commit()

        status = "updated" if price_change else "unchanged"
        return (status, price_change)
    finally:
        con.close()


def _insert_price_change(con: sqlite3.Connection, pc: PriceChange) -> None:
    """Inserisci un record price_change (dentro transazione esistente)."""
    con.execute(
        "INSERT INTO market_price_changes "
        "(listing_id, portal, old_price, new_price, change_pct, recorded_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (pc.listing_id, pc.portal, pc.old_price, pc.new_price,
         pc.change_pct, pc.recorded_at)
    )


def record_price_change(pc: PriceChange) -> None:
    """Registra una variazione prezzo (standalone)."""
    con = _connect()
    try:
        _insert_price_change(con, pc)
        con.commit()
    finally:
        con.close()


def mark_inactive(portal: str, active_ids: List[str]) -> int:
    """
    Segna come inattivi i listing del portale NON presenti in active_ids.
    Ritorna il numero di listing disattivati.
    """
    if not active_ids:
        return 0

    con = _connect()
    try:
        placeholders = ",".join(["?"] * len(active_ids))
        cur = con.execute(
            f"UPDATE market_listings SET is_active=0, last_seen_at=? "
            f"WHERE portal=? AND is_active=1 AND listing_id NOT IN ({placeholders})",
            [_now_iso(), portal] + active_ids
        )
        con.commit()
        return cur.rowcount
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Scraper Runs
# ---------------------------------------------------------------------------
def start_run(portal: str, country: str) -> int:
    """Registra inizio run, ritorna run_id."""
    con = _connect()
    try:
        cur = con.execute(
            "INSERT INTO market_scraper_runs (portal, country, started_at, status) "
            "VALUES (?, ?, ?, ?)",
            (portal, country, _now_iso(), RunStatus.RUNNING.value)
        )
        con.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        con.close()


def finish_run(run: ScraperRun) -> None:
    """Aggiorna un run completato."""
    con = _connect()
    try:
        con.execute(
            "UPDATE market_scraper_runs SET "
            "finished_at=?, status=?, listings_found=?, listings_new=?, "
            "listings_updated=?, price_changes=?, pages_scraped=?, errors=? "
            "WHERE run_id=?",
            (
                run.finished_at or _now_iso(),
                run.status.value,
                run.listings_found,
                run.listings_new,
                run.listings_updated,
                run.price_changes,
                run.pages_scraped,
                "|".join(run.errors) if run.errors else "",
                run.run_id,
            )
        )
        con.commit()
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Trend giornalieri
# ---------------------------------------------------------------------------
def compute_daily_trends(date_str: Optional[str] = None) -> List[MarketTrend]:
    """
    Calcola trend giornalieri per ogni make/model/country.
    Se date_str e' None, usa la data odierna UTC.
    """
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    yesterday = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    con = _connect()
    try:
        # Gruppi attivi per make/model/country
        rows = con.execute(
            "SELECT make, model, country, "
            "  AVG(price_current) as avg_p, MIN(price_current) as min_p, "
            "  MAX(price_current) as max_p, COUNT(*) as cnt, "
            "  AVG(km) as avg_k, AVG(year) as avg_y "
            "FROM market_listings "
            "WHERE is_active=1 AND price_current > 0 "
            "GROUP BY make, model, country"
        ).fetchall()

        trends: List[MarketTrend] = []

        for r in rows:
            make, model, country = r["make"], r["model"], r["country"]

            # Mediana (calcolata in Python perche SQLite non ha MEDIAN)
            prices = con.execute(
                "SELECT price_current FROM market_listings "
                "WHERE is_active=1 AND make=? AND model=? AND country=? "
                "AND price_current > 0 ORDER BY price_current",
                (make, model, country)
            ).fetchall()
            median_p = statistics.median([p["price_current"] for p in prices]) if prices else 0.0

            # Nuovi listing (first_seen oggi)
            new_count = con.execute(
                "SELECT COUNT(*) as c FROM market_listings "
                "WHERE make=? AND model=? AND country=? "
                "AND first_seen_at >= ?",
                (make, model, country, f"{date_str}T00:00:00Z")
            ).fetchone()["c"]

            # Rimossi (attivi ieri, non piu attivi oggi)
            removed_count = con.execute(
                "SELECT COUNT(*) as c FROM market_listings "
                "WHERE make=? AND model=? AND country=? "
                "AND is_active=0 AND last_seen_at >= ? AND last_seen_at < ?",
                (make, model, country,
                 f"{yesterday}T00:00:00Z", f"{date_str}T00:00:00Z")
            ).fetchone()["c"]

            trend = MarketTrend(
                date=date_str,
                make=make,
                model=model,
                country=country,
                avg_price=round(r["avg_p"], 2),
                median_price=round(median_p, 2),
                min_price=round(r["min_p"], 2),
                max_price=round(r["max_p"], 2),
                count_active=r["cnt"],
                avg_km=round(r["avg_k"], 0),
                avg_year=round(r["avg_y"], 1),
                new_listings=new_count,
                removed_listings=removed_count,
            )
            trends.append(trend)

            # Upsert nel DB
            d = trend.to_dict()
            con.execute(
                "INSERT OR REPLACE INTO market_daily_trends "
                "(date, make, model, country, avg_price, median_price, "
                "min_price, max_price, count_active, avg_km, avg_year, "
                "new_listings, removed_listings) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    d["date"], d["make"], d["model"], d["country"],
                    d["avg_price"], d["median_price"], d["min_price"],
                    d["max_price"], d["count_active"], d["avg_km"],
                    d["avg_year"], d["new_listings"], d["removed_listings"],
                )
            )

        con.commit()
        return trends
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Query per alert/insight
# ---------------------------------------------------------------------------
def get_price_drops(
    min_pct: float = PRICE_DROP_ALERT_PCT,
    hours: int = 24,
) -> List[Dict[str, Any]]:
    """Listing con calo prezzo >= min_pct nelle ultime N ore."""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    con = _connect()
    try:
        rows = con.execute(
            "SELECT pc.listing_id, pc.portal, pc.old_price, pc.new_price, "
            "  pc.change_pct, pc.recorded_at, "
            "  ml.make, ml.model, ml.variant, ml.year, ml.km, "
            "  ml.listing_url, ml.country "
            "FROM market_price_changes pc "
            "JOIN market_listings ml ON pc.portal=ml.portal AND pc.listing_id=ml.listing_id "
            "WHERE pc.change_pct <= ? AND pc.recorded_at >= ? "
            "ORDER BY pc.change_pct ASC",
            (-min_pct, cutoff)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def get_new_listings(hours: int = NEW_LISTING_HOURS) -> List[Dict[str, Any]]:
    """Listing nuovi nelle ultime N ore."""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    con = _connect()
    try:
        rows = con.execute(
            "SELECT listing_id, portal, make, model, variant, year, km, "
            "  price_current, country, seller_type, listing_url, first_seen_at "
            "FROM market_listings "
            "WHERE is_active=1 AND first_seen_at >= ? "
            "ORDER BY first_seen_at DESC",
            (cutoff,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def get_deal_alerts(min_below_pct: float = DEAL_ALERT_BELOW_MARKET_PCT) -> List[Dict[str, Any]]:
    """
    Listing attivi con prezzo >= min_below_pct sotto la media del gruppo
    (make/model/country). Potenziali affari.
    """
    con = _connect()
    try:
        # Media per gruppo
        avgs = con.execute(
            "SELECT make, model, country, AVG(price_current) as avg_p, COUNT(*) as cnt "
            "FROM market_listings "
            "WHERE is_active=1 AND price_current > 0 "
            "GROUP BY make, model, country "
            "HAVING cnt >= 3"
        ).fetchall()

        deals: List[Dict[str, Any]] = []

        for avg_row in avgs:
            avg_price = avg_row["avg_p"]
            threshold = avg_price * (1 - min_below_pct / 100.0)

            rows = con.execute(
                "SELECT listing_id, portal, make, model, variant, year, km, "
                "  price_current, country, seller_type, listing_url "
                "FROM market_listings "
                "WHERE is_active=1 AND make=? AND model=? AND country=? "
                "AND price_current > 0 AND price_current <= ? "
                "ORDER BY price_current ASC",
                (avg_row["make"], avg_row["model"], avg_row["country"], threshold)
            ).fetchall()

            for r in rows:
                d = dict(r)
                d["avg_market_price"] = round(avg_price, 2)
                d["below_avg_pct"] = round(
                    ((avg_price - d["price_current"]) / avg_price) * 100, 2
                )
                deals.append(d)

        deals.sort(key=lambda x: x.get("below_avg_pct", 0), reverse=True)
        return deals
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Statistiche generali
# ---------------------------------------------------------------------------
def get_market_stats() -> Dict[str, Any]:
    """Statistiche globali del market DB."""
    con = _connect()
    try:
        total = con.execute(
            "SELECT COUNT(*) as c FROM market_listings"
        ).fetchone()["c"]
        active = con.execute(
            "SELECT COUNT(*) as c FROM market_listings WHERE is_active=1"
        ).fetchone()["c"]
        portals = con.execute(
            "SELECT portal, COUNT(*) as c FROM market_listings "
            "GROUP BY portal ORDER BY c DESC"
        ).fetchall()
        countries = con.execute(
            "SELECT country, COUNT(*) as c FROM market_listings "
            "WHERE is_active=1 GROUP BY country ORDER BY c DESC"
        ).fetchall()
        recent_runs = con.execute(
            "SELECT * FROM market_scraper_runs ORDER BY run_id DESC LIMIT 10"
        ).fetchall()
        price_changes_24h = con.execute(
            "SELECT COUNT(*) as c FROM market_price_changes "
            "WHERE recorded_at >= ?",
            ((datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ"),)
        ).fetchone()["c"]

        return {
            "total_listings": total,
            "active_listings": active,
            "inactive_listings": total - active,
            "portals": {r["portal"]: r["c"] for r in portals},
            "countries": {r["country"]: r["c"] for r in countries},
            "price_changes_24h": price_changes_24h,
            "recent_runs": [dict(r) for r in recent_runs],
        }
    finally:
        con.close()
