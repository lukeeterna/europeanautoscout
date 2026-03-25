---
phase: 03-argos-grade-pdf-enterprise-v2
verified: 2026-03-24T18:30:20Z
status: gaps_found
score: 7/9 must-haves verified
re_verification: false
gaps:
  - truth: "GRADE-03: VIN decode via freevindecoder.eu integrated in dossier (specs, emissioni, anno)"
    status: failed
    reason: "Phase 1 determined freevindecoder.eu returns only WMI-level manufacturer data (SKIP). No freevindecoder integration exists in argos_grade.py or pdf_generator_enterprise.py. The dossier shows VIN from the DB (null for this listing) with no external decode. Specs (fuel_type, transmission, power_kw) come from the scraper, not freevindecoder. Emissions data is absent entirely."
    artifacts:
      - path: "src/cove/argos_grade.py"
        issue: "No freevindecoder.eu call. No emissions data. VIN shown only if present in DB."
      - path: "tools/scripts/pdf_generator_enterprise.py"
        issue: "VIN shown as 'Da verificare' (null in DB). No specs from external decode. No emission data in 7 Criteri section."
    missing:
      - "Either: implement freevindecoder.eu WMI-level data as partial VIN decode OR formally re-scope GRADE-03 to 'VIN specs from scraper data' and update REQUIREMENTS.md text to match what was actually built"
      - "Emission data (Euro 6 / WLTP) is absent from the dossier entirely — if required by GRADE-03, it must be sourced"

  - truth: "GRADE-04: Residual manufacturer warranty verified via brand site (BMW/MB/Audi) with VIN"
    status: failed
    reason: "Phase 1 confirmed all OEM warranty portals (BMW, Mercedes, Audi) require login — no public VIN endpoint. Implementation hardcodes WARRANTY_STATUS = 'richiedere al venditore' with zero actual verification. The requirement as written ('via sito brand... con VIN') is not implemented; instead Phase 3 documents the workaround."
    artifacts:
      - path: "src/cove/argos_grade.py"
        issue: "WARRANTY_STATUS is a hardcoded string constant, not derived from any brand-site lookup."
    missing:
      - "Either: implement a best-effort brand-site warranty check (even Playwright-based) OR formally re-scope GRADE-04 to 'warranty documented as not publicly verifiable, dealer to confirm' and update REQUIREMENTS.md text accordingly"
      - "Current REQUIREMENTS.md marks GRADE-04 as [x] complete — this is inaccurate relative to the written requirement text"
human_verification:
  - test: "Open dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf in a PDF viewer"
    expected: "Cover page shows large ARGOS GRADE C badge in gold/colored font, real BMW X3 photo, 'Riservato per Stile Car' watermark, and vehicle title BMW X3 2022"
    why_human: "PDF content rendering cannot be verified programmatically with available tools — ReportLab table layouts need visual confirmation"
  - test: "Check the 7 Criteri section in the PDF"
    expected: "7 rows with SI/Da verificare labels, no mention of AutoScout24, CoVe, or Claude. Financial table shows EUR 34,140 purchase + EUR 1,200 transport + EUR 430 imm + EUR 900 fee with net dealer margin clearly visible"
    why_human: "Specific PDF layout and label rendering requires visual inspection"
---

# Phase 03: ARGOS GRADE + PDF Enterprise V2 Verification Report

**Phase Goal:** A completed dossier for any PROCEED listing can be generated with real photos, ARGOS GRADE, 7 verified criteria, and financial analysis.
**Verified:** 2026-03-24T18:30:20Z
**Status:** gaps_found — 7/9 must-haves verified, 2 requirement gaps (GRADE-03, GRADE-04)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ARGOS GRADE A-E computed for listing fresh_84aec3405b5d with weighted score | VERIFIED | CLI output: GRADE C (0.6992), 6-component breakdown confirmed live |
| 2 | NHTSA recall check returns recall count for BMW X3 2022 | VERIFIED | CLI output: "Recalls: 7 (source: NHTSA)" — live API call during spot-check |
| 3 | Warranty status documented as 'richiedere al venditore' | VERIFIED | `WARRANTY_STATUS = "richiedere al venditore"` constant in argos_grade.py (honest workaround, Phase 1 confirmed no free OEM API) |
| 4 | PDF generated for fresh_84aec3405b5d with real photo from AS24 | VERIFIED | dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf — 279,954 bytes, commit 892a81b |
| 5 | PDF shows ARGOS GRADE prominently on cover | VERIFIED (human check needed) | `_build_grade_badge()` function at line 363, integrated in `_create_logo_header()` at line 325 — visual confirmation by human required |
| 6 | PDF includes 7 Criteri section with only verified data | VERIFIED (human check needed) | `_create_7_criteri_section()` at line 543, 7 rows with SI/Da verificare — no AutoScout24/CoVe/Claude in output strings |
| 7 | PDF includes financial analysis in EUR netti | VERIFIED | `_create_financial_analysis_v2()` at line 639 — EUR 34,140 + 1,200 + 430 + 900 fee = MARGINE NETTO DEALER row |
| 8 | PDF has Stile Car watermark and zero source references | VERIFIED | "Riservato per {dealer.name}" in _create_logo_header(); AutoScout24 references only in code comments (not PDF output) |
| 9 | VIN decode via freevindecoder.eu integrated (GRADE-03) | FAILED | No freevindecoder.eu call anywhere. Phase 1 decided SKIP. Specs come from scraper, not external decode. Emissions absent. |
| 10 | Warranty verified via brand site with VIN (GRADE-04) | FAILED | Hardcoded constant, no BMW/MB/Audi site lookup. Phase 1 confirmed login wall on all three OEM sites. |

**Score:** 7/9 truths verified (8-9 are automated-verified; 5-6 pending human visual confirmation)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/cove/argos_grade.py` | ARGOS GRADE calculator + NHTSA recall integration | VERIFIED | 444 lines, substantive — `compute_argos_grade()` + `get_nhtsa_recalls()` functions both present and wired |
| `tools/scripts/pdf_generator_enterprise.py` | PDF Enterprise V2 with grade badge, real photos, 7 criteri, financial | VERIFIED | 1,541 lines, all V2 functions present (`generate_dossier_from_db`, `_build_grade_badge`, `_create_7_criteri_section`, `_create_financial_analysis_v2`, `_cli_main`) |
| `dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf` | Generated dossier with real content | VERIFIED | 279,954 bytes — well above 10KB threshold |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pdf_generator_enterprise.py` | `src/cove/argos_grade.py` | `from src.cove.argos_grade import compute_argos_grade` (line 1445) | WIRED | Runtime import inside `generate_dossier_from_db()` to avoid circular imports — confirmed by SUMMARY |
| `argos_grade.py` | DuckDB `cove_results` | `duckdb.connect(db_path).execute(SELECT ... FROM cove_results)` | WIRED | Reads `confidence`, `fraud_overall`, `make`, `model`, `year` |
| `argos_grade.py` | DuckDB `vehicle_listings` | `con.execute(SELECT ... FROM vehicle_listings)` | WIRED | Reads VIN + 7 completeness fields |
| `argos_grade.py` | DuckDB `vehicle_images` | `con.execute(SELECT COUNT(*) FROM vehicle_images)` | WIRED | Photo count for grade component |
| `argos_grade.py` | NHTSA API | `requests.get("https://api.nhtsa.gov/recalls/recallsByVehicle")` | WIRED | Live API call confirmed working — 7 recalls returned |
| `pdf_generator_enterprise.py` | CDN photo | `_download_image_to_temp(image_url)` + `_convert_webp_to_jpg()` | WIRED | Photo downloaded from AS24 CDN, Pillow webp→jpg conversion |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `argos_grade.py` | `confidence`, `fraud_overall` | DuckDB `cove_results` table — real scraped data | Yes — BMW X3 2022, confidence=0.8425, fraud=CLEAN | FLOWING |
| `argos_grade.py` | `recall_count` | NHTSA REST API (live) | Yes — 7 recalls from live API call | FLOWING |
| `argos_grade.py` | `warranty_status` | Hardcoded constant | N/A — intentional static value (no free API) | STATIC (documented, not a gap) |
| `pdf_generator_enterprise.py` | `price_eu`, `market_price` | DuckDB `cove_results` — real scraped prices | Yes — EUR 34,140 purchase, EUR 37,369 market IT | FLOWING |
| `pdf_generator_enterprise.py` | `image_url` | DuckDB `vehicle_images` — AS24 CDN URLs | Yes — 181KB photo downloaded and embedded | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ARGOS GRADE computed for real listing | `python3 src/cove/argos_grade.py fresh_84aec3405b5d` | GRADE C (0.6992), 6 components, Recalls: 7, Warranty: richiedere al venditore | PASS |
| NHTSA API returns real recall data | (same as above) | 7 recalls from NHTSA, BMW X3 2022 | PASS |
| PDF file exists and is substantive | `ls -la dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf` | 279,954 bytes | PASS |
| Commits are in git history | `git log --oneline` | fee77cf, 892a81b both present | PASS |
| No AutoScout24 in PDF output strings | `grep -n "autoscout24\|AutoScout"` in pdf generator | Only in comments/docstrings, not in output text | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| GRADE-01 | 03-01-PLAN | ARGOS GRADE A-E with 6 weighted components (35%/20%/15%/15%/10%/5%) | SATISFIED | `WEIGHT_*` constants and `compute_argos_grade()` in argos_grade.py exactly match spec |
| GRADE-02 | 03-01-PLAN | Recall check automatico via car-recalls.eu o KBA | SATISFIED (substituted) | car-recalls.eu = SKIP (WordPress blog, no VIN lookup). KBA = deferred. NHTSA is Phase 1-approved substitute — 7 recalls confirmed for BMW X3 2022. Spirit of requirement met. |
| GRADE-03 | 03-01-PLAN | VIN decode via freevindecoder.eu integrato nel dossier (specs, emissioni, anno) | BLOCKED | freevindecoder.eu = SKIP (Phase 1: WMI-only, no additive value). No external VIN decode call exists. Emissions data absent from dossier. REQUIREMENTS.md marks this [x] complete but implementation does not match stated requirement text. |
| GRADE-04 | 03-01-PLAN | Verifica garanzia costruttore residua via sito brand (BMW/MB/Audi) con VIN | BLOCKED | All OEM warranty portals = login wall (Phase 1 confirmed). Hardcoded "richiedere al venditore". REQUIREMENTS.md marks this [x] complete but no brand-site lookup is performed. |
| PDF-01 | 03-02-PLAN | PDF includes real HD photos (non placeholder) | SATISFIED | 181KB AS24 CDN photo downloaded, converted, embedded in PDF |
| PDF-02 | 03-02-PLAN | PDF shows ARGOS GRADE (A-E) prominent in cover | SATISFIED | `_build_grade_badge()` in header — human visual check recommended |
| PDF-03 | 03-02-PLAN | PDF includes "7 Criteri ARGOS Premium Verified" with only verified data | SATISFIED | `_create_7_criteri_section()` — 7 rows, SI/Da verificare labels, no source references |
| PDF-04 | 03-02-PLAN | PDF includes full financial analysis (prezzo EU, costo chiavi in mano, margine netto dealer) | SATISFIED | `_create_financial_analysis_v2()` — EUR 34,140 + 1,200 + 430 + 900 with MARGINE NETTO DEALER row |
| PDF-05 | 03-02-PLAN | PDF has dealer-specific watermark and zero source references | SATISFIED | "Riservato per Stile Car" watermark. AutoScout24/CoVe/Claude only in comments, not in rendered text |

**Orphaned requirements check:** REQUIREMENTS.md Traceability table maps GRADE-01..04 and PDF-01..05 to Phase 3. All 9 IDs are claimed across the two plans. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tools/scripts/pdf_generator_enterprise.py` | 1162 | `"CoVe Status"` table header | Info | Legacy function `generate_combined_dossier()` — not invoked by V2 CLI. Does not appear in new dossier output. No dealer exposure. |
| `src/cove/argos_grade.py` | 61 | `WARRANTY_STATUS = "richiedere al venditore"` (hardcoded) | Info | Intentional and documented. Phase 1 confirms no free OEM API. This is honest, not a stub — it informs the dealer to ask. |
| `tools/scripts/pdf_generator_enterprise.py` | 566 | `delta_ok = True  # We always have price delta from CoVe (PROCEED = positive delta)` | Warning | Hardcoded True for PROCEED listings — valid assumption for PROCEED-filtered listings but not rigorous. Low impact for current use case. |

No blocker-level anti-patterns found in the V2 code paths.

---

### Human Verification Required

#### 1. PDF Visual Layout — Cover Page

**Test:** Open `/Users/macbook/Documents/combaretrovamiauto-enterprise/dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf`
**Expected:** Cover page shows ARGOS GRADE C badge (colored, large, prominent), real BMW X3 photo, "Riservato per Stile Car" watermark in gold, vehicle title "BMW X3 2022 50,058 km"
**Why human:** PDF rendering of ReportLab tables and image positioning cannot be verified from code alone

#### 2. PDF 7 Criteri Section Content

**Test:** Navigate to the 7 Criteri section in the dossier
**Expected:** 7 rows with criterion names (Km verificati, Zero flag frode, HU/revisione, Affidabilita modello, Delta mercato EU-IT, Proprietari, Foto HD originali), status column (SI / Da verificare), and detail notes. No mention of AutoScout24, CoVe, or Claude anywhere visible in the document.
**Why human:** Only visual inspection confirms rendered table content matches code intent

#### 3. PDF Financial Analysis Legibility

**Test:** Check financial table in the PDF
**Expected:** ANALISI FINANZIARIA section shows EUR 34,140 + EUR 1,200 + EUR 430 subtotal, then margin calculation, Fee ARGOS EUR 900, MARGINE NETTO DEALER on black-gold highlighted final row. Numbers are clearly readable and correctly formatted.
**Why human:** Table styling (black background, gold text on final row) requires visual confirmation

---

### Gaps Summary

**2 requirements (GRADE-03 and GRADE-04) are marked complete in REQUIREMENTS.md but their stated implementations do not exist in the codebase.**

**GRADE-03** ("VIN decode via freevindecoder.eu integrato nel dossier") — Phase 1 correctly determined freevindecoder.eu is not useful for EU vehicles (WMI data only). The Phase 3 implementation did not call freevindecoder.eu and did not integrate external emissions data. What WAS implemented is: VIN field from DB (null for this listing), fuel/transmission/power specs from the AS24 scraper. This fulfills the spirit of showing vehicle specs in the dossier but does NOT fulfill the literal requirement text (freevindecoder.eu, emissioni).

**GRADE-04** ("Verifica garanzia costruttore residua via sito brand BMW/MB/Audi con VIN") — Phase 1 confirmed all three OEM portals require login. The Phase 3 implementation hardcodes "richiedere al venditore" as WARRANTY_STATUS. This is an honest and correct approach for the current state of available free tools, but it does not fulfill the requirement as written.

**Recommended resolution:** Update REQUIREMENTS.md text for GRADE-03 and GRADE-04 to match what was actually built (acceptable scope reduction given Phase 1 tool findings), rather than re-implementing. The existing implementations are correct and honest — the requirement text is the artifact that needs updating. This is a documentation gap, not a functional gap.

**Root cause:** GRADE-03 and GRADE-04 were written before Phase 1 tool validation revealed these tools were unavailable. Phase 3 Plan 01 correctly implemented the Phase 1-approved alternatives but did not update the REQUIREMENTS.md wording to match.

**Impact on Phase Goal:** The phase goal ("completed dossier for any PROCEED listing with real photos, ARGOS GRADE, 7 verified criteria, and financial analysis") is ACHIEVED. The dossier exists, is 280KB with a real photo, shows ARGOS GRADE C, has 7 Criteri with honest SI/Da verificare labels, and includes complete financial analysis. The two failed requirements are about specific tool integrations (freevindecoder, OEM warranty sites) that Phase 1 correctly rejected — not about the dossier's fitness for delivery.

---

_Verified: 2026-03-24T18:30:20Z_
_Verifier: Claude (gsd-verifier)_
