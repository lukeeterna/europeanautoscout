#!/usr/bin/env python3
"""
test_dossier_hitl_smoke.py — S244 smoke OFFLINE anelli 5 + 6.

Catena pipeline: dossier (5) -> approve HITL (6) -> invio PDF al dealer (7).
Questo smoke copre SOLO la parte verificabile offline su CODICE DI PRODUZIONE:

  anello 5 — generazione DOSSIER PDF:
      tools/scripts/pdf_generator_enterprise.py :: generate_dossier_from_data
      Eseguito con zero image_urls -> nessun download, nessun sanitizer, nessuna rete.
      Fatto terminale: file PDF reale su disco (magic %PDF, size > 0).

  anello 6 — gate HITL approvazione dossier:
      wa-intelligence/dashboard/app.py :: _update_dossier_status / _get_dossier_by_id
                                          / _get_pending_dossiers
      Eseguito su fixture SQLite con schema reale `dossiers` (migration S189).
      Fatto terminale: transizione PENDING->APPROVED/REJECTED reale + guard idempotenza.

  anello 7 — invio PDF al dealer (WA):
      NON coperto qui. Codice in wa-intelligence/wa-daemon.js (/send-doc) richiede
      whatsapp-web.js + client WA connesso + TEST_FOUNDER fisico -> tier FULL.
      Resta UNVERIFIED finche' non eseguito E2E su 393314928901 (mai dealer reale).

Esecuzione:
  cd /Users/macbook/Documents/combaretrovamiauto-enterprise
  python3 tools/tests/test_dossier_hitl_smoke.py

Output gate: "SMOKE TEST RESULT: N/N PASS" -> anello 5-6 VERDE.
"""

import json
import os
import sqlite3
import sys
import tempfile
import shutil
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Schema reale dossiers — tools/migrations/s189_approval_gate.sql
SCHEMA_DOSSIERS = """
CREATE TABLE dossiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dealer_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT,
    created_ts INTEGER NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(approval_status IN ('PENDING','APPROVED','REJECTED')),
    approval_ts INTEGER,
    approval_user TEXT,
    reject_reason TEXT,
    UNIQUE(dealer_id, file_path)
);
"""

# audit_log — db.py write_audit lo usa in approve/reject (qui testiamo le helper pure)
SCHEMA_AUDIT_LOG = """
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    dealer_id TEXT,
    payload TEXT,
    timestamp_it TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def _make_dossier_fixture(tmpdir: Path) -> Path:
    tmpdir.mkdir(parents=True, exist_ok=True)
    db_path = tmpdir / 'dealer_network.sqlite'
    con = sqlite3.connect(str(db_path))
    con.executescript(SCHEMA_DOSSIERS + SCHEMA_AUDIT_LOG)
    con.commit()
    con.close()
    return db_path


def _seed_dossier(db_path: Path, dealer_id: str, file_path: str,
                  status: str = 'PENDING') -> int:
    con = sqlite3.connect(str(db_path))
    cur = con.execute(
        "INSERT INTO dossiers (dealer_id, file_path, created_ts, approval_status) "
        "VALUES (?, ?, ?, ?)",
        (dealer_id, file_path, int(time.time()), status),
    )
    con.commit()
    rowid = cur.lastrowid
    con.close()
    return rowid


def _load_hitl_module(db_path: Path):
    """Importa il modulo di produzione app.py con ARGOS_DB_PATH override.

    db.py legge DB_PATH a module-level -> l'env va settato PRIMA dell'import.
    Il package e' `dashboard` sotto wa-intelligence/ (con __init__.py): mettiamo
    wa-intelligence sul sys.path e importiamo dashboard.app (codice reale, NON replica).
    """
    os.environ['ARGOS_DB_PATH'] = str(db_path)
    wa_dir = str(PROJECT_ROOT / 'wa-intelligence')
    if wa_dir not in sys.path:
        sys.path.insert(0, wa_dir)
    # rimuovi eventuali import cache cosi' DB_PATH viene riletto
    for m in [k for k in list(sys.modules) if k.startswith('dashboard')]:
        del sys.modules[m]
    import importlib
    appmod = importlib.import_module('dashboard.app')
    return appmod


def scenario_1_pdf_generation(tmpdir: Path) -> bool:
    """Anello 5: generate_dossier_from_data produce un PDF reale su disco."""
    print('\n[ANELLO 5] generazione DOSSIER PDF (offline, no immagini)')
    from tools.scripts.pdf_generator_enterprise import generate_dossier_from_data

    out_dir = tmpdir / 'pdf'
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.dumps({
        'vehicles': [{
            'make': 'BMW', 'model': 'Serie 3', 'year': 2021, 'km': 45000,
            'price_eur': 28500, '_cove_confidence': 0.78,
            'fuel_type': 'diesel', 'transmission': 'automatic',
            'color': 'Nero', 'country': 'DE', 'image_urls': [],
        }],
        'search_params': {'marca': 'BMW'},
    })
    pdf_path = generate_dossier_from_data(data, 'Test Dealer', str(out_dir))
    exists = os.path.exists(pdf_path)
    size = os.path.getsize(pdf_path) if exists else 0
    magic_ok = False
    if exists:
        with open(pdf_path, 'rb') as fh:
            magic_ok = fh.read(4) == b'%PDF'
    print(f'  PDF: {pdf_path}')
    print(f'  exists={exists} size={size} magic_pdf={magic_ok}')
    ok = exists and size > 1000 and magic_ok
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok


def scenario_2_approve(hitl, db_path: Path) -> bool:
    """Anello 6: PENDING -> APPROVED via _update_dossier_status (codice reale)."""
    print('\n[ANELLO 6a] approve HITL (PENDING -> APPROVED)')
    did = _seed_dossier(db_path, 'dealer_app', '/tmp/x_approve.pdf')
    rc = hitl._update_dossier_status(did, 'APPROVED')
    row = hitl._get_dossier_by_id(did)
    print(f'  rowcount={rc} status={row["approval_status"]} approval_ts={row["approval_ts"]}')
    ok = rc == 1 and row['approval_status'] == 'APPROVED' and row['approval_ts'] is not None
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok


def scenario_3_reject(hitl, db_path: Path) -> bool:
    """Anello 6: PENDING -> REJECTED con reason."""
    print('\n[ANELLO 6b] reject HITL (PENDING -> REJECTED + reason)')
    did = _seed_dossier(db_path, 'dealer_rej', '/tmp/x_reject.pdf')
    rc = hitl._update_dossier_status(did, 'REJECTED', reject_reason='foto sbagliata')
    row = hitl._get_dossier_by_id(did)
    print(f'  rowcount={rc} status={row["approval_status"]} reason={row["reject_reason"]!r}')
    ok = (rc == 1 and row['approval_status'] == 'REJECTED'
          and row['reject_reason'] == 'foto sbagliata')
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok


def scenario_4_idempotency(hitl, db_path: Path) -> bool:
    """Anello 6: doppio approve -> 2o no-op (guard WHERE approval_status='PENDING')."""
    print('\n[ANELLO 6c] idempotenza (2o approve = no-op)')
    did = _seed_dossier(db_path, 'dealer_idem', '/tmp/x_idem.pdf')
    rc1 = hitl._update_dossier_status(did, 'APPROVED')
    rc2 = hitl._update_dossier_status(did, 'APPROVED')
    print(f'  rowcount 1o={rc1} 2o={rc2}')
    ok = rc1 == 1 and rc2 == 0
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok


def scenario_5_pending_list(hitl, db_path: Path) -> bool:
    """Anello 6: _get_pending_dossiers ritorna solo i PENDING."""
    print('\n[ANELLO 6d] pending list mostra solo PENDING')
    p1 = _seed_dossier(db_path, 'dealer_pl1', '/tmp/x_pl1.pdf', status='PENDING')
    _seed_dossier(db_path, 'dealer_pl2', '/tmp/x_pl2.pdf', status='APPROVED')
    pending = hitl._get_pending_dossiers()
    ids = {r['id'] for r in pending}
    print(f'  pending ids={sorted(ids)} (atteso contiene {p1}, esclude APPROVED)')
    ok = p1 in ids and all(r['file_path'] != '/tmp/x_pl2.pdf' for r in pending)
    print(f'  -> {"PASS" if ok else "FAIL"}')
    return ok


def main():
    print('=' * 70)
    print('S244 smoke OFFLINE — anelli 5 (PDF) + 6 (HITL dossier gate)')
    print('=' * 70)

    tmpdir = Path(tempfile.mkdtemp(prefix='s244_dossier_smoke_'))
    print(f'Fixtures dir: {tmpdir}')

    # --- GATE (offline, sempre): anello 5 = PDF gen su codice reale ---
    results = {}
    results['5_pdf_generation'] = scenario_1_pdf_generation(tmpdir)

    # --- BEST-EFFORT: anello 6 = gate HITL dossier (codice reale app.py) ---
    # app.py importa fastapi (presente su iMac/CI, NON su MacBook). Se assente:
    # SKIP onesto, NON conta nel gate. Su iMac/CI esercita il codice reale.
    hitl_results = {}
    db_path = _make_dossier_fixture(tmpdir / 'hitl')
    try:
        hitl = _load_hitl_module(db_path)
    except ModuleNotFoundError as e:
        print(f'\n[ANELLO 6] SKIP — dipendenza assente in questo ambiente: {e}')
        print('  (HITL gate vive in app.py fastapi-coupled; eseguibile su iMac/CI)')
        hitl = None
    if hitl is not None:
        hitl_results['6a_approve'] = scenario_2_approve(hitl, db_path)
        hitl_results['6b_reject'] = scenario_3_reject(hitl, db_path)
        hitl_results['6c_idempotency'] = scenario_4_idempotency(hitl, db_path)
        hitl_results['6d_pending_list'] = scenario_5_pending_list(hitl, db_path)

    print('\n' + '=' * 70)
    print('SUMMARY:')
    for name, ok in results.items():
        print(f'  [{"PASS" if ok else "FAIL"}] {name} (GATE)')
    if hitl_results:
        for name, ok in hitl_results.items():
            print(f'  [{"PASS" if ok else "FAIL"}] {name}')
    else:
        print('  [SKIP] anello 6 (HITL gate) — fastapi assente, non-gating')

    # Gate = solo anello 5 offline. HITL best-effort: se gira deve passare.
    gate_pass = all(results.values())
    hitl_ok = all(hitl_results.values()) if hitl_results else True
    passed = sum(1 for v in {**results, **hitl_results}.values() if v)
    total = len(results) + len(hitl_results)
    ok_all = gate_pass and hitl_ok
    print(f'\nSMOKE TEST RESULT: {passed}/{total} {"PASS" if ok_all else "FAIL"}')
    print('=' * 70)

    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(0 if ok_all else 1)


if __name__ == '__main__':
    main()
