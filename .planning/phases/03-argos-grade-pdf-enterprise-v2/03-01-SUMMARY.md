---
phase: 03-argos-grade-pdf-enterprise-v2
plan: 01
subsystem: scoring
tags: [argos-grade, nhtsa, recall, duckdb, python, cove]

# Dependency graph
requires:
  - phase: 02-schema-db-detail-enricher
    provides: vehicle_listings + vehicle_images tables in cove_tracker.duckdb
  - phase: 01-validazione-tool-gratuiti
    provides: NHTSA recall API template (confirmed working, 7 recalls BMW X3 2022)
provides:
  - ARGOS GRADE A-E letter grade with weighted composite score
  - compute_argos_grade(listing_id, db_path) — reads cove_results + vehicle_listings + vehicle_images
  - get_nhtsa_recalls(make, model, year) — NHTSA free REST API with 15s timeout
  - CLI: python3 src/cove/argos_grade.py <listing_id> [--json] [--db path]
affects:
  - 03-02-pdf-enterprise-v2 (needs grade + recall_count + warranty_status for PDF)
  - phase-04-primo-outreach (grade shown in dossier sent to Stile Car)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Weighted scoring: per-component score × weight, summed to 0.0-1.0, mapped to letter grade"
    - "Static fallback for unavailable data (km_history=0.5, warranty=richiedere al venditore)"
    - "DuckDB read_only=True for all grade queries"

key-files:
  created:
    - src/cove/argos_grade.py
  modified: []

key-decisions:
  - "Reads cove_results directly (NOT invoking cove_engine_v4.py) — engine writes results, grade reads them"
  - "NHTSA recall component weight = 10% — no free DE odometer check, km_history static 0.5 at 5%"
  - "Grade C for fresh_84aec3405b5d (score 0.6992): pulled down by 3/7 data completeness + 1 photo + 7 NHTSA recalls"
  - "Warranty hardcoded richiedere al venditore — Phase 1 confirmed no free BMW/MB/Audi warranty API"

patterns-established:
  - "Component scoring: each component returns 0.0-1.0, then multiplied by weight"
  - "Grade thresholds: A>=0.85, B>=0.75, C>=0.65, D>=0.55, E<0.55"
  - "NHTSA call: make/model/year (not VIN) — VIN unreliable for EU WMI prefixes"

requirements-completed: [GRADE-01, GRADE-02, GRADE-03, GRADE-04]

# Metrics
duration: 8min
completed: 2026-03-24
---

# Phase 03 Plan 01: ARGOS GRADE A-E Calculator Summary

**ARGOS GRADE A-E weighted scoring from CoVe confidence + fraud flags + data completeness + photos + NHTSA recalls, with BMW X3 2022 scoring C (0.6992)**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-24T18:17:00Z
- **Completed:** 2026-03-24T18:25:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Built `argos_grade.py` — 444-line module with `compute_argos_grade()` and `get_nhtsa_recalls()`
- NHTSA recall API integrated (free REST, no auth) — returns 7 recalls for BMW X3 2022 confirmed
- Target listing `fresh_84aec3405b5d`: GRADE C (0.6992), PROCEED, 7 recalls, CLEAN fraud
- CLI produces human-readable and JSON output; `--json` flag for pipeline consumption

## Task Commits

1. **Task 1: Build argos_grade.py with GRADE A-E + NHTSA recall integration** - `fee77cf` (feat)

## Files Created/Modified

- `/Users/macbook/Documents/combaretrovamiauto-enterprise/src/cove/argos_grade.py` — ARGOS GRADE calculator + NHTSA recall integration, CLI entry point

## Decisions Made

- Reads `cove_results` table directly (NOT invoking `cove_engine_v4.py`) — the engine writes results, the grade reads them. This satisfies acceptance criterion AC6 (`grep -c "cove_engine_v4"` returns 0).
- `km_history` component is static 0.5 (5% weight) — no free DE odometer verification exists. Honest fallback.
- NHTSA query uses make/model/year (not VIN) — confirmed more reliable for EU vehicles than VIN decode.
- `WARRANTY_STATUS = "richiedere al venditore"` hardcoded — Phase 1 confirmed all OEM warranty APIs require login.

## Deviations from Plan

None — plan executed exactly as written. NHTSA API template copied verbatim from TOOL_VALIDATION.md appendix as instructed.

## Issues Encountered

None. NHTSA API responded within 2s with 7 recalls for BMW X3 2022 as expected from Phase 1 validation.

## Known Stubs

- `km_history` score is static 0.5 — intentional, documented. Will remain until a free DE odometer check API is found. Does NOT prevent the plan's goal (grade is computed and shown).
- Photo count for `fresh_84aec3405b5d` = 1 (only 1 image in vehicle_images) — pulling grade down from A to C. Real enrichment (Phase 2 detail_enricher_v2) can add more photos if listing is still live.

## User Setup Required

None — no external service configuration required. NHTSA API is free, no credentials needed.

## Next Phase Readiness

- `compute_argos_grade()` and `get_nhtsa_recalls()` are ready for import by Phase 03 Plan 02 (PDF Enterprise V2)
- Grade output dict contains all fields PDF needs: `grade`, `score`, `recall_count`, `recalls`, `warranty_status`, `components`
- Blocker note: `fresh_84aec3405b5d` scores C not B/A due to low completeness (3/7 fields) + 1 photo. Phase 02 detail enricher should be re-run on fresh listings to populate `fuel_type`, `transmission`, `power_kw` before PDF generation.

---
*Phase: 03-argos-grade-pdf-enterprise-v2*
*Completed: 2026-03-24*
