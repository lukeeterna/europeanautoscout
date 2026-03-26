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

# What we need for a complete dossier — every field the Italian dealer expects
REQUIRED_DATA = {
    # Critical (deal-breaker if missing)
    "vin": "Vehicle Identification Number (VIN)",
    "service_history": "Complete service history / maintenance booklet (digital or scanned pages)",
    "hu_date": "Last HU/TÜV inspection date, result, and expiry",
    "previous_owners": "Number of previous owners",
    "accident_history": "Full accident and damage history (including minor repairs)",
    # Important (affects pricing and dealer decision)
    "equipment_list": "Complete equipment/options list (factory and aftermarket)",
    "num_keys": "Number of keys provided",
    "next_service_due": "Next scheduled service date and type",
    "outstanding_finance": "Confirmation vehicle is free of liens/financing",
    "interior_color_material": "Interior color and material (leather/cloth/alcantara)",
    "tire_type_condition": "Tire type (summer/winter/all-season), brand, DOT date, tread depth",
    "available_from": "Earliest collection/shipping date",
}

REQUIRED_PHOTO_VIEWS = [
    # Exterior (6)
    ("front", "Front view — full vehicle, straight on"),
    ("rear", "Rear view — full vehicle, straight on"),
    ("side_left", "Left side profile — full vehicle"),
    ("side_right", "Right side profile — full vehicle"),
    ("front_three_quarter", "Front 3/4 view (driver side)"),
    ("rear_three_quarter", "Rear 3/4 view (passenger side)"),
    # Interior (5)
    ("interior_front", "Front cabin — driver and passenger seats, center console"),
    ("interior_rear", "Rear seats and legroom"),
    ("dashboard", "Dashboard with mileage/odometer clearly visible"),
    ("infotainment", "Infotainment screen / navigation system"),
    ("trunk", "Trunk / cargo area — open, empty"),
    # Mechanical (3)
    ("engine", "Engine bay — open hood"),
    ("wheels_front", "Front wheel close-up — tire brand, DOT visible"),
    ("wheels_rear", "Rear wheel close-up — tire brand, DOT visible"),
    # Documentation (2)
    ("service_book", "Service booklet — last stamped page"),
    ("hu_report", "HU/TÜV report or sticker on plate"),
    # Condition (2)
    ("damage_detail", "Close-up of any scratches, dents, or paint issues (or confirm 'none')"),
    ("underbody", "Underbody photo (if available) or confirmation of condition"),
]

MIN_PHOTOS_COMPLETE = 8


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

    # Separate critical vs important data requests
    critical_keys = {"vin", "service_history", "hu_date", "previous_owners", "accident_history"}
    critical_data = [(k, d) for k, d in analysis["missing_data"] if k in critical_keys]
    important_data = [(k, d) for k, d in analysis["missing_data"] if k not in critical_keys]

    # Build structured sections
    photo_section = ""
    if analysis["missing_photos"]:
        # Group photos by category
        exterior = [(v, d) for v, d in analysis["missing_photos"]
                    if v in ("front", "rear", "side_left", "side_right", "front_three_quarter", "rear_three_quarter")]
        interior = [(v, d) for v, d in analysis["missing_photos"]
                    if v in ("interior_front", "interior_rear", "dashboard", "infotainment", "trunk")]
        mechanical = [(v, d) for v, d in analysis["missing_photos"]
                      if v in ("engine", "wheels_front", "wheels_rear")]
        docs = [(v, d) for v, d in analysis["missing_photos"]
                if v in ("service_book", "hu_report")]
        condition = [(v, d) for v, d in analysis["missing_photos"]
                     if v in ("damage_detail", "underbody")]

        sections = []
        if exterior:
            lines = "\n".join(f"    • {d}" for _, d in exterior)
            sections.append(f"  EXTERIOR ({len(exterior)} photos):\n{lines}")
        if interior:
            lines = "\n".join(f"    • {d}" for _, d in interior)
            sections.append(f"  INTERIOR ({len(interior)} photos):\n{lines}")
        if mechanical:
            lines = "\n".join(f"    • {d}" for _, d in mechanical)
            sections.append(f"  MECHANICAL ({len(mechanical)} photos):\n{lines}")
        if docs:
            lines = "\n".join(f"    • {d}" for _, d in docs)
            sections.append(f"  DOCUMENTATION ({len(docs)} photos):\n{lines}")
        if condition:
            lines = "\n".join(f"    • {d}" for _, d in condition)
            sections.append(f"  CONDITION ({len(condition)} photos):\n{lines}")

        photo_section = f"""
--- PHOTOS REQUESTED ({len(analysis['missing_photos'])} views) ---

We need high-resolution photos for our pre-purchase evaluation:

{chr(10).join(sections)}

Please send photos at the highest resolution available (minimum 1280x960).
If some views are not possible, please let us know."""

    data_section = ""
    if critical_data or important_data:
        lines = []
        if critical_data:
            lines.append("  ESSENTIAL (required before we can proceed):")
            for _, desc in critical_data:
                lines.append(f"    • {desc}")
        if important_data:
            lines.append("")
            lines.append("  ADDITIONAL (helps our client make a faster decision):")
            for _, desc in important_data:
                lines.append(f"    • {desc}")

        data_section = f"""
--- VEHICLE INFORMATION REQUESTED ---

{chr(10).join(lines)}"""

    # Compose body
    body = f"""Dear {analysis.get('seller_name') or 'Sales Team'},

We are ARGOS Automotive, a European vehicle sourcing company. We work with professional dealers across the EU and are interested in the following vehicle from your inventory:

  Vehicle: {vehicle}
  Mileage: {km:,} km
  Listed price: EUR {price:,.0f}

Our client is ready to proceed quickly if the vehicle meets our quality standards. To complete our pre-purchase evaluation, we kindly request the following:
{photo_section}
{data_section}

--- NEXT STEPS ---

1. Please confirm the vehicle is still available
2. Send the requested photos and information to this email
3. We will respond within 24 hours with our decision

We handle all transport, customs, and registration. If the vehicle passes our checks, we can arrange collection within 5-7 business days.

Thank you for your time. We look forward to a smooth transaction.

Best regards,

Luca Ferretti
Vehicle Sourcing Department
ARGOS Automotive — European Vehicle Intelligence
Email: ferretti.argosautomotive@gmail.com
Web: argos-automotive.pages.dev
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


def compose_followup_email(analysis: Dict, followup_num: int) -> Dict:
    """
    Compose follow-up email (Day 3 or Day 7).

    Day 3: Short reminder, reference original email
    Day 7: Final attempt, "closing inquiry in 7 days"

    All in English — lingua franca for all EU sellers.
    """
    vehicle = analysis["vehicle"]
    seller_name = analysis.get("seller_name") or "Sales Team"
    to_email = analysis.get("seller_email")

    if followup_num == 1:
        # Day 3 — short reminder
        subject = f"Follow-up: {vehicle} — Still available?"
        body = f"""Dear {seller_name},

I am following up on my inquiry about the {vehicle} from a few days ago.

Could you please confirm:
1. Is the vehicle still available?
2. Can you share the VIN number?

We are ready to proceed quickly if it meets our standards.

Best regards,
Luca Ferretti
ARGOS Automotive
ferretti.argosautomotive@gmail.com
"""
    else:
        # Day 7 — final attempt
        subject = f"Final inquiry: {vehicle}"
        body = f"""Dear {seller_name},

This is my final follow-up regarding the {vehicle}.

If I don't hear back within 7 days, I will close this inquiry and move to alternative vehicles.

If you are still interested in selling, a quick reply with the VIN and confirmation of availability would be appreciated.

Best regards,
Luca Ferretti
ARGOS Automotive
ferretti.argosautomotive@gmail.com
"""

    return {
        "subject": subject,
        "body": body.strip(),
        "to_email": to_email,
        "to_name": seller_name,
        "vehicle": vehicle,
        "followup_num": followup_num,
    }


def compose_initial_email_slim(analysis: Dict) -> Dict:
    """
    Compose SLIM initial contact email.
    Ask ONLY for VIN + availability first. Photos in follow-up.

    Research finding: asking for too much in first email lowers response rate.
    """
    vehicle = analysis["vehicle"]
    km = analysis.get("km", 0)
    price = analysis.get("price", 0)
    seller_name = analysis.get("seller_name") or "Sales Team"

    subject = f"Purchase inquiry: {vehicle}, {km:,} km"

    body = f"""Dear {seller_name},

We are ARGOS Automotive, a European vehicle sourcing company. We are interested in purchasing the following vehicle from your inventory:

  {vehicle} | {km:,} km | EUR {price:,.0f}

Before we proceed, could you please confirm:

  1. Is this vehicle still available?
  2. What is the VIN number?
  3. Is the vehicle free of any outstanding finance?

If confirmed, we would then request additional photos and documentation for our pre-purchase evaluation.

We handle all transport and registration. Collection can be arranged within 5-7 business days.

Best regards,

Luca Ferretti
ARGOS Automotive — European Vehicle Sourcing
ferretti.argosautomotive@gmail.com
"""

    return {
        "subject": subject,
        "body": body.strip(),
        "to_email": analysis.get("seller_email"),
        "to_name": seller_name,
        "vehicle": vehicle,
        "type": "initial_slim",
    }


def send_followup(listing_id: str, followup_num: int,
                  db_path: str = None, dry_run: bool = False) -> Dict:
    """Send a follow-up email for a listing."""
    analysis = analyze_missing_data(listing_id, db_path)
    if "error" in analysis or not analysis.get("seller_email"):
        return {"sent": False, "error": "no seller email"}

    email_data = compose_followup_email(analysis, followup_num)
    return send_seller_email(email_data, dry_run=dry_run)


def check_inbox_for_responses(
    listing_ids: List[str] = None,
    max_emails: int = 50,
) -> Dict[str, Dict]:
    """
    Check Gmail inbox (IMAP) for seller responses.

    Searches for replies matching seller emails from vehicle_listings.
    Returns dict: {listing_id: {"responded": True, "subject": ..., "date": ...}}

    Requires ARGOS_EMAIL and ARGOS_EMAIL_PASSWORD in env.
    """
    import imaplib
    import email as email_lib
    from email.header import decode_header

    imap_server = "imap.gmail.com"
    username = os.getenv("ARGOS_EMAIL", SENDER_EMAIL)
    password = os.getenv("ARGOS_EMAIL_PASSWORD", "")

    if not password:
        print("  IMAP: ARGOS_EMAIL_PASSWORD not set — cannot check inbox")
        return {}

    responses = {}

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, password)
        mail.select("INBOX")

        # Search for recent unread messages
        status, msg_ids = mail.search(None, '(UNSEEN SINCE "01-Mar-2026")')
        if status != "OK" or not msg_ids[0]:
            mail.logout()
            return {}

        ids = msg_ids[0].split()[-max_emails:]  # Last N messages
        print(f"  IMAP: checking {len(ids)} unread messages...")

        # Load seller emails from DB for matching
        seller_emails = {}
        if listing_ids:
            import duckdb
            db_path = str(SCRIPT_DIR.parent.parent / "src" / "cove" / "data" / "cove_tracker.duckdb")
            con = duckdb.connect(db_path, read_only=True)
            for lid in listing_ids:
                row = con.execute(
                    "SELECT seller_email FROM vehicle_listings WHERE listing_id = ?", [lid]
                ).fetchone()
                if row and row[0]:
                    seller_emails[row[0].lower()] = lid
            con.close()

        for msg_id in ids:
            status, data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            msg = email_lib.message_from_bytes(data[0][1])
            from_addr = msg.get("From", "").lower()
            subject = msg.get("Subject", "")

            # Decode subject if encoded
            try:
                decoded = decode_header(subject)
                subject = "".join(
                    part.decode(enc or "utf-8") if isinstance(part, bytes) else part
                    for part, enc in decoded
                )
            except Exception:
                pass

            # Match against seller emails
            for seller_email, lid in seller_emails.items():
                if seller_email in from_addr:
                    responses[lid] = {
                        "responded": True,
                        "from": from_addr,
                        "subject": subject,
                        "date": msg.get("Date", ""),
                        "listing_id": lid,
                    }
                    print(f"  MATCH: {lid} ← {from_addr} — {subject[:50]}")

        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"  IMAP error: {e}")
    except Exception as e:
        print(f"  IMAP connection error: {e}")

    return responses


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
