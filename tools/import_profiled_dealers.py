#!/usr/bin/env python3
"""
import_profiled_dealers.py — Importa dealer profilati nel DB conversations.
Legge s106_dealer_profiled_30.json e inserisce/aggiorna nel SQLite.

Usage:
    python3 tools/import_profiled_dealers.py [--db-path PATH] [--dry-run]
"""

import argparse
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wa-intelligence'))
from state_machine import ensure_state_columns


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-path', default=os.path.expanduser(
        '~/Documents/app-antigravity-auto/dealer_network.sqlite'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'research', 's106_dealer_profiled_30.json')

    with open(input_path) as f:
        dealers = json.load(f)

    if args.dry_run:
        print(f'[DRY RUN] Would import {len(dealers)} dealers into {args.db_path}')
        for d in dealers:
            print(f'  {d["dealer_id"]:25s} | {d["name"]:30s} | {d["archetype"]:12s} | {d["day1_variant"]}')
        return

    con = sqlite3.connect(args.db_path, timeout=10)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=10000')

    # Ensure state machine columns exist
    ensure_state_columns(args.db_path)

    # Ensure profile columns exist
    profile_cols = [
        "ALTER TABLE conversations ADD COLUMN brand_focus TEXT",
        "ALTER TABLE conversations ADD COLUMN day1_variant TEXT",
        "ALTER TABLE conversations ADD COLUMN archetype TEXT",
        "ALTER TABLE conversations ADD COLUMN premium_pct REAL",
        "ALTER TABLE conversations ADD COLUMN brands TEXT",
        "ALTER TABLE conversations ADD COLUMN city TEXT",
        "ALTER TABLE conversations ADD COLUMN fit_score REAL",
    ]
    for sql in profile_cols:
        try:
            con.execute(sql)
        except sqlite3.OperationalError:
            pass  # column already exists

    inserted = 0
    updated = 0

    for d in dealers:
        # Check if dealer already exists
        existing = con.execute(
            'SELECT dealer_id FROM conversations WHERE dealer_id = ?',
            [d['dealer_id']]
        ).fetchone()

        brands_json = json.dumps(d['brands'])

        if existing:
            # Update profile fields
            con.execute('''UPDATE conversations SET
                dealer_name = ?, phone_number = ?, persona_type = ?,
                source = ?, brand_focus = ?, day1_variant = ?,
                archetype = ?, premium_pct = ?, brands = ?,
                city = ?, fit_score = ?
                WHERE dealer_id = ?''', [
                d['name'], d['phone_wa'], d['archetype'],
                d['source_found'], d['brand_focus'], d['day1_variant'],
                d['archetype'], d['premium_pct'], brands_json,
                d['city'], d['fit_score'], d['dealer_id']
            ])
            updated += 1
        else:
            # Insert new dealer
            con.execute('''INSERT INTO conversations
                (dealer_id, dealer_name, phone_number, persona_type,
                 source, brand_focus, day1_variant, archetype,
                 premium_pct, brands, city, fit_score,
                 conversation_state, outbound_count, inbound_count,
                 current_step)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COLD', 0, 0, 'NEW')''', [
                d['dealer_id'], d['name'], d['phone_wa'], d['archetype'],
                d['source_found'], d['brand_focus'], d['day1_variant'],
                d['archetype'], d['premium_pct'], brands_json,
                d['city'], d['fit_score']
            ])
            inserted += 1

    con.commit()
    con.close()

    print(f'Importazione completata: {inserted} inseriti, {updated} aggiornati')
    print(f'DB: {args.db_path}')


if __name__ == '__main__':
    main()
