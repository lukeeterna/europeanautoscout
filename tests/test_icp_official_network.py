#!/usr/bin/env python3
"""
tests/test_icp_official_network.py — gate codice (ZERO RETE) per l'esclusione dei
concessionari UFFICIALI di rete dal filtro ICP (tools/profile_pool_icp.py).

Casi sintetici del mandato:
  (a) "Centro Porsche Latina"                         -> escluso, reason OFFICIAL_NETWORK:...
  (b) "Autosalone Rossi srl" (multimarca)             -> passa (nessun match rete)
  (c) "Da Mario Auto - concessionaria ufficiale Kia"  -> escluso ("concessionaria ufficiale")

FALSIFICATORI: se il check OFFICIAL_NETWORK viene rimosso da icp_verdict, (a) e (c)
tornerebbero ICP-VALID e questi test fallirebbero.

Run: python3 tests/test_icp_official_network.py   (oppure pytest)
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.profile_pool_icp import (  # noqa: E402
    icp_verdict,
    official_network_match,
)


def _profile(company_name, top_brands=None, stock=12):
    return {
        "company_name": company_name,
        "top_brands": top_brands if top_brands is not None else ["Porsche", "BMW"],
        "stock_count": stock,
    }


# --- (a) Centro Porsche Latina -> escluso ------------------------------------

def test_centro_porsche_latina_excluded():
    is_icp, reason, _ = icp_verdict(_profile("Centro Porsche Latina"))
    assert is_icp is False, reason
    assert reason == "OFFICIAL_NETWORK:Centro Porsche", reason


# --- (b) Autosalone Rossi srl multimarca -> passa ----------------------------

def test_autosalone_rossi_passes():
    is_icp, reason, _ = icp_verdict(
        _profile("Autosalone Rossi srl", top_brands=["Audi", "BMW", "Fiat"])
    )
    assert is_icp is True, reason
    assert reason == "ICP-VALID", reason


# --- (c) concessionaria ufficiale Kia -> escluso -----------------------------

def test_concessionaria_ufficiale_excluded():
    is_icp, reason, _ = icp_verdict(
        _profile("Da Mario Auto - concessionaria ufficiale Kia")
    )
    assert is_icp is False, reason
    assert reason == "OFFICIAL_NETWORK:concessionaria ufficiale", reason


# --- match helper: word-boundary, case-insensitive ---------------------------

def test_match_case_insensitive():
    assert official_network_match("CENTRO PORSCHE TRENTO") == "Centro Porsche"


def test_no_false_positive_on_independent():
    # brand nel top_brands ma NON nel nome: nessun match rete
    assert official_network_match("Auto Giannini srl") is None
    assert official_network_match("Scotti Srl - Automobili Per Passione") is None


def test_official_network_beats_stock_and_tier():
    # anche con stock valido + tier match, la rete ufficiale vince (hard-exclude)
    is_icp, reason, hits = icp_verdict(
        _profile("Porsche Zentrum Muenchen", top_brands=["Porsche"], stock=5)
    )
    assert is_icp is False, reason
    assert reason == "OFFICIAL_NETWORK:Porsche Zentrum", reason


if __name__ == "__main__":
    tests = [
        test_centro_porsche_latina_excluded,
        test_autosalone_rossi_passes,
        test_concessionaria_ufficiale_excluded,
        test_match_case_insensitive,
        test_no_false_positive_on_independent,
        test_official_network_beats_stock_and_tier,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} PASS")
    sys.exit(1 if failed else 0)
