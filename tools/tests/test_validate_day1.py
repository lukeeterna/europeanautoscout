#!/usr/bin/env python3
"""
test_validate_day1.py — suite sintetica per validate_day1.py (gate anti-invenzione Day-1).

FIXTURE INLINE, NESSUN DATO LIVE: profilo + KB sono definiti qui sotto, self-contained.
Ogni caso verifica un exit-code atteso E che sia scattato la violazione GIUSTA.

Il caso (e) è il CASO-COLPEVOLE: riproduce lo stile del vecchio
batch_generator.py::generate_day1_message ("tratta BMW e premium, ~20 auto" da
perche_lui_map/archetipo + get_dealer_stock_from_db fallback {"total":20,...}) su un
profilo che NON supporta il claim → il gate DEVE bloccare. Prova che avrebbe fermato
il bug reale del repo.

Run:  python3 tools/tests/test_validate_day1.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from validate_day1 import validate_day1  # noqa: E402

# ── FIXTURE INLINE ────────────────────────────────────────────────────────────

# Profilo dealer REALE-STILE (come lo produce tools/dealer_profile.py). NIENTE BMW.
PROFILE = {
    "source_url": "https://www.autoscout24.it/concessionari/auto-esempio",
    "name": "Auto Esempio SRL",
    "location": "Bari",
    "stock_count": 12,
    "top_brands": ["Audi", "Mercedes"],
    "top_segment": None,
    "top_models": ["Audi A6", "Mercedes Classe E"],
    "example_vehicles": [
        {"make": "Audi", "model": "A6", "year": 2021, "price_eur": 34000.0},
    ],
    "_provenance": {"note": "campo null = assente dai dati, non stimato"},
}

# KB inline: un solo FATTO grounding, [T3] puro, PROVENIENZA-NEUTRO (sovrapprezzo 25-30%
# pagato da chi compra un'usata coi km falsati: problema del mercato IT, non dell'origine).
# Il vecchio FATTO "importate vs domestiche = 3x" è import-based → fuori per regola geo.
KB_LINES = [
    "- FATTO: chi compra auto con km manomessi paga il 25-30% sopra il valore reale "
    "(25% e 29,3% in due studi) | FONTE: carVertical, 2025 | DATA: 2025-01-01 | "
    "NUMERO: +25-30% sul valore reale (25% e 29,3% in due studi) | VERIFICA: confronta "
    "il prezzo col valore di mercato reale del modello [T3]\n",
]

# (a) PULITO: marca dal profilo, leva 25-30% onesta (KB, neutra), opt-out + identità Azzurra.
MSG_CLEAN = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "Seguo alcuni concessionari a Bari e ho notato il vostro lavoro sulle Audi.\n"
    "Un dato che uso nel mio lavoro: in Italia chi compra un'usata coi km non veritieri "
    "paga circa il 25-30% in più del valore reale (fonte commerciale, ordine di grandezza).\n"
    "Le capita di dover verificare i km di un'usata prima di valutarla? Se non le "
    "interessa, mi risponda \"no grazie\" e non la disturbo più.\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (b) NUMERO INVENTATO: "45 auto" non è nel profilo (stock=12) né in KB.
MSG_INVENTED_NUMBER = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "Ho notato il vostro lavoro sulle Audi a Bari; nel suo parco ho contato 45 auto pronte.\n"
    "Le capita di verificare i km delle usate prima di valutarle? Un \"no grazie\" e non la disturbo più.\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (c) T3 SPACCIATO PER CERTO: la leva 25-30% (fonte solo T3) presentata come "dimostrato/certificato".
MSG_T3_AS_CERTAIN = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "Ho notato il vostro lavoro sulle Audi. È dimostrato e certificato che chi compra "
    "un'usata coi km truccati paga il 25-30% sopra il valore reale.\n"
    "Le capita di verificare i km prima di valutare? Un \"no grazie\" e non la disturbo più.\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (d) OPT-OUT ASSENTE: tutto valido tranne la via d'uscita.
MSG_NO_OPTOUT = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "Ho notato il vostro lavoro sulle Audi a Bari.\n"
    "Le capita di verificare i km delle usate prima di valutarle?\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (e) CASO-COLPEVOLE: stile batch_generator (claim da archetipo/fallback) su profilo che NON lo supporta.
MSG_GUILTY_BATCH = (
    "Buongiorno, sono Azzurra, assistente di Luca Ferretti.\n"
    "Ho visto il suo stock, tratta BMW e premium, circa 20 auto.\n"
    "Le capita di verificare i km delle usate prima di valutarle? Un \"no grazie\" e non la disturbo più.\n"
    "Azzurra"
)

# (f) DIREZIONE-SERVIZIO (vi-a): verifica km riferita allo STOCK / "auto in vendita" del destinatario.
MSG_STOCK_TARGET = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "Ho notato il vostro lavoro sulle Audi a Bari.\n"
    "Posso aiutarla a verificare i km delle auto in vendita nel suo salone? "
    "Un \"no grazie\" e non la disturbo più.\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (g) DIREZIONE-SERVIZIO (vi-b): claim di DANNO ai clienti del destinatario.
MSG_CLIENT_HARM = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "La frode sui km danneggia i suoi clienti quando comprano un'usata.\n"
    "Le va di verificare i km prima di un acquisto? Un \"no grazie\" e non la disturbo più.\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (h) PULITO DIREZIONE-ACQUISTI: verifica km sugli ACQUISTI del dealer (permute/valutazione) → PASS.
MSG_CLEAN_BUY = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "Seguo alcuni concessionari a Bari e ho notato il vostro lavoro sulle Audi.\n"
    "Quando ritira un'usata in permuta o valuta un acquisto, le capita di dover verificare "
    "i km prima? Se non le interessa, mi risponda \"no grazie\" e non la disturbo più.\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (i) FORMA-FINALE (vii-a): opt-out NON-istruzione ("no grazie" senza verbo risponda/scriva/mi dica).
MSG_OPTOUT_NO_VERB = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "Seguo alcuni concessionari a Bari e ho notato il vostro lavoro sulle Audi.\n"
    "Quando valuta un acquisto, le capita di dover verificare i km prima? "
    "Se non le interessa, un \"no grazie\" e non la disturbo più.\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (j) FORMA-FINALE (vii-b): la frase FINALE contiene un commitment-ask ('procediamo').
MSG_COMMITMENT_ASK = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti.\n"
    "Seguo alcuni concessionari a Bari e ho notato il vostro lavoro sulle Audi.\n"
    "Se non le interessa, mi risponda \"no grazie\" e non la disturbo più.\n"
    "Se le va, procediamo insieme?"
)

# (k) FORMA-FINALE (vii-c): denominazione aziendale 'ARGOS' presente.
MSG_COMPANY_NAME = (
    "Buongiorno Auto Esempio SRL, sono Azzurra, assistente di Luca Ferretti di ARGOS Automotive.\n"
    "Seguo alcuni concessionari a Bari e ho notato il vostro lavoro sulle Audi.\n"
    "Se non le interessa, mi risponda \"no grazie\" e non la disturbo più.\n"
    "Azzurra, per conto di Luca Ferretti"
)

# (case_label, message, exit_atteso, substring_violazione_attesa|None)
CASES = [
    ("a) pulito e tracciato", MSG_CLEAN, 0, None),
    ("b) numero inventato (45)", MSG_INVENTED_NUMBER, 1, "45"),
    ("c) T3 spacciato per certo", MSG_T3_AS_CERTAIN, 1, "[T3] spacciato"),
    ("d) opt-out assente", MSG_NO_OPTOUT, 1, "opt-out assente"),
    ("e) CASO-COLPEVOLE (batch: BMW+20)", MSG_GUILTY_BATCH, 1, "BMW"),
    ("f) DIREZIONE-SERVIZIO stock/auto-in-vendita (vi-a)", MSG_STOCK_TARGET, 1, "(vi)"),
    ("g) DIREZIONE-SERVIZIO danno-ai-clienti (vi-b)", MSG_CLIENT_HARM, 1, "(vi)"),
    ("h) PULITO direzione-acquisti (permuta/valutazione)", MSG_CLEAN_BUY, 0, None),
    ("i) FORMA-FINALE opt-out non-istruzione (vii-a)", MSG_OPTOUT_NO_VERB, 1, "(vii-a)"),
    ("j) FORMA-FINALE commitment-ask in chiusura (vii-b)", MSG_COMMITMENT_ASK, 1, "(vii-b)"),
    ("k) FORMA-FINALE denominazione aziendale ARGOS (vii-c)", MSG_COMPANY_NAME, 1, "(vii-c)"),
]


def run():
    fails = []
    print("=== suite validate_day1 (fixture inline, zero dati live) ===")
    for label, msg, want_exit, want_sub in CASES:
        problems = validate_day1(msg, PROFILE, KB_LINES)
        got_exit = 1 if problems else 0
        ok_exit = got_exit == want_exit
        ok_sub = True
        if want_sub is not None:
            ok_sub = any(want_sub in p for p in problems)
        status = "PASS" if (ok_exit and ok_sub) else "FAIL"
        print(f"[{status}] {label}: exit={got_exit} (atteso {want_exit})")
        for p in problems:
            print(f"        · {p}")
        if not ok_exit:
            fails.append(f"{label}: exit={got_exit} atteso={want_exit}")
        if not ok_sub:
            fails.append(f"{label}: violazione attesa '{want_sub}' non trovata")

    print("---")
    if fails:
        print(f"SUITE FAIL — {len(fails)} problema/i:")
        for f in fails:
            print("  -", f)
        return 1
    print("SUITE PASS (11/11: pulito→exit0, inventato→exit1, T3-certo→exit1, "
          "opt-out→exit1, colpevole-batch→exit1, vi-a-stock→exit1, "
          "vi-b-danno-clienti→exit1, pulito-acquisti→exit0, vii-a-optout-non-istruzione→exit1, "
          "vii-b-commitment-ask→exit1, vii-c-denominazione-argos→exit1)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
