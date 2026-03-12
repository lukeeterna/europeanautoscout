# -*- coding: utf-8 -*-
"""
Handler /briefing — Report giornaliero dealer
Top 3 veicoli CERTIFICATO del giorno
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from storage.duckdb_storage import BotStorage

logger = logging.getLogger(__name__)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /briefing command"""
    chat_id = update.effective_chat.id
    
    # Get storage from bot_data
    storage = context.application.bot_data.get('storage')
    
    # Log command
    if storage:
        await storage.log_command(chat_id, "/briefing")
        await send_briefing_to_user(context.bot, chat_id, storage)


async def send_briefing_to_user(bot, chat_id: int, storage):
    """Send daily briefing to a specific user - can be called directly for scheduled briefings"""
    
    if not storage:
        logger.error("Storage not available")
        return
    
    today = datetime.now().strftime("%d/%m/%Y")
    
    # Fetch top CERTIFICATO vehicles
    try:
        vehicles = await storage.get_today_certificato(limit=3)
    except Exception as e:
        logger.error(f"Error fetching vehicles: {e}")
        vehicles = []
    
    if not vehicles:
        # Graceful message when no data
        message = f"""BRIEFING ARGOS - {today}

Nessuna opportunita CERTIFICATO disponibile oggi.

Il nostro sistema analizza continuamente i mercati EU.
Riceverai un aggiornamento quando identificheremo veicoli che 
rispettano i criteri ARGOS.

Per info: ilcombeeretrasher@gmail.com"""
        
        await bot.send_message(chat_id=chat_id, text=message)
        return
    
    # Build briefing message
    n_vehicles = len(vehicles)
    message_lines = [
        f"BRIEFING ARGOS - {today}",
        "",
        f"Veicoli CERTIFICATO disponibili oggi: {n_vehicles}",
    ]
    
    # Add top 3 vehicles
    medals = ["#1", "#2", "#3"]
    
    for i, v in enumerate(vehicles[:3]):
        medal = medals[i] if i < 3 else "-"
        price_eu = v.get('price_eu', 0)
        price_it = v.get('price_it', 0)
        mileage = v.get('mileage', 0)
        
        # Calculate delta if both prices available
        delta_str = ""
        if price_eu and price_it and price_eu > 0:
            delta = ((price_it - price_eu) / price_eu) * 100
            delta_int = int(delta)
            delta_str = f" (+{delta_int} percento)"
        
        conf_pct = int(v.get('confidence', 0)*100)
        price_eu_fmt = f"{int(price_eu):,}" if price_eu else "N/A"
        price_it_fmt = f"{int(price_it):,}" if price_it else "N/A"
        mileage_fmt = f"{int(mileage):,}" if mileage else "N/A"
        
        vehicle_block = [
            "",
            "----------------",
            f"{medal} #{i+1} | {v.get('make', 'N/A')} {v.get('model', 'N/A')} {v.get('year', 'N/A')}",
            f"   Indice ARGOS: {conf_pct} percento",
            f"   Prezzo EU: EUR {price_eu_fmt}",
            f"   Stima IT: EUR {price_it_fmt}{delta_str}",
            f"   Km: {mileage_fmt} | Mercato: {v.get('country', 'N/A')}",
        ]
        message_lines.extend(vehicle_block)
    
    message_lines.extend([
        "",
        "----------------",
        "Per info: ilcombeeretrasher@gmail.com"
    ])
    
    message = "\n".join(message_lines)
    
    # Action buttons
    keyboard = [
        [InlineKeyboardButton("Richiedi dettagli", callback_data="richiedi_dettagli")],
        [InlineKeyboardButton("Contatto", callback_data="contatto")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=reply_markup
    )
