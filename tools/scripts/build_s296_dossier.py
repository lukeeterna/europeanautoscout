#!/usr/bin/env python3
r"""S296 UNITÀ B — genera 3 PDF di prova del template dossier v2 (artifact-layer).

NESSUN edit al generatore/band-logic: questo driver costruisce solo i payload e
invoca `generate_dossier_from_data`. Pattern = tools/scripts/build_s268_dossier.py.

3 casi (verifica RESA template v2 sull'artefatto, non solo sul diff):
  (a) 330i REALE su fixture geo-pura cont4 -> banda con dicitura FALLBACK (L3 adiacente)
  (b) sintetico NO_VERDICT -> blocco "Campione insufficiente", NESSUNA banda
  (c) sintetico exact-config -> banda SENZA dicitura fallback (L<=2)

Run:  python3 -m tools.scripts.build_s296_dossier
"""
from __future__ import annotations

import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

FIXTURE_CONT4 = os.path.join(
    _REPO, "tests", "fixtures", "it_dist_bmw_serie3_2021_s273cont4.json")
OUT_DIR = os.path.join(_REPO, "tests", "dossiers_s296")


def _preflight() -> None:
    try:
        import reportlab  # noqa: F401
    except Exception as e:  # pragma: no cover
        print(f"PRE-FLIGHT FAIL: reportlab non importabile ({e})", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(FIXTURE_CONT4):
        print(f"PRE-FLIGHT FAIL: fixture cont4 assente {FIXTURE_CONT4}", file=sys.stderr)
        sys.exit(1)


def payload_a_real_fallback():
    """(a) 330i REALE dalla fixture geo-pura cont4 -> fallback_declared=True."""
    from tools.it_market_price import get_it_distribution
    from tools.margin_gate import evaluate_margin

    dist = get_it_distribution(
        make="BMW", model="Serie 3", year=2021, km=45_000, fuel="petrol",
        target_variant="330i", target_transmission="automatic",
        target_power_hp=258, fixture_path=FIXTURE_CONT4)
    dist["is_floor"] = True

    prezzo_eu = 31000
    veh = {
        "make": "BMW", "model": "Serie 3", "year": 2021, "km": 45_000,
        "price_eur": prezzo_eu, "fuel_type": "petrol", "transmission": "automatic",
        "_cove_confidence": 0.75,
        "country": "NL",                 # classe-regime interna -> output country-free
        "_fraud_doc_obtained": True,     # esercita il grado di certezza reale
        "_it_distribution": dist,
    }
    if dist.get("no_verdict"):
        veh["_margin_decision"] = "NO_VERDICT"
    elif dist.get("median") is not None:
        veh["_margin_decision"] = evaluate_margin(
            float(prezzo_eu), float(dist["median"])).decision
    return veh, dist


def payload_b_no_verdict():
    """(b) sintetico NO_VERDICT -> nessuna banda."""
    dist = {
        "n": 3, "relaxation_level": 3, "no_verdict": True,
        "median": None, "band_low": None, "band_high": None,
        "p25": None, "p75": None, "confidence": "nulla",
        "source": "AutoScout24.it", "scrape_date": "2026-07-04",
        "is_floor": True, "fallback_declared": False,
    }
    veh = {
        "make": "BMW", "model": "Serie 3", "year": 2021, "km": 52_000,
        "price_eur": 30000, "fuel_type": "petrol", "transmission": "automatic",
        "_cove_confidence": 0.70, "country": "BE",
        "_margin_decision": "NO_VERDICT",
        "_it_distribution": dist,
    }
    return veh, dist


def payload_c_exact():
    """(c) sintetico exact-config -> banda SENZA fallback (L<=2)."""
    from tools.margin_gate import evaluate_margin

    dist = {
        "n": 15, "relaxation_level": 1, "no_verdict": False,
        "median": 31000.0, "band_low": 28000.0, "band_high": 34000.0,
        "p25": 28000.0, "p75": 34000.0, "confidence": "media",
        "n_by_level": {"1": 15}, "source": "AutoScout24.it",
        "scrape_date": "2026-07-04", "is_floor": True,
        "fallback_declared": False,
    }
    prezzo_eu = 29000
    veh = {
        "make": "BMW", "model": "Serie 3", "year": 2021, "km": 40_000,
        "price_eur": prezzo_eu, "fuel_type": "petrol", "transmission": "automatic",
        "_cove_confidence": 0.80, "country": "FR",
        "_margin_decision": evaluate_margin(
            float(prezzo_eu), float(dist["median"])).decision,
        "_it_distribution": dist,
    }
    return veh, dist


CASES = [
    ("a_330i_REAL_fallback", payload_a_real_fallback, "DEMO S296 A"),
    ("b_NO_VERDICT", payload_b_no_verdict, "DEMO S296 B"),
    ("c_exact_config", payload_c_exact, "DEMO S296 C"),
]


def main() -> int:
    _preflight()
    from tools.scripts.pdf_generator_enterprise import generate_dossier_from_data

    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for tag, fn, dealer in CASES:
        veh, dist = fn()
        out_path = os.path.join(OUT_DIR, f"ARGOS_DEMO_S296_{tag}.pdf")
        data_json = json.dumps({"vehicles": [veh]})
        result = generate_dossier_from_data(
            data_json, dealer_name=dealer, output_path=out_path)
        rows.append((tag, result, dist))

    for tag, result, dist in rows:
        print(f"[{tag}] n={dist.get('n')} L{dist.get('relaxation_level')} "
              f"no_verdict={dist.get('no_verdict')} "
              f"fallback={dist.get('fallback_declared')} "
              f"band={dist.get('band_low')}-{dist.get('band_high')} -> {result}")

    print("\nUNITÀ B — 3 PDF:")
    ok_all = True
    for tag, p, _dist in rows:
        ok = os.path.isfile(p) and os.path.getsize(p) > 0
        ok_all = ok_all and ok
        print(f"  {'OK ' if ok else 'MISSING '}{p} "
              f"({os.path.getsize(p) if ok else 0} byte)")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
