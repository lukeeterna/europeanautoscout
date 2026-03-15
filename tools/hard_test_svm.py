#!/usr/bin/env python3
"""
ARGOS Hard Test SVM — S56
Certifica il classificatore con 5 categorie adversariali prima dell'outreach dealer.

GO  = archetipo corretto + conf > 0.65
NO-GO = archetipo sbagliato OR conf < 0.50
"""

import json
import pickle
import sys
from pathlib import Path
from collections import defaultdict

MODEL_PATH = Path(__file__).parent.parent / "data/models/argos_svm_classifier.pkl"
REPORT_PATH = Path(__file__).parent.parent / "data/hard_test_report_s56.json"

# ──────────────────────────────────────────────
# LOAD MODEL
# ──────────────────────────────────────────────

def load_model():
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    return bundle["pipeline"]

def predict(pipeline, text):
    proba = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    pred_idx = proba.argmax()
    return {
        "predicted": classes[pred_idx],
        "confidence": round(float(proba[pred_idx]), 3),
        "top3": [
            {"archetype": classes[i], "prob": round(float(p), 3)}
            for i, p in sorted(enumerate(proba), key=lambda x: -x[1])[:3]
        ]
    }

# ──────────────────────────────────────────────
# TEST CASES
# ──────────────────────────────────────────────

CAT_1A_ADVERSARIAL = [
    # (text, expected, description)
    (
        "Non sono il tipo che guarda i numeri, voglio solo capire se conviene",
        "RAGIONIERE",
        "keyword_poison: nega interesse numeri ma chiede ROI → RAGIONIERE non OPPORTUNISTA"
    ),
    (
        "Ho già i miei fornitori ma dimmi: esclusiva zona sì o no?",
        "VISIONARIO",
        "keyword_poison: BARONE bait (fornitori) ma segnale netto VISIONARIO (esclusiva zona)"
    ),
    (
        "Guarda ho fretta ma prima dimmi chi firma il contratto",
        "TECNICO",
        "keyword_poison: PERFORMANTE bait (fretta) ma priorità chi-firma → TECNICO"
    ),
    (
        "Ne parlo col commercialista ma intanto mandami i numeri IVA",
        "RAGIONIERE",
        "keyword_poison: DELEGATORE bait (commercialista) ma IVA/numeri → RAGIONIERE"
    ),
    (
        "Non cambio quello che funziona però se mi dai l'esclusiva...",
        "VISIONARIO",
        "keyword_poison: CONSERVATORE bait (non cambio) ma esclusiva → VISIONARIO"
    ),
    (
        "Ho sempre fatto così però ho bisogno entro fine mese",
        "PERFORMANTE",
        "keyword_poison: CONSERVATORE bait (sempre fatto così) ma deadline → PERFORMANTE"
    ),
    # Negation traps
    (
        "Non mi interessano i documenti, mi interessa solo il prezzo finale",
        "OPPORTUNISTA",
        "negation_trap: nega documenti (TECNICO vocab) → focus prezzo = OPPORTUNISTA"
    ),
    (
        "Non voglio essere il primo, voglio solo guadagnare",
        "RAGIONIERE",
        "negation_trap: nega primo (VISIONARIO vocab) → guadagnare/ROI = RAGIONIERE"
    ),
    (
        "Non ho tempo per garanzie e certificazioni, parlami di tempi",
        "PERFORMANTE",
        "negation_trap: nega garanzie (TECNICO vocab) → velocità/tempi = PERFORMANTE"
    ),
    # Fake signals
    (
        "48 ore o chiudo. Ps: ma quanto rimane netto con l'IVA?",
        "RAGIONIERE",
        "fake_signal: PERFORMANTE bait (48 ore) ma IVA/netto è segnale dominante → RAGIONIERE"
    ),
    (
        "Sono il riferimento della zona. Comunque quanto costa?",
        "OPPORTUNISTA",
        "fake_signal: BARONE bait (riferimento zona) ma 'quanto costa' = OPPORTUNISTA"
    ),
]

CAT_1B_NOISE = [
    (
        "cmq ho già i miei ke mi trovan tutto nn ho bisogno",
        "BARONE",
        "noise: typo+abbr WA — 'già i miei' = BARONE"
    ),
    (
        "dotto senziamoci ma prima mi dica i costi reali",
        "RAGIONIERE",
        "dialect: campano 'dotto/senziamoci' + 'costi reali' = RAGIONIERE"
    ),
    (
        "xché dovrei pagare 900€??? il mio importatore prende 600",
        "OPPORTUNISTA",
        "noise: typo+emoji — price comparison = OPPORTUNISTA"
    ),
    (
        "👀 vediamo cosa ha... ma non è detto eh",
        "CONSERVATORE",
        "noise: emoji+ellipsis — ambiguous resistance = CONSERVATORE"
    ),
    (
        "MANDAMI SUBITO QUELLO CHE HAI DISPONIBILE ADESSO",
        "PERFORMANTE",
        "noise: ALL CAPS — urgency immediate = PERFORMANTE"
    ),
    (
        "Interessante 🤔 però ne parlo col mio socio (lui sa più di me su ste cose)",
        "DELEGATORE",
        "noise: emoji+parenth — deferral to socio = DELEGATORE"
    ),
    (
        "boh... ci vediamo forse. vedremo 🙏",
        "CONSERVATORE",
        "dialect: sicilia flavor — extreme hedging = CONSERVATORE"
    ),
]

CAT_1C_MINIMAL = [
    ("Ok", None, "1w — ambiguous ack, expect conf <0.70"),
    ("Vedrò", None, "1w — hedging, expect conf <0.70"),
    ("Ci penso", None, "2w — defer, expect conf <0.70"),
    ("Mah", None, "1w — doubt signal, expect conf <0.70"),
    ("Interessante", None, "1w — positive lean but weak, expect conf <0.70"),
    ("Forse", None, "1w — extreme hedge, expect conf <0.70"),
    ("Disponibile adesso?", None, "2w — urgency, expect conf <0.70"),
    ("Garanzie?", None, "1w — TECNICO lean but weak, expect conf <0.70"),
    ("Esclusiva?", None, "1w — VISIONARIO lean but weak, expect conf <0.70"),
    ("Sconto?", None, "1w — OPPORTUNISTA lean but weak, expect conf <0.70"),
    ("Ne parlo", None, "2w — DELEGATORE lean but weak, expect conf <0.70"),
    ("Non so", None, "2w — ambiguous, expect conf <0.70"),
    ("Ci sento", None, "2w — defer, expect conf <0.70"),
    ("Mandami qualcosa", None, "3w — neutral interest, expect conf <0.70"),
]

CAT_1D_REAL_DEALER = [
    (
        "Luca dimmi subito che BMW hai. Ho un cliente che aspetta. Entro giovedì o vado da altri.",
        "PERFORMANTE",
        "Mazzilli Auto BA — deadline esplicita + cliente che aspetta"
    ),
    (
        "Buongiorno. Chi emette il Gutachten? È DEKRA accreditato EU? Il contratto lo firma ARGOS come principale?",
        "TECNICO",
        "Prime Cars CT — domande tecniche certificazione + chi firma"
    ),
    (
        "Dotto mi dica: con le sue auto quanto rimane in tasca netto? Come funziona l'IVA sul regime margine?",
        "RAGIONIERE",
        "Campania Sport Car NA — IVA regime margine + netto"
    ),
    (
        "Ho già i miei contatti. Lavoro da 20 anni. Cosa mi dai che non ho.",
        "BARONE",
        "Autosannino NA — status 20 anni + già fornitori"
    ),
    (
        "I miei clienti sono esigenti. Com'è messa la vettura visivamente? Non voglio problemi di immagine.",
        "NARCISO",
        "Magicar PA — immagine clienti esigenti + aspetto visivo"
    ),
]

CAT_1E_CONFUSION_PAIRS = {
    "VISIONARIO_vs_PERFORMANTE": [
        ("Voglio essere il primo dealer della zona ad avere questo servizio", "VISIONARIO"),
        ("Entro venerdì mi serve una risposta definitiva, non ho tempo da perdere", "PERFORMANTE"),
        ("Se mi garantisci l'esclusiva per tutta la Puglia sono dentro", "VISIONARIO"),
        ("Ho già un acquirente. BMW Serie 5, 2021. Dimmi se ce l'hai entro domani.", "PERFORMANTE"),
        ("Nessun altro qui fa quello che fai tu? Voglio capire se posso diventare il riferimento", "VISIONARIO"),
        ("Considera questo come ultimatum: o mi mandi l'offerta oggi o chiudo", "PERFORMANTE"),
        ("Mi interessa essere l'unico nella mia provincia ad avere veicoli tedeschi certificati", "VISIONARIO"),
        ("Cliente aspetta risposta. Hai una Mercedes C 2022 disponibile adesso?", "PERFORMANTE"),
        ("Posso avere diritto di prelazione sulla zona? Prima di tutti gli altri?", "VISIONARIO"),
        ("Non ho tempo per lunghe trattative. Dimmi sì o no entro oggi.", "PERFORMANTE"),
    ],
    "BARONE_vs_CONSERVATORE": [
        ("Ho i miei fornitori da 15 anni. Non ho bisogno di nessuno.", "BARONE"),
        ("Ho sempre lavorato così. Non cambio metodo adesso.", "CONSERVATORE"),
        ("Conosco già tutti nel settore. Non mi serve un nuovo contatto.", "BARONE"),
        ("Il rischio non fa per me. Preferisco quello che conosco.", "CONSERVATORE"),
        ("Il mio nome vale in questa zona. Mica ho bisogno di intermediari.", "BARONE"),
        ("Capisco ma ho paura di problemi. Mai avuto complicazioni finora.", "CONSERVATORE"),
        ("Ho costruito la mia rete da solo. Non la cambio certo adesso.", "BARONE"),
        ("Preferirei aspettare e vedere come va con altri prima di buttarmi.", "CONSERVATORE"),
        ("Sono il punto di riferimento qui. Lo sanno tutti.", "BARONE"),
        ("Non mi fido di cose nuove. Ho già abbastanza da gestire.", "CONSERVATORE"),
    ],
    "OPPORTUNISTA_vs_RAGIONIERE": [
        ("Quanto costa? Se faccio 3 operazioni mi fai uno sconto?", "OPPORTUNISTA"),
        ("Mi spieghi come funziona l'IVA sul regime margine? Voglio capire il netto.", "RAGIONIERE"),
        ("Il tuo concorrente mi ha offerto 700. Cosa fai?", "OPPORTUNISTA"),
        ("Voglio vedere un'analisi ROI completa prima di decidere.", "RAGIONIERE"),
        ("Prezzo finale tutto incluso. Dimmi solo quello.", "OPPORTUNISTA"),
        ("Quante tasse pago? Come si struttura fiscalmente l'operazione?", "RAGIONIERE"),
        ("Se prendo 5 auto in 3 mesi quanto mi fai pagare?", "OPPORTUNISTA"),
        ("Il commercialista vuole capire come si registra contabilmente.", "RAGIONIERE"),
        ("Ho trovato lo stesso veicolo a 200€ in meno. Pareggi?", "OPPORTUNISTA"),
        ("Parliamo di struttura: fee deducibile? Fattura italiana?", "RAGIONIERE"),
    ],
    "RELAZIONALE_vs_DELEGATORE": [
        ("Prima di parlare di business voglio conoscerti. Vieni in concessionaria?", "RELAZIONALE"),
        ("Ne devo parlare con il mio socio. Lui gestisce i fornitori.", "DELEGATORE"),
        ("Con te mi trovo bene ma ho bisogno di fidarmi prima di comprare.", "RELAZIONALE"),
        ("Non posso decidere da solo su queste cose. Sento il titolare.", "DELEGATORE"),
        ("Ti chiamo quando sei di persona in zona. Non faccio business a distanza.", "RELAZIONALE"),
        ("Mio fratello si occupa degli acquisti. Parla con lui.", "DELEGATORE"),
        ("Ho bisogno di sentire una referenza, qualcuno che ti conosce già.", "RELAZIONALE"),
        ("Sì mi sembra interessante ma la parola finale ce l'ha il commercialista.", "DELEGATORE"),
        ("Non lavoro con persone che non vedo in faccia. Ci possiamo incontrare?", "RELAZIONALE"),
        ("Ne parliamo in famiglia, poi ti ricontatto noi.", "DELEGATORE"),
    ],
}

# ──────────────────────────────────────────────
# RUNNER
# ──────────────────────────────────────────────

def eval_go_nogo(predicted, expected, confidence):
    """
    GO  = corretto + conf >= 0.65
    MARGINAL = corretto + 0.50 <= conf < 0.65
    NO-GO = sbagliato OR conf < 0.50
    """
    if expected is None:
        return "AMBIGUOUS_OK" if confidence < 0.70 else "AMBIGUOUS_OVERCONF"
    if predicted == expected and confidence >= 0.65:
        return "GO"
    if predicted == expected and confidence >= 0.50:
        return "MARGINAL"
    return "NO-GO"

def run_category(pipeline, cases, cat_id, cat_name, expect_low_conf=False):
    results = []
    counts = defaultdict(int)
    for text, expected, desc in cases:
        r = predict(pipeline, text)
        status = eval_go_nogo(r["predicted"], expected, r["confidence"])
        counts[status] += 1
        results.append({
            "text": text[:80] + "..." if len(text) > 80 else text,
            "expected": expected,
            "predicted": r["predicted"],
            "confidence": r["confidence"],
            "top3": r["top3"],
            "status": status,
            "description": desc,
        })
    return {
        "category": cat_id,
        "name": cat_name,
        "total": len(cases),
        "counts": dict(counts),
        "go_rate": round(counts["GO"] / len(cases) * 100, 1),
        "cases": results,
    }

def run_confusion_pair(pipeline, pair_name, cases):
    results = []
    correct = 0
    for text, expected in cases:
        r = predict(pipeline, text)
        ok = r["predicted"] == expected
        if ok:
            correct += 1
        results.append({
            "text": text[:70] + "..." if len(text) > 70 else text,
            "expected": expected,
            "predicted": r["predicted"],
            "confidence": r["confidence"],
            "correct": ok,
        })
    accuracy = round(correct / len(cases) * 100, 1)
    # Identify discriminant tokens (most common words in correct vs wrong)
    correct_texts = [c["text"] for c in results if c["correct"]]
    wrong_texts = [c["text"] for c in results if not c["correct"]]
    return {
        "pair": pair_name,
        "total": len(cases),
        "correct": correct,
        "accuracy": accuracy,
        "go": accuracy >= 65,
        "cases": results,
    }

def compute_archetype_verdict(report):
    """Aggregate GO/NO-GO per archetipo across all non-minimal categories."""
    arch_stats = defaultdict(lambda: {"go": 0, "marginal": 0, "nogo": 0, "total": 0})

    for cat in ["1a_adversarial", "1b_noise", "1d_real_dealer"]:
        if cat in report:
            for case in report[cat]["cases"]:
                exp = case.get("expected")
                if exp:
                    arch_stats[exp]["total"] += 1
                    s = case["status"]
                    if s == "GO":
                        arch_stats[exp]["go"] += 1
                    elif s == "MARGINAL":
                        arch_stats[exp]["marginal"] += 1
                    else:
                        arch_stats[exp]["nogo"] += 1

    verdicts = {}
    for arch, stats in arch_stats.items():
        if stats["total"] == 0:
            continue
        go_rate = (stats["go"] + stats["marginal"] * 0.5) / stats["total"] * 100
        verdicts[arch] = {
            "go_rate": round(go_rate, 1),
            "stats": dict(stats),
            "verdict": "GO" if go_rate >= 65 else ("MARGINAL" if go_rate >= 50 else "NO-GO"),
        }

    # Integrate confusion pair accuracy
    if "1e_confusion_pairs" in report:
        for pair_data in report["1e_confusion_pairs"].values():
            pair = pair_data["pair"]
            archs = pair.split("_vs_")
            for arch in archs:
                arch_clean = arch.strip()
                if arch_clean in verdicts:
                    # Penalize if pair accuracy is low
                    if not pair_data["go"]:
                        verdicts[arch_clean]["confusion_warning"] = f"Weak on {pair}"

    return verdicts

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("ARGOS HARD TEST SVM — S56")
    print("=" * 60)

    pipeline = load_model()
    print(f"Model loaded. Classes: {list(pipeline.classes_)}\n")

    report = {}

    # 1a — Adversarial traps
    print("[ 1a ] Running ADVERSARIAL TRAPS...")
    report["1a_adversarial"] = run_category(
        pipeline, CAT_1A_ADVERSARIAL, "1a", "Adversarial Traps"
    )
    r = report["1a_adversarial"]
    print(f"  GO: {r['counts'].get('GO',0)}  MARGINAL: {r['counts'].get('MARGINAL',0)}  NO-GO: {r['counts'].get('NO-GO',0)}  |  GO rate: {r['go_rate']}%")

    # 1b — Noise + dialect
    print("[ 1b ] Running NOISE + DIALECT STRESS...")
    report["1b_noise"] = run_category(
        pipeline, CAT_1B_NOISE, "1b", "Noise + Dialect Stress"
    )
    r = report["1b_noise"]
    print(f"  GO: {r['counts'].get('GO',0)}  MARGINAL: {r['counts'].get('MARGINAL',0)}  NO-GO: {r['counts'].get('NO-GO',0)}  |  GO rate: {r['go_rate']}%")

    # 1c — Minimal signal
    print("[ 1c ] Running MINIMAL SIGNAL TEST...")
    report["1c_minimal"] = run_category(
        pipeline, CAT_1C_MINIMAL, "1c", "Minimal Signal (expect low conf)"
    )
    # For minimal: count how many have conf < 0.70 as expected
    minimal_ok = sum(1 for c in report["1c_minimal"]["cases"] if c["status"] == "AMBIGUOUS_OK")
    minimal_overconf = sum(1 for c in report["1c_minimal"]["cases"] if c["status"] == "AMBIGUOUS_OVERCONF")
    print(f"  Under 0.70 (OK): {minimal_ok}  Over 0.70 (overconf): {minimal_overconf}  |  Calibration: {round(minimal_ok/len(CAT_1C_MINIMAL)*100,1)}%")

    # 1d — Real dealer simulation
    print("[ 1d ] Running REAL DEALER SIMULATION...")
    report["1d_real_dealer"] = run_category(
        pipeline, CAT_1D_REAL_DEALER, "1d", "Real Dealer Simulation"
    )
    r = report["1d_real_dealer"]
    print(f"  GO: {r['counts'].get('GO',0)}  MARGINAL: {r['counts'].get('MARGINAL',0)}  NO-GO: {r['counts'].get('NO-GO',0)}  |  GO rate: {r['go_rate']}%")

    # 1e — Confusion pairs
    print("[ 1e ] Running CONFUSION PAIR DEEP DIVE...")
    report["1e_confusion_pairs"] = {}
    for pair_name, cases in CAT_1E_CONFUSION_PAIRS.items():
        pd = run_confusion_pair(pipeline, pair_name, cases)
        report["1e_confusion_pairs"][pair_name] = pd
        go_label = "✅ GO" if pd["go"] else "❌ NO-GO"
        print(f"  {pair_name}: {pd['correct']}/{pd['total']} correct ({pd['accuracy']}%) — {go_label}")

    # Aggregate verdicts
    print("\n" + "=" * 60)
    print("ARCHETYPE VERDICTS")
    print("=" * 60)
    verdicts = compute_archetype_verdict(report)
    report["archetype_verdicts"] = verdicts

    all_go = []
    all_nogo = []
    for arch, v in sorted(verdicts.items()):
        label = "✅ GO" if v["verdict"] == "GO" else ("⚠️  MARGINAL" if v["verdict"] == "MARGINAL" else "❌ NO-GO")
        warn = f"  ⚠ {v.get('confusion_warning','')}" if "confusion_warning" in v else ""
        print(f"  {arch:<15} {label}  (go_rate={v['go_rate']}%){warn}")
        if v["verdict"] == "GO":
            all_go.append(arch)
        else:
            all_nogo.append(arch)

    # Dealer outreach decision
    print("\n" + "=" * 60)
    print("OUTREACH DECISION PER DEALER")
    print("=" * 60)
    dealer_batch = [
        ("Mazzilli Auto BA",      "PERFORMANTE"),
        ("Prime Cars CT",         "TECNICO"),
        ("Campania Sport Car NA",  "RAGIONIERE"),
        ("Autosannino NA",        "BARONE"),
        ("Magicar PA",            "NARCISO"),
    ]
    outreach_go = []
    for dealer, arch in dealer_batch:
        v = verdicts.get(arch, {})
        verdict = v.get("verdict", "UNKNOWN")

        # Also check real dealer result
        real_case = next((c for c in report["1d_real_dealer"]["cases"] if arch in c.get("description","") or c.get("expected")==arch), None)
        if real_case:
            real_ok = real_case["status"] in ("GO", "MARGINAL")
            real_label = f"real={real_case['predicted']}({real_case['confidence']})"
        else:
            real_ok = None
            real_label = "n/a"

        final = "GO" if verdict == "GO" and (real_ok is None or real_ok) else ("MARGINAL" if verdict in ("GO","MARGINAL") else "NO-GO")
        icon = "✅" if final == "GO" else ("⚠️ " if final == "MARGINAL" else "❌")
        print(f"  {icon} {dealer:<28} [{arch}] {real_label}")
        if final in ("GO", "MARGINAL"):
            outreach_go.append(dealer)

    report["outreach_decisions"] = {
        dealer: "GO" if dealer in outreach_go else "NO-GO"
        for dealer, _ in dealer_batch
    }

    # Save report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nReport salvato: {REPORT_PATH}")
    print(f"\nSUMMARY: GO={len(all_go)} archetipi | NO-GO={len(all_nogo)} archetipi")
    if all_nogo:
        print(f"⚠️  Archetipi deboli: {', '.join(all_nogo)} → considera dataset aggiuntivo")

    return 0 if len(all_nogo) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
