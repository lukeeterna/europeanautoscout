#!/usr/bin/env python3
"""Check deterministico gate base-mercato (anello BM) — S298.

Chiude la riga stale "base-mercato NON affidabile (cap-truncated)" (finding S273
SUPERSEDED). La base-mercato E' chiusa da S295-C: fixture geo-pura esaustiva
committata (ebe422e) + gate banda deterministico (d586f03). Questo check e' il
fatto terminale che il generatore (state/refresh.py) esegue per marcare l'anello.

Invariante (DEVE poter FALLIRE):
  1. la fixture geo-pura esaustiva esiste su disco;
  2. contiene 323 listing con prezzo (n_priced, meta esaustiva 21 pagine,
     terminated_by_empty=true — NON i 325 cap-truncated di S273);
  3. gate_it_band gira sul 330i REALE della fixture ed emette un verdict
     ('VERDICT'|'NO_VERDICT') senza eccezioni.

Se la fixture sparisce -> (1)/(2) FAIL. Se il gate si rompe -> (3) eccezione = FAIL.
exit 0 = PASS, exit 1 = FAIL. Offline puro (fixture, zero rete).
"""
from __future__ import annotations

import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

FIXTURE = os.path.join(
    _REPO, "tests", "fixtures", "it_dist_bmw_serie3_2021_s273cont4.json")
N_PRICED_EXPECTED = 323


def main() -> int:
    # (1) fixture esiste
    if not os.path.isfile(FIXTURE):
        print(f"FAIL (1): fixture geo-pura assente: {FIXTURE}")
        return 1

    # (2) count 323 con prezzo, meta esaustiva (non cap-truncated)
    d = json.load(open(FIXTURE, encoding="utf-8"))
    listings = d.get("listings", [])
    n_priced = sum(1 for x in listings if (x.get("price_eur") or 0) > 0)
    meta = d.get("meta", {})
    if n_priced != N_PRICED_EXPECTED:
        print(f"FAIL (2): n_priced={n_priced} != {N_PRICED_EXPECTED}")
        return 1
    if not meta.get("terminated_by_empty"):
        print("FAIL (2): meta.terminated_by_empty non True "
              "(base-mercato non esaustiva = cap-truncated)")
        return 1

    # (3) gate emette verdict senza eccezioni sul 330i reale della fixture
    from tools.validate_band import gate_it_band
    g = gate_it_band(
        make="BMW", model="Serie 3", year=2021, km=45_000, fuel="petrol",
        target_variant="330i", target_transmission="automatic",
        target_power_hp=258, fixture_path=FIXTURE)
    if g.get("verdict") not in ("VERDICT", "NO_VERDICT"):
        print(f"FAIL (3): gate_it_band verdict inatteso: {g.get('verdict')!r}")
        return 1

    print(f"PASS: fixture esaustiva n_priced={n_priced} pages="
          f"{meta.get('pages_scraped')} terminated_by_empty=True · "
          f"gate verdict={g['verdict']} fallback={g['fallback_declared']} "
          f"n_by_level={g['n_by_level']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
