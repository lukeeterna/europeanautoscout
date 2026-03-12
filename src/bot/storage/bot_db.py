"""
ARGOS™ Bot — Database Layer
===========================

DuckDB integration for lead storage.
Thread-safe con asyncio.Lock.
CoVe 2026 FACTORED
"""

from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from python.bot.config import Config

logger = logging.getLogger(__name__)


class BotDatabase:
    """
    DuckDB database handler for bot leads.
    Thread-safe with asyncio.Lock for concurrent access.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = Config()
        self.db_path = self.config.db_path
        self._ensure_db_path()
        self._init_schema()
        self._initialized = True

    def _ensure_db_path(self):
        """Create directory if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """Initialize DuckDB schema if not exists."""
        conn = duckdb.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_leads (
                    id VARCHAR PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    telegram_user_id BIGINT NOT NULL,
                    telegram_username VARCHAR,
                    nome_azienda VARCHAR,
                    telefono VARCHAR,
                    brand VARCHAR,
                    modello VARCHAR,
                    anno INTEGER,
                    km_max VARCHAR,
                    budget_max VARCHAR,
                    status VARCHAR DEFAULT 'NUOVO',
                    note_interne VARCHAR,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_leads_user_id 
                ON bot_leads(telegram_user_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_leads_status 
                ON bot_leads(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_leads_created 
                ON bot_leads(created_at)
            """)

            conn.commit()
            logger.info(f"Bot database initialized: {self.db_path}")

        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            raise
        finally:
            conn.close()

    async def _execute(self, query: str, params: tuple = ()) -> Any:
        """
        Execute query with lock for thread safety.
        """
        async with self._lock:
            conn = duckdb.connect(self.db_path)
            try:
                result = conn.execute(query, params).fetchall()
                conn.commit()
                return result
            finally:
                conn.close()

    def save_lead(self, data: dict[str, Any]) -> str:
        """
        Save a new lead to the database.
        Returns the lead ID.
        """
        lead_id = str(uuid.uuid4())

        conn = duckdb.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO bot_leads (
                    id, telegram_user_id, telegram_username, nome_azienda,
                    telefono, brand, modello, anno, km_max, budget_max, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_id,
                data.get("telegram_user_id", 0),
                data.get("telegram_username", ""),
                data.get("nome_azienda", ""),
                data.get("telefono"),
                data.get("brand", ""),
                data.get("modello", ""),
                data.get("anno", 0),
                data.get("km_max", ""),
                data.get("budget_max", ""),
                data.get("status", "NUOVO"),
            ))
            conn.commit()
            logger.info(f"Lead saved: {lead_id}")
            return lead_id

        except Exception as e:
            logger.error(f"Error saving lead: {e}")
            raise
        finally:
            conn.close()

    def get_lead_by_user(self, telegram_user_id: int) -> dict[str, Any] | None:
        """
        Get the most recent lead for a user.
        """
        conn = duckdb.connect(self.db_path)
        try:
            result = conn.execute("""
                SELECT * FROM bot_leads
                WHERE telegram_user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (telegram_user_id,)).fetchone()

            if not result:
                return None

            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))

        except Exception as e:
            logger.error(f"Error getting lead by user: {e}")
            return None
        finally:
            conn.close()

    def get_lead_by_id(self, lead_id: str) -> dict[str, Any] | None:
        """
        Get a lead by its ID.
        """
        conn = duckdb.connect(self.db_path)
        try:
            result = conn.execute("""
                SELECT * FROM bot_leads
                WHERE id = ?
            """, (lead_id,)).fetchone()

            if not result:
                return None

            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))

        except Exception as e:
            logger.error(f"Error getting lead by id: {e}")
            return None
        finally:
            conn.close()

    def update_lead_status(self, lead_id: str, status: str) -> bool:
        """
        Update the status of a lead.
        Returns True if successful.
        """
        conn = duckdb.connect(self.db_path)
        try:
            result = conn.execute("""
                UPDATE bot_leads
                SET status = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, lead_id))

            conn.commit()
            updated = result.rowcount > 0
            if updated:
                logger.info(f"Lead {lead_id} status updated to {status}")
            return updated

        except Exception as e:
            logger.error(f"Error updating lead status: {e}")
            return False
        finally:
            conn.close()

    def get_all_leads(self, status_filter: str | None = None) -> list[dict[str, Any]]:
        """
        Get all leads, optionally filtered by status.
        """
        conn = duckdb.connect(self.db_path)
        try:
            if status_filter:
                result = conn.execute("""
                    SELECT * FROM bot_leads
                    WHERE status = ?
                    ORDER BY created_at DESC
                """, (status_filter,)).fetchall()
            else:
                result = conn.execute("""
                    SELECT * FROM bot_leads
                    ORDER BY created_at DESC
                """).fetchall()

            if not result:
                return []

            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]

        except Exception as e:
            logger.error(f"Error getting all leads: {e}")
            return []
        finally:
            conn.close()

    def count_leads_today(self) -> int:
        """
        Count leads created today.
        """
        conn = duckdb.connect(self.db_path)
        try:
            result = conn.execute("""
                SELECT COUNT(*) FROM bot_leads
                WHERE created_at >= CURRENT_DATE
            """).fetchone()

            return result[0] if result else 0

        except Exception as e:
            logger.error(f"Error counting leads today: {e}")
            return 0
        finally:
            conn.close()

    def add_note(self, lead_id: str, note: str) -> bool:
        """
        Add internal note to a lead.
        """
        conn = duckdb.connect(self.db_path)
        try:
            # Get current notes
            result = conn.execute("""
                SELECT note_interne FROM bot_leads WHERE id = ?
            """, (lead_id,)).fetchone()

            current_notes = result[0] if result and result[0] else ""
            new_notes = f"{current_notes}\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}".strip()

            conn.execute("""
                UPDATE bot_leads
                SET note_interne = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_notes, lead_id))

            conn.commit()
            logger.info(f"Note added to lead {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding note: {e}")
            return False
        finally:
            conn.close()
