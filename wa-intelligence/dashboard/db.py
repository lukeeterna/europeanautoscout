"""
db.py -- ARGOS Dashboard Database Layer
CoVe 2026 | Enterprise Grade

Queries READ-ONLY + azioni esplicite F5 (approve/skip/note).
Il DB e' condiviso con wa-daemon e tg-bot via SQLite WAL mode.
"""

import sqlite3
import os
from datetime import datetime, timedelta
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
        # S202-INBOX: ALTER idempotent — 3 colonne reactive classifier su messages
        # SQLite non supporta ADD COLUMN IF NOT EXISTS: check via PRAGMA table_info
        existing_cols = {row[1] for row in con.execute("PRAGMA table_info(messages)").fetchall()}
        for col_def, col_name in [
            ("classifier_intent TEXT",    "classifier_intent"),
            ("classifier_confidence REAL", "classifier_confidence"),
            ("raw_payload TEXT",          "raw_payload"),
        ]:
            if col_name not in existing_cols:
                con.execute(f"ALTER TABLE messages ADD COLUMN {col_def}")
                import logging
                logging.getLogger(__name__).info("S202: ADD COLUMN messages.%s", col_name)

        # Indici partial reactive (IF NOT EXISTS sicuro su SQLite)
        con.execute("""CREATE INDEX IF NOT EXISTS idx_messages_phone_dir_ts
            ON messages(phone_number, direction, created_at DESC)""")
        con.execute("""CREATE INDEX IF NOT EXISTS idx_messages_intent
            ON messages(classifier_intent) WHERE classifier_intent IS NOT NULL""")
        con.execute("""CREATE INDEX IF NOT EXISTS idx_messages_unprocessed
            ON messages(processed) WHERE processed = 0""")

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

def approve_reply(reply_id: str) -> dict:
    """Approva una pending_reply e inserisce in bridge_outbound per invio daemon.

    S196-P2: signature dict per propagare stato bridge_outbound a caller (app.py).
    Risolve silent-failure return True senza INSERT bridge (schema drift, env mancante,
    insert exception) che bloccava il daemon senza segnalarlo all'operatore.

    S192: reply_id e' TEXT PK (es. 'reply_abc12345'), non int.

    Returns:
        {
          "approved": bool,           # True se UPDATE pending_replies ha avuto effetto
          "bridge_queued": bool,      # True se INSERT bridge_outbound OK (riga nuova)
          "error": Optional[str],     # codice strutturato (None se path felice)
        }

    Error codes (caller interpretation):
        None                       — happy path completo (approved + bridge_queued)
        "not_found_or_processed"   — reply non trovata o gia' approvata
        "schema_drift"             — sqlite3.OperationalError su SELECT pending_replies
        "bridge_db_path_missing"   — env var BRIDGE_DB_PATH non impostata
        "bridge_duplicate"         — riga gia' in bridge_outbound (INSERT OR IGNORE rowcount=0)
        "bridge_insert_failed"     — eccezione su INSERT bridge_outbound
        "phone_or_text_missing"    — phone o reply_text vuoti — bridge skip

    Trade-off: cambia signature pubblica (era bool). Path felice S193-fix HIGH-2
    dipende da env var non verificata — degradazione silenziosa e' bug peggiore
    di breaking change su un solo callsite (app.py action_approve_reply).
    """
    import logging as _log
    _logger = _log.getLogger(__name__)

    con = _connect()
    try:
        cur = con.execute(
            'UPDATE pending_replies SET approved = 1 WHERE id = ? AND approved IS NULL',
            (reply_id,)
        )
        if cur.rowcount == 0:
            return {"approved": False, "bridge_queued": False, "error": "not_found_or_processed"}

        # S193-fix HIGH-2: rimosso LEFT JOIN dealers (tabella inesistente in dealer_network.sqlite)
        # Schema dump iMac 2026-05-26 conferma: solo conversations ha phone_number (PK dealer_id 1:1).
        # try/except sqlite3 safety-net per schema drift futuro (es. rename colonna).
        try:
            row = con.execute(
                '''SELECT pr.dealer_id, pr.reply_text,
                          c.phone_number AS phone,
                          COALESCE(c.current_step, 'RESPONSE_RECEIVED') AS current_step
                   FROM pending_replies pr
                   LEFT JOIN conversations c ON c.dealer_id = pr.dealer_id
                   WHERE pr.id = ?''',
                (reply_id,)
            ).fetchone()
        except sqlite3.OperationalError as schema_err:
            _logger.error(
                f'[HITL][approve_reply] schema drift SELECT fallita per {reply_id}: {schema_err} '
                f'— UPDATE approved=1 gia\' committato, bridge_outbound NON inserito'
            )
            # UPDATE gia' rowcount=1: approved=True, bridge_queued=False, errore strutturato
            con.commit()
            return {"approved": True, "bridge_queued": False, "error": "schema_drift"}

        dealer_id = dict(row)['dealer_id'] if row else None
        _audit(con, 'REPLY_APPROVED', dealer_id, {'reply_id': reply_id})
        con.commit()

        # INSERT bridge_outbound — single-writer pattern (S173)
        bridge_db_path = os.environ.get('BRIDGE_DB_PATH', '')
        if not bridge_db_path:
            _logger.warning(
                f'[HITL][bridge] BRIDGE_DB_PATH non impostato — reply {reply_id} approvata ma NON in coda daemon'
            )
            return {"approved": True, "bridge_queued": False, "error": "bridge_db_path_missing"}

        if not row:
            # row None solo se pending_replies non aveva pr.dealer_id risolvibile
            _logger.warning(
                f'[HITL][bridge] reply {reply_id}: SELECT post-UPDATE ha ritornato NULL — bridge skip'
            )
            return {"approved": True, "bridge_queued": False, "error": "phone_or_text_missing"}

        r = dict(row)
        phone = (r.get('phone') or '').replace('+', '').replace(' ', '').replace('-', '')
        reply_text = r.get('reply_text') or ''
        current_step = r.get('current_step') or 'RESPONSE_RECEIVED'

        if not (phone and reply_text):
            _logger.warning(
                f'[HITL][bridge] reply {reply_id}: phone o reply_text mancante — bridge skip'
            )
            return {"approved": True, "bridge_queued": False, "error": "phone_or_text_missing"}

        try:
            import sqlite3 as _sqlite3
            b_con = _sqlite3.connect(bridge_db_path, timeout=10)
            b_con.execute('PRAGMA journal_mode=WAL')
            b_con.execute('PRAGMA busy_timeout=10000')
            b_res = b_con.execute(
                """INSERT OR IGNORE INTO bridge_outbound
                       (deal_id, target_role, target_phone, template_phase, template_lang,
                        body, state_at_send, created_ts, approved_ts)
                   VALUES (?, 'dealer', ?, 'response', 'it', ?, ?, strftime('%s','now'), strftime('%s','now'))""",
                (reply_id, phone, reply_text, current_step)
            )
            b_con.commit()
            bridge_inserted = b_res.rowcount == 1
            b_con.close()
        except Exception as b_err:
            _logger.error(
                f'[HITL][bridge] INSERT fallito per {reply_id}: {b_err} — approvazione gia\' salvata'
            )
            return {"approved": True, "bridge_queued": False, "error": "bridge_insert_failed"}

        if not bridge_inserted:
            _logger.warning(
                f'[HITL][bridge][dedup] reply {reply_id} gia\' in bridge_outbound — skip'
            )
            return {"approved": True, "bridge_queued": False, "error": "bridge_duplicate"}

        # Audit separato bridge insert
        # S193-fix LOW-2: phone masking corretto — nasconde ultime 4 cifre
        # S196-precondition-2 (revisore claude.ai esterno): bridge_outbound e' GIA'
        # committato su b_con (chiuso sopra). Se _audit/commit qui fallisce, il msg
        # WA verra' inviato dal daemon ma audit_log NON registrera' l'evento →
        # buco compliance opt-out (non solo "operational" come da MED-2 backlog).
        # Mitigation: log ERROR esplicito (visibile fuori audit_log) + return
        # success comunque (bridge queue e' la verita' operativa).
        try:
            _audit(con, 'BRIDGE_INSERTED', dealer_id,
                   {'reply_id': reply_id, 'phone': phone[:-4] + '****' if len(phone) > 4 else '****'})
            con.commit()
        except Exception as audit_err:
            _logger.error(
                f'[HITL][bridge][AUDIT-LOSS] reply {reply_id}: bridge_outbound INSERTED '
                f'ma audit_log commit fallito ({type(audit_err).__name__}: {audit_err}). '
                f'Compliance gap: msg verra\' inviato senza traccia audit. '
                f'Manual reconciliation richiesta.'
            )
            # NON return error: bridge e' gia' committed, daemon invierà comunque
        _logger.info(f'[HITL][bridge] reply {reply_id} → bridge_outbound queued')

        return {"approved": True, "bridge_queued": True, "error": None}
    finally:
        con.close()


def skip_reply(reply_id: str) -> bool:
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


def get_operational_kpis() -> dict:
    """KPI operativi per controllo quotidiano 5 minuti."""
    con = _connect()
    try:
        # Response rate
        total_outbound = con.execute(
            "SELECT COUNT(*) FROM conversations WHERE outbound_count > 0"
        ).fetchone()[0]
        total_responded = con.execute(
            "SELECT COUNT(*) FROM conversations WHERE inbound_count > 0"
        ).fetchone()[0]
        response_rate = round((total_responded / total_outbound * 100) if total_outbound > 0 else 0)

        # Messaggi inviati oggi
        today = datetime.now().strftime('%Y-%m-%d')
        sent_today = con.execute(
            "SELECT COUNT(*) FROM messages WHERE direction='OUTBOUND' AND created_at LIKE ?",
            (f'{today}%',)
        ).fetchone()[0]

        # Dealer con scadenza nelle prossime 24h
        days_map = {'DAY1_SENT': 3, 'DAY3_SENT': 4, 'DAY7_VOICE_SENT': 7, 'DAY7_SENT': 7}
        rows = con.execute(
            "SELECT dealer_name, dealer_id, current_step, last_contact_at FROM conversations "
            "WHERE current_step IN ('DAY1_SENT','DAY3_SENT','DAY7_VOICE_SENT','DAY7_SENT') "
            "AND last_contact_at IS NOT NULL"
        ).fetchall()

        now = datetime.now()
        due_soon = []
        for dealer_name, dealer_id, step, last_contact in rows:
            days = days_map.get(step, 7)
            try:
                last_dt = datetime.fromisoformat(last_contact)
                deadline = last_dt + timedelta(days=days)
                hours_until = (deadline - now).total_seconds() / 3600
                if hours_until <= 24:
                    due_soon.append({
                        'name': dealer_name,
                        'step': step,
                        'hours': round(hours_until, 1),
                        'overdue': hours_until < 0,
                    })
            except Exception:
                pass

        # Ultima risposta inbound
        last_inbound = con.execute(
            "SELECT dealer_name, body, timestamp_it FROM messages "
            "WHERE direction='INBOUND' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()

        # Dealer con risposta in attesa di approvazione (pending replies)
        pending_urgent = con.execute(
            "SELECT COUNT(*) FROM pending_replies WHERE approved IS NULL AND sent=0"
        ).fetchone()[0]

        return {
            'response_rate':            response_rate,
            'total_responded':          total_responded,
            'total_outbound_dealers':   total_outbound,
            'sent_today':               sent_today,
            'due_soon':                 due_soon,
            'pending_urgent':           pending_urgent,
            'last_inbound':             dict(zip(['dealer_name', 'body', 'timestamp_it'], last_inbound)) if last_inbound else None,
        }
    finally:
        con.close()
