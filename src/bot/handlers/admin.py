"""
ARGOS™ Bot — Admin Handler
==========================

Owner notifications and admin callbacks.
Notifiche Telegram + Email SMTP per nuovi lead.
CoVe 2026 FACTORED
"""

from __future__ import annotations

import html
import logging
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from python.bot.config import Config
from python.bot.storage.bot_db import BotDatabase

logger = logging.getLogger(__name__)


class AdminHandler:
    """Handles owner notifications and admin callbacks."""

    def __init__(self):
        self.config = Config()
        self.db = BotDatabase()

    async def notify_new_lead(
        self,
        bot: Bot,
        lead_data: dict[str, Any],
        lead_id: str,
    ) -> None:
        """
        Notify owner of new lead via Telegram and optionally email.
        """
        if not self.config.owner_chat_id:
            logger.warning("No owner chat ID configured, skipping notification")
            return

        # Build notification message
        telefono = lead_data.get("telefono") or "<i>Non fornito</i>"
        username = html.escape(lead_data.get("telegram_username", "Unknown"))
        nome_azienda = html.escape(lead_data.get("nome_azienda", "N/D"))

        message = f"""🔔 <b>NUOVO BRIEFING RICEVUTO</b>

👤 @{username} | {nome_azienda}
📱 {html.escape(str(telefono))}

🚗 {html.escape(lead_data.get('brand', 'N/D'))} {html.escape(lead_data.get('modello', 'N/D'))} {lead_data.get('anno', 'N/D')}
📏 Max: {html.escape(lead_data.get('km_max', 'N/D'))}
💶 Budget: {html.escape(lead_data.get('budget_max', 'N/D'))}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}
🆔 Lead ID: <code>{lead_id}</code>
"""

        # Admin keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Segna In Lavorazione", callback_data=f"mark_working_{lead_id}")],
        ])

        try:
            # Send Telegram notification
            await bot.send_message(
                chat_id=self.config.owner_chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
            logger.info(f"Owner notified of new lead: {lead_id}")

        except Exception as e:
            logger.error(f"Failed to notify owner via Telegram: {e}")

        # Send email notification if SMTP configured
        if self.config.smtp_enabled:
            try:
                self._send_email_notification(lead_data, lead_id)
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")

    def _send_email_notification(self, lead_data: dict[str, Any], lead_id: str) -> None:
        """Send email notification to owner."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🔔 Nuovo Briefing — {lead_data.get('brand', 'N/D')} {lead_data.get('modello', 'N/D')}"
            msg["From"] = self.config.gmail_user
            msg["To"] = self.config.owner_email

            # Plain text version
            text_body = f"""
NUOVO BRIEFING RICEVUTO

Utente: @{lead_data.get('telegram_username', 'Unknown')}
Nome/Azienda: {lead_data.get('nome_azienda', 'N/D')}
Telefono: {lead_data.get('telefono') or 'Non fornito'}

Veicolo: {lead_data.get('brand', 'N/D')} {lead_data.get('modello', 'N/D')} {lead_data.get('anno', 'N/D')}
Km max: {lead_data.get('km_max', 'N/D')}
Budget: {lead_data.get('budget_max', 'N/D')}

Lead ID: {lead_id}
Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

            # HTML version
            telefono = lead_data.get("telefono") or "Non fornito"
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
<h2>🔔 Nuovo Briefing Ricevuto</h2>

<table style="border-collapse: collapse; width: 100%;">
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Utente</b></td><td style="padding: 8px; border: 1px solid #ddd;">@{lead_data.get('telegram_username', 'Unknown')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Nome/Azienda</b></td><td style="padding: 8px; border: 1px solid #ddd;">{html.escape(lead_data.get('nome_azienda', 'N/D'))}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Telefono</b></td><td style="padding: 8px; border: 1px solid #ddd;">{html.escape(str(telefono))}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Brand</b></td><td style="padding: 8px; border: 1px solid #ddd;">{html.escape(lead_data.get('brand', 'N/D'))}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Modello</b></td><td style="padding: 8px; border: 1px solid #ddd;">{html.escape(lead_data.get('modello', 'N/D'))}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Anno</b></td><td style="padding: 8px; border: 1px solid #ddd;">{lead_data.get('anno', 'N/D')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Km max</b></td><td style="padding: 8px; border: 1px solid #ddd;">{html.escape(lead_data.get('km_max', 'N/D'))}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Budget</b></td><td style="padding: 8px; border: 1px solid #ddd;">{html.escape(lead_data.get('budget_max', 'N/D'))}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Lead ID</b></td><td style="padding: 8px; border: 1px solid #ddd;"><code>{lead_id}</code></td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Data</b></td><td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</td></tr>
</table>

<p><i>COMBARETROVAMIAUTO — Protocollo ARGOS™</i></p>
</body>
</html>
"""

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Send via Gmail SMTP
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.config.gmail_user, self.config.gmail_password)
                server.sendmail(
                    self.config.gmail_user,
                    self.config.owner_email,
                    msg.as_string(),
                )

            logger.info(f"Email notification sent for lead: {lead_id}")

        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise

    async def mark_working(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle 'Mark as Working' callback from owner.
        Updates lead status and notifies dealer.
        """
        if not update.callback_query or not update.effective_user:
            return

        query = update.callback_query
        user_id = update.effective_user.id

        # Check if user is admin
        if user_id not in self.config.admin_chat_ids:
            await query.answer("⛔ Non autorizzato", show_alert=True)
            return

        await query.answer()

        # Extract lead ID from callback data
        callback_data = query.data
        lead_id = callback_data.replace("mark_working_", "")

        try:
            # Update lead status
            success = self.db.update_lead_status(lead_id, "IN_LAVORAZIONE")

            if not success:
                await query.edit_message_text(
                    f"{query.message.text}\n\n❌ Lead non trovato o già aggiornato"
                )
                return

            # Get lead data to notify dealer
            lead = self.db.get_lead_by_id(lead_id)
            if lead:
                # Notify dealer
                await context.bot.send_message(
                    chat_id=lead["telegram_user_id"],
                    text="""
<b>📋 Briefing Preso in Carico</b>

Il tuo briefing è stato preso in carico dal team.

Ti contatteremo presto con i veicoli disponibili.

<i>COMBARETROVAMIAUTO — Protocollo ARGOS™</i>
""",
                    parse_mode=ParseMode.HTML,
                )

            # Update owner message
            await query.edit_message_text(
                f"{query.message.text}\n\n✅ <b>Segnato come IN LAVORAZIONE</b>",
                parse_mode=ParseMode.HTML,
            )

            logger.info(f"Lead {lead_id} marked as IN_LAVORAZIONE by admin {user_id}")

        except Exception as e:
            logger.exception(f"Error marking lead as working: {e}")
            await query.edit_message_text(
                f"{query.message.text}\n\n❌ Errore nell'aggiornamento"
            )
