#!/usr/bin/env python3
r"""S266 DoD — test NO-RETE su fixture reale committata (chiude debito S264).

Gira su tests/fixtures/it_dist_bmw_serie3_2021.json (output di build_it_fixture.py,
scrape profonda reale persistita UNA volta). Verifica invarianti STRUTTURALI,
non numeri di mercato hardcoded: i conteggi reali (N, livello) vivono nella
fixture e si leggono, non si presumono. Riproducibile a ogni sessione senza rete.

Run: python3 -m tools.tests.test_it_distribution_fixture
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.it_market_price import get_it_distribution

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "it_dist_bmw_serie3_2021.json"


def _check(cond: bool, msg: str) -> int:
    print(("  OK: " if cond else "  !! FAIL: ") + msg)
    return 0 if cond else 1


def main() -> int:
    if not FIXTURE.exists():
        print(f"!! fixture mancante: {FIXTURE}\n   esegui prima: python3 -m tools.scripts.build_it_fixture")
        return 1

    meta = (json.loads(FIXTURE.read_text(encoding="utf-8")).get("meta") or {})
    fixture_date = meta.get("scrape_date")
    fail = 0

    # 320d xDrive 2021 diesel awd
    d320 = get_it_distribution(
        "BMW", "Serie 3", year=2021, km=60_000, fuel="diesel",
        target_variant="320d xDrive", target_transmission="automatic", target_power_hp=190,
        fixture_path=str(FIXTURE),
    )
    # 330i 2021 petrol
    d330 = get_it_distribution(
        "BMW", "Serie 3", year=2021, km=50_000, fuel="petrol",
        target_variant="330i", target_transmission="automatic", target_power_hp=258,
        fixture_path=str(FIXTURE),
    )

    print(f"\n=== fixture {FIXTURE.name} (scrape_date={fixture_date}, n_raw={meta.get('n_raw')}) ===")
    for tag, d in (("320d xDrive", d320), ("330i", d330)):
        print(f"  [{tag}] n={d['n']} level=L{d['relaxation_level']} "
              f"no_verdict={d['no_verdict']} band={d['band_low']}..{d['band_high']} "
              f"conf={d['confidence']} width={d['width_nature']}")

    print("\n=== invarianti (no rete) ===")
    # (1) scrape_date = fotografia della fixture, NON oggi (GAP-2).
    fail += _check(d320["scrape_date"] == fixture_date,
                   f"scrape_date dalla fixture ({d320['scrape_date']}), non da date.today()")
    # (2) determinismo: stesso input -> stesso output (riproducibilita' S264).
    d320b = get_it_distribution(
        "BMW", "Serie 3", year=2021, km=60_000, fuel="diesel",
        target_variant="320d xDrive", target_transmission="automatic", target_power_hp=190,
        fixture_path=str(FIXTURE),
    )
    fail += _check(d320b["n"] == d320["n"] and d320b["band_low"] == d320["band_low"],
                   "due chiamate identiche -> stesso N e stessa banda (deterministico)")
    # (3) gate composto coerente (Luke S265): no_verdict <=> N<min_n OR L3-indeterminato.
    for tag, d in (("320d", d320), ("330i", d330)):
        l3_unverif = (d["relaxation_level"] == 3 and d["spread_infra_trim"] is None)
        expect_nv = (d["n"] < d["min_n"]) or l3_unverif
        fail += _check(d["no_verdict"] == expect_nv,
                       f"[{tag}] no_verdict={d['no_verdict']} coerente col gate composto")
    # (4) confidence onesta su dato reale: mai "alta" a L3.
    for tag, d in (("320d", d320), ("330i", d330)):
        fail += _check(not (d["relaxation_level"] == 3 and d["confidence"] == "alta"),
                       f"[{tag}] L3 non e' mai 'alta' (anti falso-PASS)")
    # (5) banda contiene la mediana quando c'e' verdetto con N>=2.
    for tag, d in (("320d", d320), ("330i", d330)):
        if not d["no_verdict"] and d["n"] >= 2:
            fail += _check(d["band_low"] <= d["median"] <= d["band_high"],
                           f"[{tag}] band_low <= median <= band_high")

    print("\nTUTTI I CONTROLLI OK" if fail == 0 else f"{fail} CONTROLLI FALLITI")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
