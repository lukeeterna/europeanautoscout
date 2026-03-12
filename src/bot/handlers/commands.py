"""
ARGOS™ Bot — Command Handlers
=============================

/start, /help, /briefing, /stato, /fee, /come_funziona, /contatto, /cancel
CoVe 2026 FACTORED
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from python.bot.config import MESSAGES, get_main_menu_keyboard, get_briefing_button
from python.bot.storage.bot_db import BotDatabase

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.effective_message:
        return

    await update.effective_message.reply_text(
        MESSAGES["start"],
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard(),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.effective_message:
        return

    await update.effective_message.reply_text(
        MESSAGES["help"],
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard(),
    )


async def cmd_stato(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stato command — show briefing status for user."""
    if not update.effective_message or not update.effective_user:
        return

    user_id = update.effective_user.id
    db = BotDatabase()

    try:
        lead = db.get_lead_by_user(user_id)

        if not lead:
            await update.effective_message.reply_text(
                MESSAGES["stato_nessun_briefing"],
                parse_mode=ParseMode.HTML,
                reply_markup=get_briefing_button(),
            )
            return

        # Format status message
        status_emoji = {
            "NUOVO": "🆕",
            "IN_LAVORAZIONE": "🔄",
            "COMPLETATO": "✅",
            "ANNULLATO": "❌",
        }.get(lead["status"], "📝")

        await update.effective_message.reply_text(
            MESSAGES["stato_in_lavorazione"].format(
                brand=lead["brand"],
                modello=lead["modello"],
                anno=lead["anno"],
                km_max=lead["km_max"],
                budget_max=lead["budget_max"],
                status=f"{status_emoji} {lead['status'].replace('_', ' ')}",
            ),
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logger.error(f"Error in cmd_stato: {e}")
        await update.effective_message.reply_text(
            "Si è verificato un errore nel recuperare lo stato. Riprova più tardi."
        )


async def cmd_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /fee command — show pricing information."""
    if not update.effective_message:
        return

    await update.effective_message.reply_text(
        MESSAGES["fee"],
        parse_mode=ParseMode.HTML,
        reply_markup=get_briefing_button(),
    )


async def cmd_come_funziona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /come_funziona command — explain the process."""
    if not update.effective_message:
        return

    await update.effective_message.reply_text(
        MESSAGES["come_funziona"],
        parse_mode=ParseMode.HTML,
        reply_markup=get_briefing_button(),
    )


async def cmd_contatto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /contatto command — show contact information."""
    if not update.effective_message:
        return

    await update.effective_message.reply_text(
        MESSAGES["contatto"],
        parse_mode=ParseMode.HTML,
        reply_markup=get_briefing_button(),
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command — cancel ongoing conversation."""
    if not update.effective_message:
        return ConversationHandler.END

    await update.effective_message.reply_text(
        "❌ Operazione annullata. Puoi ricominciare con /briefing",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END
