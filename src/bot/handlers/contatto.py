# -*- coding: utf-8 -*-
"""
Handler /contatto — Informazioni contatto diretto
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /contatto command - show contact information"""
    
    chat_id = update.effective_chat.id
    
    # Get storage from bot_data
    storage = context.application.bot_data.get('storage')
    
    # Log command
    if storage:
        await storage.log_command(chat_id, "/contatto")
    
    message = """CONTATTO DIRETTO

Per informazioni, partnership o richieste specifiche:

Email: ilcombeeretrasher@gmail.com

Rispondiamo entro 24 ore lavorative.

----------------
COMBARETROVAMIAUTO
Scouting veicoli premium EU per dealer italiani
Protocollo ARGOS - Fee solo a buon fine"""
    
    keyboard = [
        [InlineKeyboardButton("Report oggi", callback_data="briefing")],
        [InlineKeyboardButton("Torna al menu", callback_data="start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )
