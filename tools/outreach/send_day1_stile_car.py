#!/usr/bin/env python3
"""
send_day1_stile_car.py — Day 1 Outreach: Stile Car (Domenico, NARCISO)
ARGOS Automotive | CoVe 2026

Script end-to-end per il primo contatto con Stile Car:
  1. Verifica dossier PDF esiste (> 10KB)
  2. Crafta messaggio Day 1 NARCISO per BMW X3 2022 (dati reali)
  3. Controlla WA daemon health, invia messaggio
  4. Aggiorna CRM: pipeline_status=CONTACTED, log interazione, proposta veicolo

Uso:
  python3 tools/outreach/send_day1_stile_car.py             # INVIA DAVVERO
  python3 tools/outreach/send_day1_stile_car.py --dry-run   # Stampa senza inviare

Regole messaggio rispettate (CLAUDE.md + s73_messaging_v2.md):
  - Max 5 righe contenuto
  - Domanda chiusa (si/no): "Le mando la scheda completa?"
  - Primo contenuto = veicolo REALE con numeri REALI
  - Nessun brand "ARGOS" nel messaggio (persona prima del brand)
  - Nessuna fee, nessun link, nessun attacco competitor
  - Linguaggio dealer: "auto" non "veicolo", EUR netti non percentuali
  - Trigger NARCISO: "2-3 concessionari della zona" = esclusivita'
  - Specificita': "Ho visto il suo stock" = ricerca su di HIM
"""

import sys
import os
import subprocess
import requests
import json
from pathlib import Path

# ── Configurazione ──────────────────────────────────────────────────────────

# Percorsi (relativi alla root del progetto)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DOSSIER_PATH = PROJECT_ROOT / "dossiers" / "ARGOS_BMW_X3_2022_Stile_Car.pdf"
CRM_SCRIPT = PROJECT_ROOT / "tools" / "dealer_crm.py"

# Target dealer
DEALER_ID = "stile_car_fg"
DEALER_PHONE = "393334254654"  # +39 333 4254654 (formato internazionale senza +)
TITOLARE_NAME = "Domenico"
ARCHETYPE = "NARCISO"

# WA daemon
WA_DAEMON_BASE = "http://192.168.1.2:9191"
WA_HEALTH_URL = f"{WA_DAEMON_BASE}/"
WA_SEND_URL = f"{WA_DAEMON_BASE}/send"  # http://192.168.1.2:9191/send

# Dati veicolo (reali, da Phase 3 — listing fresh_84aec3405b5d)
VEHICLE_MODEL = "BMW X3 xDrive20d 2022"
VEHICLE_KM = "50.000 km"
VEHICLE_PRICE_EU = 34140
VEHICLE_PRICE_IT_EST = 37369
VEHICLE_COUNTRY = "Germania"
VEHICLE_REGION_IT = "Puglia"

# ── Messaggio NARCISO Day 1 ──────────────────────────────────────────────────
# Template adattato da research/s73_messaging_v2.md (sezione NARCISO)
# Regole: max 5 righe contenuto, domanda chiusa, numeri reali, nessun brand in Day 1
# Trigger NARCISO: esclusivita' (2-3 concessionari) + specificita' (suo stock)

DAY1_MESSAGE = """\
Buongiorno, ho trovato una BMW X3 xDrive20d 2022, 50.000 km,
in Germania — €34.140. In Puglia gli stessi esemplari partono da €37-39.000.

Sto cercando 2-3 concessionari della zona per questo tipo di auto.
Ho visto il suo stock su AutoScout24 — tratta questa fascia.

Le mando la scheda completa?

Luca Ferretti"""


def step1_verify_dossier() -> bool:
    """Step 1: Verifica che il dossier PDF esiste e supera i 10KB."""
    print("\n── Step 1: Verifica dossier ─────────────────────────────────────")
    if not DOSSIER_PATH.exists():
        print(f"  ERRORE: dossier non trovato: {DOSSIER_PATH}")
        print("  Rigenerare con: python3 tools/scripts/pdf_generator_enterprise.py")
        return False

    size_bytes = DOSSIER_PATH.stat().st_size
    size_kb = size_bytes / 1024
    print(f"  DOSSIER OK: {DOSSIER_PATH.name}")
    print(f"  Dimensione: {size_kb:.1f} KB ({size_bytes:,} bytes)")

    if size_bytes < 10 * 1024:
        print(f"  ERRORE: dossier troppo piccolo ({size_kb:.1f} KB < 10 KB) — potrebbe essere corrotto")
        return False

    print(f"  Stato: OK (> 10KB)")
    return True


def step2_craft_message(dry_run: bool = False) -> str:
    """Step 2: Crafta e visualizza il messaggio Day 1 NARCISO."""
    print("\n── Step 2: Messaggio Day 1 NARCISO ─────────────────────────────")
    print(f"  Target: {TITOLARE_NAME} | Dealer: {DEALER_ID} | WA: +{DEALER_PHONE}")
    print(f"  Archetipo: {ARCHETYPE}")
    print(f"  Veicolo: {VEHICLE_MODEL} | {VEHICLE_KM} | €{VEHICLE_PRICE_EU:,}")
    print()
    print("  ┌─ Messaggio ─────────────────────────────────────────────────┐")
    for line in DAY1_MESSAGE.split('\n'):
        print(f"  │ {line}")
    print("  └──────────────────────────────────────────────────────────────┘")
    print()

    # Verifica regole CLAUDE.md
    lines = [l for l in DAY1_MESSAGE.strip().split('\n') if l.strip()]
    content_lines = lines[:-1]  # Escludi firma "Luca Ferretti"
    print("  Verifica regole CLAUDE.md:")
    print(f"  - Righe contenuto: {len(content_lines)} (max 5): {'OK' if len(content_lines) <= 5 else 'FAIL'}")
    print(f"  - Domanda chiusa: {'OK' if 'Le mando la scheda completa?' in DAY1_MESSAGE else 'FAIL'}")
    print(f"  - Prezzo EU reale: {'OK' if '34.140' in DAY1_MESSAGE else 'FAIL'}")
    print(f"  - Firma presente: {'OK' if 'Luca Ferretti' in DAY1_MESSAGE else 'FAIL'}")
    print(f"  - No brand ARGOS: {'OK' if 'ARGOS' not in DAY1_MESSAGE else 'WARN: ARGOS nel messaggio'}")
    print(f"  - No fee: {'OK' if '800' not in DAY1_MESSAGE and '900' not in DAY1_MESSAGE and '1.200' not in DAY1_MESSAGE else 'WARN'}")
    print(f"  - No link: {'OK' if 'http' not in DAY1_MESSAGE else 'WARN: link nel messaggio'}")
    print(f"  - Trigger NARCISO (esclusivita'): {'OK' if '2-3 concessionari' in DAY1_MESSAGE else 'FAIL'}")
    print(f"  - Specificita' (suo stock): {'OK' if 'stock' in DAY1_MESSAGE else 'FAIL'}")

    return DAY1_MESSAGE


def step3_send_wa(message: str, dry_run: bool = False) -> bool:
    """Step 3: Controlla health WA daemon e invia messaggio."""
    print("\n── Step 3: WA Daemon + Invio ────────────────────────────────────")

    # Health check
    print(f"  Controllo WA daemon: {WA_HEALTH_URL}")
    try:
        resp = requests.get(WA_HEALTH_URL, timeout=5)
        resp.raise_for_status()
        health = resp.json()
        wa_connected = health.get("wa_connected", False)
        daily_sent = health.get("daily_sent", "?")
        daily_limit = health.get("daily_limit", "?")
        print(f"  WA daemon: {'ONLINE' if wa_connected else 'OFFLINE'}")
        print(f"  WA connected: {wa_connected}")
        print(f"  Messaggi oggi: {daily_sent}/{daily_limit}")

        if not wa_connected:
            print()
            print("  ERRORE: WA daemon offline o WhatsApp non connesso.")
            print("  Soluzione: ssh gianlucadistasi@192.168.1.2 \"pm2 start wa-daemon\"")
            print("  Poi verifica la connessione WA Business e riprova.")
            if not dry_run:
                return False
    except requests.exceptions.ConnectionError:
        print(f"  ERRORE: Impossibile connettersi a {WA_HEALTH_URL}")
        print("  Daemon non raggiungibile — verificare:")
        print("    1. iMac acceso e connesso alla rete")
        print("    2. pm2 list sul iMac mostra wa-daemon 'online'")
        print("    3. curl http://192.168.1.2:9191/ risponde")
        if not dry_run:
            return False
        print("  DRY RUN: continuo nonostante daemon irraggiungibile")
    except Exception as e:
        print(f"  ERRORE health check: {e}")
        if not dry_run:
            return False
        print("  DRY RUN: continuo nonostante errore")

    if dry_run:
        print()
        print("  ─── DRY RUN ─── NON INVIO IL MESSAGGIO ────────────────────")
        print(f"  Avrei inviato a: +{DEALER_PHONE}")
        print(f"  dealer_id: {DEALER_ID}")
        payload = {
            "phone": DEALER_PHONE,
            "message": message,
            "dealer_id": DEALER_ID
        }
        print(f"  Payload: {json.dumps(payload, ensure_ascii=False, indent=4)}")
        print("  ─── DRY RUN COMPLETATO — esegui senza --dry-run per inviare ─")
        return True

    # Invio reale
    print()
    print(f"  Invio messaggio a +{DEALER_PHONE} ({TITOLARE_NAME} @ {DEALER_ID})...")
    payload = {
        "phone": DEALER_PHONE,
        "message": message,
        "dealer_id": DEALER_ID
    }
    try:
        resp = requests.post(WA_SEND_URL, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        status = result.get("status", "unknown")
        msg_id = result.get("msg_id", "?")
        daily_sent = result.get("daily_sent", "?")

        if status == "sent":
            print(f"  INVIATO: status={status} | msg_id={msg_id} | daily_sent={daily_sent}")
            return True
        else:
            print(f"  ERRORE: status={status} — risposta completa: {result}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ERRORE invio: {e}")
        return False


def step4_update_crm(dry_run: bool = False) -> bool:
    """Step 4: Aggiorna CRM dealer con stato CONTACTED, log e proposta veicolo."""
    print("\n── Step 4: Aggiornamento CRM ────────────────────────────────────")

    if dry_run:
        print("  DRY RUN: mostrare comandi CRM che verrebbero eseguiti:")
        print(f"    python3 {CRM_SCRIPT} update {DEALER_ID} pipeline_status CONTACTED")
        print(f"    python3 {CRM_SCRIPT} log {DEALER_ID} WA OUT \"Day 1: {VEHICLE_MODEL} {VEHICLE_KM} EUR{VEHICLE_PRICE_EU} — NARCISO template\"")
        print(f"    python3 {CRM_SCRIPT} propose {DEALER_ID} \"{VEHICLE_MODEL}\" {VEHICLE_PRICE_EU} {VEHICLE_PRICE_IT_EST}")
        return True

    python_exe = sys.executable
    crm = str(CRM_SCRIPT)

    def run_crm(args: list, description: str) -> bool:
        cmd = [python_exe, crm] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
            if result.returncode == 0:
                print(f"  OK: {description}")
                if result.stdout.strip():
                    for line in result.stdout.strip().split('\n')[:3]:
                        print(f"     {line}")
                return True
            else:
                print(f"  ERRORE {description}: {result.stderr.strip() or result.stdout.strip()}")
                return False
        except Exception as e:
            print(f"  ERRORE {description}: {e}")
            return False

    # 1. Aggiorna pipeline_status
    run_crm(
        ["update", DEALER_ID, "pipeline_status", "CONTACTED"],
        "pipeline_status → CONTACTED"
    )

    # 2. Log interazione Day 1
    log_content = f"Day 1: {VEHICLE_MODEL} {VEHICLE_KM} EUR{VEHICLE_PRICE_EU} — NARCISO template"
    run_crm(
        ["log", DEALER_ID, "WA", "OUT", log_content],
        "log interazione Day 1"
    )

    # 3. Registra proposta veicolo
    run_crm(
        ["propose", DEALER_ID, f"{VEHICLE_MODEL}", str(VEHICLE_PRICE_EU), str(VEHICLE_PRICE_IT_EST)],
        f"proposta veicolo: {VEHICLE_MODEL}"
    )

    # 4. Mostra stato finale CRM
    print()
    print("  Stato finale CRM:")
    cmd = [python_exe, crm, "show", DEALER_ID]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(f"     {line}")
    except Exception as e:
        print(f"  (impossibile mostrare stato: {e})")

    return True


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 65)
    if dry_run:
        print("  ARGOS AUTOMOTIVE — Day 1 Outreach: Stile Car [DRY RUN]")
    else:
        print("  ARGOS AUTOMOTIVE — Day 1 Outreach: Stile Car [INVIO REALE]")
    print("=" * 65)
    print(f"  Target:   {TITOLARE_NAME} @ {DEALER_ID}")
    print(f"  WA:       +{DEALER_PHONE}")
    print(f"  Veicolo:  {VEHICLE_MODEL}")
    print(f"  Prezzo:   €{VEHICLE_PRICE_EU:,} EU | ~€{VEHICLE_PRICE_IT_EST:,} IT")
    print(f"  Dossier:  {DOSSIER_PATH.name}")
    print()

    # Step 1: Verifica dossier
    if not step1_verify_dossier():
        print("\nABORTED: dossier non valido")
        sys.exit(1)

    # Step 2: Crafta messaggio
    message = step2_craft_message(dry_run=dry_run)

    # Step 3: Controlla daemon e invia
    if not step3_send_wa(message, dry_run=dry_run):
        print("\nABORTED: invio WA fallito")
        sys.exit(1)

    # Step 4: Aggiorna CRM
    step4_update_crm(dry_run=dry_run)

    # Riepilogo finale
    print()
    print("=" * 65)
    if dry_run:
        print("  DRY RUN COMPLETATO")
        print()
        print("  Per inviare davvero:")
        print("    1. Verificare WA daemon: curl http://192.168.1.2:9191/")
        print("    2. Lanciare: python3 tools/outreach/send_day1_stile_car.py")
        print()
        print("  PDF dossier pronto (da inviare manualmente quando risponde):")
        print(f"    {DOSSIER_PATH}")
    else:
        print("  OUTREACH COMPLETATO")
        print()
        print("  Prossimi step:")
        print("  - Attendi risposta Domenico (check WA Business 328-1536308)")
        print("  - Se risponde 'si': invia PDF dossier manualmente")
        print("  - Day 3: seconda foto + BMW diversa (da sequencer s73)")
        print("  - CRM: aggiorna pipeline_status a REPLIED quando risponde")
    print("=" * 65)


if __name__ == "__main__":
    main()
