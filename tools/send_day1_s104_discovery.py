#!/usr/bin/env python3
"""
ARGOS Automotive — Invio Day 1 S104 Discovery
5 nuovi dealer dalla discovery P1, veicoli reali da CoVe DB.

Usage:
  python3 tools/send_day1_s104_discovery.py --dry-run   # preview senza invio
  python3 tools/send_day1_s104_discovery.py              # invio reale
"""

import os
import sys
import time
import random
import json
import logging
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Load .env
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k.strip(), v)

WA_DAEMON_URL = "http://192.168.1.2:9191"
WA_API_KEY = os.environ.get("ARGOS_API_KEY") or os.environ.get("WA_API_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("argos.outreach.s104")

# ── 5 Dealer Target (WA disponibile, veicoli reali CoVe) ─────
DEALERS = [
    {
        "id": "AUTOQUARTA_MONTERONI_001",
        "name": "AutoQuarta",
        "city": "Monteroni di Lecce",
        "province": "LE",
        "phone_wa": "393803442964",
        "archetipo": "RELAZIONALE",
        "listing_id": "autoscout24_de_b0d65f095510",
        "veicolo": "BMW X3 xDrive20d 2022",
        "km": "50.000",
        "prezzo_de": "34.140",
        "message": (
            "Buongiorno, ho una BMW X3 xDrive20d 2022, 50.000 km,\n"
            "dalla Germania \u2014 \u20ac34.140.\n"
            "Km certificati, storico tagliandi BMW completo.\n"
            "Ho visto che trattate gia' BMW e Mercedes \u2014\n"
            "le mando la scheda con tutti i dettagli?\n\n"
            "Luca Ferretti"
        ),
    },
    {
        "id": "AZ_AUTO_EVOLUTION_002",
        "name": "AZ Auto Evolution",
        "city": "Solofra",
        "province": "AV",
        "phone_wa": "393454146671",
        "archetipo": "RAGIONIERE",
        "listing_id": "autoscout24_de_83adee60eed0",
        "veicolo": "BMW X3 xDrive20d 2022",
        "km": "79.000",
        "prezzo_de": "32.900",
        "message": (
            "Buongiorno, ho una BMW X3 2022, 79.000 km,\n"
            "Germania \u2014 \u20ac32.900. In Italia la stessa\n"
            "non scende sotto i \u20ac38-39.000.\n"
            "Km certificati, garanzia costruttore UE.\n"
            "I numeri le tornano?\n\n"
            "Luca Ferretti"
        ),
    },
    {
        "id": "GRECO_AUTO_RENDE_001",
        "name": "Greco Auto",
        "city": "Rende",
        "province": "CS",
        "phone_wa": "393381668681",
        "archetipo": "TECNICO",
        "listing_id": "mobile_de_421064539",
        "veicolo": "BMW X3 xDrive20d 2021",
        "km": "75.000",
        "prezzo_de": "30.800",
        "message": (
            "Buongiorno, ho una BMW X3 xDrive20d 2021,\n"
            "75.000 km, Germania \u2014 \u20ac30.800.\n"
            "Allestimento M Sport, full LED, navigatore.\n"
            "Km certificati con storico tagliandi BMW.\n"
            "Le interessa vedere la scheda tecnica?\n\n"
            "Luca Ferretti"
        ),
    },
    {
        "id": "STEFANO_AUTO_CERIGNOLA_001",
        "name": "Stefano Auto",
        "city": "Cerignola",
        "province": "FG",
        "phone_wa": "393388199414",
        "archetipo": "PERFORMANTE",
        "listing_id": "autoscout24_de_b0d65f095510",
        "veicolo": "BMW X3 xDrive20d 2022",
        "km": "50.000",
        "prezzo_de": "34.140",
        "message": (
            "Buongiorno, BMW X3 2022, 50.000 km,\n"
            "Germania \u2014 \u20ac34.140.\n"
            "Pronta in 5-7 giorni, tutto gestito.\n"
            "Le mando i dettagli?\n\n"
            "Luca Ferretti"
        ),
    },
    {
        "id": "3D_AUTOMOTIVE_MANDURIA_001",
        "name": "3D Automotive",
        "city": "Manduria",
        "province": "TA",
        "phone_wa": "393289163991",
        "archetipo": "OPPORTUNISTA",
        "listing_id": "autoscout24_de_83adee60eed0",
        "veicolo": "BMW X3 xDrive20d 2022",
        "km": "79.000",
        "prezzo_de": "32.900",
        "message": (
            "Buongiorno, ho una BMW X3 2022, 79.000 km,\n"
            "dalla Germania a \u20ac32.900.\n"
            "In Italia la stessa parte da \u20ac38-39.000.\n"
            "Margine netto interessante.\n"
            "Le mando i numeri completi?\n\n"
            "Luca Ferretti"
        ),
    },
]


def is_business_hours() -> bool:
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    h = now.hour + now.minute / 60
    return (8.0 <= h < 12.0) or (14.0 <= h < 18.0)


def send_wa(phone: str, message: str, dealer_id: str) -> dict:
    """Invia messaggio via WA daemon."""
    import urllib.request
    payload = json.dumps({
        "phone": phone,
        "message": message,
        "dealer_id": dealer_id,
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": WA_API_KEY,
    }
    req = urllib.request.Request(
        f"{WA_DAEMON_URL}/send",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("ARGOS DAY 1 — S104 DISCOVERY (5 dealer)")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE SEND'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"API Key: {'SET' if WA_API_KEY else 'MISSING'}")
    print("=" * 60)

    if not args.dry_run and not is_business_hours():
        print("\n[BLOCK] Fuori orario business (lun-ven 8-12, 14-18)")
        print("Usa --dry-run per preview")
        return

    if not WA_API_KEY and not args.dry_run:
        print("\n[ERROR] ARGOS_API_KEY non impostata in .env")
        return

    sent = 0
    for i, dealer in enumerate(DEALERS, 1):
        print(f"\n--- #{i} {dealer['name']} ({dealer['city']}, {dealer['province']}) ---")
        print(f"  Tel: {dealer['phone_wa']}")
        print(f"  Veicolo: {dealer['veicolo']} | {dealer['km']} km | EUR {dealer['prezzo_de']}")
        print(f"  Listing: {dealer['listing_id']}")
        print(f"  Archetipo: {dealer['archetipo']}")
        print(f"  Messaggio:")
        for line in dealer['message'].split('\n'):
            print(f"    {line}")

        if args.dry_run:
            print(f"  [DRY RUN] Messaggio NON inviato")
            continue

        # Anti-ban delay
        if i > 1:
            delay = random.randint(45, 90)
            print(f"  [WAIT] {delay}s anti-ban delay...")
            time.sleep(delay)

        result = send_wa(dealer['phone_wa'], dealer['message'], dealer['id'])
        if result.get('status') in ('sent', 'queued'):
            print(f"  [OK] Inviato: {result.get('msg_id', '?')}")
            sent += 1
        else:
            print(f"  [ERROR] {result}")

    print(f"\n{'=' * 60}")
    print(f"RISULTATO: {sent}/{len(DEALERS)} messaggi inviati")
    print("=" * 60)


if __name__ == "__main__":
    main()
