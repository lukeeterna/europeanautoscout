#!/usr/bin/env python3
r"""S266 — Builder fixture reale IT market-price (chiude il debito S264).

S264 ha prodotto il fatto fondante (310 listing) e poi ha BUTTATO la prova
(override revertito, /tmp pulito): il DoD non era riproducibile. Questo script
fa la scrape profonda UNA volta e ne PERSISTE l'output come fixture committata
nel repo (tests/fixtures/it_dist_*.json). Da li' in poi DoD #2/#3 e i test
girano su quel dato vero, NON ri-scrapando ogni sessione.

Tecnica (S264, autorizzata — lettura dato pubblico):
  override RUNTIME `results_per_page=1` -> bypassa il break short-page in
  base_scraper.py:374 (`if len(page_listings) < self.config.results_per_page`),
  che altrimenti ferma alla pagina-1 SSR (~19 listing, muro descritto S263).
  L'override e' a runtime via object.__setattr__ (config e' frozen dataclass,
  stesso workaround gia' usato da scrape() per max_pages): NESSUN file editato,
  NESSUN git restore necessario (Rule 1d: niente mutazione di source-of-truth).

Uso (dalla root del repo):
  python3 -m tools.scripts.build_it_fixture
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from tools.scrapers.autoscout_scraper import AutoScoutScraper

# Pool reale condiviso: BMW Serie 3 2019-2023 (anno target 2021 +-2). I due
# veicoli del DoD (320d xDrive diesel awd, 330i petrol) si filtrano ENTRAMBI da
# questo unico snapshot -> piu' onesto di due scrape separate (stesso mercato,
# stesso giorno). Il filtro per trim avviene in get_it_distribution, NON qui.
MAKE = "BMW"
MODEL = "Serie 3"
YEAR = 2021
YEAR_SPAN = 2
DEEP_PAGES = 60  # tetto-di-sicurezza; il vero terminatore e' get_total_pages
# (S273 ADD-2): AS24 dichiara numberOfPages -> base_scraper clampa max_pages a
# quel valore (~22) e si ferma all'ultima pagina REALE. DEEP_PAGES alto = solo
# guard se il blob mancasse. Path NUOVO (Rule 1d: additivo, non sovrascrive la
# fixture committata cap-truncated 325).
OUT = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "it_dist_bmw_serie3_2021_s273.json"


def main() -> int:
    scraper = AutoScoutScraper("autoscout24_it")
    # override RUNTIME (frozen dataclass): results_per_page=1 -> il break
    # short-page scatta solo su pagina VUOTA; max_pages alto -> pagina profondo.
    object.__setattr__(scraper.config, "results_per_page", 1)
    object.__setattr__(scraper.config, "max_pages", DEEP_PAGES)

    print(f"[fixture] scrape profonda {MAKE} {MODEL} {YEAR-YEAR_SPAN}-{YEAR+YEAR_SPAN} "
          f"(results_per_page=1, max_pages={DEEP_PAGES})...", flush=True)
    raw = scraper.scrape_model(
        make=MAKE, model=MODEL,
        year_min=YEAR - YEAR_SPAN, year_max=YEAR + YEAR_SPAN,
    )
    n = len(raw)
    n_priced = sum(1 for l in raw if (getattr(l, "price_eur", 0) or 0) > 0)
    print(f"[fixture] raccolti {n} listing ({n_priced} con prezzo>0)", flush=True)

    if n_priced < 20:
        print(f"[fixture] !! SOLO {n_priced} listing con prezzo: muro pagina-1 "
              f"NON superato (atteso ~300 come S264). Fixture NON scritta.", flush=True)
        return 1

    blob = {
        "meta": {
            "make": MAKE, "model": MODEL, "year": YEAR, "year_span": YEAR_SPAN,
            "scrape_date": date.today().isoformat(),
            "source": "AutoScout24.it",
            "n_raw": n, "n_priced": n_priced,
            "declared_results": getattr(scraper, "_last_declared_results", None),
            "declared_pages": getattr(scraper, "_last_declared_pages", None),
            "terminator": "get_total_pages/numberOfPages clamp (S273 ADD-2, term. a)",
            # ADD-3: campione ordinato per RILEVANZA (sort=standard), NON per prezzo
            # -> nessun price-bias; la banda riflette tutto il pool, non una meta'.
            "sort": "standard (relevance-ordered)",
            "price_field": "prezzi RICHIESTI (annunci), non di transazione (ADD-4)",
            "technique": "results_per_page=1 runtime override (S266) + numberOfPages clamp (S273)",
        },
        "listings": [l.to_dict() for l in raw],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(blob, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[fixture] scritta: {OUT} ({n} listing)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
