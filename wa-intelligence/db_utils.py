"""
db_utils.py — ARGOS SQLite Connection Factory
Single source of truth for all SQLite connection configuration.
All Python processes MUST use get_connection() instead of raw sqlite3.connect().
"""

import sqlite3
import os

DB_PATH = os.environ.get(
    'ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite')
)

# Production PRAGMAs — applied to EVERY connection
_PRAGMAS = [
    ('journal_mode', 'WAL'),
    ('busy_timeout', '10000'),
    ('synchronous', 'NORMAL'),
]


def get_connection(db_path: str = None, row_factory=None) -> sqlite3.Connection:
    """Returns a configured SQLite connection with all production PRAGMAs."""
    path = db_path or DB_PATH
    con = sqlite3.connect(path, timeout=10)
    if row_factory:
        con.row_factory = row_factory
    for pragma, value in _PRAGMAS:
        con.execute(f'PRAGMA {pragma} = {value}')
    return con
