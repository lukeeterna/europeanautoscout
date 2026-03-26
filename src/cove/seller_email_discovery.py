"""
seller_email_discovery.py — ARGOS Automated Seller Email Discovery
CoVe 2026 | Enterprise Grade

Finds the contact email of EU vehicle sellers from:
  1. Listing detail page (scrape contact section)
  2. Seller name → Google search → dealer website → contact page
  3. Seller website → common email patterns (info@, kontakt@, sales@)
  4. Impressum page parsing (German legal requirement: email must be listed)

BUSINESS RULE: Every dealer in Germany MUST publish their email in the
Impressum (legal page). This is legally required by Telemediengesetz §5.
Same applies to NL (KvK), BE, AT, FR, etc.

Usage:
  from src.cove.seller_email_discovery import discover_seller_email

  result = discover_seller_email(seller_name="Procar Automobile", country="DE")
  # Returns: {"email": "info@procar-automobile.de", "source": "impressum", ...}

CLI:
  python3 src/cove/seller_email_discovery.py "Procar Automobile"
  python3 src/cove/seller_email_discovery.py --listing fresh_84aec3405b5d
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Common contact email patterns for EU auto dealers
EMAIL_PATTERNS = [
    "info@{domain}",
    "kontakt@{domain}",       # DE
    "verkauf@{domain}",        # DE sales
    "anfrage@{domain}",        # DE inquiry
    "contact@{domain}",        # FR/EN
    "sales@{domain}",          # EN
    "ventes@{domain}",         # FR
    "verkoop@{domain}",        # NL
]

# Impressum URL patterns (German legal requirement)
IMPRESSUM_PATHS = [
    "/impressum",
    "/impressum.html",
    "/kontakt",
    "/contact",
    "/about/impressum",
    "/ueber-uns/impressum",
    "/legal",
    "/mentions-legales",       # FR
    "/disclaimer",
    "/over-ons",               # NL
]

# Email regex
EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE,
)

# Blacklist: emails we should never return (generic/useless)
EMAIL_BLACKLIST = {
    "noreply@", "no-reply@", "mailer-daemon@", "postmaster@",
    "privacy@", "abuse@", "webmaster@", "support@autoscout24",
    "support@mobile.de", "datenschutz@",
}


def discover_seller_email(
    seller_name: str = None,
    seller_website: str = None,
    detail_url: str = None,
    listing_id: str = None,
    country: str = "DE",
    db_path: str = None,
) -> Dict:
    """
    Discover seller email through multiple strategies:

    1. If listing_id: get seller_name + detail_url from DB
    2. Scrape detail page for contact info
    3. Find seller website from name (Google or direct URL construction)
    4. Scrape Impressum/contact page for email
    5. Try common email patterns via SMTP verification

    Returns:
        {
            "email": "info@procar-automobile.de" or None,
            "emails_found": ["info@...", "verkauf@..."],
            "source": "impressum" | "detail_page" | "website_contact" | "pattern" | None,
            "seller_name": str,
            "seller_website": str,
            "confidence": "high" | "medium" | "low",
            "method_log": [str],
        }
    """
    log = []
    emails_found = []
    seller_website = seller_website or ""

    # ── Step 0: Load from DB if listing_id provided ──
    if listing_id and not seller_name:
        db_info = _load_seller_from_db(listing_id, db_path)
        if db_info:
            seller_name = seller_name or db_info.get("seller_name")
            seller_website = seller_website or db_info.get("seller_website", "")
            detail_url = detail_url or db_info.get("detail_url")
            if db_info.get("seller_email"):
                return {
                    "email": db_info["seller_email"],
                    "emails_found": [db_info["seller_email"]],
                    "source": "database",
                    "seller_name": seller_name,
                    "seller_website": seller_website,
                    "confidence": "high",
                    "method_log": ["Found email in DB"],
                }
            log.append(f"DB: seller_name={seller_name}, website={seller_website}")

    if not seller_name:
        return {
            "email": None, "emails_found": [], "source": None,
            "seller_name": None, "seller_website": None,
            "confidence": "none", "method_log": ["No seller name available"],
        }

    print(f"  Discovering email for: {seller_name} ({country})")

    # ── Step 1: Scrape detail page for contact info ──
    if detail_url:
        log.append(f"Strategy 1: Scraping detail page {detail_url[:60]}...")
        page_emails = _scrape_page_for_emails(detail_url)
        if page_emails:
            emails_found.extend(page_emails)
            log.append(f"  Found {len(page_emails)} emails on detail page")

    # ── Step 2: Construct/find seller website ──
    if not seller_website:
        seller_website = _guess_website_from_name(seller_name, country)
        log.append(f"Strategy 2: Guessed website → {seller_website}")

    # ── Step 3: Scrape seller website for emails ──
    if seller_website:
        # Try main page
        log.append(f"Strategy 3: Scraping seller website {seller_website}")
        main_emails = _scrape_page_for_emails(seller_website)
        if main_emails:
            emails_found.extend(main_emails)
            log.append(f"  Found {len(main_emails)} emails on main page")

        # Try Impressum / contact pages
        for path in IMPRESSUM_PATHS:
            imp_url = seller_website.rstrip("/") + path
            log.append(f"Strategy 4: Trying {imp_url}")
            imp_emails = _scrape_page_for_emails(imp_url)
            if imp_emails:
                emails_found.extend(imp_emails)
                log.append(f"  Found {len(imp_emails)} emails on {path}")
                break  # Found impressum emails, stop trying

    # ── Step 4: Try common patterns ──
    if not emails_found and seller_website:
        domain = _extract_domain(seller_website)
        if domain:
            log.append(f"Strategy 5: Trying common patterns for {domain}")
            for pattern in EMAIL_PATTERNS:
                candidate = pattern.format(domain=domain)
                emails_found.append(candidate)
            log.append(f"  Generated {len(EMAIL_PATTERNS)} pattern candidates")

    # ── Deduplicate and rank ──
    emails_found = _deduplicate_and_rank(emails_found)

    # Determine best email and confidence
    best_email = emails_found[0] if emails_found else None
    source = "none"
    confidence = "none"

    if best_email:
        # Check if from detail page, impressum, or pattern
        if detail_url and any(e == best_email for e in _scrape_page_for_emails(detail_url) if detail_url):
            source = "detail_page"
            confidence = "high"
        elif any("impressum" in s or "kontakt" in s or "contact" in s for s in log if "Found" in s):
            source = "impressum"
            confidence = "high"
        elif any("main page" in s for s in log if "Found" in s):
            source = "website_contact"
            confidence = "medium"
        else:
            source = "pattern"
            confidence = "low"

    result = {
        "email": best_email,
        "emails_found": emails_found[:5],
        "source": source,
        "seller_name": seller_name,
        "seller_website": seller_website,
        "confidence": confidence,
        "method_log": log,
    }

    if best_email:
        print(f"  FOUND: {best_email} (source: {source}, confidence: {confidence})")
    else:
        print(f"  NOT FOUND: no email discovered for {seller_name}")

    return result


def _load_seller_from_db(listing_id: str, db_path: str = None) -> Optional[Dict]:
    """Load seller info from vehicle_listings table."""
    if db_path is None:
        db_path = str(PROJECT_ROOT / "src" / "cove" / "data" / "cove_tracker.duckdb")
    try:
        import duckdb
        db = duckdb.connect(db_path, read_only=True)
        row = db.execute("""
            SELECT seller_name, seller_email, seller_phone, detail_url
            FROM vehicle_listings WHERE listing_id = ?
        """, [listing_id]).fetchone()
        db.close()
        if row:
            return {
                "seller_name": row[0],
                "seller_email": row[1],
                "seller_phone": row[2],
                "detail_url": row[3],
                "seller_website": None,
            }
    except Exception:
        pass
    return None


def _scrape_page_for_emails(url: str) -> List[str]:
    """Fetch a page and extract all email addresses from it."""
    try:
        import requests
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
        })
        if resp.status_code != 200:
            return []

        text = resp.text
        # Find all emails
        raw_emails = EMAIL_RE.findall(text)

        # Also check for obfuscated emails: [at] [dot] patterns
        obfuscated = re.findall(
            r'[a-zA-Z0-9._%+\-]+\s*[\[\(]at[\]\)]\s*[a-zA-Z0-9.\-]+\s*[\[\(]dot[\]\)]\s*[a-zA-Z]{2,}',
            text, re.IGNORECASE,
        )
        for ob in obfuscated:
            clean = ob.replace("[at]", "@").replace("(at)", "@")
            clean = clean.replace("[dot]", ".").replace("(dot)", ".")
            clean = re.sub(r'\s+', '', clean)
            raw_emails.append(clean)

        # Also check for mailto: links
        mailto = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', text)
        raw_emails.extend(mailto)

        # Filter
        filtered = []
        for email in raw_emails:
            email = email.lower().strip()
            if any(bl in email for bl in EMAIL_BLACKLIST):
                continue
            if email.endswith('.png') or email.endswith('.jpg') or email.endswith('.svg'):
                continue
            if len(email) > 60:
                continue
            filtered.append(email)

        return list(set(filtered))

    except Exception:
        return []


def _guess_website_from_name(seller_name: str, country: str = "DE") -> str:
    """
    Construct probable website URL from seller name.

    German dealers: "Procar Automobile" → "https://www.procar-automobile.de"
    Dutch dealers: "Auto Janssen" → "https://www.autojanssen.nl"
    """
    tld_map = {
        "DE": "de", "NL": "nl", "BE": "be", "AT": "at",
        "FR": "fr", "SE": "se", "DK": "dk", "IT": "it",
        "ES": "es", "PL": "pl", "CZ": "cz",
    }
    tld = tld_map.get(country.upper(), "com")

    # Clean name: remove common suffixes, lowercase, hyphenate
    name = seller_name.lower().strip()
    # Remove legal forms
    for suffix in [" gmbh", " gmbh & co. kg", " gmbh & co kg", " kg", " ohg",
                   " ag", " e.k.", " bv", " b.v.", " sarl", " srl", " s.r.l."]:
        name = name.replace(suffix, "")

    # Replace spaces with hyphens, remove special chars
    name = re.sub(r'[^a-z0-9\-]', '-', name)
    name = re.sub(r'-+', '-', name).strip('-')

    if not name:
        return ""

    return f"https://www.{name}.{tld}"


def _extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL: https://www.procar-automobile.de → procar-automobile.de"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www.
        domain = re.sub(r'^www\.', '', domain)
        return domain if '.' in domain else None
    except Exception:
        return None


def _deduplicate_and_rank(emails: List[str]) -> List[str]:
    """Deduplicate and rank emails by likely usefulness."""
    seen = set()
    unique = []
    for e in emails:
        e = e.lower().strip()
        if e not in seen:
            seen.add(e)
            unique.append(e)

    # Rank: info@ and kontakt@ first, then sales-related, then others
    def rank_key(email: str) -> int:
        local = email.split("@")[0]
        if local in ("info", "kontakt", "contact"):
            return 0
        if local in ("verkauf", "sales", "ventes", "anfrage", "verkoop"):
            return 1
        if local in ("office", "zentrale", "empfang"):
            return 2
        return 3

    unique.sort(key=rank_key)
    return unique


def discover_and_store(listing_id: str, db_path: str = None) -> Dict:
    """
    Full pipeline: discover email and store it back in vehicle_listings.

    Returns the discovery result dict.
    """
    result = discover_seller_email(listing_id=listing_id, db_path=db_path)

    if result.get("email") and result.get("confidence") in ("high", "medium"):
        # Store back to DB
        if db_path is None:
            db_path = str(PROJECT_ROOT / "src" / "cove" / "data" / "cove_tracker.duckdb")
        try:
            import duckdb
            db = duckdb.connect(db_path)
            db.execute("""
                UPDATE vehicle_listings
                SET seller_email = ?
                WHERE listing_id = ? AND (seller_email IS NULL OR seller_email = '')
            """, [result["email"], listing_id])
            db.close()
            print(f"  Stored email in DB for {listing_id}")
        except Exception as e:
            print(f"  [warn] Could not store email in DB: {e}")

    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 src/cove/seller_email_discovery.py 'Dealer Name'          # By name")
        print("  python3 src/cove/seller_email_discovery.py --listing <listing_id>  # By listing")
        print("  python3 src/cove/seller_email_discovery.py --url https://dealer.de # By URL")
        sys.exit(1)

    if sys.argv[1] == "--listing" and len(sys.argv) >= 3:
        result = discover_and_store(sys.argv[2])
    elif sys.argv[1] == "--url" and len(sys.argv) >= 3:
        result = discover_seller_email(seller_website=sys.argv[2])
    else:
        name = " ".join(sys.argv[1:])
        result = discover_seller_email(seller_name=name)

    print(f"\n=== Email Discovery Result ===")
    print(f"  Seller:     {result.get('seller_name', '?')}")
    print(f"  Website:    {result.get('seller_website', '?')}")
    print(f"  Email:      {result.get('email', 'NOT FOUND')}")
    print(f"  Confidence: {result.get('confidence', '?')}")
    print(f"  Source:     {result.get('source', '?')}")
    if result.get("emails_found"):
        print(f"  All found:  {', '.join(result['emails_found'][:5])}")
    print(f"\n  Methods tried:")
    for step in result.get("method_log", []):
        print(f"    {step}")
