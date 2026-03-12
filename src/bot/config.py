"""
config.py — Configurazione bot da variabili ambiente
File .env in ~/Documents/app-antigravity-auto/.env

Variabili richieste:
    TELEGRAM_BOT_TOKEN=...
    OWNER_CHAT_ID=...
    DUCKDB_PATH=~/Documents/app-antigravity-auto/python/cove/data/cove_tracker.duckdb
    
Variabili opzionali:
    NOTIFY_EVERY_N_LEADS=5   # notifica owner ogni N lead (default: 1)
    BRIEFING_HOUR=8          # ora invio briefing giornaliero (default: 8)
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    telegram_bot_token: str
    owner_chat_id: int
    duckdb_path: Path = Path.home() / "Documents/app-antigravity-auto/python/cove/data/cove_tracker.duckdb"
    notify_every_n_leads: int = 1
    briefing_hour: int = 8
    
    class Config:
        env_file = str(Path.home() / "Documents/app-antigravity-auto/.env")


settings = Settings()
