#!/usr/bin/env python3
"""
Dealer Profiling Collector — Fase 1 [S4] (ARCHITETTURA_E2E.md sez.4/6).

Perno mancante: da URL pagina-dealer AS24 -> inventario commerciale -> data/dealers.db.

ADDITIVO: NON tocca il ramo ricerca (build_search_url / parse_listings / item.price).
Riusa l'infra fetch (_fetch curl_cffi chrome120) + get_total_pages AS-IS dello scraper.
Il data path (__NEXT_DATA__ -> props.pageProps.listings) e' lo stesso della ricerca, ma
le CHIAVI del singolo listing su pagina-dealer differiscono (S286 RUN2, fetch reali):
  - prezzo: listing.prices.public.priceRaw   (NON item.price, che e' null -> 0)
  - anno:   vehicle.firstRegistrationDate.{raw,formatted}
  - km:     vehicle.mileageInKm.formatted
  - nome dealer: pageProps.dealerInfoPage   (NON nel listing-item)
Quindi: ESTRAGGO il raw listings[] (stesso JSON path) + applico un ADATTATORE chiavi
pagina-dealer dedicato. NON riuso _next_data_item_to_listing (userebbe item.price -> 0).

GDPR (confine §0 architettura): persisto SOLO dati commerciali. dealerInfoPage contiene
contact_person/phone/email -> NON li salvo. Schema DB = zero colonne personali.

Idempotente: CREATE TABLE IF NOT EXISTS + upsert ON CONFLICT(dealer_id). Re-run = stesso stato.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.scrapers.autoscout_scraper import AutoScoutScraper  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "dealers.db"
_NEXT_DATA_RE = re.compile(
    r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


# ──────────────────────────────────────────────────────────────────────
# SCHEMA — zero colonne di dati personali (confine GDPR)
# ──────────────────────────────────────────────────────────────────────
def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS dealers (
            dealer_id            TEXT PRIMARY KEY,
            business_name        TEXT,
            as24_dealer_url      TEXT,
            brands               TEXT,   -- JSON array
            price_band_min       INTEGER,
            price_band_max       INTEGER,
            active_listings      INTEGER,
            avg_vehicle_age_days REAL,   -- ETA' VEICOLO (da firstRegistrationDate), NON anzianita'-annuncio
            inventory_snapshot   TEXT,   -- JSON array di vehicle-lite
            first_seen           TEXT,
            last_seen            TEXT
        );

        CREATE TABLE IF NOT EXISTS dealer_profiles (
            dealer_id   TEXT PRIMARY KEY,
            brand_focus TEXT,   -- JSON array (brand ordinati per conteggio)
            provenance  TEXT,
            updated_at  TEXT,
            FOREIGN KEY (dealer_id) REFERENCES dealers(dealer_id)
        );

        -- Metrica-tempo OSSERVATA: l'anzianita'-annuncio non e' leggibile dal JSON
        -- (nessun campo data-pubblicazione nativo), si MISURA osservando run dopo run.
        CREATE TABLE IF NOT EXISTS vehicle_observations (
            dealer_id         TEXT NOT NULL,
            vehicle_key       TEXT NOT NULL,   -- listing.id (UUID nativo)
            first_observed_at TEXT NOT NULL,
            last_observed_at  TEXT NOT NULL,
            status            TEXT NOT NULL DEFAULT 'PRESENT',   -- PRESENT | GONE
            PRIMARY KEY (dealer_id, vehicle_key)
        );
        """
    )
    conn.commit()


def migrate_schema(conn: sqlite3.Connection) -> bool:
    """Rinomina idempotente avg_listing_age_days -> avg_vehicle_age_days.

    CREATE TABLE IF NOT EXISTS non rinomina colonne di tabelle gia' esistenti (S287),
    quindi per i DB gia' creati serve un ALTER guardato da PRAGMA table_info.
    Ritorna True se ha eseguito la rinomina.
    """
    cols = [r[1] for r in conn.execute("PRAGMA table_info(dealers)").fetchall()]
    if cols and "avg_listing_age_days" in cols and "avg_vehicle_age_days" not in cols:
        conn.execute(
            "ALTER TABLE dealers RENAME COLUMN avg_listing_age_days TO avg_vehicle_age_days"
        )
        conn.commit()
        return True
    return False


def _backup_db(src: Path) -> Optional[Path]:
    """Restore-point (vincolo 1d) PRIMA di un ALTER su data/dealers.db.

    SQLite backup API, MAI cp su file SQLite (rule security.md). Il file e' rigenerabile
    dal collector, quindi il backup verificato-per-stat e' sufficiente come reversibilita'.
    """
    if not src.exists():
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = src.with_name(f"{src.stem}.backup-{ts}.db")
    src_conn = sqlite3.connect(src)
    dst_conn = sqlite3.connect(dst)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()
    return dst


# ──────────────────────────────────────────────────────────────────────
# ADATTATORE chiavi pagina-dealer (mapping, NON rewrite)
# ──────────────────────────────────────────────────────────────────────
def _adapt_listing(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Mappa un listing-item della PAGINA-DEALER in un vehicle-lite commerciale."""
    if not isinstance(item, dict):
        return None
    prices = item.get("prices", {}) or {}
    public = prices.get("public", {}) or {}
    price = public.get("priceRaw")
    if price is None:
        dealer_p = prices.get("dealer", {}) or {}
        price = dealer_p.get("priceRaw")

    vehicle = item.get("vehicle", {}) or {}
    make = vehicle.get("make", {})
    make = make.get("formatted") if isinstance(make, dict) else make
    model = vehicle.get("model", {})
    model = model.get("formatted") if isinstance(model, dict) else model

    fr = vehicle.get("firstRegistrationDate", {}) or {}
    first_reg = fr.get("raw") or fr.get("formatted")

    mileage = vehicle.get("mileageInKm", {}) or {}
    km = mileage.get("raw")
    if km is None:
        km_fmt = mileage.get("formatted")
        if km_fmt:
            km = int(re.sub(r"[^\d]", "", str(km_fmt)) or 0)

    return {
        # vehicle_key = listing.id (UUID v4 nativo, stabile per-annuncio). NON hash di
        # contenuto: l'hash col prezzo dentro cambierebbe a ogni ribasso -> falso "venduto".
        "vehicle_key": item.get("id"),
        "make": make,
        "model": model,
        "price": int(price) if isinstance(price, (int, float)) else None,
        "first_registration": first_reg,
        "km": km,
    }


def _first_reg_to_age_days(first_reg: Optional[str], now: datetime) -> Optional[float]:
    """firstRegistrationDate.raw == 'MM-YYYY' (o 'YYYY-MM-...') -> eta' veicolo in giorni."""
    if not first_reg:
        return None
    s = str(first_reg)
    m = re.match(r"^(\d{1,2})-(\d{4})$", s)            # 'MM-YYYY'
    if m:
        mm, yyyy = int(m.group(1)), int(m.group(2))
    else:
        m = re.match(r"^(\d{4})-(\d{1,2})", s)         # 'YYYY-MM...'
        if m:
            yyyy, mm = int(m.group(1)), int(m.group(2))
        else:
            m = re.match(r"^(\d{4})$", s)              # 'YYYY'
            if not m:
                return None
            yyyy, mm = int(m.group(1)), 1
    try:
        reg = datetime(yyyy, max(1, min(12, mm)), 1, tzinfo=timezone.utc)
    except ValueError:
        return None
    return max(0.0, (now - reg).days)


# ──────────────────────────────────────────────────────────────────────
# COLLECTOR — _fetch(dealer_url) + paginazione (get_total_pages AS-IS)
# ──────────────────────────────────────────────────────────────────────
def _extract_page_props(html: str) -> Dict[str, Any]:
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return {}
    try:
        return json.loads(m.group(1)).get("props", {}).get("pageProps", {})
    except (json.JSONDecodeError, ValueError):
        return {}


def collect_dealer(dealer_url: str, portal_key: str = "autoscout24_it") -> Dict[str, Any]:
    scraper = AutoScoutScraper(portal_key)
    html = scraper._fetch(dealer_url)
    pp = _extract_page_props(html)
    if not pp:
        raise RuntimeError(f"__NEXT_DATA__ assente/illeggibile su {dealer_url}")

    declared_results = pp.get("numberOfResults")
    total_pages = scraper.get_total_pages(html)  # AS-IS

    dealer_info = pp.get("dealerInfoPage", {}) or {}
    # GDPR: da dealerInfoPage estraggo SOLO il nome commerciale (customerName).
    # customerPhoneNumbers/contactName/contactPersons = personali -> MAI persistiti.
    business_name = (
        dealer_info.get("customerName")
        or dealer_info.get("companyName")
        or dealer_info.get("name")
    )

    # slug = dealer_id stabile dall'URL /concessionari/{slug}
    slug_m = re.search(r"/concessionari/([^/?#]+)", dealer_url)
    dealer_id = slug_m.group(1) if slug_m else dealer_url

    # raccolta inventario su tutte le pagine
    all_items: List[Dict[str, Any]] = list(pp.get("listings", []) or [])
    pages = total_pages or 1
    fetch_ok = True
    for page in range(2, pages + 1):
        sep = "&" if "?" in dealer_url else "?"
        try:
            page_html = scraper._fetch(f"{dealer_url}{sep}page={page}")
        except Exception as exc:  # noqa: BLE001 — fetch parziale: NIENTE diff GONE (CORREZIONE #2)
            fetch_ok = False
            print(f"[warn] fetch pagina {page} fallita ({exc}) -> run parziale", file=sys.stderr)
            break
        page_pp = _extract_page_props(page_html)
        all_items.extend(page_pp.get("listings", []) or [])

    # run COMPLETO sse: nessun errore fetch AND conteggio raccolto coerente con numberOfResults.
    # Solo allora e' lecito marcare GONE gli assenti (altrimenti valanga di falsi-GONE).
    run_complete = (
        fetch_ok
        and declared_results is not None
        and len(all_items) >= declared_results
    )

    vehicles = [v for v in (_adapt_listing(it) for it in all_items) if v]

    # aggregati commerciali
    now = datetime.now(timezone.utc)
    prices = [v["price"] for v in vehicles if v["price"]]
    ages = [d for d in (_first_reg_to_age_days(v["first_registration"], now) for v in vehicles) if d is not None]
    brand_counts: Dict[str, int] = {}
    for v in vehicles:
        b = v.get("make")
        if b:
            brand_counts[b] = brand_counts.get(b, 0) + 1
    brands_sorted = sorted(brand_counts, key=lambda b: brand_counts[b], reverse=True)

    return {
        "dealer_id": dealer_id,
        "business_name": business_name,
        "as24_dealer_url": dealer_url,
        "brands": brands_sorted,
        "brand_focus": brands_sorted[:3],
        "price_band_min": min(prices) if prices else None,
        "price_band_max": max(prices) if prices else None,
        "active_listings": len(vehicles),
        "declared_results": declared_results,
        "avg_vehicle_age_days": round(sum(ages) / len(ages), 1) if ages else None,
        "inventory_snapshot": vehicles,
        "vehicle_keys": [v["vehicle_key"] for v in vehicles if v.get("vehicle_key")],
        "run_complete": run_complete,
        "provenance": f"AutoScout24 pagina-dealer {dealer_url}",
    }


# ──────────────────────────────────────────────────────────────────────
# METRICA-TEMPO OSSERVATA — snapshot/diff idempotente su vehicle_observations
# ──────────────────────────────────────────────────────────────────────
def snapshot_observations(
    conn: sqlite3.Connection,
    dealer_id: str,
    present_keys: List[str],
    now_iso: str,
    run_complete: bool,
) -> Dict[str, Any]:
    """Registra le osservazioni di questo run e (se completo) marca GONE gli assenti.

    Upsert PRESENT su PK (dealer_id, vehicle_key):
      - nuovo      -> insert first_observed_at=last_observed_at=now, status PRESENT
      - gia' visto -> last_observed_at=now (first_observed_at INVARIATO), status PRESENT
    Diff-GONE (chiavi note ma assenti ORA -> status GONE, MAI delete) SOLO se run_complete
    (CORREZIONE #2): un fetch parziale non deve marcare GONE l'inventario non raccolto.
    """
    inserted = updated = gone = 0
    for vk in present_keys:
        if vk is None:
            continue
        exists = conn.execute(
            "SELECT 1 FROM vehicle_observations WHERE dealer_id=? AND vehicle_key=?",
            (dealer_id, vk),
        ).fetchone()
        if exists is None:
            conn.execute(
                "INSERT INTO vehicle_observations "
                "(dealer_id, vehicle_key, first_observed_at, last_observed_at, status) "
                "VALUES (?, ?, ?, ?, 'PRESENT')",
                (dealer_id, vk, now_iso, now_iso),
            )
            inserted += 1
        else:
            conn.execute(
                "UPDATE vehicle_observations SET last_observed_at=?, status='PRESENT' "
                "WHERE dealer_id=? AND vehicle_key=?",
                (now_iso, dealer_id, vk),
            )
            updated += 1

    diff_ran = bool(run_complete)
    if diff_ran:
        present = {vk for vk in present_keys if vk is not None}
        known = [
            r[0] for r in conn.execute(
                "SELECT vehicle_key FROM vehicle_observations "
                "WHERE dealer_id=? AND status != 'GONE'",
                (dealer_id,),
            ).fetchall()
        ]
        for vk in known:
            if vk not in present:
                conn.execute(
                    "UPDATE vehicle_observations SET status='GONE' "
                    "WHERE dealer_id=? AND vehicle_key=?",
                    (dealer_id, vk),
                )
                gone += 1
    conn.commit()
    return {"inserted": inserted, "updated": updated, "gone": gone, "diff_ran": diff_ran}


# ──────────────────────────────────────────────────────────────────────
# PERSISTENZA — upsert idempotente
# ──────────────────────────────────────────────────────────────────────
def upsert_dealer(conn: sqlite3.Connection, d: Dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO dealers (
            dealer_id, business_name, as24_dealer_url, brands,
            price_band_min, price_band_max, active_listings,
            avg_vehicle_age_days, inventory_snapshot, first_seen, last_seen
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dealer_id) DO UPDATE SET
            business_name        = excluded.business_name,
            as24_dealer_url      = excluded.as24_dealer_url,
            brands               = excluded.brands,
            price_band_min       = excluded.price_band_min,
            price_band_max       = excluded.price_band_max,
            active_listings      = excluded.active_listings,
            avg_vehicle_age_days = excluded.avg_vehicle_age_days,
            inventory_snapshot   = excluded.inventory_snapshot,
            last_seen            = excluded.last_seen
        """,
        (
            d["dealer_id"], d["business_name"], d["as24_dealer_url"],
            json.dumps(d["brands"], ensure_ascii=False),
            d["price_band_min"], d["price_band_max"], d["active_listings"],
            d["avg_vehicle_age_days"],
            json.dumps(d["inventory_snapshot"], ensure_ascii=False),
            now, now,
        ),
    )
    conn.execute(
        """
        INSERT INTO dealer_profiles (dealer_id, brand_focus, provenance, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(dealer_id) DO UPDATE SET
            brand_focus = excluded.brand_focus,
            provenance  = excluded.provenance,
            updated_at  = excluded.updated_at
        """,
        (
            d["dealer_id"],
            json.dumps(d["brand_focus"], ensure_ascii=False),
            d["provenance"], now,
        ),
    )
    conn.commit()


def read_dealer(conn: sqlite3.Connection, dealer_id: str) -> Optional[Tuple]:
    cur = conn.execute(
        """
        SELECT d.business_name, p.brand_focus, d.active_listings, d.avg_vehicle_age_days
        FROM dealers d
        JOIN dealer_profiles p ON p.dealer_id = d.dealer_id
        WHERE d.dealer_id = ?
        """,
        (dealer_id,),
    )
    return cur.fetchone()


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: dealer_collector.py <dealer_url>")
        return 2
    dealer_url = sys.argv[1]
    os.makedirs(DB_PATH.parent, exist_ok=True)

    # vincolo 1d: restore-point PRIMA dell'ALTER su data/dealers.db (source-of-truth)
    if DB_PATH.exists():
        probe = sqlite3.connect(DB_PATH)
        cols = [r[1] for r in probe.execute("PRAGMA table_info(dealers)").fetchall()]
        probe.close()
        if "avg_listing_age_days" in cols and "avg_vehicle_age_days" not in cols:
            bk = _backup_db(DB_PATH)
            print(f"[1d] restore-point pre-migrazione: {bk}", file=sys.stderr)

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        migrate_schema(conn)
        d = collect_dealer(dealer_url)
        upsert_dealer(conn, d)
        obs = snapshot_observations(
            conn, d["dealer_id"], d["vehicle_keys"],
            datetime.now(timezone.utc).isoformat(), d["run_complete"],
        )
        row = read_dealer(conn, d["dealer_id"])
        print(json.dumps({
            "dealer_id": d["dealer_id"],
            "declared_results": d["declared_results"],
            "active_listings": d["active_listings"],
            "run_complete": d["run_complete"],
            "observations": obs,
            "readback": {
                "business_name": row[0],
                "brand_focus": json.loads(row[1]) if row and row[1] else None,
                "active_listings": row[2],
                "avg_vehicle_age_days": row[3],
            },
        }, ensure_ascii=False, indent=2))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
