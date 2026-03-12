# -*- coding: utf-8 -*-
"""
Handler /stato — Stato sistema ARGOS
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stato command - show system status"""
    
    chat_id = update.effective_chat.id
    
    # Get storage from bot_data
    storage = context.application.bot_data.get('storage')
    
    # Log command
    if storage:
        await storage.log_command(chat_id, "/stato")
    
    # Fetch stats
    try:
        stats = await storage.get_system_stats() if storage else {
            "analyzed_today": 0,
            "certificato": 0,
            "verifica_estesa": 0,
            "escluso": 0,
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        stats = {
            "analyzed_today": 0,
            "certificato": 0,
            "verifica_estesa": 0,
            "escluso": 0,
            "last_update": datetime.now().isoformat()
        }
    
    # Format timestamp
    try:
        last_update = datetime.fromisoformat(stats.get('last_update', '')).strftime("%H:%M:%S")
    except:
        last_update = datetime.now().strftime("%H:%M:%S")
    
    message = f"""SISTEMA ARGOS - OPERATIVO

Protocollo: ARGOS v4
Mercati attivi: DE - BE - NL - AT
Veicoli analizzati oggi: {stats.get('analyzed_today', 0)}
CERTIFICATO: {stats.get('certificato', 0)} | VERIFICA ESTESA: {stats.get('verifica_estesa', 0)} | ESCLUSO: {stats.get('escluso', 0)}
Ultimo aggiornamento: {last_update}"""
    
    await update.message.reply_text(message)
