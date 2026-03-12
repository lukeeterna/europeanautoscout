# -*- coding: utf-8 -*-
"""
bot_main.py — Entry point @CombaRetrovamiautoNotifierbot
"""
import asyncio
import logging
import signal
import sys
from datetime import time
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import settings
from handlers import start, briefing, stato, fee, come_funziona, contatto, callbacks
from storage.duckdb_storage import BotStorage
from notifications.owner_notify import OwnerNotifier

# Check if JobQueue is available
HAS_JOB_QUEUE = True

# Log file: dinamico rispetto alla home utente corrente (MacBook / iMac / CI)
_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "bot.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(_LOG_FILE)),
    ]
)
logger = logging.getLogger(__name__)

# Global instances
storage: BotStorage = None
notifier: OwnerNotifier = None


async def post_init(application: Application):
    """Setup post-init: inizializza storage, schedule briefing giornaliero"""
    global storage, notifier
    
    logger.info("Initializing bot storage...")
    storage = BotStorage()
    await storage.init_schema()
    
    # Store in bot_data for access from handlers
    application.bot_data['storage'] = storage
    
    logger.info("Initializing owner notifier...")
    notifier = OwnerNotifier(application, settings.owner_chat_id)
    application.bot_data['notifier'] = notifier
    
    # Also store in global for scheduled jobs
    application.bot_data['global_storage'] = storage
    application.bot_data['global_notifier'] = notifier
    
    # Schedule daily briefing job
    if HAS_JOB_QUEUE and application.job_queue:
        application.job_queue.run_daily(
            send_daily_briefings,
            time=time(hour=settings.briefing_hour, minute=0),
            name="daily_briefing"
        )
        logger.info(f"Daily briefing scheduled for {settings.briefing_hour}:00")
    else:
        logger.info("JobQueue not available. Daily briefing must be triggered manually.")
    
    # Notify owner that bot is online
    await notifier.notify_bot_online()
    logger.info("Bot initialization complete")


async def send_daily_briefings(context: ContextTypes.DEFAULT_TYPE):
    """Send daily briefing to all leads who haven't received it today"""
    from datetime import datetime
    
    today = datetime.now().strftime("%Y-%m-%d")
    storage = context.application.bot_data.get('storage')
    
    if not storage:
        logger.error("Storage not available for daily briefing")
        return
    
    chat_ids = await storage.get_all_lead_chat_ids()
    
    for chat_id in chat_ids:
        if not await storage.has_received_briefing(chat_id, today):
            try:
                await briefing.send_briefing_to_user(context.bot, chat_id, storage)
                await storage.mark_briefing_sent(chat_id, today)
                logger.info(f"Briefing sent to {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send briefing to {chat_id}: {e}")


async def shutdown_signal_handler(sig, frame):
    """Handle graceful shutdown"""
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    sys.exit(0)


def main():
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, lambda sig, frame: asyncio.create_task(shutdown_signal_handler(sig, frame)))
    signal.signal(signal.SIGINT, lambda sig, frame: asyncio.create_task(shutdown_signal_handler(sig, frame)))
    
    logger.info("Starting @CombaRetrovamiautoNotifierbot...")
    
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )
    
    # Command handlers
    app.add_handler(CommandHandler("start", start.handle))
    app.add_handler(CommandHandler("briefing", briefing.handle))
    app.add_handler(CommandHandler("stato", stato.handle))
    app.add_handler(CommandHandler("fee", fee.handle))
    app.add_handler(CommandHandler("come_funziona", come_funziona.handle))
    app.add_handler(CommandHandler("contatto", contatto.handle))
    app.add_handler(CallbackQueryHandler(callbacks.handle))
    
    logger.info("Bot handlers registered, starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
