"""ARGOS Automotive — guarded EU seller contact.

Seller contact belongs *after* an S292 dealer commission.  This module keeps
its historical public API names but fails closed unless the caller supplies a
traceable :class:`DemandEvidence` authorising sourcing for the listing/request.

No function in this module infers that a dealer is ready to buy, promises a
collection date, or promotes a raw photo count to semantic completeness.
"""
from __future__ import annotations

import argparse
import imaplib
import json
import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    from src.cove.demand_contract import (
        DemandEvidence,
        NOT_AVAILABLE,
        require_listing_authorization,
    )
except ModuleNotFoundError:  # direct CLI execution from src/cove
    from demand_contract import (  # type: ignore
        DemandEvidence,
        NOT_AVAILABLE,
        require_listing_authorization,
    )

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_DB_PATH = SCRIPT_DIR / "data" / "cove_tracker.duckdb"

SMTP_SERVER = os.getenv("ARGOS_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("ARGOS_SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("ARGOS_EMAIL", "")
SENDER_PASSWORD = os.getenv("ARGOS_EMAIL_PASSWORD", "")
SENDER_NAME = os.getenv("ARGOS_SELLER_SENDER_NAME", "ARGOS Automotive")

REQUIRED_DATA: Dict[str, str] = {
    "vin": "Vehicle Identification Number (VIN)",
    "service_history": "Service/maintenance history available for the vehicle",
    "hu_date": "Latest HU/TÜV inspection date/result where applicable",
    "previous_owners": "Number of previous owners, if known",
    "accident_history": "Known accident/damage and repair history",
    "equipment_list": "Equipment/options list",
    "num_keys": "Number of keys supplied",
    "next_service_due": "Next scheduled service, if known",
    "outstanding_finance": "Confirmation of any outstanding finance/liens",
    "interior_color_material": "Interior colour/material",
    "tire_type_condition": "Tyre type/condition and DOT/tread information if available",
    "available_from": "Current availability / earliest possible handover",
}

REQUIRED_PHOTO_VIEWS: Tuple[Tuple[str, str], ...] = (
    ("front", "Front view — full vehicle"),
    ("rear", "Rear view — full vehicle"),
    ("side_left", "Left side profile"),
    ("side_right", "Right side profile"),
    ("front_three_quarter", "Front three-quarter view"),
    ("rear_three_quarter", "Rear three-quarter view"),
    ("interior_front", "Front cabin / seats / centre console"),
    ("interior_rear", "Rear seats"),
    ("dashboard", "Dashboard with odometer visible"),
    ("infotainment", "Infotainment screen"),
    ("trunk", "Boot / cargo area"),
    ("engine", "Engine bay"),
    ("wheels_front", "Front wheel/tyre close-up"),
    ("wheels_rear", "Rear wheel/tyre close-up"),
    ("service_book", "Relevant service-history documentation"),
    ("hu_report", "HU/TÜV documentation where applicable"),
    ("damage_detail", "Close-up of disclosed damage/repairs, if any"),
    ("underbody", "Underbody view, if available"),
)
PHOTO_VIEW_KEYS = {view for view, _ in REQUIRED_PHOTO_VIEWS}
MIN_PHOTOS_COMPLETE = len(PHOTO_VIEW_KEYS)  # compatibility constant; semantics still mandatory

_DATA_ALIASES: Dict[str, Tuple[str, ...]] = {
    "vin": ("vin",),
    "service_history": ("service_history", "service_history_present", "service_history_verified"),
    "hu_date": ("hu_date", "tuv_date", "inspection_date"),
    "previous_owners": ("previous_owners", "owner_count"),
    "accident_history": ("accident_history", "accident_history_verified", "accident_free_confirmed"),
    "equipment_list": ("equipment_list", "equipment"),
    "num_keys": ("num_keys", "keys_count"),
    "next_service_due": ("next_service_due",),
    "outstanding_finance": ("outstanding_finance", "finance_status", "lien_status"),
    "interior_color_material": ("interior_color_material", "interior", "interior_material"),
    "tire_type_condition": ("tire_type_condition", "tire_condition"),
    "available_from": ("available_from", "seller_availability", "availability_status"),
}


def _known(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        return bool(stripped) and stripped not in {NOT_AVAILABLE, "DA_VERIFICARE", "NO-VERDICT"}
    return True


def _table_columns(con: Any, table: str) -> set[str]:
    try:
        rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    except Exception:
        return set()
    return {str(row[1]) for row in rows if len(row) > 1}


def _fetch_dict(con: Any, table: str, listing_id: str) -> Dict[str, Any]:
    cols = _table_columns(con, table)
    if "listing_id" not in cols:
        return {}
    ordered = sorted(cols)
    projection = ", ".join(f'"{col}"' for col in ordered)
    row = con.execute(
        f'SELECT {projection} FROM "{table}" WHERE listing_id = ? LIMIT 1',
        [listing_id],
    ).fetchone()
    return dict(zip(ordered, row)) if row else {}


def _first_known(mapping: Mapping[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name in mapping and _known(mapping[name]):
            return mapping[name]
    return None


def _semantic_photo_coverage(con: Any, listing_id: str) -> tuple[int, set[str], bool]:
    cols = _table_columns(con, "vehicle_images")
    if "listing_id" not in cols:
        return 0, set(), False
    label_col = next(
        (name for name in ("view", "view_type", "photo_view", "semantic_view", "image_type") if name in cols),
        None,
    )
    if label_col is None:
        count = con.execute(
            "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?", [listing_id]
        ).fetchone()[0]
        return int(count or 0), set(), False
    rows = con.execute(
        f'SELECT "{label_col}" FROM vehicle_images WHERE listing_id = ?', [listing_id]
    ).fetchall()
    views = {
        str(row[0]).strip().lower()
        for row in rows
        if row and _known(row[0]) and str(row[0]).strip().lower() in PHOTO_VIEW_KEYS
    }
    return len(rows), views, bool(views)


def _vehicle_label(row: Mapping[str, Any]) -> str:
    parts = [row.get("make"), row.get("model"), row.get("year")]
    value = " ".join(str(part).strip() for part in parts if _known(part)).strip()
    return value or NOT_AVAILABLE


def analyze_missing_data(listing_id: str, db_path: str | None = None) -> Dict[str, Any]:
    """Read factual vehicle/seller data and semantic photo coverage.

    Raw image count is returned for diagnostics but cannot satisfy a requested
    view unless the DB stores a recognised semantic label for that image.
    """
    import duckdb

    listing_id = str(listing_id or "").strip()
    if not listing_id:
        return {"error": "listing_id is required"}
    path = str(db_path or DEFAULT_DB_PATH)
    con = duckdb.connect(path, read_only=True)
    try:
        cove = _fetch_dict(con, "cove_results", listing_id)
        listing = _fetch_dict(con, "vehicle_listings", listing_id)
        photo_count, observed_views, semantics_available = _semantic_photo_coverage(con, listing_id)
    finally:
        con.close()

    if not cove and not listing:
        return {"error": f"Listing {listing_id} not found"}

    merged = {**cove, **listing}
    missing_data: List[Tuple[str, str]] = []
    data_status: Dict[str, bool] = {}
    for key, description in REQUIRED_DATA.items():
        value = _first_known(merged, _DATA_ALIASES[key])
        # A malformed/short VIN is not evidence of a VIN.
        has_value = _known(value)
        if key == "vin" and has_value:
            compact = "".join(ch for ch in str(value).upper() if ch.isalnum())
            has_value = len(compact) == 17
        data_status[key] = bool(has_value)
        if not has_value:
            missing_data.append((key, description))

    missing_photos = [
        (view, description)
        for view, description in REQUIRED_PHOTO_VIEWS
        if view not in observed_views
    ]

    return {
        "listing_id": listing_id,
        "vehicle": _vehicle_label(merged),
        "price": _first_known(merged, ("price_eu", "price")),
        "km": _first_known(merged, ("mileage", "km")),
        "vin": _first_known(merged, ("vin",)),
        "source": _first_known(merged, ("source",)) or NOT_AVAILABLE,
        "seller_name": _first_known(merged, ("seller_name", "seller", "dealer_name")),
        "seller_email": _first_known(merged, ("seller_email", "email")),
        "seller_phone": _first_known(merged, ("seller_phone", "phone")),
        "detail_url": _first_known(merged, ("detail_url", "url")),
        "photo_count": photo_count,
        "photo_semantics_available": semantics_available,
        "observed_photo_views": sorted(observed_views),
        "missing_data": missing_data,
        "missing_photos": missing_photos,
        "data_completeness": data_status,
        "needs_contact": bool(missing_data or missing_photos),
    }


def _require_contact_context(
    analysis: Mapping[str, Any],
    evidence: Optional[DemandEvidence],
) -> DemandEvidence:
    return require_listing_authorization(evidence, str(analysis.get("listing_id") or ""))


def _format_vehicle_line(analysis: Mapping[str, Any]) -> str:
    parts = [str(analysis.get("vehicle") or NOT_AVAILABLE)]
    km = analysis.get("km")
    price = analysis.get("price")
    if _known(km):
        parts.append(f"{km} km")
    if _known(price):
        parts.append(f"listed price EUR {price}")
    return " | ".join(parts)


def compose_initial_email_slim(
    analysis: Dict[str, Any],
    evidence: Optional[DemandEvidence] = None,
) -> Dict[str, Any]:
    """Compose the first evidence-safe seller inquiry."""
    authorized = _require_contact_context(analysis, evidence)
    seller_name = analysis.get("seller_name") or "Sales Team"
    vehicle = analysis.get("vehicle") or NOT_AVAILABLE
    subject = f"Vehicle information request: {vehicle}"
    body = f"""Dear {seller_name},

ARGOS Automotive is evaluating this vehicle in connection with a professional sourcing request:

  {_format_vehicle_line(analysis)}

Could you please confirm:
1. whether the vehicle is currently available;
2. the 17-character VIN, if it is not already shown in the listing;
3. whether there is any outstanding finance or lien that would affect a professional purchase.

If the vehicle remains a candidate after these checks, we may request specific photos and documentation required for the evaluation.

This message is a request for information only and is not a purchase commitment.

Best regards,
{SENDER_NAME}
ARGOS Automotive
"""
    return {
        "subject": subject,
        "body": body.strip(),
        "to_email": analysis.get("seller_email"),
        "to_name": seller_name,
        "vehicle": vehicle,
        "type": "initial_slim",
        "dealer_id": authorized.dealer_id,
        "evidence_id": authorized.evidence_id,
        "listing_id": analysis.get("listing_id"),
    }


def compose_seller_email(
    analysis: Dict[str, Any],
    evidence: Optional[DemandEvidence] = None,
) -> Dict[str, Any]:
    """Compose a detailed request only after S292 sourcing authorization."""
    authorized = _require_contact_context(analysis, evidence)
    seller_name = analysis.get("seller_name") or "Sales Team"
    vehicle = analysis.get("vehicle") or NOT_AVAILABLE
    subject = f"Additional information request: {vehicle}"

    data_lines = [f"  • {description}" for _, description in analysis.get("missing_data", [])]
    photo_lines = [f"  • {description}" for _, description in analysis.get("missing_photos", [])]
    sections: List[str] = []
    if data_lines:
        sections.append("VEHICLE INFORMATION\n" + "\n".join(data_lines))
    if photo_lines:
        sections.append("PHOTOS / DOCUMENT IMAGES\n" + "\n".join(photo_lines))
    requested = "\n\n".join(sections) or "No additional item is currently required."

    body = f"""Dear {seller_name},

ARGOS Automotive is evaluating the following vehicle in connection with a professional sourcing request:

  {_format_vehicle_line(analysis)}

To complete the evidence package, could you please provide or confirm the items below where available?

{requested}

Please state explicitly when an item is unavailable or unknown; we prefer an accurate 'not available' to an assumption. Any information supplied will be treated as seller-provided evidence for this vehicle evaluation.

This inquiry does not constitute a purchase commitment, a promise of collection, or acceptance of the vehicle.

Best regards,
{SENDER_NAME}
ARGOS Automotive
"""
    return {
        "subject": subject,
        "body": body.strip(),
        "to_email": analysis.get("seller_email"),
        "to_name": seller_name,
        "vehicle": vehicle,
        "type": "evidence_request",
        "dealer_id": authorized.dealer_id,
        "evidence_id": authorized.evidence_id,
        "listing_id": analysis.get("listing_id"),
    }


def compose_followup_email(
    analysis: Dict[str, Any],
    followup_num: int,
    evidence: Optional[DemandEvidence] = None,
) -> Dict[str, Any]:
    """Compose a factual follow-up; no artificial urgency or purchase promise."""
    authorized = _require_contact_context(analysis, evidence)
    seller_name = analysis.get("seller_name") or "Sales Team"
    vehicle = analysis.get("vehicle") or NOT_AVAILABLE
    final = int(followup_num) >= 2
    subject = f"{'Final ' if final else ''}follow-up: {vehicle}"
    if final:
        action = "If the vehicle or requested information is no longer available, a short confirmation is sufficient and we will close the evaluation."
    else:
        action = "A short confirmation of current availability and the VIN, if available, is sufficient for the next step."
    body = f"""Dear {seller_name},

I am following up on our information request concerning:

  {_format_vehicle_line(analysis)}

{action}

This remains an information request only and is not a purchase commitment.

Best regards,
{SENDER_NAME}
ARGOS Automotive
"""
    return {
        "subject": subject,
        "body": body.strip(),
        "to_email": analysis.get("seller_email"),
        "to_name": seller_name,
        "vehicle": vehicle,
        "followup_num": int(followup_num),
        "type": "followup",
        "dealer_id": authorized.dealer_id,
        "evidence_id": authorized.evidence_id,
        "listing_id": analysis.get("listing_id"),
    }


def send_seller_email(
    email_data: Dict[str, Any],
    dry_run: bool = False,
    *,
    evidence: Optional[DemandEvidence] = None,
) -> Dict[str, Any]:
    """Send via SMTP only after re-validating the S292 listing gate."""
    listing_id = str(email_data.get("listing_id") or "").strip()
    authorized = require_listing_authorization(evidence, listing_id)
    if email_data.get("dealer_id") and str(email_data["dealer_id"]) != authorized.dealer_id:
        return {"sent": False, "error": "S292_GATE: dealer_id mismatch"}
    if email_data.get("evidence_id") and str(email_data["evidence_id"]) != authorized.evidence_id:
        return {"sent": False, "error": "S292_GATE: evidence_id mismatch"}

    to_email = str(email_data.get("to_email") or "").strip()
    if not to_email:
        return {"sent": False, "error": "No seller email available"}

    if dry_run:
        return {
            "sent": False,
            "dry_run": True,
            "to": to_email,
            "subject": email_data.get("subject"),
            "dealer_id": authorized.dealer_id,
            "evidence_id": authorized.evidence_id,
        }

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return {"sent": False, "error": "ARGOS_EMAIL/ARGOS_EMAIL_PASSWORD not configured"}

    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = f"{email_data.get('to_name') or 'Sales Team'} <{to_email}>"
    msg["Subject"] = str(email_data.get("subject") or "ARGOS vehicle information request")
    msg.attach(MIMEText(str(email_data.get("body") or ""), "plain", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
    except (OSError, smtplib.SMTPException) as exc:
        return {"sent": False, "error": f"smtp_error: {type(exc).__name__}"}

    return {
        "sent": True,
        "to": to_email,
        "subject": msg["Subject"],
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "dealer_id": authorized.dealer_id,
        "evidence_id": authorized.evidence_id,
        "listing_id": listing_id,
    }


def _record_contact_result(
    listing_id: str,
    result: Mapping[str, Any],
    db_path: str | None,
) -> None:
    """Best-effort audit update only when compatible columns already exist."""
    if not result.get("sent"):
        return
    try:
        import duckdb
        con = duckdb.connect(str(db_path or DEFAULT_DB_PATH))
        try:
            cols = _table_columns(con, "vehicle_listings")
            assignments: List[str] = []
            params: List[Any] = []
            if "seller_contact_sent_at" in cols:
                assignments.append("seller_contact_sent_at = ?")
                params.append(result.get("sent_at"))
            if "seller_contact_evidence_id" in cols:
                assignments.append("seller_contact_evidence_id = ?")
                params.append(result.get("evidence_id"))
            if assignments:
                params.append(listing_id)
                con.execute(
                    f"UPDATE vehicle_listings SET {', '.join(assignments)} WHERE listing_id = ?",
                    params,
                )
        finally:
            con.close()
    except Exception:
        # Sending result remains authoritative; absence of legacy audit columns
        # must not be rewritten as a false successful DB persistence event.
        return


def send_followup(
    listing_id: str,
    followup_num: int,
    db_path: str | None = None,
    dry_run: bool = False,
    *,
    evidence: Optional[DemandEvidence] = None,
) -> Dict[str, Any]:
    analysis = analyze_missing_data(listing_id, db_path)
    if "error" in analysis:
        return {"sent": False, "error": analysis["error"]}
    if not analysis.get("seller_email"):
        return {"sent": False, "error": "No seller email available"}
    data = compose_followup_email(analysis, followup_num, evidence=evidence)
    result = send_seller_email(data, dry_run=dry_run, evidence=evidence)
    _record_contact_result(listing_id, result, db_path)
    return result


def check_inbox_for_responses(
    listing_ids: List[str] | None = None,
    max_emails: int = 50,
    *,
    db_path: str | None = None,
    since_days: int = 30,
) -> Dict[str, Dict[str, Any]]:
    """Read recent unread replies and correlate only against known seller emails."""
    import email as email_lib
    import duckdb

    if not SENDER_EMAIL or not SENDER_PASSWORD or not listing_ids:
        return {}

    seller_emails: Dict[str, str] = {}
    con = duckdb.connect(str(db_path or DEFAULT_DB_PATH), read_only=True)
    try:
        cols = _table_columns(con, "vehicle_listings")
        if "seller_email" not in cols:
            return {}
        for listing_id in listing_ids:
            row = con.execute(
                "SELECT seller_email FROM vehicle_listings WHERE listing_id = ?", [listing_id]
            ).fetchone()
            if row and _known(row[0]):
                seller_emails[str(row[0]).strip().lower()] = str(listing_id)
    finally:
        con.close()
    if not seller_emails:
        return {}

    since = (datetime.now(timezone.utc) - timedelta(days=max(1, int(since_days)))).strftime("%d-%b-%Y")
    responses: Dict[str, Dict[str, Any]] = {}
    mail = imaplib.IMAP4_SSL(os.getenv("ARGOS_IMAP_SERVER", "imap.gmail.com"), timeout=20)
    try:
        mail.login(SENDER_EMAIL, SENDER_PASSWORD)
        mail.select("INBOX", readonly=True)
        status, msg_ids = mail.search(None, f'(UNSEEN SINCE "{since}")')
        if status != "OK" or not msg_ids or not msg_ids[0]:
            return {}
        for msg_id in msg_ids[0].split()[-max(1, int(max_emails)):]:
            status, data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK" or not data or not isinstance(data[0], tuple):
                continue
            msg = email_lib.message_from_bytes(data[0][1])
            sender = parseaddr(msg.get("From", ""))[1].strip().lower()
            listing_id = seller_emails.get(sender)
            if not listing_id:
                continue
            subject = msg.get("Subject", "")
            try:
                subject = "".join(
                    part.decode(enc or "utf-8", errors="replace") if isinstance(part, bytes) else part
                    for part, enc in decode_header(subject)
                )
            except Exception:
                subject = str(subject)
            responses[listing_id] = {
                "responded": True,
                "from": sender,
                "subject": subject,
                "date": msg.get("Date", ""),
                "listing_id": listing_id,
            }
    finally:
        try:
            mail.logout()
        except Exception:
            pass
    return responses


def request_missing_data(
    listing_id: str,
    db_path: str | None = None,
    dry_run: bool = False,
    *,
    evidence: Optional[DemandEvidence] = None,
    initial_slim: bool = True,
) -> Dict[str, Any]:
    """Analyse -> compose -> guarded send for an authorised sourcing request."""
    require_listing_authorization(evidence, listing_id)
    analysis = analyze_missing_data(listing_id, db_path)
    if "error" in analysis:
        return analysis
    if not analysis["needs_contact"]:
        return {"listing_id": listing_id, "needs_contact": False, "complete": True, "analysis": analysis}
    email_data = (
        compose_initial_email_slim(analysis, evidence=evidence)
        if initial_slim
        else compose_seller_email(analysis, evidence=evidence)
    )
    result = send_seller_email(email_data, dry_run=dry_run, evidence=evidence)
    _record_contact_result(listing_id, result, db_path)
    return {
        "listing_id": listing_id,
        "analysis": analysis,
        "email": email_data,
        "send_result": result,
    }


def _load_evidence(path: str) -> DemandEvidence:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("evidence JSON must contain an object")
    return DemandEvidence.from_mapping(data)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="ARGOS guarded seller-contact utility")
    parser.add_argument("listing_id")
    parser.add_argument("--db", dest="db_path")
    parser.add_argument("--check", action="store_true", help="read-only completeness check")
    parser.add_argument("--dry-run", action="store_true", help="validate gate and compose without sending")
    parser.add_argument("--send", action="store_true", help="live send; requires S292 evidence JSON")
    parser.add_argument("--evidence-json", help="path to serialized DemandEvidence")
    args = parser.parse_args(argv)

    if args.check:
        print(json.dumps(analyze_missing_data(args.listing_id, args.db_path), indent=2, ensure_ascii=False, default=str))
        return 0

    if not args.evidence_json:
        print("BLOCKED: --evidence-json is required for any seller-contact composition/send", file=sys.stderr)
        return 2
    try:
        evidence = _load_evidence(args.evidence_json)
        result = request_missing_data(
            args.listing_id,
            args.db_path,
            dry_run=(args.dry_run or not args.send),
            evidence=evidence,
        )
    except (PermissionError, TypeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0 if result.get("send_result", {}).get("sent") or result.get("send_result", {}).get("dry_run") or result.get("complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())
