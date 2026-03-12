"""
Handler /start — Onboarding nuovi lead COMBARETROVAMIAUTO
Tono: professionale B2B, NO emoji eccessive
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - register lead and show welcome message"""
    
    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username if user else None
    first_name = user.first_name if user else None
    
    # Access storage and notifier from bot_data (set in post_init)
    storage = context.application.bot_data.get('storage')
    notifier = context.application.bot_data.get('notifier')
    
    # Save lead to database
    try:
        if storage:
            is_new_lead = await storage.upsert_lead(
                chat_id=chat_id,
                username=username,
                first_name=first_name,
                source="telegram_start"
            )
            
            # Log command
            await storage.log_command(chat_id, "/start")
            
            # Notify owner if new lead
            if is_new_lead and notifier:
                await notifier.notify_new_lead(chat_id, username, first_name)
            
    except Exception as e:
        logger.error(f"Error saving lead: {e}")
    
    # Build welcome message - professional B2B tone
    welcome_text = """Benvenuto in COMBARETROVAMIAUTO.

Scouting veicoli premium EU per dealer italiani indipendenti.
BMW · Mercedes · Audi · 2018-2023 · EUR 15k-60k

Il nostro Protocollo ARGOS™ analizza ogni veicolo su 4 dimensioni indipendenti prima di proporlo.

Fee: EUR 800-1.200 per transazione completata.
Zero costi fissi — paghi solo se acquisti.

----------------
Cosa vuoi fare?"""
    
    # Inline keyboard
    keyboard = [
        [InlineKeyboardButton("Come funziona", callback_data="come_funziona")],
        [InlineKeyboardButton("Struttura fee", callback_data="fee")],
        [InlineKeyboardButton("Contatto diretto", callback_data="contatto")],
        [InlineKeyboardButton("Report oggi", callback_data="briefing")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=None  # No markdown needed for this message
    )