#!/usr/bin/env python3.11
"""
Mario Deployment Setup — P1 Priority Unblock
============================================

Session 32: Inserisce Mario Orefice in DuckDB + seed BMW 330i data per deployment immediato.

Target: Mario Orefice, Direttore amministrativo Mariauto Srl Napoli
Contact: +393336142544 (verified official website)
Vehicle: BMW 330i 2020, €27,800, 45,200 km, ARGOS Score 89/100
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

import duckdb

# Ensure we can import from python/ directory
sys.path.insert(0, str(Path(__file__).parent / "python"))

from cove.cove_tracker import CoveV4Tracker

# Configuration
DB_PATH = "python/cove/data/cove_tracker.duckdb"
MARIO_CONTACT = "+393336142544"
MARIO_COMPANY = "Mariauto Srl"
MARIO_NAME = "Mario Orefice"
MARIO_ROLE = "Direttore amministrativo"
MARIO_LOCATION = "Napoli"

# BMW 330i ARGOS data
BMW_LISTING_ID = "MARIO_BMW_330i_2020_20260310"
BMW_CONFIDENCE = 0.89  # ARGOS Score 89/100
BMW_PRICE = 27800
BMW_KM = 45200
BMW_YEAR = 2020
BMW_MAKE_MODEL = "BMW 330i"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_contacts_table(db_path: str) -> bool:
    """Create contacts table for WhatsApp deployment tracking."""
    conn = duckdb.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dealer_contacts (
                contact_id VARCHAR PRIMARY KEY,
                phone_number VARCHAR UNIQUE NOT NULL,
                contact_name VARCHAR NOT NULL,
                company VARCHAR NOT NULL,
                role VARCHAR,
                location VARCHAR,
                status VARCHAR DEFAULT 'ACTIVE',
                source VARCHAR DEFAULT 'CoVe',
                first_contact TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_contact TIMESTAMP,
                conversion_stage VARCHAR DEFAULT 'LEAD',
                notes TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_assignments (
                assignment_id VARCHAR PRIMARY KEY,
                contact_id VARCHAR NOT NULL,
                listing_id VARCHAR NOT NULL,
                make_model VARCHAR NOT NULL,
                year INTEGER,
                price_eur INTEGER,
                km INTEGER,
                argos_confidence DOUBLE,
                assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR DEFAULT 'ASSIGNED',
                response_received BOOLEAN DEFAULT FALSE,
                conversion_outcome VARCHAR,
                FOREIGN KEY (contact_id) REFERENCES dealer_contacts(contact_id),
                FOREIGN KEY (listing_id) REFERENCES cove_verifications(listing_id)
            )
        """)

        conn.commit()
        logger.info("✓ Contact tables created successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False
    finally:
        conn.close()

def insert_mario_contact(db_path: str) -> bool:
    """Insert Mario Orefice contact information."""
    conn = duckdb.connect(db_path)
    try:
        # Insert Mario's contact (delete first to handle constraints)
        conn.execute("DELETE FROM dealer_contacts WHERE phone_number = ?", [MARIO_CONTACT])

        conn.execute("""
            INSERT INTO dealer_contacts
            (contact_id, phone_number, contact_name, company, role, location, source, conversion_stage, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            f"MARIO_{datetime.now().strftime('%Y%m%d')}",
            MARIO_CONTACT,
            MARIO_NAME,
            MARIO_COMPANY,
            MARIO_ROLE,
            MARIO_LOCATION,
            "CoVe Session 31 Verified",
            "CRISIS_RECOVERY",
            "Data inconsistency crisis (45,200 km) - requires professional recovery deployment"
        ])

        conn.commit()
        logger.info(f"✓ Mario contact inserted: {MARIO_CONTACT}")
        return True

    except Exception as e:
        logger.error(f"Failed to insert Mario contact: {e}")
        return False
    finally:
        conn.close()

def seed_bmw_data(db_path: str) -> bool:
    """Seed BMW 330i data for Mario deployment tracking."""
    # First record in CoVe verification system
    tracker = CoveV4Tracker(db_path)
    success = tracker.record(
        listing_id=BMW_LISTING_ID,
        confidence_score=BMW_CONFIDENCE,
        had_vin=False,  # No VIN check performed yet
        fraud_flags=0   # No fraud indicators
    )

    if not success:
        return False

    # Then create vehicle assignment
    conn = duckdb.connect(db_path)
    try:
        # Delete existing assignment first
        conn.execute("DELETE FROM vehicle_assignments WHERE listing_id = ?", [BMW_LISTING_ID])

        conn.execute("""
            INSERT INTO vehicle_assignments
            (assignment_id, contact_id, listing_id, make_model, year, price_eur, km, argos_confidence, status, conversion_outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            f"MARIO_BMW_ASSIGNMENT_{datetime.now().strftime('%Y%m%d')}",
            f"MARIO_{datetime.now().strftime('%Y%m%d')}",
            BMW_LISTING_ID,
            BMW_MAKE_MODEL,
            BMW_YEAR,
            BMW_PRICE,
            BMW_KM,
            BMW_CONFIDENCE,
            "CRISIS_RECOVERY",
            "PENDING_RECOVERY"
        ])

        conn.commit()
        logger.info(f"✓ BMW 330i assignment created for Mario")
        return True

    except Exception as e:
        logger.error(f"Failed to create BMW assignment: {e}")
        return False
    finally:
        conn.close()

def verify_mario_deployment_ready(db_path: str) -> bool:
    """Verify Mario deployment data is ready."""
    conn = duckdb.connect(db_path)
    try:
        # Check Mario contact
        mario_contact = conn.execute("""
            SELECT contact_name, phone_number, company, conversion_stage
            FROM dealer_contacts
            WHERE phone_number = ?
        """, [MARIO_CONTACT]).fetchone()

        if not mario_contact:
            logger.error("Mario contact not found in database")
            return False

        # Check BMW assignment
        bmw_assignment = conn.execute("""
            SELECT assignment_id, make_model, price_eur, km, status
            FROM vehicle_assignments
            WHERE contact_id LIKE 'MARIO_%'
            AND listing_id = ?
        """, [BMW_LISTING_ID]).fetchone()

        if not bmw_assignment:
            logger.error("BMW assignment not found in database")
            return False

        # Check CoVe verification
        cove_verification = conn.execute("""
            SELECT listing_id, confidence_score, fraud_flags
            FROM cove_verifications
            WHERE listing_id = ?
        """, [BMW_LISTING_ID]).fetchone()

        if not cove_verification:
            logger.error("CoVe verification not found in database")
            return False

        logger.info("🚀 MARIO DEPLOYMENT READY:")
        logger.info(f"   Contact: {mario_contact[0]} ({mario_contact[1]})")
        logger.info(f"   Company: {mario_contact[2]}")
        logger.info(f"   Stage: {mario_contact[3]}")
        logger.info(f"   Vehicle: {bmw_assignment[1]} - €{bmw_assignment[2]:,} - {bmw_assignment[3]:,} km")
        logger.info(f"   ARGOS Score: {cove_verification[1]:.0%}")
        logger.info(f"   Status: {bmw_assignment[4]}")

        return True

    except Exception as e:
        logger.error(f"Failed to verify deployment readiness: {e}")
        return False
    finally:
        conn.close()

def main():
    """Execute Mario deployment setup sequence."""
    logger.info("🚨 P1 PRIORITY: Mario Deployment Setup")
    logger.info("="*50)

    # Step 1: Create tables if needed
    logger.info("Step 1: Creating contact tables...")
    if not create_contacts_table(DB_PATH):
        logger.error("Failed to create tables - ABORT")
        return False

    # Step 2: Insert Mario contact
    logger.info("Step 2: Inserting Mario contact...")
    if not insert_mario_contact(DB_PATH):
        logger.error("Failed to insert Mario - ABORT")
        return False

    # Step 3: Seed BMW data
    logger.info("Step 3: Seeding BMW 330i data...")
    if not seed_bmw_data(DB_PATH):
        logger.error("Failed to seed BMW data - ABORT")
        return False

    # Step 4: Verify deployment readiness
    logger.info("Step 4: Verifying deployment readiness...")
    if not verify_mario_deployment_ready(DB_PATH):
        logger.error("Deployment verification failed - ABORT")
        return False

    logger.info("✅ MARIO DEPLOYMENT SETUP COMPLETE")
    logger.info("🎯 READY FOR: WhatsApp crisis recovery execution")
    logger.info(f"📱 Target: {MARIO_CONTACT}")
    logger.info(f"🚗 Vehicle: {BMW_MAKE_MODEL} {BMW_YEAR} - €{BMW_PRICE:,}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)