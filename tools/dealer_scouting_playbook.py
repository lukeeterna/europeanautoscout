#!/usr/bin/env python3
"""
ARGOS DEALER SCOUTING & SCORING ENGINE
=======================================
Playbook operativo automatizzato per trovare, qualificare e approcciare dealer.

Questo script E' il sistema. Quando Claude non c'e', questo gira.

Usage:
    python3 tools/dealer_scouting_playbook.py --region campania
    python3 tools/dealer_scouting_playbook.py --score-dealer "Stile Car" --stock 36 --years 10 --premium-pct 40 --reviews 62 --rating 4.9 --has-import --age-under-45
    python3 tools/dealer_scouting_playbook.py --generate-message PERFORMANTE --dealer-name "Domenico" --vehicle "BMW X5 30d 2022" --price-eu 38500 --price-it 47000
    python3 tools/dealer_scouting_playbook.py --sequence --dealer-name "Stile Car" --archetype PERFORMANTE --day 1

Author: ARGOS Automotive CoVe 2026
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════════════
# SEZIONE 1: CRITERI QUALIFICAZIONE DEALER
# ══════════════════════════════════════════════════════════════

IDEAL_PROFILE = {
    "stock_min": 20,
    "stock_max": 40,
    "stock_extended_max": 60,  # accettabile se altri criteri forti
    "years_min": 3,
    "years_max": 8,
    "years_extended_max": 15,  # accettabile se segnale import EU
    "premium_pct_min": 15,  # % stock che e' BMW/Merc/Audi/Porsche
    "reviews_min": 25,
    "reviews_max": 100,
    "reviews_extended_max": 300,
    "rating_min": 3.8,
    "rating_max": 4.4,  # sopra 4.4 = gia' troppo forte
    "rating_extended_max": 5.0,  # accettabile con altri segnali
    "titolare_age_max": 48,
}

# Pesi scoring (totale = 100%)
SCORING_WEIGHTS = {
    "stock_fit": 0.20,        # 20-40 auto
    "years_fit": 0.15,        # 3-8 anni
    "premium_pct": 0.20,      # quota premium >15%
    "social_active": 0.10,    # Instagram/Facebook attivo
    "reviews_fit": 0.10,      # 25-100 recensioni Google
    "import_signal": 0.15,    # segnale import EU presente
    "young_owner": 0.10,      # titolare under-45
}


# ══════════════════════════════════════════════════════════════
# SEZIONE 2: ARCHETIPI DEALER
# ══════════════════════════════════════════════════════════════

ARCHETYPES = {
    "NARCISO": {
        "description": "Vuole sentirsi SCELTO, esclusivo, unico",
        "trigger": "Veicolo raro, 'sto selezionando 2-3 dealer'",
        "anti_trigger": "Approccio di massa, tono generico",
        "tone": "Esclusivo, da peer, 'ho scelto lei perche'...'",
        "fee_timing": "MAI al primo contatto",
    },
    "BARONE": {
        "description": "Vuole RISPETTO per storia e reputazione",
        "trigger": "Riconoscere reputazione, referral collega zona",
        "anti_trigger": "Chi non conosce mercato locale",
        "tone": "Rispettoso, deferente, professionale",
        "fee_timing": "Solo quando chiede",
    },
    "RAGIONIERE": {
        "description": "Vuole NUMERI chiari, margine netto in EUR",
        "trigger": "Tabella completa: DE €X → IT €Y → fee €Z → netto €W",
        "anti_trigger": "Vaghezze, promesse senza cifre",
        "tone": "Diretto, numerico, trasparente",
        "fee_timing": "SI' al primo contatto (il Ragioniere VUOLE sapere)",
    },
    "TECNICO": {
        "description": "Vuole CAPIRE TUTTO, step by step",
        "trigger": "PDF dossier completo, documentazione, processo spiegato",
        "anti_trigger": "Promesse non verificabili",
        "tone": "Tecnico, trasparente, paziente",
        "fee_timing": "Dopo aver spiegato il processo",
    },
    "PERFORMANTE": {
        "description": "Vuole VELOCITA' e risultati immediati",
        "trigger": "Scarsita', 'va via in 48h', azione rapida",
        "anti_trigger": "Processi lenti, lunghe spiegazioni",
        "tone": "Diretto, veloce, action-oriented",
        "fee_timing": "Breve, integrata nel numero: 'fee €900, netto per lei €4.500'",
    },
    "RELAZIONALE": {
        "description": "Vuole costruire un RAPPORTO prima di comprare",
        "trigger": "Tono umano, riconoscere la sua storia, proporre telefonata",
        "anti_trigger": "Messaggi copia-incolla, transazionalita'",
        "tone": "Personale, caldo, interessato alla SUA storia",
        "fee_timing": "Durante la telefonata, non via WA",
    },
}


# ══════════════════════════════════════════════════════════════
# SEZIONE 3: TEMPLATE MESSAGGI PER ARCHETIPO E GIORNO
# ══════════════════════════════════════════════════════════════

MESSAGE_TEMPLATES = {
    # ── DAY 1 ──────────────────────────────────────────────
    "NARCISO_DAY1": """Buongiorno {dealer_name}, ho trovato un {vehicle}
a {price_eu_str} su portale {country}. In Italia lo stesso esemplare
parte da {price_it_str}.

Sto cercando 2-3 concessionari della zona per questo tipo di auto.
Ho visto il suo stock — tratta questa fascia.

Le mando la scheda completa?

Luca Ferretti""",

    "BARONE_DAY1": """Buongiorno, ho un {vehicle},
certificato — {price_eu_str} in {country}.

Su AutoScout24 Italia la stessa auto sta a {price_it_str}.
Km verificati prima di proporla.

Ha interesse per questa fascia?

Luca Ferretti""",

    "RAGIONIERE_DAY1": """Buongiorno, ho trovato un {vehicle}
a {price_eu_str} in {country}.

In Italia la stessa auto sta a {price_it_str}.
Trasporto: ~€750. Fee mia: €900.
Margine netto per lei: circa {margin_str}.

Le interessa?

Luca Ferretti""",

    "TECNICO_DAY1": """Buongiorno, ho trovato un {vehicle},
{specs} — {price_eu_str} in {country}.

Allestimento completo e VIN check gia' fatto.
Posso mandarle la scheda tecnica con tutti i dettagli?

Luca Ferretti""",

    "PERFORMANTE_DAY1": """Buongiorno {dealer_name}, ho un {vehicle}
a {price_eu_str} — in Italia va via a {price_it_str}.

Margine netto {margin_str} dopo fee e trasporto.
Disponibile adesso. Le mando i dettagli?

Luca Ferretti""",

    "RELAZIONALE_DAY1": """Buongiorno, sono Luca — lavoro con concessionari
della zona per trovare auto dall'Europa.

Ho visto le sue recensioni — {reviews_note}.
Posso chiamarla 2 minuti per presentarmi?

Luca""",

    # ── DAY 3 (follow-up se silenzio) ──────────────────────
    "NARCISO_DAY3": """[FOTO HD veicolo con watermark ARGOS]

Questa e' appena uscita — {vehicle_2}, config rara.
{price_eu_str} {country}.

In Italia non la trovo sotto {price_it_str}.

Se tratta questa fascia, e' roba da pochi.""",

    "BARONE_DAY3": """[FOTO HD veicolo]

{vehicle_2}, {km} km.
{price_eu_str} {country} — certificata e disponibile.

Km verificati, libretto tagliandi completo.
Se ha interesse le mando tutto il dettaglio.""",

    "RAGIONIERE_DAY3": """Buongiorno, un altro esemplare appena trovato:

{vehicle_2} — {price_eu_str} {country}
Italia: {price_it_str}
Trasporto + fee: €1.650
Netto per lei: ~{margin_str}

Due opzioni su due marchi diversi se le interessa confrontare.""",

    "PERFORMANTE_DAY3": """[FOTO HD veicolo]

{vehicle_2} — {price_eu_str}.
Margine {margin_str} netto. Disponibile ora.

Quello di prima e' andato. Questo e' appena uscito.""",

    # ── DAY 7 (recovery) ──────────────────────────────────
    "NARCISO_DAY7": """Buongiorno — il {vehicle} che le avevo segnalato
e' stato preso da un dealer di {nearby_city}.

Ne ho trovato un altro simile, stessa fascia.
Se ha interesse me lo dica prima che vada anche questo.""",

    "BARONE_DAY7": """Buongiorno — se non e' il momento giusto,
nessun problema. Sono qui quando le serve.

Se in futuro cerca un modello specifico dall'estero,
mi scriva pure — le faccio una ricerca senza impegno.""",

    "RAGIONIERE_DAY7": """Buongiorno — so che il tempo e' poco.

Le lascio un dato: su 10 auto premium importate EU,
il margine extra medio e' €3.000-4.500 a pezzo
rispetto all'acquisto in Italia.

Se vuole i numeri precisi su un modello specifico, mi scriva.""",

    "PERFORMANTE_DAY7": """Il {vehicle} e' andato.

Ne trovo uno simile in 48h se mi dice il modello
e la fascia di prezzo che le interessa.

Zero impegno — paga solo se le piace.""",

    # ── DAY 10 (vocale) ──────────────────────────────────
    "VOCALE_SCRIPT": """Buongiorno, sono Luca Ferretti. Le ho scritto
la settimana scorsa per un {vehicle} che avevo trovato in {country}.

So che il tempo e' poco, quindi vado al punto:
trovo auto premium europee per concessionari come il suo,
e paga solo se l'auto le piace.

Se le interessa, mi risponda qui su WhatsApp
o mi chiami al {phone}. Buona giornata.""",

    # ── DAY 21 (break-up) ─────────────────────────────────
    "BREAKUP": """Buongiorno {dealer_name} — capisco che non sia
il momento giusto. Nessun problema.

Se in futuro cerca un modello specifico dall'Europa,
mi scriva pure. Buon lavoro.

Luca Ferretti""",
}

# ── Messaggi per dealer che GIA' FANNO IMPORT (OBJ-3 handler) ──
IMPORT_DEALER_TEMPLATES = {
    "DAY1_ALREADY_IMPORTS": """Buongiorno {dealer_name}, ho visto che lavora gia'
con importazioni europee — ottimo, pochi in zona lo fanno.

Ho trovato un {vehicle} su portale {country} a {price_eu_str}.
{price_diff_str} sotto il prezzo di mercato italiano.

Se le interessa, le mando foto e specifiche.
Con me paga solo a consegna — zero anticipi.

Luca Ferretti""",

    "DAY3_ALREADY_IMPORTS": """[FOTO HD veicolo]

{vehicle_2} — {price_eu_str} {country}.
Questo viene da un portale {country_adj} che in Italia
non compare su AutoScout24.

Il vantaggio di avere qualcuno che cerca su 73 portali
in 19 paesi: trova cose che da solo non vede.

Le interessa?""",
}


# ══════════════════════════════════════════════════════════════
# SEZIONE 4: SEQUENZA TOUCHPOINT
# ══════════════════════════════════════════════════════════════

SEQUENCE = [
    {"day": 1,  "channel": "WA_TEXT",  "content": "Veicolo concreto + domanda chiusa",
     "timing": "mart/merc 8:30-9:00"},
    {"day": 3,  "channel": "WA_PHOTO", "content": "Foto HD + secondo veicolo o aggiornamento",
     "timing": "mart/merc 8:30-9:00"},
    {"day": 7,  "channel": "WA_TEXT",  "content": "FOMO lieve O uscita dignitosa",
     "timing": "mart/merc 8:30-9:00"},
    {"day": 10, "channel": "WA_VOICE", "content": "Vocale 20 sec — voce umana rompe barriera",
     "timing": "matt 9:00 o sab 8:30-10:00"},
    {"day": 14, "channel": "WA_TEXT",  "content": "Referral zona o case study anonimo",
     "timing": "mart/merc 8:30-9:00"},
    {"day": 21, "channel": "WA_TEXT",  "content": "Break-up gentile",
     "timing": "qualsiasi giorno lavorativo"},
    {"day": 30, "channel": "PHONE",    "content": "Telefonata 2 min O proposta visita fisica",
     "timing": "mart/merc 9:00-10:00"},
]


# ══════════════════════════════════════════════════════════════
# SEZIONE 5: CHECKLIST PRE-INVIO
# ══════════════════════════════════════════════════════════════

PRE_SEND_CHECKLIST = [
    "Il veicolo citato e' REALE e disponibile ORA (verificato su portale)",
    "I numeri (prezzo EU, prezzo IT, margine) sono VERIFICATI",
    "Il messaggio e' < 6 righe",
    "NON contiene: ARGOS nel corpo, DEKRA, DAT, CoVe, AI, algoritmo, piattaforma",
    "NON contiene link",
    "NON attacca la concorrenza",
    "E' personalizzato per l'archetipo del dealer",
    "Cita dati SPECIFICI del dealer (stock, recensioni, modelli) se possibile",
    "Orario invio: mart/merc 8:30-9:00 OPPURE sab 8:30-10:00",
    "Identita' Luca Ferretti verificabile su Google (landing + Google Business)",
]


# ══════════════════════════════════════════════════════════════
# SEZIONE 6: REGOLE LINGUAGGIO
# ══════════════════════════════════════════════════════════════

LANGUAGE_RULES = {
    "use": [
        ("macchina", "auto"),
        ("auto europea", "dalla Germania/Belgio/Olanda"),
        ("margine", "ci guadagna €X"),
        ("km certificati", "km verificati"),
        ("documenti a posto", "tutto in regola"),
        ("la porto a [citta']", "consegna diretta"),
    ],
    "never_use": [
        "veicolo EU", "reimportazione", "ROI", "spread", "delta",
        "pipeline", "piattaforma", "algoritmo", "sistema",
        "importazione parallela", "processo end-to-end",
        "KPI", "lead", "scalabilita'", "customer care",
        "DEKRA", "DAT", "CoVe", "Claude", "AI", "Anthropic",
    ],
}


# ══════════════════════════════════════════════════════════════
# SEZIONE 7: FUNZIONI OPERATIVE
# ══════════════════════════════════════════════════════════════

def score_dealer(stock: int, years: int, premium_pct: float,
                 reviews: int, rating: float,
                 has_import_signal: bool, age_under_45: bool,
                 social_active: bool) -> dict:
    """Calcola score ARGOS per un dealer. Ritorna score 0-10 + breakdown."""

    scores = {}

    # Stock fit (20-40 ideale, 15-60 accettabile)
    if 20 <= stock <= 40:
        scores["stock_fit"] = 10.0
    elif 15 <= stock < 20 or 40 < stock <= 60:
        scores["stock_fit"] = 7.0
    elif stock < 15:
        scores["stock_fit"] = 3.0
    else:
        scores["stock_fit"] = 4.0

    # Years fit (3-8 ideale)
    if 3 <= years <= 8:
        scores["years_fit"] = 10.0
    elif 1 <= years < 3:
        scores["years_fit"] = 5.0
    elif 8 < years <= 15:
        scores["years_fit"] = 6.0
    else:
        scores["years_fit"] = 3.0

    # Premium percentage
    if premium_pct >= 50:
        scores["premium_pct"] = 10.0
    elif premium_pct >= 30:
        scores["premium_pct"] = 8.0
    elif premium_pct >= 15:
        scores["premium_pct"] = 6.0
    else:
        scores["premium_pct"] = 2.0

    # Social
    scores["social_active"] = 10.0 if social_active else 3.0

    # Reviews fit (25-100 ideale)
    if 25 <= reviews <= 100:
        scores["reviews_fit"] = 10.0
    elif 100 < reviews <= 300:
        scores["reviews_fit"] = 7.0
    elif reviews < 25:
        scores["reviews_fit"] = 4.0
    else:
        scores["reviews_fit"] = 5.0

    # Import signal (il piu' importante dopo premium)
    scores["import_signal"] = 10.0 if has_import_signal else 2.0

    # Young owner
    scores["young_owner"] = 10.0 if age_under_45 else 4.0

    # Weighted total
    total = sum(scores[k] * SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS)

    # Bonus: se ha segnale import + premium > 30% → +0.5
    if has_import_signal and premium_pct >= 30:
        total = min(10.0, total + 0.5)

    return {
        "total": round(total, 1),
        "breakdown": scores,
        "tier": "TIER_0_IMPORT" if has_import_signal else
                "TIER_1_PREMIUM" if total >= 7.5 else
                "TIER_2_MONITOR" if total >= 6.0 else
                "SKIP",
    }


def generate_message(archetype: str, day: int, dealer_name: str = "",
                     vehicle: str = "", price_eu: int = 0, price_it: int = 0,
                     country: str = "Germania", specs: str = "",
                     reviews_note: str = "", nearby_city: str = "",
                     already_imports: bool = False, **kwargs) -> str:
    """Genera messaggio WA per archetipo e giorno specifico."""

    margin = price_it - price_eu - 1650  # trasporto + fee stimati
    price_eu_str = f"€{price_eu:,}".replace(",", ".")
    price_it_str = f"€{price_it:,}".replace(",", ".")
    margin_str = f"€{margin:,}".replace(",", ".")
    price_diff = price_it - price_eu
    price_diff_str = f"€{price_diff:,}".replace(",", ".")

    # Se il dealer gia' importa, usa template dedicato
    if already_imports and day <= 3:
        key = f"DAY{day}_ALREADY_IMPORTS"
        template = IMPORT_DEALER_TEMPLATES.get(key, "")
        if template:
            country_adj = {
                "Germania": "tedesco", "Belgio": "belga",
                "Olanda": "olandese", "Austria": "austriaco",
                "Francia": "francese", "Svezia": "svedese",
            }.get(country, "europeo")
            return template.format(
                dealer_name=dealer_name, vehicle=vehicle,
                price_eu_str=price_eu_str, price_it_str=price_it_str,
                price_diff_str=price_diff_str, country=country,
                country_adj=country_adj, margin_str=margin_str,
                vehicle_2=kwargs.get("vehicle_2", vehicle),
                km=kwargs.get("km", ""),
            )

    key = f"{archetype}_DAY{day}"
    template = MESSAGE_TEMPLATES.get(key, "")

    if not template:
        if day == 10:
            template = MESSAGE_TEMPLATES.get("VOCALE_SCRIPT", "")
        elif day == 21:
            template = MESSAGE_TEMPLATES.get("BREAKUP", "")
        else:
            return f"[Template non trovato per {archetype} Day {day}]"

    return template.format(
        dealer_name=dealer_name, vehicle=vehicle,
        price_eu_str=price_eu_str, price_it_str=price_it_str,
        margin_str=margin_str, country=country, specs=specs,
        reviews_note=reviews_note, nearby_city=nearby_city,
        vehicle_2=kwargs.get("vehicle_2", vehicle),
        km=kwargs.get("km", ""),
        phone=kwargs.get("phone", "328-XXXXXXX"),
    )


def print_sequence(dealer_name: str, archetype: str, start_date: str = None):
    """Stampa la sequenza completa di touchpoint per un dealer."""
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start = datetime.now()

    print(f"\n{'='*60}")
    print(f"SEQUENZA OUTREACH — {dealer_name} ({archetype})")
    print(f"{'='*60}")
    for step in SEQUENCE:
        date = start + timedelta(days=step["day"] - 1)
        day_name = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"][date.weekday()]
        print(f"  Day {step['day']:2d} | {date.strftime('%d/%m')} ({day_name}) | "
              f"{step['channel']:10s} | {step['content']}")
        print(f"         | Orario: {step['timing']}")
    print(f"{'='*60}\n")


def print_checklist():
    """Stampa checklist pre-invio."""
    print("\n" + "="*60)
    print("CHECKLIST PRE-INVIO — Verifica OGNI punto")
    print("="*60)
    for i, item in enumerate(PRE_SEND_CHECKLIST, 1):
        print(f"  [ ] {i}. {item}")
    print("="*60 + "\n")


def print_archetype_guide(archetype: str):
    """Stampa guida completa per un archetipo."""
    a = ARCHETYPES.get(archetype)
    if not a:
        print(f"Archetipo '{archetype}' non trovato. Disponibili: {list(ARCHETYPES.keys())}")
        return
    print(f"\n{'='*60}")
    print(f"GUIDA ARCHETIPO: {archetype}")
    print(f"{'='*60}")
    for k, v in a.items():
        print(f"  {k:15s}: {v}")
    print(f"{'='*60}\n")


# ══════════════════════════════════════════════════════════════
# SEZIONE 8: CLI
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="ARGOS Dealer Scouting Playbook")
    sub = parser.add_subparsers(dest="command")

    # Score dealer
    sc = sub.add_parser("score", help="Calcola score dealer")
    sc.add_argument("--stock", type=int, required=True)
    sc.add_argument("--years", type=int, required=True)
    sc.add_argument("--premium-pct", type=float, required=True)
    sc.add_argument("--reviews", type=int, required=True)
    sc.add_argument("--rating", type=float, default=4.0)
    sc.add_argument("--has-import", action="store_true")
    sc.add_argument("--age-under-45", action="store_true")
    sc.add_argument("--social-active", action="store_true")
    sc.add_argument("--dealer-name", default="")

    # Generate message
    msg = sub.add_parser("message", help="Genera messaggio WA")
    msg.add_argument("--archetype", required=True, choices=list(ARCHETYPES.keys()))
    msg.add_argument("--day", type=int, required=True)
    msg.add_argument("--dealer-name", default="")
    msg.add_argument("--vehicle", default="BMW X3 20d 2021")
    msg.add_argument("--price-eu", type=int, default=28000)
    msg.add_argument("--price-it", type=int, default=34000)
    msg.add_argument("--country", default="Germania")
    msg.add_argument("--already-imports", action="store_true")

    # Sequence
    seq = sub.add_parser("sequence", help="Mostra sequenza touchpoint")
    seq.add_argument("--dealer-name", required=True)
    seq.add_argument("--archetype", required=True)
    seq.add_argument("--start-date", default=None)

    # Checklist
    sub.add_parser("checklist", help="Mostra checklist pre-invio")

    # Archetype guide
    ag = sub.add_parser("archetype", help="Guida archetipo")
    ag.add_argument("--type", required=True, choices=list(ARCHETYPES.keys()))

    args = parser.parse_args()

    if args.command == "score":
        result = score_dealer(
            stock=args.stock, years=args.years, premium_pct=args.premium_pct,
            reviews=args.reviews, rating=args.rating,
            has_import_signal=args.has_import, age_under_45=args.age_under_45,
            social_active=args.social_active,
        )
        print(f"\n{'='*60}")
        print(f"SCORE DEALER: {args.dealer_name or 'N/A'}")
        print(f"{'='*60}")
        print(f"  TOTALE: {result['total']}/10 — {result['tier']}")
        print(f"  Breakdown:")
        for k, v in result['breakdown'].items():
            weight = SCORING_WEIGHTS[k] * 100
            print(f"    {k:20s}: {v:4.1f}/10 (peso {weight:.0f}%)")
        print(f"{'='*60}\n")

    elif args.command == "message":
        msg_text = generate_message(
            archetype=args.archetype, day=args.day,
            dealer_name=args.dealer_name, vehicle=args.vehicle,
            price_eu=args.price_eu, price_it=args.price_it,
            country=args.country, already_imports=args.already_imports,
        )
        print(f"\n{'='*60}")
        print(f"MESSAGGIO {args.archetype} — Day {args.day}")
        print(f"{'='*60}")
        print(msg_text)
        print(f"{'='*60}")
        print(f"Caratteri: {len(msg_text)}")
        # Checklist rapida
        for word in LANGUAGE_RULES["never_use"]:
            if word.lower() in msg_text.lower():
                print(f"  ⚠️  ATTENZIONE: contiene '{word}' — VIETATO")
        print()

    elif args.command == "sequence":
        print_sequence(args.dealer_name, args.archetype, args.start_date)

    elif args.command == "checklist":
        print_checklist()

    elif args.command == "archetype":
        print_archetype_guide(args.type)

    else:
        parser.print_help()
        print("\nEsempi:")
        print("  python3 tools/dealer_scouting_playbook.py score --stock 36 --years 10 --premium-pct 40 --reviews 62 --rating 4.9 --has-import --social-active --dealer-name 'Stile Car'")
        print("  python3 tools/dealer_scouting_playbook.py message --archetype PERFORMANTE --day 1 --dealer-name Domenico --vehicle 'BMW X5 30d 2022' --price-eu 38500 --price-it 47000 --already-imports")
        print("  python3 tools/dealer_scouting_playbook.py sequence --dealer-name 'Stile Car' --archetype PERFORMANTE --start-date 2026-03-25")
        print("  python3 tools/dealer_scouting_playbook.py checklist")
        print("  python3 tools/dealer_scouting_playbook.py archetype --type PERFORMANTE")


if __name__ == "__main__":
    main()
