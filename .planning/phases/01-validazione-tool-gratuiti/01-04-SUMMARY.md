---
phase: 01-validazione-tool-gratuiti
plan: "04"
subsystem: validation
tags: [tool-validation, nhtsa, kba, rdw, dat, freevindecoder, car-recalls, bmw-warranty, argos-grade, integration-decisions]

# Dependency graph
requires:
  - phase: 01-02
    provides: tools/validation/results/vin_decode_results.json (freevindecoder, NHTSA, DAT results)
  - phase: 01-03
    provides: tools/validation/results/recalls_warranty_results.json (car-recalls, KBA, BMW warranty, RDW results)

provides:
  - tools/validation/TOOL_VALIDATION.md — definitive 7-tool validation matrix with INTEGRATE/SKIP decisions, exact API call templates, and ARGOS GRADE impact map

affects:
  - phase 02: detail-enricher-v2 (use NHTSA recalls API + KBA RRDB + RDW for enrichment)
  - phase 03: argos-grade (recall criterion: NHTSA primary, KBA secondary, RDW for NL plates)
  - phase 04: dossier-primo-outreach (recall section populated by NHTSA + KBA; BMW warranty = "not verified")

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Read JSON test results → generate human-readable decision matrix"
    - "Tool integration decision format: INTEGRATE / SKIP / INVESTIGATE with exact API call template for INTEGRATE"

key-files:
  created:
    - tools/validation/TOOL_VALIDATION.md
  modified: []

key-decisions:
  - "NHTSA recalls API: INTEGRATE — free REST, no auth, 7 recalls found for BMW X3 2022, works for EU premium makes"
  - "KBA RRDB: INTEGRATE — altcha PoW solvable in Python; make/model/year recall lookup for DE vehicles"
  - "RDW open data: INTEGRATE — free REST, no auth, plate-based; openstaande_terugroepactie_indicator for NL vehicles"
  - "DAT Orientierungswert: INVESTIGATE — high value (market price) but requires Playwright, defer to browser-automation phase"
  - "freevindecoder.eu: SKIP — manufacturer info only (WMI), redundant with scraper data"
  - "NHTSA VIN decode: SKIP — unreliable for EU WMI prefixes, US-centric DB"
  - "car-recalls.eu: SKIP — WordPress blog, /en/vin/{VIN} returns 404, no integration path"
  - "BMW warranty: SKIP — login wall (MyBMW), no public API found; mark as 'warranty not verified' in dossier"

patterns-established:
  - "ARGOS GRADE recall criterion: NHTSA (primary, US-sold models) + KBA (secondary, DE registry) + RDW (NL plates only)"
  - "Exact Python code templates documented in TOOL_VALIDATION.md Appendix for immediate copy-paste in detail-enricher-v2"

requirements-completed: [TOOL-02, TOOL-03]

# Metrics
duration: 4min
completed: 2026-03-24
---

# Phase 01 Plan 04: Tool Validation Matrix — Summary

**TOOL_VALIDATION.md generated from live test results: 3 INTEGRATE (NHTSA recalls, KBA RRDB, RDW), 1 INVESTIGATE (DAT Playwright), 3 SKIP (freevindecoder, NHTSA VIN decode, car-recalls.eu, BMW warranty) — Phase 3 planner has exact API call templates for all viable tools**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-24T12:47:54Z
- **Completed:** 2026-03-24T12:51:XX Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments

- Consolidated all 7 tool test results from Plans 02 and 03 into a single human-readable decision matrix
- Documented exact INTEGRATE/SKIP/INVESTIGATE decision for every tool with concrete reasons (no ambiguity)
- Wrote ready-to-paste Python code templates for NHTSA recalls API, KBA RRDB (with altcha solver), and RDW open data
- Mapped each working tool to the ARGOS GRADE criterion it feeds (recall weight 10%, km history fraud flag, warranty gap)

## Task Commits

1. **Task 1: Generate TOOL_VALIDATION.md from test results** - `0ce29d8` (feat)

## Files Created/Modified

- `tools/validation/TOOL_VALIDATION.md` — 223-line validation matrix. Section 1: test VINs. Section 2: 7-tool matrix (HTTP status, fields, pass/fail). Section 3: integration decisions with exact API call patterns. Section 4: ARGOS GRADE impact. Section 5: open issues. Appendix: Python code templates.

## Decisions Made

- NHTSA recalls API integrated as primary recall source: free, no auth, returns 7 recalls for BMW X3 2022. Coverage: all EU premium makes sold in US market (BMW, Audi, Mercedes, Porsche, VW).
- KBA RRDB integrated as secondary DE recall source: altcha PoW solvable in pure Python, make/model/year lookup.
- RDW integrated for NL-sourced listings: `openstaande_terugroepactie_indicator` field = recall status, `tellerstandoordeel` = km history judgment.
- DAT Orientierungswert deferred: valuable (market price reference) but requires Playwright browser automation. Phase 3 proceeds with Market Price Index from scraper data + ADAC.
- BMW warranty: mark as "garanzia: richiedere al venditore" (ask seller) in dossier — no free public API exists.

## Deviations from Plan

None — plan executed exactly as written. All data came directly from Plans 02 and 03 JSON results.

## Issues Encountered

None — data was complete in the JSON result files.

## User Setup Required

None.

## Next Phase Readiness

**Ready for Phase 02 (detail-enricher-v2):**

- NHTSA recalls: `GET https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}` — ready to integrate, Python template in TOOL_VALIDATION.md Appendix
- KBA RRDB: altcha PoW solver + POST to `/api/rueckruf/verkaufsbezeichnungBaujahr` — Python template documented
- RDW: `GET https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={PLATE}` — for NL-sourced listings
- DAT: defer to browser automation phase
- BMW warranty: document as "not verified via public API" in ARGOS Grade

**Phase 01 complete.** All 4 tool validation plans executed. TOOL_VALIDATION.md is the ground truth for Phase 3 integration decisions.

---
*Phase: 01-validazione-tool-gratuiti*
*Completed: 2026-03-24*

## Self-Check: PASSED

- tools/validation/TOOL_VALIDATION.md: FOUND (223 lines, 15404 chars)
- .planning/phases/01-validazione-tool-gratuiti/01-04-SUMMARY.md: FOUND
- Commit 0ce29d8 (Task 1): FOUND
