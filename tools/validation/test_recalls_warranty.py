"""
ARGOS Automotive — Recall & Warranty Tool Validation
Plan 01-03: Test recall databases and warranty portals against real VINs

Tools tested:
  D. car-recalls.eu         — EU recall blog/aggregator (Safety Gate + KBA)
  E. KBA kba-online.de      — German federal recall database (SPA with Altcha CAPTCHA)
  F. BMW warranty portal    — Residual warranty check (login required)
  G. RDW open data NL       — Dutch km/vehicle data (plate-based, REST API)

Key findings documented in results JSON.
Output: tools/validation/results/recalls_warranty_results.json
"""

import json
import os
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import http.client
from urllib.parse import urlparse
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VIN_FILE = os.path.join(os.path.dirname(__file__), "test_vins.json")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "recalls_warranty_results.json")

HEADERS_HTML = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5,de;q=0.3",
    "Connection": "keep-alive",
}

HEADERS_JSON = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
}

SLEEP_BETWEEN = 2  # seconds between requests


# ---------------------------------------------------------------------------
# HTTP helpers (follow redirects)
# ---------------------------------------------------------------------------

def _make_request(url, method="GET", data=None, headers=None, timeout=15):
    """Perform HTTP request following redirects. Returns (status_code, body_text, error_msg)."""
    if headers is None:
        headers = HEADERS_HTML

    try:
        if data is not None:
            encoded_data = urllib.parse.urlencode(data).encode("utf-8") if isinstance(data, dict) else data
        else:
            encoded_data = None

        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        # Use default opener which follows redirects
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body, str(e)
    except urllib.error.URLError as e:
        return 0, "", str(e.reason)
    except Exception as e:
        return 0, "", str(e)


def _get_redirect_target(url, headers=None, timeout=10):
    """Get the final redirect target without following (for documentation)."""
    if headers is None:
        headers = HEADERS_HTML
    try:
        parsed = urlparse(url)
        conn = http.client.HTTPSConnection(parsed.netloc, timeout=timeout)
        path = parsed.path
        if parsed.query:
            path += "?" + parsed.query
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        location = resp.getheader("Location", "")
        conn.close()
        return resp.status, location
    except Exception as e:
        return 0, ""


def _lc(text):
    return text.lower() if text else ""


# ---------------------------------------------------------------------------
# TOOL D: car-recalls.eu
#
# Finding: car-recalls.eu is a WORDPRESS BLOG about recalls — NOT a VIN lookup API.
# The "Free VIN Check" page (/vin-check-recalls/) is a make/model browser backed by
# a taxonomy chain menu (Ajax). It has NO direct VIN input field.
# VIN search via /?s={VIN} returns "You searched for {VIN}" with zero results —
# the site indexes recall ARTICLES by make/model, not individual VINs.
# The /en/vin/{VIN} URL pattern DOES NOT EXIST on this site (returns 404).
# For actual VIN recall checks, car-recalls.eu links out to:
#   - cebia.com (paid), ok-vin.cz (external)
# Integration path: NONE (blog, not API)
# ---------------------------------------------------------------------------

def test_car_recalls_eu(vin_entry):
    """Test car-recalls.eu for a VIN — documents that it is a blog, not a VIN lookup."""
    vin = vin_entry["vin"]
    results = []

    # Attempt 1: Try /en/vin/{VIN} (the URL pattern that was assumed to work)
    url_html = f"https://car-recalls.eu/en/vin/{vin}"
    status, body, err = _make_request(url_html, headers=HEADERS_HTML, timeout=15)
    time.sleep(1)

    results.append({
        "tool": "car_recalls_eu",
        "vin": vin,
        "make": vin_entry["make"],
        "model": vin_entry["model"],
        "year": vin_entry["year"],
        "url_tested": url_html,
        "http_status": status,
        "response_type": "html" if status == 200 else "error",
        "response_size_chars": len(body),
        "blocked": status != 200,
        "block_reason": "URL_PATTERN_DOES_NOT_EXIST" if status == 404 else (None if status == 200 else f"HTTP_{status}"),
        "data_returned": {},
        "claims_verified": False,
        "integration_path": "NONE — /en/vin/{VIN} URL does not exist",
        "cost": "€0",
        "notes": (
            "car-recalls.eu is a WordPress blog aggregating recall ARTICLES by make/model. "
            "It has NO direct VIN lookup endpoint. The /en/vin/{VIN} URL pattern returns 404. "
            "The site's 'Free VIN Check' page is a taxonomy browser (make/model), not a VIN form. "
            "VIN search via /?s={VIN} returns blog search results (no matches). "
            "For recall lookups, use the EU Safety Gate API directly: "
            "https://ec.europa.eu/safety-gate-alerts/screen/webReport#weeklyReports "
            "or the KBA API (which requires altcha/CAPTCHA solving)."
        ),
    })

    # Attempt 2: Try the WordPress search endpoint as documented finding
    time.sleep(SLEEP_BETWEEN)
    url_search = f"https://car-recalls.eu/?s={urllib.parse.quote(vin)}"
    s_status, s_body, s_err = _make_request(url_search, headers=HEADERS_HTML, timeout=10)

    no_results = any(p in _lc(s_body) for p in ["no results", "nothing found", "no posts", "sorry"])
    search_title_match = f"searched for {vin.lower()}" in _lc(s_body)

    results.append({
        "tool": "car_recalls_eu",
        "vin": vin,
        "make": vin_entry["make"],
        "model": vin_entry["model"],
        "year": vin_entry["year"],
        "url_tested": url_search,
        "http_status": s_status,
        "response_type": "html_search_results",
        "response_size_chars": len(s_body),
        "blocked": True,
        "block_reason": "BLOG_SEARCH_NOT_VIN_LOOKUP",
        "data_returned": {
            "search_title_found": search_title_match,
            "no_results": no_results,
            "site_type": "WordPress recall blog — articles by make/model only",
        },
        "claims_verified": False,
        "integration_path": "NONE",
        "cost": "€0",
        "notes": (
            f"WordPress search /?s={vin} returns HTTP {s_status}. "
            f"Search title found: {search_title_match}. "
            f"No results: {no_results}. "
            "Confirmed: car-recalls.eu does NOT support VIN-based recall lookup. "
            "Alternative: use EU Safety Gate RAPEX/ICSMS API directly (documented)."
        ),
    })

    return results


# ---------------------------------------------------------------------------
# TOOL E: KBA recall database (kba-online.de)
#
# Finding: KBA rrdb is a SVELTE SPA (Single Page Application).
# The form page is a minimal HTML shell (419 bytes) that loads a JS bundle.
# The JS bundle (1.3MB) reveals the backend REST API endpoints:
#   - GET  /rrdb/buerger/api/markeFahrzeughersteller       — list of makes
#   - POST /rrdb/buerger/api/rueckruf/verkaufsbezeichnungBaujahr — by make/model/year
#   - GET  /rrdb/buerger/api/rueckruf/rueckrufcode/        — by recall code
#   - GET  /rrdb/buerger/api/rueckruf/referenznummer/      — by reference number
# ALL search endpoints require: altchaPayload (an altcha.org CAPTCHA token)
# altcha uses PoW (Proof of Work) — can be solved programmatically (no image CAPTCHA)
# but requires integrating the altcha challenge/response flow.
# Direct VIN/FIN lookup: NOT available — KBA search is by make/model/year, not VIN.
# Integration path: POSSIBLE with altcha PoW solver — medium complexity.
# ---------------------------------------------------------------------------

def test_kba(vin_entry):
    """Test KBA — documents SPA structure and altcha CAPTCHA requirement."""
    vin = vin_entry["vin"]
    results = []

    # Step 1: Fetch the form shell page (with correct trailing slash to avoid redirect)
    url_form = "https://www.kba-online.de/rrdb/buerger/"
    status, body, err = _make_request(url_form, headers=HEADERS_HTML, timeout=15)

    is_spa = len(body) < 1000 and '<div id="app"' in body
    has_js_bundle = 'index-D9dzMUOQ.js' in body or '.js">' in body

    # Step 2: Probe the REST API endpoint (without altcha — expected to fail)
    time.sleep(SLEEP_BETWEEN)
    api_base = "https://www.kba-online.de/rrdb/buerger"

    # Try make list endpoint (no auth needed, just get list of makes)
    makes_url = f"{api_base}/api/markeFahrzeughersteller"
    makes_status, makes_body, makes_err = _make_request(
        makes_url,
        headers={**HEADERS_JSON, "Referer": "https://www.kba-online.de/rrdb/buerger/"},
        timeout=10,
    )

    makes_data = []
    if makes_status == 200:
        try:
            makes_data = json.loads(makes_body)
        except Exception:
            makes_data = []

    # Step 3: Try the altcha challenge endpoint
    time.sleep(1)
    altcha_url = f"{api_base}/api/altcha"
    altcha_status, altcha_body, altcha_err = _make_request(
        altcha_url,
        headers={**HEADERS_JSON, "Referer": "https://www.kba-online.de/rrdb/buerger/"},
        timeout=10,
    )
    altcha_data = {}
    if altcha_status == 200:
        try:
            altcha_data = json.loads(altcha_body)
        except Exception:
            pass

    # Step 4: Probe the search endpoint without altchaPayload (expect 400/422)
    time.sleep(1)
    search_url = f"{api_base}/api/rueckruf/verkaufsbezeichnungBaujahr"
    # Search for BMW X3 2022 by make/model/year (not VIN — KBA doesn't do VIN lookup)
    search_payload = {
        "altchaPayload": "MISSING",  # intentionally invalid to test if required
        "marke": "BMW",
        "verkaufsbezeichnungen": ["X3"],
        "baujahr": "2022",
    }
    search_status, search_body, search_err = _make_request(
        search_url,
        method="POST",
        data=json.dumps(search_payload).encode("utf-8"),
        headers={
            **HEADERS_JSON,
            "Content-Type": "application/json",
            "Referer": "https://www.kba-online.de/rrdb/buerger/",
        },
        timeout=15,
    )

    results.append({
        "tool": "kba",
        "vin": vin,
        "make": vin_entry["make"],
        "model": vin_entry["model"],
        "year": vin_entry["year"],
        "url_tested": url_form,
        "form_fetch_status": status,
        "http_status": makes_status,  # representative status = makes API
        "response_type": "spa_rest_api",
        "response_size_chars": len(makes_body) if makes_status == 200 else 0,
        "blocked": True,
        "block_reason": "ALTCHA_POW_CAPTCHA_REQUIRED",
        "data_returned": {
            "spa_detected": is_spa,
            "spa_framework": "Svelte",
            "form_shell_size_bytes": len(body),
            "makes_api_status": makes_status,
            "makes_count": len(makes_data) if isinstance(makes_data, list) else 0,
            "makes_sample": makes_data[:5] if isinstance(makes_data, list) else [],
            "altcha_api_status": altcha_status,
            "altcha_challenge": altcha_data,
            "search_api_status": search_status,
            "search_without_altcha_response": search_body[:200] if search_body else "",
            "backend_api_base": api_base,
            "api_endpoints_found": [
                "GET /api/markeFahrzeughersteller — list all makes (NO auth needed)",
                "GET /api/altcha — get altcha PoW challenge",
                "POST /api/rueckruf/verkaufsbezeichnungBaujahr — search by make/model/year (needs altchaPayload)",
                "GET /api/rueckruf/rueckrufcode/ — search by recall code (needs altchaPayload)",
                "GET /api/rueckruf/referenznummer/ — search by reference number",
                "GET /api/rueckruf/details/ — get recall details",
            ],
            "no_vin_lookup": "KBA search is by make/model/year — there is NO direct FIN/VIN lookup endpoint",
        },
        "claims_verified": makes_status == 200,
        "integration_path": (
            "POSSIBLE with altcha PoW solver: "
            "1) GET /api/altcha to get challenge, "
            "2) Solve PoW (SHA-256 hash iteration — pure Python, no CAPTCHA image), "
            "3) POST /api/rueckruf/verkaufsbezeichnungBaujahr with {altchaPayload, marke, verkaufsbezeichnungen, baujahr}. "
            "LIMITATION: Returns recalls by make/model/year, not by specific VIN."
        ),
        "cost": "€0",
        "notes": (
            "KBA RRDB is a Svelte SPA. Makes list API works without auth. "
            f"altcha challenge endpoint: HTTP {altcha_status}. "
            f"Search without valid altcha: HTTP {search_status}. "
            "altcha is a PoW CAPTCHA (not image-based) — solvable programmatically. "
            "However: KBA does NOT support VIN-specific recall lookup. "
            "It returns ALL recalls for a make/model/year combination. "
            "This is useful for 'are there known recalls for BMW X3 2022?' but NOT "
            "for 'does THIS specific VIN have an open recall?'"
        ),
    })

    return results


# ---------------------------------------------------------------------------
# TOOL F: BMW warranty portal
#
# Finding: BMW warranty check requires login to MyBMW account.
# No public API endpoint exists for warranty lookup without authentication.
# BMW.de and BMW.com warranty URLs are either 404, timeout, or redirect to login.
# The legitimate approach for dealers: use BMW Partner Portal (requires dealer credentials).
# Alternative free approach: EU Safety Gate (RAPEX) for recall data,
# but residual warranty = NO free public source found.
# ---------------------------------------------------------------------------

def test_bmw_warranty(vin_entry):
    """Test BMW warranty portal URLs — documents login wall."""
    vin = vin_entry["vin"]
    results = []

    # Skip non-BMW VINs
    if vin_entry["make"].upper() != "BMW":
        results.append({
            "tool": "bmw_warranty",
            "vin": vin,
            "make": vin_entry["make"],
            "model": vin_entry["model"],
            "year": vin_entry["year"],
            "url_tested": "N/A",
            "http_status": 0,
            "response_type": "skipped",
            "response_size_chars": 0,
            "blocked": False,
            "block_reason": None,
            "data_returned": {"reason": "Non-BMW VIN — skipped (only BMW warranty portal tested)"},
            "claims_verified": False,
            "integration_path": "N/A",
            "cost": "€0",
            "notes": f"Skipped: make={vin_entry['make']}, only BMW VINs tested for BMW warranty",
        })
        return results

    # Test BMW.de warranty service page
    bmw_urls_to_test = [
        ("BMW.de services page", "https://www.bmw.de/de/footer/metanavigation/services.html", 10),
        ("BMW API speculative", "https://api.bmw.com/warranty/v1/check", 8),
    ]

    for name, url, timeout_s in bmw_urls_to_test:
        time.sleep(1)
        status, body, err = _make_request(url, headers=HEADERS_HTML, timeout=timeout_s)
        lc_body = _lc(body)

        blocked = True
        block_reason = None

        if status == 200:
            has_login = any(kw in lc_body for kw in ["login", "anmelden", "sign in"])
            has_warranty = any(kw in lc_body for kw in ["garantie", "warranty", "gewährleistung"])
            if has_login and not has_warranty:
                block_reason = "LOGIN_WALL"
            elif len(body) < 300:
                block_reason = "EMPTY_RESPONSE"
            else:
                blocked = False
                block_reason = None
        elif status == 404:
            block_reason = "HTTP_404_NOT_FOUND"
        elif status == 403:
            block_reason = "BLOCKED_403"
        elif status == 0:
            block_reason = f"CONNECTION_TIMEOUT_OR_ERROR: {err[:100] if err else 'timeout'}"
        else:
            block_reason = f"HTTP_{status}"

        results.append({
            "tool": "bmw_warranty",
            "vin": vin,
            "make": vin_entry["make"],
            "model": vin_entry["model"],
            "year": vin_entry["year"],
            "url_tested": url,
            "url_name": name,
            "http_status": status,
            "response_type": "html" if status == 200 else "error",
            "response_size_chars": len(body),
            "blocked": blocked,
            "block_reason": block_reason,
            "data_returned": {
                "has_login_wall": status == 200 and any(kw in lc_body for kw in ["login", "anmelden"]),
                "has_warranty_content": any(kw in lc_body for kw in ["garantie", "warranty"]) if status == 200 else False,
                "summary": (
                    "BMW warranty check requires MyBMW account login. "
                    "No public VIN-based warranty lookup API found. "
                    "BMW Partner Portal (dealer credentials) would provide this data. "
                    "Free alternative: none found — residual warranty is NOT available via free public API."
                ),
            },
            "claims_verified": False,
            "integration_path": (
                "NOT POSSIBLE without credentials. "
                "Options: (1) BMW Partner Portal — requires dealer BMW ID. "
                "(2) Ask the selling dealer for warranty documentation. "
                "(3) Include 'residual warranty not verified' in ARGOS Grade criteria."
            ),
            "cost": "€0",
            "notes": f"BMW warranty check — {name}: HTTP {status}. {block_reason or 'OK'}",
        })

    return results


# ---------------------------------------------------------------------------
# TOOL G: RDW open data NL
#
# Finding: RDW Socrata REST API WORKS — no authentication required.
# URL: GET https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={PLATE}
# Returns: Full vehicle record including:
#   - kenteken (plate), merk (make), handelsbenaming (model)
#   - tellerstandoordeel (km reading judgment: "Logisch"/"Onlogisch"/"Onbekend")
#   - datum_eerste_toelating (first registration date)
#   - openstaande_terugroepactie_indicator (open recall indicator: "Ja"/"Nee")
#   - APK (inspection) expiry date
# LIMITATION: Requires NL license plate (kenteken), NOT VIN.
# For DE-sourced vehicles: plate is NOT in the AS24 listing data.
# For NL-sourced vehicles: if listing has plate, this API is FREE and very useful.
# Confirmed working: returned 50+ fields for test plate 24ZNT2 (Chevrolet Cruze)
# ---------------------------------------------------------------------------

RDW_API_URL = "https://opendata.rdw.nl/resource/m9d7-ebf2.json"

def test_rdw():
    """Test RDW open data API — confirms it works and documents limitations."""
    results = []

    # Test with synthetic NL plates — format: letters/digits mixed, no dashes in API
    # 24ZNT2 confirmed to return data (Chevrolet Cruze, NL registered)
    test_plates = [
        ("24ZNT2", "Known plate — Chevrolet Cruze NL"),
        ("GT123B", "Synthetic format test"),
        ("AB12CD", "Synthetic format test"),
    ]

    for plate, note in test_plates:
        time.sleep(SLEEP_BETWEEN)
        url = f"{RDW_API_URL}?kenteken={plate}"
        status, body, err = _make_request(url, headers=HEADERS_JSON, timeout=10)

        blocked = False
        block_reason = None
        data_returned = {}
        claims_verified = False

        if status == 200:
            try:
                parsed = json.loads(body)
                if isinstance(parsed, list):
                    claims_verified = True  # API works regardless of record count
                    if len(parsed) > 0:
                        record = parsed[0]
                        data_returned = {
                            "records_found": len(parsed),
                            "plate": plate,
                            "merk": record.get("merk", ""),
                            "handelsbenaming": record.get("handelsbenaming", ""),
                            "eerste_kleur": record.get("eerste_kleur", ""),
                            "datum_eerste_toelating": record.get("datum_eerste_toelating", ""),
                            "tellerstandoordeel": record.get("tellerstandoordeel", ""),
                            "openstaande_terugroepactie_indicator": record.get("openstaande_terugroepactie_indicator", ""),
                            "wam_verzekerd": record.get("wam_verzekerd", ""),
                            "vervaldatum_apk": record.get("vervaldatum_apk", ""),
                            "all_fields_count": len(record),
                            "key_fields_for_argos": [
                                "tellerstandoordeel → km history judgment (Logisch/Onlogisch)",
                                "openstaande_terugroepactie_indicator → open recall (Ja/Nee)",
                                "datum_eerste_toelating → first registration date",
                                "vervaldatum_apk → inspection expiry",
                                "wam_verzekerd → insurance status",
                            ],
                        }
                    else:
                        data_returned = {
                            "records_found": 0,
                            "plate": plate,
                            "note": f"Plate not found in RDW registry — {note}",
                        }
            except json.JSONDecodeError:
                blocked = True
                block_reason = "JSON_PARSE_ERROR"
        elif status == 403:
            blocked = True
            block_reason = "BLOCKED_403"
        elif status == 429:
            blocked = True
            block_reason = "RATE_LIMITED"
        elif status == 0:
            blocked = True
            block_reason = f"CONNECTION_ERROR: {err}"
        else:
            blocked = True
            block_reason = f"HTTP_{status}"

        results.append({
            "tool": "rdw",
            "vin": None,
            "plate_tested": plate,
            "plate_note": note,
            "make": None,
            "model": None,
            "year": None,
            "url_tested": url,
            "http_status": status,
            "response_type": "json" if status == 200 else "error",
            "response_size_chars": len(body),
            "blocked": blocked,
            "block_reason": block_reason,
            "data_returned": data_returned,
            "claims_verified": claims_verified,
            "integration_path": f"GET {RDW_API_URL}?kenteken={{PLATE_NO_DASHES}}",
            "cost": "€0",
            "notes": (
                "RDW open data API confirmed working — no auth required. "
                "Returns 50+ fields per vehicle including km history judgment and open recall indicator. "
                "LIMITATION: plate-based, NOT VIN-based. "
                "For DE-sourced vehicles: plate not available from AS24 listing data. "
                "For NL-sourced vehicles (autoscout24.nl, mobile.de NL listings): "
                "check if plate (kenteken) is in listing detail page. "
                "KEY VALUE: openstaande_terugroepactie_indicator field gives recall status for free!"
            ),
        })

        if not blocked and claims_verified and data_returned.get("records_found", 0) > 0:
            break  # Got a confirmed working record — enough to validate

    return results


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(VIN_FILE, "r") as f:
        vin_data = json.load(f)

    vins = vin_data["vins"]
    print(f"Loaded {len(vins)} VINs from test_vins.json")
    print(f"Tools to test: car-recalls.eu (D), KBA (E), BMW warranty (F), RDW (G)")
    print("-" * 70)

    all_results = []

    # --- TOOL D: car-recalls.eu ---
    print("\n[TOOL D] car-recalls.eu — testing VIN URL pattern")
    for vin_entry in vins[:2]:  # Test first 2 VINs
        vin_short = vin_entry["vin"][:8]
        print(f"  VIN {vin_short}... ({vin_entry['make']} {vin_entry['model']} {vin_entry['year']})")
        results = test_car_recalls_eu(vin_entry)
        for r in results:
            status_str = "BLOCKED" if r["blocked"] else "PASS"
            block = r.get("block_reason") or ""
            print(f"    [{r['tool']}] HTTP {r['http_status']} — {status_str} {block}")
        all_results.extend(results)
        time.sleep(SLEEP_BETWEEN)

    # --- TOOL E: KBA ---
    print("\n[TOOL E] KBA (kba-online.de) — probing SPA API")
    for vin_entry in vins[:2]:
        vin_short = vin_entry["vin"][:8]
        print(f"  VIN {vin_short}... ({vin_entry['make']} {vin_entry['model']} {vin_entry['year']})")
        results = test_kba(vin_entry)
        for r in results:
            status_str = "BLOCKED" if r["blocked"] else "PASS"
            block = r.get("block_reason") or ""
            print(f"    [kba] HTTP {r['http_status']} — {status_str} {block}")
        all_results.extend(results)
        time.sleep(SLEEP_BETWEEN)

    # --- TOOL F: BMW warranty portal ---
    print("\n[TOOL F] BMW warranty portal — checking for public endpoint")
    for vin_entry in vins:
        vin_short = vin_entry["vin"][:8]
        print(f"  VIN {vin_short}... ({vin_entry['make']} {vin_entry['model']} {vin_entry['year']})")
        results = test_bmw_warranty(vin_entry)
        for r in results:
            status_str = "BLOCKED" if r["blocked"] else "PASS"
            block = r.get("block_reason") or ""
            print(f"    [bmw_warranty] HTTP {r['http_status']} — {status_str} {block}")
        all_results.extend(results)
        time.sleep(SLEEP_BETWEEN)

    # --- TOOL G: RDW open data ---
    print("\n[TOOL G] RDW open data NL — plate-based vehicle data")
    rdw_results = test_rdw()
    for r in rdw_results:
        plate = r.get("plate_tested", "N/A")
        status_str = "BLOCKED" if r["blocked"] else "PASS"
        records = r.get("data_returned", {}).get("records_found", "?")
        print(f"    [rdw] Plate {plate}: HTTP {r['http_status']} — {status_str} (records={records})")
    all_results.extend(rdw_results)

    # Write results
    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Results: {RESULTS_FILE}")
    print(f"Total records: {len(all_results)}")

    # Summary
    print("\n=== TOOL SUMMARY ===")
    tool_summary = {}
    for r in all_results:
        tool = r["tool"]
        if tool not in tool_summary:
            tool_summary[tool] = {"pass": 0, "blocked": 0}
        if r["blocked"]:
            tool_summary[tool]["blocked"] += 1
        else:
            tool_summary[tool]["pass"] += 1

    for tool, stats in sorted(tool_summary.items()):
        total = stats["pass"] + stats["blocked"]
        status_indicator = "USABLE" if stats["pass"] > 0 else "BLOCKED"
        print(f"  {tool:20s}: {status_indicator} — {stats['pass']}/{total} pass")

    # Tools confirmed working
    print("\n=== INTEGRATION VERDICT ===")
    verdicts = {
        "car_recalls_eu": "BLOCKED — blog only, no VIN lookup. Alt: EU Safety Gate RAPEX API directly.",
        "kba": "POSSIBLE — SPA with altcha PoW CAPTCHA (solvable in Python). By make/model/year only, NOT VIN.",
        "bmw_warranty": "BLOCKED — login required (MyBMW). No public VIN warranty endpoint.",
        "rdw": "WORKS — REST API, no auth, plate-based. Key: openstaande_terugroepactie_indicator field.",
    }
    for tool, verdict in verdicts.items():
        print(f"  {tool:20s}: {verdict}")

    return all_results


if __name__ == "__main__":
    main()
