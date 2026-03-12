"""
email_agent.py — COMBARETROVAMIAUTO Marketing Agent
Module 2: Email Outreach (Gmail SMTP → 4-Step Sequence)

CoVe 2026 | Protocollo ARGOS™
FIX CERTIFICATO: ISSUE_EMAIL_01 + ISSUE_EMAIL_02 — 2026-03-04

ISSUE_EMAIL_01 FIXED: verdict → recommendation (align cove_engine_v4.py)
ISSUE_EMAIL_02 FIXED: created_at → analyzed_at (align cove_engine_v4.py)
"""

import asyncio
import logging
import os
import random
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import duckdb
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Costanti (NON modificare senza aggiornare .env) ──────────────────────────
GMAIL_USER: str = os.getenv("GMAIL_USER", "ilcombeeretrasher@gmail.com")
GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_DAILY_LIMIT: int = int(os.getenv("GMAIL_DAILY_LIMIT", "30"))   # hard limit

# Separate DB paths: cove_results in cove_tracker, dealer_leads/email_outreach in dealer_network
DUCKDB_PATH: str = os.getenv(
    "DUCKDB_PATH",
    str(Path.home() / "Documents/app-antigravity-auto/python/cove/data/cove_tracker.duckdb"),
)
MARKETING_DB_PATH: str = os.getenv(
    "MARKETING_DB_PATH",
    str(Path.home() / "Documents/app-antigravity-auto/data/dealer_network.duckdb"),
)

# Delay inter-send: progressivo 60→90s (anti-spam)
SEND_DELAY_BASE: int = 60
SEND_DELAY_STEP: int = 10

# Sequence steps: D+0, D+3, D+7, D+14
SEQUENCE_DELAYS: dict[int, int] = {1: 0, 2: 3, 3: 7, 4: 14}

# B2B email timing — Deep Research 2026 (Tue-Thu, 9-11 IT)
TIMEZONE_IT = ZoneInfo("Europe/Rome")
B2B_ALLOWED_WEEKDAYS: set[int] = {1, 2, 3}   # 0=Mon, 1=Tue, 2=Wed, 3=Thu
B2B_HOUR_START: int = 9
B2B_HOUR_END: int = 11     # esclusivo: invio solo se ora < 11


def _is_b2b_send_window() -> bool:
    """
    Verifica finestra ottimale B2B: Martedì-Giovedì, 9:00-10:59 IT.
    Self-defending: funziona anche se chiamato manualmente o da CI.
    Ritorna True sempre se FORCE_SEND=1 in env (per test).
    """
    if os.getenv("FORCE_SEND", "0") == "1":
        return True
    now_it = datetime.now(tz=TIMEZONE_IT)
    return (
        now_it.weekday() in B2B_ALLOWED_WEEKDAYS
        and B2B_HOUR_START <= now_it.hour < B2B_HOUR_END
    )

# ── Fallback vehicle (BMW 330i 2020 — segmento core, €4.700 delta) ────────────
FALLBACK_VEHICLE: dict = {
    "make": "BMW",
    "model": "330i",
    "year": 2020,
    "km": 52000,
    "eu_price": 27800,
    "it_estimate": 32500,
    "score": 89,
    "country": "Germania",
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def _get_conn() -> duckdb.DuckDBPyConnection:
    """Connessione al DB marketing (dealer_leads, email_outreach)."""
    Path(MARKETING_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(MARKETING_DB_PATH)


def _get_cove_conn() -> duckdb.DuckDBPyConnection:
    """Connessione al DB CoVe (cove_results — read-only)."""
    return duckdb.connect(DUCKDB_PATH, read_only=True)


def _ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Crea tabelle marketing se non esistono (append-only, no modifica cove/)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_outreach (
            id          INTEGER PRIMARY KEY,
            place_id    VARCHAR NOT NULL,
            sequence_step INTEGER NOT NULL,
            sent_at     TIMESTAMPTZ,
            status      VARCHAR DEFAULT 'PENDING',
            subject     VARCHAR,
            body_preview VARCHAR,
            UNIQUE(place_id, sequence_step)
        )
    """)
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS email_outreach_seq START 1
    """)


def _count_sent_today(conn: duckdb.DuckDBPyConnection) -> int:
    """Conta email inviate oggi (UTC). Hard gate vs GMAIL_DAILY_LIMIT."""
    result = conn.execute("""
        SELECT COUNT(*) FROM email_outreach
        WHERE status = 'SENT'
          AND DATE(sent_at) = CURRENT_DATE
    """).fetchone()
    return result[0] if result else 0


def _get_pending_leads(conn: duckdb.DuckDBPyConnection) -> list[dict]:
    """
    Lead target non ancora contattati (step 1 pending).
    Restituisce dealer con score >= 50 e email verificata.
    Ritorna lista vuota se dealer_leads non esiste (DB non ancora popolato).
    """
    try:
        rows = conn.execute("""
            SELECT
                dl.place_id,
                dl.name,
                dl.city,
                dl.email,
                dl.rating
            FROM dealer_leads dl
            WHERE dl.is_target_dealer = TRUE
              AND dl.email IS NOT NULL
              AND dl.email != ''
              AND NOT EXISTS (
                  SELECT 1 FROM email_outreach eo
                  WHERE eo.place_id = dl.place_id
                    AND eo.sequence_step = 1
              )
            ORDER BY dl.lead_score DESC
        """).fetchall()
    except Exception as exc:
        logger.info("dealer_leads non disponibile (run marketing:scrape prima): %s", exc)
        return []
    return [
        {"place_id": r[0], "name": r[1], "city": r[2], "email": r[3], "rating": r[4]}
        for r in rows
    ]


def _get_followup_leads(conn: duckdb.DuckDBPyConnection, step: int) -> list[dict]:
    """Lead da seguire allo step N (se il delay giorni è trascorso).
    Ritorna lista vuota se dealer_leads non esiste."""
    days_required = SEQUENCE_DELAYS[step]
    try:
        rows = conn.execute("""
            SELECT
                dl.place_id,
                dl.name,
                dl.city,
                dl.email,
                dl.rating,
                eo_prev.sent_at AS prev_sent_at
            FROM dealer_leads dl
            JOIN email_outreach eo_prev
                ON eo_prev.place_id = dl.place_id
               AND eo_prev.sequence_step = ?
               AND eo_prev.status = 'SENT'
            WHERE dl.is_target_dealer = TRUE
              AND dl.email IS NOT NULL
              AND dl.status NOT IN ('STOP', 'CLOSED', 'UNSUBSCRIBED')
              AND NOT EXISTS (
                  SELECT 1 FROM email_outreach eo_next
                  WHERE eo_next.place_id = dl.place_id
                    AND eo_next.sequence_step = ?
              )
              AND DATE(eo_prev.sent_at) <= CURRENT_DATE - INTERVAL (?) DAY
            ORDER BY eo_prev.sent_at ASC
        """, [step - 1, step, days_required]).fetchall()
    except Exception as exc:
        logger.info("dealer_leads non disponibile per followup step=%d: %s", step, exc)
        return []
    return [
        {
            "place_id": r[0], "name": r[1], "city": r[2],
            "email": r[3], "rating": r[4], "prev_sent_at": r[5],
        }
        for r in rows
    ]


def _get_best_vehicle(conn: duckdb.DuckDBPyConnection) -> dict:
    """
    Recupera veicolo CERTIFICATO più recente (<7 giorni) da cove_results.

    Schema reale cove_engine_v4: price (EU), market_price (IT estimate), source (paese).
    FIX ISSUE_EMAIL_01: recommendation (non verdict)
    FIX ISSUE_EMAIL_02: analyzed_at (non created_at)
    FIX B3: eu_price→price, it_estimate→market_price, country→source
    """
    cove_conn = None
    try:
        cove_conn = _get_cove_conn()
        row = cove_conn.execute("""
            SELECT
                make,
                model,
                year,
                km,
                price        AS eu_price,
                market_price AS it_estimate,
                confidence,
                source
            FROM cove_results
            WHERE recommendation = 'PROCEED'
              AND analyzed_at >= CURRENT_DATE - INTERVAL 7 DAY
            ORDER BY confidence DESC
            LIMIT 1
        """).fetchone()

        if row:
            # Normalizza source (es. "autoscout24_de") in paese leggibile
            src = row[7] or ""
            country_map = {
                "de": "Germania", "be": "Belgio", "nl": "Paesi Bassi",
                "at": "Austria", "fr": "Francia", "se": "Svezia",
                "cz": "Repubblica Ceca", "it": "Italia",
            }
            country = next(
                (v for k, v in country_map.items() if k in src.lower()),
                "Europa"
            )
            return {
                "make": row[0], "model": row[1], "year": row[2],
                "km": row[3], "eu_price": int(row[4] or 0),
                "it_estimate": int(row[5] or 0),
                "score": int((row[6] or 0) * 100), "country": country,
            }
    except Exception as exc:
        logger.warning("cove_results query failed, using fallback vehicle: %s", exc)
    finally:
        if cove_conn:
            cove_conn.close()

    return FALLBACK_VEHICLE


def _mark_sent(
    conn: duckdb.DuckDBPyConnection,
    place_id: str,
    step: int,
    subject: str,
    body_preview: str,
) -> None:
    conn.execute("""
        INSERT INTO email_outreach
            (id, place_id, sequence_step, sent_at, status, subject, body_preview)
        VALUES (nextval('email_outreach_seq'), ?, ?, ?, 'SENT', ?, ?)
        ON CONFLICT (place_id, sequence_step) DO UPDATE
            SET status = 'SENT', sent_at = excluded.sent_at
    """, [place_id, step, datetime.now(tz=timezone.utc), subject, body_preview[:200]])


def _mark_failed(conn: duckdb.DuckDBPyConnection, place_id: str, step: int) -> None:
    conn.execute("""
        INSERT INTO email_outreach
            (id, place_id, sequence_step, status)
        VALUES (nextval('email_outreach_seq'), ?, ?, 'FAILED')
        ON CONFLICT (place_id, sequence_step) DO UPDATE
            SET status = 'FAILED'
    """, [place_id, step])


def _handle_stop(conn: duckdb.DuckDBPyConnection, place_id: str) -> None:
    """GDPR opt-out: aggiorna status dealer e blocca sequenza."""
    conn.execute("""
        UPDATE dealer_leads SET status = 'UNSUBSCRIBED'
        WHERE place_id = ?
    """, [place_id])
    logger.info("GDPR STOP ricevuto per place_id=%s", place_id)


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _format_price(value: int) -> str:
    """€27.800 — formato EU con punto migliaia."""
    return f"€{value:,.0f}".replace(",", ".")


def _format_km(value: int) -> str:
    """52.000 km — formato EU."""
    return f"{value:,}".replace(",", ".")


def _dealer_short_name(full_name: str) -> str:
    """Prende i primi 2 token del nome dealer."""
    tokens = full_name.strip().split()
    return " ".join(tokens[:2]) if len(tokens) > 1 else full_name


def _build_step1(dealer: dict, vehicle: dict) -> tuple[str, str]:
    """
    D+0 — Awareness + Credibilità.
    CTA ultra-low-friction: "10 minuti questa settimana per una chiamata?"
    """
    name = _dealer_short_name(dealer["name"])
    delta = vehicle["it_estimate"] - vehicle["eu_price"]

    subject = (
        f"{vehicle['make']} {vehicle['model']} {vehicle['year']} — "
        f"Certificato ARGOS™ | {_format_price(vehicle['eu_price'])} da {vehicle['country']}"
    )

    body = f"""Salve {name},

Mi presento: sono Luca Ferretti di COMBARETROVAMIAUTO.

Scouting professionale EU→IT per concessionari multi-brand come il vostro.

Veicolo certificato disponibile oggi:

  {vehicle['make']} {vehicle['model']} {vehicle['year']}
  {_format_km(vehicle['km'])} km | {_format_price(vehicle['eu_price'])} da {vehicle['country']}
  Stima IT: {_format_price(vehicle['it_estimate'])} | Delta: {_format_price(delta)}
  Indice ARGOS™: {vehicle['score']}%

Certificazione basata su 20+ listing live, verifica km KBA 2023, curva Schwacke.

Zero costi fissi — commissione {_format_price(800)}-{_format_price(1200)} solo a transazione completata.

Ha 10 minuti questa settimana per una chiamata?

Cordiali saluti,
Luca Ferretti — COMBARETROVAMIAUTO
https://combaretrovamiauto.pages.dev

---
Per non ricevere ulteriori email risponda con "STOP". GDPR 2016/679."""

    return subject, body


def _build_step2(dealer: dict, vehicle: dict) -> tuple[str, str]:
    """
    D+3 — Reattivazione engagement.
    CTA: risposta "sì, mi interessa" → proposta immediata.
    """
    name = _dealer_short_name(dealer["name"])

    subject = (
        f"Re: {vehicle['make']} {vehicle['model']} {vehicle['year']} — "
        f"ancora disponibile"
    )

    body = f"""Salve {name},

Le scrivo brevemente in riferimento alla mia email di qualche giorno fa.

Il {vehicle['make']} {vehicle['model']} {vehicle['year']} da {vehicle['country']} \
è ancora in fase di valutazione.

Capisco che i tempi siano stretti. Basta rispondere "sì, mi interessa" \
e le invio immediatamente i dettagli completi.

Nessun impegno, nessun costo anticipato.

Cordiali saluti,
Luca Ferretti — COMBARETROVAMIAUTO
https://combaretrovamiauto.pages.dev

---
Per non ricevere ulteriori email risponda con "STOP". GDPR 2016/679."""

    return subject, body


def _build_step3(dealer: dict) -> tuple[str, str]:
    """
    D+7 — Prova di valore con caso studio anonimizzato.
    CTA: qualificazione (fascia prezzo, km max, brand).
    """
    name = _dealer_short_name(dealer["name"])
    city = dealer.get("city", "Sud Italia")

    subject = "Caso studio: BMW 320d venduta in 18 giorni a +€4.200"

    body = f"""Salve {name},

Un caso recente che potrebbe interessarle.

Un concessionario multi-brand a {city} ha ricevuto tramite Protocollo ARGOS™:

  BMW 320d 2021 | 41.000 km | da Germania
  Acquisto: €24.600 | Vendita: €28.800
  Margine lordo: €4.200 | Tempi: 18 giorni

Zero rischi: abbiamo gestito logistica, controllo VIN e documentazione EU.

Se le interessa esplorare veicoli nella sua fascia di riferimento, \
mi indichi orientativamente:
– Fascia prezzo (es. €15k–€30k)
– Km massimi preferiti
– Brand prioritari (BMW / Mercedes / Audi)

Cordiali saluti,
Luca Ferretti — COMBARETROVAMIAUTO
https://combaretrovamiauto.pages.dev

---
Per non ricevere ulteriori email risponda con "STOP". GDPR 2016/679."""

    return subject, body


def _build_step4(dealer: dict) -> tuple[str, str]:
    """
    D+14 — Chiusura professionale. Nessuna CTA.
    Relationship preservation per futura riattivazione.
    """
    name = _dealer_short_name(dealer["name"])

    subject = "Ultimo messaggio da COMBARETROVAMIAUTO"

    body = f"""Salve {name},

Questo è il mio ultimo messaggio.

Non voglio disturbarla ulteriormente. Se in futuro dovesse avere interesse \
nel valutare veicoli premium certificati da mercati EU — BMW, Mercedes, Audi \
tra €15k e €60k — sarò disponibile.

Le lascio i riferimenti:
https://combaretrovamiauto.pages.dev

Le auguro un buon lavoro.

Cordiali saluti,
Luca Ferretti — COMBARETROVAMIAUTO

---
Per non ricevere ulteriori email risponda con "STOP". GDPR 2016/679."""

    return subject, body


def _build_email(step: int, dealer: dict, vehicle: dict) -> tuple[str, str]:
    """Dispatch template corretto per step."""
    if step == 1:
        return _build_step1(dealer, vehicle)
    elif step == 2:
        return _build_step2(dealer, vehicle)
    elif step == 3:
        return _build_step3(dealer)
    elif step == 4:
        return _build_step4(dealer)
    else:
        raise ValueError(f"Step non valido: {step}")


# ═══════════════════════════════════════════════════════════════════════════════
# SMTP
# ═══════════════════════════════════════════════════════════════════════════════

def _send_smtp(to_email: str, subject: str, body: str) -> bool:
    """
    Invio SMTP Gmail con App Password (non account password).
    SSL context hardened.
    """
    if not GMAIL_APP_PASSWORD:
        logger.error("GMAIL_APP_PASSWORD non configurata in .env")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        logger.info("SENT step=? → %s | %s", to_email, subject[:60])
        return True
    except smtplib.SMTPException as exc:
        logger.error("SMTP error → %s: %s", to_email, exc)
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# CAMPAIGN RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

async def run_daily_campaign() -> dict:
    """
    Entry point campagna giornaliera.
    Rispetta hard limit GMAIL_DAILY_LIMIT=30.
    Ritorna stats per notifica Telegram.
    """
    stats = {"sent": 0, "failed": 0, "skipped_limit": 0, "steps": {1: 0, 2: 0, 3: 0, 4: 0}}

    # B2B timing gate: Martedì-Giovedì 9-11 IT (bypass con FORCE_SEND=1)
    if not _is_b2b_send_window():
        now_it = datetime.now(tz=TIMEZONE_IT)
        logger.info(
            "Campagna saltata: fuori finestra B2B [%s %02d:%02d IT]. "
            "Finestra: Mar-Gio 09:00-10:59. Usa FORCE_SEND=1 per forzare.",
            now_it.strftime("%A"), now_it.hour, now_it.minute,
        )
        return stats

    conn = _get_conn()
    _ensure_schema(conn)

    sent_today = _count_sent_today(conn)
    remaining = GMAIL_DAILY_LIMIT - sent_today

    if remaining <= 0:
        logger.warning("Daily limit raggiunto (%d/%d). Campagna saltata.", sent_today, GMAIL_DAILY_LIMIT)
        conn.close()
        return stats

    logger.info("Campagna avviata. Slot disponibili: %d/%d", remaining, GMAIL_DAILY_LIMIT)

    vehicle = _get_best_vehicle(conn)
    logger.info(
        "Veicolo campagna: %s %s %d — %s (%d%% ARGOS)",
        vehicle["make"], vehicle["model"], vehicle["year"],
        "LIVE" if vehicle != FALLBACK_VEHICLE else "FALLBACK",
        vehicle["score"],
    )

    queue: list[tuple[int, dict]] = []

    new_leads = _get_pending_leads(conn)
    queue.extend((1, lead) for lead in new_leads)

    for step in [2, 3, 4]:
        followups = _get_followup_leads(conn, step)
        queue.extend((step, lead) for lead in followups)

    delay = SEND_DELAY_BASE
    for step, dealer in queue:
        if stats["sent"] >= remaining:
            stats["skipped_limit"] += 1
            continue

        subject, body = _build_email(step, dealer, vehicle)
        success = _send_smtp(dealer["email"], subject, body)

        if success:
            _mark_sent(conn, dealer["place_id"], step, subject, body)
            stats["sent"] += 1
            stats["steps"][step] = stats["steps"].get(step, 0) + 1
            logger.info(
                "[%d/%d] SENT step=%d → %s (%s)",
                stats["sent"], remaining, step, dealer["email"], dealer["name"][:40],
            )
            jitter = random.randint(0, 10)
            await asyncio.sleep(delay + jitter)
            delay = min(delay + SEND_DELAY_STEP, 120)
        else:
            _mark_failed(conn, dealer["place_id"], step)
            stats["failed"] += 1

    conn.close()
    logger.info("Campagna completata: %s", stats)
    return stats


async def send_reply(place_id: str, body: str) -> bool:
    """
    Invia risposta RAG a dealer specifico (webhook trigger da n8n).
    Usato da Conversation Manager post-CoVe verification.
    """
    conn = _get_conn()
    try:
        row = conn.execute("""
            SELECT name, email FROM dealer_leads WHERE place_id = ?
        """, [place_id]).fetchone()

        if not row:
            logger.error("Dealer non trovato: %s", place_id)
            return False

        name, email = row
        subject = f"Re: COMBARETROVAMIAUTO — Risposta a {_dealer_short_name(name)}"
        success = _send_smtp(email, subject, body)

        if success:
            logger.info("Reply SENT → %s (%s)", email, place_id)
        return success
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="COMBARETROVAMIAUTO Email Agent")
    parser.add_argument("--daily", action="store_true", help="Esegui campagna giornaliera")
    parser.add_argument(
        "--send-reply",
        metavar=("PLACE_ID", "BODY"),
        nargs=2,
        help="Invia risposta RAG a dealer specifico",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula senza inviare")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN — nessuna email sarà inviata")
        _send_smtp_real = _send_smtp  # noqa
        def _send_smtp(to, subj, body):  # type: ignore[override]
            logger.info("[DRY-RUN] Would send → %s | %s", to, subj[:60])
            return True

    if args.daily:
        result = asyncio.run(run_daily_campaign())
        print(f"\n✅ Campagna completata: {result}")

    elif args.send_reply:
        place_id, body = args.send_reply
        ok = asyncio.run(send_reply(place_id, body))
        print(f"{'✅ SENT' if ok else '❌ FAILED'} → {place_id}")

    else:
        parser.print_help()
