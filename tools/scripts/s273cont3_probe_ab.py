#!/usr/bin/env python3
"""S273-cont3 STEP 0-bis — cattura A/B ON e falsifica CORR-2 sui DATI.

Buco onesto lasciato da S273-cont2: il campo geo (location.countryCode) ESISTE
ed e' affidabile, ma con A/B OFF (isEuWideCountExperimentActive=False) NON e'
stato osservato NESSUN listing non-IT -> CORR-2 (il padding e' geo!=IT) resta
[UNVERIFIED], non "vero".

Questo probe:
  1. Ripete fetch di pagina 1 (cheap) finche' isEuWideCountExperimentActive=True
     o esauriti i tentativi (~MAX_TRIES). Logga il flag ad ogni giro.
  2. Appena A/B e' ON, legge i listing OLTRE pag.22 (DEEP_PAGE) e misura la
     distribuzione location.countryCode: ci sono non-IT? -> CORR-2 confermato/falso.
  3. Se A/B non si cattura in MAX_TRIES -> esito [BLOCKED-ON: A/B ON non osservabile
     in sessione]; il geo-filter resta giustificato da correttezza-comp (dealer
     estero su .it inquina il comp IT a prescindere dal padding).

NON scrive fixture, NON tocca codice. Output -> /tmp/s273cont3_probe_ab.txt.
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
MAX_TRIES = 6          # tentativi pagina-1 per catturare A/B ON
DEEP_PAGE = 25         # oltre il 22 dichiarato in A/B OFF
OUT = Path("/tmp/s273cont3_probe_ab.txt")

NEXT_RE = re.compile(r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)


def page_props(html: str) -> dict:
    m = NEXT_RE.search(html)
    if not m:
        return {}
    try:
        return json.loads(m.group(1)).get("props", {}).get("pageProps", {})
    except (json.JSONDecodeError, ValueError):
        return {}


def listings_of(pp: dict) -> list:
    return pp.get("listings", []) or pp.get("searchResult", {}).get("listings", [])


def cc_of(item: dict):
    loc = item.get("location", {}) or {}
    if isinstance(loc, dict):
        cc = loc.get("countryCode")
        if cc:
            return str(cc).upper()
    return None


def price_of(item: dict):
    tr = item.get("tracking", {}) or {}
    if tr.get("price"):
        try:
            return float(re.sub(r"[^\d]", "", str(tr["price"])) or 0) or None
        except ValueError:
            pass
    return None


def fetch_page(sc: AutoScoutScraper, pg: int):
    url = sc.build_search_url(MAKE, MODEL, pg, year_min=YEAR_MIN, year_max=YEAR_MAX,
                              sort="standard")
    html = sc._fetch(url)
    pp = page_props(html)
    return pp, listings_of(pp)


def cc_dist(items) -> dict:
    d: dict = {}
    for it in items:
        k = cc_of(it) or "None"
        d[k] = d.get(k, 0) + 1
    return d


def main() -> int:
    lines = ["=== S273-cont3 STEP 0-bis — cattura A/B ON ==="]
    ab_on_seen = False
    ab_states = []

    for attempt in range(1, MAX_TRIES + 1):
        sc = AutoScoutScraper("autoscout24_it")  # sessione/cookie fresca ad ogni giro
        pp, items = fetch_page(sc, 1)
        ab = pp.get("isEuWideCountExperimentActive")
        nres = pp.get("numberOfResults")
        npag = pp.get("numberOfPages")
        ab_states.append(ab)
        lines.append(f"[try {attempt}] A/B={ab} numberOfResults={nres} "
                     f"numberOfPages={npag} listings_pag1={len(items)}")
        if ab is True:
            ab_on_seen = True
            lines.append(f"  -> A/B ON catturato al tentativo {attempt}. Deep-probe pag.{DEEP_PAGE}.")
            pp_d, items_d = fetch_page(sc, DEEP_PAGE)
            d = cc_dist(items_d)
            non_it = sum(v for k, v in d.items() if k not in ("IT", "I", "NONE", "None"))
            prices = [p for it in items_d if (p := price_of(it))]
            lines.append(f"  PAG.{DEEP_PAGE} (A/B ON): n={len(items_d)} "
                         f"numberOfPages={pp_d.get('numberOfPages')} cc_dist={d}")
            lines.append(f"  -> non_IT oltre pag.22 = {non_it}/{len(items_d)} "
                         f"| mediana prezzo deep = "
                         f"{statistics.median(prices) if prices else None}")
            lines.append("  [CORR-2] "
                         + ("CONFERMATO: il padding oltre pag.22 e' geo!=IT"
                            if non_it > 0
                            else "FALSIFICATO: padding presente ma tutto geo=IT "
                                 "(IT-servito-EU-wide) -> geo-filter NON taglia il padding"))
            break

    lines.append("")
    lines.append(f"A/B states osservati: {ab_states}")
    if not ab_on_seen:
        lines.append("[ESITO] A/B ON NON catturato in "
                     f"{MAX_TRIES} tentativi -> "
                     "[BLOCKED-ON: A/B ON non osservabile in sessione]. "
                     "Geo-filter resta giustificato da correttezza-comp "
                     "(dealer estero su .it inquina comp IT a prescindere dal padding).")

    report = "\n".join(lines)
    OUT.write_text(report)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
