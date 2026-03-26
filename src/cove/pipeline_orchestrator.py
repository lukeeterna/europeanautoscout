#!/usr/bin/env python3
"""
pipeline_orchestrator.py — ARGOS Pipeline Orchestrator
CoVe 2026 | Enterprise Grade

Runs every 4 hours via cron. Processes all vehicles through the 7-state pipeline:
  DISCOVERED → SCORED → ENRICHED → SELLER_CONTACTED → DATA_COMPLETE → DOSSIER_READY → DELIVERED

Each run:
  1. Queries all non-terminal vehicles
  2. Checks if state transition conditions are met
  3. Executes transitions (CoVe, enricher, email, PDF)
  4. Updates state + logs everything

Cron setup (iMac):
  0 */4 * * * cd /path/to/combaretrovamiauto-enterprise && python3 src/cove/pipeline_orchestrator.py >> logs/pipeline.log 2>&1

Usage:
  python3 src/cove/pipeline_orchestrator.py              # Full run
  python3 src/cove/pipeline_orchestrator.py --status      # Show pipeline summary
  python3 src/cove/pipeline_orchestrator.py --dry-run     # Show what would happen
  python3 src/cove/pipeline_orchestrator.py --state SCORED # Process only one state
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = str(SCRIPT_DIR / "data" / "cove_tracker.duckdb")

# Add project root to path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cove.pipeline_states import (
    transition, gate1_check, gate2_check, gate3_check,
    get_pipeline_summary, STATES,
    GATE2_FOLLOWUP1_DAYS, GATE2_FOLLOWUP2_DAYS, GATE2_ABANDON_DAYS,
)


class PipelineOrchestrator:
    """
    State machine orchestrator. Processes vehicles through the pipeline.
    Each method handles one state's transitions.
    """

    def __init__(self, db_path: str = DB_PATH, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.stats = {s: 0 for s in ["processed", "transitioned", "errors", "skipped"]}
        self._log(f"{'DRY RUN — ' if dry_run else ''}Pipeline run started at {datetime.now(timezone.utc).isoformat()}")

    def run(self, only_state: str = None):
        """Process all active states in order."""
        self._log("\n" + "=" * 60)
        self._log("  ARGOS PIPELINE ORCHESTRATOR")
        self._log("=" * 60)

        # Show current state
        summary = get_pipeline_summary(self.db_path)
        self._log(f"\n  Current pipeline state:")
        for state, count in sorted(summary.items(), key=lambda x: x[1], reverse=True):
            self._log(f"    {state:25s} {count:4d}")

        processors = [
            ("DISCOVERED", self.process_discovered),
            ("SCORED", self.process_scored),
            ("ENRICHED", self.process_enriched),
            ("SELLER_CONTACTED", self.process_seller_contacted),
            ("DATA_COMPLETE", self.process_data_complete),
            ("DOSSIER_READY", self.process_dossier_ready),
        ]

        for state_name, processor in processors:
            if only_state and only_state != state_name:
                continue
            try:
                processor()
            except Exception as e:
                self._log(f"\n  ERROR processing {state_name}: {e}")
                self.stats["errors"] += 1

        # Final summary
        self._log(f"\n{'=' * 60}")
        self._log(f"  Run complete: {self.stats['processed']} processed, "
                   f"{self.stats['transitioned']} transitioned, "
                   f"{self.stats['errors']} errors, "
                   f"{self.stats['skipped']} skipped")
        self._log("=" * 60)

    # ── State Processors ──────────────────────────────────────────────────────

    def process_discovered(self):
        """Score all DISCOVERED listings through CoVe."""
        listings = self._query_state("DISCOVERED")
        if not listings:
            return
        self._log(f"\n── DISCOVERED → SCORED ({len(listings)} listings) ──")

        for lid, row in listings:
            self.stats["processed"] += 1
            # Check if already scored in cove_results
            cove = self._get_cove_result(lid)
            if not cove:
                self._log(f"  {lid}: no CoVe result — needs scoring (skipping)")
                self.stats["skipped"] += 1
                continue

            recommendation, confidence, fraud = cove
            passed, reason = gate1_check(recommendation, confidence, fraud)

            if passed:
                self._transition(lid, "DISCOVERED", "SCORED",
                                 "gate1_pass", {"confidence": confidence, "fraud": fraud, "reason": reason})
            else:
                self._transition(lid, "DISCOVERED", "REJECTED",
                                 "gate1_fail", {"reason": reason})

    def process_scored(self):
        """Enrich all SCORED listings (detail page scrape)."""
        listings = self._query_state("SCORED")
        if not listings:
            return
        self._log(f"\n── SCORED → ENRICHED ({len(listings)} listings) ──")

        for lid, row in listings:
            self.stats["processed"] += 1
            # Check if enrichment data already exists
            has_detail = self._has_enrichment(lid)
            if has_detail:
                self._transition(lid, "SCORED", "ENRICHED",
                                 "already_enriched", {"source": "existing_data"})
            else:
                # Run detail enricher
                if self.dry_run:
                    self._log(f"  {lid}: would run detail_enricher_v2")
                    self.stats["skipped"] += 1
                    continue
                success = self._run_enricher(lid)
                if success:
                    self._transition(lid, "SCORED", "ENRICHED",
                                     "enricher_v2", {"enriched": True})
                else:
                    self._log(f"  {lid}: enrichment failed — staying in SCORED")
                    self.stats["errors"] += 1

    def process_enriched(self):
        """Decide: contact seller or skip to DATA_COMPLETE."""
        listings = self._query_state("ENRICHED")
        if not listings:
            return
        self._log(f"\n── ENRICHED → SELLER_CONTACTED / DATA_COMPLETE ({len(listings)} listings) ──")

        for lid, row in listings:
            self.stats["processed"] += 1
            photo_count = self._get_photo_count(lid)
            completeness = self._get_data_completeness(lid)

            # If already have enough data, skip seller contact
            if photo_count >= 6 and completeness >= 0.7:
                self._transition(lid, "ENRICHED", "DATA_COMPLETE",
                                 "sufficient_data", {"photos": photo_count, "completeness": completeness})
                continue

            # Need seller contact — discover email and send
            if self.dry_run:
                self._log(f"  {lid}: would discover email + send seller contact request")
                self.stats["skipped"] += 1
                continue

            email_sent = self._contact_seller(lid)
            if email_sent:
                self._transition(lid, "ENRICHED", "SELLER_CONTACTED",
                                 "email_sent", {"photos": photo_count})
            else:
                # No email found — if we have minimum data, proceed anyway
                if photo_count >= 4:
                    self._transition(lid, "ENRICHED", "DATA_COMPLETE",
                                     "no_seller_email_but_min_data",
                                     {"photos": photo_count, "completeness": completeness})
                else:
                    self._log(f"  {lid}: no seller email + insufficient data ({photo_count} photos)")
                    self.stats["skipped"] += 1

    def process_seller_contacted(self):
        """Check timeouts and follow-ups for contacted sellers."""
        listings = self._query_state("SELLER_CONTACTED")
        if not listings:
            return
        self._log(f"\n── SELLER_CONTACTED checks ({len(listings)} listings) ──")

        import duckdb
        con = duckdb.connect(self.db_path, read_only=True)

        for lid, row in listings:
            self.stats["processed"] += 1

            # Get contact tracking data
            tracking = con.execute("""
                SELECT seller_contact_sent_at, seller_followup_count
                FROM vehicle_listings WHERE listing_id = ?
            """, [lid]).fetchone()

            if not tracking or not tracking[0]:
                self._log(f"  {lid}: no contact timestamp — check manually")
                self.stats["skipped"] += 1
                continue

            sent_at = datetime.fromisoformat(str(tracking[0]))
            followup_count = tracking[1] or 0
            days = (datetime.now(timezone.utc) - sent_at).days
            photo_count = self._get_photo_count(lid)
            completeness = self._get_data_completeness(lid)

            action, reason = gate2_check(photo_count, days, followup_count,
                                         int(completeness * 7), 7)

            if action == "COMPLETE":
                self._transition(lid, "SELLER_CONTACTED", "DATA_COMPLETE",
                                 "gate2_complete", {"reason": reason})
            elif action == "ABANDON":
                self._transition(lid, "SELLER_CONTACTED", "ABANDONED",
                                 "gate2_abandon", {"days": days, "followups": followup_count})
            elif action in ("FOLLOWUP1", "FOLLOWUP2"):
                if self.dry_run:
                    self._log(f"  {lid}: would send {action} (day {days})")
                else:
                    self._send_followup(lid, followup_count + 1)
                self.stats["skipped"] += 1
            else:
                self._log(f"  {lid}: waiting (day {days}, {followup_count} follow-ups)")
                self.stats["skipped"] += 1

        con.close()

    def process_data_complete(self):
        """Generate dossier if Gate 3 passes."""
        listings = self._query_state("DATA_COMPLETE")
        if not listings:
            return
        self._log(f"\n── DATA_COMPLETE → DOSSIER_READY ({len(listings)} listings) ──")

        for lid, row in listings:
            self.stats["processed"] += 1

            # Compute ARGOS GRADE
            grade_data = self._compute_grade(lid)
            if not grade_data:
                self._log(f"  {lid}: grade computation failed")
                self.stats["errors"] += 1
                continue

            grade = grade_data.get("grade", "E")
            photo_count = self._get_photo_count(lid)
            margin = self._estimate_margin(lid)

            passed, reason = gate3_check(grade, photo_count, margin)

            if passed:
                if self.dry_run:
                    self._log(f"  {lid}: would generate PDF (grade={grade} photos={photo_count} margin=EUR{margin:.0f})")
                    self.stats["skipped"] += 1
                    continue

                pdf_path = self._generate_dossier(lid, grade_data)
                if pdf_path:
                    self._transition(lid, "DATA_COMPLETE", "DOSSIER_READY",
                                     "gate3_pass_pdf_generated",
                                     {"grade": grade, "photos": photo_count, "margin": margin,
                                      "pdf": pdf_path})
                else:
                    self._log(f"  {lid}: PDF generation failed")
                    self.stats["errors"] += 1
            else:
                self._transition(lid, "DATA_COMPLETE", "PARKED",
                                 "gate3_fail", {"reason": reason})

    def process_dossier_ready(self):
        """Report vehicles ready for human review + dealer delivery."""
        listings = self._query_state("DOSSIER_READY")
        if not listings:
            return
        self._log(f"\n── DOSSIER_READY (awaiting human review) ──")
        for lid, row in listings:
            self._log(f"  READY: {lid} — needs human review before sending to dealer")

    # ── Helper Methods ────────────────────────────────────────────────────────

    def _query_state(self, state: str) -> List:
        """Get all listings in a given state."""
        import duckdb
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            rows = con.execute("""
                SELECT listing_id, make, model, year, mileage, price_eu
                FROM vehicle_listings WHERE pipeline_state = ?
                ORDER BY state_updated_at ASC NULLS FIRST
            """, [state]).fetchall()
            return [(r[0], r) for r in rows]
        except Exception:
            return []
        finally:
            con.close()

    def _get_cove_result(self, listing_id: str):
        """Get CoVe scoring result for a listing."""
        import duckdb
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            row = con.execute("""
                SELECT recommendation, confidence, fraud_overall
                FROM cove_results WHERE listing_id = ?
            """, [listing_id]).fetchone()
            return row
        finally:
            con.close()

    def _has_enrichment(self, listing_id: str) -> bool:
        """Check if listing has enrichment data (fuel_type, images)."""
        import duckdb
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            row = con.execute("""
                SELECT fuel_type, image_count FROM vehicle_listings WHERE listing_id = ?
            """, [listing_id]).fetchone()
            if row and row[0] and row[0] != 'Sconosciuto':
                return True
            img = con.execute(
                "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?", [listing_id]
            ).fetchone()
            return img and img[0] > 0
        finally:
            con.close()

    def _get_photo_count(self, listing_id: str) -> int:
        import duckdb
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            row = con.execute(
                "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?", [listing_id]
            ).fetchone()
            return row[0] if row else 0
        finally:
            con.close()

    def _get_data_completeness(self, listing_id: str) -> float:
        """Compute data completeness score 0.0-1.0."""
        import duckdb
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            row = con.execute("""
                SELECT vin, fuel_type, transmission, power_kw, color, mileage, price_eu
                FROM vehicle_listings WHERE listing_id = ?
            """, [listing_id]).fetchone()
            if not row:
                return 0.0
            filled = sum(1 for v in row if v is not None and str(v).strip() not in ('', '0', 'Sconosciuto'))
            return filled / len(row)
        finally:
            con.close()

    def _estimate_margin(self, listing_id: str) -> float:
        """Estimate dealer margin EUR."""
        import duckdb
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            row = con.execute("""
                SELECT price, market_price FROM cove_results WHERE listing_id = ?
            """, [listing_id]).fetchone()
            if not row or not row[1]:
                return 0.0
            price_eu = float(row[0])
            market_it = float(row[1])
            transport = 1200
            immatricolazione = 430
            fee_argos = 900
            return market_it - price_eu - transport - immatricolazione - fee_argos
        finally:
            con.close()

    def _run_enricher(self, listing_id: str) -> bool:
        """Run detail enricher on a listing."""
        try:
            from src.cove.detail_enricher_v2 import enrich_listing
            return enrich_listing(listing_id, self.db_path)
        except Exception as e:
            self._log(f"  {listing_id}: enricher error: {e}")
            return False

    def _contact_seller(self, listing_id: str) -> bool:
        """Discover email + send seller contact request."""
        try:
            from src.cove.seller_email_discovery import discover_and_store
            from src.cove.seller_contact import request_missing_data

            # Step 1: Find email
            disc = discover_and_store(listing_id, self.db_path)
            if not disc.get("email"):
                self._log(f"  {listing_id}: no seller email found")
                return False

            # Step 2: Send request (dry_run respects orchestrator mode)
            result = request_missing_data(listing_id, self.db_path, dry_run=self.dry_run)
            sent = result.get("send_result", {}).get("sent", False)

            if sent:
                # Update tracking in DB
                import duckdb
                now = datetime.now(timezone.utc).isoformat()
                con = duckdb.connect(self.db_path)
                con.execute("""
                    UPDATE vehicle_listings
                    SET seller_contact_sent_at = ?, seller_followup_count = 0
                    WHERE listing_id = ?
                """, [now, listing_id])
                con.close()

            return sent
        except Exception as e:
            self._log(f"  {listing_id}: seller contact error: {e}")
            return False

    def _send_followup(self, listing_id: str, followup_num: int):
        """Send follow-up email to seller."""
        self._log(f"  {listing_id}: sending follow-up #{followup_num}")
        # TODO: implement follow-up email template
        import duckdb
        con = duckdb.connect(self.db_path)
        con.execute("""
            UPDATE vehicle_listings
            SET seller_followup_count = ?
            WHERE listing_id = ?
        """, [followup_num, listing_id])
        con.close()

    def _compute_grade(self, listing_id: str) -> Optional[Dict]:
        """Compute ARGOS GRADE."""
        try:
            from src.cove.argos_grade import compute_argos_grade
            return compute_argos_grade(listing_id, self.db_path)
        except Exception as e:
            self._log(f"  {listing_id}: grade error: {e}")
            return None

    def _generate_dossier(self, listing_id: str, grade_data: dict) -> Optional[str]:
        """Generate PDF dossier."""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / "tools" / "scripts"))
            from pdf_generator_enterprise import generate_dossier_from_db
            output_dir = str(PROJECT_ROOT / "dossiers")
            # For now, use generic dealer name — matching will be added later
            return generate_dossier_from_db(listing_id, "ARGOS Preview", output_dir, self.db_path)
        except Exception as e:
            self._log(f"  {listing_id}: PDF error: {e}")
            return None

    def _transition(self, listing_id: str, from_state: str, to_state: str,
                    action: str, details: dict = None):
        """Transition with logging."""
        if self.dry_run:
            self._log(f"  {listing_id}: {from_state} → {to_state} ({action})")
            self.stats["transitioned"] += 1
            return
        try:
            transition(listing_id, from_state, to_state, action, details, self.db_path)
            self._log(f"  {listing_id}: {from_state} → {to_state} ({action})")
            self.stats["transitioned"] += 1
        except Exception as e:
            self._log(f"  {listing_id}: transition FAILED {from_state}→{to_state}: {e}")
            self.stats["errors"] += 1

    def _log(self, msg: str):
        print(msg)


# ── DB Schema Setup ───────────────────────────────────────────────────────────

def setup_pipeline_schema(db_path: str = DB_PATH):
    """Add pipeline columns + log table. Safe to run multiple times."""
    import duckdb
    con = duckdb.connect(db_path)

    # Add columns to vehicle_listings (idempotent)
    columns_to_add = {
        "pipeline_state": "VARCHAR DEFAULT 'DISCOVERED'",
        "state_updated_at": "TIMESTAMP",
        "seller_contact_sent_at": "TIMESTAMP",
        "seller_followup_count": "INTEGER DEFAULT 0",
        "seller_name": "VARCHAR",
        "seller_email": "VARCHAR",
        "seller_phone": "VARCHAR",
        "matched_dealer": "VARCHAR",
        "dossier_path": "VARCHAR",
    }

    existing = [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='vehicle_listings'"
    ).fetchall()]

    for col, definition in columns_to_add.items():
        if col not in existing:
            con.execute(f"ALTER TABLE vehicle_listings ADD COLUMN {col} {definition}")
            print(f"  Added column: {col}")

    # Create pipeline_log table
    con.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_log (
            id INTEGER,
            listing_id VARCHAR NOT NULL,
            from_state VARCHAR,
            to_state VARCHAR NOT NULL,
            action VARCHAR NOT NULL,
            details VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create sequence for log IDs if not exists
    try:
        con.execute("CREATE SEQUENCE IF NOT EXISTS pipeline_log_seq START 1")
    except Exception:
        pass

    # Set initial state for listings that don't have one
    con.execute("""
        UPDATE vehicle_listings
        SET pipeline_state = 'DISCOVERED'
        WHERE pipeline_state IS NULL
    """)

    print("  Pipeline schema ready.")
    con.close()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ARGOS Pipeline Orchestrator")
    parser.add_argument("--status", action="store_true", help="Show pipeline summary")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--state", type=str, help="Process only this state")
    parser.add_argument("--setup", action="store_true", help="Setup/upgrade DB schema")
    parser.add_argument("--db", type=str, default=DB_PATH, help="DB path")
    args = parser.parse_args()

    if args.setup:
        setup_pipeline_schema(args.db)
        return

    if args.status:
        summary = get_pipeline_summary(args.db)
        print("\n  ARGOS Pipeline Status")
        print("  " + "=" * 40)
        total = sum(summary.values())
        for state, count in sorted(summary.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(count / max(total, 1) * 30)
            print(f"  {state:25s} {count:4d}  {bar}")
        print(f"  {'TOTAL':25s} {total:4d}")
        return

    orch = PipelineOrchestrator(db_path=args.db, dry_run=args.dry_run)
    orch.run(only_state=args.state)


if __name__ == "__main__":
    main()
