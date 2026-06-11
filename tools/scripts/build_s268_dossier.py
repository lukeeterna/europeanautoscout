#!/usr/bin/env python3
r"""S268 — genera 2 PDF dossier REALI dalla fixture committata (NO rete).

DoD #2/#3: i 2 PDF dimostrano la FASE 2 (banda-come-prodotto + intervallo
margine + pavimento onesto) su dato vero su disco, senza scrapare.

Pool: tests/fixtures/it_dist_bmw_serie3_2021.json (scrape AS24.it 2026-06-11,
campione CAP 20 pagine / 325 annunci -> N e' un PAVIMENTO, non un totale mercato).

Due veicoli, STESSA fixture, target_variant diverso:
  - 320d xDrive  -> verdetto-banda (N alto)
  - 330i         -> atteso NO_VERDICT (config esatta sotto-rappresentata sul cap)

NB prezzo_de = valore ILLUSTRATIVO (demo). Questi dossier dimostrano la
RESA del PDF, non sono il primo dossier a un dealer reale (DoD#4 = BLOCKED-ON
scrape esaustiva, vedi STATE.md). La BANDA IT e' dato reale dalla fixture;
il prezzo DE e' un input dimostrativo dichiarato.

Run:  python3 -m tools.scripts.build_s268_dossier
"""
from __future__ import annotations

import json
import os
import sys

# repo root su sys.path (per gli import di package quando lanciato come script)
_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

FIXTURE = os.path.join(_REPO, "tests", "fixtures", "it_dist_bmw_serie3_2021.json")
OUT_DIR = os.path.join(_REPO, "tests", "dossiers_s268")  # dossiers/ e' gitignored

# (tag, kwargs get_it_distribution, prezzo_de illustrativo)
VEHICLES = [
    dict(
        tag="320d_xDrive",
        prezzo_de=29500,
        gd=dict(
            make="BMW", model="Serie 3", year=2021, km=60_000, fuel="diesel",
            target_variant="320d xDrive", target_transmission="automatic",
            target_power_hp=190,
        ),
    ),
    dict(
        tag="330i",
        prezzo_de=31000,
        gd=dict(
            make="BMW", model="Serie 3", year=2021, km=45_000, fuel="petrol",
            target_variant="330i", target_transmission="automatic",
            target_power_hp=258,
        ),
    ),
]


def _preflight() -> None:
    try:
        import reportlab  # noqa: F401
    except Exception as e:  # pragma: no cover
        print(f"PRE-FLIGHT FAIL: reportlab non importabile ({e})", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(FIXTURE):
        print(f"PRE-FLIGHT FAIL: fixture assente {FIXTURE}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    _preflight()
    from tools.it_market_price import get_it_distribution
    from tools.margin_gate import evaluate_margin
    from tools.scripts.pdf_generator_enterprise import generate_dossier_from_data

    os.makedirs(OUT_DIR, exist_ok=True)
    paths = []
    for v in VEHICLES:
        dist = get_it_distribution(fixture_path=FIXTURE, **v["gd"])
        dist["is_floor"] = True  # campione cap -> N e' un PAVIMENTO (DELTA-2)

        prezzo_de = float(v["prezzo_de"])
        # _margin_* puntuali (sul mediano) — l'INTERVALLO lo calcola il generatore
        # dalla banda. Se NO_VERDICT, il gate non emette PASS/REJECT.
        margin = None
        if dist.get("median") is not None and not dist.get("no_verdict"):
            margin = evaluate_margin(prezzo_de, float(dist["median"]))

        veh = {
            "make": v["gd"]["make"], "model": v["gd"]["model"],
            "year": v["gd"]["year"], "km": v["gd"]["km"],
            "price_eur": int(prezzo_de),
            "fuel_type": v["gd"]["fuel"], "transmission": v["gd"]["target_transmission"],
            "_cove_confidence": 0.75,
            "_it_distribution": dist,
        }
        if dist.get("no_verdict"):
            veh["_margin_decision"] = "NO_VERDICT"
        elif margin is not None:
            veh.update(
                _margin_decision=margin.decision,
                _margin_chiavi_in_mano=margin.chiavi_in_mano,
                _margin_spread_lordo=margin.spread_lordo,
                _margin_dealer_floor=margin.dealer_floor_amount,
                _margin_surplus=margin.surplus,
                _margin_fee_argos=margin.fee_argos,
                _margin_netto_dealer=margin.margine_netto_dealer,
                _margin_netto_pct=margin.margine_netto_pct,
            )

        out_path = os.path.join(OUT_DIR, f"ARGOS_DEMO_S268_{v['tag']}.pdf")
        data_json = json.dumps({"vehicles": [veh]})
        result = generate_dossier_from_data(data_json, dealer_name="DEMO S268", output_path=out_path)
        paths.append(result)
        print(f"[{v['tag']}] N={dist.get('n')} L{dist.get('relaxation_level')} "
              f"no_verdict={dist.get('no_verdict')} conf={dist.get('confidence')} "
              f"band={dist.get('band_low')}-{dist.get('band_high')} -> {result}")

    print("\nDoD #2/#3 PDF generati:")
    for p in paths:
        ok = os.path.isfile(p) and os.path.getsize(p) > 0
        print(f"  {'OK ' if ok else 'MISSING '}{p} ({os.path.getsize(p) if ok else 0} byte)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
