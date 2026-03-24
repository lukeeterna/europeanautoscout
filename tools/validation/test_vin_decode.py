"""
test_vin_decode.py — ARGOS Automotive Phase 01 Plan 02
Tests three free VIN/vehicle lookup tools against real VINs from test_vins.json.

Tools tested:
  A. freevindecoder.eu — VIN decode (make, model, year, engine, fuel, country)
  B. NHTSA API (vpic.nhtsa.dot.gov) — VIN decode + recall lookup
  C. DAT consumer portal (dat.de/gebrauchtfahrzeugwerte) — used vehicle value estimate

Usage: python3 tools/validation/test_vin_decode.py
Output: tools/validation/results/vin_decode_results.json
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "vin_decode_results.json")
VINS_FILE = os.path.join(os.path.dirname(__file__), "test_vins.json")

SESSION_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    "Connection": "keep-alive",
}

REQUEST_TIMEOUT = 15  # seconds
INTER_CALL_SLEEP = 1.5  # seconds between tool calls


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    print(msg, flush=True)


def _make_result(tool: str, vin: str, http_status: int, fields_returned: list,
                 sample_value: dict, claims_verified: bool, integration_path: str,
                 cost: str, notes: str) -> dict:
    return {
        "tool": tool,
        "vin": vin,
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "http_status": http_status,
        "fields_returned": fields_returned,
        "sample_value": sample_value,
        "claims_verified": claims_verified,
        "integration_path": integration_path,
        "cost": "€0",
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Tool A: freevindecoder.eu
# ---------------------------------------------------------------------------

def test_freevindecoder(vin: str, make: str, model: str, year: int) -> dict:
    """
    Tests freevindecoder.eu for a single VIN.

    Discovery findings:
    - /api endpoint always returns HTTP 404 (API not publicly accessible)
    - Direct GET /?vin=VIN returns the homepage HTML with no embedded decode data
      (results are rendered by Vue.js after a POST to /search)
    - Correct flow: GET /?vin=VIN to extract CSRF _token, then POST to /search
      which redirects to /VIN containing the actual server-rendered decode table
    - Table uses <td class="info-left">key</td><td class="info-right">value</td>
    - Returns manufacturer info (6 fields) — NOT full VIN decode (no model/year/engine)
    """
    tool = "freevindecoder"

    # --- Step 1: Fetch CSRF token from homepage ---
    home_url = f"https://www.freevindecoder.eu/?vin={vin}"
    try:
        session = requests.Session()
        resp = session.get(home_url, headers=SESSION_HEADERS, timeout=REQUEST_TIMEOUT)
        status = resp.status_code
        _log(f"  [freevindecoder] Token fetch → HTTP {status}")
        if status != 200:
            return _make_result(
                tool, vin, status, [], {}, False,
                "GET https://www.freevindecoder.eu/?vin=VIN (token fetch)",
                "€0",
                f"Homepage returned HTTP {status} — cannot proceed",
            )

        token_match = re.search(
            r'_token[^>]*value=["\']([A-Za-z0-9_/=+]+)["\']', resp.text
        )
        token = token_match.group(1) if token_match else ""
        if not token:
            return _make_result(
                tool, vin, status, [], {}, False,
                "GET https://www.freevindecoder.eu/?vin=VIN",
                "€0",
                "CSRF token not found in homepage — site structure may have changed",
            )
        _log(f"  [freevindecoder] CSRF token extracted (len={len(token)})")
    except requests.RequestException as exc:
        _log(f"  [freevindecoder] Token fetch error: {exc}")
        return _make_result(
            tool, vin, 0, [], {}, False,
            "GET https://www.freevindecoder.eu/?vin=VIN",
            "€0",
            f"Connection error during token fetch: {exc}",
        )

    time.sleep(INTER_CALL_SLEEP)

    # --- Step 2: POST to /search with CSRF token ---
    post_url = "https://www.freevindecoder.eu/search"
    post_headers = {
        **SESSION_HEADERS,
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": home_url,
        "Origin": "https://www.freevindecoder.eu",
    }
    try:
        resp2 = session.post(
            post_url,
            data={"_token": token, "vin": vin},
            headers=post_headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        status = resp2.status_code
        _log(f"  [freevindecoder] POST /search → HTTP {status} → {resp2.url}")

        if status == 200:
            html = resp2.text

            # Check for block / CAPTCHA
            blocked = (
                "captcha" in html.lower()
                or "access denied" in html.lower()
                or "rate limit" in html.lower()
            )
            if blocked:
                _log("  [freevindecoder] BLOCKED (CAPTCHA/rate-limit)")
                return _make_result(
                    tool, vin, status, [], {}, False,
                    "POST https://www.freevindecoder.eu/search",
                    "€0",
                    "BLOCKED — CAPTCHA or rate-limit in response",
                )

            # Extract key-value pairs: <td class="info-left">k</td><td class="info-right">v</td>
            pairs = re.findall(
                r'<td class="info-left">(.*?)</td>\s*<td class="info-right">(.*?)</td>',
                html,
                re.DOTALL,
            )
            fields = []
            sample = {}
            for raw_label, raw_value in pairs:
                label = re.sub(r'<[^>]+>', '', raw_label).strip()
                value = re.sub(r'<[^>]+>', '', raw_value).strip()
                if not value or value.lower() in ("n/a", "-", ""):
                    continue
                key = label.lower().replace(" ", "_")
                if key not in fields:
                    fields.append(key)
                sample[key] = value

            claims_verified = len(fields) >= 3
            _log(
                f"  [freevindecoder] VIN {vin[:8]}... → "
                f"{len(fields)} fields — {'PASS' if claims_verified else 'PARTIAL (manufacturer only)'}"
            )

            # Assess what was actually returned vs claimed
            has_full_decode = any(
                k in fields for k in ["model", "year", "engine", "fuel_type", "body"]
            )
            notes = (
                f"POST→redirect flow works. {len(fields)} fields returned. "
                f"Full decode (model/year/engine): {'YES' if has_full_decode else 'NO — manufacturer info only'}. "
                f"Final URL: {resp2.url}"
            )

            return _make_result(
                tool, vin, status, fields, sample, claims_verified,
                "POST https://www.freevindecoder.eu/search (with CSRF token) → redirect to /VIN",
                "€0",
                notes,
            )

        else:
            return _make_result(
                tool, vin, status, [], {}, False,
                "POST https://www.freevindecoder.eu/search",
                "€0",
                f"POST returned HTTP {status}",
            )
    except requests.RequestException as exc:
        _log(f"  [freevindecoder] POST error: {exc}")
        return _make_result(
            tool, vin, 0, [], {}, False,
            "POST https://www.freevindecoder.eu/search",
            "€0",
            f"Connection error during POST: {exc}",
        )


# ---------------------------------------------------------------------------
# Tool B: NHTSA API
# ---------------------------------------------------------------------------

def test_nhtsa(vin: str, make: str, model: str, year: int) -> dict:
    """
    Tests NHTSA public API for VIN decode + recall lookup.
    Endpoint 1: VIN decode (vpic.nhtsa.dot.gov)
    Endpoint 2: Recall lookup by make/model/year (api.nhtsa.gov)
    """
    tool = "nhtsa"
    fields_returned = []
    sample_value = {}
    notes_parts = []
    final_status = 0

    # --- Endpoint 1: VIN Decode ---
    decode_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    _log(f"  [nhtsa] VIN decode → {decode_url[:70]}...")
    try:
        resp = requests.get(
            decode_url,
            headers={**SESSION_HEADERS, "Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        status = resp.status_code
        final_status = status
        _log(f"  [nhtsa] VIN decode → HTTP {status}")

        if status == 200:
            data = resp.json()
            results = data.get("Results", [{}])
            if results:
                veh = results[0]
                # Fields of interest to ARGOS
                interest = [
                    "Make", "Model", "ModelYear", "FuelTypePrimary", "EngineModel",
                    "DisplacementL", "Cylinders", "BodyClass", "DriveType",
                    "TransmissionStyle", "PlantCountry", "VehicleType",
                    "EngineHP", "GVWR", "ErrorCode", "ErrorText",
                ]
                for field in interest:
                    val = veh.get(field, "")
                    if val and val.strip() not in ("", "0", "Not Applicable"):
                        fields_returned.append(field.lower())
                        sample_value[field.lower()] = val.strip()

                error_code = veh.get("ErrorCode", "")
                error_text = veh.get("ErrorText", "")
                error_text_short = repr(error_text[:80])
                notes_parts.append(
                    f"VIN decode: {len(fields_returned)} fields. "
                    f"ErrorCode={error_code!r}. ErrorText={error_text_short}"
                )
    except requests.RequestException as exc:
        _log(f"  [nhtsa] VIN decode request error: {exc}")
        notes_parts.append(f"VIN decode failed: {exc}")

    time.sleep(INTER_CALL_SLEEP)

    # --- Endpoint 2: Recall Lookup ---
    recall_url = (
        f"https://api.nhtsa.gov/recalls/recallsByVehicle"
        f"?make={make}&model={model}&modelYear={year}"
    )
    _log(f"  [nhtsa] Recall lookup → {recall_url[:80]}...")
    try:
        resp2 = requests.get(
            recall_url,
            headers={**SESSION_HEADERS, "Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        status2 = resp2.status_code
        if final_status == 0:
            final_status = status2
        _log(f"  [nhtsa] Recall lookup → HTTP {status2}")

        if status2 == 200:
            data2 = resp2.json()
            results2 = data2.get("results", data2.get("Results", []))
            recall_count = len(results2)
            open_recalls = [r for r in results2 if not r.get("Consequence", "")]
            notes_parts.append(
                f"Recall lookup: {recall_count} recalls found for {make} {model} {year}"
            )
            if recall_count > 0:
                # Include a sample recall
                sample_recall = results2[0]
                sample_value["recall_count"] = recall_count
                sample_value["recall_sample_component"] = sample_recall.get("Component", "")
                sample_value["recall_sample_summary"] = sample_recall.get("Summary", "")[:100]
                if "recall_count" not in fields_returned:
                    fields_returned.append("recall_count")
            else:
                notes_parts.append("No recalls found (may be normal for this make/model/year)")
        else:
            notes_parts.append(f"Recall endpoint HTTP {status2}")
    except requests.RequestException as exc:
        _log(f"  [nhtsa] Recall request error: {exc}")
        notes_parts.append(f"Recall lookup failed: {exc}")

    claims_verified = len(fields_returned) >= 3
    _log(
        f"  [nhtsa] VIN {vin[:8]}... → "
        f"{len(fields_returned)} fields — {'PASS' if claims_verified else 'FAIL'}"
    )

    return _make_result(
        tool, vin, final_status, fields_returned, sample_value, claims_verified,
        "GET https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/VIN?format=json",
        "€0",
        " | ".join(notes_parts),
    )


# ---------------------------------------------------------------------------
# Tool C: DAT consumer portal
# ---------------------------------------------------------------------------

def test_dat_consumer(make: str = "BMW", model: str = "X3",
                      year: int = 2022, km: int = 50000) -> dict:
    """
    Tests DAT consumer portal (dat.de/gebrauchtfahrzeugwerte).
    NOT VIN-based — uses make/model/year/km.
    Documents whether it's accessible, requires login/CAPTCHA, or can be queried.

    Discovery findings:
    - Portal loads (HTTP 200), page title: 'Was ist mein Auto wert? Kostenloser Gebrauchtfahrzeugwert'
    - The valuation wizard is JavaScript-rendered (React/embedded config, ~524KB HTML)
    - No static HTML form — form inputs are dynamically injected by JS
    - A login button exists in the nav header (optional, not required for the consumer form)
    - The form fields config is embedded as JSON in a <script> tag (i18n strings visible)
    - No direct POST endpoint is accessible without JS execution
    - Conclusion: REQUIRES BROWSER (Playwright) to query — not HTTP-scrape-able
    """
    tool = "dat"
    # DAT does not take a VIN — use a placeholder
    vin = f"DAT_QUERY_{make}_{model}_{year}"
    portal_url = "https://www.dat.de/gebrauchtfahrzeugwerte"

    _log(f"  [dat] Portal check → {portal_url}")
    try:
        resp = requests.get(
            portal_url,
            headers={**SESSION_HEADERS, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
            timeout=REQUEST_TIMEOUT,
        )
        status = resp.status_code
        _log(f"  [dat] Portal → HTTP {status}")

        if status == 200:
            html = resp.text

            # Page metadata
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            page_title = title_match.group(1).strip() if title_match else "unknown"

            # Assess page characteristics
            has_static_form = bool(re.findall(r'<form[^>]+action=', html, re.IGNORECASE))
            has_static_inputs = bool(re.findall(r'<input[^>]+name=["\'][^"\']+["\']', html, re.IGNORECASE))
            has_js_config = bool(re.search(r'vehicleBrandQuestion|vehicleTypeQuestion', html))
            is_js_rendered = (
                bool(re.search(r'(react|angular|vue|webpack|__next)', html, re.IGNORECASE))
                and not has_static_inputs
            )
            has_nav_login = bool(
                re.search(r'class=["\'][^"\']*login[^"\']*["\']', html, re.IGNORECASE)
            )
            has_captcha = bool(re.search(r'captcha|recaptcha', html, re.IGNORECASE))

            # Form requires browser execution — not directly queryable via HTTP POST
            # The valuation data is served via JS fetch to an internal API
            # Login is optional (nav button) — the consumer form itself appears free
            login_gate = has_nav_login and not has_static_form  # nav login ≠ form gate

            fields = ["page_accessible"]
            sample: dict = {
                "page_accessible": True,
                "page_title": page_title,
                "has_static_form": has_static_form,
                "has_static_inputs": has_static_inputs,
                "has_js_config": has_js_config,
                "is_js_rendered": is_js_rendered,
                "has_nav_login_button": has_nav_login,
                "has_captcha": has_captcha,
                "html_size_bytes": len(html),
                "query_make": make, "query_model": model,
                "query_year": year, "query_km": km,
            }
            if has_js_config:
                fields.append("form_config_embedded")

            # Conclusion
            # The portal is FREE (Kostenloser Gebrauchtfahrzeugwert = free used car value)
            # but requires Playwright/browser to interact with the React wizard
            # Direct HTTP scrape returns only the shell page with embedded JS config
            notes = (
                f"Page title: {page_title!r}. "
                f"Page loads HTTP 200, size={len(html):,} bytes. "
                f"JS-rendered React wizard — form fields not in static HTML. "
                f"Form config (vehicleBrandQuestion etc.) found in embedded script. "
                f"Nav login button present but is OPTIONAL (consumer form is free). "
                f"VERDICT: NOT HTTP-scrape-able. Requires Playwright browser automation "
                f"to interact with wizard and extract Orientierungswert. "
                f"No CAPTCHA detected. Integration path: Playwright → fill wizard → "
                f"extract price from rendered DOM."
            )

            claims_verified = False  # Cannot scrape via HTTP — browser required
            _log(
                f"  [dat] {make} {model} {year} — "
                f"HTTP 200 accessible but JS-only wizard — "
                f"BLOCKED for HTTP scrape (browser required)"
            )
            return _make_result(
                tool, vin, status, fields, sample, claims_verified,
                "GET https://www.dat.de/gebrauchtfahrzeugwerte (HTTP only — JS wizard not executable)",
                "€0",
                notes,
            )

        else:
            return _make_result(
                tool, vin, status, [], {}, False,
                portal_url, "€0",
                f"Portal returned HTTP {status} — inaccessible",
            )

    except requests.RequestException as exc:
        _log(f"  [dat] Request error: {exc}")
        return _make_result(
            tool, vin, 0, [], {}, False,
            portal_url, "€0",
            f"Connection error: {exc}",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load VINs
    if not os.path.exists(VINS_FILE):
        _log(f"ERROR: {VINS_FILE} not found — run vin_fetcher.py first (Plan 01)")
        sys.exit(1)

    with open(VINS_FILE, "r") as f:
        vins_data = json.load(f)

    vins = vins_data.get("vins", [])
    _log(f"Loaded {len(vins)} VINs from test_vins.json")
    _log("=" * 60)

    results = []
    total_tests = 0
    passed_tests = 0

    for entry in vins:
        vin = entry["vin"]
        make = entry["make"]
        model = entry["model"]
        year = entry["year"]
        listing_id = entry["listing_id"]

        _log(f"\nVIN: {vin}  ({make} {model} {year})  listing: {listing_id}")
        _log("-" * 50)

        # Tool A: freevindecoder.eu
        _log("Testing Tool A: freevindecoder.eu")
        r_free = test_freevindecoder(vin, make, model, year)
        r_free["listing_id"] = listing_id
        results.append(r_free)
        total_tests += 1
        if r_free["claims_verified"]:
            passed_tests += 1
        _log(
            f"[freevindecoder] VIN {vin[:8]}... HTTP:{r_free['http_status']} "
            f"fields:{len(r_free['fields_returned'])} pass:{r_free['claims_verified']}"
        )
        time.sleep(INTER_CALL_SLEEP)

        # Tool B: NHTSA API
        _log("Testing Tool B: NHTSA API")
        r_nhtsa = test_nhtsa(vin, make, model, year)
        r_nhtsa["listing_id"] = listing_id
        results.append(r_nhtsa)
        total_tests += 1
        if r_nhtsa["claims_verified"]:
            passed_tests += 1
        _log(
            f"[nhtsa] VIN {vin[:8]}... HTTP:{r_nhtsa['http_status']} "
            f"fields:{len(r_nhtsa['fields_returned'])} pass:{r_nhtsa['claims_verified']}"
        )
        time.sleep(INTER_CALL_SLEEP)

    # Tool C: DAT consumer portal (NOT per-VIN — test once with BMW X3 2022)
    _log("\nTesting Tool C: DAT consumer portal (make/model/year — not VIN-based)")
    r_dat = test_dat_consumer(make="BMW", model="X3", year=2022, km=50000)
    r_dat["listing_id"] = "dat_query_bmw_x3_2022"
    results.append(r_dat)
    total_tests += 1
    if r_dat["claims_verified"]:
        passed_tests += 1
    _log(
        f"[dat] HTTP:{r_dat['http_status']} "
        f"fields:{len(r_dat['fields_returned'])} pass:{r_dat['claims_verified']}"
    )

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    _log("\n" + "=" * 60)
    _log(f"DONE — {total_tests} tests, {passed_tests} passed")
    _log(f"Results saved to: {RESULTS_FILE}")
    _log("=" * 60)

    # Summary table
    _log("\nSummary:")
    for r in results:
        _log(
            f"  {r['tool']:20s} VIN:{r['vin'][:8]}... "
            f"HTTP:{r['http_status']} "
            f"fields:{len(r.get('fields_returned', []))} "
            f"pass:{r['claims_verified']}"
        )


if __name__ == "__main__":
    main()
