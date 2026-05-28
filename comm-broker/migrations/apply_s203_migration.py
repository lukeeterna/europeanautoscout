"""S203 migration: ADD COLUMN action_type TEXT DEFAULT 'agent_auto' su bridge_outbound.

Idempotente: controlla PRAGMA table_info prima di ALTER.
Eseguire su iMac dopo deploy (Step C):
    python3 comm-broker/migrations/apply_s203_migration.py [bridge_db_path]

Default path: comm-broker/bridge.sqlite (relativo alla root repo ARGOS su iMac).
"""
import sqlite3
import sys
import os

MIGRATION_NAME = "s203_bridge_outbound_action_type"


def apply(db_path: str) -> None:
    if not os.path.exists(db_path):
        print(f"[S203-MIGRATION] ERRORE: DB non trovato → {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(bridge_outbound)").fetchall()}

        if "action_type" in cols:
            print(f"[S203-MIGRATION] action_type già presente in bridge_outbound — skip (idempotente).")
            return

        conn.execute("ALTER TABLE bridge_outbound ADD COLUMN action_type TEXT DEFAULT 'agent_auto'")
        conn.commit()
        print(f"[S203-MIGRATION] OK — action_type aggiunto a bridge_outbound in {db_path}")

        # Verifica post-alter
        cols_after = {row[1] for row in conn.execute("PRAGMA table_info(bridge_outbound)").fetchall()}
        assert "action_type" in cols_after, "ERRORE post-alter: action_type non trovato"
        print(f"[S203-MIGRATION] Verifica PRAGMA OK — colonne bridge_outbound: {sorted(cols_after)}")
    finally:
        conn.close()


if __name__ == "__main__":
    default_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bridge.sqlite",
    )
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(default_path)
    apply(db_path)
