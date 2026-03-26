"""
pipeline_states.py — ARGOS Pipeline State Machine
CoVe 2026 | Enterprise Grade

7-state pipeline for processing vehicles from raw listing to dealer delivery.
Based on deep research of ACV Auctions, Manheim, BCA, AUTO1 patterns.

States:
  DISCOVERED → SCORED → ENRICHED → SELLER_CONTACTED → DATA_COMPLETE → DOSSIER_READY → DELIVERED

Terminal states: REJECTED, ABANDONED, PARKED

4 Quality Gates prevent low-quality output from reaching dealers.

Usage:
  from src.cove.pipeline_states import transition, get_state, gate_check, STATES
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple

# ── State Definitions ─────────────────────────────────────────────────────────

STATES = {
    # Active states (vehicle progressing)
    "DISCOVERED":        "Raw listing found by scraper",
    "SCORED":            "CoVe scored — has confidence, fraud, recommendation",
    "ENRICHED":          "Detail page scraped — specs, VIN attempt, images",
    "SELLER_CONTACTED":  "Email sent to EU seller, awaiting response",
    "DATA_COMPLETE":     "Sufficient data for dossier generation",
    "DOSSIER_READY":     "PDF generated, images sanitized, matched to dealer",
    "DELIVERED":         "Dossier sent to dealer, tracking conversion",
    # Terminal states
    "REJECTED":          "Failed Gate 1 — low score, SKIP, or suspicious",
    "ABANDONED":         "Seller never responded after 14 days + 2 follow-ups",
    "PARKED":            "Passed scoring but failed Gate 3 — low margin or grade",
    "ERROR":             "Technical failure — retry with backoff",
}

# Valid transitions: {from_state: [to_state, ...]}
VALID_TRANSITIONS = {
    "DISCOVERED":        ["SCORED", "REJECTED", "ERROR"],
    "SCORED":            ["ENRICHED", "REJECTED"],
    "ENRICHED":          ["SELLER_CONTACTED", "DATA_COMPLETE", "ERROR"],
    "SELLER_CONTACTED":  ["DATA_COMPLETE", "ABANDONED", "ERROR"],
    "DATA_COMPLETE":     ["DOSSIER_READY", "PARKED"],
    "DOSSIER_READY":     ["DELIVERED"],
    "DELIVERED":         [],  # Terminal
    "REJECTED":          [],  # Terminal
    "ABANDONED":         ["DISCOVERED"],  # Can retry after 30 days
    "PARKED":            ["DATA_COMPLETE"],  # Re-check if market changes
    "ERROR":             ["DISCOVERED"],  # Retry
}

# ── Gate Definitions ──────────────────────────────────────────────────────────

# Gate 1: DISCOVERED → SCORED → ENRICHED
GATE1_MIN_CONFIDENCE = 0.65
GATE1_ALLOWED_RECOMMENDATIONS = {"PROCEED"}
GATE1_BLOCKED_FRAUD = {"SUSPICIOUS"}

# Gate 2: SELLER_CONTACTED → DATA_COMPLETE (timeout rules)
GATE2_FOLLOWUP1_DAYS = 3
GATE2_FOLLOWUP2_DAYS = 7
GATE2_ABANDON_DAYS = 14
GATE2_AUTO_COMPLETE_PHOTOS = 6  # Skip seller contact if already have enough

# Gate 3: DATA_COMPLETE → DOSSIER_READY
GATE3_MIN_GRADE = "C"  # A, B, C pass — D, E blocked
GATE3_MIN_PHOTOS = 4
GATE3_MIN_MARGIN = 2500  # EUR

# Gate 4: DOSSIER_READY → DELIVERED (human review — no automation)

GRADE_ORDER = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}


def gate1_check(recommendation: str, confidence: float, fraud_overall: str) -> Tuple[bool, str]:
    """
    Gate 1: Should this listing be enriched?
    Returns (passed, reason)
    """
    if recommendation not in GATE1_ALLOWED_RECOMMENDATIONS:
        return False, f"recommendation={recommendation} (need PROCEED)"
    if confidence < GATE1_MIN_CONFIDENCE:
        return False, f"confidence={confidence:.2f} (need >={GATE1_MIN_CONFIDENCE})"
    if fraud_overall in GATE1_BLOCKED_FRAUD:
        return False, f"fraud={fraud_overall} (SUSPICIOUS blocked)"
    return True, "PROCEED + confidence OK + fraud OK"


def gate2_check(photo_count: int, days_since_contact: int, followup_count: int,
                critical_fields_filled: int, total_critical: int = 7) -> Tuple[str, str]:
    """
    Gate 2: What should happen to a SELLER_CONTACTED listing?
    Returns (action, reason) where action is:
      "COMPLETE" — enough data, proceed
      "FOLLOWUP1" — send first follow-up
      "FOLLOWUP2" — send second follow-up
      "ABANDON" — give up
      "WAIT" — keep waiting
    """
    # Auto-complete without seller if we already have enough
    if photo_count >= GATE2_AUTO_COMPLETE_PHOTOS and critical_fields_filled >= total_critical * 0.7:
        return "COMPLETE", f"photos={photo_count} fields={critical_fields_filled}/{total_critical} — sufficient without seller"

    if days_since_contact >= GATE2_ABANDON_DAYS:
        return "ABANDON", f"14+ days, {followup_count} follow-ups sent"
    if days_since_contact >= GATE2_FOLLOWUP2_DAYS and followup_count < 2:
        return "FOLLOWUP2", f"7+ days, sending follow-up 2"
    if days_since_contact >= GATE2_FOLLOWUP1_DAYS and followup_count < 1:
        return "FOLLOWUP1", f"3+ days, sending follow-up 1"
    return "WAIT", f"day {days_since_contact}, {followup_count} follow-ups"


def gate3_check(grade: str, photo_count: int, estimated_margin: float) -> Tuple[bool, str]:
    """
    Gate 3: Is this vehicle worth a dossier?
    Returns (passed, reason)
    """
    reasons = []
    passed = True

    grade_val = GRADE_ORDER.get(grade, 0)
    min_grade_val = GRADE_ORDER.get(GATE3_MIN_GRADE, 3)
    if grade_val < min_grade_val:
        passed = False
        reasons.append(f"grade={grade} (need >={GATE3_MIN_GRADE})")

    if photo_count < GATE3_MIN_PHOTOS:
        passed = False
        reasons.append(f"photos={photo_count} (need >={GATE3_MIN_PHOTOS})")

    if estimated_margin < GATE3_MIN_MARGIN:
        passed = False
        reasons.append(f"margin=EUR{estimated_margin:.0f} (need >={GATE3_MIN_MARGIN})")

    if passed:
        return True, f"grade={grade} photos={photo_count} margin=EUR{estimated_margin:.0f}"
    return False, " | ".join(reasons)


# ── State Transition ──────────────────────────────────────────────────────────

def transition(listing_id: str, from_state: str, to_state: str,
               action: str, details: dict = None, db_path: str = None) -> bool:
    """
    Atomically transition a listing and log it.
    Returns True on success, raises on invalid transition.
    """
    import duckdb
    from pathlib import Path

    if db_path is None:
        db_path = str(Path(__file__).parent / "data" / "cove_tracker.duckdb")

    # Validate transition
    if to_state not in VALID_TRANSITIONS.get(from_state, []):
        raise ValueError(f"Invalid transition: {from_state} → {to_state}")

    now = datetime.now(timezone.utc).isoformat()

    con = duckdb.connect(db_path)
    try:
        # Verify current state
        current = con.execute(
            "SELECT pipeline_state FROM vehicle_listings WHERE listing_id = ?",
            [listing_id]
        ).fetchone()

        if not current:
            raise ValueError(f"Listing {listing_id} not found in vehicle_listings")
        if current[0] != from_state:
            raise ValueError(f"State mismatch: expected {from_state}, got {current[0]}")

        # Update state
        con.execute("""
            UPDATE vehicle_listings
            SET pipeline_state = ?, state_updated_at = ?
            WHERE listing_id = ?
        """, [to_state, now, listing_id])

        # Log transition
        con.execute("""
            INSERT INTO pipeline_log (listing_id, from_state, to_state, action, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [listing_id, from_state, to_state, action,
              json.dumps(details) if details else None, now])

        return True
    finally:
        con.close()


def get_state(listing_id: str, db_path: str = None) -> Optional[str]:
    """Get current pipeline state for a listing."""
    import duckdb
    from pathlib import Path

    if db_path is None:
        db_path = str(Path(__file__).parent / "data" / "cove_tracker.duckdb")

    con = duckdb.connect(db_path, read_only=True)
    try:
        row = con.execute(
            "SELECT pipeline_state FROM vehicle_listings WHERE listing_id = ?",
            [listing_id]
        ).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def get_pipeline_summary(db_path: str = None) -> Dict:
    """Get count of vehicles in each state."""
    import duckdb
    from pathlib import Path

    if db_path is None:
        db_path = str(Path(__file__).parent / "data" / "cove_tracker.duckdb")

    con = duckdb.connect(db_path, read_only=True)
    try:
        rows = con.execute("""
            SELECT pipeline_state, COUNT(*) as cnt
            FROM vehicle_listings
            GROUP BY pipeline_state
            ORDER BY cnt DESC
        """).fetchall()
        return {row[0]: row[1] for row in rows}
    finally:
        con.close()
