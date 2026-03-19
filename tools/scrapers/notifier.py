"""
ARGOS™ Market Intelligence — Telegram Notifier
Invia digest e alert al founder via Telegram.

Usa urllib stdlib — zero dipendenze esterne.
Pattern identico a wa-intelligence/response-analyzer.py
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.environ.get('ARGOS_TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('ARGOS_TELEGRAM_CHAT_ID', '931063621')


def send_telegram(text: str, parse_mode: str = '') -> bool:
    """Invia messaggio Telegram. Ritorna True se OK."""
    if not TELEGRAM_BOT_TOKEN:
        print('[WARN] ARGOS_TELEGRAM_TOKEN non impostato — skip notifica')
        return False

    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

    # Tronca a 4096 char (limite Telegram)
    if len(text) > 4000:
        text = text[:3997] + '...'

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
    }
    if parse_mode:
        payload['parse_mode'] = parse_mode

    data = urllib.parse.urlencode(payload).encode()
    try:
        req = urllib.request.Request(url, data=data, method='POST')
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.status == 200
    except Exception as e:
        print(f'[ERROR] Telegram send failed: {e}')
        # Retry senza parse_mode se Markdown fallisce
        if parse_mode:
            return send_telegram(text, parse_mode='')
        return False


def send_market_digest(digest_text: str) -> bool:
    """Invia il digest market intelligence."""
    return send_telegram(digest_text)


def send_deal_alert(make: str, model: str, year: int, price: int,
                    avg_price: int, country: str, url: str) -> bool:
    """Invia alert per deal interessante."""
    discount = int(((avg_price - price) / avg_price) * 100) if avg_price > 0 else 0
    text = (
        f"DEAL ALERT — ARGOS Market Intel\n\n"
        f"{make} {model} {year}\n"
        f"Prezzo: EUR {price:,} ({discount}% sotto media EUR {avg_price:,})\n"
        f"Paese: {country}\n"
        f"Link: {url}"
    )
    return send_telegram(text)


def send_scraper_error(portal: str, country: str, error: str) -> bool:
    """Notifica errore scraper."""
    text = (
        f"SCRAPER ERROR — ARGOS Market Intel\n\n"
        f"Portale: {portal} [{country}]\n"
        f"Errore: {error}\n"
        f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    return send_telegram(text)


def send_scraper_summary(portal: str, total_found: int, new: int,
                         updated: int, removed: int, duration_sec: float,
                         errors: int = 0) -> bool:
    """Invia summary dopo run scraper."""
    text = (
        f"SCRAPER COMPLETATO — {portal.upper()}\n\n"
        f"Trovati: {total_found} | Nuovi: {new} | Aggiornati: {updated} | Rimossi: {removed}\n"
        f"Errori: {errors} | Durata: {duration_sec:.0f}s\n"
        f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    return send_telegram(text)
