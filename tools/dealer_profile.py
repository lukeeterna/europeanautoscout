#!/usr/bin/env python3
"""
dealer_profile.py — Estrattore DETERMINISTICO di profilo dealer da pagina AS24.

MANDATO (UNITÀ A): dato l'URL pubblico AS24 di un dealer, estrae in JSON:
  nome, località, stock_count, top_brands, top_segment, 1-2 veicoli esempio.

REGOLA FERREA (anti-invenzione): SOLO campi presenti nella pagina.
  Campo non derivabile dai dati = null. MAI stimato, MAI euristica, MAI fallback plausibile.
  (Distinzione da profile_dealers_s106.py che STIMA archetipo/premium_pct — qui NO.)

Riusa lo scraper verificato (AutoScoutScraper.fetch + parse_listings + get_total_pages),
non reimplementa parsing. Rispetta i limiti scraper (rate-limit interno di fetch()) — IMMUTABILI.

Uso:
  python3 tools/dealer_profile.py --url "<AS24_dealer_url>" [--out profilo.json]
  python3 tools/dealer_profile.py --html-file page.html --country IT   # offline
  python3 tools/dealer_profile.py --selftest                            # aggregazione pura
"""

import argparse
import json
import os
import sys
from collections import Counter
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrapers"))
from models import Listing  # noqa: E402


def _most_common_nonempty(values: List[str]) -> Optional[str]:
    """Valore stringa più frequente tra i non-vuoti, o None se tutti vuoti."""
    cnt = Counter(v.strip() for v in values if v and v.strip())
    if not cnt:
        return None
    return cnt.most_common(1)[0][0]


def aggregate_profile(
    listings: List[Listing],
    declared_total: Optional[int],
    *,
    url: Optional[str] = None,
) -> dict:
    """Aggrega una lista di Listing in un profilo dealer. FUNZIONE PURA.

    Ogni campo NON derivabile dai dati presenti → None (mai stimato).
    - name/location: valore più frequente tra i seller_* non-vuoti (fatto presente).
    - stock_count: SOLO il totale dichiarato da AS24 (numberOfResults). len(listings) di
      una pagina sarebbe un floor parziale → NON usato come stima. Assente → None.
    - top_brands: marche realmente presenti negli annunci, ordinate per frequenza. [] se nessuna.
    - top_segment: AS24 Listing NON espone un campo "segmento" → None (nessuna fonte, no stima).
      top_models porta il fatto presente (marca+modello effettivi).
    - example_vehicles: SOLO annunci con marca+modello+anno+prezzo TUTTI presenti (max 2).
    """
    name = _most_common_nonempty([l.seller_name for l in listings])
    location = _most_common_nonempty([l.seller_location for l in listings])

    stock_count = declared_total if isinstance(declared_total, int) and declared_total > 0 else None

    brand_counter = Counter(l.make.strip() for l in listings if l.make and l.make.strip())
    top_brands = [b for b, _ in brand_counter.most_common()] or None

    model_counter = Counter(
        f"{l.make.strip()} {l.model.strip()}"
        for l in listings
        if l.make and l.make.strip() and l.model and l.model.strip()
    )
    top_models = [m for m, _ in model_counter.most_common(3)] or None

    example_vehicles = []
    for l in listings:
        if l.make and l.make.strip() and l.model and l.model.strip() and l.year and l.year > 0 and l.price_eur and l.price_eur > 0:
            example_vehicles.append({
                "make": l.make.strip(),
                "model": l.model.strip(),
                "year": int(l.year),
                "price_eur": float(l.price_eur),
            })
        if len(example_vehicles) >= 2:
            break

    return {
        "source_url": url,
        "name": name,
        "location": location,
        "stock_count": stock_count,
        "top_brands": top_brands,
        "top_segment": None,  # nessuna fonte deterministica su AS24 → mai stimato
        "top_models": top_models,
        "example_vehicles": example_vehicles,
        "_provenance": {
            "listings_parsed": len(listings),
            "declared_total_from_as24": declared_total,
            "note": "campo null = assente dai dati, non stimato",
        },
    }


def extract_profile(url: str, *, html: Optional[str] = None, country: str = "IT") -> dict:
    """Fetch (o html offline) + parse via scraper verificato + aggregate."""
    from autoscout_scraper import AutoScoutScraper

    portal = f"autoscout24_{country.lower()}"
    scraper = AutoScoutScraper(portal)

    if html is None:
        status, html = scraper.fetch(url)
        if status != 200 or not html:
            raise RuntimeError(f"fetch fallito: status={status} url={url}")

    declared_total = None
    scraper.get_total_pages(html)  # popola _last_declared_results dal __NEXT_DATA__
    declared_total = getattr(scraper, "_last_declared_results", None)

    listings = scraper.parse_listings(html, country=country, make="", model="")
    return aggregate_profile(listings, declared_total, url=url)


# ── SELFTEST (aggregazione pura, deterministica, offline) ──────────────────────

def _selftest() -> int:
    from models import SellerType

    def mk(make="", model="", year=0, price=0.0, seller="Auto Rossi", loc="Bari"):
        return Listing(
            listing_id="x", portal="autoscout24_it", country="IT",
            make=make, model=model, year=year, price_eur=price,
            seller_type=SellerType.DEALER, seller_name=seller, seller_location=loc,
        )

    fails = []

    # Caso 1: aggregazione normale — brand ordinati, example solo completi
    listings = [
        mk("BMW", "Serie 3", 2020, 28000),
        mk("BMW", "Serie 5", 2019, 34000),
        mk("Audi", "A4", 2021, 31000),
        mk("BMW", "X3", 0, 0),          # anno+prezzo assenti → NON in example
    ]
    p = aggregate_profile(listings, declared_total=87)
    if p["name"] != "Auto Rossi": fails.append(f"name={p['name']}")
    if p["location"] != "Bari": fails.append(f"location={p['location']}")
    if p["stock_count"] != 87: fails.append(f"stock_count={p['stock_count']}")
    if p["top_brands"][0] != "BMW": fails.append(f"top_brands={p['top_brands']}")
    if p["top_segment"] is not None: fails.append("top_segment non-null (deve essere null)")
    if len(p["example_vehicles"]) != 2: fails.append(f"example n={len(p['example_vehicles'])} (atteso 2, l'incompleto escluso)")
    if any(e["year"] == 0 for e in p["example_vehicles"]): fails.append("example include veicolo con year=0")

    # Caso 2: campo assente → null, mai stimato
    empty = aggregate_profile([], declared_total=None)
    for k in ("name", "location", "stock_count", "top_brands", "top_models"):
        if empty[k] is not None: fails.append(f"lista vuota: {k}={empty[k]} (atteso None)")
    if empty["example_vehicles"] != []: fails.append("lista vuota: example non []")

    # Caso 3: stock_count NON stimato da len(listings) — declared assente → None
    p3 = aggregate_profile(listings, declared_total=None)
    if p3["stock_count"] is not None:
        fails.append(f"stock_count stimato da len()={p3['stock_count']} (deve essere None)")

    if fails:
        print("SELFTEST FAIL:")
        for f in fails:
            print("  -", f)
        return 1
    print("SELFTEST PASS (3 casi: aggregazione, null-discipline, no-stima stock_count)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Estrattore profilo dealer AS24 (deterministico)")
    ap.add_argument("--url", help="URL pubblico AS24 del dealer")
    ap.add_argument("--html-file", help="File HTML locale (offline, salta fetch)")
    ap.add_argument("--country", default="IT", help="ISO2 paese portale (default IT)")
    ap.add_argument("--out", help="Path output JSON (default: stdout)")
    ap.add_argument("--selftest", action="store_true", help="Esegue selftest aggregazione")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if not args.url and not args.html_file:
        ap.error("serve --url o --html-file (o --selftest)")

    html = None
    if args.html_file:
        with open(args.html_file, encoding="utf-8") as f:
            html = f.read()

    profile = extract_profile(args.url or args.html_file, html=html, country=args.country)
    out = json.dumps(profile, indent=2, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Scritto: {args.out}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
