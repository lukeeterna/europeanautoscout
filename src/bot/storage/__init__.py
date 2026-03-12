"""Storage module for Telegram bot data persistence."""

from .duckdb_storage import BotStorage

__all__ = ["BotStorage"]
