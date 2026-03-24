---
phase: 03-argos-grade-pdf-enterprise-v2
plan: 02
subsystem: pdf-generator
tags: [pdf, dossier, argos-grade, vehicle-dossier, dealer-outreach]
dependency_graph:
  requires:
    - 03-01 (argos_grade.py — compute_argos_grade + NHTSA recall)
    - 02-02 (vehicle_listings + vehicle_images tables in DuckDB)
  provides:
    - dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf (real dossier for Stile Car)
    - generate_dossier_from_db() CLI function
  affects:
    - tools/scripts/pdf_generator_enterprise.py
tech_stack:
  added: []
  patterns:
    - ReportLab PDF generation with Table/Paragraph compositing
    - DuckDB read-only connection for vehicle data
    - requests CDN photo download + Pillow webp→jpg conversion
    - argparse CLI with --listing/--dealer/--output flags
key_files:
  created:
    - dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf
  modified:
    - tools/scripts/pdf_generator_enterprise.py
decisions:
  - "Transport cost fixed at EUR 1200 (DE→Sud Italia bisarca estimate, not calculated per-listing)"
  - "Photo webp→jpg conversion via Pillow for ReportLab compatibility"
  - "argos_grade.py imported at runtime inside generate_dossier_from_db to avoid circular imports"
  - "Legacy __main__ (Mario BMW) preserved — new CLI activated only when --listing flag present"
metrics:
  duration: 18 minutes
  completed: "2026-03-24"
  tasks_completed: 1
  files_modified: 2
---

# Phase 03 Plan 02: PDF Enterprise V2 Summary

## One-Liner

PDF Enterprise V2 generates dealer dossiers from DuckDB with ARGOS GRADE badge (A-E), real CDN photo, 7 Criteri ARGOS Premium Verified section, and success-fee financial analysis — zero source references.

## What Was Built

### Task 1: PDF Generator V2 (commit 892a81b)

Updated `tools/scripts/pdf_generator_enterprise.py` with:

**New V2 functions:**
- `generate_dossier_from_db(listing_id, dealer_name, output_dir, db_path)` — CLI function that reads from DuckDB (cove_results + vehicle_listings + vehicle_images), computes ARGOS GRADE, downloads real photo, generates PDF
- `_build_grade_badge(grade_letter)` — colored grade badge (A=green, B=light-green, C=gold, D=amber, E=red)
- `_create_7_criteri_section(vehicle, grade_data)` — 7 CRITERI ARGOS PREMIUM VERIFIED section with SI/NO/Da verificare per criterion
- `_create_financial_analysis_v2(vehicle, grade_data)` — full cost breakdown: prezzo EU + trasporto EUR 1.200 + immatricolazione EUR 430 + fee ARGOS EUR 900 = MARGINE NETTO DEALER
- `_download_image_to_temp(url)` — CDN photo download to temp file
- `_convert_webp_to_jpg(path)` — webp→jpg conversion via Pillow
- `_cli_main()` — argparse CLI entry point

**Updated existing methods:**
- `generate_vehicle_sheet()` — now accepts `grade_data` optional dict, uses it for badge + 7 criteri + V2 financial
- `_create_logo_header()` — now accepts `grade_data`, renders grade badge in center column
- `_create_executive_summary()` — now accepts `grade_data` parameter

**New CLI usage:**
```
python3 tools/scripts/pdf_generator_enterprise.py \
    --listing fresh_84aec3405b5d \
    --dealer "Stile Car" \
    --output dossiers/
```

**Generated dossier:**
- File: `dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf`
- Size: 273KB (real photo embedded)
- ARGOS GRADE: C (score 0.6992)
- Photo: BMW X3 downloaded from AS24 CDN (181,872 bytes → converted to JPEG)
- Watermark: "Riservato per Stile Car"
- Financial: EUR 34.140 + EUR 1.200 trasporto + EUR 430 imm + EUR 900 fee = MARGINE NETTO DEALER

## Verification Results

All acceptance criteria met:
- PDF file created: dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf (273KB)
- Output shows "PDF generated:" with file path
- File size 273KB > 10KB
- `grep -c "ARGOS GRADE" tools/scripts/pdf_generator_enterprise.py` = 11 (> 0)
- No autoscout24/AutoScout references in PDF output strings (only in docstring comments)

## Deviations from Plan

### Auto-fixed Issues

None. Plan executed exactly as written.

### Minor Implementation Notes

- `_create_financial_analysis_v2()` added as separate method (not modifying existing `_create_financial_analysis()`) to preserve backward compatibility with `generate_opportunity_dossier()` and `generate_combined_dossier()` functions
- Transport cost set to EUR 1.200 (per plan spec: "Trasporto bisarca: €1.200 (stima DE→Sud Italia)") rather than dynamic calculation
- Legacy `generate_mario_bmw_sheet()` and old `__main__` preserved for backward compatibility — V2 CLI activates only when `--listing` flag is present

## Known Stubs

None — all data used in the dossier is real:
- Price: EUR 34.140 from cove_results (scraped live)
- Market price IT: EUR 37.369 from CoVe scoring (real comparable listings)
- Photo: real HD image from AS24 CDN (181KB)
- ARGOS GRADE: computed live (C, 0.6992) from real data
- NHTSA recalls: 7 (live API)
- VIN: null (AS24 does not expose VIN for dealer listings) — documented as "Da verificare"

## Self-Check: PASSED

Files exist:
- dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf — FOUND
- tools/scripts/pdf_generator_enterprise.py — FOUND

Commits exist:
- 892a81b — feat(03-02): PDF Enterprise V2 — FOUND
