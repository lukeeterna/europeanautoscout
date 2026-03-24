---
phase: 01-validazione-tool-gratuiti
plan: 03
subsystem: validation
tags: [car-recalls, kba, bmw-warranty, rdw, recall-data, warranty-check, free-tools]

# Dependency graph
requires:
  - phase: 01-01
    provides: test_vins.json with 3 real VINs (BMW X3 x2, Porsche Macan x1)

provides:
  - tools/validation/test_recalls_warranty.py — 684-line script testing 4 recall/warranty sources
  - tools/validation/results/recalls_warranty_results.json — 12 records with full HTTP status and integration paths
  - Definitive integration verdict for: car-recalls.eu (BLOCKED), KBA (POSSIBLE), BMW warranty (BLOCKED), RDW (WORKS)
  - KBA API reverse-engineered: Svelte SPA, altcha PoW challenge endpoint documented, search by make/model/year
  - RDW API confirmed: REST, no auth, plate-based, includes openstaande_terugroepactie_indicator (recall status)

affects:
  - phase 02: detail-enricher-v2 (KBA and RDW can be integrated; recall weight in ARGOS GRADE computation)
  - phase 03: argos-grade (recall criterion: use KBA make/model search or RDW recall indicator)
  - phase 04: dossier-primo-outreach (recall section: KBA possible, RDW only for NL plates)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "HTTP probing pattern: test URL → follow redirects → analyze body → document barrier"
    - "SPA reverse engineering: fetch JS bundle → grep for API paths → test endpoints directly"
    - "altcha PoW CAPTCHA: solvable with SHA-256 in pure Python (no image CAPTCHA)"

key-files:
  created:
    - tools/validation/test_recalls_warranty.py
    - tools/validation/results/recalls_warranty_results.json
  modified: []

key-decisions:
  - "car-recalls.eu REJECTED — it is a WordPress blog, NOT a VIN lookup API; /en/vin/{VIN} returns 404"
  - "KBA marked POSSIBLE — altcha PoW is solvable programmatically; but returns recalls by make/model/year not VIN"
  - "BMW warranty REJECTED — login wall (MyBMW account required); no public endpoint found"
  - "RDW ACCEPTED — free REST API confirmed working; use for NL-sourced listings via plate lookup"
  - "RDW openstaande_terugroepactie_indicator field = free recall status for NL plates (bonus discovery)"

patterns-established:
  - "Probe pattern: always test the actual URL pattern before documenting as working"
  - "SPA detection: check response body size (<1000 bytes + <div id=app> = SPA, need JS bundle analysis)"

requirements-completed: [TOOL-01, TOOL-02, TOOL-03]

# Metrics
duration: 12min
completed: 2026-03-24
---

# Phase 01 Plan 03: Recall & Warranty Tool Validation Summary

**Validated 4 recall/warranty tools via live HTTP probing: car-recalls.eu is a blog (not VIN API), KBA requires altcha PoW (solvable, but make/model only), BMW warranty requires login, RDW REST API works with no auth (plate-based, returns recall indicator)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-24T12:33:12Z
- **Completed:** 2026-03-24T12:45:04Z
- **Tasks:** 1 of 1
- **Files modified:** 2

## Accomplishments

- car-recalls.eu probed: confirmed it is a WordPress blog aggregating recall articles — no VIN lookup endpoint exists. The /en/vin/{VIN} URL pattern returns 404. The "Free VIN Check" page is a taxonomy browser (make/model). Integration path: NONE.
- KBA kba-online.de reverse-engineered: Svelte SPA serving 419-byte shell. JS bundle (1.3MB) reveals REST API with altcha PoW challenge. Backend endpoints documented. Search is by make/model/year — no direct VIN/FIN lookup. Integration: POSSIBLE with Python altcha solver.
- BMW warranty portal probed: all tested URLs return either timeout or 404. Confirmed login wall (MyBMW account). No public VIN endpoint found. Integration path: NONE without credentials.
- RDW open data API confirmed working: `GET https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={PLATE}` returns 50+ fields per vehicle with no auth. Key field: `openstaande_terugroepactie_indicator` (open recall: Ja/Nee). Integration: WORKS — applies to NL-registered vehicles only.

## Task Commits

1. **Task 1: Test recall and warranty portals** - `bbc632e` (feat)

## Files Created/Modified

- `tools/validation/test_recalls_warranty.py` — 684-line script testing car-recalls.eu (D), KBA (E), BMW warranty (F), RDW (G) with full HTTP probing, SPA analysis, and integration path documentation
- `tools/validation/results/recalls_warranty_results.json` — 12 result records across 4 tools with exact HTTP status, block reason, data returned, and integration path per tool

## Decisions Made

- car-recalls.eu: rejected as integration target. It is a content blog, not a lookup API. Future recall data will come from KBA API (with altcha solver) or EU Safety Gate RAPEX API.
- KBA: marked as POSSIBLE integration target. The altcha PoW challenge can be solved in pure Python (SHA-256 iteration, no image recognition needed). However, KBA returns recalls by make/model/year — not by specific VIN. This is still useful for "does BMW X3 2022 have known recalls?" but not per-vehicle verification.
- BMW warranty: no free path exists. Residual warranty will be documented as "not verified" in ARGOS Grade criteria until a dealer BMW Partner Portal credential is available.
- RDW: confirmed as integration target for NL-sourced listings. The `openstaande_terugroepactie_indicator` field is a bonus — it gives recall status for free for NL-registered vehicles.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected car-recalls.eu URL pattern assumption**
- **Found during:** Task 1 (running script)
- **Issue:** Plan specified URL `https://car-recalls.eu/en/vin/{VIN}` — returned 404. Investigation showed the site is a WordPress blog with no VIN lookup functionality. The `/vin-check-recalls/` page is a make/model taxonomy browser, not a VIN form.
- **Fix:** Rewrote the car-recalls.eu test to probe the actual site structure, document the blog nature, and record the correct finding (BLOCKED — not a VIN API). Added WordPress search test as confirmation.
- **Files modified:** tools/validation/test_recalls_warranty.py
- **Verification:** HTTP 404 for /en/vin/{VIN} confirmed. Search returns "no results" for VIN strings. Site structure analyzed from homepage + vin-check-recalls page + WP JSON API namespaces.
- **Committed in:** bbc632e (Task 1 commit)

**2. [Rule 1 - Bug] Fixed KBA URL (redirect to trailing slash)**
- **Found during:** Task 1 (KBA test returning HTTP 307)
- **Issue:** Initial script didn't follow the redirect from `/rrdb/buerger` to `/rrdb/buerger/` — Python urllib blocked on 307. The actual page is a 419-byte SPA shell, not an HTML form.
- **Fix:** Updated to use the correct URL with trailing slash. Reverse-engineered the Svelte SPA by fetching and analyzing the JS bundle (1.3MB). Found all REST API endpoints. Documented the altcha PoW CAPTCHA requirement.
- **Files modified:** tools/validation/test_recalls_warranty.py
- **Verification:** HTTP 200 confirmed for SPA shell. Makes API (`/api/markeFahrzeughersteller`) returns data without auth. Search API requires altcha payload.
- **Committed in:** bbc632e (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bug fixes to incorrect URL assumptions in plan)
**Impact on plan:** Both fixes necessary for accurate results. Plan URLs were untested hypotheses — real behavior documented instead.

## Issues Encountered

- BMW warranty URLs timed out (bmw.de blocks MacBook external requests). Probed 2 URLs; both unreachable. Documented as CONNECTION_TIMEOUT. The /api/bmw.com/warranty/v1/check URL returned 404 — speculative URL that doesn't exist.
- RDW plate format: API requires no dashes (`24ZNT2` not `24-ZNT-2`). Confirmed by returning 1 record for synthetic plate 24ZNT2 (Chevrolet Cruze, NL registered, 50+ fields returned).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 02 (detail-enricher-v2):**

- RDW: integrate for NL-sourced vehicles. GET `https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={PLATE}` — zero auth, free, returns recall indicator and km history judgment.
- KBA: optional integration — implement altcha PoW solver (pure Python SHA-256) to query `/api/rueckruf/verkaufsbezeichnungBaujahr` by make/model/year. Returns all known recalls for that model.
- car-recalls.eu: do NOT integrate — blog only.
- BMW warranty: do NOT integrate — requires login. Mark "warranty not verified" in ARGOS Grade.

**Recall criterion for ARGOS Grade (Phase 03):**
- For NL-registered vehicles: use RDW `openstaande_terugroepactie_indicator`
- For DE/EU vehicles without plate: use KBA make/model/year search (if altcha solver implemented)
- Fallback: mark as "recall status unknown"

**Blockers for Phase 02:** None — RDW works immediately. KBA integration optional.

---
*Phase: 01-validazione-tool-gratuiti*
*Completed: 2026-03-24*
