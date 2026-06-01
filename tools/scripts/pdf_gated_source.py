"""pdf_gated_source.py — C-GATE-FONTE-001: rilascio PDF con fonte post-pagamento.

Unico punto di guard: la fonte (listing_url, seller, city, phone, portal) viene
inclusa nel PDF SOLO se current_state == 'payment_confirmed'.

Usage:
    from tools.scripts.pdf_gated_source import release_source_dossier
    path = release_source_dossier("DEAL-XXX", "/path/deals.sqlite", "/tmp/argos_gated")
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

# Assicura import dal repo root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.scripts.pdf_generator_enterprise import (
    ARGOSPDFGenerator,
    VehicleData,
    DealerInfo,
)

REQUIRED_STATE = "payment_confirmed"


class GatingError(RuntimeError):
    """Sollevata quando la fonte viene richiesta prima del pagamento."""


def release_source_dossier(
    deal_id: str,
    deals_db_path: str | Path,
    output_dir: str | Path,
) -> str:
    """Genera PDF con fonte rivelata per un deal in stato payment_confirmed.

    Args:
        deal_id: ID univoco del deal.
        deals_db_path: Path al DB SQLite deals (es. /tmp/s213-test-deals.sqlite).
        output_dir: Directory dove salvare il PDF. Creata se non esiste.

    Returns:
        Path assoluto del PDF generato.

    Raises:
        GatingError: se current_state != 'payment_confirmed'.
        ValueError: se deal_id non trovato o source_locked mancante/incompleto.
    """
    deals_db_path = Path(deals_db_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Legge deal da DB
    conn = sqlite3.connect(deals_db_path)
    try:
        cur = conn.execute(
            "SELECT current_state, metadata_json, dealer_alias, vehicle_desc, fee_eur "
            "FROM deals WHERE deal_id = ?",
            (deal_id,),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError(f"Deal '{deal_id}' non trovato in {deals_db_path}")

    current_state, metadata_json, dealer_alias, vehicle_desc, fee_eur = row

    # 2. GUARD — fonte non esce prima del pagamento
    if current_state != REQUIRED_STATE:
        raise GatingError(
            f"C-GATE-FONTE-001 BLOCKED: deal '{deal_id}' è in stato '{current_state}', "
            f"richiesto '{REQUIRED_STATE}'. Confermare il pagamento prima di rilasciare la fonte."
        )

    # 3. Estrae source_locked da metadata
    metadata = json.loads(metadata_json or "{}")
    source_locked = metadata.get("source_locked")
    if not source_locked:
        raise ValueError(
            f"Deal '{deal_id}': metadata source_locked assente. "
            "Il deal deve essere creato con create_deal() che imposta source_locked."
        )

    required_keys = {"listing_url", "seller_name", "seller_city", "seller_phone", "portal"}
    missing = required_keys - set(source_locked.keys())
    if missing:
        raise ValueError(f"source_locked incompleto, campi mancanti: {missing}")

    # 4. Costruisce VehicleData con fonte sbloccata
    # Parsa vehicle_desc "MARCA MODELLO ANNO KM PREZZO" (best-effort, dati reali nel PDF)
    parts = (vehicle_desc or "").split()
    make = parts[0] if len(parts) > 0 else "N/D"
    model = parts[1] if len(parts) > 1 else "N/D"
    try:
        year = int(parts[2]) if len(parts) > 2 else 2020
    except ValueError:
        year = 2020
    try:
        km = int(parts[3]) if len(parts) > 3 else 0
    except ValueError:
        km = 0
    try:
        price_eu = int(parts[4]) if len(parts) > 4 else fee_eur
    except ValueError:
        price_eu = fee_eur

    vehicle = VehicleData(
        make=make,
        model=model,
        year=year,
        km=km,
        price_eu=price_eu,
        price_it_estimate=int(price_eu * 1.12),
        confidence=0.85,
        source_url=source_locked["listing_url"],       # FONTE SBLOCCATA
        source_country=_city_to_country(source_locked["seller_city"]),
        portal=source_locked.get("portal", ""),
    )

    # 5. DealerInfo sintetico (dealer_alias è anonimo; il PDF gated è per Luke/archivio)
    dealer = DealerInfo(
        name=dealer_alias,
        company="ARGOS Automotive — Documento riservato founder",
        city="",
        contact_person="Luke",
    )

    # 6. Genera PDF con la fonte renderizzata in sezione dedicata.
    # source_dossier viene passato esplicitamente: è l'UNICO modo per far comparire
    # la fonte nel PDF (il generatore non la stampa altrimenti — C-GATE-FONTE-001).
    output_filename = f"GATED_{deal_id}_{current_state}.pdf"
    output_path = str(output_dir / output_filename)

    generator = ARGOSPDFGenerator()
    generated = generator.generate_vehicle_sheet(
        vehicle,
        dealer,
        output_path,
        grade_data=None,
        source_dossier=source_locked,
    )
    return os.path.abspath(generated or output_path)


def _city_to_country(city: str) -> str:
    """Best-effort mapping città → paese per source_country."""
    german_cities = {"munich", "münchen", "berlin", "hamburg", "frankfurt", "cologne", "köln",
                     "stuttgart", "düsseldorf", "dresden", "leipzig", "nuremberg", "nürnberg"}
    if city.lower() in german_cities:
        return "Germania"
    return "Europa"
