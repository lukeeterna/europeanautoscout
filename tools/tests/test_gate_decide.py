#!/usr/bin/env python3
r"""S267 DoD (b) — test sintetici IN-MEMORIA (NO rete) sulla decisione gate PURA.

Chiudono il debito S266 "gate AFFERMATO-NON-PROVATO": i due veicoli reali della
fixture NON discriminano il gate composto (320d passa con min_n 8 e 5; 330i cade
su N e width insieme). Qui si testa `_decide` diretta, forzando (N, width) ai
bracci che la fixture non esercita. La funzione pura blocca la tavola di verita'.

Run: python3 -m tools.tests.test_gate_decide
"""
from __future__ import annotations

import sys

from tools.it_market_price import _decide

MIN_N = 8  # = MIN_N_DEFAULT (it_market_price.py:38), ratificato Luke S265.


def _check(cond: bool, msg: str) -> int:
    print(("  OK: " if cond else "  !! FAIL: ") + msg)
    return 0 if cond else 1


def main() -> int:
    fail = 0
    print("=== S267 (b) — tavola di verita' gate _decide (no rete) ===")

    # T-A (FALSIFICATORE del braccio width): N>=min_n MA L3-indeterminato
    # (sub-pool trim-esatto <2 punti -> spread_infra_trim=None) DEVE NO_VERDICT.
    # Se si togliesse il braccio width da `no_verdict`, qui passerebbe = T-A rompe.
    nv, width, conf = _decide(
        n=10, min_n=MIN_N, relaxation_level=3,
        spread_pool=8000.0, spread_infra_trim=None, median=36000.0,
    )
    fail += _check(nv is True and width == "indeterminato" and conf == "NO_VERDICT",
                   f"T-A: N=10 L3 indeterminato -> NO_VERDICT (nv={nv} width={width} conf={conf})")

    # T-B (min_n=8 NON 5): N=7 con incertezza_campione (width dichiarabile) DEVE
    # NO_VERDICT a min_n=8; con min_n=5 PASSEREBBE -> prova che la soglia e' 8.
    nv8, w8, c8 = _decide(
        n=7, min_n=8, relaxation_level=3,
        spread_pool=1200.0, spread_infra_trim=1000.0, median=36000.0,
    )
    nv5, _, _ = _decide(
        n=7, min_n=5, relaxation_level=3,
        spread_pool=1200.0, spread_infra_trim=1000.0, median=36000.0,
    )
    fail += _check(nv8 is True and w8 == "incertezza_campione",
                   f"T-B: N=7 incertezza_campione @min_n=8 -> NO_VERDICT (nv={nv8} width={w8})")
    fail += _check(nv5 is False,
                   f"T-B/ctrl: stesso caso @min_n=5 NON e' NO_VERDICT (nv={nv5}) -> soglia=8 attiva")

    # T-C (confine + ramo MAI esercitato dai 2 veicoli): N=8 con incertezza_campione
    # DEVE dare verdetto, confidence=media (L3 non-fuso, non indeterminato).
    nvc, wc, cc = _decide(
        n=8, min_n=MIN_N, relaxation_level=3,
        spread_pool=1200.0, spread_infra_trim=1000.0, median=36000.0,
    )
    fail += _check(nvc is False and wc == "incertezza_campione" and cc == "media",
                   f"T-C: N=8 incertezza_campione -> verdetto conf=media (nv={nvc} width={wc} conf={cc})")

    print("\nTUTTI I CONTROLLI OK" if fail == 0 else f"{fail} CONTROLLI FALLITI")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
