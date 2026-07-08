#!/usr/bin/env python3
"""discover_dealers.py — UNITÀ A: harvest concessionari DISTINTI dai listing ICP AS24.

Pre-req 4a RISOLTO (S303 fetch-di-prova): l'oggetto `seller` del __NEXT_DATA__ espone
`seller.links.infoPage` = URL pagina concessionario (`/concessionari/<slug>`), `seller.id`
(dealer_id stabile), `companyName`, `phones`, `type`. Questo file estrae quelle coppie.

REGOLE FERREE:
- Limiti scraper IMMUTABILI: usa AutoScoutScraper._fetch (rate-limit interno). Rate 4-10s.
- null se assente, MAI stimato.
- Nessun profiling qui (stock_count vive su dealer_profile.py). Solo DISCOVERY di candidati.
- Guard globale: STOP a 80% del daily_cap reale del portale (letto a runtime).

Uso:
  python3 tools/discover_dealers.py [--max-pages 10] [--max-dealers 0] \
      [--models "BMW:X5,Audi:Q7"] [--out data/pool_icp/_candidates.json]
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")
from tools.scrapers.autoscout_scraper import AutoScoutScraper  # noqa: E402

# ICP (docs/ROADMAP.md S292 · BRIEF_A2). make:model come attesi dagli slug AS24.
ICP_MODELS = [
    # TIER A
    ("Porsche", "Macan"), ("Porsche", "Cayenne"),
    ("Land Rover", "Range Rover Sport"), ("Land Rover", "Range Rover Velar"),
    ("Land Rover", "Range Rover Evoque"),
    ("Audi", "Q7"), ("Audi", "Q8"),
    ("BMW", "X5"),
    ("Mercedes-Benz", "GLE"), ("Mercedes-Benz", "GLC"),
    # TIER B
    ("Audi", "A6"), ("BMW", "Serie 5"),
    ("Mercedes-Benz", "Classe E"), ("Porsche", "Panamera"),
]

YEAR_MIN, YEAR_MAX = 2018, 2023
PRICE_MIN, PRICE_MAX = 25000, 90000
NEXT_RE = re.compile(r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)


def _sellers_from_html(html):
    """Estrae la lista di oggetti seller grezzi dai listing del __NEXT_DATA__."""
    m = NEXT_RE.search(html)
    if not m:
        return [], None, None
    try:
        pp = json.loads(m.group(1)).get("props", {}).get("pageProps", {})
    except (json.JSONDecodeError, ValueError):
        return [], None, None
    items = (pp.get("listings", []) or pp.get("searchResult", {}).get("listings", [])
             or pp.get("listingsData", {}).get("listings", []))
    sellers = [it.get("seller", {}) for it in items if isinstance(it.get("seller", {}), dict)]
    return sellers, pp.get("numberOfPages"), pp.get("numberOfResults")


def _candidate_from_seller(s, model_tag):
    """Normalizza un seller in un record candidato. null se assente, mai stimato."""
    if not isinstance(s, dict):
        return None
    sid = s.get("id")
    if not sid:
        return None  # senza dealer_id stabile non è dedup-abile → scarta
    links = s.get("links", {}) if isinstance(s.get("links"), dict) else {}
    phones = []
    for p in (s.get("phones") or []):
        if isinstance(p, dict) and p.get("callTo"):
            phones.append({"type": p.get("phoneType"), "callTo": p.get("callTo")})
    return {
        "seller_id": str(sid),
        "company_name": s.get("companyName") or None,
        "seller_type": s.get("type") or None,
        "info_page": links.get("infoPage") or None,
        "imprint": links.get("imprint") or None,
        "phones": phones,
        "first_seen_model": model_tag,
        "seen_count": 1,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--max-dealers", type=int, default=0, help="0 = illimitato (guard cap)")
    ap.add_argument("--models", default="", help="override 'Make:Model,Make:Model'")
    ap.add_argument("--out", default="data/pool_icp/_candidates.json")
    args = ap.parse_args()

    if args.models:
        models = [tuple(x.split(":", 1)) for x in args.models.split(",") if ":" in x]
    else:
        models = ICP_MODELS

    s = AutoScoutScraper("autoscout24_it", rate_limit_min_s=4.0, rate_limit_max_s=10.0)
    cap = s.stats.get("daily_cap") or 2000
    guard = int(cap * 0.8)
    print(f"daily_cap={cap} guard(80%)={guard} models={len(models)} max_pages={args.max_pages}")

    candidates = {}  # seller_id -> record
    stopped = None
    for make, model in models:
        if stopped:
            break
        for page in range(1, args.max_pages + 1):
            dc = s.stats.get("daily_count", 0)
            if dc >= guard:
                stopped = f"GUARD daily_count={dc}>=guard={guard}"
                break
            if args.max_dealers and len(candidates) >= args.max_dealers:
                stopped = f"MAX_DEALERS reached ({len(candidates)})"
                break
            url = s.build_search_url(make, model, page, year_min=YEAR_MIN, year_max=YEAR_MAX,
                                     price_min=PRICE_MIN, price_max=PRICE_MAX)
            try:
                html = s._fetch(url)
            except Exception as e:
                print(f"  [{make}:{model} p{page}] fetch err: {e}")
                break
            if not html:
                print(f"  [{make}:{model} p{page}] empty/404 -> next model")
                break
            sellers, npages, nresults = _sellers_from_html(html)
            new = 0
            for sel in sellers:
                rec = _candidate_from_seller(sel, f"{make}:{model}")
                if not rec:
                    continue
                if rec["seller_id"] in candidates:
                    candidates[rec["seller_id"]]["seen_count"] += 1
                else:
                    candidates[rec["seller_id"]] = rec
                    new += 1
            print(f"  [{make}:{model} p{page}] sellers={len(sellers)} new={new} "
                  f"total={len(candidates)} req={s.stats.get('daily_count')} "
                  f"npages={npages} nresults={nresults}")
            if not sellers:
                break
            if isinstance(npages, int) and page >= npages:
                break

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out = {
        "generated_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "icp_filters": {"year": [YEAR_MIN, YEAR_MAX], "price": [PRICE_MIN, PRICE_MAX],
                        "fuel": "D,G (no BEV)"},
        "daily_cap": cap, "guard_80pct": guard,
        "requests_used": s.stats.get("daily_count", 0),
        "stopped_reason": stopped or "MODELS_EXHAUSTED",
        "n_candidates": len(candidates),
        "candidates": sorted(candidates.values(), key=lambda r: r["seller_id"]),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nDONE-A: {len(candidates)} candidati DISTINTI · richieste={out['requests_used']} "
          f"· stop={out['stopped_reason']} · out={args.out}")


if __name__ == "__main__":
    main()
