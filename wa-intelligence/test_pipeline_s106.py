#!/usr/bin/env python3
"""
test_pipeline_s106.py — E2E test for S106 state machine + template integration.
Tests the full pipeline: outbound guard → send → post-update → inbound → classify → state → template → validate.
Uses a temporary in-memory SQLite DB.
"""

import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state_machine import (
    ensure_state_columns, can_send, increment_outbound,
    process_inbound, get_dealer_state, is_duplicate
)
from templates import fill_template, select_template, select_day1_variant, TEMPLATES
from validator import validate

PASS = 0
FAIL = 0


def check(name, condition, detail=''):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name} — {detail}')


def create_test_db():
    """Create a temporary SQLite DB with schema matching dealer_network.sqlite."""
    fd, path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)
    con = sqlite3.connect(path)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('''CREATE TABLE IF NOT EXISTS conversations (
        dealer_id TEXT PRIMARY KEY,
        dealer_name TEXT,
        phone_number TEXT,
        persona_type TEXT DEFAULT 'RAGIONIERE',
        current_step TEXT DEFAULT 'COLD',
        source TEXT DEFAULT 'AutoScout24',
        brand_focus TEXT DEFAULT 'BMW',
        city TEXT DEFAULT 'Napoli',
        day1_message TEXT,
        conversation_state TEXT DEFAULT 'COLD',
        outbound_count INTEGER DEFAULT 0,
        inbound_count INTEGER DEFAULT 0,
        last_inbound_at TEXT,
        state_updated_at TEXT,
        escalation_flag INTEGER DEFAULT 0,
        last_contact_at TEXT,
        analyzed_at TEXT
    )''')
    con.execute('''CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        dealer_id TEXT,
        dealer_name TEXT,
        phone_number TEXT,
        direction TEXT,
        body TEXT,
        timestamp_it TEXT,
        timestamp_iso TEXT,
        wa_msg_id TEXT,
        processed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )''')
    # Insert test dealer
    con.execute('''INSERT INTO conversations
        (dealer_id, dealer_name, phone_number, persona_type, source, brand_focus, city)
        VALUES ('TEST_001', 'Mario Rossi', '393281536308', 'RAGIONIERE', 'AutoScout24', 'BMW', 'Napoli')
    ''')
    con.commit()
    con.close()
    return path


def test_outbound_flow(db_path):
    """Test: COLD dealer → can_send DAY1 → fill → validate → increment → state transition."""
    print('\n=== TEST OUTBOUND FLOW ===')

    ensure_state_columns(db_path)

    # 1. can_send: COLD + DAY1_INTRO → OK
    ok, reason = can_send(db_path, 'TEST_001', 'DAY1_INTRO')
    check('can_send COLD+DAY1_INTRO', ok, reason)

    # 2. can_send: COLD + VEHICLE_PROPOSAL → BLOCKED (not allowed in COLD)
    ok2, reason2 = can_send(db_path, 'TEST_001', 'VEHICLE_PROPOSAL')
    check('can_send COLD+VEHICLE_PROPOSAL blocked', not ok2, reason2)

    # 3. Fill template
    msg = fill_template('DAY1_PREMIUM', {
        'source': 'AutoScout24',
        'brand_focus': 'BMW',
    })
    check('fill_template DAY1_PREMIUM', len(msg) > 50, f'len={len(msg)}')
    check('fill_template contains Luca', 'Luca Ferretti' in msg)

    # 4. Validate
    result = validate(msg, 'DAY1_PREMIUM', {})
    check('validate DAY1_PREMIUM PASS', result['result'] == 'PASS', result.get('reason', ''))

    # 5. Validate with fee leak
    bad_msg = msg + '\nLa fee e 1.000 euro'
    result2 = validate(bad_msg, 'DAY1_PREMIUM', {})
    check('validate fee leak BLOCK', result2['result'] == 'BLOCK', result2.get('check_failed', ''))

    # 6. Increment outbound + state check
    increment_outbound(db_path, 'TEST_001')
    dealer = get_dealer_state(db_path, 'TEST_001')
    check('outbound_count incremented', dealer.get('outbound_count') == 1)

    # 7. Simulate state transition COLD → CONTACTED
    from state_machine import get_transition, update_state
    new_state = get_transition('COLD', 'OUTBOUND_SENT')
    update_state(db_path, 'TEST_001', new_state)
    dealer2 = get_dealer_state(db_path, 'TEST_001')
    check('state COLD→CONTACTED', dealer2.get('conversation_state') == 'CONTACTED')

    # 8. can_send: CONTACTED + DAY1_INTRO → BLOCKED (not in allowed_templates)
    ok3, reason3 = can_send(db_path, 'TEST_001', 'DAY1_INTRO')
    check('can_send CONTACTED+DAY1_INTRO blocked', not ok3, reason3)

    # 9. can_send: CONTACTED cap reached (1 outbound, max 3 but no inbound yet)
    ok4, reason4 = can_send(db_path, 'TEST_001', 'DAY7_RECOVERY')
    check('can_send CONTACTED+DAY7_RECOVERY', ok4, reason4)


def test_inbound_flow(db_path):
    """Test: dealer responds → classify → process_inbound → state transition → select template."""
    print('\n=== TEST INBOUND FLOW ===')

    # 1. Simulate dealer POSITIVE response
    new_state = process_inbound(db_path, 'TEST_001', 'POSITIVE')
    check('process_inbound POSITIVE → ENGAGED', new_state == 'ENGAGED')

    # 2. Select template for (POSITIVE, ENGAGED)
    tpl_id = select_template('POSITIVE', 'ENGAGED')
    check('select_template POSITIVE+ENGAGED', tpl_id == 'VEHICLE_PROPOSAL', tpl_id)

    # 3. Fill vehicle proposal
    msg = fill_template('VEHICLE_PROPOSAL', {
        'dealer_name': 'Mario',
        'vehicle_brand': 'BMW',
        'vehicle_model': 'X3 xDrive20d',
        'vehicle_year': '2022',
        'km': '45.000',
        'price_eur': '33.500',
        'price_delta': '4.200',
        'city': 'Napoli',
    })
    check('fill VEHICLE_PROPOSAL', 'BMW' in msg and 'Mario' in msg)
    check('fill contains price', '33.500' in msg)

    # 4. Validate vehicle proposal
    result = validate(msg, 'VEHICLE_PROPOSAL', {})
    check('validate VEHICLE_PROPOSAL PASS', result['result'] == 'PASS', result.get('reason', ''))

    # 5. CURIOSITY → IDENTITY_RESPONSE
    new_state2 = process_inbound(db_path, 'TEST_001', 'CURIOSITY')
    check('process_inbound CURIOSITY in ENGAGED', new_state2 == 'ENGAGED')
    tpl2 = select_template('CURIOSITY', 'ENGAGED')
    check('select_template CURIOSITY+ENGAGED', tpl2 == 'IDENTITY_RESPONSE', tpl2)

    # 6. VEHICLE_REQUEST → INTERESTED
    new_state3 = process_inbound(db_path, 'TEST_001', 'VEHICLE_REQUEST')
    check('process_inbound VEHICLE_REQUEST → INTERESTED', new_state3 == 'INTERESTED')


def test_day1_variant_selection():
    """Test DAY1 variant selection based on dealer brands."""
    print('\n=== TEST DAY1 VARIANT SELECTION ===')

    v1 = select_day1_variant(['BMW', 'Mercedes', 'Audi', 'Porsche'])
    check('all premium → DAY1_PREMIUM', v1 == 'DAY1_PREMIUM', v1)

    v2 = select_day1_variant(['BMW', 'Fiat', 'Ford', 'Peugeot'])
    check('mixed → DAY1_MIXED', v2 == 'DAY1_MIXED', v2)

    v3 = select_day1_variant(['Fiat', 'Ford', 'Peugeot', 'Citroen'])
    check('no premium → DAY1_GENERALIST', v3 == 'DAY1_GENERALIST', v3)

    v4 = select_day1_variant([])
    check('empty → DAY1_GENERALIST', v4 == 'DAY1_GENERALIST', v4)


def test_dedup(db_path):
    """Test dedup check."""
    print('\n=== TEST DEDUP ===')

    # Insert a recent outbound message
    con = sqlite3.connect(db_path)
    con.execute('''INSERT INTO messages (id, dealer_id, direction, body, created_at)
        VALUES ('msg_dedup_1', 'TEST_001', 'OUTBOUND', 'Buongiorno, sono Luca Ferretti', datetime('now'))''')
    con.commit()
    con.close()

    is_dup = is_duplicate(db_path, 'TEST_001', 'Buongiorno, sono Luca Ferretti')
    check('is_duplicate same msg', is_dup)

    is_dup2 = is_duplicate(db_path, 'TEST_001', 'Messaggio completamente diverso')
    check('is_duplicate different msg', not is_dup2)


def test_validator_comprehensive():
    """Test all validator checks."""
    print('\n=== TEST VALIDATOR COMPREHENSIVE ===')

    # TECH_LEAK
    r = validate('Abbiamo 28 portali monitorati', 'VEHICLE_PROPOSAL', {})
    check('tech_leak BLOCK', r['result'] == 'BLOCK' and r['check_failed'] == 'TECH_LEAK')

    # BANNED_WORD
    r2 = validate('Il nostro algoritmo trova auto', 'VEHICLE_PROPOSAL', {})
    check('banned_word algoritmo', r2['result'] == 'BLOCK')

    # IDENTITY_INVERSION
    r3 = validate('posso chiederle come ha avuto il mio numero?', 'IDENTITY_RESPONSE', {})
    check('identity_inversion BLOCK', r3['result'] == 'BLOCK')

    # FEE in OBJ_2_FEE → PASS
    r4 = validate('La mia fee e EUR 1.000 a veicolo consegnato', 'OBJ_2_FEE', {})
    check('fee in OBJ_2_FEE PASS', r4['result'] == 'PASS')

    # TOO_LONG
    long_msg = '\n'.join([f'Riga {i}' for i in range(10)])
    r5 = validate(long_msg, 'VEHICLE_PROPOSAL', {})
    check('too_long BLOCK', r5['result'] == 'BLOCK')

    # Clean message PASS
    r6 = validate('Buongiorno Mario, ho trovato una BMW X3 interessante.', 'VEHICLE_PROPOSAL', {})
    check('clean msg PASS', r6['result'] == 'PASS')


def test_template_coverage():
    """Test that all templates in TEMPLATE_MAP have valid template IDs."""
    print('\n=== TEST TEMPLATE COVERAGE ===')
    from templates import TEMPLATE_MAP
    missing = []
    for (intent, state), tpl_id in TEMPLATE_MAP.items():
        if tpl_id not in TEMPLATES:
            missing.append(f'{intent}+{state} → {tpl_id}')
    check('all TEMPLATE_MAP entries have valid templates', len(missing) == 0, str(missing))


def test_outbound_guard_script(db_path):
    """Test outbound_guard.py as subprocess (simulates daemon call)."""
    print('\n=== TEST OUTBOUND_GUARD SCRIPT ===')
    import subprocess

    # Reset dealer to COLD for guard test
    con = sqlite3.connect(db_path)
    con.execute("UPDATE conversations SET conversation_state='COLD', outbound_count=0 WHERE dealer_id='TEST_001'")
    con.commit()
    con.close()

    guard_script = os.path.join(os.path.dirname(__file__), 'outbound_guard.py')

    # Should PASS
    result = subprocess.run(
        [sys.executable, guard_script,
         '--db-path', db_path,
         '--dealer-id', 'TEST_001',
         '--template-id', 'DAY1_INTRO',
         '--message', 'Buongiorno, sono Luca Ferretti. Ho visto il suo salone.'],
        capture_output=True, text=True, timeout=10
    )
    out = json.loads(result.stdout.strip())
    check('outbound_guard PASS', out.get('ok') is True, result.stdout)

    # Should BLOCK (VEHICLE_PROPOSAL not allowed in COLD)
    result2 = subprocess.run(
        [sys.executable, guard_script,
         '--db-path', db_path,
         '--dealer-id', 'TEST_001',
         '--template-id', 'VEHICLE_PROPOSAL',
         '--message', 'BMW X3 2022 per lei'],
        capture_output=True, text=True, timeout=10
    )
    out2 = json.loads(result2.stdout.strip())
    check('outbound_guard BLOCK wrong template', out2.get('ok') is False, result2.stdout)


def test_post_send_script(db_path):
    """Test post_send_update.py as subprocess."""
    print('\n=== TEST POST_SEND_UPDATE SCRIPT ===')
    import subprocess

    # Reset dealer to COLD
    con = sqlite3.connect(db_path)
    con.execute("UPDATE conversations SET conversation_state='COLD', outbound_count=0 WHERE dealer_id='TEST_001'")
    con.commit()
    con.close()

    post_script = os.path.join(os.path.dirname(__file__), 'post_send_update.py')
    result = subprocess.run(
        [sys.executable, post_script,
         '--db-path', db_path,
         '--dealer-id', 'TEST_001',
         '--template-id', 'DAY1_INTRO'],
        capture_output=True, text=True, timeout=10
    )
    out = json.loads(result.stdout.strip())
    check('post_send_update ok', out.get('ok') is True, result.stdout)
    check('post_send_update → CONTACTED', out.get('new_state') == 'CONTACTED', out.get('new_state'))
    check('post_send_update outbound_count=1', out.get('outbound_count') == 1)


if __name__ == '__main__':
    print('=' * 60)
    print('S106 E2E Pipeline Test')
    print('=' * 60)

    db_path = create_test_db()
    print(f'Test DB: {db_path}')

    try:
        test_outbound_flow(db_path)
        test_inbound_flow(db_path)
        test_day1_variant_selection()
        test_dedup(db_path)
        test_validator_comprehensive()
        test_template_coverage()
        test_outbound_guard_script(db_path)
        test_post_send_script(db_path)
    finally:
        os.unlink(db_path)

    print(f'\n{"=" * 60}')
    print(f'RESULTS: {PASS} passed, {FAIL} failed')
    print(f'{"=" * 60}')

    sys.exit(0 if FAIL == 0 else 1)
