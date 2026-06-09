"""ARGOS IT market-price distribution (S256).

Fetcher di comparabili REALI sul mercato italiano. Sostituisce il falso
`prezzo_de * 1.15` hardcoded sparso nel codice: il prezzo di mercato IT
e' la MEDIANA di una distribuzione di annunci reali AutoScout24.it dello
stesso make/model/fascia-anno/fascia-km.

Alimenta `margin_gate.evaluate_margin(prezzo_de, prezzo_mercato_it=median)`.

NON riusa `market_price_index` persistito (DE-dominato). Usa SOLO punti IT
freschi dallo scraper, gia' validato live in produzione (S255/S256).
"""

from __future__ import annotations

import logging
import statistics
from typing import Optional

from .scrapers.autoscout_scraper import AutoScoutScraper

logger = logging.getLogger(__name__)

KM_BAND_DEFAULT = 30_000   # +/- attorno al km target
MIN_CONFIDENT_N = 5        # sotto questa soglia: bassa confidenza


def get_it_distribution(
    make: str,
    model: str,
    year: int,
    km: int,
    fuel: Optional[str] = None,
    *,
    km_band: int = KM_BAND_DEFAULT,
    year_span: int = 1,
) -> dict:
    """Distribuzione prezzi reali IT per comparabili dello stesso veicolo.

    Args:
        make:  "BMW", "Audi", "Mercedes-Benz", ...
        model: "Serie 3", "A4", "Classe C", ... (slug risolto dallo scraper)
        year:  anno del veicolo DE da comparare (banda year +/- year_span)
        km:    km del veicolo DE da comparare (banda km +/- km_band)
        fuel:  opzionale, filtra per fuel ("diesel"/"petrol"/...) su .value

    Returns:
        dict con: median, p25, p75, min, max, n (comparabili usati),
        n_raw (annunci grezzi scrapati), source, low_confidence (bool),
        listings (lista di dict prezzo/km/anno/url per audit/PDF).
        Se n==0 -> median=None e low_confidence=True.
    """
    scraper = AutoScoutScraper("autoscout24_it")
    raw = scraper.scrape_model(
        make=make,
        model=model,
        year_min=year - year_span,
        year_max=year + year_span,
    )

    comps = []
    for lst in raw:
        price = getattr(lst, "price_eur", 0) or 0
        l_km = getattr(lst, "km", 0) or 0
        if price <= 0:
            continue
        # banda km (se km target ignoto, non filtrare per km)
        if km and l_km and abs(l_km - km) > km_band:
            continue
        if fuel:
            ft = getattr(lst, "fuel_type", None)
            ftv = getattr(ft, "value", str(ft)) if ft is not None else ""
            if fuel.lower() not in str(ftv).lower():
                continue
        comps.append(lst)

    prices = sorted(float(l.price_eur) for l in comps)
    n = len(prices)

    out: dict = {
        "source": "AutoScout24.it",
        "n": n,
        "n_raw": len(raw),
        "low_confidence": n < MIN_CONFIDENT_N,
        "listings": [
            {
                "price_eur": float(l.price_eur),
                "km": int(getattr(l, "km", 0) or 0),
                "year": int(getattr(l, "year", 0) or 0),
                "variant": getattr(l, "variant", "") or "",
                "url": getattr(l, "listing_url", "") or "",
            }
            for l in comps
        ],
    }

    if n == 0:
        out.update(median=None, p25=None, p75=None, min=None, max=None)
        logger.warning(
            "[it_market_price] %s %s %s: 0 comparabili IT (raw=%d)",
            make, model, year, len(raw),
        )
        return out

    # percentili: quantiles richiede n>=2; per n==1 collassa al singolo punto.
    if n >= 2:
        q = statistics.quantiles(prices, n=4, method="inclusive")
        p25, p75 = q[0], q[2]
    else:
        p25 = p75 = prices[0]

    out.update(
        median=round(statistics.median(prices), 2),
        p25=round(p25, 2),
        p75=round(p75, 2),
        min=round(prices[0], 2),
        max=round(prices[-1], 2),
    )
    return out


def _selftest() -> int:
    """Smoke live: BMW Serie 3 2022 ~50k km deve dare una mediana plausibile."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    d = get_it_distribution("BMW", "Serie 3", year=2022, km=50_000, fuel="diesel")
    print("=== IT distribution BMW Serie 3 2022 ~50k km diesel ===")
    print(f"  source        = {d['source']}")
    print(f"  n_raw         = {d['n_raw']}")
    print(f"  n_comparabili = {d['n']}")
    print(f"  low_confidence= {d['low_confidence']}")
    print(f"  median        = {d['median']}")
    print(f"  p25 / p75     = {d['p25']} / {d['p75']}")
    print(f"  min / max     = {d['min']} / {d['max']}")
    if d["n"] == 0:
        print("  !! 0 comparabili — scraper IT down o filtro troppo stretto")
        return 1
    if d["median"] is None or d["median"] < 5000 or d["median"] > 200000:
        print("  !! mediana implausibile")
        return 1
    print("  OK")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
