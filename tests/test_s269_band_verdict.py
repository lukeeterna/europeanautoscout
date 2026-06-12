#!/usr/bin/env python3
"""
tests/test_s269_band_verdict.py — S269/S270 verdetto-affare sull'INTERA banda IT.

Gate codice (no rete) per le tre funzioni pure introdotte in S269 (_band_verdict,
_margin_verdict_rows) e S270 (_header_margin_envelope FIX-A). I numeri attesi sono
stati ottenuti ESEGUENDO il codice reale (margin_gate.evaluate_margin), non a mano.

FALSIFICATORI (devono FALLIRE se la logica viene degradata):
  - _band_verdict: rimuovendo il ramo CONDIZIONATO, un caso che ATTRAVERSA il
    pavimento dealer tornerebbe 'PASS' secco -> test_band_verdict_crosses_floor.
  - _header_margin_envelope: forzando il ramo CONDIZIONATO a usare band_low
    (margine 1.785, regione che il verdetto RIFIUTA), l'header esporrebbe 1.785
    -> test_header_envelope_condizionato asserisce round(bound_inf)==4284 e !=1785.
  - _margin_verdict_rows(no_verdict): se reintroducesse banda/spread/surplus nel
    caso senza verdetto -> test_no_verdict_minimal fallisce.

Run: python3 tests/test_s269_band_verdict.py   (oppure pytest tests/test_s269_band_verdict.py)
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.scripts.pdf_generator_enterprise import (  # noqa: E402
    _band_verdict,
    _header_margin_envelope,
    _margin_verdict_rows,
    VehicleData,
)


# --- _band_verdict -----------------------------------------------------------

def test_band_verdict_320d_condizionato():
    """320d reale: price 29500, banda IT 33200-39950 -> CONDIZIONATO @ 35699."""
    _ml, _mh, breakeven, status, _label = _band_verdict(29500, 33200, 39950)
    assert status == "CONDIZIONATO", status
    assert round(breakeven) == 35699, breakeven


def test_band_verdict_crosses_floor_never_pass():
    """FALSIFICATORE: banda che attraversa il pavimento (m_low REJECT, m_high PASS)
    NON deve mai dare 'PASS' secco. Togliendo il ramo CONDIZIONATO da _band_verdict
    questo test fallisce."""
    m_low, m_high, _be, status, _label = _band_verdict(29500, 33200, 39950)
    assert m_low.decision == "REJECT", m_low.decision      # bordo basso sotto pavimento
    assert m_high.decision == "PASS", m_high.decision       # bordo alto sopra
    assert status != "PASS", status
    assert status == "CONDIZIONATO", status


# --- _margin_verdict_rows (NO_VERDICT) --------------------------------------

def test_no_verdict_minimal():
    """no_verdict=True -> riga minimale (3 righe), NESSUNA banda/spread/surplus."""
    v = VehicleData(
        make="BMW", model="330i", year=2021, km=40000,
        price_eu=27000, price_it_estimate=30000, confidence=0.7,
        no_verdict=True, it_band_low=25299, it_band_high=30900,
        it_n=5, relaxation_level=2,
    )
    rows, status, breakeven = _margin_verdict_rows(v)
    assert status == "NO_VERDICT", status
    assert breakeven is None
    assert len(rows) == 3, rows
    flat = " ".join(str(c) for r in rows for c in r)
    for forbidden in ("Spread", "Surplus", "25.299", "30.900", "–"):
        assert forbidden not in flat, f"cella vietata presente: {forbidden!r}"


# --- _header_margin_envelope (S270 FIX-A) -----------------------------------

def test_header_envelope_condizionato():
    """CONDIZIONATO: bound inferiore = margine al BREAK-EVEN (4.284), MAI a band_low
    (1.785, che il verdetto rifiuta). disp deve esporre la condizione '>= 35.699'."""
    disp, bound_inf, status, breakeven = _header_margin_envelope(29500, 33200, 39950)
    assert status == "CONDIZIONATO", status
    assert round(bound_inf) == 4284, bound_inf
    assert round(bound_inf) != 1785                       # falsificatore band_low
    assert "35.699" in disp, disp
    assert round(breakeven) == 35699, breakeven


def test_header_envelope_reject():
    """REJECT (banda interamente sotto il pavimento): regione valida vuota ->
    'n.d.', MAI un range; bound_inf None."""
    disp, bound_inf, status, _be = _header_margin_envelope(35000, 33000, 36000)
    assert status == "REJECT", status
    assert disp == "n.d.", disp
    assert bound_inf is None


def test_header_envelope_pass():
    """PASS (banda interamente sopra il pavimento): bound_inf = margine a band_low."""
    disp, bound_inf, status, _be = _header_margin_envelope(20000, 30000, 35000)
    assert status == "PASS", status
    assert round(bound_inf) == 6291, bound_inf
    assert "n.d." not in disp


if __name__ == "__main__":
    tests = [
        test_band_verdict_320d_condizionato,
        test_band_verdict_crosses_floor_never_pass,
        test_no_verdict_minimal,
        test_header_envelope_condizionato,
        test_header_envelope_reject,
        test_header_envelope_pass,
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
