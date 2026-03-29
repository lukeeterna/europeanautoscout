"""
ARGOS Automotive — Dossier Quality Standard
CoVe 2026 | Enterprise Grade

Defines the minimum requirements for a dealer-ready dossier.
A listing that does not meet ALL mandatory criteria CANNOT be sent to a dealer.

Usage:
    from src.cove.dossier_standard import check_dossier_readiness

    result = check_dossier_readiness(listing_id)
    # Returns: {"ready": False, "missing": [...], "score": 65, ...}
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class ReadinessLevel(Enum):
    """Dossier readiness levels."""
    NOT_READY = "NOT_READY"       # Missing mandatory items — cannot send
    DRAFT = "DRAFT"               # Has basics but missing photos/data
    REVIEW = "REVIEW"             # Almost ready, needs human review
    DEALER_READY = "DEALER_READY" # Complete — can be sent to dealer


# ── DOSSIER STANDARD ─────────────────────────────────────────────────────────

# Mandatory: if ANY of these is missing, dossier is NOT_READY
MANDATORY = {
    "make_model_year": "Marca, modello e anno verificati",
    "price_eu": "Prezzo EU verificato e attuale",
    "mileage": "Chilometraggio dall'annuncio",
    "min_photos": "Almeno 8 foto HD (6 ext + 2 int minimo)",
    "argos_grade": "ARGOS Grade calcolato (A-E)",
    "margin_positive": "Margine netto dealer >= €2,000",
    "no_fraud_flags": "Zero fraud flag attivi",
}

# Important: dossier can go out as DRAFT without these, but not DEALER_READY
IMPORTANT = {
    "vin_verified": "VIN verificato con NHTSA/freevindecoder",
    "seller_confirmed_available": "Venditore ha confermato disponibilita'",
    "service_history": "Storico tagliandi (almeno ultimo tagliando)",
    "interior_photos": "Foto interni (almeno 3: abitacolo, cruscotto, bagagliaio)",
    "hu_date": "Data ultima revisione HU/TUV",
    "accident_free": "Conferma assenza incidenti dal venditore",
    "previous_owners": "Numero proprietari precedenti",
}

# Nice to have: improve dossier quality but not blocking
OPTIONAL = {
    "underbody_photos": "Foto sottoscocca",
    "tire_condition": "Condizione pneumatici (marca, DOT, battistrada)",
    "equipment_list": "Lista optional completa",
    "num_keys": "Numero chiavi",
    "next_service_due": "Prossimo tagliando previsto",
    "transport_quote": "Preventivo trasporto reale (non stima)",
}

# Photo requirements
MIN_PHOTOS_MANDATORY = 8
MIN_PHOTOS_DEALER_READY = 12
PHOTO_VIEWS_MANDATORY = [
    "front", "rear", "side_left", "side_right",      # 4 exterior
    "front_three_quarter", "rear_three_quarter",       # 2 exterior
    "interior_front", "dashboard",                     # 2 interior minimum
]
PHOTO_VIEWS_DEALER_READY = PHOTO_VIEWS_MANDATORY + [
    "interior_rear", "trunk", "engine", "wheels_front", # +4
]

# Margin requirements
MIN_MARGIN_EUR = 2000  # Minimum net margin for dossier to be worth sending
MIN_MARGIN_IDEAL = 3000  # Ideal margin — prioritize these


@dataclass
class DossierReadiness:
    """Result of dossier readiness check."""
    listing_id: str
    level: ReadinessLevel
    score: int  # 0-100
    ready: bool
    missing_mandatory: List[str] = field(default_factory=list)
    missing_important: List[str] = field(default_factory=list)
    missing_optional: List[str] = field(default_factory=list)
    photo_count: int = 0
    margin_net: int = 0
    next_action: str = ""
    details: Dict = field(default_factory=dict)


def check_dossier_readiness(
    listing_id: str,
    db_path: str = None,
) -> DossierReadiness:
    """
    Check if a listing meets the dossier standard for dealer delivery.

    Returns DossierReadiness with level, missing items, and next action.
    """
    import duckdb
    import os
    from pathlib import Path

    if db_path is None:
        db_path = str(Path(__file__).parent / "data" / "cove_tracker.duckdb")

    con = duckdb.connect(db_path, read_only=True)

    # Fetch all data
    cr = con.execute("""
        SELECT make, model, year, km, price, market_price,
               recommendation, confidence, fraud_overall, vin
        FROM cove_results WHERE listing_id = ?
    """, [listing_id]).fetchone()

    if not cr:
        con.close()
        return DossierReadiness(
            listing_id=listing_id,
            level=ReadinessLevel.NOT_READY,
            score=0, ready=False,
            missing_mandatory=["Listing non trovato in cove_results"],
            next_action="Eseguire scoring CoVe prima",
        )

    make, model, year, km, price, market_price, rec, conf, fraud, vin = cr

    # Vehicle listings data
    vl = con.execute("""
        SELECT vin_verified, seller_name, seller_email,
               seller_contact_sent_at, seller_followup_count
        FROM vehicle_listings WHERE listing_id = ?
    """, [listing_id]).fetchone()

    vin_verified = bool(vl[0]) if vl else False
    seller_email = vl[2] if vl else None
    seller_contacted = bool(vl[3]) if vl else False

    # Photo count
    photo_count = con.execute(
        "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?",
        [listing_id]
    ).fetchone()[0]

    con.close()

    # Calculate margin
    market_it = int((market_price or 0) * 1.12)
    transport = 600
    immatricolazione = 430
    argos_fee = 900
    margin_net = market_it - int(price or 0) - transport - immatricolazione - argos_fee

    # Check mandatory
    missing_mandatory = []
    if not (make and model and year):
        missing_mandatory.append("make_model_year")
    if not price or price <= 0:
        missing_mandatory.append("price_eu")
    if not km or km <= 0:
        missing_mandatory.append("mileage")
    if photo_count < MIN_PHOTOS_MANDATORY:
        missing_mandatory.append(f"min_photos (have {photo_count}, need {MIN_PHOTOS_MANDATORY})")
    if not conf or conf <= 0:
        missing_mandatory.append("argos_grade")
    if margin_net < MIN_MARGIN_EUR:
        missing_mandatory.append(f"margin_positive (€{margin_net} < €{MIN_MARGIN_EUR})")
    if fraud and str(fraud).upper() not in ("CLEAN", "LOW", ""):
        missing_mandatory.append(f"no_fraud_flags ({fraud})")

    # Check important
    missing_important = []
    if not vin_verified:
        missing_important.append("vin_verified")
    if not seller_contacted:
        missing_important.append("seller_confirmed_available")
    missing_important.append("service_history")  # Never available from scraping
    if photo_count < 5:
        missing_important.append("interior_photos")
    missing_important.append("hu_date")
    missing_important.append("accident_free")
    missing_important.append("previous_owners")

    # Check optional
    missing_optional = list(OPTIONAL.keys())

    # Calculate score
    total_checks = len(MANDATORY) + len(IMPORTANT) + len(OPTIONAL)
    passed = total_checks - len(missing_mandatory) - len(missing_important) - len(missing_optional)
    # Weight: mandatory=3x, important=2x, optional=1x
    max_score = len(MANDATORY) * 3 + len(IMPORTANT) * 2 + len(OPTIONAL)
    actual_score = (len(MANDATORY) - len(missing_mandatory)) * 3 + \
                   (len(IMPORTANT) - len(missing_important)) * 2 + \
                   (len(OPTIONAL) - len(missing_optional))
    score = int(actual_score / max_score * 100) if max_score > 0 else 0

    # Determine level
    if missing_mandatory:
        level = ReadinessLevel.NOT_READY
    elif len(missing_important) <= 2:
        level = ReadinessLevel.DEALER_READY
    elif len(missing_important) <= 5:
        level = ReadinessLevel.REVIEW
    else:
        level = ReadinessLevel.DRAFT

    # Determine next action
    if "min_photos" in str(missing_mandatory):
        next_action = f"Richiedere foto HD al venditore EU ({photo_count}/{MIN_PHOTOS_MANDATORY})"
    elif missing_mandatory:
        next_action = f"Risolvere: {missing_mandatory[0]}"
    elif not seller_contacted:
        next_action = "Contattare venditore EU per conferma disponibilita' e foto"
    elif not vin_verified and vin:
        next_action = "Eseguire VIN verification"
    elif missing_important:
        next_action = f"Ottenere: {IMPORTANT.get(missing_important[0], missing_important[0])}"
    else:
        next_action = "Dossier pronto — generare PDF e inviare al dealer"

    return DossierReadiness(
        listing_id=listing_id,
        level=level,
        score=score,
        ready=(level == ReadinessLevel.DEALER_READY),
        missing_mandatory=missing_mandatory,
        missing_important=missing_important,
        missing_optional=missing_optional,
        photo_count=photo_count,
        margin_net=margin_net,
        next_action=next_action,
        details={
            "make": make, "model": model, "year": year,
            "km": km, "price_eu": int(price or 0),
            "market_it": market_it, "margin_net": margin_net,
            "vin": vin, "vin_verified": vin_verified,
            "seller_email": seller_email,
            "seller_contacted": seller_contacted,
            "recommendation": rec,
        },
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 src/cove/dossier_standard.py <listing_id>")
        sys.exit(1)

    listing_id = sys.argv[1]
    result = check_dossier_readiness(listing_id)

    print(f"\n{'='*60}")
    print(f"DOSSIER READINESS: {result.details.get('make','')} {result.details.get('model','')} {result.details.get('year','')}")
    print(f"{'='*60}")
    print(f"Level:    {result.level.value}")
    print(f"Score:    {result.score}/100")
    print(f"Ready:    {'SI' if result.ready else 'NO'}")
    print(f"Photos:   {result.photo_count}/{MIN_PHOTOS_MANDATORY} min")
    print(f"Margin:   €{result.margin_net:,}")
    print(f"")

    if result.missing_mandatory:
        print(f"BLOCCANTI ({len(result.missing_mandatory)}):")
        for m in result.missing_mandatory:
            desc = MANDATORY.get(m, m)
            print(f"  ✗ {desc}")

    if result.missing_important:
        print(f"\nIMPORTANTI ({len(result.missing_important)}):")
        for m in result.missing_important:
            desc = IMPORTANT.get(m, m)
            print(f"  △ {desc}")

    print(f"\n→ NEXT: {result.next_action}")
