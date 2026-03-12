#!/usr/bin/env python3.11
"""
PILOT TEST LEAD — SESSION 26
Mock lead per validare workflow end-to-end con enhanced presentation
"""

import duckdb
from pathlib import Path

# Database path
db_path = Path("python/dealer/dealer_network.duckdb")

# Creo mock lead per pilot test
lead_data = {
    'business_name': 'TEST DEALER - Centro BMW Premium',
    'city': 'Napoli',
    'region': 'Campania',
    'phone': '+39 081 123 4567',
    'email': 'test.pilot@centrobmwpremium.it',
    'website': 'https://www.centrobmwpremium.it',
    'address': 'Via Roma 123, Napoli',
    'contact_person': 'Mario Rossi',
    'tier': 1,
    'target_flag': True,
    'business_score': 89,
    'notes': 'MOCK LEAD - Session 26 Pilot Test - Enhanced Presentation Validation'
}

print("=== SESSION 26 PILOT TEST LEAD ===")
print(f"Creating mock lead: {lead_data['business_name']}")

# Create database and table
con = duckdb.connect(str(db_path))

con.execute("""
    CREATE TABLE IF NOT EXISTS dealer_leads (
        id INTEGER,
        business_name VARCHAR NOT NULL,
        city VARCHAR NOT NULL,
        region VARCHAR NOT NULL,
        phone VARCHAR,
        email VARCHAR,
        website VARCHAR,
        address VARCHAR,
        contact_person VARCHAR,
        tier INTEGER DEFAULT 1,
        target_flag BOOLEAN DEFAULT FALSE,
        business_score INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_contact TIMESTAMP,
        status VARCHAR DEFAULT 'new'
    )
""")

# Insert mock lead
con.execute("""
    INSERT INTO dealer_leads
    (id, business_name, city, region, phone, email, website, address, contact_person, tier, target_flag, business_score, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", [
    300,  # Manual ID (unique)
    lead_data['business_name'], lead_data['city'], lead_data['region'],
    lead_data['phone'], lead_data['email'], lead_data['website'],
    lead_data['address'], lead_data['contact_person'], lead_data['tier'],
    lead_data['target_flag'], lead_data['business_score'], lead_data['notes']
])

# Verify
count = con.execute("SELECT COUNT(*) FROM dealer_leads").fetchone()[0]
lead = con.execute("SELECT * FROM dealer_leads WHERE business_name LIKE 'TEST DEALER%'").fetchone()

print(f"✅ Mock lead created successfully")
print(f"📊 Total leads in database: {count}")
print(f"🏢 Test dealer: {lead[1]} ({lead[2]})")
print(f"📧 Email: {lead[5]}")
print(f"⭐ Business score: {lead[11]}")

con.close()
print("\n🚀 Ready for pilot test!")