#!/usr/bin/env python3
"""
ARGOS™ Batch Runner — Pipeline notturna / batch interattiva
CoVe 2026 | Enterprise Grade | Zero Costi

Esegue la pipeline completa per N modelli su tutti i portali:
  Scraper (FAST o ALL) → Dedup → CoVe → Opportunity Score → PDF Dossier

Modalita':
  FAST:  16 portali veloci, < 3 min per modello (demo interattive)
  ALL:   73 portali, < 30 min per modello (batch notturni su iMac)

Uso:
  # Singolo modello, fast
  python3 tools/batch_runner.py BMW X3

  # Multi modello, fast, con PDF per Autovanny
  python3 tools/batch_runner.py BMW X3 BMW X5 Mercedes GLC Audi Q5 Porsche Macan \\
      --dealer "Giovanni Vannicola" --company "Autovanny Group" --city Eboli

  # Batch notturno, tutti i portali
  python3 tools/batch_runner.py --all-vehicles --mode all --top 3

  # PM2 cron su iMac (03:00 ogni notte)
  pm2 start tools/batch_runner.py --name argos-batch --cron "0 3 * * *" -- \\
      --all-vehicles --mode all --top 3 --dealer "Giovanni Vannicola" \\
      --company "Autovanny Group" --city Eboli

Author: ARGOS CTO Stack
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Path setup
_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("argos.batch")


# ---------------------------------------------------------------------------
# Portal sets — FAST (demo) vs ALL (batch notturno)
# ---------------------------------------------------------------------------
# WAF-blocked portals: skip always (Akamai/DPG Media hard blocks)
WAF_BLOCKED = {
    # mobile_de: S72 FIX — bypassato via Google Translate proxy
    "autotrack_nl",    # DPG Media WAF — 403 + "Access Denied"
    "leboncoin_fr",    # DataDome — intermittent blocks
}

# FAST: portali che rispondono in < 5s senza WAF issues
FAST_PORTALS = [
    # DE (7 portali, AutoScout24 + mobile.de lead)
    "autoscout24_de", "mobile_de", "kleinanzeigen_de", "pkw_de", "auto_de",
    "caronsale_de", "autobid_de",
    # NL/BE/AT
    "autoscout24_nl", "marktplaats_nl", "autoscout24_be",
    "autoscout24_at", "willhaben_at",
    # FR/SE
    "autoscout24_fr", "autoscout24_se",
    # Nordic
    "finn_no", "bilbasen_dk",
    # IT (reference pricing)
    "autoscout24_it",
]

# Error tracking per portal (skip after 3 consecutive failures)
_error_counts: Dict[str, int] = {}
_ERROR_THRESHOLD = 3

# Results cache directory
RESULTS_DIR = _PROJECT_ROOT / "data" / "batch_results"


def _get_all_portals() -> List[str]:
    """Tutti i portali tranne WAF-blocked."""
    from tools.scrapers.config import PORTALS
    return [k for k in PORTALS.keys() if k not in WAF_BLOCKED]


def _should_skip(portal_key: str) -> bool:
    """Skip se WAF-blocked o > 3 errori consecutivi."""
    if portal_key in WAF_BLOCKED:
        return True
    return _error_counts.get(portal_key, 0) >= _ERROR_THRESHOLD


def run_pipeline(
    make: str,
    model: str,
    mode: str = "fast",
    max_pages: int = 1,
    min_discount_pct: float = 0.08,
    top_n: int = 5,
    save_results: bool = True,
) -> Tuple[list, dict]:
    """
    Esegue pipeline completa per un singolo modello.

    Args:
        make, model: Veicolo target
        mode: "fast" (16 portali) o "all" (73 portali)
        max_pages: Pagine per portale
        min_discount_pct: Sconto minimo per filtrare
        top_n: Top N opportunita' da restituire
        save_results: Salva JSON su disco

    Returns:
        (opportunities, stats)
    """
    from src.cove.scraper_cove_pipeline import ScraperCovePipeline

    portals = FAST_PORTALS if mode == "fast" else _get_all_portals()
    # Filter out portals with too many errors
    portals = [p for p in portals if not _should_skip(p)]

    logger.info(
        "=== %s %s | mode=%s | %d portali | max_pages=%d ===",
        make, model, mode, len(portals), max_pages,
    )

    start = time.time()
    pipeline = ScraperCovePipeline()

    opportunities = pipeline.run(
        make=make,
        model=model,
        portals=portals,
        max_pages=max_pages,
        min_discount_pct=min_discount_pct,
    )

    elapsed = time.time() - start

    stats = {
        "make": make,
        "model": model,
        "mode": mode,
        "portals_attempted": len(portals),
        "total_opportunities": len(opportunities),
        "top_score": opportunities[0].opportunity_score if opportunities else 0,
        "top_margin": opportunities[0].estimated_margin_eur if opportunities else 0,
        "elapsed_sec": round(elapsed, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        ">>> %s %s: %d opportunita' in %.0fs (top score: %d, top margin: EUR %+d)",
        make, model, len(opportunities), elapsed,
        stats["top_score"], int(stats["top_margin"]),
    )

    # Save results
    if save_results and opportunities:
        _save_results(make, model, opportunities, stats)

    # Return top N
    return opportunities[:top_n], stats


def _save_results(make: str, model: str, opportunities: list, stats: dict) -> Path:
    """Salva risultati batch in JSON persistente."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{date_str}_{make}_{model}.json"
    filepath = RESULTS_DIR / filename

    data = {
        "stats": stats,
        "opportunities": [o.to_dict() for o in opportunities],
    }

    filepath.write_text(json.dumps(data, indent=2, default=str))
    logger.info("Risultati salvati: %s (%d opp)", filepath, len(opportunities))
    return filepath


def run_batch(
    vehicles: List[Tuple[str, str]],
    mode: str = "fast",
    max_pages: int = 1,
    top_n: int = 5,
    dealer_name: str = "",
    dealer_company: str = "",
    dealer_city: str = "Eboli",
    generate_pdf: bool = True,
    combined_pdf: bool = True,
) -> Dict:
    """
    Esegue batch su multipli veicoli con opzionale generazione PDF.

    Args:
        vehicles: Lista di (make, model)
        mode: "fast" o "all"
        max_pages: Pagine per portale
        top_n: Top N per modello
        dealer_*: Info dealer per PDF
        generate_pdf: Genera singoli PDF
        combined_pdf: Genera dossier combinato

    Returns:
        Dizionario con risultati e paths PDF
    """
    batch_start = time.time()
    all_opportunities = []
    all_stats = []

    logger.info(
        "━━━ ARGOS BATCH: %d modelli, mode=%s ━━━",
        len(vehicles), mode,
    )

    for make, model in vehicles:
        try:
            opps, stats = run_pipeline(
                make=make, model=model, mode=mode,
                max_pages=max_pages, top_n=top_n,
            )
            all_opportunities.extend(opps)
            all_stats.append(stats)
        except Exception as e:
            logger.error("ERRORE %s %s: %s", make, model, e)
            all_stats.append({
                "make": make, "model": model, "error": str(e),
                "total_opportunities": 0,
            })

    # Sort all opportunities by score
    all_opportunities.sort(key=lambda o: o.opportunity_score, reverse=True)

    batch_elapsed = time.time() - batch_start
    total_opps = sum(s.get("total_opportunities", 0) for s in all_stats)

    logger.info(
        "━━━ BATCH COMPLETATO: %d modelli, %d opp totali, %.0fs ━━━",
        len(vehicles), total_opps, batch_elapsed,
    )

    result = {
        "vehicles": len(vehicles),
        "total_opportunities": total_opps,
        "top_opportunities": len(all_opportunities),
        "elapsed_sec": round(batch_elapsed, 1),
        "stats": all_stats,
        "pdf_paths": [],
        "combined_pdf_path": None,
    }

    # Generate PDFs
    if generate_pdf and all_opportunities and dealer_name:
        try:
            from tools.scripts.pdf_generator_enterprise import (
                generate_opportunity_dossier,
            )
            output_dir = f"/tmp/argos_dossier/{datetime.now().strftime('%Y%m%d')}"
            pdf_paths = generate_opportunity_dossier(
                opportunities=all_opportunities,
                dealer_name=dealer_name,
                dealer_company=dealer_company,
                dealer_city=dealer_city,
                output_dir=output_dir,
                download_images=True,
                watermark=True,
            )
            result["pdf_paths"] = pdf_paths
            logger.info("PDF generati: %d singoli in %s", len(pdf_paths), output_dir)
        except Exception as e:
            logger.error("Errore generazione PDF singoli: %s", e)

    # Generate combined dossier
    if combined_pdf and all_opportunities and dealer_name:
        try:
            from tools.scripts.pdf_generator_enterprise import (
                generate_combined_dossier,
            )
            output_dir = f"/tmp/argos_dossier/{datetime.now().strftime('%Y%m%d')}"
            combined_path = generate_combined_dossier(
                opportunities=all_opportunities,
                dealer_name=dealer_name,
                dealer_company=dealer_company,
                dealer_city=dealer_city,
                output_dir=output_dir,
                max_per_model=top_n,
            )
            result["combined_pdf_path"] = combined_path
            logger.info("Dossier combinato: %s", combined_path)
        except Exception as e:
            logger.error("Errore dossier combinato: %s", e)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="ARGOS™ Batch Runner — Pipeline E2E per dealer delivery"
    )
    parser.add_argument(
        "vehicles", nargs="*",
        help="Coppie make model (es: BMW X3 Porsche Macan)"
    )
    parser.add_argument("--mode", choices=["fast", "all"], default="fast",
                        help="fast=16 portali, all=73 portali")
    parser.add_argument("--pages", type=int, default=1,
                        help="Max pagine per portale")
    parser.add_argument("--top", type=int, default=5,
                        help="Top N opportunita' per modello")
    parser.add_argument("--discount", type=float, default=0.08,
                        help="Min discount %% (default 8%%)")
    parser.add_argument("--all-vehicles", action="store_true",
                        help="Usa tutti i TARGET_VEHICLES da config")
    parser.add_argument("--dealer", type=str, default="",
                        help="Nome dealer per PDF")
    parser.add_argument("--company", type=str, default="",
                        help="Azienda dealer per PDF")
    parser.add_argument("--city", type=str, default="Eboli",
                        help="Citta' dealer per trasporto/import")
    parser.add_argument("--no-pdf", action="store_true",
                        help="Skip generazione PDF")
    parser.add_argument("--no-combined", action="store_true",
                        help="Skip dossier combinato")
    args = parser.parse_args()

    # Parse vehicles
    vehicles: List[Tuple[str, str]] = []

    if args.all_vehicles:
        from tools.scrapers.config import TARGET_VEHICLES
        for make, models in TARGET_VEHICLES.items():
            for model in models:
                vehicles.append((make, model))
    elif args.vehicles:
        if len(args.vehicles) % 2 != 0:
            parser.error("Veicoli devono essere in coppie make model")
        for i in range(0, len(args.vehicles), 2):
            vehicles.append((args.vehicles[i], args.vehicles[i + 1]))
    else:
        parser.error("Specifica veicoli o usa --all-vehicles")

    result = run_batch(
        vehicles=vehicles,
        mode=args.mode,
        max_pages=args.pages,
        top_n=args.top,
        dealer_name=args.dealer,
        dealer_company=args.company,
        dealer_city=args.city,
        generate_pdf=not args.no_pdf and bool(args.dealer),
        combined_pdf=not args.no_combined and bool(args.dealer),
    )

    # Summary
    print(f"\n{'='*70}")
    print(f"ARGOS BATCH RUNNER — RISULTATI")
    print(f"{'='*70}")
    print(f"Modelli:      {result['vehicles']}")
    print(f"Opportunita': {result['total_opportunities']}")
    print(f"Tempo:        {result['elapsed_sec']}s")

    if result["pdf_paths"]:
        print(f"PDF singoli:  {len(result['pdf_paths'])}")
    if result["combined_pdf_path"]:
        print(f"Dossier:      {result['combined_pdf_path']}")

    print(f"\nDettaglio per modello:")
    for s in result["stats"]:
        if "error" in s:
            print(f"  {s['make']} {s['model']}: ERRORE — {s['error']}")
        else:
            print(
                f"  {s['make']} {s['model']}: {s['total_opportunities']} opp | "
                f"top score {s.get('top_score', 0)} | "
                f"top margin EUR {s.get('top_margin', 0):+,.0f} | "
                f"{s.get('elapsed_sec', 0):.0f}s"
            )


if __name__ == "__main__":
    main()
