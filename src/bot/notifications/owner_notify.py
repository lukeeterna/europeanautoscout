# -*- coding: utf-8 -*-
"""Notifica owner (@OWNER_CHAT_ID) su nuovi lead e eventi importanti"""

import logging
from datetime import datetime
from telegram import Bot
from telegram.ext import Application
from config import settings

logger = logging.getLogger(__name__)


class OwnerNotifier:
    def __init__(self, application: Application, owner_chat_id: int):
        self.application = application
        self.owner_chat_id = owner_chat_id
        self._lead_counter = 0
    
    async def notify_new_lead(self, chat_id: int, username: str, first_name: str):
        """
        Notifica owner di un nuovo lead registrato.
        Rispetta impostazione NOTIFY_EVERY_N_LEADS.
        """
        self._lead_counter += 1
        
        # Notify only every N leads based on settings
        if self._lead_counter % settings.notify_every_n_leads != 0:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username_display = f"@{username}" if username else "N/A"
        
        message = f"""NUOVO LEAD #{self._lead_counter}

User: {first_name or 'N/A'} ({username_display})
Chat ID: {chat_id}
Ora: {timestamp}

Bot: @CombaRetrovamiautoNotifierbot"""
        
        try:
            await self.application.bot.send_message(
                chat_id=self.owner_chat_id,
                text=message,
                disable_notification=False
            )
            logger.info(f"Owner notified about new lead: {chat_id}")
        except Exception as e:
            logger.error(f"Failed to notify owner about new lead: {e}")
    
    async def notify_daily_summary(self, stats: dict):
        """
        📈 RIEPILOGO GIORNALIERO
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""RIEPILOGO GIORNALIERO

Data: {timestamp}
Veicoli analizzati oggi: {stats.get('analyzed_today', 0)}
CERTIFICATO: {stats.get('certificato', 0)}
VERIFICA ESTESA: {stats.get('verifica_estesa', 0)}
ESCLUSO: {stats.get('escluso', 0)}

Bot: @CombaRetrovamiautoNotifierbot"""
        
        try:
            await self.application.bot.send_message(
                chat_id=self.owner_chat_id,
                text=message,
                disable_notification=True
            )
            logger.info("Daily summary sent to owner")
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
    
    async def notify_bot_online(self):
        """Notify owner when bot starts"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""BOT ONLINE

@CombaRetrovamiautoNotifierbot è operativo.

Orario avvio: {timestamp}
Briefing automatico: ore {settings.briefing_hour}:00
Notifica lead: ogni {settings.notify_every_n_leads}

Protocollo: ARGOS v4"""
        
        try:
            await self.application.bot.send_message(
                chat_id=self.owner_chat_id,
                text=message,
                disable_notification=True
            )
            logger.info("Bot online notification sent to owner")
        except Exception as e:
            logger.error(f"Failed to send bot online notification: {e}")
    
    async def notify_error(self, error_message: str, context: str = ""):
        """Notify owner of critical errors"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""ERRORE BOT

Orario: {timestamp}
Contesto: {context or 'N/A'}
Errore: {error_message[:500]}

@CombaRetrovamiautoNotifierbot"""
        
        try:
            await self.application.bot.send_message(
                chat_id=self.owner_chat_id,
                text=message,
                disable_notification=False
            )
            logger.info("Error notification sent to owner")
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
