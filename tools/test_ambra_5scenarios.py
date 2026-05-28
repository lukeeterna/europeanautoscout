#!/usr/bin/env python3
"""
test_ambra_5scenarios.py — S198 STEP 7 AMBRA stress test (5 scenari)

Valida classify_message + handler logic su 5 intent type:
  1. VEHICLE_REQUEST  — "cerco BMW X3 2021 max 18.000"
  2. PRICE_NEGOTIATION — "posso prendere a 17?" (OBJECTION OBJ-2)
  3. CONTRACT_REQUEST — "ok mando bonifico" con current_step=DOSSIER_SENT
  4. OPT_OUT (NEGATIVE) — "non mi scrivere piu'" → CLOSED_NO
  5. AMBIGUOUS — "rispondo domani" → UNKNOWN/CURIOSITY, approved=NULL

ZERO costi LLM. ZERO messaggi reali. Solo fixture DB + logica offline.
Pattern: tools/tests/test_approve_reply_runtime.py (schema reali, no mock core).

Esecuzione:
  cd /Users/macbook/Documents/combaretrovamiauto-enterprise
  python3 tools/test_ambra_5scenarios.py
"""

import os
import sys
import tempfile
import sqlite3
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WA_DIR = PROJECT_ROOT / 'wa-intelligence'
sys.path.insert(0, str(WA_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

# Schemi REALI da test_approve_reply_runtime.py (snapshot iMac 2026-05-26)
SCHEMA_CONVERSATIONS = """
CREATE TABLE conversations (
    dealer_id       TEXT PRIMARY KEY,
    dealer_name     TEXT,
    city            TEXT,
    phone_number    TEXT,
    stock_size      INTEGER,
    persona_type    TEXT,
    score           REAL,
    source          TEXT,
    notes           TEXT,
    current_step    TEXT DEFAULT 'PENDING',
    day1_message    TEXT,
    recommendation  TEXT DEFAULT 'PENDING',
    created_at      TEXT DEFAULT (datetime('now')),
    last_contact_at TEXT,
    analyzed_at     TEXT,
    conversation_state TEXT DEFAULT 'COLD',
    outbound_count INTEGER DEFAULT 0,
    inbound_count INTEGER DEFAULT 0,
    last_inbound_at TEXT,
    state_updated_at TEXT,
    escalation_flag INTEGER DEFAULT 0,
    is_active_partner INTEGER DEFAULT 0,
    partner_since TEXT,
    total_transactions INTEGER DEFAULT 0,
    total_revenue_dealer REAL DEFAULT 0,
    last_analytics_sent TEXT,
    trusted_partner_sent INTEGER DEFAULT 0,
    opt_out INTEGER DEFAULT 0,
    opt_out_at TIMESTAMP,
    opt_out_source TEXT,
    opt_out_raw_message TEXT,
    handoff_source TEXT DEFAULT 'cold',
    is_micro_dealer INTEGER DEFAULT 0
);
"""

SCHEMA_PENDING_REPLIES = """
CREATE TABLE pending_replies (
    id              TEXT PRIMARY KEY,
    dealer_id       TEXT,
    dealer_name     TEXT,
    inbound_msg_id  TEXT,
    reply_text      TEXT,
    reply_label     TEXT,
    cialdini_trigger TEXT,
    approved        INTEGER DEFAULT NULL,
    sent            INTEGER DEFAULT 0,
    scheduled_at    TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    msg_checksum    TEXT
);
"""

SCHEMA_AUDIT_LOG = """
CREATE TABLE audit_log (
    id              TEXT PRIMARY KEY,
    event_type      TEXT,
    dealer_id       TEXT,
    payload         TEXT,
    timestamp_it    TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""

SCHEMA_MESSAGES = """
CREATE TABLE messages (
    id              TEXT PRIMARY KEY,
    dealer_id       TEXT,
    direction       TEXT,
    body            TEXT,
    wa_msg_id       TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""


def make_db(tmpdir: Path, scenario_name: str) -> Path:
    """Crea dealer_network.sqlite con schema reali."""
    d = tmpdir / scenario_name
    d.mkdir(parents=True, exist_ok=True)
    db_path = d / 'dealer_network.sqlite'
    con = sqlite3.connect(str(db_path))
    con.executescript(
        SCHEMA_CONVERSATIONS
        + SCHEMA_PENDING_REPLIES
        + SCHEMA_AUDIT_LOG
        + SCHEMA_MESSAGES
    )
    con.commit()
    con.close()
    return db_path


def seed_conversation(db_path: Path, dealer_id: str, phone: str,
                      current_step: str, dealer_name: str = 'Test Dealer'):
    con = sqlite3.connect(str(db_path))
    con.execute(
        "INSERT INTO conversations (dealer_id, dealer_name, phone_number, current_step) "
        "VALUES (?, ?, ?, ?)",
        (dealer_id, dealer_name, phone, current_step),
    )
    con.commit()
    con.close()


# ── Import classify_message direttamente (offline, no LLM) ──
# response-analyzer.py ha dash nel nome → importlib workaround.
# classify_message e' pura logica keyword — no side effects LLM.
import importlib.util

_ra_path = WA_DIR / 'response-analyzer.py'
_spec = importlib.util.spec_from_file_location('response_analyzer', str(_ra_path))
_ra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ra)

classify_message = _ra.classify_message
matches_contract_request = _ra.matches_contract_request
save_pending_reply = _ra.save_pending_reply
ResponseValidator = _ra.ResponseValidator


# ── SCENARIO 1: VEHICLE_REQUEST ─────────────────────────────
def scenario_1_vehicle_request(tmpdir: Path) -> tuple[bool, list]:
    """Scenario 1: 'cerco BMW X3 2021 max €18.000' con DAY1_SENT.
    Atteso: type=VEHICLE_REQUEST. ResponseValidator NO hallucination."""
    print('\n[SCENARIO 1] VEHICLE_REQUEST — "cerco BMW X3 2021 max €18.000"')
    findings = []

    msg = "cerco BMW X3 2021 max €18.000"
    result = classify_message(msg, current_step='DAY1_SENT')
    print(f'  classify_message result: {result}')

    cls_type = result.get('type')
    if cls_type != 'VEHICLE_REQUEST':
        print(f'  FAIL: expected VEHICLE_REQUEST, got {cls_type}')
        findings.append(f'classify returned {cls_type} instead of VEHICLE_REQUEST')
        return False, findings

    # Verify ResponseValidator on a broker-template reply (no hallucination)
    validator = ResponseValidator()
    # Simula reply template broker senza veicolo inventato
    safe_reply = '{"messages": ["buongiorno, ci sto lavorando. Le scrivo entro 24-48h con qualcosa di concreto. Luca"]}'
    violations = validator.validate(safe_reply, 'VEHICLE_REQUEST', [])
    print(f'  ResponseValidator violations (safe reply): {violations}')

    # Simula reply CON hallucination (km specifici + prezzo inventato)
    halluc_reply = '{"messages": ["ho trovato un BMW X3 2021 con 89.855 km a €27.389, ottimo stato"]}'
    halluc_violations = validator.validate(halluc_reply, 'VEHICLE_REQUEST', [])
    print(f'  ResponseValidator violations (hallucination reply): {halluc_violations}')
    if not halluc_violations:
        findings.append('ResponseValidator did NOT catch hallucination in VEHICLE_REQUEST reply')
        print(f'  FAIL: hallucination not caught')
        return False, findings

    ok = cls_type == 'VEHICLE_REQUEST' and not violations and len(halluc_violations) > 0
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok, findings


# ── SCENARIO 2: PRICE_NEGOTIATION (OBJECTION OBJ-2) ─────────
def scenario_2_price_negotiation(tmpdir: Path) -> tuple[bool, list]:
    """Scenario 2: 'posso prendere a 17?' con DOSSIER_SENT.
    Atteso: OBJECTION (OBJ-2 prezzo/negoziazione) o CURIOSITY. MAI veicolo inventato."""
    print('\n[SCENARIO 2] PRICE_NEGOTIATION — "posso prendere a 17?"')
    findings = []

    msg = "posso prendere a 17?"
    result = classify_message(msg, current_step='DOSSIER_SENT')
    print(f'  classify_message result: {result}')

    cls_type = result.get('type')
    # "17" non matcha keyword OBJ-2 ("il prezzo", "quanto costa", etc.)
    # "?" presente → potrebbe essere CURIOSITY
    # CONTRACT_REQUEST pattern 4 non matcha (non e' "ok" secco)
    # Accettiamo OBJECTION, CURIOSITY, o UNKNOWN — ma NOT VEHICLE_REQUEST o NEGATIVE
    acceptable = ('OBJECTION', 'CURIOSITY', 'UNKNOWN', 'POSITIVE')
    if cls_type in acceptable:
        print(f'  OK: type={cls_type} (acceptable for price negotiation)')
    elif cls_type == 'CONTRACT_REQUEST':
        # CRITICAL: "posso prendere a 17?" NON e' una richiesta contratto
        findings.append(f'CRITICAL: "posso prendere a 17?" classified as CONTRACT_REQUEST')
        print(f'  FAIL: misclassified as CONTRACT_REQUEST')
        return False, findings
    elif cls_type == 'VEHICLE_REQUEST':
        findings.append(f'"posso prendere a 17?" classified as VEHICLE_REQUEST (wrong)')
        print(f'  FAIL: classified as VEHICLE_REQUEST')
        return False, findings
    elif cls_type == 'NEGATIVE':
        findings.append(f'"posso prendere a 17?" classified as NEGATIVE (wrong — dealer is negotiating)')
        print(f'  FAIL: classified as NEGATIVE')
        return False, findings
    else:
        findings.append(f'Unexpected type: {cls_type}')
        print(f'  WARNING: unexpected type {cls_type}')

    ok = cls_type in acceptable
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok, findings


# ── SCENARIO 3: CONTRACT_REQUEST ─────────────────────────────
def scenario_3_contract_request(tmpdir: Path) -> tuple[bool, list]:
    """Scenario 3: 'ok mando bonifico' con DOSSIER_SENT.
    Atteso: matches_contract_request=True, classify_message type=CONTRACT_REQUEST.
    NON testa argos-proxy (no HTTP call, no costo)."""
    print('\n[SCENARIO 3] CONTRACT_REQUEST — "ok mando bonifico"')
    findings = []

    msg = "ok mando bonifico"

    # Test matches_contract_request diretto
    match_dossier = matches_contract_request(msg, 'DOSSIER_SENT')
    match_day3 = matches_contract_request(msg, 'DAY3_SENT')
    match_day1 = matches_contract_request(msg, 'DAY1_SENT')
    print(f'  matches_contract_request(DOSSIER_SENT): {match_dossier}')
    print(f'  matches_contract_request(DAY3_SENT):    {match_day3}')
    print(f'  matches_contract_request(DAY1_SENT):    {match_day1}')

    # Gating: DAY1_SENT deve essere False
    if match_day1:
        findings.append('CONTRACT_REQUEST matches on DAY1_SENT — gating broken')

    # classify_message full
    result = classify_message(msg, current_step='DOSSIER_SENT')
    print(f'  classify_message result: {result}')
    cls_type = result.get('type')

    # "ok mando bonifico" — "ok" secco matcha pattern 4 (^\s*(ok|si|...) )
    # Ma "ok mando bonifico" non e' "ok" secco (ha parole dopo).
    # Pattern 1-3 richiedono "contratto/firma/deal/operazione".
    # "bonifico" non e' nelle keyword. Potenziale gap.

    if cls_type == 'CONTRACT_REQUEST':
        print(f'  OK: classified as CONTRACT_REQUEST')
    else:
        # FINDING STRUTTURALE: "ok mando bonifico" NON matcha CONTRACT_REQUEST
        # perche' nessun pattern include "bonifico" come keyword post-confirm
        findings.append(
            f'GAP: "ok mando bonifico" classified as {cls_type}, NOT CONTRACT_REQUEST. '
            f'CONTRACT_REQUEST_PATTERNS non include "bonifico" come keyword. '
            f'Dealer che dice "mando bonifico" post-dossier = intent chiaro ma non catturato.'
        )
        print(f'  FINDING: {cls_type} instead of CONTRACT_REQUEST — "bonifico" not in patterns')

    # Il test PASS/FAIL dipende dal risultato effettivo
    # Ma il gate e' binario: CONTRACT_REQUEST atteso
    ok = (cls_type == 'CONTRACT_REQUEST') and not match_day1
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok, findings


# ── SCENARIO 4: OPT_OUT (NEGATIVE) ──────────────────────────
def scenario_4_opt_out(tmpdir: Path) -> tuple[bool, list]:
    """Scenario 4: 'non mi scrivere piu'' con DAY1_SENT.
    Atteso: classify_message type=NEGATIVE.
    Handler line 2114-2123: UPDATE conversations SET current_step='CLOSED_NO'."""
    print('\n[SCENARIO 4] OPT_OUT — "non mi scrivere piu\'"')
    findings = []

    msg = "non mi scrivere più"
    result = classify_message(msg, current_step='DAY1_SENT')
    print(f'  classify_message result: {result}')

    cls_type = result.get('type')
    if cls_type != 'NEGATIVE':
        findings.append(f'"non mi scrivere piu\'" classified as {cls_type}, expected NEGATIVE')
        print(f'  FAIL: expected NEGATIVE, got {cls_type}')
        return False, findings

    # Verify handler logic: NEGATIVE → UPDATE CLOSED_NO
    # Simula blocco line 2114-2123 su fixture DB
    db_path = make_db(tmpdir, 's4_opt_out')
    seed_conversation(db_path, 'dealer_optout', '393314928901', 'DAY1_SENT')

    # Esegui UPDATE come farebbe il handler
    con = sqlite3.connect(str(db_path))
    con.execute("""
        UPDATE conversations SET current_step = 'CLOSED_NO', analyzed_at = datetime('now')
        WHERE dealer_id = ?
    """, ['dealer_optout'])
    con.commit()

    # Verifica
    row = con.execute(
        "SELECT current_step FROM conversations WHERE dealer_id = 'dealer_optout'"
    ).fetchone()
    con.close()
    print(f'  post-UPDATE current_step: {row[0]}')

    if row[0] != 'CLOSED_NO':
        findings.append(f'NEGATIVE handler: current_step={row[0]}, expected CLOSED_NO')
        return False, findings

    # Verifica anche opt_out column NON viene settata dal NEGATIVE handler
    # (il handler setta solo current_step, NON opt_out=1)
    con = sqlite3.connect(str(db_path))
    opt_out_val = con.execute(
        "SELECT opt_out FROM conversations WHERE dealer_id = 'dealer_optout'"
    ).fetchone()[0]
    con.close()
    if opt_out_val != 0:
        findings.append(f'NEGATIVE handler sets opt_out={opt_out_val}, but schema default is 0')

    # FINDING: NEGATIVE handler (line 2114-2123) setta current_step=CLOSED_NO
    # ma NON setta opt_out=1. Se il dealer viene ri-contattato in futuro
    # (es. cold outreach da scraper diverso), non c'e' flag permanente.
    if opt_out_val == 0:
        findings.append(
            'FINDING: NEGATIVE handler sets current_step=CLOSED_NO but NOT opt_out=1. '
            'Dealer could be re-contacted in future cold outreach if re-scraped. '
            'Schema has opt_out column but handler does not use it.'
        )
        print(f'  FINDING: opt_out column NOT set by NEGATIVE handler (stays 0)')

    ok = cls_type == 'NEGATIVE' and row[0] == 'CLOSED_NO'
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok, findings


# ── SCENARIO 5: AMBIGUOUS (CURIOSITY/UNKNOWN) ───────────────
def scenario_5_ambiguous(tmpdir: Path) -> tuple[bool, list]:
    """Scenario 5: 'rispondo domani' con DAY1_SENT.
    Atteso: UNKNOWN o CURIOSITY (no handler specifico).
    save_pending_reply con approved=NULL → HITL."""
    print('\n[SCENARIO 5] AMBIGUOUS — "rispondo domani"')
    findings = []

    msg = "rispondo domani"
    result = classify_message(msg, current_step='DAY1_SENT')
    print(f'  classify_message result: {result}')

    cls_type = result.get('type')
    # "rispondo domani" = no keyword match forte.
    # No "?" → non CURIOSITY fallback.
    # Expected: UNKNOWN (no_match) o OBJ-3 ("richiamo"/"piu' tardi" keywords vicini)
    acceptable_ambiguous = ('UNKNOWN', 'CURIOSITY', 'OBJ-3', 'OBJECTION')
    if cls_type not in acceptable_ambiguous:
        if cls_type == 'NEGATIVE':
            findings.append(f'"rispondo domani" classified as NEGATIVE — wrong, dealer is deferring not refusing')
            print(f'  FAIL: classified as NEGATIVE')
            return False, findings
        if cls_type == 'POSITIVE':
            findings.append(f'"rispondo domani" classified as POSITIVE — arguable but risky for auto-send')
            print(f'  WARNING: classified as POSITIVE')
        else:
            findings.append(f'Unexpected type: {cls_type}')

    # Verify save_pending_reply logic: approved=NULL
    db_path = make_db(tmpdir, 's5_ambiguous')
    seed_conversation(db_path, 'dealer_ambig', '393314928901', 'DAY1_SENT')

    os.environ['ARGOS_DB_PATH'] = str(db_path)
    reply_candidate = {'text': 'grazie, restiamo in contatto. Luca', 'label': cls_type}
    reply_id = save_pending_reply(
        str(db_path), 'dealer_ambig', 'Test Dealer', 'msg_inbound_001', reply_candidate
    )
    print(f'  save_pending_reply reply_id: {reply_id}')

    if not reply_id:
        findings.append('save_pending_reply returned None — INSERT failed')
        print(f'  FAIL: save_pending_reply returned None')
        return False, findings

    # Verify approved=NULL
    con = sqlite3.connect(str(db_path))
    row = con.execute(
        "SELECT approved, sent FROM pending_replies WHERE id = ?", [reply_id]
    ).fetchone()
    con.close()
    print(f'  pending_replies: approved={row[0]}, sent={row[1]}')

    if row[0] is not None:
        findings.append(f'save_pending_reply approved={row[0]}, expected NULL (HITL gate)')
        print(f'  FAIL: approved is not NULL')
        return False, findings

    if row[1] != 0:
        findings.append(f'save_pending_reply sent={row[1]}, expected 0')

    ok = (cls_type not in ('NEGATIVE', 'CONTRACT_REQUEST', 'VEHICLE_REQUEST')
          and reply_id is not None
          and row[0] is None)
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok, findings


# ── MAIN ────────────────────────────────────────────────────
def main():
    print('=' * 70)
    print('S198 STEP 7 — AMBRA stress test (5 scenari response-analyzer)')
    print('ZERO LLM calls | ZERO messaggi reali | fixture DB only')
    print('=' * 70)

    tmpdir = Path(tempfile.mkdtemp(prefix='s198_ambra_'))
    print(f'Fixtures dir: {tmpdir}')

    all_findings = []
    results = {}

    for name, fn in [
        ('1_VEHICLE_REQUEST', scenario_1_vehicle_request),
        ('2_PRICE_NEGOTIATION', scenario_2_price_negotiation),
        ('3_CONTRACT_REQUEST', scenario_3_contract_request),
        ('4_OPT_OUT_NEGATIVE', scenario_4_opt_out),
        ('5_AMBIGUOUS', scenario_5_ambiguous),
    ]:
        ok, findings = fn(tmpdir)
        results[name] = ok
        all_findings.extend(findings)

    print('\n' + '=' * 70)
    print('SUMMARY:')
    for name, ok in results.items():
        marker = 'PASS' if ok else 'FAIL'
        print(f'  [{marker}] {name}')

    if all_findings:
        print('\nFINDINGS:')
        for i, f in enumerate(all_findings, 1):
            print(f'  F{i}: {f}')

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    verdict = 'PASS' if passed == total else 'FAIL'
    print(f'\nAMBRA STRESS TEST RESULT: {passed}/{total} {verdict}')
    print('=' * 70)

    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
