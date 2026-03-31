#!/usr/bin/env python3
"""
send_day7_tier0.py — Invia Day 7 ai 3 TIER0 con PDF allegato
Eseguire domani mattina (1 aprile) alle 8:30.

PREREQUISITO: Google Business Profile DEVE essere live prima dell'invio.
Se GBP non è creato, NON inviare — il dealer cerca e non trova nulla.

Uso: python3 tools/send_day7_tier0.py [--dry-run]
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WA_DAEMON = "http://192.168.1.2:9191"

# PDF dossier da allegare (i migliori per ciascun dealer)
DOSSIERS = {
    "stile_car": os.path.join(PROJECT_ROOT, "dossiers/ARGOS_BMW_X3_2022_Stile_Car_ee60eed0.pdf"),
    "car_plus": os.path.join(PROJECT_ROOT, "dossiers/ARGOS_BMW_X3_2022_Car_Plus_c3405b5d.pdf"),
    "samy_auto": os.path.join(PROJECT_ROOT, "dossiers/ARGOS_BMW_X3_2022_Sa.My._Auto_4c65e9de.pdf"),
}

# Messaggi Day 7 — V3 bridge on-demand
MESSAGES = {
    "stile_car": {
        "wa": "393334254654",
        "name": "Stile Car",
        "titolare": "Domenico",
        "text": (
            "Buongiorno Domenico — le avevo scritto la settimana scorsa "
            "per un paio di auto dalla Germania.\n\n"
            "Ho capito che probabilmente non è il momento giusto. "
            "Volevo solo che sapesse: quando ha un cliente che cerca "
            "una tedesca specifica, mi scriva marca e budget. "
            "Le mando 3 opzioni verificate in 24 ore, paga solo a consegna.\n\n"
            "Le allego un esempio di quello che preparo per i dealer "
            "con cui lavoro.\n\n"
            "Luca Ferretti"
        ),
    },
    "car_plus": {
        "wa": "393289617180",
        "name": "Car Plus",
        "titolare": "Luca",
        "text": (
            "Buongiorno — le avevo scritto qualche giorno fa.\n\n"
            "Nessun problema se non era il momento. "
            "Se le capita un cliente che cerca una tedesca "
            "(BMW, Audi, Mercedes, Porsche) mi scriva modello e budget. "
            "In 24 ore le mando 3 opzioni con km certificati e margine. "
            "Zero impegno, paga solo se la prende.\n\n"
            "Le lascio un esempio di dossier che preparo.\n\n"
            "Luca Ferretti"
        ),
    },
    "samy_auto": {
        "wa": "393492587423",
        "name": "Sa.My. Auto",
        "titolare": "Antonio",
        "text": (
            "Buongiorno Antonio — le avevo scritto per un'opportunità "
            "dalla Germania.\n\n"
            "So che con la sua esperienza in Germania ha già "
            "i suoi canali. Se però le serve un secondo occhio "
            "su 73 portali EU per una richiesta specifica del cliente, "
            "sono a disposizione. Ricerca gratuita, paga solo a consegna.\n\n"
            "Le allego un esempio.\n\n"
            "Luca Ferretti"
        ),
    },
}


def check_daemon():
    try:
        resp = urllib.request.urlopen(f"{WA_DAEMON}/status", timeout=5)
        data = json.loads(resp.read())
        if data.get("wa_status") != "connected":
            print("[ERROR] WA not connected")
            return False
        if data.get("daily_remaining", 0) < 6:
            print(f"[WARN] Only {data.get('daily_remaining')} messages remaining today")
            return False
        print(f"[OK] WA daemon connected, {data.get('daily_remaining')} remaining")
        return True
    except Exception as e:
        print(f"[ERROR] Daemon unreachable: {e}")
        return False


def send_message(wa_number, text, pdf_path=None):
    """Send WA message via daemon. Returns True on success."""
    payload = {
        "to": wa_number,
        "text": text,
    }
    if pdf_path and os.path.exists(pdf_path):
        payload["pdf"] = pdf_path

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{WA_DAEMON}/send",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result.get("status") == "sent"
    except Exception as e:
        print(f"[ERROR] Send failed: {e}")
        return False


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("ARGOS — Day 7 TIER0 Outreach")
    print("=" * 60)

    if not dry_run:
        if not check_daemon():
            print("\n[ABORT] Fix daemon issues before sending.")
            sys.exit(1)

    for dealer_id, msg in MESSAGES.items():
        pdf = DOSSIERS.get(dealer_id)
        pdf_exists = pdf and os.path.exists(pdf)
        pdf_size = os.path.getsize(pdf) if pdf_exists else 0

        print(f"\n--- {msg['name']} ({msg['titolare']}) ---")
        print(f"  WA: {msg['wa']}")
        print(f"  PDF: {'OK' if pdf_exists else 'MISSING'} ({pdf_size // 1024}KB)")
        print(f"  Messaggio ({len(msg['text'])} chars):")
        print(f"  {msg['text'][:100]}...")

        if dry_run:
            print("  [DRY RUN] Would send message + PDF")
        else:
            # Send text first
            ok = send_message(msg["wa"], msg["text"])
            if ok:
                print(f"  [SENT] Text message")
                time.sleep(3)  # Anti-ban delay
                # Then send PDF
                if pdf_exists:
                    ok_pdf = send_message(msg["wa"], "Dossier esempio — BMW X3 2022", pdf)
                    print(f"  [{'SENT' if ok_pdf else 'FAIL'}] PDF dossier")
                time.sleep(5)  # Anti-ban delay between dealers
            else:
                print(f"  [FAIL] Message not sent")

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN complete. Run without --dry-run to send.")
    else:
        print("Day 7 outreach complete.")


if __name__ == "__main__":
    main()
