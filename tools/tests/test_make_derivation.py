#!/usr/bin/env python3
"""Selftest esteso — derivazione brand DALL'ITEM quando la query non porta il make.

Chiude il blocco S304/S305: su dealer-page parse_listings è chiamato con make=""
(dealer_profile.py) e l'estrattore iniettava make dalla query → top_brands null su
OGNI dealer. Il fix deriva il brand dai campi strutturati dell'item o dal title con
match ESATTO sulla lista chiusa MAKE_SLUG (mai fuzzy, mai stima).

Invarianti (DEVONO poter FALLIRE):
  (a) item con brand nel __NEXT_DATA__/JSON-LD → brand corretto derivato;
  (b) item senza NESSUNA fonte → make="" (null, mai stimato);
  (c) query-param make PRESENTE → comportamento INVARIATO (regressione path esistenti).

exit 0 = PASS, exit 1 = FAIL. Offline puro (item costruiti a mano, zero rete).
"""
from __future__ import annotations

import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from tools.scrapers.autoscout_scraper import AutoScoutScraper  # noqa: E402


def main() -> int:
    s = AutoScoutScraper("autoscout24_it")
    fails = []

    # ── (a) BRAND DERIVATO DALL'ITEM (make query="") ──────────────────────────
    nd = s._next_data_item_to_listing(
        {"url": "/angebote/a1", "vehicle": {"make": "BMW"}}, "IT", "", "")
    if not nd or nd.make != "BMW":
        fails.append(f"(a) NEXT_DATA vehicle.make=BMW → make={nd.make if nd else None!r} (atteso BMW)")

    # slug canonicalizzato al nome ICP
    nd_slug = s._next_data_item_to_listing(
        {"url": "/angebote/a2", "vehicle": {"make": "mercedes-benz"}}, "IT", "", "")
    if not nd_slug or nd_slug.make != "Mercedes-Benz":
        fails.append(f"(a) slug mercedes-benz → make={nd_slug.make if nd_slug else None!r} (atteso Mercedes-Benz)")

    # JSON-LD brand dict
    jl = s._json_ld_to_listing(
        {"@type": "Car", "url": "https://x/1", "brand": {"name": "Porsche"}}, "IT", "", "")
    if not jl or jl.make != "Porsche":
        fails.append(f"(a) JSON-LD brand.name=Porsche → make={jl.make if jl else None!r} (atteso Porsche)")

    # JSON-LD fallback title (match ESATTO lista chiusa)
    jl_t = s._json_ld_to_listing(
        {"@type": "Car", "url": "https://x/2", "name": "BMW Serie 3 320d Touring"}, "IT", "", "")
    if not jl_t or jl_t.make != "BMW":
        fails.append(f"(a) title 'BMW Serie 3…' → make={jl_t.make if jl_t else None!r} (atteso BMW)")

    # ── (b) NESSUNA FONTE → null (mai stimato) ────────────────────────────────
    nd_none = s._next_data_item_to_listing(
        {"url": "/angebote/b1", "vehicle": {}}, "IT", "", "")
    if not nd_none or nd_none.make != "":
        fails.append(f"(b) NEXT_DATA senza brand → make={nd_none.make if nd_none else None!r} (atteso '')")

    # makeId puramente numerico NON è un brand → non deve inquinare
    nd_id = s._next_data_item_to_listing(
        {"url": "/angebote/b2", "vehicle": {"makeId": 9}}, "IT", "", "")
    if not nd_id or nd_id.make != "":
        fails.append(f"(b) makeId numerico → make={nd_id.make if nd_id else None!r} (atteso '')")

    jl_none = s._json_ld_to_listing(
        {"@type": "Car", "url": "https://x/3", "name": "Occasione imperdibile"}, "IT", "", "")
    if not jl_none or jl_none.make != "":
        fails.append(f"(b) JSON-LD title non-ICP → make={jl_none.make if jl_none else None!r} (atteso '')")

    # ── (c) QUERY-PARAM PRESENTE → INVARIATO (regressione) ────────────────────
    nd_q = s._next_data_item_to_listing(
        {"url": "/angebote/c1", "vehicle": {"make": "BMW"}}, "IT", "Audi", "A4")
    if not nd_q or nd_q.make != "Audi":
        fails.append(f"(c) query make=Audi (item vehicle.make=BMW) → make={nd_q.make if nd_q else None!r} (atteso Audi, INVARIATO)")

    jl_q = s._json_ld_to_listing(
        {"@type": "Car", "url": "https://x/4", "brand": {"name": "Porsche"}}, "IT", "BMW", "Serie 3")
    if not jl_q or jl_q.make != "BMW":
        fails.append(f"(c) query make=BMW (item brand=Porsche) → make={jl_q.make if jl_q else None!r} (atteso BMW, INVARIATO)")

    if fails:
        print("SELFTEST FAIL (derivazione brand):")
        for f in fails:
            print("  -", f)
        return 1
    print("SELFTEST PASS (a: brand derivato item/title · b: null-discipline+makeId · c: query-param invariato)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
