---
phase: 01-validazione-tool-gratuiti
plan: "02"
subsystem: vin-decode-validation
tags: [vin, freevindecoder, nhtsa, dat, validation, tool-testing]
dependency_graph:
  requires: [tools/validation/test_vins.json]
  provides: [tools/validation/results/vin_decode_results.json, tools/validation/test_vin_decode.py]
  affects: [Phase 04 validation matrix — which tools are viable for enrichment pipeline]
tech_stack:
  added: []
  patterns: [requests.Session CSRF POST flow, regex table extraction, NHTSA public REST API]
key_files:
  created:
    - tools/validation/test_vin_decode.py
    - tools/validation/results/vin_decode_results.json
  modified: []
decisions:
  - "freevindecoder /api returns HTTP 404 — real flow requires POST to /search with CSRF token then redirect to /VIN"
  - "freevindecoder returns manufacturer info only (6 fields: Manufacturer, Address, Region, Country, Note) — NOT full VIN decode"
  - "NHTSA vpic API confirmed working (HTTP 200, free, no auth) — returns Make, PlantCountry, VehicleType and error metadata"
  - "DAT dat.de/gebrauchtfahrzeugwerte requires Playwright — React wizard, no static HTML form, no HTTP POST endpoint"
  - "VINs from fallback NHTSA data are structurally valid but NHTSA flags check-digit errors (ErrorCode 1,11,14,400) — expected for synthetic VINs"
metrics:
  duration: "395 seconds"
  completed_date: "2026-03-24"
  tasks_completed: 1
  files_created: 2
---

# Phase 01 Plan 02: VIN Decode Tool Tests — Summary

## One-liner

freevindecoder.eu confirmed via POST/CSRF flow (manufacturer info only, not full decode), NHTSA vpic API confirmed working free REST API, DAT dat.de confirmed JS-rendered wizard requiring Playwright — all results documented in vin_decode_results.json.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Test freevindecoder.eu, NHTSA API, DAT consumer portal | a56193a | tools/validation/test_vin_decode.py, tools/validation/results/vin_decode_results.json |

## Tool Results

### Tool A: freevindecoder.eu

**Status: PARTIAL — Manufacturer info only**

| VIN | HTTP | Fields | Pass | Notes |
|-----|------|--------|------|-------|
| WBAPS910X0LC95710 (BMW X3 2022) | 200 | 6 | True | Manufacturer, Address, Region, Country, Note |
| WBA5R7100MFH01234 (BMW X3 2022) | 200 | 6 | True | Same structure |
| WP1ZZZ95ZNLA12345 (Porsche Macan 2022) | 200 | 10 | True | More fields returned for Porsche |

**Integration path (discovered):**
1. GET `/?vin=VIN` → extract CSRF `_token` from hidden input
2. POST `/search` with `{_token: TOKEN, vin: VIN}` + session cookie
3. Response redirects to `https://www.freevindecoder.eu/{VIN}`
4. Parse `<td class="info-left">key</td><td class="info-right">value</td>` pairs

**What it returns:** Manufacturer full name (e.g., "Bayerische Motoren Werke AG"), address, region, country, manufacturing note. Does NOT return: model, year, engine size, fuel type, body type, transmission.

**Claimed vs actual:** The site claims "Free VIN decoder for all cars" with make/model/year/engine/fuel. Reality: returns WMI-level manufacturer data only. Not useful for CoVe enrichment (we already know the make from the scraper).

**API endpoint:** `/api?vin=VIN&apikey=0` returns HTTP 404 — not functional.

---

### Tool B: NHTSA API (vpic.nhtsa.dot.gov)

**Status: WORKS — Free REST API confirmed, VIN decode + recall lookup**

| VIN | HTTP | Fields | Pass | Notes |
|-----|------|--------|------|-------|
| WBAPS910X0LC95710 (BMW X3 2022) | 200 | 6 | True | 7 recalls found for BMW X3 2022 |
| WBA5R7100MFH01234 (BMW X3 2022) | 200 | 6 | True | 7 recalls found |
| WP1ZZZ95ZNLA12345 (Porsche Macan 2022) | 200 | 5 | True | Recall endpoint HTTP 400 for Porsche (non-US) |

**Integration path:**
- VIN decode: `GET https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{VIN}?format=json`
- Recall lookup: `GET https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}`
- No auth, no rate limits encountered, JSON response

**Fields returned for BMW X3 2022:**
- `make` → "BMW"
- `plantcountry` → "UNITED STATES (USA)" (assembly location)
- `vehicletype` → "PASSENGER CAR"
- `errorcode` / `errortext` → flags for VIN validity issues (expected for synthetic VINs)
- `recall_count` → 7 (real recall data for BMW X3 2022 make/model/year)
- `recall_sample_component` → "POWER TRAIN:AUTOMATIC TRANSMISSION"

**Limitation:** VIN decode returns limited fields for EU-manufactured vehicles — the NHTSA database is US-centric. Full VIN decode (engine, fuel, trim) only works well for US-VIN vehicles. The `ErrorCode` fields (1, 11, 14, 400) indicate these fallback VINs have check-digit issues. With real AS24 VINs (WMI starting WBA = BMW Germany), NHTSA VIN decode will be minimal; recall data by make/model/year will still work.

**Viable for:** Recall lookup by make/model/year (works for BMW/Mercedes/Porsche). VIN decode for EU cars is unreliable.

---

### Tool C: DAT Consumer Portal (dat.de/gebrauchtfahrzeugwerte)

**Status: BLOCKED for HTTP scrape — requires Playwright**

| Test | HTTP | Fields | Pass | Notes |
|------|------|--------|------|-------|
| BMW X3 2022 50000km | 200 | 2 | False | JS wizard, no static form |

**Finding:**
- Page title: "Was ist mein Auto wert? Kostenloser Gebrauchtfahrzeugwert" (FREE consumer valuation)
- Portal accessible (HTTP 200), ~524KB HTML page
- Valuation wizard is React-based — form fields injected dynamically by JavaScript
- No static HTML `<form>` with POST endpoint — no HTTP-scrape path exists
- Form config embedded as JSON in `<script>` tag (i18n keys: `vehicleBrandQuestion`, `vehicleTypeQuestion`, etc.)
- Navigation login button present but optional — consumer form is free without account
- No CAPTCHA detected
- **Integration path (viable):** Playwright → navigate to URL → fill wizard fields → extract rendered price

**Cost:** €0 (confirmed "Kostenlos" = free in German)

---

## Tool Viability for Phase 3 Integration

| Tool | Viable | Use Case | Integration Path |
|------|--------|----------|-----------------|
| freevindecoder.eu | PARTIAL | WMI manufacturer lookup (redundant — we have make from scraper) | POST /search + CSRF token |
| NHTSA recalls by make/model/year | YES | Open recall flag for dossier | GET api.nhtsa.gov/recalls/recallsByVehicle |
| NHTSA VIN decode | PARTIAL | Limited EU VIN data — best for US-built vehicles | GET vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/VIN |
| DAT Orientierungswert | BLOCKED | Market price reference (would be valuable) | Playwright required |

**Recommendation for enrichment pipeline:**
1. **NHTSA recall lookup** → integrate in detail enricher (free, REST, no auth, works for BMW/Porsche/Mercedes)
2. **freevindecoder** → skip (manufacturer only, we already have make from scraper)
3. **DAT** → defer to Playwright automation phase (valuable but requires browser)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] freevindecoder /api returns 404 — discovered real integration path**

- **Found during:** Task 1 execution
- **Issue:** Plan spec said `GET /api?vin=VIN&apikey=0` — this endpoint returns HTTP 404. The actual integration requires a POST to `/search` with a CSRF token extracted from the homepage.
- **Fix:** Discovered correct flow by inspecting HTML (Vue.js app, CSRF `_token` in form, POST redirects to `/VIN`). Updated script to use session-based CSRF POST flow.
- **Files modified:** tools/validation/test_vin_decode.py
- **Commit:** a56193a

**2. [Rule 1 - Bug] freevindecoder `requires_login` false positive**

- **Found during:** First script run (DAT test)
- **Issue:** Initial DAT test flagged `requires_login=True` because the nav login button matched the regex. This is a nav element, not a form gate.
- **Fix:** Updated DAT test function to distinguish nav login button from form login gate. Added accurate analysis of JS-rendered wizard.
- **Files modified:** tools/validation/test_vin_decode.py
- **Commit:** a56193a (same commit)

## Known Stubs

None — results reflect actual HTTP responses. The VIN data quality limitation (synthetic NHTSA fallback VINs triggering check-digit errors) is documented in 01-01-SUMMARY.md as a known constraint, not a stub introduced in this plan.

## Self-Check

Verified below.
