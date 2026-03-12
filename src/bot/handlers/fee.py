# -*- coding: utf-8 -*-
"""
Handler /fee — Informazioni struttura commissioni
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fee command - show fee structure"""
    
    chat_id = update.effective_chat.id
    
    # Get storage from bot_data
    storage = context.application.bot_data.get('storage')
    
    # Log command
    if storage:
        await storage.log_command(chat_id, "/fee")
    
    message = """STRUTTURA FEE

COMBARETROVAMIAUTO opera SOLO a buon fine.

Zero costi di attivazione.
Zero abbonamenti mensili.
Zero rischi.

Fee per transazione completata: EUR 800 - EUR 1.200
(variabile in base al valore del veicolo)

Come funziona:
1. Ti proponiamo veicoli CERTIFICATO
2. Valuti e scegli se procedere
3. Gestiamo acquisto e logistica EU->IT
4. Paghi la fee solo a veicolo consegnato

Per accordi specifici: ilcombeeretrasher@gmail.com"""
    
    keyboard = [
        [InlineKeyboardButton("Torna al menu", callback_data="start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )
