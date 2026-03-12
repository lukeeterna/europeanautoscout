"""
CoVe v4 Tracker — DuckDB-based verification tracking
======================================================

Tracks CoVe verification results and dealer acceptance outcomes.
Enables performance measurement: confidence with/without VIN verification.

Usage:
    from python.cove.cove_tracker import CoveV4Tracker
    
    tracker = CoveV4Tracker()
    tracker.record("listing_123", 0.85, had_vin=True, fraud_flags=0)
    tracker.mark_accepted("listing_123")
    stats = tracker.get_stats()
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import duckdb

logger = logging.getLogger(__name__)

# Default path for DuckDB file
DEFAULT_DB_PATH = "data/cove_tracker.duckdb"


class CoveV4Tracker:
    """
    Tracks CoVe v4 verification results and dealer outcomes.
    
    Schema:
        - listing_id: VARCHAR (primary key)
        - had_vin: BOOLEAN (whether VIN was verified)
        - confidence_score: FLOAT (0.0-1.0)
        - dealer_accepted: BOOLEAN (whether dealer accepted the listing)
        - fraud_flags: INTEGER (count of fraud indicators)
        - ts: TIMESTAMP (default: now())
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Initialize tracker with DuckDB.
        
        Args:
            db_path: Path to DuckDB file (creates if not exists)
        """
        self.db_path = db_path
        self._ensure_db_path()
        self._init_schema()

    def _ensure_db_path(self):
        """Create directory if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """Initialize DuckDB schema if not exists."""
        conn = duckdb.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cove_verifications (
                    listing_id VARCHAR PRIMARY KEY,
                    had_vin BOOLEAN NOT NULL,
                    confidence_score DOUBLE NOT NULL,
                    dealer_accepted BOOLEAN DEFAULT FALSE,
                    fraud_flags INTEGER DEFAULT 0,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cove_had_vin 
                ON cove_verifications(had_vin)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cove_dealer_accepted 
                ON cove_verifications(dealer_accepted)
            """)
            
            conn.commit()
            logger.info(f"CoVe tracker initialized: {self.db_path}")
        finally:
            conn.close()

    def record(
        self,
        listing_id: str,
        confidence_score: float,
        had_vin: bool,
        fraud_flags: int = 0,
    ) -> bool:
        """
        Record a verification result.
        
        Args:
            listing_id: Unique listing identifier
            confidence_score: CoVe confidence (0.0-1.0)
            had_vin: Whether VIN was verified
            fraud_flags: Count of fraud indicators detected
            
        Returns:
            True if recorded successfully
        """
        conn = duckdb.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO cove_verifications 
                (listing_id, had_vin, confidence_score, fraud_flags, ts)
                VALUES (?, ?, ?, ?, ?)
            """, [listing_id, had_vin, confidence_score, fraud_flags, datetime.utcnow()])
            conn.commit()
            
            logger.info(
                f"Recorded: {listing_id} | confidence={confidence_score:.2f} | "
                f"had_vin={had_vin} | fraud_flags={fraud_flags}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to record {listing_id}: {e}")
            return False
        finally:
            conn.close()

    def mark_accepted(self, listing_id: str) -> bool:
        """
        Mark a listing as accepted by dealer.
        
        Args:
            listing_id: Unique listing identifier
            
        Returns:
            True if updated successfully
        """
        conn = duckdb.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE cove_verifications 
                SET dealer_accepted = TRUE 
                WHERE listing_id = ?
            """, [listing_id])
            conn.commit()
            
            rows = conn.execute("SELECT changes()").fetchone()[0]
            if rows > 0:
                logger.info(f"Marked accepted: {listing_id}")
                return True
            else:
                logger.warning(f"Listing not found: {listing_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to mark accepted {listing_id}: {e}")
            return False
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics on verification performance.
        
        Returns:
            Dict with:
            - total_verifications: int
            - avg_confidence_with_vin: float
            - avg_confidence_without_vin: float
            - acceptance_rate_with_vin: float
            - acceptance_rate_without_vin: float
            - fraud_rate: float
        """
        conn = duckdb.connect(self.db_path)
        try:
            # Total count
            total = conn.execute(
                "SELECT COUNT(*) FROM cove_verifications"
            ).fetchone()[0]
            
            if total == 0:
                return {
                    "total_verifications": 0,
                    "avg_confidence_with_vin": 0.0,
                    "avg_confidence_without_vin": 0.0,
                    "acceptance_rate_with_vin": 0.0,
                    "acceptance_rate_without_vin": 0.0,
                    "fraud_rate": 0.0,
                }

            # Avg confidence WITH VIN
            avg_with_vin = conn.execute("""
                SELECT AVG(confidence_score) 
                FROM cove_verifications 
                WHERE had_vin = TRUE
            """).fetchone()[0] or 0.0

            # Avg confidence WITHOUT VIN
            avg_without_vin = conn.execute("""
                SELECT AVG(confidence_score) 
                FROM cove_verifications 
                WHERE had_vin = FALSE
            """).fetchone()[0] or 0.0

            # Acceptance rate WITH VIN
            accept_with_vin = conn.execute("""
                SELECT AVG(CASE WHEN dealer_accepted THEN 1.0 ELSE 0.0 END)
                FROM cove_verifications 
                WHERE had_vin = TRUE
            """).fetchone()[0] or 0.0

            # Acceptance rate WITHOUT VIN
            accept_without_vin = conn.execute("""
                SELECT AVG(CASE WHEN dealer_accepted THEN 1.0 ELSE 0.0 END)
                FROM cove_verifications 
                WHERE had_vin = FALSE
            """).fetchone()[0] or 0.0

            # Fraud rate
            fraud_rate = conn.execute("""
                SELECT AVG(CASE WHEN fraud_flags > 0 THEN 1.0 ELSE 0.0 END)
                FROM cove_verifications
            """).fetchone()[0] or 0.0

            # Count with/without VIN
            count_with_vin = conn.execute("""
                SELECT COUNT(*) FROM cove_verifications WHERE had_vin = TRUE
            """).fetchone()[0]
            
            count_without_vin = conn.execute("""
                SELECT COUNT(*) FROM cove_verifications WHERE had_vin = FALSE
            """).fetchone()[0]

            return {
                "total_verifications": total,
                "count_with_vin": count_with_vin,
                "count_without_vin": count_without_vin,
                "avg_confidence_with_vin": round(avg_with_vin, 3),
                "avg_confidence_without_vin": round(avg_without_vin, 3),
                "acceptance_rate_with_vin": round(accept_with_vin, 3),
                "acceptance_rate_without_vin": round(accept_without_vin, 3),
                "fraud_rate": round(fraud_rate, 3),
            }
        finally:
            conn.close()

    def get_dataframe(self):
        """
        Get all verifications as DataFrame.
        
        Returns:
            duckdb.DataFrame with all records
        """
        conn = duckdb.connect(self.db_path)
        try:
            df = conn.execute("""
                SELECT * FROM cove_verifications 
                ORDER BY ts DESC
            """).df()
            return df
        finally:
            conn.close()

    def get_pending_acceptance(self) -> List[Dict[str, Any]]:
        """
        Get listings that haven't been marked as accepted yet.
        
        Returns:
            List of dicts with listing details
        """
        conn = duckdb.connect(self.db_path)
        try:
            results = conn.execute("""
                SELECT * FROM cove_verifications 
                WHERE dealer_accepted = FALSE 
                ORDER BY ts DESC
                LIMIT 100
            """).fetchall()
            
            return [
                {
                    "listing_id": r[0],
                    "had_vin": r[1],
                    "confidence_score": r[2],
                    "dealer_accepted": r[3],
                    "fraud_flags": r[4],
                    "ts": r[5].isoformat() if r[5] else None,
                }
                for r in results
            ]
        finally:
            conn.close()

    def close(self):
        """Close connections (no-op for DuckDB)."""
        pass


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main():
    """CLI for quick testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CoVe v4 Tracker CLI")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="DB path")
    parser.add_argument("--record", nargs=4, metavar=("ID", "SCORE", "VIN", "FLAGS"),
                       help="Record: listing_id score had_vin(0/1) fraud_flags")
    parser.add_argument("--accept", metavar="ID", help="Mark as accepted")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--pending", action="store_true", help="Show pending")
    
    args = parser.parse_args()
    
    tracker = CoveV4Tracker(db_path=args.db)
    
    if args.record:
        listing_id, score, had_vin, flags = args.record
        tracker.record(
            listing_id, 
            float(score), 
            had_vin == "1", 
            int(flags)
        )
        print(f"✓ Recorded {listing_id}")
    
    if args.accept:
        tracker.mark_accepted(args.accept)
        print(f"✓ Marked accepted: {args.accept}")
    
    if args.stats:
        import json
        print(json.dumps(tracker.get_stats(), indent=2))
    
    if args.pending:
        import json
        print(json.dumps(tracker.get_pending_acceptance(), indent=2))
    
    tracker.close()


if __name__ == "__main__":
    main()
