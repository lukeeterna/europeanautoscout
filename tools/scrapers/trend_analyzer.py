"""
ARGOS™ Market Intelligence — Trend Analyzer
Analizza i dati scrappati e genera insight actionable.

Responsabilità:
  - Calcola aggregati giornalieri per make/model/country
  - Rileva price drops significativi
  - Identifica deal alerts (prezzo sotto media)
  - Genera digest per notifica Telegram
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Optional

DB_PATH = os.environ.get(
    'ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite')
)


@dataclass
class MarketInsight:
    insight_type: str   # PRICE_DROP, DEAL_ALERT, NEW_LISTINGS, TREND_CHANGE, SOLD_FAST
    severity: str       # INFO, NOTABLE, ALERT
    make: str
    model: str
    country: str
    message: str
    data: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.row_factory = sqlite3.Row
    return con


def compute_daily_trends(date_str: Optional[str] = None) -> int:
    """Calcola aggregati giornalieri dalla tabella market_listings.
    Ritorna il numero di trend calcolati."""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')

    con = _connect()
    try:
        # Aggregati per make/model/country
        rows = con.execute("""
            SELECT make, model, country,
                   COUNT(*) as listing_count,
                   AVG(price_eur) as avg_price,
                   MIN(price_eur) as min_price,
                   MAX(price_eur) as max_price,
                   AVG(km) as avg_km
            FROM market_listings
            WHERE is_active = 1
              AND price_eur > 0
            GROUP BY make, model, country
            HAVING COUNT(*) >= 2
        """).fetchall()

        count = 0
        for row in rows:
            # Cerca il trend del giorno precedente per calcolare delta
            prev = con.execute("""
                SELECT avg_price FROM market_trends
                WHERE make = ? AND model = ? AND country = ?
                  AND date < ?
                ORDER BY date DESC LIMIT 1
            """, [row['make'], row['model'], row['country'], date_str]).fetchone()

            delta_pct = None
            if prev and prev['avg_price'] and prev['avg_price'] > 0:
                delta_pct = ((row['avg_price'] - prev['avg_price']) / prev['avg_price']) * 100

            # Calcola mediana manualmente
            prices = con.execute("""
                SELECT price_eur FROM market_listings
                WHERE make = ? AND model = ? AND country = ?
                  AND is_active = 1 AND price_eur > 0
                ORDER BY price_eur
            """, [row['make'], row['model'], row['country']]).fetchall()

            median_price = None
            if prices:
                n = len(prices)
                mid = n // 2
                if n % 2 == 0:
                    median_price = (prices[mid - 1]['price_eur'] + prices[mid]['price_eur']) // 2
                else:
                    median_price = prices[mid]['price_eur']

            con.execute("""
                INSERT INTO market_trends
                    (date, make, model, country, avg_price, median_price,
                     min_price, max_price, listing_count, avg_km, price_delta_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date, make, model, country) DO UPDATE SET
                    avg_price = excluded.avg_price,
                    median_price = excluded.median_price,
                    min_price = excluded.min_price,
                    max_price = excluded.max_price,
                    listing_count = excluded.listing_count,
                    avg_km = excluded.avg_km,
                    price_delta_pct = excluded.price_delta_pct
            """, [
                date_str, row['make'], row['model'], row['country'],
                int(row['avg_price']), median_price,
                row['min_price'], row['max_price'],
                row['listing_count'], int(row['avg_km']) if row['avg_km'] else None,
                round(delta_pct, 2) if delta_pct is not None else None
            ])
            count += 1

        con.commit()
        return count
    finally:
        con.close()


def detect_price_drops(threshold_pct: float = -3.0, days: int = 7) -> List[MarketInsight]:
    """Rileva modelli con calo prezzo significativo negli ultimi N giorni."""
    con = _connect()
    insights = []
    try:
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = con.execute("""
            SELECT t1.make, t1.model, t1.country,
                   t1.avg_price as price_now,
                   t2.avg_price as price_before,
                   ((t1.avg_price - t2.avg_price) * 100.0 / t2.avg_price) as delta_pct
            FROM market_trends t1
            JOIN market_trends t2
              ON t1.make = t2.make AND t1.model = t2.model AND t1.country = t2.country
            WHERE t1.date = (SELECT MAX(date) FROM market_trends)
              AND t2.date <= ?
              AND t2.date = (
                  SELECT MIN(date) FROM market_trends
                  WHERE make = t1.make AND model = t1.model
                    AND country = t1.country AND date >= ?
              )
              AND ((t1.avg_price - t2.avg_price) * 100.0 / t2.avg_price) <= ?
              AND t2.avg_price > 0
            ORDER BY delta_pct ASC
        """, [cutoff, cutoff, threshold_pct]).fetchall()

        for row in rows:
            insights.append(MarketInsight(
                insight_type='PRICE_DROP',
                severity='ALERT' if row['delta_pct'] <= -5.0 else 'NOTABLE',
                make=row['make'],
                model=row['model'],
                country=row['country'],
                message=(
                    f"{row['make']} {row['model']} {row['country']}: "
                    f"{row['delta_pct']:+.1f}% in {days}gg "
                    f"(€{int(row['price_before']):,} → €{int(row['price_now']):,})"
                ),
                data={
                    'price_before': int(row['price_before']),
                    'price_now': int(row['price_now']),
                    'delta_pct': round(row['delta_pct'], 2),
                    'days': days,
                }
            ))
    finally:
        con.close()
    return insights


def detect_deal_alerts(threshold_pct: float = 15.0) -> List[MarketInsight]:
    """Trova listing con prezzo significativamente sotto la media del segmento."""
    con = _connect()
    insights = []
    try:
        rows = con.execute("""
            SELECT ml.listing_id, ml.make, ml.model, ml.variant, ml.year,
                   ml.km, ml.price_eur, ml.country, ml.listing_url,
                   mt.avg_price, mt.median_price,
                   ((mt.avg_price - ml.price_eur) * 100.0 / mt.avg_price) as discount_pct
            FROM market_listings ml
            JOIN market_trends mt
              ON ml.make = mt.make AND ml.model = mt.model AND ml.country = mt.country
            WHERE ml.is_active = 1
              AND mt.date = (SELECT MAX(date) FROM market_trends WHERE make = ml.make AND model = ml.model)
              AND mt.avg_price > 0
              AND ((mt.avg_price - ml.price_eur) * 100.0 / mt.avg_price) >= ?
              AND ml.price_eur > 5000
            ORDER BY discount_pct DESC
            LIMIT 20
        """, [threshold_pct]).fetchall()

        for row in rows:
            insights.append(MarketInsight(
                insight_type='DEAL_ALERT',
                severity='ALERT' if row['discount_pct'] >= 25 else 'NOTABLE',
                make=row['make'],
                model=row['model'],
                country=row['country'],
                message=(
                    f"DEAL: {row['make']} {row['model']} {row['variant'] or ''} "
                    f"{row['year']} — €{row['price_eur']:,} "
                    f"({row['discount_pct']:.0f}% sotto media €{int(row['avg_price']):,}) "
                    f"[{row['country']}]"
                ),
                data={
                    'listing_id': row['listing_id'],
                    'price': row['price_eur'],
                    'avg_price': int(row['avg_price']),
                    'discount_pct': round(row['discount_pct'], 1),
                    'km': row['km'],
                    'year': row['year'],
                    'url': row['listing_url'],
                }
            ))
    finally:
        con.close()
    return insights


def detect_new_listings_summary(hours: int = 24) -> List[MarketInsight]:
    """Conta nuovi listing per make nelle ultime N ore."""
    con = _connect()
    insights = []
    try:
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        rows = con.execute("""
            SELECT make, model, country, COUNT(*) as new_count,
                   AVG(price_eur) as avg_price
            FROM market_listings
            WHERE first_seen_at >= ?
              AND is_active = 1
            GROUP BY make, model, country
            HAVING COUNT(*) >= 3
            ORDER BY new_count DESC
        """, [cutoff]).fetchall()

        for row in rows:
            insights.append(MarketInsight(
                insight_type='NEW_LISTINGS',
                severity='INFO',
                make=row['make'],
                model=row['model'],
                country=row['country'],
                message=(
                    f"{row['new_count']} nuovi {row['make']} {row['model']} "
                    f"in {row['country']} (avg €{int(row['avg_price']):,})"
                ),
                data={
                    'count': row['new_count'],
                    'avg_price': int(row['avg_price']),
                }
            ))
    finally:
        con.close()
    return insights


def generate_full_digest() -> dict:
    """Genera digest completo per notifica Telegram."""
    # Calcola trend
    trends_count = compute_daily_trends()

    # Raccogli insight
    price_drops = detect_price_drops(threshold_pct=-3.0, days=7)
    deals = detect_deal_alerts(threshold_pct=15.0)
    new_listings = detect_new_listings_summary(hours=24)

    # Statistiche globali
    con = _connect()
    try:
        stats = con.execute("""
            SELECT COUNT(*) as total_active,
                   COUNT(DISTINCT make || model || country) as segments,
                   COUNT(DISTINCT country) as countries,
                   COUNT(DISTINCT portal) as portals
            FROM market_listings WHERE is_active = 1
        """).fetchone()

        new_24h = con.execute("""
            SELECT COUNT(*) as c FROM market_listings
            WHERE first_seen_at >= datetime('now', '-24 hours') AND is_active = 1
        """).fetchone()

        removed_24h = con.execute("""
            SELECT COUNT(*) as c FROM market_listings
            WHERE is_active = 0 AND last_seen_at >= datetime('now', '-24 hours')
        """).fetchone()
    finally:
        con.close()

    return {
        'timestamp': datetime.now().isoformat(),
        'trends_computed': trends_count,
        'insights': {
            'price_drops': [asdict(i) for i in price_drops],
            'deals': [asdict(i) for i in deals],
            'new_listings': [asdict(i) for i in new_listings],
        },
        'stats': {
            'total_active': stats['total_active'] if stats else 0,
            'segments': stats['segments'] if stats else 0,
            'countries': stats['countries'] if stats else 0,
            'portals': stats['portals'] if stats else 0,
            'new_24h': new_24h['c'] if new_24h else 0,
            'removed_24h': removed_24h['c'] if removed_24h else 0,
        },
    }


def format_telegram_digest(digest: dict) -> str:
    """Formatta il digest per Telegram (plain text, no Markdown problemi)."""
    lines = [
        f"ARGOS MARKET INTELLIGENCE — {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
    ]

    # Price drops
    drops = digest['insights']['price_drops']
    if drops:
        lines.append("PRICE DROPS (7gg):")
        for d in drops[:5]:
            lines.append(f"  {d['message']}")
        lines.append("")

    # Deal alerts
    deals = digest['insights']['deals']
    if deals:
        lines.append("DEAL ALERTS:")
        for d in deals[:5]:
            lines.append(f"  {d['message']}")
        lines.append("")

    # New listings
    new = digest['insights']['new_listings']
    if new:
        lines.append("NUOVI LISTING (24h):")
        for n in new[:5]:
            lines.append(f"  {n['message']}")
        lines.append("")

    # Stats
    s = digest['stats']
    lines.append(
        f"Totale: {s['total_active']} listing attivi | "
        f"{s['new_24h']} nuovi | {s['removed_24h']} rimossi | "
        f"{s['countries']} paesi | {s['portals']} portali"
    )

    return '\n'.join(lines)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    digest = generate_full_digest()
    print(format_telegram_digest(digest))
    print(f"\n--- Raw digest: {json.dumps(digest, indent=2, default=str)}")
