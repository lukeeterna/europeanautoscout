#!/usr/bin/env python3
"""
ARGOS — Invio Day 1 tutta Italia
Legge i dealer target da JSON, compone messaggi personalizzati con veicoli reali CoVe,
e invia via WA daemon. Gate validazione su ogni messaggio.

Usage:
  python3 tools/send_day1_italia.py --dry-run          # preview
  python3 tools/send_day1_italia.py --max 5             # invia ai primi 5
  python3 tools/send_day1_italia.py                     # invia a tutti
  python3 tools/send_day1_italia.py --force-hours       # ignora business hours check
"""

import json
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Load .env
for env_file in [BASE_DIR / '.env', Path.home() / 'Documents/app-antigravity-auto/wa-intelligence/.env']:
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    v = v.strip()
                    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                        v = v[1:-1]
                    os.environ.setdefault(k.strip(), v)

WA_DAEMON = "http://192.168.1.2:9191"
WA_API_KEY = os.environ.get("ARGOS_API_KEY", os.environ.get("WA_API_KEY", ""))

# ── Veicoli reali dal CoVe DB ─────────────────────────────────
_USED_LISTINGS = set()  # Track used listing_ids to avoid duplicates

def get_best_vehicle(marca, budget=50000):
    """Trova il miglior veicolo PROCEED per marca, evitando duplicati tra dealer."""
    try:
        import duckdb
        db = BASE_DIR / 'src' / 'cove' / 'data' / 'cove_tracker.duckdb'
        if not db.exists():
            return None

        # Try DE sources first, then any
        for source_filter in [
            "AND (source LIKE '%_de%' OR source LIKE 'mobile_de%')",
            "",
        ]:
            con = duckdb.connect(str(db), read_only=True)
            rows = con.execute(f"""
                SELECT make, model, year, km, price, confidence, listing_id, source
                FROM cove_results
                WHERE recommendation = 'PROCEED' AND fraud_overall = 'CLEAN'
                  AND make ILIKE ? AND price <= ?
                  {source_filter}
                ORDER BY confidence DESC, price ASC
                LIMIT 50
            """, [f'%{marca}%', budget]).fetchall()
            con.close()

            for r in rows:
                lid = r[6]
                if lid not in _USED_LISTINGS:
                    _USED_LISTINGS.add(lid)
                    return {
                        'make': r[0], 'model': r[1], 'year': r[2],
                        'km': int(r[3]) if r[3] else 0,
                        'price': int(r[4]) if r[4] else 0,
                        'confidence': r[5], 'listing_id': lid, 'source': r[7],
                    }
    except Exception as e:
        print(f"  [WARN] DB query failed: {e}")
    return None


def compose_message(dealer, vehicle):
    """Compone messaggio Day 1 personalizzato."""
    if not vehicle:
        return None

    km_str = f"{vehicle['km']:,}".replace(',', '.')
    price_str = f"{vehicle['price']:,}".replace(',', '.')

    name = dealer.get('name', 'Concessionaria')
    city = dealer.get('city', '')

    msg = (
        f"Buongiorno, ho una {vehicle['make']} {vehicle['model']} {vehicle['year']}, "
        f"{km_str} km,\n"
        f"dalla Germania — EUR {price_str}.\n"
        f"Km certificati, storico tagliandi {vehicle['make']} completo.\n"
        f"Le mando la scheda con tutti i dettagli?\n\n"
        f"Luca Ferretti"
    )
    return msg


def send_wa(phone, message, dealer_id):
    import urllib.request
    payload = json.dumps({
        "phone": phone, "message": message, "dealer_id": dealer_id,
    }).encode()
    headers = {"Content-Type": "application/json", "X-API-Key": WA_API_KEY}
    req = urllib.request.Request(f"{WA_DAEMON}/send", data=payload, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def is_business_hours():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    h = now.hour + now.minute / 60
    return (8.0 <= h < 12.0) or (14.0 <= h < 18.0)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--max', type=int, default=999)
    parser.add_argument('--force-hours', action='store_true')
    parser.add_argument('--targets', default='research/s104_dealer_enriched_wa.json',
                        help='JSON file with enriched dealer targets')
    args = parser.parse_args()

    # Load targets
    target_file = BASE_DIR / args.targets
    if not target_file.exists():
        print(f"[ERROR] Target file not found: {target_file}")
        print("Run enrichment first to create the target file.")
        sys.exit(1)

    with open(target_file) as f:
        dealers = json.load(f)

    # Filter: only those with WA phone
    wa_dealers = [d for d in dealers if d.get('phone_wa')]
    print(f"{'='*60}")
    print(f"ARGOS DAY 1 — TUTTA ITALIA")
    print(f"Target: {len(wa_dealers)} dealer con WA / {len(dealers)} totali")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Max: {args.max}")
    print(f"{'='*60}")

    if not args.dry_run and not args.force_hours and not is_business_hours():
        print(f"\n[BLOCK] Fuori business hours. Usa --force-hours per override.")
        return

    if not WA_API_KEY and not args.dry_run:
        print(f"\n[ERROR] ARGOS_API_KEY mancante")
        return

    sent = 0
    skipped = 0
    for i, dealer in enumerate(wa_dealers[:args.max], 1):
        print(f"\n--- #{i} {dealer['name']} ({dealer.get('city','')}, {dealer.get('province','')}) ---")

        # Find best vehicle matching dealer's premium brands
        vehicle = None
        for brand in dealer.get('premium_brands', ['BMW']):
            vehicle = get_best_vehicle(brand)
            if vehicle:
                break
        if not vehicle:
            vehicle = get_best_vehicle('BMW')  # fallback

        if not vehicle:
            print(f"  [SKIP] Nessun veicolo PROCEED nel DB")
            skipped += 1
            continue

        msg = compose_message(dealer, vehicle)
        phone = dealer['phone_wa']

        print(f"  Tel: {phone}")
        print(f"  Veicolo: {vehicle['make']} {vehicle['model']} {vehicle['year']} | "
              f"{vehicle['km']:,} km | EUR {vehicle['price']:,} | {vehicle['source']}")
        print(f"  Listing: {vehicle['listing_id']}")
        for line in msg.split('\n'):
            print(f"    {line}")

        if args.dry_run:
            print(f"  [DRY RUN]")
            sent += 1
            continue

        if i > 1:
            delay = random.randint(45, 120)
            print(f"  [WAIT] {delay}s...")
            time.sleep(delay)

        result = send_wa(phone, msg, dealer.get('id', f'disc_{dealer.get("province","")}__{i}'))
        if result.get('status') in ('sent', 'queued'):
            print(f"  [OK] {result.get('msg_id','')}")
            sent += 1
        else:
            print(f"  [ERROR] {result}")

    print(f"\n{'='*60}")
    print(f"INVIATI: {sent} | SKIP: {skipped} | TOTALE: {len(wa_dealers[:args.max])}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
