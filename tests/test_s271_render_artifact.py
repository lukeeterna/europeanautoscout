#!/usr/bin/env python3
"""
tests/test_s271_render_artifact.py — S271/S272: render-verify del WIRING (DURABILE).

PERCHE' ESISTE (durabilita' DoD#4-i): test_s269_band_verdict.py testa solo la
LOGICA delle helper pure (zero pypdf). Il Frankenstein S268 e' nato dal WIRING
(helper giuste, ma _create_financial_analysis_v2 trascinava la mediana morta /
header con falso-PASS). Un unit-test di logica NON lo prende. Questo test
RIGENERA i 2 PDF dalla fixture committata e asserisce sullo STREAM reso (pypdf):
la regressione helper->cella-PDF e' presa SENZA lettura esterna.

DISCIPLINA S266 (invarianti STRUTTURALI, non N cablati): gli attesi sono
RICOMPUTATI dalle helper (_header_margin_envelope, evaluate_margin) sulla banda
della fixture corrente — NON hardcodati come "4.284". Cosi' il test sopravvive a
un cambio-fixture (ITEM 3 S272 sostituira' la fixture-cap con la scrape esaustiva:
ricalcola i bound da solo).

AMBIENTE: system python3 (reportlab 4.4.10 + pypdf 6.13.2). NON .venv (no reportlab).
Rigenera in tempdir: NON tocca i demo committati in tests/dossiers_s268/.

Run: python3 tests/test_s271_render_artifact.py   (oppure pytest)
"""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.margin_gate import evaluate_margin  # noqa: E402
from tools.scripts.build_s268_dossier import generate_dossiers  # noqa: E402
from tools.scripts.pdf_generator_enterprise import _header_margin_envelope  # noqa: E402

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    print("SKIP: pypdf assente (usa system python3, non .venv)")
    sys.exit(0)


# ---- formatter IDENTICO al generatore (_fmt riga 662 / _f riga 321) ----------
def _f(n):
    return f"{int(round(n)):,}".replace(",", ".")


def _norm(s):
    """Whitespace-collapse: reportlab+pypdf iniettano spazi spuri
    (es. '4.284' puo' uscire '4 284'). Normalizza prima del match."""
    return " ".join(s.split())


# ---- genera UNA volta in tempdir, indicizza per tag --------------------------
_TMP = tempfile.mkdtemp(prefix="s271_render_")
_ROWS = {tag: (path, veh, dist) for tag, path, veh, dist in generate_dossiers(_TMP)}


def _page_text(tag):
    path, _veh, _dist = _ROWS[tag]
    r = PdfReader(path)
    return "\n".join(p.extract_text() for p in r.pages)


def _header(full_text):
    """Header = inviluppo summary, PRIMA di 'DETTAGLI VEICOLO'."""
    return _norm(full_text.split("DETTAGLI VEICOLO")[0])


# ============================ 320d — CONDIZIONATO ============================

def test_320d_header_bound_inferiore_al_breakeven_non_band_low():
    """Header CONDIZIONATO: espone il margine al BREAK-EVEN (bound valido), MAI il
    margine a band_low (regione che il verdetto rifiuta = falso-PASS d'header).
    Tutti i numeri RICOMPUTATI dalla banda della fixture."""
    _path, veh, dist = _ROWS["320d_xDrive"]
    assert not dist.get("no_verdict"), "fixture 320d cambiata: atteso verdetto-banda"

    price = float(veh["price_eur"])
    band_low, band_high = float(dist["band_low"]), float(dist["band_high"])
    disp, bound_inf, status, breakeven = _header_margin_envelope(price, band_low, band_high)
    assert status == "CONDIZIONATO", status

    # falsificatore d'artefatto: margine a band_low (la regione rifiutata)
    margine_band_low = evaluate_margin(price, band_low).margine_netto_dealer

    hdr = _header(_page_text("320d_xDrive"))
    assert _f(bound_inf) in hdr, f"header NON contiene bound valido {_f(bound_inf)}"
    assert f"(se prezzo IT >= {_f(breakeven)})" in hdr, \
        f"header NON contiene la condizione breakeven {_f(breakeven)}"
    assert _f(margine_band_low) not in hdr, \
        f"header ESPONE il margine a band_low {_f(margine_band_low)} (falso-PASS)"


def test_320d_distribuzione_nbl_intera_non_clippata():
    """FIX-B S270: la nota 'L0:.. L1:.. L2:.. L3:..' (n_by_level) wrappata in
    Paragraph NON deve essere clippata. Stringa RICOSTRUITA da dist['n_by_level']."""
    _path, _veh, dist = _ROWS["320d_xDrive"]
    nbl = dist.get("n_by_level") or {}
    assert nbl, "fixture 320d senza n_by_level: impossibile verificare FIX-B"
    nbl_str = " ".join(f"L{k}:{v}" for k, v in sorted(nbl.items(), key=lambda x: int(x[0])))
    full = _norm(_page_text("320d_xDrive"))
    assert nbl_str in full, f"nota distribuzione clippata: atteso '{nbl_str}'"


def test_320d_no_legacy_financial_path():
    """Whole-page: nessun residuo del path legacy _create_financial_analysis
    (mediana morta 38.799 / 'Media mercato' / fee flat 900). Markers STRUTTURALI
    di feature morte — letterali by design, non valori della fixture."""
    full = _norm(_page_text("320d_xDrive"))
    for dead in ("38.799", "Media mercato", "900"):
        assert dead not in full, f"residuo legacy presente: {dead!r}"


# ============================ 330i — NO_VERDICT =============================

def test_330i_header_nessuna_cifra_margine():
    """NO_VERDICT: header margine = 'n.d.', ZERO cifre-margine. Falsificatore:
    se l'header ricalcolasse la banda 330i, esporrebbe i bound RICOMPUTATI ->
    asserisce la loro ASSENZA (suppressione totale all'header)."""
    _path, veh, dist = _ROWS["330i"]
    assert dist.get("no_verdict"), "fixture 330i cambiata: atteso NO_VERDICT"

    hdr = _header(_page_text("330i"))
    assert "n.d." in hdr, "header NO_VERDICT non espone 'n.d.'"

    # cosa esporrebbe l'header SE (erroneamente) ricalcolasse la banda 330i
    price = float(veh["price_eur"])
    bl, bh = dist.get("band_low"), dist.get("band_high")
    if bl is not None and bh is not None:
        ml = evaluate_margin(price, float(bl)).margine_netto_dealer
        mh = evaluate_margin(price, float(bh)).margine_netto_dealer
        assert _f(ml) not in hdr, f"header NO_VERDICT espone margine {_f(ml)}"
        assert _f(mh) not in hdr, f"header NO_VERDICT espone margine {_f(mh)}"


def test_330i_verdetto_minimale_nessuna_voce_margine():
    """NO_VERDICT: la sezione VERDETTO AFFARE e' minimale — nessuna label di
    margine/banda (Spread/Surplus/Pavimento/MARGINE NETTO). Label STRUTTURALI."""
    full = _page_text("330i")
    seg = _norm(full.split("VERDETTO AFFARE")[1].split("MERCATO ITALIA")[0])
    for bad in ("Spread", "Surplus", "Pavimento dealer", "MARGINE NETTO"):
        assert bad not in seg, f"verdetto NO_VERDICT contiene voce margine: {bad!r}"


if __name__ == "__main__":
    tests = [
        test_320d_header_bound_inferiore_al_breakeven_non_band_low,
        test_320d_distribuzione_nbl_intera_non_clippata,
        test_320d_no_legacy_financial_path,
        test_330i_header_nessuna_cifra_margine,
        test_330i_verdetto_minimale_nessuna_voce_margine,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} PASS  (tempdir: {_TMP})")
    sys.exit(1 if failed else 0)
