# -*- coding: utf-8 -*-
"""
duckdb_storage.py — Storage DuckDB per bot Telegram

Tabelle create (se non esistono):
    bot_leads: chat_id, username, first_name, source, created_at, last_seen
    bot_sessions: chat_id, command, timestamp
    briefing_log: chat_id, date, sent_at

Condivide lo stesso DuckDB di cove_engine (cove_tracker.duckdb)
MA usa tabelle separate → nessun conflitto con dati ARGOS
"""

import duckdb
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# NOTE_BOT_POST_DEPLOY: Mappa per convertire nomi piattaforma in paesi leggibili
COUNTRY_MAP = {
    "autoscout24_de": "Germania",
    "autoscout24_nl": "Olanda", 
    "autoscout24_be": "Belgio",
    "autoscout24_at": "Austria",
    "autoscout24_fr": "Francia",
    "autoscout24_it": "Italia",
    "autoscout24_es": "Spagna",
    "autoscout24_ch": "Svizzera",
    "autoscout24_pl": "Polonia",
    "mobile_de": "Germania",
    "leboncoin_fr": "Francia",
    "marktplaats_nl": "Olanda",
    "subito_it": "Italia",
    "as24_": "Europa",  # AutoScout24 generic fallback
}


class BotStorage:
    """Thread-safe DuckDB storage per bot."""
    
    def __init__(self):
        self.db_path = settings.duckdb_path
        self._lock = asyncio.Lock()
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self):
        """Create a new DuckDB connection"""
        return duckdb.connect(str(self.db_path))
    
    @staticmethod
    def _map_country(source: str) -> str:
        """Map platform source name to human-readable country name.
        
        NOTE_BOT_POST_DEPLOY: Aggiungere qui nuove piattaforme se necessario.
        """
        if not source:
            return "N/A"
        
        source_lower = source.lower()
        
        # Check for exact match first
        if source_lower in COUNTRY_MAP:
            return COUNTRY_MAP[source_lower]
        
        # Check for partial matches
        for key, country in COUNTRY_MAP.items():
            if key.endswith("_") and source_lower.startswith(key):
                return country
            if key in source_lower:
                return country
        
        # Return original if no match found
        return source
    
    async def init_schema(self):
        """Initialize database schema if not exists"""
        async with self._lock:
            conn = self._get_connection()
            try:
                # Leads table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bot_leads (
                        chat_id BIGINT PRIMARY KEY,
                        username VARCHAR,
                        first_name VARCHAR,
                        source VARCHAR DEFAULT 'telegram',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 1
                    )
                """)
                
                # Sessions/commands log
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bot_sessions (
                        id INTEGER PRIMARY KEY,
                        chat_id BIGINT,
                        command VARCHAR,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Briefing log
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS briefing_log (
                        id INTEGER PRIMARY KEY,
                        chat_id BIGINT,
                        date VARCHAR,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # COVERAGE_GAP: No index on chat_id for performance - consider adding if table grows large
                conn.commit()
                logger.info("Bot storage schema initialized")
            finally:
                conn.close()
    
    async def upsert_lead(
        self,
        chat_id: int,
        username: Optional[str],
        first_name: Optional[str],
        source: str = "telegram"
    ) -> bool:
        """Inserisce o aggiorna lead. Return True se nuovo lead."""
        async with self._lock:
            conn = self._get_connection()
            try:
                # Check if lead exists
                result = conn.execute(
                    "SELECT chat_id FROM bot_leads WHERE chat_id = ?",
                    (chat_id,)
                ).fetchone()
                
                is_new = result is None
                
                if is_new:
                    conn.execute("""
                        INSERT INTO bot_leads (chat_id, username, first_name, source, created_at, last_seen)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (chat_id, username, first_name, source))
                    logger.info(f"New lead registered: {chat_id} (@{username})")
                else:
                    conn.execute("""
                        UPDATE bot_leads 
                        SET last_seen = CURRENT_TIMESTAMP,
                            message_count = message_count + 1,
                            username = COALESCE(?, username),
                            first_name = COALESCE(?, first_name)
                        WHERE chat_id = ?
                    """, (username, first_name, chat_id))
                
                conn.commit()
                return is_new
            finally:
                conn.close()
    
    async def log_command(self, chat_id: int, command: str):
        """Log a command execution"""
        async with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                    INSERT INTO bot_sessions (chat_id, command, timestamp)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (chat_id, command))
                conn.commit()
            finally:
                conn.close()
    
    async def get_today_certificato(self, limit: int = 3) -> list[dict]:
        """
        Recupera top N veicoli CERTIFICATO del giorno da cove_results.
        Ordine: confidence DESC
        """
        async with self._lock:
            conn = self._get_connection()
            try:
                # Check if cove_results table exists
                tables = conn.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'cove_results'
                """).fetchall()
                
                if not tables:
                    logger.warning("cove_results table not found")
                    return []
                
                today = datetime.now().strftime("%Y-%m-%d")
                
                # VQ_BOT_1: Schema aligned with cove_engine_v4.py
                # Columns: listing_id, make, model, year, km, price, market_price, 
                #          source, status, confidence, recommendation, analyzed_at
                result = conn.execute("""
                    SELECT 
                        make,
                        model,
                        year,
                        price,
                        market_price,
                        km,
                        source,
                        confidence,
                        recommendation
                    FROM cove_results 
                    WHERE recommendation = 'CERTIFICATO'
                        AND DATE(analyzed_at) = ?
                    ORDER BY confidence DESC
                    LIMIT ?
                """, (today, limit)).fetchall()
                
                vehicles = []
                for row in result:
                    vehicles.append({
                        "make": row[0],
                        "model": row[1],
                        "year": row[2],
                        "price_eu": row[3],
                        "price_it": row[4],
                        "mileage": row[5],
                        "country": self._map_country(row[6]),  # NOTE_BOT_POST_DEPLOY: mapped to human-readable
                        "confidence": row[7],
                        "verdict": row[8]
                    })
                
                return vehicles
            except Exception as e:
                logger.error(f"Error fetching certificato vehicles: {e}")
                return []
            finally:
                conn.close()
    
    async def get_system_stats(self) -> dict:
        """Stats per /stato: n veicoli oggi, breakdown verdetti"""
        async with self._lock:
            conn = self._get_connection()
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                stats = {
                    "analyzed_today": 0,
                    "certificato": 0,
                    "verifica_estesa": 0,
                    "escluso": 0,
                    "last_update": datetime.now().isoformat()
                }
                
                # Check if cove_results table exists
                tables = conn.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'cove_results'
                """).fetchall()
                
                if tables:
                    # Count analyzed today
                    result = conn.execute("""
                        SELECT COUNT(*) FROM cove_results 
                        WHERE DATE(analyzed_at) = ?
                    """, (today,)).fetchone()
                    stats["analyzed_today"] = result[0] if result else 0
                    
                    # Count by recommendation (formerly verdict)
                    for recommendation in ["CERTIFICATO", "VERIFICA_ESTESA", "ESCLUSO"]:
                        result = conn.execute("""
                            SELECT COUNT(*) FROM cove_results 
                            WHERE recommendation = ? AND DATE(analyzed_at) = ?
                        """, (recommendation, today)).fetchone()
                        key = recommendation.lower().replace("_", "_")
                        stats[key] = result[0] if result else 0
                
                return stats
            except Exception as e:
                logger.error(f"Error fetching system stats: {e}")
                return stats
            finally:
                conn.close()
    
    async def has_received_briefing(self, chat_id: int, date: str) -> bool:
        """Check if user has already received briefing for date"""
        async with self._lock:
            conn = self._get_connection()
            try:
                result = conn.execute("""
                    SELECT id FROM briefing_log 
                    WHERE chat_id = ? AND date = ?
                """, (chat_id, date)).fetchone()
                return result is not None
            finally:
                conn.close()
    
    async def mark_briefing_sent(self, chat_id: int, date: str):
        """Mark briefing as sent for user on date"""
        async with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                    INSERT INTO briefing_log (chat_id, date, sent_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (chat_id, date))
                conn.commit()
            finally:
                conn.close()
    
    async def get_all_lead_chat_ids(self) -> list[int]:
        """Get all lead chat IDs for broadcasting"""
        async with self._lock:
            conn = self._get_connection()
            try:
                result = conn.execute("SELECT chat_id FROM bot_leads").fetchall()
                return [row[0] for row in result]
            finally:
                conn.close()
    
    async def get_lead_count(self) -> int:
        """Get total number of leads"""
        async with self._lock:
            conn = self._get_connection()
            try:
                result = conn.execute("SELECT COUNT(*) FROM bot_leads").fetchone()
                return result[0] if result else 0
            finally:
                conn.close()
