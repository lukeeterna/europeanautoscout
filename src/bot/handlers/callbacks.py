# -*- coding: utf-8 -*-
"""
Handler callbacks — Gestione InlineKeyboard callbacks
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    callback_data = query.data
    chat_id = update.effective_chat.id
    
    # Log the callback
    storage = context.application.bot_data.get('storage')
    if storage:
        await storage.log_command(chat_id, f"callback:{callback_data}")
    
    # Route to appropriate handler
    if callback_data == "start":
        # Re-send welcome message
        keyboard = [
            [InlineKeyboardButton("Come funziona", callback_data="come_funziona")],
            [InlineKeyboardButton("Struttura fee", callback_data="fee")],
            [InlineKeyboardButton("Contatto diretto", callback_data="contatto")],
            [InlineKeyboardButton("Report oggi", callback_data="briefing")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="""Benvenuto in COMBARETROVAMIAUTO.

Scouting veicoli premium EU per dealer italiani indipendenti.
BMW · Mercedes · Audi · 2018-2023 · EUR 15k-60k

Il nostro Protocollo ARGOS™ analizza ogni veicolo su 4 dimensioni indipendenti prima di proporlo.

Fee: EUR 800-1.200 per transazione completata.
Zero costi fissi — paghi solo se acquisti.

----------------
Cosa vuoi fare?""",
            reply_markup=reply_markup
        )
        
    elif callback_data == "briefing":
        # Send briefing directly via callback
        if storage:
            from . import briefing
            await briefing.send_briefing_to_user(context.bot, chat_id, storage)
        
    elif callback_data == "fee":
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
        await query.edit_message_text(text=message)
        
    elif callback_data == "come_funziona":
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
        await query.edit_message_text(text=message)
        
    elif callback_data == "contatto":
        message = """CONTATTO DIRETTO

Per informazioni, partnership o richieste specifiche:

Email: ilcombeeretrasher@gmail.com

Rispondiamo entro 24 ore lavorative.

----------------
COMBARETROVAMIAUTO
Scouting veicoli premium EU per dealer italiani
Protocollo ARGOS - Fee solo a buon fine"""
        await query.edit_message_text(text=message)
        
    elif callback_data == "richiedi_dettagli":
        message = """RICHIESTA DETTAGLI

Per ricevere dettagli completi sui veicoli mostrati:

Email: ilcombeeretrasher@gmail.com
Indica il modello di tuo interesse e ti invieremo:
- Link all'annuncio originale
- Report ARGOS™ completo
- Stima costi totali (veicolo + trasporto + formalità)

Risposta entro 24 ore."""
        await query.edit_message_text(text=message)
        
    else:
        logger.warning(f"Unknown callback: {callback_data}")
        await query.edit_message_text(text="Opzione non riconosciuta. Usa /start per ricominciare.")
