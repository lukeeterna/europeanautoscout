#!/usr/bin/env python3
"""
reapply_icp_filter.py — ZERO RETE. Ri-applica il filtro ICP corrente (incluso il
check OFFICIAL_NETWORK introdotto con l'esclusione dei concessionari di rete) ai
profili GIÀ su disco in data/pool_icp/dealer_*.json.

Non tocca la rete: `icp_verdict` è puro (legge stock_count/top_brands/company_name
dal profilo salvato). Aggiorna in-place il blocco `_icp` di ogni file e stampa una
tabella (seller_id · company_name · is_icp · reason).

Rule 1d: prima di scrivere fa un backup verificato dell'intera cartella pool_icp in
data/pool_icp/_backup_reapply_<ts>/ (path citato a stdout).

Uso: python3 tools/reapply_icp_filter.py
"""

import glob
import json
import os
import shutil
import sys
from datetime import datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from tools.profile_pool_icp import icp_verdict  # noqa: E402

POOL_DIR = os.path.join(_REPO_ROOT, "data", "pool_icp")


def _backup():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = os.path.join(POOL_DIR, f"_backup_reapply_{ts}")
    os.makedirs(dst, exist_ok=True)
    for p in glob.glob(os.path.join(POOL_DIR, "dealer_*.json")):
        shutil.copy2(p, dst)
    return dst


def main():
    paths = sorted(glob.glob(os.path.join(POOL_DIR, "dealer_*.json")))
    if not paths:
        print("Nessun dealer_*.json su disco.", file=sys.stderr)
        return 1

    bkp = _backup()
    print(f"[1d] backup profili → {bkp}\n")

    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            prof = json.load(f)
        is_icp, reason, tier_hits = icp_verdict(prof)
        prof["_icp"] = {"is_icp": is_icp, "reason": reason, "tier_hits": tier_hits}
        with open(p, "w", encoding="utf-8") as f:
            json.dump(prof, f, ensure_ascii=False, indent=2)
        rows.append((str(prof.get("seller_id")), prof.get("company_name"), is_icp, reason))

    w_id = max(len(r[0]) for r in rows)
    w_name = max(len(r[1] or "") for r in rows)
    print(f"{'seller_id':<{w_id}} │ {'company_name':<{w_name}} │ is_icp │ reason")
    print(f"{'-'*w_id}─┼─{'-'*w_name}─┼────────┼───────")
    for sid, name, is_icp, reason in rows:
        print(f"{sid:<{w_id}} │ {name or '':<{w_name}} │ {str(is_icp):<6} │ {reason}")

    kept = sum(1 for r in rows if r[2])
    print(f"\nICP-validi dopo re-apply: {kept}/{len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
