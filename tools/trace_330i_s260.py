"""S260 FASE 1a — trace no-fusione su 330i (petrol, rwd), ingresso diverso da 320d.

Itera L0->L3 SENZA break anticipato e stampa, per ogni livello:
  N, set(drivetrains), set(fuel) dei comparabili matchati.
Atteso: a NESSUN livello drivetrains contiene {awd,rwd} insieme, ne' fuel {petrol,diesel}.
"""
from __future__ import annotations

from tools.it_market_price import (
    derive_trim_family, _levels, _match,
)
from tools.scrapers.autoscout_scraper import AutoScoutScraper

YEAR, KM = 2021, 60_000
KM_BAND = 30_000


def main() -> int:
    scraper = AutoScoutScraper("autoscout24_it")
    raw = scraper.scrape_model(make="BMW", model="Serie 3",
                               year_min=YEAR - 2, year_max=YEAR + 2)

    target = derive_trim_family("330i", "petrol", "automatic", 258)
    print(f"TARGET 330i = {target['key']}  "
          f"(engine={target['engine_class']} drive={target['drivetrain']} fuel={target['fuel']})")

    pool = []
    for lst in raw:
        price = getattr(lst, "price_eur", 0) or 0
        if price <= 0:
            continue
        ft = getattr(lst, "fuel_type", None)
        ftv = getattr(ft, "value", str(ft)) if ft is not None else ""
        tr = getattr(lst, "transmission", None)
        trv = getattr(tr, "value", str(tr)) if tr is not None else ""
        cspec = derive_trim_family(getattr(lst, "variant", "") or "", ftv, trv,
                                   getattr(lst, "power_hp", 0) or 0)
        pool.append((lst, cspec,
                     int(getattr(lst, "km", 0) or 0),
                     int(getattr(lst, "year", 0) or 0)))

    print(f"\nPOOL raw={len(raw)}  prezzo>0 -> {len(pool)} comparabili\n")

    levels = _levels(year_span=1)
    fusion_violation = False
    for idx, cfg in enumerate(levels):
        matched = [p for p in pool
                   if _match(target, p[1], p[2], p[3], KM, YEAR, KM_BAND, cfg)]
        dts = sorted({p[1]["drivetrain"] for p in matched})
        fuels = sorted({p[1]["fuel"] for p in matched if p[1]["fuel"]})
        engines = sorted({p[1]["engine_class"] for p in matched if p[1]["engine_class"]})
        print(f"L{idx}  cfg(engine={cfg['engine']},drive={cfg['drivetrain']},"
              f"trim={cfg['trim']},fuel={cfg['fuel']},km={cfg['km']},yt={cfg['year_tol']})")
        print(f"     N={len(matched):2d}  drivetrains={dts}  fuels={fuels}  engines={engines}")
        if "awd" in dts and "rwd" in dts:
            print("     !! FUSIONE drivetrain awd+rwd")
            fusion_violation = True
        if "petrol" in fuels and "diesel" in fuels:
            print("     !! FUSIONE fuel petrol+diesel")
            fusion_violation = True

    print("\n=== VERDETTO 1a ===")
    if fusion_violation:
        print("FUSIONE RILEVATA -> principio NON solido: BLOCKED")
        return 1
    print("NESSUNA FUSIONE su L0->L3 (drivetrain e fuel pinnati) -> principio solido")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
