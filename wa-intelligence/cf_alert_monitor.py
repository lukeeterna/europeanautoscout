#!/usr/bin/env python3
"""
cf_alert_monitor.py — ARGOS Cloudflare Alert Monitor
S153 | Enterprise Grade | PM2 Managed

RESPONSABILITA':
  - Polling IMAP Gmail (ferretti.argosautomotive@gmail.com) ogni 5 min
  - Filtro FROM *.cloudflare.com UNSEEN
  - Parse subject + body per estrarre product/threshold/usage
  - Push Telegram a Luke con riepilogo + link dashboard CF
  - Mark email come \\Seen dopo invio (idempotenza)
  - Log audit su /tmp/argos-cf-monitor.log

ENV richieste (da wa-intelligence/.env, caricate via PM2 ecosystem):
  - GMAIL_FERRETTI_EMAIL
  - GMAIL_FERRETTI_APP_PASSWORD
  - ARGOS_TELEGRAM_TOKEN
  - ARGOS_TELEGRAM_CHAT_ID

AVVIO daemon:  pm2 start ecosystem.config.js --only argos-cf-monitor
TEST one-shot: python3 cf_alert_monitor.py --once
"""

import email
import imaplib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from email.header import decode_header
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Rome")
POLL_INTERVAL_SEC = 300  # 5 min
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
LOG_FILE = "/tmp/argos-cf-monitor.log"
CF_DASHBOARD_URL = "https://dash.cloudflare.com/22ddff3a4ef544511523a841b3dcadf8/r2/overview"

# Stati salute monitor (per /status)
HEARTBEAT_FILE = "/tmp/argos-cf-monitor-heartbeat.txt"


def log(msg: str):
    """Log JSON-line su stdout (PM2 raccoglie) + file."""
    line = f"[{datetime.now(TZ).strftime('%d/%m/%Y %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def heartbeat():
    """Touch file per healthcheck esterno."""
    try:
        with open(HEARTBEAT_FILE, "w") as f:
            f.write(datetime.now(TZ).isoformat())
    except Exception:
        pass


def env(key: str, required: bool = True) -> str:
    val = os.environ.get(key, "").strip()
    if required and not val:
        log(f"FATAL: env '{key}' missing")
        sys.exit(2)
    return val


def telegram_send(text: str, token: str, chat_id: str) -> bool:
    """Send a Telegram message via HTTP API. Returns True on 200."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        log(f"telegram_send_error: {type(e).__name__}: {e}")
        return False


def decode_mime(raw) -> str:
    """Decode MIME-encoded header to plain str."""
    if raw is None:
        return ""
    parts = decode_header(raw)
    out = []
    for txt, enc in parts:
        if isinstance(txt, bytes):
            try:
                out.append(txt.decode(enc or "utf-8", errors="replace"))
            except Exception:
                out.append(txt.decode("utf-8", errors="replace"))
        else:
            out.append(txt)
    return "".join(out)


def extract_body(msg) -> str:
    """Extract plain text body from email.message.Message."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                except Exception:
                    continue
        # fallback HTML strip
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    html = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                    return re.sub(r"<[^>]+>", " ", html)
                except Exception:
                    continue
    else:
        try:
            return msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="replace"
            )
        except Exception:
            return str(msg.get_payload())
    return ""


def severity_from_subject(subject: str) -> str:
    """Heuristic severity tagging based on CF email subject."""
    s = subject.lower()
    if any(k in s for k in ["exceeded", "over limit", "billing", "charge", "invoice"]):
        return "🔴 CRITICAL"
    if any(k in s for k in ["80%", "approaching", "warning", "near limit"]):
        return "🟡 WARNING"
    if any(k in s for k in ["50%", "notice", "info"]):
        return "🟢 INFO"
    return "⚪ ALERT"


def format_alert(subject: str, body: str, date_hdr: str) -> str:
    """Build Telegram message from CF email."""
    sev = severity_from_subject(subject)
    # Trim body: keep first 600 chars, strip excessive whitespace
    body_clean = re.sub(r"\s+", " ", body).strip()[:600]
    return (
        f"{sev} <b>Cloudflare Alert</b>\n\n"
        f"<b>Subject:</b> {subject}\n"
        f"<b>Received:</b> {date_hdr}\n\n"
        f"<i>{body_clean}</i>\n\n"
        f"📊 Dashboard: {CF_DASHBOARD_URL}\n"
        f"🤖 ARGOS CF Alert Monitor"
    )


def poll_once(imap_email: str, imap_pwd: str, tg_token: str, tg_chat: str) -> dict:
    """One IMAP poll cycle. Returns counters."""
    stats = {"checked": 0, "cf_unseen": 0, "sent": 0, "errors": 0}
    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        imap.login(imap_email, imap_pwd)
        imap.select("INBOX")

        # Search Cloudflare unseen messages
        # FROM matches cloudflare.com (covers notifications@cloudflare.com, billing@, etc.)
        status, data = imap.search(None, '(UNSEEN FROM "cloudflare.com")')
        if status != "OK":
            log(f"imap_search_fail: {status}")
            stats["errors"] += 1
            imap.logout()
            return stats

        ids = data[0].split()
        stats["checked"] = stats["cf_unseen"] = len(ids)
        if not ids:
            imap.logout()
            return stats

        for msg_id in ids:
            try:
                status, msg_data = imap.fetch(msg_id, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    stats["errors"] += 1
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subject = decode_mime(msg.get("Subject"))
                date_hdr = msg.get("Date", "")
                body = extract_body(msg)

                alert_text = format_alert(subject, body, date_hdr)
                if telegram_send(alert_text, tg_token, tg_chat):
                    # Mark as read only after successful Telegram delivery
                    imap.store(msg_id, "+FLAGS", "\\Seen")
                    stats["sent"] += 1
                    log(f"alert_sent subject={subject!r}")
                else:
                    log(f"telegram_failed_keep_unseen subject={subject!r}")
                    stats["errors"] += 1
            except Exception as e:
                log(f"msg_process_error id={msg_id}: {type(e).__name__}: {e}")
                stats["errors"] += 1

        imap.logout()
    except imaplib.IMAP4.error as e:
        log(f"imap_login_fail: {e}")
        stats["errors"] += 1
    except Exception as e:
        log(f"poll_error: {type(e).__name__}: {e}")
        stats["errors"] += 1

    return stats


def main():
    once_mode = "--once" in sys.argv

    imap_email = env("GMAIL_FERRETTI_EMAIL")
    imap_pwd = env("GMAIL_FERRETTI_APP_PASSWORD")
    tg_token = env("ARGOS_TELEGRAM_TOKEN")
    tg_chat = env("ARGOS_TELEGRAM_CHAT_ID")

    log(f"cf_alert_monitor_start mode={'once' if once_mode else 'daemon'} email={imap_email}")

    # Startup ping (only on daemon mode, helps verify Telegram config)
    if not once_mode and os.environ.get("CF_MONITOR_STARTUP_PING", "1") == "1":
        startup_msg = (
            "🟢 <b>ARGOS CF Alert Monitor avviato</b>\n\n"
            f"Account: {imap_email}\n"
            f"Poll interval: {POLL_INTERVAL_SEC}s\n"
            f"Filter: FROM cloudflare.com UNSEEN\n\n"
            "Riceverai alert qui quando R2 si avvicina a soglie free tier."
        )
        telegram_send(startup_msg, tg_token, tg_chat)

    while True:
        stats = poll_once(imap_email, imap_pwd, tg_token, tg_chat)
        heartbeat()
        log(f"poll_done {json.dumps(stats)}")

        if once_mode:
            sys.exit(0 if stats["errors"] == 0 else 1)

        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
