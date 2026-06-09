"""ARGOS margin-gate E2E harness (S256 — DoD #1 + #3).

Scrapa annunci DE reali, calcola il prezzo di mercato IT REALE (mediana
comparabili AutoScout24.it), applica il margin gate a ciascuno e stampa la
tabella decisionale completa + conteggio PASS. Chiude anche DoD #3 facendo
passare la X1 del dossier S254 attraverso lo STESSO gate (atteso REJECT).

Uso:
    python3 -m tools.margin_e2e --make BMW --model "Serie 3" --year-min 2021 --year-max 2024 --pages 3 --limit 22
"""

from __future__ import annotations

import argparse
import logging

from .scrapers.autoscout_scraper import AutoScoutScraper
from .it_market_price import get_it_distribution
from .margin_gate import evaluate_margin, DEFAULT_FRICTION_EUR


def run(make: str, model: str, year_min: int, year_max: int, pages: int, limit: int) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    # 1) Annunci DE reali (fonte di acquisto auto)
    de = AutoScoutScraper("autoscout24_de")
    listings, _ = de.scrape(make, model, max_pages=pages, year_min=year_min, year_max=year_max)
    de_valid = [l for l in listings if (l.price_eur or 0) > 0 and (l.year or 0) >= year_min][:limit]

    print(f"\n{'='*120}")
    print(f"MARGIN GATE E2E — {make} {model} ({year_min}-{year_max}) | frizione DE->IT = €{DEFAULT_FRICTION_EUR:.0f}")
    print(f"Annunci DE reali analizzati: {len(de_valid)} (su {len(listings)} scrapati)")
    print(f"{'='*120}\n")

    it_cache: dict[int, dict] = {}

    def it_for(year: int) -> dict:
        if year not in it_cache:
            # km=0 -> distribuzione market per model/anno (km-agnostica), N comparabili disclosed
            it_cache[year] = get_it_distribution(make, model, year, km=0)
        return it_cache[year]

    hdr = (f"{'#':<3}{'anno':<5}{'km':>8}  {'prezzo_DE':>10}{'mercato_IT':>11}"
           f"{'(N)':>5}{'chiavi':>9}{'spread':>8}{'floor':>8}{'surplus':>9}"
           f"{'fee':>7}{'netto€':>9}{'netto%':>8}  DECIS  url")
    print(hdr)
    print("-" * 120)

    passed = 0
    rows = []
    for i, l in enumerate(de_valid, 1):
        it = it_for(int(l.year))
        if not it.get("median"):
            print(f"{i:<3}{l.year:<5}{(l.km or 0):>8}  {l.price_eur:>10.0f}  --- 0 comparabili IT ---  SKIP  {l.listing_url}")
            continue
        mr = evaluate_margin(prezzo_de=float(l.price_eur), prezzo_mercato_it=it["median"])
        if mr.decision == "PASS":
            passed += 1
        rows.append((l, it, mr))
        print(
            f"{i:<3}{l.year:<5}{(l.km or 0):>8}  {l.price_eur:>10.0f}{it['median']:>11.0f}"
            f"{it['n']:>5}{mr.chiavi_in_mano:>9.0f}{mr.spread_lordo:>8.0f}{mr.dealer_floor_amount:>8.0f}"
            f"{mr.surplus:>9.0f}{mr.fee_argos:>7.0f}{mr.margine_netto_dealer:>9.0f}{mr.margine_netto_pct:>7.1f}%"
            f"  {mr.decision:<6} {l.listing_url}"
        )

    print("-" * 120)
    print(f"\nRISULTATO DoD #1: {passed} PASS su {len(de_valid)} annunci DE reali "
          f"({len(de_valid)-passed} REJECT/SKIP via VETO gate margine).")

    # DoD #3 — X1 del dossier S254 attraverso lo STESSO gate (atteso REJECT)
    print(f"\n{'='*120}")
    print("DoD #3 — Falsificazione X1 (dossier S254 €167 margine) attraverso il gate:")
    x1 = evaluate_margin(prezzo_de=21795.0, prezzo_mercato_it=22862.0, friction_eur=0.0)
    print(f"  chiavi_in_mano={x1.chiavi_in_mano:.0f}  spread={x1.spread_lordo:.0f}  "
          f"floor={x1.dealer_floor_amount:.0f}  surplus={x1.surplus:.0f}  -> {x1.decision}")
    ok_x1 = x1.decision == "REJECT"
    print(f"  {'OK: X1 correttamente REJECT (€167 mascherato bloccato)' if ok_x1 else '!! FAIL: X1 doveva uscire REJECT'}")

    print(f"\n{'='*120}")
    enough = len(de_valid) >= 20
    print(f"GATE DoD: annunci>=20 {'OK' if enough else 'NO (' + str(len(de_valid)) + ')'} | X1 REJECT {'OK' if ok_x1 else 'FAIL'}")
    return 0 if (enough and ok_x1) else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--make", default="BMW")
    p.add_argument("--model", default="Serie 3")
    p.add_argument("--year-min", type=int, default=2021)
    p.add_argument("--year-max", type=int, default=2024)
    p.add_argument("--pages", type=int, default=3)
    p.add_argument("--limit", type=int, default=22)
    a = p.parse_args()
    import sys
    sys.exit(run(a.make, a.model, a.year_min, a.year_max, a.pages, a.limit))
