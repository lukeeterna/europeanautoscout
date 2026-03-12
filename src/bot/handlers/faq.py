"""
ARGOS™ Bot — FAQ Handler
========================

Keyword-based automatic FAQ responses.
CoVe 2026 FACTORED
"""

from __future__ import annotations

import logging
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from python.bot.config import FAQ_KEYWORDS, FAQ_RESPONSES, get_briefing_button

logger = logging.getLogger(__name__)


class FAQHandler:
    """Handles automatic FAQ responses based on keywords."""

    def __init__(self):
        # Compile regex patterns for each keyword group
        self._patterns = {}
        for keyword, response_key in FAQ_KEYWORDS.items():
            # Case-insensitive regex with word boundaries for better matching
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            self._patterns[keyword] = (pattern, response_key)

    def _find_best_match(self, text: str) -> str | None:
        """
        Find the best FAQ match for the given text.
        Returns response key or None if no match.
        """
        if not text:
            return None

        text_lower = text.lower()

        # First, try exact keyword matches (higher priority)
        for keyword, response_key in FAQ_KEYWORDS.items():
            if keyword in text_lower:
                return response_key

        # Then try regex patterns for partial matches
        matched_responses = []
        for keyword, (pattern, response_key) in self._patterns.items():
            if pattern.search(text):
                matched_responses.append(response_key)

        # Return most common response if multiple matches
        if matched_responses:
            from collections import Counter
            return Counter(matched_responses).most_common(1)[0][0]

        return None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle incoming text message — check for FAQ keywords.
        """
        if not update.effective_message or not update.effective_message.text:
            return

        # Skip if in conversation
        if context.user_data and context.user_data.get("briefing_started"):
            return

        user_text = update.effective_message.text
        user_id = update.effective_user.id if update.effective_user else "unknown"

        logger.debug(f"FAQ check for user {user_id}: {user_text[:50]}...")

        # Find match
        response_key = self._find_best_match(user_text)

        if response_key and response_key in FAQ_RESPONSES:
            # Send FAQ response
            response_text = FAQ_RESPONSES[response_key]
            await update.effective_message.reply_text(
                response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_briefing_button(),
            )
            logger.info(f"FAQ response sent to {user_id}: {response_key}")

        else:
            # No match — generic fallback
            from python.bot.config import MESSAGES
            await update.effective_message.reply_text(
                MESSAGES["faq_fallback"],
                parse_mode=ParseMode.HTML,
                reply_markup=get_briefing_button(),
            )
            logger.info(f"FAQ fallback sent to {user_id}")

    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle menu button callbacks."""
        if not update.callback_query:
            return

        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "menu_briefing" or data == "start_briefing":
            # Start briefing conversation
            from python.bot.handlers.briefing import BriefingConversation
            briefing = BriefingConversation()
            await briefing.cmd_briefing(update, context)

        elif data == "menu_how":
            from python.bot.handlers.commands import cmd_come_funziona
            await cmd_come_funziona(update, context)

        elif data == "menu_contact":
            from python.bot.handlers.commands import cmd_contatto
            await cmd_contatto(update, context)

        elif data == "menu_faq":
            await query.edit_message_text(
                "<b>❓ FAQ — Domande Frequenti</b>\n\n"
                "Scrivi la tua domanda e cercherò di risponderti automaticamente.\n\n"
                "<b>Argomenti comuni:</b>\n"
                "• Quanto costa il servizio\n"
                "• Come funziona il Protocollo ARGOS™\n"
                "• Tempi di ricerca e consegna\n"
                "• Garanzie e certificazioni\n"
                "• Mercati coperti\n\n"
                "Oppure usa /help per vedere tutti i comandi.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_briefing_button(),
            )
