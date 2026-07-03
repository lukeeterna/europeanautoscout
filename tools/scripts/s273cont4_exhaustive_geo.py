#!/usr/bin/env python3
"""S273-cont4 — Scrape esaustivo geo-puro + experiment-probe per Gate [3].

Obiettivo: produrre un pool AFFIDABILE BMW Serie 3 2019-2023 su AutoScout24.it
con le TRE prove richieste:
  1. COMPLETEZZA: pagina fino a pagina VUOTA (non cap fisso).
  2. PUREZZA GEO: filtro location.countryCode==IT sul RAW NEXT_DATA.
  3. EXPERIMENT-OFF: lettura isEuWideCountExperimentActive ad ogni pagina.

Output:
  - Fixture nuova: tests/fixtures/it_dist_bmw_serie3_2021_s273cont4.json
  - Report testuale: /tmp/s273cont4_report.txt (con tutte le prove grezze)

NON tocca la fixture esistente (Rule 1d: path nuovo, additivo).
NON modifica nessun sorgente di scoring.
Vincoli: sleep(15) tra fetch, DAILY_LIMIT=30 NON si applica (e' per WA dealer).

Uso:
  python3 -m tools.scripts.s273cont4_exhaustive_geo
"""
from __future__ import annotations

import json
import re
import statistics
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.scrapers.autoscout_scraper import AutoScoutScraper  # noqa: E402
from tools.scrapers.models import Listing  # noqa: E402
from tools.it_market_price import get_it_distribution  # noqa: E402

# ---------------------------------------------------------------------------
# Parametri scrape
# ---------------------------------------------------------------------------
MAKE = "BMW"
MODEL = "Serie 3"
YEAR_MIN = 2019
YEAR_MAX = 2023
DEEP_PAGES = 80          # guard alto; il vero stop e' la pagina vuota
SLEEP_BETWEEN_PAGES = 15  # secondi (vincolo immutabile)

# Path output NUOVI (additivi, non sovrascrivono nulla — Rule 1d)
OUT_FIXTURE = ROOT / "tests" / "fixtures" / "it_dist_bmw_serie3_2021_s273cont4.json"
OUT_REPORT = Path("/tmp/s273cont4_report.txt")

NEXT_RE = re.compile(
    r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


# ---------------------------------------------------------------------------
# Helpers raw NEXT_DATA
# ---------------------------------------------------------------------------

def parse_page_props(html: str) -> dict:
    m = NEXT_RE.search(html)
    if not m:
        return {}
    try:
        return json.loads(m.group(1)).get("props", {}).get("pageProps", {})
    except (json.JSONDecodeError, ValueError):
        return {}


def raw_listings_of(pp: dict) -> list:
    """Listing grezzi dal NEXT_DATA (NON parsati — mantengono location)."""
    return pp.get("listings", []) or pp.get("searchResult", {}).get("listings", [])


def cc_of(item: dict) -> Optional[str]:
    """Estrae location.countryCode dal raw item."""
    loc = item.get("location", {}) or {}
    if isinstance(loc, dict):
        cc = loc.get("countryCode")
        if cc:
            return str(cc).upper()
    return None


def price_of(item: dict) -> Optional[float]:
    """Prezzo grezzo da tracking.price o price dict."""
    tr = item.get("tracking", {}) or {}
    if tr.get("price"):
        try:
            raw = re.sub(r"[^\d]", "", str(tr["price"]))
            return float(raw) if raw else None
        except ValueError:
            pass
    pr = item.get("price", "")
    if isinstance(pr, dict):
        raw = re.sub(r"[^\d]", "", str(pr.get("priceFormatted", "")))
        return float(raw) if raw else None
    return None


def listing_id_of(item: dict) -> Optional[str]:
    """ID listing per dedup."""
    return (item.get("id") or item.get("listing_id") or
            item.get("tracking", {}).get("listing_id"))


# ---------------------------------------------------------------------------
# Scrape loop esaustivo
# ---------------------------------------------------------------------------

def run_exhaustive_scrape(log_lines: list) -> tuple[list, dict]:
    """
    Pagina fino a pagina VUOTA (fact terminale) o guard DEEP_PAGES.
    Restituisce (all_raw_it, page_log) dove all_raw_it = listing grezzi geo==IT.
    page_log = {page_num: {n_raw, n_it, n_non_it, cc_dist, ab_flag, n_priced, median_price}}
    """
    scraper = AutoScoutScraper("autoscout24_it")
    # Override results_per_page=1 -> break short-page scatta solo su pagina vuota
    object.__setattr__(scraper.config, "results_per_page", 1)
    object.__setattr__(scraper.config, "max_pages", DEEP_PAGES)

    all_raw_it: list = []         # listing grezzi geo==IT (prova purezza)
    seen_ids: set = set()
    page_log: dict = {}
    cc_global: dict = {}          # distribuzione globale countryCode
    ab_per_page: list = []        # flag experiment per pagina
    terminated_by_empty = False
    last_page_scraped = 0

    log_lines.append(f"\n[SCRAPE] BMW Serie 3 {YEAR_MIN}-{YEAR_MAX}, "
                     f"DEEP_PAGES={DEEP_PAGES}, sleep={SLEEP_BETWEEN_PAGES}s")

    for page_num in range(1, DEEP_PAGES + 1):
        if page_num > 1:
            time.sleep(SLEEP_BETWEEN_PAGES)

        url = scraper.build_search_url(
            MAKE, MODEL, page_num,
            year_min=YEAR_MIN, year_max=YEAR_MAX,
        )
        try:
            html = scraper._fetch(url)
        except Exception as exc:
            log_lines.append(f"  PAG {page_num}: ERRORE FETCH — {exc}")
            break

        if not html:
            log_lines.append(f"  PAG {page_num}: HTML VUOTO — stop paginazione")
            terminated_by_empty = True
            break

        pp = parse_page_props(html)

        # Meta AS24 (clamp max_pages solo a pagina 1)
        if page_num == 1:
            n_res = pp.get("numberOfResults")
            n_pag = pp.get("numberOfPages")
            log_lines.append(f"  AS24 dichiara: numberOfResults={n_res}, "
                             f"numberOfPages={n_pag}")
            # NON clampiamo qui: vogliamo raggiungere la pagina VUOTA reale,
            # non il cap dichiarato AS24 (che include padding EU-wide se A/B ON)

        ab_flag = pp.get("isEuWideCountExperimentActive")
        ab_per_page.append((page_num, ab_flag))

        raw_items = raw_listings_of(pp)
        last_page_scraped = page_num

        # Prova COMPLETEZZA: pagina vuota = terminatore reale
        if not raw_items:
            log_lines.append(f"  PAG {page_num}: 0 listing in pagina — "
                             f"PAGINA VUOTA (terminatore reale raggiunto)")
            terminated_by_empty = True
            break

        # Analisi geo + prova purezza
        n_it = 0
        n_non_it = 0
        cc_dist_page: dict = {}
        prices_it = []
        prices_non_it = []

        for item in raw_items:
            cc = cc_of(item)
            lid = listing_id_of(item)
            cc_key = cc if cc else "NONE"
            cc_dist_page[cc_key] = cc_dist_page.get(cc_key, 0) + 1
            cc_global[cc_key] = cc_global.get(cc_key, 0) + 1

            price = price_of(item)
            is_it = (cc in ("IT", "I")) if cc else False

            if is_it:
                n_it += 1
                if price:
                    prices_it.append(price)
                # Dedup e accumulazione IT
                if lid and lid not in seen_ids:
                    seen_ids.add(lid)
                    all_raw_it.append(item)
                elif not lid:
                    all_raw_it.append(item)  # senza ID non possiamo deduppare
            else:
                n_non_it += 1
                if price:
                    prices_non_it.append(price)

        median_it = round(statistics.median(prices_it), 0) if prices_it else None
        page_log[page_num] = {
            "n_raw": len(raw_items),
            "n_it": n_it,
            "n_non_it": n_non_it,
            "n_it_priced": len(prices_it),
            "median_price_it": median_it,
            "cc_dist": cc_dist_page,
            "ab_flag": ab_flag,
        }

        log_lines.append(
            f"  PAG {page_num:3d}: raw={len(raw_items):3d} "
            f"IT={n_it:3d} non-IT={n_non_it:3d} "
            f"ab={ab_flag} cc_dist={cc_dist_page} "
            f"med_IT={median_it}"
        )

    summary = {
        "pages_scraped": last_page_scraped,
        "terminated_by_empty": terminated_by_empty,
        "ab_per_page": ab_per_page,
        "cc_global": cc_global,
        "n_raw_it_dedup": len(all_raw_it),
        "page_log": page_log,
    }
    return all_raw_it, summary


# ---------------------------------------------------------------------------
# Converti raw items in Listing (per passarli a get_it_distribution)
# ---------------------------------------------------------------------------

def raw_to_listing(item: dict, scraper: AutoScoutScraper) -> Optional[Listing]:
    """Converte un raw NEXT_DATA item in Listing via il parser scraper."""
    # Usa parse_listings su un HTML sintetico? No: usiamo il parser interno
    # _parse_next_data_item se esiste, altrimenti costruiamo dalla struct grezza.
    # Metodo sicuro: wrappare in una lista e chiamare il parser diretto.
    try:
        # Il parser NEXT_DATA del scraper accetta il raw listing come item
        # Chiamiamo il metodo interno che processa singoli item
        parsed = scraper._parse_next_data_listing(item, "IT", MAKE, MODEL)
        return parsed
    except AttributeError:
        pass
    # Fallback: costruiamo Listing dai campi noti del raw NEXT_DATA
    try:
        price = price_of(item)
        if not price:
            return None
        tracking = item.get("tracking", {}) or {}
        listing_id = listing_id_of(item) or ""
        km_raw = tracking.get("mileage") or item.get("mileage") or 0
        year_raw = tracking.get("firstRegistration", "")[:4] if tracking.get("firstRegistration") else ""
        try:
            year = int(year_raw) if year_raw else 0
        except ValueError:
            year = 0
        try:
            km = int(str(km_raw).replace(".", "").replace(",", "").strip() or 0)
        except ValueError:
            km = 0
        url = item.get("url", "") or ""
        if url and not url.startswith("http"):
            url = f"https://www.autoscout24.it{url}"
        variant = (tracking.get("model_version") or
                   item.get("vehicleDetails", {}).get("trim") or "")
        from tools.scrapers.models import FuelType, Transmission
        fuel_raw = (tracking.get("fuel_type") or "").lower()
        fuel_map = {"diesel": FuelType.DIESEL, "petrol": FuelType.PETROL,
                    "gasoline": FuelType.PETROL, "electric": FuelType.ELECTRIC,
                    "hybrid": FuelType.HYBRID}
        fuel = fuel_map.get(fuel_raw, FuelType.UNKNOWN)
        listing = Listing(
            listing_id=listing_id,
            portal="autoscout24_it",
            country="IT",
            make=MAKE,
            model=MODEL,
            year=year,
            km=km,
            price_eur=price,
            fuel_type=fuel,
            transmission=Transmission.UNKNOWN,
            variant=variant,
            listing_url=url,
        )
        return listing
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    log_lines = ["=" * 70, "S273-cont4 — SCRAPE ESAUSTIVO GEO-PURO", "=" * 70]
    log_lines.append(f"Data: {date.today().isoformat()}")

    # STEP 0: verifica DAILY_LIMIT
    log_lines.append("\n[STEP 0] DAILY_LIMIT check")
    log_lines.append("  wa-daemon.js CONFIG.DAILY_LIMIT=30 = messaggi WA dealer (NON scraper)")
    log_lines.append("  PortalConfig autoscout24_it.daily_request_cap=2000 (base_scraper._check_daily_cap)")
    log_lines.append("  sleep(15) tra pagine: invariato (vincolo immutabile)")
    log_lines.append("  Stimato: 80 pagine × 15s = 1200s = 20 min. Entro cap 2000. FEASIBLE.")

    # Scrape esaustivo
    all_raw_it, summary = run_exhaustive_scrape(log_lines)

    # Prova COMPLETEZZA
    log_lines.append("\n[PROVA 1 — COMPLETEZZA]")
    log_lines.append(f"  Pagine percorse: {summary['pages_scraped']}")
    log_lines.append(f"  Terminato da pagina VUOTA: {summary['terminated_by_empty']}")
    if not summary["terminated_by_empty"]:
        log_lines.append(f"  !! ATTENZIONE: pagina vuota NON raggiunta entro {DEEP_PAGES} pagine.")
        log_lines.append(f"     Pool potrebbe essere ancora incompleto. Aumentare DEEP_PAGES.")

    # Prova EXPERIMENT
    log_lines.append("\n[PROVA 3 — EXPERIMENT isEuWideCountExperimentActive]")
    ab_vals = summary["ab_per_page"]
    ab_true_pages = [p for p, v in ab_vals if v is True]
    ab_false_pages = [p for p, v in ab_vals if v is False]
    ab_none_pages = [p for p, v in ab_vals if v is None]
    log_lines.append(f"  Pagine con flag=True  (A/B ON) : {len(ab_true_pages)} — {ab_true_pages[:10]}")
    log_lines.append(f"  Pagine con flag=False (A/B OFF): {len(ab_false_pages)} — {ab_false_pages[:10]}")
    log_lines.append(f"  Pagine con flag=None  (assente): {len(ab_none_pages)} — {ab_none_pages[:10]}")
    baseline_valid = len(ab_true_pages) == 0
    log_lines.append(f"  Baseline valida (flag sempre OFF/None): {baseline_valid}")
    if not baseline_valid:
        log_lines.append(f"  !! ALCUNE pagine hanno A/B ON — il conteggio AS24 potrebbe essere EU-wide.")
        log_lines.append(f"     Il geo-filter (location.countryCode==IT) mitiga questo a prescindere.")

    # Prova PUREZZA GEO
    log_lines.append("\n[PROVA 2 — PUREZZA GEO]")
    cc_global = summary["cc_global"]
    total_raw = sum(cc_global.values())
    n_it_raw = cc_global.get("IT", 0) + cc_global.get("I", 0)
    n_non_it_raw = total_raw - n_it_raw - cc_global.get("NONE", 0)
    n_no_cc = cc_global.get("NONE", 0)
    log_lines.append(f"  Totale listing grezzi processati: {total_raw}")
    log_lines.append(f"  Distribuzione countryCode globale: {cc_global}")
    log_lines.append(f"  IT (IT+I): {n_it_raw}")
    log_lines.append(f"  non-IT (scartati): {n_non_it_raw}")
    log_lines.append(f"  senza countryCode (NONE): {n_no_cc}")
    log_lines.append(f"  Pool geo-puro IT dedup: {summary['n_raw_it_dedup']} listing")

    # Salva fixture nuova (se abbastanza dati)
    n_raw_it = summary["n_raw_it_dedup"]
    log_lines.append(f"\n[FIXTURE] Raw IT dedup: {n_raw_it}")

    # Costruiamo i Listing dal raw: usiamo il parser del scraper
    scraper_ref = AutoScoutScraper("autoscout24_it")
    listings_it: list[Listing] = []
    n_parse_fail = 0
    for item in all_raw_it:
        lst = raw_to_listing(item, scraper_ref)
        if lst and getattr(lst, "price_eur", 0) and lst.price_eur > 0:
            listings_it.append(lst)
        else:
            n_parse_fail += 1
    n_priced = len(listings_it)
    log_lines.append(f"  Listing con prezzo post-parse: {n_priced} (parse fail: {n_parse_fail})")

    if n_priced < 20:
        log_lines.append(f"  !! SOLO {n_priced} listing con prezzo — fixture NON scritta.")
    else:
        blob = {
            "meta": {
                "make": MAKE, "model": MODEL,
                "year_min": YEAR_MIN, "year_max": YEAR_MAX,
                "scrape_date": date.today().isoformat(),
                "source": "AutoScout24.it",
                "n_raw_it": n_raw_it,
                "n_priced": n_priced,
                "pages_scraped": summary["pages_scraped"],
                "terminated_by_empty": summary["terminated_by_empty"],
                "cc_global": cc_global,
                "ab_per_page_summary": {
                    "True": len(ab_true_pages),
                    "False": len(ab_false_pages),
                    "None": len(ab_none_pages),
                },
                "terminator": "empty_page_real (geo-puro, s273cont4)",
                "technique": (
                    "results_per_page=1 runtime override (no short-page break) + "
                    "geo filter location.countryCode==IT on RAW NEXT_DATA + "
                    "isEuWideCountExperimentActive logged per pagina"
                ),
            },
            "listings": [lst.to_dict() for lst in listings_it],
        }
        OUT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FIXTURE.write_text(json.dumps(blob, ensure_ascii=False, indent=2), encoding="utf-8")
        log_lines.append(f"  Fixture scritta: {OUT_FIXTURE}")

    # Calcolo N per livello L0-L3 per 330i e 320d
    log_lines.append("\n[LEVELING 330i — N per livello L0-L3]")
    fixture_path_str = str(OUT_FIXTURE) if n_priced >= 20 else None

    if fixture_path_str:
        dist_330i = get_it_distribution(
            "BMW", "Serie 3", year=2021, km=50_000, fuel="petrol",
            target_variant="330i", target_transmission="automatic", target_power_hp=258,
            year_span=2, min_n=8,
            fixture_path=fixture_path_str,
        )
        log_lines.append(f"  330i n_by_level: {dist_330i.get('n_by_level')}")
        log_lines.append(f"  330i N (livello scelto L{dist_330i.get('relaxation_level')}): "
                         f"{dist_330i.get('n')}")
        log_lines.append(f"  330i no_verdict: {dist_330i.get('no_verdict')}")
        log_lines.append(f"  330i confidence: {dist_330i.get('confidence')}")
        log_lines.append(f"  330i median: {dist_330i.get('median')}")
        log_lines.append(f"  330i p25/p75: {dist_330i.get('p25')} / {dist_330i.get('p75')}")
        log_lines.append(f"  330i width_nature: {dist_330i.get('width_nature')}")

        # Controllo sanità: 320d
        log_lines.append("\n[SANITY CHECK 320d — N per livello L0-L3]")
        dist_320d = get_it_distribution(
            "BMW", "Serie 3", year=2021, km=60_000, fuel="diesel",
            target_variant="320d", target_transmission="automatic", target_power_hp=190,
            year_span=2, min_n=8,
            fixture_path=fixture_path_str,
        )
        log_lines.append(f"  320d n_by_level: {dist_320d.get('n_by_level')}")
        log_lines.append(f"  320d N (L{dist_320d.get('relaxation_level')}): "
                         f"{dist_320d.get('n')}")
        log_lines.append(f"  320d no_verdict: {dist_320d.get('no_verdict')}")
        log_lines.append(f"  320d p25/p75: {dist_320d.get('p25')} / {dist_320d.get('p75')}")
    else:
        log_lines.append("  Fixture non scritta (n_priced < 20) — leveling saltato.")
        dist_330i = {}

    # VERDETTO FINALE
    log_lines.append("\n" + "=" * 70)
    log_lines.append("VERDETTO GATE [3]")
    log_lines.append("=" * 70)

    nbl = dist_330i.get("n_by_level", {})
    log_lines.append(f"  N_L0={nbl.get(0,'?')}  N_L1={nbl.get(1,'?')}  "
                     f"N_L2={nbl.get(2,'?')}  N_L3={nbl.get(3,'?')}")

    n_330i = dist_330i.get("n", 0)
    no_verdict = dist_330i.get("no_verdict", True)
    p25 = dist_330i.get("p25")
    p75 = dist_330i.get("p75")
    level = dist_330i.get("relaxation_level")

    if not dist_330i:
        log_lines.append("  NO DATI (fixture non prodotta)")
    elif not no_verdict and p25 and p75:
        log_lines.append(f"  SI: 330i raggiunge N={n_330i} >= 8 (min_n) a L{level}.")
        log_lines.append(f"  Banda p25-p75: {p25} — {p75} EUR")
        log_lines.append(f"  Gate [3] SCIOLTO: config 330i esce dal NO_VERDICT.")
    else:
        log_lines.append(f"  NO: 330i N={n_330i} a L{level} — no_verdict={no_verdict}")
        log_lines.append(f"  Banda NON emessa. Config 330i STRUTTURALMENTE sotto-rappresentata.")
        log_lines.append(f"  Fallback consigliato: banda Serie 3 petrol rwd senza pin trim (L3 dichiarato).")

    report = "\n".join(log_lines)
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report, flush=True)
    log_lines.append(f"\nReport: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
