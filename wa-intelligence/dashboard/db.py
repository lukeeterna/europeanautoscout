"""
db.py -- ARGOS Dashboard Database Layer
CoVe 2026 | Enterprise Grade

Queries READ-ONLY + azioni esplicite F5 (approve/skip/note).
Il DB e' condiviso con wa-daemon e tg-bot via SQLite WAL mode.
"""

import sqlite3
import os
from typing import Any, Optional

DB_PATH = os.environ.get(
    'ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite')
)


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    return con


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def ensure_tables():
    """Crea tabelle mancanti (solo struttura, nessun dato)."""
    con = _connect()
    try:
        if not _table_exists(con, 'messages'):
            con.execute('''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dealer_id TEXT, dealer_name TEXT, phone_number TEXT,
                direction TEXT, body TEXT,
                timestamp_it TEXT, timestamp_iso TEXT,
                wa_msg_id TEXT, processed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )''')
        if not _table_exists(con, 'pending_replies'):
            con.execute('''CREATE TABLE IF NOT EXISTS pending_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dealer_id TEXT, dealer_name TEXT, inbound_msg_id TEXT,
                reply_text TEXT, reply_label TEXT, cialdini_trigger TEXT,
                approved INTEGER, sent INTEGER DEFAULT 0,
                scheduled_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )''')
        if not _table_exists(con, 'scheduled_actions'):
            con.execute('''CREATE TABLE IF NOT EXISTS scheduled_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dealer_id TEXT, dealer_name TEXT,
                action_type TEXT, due_at TEXT,
                status TEXT DEFAULT 'PENDING', fired_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )''')
        if not _table_exists(con, 'audit_log'):
            con.execute('''CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT, dealer_id TEXT, payload TEXT,
                timestamp_it TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )''')
        if not _table_exists(con, 'llm_costs'):
            con.execute('''CREATE TABLE IF NOT EXISTS llm_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT, tokens INTEGER, cost_usd REAL,
                dealer_id TEXT, purpose TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )''')
        con.commit()
    finally:
        con.close()


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Esegue una query read-only e restituisce lista di dict."""
    con = _connect()
    try:
        rows = con.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def query_one(sql: str, params: tuple = ()) -> Optional[dict[str, Any]]:
    """Restituisce un singolo risultato o None."""
    results = query(sql, params)
    return results[0] if results else None


# ── KPI Queries ─────────────────────────────────────────

def get_pipeline_stats() -> dict:
    """KPI principali per la dashboard."""
    con = _connect()
    try:
        total = con.execute('SELECT COUNT(*) FROM conversations').fetchone()[0]
        active = con.execute(
            "SELECT COUNT(*) FROM conversations WHERE current_step NOT IN ('PENDING', 'CLOSED_NO', 'CLOSED_YES')"
        ).fetchone()[0]
        pending_replies = con.execute(
            'SELECT COUNT(*) FROM pending_replies WHERE approved IS NULL'
        ).fetchone()[0]
        total_messages = con.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
        return {
            'total_dealers': total,
            'active_dealers': active,
            'pending_replies': pending_replies,
            'total_messages': total_messages,
        }
    finally:
        con.close()


def get_dealers() -> list[dict]:
    """Lista completa dealer con ultimo messaggio."""
    return query('''
        SELECT c.*,
               (SELECT COUNT(*) FROM messages m WHERE m.dealer_id = c.dealer_id) as msg_count,
               (SELECT body FROM messages m WHERE m.dealer_id = c.dealer_id
                ORDER BY created_at DESC LIMIT 1) as last_message
        FROM conversations c
        ORDER BY c.score DESC NULLS LAST
    ''')


def get_dealer(dealer_id: str) -> Optional[dict]:
    """Dettaglio singolo dealer."""
    return query_one('SELECT * FROM conversations WHERE dealer_id = ?', (dealer_id,))


def get_messages(dealer_id: str, limit: int = 50) -> list[dict]:
    """Messaggi per dealer, ordine cronologico."""
    return query('''
        SELECT * FROM messages
        WHERE dealer_id = ?
        ORDER BY created_at ASC
        LIMIT ?
    ''', (dealer_id, limit))


def get_all_recent_messages(limit: int = 20) -> list[dict]:
    """Ultimi messaggi globali (per feed dashboard)."""
    return query('''
        SELECT * FROM messages
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))


def get_pending_replies() -> list[dict]:
    """Risposte in attesa di approvazione."""
    return query('''
        SELECT * FROM pending_replies
        WHERE approved IS NULL
        ORDER BY created_at DESC
    ''')


def get_pending_replies_for_dealer(dealer_id: str) -> list[dict]:
    """Risposte in attesa per un dealer specifico."""
    return query('''
        SELECT * FROM pending_replies
        WHERE dealer_id = ? AND approved IS NULL
        ORDER BY created_at DESC
    ''', (dealer_id,))


def get_archetype_distribution() -> list[dict]:
    """Distribuzione archetipi per chart donut."""
    return query('''
        SELECT persona_type, COUNT(*) as count
        FROM conversations
        WHERE persona_type IS NOT NULL
        GROUP BY persona_type
        ORDER BY count DESC
    ''')


def get_funnel_data() -> dict:
    """Dati funnel pipeline."""
    steps = ['PENDING', 'DAY1_SENT', 'RESPONSE_RECEIVED', 'NEGOTIATION', 'DEAL', 'CLOSED_NO']
    result = {}
    con = _connect()
    try:
        for step in steps:
            count = con.execute(
                "SELECT COUNT(*) FROM conversations WHERE current_step LIKE ?",
                (f'{step}%',)
            ).fetchone()[0]
            result[step] = count
        return result
    finally:
        con.close()


# ── Finance Queries ─────────────────────────────────────

def get_llm_costs(days: int = 30) -> list[dict]:
    """Costi LLM aggregati per giorno."""
    return query('''
        SELECT date(created_at) as day,
               COUNT(*) as requests,
               SUM(CAST(cost_usd AS REAL)) as total_cost
        FROM llm_costs
        WHERE created_at >= datetime('now', ?)
        GROUP BY date(created_at)
        ORDER BY day ASC
    ''', (f'-{days} days',))


def get_llm_cost_total() -> dict:
    """Costo totale LLM."""
    row = query_one('''
        SELECT COUNT(*) as total_requests,
               COALESCE(SUM(CAST(cost_usd AS REAL)), 0) as total_cost
        FROM llm_costs
    ''')
    return row or {'total_requests': 0, 'total_cost': 0.0}


# ── System Queries ──────────────────────────────────────

# ── Action Queries (F5) ────────────────────────────────

def approve_reply(reply_id: int) -> bool:
    """Approva una pending_reply."""
    con = _connect()
    try:
        cur = con.execute(
            'UPDATE pending_replies SET approved = 1 WHERE id = ? AND approved IS NULL',
            (reply_id,)
        )
        if cur.rowcount > 0:
            row = con.execute('SELECT dealer_id FROM pending_replies WHERE id = ?', (reply_id,)).fetchone()
            _audit(con, 'REPLY_APPROVED', dict(row)['dealer_id'] if row else None, {'reply_id': reply_id})
            con.commit()
            return True
        return False
    finally:
        con.close()


def skip_reply(reply_id: int) -> bool:
    """Rifiuta (skip) una pending_reply."""
    con = _connect()
    try:
        cur = con.execute(
            'UPDATE pending_replies SET approved = 0 WHERE id = ? AND approved IS NULL',
            (reply_id,)
        )
        if cur.rowcount > 0:
            row = con.execute('SELECT dealer_id FROM pending_replies WHERE id = ?', (reply_id,)).fetchone()
            _audit(con, 'REPLY_SKIPPED', dict(row)['dealer_id'] if row else None, {'reply_id': reply_id})
            con.commit()
            return True
        return False
    finally:
        con.close()


def update_dealer_note(dealer_id: str, note: str) -> bool:
    """Aggiorna note dealer."""
    con = _connect()
    try:
        cur = con.execute(
            'UPDATE conversations SET notes = ? WHERE dealer_id = ?',
            (note, dealer_id)
        )
        if cur.rowcount > 0:
            _audit(con, 'NOTE_UPDATED', dealer_id, {'note': note[:200]})
            con.commit()
            return True
        return False
    finally:
        con.close()


def update_dealer_step(dealer_id: str, step: str) -> bool:
    """Aggiorna step dealer (es. dopo invio Day 1)."""
    con = _connect()
    try:
        cur = con.execute(
            'UPDATE conversations SET current_step = ? WHERE dealer_id = ?',
            (step, dealer_id)
        )
        if cur.rowcount > 0:
            _audit(con, 'STEP_UPDATED', dealer_id, {'new_step': step})
            con.commit()
            return True
        return False
    finally:
        con.close()


def _audit(con: sqlite3.Connection, event_type: str, dealer_id: Optional[str], payload: dict):
    """Scrive audit log (chiamato dentro transazione esistente)."""
    import json as _json
    from datetime import datetime
    con.execute(
        'INSERT INTO audit_log (event_type, dealer_id, payload, timestamp_it, created_at) VALUES (?, ?, ?, ?, ?)',
        (event_type, dealer_id, _json.dumps(payload),
         datetime.now().strftime('%d/%m/%Y %H:%M'), datetime.now().isoformat())
    )


def write_audit(event_type: str, dealer_id: Optional[str], payload: str = '{}'):
    """Scrive audit log standalone (fuori transazione)."""
    from datetime import datetime
    con = _connect()
    try:
        con.execute(
            'INSERT INTO audit_log (event_type, dealer_id, payload, timestamp_it, created_at) VALUES (?, ?, ?, ?, ?)',
            (event_type, dealer_id, payload,
             datetime.now().strftime('%d/%m/%Y %H:%M'), datetime.now().isoformat())
        )
        con.commit()
    finally:
        con.close()


def get_recent_audit(limit: int = 20) -> list[dict]:
    """Ultimi eventi audit log."""
    return query('''
        SELECT * FROM audit_log
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))


def get_db_stats() -> dict:
    """Statistiche database."""
    con = _connect()
    try:
        tables = {}
        for table in ['conversations', 'messages', 'pending_replies', 'scheduled_actions', 'audit_log']:
            try:
                count = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                tables[table] = count
            except Exception:
                tables[table] = -1

        # DB file size
        try:
            size_bytes = os.path.getsize(DB_PATH)
            size_kb = round(size_bytes / 1024, 1)
        except Exception:
            size_kb = 0

        # WAL mode check
        wal = con.execute('PRAGMA journal_mode').fetchone()[0]

        return {
            'tables': tables,
            'size_kb': size_kb,
            'journal_mode': wal,
        }
    finally:
        con.close()
