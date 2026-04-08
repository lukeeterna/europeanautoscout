#!/usr/bin/env python3
"""
ARGOS Automotive — Invio Day 1 Top 5 Discovery S100
Genera messaggi WA per i 5 dealer scoperti nella sessione S100.

Regole:
- Solo business hours: lun-ven 8:00-12:00 e 14:00-18:00
- Delay random 45-90 sec tra messaggi (anti-ban)
- Idempotente: dealer gia' CONTACTED vengono skippati
- API key dal .env (MAI hardcoded)
- Log ogni invio con timestamp
"""

import os
import sys
import time
import random
import sqlite3
import requests
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ── Setup ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

WA_DAEMON_URL = "http://192.168.1.2:9191/send"
WA_API_KEY    = os.getenv("ARGOS_API_KEY") or os.getenv("WA_API_KEY")
DB_PATH       = BASE_DIR / "dealer_network.sqlite"

_log_dir = BASE_DIR / "logs"
_log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_log_dir / "outreach_day1_top5.log", mode="a"),
    ],
)
log = logging.getLogger("argos.outreach.day1_top5")

# ── Dealer list ────────────────────────────────────────────────────────────────
# Formato telefono: prefisso 39 + numero senza zero iniziale (per WA)
# Canale: 'wa' = invia direttamente | 'tel_first' = solo log, WA non attivo per fissi
DEALERS = [
    {
        "id":       "AZ_AUTO_EVOLUTION_001",
        "name":     "Az Auto Evolution",
        "titolare": None,
        "phone_wa": "393683259045",   # WA diretto
        "canale":   "wa",
        "listing_id": "autoscout24_de_d9204d82ff00",
        "message":  (
            "Buongiorno, ho una Porsche Macan 2022, 55.000 km, Germania \u2014 \u20ac62.500.\n"
            "In Campania la stessa auto non scende sotto i \u20ac72-75.000.\n"
            "Km verificati, tagliandi Porsche Italia compatibili.\n"
            "Ho visto che trattate gi\u00e0 questa fascia \u2014 sono Luca Ferretti.\n"
            "Le mando la scheda completa?"
        ),
    },
    {
        "id":       "AUTOESSE_SRL_001",
        "name":     "Autoesse S.r.l.",
        "titolare": None,
        "phone_wa": None,             # fisso — nessun WA disponibile
        "phone_tel": "0825610208",    # numero da chiamare
        "canale":   "tel_first",      # chiamare prima, WA se non risponde
        "listing_id": "autoscout24_de_b0d65f095510",
        "message":  (
            "Buongiorno, ho trovato una BMW X3 xDrive20d 2022, 50.000 km\n"
            "a \u20ac34.000 in Germania. In Italia la stessa sta a \u20ac38.500.\n"
            "Trasporto Atripalda: circa \u20ac800. Netto per lei: ~\u20ac3.700.\n"
            "Trattate BMW \u2014 ha senso parlarne?\n\n"
            "Luca Ferretti"
        ),
    },
    {
        "id":       "WP_CARS_EBOLI_001",
        "name":     "WP Cars",
        "titolare": None,
        "phone_wa": "393479227573",   # WA diretto
        "canale":   "wa",
        "listing_id": None,  # scraper AS24 404 — prezzo da verifica web mobile.de
        "message":  (
            "Buongiorno, ho una Mercedes GLC 220d 2022, 55.000 km,\n"
            "Germania \u2014 \u20ac39.000. In Campania la stessa parte da \u20ac45.000.\n"
            "Ho visto il vostro stock \u2014 SUV premium \u00e8 il vostro forte.\n"
            "Le mando la scheda con tutti i dettagli?\n\n"
            "Luca Ferretti"
        ),
    },
    {
        "id":       "EXPERT_AUTO_RIARDO_001",
        "name":     "Expert Auto",
        "titolare": "Domenico",
        "phone_wa": None,             # fisso — nessun WA disponibile
        "phone_tel": "0823987096",    # numero da chiamare
        "canale":   "tel_first",
        "listing_id": "autoscout24_de_da6eb6e540f8",
        "message":  (
            "Buongiorno Domenico, ho trovato un\u2019Audi Q5 40 TDI 2022,\n"
            "63.000 km, Germania \u2014 \u20ac33.800. In Italia la stessa sta a \u20ac39.000.\n"
            "Tratta Audi \u2014 i numeri le tornano?\n\n"
            "Luca Ferretti"
        ),
    },
    {
        "id":       "ROMANAZZI_AUTO_001",
        "name":     "Romanazzi Auto",
        "titolare": "Luca Romanazzi",
        "phone_wa": None,             # fisso — nessun WA disponibile
        "phone_tel": "0804249944",    # numero da chiamare
        "canale":   "tel_first",
        "listing_id": "autoscout24_de_b0d65f095510",
        "message":  (
            "Buongiorno, sono Luca Ferretti \u2014 lavoro con concessionari\n"
            "del Sud per trovare BMW e Audi dalla Germania.\n"
            "30 anni di attivit\u00e0 come i suoi si vedono \u2014 sa gi\u00e0 come funziona l\u2019import.\n"
            "Ho una BMW X3 2022, 50.000 km, Germania, \u20ac34.000. Le mando i numeri?\n\n"
            "Luca"
        ),
    },
]


# ── Business hours check ───────────────────────────────────────────────────────
def is_business_hours() -> bool:
    """Lun-ven 8:00-12:00 e 14:00-18:00."""
    now = datetime.now()
    if now.weekday() >= 5:          # sabato=5, domenica=6
        return False
    h = now.hour + now.minute / 60
    return (8.0 <= h < 12.0) or (14.0 <= h < 18.0)


def next_business_slot() -> str:
    """Restituisce una stringa human-readable del prossimo slot utile."""
    now = datetime.now()
    wd  = now.weekday()
    h   = now.hour + now.minute / 60
    if wd < 5:
        if h < 8.0:
            return f"oggi alle 08:00"
        if h < 12.0:
            return f"oggi alle 08:00 (sei gia' in orario — controlla)"
        if h < 14.0:
            return f"oggi alle 14:00"
        if h < 18.0:
            return f"oggi alle 14:00 (sei gia' in orario — controlla)"
    days_until_monday = (7 - wd) % 7 or 7
    return f"lunedi' prossimo alle 08:00"


# ── CRM helpers ────────────────────────────────────────────────────────────────
def get_dealer_status(conn: sqlite3.Connection, dealer_id: str) -> str | None:
    row = conn.execute(
        "SELECT pipeline_status FROM dealers WHERE dealer_id = ?", (dealer_id,)
    ).fetchone()
    return row[0] if row else None


def mark_contacted(conn: sqlite3.Connection, dealer_id: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute(
        """
        UPDATE dealers
        SET pipeline_status  = 'CONTACTED',
            first_contact_at = COALESCE(first_contact_at, datetime('now')),
            last_contact_at  = datetime('now'),
            notes            = notes || ' | Day1 sent ' || ?,
            updated_at       = datetime('now')
        WHERE dealer_id = ?
        """,
        (today, dealer_id),
    )
    conn.commit()


# ── Listing validation gate ───────────────────────────────────────────────────
def validate_listing(dealer: dict) -> bool:
    """Verifica che il listing CoVe referenziato esista ancora in DuckDB.
    Se il dealer non ha listing_id (es. prezzo da web), skip validation."""
    listing_id = dealer.get("listing_id")
    if not listing_id:
        log.info(f"  [GATE] No listing_id — skip validation (prezzo da web)")
        return True

    try:
        import duckdb
        db_path = BASE_DIR / "src" / "cove" / "data" / "cove_tracker.duckdb"
        db = duckdb.connect(str(db_path), read_only=True)
        row = db.execute(
            "SELECT recommendation, confidence, fraud_overall FROM cove_results WHERE listing_id = ?",
            [listing_id],
        ).fetchone()
        db.close()

        if not row:
            log.warning(f"  [GATE] BLOCCATO — listing {listing_id} non trovato in DuckDB")
            return False

        recommendation, confidence, fraud = row
        if recommendation == "SKIP":
            log.warning(f"  [GATE] BLOCCATO — listing {listing_id} ha recommendation=SKIP")
            return False
        if fraud and fraud != "CLEAN":
            log.warning(f"  [GATE] BLOCCATO — listing {listing_id} ha fraud={fraud}")
            return False

        log.info(f"  [GATE] OK — {listing_id} | {recommendation} | conf={confidence} | {fraud}")
        return True
    except (ImportError, FileNotFoundError) as e:
        log.error(f"  [GATE] BLOCCATO — DuckDB non disponibile: {e}")
        return False
    except Exception as e:
        log.warning(f"  [GATE] Errore transiente: {e} — BLOCCATO per sicurezza")
        return False


# ── WA send ────────────────────────────────────────────────────────────────────
def send_wa(phone: str, message: str, dry_run: bool = False) -> dict:
    """Invia messaggio via WA daemon. Ritorna dict con esito."""
    if not WA_API_KEY:
        raise EnvironmentError("ARGOS_API_KEY non trovata nel .env")

    payload = {"phone": phone, "message": message}
    if dry_run:
        payload["dry_run"] = True

    resp = requests.post(
        WA_DAEMON_URL,
        json=payload,
        headers={"Content-Type": "application/json", "X-API-Key": WA_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    force   = "--force" in sys.argv      # bypass orario (solo per test)

    if dry_run:
        log.info("=== MODALITA' DRY-RUN — nessun messaggio inviato ===")

    # Controllo orario
    if not force and not dry_run and not is_business_hours():
        slot = next_business_slot()
        log.warning(
            "Orario non business (lun-ven 8-12 / 14-18). "
            f"Attendi: {slot}. Usa --force per bypassare (solo test)."
        )
        sys.exit(0)

    if not WA_API_KEY:
        log.error("ARGOS_API_KEY non trovata nel .env — impossibile procedere")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))

    sent     = 0
    skipped  = 0
    failed   = 0

    for i, dealer in enumerate(DEALERS):
        name      = dealer["name"]
        dealer_id = dealer["id"]
        phone     = dealer["phone_wa"]
        phone_tel = dealer.get("phone_tel")
        canale    = dealer["canale"]
        message   = dealer["message"]
        log.info(f"--- [{i+1}/5] {name} | WA: {phone or 'N/A'} | Tel: {phone_tel or 'N/A'} ---")

        # Idempotenza: skip se gia' CONTACTED
        status = get_dealer_status(conn, dealer_id)
        if status == "CONTACTED":
            log.info(f"  SKIP — gia' CONTACTED nel CRM")
            skipped += 1
            continue

        # Gate validazione: verifica listing CoVe prima di inviare
        if not validate_listing(dealer):
            log.error(f"  BLOCCATO — listing non valido, messaggio NON inviato")
            failed += 1
            continue

        # Dealer su fisso senza WA: solo log istruzione telefonica, nessun invio WA
        if canale == "tel_first" and not phone:
            log.info(
                f"  [AZIONE MANUALE RICHIESTA] Canale = TELEFONO.\n"
                f"  Chiamare: {phone_tel}\n"
                f"  Messaggio da leggere/inviare dopo la chiamata:\n"
                f"  -----\n"
                f"{message}\n"
                f"  -----"
            )
            log.info(f"  Nessun WA disponibile — dealer registrato come TEL_PENDING")
            # Non segniamo CONTACTED finche' non chiamato — solo aggiorniamo la nota
            conn.execute(
                "UPDATE dealers SET notes = notes || ' | Tel-first: chiamata da fare', "
                "updated_at = datetime('now') WHERE dealer_id = ?",
                (dealer_id,),
            )
            conn.commit()
            skipped += 1
            continue

        # Dealer su fisso CON WA disponibile: prima informa di chiamare, poi manda WA
        if canale == "tel_first" and phone:
            log.info(
                f"  NOTA: canale primario = TELEFONO. "
                f"Chiamare {phone_tel} prima di inviare WA se possibile."
            )

        # Invio WA (o dry-run)
        try:
            result = send_wa(phone, message, dry_run=dry_run)
            tag = "[DRY-RUN]" if dry_run else "[INVIATO]"
            log.info(f"  {tag} {name} → {phone} | risposta: {result}")

            if not dry_run:
                mark_contacted(conn, dealer_id)
                log.info(f"  CRM aggiornato → CONTACTED")
            sent += 1

        except requests.exceptions.ConnectionError:
            log.error(f"  ERRORE connessione daemon ({WA_DAEMON_URL}) — continuo")
            failed += 1
        except requests.exceptions.HTTPError as e:
            log.error(f"  ERRORE HTTP {e.response.status_code}: {e.response.text} — continuo")
            failed += 1
        except Exception as e:
            log.error(f"  ERRORE imprevisto: {e} — continuo")
            failed += 1

        # Delay anti-ban tra messaggi WA (basato su ultimo invio reale, non posizione nel loop)
        if not dry_run and phone and sent > 0:
            delay = random.randint(45, 90)
            log.info(f"  Attendo {delay}s prima del prossimo invio...")
            time.sleep(delay)

    conn.close()

    log.info("==============================================")
    log.info(f"RIEPILOGO: inviati={sent} | skippati={skipped} | falliti={failed}")
    log.info("==============================================")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
