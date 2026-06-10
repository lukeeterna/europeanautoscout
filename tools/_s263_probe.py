r"""S263 PROBE (THROWAWAY — eliminabile dopo il report).

Misura la PROFONDITA' del pool IT per 4 famiglie-trim ESATTE.
NON modifica nulla: sola lettura del mercato AutoScout24.it.
Conta N a OGNI livello L0->L3 con le STESSE chiavi del gate, DOPO dedup.

Run:  python3 -m tools._s263_probe > /tmp/s263.txt 2>&1
"""
from __future__ import annotations

import logging
import statistics
import time

from tools.it_market_price import (
    derive_trim_family, _levels, _match, KM_BAND_DEFAULT, MIN_N_DEFAULT,
)
from tools.scrapers.autoscout_scraper import AutoScoutScraper

logging.basicConfig(level=logging.WARNING, format="%(message)s")

MAKE = "BMW"
MODEL = "Serie 3"
YEAR = 2021
SCRAPE_SPAN = 2          # anno +-2 (come get_it_distribution spec-aware)
DEEP_PAGES = 20          # spingi paginazione al cap curl (MAX_PAGES=20)

# (tag, variant, fuel, transmission, power_hp)
FAMILIES = [
    ("320d xDrive 2021", "320d xDrive", "diesel", "automatic", 190),
    ("318d 2021",        "318d",        "diesel", "automatic", 150),
    ("330i 2021",        "330i",        "petrol", "automatic", 258),
    ("M340 2021",        "M340i xDrive","petrol", "automatic", 374),
]


def scrape_deep():
    """Una sola scrape profonda del model (anno+-2, km-agnostica), riusata
    per tutte le famiglie. Ritorna lista raw di Listing."""
    sc = AutoScoutScraper("autoscout24_it")
    # bump max_pages a DEEP_PAGES (frozen dataclass workaround, come scrape())
    try:
        object.__setattr__(sc.config, "max_pages", DEEP_PAGES)
    except Exception as e:
        print(f"[warn] non riesco a bumpare max_pages: {e}")
    # S264 de-gate REALE: il muro S263 (19 listing) NON era get_total_pages ne'
    # il gate Selenium, ma lo short-page break base_scraper:374-375
    # (len(page)=19 < results_per_page=20 -> break dopo pagina 1). Quando pagina-1
    # torna piena (20) il curl pagina fino a 305/20pag. Forzo results_per_page=1
    # cosi' lo short-page break non scatta mai e il curl pagina fino a max_pages.
    # Probe-local (istanza throwaway), nessun impatto su produzione.
    try:
        object.__setattr__(sc.config, "results_per_page", 1)
    except Exception as e:
        print(f"[warn] results_per_page: {e}")
    t0 = time.time()
    raw = sc.scrape_model(
        make=MAKE, model=MODEL,
        year_min=YEAR - SCRAPE_SPAN, year_max=YEAR + SCRAPE_SPAN,
    )
    print(f"[scrape] {MAKE} {MODEL} {YEAR}+-{SCRAPE_SPAN}: "
          f"{len(raw)} listing grezzi in {time.time()-t0:.1f}s "
          f"(max_pages={DEEP_PAGES})")
    return raw


def dedup(raw):
    """Dedup per listing_id (VIN spesso vuoto su AS24). Ritorna lista unica +
    quanti VIN reali c'erano."""
    seen = {}
    vin_count = 0
    for l in raw:
        if getattr(l, "vin", ""):
            vin_count += 1
        key = getattr(l, "listing_id", "") or getattr(l, "listing_url", "")
        if not key:
            continue
        if key not in seen:
            seen[key] = l
    return list(seen.values()), vin_count


def build_pool(uniq):
    """(listing, cspec, km, year) per i soli con prezzo>0."""
    pool = []
    for lst in uniq:
        price = getattr(lst, "price_eur", 0) or 0
        if price <= 0:
            continue
        ft = getattr(lst, "fuel_type", None)
        ftv = getattr(ft, "value", str(ft)) if ft is not None else ""
        tr = getattr(lst, "transmission", None)
        trv = getattr(tr, "value", str(tr)) if tr is not None else ""
        cspec = derive_trim_family(
            getattr(lst, "variant", "") or "", ftv, trv,
            getattr(lst, "power_hp", 0) or 0,
        )
        pool.append((
            lst, cspec,
            int(getattr(lst, "km", 0) or 0),
            int(getattr(lst, "year", 0) or 0),
        ))
    return pool


def count_levels(tag, variant, fuel, trans, power, pool, n_raw, n_dedup, vin_count):
    target = derive_trim_family(variant, fuel, trans, power)
    levels = _levels(year_span=1)  # year_span influenza solo year_tol L0 (=1)

    # target km per L0: mediana km dei comparabili che matchano a L2
    # (engine+drivetrain+trim+fuel, km-agnostico) -> centra la banda km sul bulk
    cfg_l2 = levels[2]
    l2_km = [p[2] for p in pool
             if _match(target, p[1], p[2], p[3], 0, YEAR, KM_BAND_DEFAULT, cfg_l2)
             and p[2] > 0]
    t_km = int(statistics.median(l2_km)) if l2_km else 50_000

    counts = []
    for cfg in levels:
        n = sum(1 for p in pool
                if _match(target, p[1], p[2], p[3], t_km, YEAR, KM_BAND_DEFAULT, cfg))
        counts.append(n)

    # primo livello (se mai) con N>=MIN_N_DEFAULT
    reach = next((f"L{i}" for i, n in enumerate(counts) if n >= MIN_N_DEFAULT), "MAI")
    print(f"\n=== {tag}  (key={target['key']}, km-target L0={t_km}) ===")
    print(f"  grezzi={n_raw}  dedup={n_dedup}  (VIN reali nel raw={vin_count})  "
          f"pool_prezzato={len(pool)}")
    print(f"  L0={counts[0]}  L1={counts[1]}  L2={counts[2]}  L3={counts[3]}"
          f"   -> N>={MIN_N_DEFAULT} a: {reach}")
    return tag, n_raw, n_dedup, counts, reach


def main():
    print("S263 PROBE — profondita' pool IT (MIN_N_DEFAULT=%d)\n" % MIN_N_DEFAULT)
    raw = scrape_deep()
    uniq, vin_count = dedup(raw)
    pool = build_pool(uniq)
    print(f"[dedup] grezzi={len(raw)} -> dedup={len(uniq)} "
          f"(chiave=listing_id; VIN reali={vin_count}) -> pool_prezzato={len(pool)}")

    rows = []
    for tag, variant, fuel, trans, power in FAMILIES:
        rows.append(count_levels(
            tag, variant, fuel, trans, power, pool,
            len(raw), len(uniq), vin_count,
        ))

    print("\n\n========== TABELLA FINALE ==========")
    print("FAMIGLIA | grezzi | dedup | L0 L1 L2 L3 | N>=8")
    for tag, nr, nd, c, reach in rows:
        print(f"{tag:18} | {nr:4} | {nd:4} | "
              f"{c[0]:2} {c[1]:2} {c[2]:2} {c[3]:2} | {reach}")


if __name__ == "__main__":
    main()
