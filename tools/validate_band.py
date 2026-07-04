"""ARGOS Band Gate (S295) — gate-soglia-N deterministico per la BANDA prezzo IT.

Asse "la banda esce SOLO dal gate". Analogo strutturale a validate_kb.py
(gate deterministico, exit-code, self-test falsificabile) e gemello di
margin_gate.py nel namespace pricing (tools/): dataclass result + funzione
PURA + `_selftest()`.

PROBLEMA che chiude: prima la banda p25-p75 usciva inline da get_it_distribution
(it_market_price.py `_decide`), mescolata con confidence/width_nature. Il rischio
strutturale (ucciso S256-S262) e' la BANDA FABBRICATA: p25-p75 calcolati su un
pugno di comparabili e spacciati per verdetto. Qui l'invariante e' DURO e in UN
solo posto:

    N_exact  < soglia  E  N_adiacente < soglia  ->  NO_VERDICT, banda = None
    N_exact >= soglia                            ->  banda p25-p75 (fallback_declared=False)
    N_exact  < soglia  ma N_adiacente >= soglia  ->  banda p25-p75 (fallback_declared=True)

soglia_n default = it_market_price.MIN_N_DEFAULT (=8, RATIFICATO Luke S265):
exact-config raramente raggiunge >=8 annunci sul mercato IT, quindi il fallback
config-adiacente (drop trim_line, L3) e' la regola documentata — ma DEVE essere
DICHIARATO (fallback_declared=True), mai silenzioso.

Mapping livelli (it_market_price._levels):
    L0/L1/L2 = config ESATTA  (engine+drivetrain+trim+fuel tenuti)
    L3        = config ADIACENTE (trim_line droppato) = FALLBACK

NON tocca cove_engine_v4.py. NON calcola margini (quello e' margin_gate).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, asdict
from typing import Optional

from .it_market_price import MIN_N_DEFAULT  # soglia ratificata Luke S265 (=8)

# Soglia-N di default: unica fonte di verita' = it_market_price.MIN_N_DEFAULT.
SOGLIA_N_DEFAULT: int = MIN_N_DEFAULT


@dataclass
class BandResult:
    verdict: str                  # "VERDICT" | "NO_VERDICT"
    band_low: Optional[float]     # p25 (None se NO_VERDICT)
    band_high: Optional[float]    # p75 (None se NO_VERDICT)
    n_exact: int                  # N config esatta (max livelli L0-L2)
    n_adjacent: int               # N config adiacente (L3, trim droppato)
    soglia_n: int
    fallback_declared: bool       # True SOLO se la banda viene dal pool adiacente
    source: Optional[str]         # "exact" | "adjacent" | None

    def to_dict(self) -> dict:
        return asdict(self)


def _band_p25_p75(prices: list) -> tuple[float, float]:
    """p25-p75 (quartili inclusivi, come it_market_price). Richiede >=2 prezzi."""
    s = sorted(float(p) for p in prices)
    if len(s) < 2:
        # Non raggiungibile con soglia>=2, ma guardia difensiva: banda degenere.
        return round(s[0], 2), round(s[0], 2)
    q = statistics.quantiles(s, n=4, method="inclusive")
    return round(q[0], 2), round(q[2], 2)


def evaluate_band(
    exact_prices: list,
    adjacent_prices: list,
    soglia_n: int = SOGLIA_N_DEFAULT,
) -> BandResult:
    """GATE PURO: la banda esce SOLO da qui, mai da un if a mano.

    Args:
        exact_prices:    prezzi (EUR) dei comparabili a config ESATTA (L0-L2).
        adjacent_prices: prezzi (EUR) dei comparabili a config ADIACENTE (L3).
        soglia_n:        N minimo per emettere banda (default 8, Luke S265).

    Invariante DURO (testato in _selftest):
        - N_exact < soglia E N_adiacente < soglia  =>  NO_VERDICT, banda None.
        - N_exact >= soglia                        =>  banda exact, no fallback.
        - N_exact < soglia ma N_adiacente >= soglia => banda adiacente, fallback.
      La banda NON e' MAI fabbricata su N < soglia.
    """
    n_exact = len(exact_prices)
    n_adjacent = len(adjacent_prices)

    # 1) config esatta ha priorita': se raggiunge la soglia, banda senza fallback.
    if n_exact >= soglia_n:
        low, high = _band_p25_p75(exact_prices)
        return BandResult("VERDICT", low, high, n_exact, n_adjacent,
                          soglia_n, False, "exact")

    # 2) fallback config-adiacente (DICHIARATO): banda dal pool L3.
    if n_adjacent >= soglia_n:
        low, high = _band_p25_p75(adjacent_prices)
        return BandResult("VERDICT", low, high, n_exact, n_adjacent,
                          soglia_n, True, "adjacent")

    # 3) invariante duro: nessun livello raggiunge la soglia -> NIENTE banda.
    return BandResult("NO_VERDICT", None, None, n_exact, n_adjacent,
                      soglia_n, False, None)


# ---------------------------------------------------------------------------
# Adapter Unita' C: instrada un pool geo-puro REALE (variant, fuel) nel gate.
# Riusa le primitive canoniche di it_market_price (nessuna duplicazione della
# logica di matching/leveling): estrae i prezzi per livello e li passa al gate.
# ---------------------------------------------------------------------------

def level_prices_from_pool(
    make: str,
    model: str,
    year: int,
    km: int,
    fuel: Optional[str],
    *,
    target_variant: str,
    target_transmission: Optional[str] = None,
    target_power_hp: Optional[int] = None,
    fixture_path: Optional[str] = None,
    year_span: int = 1,
) -> dict:
    """Prezzi per livello L0..L3 dallo STESSO pool/leveling di get_it_distribution.

    Ritorna {0:[...],1:[...],2:[...],3:[...]} (prezzi EUR). Usa la fixture se
    passata (geo-pura, S294), altrimenti scrape live. Non decide nulla: la
    decisione e' del gate (evaluate_band).
    """
    from .it_market_price import (
        derive_trim_family, _levels, _match, _load_fixture,
        KM_BAND_DEFAULT,
    )
    from .scrapers.autoscout_scraper import AutoScoutScraper

    if fixture_path:
        raw, _scrape_date = _load_fixture(fixture_path)
    else:
        scraper = AutoScoutScraper("autoscout24_it")
        raw = scraper.scrape_model(
            make=make, model=model,
            year_min=year - 2, year_max=year + 2,
        )

    target = derive_trim_family(
        target_variant or "", fuel, target_transmission, target_power_hp or 0,
    )

    pool = []
    for lst in raw:
        price = getattr(lst, "price_eur", 0) or 0
        if price <= 0:
            continue
        ft = getattr(lst, "fuel_type", None)
        ftv = getattr(ft, "value", str(ft)) if ft is not None else ""
        tr = getattr(lst, "transmission", None)
        trv = getattr(tr, "value", str(tr)) if tr is not None else ""
        cspec = derive_trim_family(
            getattr(lst, "variant", "") or "", ftv, trv,
            getattr(lst, "power_hp", 0) or 0,
        )
        pool.append((
            float(price), cspec,
            int(getattr(lst, "km", 0) or 0),
            int(getattr(lst, "year", 0) or 0),
        ))

    out: dict = {}
    for i, cfg in enumerate(_levels(year_span)):
        out[i] = [
            p[0] for p in pool
            if _match(target, p[1], p[2], p[3], km, year, KM_BAND_DEFAULT, cfg)
        ]
    return out


def gate_it_band(
    make: str,
    model: str,
    year: int,
    km: int,
    fuel: Optional[str],
    *,
    target_variant: str,
    target_transmission: Optional[str] = None,
    target_power_hp: Optional[int] = None,
    fixture_path: Optional[str] = None,
    year_span: int = 1,
    soglia_n: int = SOGLIA_N_DEFAULT,
) -> dict:
    """Instrada il pool geo-puro (variant, fuel) DENTRO evaluate_band.

    exact  = livello ESATTO piu' stretto (L0->L2) che raggiunge la soglia; se
             nessuno la raggiunge, L2 (config esatta piu' larga) cosi' n_exact
             riflette la massima disponibilita' a trim tenuto.
    adjacent = L3 (trim droppato = fallback).
    Ritorna il dict del BandResult + n_by_level per la riga d'onesta'.
    """
    lp = level_prices_from_pool(
        make, model, year, km, fuel,
        target_variant=target_variant,
        target_transmission=target_transmission,
        target_power_hp=target_power_hp,
        fixture_path=fixture_path,
        year_span=year_span,
    )
    n_by_level = {i: len(lp[i]) for i in lp}

    # exact = livello esatto piu' stretto che raggiunge la soglia, else L2.
    exact_prices = lp[2]
    for lvl in (0, 1, 2):
        if len(lp[lvl]) >= soglia_n:
            exact_prices = lp[lvl]
            break
    adjacent_prices = lp[3]

    res = evaluate_band(exact_prices, adjacent_prices, soglia_n).to_dict()
    res["n_by_level"] = n_by_level
    res["target_variant"] = target_variant
    res["fuel"] = fuel
    return res


# ---------------------------------------------------------------------------
# Self-test SINTETICO (Unita' A) — 3 case, fixture sintetica, NON serve il pool
# reale. Falsifica l'invariante duro del gate.
# ---------------------------------------------------------------------------

def _selftest() -> int:
    """DoD Unita' A: 3 case sintetici sull'invariante del gate-banda."""
    failed = 0
    SOGLIA = 8

    # (a) N sotto soglia su exact E adiacente -> NO_VERDICT, banda None.
    exact_a = [30000.0, 31000.0, 29500.0]          # 3 < 8
    adj_a = [28000.0, 33000.0, 30500.0, 31500.0]   # 4 < 8
    ra = evaluate_band(exact_a, adj_a, SOGLIA)
    print("=== (a) sotto soglia exact E adiacente ===")
    print(f"  n_exact={ra.n_exact} n_adjacent={ra.n_adjacent} "
          f"verdict={ra.verdict} band=({ra.band_low},{ra.band_high}) "
          f"fallback={ra.fallback_declared}")
    if not (ra.verdict == "NO_VERDICT" and ra.band_low is None
            and ra.band_high is None):
        print("  !! FAIL: doveva essere NO_VERDICT con banda None")
        failed += 1
    else:
        print("  OK: NO_VERDICT, banda None (nessuna banda fabbricata)")

    # (b) N>=soglia su exact -> banda p25-p75, fallback_declared False.
    exact_b = [30000.0, 31000.0, 32000.0, 33000.0,
               34000.0, 35000.0, 36000.0, 37000.0, 38000.0]  # 9 >= 8
    adj_b = [10000.0, 90000.0]                                # irrilevante
    rb = evaluate_band(exact_b, adj_b, SOGLIA)
    exp_low, exp_high = _band_p25_p75(exact_b)
    print("\n=== (b) exact >= soglia ===")
    print(f"  n_exact={rb.n_exact} verdict={rb.verdict} "
          f"band=({rb.band_low},{rb.band_high}) fallback={rb.fallback_declared} "
          f"source={rb.source}")
    if not (rb.verdict == "VERDICT" and rb.fallback_declared is False
            and rb.band_low == exp_low and rb.band_high == exp_high
            and rb.band_low is not None and rb.band_low < rb.band_high):
        print(f"  !! FAIL: attesa banda exact ({exp_low},{exp_high}) senza fallback")
        failed += 1
    else:
        print(f"  OK: banda exact p25-p75=({rb.band_low},{rb.band_high}), no fallback")

    # (c) exact<soglia ma adiacente>=soglia -> banda emessa, fallback True.
    exact_c = [30000.0, 31000.0, 32000.0]                     # 3 < 8
    adj_c = [25000.0, 26000.0, 27000.0, 28000.0,
             29000.0, 30000.0, 31000.0, 32000.0, 33000.0, 34000.0]  # 10 >= 8
    rc = evaluate_band(exact_c, adj_c, SOGLIA)
    exp_low_c, exp_high_c = _band_p25_p75(adj_c)
    print("\n=== (c) exact<soglia, adiacente>=soglia (fallback) ===")
    print(f"  n_exact={rc.n_exact} n_adjacent={rc.n_adjacent} verdict={rc.verdict} "
          f"band=({rc.band_low},{rc.band_high}) fallback={rc.fallback_declared} "
          f"source={rc.source}")
    if not (rc.verdict == "VERDICT" and rc.fallback_declared is True
            and rc.band_low == exp_low_c and rc.band_high == exp_high_c
            and rc.band_low is not None):
        print(f"  !! FAIL: attesa banda adiacente ({exp_low_c},{exp_high_c}) con fallback")
        failed += 1
    else:
        print(f"  OK: banda adiacente=({rc.band_low},{rc.band_high}), fallback DICHIARATO")

    print(f"\n{'TUTTI I TEST PASSATI' if failed == 0 else f'{failed} TEST FALLITI'}")
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(1 if _selftest() else 0)
