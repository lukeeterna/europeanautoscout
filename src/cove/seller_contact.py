"""
seller_contact.py — ARGOS Automated EU Seller Contact Module
CoVe 2026 | Enterprise Grade

Automatically contacts EU sellers (in English) via email to request:
  1. Missing vehicle photos (interior, rear, engine, etc.)
  2. Vehicle details not available on listing (VIN, service history, HU date)
  3. Current availability confirmation

BUSINESS RULES:
  - All communication in ENGLISH (EU dealers/sellers)
  - Professional tone, presents as vehicle sourcing company
  - Never reveals the Italian dealer client
  - Tracks contact status in DuckDB
  - Uses SMTP via Gmail (ferretti.argosautomotive@gmail.com)

Usage:
  from src.cove.seller_contact import request_missing_data

  result = request_missing_data(listing_id, db_path)
  # Returns: {"sent": True, "email": "...", "requested": ["photos", "vin", ...]}

CLI:
  python3 src/cove/seller_contact.py <listing_id>              # Send request
  python3 src/cove/seller_contact.py <listing_id> --dry-run    # Preview only
  python3 src/cove/seller_contact.py --check <listing_id>      # Check what's missing
"""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List

# ── Configuration ─────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Email config (from .env)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("ARGOS_EMAIL", "ferretti.argosautomotive@gmail.com")
SENDER_PASSWORD = os.getenv("ARGOS_EMAIL_PASSWORD", "")  # App password from .env
SENDER_NAME = "Luca Ferretti — ARGOS Automotive"

# What we need for a complete dossier
REQUIRED_DATA = {
    "vin": "Vehicle Identification Number (VIN)",
    "service_history": "Service history / maintenance records",
    "hu_date": "Last HU/TÜV inspection date and result",
    "previous_owners": "Number of previous owners",
    "accident_history": "Any accident or damage history",
}

REQUIRED_PHOTO_VIEWS = [
    ("front", "Front view (full vehicle)"),
    ("rear", "Rear view (full vehicle)"),
    ("side_left", "Left side view"),
    ("side_right", "Right side view"),
    ("interior_front", "Front interior / cockpit"),
    ("interior_rear", "Rear seats"),
    ("dashboard", "Dashboard / instrument cluster / mileage display"),
    ("engine", "Engine bay"),
    ("trunk", "Trunk / cargo area"),
    ("wheels", "Wheels / tires close-up"),
]

MIN_PHOTOS_COMPLETE = 6


def analyze_missing_data(listing_id: str, db_path: str = None) -> Dict:
    """
    Analyze what data/photos are missing for a complete dossier.

    Returns dict with:
      missing_data: list of (key, description) for missing vehicle data
      missing_photos: list of (view, description) for missing photo views
      seller_email: str or None (from listing detail page)
      seller_name: str or None
      photo_count: int
      data_completeness: dict of field -> bool
      needs_contact: bool
    """
    if db_path is None:
        db_path = str(PROJECT_ROOT / "src" / "cove" / "data" / "cove_tracker.duckdb")

    import duckdb
    db = duckdb.connect(db_path, read_only=True)

    # Get listing data
    listing = db.execute("""
        SELECT make, model, year, km, price, vin, source, market_price,
               confidence, fraud_overall, recommendation
        FROM cove_results WHERE listing_id = ?
    """, [listing_id]).fetchone()

    if not listing:
        db.close()
        return {"error": f"Listing {listing_id} not found"}

    make, model, year, km, price, vin, source, market_price, conf, fraud, rec = listing

    # Get vehicle_listings extended data (if exists)
    extended = {}
    try:
        ext_row = db.execute("""
            SELECT seller_name, seller_email, seller_phone, detail_url,
                   fuel_type, transmission, color, power_kw
            FROM vehicle_listings WHERE listing_id = ?
        """, [listing_id]).fetchone()
        if ext_row:
            keys = ['seller_name', 'seller_email', 'seller_phone', 'detail_url',
                    'fuel_type', 'transmission', 'color', 'power_kw']
            extended = {k: v for k, v in zip(keys, ext_row) if v}
    except Exception:
        pass

    # Get photo count
    photo_count = db.execute(
        "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?",
        [listing_id]
    ).fetchone()[0]

    db.close()

    # Determine what's missing
    missing_data = []
    data_status = {}
    for key, desc in REQUIRED_DATA.items():
        if key == "vin":
            has_it = bool(vin and len(str(vin)) >= 11)
        elif key == "service_history":
            has_it = False  # Never available from scraping
        elif key == "hu_date":
            has_it = False  # Rarely available
        elif key == "previous_owners":
            has_it = False  # Rarely in listing
        elif key == "accident_history":
            has_it = False  # Rarely disclosed in listing
        else:
            has_it = False

        data_status[key] = has_it
        if not has_it:
            missing_data.append((key, desc))

    # Determine missing photos (we just check count, not specific views)
    missing_photos = []
    if photo_count < MIN_PHOTOS_COMPLETE:
        for view, desc in REQUIRED_PHOTO_VIEWS:
            missing_photos.append((view, desc))

    needs_contact = len(missing_data) > 0 or len(missing_photos) > 0

    return {
        "listing_id": listing_id,
        "vehicle": f"{make} {model} {year}",
        "price": price,
        "km": km,
        "vin": vin,
        "source": source,
        "seller_name": extended.get("seller_name"),
        "seller_email": extended.get("seller_email"),
        "seller_phone": extended.get("seller_phone"),
        "detail_url": extended.get("detail_url"),
        "photo_count": photo_count,
        "missing_data": missing_data,
        "missing_photos": missing_photos,
        "data_completeness": data_status,
        "needs_contact": needs_contact,
    }


def compose_seller_email(analysis: Dict) -> Dict:
    """
    Compose a professional English email to the EU seller requesting
    missing photos and vehicle data.

    Returns dict with: subject, body, to_email, to_name
    """
    vehicle = analysis["vehicle"]
    km = analysis.get("km", 0)
    price = analysis.get("price", 0)

    # Subject
    subject = f"Inquiry: {vehicle} — Additional Photos & Information Request"

    # Build request sections
    photo_section = ""
    if analysis["missing_photos"]:
        photo_lines = []
        for view, desc in analysis["missing_photos"]:
            photo_lines.append(f"  • {desc}")
        photo_section = f"""
We would appreciate additional high-resolution photos of the vehicle, specifically:

{chr(10).join(photo_lines)}

These photos are essential for our client's evaluation process."""

    data_section = ""
    if analysis["missing_data"]:
        data_lines = []
        for key, desc in analysis["missing_data"]:
            data_lines.append(f"  • {desc}")
        data_section = f"""
We also kindly request the following information:

{chr(10).join(data_lines)}"""

    # Compose body
    body = f"""Dear {analysis.get('seller_name') or 'Sales Team'},

We are ARGOS Automotive, a vehicle sourcing company based in Europe. We are interested in the {vehicle}, {km:,} km, listed at EUR {price:,.0f}.

Before proceeding with a potential purchase on behalf of our client, we require some additional documentation to complete our evaluation.
{photo_section}
{data_section}

Please confirm the vehicle is still available and let us know if you can provide the above within the next 2-3 business days.

We handle all logistics including transport and registration. If terms are agreeable, we can proceed quickly.

Kind regards,

Luca Ferretti
Vehicle Sourcing — ARGOS Automotive
ferretti.argosautomotive@gmail.com
"""

    return {
        "subject": subject,
        "body": body.strip(),
        "to_email": analysis.get("seller_email"),
        "to_name": analysis.get("seller_name", "Sales Team"),
        "vehicle": vehicle,
    }


def send_seller_email(email_data: Dict, dry_run: bool = False) -> Dict:
    """
    Send the email to the EU seller via Gmail SMTP.

    Returns dict: sent, message_id, error
    """
    to_email = email_data.get("to_email")

    if not to_email:
        return {
            "sent": False,
            "error": "No seller email available — contact must be manual via portal messaging"
        }

    if dry_run:
        print(f"\n  ─── DRY RUN ───")
        print(f"  To: {email_data['to_name']} <{to_email}>")
        print(f"  Subject: {email_data['subject']}")
        print(f"  ────────────────────────────────────────")
        print(email_data['body'])
        print(f"  ─── END DRY RUN ───")
        return {"sent": False, "dry_run": True}

    if not SENDER_PASSWORD:
        return {
            "sent": False,
            "error": "ARGOS_EMAIL_PASSWORD not set in environment. Set Gmail app password in .env"
        }

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = f"{email_data['to_name']} <{to_email}>"
        msg['Subject'] = email_data['subject']
        msg.attach(MIMEText(email_data['body'], 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        return {
            "sent": True,
            "to": to_email,
            "subject": email_data['subject'],
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"sent": False, "error": str(e)}


def request_missing_data(listing_id: str, db_path: str = None, dry_run: bool = False) -> Dict:
    """
    Full pipeline: analyze → compose → send email to EU seller.

    Returns complete result dict.
    """
    print(f"\n  Analyzing listing {listing_id}...")
    analysis = analyze_missing_data(listing_id, db_path)

    if "error" in analysis:
        print(f"  ERROR: {analysis['error']}")
        return analysis

    print(f"  Vehicle: {analysis['vehicle']}")
    print(f"  Photos: {analysis['photo_count']} (min {MIN_PHOTOS_COMPLETE})")
    print(f"  Missing data: {len(analysis['missing_data'])} fields")
    print(f"  Missing photos: {'YES' if analysis['missing_photos'] else 'NO'}")
    print(f"  Seller: {analysis.get('seller_name', 'Unknown')}")
    print(f"  Seller email: {analysis.get('seller_email', 'Not available')}")

    if not analysis["needs_contact"]:
        print(f"\n  Listing is complete — no contact needed.")
        return {"listing_id": listing_id, "needs_contact": False, "complete": True}

    email_data = compose_seller_email(analysis)
    result = send_seller_email(email_data, dry_run=dry_run)

    return {
        "listing_id": listing_id,
        "analysis": analysis,
        "email": email_data,
        "send_result": result,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 src/cove/seller_contact.py <listing_id>           # Send request email")
        print("  python3 src/cove/seller_contact.py <listing_id> --dry-run # Preview email")
        print("  python3 src/cove/seller_contact.py --check <listing_id>   # Check what's missing")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv

    if sys.argv[1] == "--check" and len(sys.argv) >= 3:
        listing_id = sys.argv[2]
        analysis = analyze_missing_data(listing_id)
        if "error" in analysis:
            print(f"ERROR: {analysis['error']}")
            sys.exit(1)
        print(f"\n  === Data Completeness: {analysis['vehicle']} ===")
        print(f"  Photos: {analysis['photo_count']}")
        for key, has_it in analysis['data_completeness'].items():
            status = "OK" if has_it else "MISSING"
            print(f"  {key}: {status}")
        if analysis['missing_photos']:
            print(f"\n  Missing photo views ({len(analysis['missing_photos'])}):")
            for view, desc in analysis['missing_photos']:
                print(f"    - {desc}")
        print(f"\n  Needs seller contact: {'YES' if analysis['needs_contact'] else 'NO'}")
    else:
        listing_id = sys.argv[1] if sys.argv[1] != "--dry-run" else sys.argv[2]
        result = request_missing_data(listing_id, dry_run=dry_run)
        if result.get("send_result", {}).get("sent"):
            print(f"\n  Email sent to {result['send_result']['to']}")
        elif result.get("send_result", {}).get("dry_run"):
            print(f"\n  Dry run complete — review email above")
        elif result.get("complete"):
            print(f"\n  No action needed — listing is complete")
        else:
            error = result.get("send_result", {}).get("error", "Unknown error")
            print(f"\n  Not sent: {error}")
