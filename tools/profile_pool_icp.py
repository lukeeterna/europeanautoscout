#!/usr/bin/env python3
"""
profile_pool_icp.py — UNITÀ B (BRIEF_A2): profiling dei candidati pool ICP.

Legge data/pool_icp/_candidates.json (45 candidati con info_page), profila ogni
dealer via dealer_profile.aggregate_profile riusando lo SCRAPER VERIFICATO
(AutoScoutScraper, istanza CONDIVISA → il rate-limit interno + il contatore
richieste accumulano realmente tra candidati). Limiti scraper IMMUTABILI: NON
toccati (sleep/rate/daily_cap restano quelli di config.py).

Filtro ICP (per profilo, arbitro = numberOfResults, MAI len()):
  stock_count < 20  ∧  top_brands interseca TIER A/B  ∧  (BEV non decidibile a
  livello dealer → gestito a discovery: fuel D,G; qui NON inventato).
Campo assente = null → il vincolo che vi si appoggia NON è soddisfatto (mai stimato).

STOP appena 10 profili ICP-validi (o candidati esauriti, o guard 80% del cap).

Output:
  - data/pool_icp/dealer_<seller_id>.json  per OGNI profilo ICP-valido
  - data/pool_icp/_profiling_run.json       riepilogo run (contatore, shortlist)
  - stdout: log per-candidato + shortlist finale
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "scrapers"))
sys.path.insert(0, _REPO_ROOT)

from tools.dealer_profile import aggregate_profile  # noqa: E402
from tools.scrapers.autoscout_scraper import AutoScoutScraper  # noqa: E402

POOL_DIR = os.path.join(_REPO_ROOT, "data", "pool_icp")
CANDIDATES = os.path.join(POOL_DIR, "_candidates.json")
RUN_OUT = os.path.join(POOL_DIR, "_profiling_run.json")

TARGET_ICP = 10
# TIER A/B: keyword lowercase, match per substring sul brand normalizzato
# (AS24 espone "Mercedes-Benz", "Land Rover" ecc.). Lista chiusa, no fuzzy.
TIER_AB = ["porsche", "audi", "bmw", "mercedes", "land rover", "range rover"]

# Concessionari UFFICIALI di rete (filiali brand) — NON target ARGOS, che cerca
# family-business INDIPENDENTI/multimarca. Lista CHIUSA di pattern (label, regex),
# word-boundary, case-insensitive. Un match sul company_name => is_icp:false con
# reason NOMINATA ("OFFICIAL_NETWORK:<label>"), mai esclusione silenziosa.
OFFICIAL_NETWORK_PATTERNS = [
    ("Centro Porsche",              r"\bcentro\s+porsche\b"),
    ("Porsche Zentrum",             r"\bporsche\s+zentrum\b"),
    ("Centro BMW",                  r"\bcentro\s+bmw\b"),
    ("BMW <City>",                  r"\bbmw\s+\w+\b"),
    ("Mercedes-Benz <City>",        r"\bmercedes[-\s]benz\s+\w+\b"),
    ("Audi Zentrum",                r"\baudi\s+zentrum\b"),
    ("Centro Audi",                 r"\bcentro\s+audi\b"),
    ("Land Rover <City> ufficiale", r"\bland\s+rover\s+\w+\s+ufficiale\b"),
    ("concessionaria ufficiale",    r"\bconcessionari[ao]\s+ufficiale\b"),
]


def official_network_match(company_name):
    """Ritorna il LABEL del primo pattern di rete ufficiale che matcha
    company_name, altrimenti None. Word-boundary, case-insensitive, lista chiusa
    (no fuzzy). company_name None/"" → None."""
    if not company_name:
        return None
    for label, pat in OFFICIAL_NETWORK_PATTERNS:
        if re.search(pat, company_name, re.IGNORECASE):
            return label
    return None


def is_tier_ab(top_brands):
    """True se ALMENO un brand del profilo è TIER A/B. top_brands None/[] → False."""
    if not top_brands:
        return False
    hits = []
    for b in top_brands:
        bl = b.strip().lower()
        for kw in TIER_AB:
            if kw in bl:
                hits.append(b.strip())
                break
    return hits  # lista (truthy se non vuota) → riusabile come prova


def icp_verdict(profile):
    """Ritorna (is_icp: bool, reason: str, tier_hits: list)."""
    tier_hits = is_tier_ab(profile.get("top_brands")) or []

    # Hard-exclude PRIORITARIO: concessionario ufficiale di rete → mai ICP,
    # indipendentemente da stock/tier. Motivazione nominata.
    onet = official_network_match(profile.get("company_name"))
    if onet:
        return False, f"OFFICIAL_NETWORK:{onet}", tier_hits

    stock = profile.get("stock_count")

    reasons = []
    if stock is None:
        reasons.append("stock_count=null (numberOfResults assente, non stimabile)")
    elif stock >= 20:
        reasons.append(f"stock={stock} >= 20")
    if not tier_hits:
        reasons.append("nessun brand TIER A/B in top_brands")

    is_icp = (stock is not None and stock < 20) and bool(tier_hits)
    reason = "ICP-VALID" if is_icp else "; ".join(reasons)
    return is_icp, reason, tier_hits


def main():
    with open(CANDIDATES, encoding="utf-8") as f:
        pool = json.load(f)

    candidates = pool["candidates"]
    daily_cap = pool.get("daily_cap", 2000)
    guard_80 = pool.get("guard_80pct", int(daily_cap * 0.8))
    baseline_used = pool.get("requests_used", 0)

    scraper = AutoScoutScraper("autoscout24_it")
    # sanity: il cap effettivo dello scraper deve coincidere col brief (2000)
    eff_cap = scraper.config.daily_request_cap
    print(f"[cfg] daily_request_cap effettivo={eff_cap} · guard_80%={guard_80} · "
          f"baseline_requests_used={baseline_used} · rate={scraper.config.rate_limit_min_s}-"
          f"{scraper.config.rate_limit_max_s}s", flush=True)

    icp_profiles = []   # (candidate, profile, tier_hits)
    profiled = 0
    stopped_reason = None

    for i, cand in enumerate(candidates, 1):
        session_reqs = scraper.request_count
        total_reqs = baseline_used + session_reqs
        # guard 80%: fermati PRIMA di superare la soglia
        if total_reqs >= guard_80:
            stopped_reason = f"GUARD_80PCT ({total_reqs}>={guard_80})"
            break

        url = cand["info_page"]
        sid = cand["seller_id"]
        cname = cand.get("company_name", "?")
        try:
            html = scraper._fetch(url)  # rate-limit INTERNO (immutabile); vuoto su 404
            if not html:
                print(f"[{i}/{len(candidates)}] SKIP fetch-vuoto/404 · {cname} · {url}", flush=True)
                profiled += 1
                continue
            scraper.get_total_pages(html)  # popola _last_declared_results
            declared = getattr(scraper, "_last_declared_results", None)
            listings = scraper.parse_listings(html, country="IT", make="", model="")
            profile = aggregate_profile(listings, declared, url=url)
        except Exception as exc:  # noqa: BLE001 — fetch/parse fail su un candidato non abortisce il run
            print(f"[{i}/{len(candidates)}] ERRORE {type(exc).__name__}: {exc} · {cname}", flush=True)
            profiled += 1
            continue

        profiled += 1
        # arricchisce il profilo con identità stabile del candidato (dealer_id per C-select)
        # PRIMA del verdetto: icp_verdict legge company_name per il check OFFICIAL_NETWORK.
        profile["seller_id"] = sid
        profile["company_name"] = cname
        profile["phones"] = cand.get("phones")
        is_icp, reason, tier_hits = icp_verdict(profile)
        profile["_icp"] = {"is_icp": is_icp, "reason": reason, "tier_hits": tier_hits}

        tag = "✅ICP" if is_icp else "  ──"
        print(f"[{i}/{len(candidates)}] {tag} · {cname} · stock={profile.get('stock_count')} · "
              f"brands={profile.get('top_brands')} · {reason}", flush=True)

        if is_icp:
            out_path = os.path.join(POOL_DIR, f"dealer_{sid}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            icp_profiles.append(profile)
            if len(icp_profiles) >= TARGET_ICP:
                stopped_reason = f"TARGET_ICP reached ({TARGET_ICP})"
                break

    if stopped_reason is None:
        stopped_reason = "CANDIDATES_EXHAUSTED"

    session_reqs = scraper.request_count
    total_reqs = baseline_used + session_reqs

    shortlist = [{
        "seller_id": p["seller_id"],
        "company_name": p["company_name"],
        "stock_count": p["stock_count"],
        "top_brands": p["top_brands"],
        "location": p["location"],
        "source_url": p["source_url"],
    } for p in icp_profiles]

    run = {
        "generated_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidates_total": len(candidates),
        "profiled": profiled,
        "icp_valid": len(icp_profiles),
        "stopped_reason": stopped_reason,
        "requests_session": session_reqs,
        "requests_total_with_baseline": total_reqs,
        "baseline_requests_used": baseline_used,
        "daily_cap": eff_cap,
        "guard_80pct": guard_80,
        "shortlist": shortlist,
    }
    with open(RUN_OUT, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=2)

    print("\n=== RUN SUMMARY ===", flush=True)
    print(json.dumps(run, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
