#!/usr/bin/env python3
"""
select_pilot_dealer.py — UNITÀ C-SELECT (BRIEF_A2): selezione riproducibile del
dealer pilota tra i profili ICP-validi. ZERO RETE.

Carica data/pool_icp/dealer_*.json (profili ICP-validi prodotti da UNITÀ B),
ordina per seller_id (ordine STABILE, deterministico), poi sceglie con
random.Random(SEED=42) → data/pool_icp/SELECTED.json.

Eseguito 2 volte = stesso dealer (riproducibilità provata: l'ordinamento stabile
+ seed fisso rendono la scelta deterministica).
"""

import glob
import json
import os
import random
import sys
from datetime import datetime, timezone

SEED = 42
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL_DIR = os.path.join(_REPO_ROOT, "data", "pool_icp")
SELECTED_OUT = os.path.join(POOL_DIR, "SELECTED.json")


def load_icp_profiles():
    """Carica i profili ICP-validi (dealer_<seller_id>.json), ordinati per seller_id."""
    paths = sorted(glob.glob(os.path.join(POOL_DIR, "dealer_*.json")))
    profiles = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            prof = json.load(f)
        profiles.append(prof)
    # ordine stabile per dealer_id (seller_id come stringa → chiave canonica)
    profiles.sort(key=lambda x: str(x.get("seller_id", "")))
    return profiles


def select(write: bool = True):
    profiles = load_icp_profiles()
    if not profiles:
        print("NESSUN profilo ICP-valido in data/pool_icp/dealer_*.json — C-SELECT non eseguibile.",
              file=sys.stderr)
        return None

    rng = random.Random(SEED)
    chosen = rng.choice(profiles)

    result = dict(chosen)
    result["selection_meta"] = {
        "pool_size": len(profiles),
        "seed": SEED,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pool_order_seller_ids": [str(p.get("seller_id")) for p in profiles],
    }

    if write:
        with open(SELECTED_OUT, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def main():
    result = select(write=True)
    if result is None:
        return 1
    print(f"SELECTED seller_id={result['seller_id']} · {result['company_name']} · "
          f"pool_size={result['selection_meta']['pool_size']} · seed={SEED}")
    print(f"Scritto: {SELECTED_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
