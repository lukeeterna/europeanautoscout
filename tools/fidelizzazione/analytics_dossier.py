"""
ARGOS Automotive — Analytics Dossier Trimestrale
Genera PDF "quanto hai guadagnato con ARGOS" da inviare via WA dopo 2-3 transazioni.

CLI:
  python3 analytics_dossier.py --dealer TIER0_FG_001 --output /tmp/
  python3 analytics_dossier.py --dealer TIER0_FG_001 --preview  # stampa dati senza PDF
"""

import argparse
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = os.environ.get(
    "ARGOS_DB_PATH",
    "/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite"
)

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


# ── Colori brand ARGOS ──────────────────────────────────────────────────────
ARGOS_BLU   = HexColor("#1A2744") if REPORTLAB_OK else None
ARGOS_ORO   = HexColor("#C9A84C") if REPORTLAB_OK else None
GRIGIO_LIGHT = HexColor("#F5F5F5") if REPORTLAB_OK else None


def get_dealer_stats(dealer_id: str) -> dict:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    row = cur.execute(
        "SELECT * FROM conversations WHERE dealer_id = ?", (dealer_id,)
    ).fetchone()
    if not row:
        con.close()
        raise ValueError(f"Dealer non trovato: {dealer_id}")

    # messaggi INBOUND (risposte) negli ultimi 90 giorni
    since = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
    msgs = cur.execute(
        "SELECT direction, body, timestamp_it FROM messages "
        "WHERE dealer_id = ? AND created_at >= ? ORDER BY created_at",
        (dealer_id, since)
    ).fetchall()

    con.close()

    return {
        "dealer_id":          dealer_id,
        "dealer_name":        row["dealer_name"],
        "city":               row["city"],
        "total_transactions": row["total_transactions"] or 0,
        "total_revenue":      row["total_revenue_dealer"] or 0.0,
        "is_active_partner":  bool(row["is_active_partner"]),
        "partner_since":      row["partner_since"],
        "messages_90d":       [dict(m) for m in msgs],
        "current_step":       row["current_step"],
    }


def generate_pdf(stats: dict, output_dir: str) -> str:
    if not REPORTLAB_OK:
        raise ImportError("reportlab non installato: pip install reportlab")

    os.makedirs(output_dir, exist_ok=True)
    nome_file = f"ARGOS_Analytics_{stats['dealer_id']}_{datetime.now().strftime('%Y%m')}.pdf"
    output_path = os.path.join(output_dir, nome_file)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=18*mm, rightMargin=18*mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ─────────────────────────────────────────────────────────────
    header_style = ParagraphStyle(
        "header", fontSize=22, textColor=ARGOS_BLU,
        fontName="Helvetica-Bold", spaceAfter=4
    )
    sub_style = ParagraphStyle(
        "sub", fontSize=11, textColor=ARGOS_ORO,
        fontName="Helvetica", spaceAfter=16
    )
    body_style = ParagraphStyle(
        "body", fontSize=10, textColor=colors.HexColor("#333333"),
        fontName="Helvetica", leading=15, spaceAfter=8
    )
    label_style = ParagraphStyle(
        "label", fontSize=9, textColor=colors.HexColor("#888888"),
        fontName="Helvetica", spaceAfter=2
    )

    trimestre = f"Q{((datetime.now().month-1)//3)+1} {datetime.now().year}"
    story.append(Paragraph("ARGOS Automotive", header_style))
    story.append(Paragraph(f"Report Partner — {trimestre}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ARGOS_ORO, spaceAfter=12))

    story.append(Paragraph(f"Gentile {stats['dealer_name']},", body_style))
    story.append(Paragraph(
        "di seguito il riepilogo della nostra collaborazione. "
        "Questi numeri sono il risultato concreto del nostro lavoro insieme.",
        body_style
    ))
    story.append(Spacer(1, 8*mm))

    # ── Tabella KPI ─────────────────────────────────────────────────────────
    n_tx   = stats["total_transactions"]
    rev    = stats["total_revenue"]
    avg    = (rev / n_tx) if n_tx > 0 else 0
    msgs90 = len([m for m in stats["messages_90d"] if m["direction"] == "INBOUND"])

    kpi_data = [
        ["", ""],
        ["Transazioni completate",       str(n_tx)],
        ["Margine netto stimato dealer",  f"€ {rev:,.0f}".replace(",", ".")],
        ["Margine medio per veicolo",     f"€ {avg:,.0f}".replace(",", ".")],
        ["Scambi negli ultimi 90 giorni", str(msgs90)],
        ["", ""],
    ]

    tbl = Table(kpi_data, colWidths=[110*mm, 50*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  GRIGIO_LIGHT),
        ("BACKGROUND",  (0, -1), (-1, -1), GRIGIO_LIGHT),
        ("BACKGROUND",  (0, 1), (-1, -2),  colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, GRIGIO_LIGHT]),
        ("FONTNAME",    (0, 1), (0, -2),   "Helvetica-Bold"),
        ("FONTNAME",    (1, 1), (1, -2),   "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1),  10),
        ("TEXTCOLOR",   (0, 1), (0, -2),   ARGOS_BLU),
        ("TEXTCOLOR",   (1, 1), (1, -2),   colors.HexColor("#111111")),
        ("ALIGN",       (1, 0), (1, -1),   "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1),  8),
        ("RIGHTPADDING",(0, 0), (-1, -1),  8),
        ("TOPPADDING",  (0, 0), (-1, -1),  5),
        ("BOTTOMPADDING",(0,0), (-1, -1),  5),
        ("LINEBELOW",   (0, 1), (-1, -2),  0.3, colors.HexColor("#DDDDDD")),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10*mm))

    # ── Messaggio ──────────────────────────────────────────────────────────
    if n_tx > 0:
        story.append(Paragraph(
            f"In questo periodo lei ha guadagnato <b>€ {rev:,.0f}</b> lavorando con noi, "
            f"su {n_tx} vettura{'e' if n_tx>1 else ''} importata{'e' if n_tx>1 else ''}. "
            "Zero anticipo, zero rischio di capitale.",
            body_style
        ))
    else:
        story.append(Paragraph(
            "La collaborazione è nelle fasi iniziali — il primo veicolo è quello che apre la strada.",
            body_style
        ))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        "Come partner prioritario, lei vede i nuovi veicoli 48 ore prima degli altri. "
        "Se ha richieste specifiche di clienti in attesa, me le mandi — le cerco io.",
        body_style
    ))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ARGOS_ORO, spaceAfter=8))

    firma_style = ParagraphStyle(
        "firma", fontSize=9, textColor=colors.HexColor("#555555"),
        fontName="Helvetica-Oblique", spaceAfter=4
    )
    story.append(Paragraph("Luca Ferretti — ARGOS Automotive", firma_style))
    story.append(Paragraph(
        f"Report generato il {datetime.now().strftime('%d/%m/%Y')} · Riservato per {stats['dealer_name']}",
        label_style
    ))

    doc.build(story)
    return output_path


def mark_analytics_sent(dealer_id: str):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "UPDATE conversations SET last_analytics_sent = ? WHERE dealer_id = ?",
        (datetime.utcnow().isoformat(), dealer_id)
    )
    con.commit()
    con.close()


def main():
    parser = argparse.ArgumentParser(description="ARGOS Analytics Dossier Generator")
    parser.add_argument("--dealer",  required=True, help="dealer_id")
    parser.add_argument("--output",  default="/tmp/argos_analytics/", help="output directory")
    parser.add_argument("--preview", action="store_true", help="stampa stats senza PDF")
    parser.add_argument("--mark-sent", action="store_true", help="aggiorna last_analytics_sent nel DB")
    args = parser.parse_args()

    stats = get_dealer_stats(args.dealer)

    if args.preview:
        print(f"\n=== Analytics Preview: {stats['dealer_name']} ({args.dealer}) ===")
        print(f"  Transazioni:      {stats['total_transactions']}")
        print(f"  Revenue dealer:   € {stats['total_revenue']:,.0f}")
        print(f"  Partner attivo:   {'SI' if stats['is_active_partner'] else 'NO'}")
        print(f"  Partner dal:      {stats['partner_since'] or 'N/A'}")
        print(f"  Step corrente:    {stats['current_step']}")
        print(f"  Messaggi 90gg:    {len(stats['messages_90d'])}")
        return

    path = generate_pdf(stats, args.output)
    print(f"PDF generato: {path}")

    if args.mark_sent:
        mark_analytics_sent(args.dealer)
        print(f"last_analytics_sent aggiornato per {args.dealer}")


if __name__ == "__main__":
    main()
