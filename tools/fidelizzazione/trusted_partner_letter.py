"""
ARGOS Automotive — Lettera "Trusted Partner" (stampa fisica)
Da inviare dopo la prima transazione completata.

CLI:
  python3 trusted_partner_letter.py --dealer TIER0_FG_001 --output /tmp/
  python3 trusted_partner_letter.py --dealer TIER0_FG_001 --mark-sent
"""

import argparse
import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get(
    "ARGOS_DB_PATH",
    "/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite"
)

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.lib import colors
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

ARGOS_BLU = HexColor("#1A2744") if REPORTLAB_OK else None
ARGOS_ORO = HexColor("#C9A84C") if REPORTLAB_OK else None


def get_dealer(dealer_id: str) -> dict:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT dealer_name, city, total_transactions, total_revenue_dealer "
        "FROM conversations WHERE dealer_id = ?", (dealer_id,)
    ).fetchone()
    con.close()
    if not row:
        raise ValueError(f"Dealer non trovato: {dealer_id}")
    return dict(row)


def generate_letter(dealer_id: str, output_dir: str) -> str:
    if not REPORTLAB_OK:
        raise ImportError("pip install reportlab")

    dealer = get_dealer(dealer_id)
    os.makedirs(output_dir, exist_ok=True)
    nome_file = f"ARGOS_TrustedPartner_{dealer_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    path = os.path.join(output_dir, nome_file)

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=28*mm, bottomMargin=28*mm,
        leftMargin=22*mm, rightMargin=22*mm,
    )

    h1 = ParagraphStyle("h1", fontSize=18, fontName="Helvetica-Bold",
                         textColor=ARGOS_BLU, spaceAfter=4)
    gold = ParagraphStyle("gold", fontSize=11, fontName="Helvetica-Bold",
                           textColor=ARGOS_ORO, spaceAfter=14)
    body = ParagraphStyle("body", fontSize=11, fontName="Helvetica",
                           textColor=colors.HexColor("#333333"), leading=17, spaceAfter=10)
    firma = ParagraphStyle("firma", fontSize=10, fontName="Helvetica-Oblique",
                            textColor=colors.HexColor("#555555"), spaceAfter=4)
    small = ParagraphStyle("small", fontSize=8, fontName="Helvetica",
                            textColor=colors.HexColor("#999999"))

    data_it = datetime.now().strftime("%d %B %Y")
    n_tx = dealer["total_transactions"] or 0
    rev  = dealer["total_revenue_dealer"] or 0.0

    story = [
        Paragraph("ARGOS Automotive", h1),
        Paragraph("Certificato di Partner di Fiducia", gold),
        HRFlowable(width="100%", thickness=1, color=ARGOS_ORO, spaceAfter=14),

        Paragraph(f"Gentile {dealer['dealer_name']},", body),
        Paragraph(
            "con questa lettera desidero ringraziarla formalmente per la fiducia "
            "accordata ad ARGOS Automotive.",
            body
        ),
        Paragraph(
            f"Lei è il {'primo' if n_tx <= 1 else str(n_tx) + 'esimo'} dealer "
            f"a completare una transazione con noi in {dealer['city']}. "
            "Questo per noi non è un dato amministrativo — è la prova che il modello funziona, "
            "e lei ne è protagonista.",
            body
        ),
    ]

    if rev > 0:
        story.append(Paragraph(
            f"Grazie alla nostra collaborazione, ha già realizzato un margine netto stimato "
            f"di <b>€ {rev:,.0f}</b>. Zero anticipo, zero rischio.",
            body
        ))

    story += [
        Spacer(1, 6*mm),
        Paragraph(
            "Come Trusted Partner, le riconosco:",
            body
        ),
        Paragraph("· <b>Accesso prioritario</b> ai veicoli — li vede 48h prima di chiunque altro", body),
        Paragraph("· <b>Report trimestrale</b> personalizzato con i numeri della nostra collaborazione", body),
        Paragraph("· <b>Canale diretto</b> — mi contatti direttamente per veicoli su richiesta dei suoi clienti", body),

        Spacer(1, 10*mm),
        Paragraph("Con stima,", body),
        Paragraph("Luca Ferretti", firma),
        Paragraph("ARGOS Automotive", firma),
        Spacer(1, 6*mm),
        HRFlowable(width="100%", thickness=0.5, color=ARGOS_ORO, spaceAfter=6),
        Paragraph(
            f"Lettera emessa il {data_it} · Riservata a {dealer['dealer_name']} — {dealer['city']}",
            small
        ),
    ]

    doc.build(story)
    return path


def mark_sent(dealer_id: str):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "UPDATE conversations SET trusted_partner_sent = 1, is_active_partner = 1, "
        "partner_since = ? WHERE dealer_id = ?",
        (datetime.utcnow().isoformat(), dealer_id)
    )
    con.commit()
    con.close()


def main():
    parser = argparse.ArgumentParser(description="ARGOS Trusted Partner Letter")
    parser.add_argument("--dealer",    required=True)
    parser.add_argument("--output",    default="/tmp/argos_letters/")
    parser.add_argument("--mark-sent", action="store_true",
                        help="setta trusted_partner_sent=1 e is_active_partner=1")
    args = parser.parse_args()

    path = generate_letter(args.dealer, args.output)
    print(f"Lettera generata: {path}")

    if args.mark_sent:
        mark_sent(args.dealer)
        print(f"DB aggiornato: trusted_partner_sent=1, is_active_partner=1 per {args.dealer}")


if __name__ == "__main__":
    main()
