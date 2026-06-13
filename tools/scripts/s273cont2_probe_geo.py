#!/usr/bin/env python3
"""S273-cont2 STEP 0 — PROBE GEO+PREZZO (decide tutta l'architettura).

Fetch pagina 1 e pagina ~40 della query-fixture (BMW Serie 3 2019-2023, sort=standard,
cy=I), ri-parsa il RAW pageProps.listings[] (il parser scraper SCARTA il geo) e risponde
ai 3 quesiti terminali sui DATI:
  (a) esiste un campo geo affidabile nel raw? (zip/countryCode/location per listing)
  (b) i listing oltre pag.~22 sono geo!=IT? (CORR-2)
  (c) mediana prezzo padding(pag.40) vs IT-core(pag.1): il padding comprime il comp? (CORR-5)

NON scrive fixture, NON tocca codice. Solo lettura + report su /tmp/s273cont2_probe.txt.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.scrapers.autoscout_scraper import AutoScoutScraper  # noqa: E402

MAKE, MODEL = "BMW", "Serie 3"
YEAR_MIN, YEAR_MAX = 2019, 2023
PAGES = [20, 23]
OUT = Path("/tmp/s273cont2_probe.txt")

NEXT_RE = re.compile(r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)


def page_props(html: str) -> dict:
    m = NEXT_RE.search(html)
    if not m:
        return {}
    try:
        return json.loads(m.group(1)).get("props", {}).get("pageProps", {})
    except (json.JSONDecodeError, ValueError):
        return {}


def find_geo(item: dict) -> dict:
    """Cerca campi geo plausibili nell'item raw (e nel sotto-dict seller/location)."""
    out = {}
    seller = item.get("seller", {}) or {}
    loc = item.get("location", {}) or {}
    # candidati comuni AS24
    for src_name, src in (("item", item), ("seller", seller), ("location", loc)):
        if not isinstance(src, dict):
            continue
        for k in ("zip", "zipCode", "postalCode", "countryCode", "country",
                  "city", "cityName"):
            if k in src and src[k] not in (None, ""):
                out[f"{src_name}.{k}"] = src[k]
        # seller.address spesso annidato
        addr = src.get("address", {})
        if isinstance(addr, dict):
            for k in ("zip", "zipCode", "postalCode", "countryCode", "country", "city"):
                if k in addr and addr[k] not in (None, ""):
                    out[f"{src_name}.address.{k}"] = addr[k]
    return out


def price_of(item: dict):
    tracking = item.get("tracking", {}) or {}
    if tracking.get("price"):
        try:
            return float(re.sub(r"[^\d]", "", str(tracking["price"])) or 0) or None
        except ValueError:
            pass
    pr = item.get("price", "")
    if isinstance(pr, dict):
        raw = re.sub(r"[^\d]", "", str(pr.get("priceFormatted", "")))
        return float(raw) if raw else None
    return None


def main() -> int:
    sc = AutoScoutScraper("autoscout24_it")
    lines = ["=== S273-cont2 PROBE GEO+PREZZO ==="]
    page_data = {}

    for pg in PAGES:
        url = sc.build_search_url(MAKE, MODEL, pg, year_min=YEAR_MIN, year_max=YEAR_MAX,
                                  sort="standard")
        html = sc._fetch(url)
        status = 200 if html else 0
        pp = page_props(html)
        items = (pp.get("listings", [])
                 or pp.get("searchResult", {}).get("listings", []))
        lines.append(f"\n--- PAGINA {pg} (HTTP {status}, html {len(html)}b) ---")
        lines.append(f"URL: {url}")
        lines.append(f"numberOfResults={pp.get('numberOfResults')} "
                     f"numberOfPages={pp.get('numberOfPages')} "
                     f"isEuWideCountExperimentActive={pp.get('isEuWideCountExperimentActive')}")
        lines.append(f"listings in raw: {len(items)}")
        page_data[pg] = items

        # dump struttura del PRIMO item (solo pagina 1) per scoprire dove sta il geo
        if pg == 1 and items:
            it0 = items[0]
            lines.append(f"\n[STEP 0a] chiavi item[0]: {sorted(it0.keys())}")
            sel = it0.get("seller", {})
            if isinstance(sel, dict):
                lines.append(f"[STEP 0a] chiavi seller: {sorted(sel.keys())}")
                addr = sel.get("address", {})
                if isinstance(addr, dict):
                    lines.append(f"[STEP 0a] chiavi seller.address: {sorted(addr.keys())}")
            loc = it0.get("location", {})
            if isinstance(loc, dict) and loc:
                lines.append(f"[STEP 0a] chiavi location: {sorted(loc.keys())}")
            lines.append(f"[STEP 0a] geo trovato item[0]: {find_geo(it0)}")

    # tabella geo+prezzo per pagina
    summary = {}
    for pg, items in page_data.items():
        geos = [find_geo(it) for it in items]
        prices = [p for it in items if (p := price_of(it))]
        # ricava countryCode/zip prefix per ogni listing
        ccs = []
        for g in geos:
            cc = (g.get("seller.countryCode") or g.get("seller.address.countryCode")
                  or g.get("location.countryCode") or g.get("item.countryCode"))
            zp = (g.get("seller.zip") or g.get("seller.address.zip")
                  or g.get("seller.address.postalCode") or g.get("location.zip"))
            ccs.append((cc, zp))
        non_it = [c for c in ccs if c[0] and str(c[0]).upper() not in ("IT", "I")]
        summary[pg] = {
            "n": len(items),
            "n_priced": len(prices),
            "median_price": statistics.median(prices) if prices else None,
            "geo_coverage": sum(1 for c in ccs if c[0]),
            "non_it_count": len(non_it),
            "cc_distribution": _dist([c[0] for c in ccs]),
            "sample_geo": geos[:3],
        }

    lines.append("\n=== RISPOSTE TERMINALI ===")
    for pg in PAGES:
        s = summary[pg]
        lines.append(f"\nPAG {pg}: n={s['n']} priced={s['n_priced']} "
                     f"median_price={s['median_price']} "
                     f"geo_cov={s['geo_coverage']}/{s['n']} non_IT={s['non_it_count']}")
        lines.append(f"  countryCode dist: {s['cc_distribution']}")
        lines.append(f"  sample_geo: {s['sample_geo']}")

    p1, p40 = summary.get(1, {}), summary.get(40, {})
    lines.append("\n[STEP 0a] campo geo affidabile? -> "
                 + ("SI" if p1.get("geo_coverage", 0) > 0 else "NO (nessun geo nel raw!)"))
    lines.append(f"[STEP 0b] padding pag40 geo!=IT? -> non_IT={p40.get('non_it_count')} "
                 f"su {p40.get('n')} (SI=discrimina / NO=IT-servito-EU-wide)")
    if p1.get("median_price") and p40.get("median_price"):
        delta = p40["median_price"] - p1["median_price"]
        lines.append(f"[STEP 0c] mediana pag1(IT-core)={p1['median_price']} "
                     f"vs pag40(padding)={p40['median_price']} delta={delta:+.0f} "
                     f"-> padding {'COMPRIME' if delta < 0 else 'ALZA' if delta > 0 else 'neutro'} il comp")

    report = "\n".join(lines)
    OUT.write_text(report)
    print(report)
    return 0


def _dist(vals):
    d = {}
    for v in vals:
        k = str(v).upper() if v else "None"
        d[k] = d.get(k, 0) + 1
    return d


if __name__ == "__main__":
    sys.exit(main())
