# -*- coding: utf-8 -*-
"""
Handler /come_funziona — Workflow scouting Protocollo ARGOS™
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /come_funziona command - explain ARGOS workflow"""
    
    chat_id = update.effective_chat.id
    
    # Get storage from bot_data
    storage = context.application.bot_data.get('storage')
    
    # Log command
    if storage:
        await storage.log_command(chat_id, "/come_funziona")
    
    message = """COME FUNZIONA ARGOS

Il Protocollo ARGOS analizza ogni veicolo su 4 pilastri:

[1] PREZZO (peso 40%)
   Confronto con 20+ annunci comparabili live
   nei mercati EU target

[2] CHILOMETRAGGIO (peso 30%)
   Verifica anomalie vs media KBA 2023
   Rilevamento frode odometro per veicoli NL

[3] ETA / SVALUTAZIONE (peso 20%)
   Curva Schwacke 2024 per BMW/Mercedes/Audi

[4] STORICO (peso 10%)
   VIN decode + verifica provenienza

----------------
VERDETTI POSSIBILI:

[OK] CERTIFICATO - Indice >=75%
   Veicolo pronto per proposta dealer

[!] VERIFICA ESTESA - Indice 60-74%
   Richiede approfondimento manuale

[X] ESCLUSO - Indice <60%
   Non proposto"""
    
    keyboard = [
        [InlineKeyboardButton("Struttura fee", callback_data="fee")],
        [InlineKeyboardButton("Contatto", callback_data="contatto")],
        [InlineKeyboardButton("Torna al menu", callback_data="start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )
