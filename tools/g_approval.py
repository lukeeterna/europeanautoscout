"""g_approval.py — C-GATE-FONTE-001: conferma pagamento manuale Luke + rilascio PDF gated.

CLI atomica e idempotente per confermare il pagamento di un deal e generare
il PDF con fonte rivelata (listing_url, seller, phone).

Usage:
    python3 tools/g_approval.py --deal-id DEAL-XXX --deals-db /path/deals.sqlite
    python3 tools/g_approval.py --deal-id DEAL-XXX --deals-db /path/deals.sqlite --dry-run
    python3 tools/g_approval.py --deal-id DEAL-XXX --deals-db /path/deals.sqlite --output-dir /tmp/miei_pdf

Idempotenza: se il deal è già payment_confirmed e il PDF esiste, restituisce il path
esistente senza toccare il DB. Se il PDF non esiste, lo rigenera.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# Aggiunge repo root al path per import relativi
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
_COMM_BROKER_DIR = os.path.join(_REPO_ROOT, "comm-broker")

# comm-broker ha trattino → non importabile come package Python standard.
# Aggiunge la directory direttamente al path per import diretto del modulo.
if _COMM_BROKER_DIR not in sys.path:
    sys.path.insert(0, _COMM_BROKER_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import deal_state_machine as _dsm
DealStateMachine = _dsm.DealStateMachine
Deal = _dsm.Deal

from tools.scripts.pdf_gated_source import release_source_dossier, GatingError


def _load_deal_row(deals_db: Path, deal_id: str) -> dict | None:
    """Legge il record del deal dal DB. Ritorna None se non esiste."""
    conn = sqlite3.connect(deals_db)
    try:
        cur = conn.execute(
            "SELECT deal_id, current_state, dealer_alias, seller_alias, "
            "vehicle_desc, fee_eur, metadata_json, paid_at "
            "FROM deals WHERE deal_id = ?",
            (deal_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = ["deal_id", "current_state", "dealer_alias", "seller_alias",
                "vehicle_desc", "fee_eur", "metadata_json", "paid_at"]
        return dict(zip(cols, row))
    finally:
        conn.close()


def _find_existing_pdf(output_dir: Path, deal_id: str) -> str | None:
    """Cerca un PDF gated già generato per questo deal in output_dir."""
    if not output_dir.exists():
        return None
    pattern = f"GATED_{deal_id}_*.pdf"
    matches = list(output_dir.glob(pattern))
    if matches:
        return str(matches[0].resolve())
    return None


def _update_paid_metadata(deals_db: Path, deal_id: str) -> None:
    """Scrive paid_at e paid_by='luke_manual' in metadata_json e colonna paid_at."""
    now = int(time.time())
    conn = sqlite3.connect(deals_db)
    try:
        cur = conn.execute(
            "SELECT metadata_json FROM deals WHERE deal_id = ?", (deal_id,)
        )
        row = cur.fetchone()
        metadata = json.loads(row[0] or "{}") if row else {}
        metadata["paid_at"] = now
        metadata["paid_by"] = "luke_manual"
        conn.execute(
            "UPDATE deals SET metadata_json = ?, paid_at = ?, updated_ts = ? "
            "WHERE deal_id = ?",
            (json.dumps(metadata), now, now, deal_id),
        )
        conn.commit()
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="C-GATE-FONTE-001: conferma pagamento manuale e genera PDF con fonte."
    )
    parser.add_argument("--deal-id", required=True, help="ID univoco del deal")
    parser.add_argument("--deals-db", required=True, help="Path al DB SQLite deals")
    parser.add_argument(
        "--output-dir",
        default="/tmp/argos_gated",
        help="Directory output PDF (default: /tmp/argos_gated)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Stampa le azioni previste senza toccare il DB",
    )
    args = parser.parse_args()

    deal_id = args.deal_id
    deals_db = Path(args.deals_db).resolve()
    output_dir = Path(args.output_dir).resolve()

    # Verifica DB esiste
    if not deals_db.exists():
        print(f"ERRORE: DB non trovato: {deals_db}", file=sys.stderr)
        return 1

    # Legge stato corrente
    row = _load_deal_row(deals_db, deal_id)
    if row is None:
        print(f"ERRORE: deal '{deal_id}' non trovato in {deals_db}", file=sys.stderr)
        return 1

    current_state = row["current_state"]

    # ── CASO A: già payment_confirmed (idempotenza) ──────────────────────────
    if current_state == "payment_confirmed":
        existing_pdf = _find_existing_pdf(output_dir, deal_id)
        if existing_pdf:
            print(f"[IDEMPOTENTE] Deal già payment_confirmed, PDF esistente:")
            print(existing_pdf)
            return 0
        # PDF mancante → rigenera
        if args.dry_run:
            print(f"[DRY-RUN] Deal già payment_confirmed.")
            print(f"[DRY-RUN] Azione 1: SKIP — transizione già eseguita.")
            print(f"[DRY-RUN] Azione 2: SKIP — paid_at già impostato.")
            print(f"[DRY-RUN] Azione 3: release_source_dossier('{deal_id}', '{deals_db}', '{output_dir}')")
            return 0
        print(f"[IDEMPOTENTE] Deal già payment_confirmed, PDF assente — rigenero...")
        try:
            pdf_path = release_source_dossier(deal_id, deals_db, output_dir)
            print(f"PDF rigenerato: {pdf_path}")
            return 0
        except Exception as exc:
            print(f"ERRORE rigenerazione PDF: {exc}", file=sys.stderr)
            print("Rilancia il comando per ritentare la generazione del PDF.", file=sys.stderr)
            return 2

    # ── CASO B: stato incompatibile (non payment_pending) ────────────────────
    if current_state != "payment_pending":
        print(
            f"ERRORE: deal '{deal_id}' è in stato '{current_state}'. "
            f"Atteso 'payment_pending' per confermare il pagamento.",
            file=sys.stderr,
        )
        return 1

    # ── CASO C: stato payment_pending → esegui sequenza atomica ─────────────
    if args.dry_run:
        print(f"[DRY-RUN] Deal '{deal_id}' in stato '{current_state}'. Azioni previste:")
        print(f"[DRY-RUN] Azione 1: DealStateMachine.confirm_payment() → payment_confirmed")
        print(f"[DRY-RUN] Azione 2: UPDATE deals SET metadata_json (paid_at=<ts>, paid_by='luke_manual'), paid_at=<ts>")
        print(f"[DRY-RUN] Azione 3: release_source_dossier('{deal_id}', '{deals_db}', '{output_dir}')")
        return 0

    # Azione 1: transizione confirm_payment via DealStateMachine
    deal_obj = Deal(
        deal_id=row["deal_id"],
        dealer_alias=row["dealer_alias"],
        seller_alias=row["seller_alias"],
        vehicle_desc=row["vehicle_desc"] or "",
        fee_eur=row["fee_eur"] or 1000,
        metadata=json.loads(row["metadata_json"] or "{}"),
    )
    try:
        fsm = DealStateMachine(deal_obj, db_path=deals_db)
        fsm.confirm_payment()
        print(f"[OK] Transizione confirm_payment eseguita → payment_confirmed")
    except Exception as exc:
        print(f"ERRORE transizione confirm_payment: {exc}", file=sys.stderr)
        return 1

    # Azione 2: aggiorna metadata paid_at + paid_by
    try:
        _update_paid_metadata(deals_db, deal_id)
        print(f"[OK] Metadata aggiornata: paid_at={int(time.time())}, paid_by='luke_manual'")
    except Exception as exc:
        print(f"ERRORE aggiornamento metadata: {exc}", file=sys.stderr)
        # Non blocca: la transizione è già confermata

    # Azione 3: genera PDF con fonte sbloccata
    try:
        pdf_path = release_source_dossier(deal_id, deals_db, output_dir)
        print(f"[OK] PDF gated generato:")
        print(pdf_path)
        return 0
    except GatingError as exc:
        # Non dovrebbe accadere dopo confirm_payment — bug strutturale
        print(f"ERRORE INATTESO GatingError (bug): {exc}", file=sys.stderr)
        print("Pagamento confermato nel DB. Rilancia il comando per rigenerare il PDF.", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERRORE generazione PDF: {exc}", file=sys.stderr)
        print("Pagamento confermato nel DB. Rilancia il comando per rigenerare il PDF.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
