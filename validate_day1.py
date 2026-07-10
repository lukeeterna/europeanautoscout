#!/usr/bin/env python3
"""
validate_day1.py — gate deterministico ANTI-INVENZIONE per il messaggio Day-1.

È l'artefatto di PRODUZIONE del Day-1: verifica la FORMA di un messaggio già
composto, senza dati live e senza generarlo. NON valuta la condotta del generatore
LLM — impone che ogni claim del messaggio sia TRACCIABILE a una fonte verificata.

Fonti di verità ammesse (le UNICHE):
  1. dealer_profile.json  — prodotto da tools/dealer_profile.py (campi reali, null-discipline).
  2. kb/dominio/*.md      — FATTI taggati [T1|T2|T3] nel formato RUBRICA (parser da validate_kb.py).

Checks (tutti deterministici):
  (i)   TRACCIABILITÀ CLAIM:
          - ogni NUMERO nel messaggio traccia a un numero del profilo O di un FATTO KB;
          - ogni MARCA auto presentata come STOCK del dealer traccia a profile.top_brands
            (una marca fuori-contesto-stock può tracciare anche alla KB).
        Claim orfano → violazione nominata.
  (ii)  LESSICO VIETATO: garanzia|garantit*|certificato costruttore|assicuriamo → 0 match.
  (iii) OPT-OUT presente · FIRMA/IDENTITÀ "Azzurra" presente.
  (iv)  FATTI [T3] mai spacciati per certi: nessuna parola di certezza
        (certificato/provato/dimostrato/certo…) attaccata a un numero che traccia SOLO a [T3].

Uso:
  python3 validate_day1.py --message msg.txt --profile profilo.json [--kb-dir kb/dominio]
Exit-code: 0 = conforme; 1 = almeno una violazione (nominata su stderr/stdout).
Stdlib only. Compatibile python3.11+.
"""
import argparse
import glob
import json
import os
import re
import sys

# Riusa il parser di FORMATO dei FATTI KB (single source of truth per il formato RUBRICA).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_kb import parse_fact, FACT_RE, TIER_RE  # noqa: E402

# ── vocabolari di FORMA (deterministici) ──────────────────────────────────────

CAR_BRANDS = (
    "BMW", "Mercedes-Benz", "Mercedes", "Audi", "Porsche", "Range Rover",
    "Land Rover", "Volkswagen", "Volvo", "MINI", "Fiat", "Skoda", "Jaguar",
    "Opel", "Toyota", "Ferrari", "Lamborghini", "Maserati", "Alfa Romeo",
)
CAR_BRANDS_LOWER = {b.lower() for b in CAR_BRANDS}

# parole che marcano un claim sullo STOCK del dealer (→ la marca deve stare nel profilo)
STOCK_CONTEXT = (
    "stock", "tratta", "trattano", "vende", "vendono", "parco", "vetture",
    "in pronta", "disponibil", "il suo ", "le sue ", "i suoi ", "gamma", "listino",
)
OPT_OUT_MARKERS = (
    "no grazie", "un no e", "non la disturbo", "risponda no", "mi dica no",
    "basta un no", "un secco no", "un no basta",
)
IDENTITY_TOKEN = "azzurra"  # ARGOS_ASSISTANT='Azzurra' (assistente di Luca Ferretti, non Luca 1ª persona)

CERTAINTY_WORDS = (
    "certificato", "certificata", "provato", "provata", "comprovato",
    "dimostrato", "dimostrata", "dimostra", "certo", "certa", "sicuro al 100",
    "garantito", "garantita",
)
FORBIDDEN_LEXICON = (
    (re.compile(r"\bgaranzi[ae]\b", re.IGNORECASE), "garanzia"),
    (re.compile(r"\bgarantit[oaie]\b", re.IGNORECASE), "garantito"),
    (re.compile(r"certificato\s+costruttore", re.IGNORECASE), "certificato costruttore"),
    (re.compile(r"\bassicuriamo\b", re.IGNORECASE), "assicuriamo"),
)

# PROVENIENZA ESTERA/IMPORT vietata nel Day-1. Rete deterministica del vincolo geo:
#   communication.md:21  → MAI "veicolo EU" … "reimportazione"
#   CLAUDE.md:17 (progetto) → Day 1: MAI "Germania", "import", … "estero"
# Copre i termini DIRETTI e le PERIFRASI eufemistiche (il gate non deve poter essere
# aggirato con un sinonimo: "auto che arrivano da fuori mercato italiano" ≡ estero/import).
FORBIDDEN_PROVENANCE = (
    (re.compile(r"fuori\s+mercato\s+italiano", re.IGNORECASE), "fuori mercato italiano"),
    (re.compile(r"fuori\s+dall['\u2019\s]*italia", re.IGNORECASE), "fuori dall'Italia"),
    (re.compile(r"oltre\s+confine", re.IGNORECASE), "oltre confine"),
    (re.compile(r"provenienza\s+ester[ae]", re.IGNORECASE), "provenienza estera"),
    (re.compile(r"\bnon\s+nazional[ei]\b", re.IGNORECASE), "non nazionale"),
    (re.compile(r"\bda\s+altri\s+(paesi|mercati)\b", re.IGNORECASE), "da altri paesi/mercati"),
    (re.compile(r"\bester[oaie]\b", re.IGNORECASE), "estero"),
    (re.compile(r"\bimport\b", re.IGNORECASE), "import"),
    (re.compile(r"\bimportat[oaei]\b", re.IGNORECASE), "importate"),
    (re.compile(r"\bimportazion[ei]\b", re.IGNORECASE), "importazione"),
    (re.compile(r"\breimportazion[ei]\b", re.IGNORECASE), "reimportazione"),
    (re.compile(r"\bgermania\b", re.IGNORECASE), "Germania"),
    (re.compile(r"\bveicol[oi]\s+eu\b", re.IGNORECASE), "veicolo EU"),
)

# (vi) DIREZIONE-SERVIZIO — il gancio km protegge gli ACQUISTI del dealer (permute,
# approvvigionamento, valutazioni d'acquisto), MAI lo stock / le "auto in vendita" del
# destinatario; ed è VIETATO affermare o implicare danno ai SUOI clienti. Riferire la
# verifica km allo stock del dealer lo accusa implicitamente di vendere auto frodate;
# il servizio va rivolto a monte (quando il dealer COMPRA), non a valle.
# Liste chiuse word-boundary (stile FORBIDDEN_PROVENANCE), CONSERVATIVE: beccano le forme
# letterali evidenti — la semantica fine (implicazioni sfumate) resta al grader LLM.

# (vi-a) verifica km riferita allo STOCK / "auto in vendita" del destinatario
FORBIDDEN_STOCK_TARGET = (
    (re.compile(r"\bauto\s+in\s+vendita\b", re.IGNORECASE), "auto in vendita"),
    (re.compile(r"\bvetture\s+in\s+vendita\b", re.IGNORECASE), "vetture in vendita"),
    (re.compile(r"\bmacchine\s+in\s+vendita\b", re.IGNORECASE), "macchine in vendita"),
    (re.compile(r"\busat[oe]\s+in\s+vendita\b", re.IGNORECASE), "usato in vendita"),
    (re.compile(r"\b(?:auto|vetture|macchine|usat[ae])\s+che\s+(?:vende|vendete|rivende|rivendete)\b", re.IGNORECASE), "auto che vende"),
    (re.compile(r"\bkm\s+(?:del(?:la|le|lo)?|dei|degli|di)\s+(?:suo\s+|vostro\s+|proprio\s+)?stock\b", re.IGNORECASE), "km dello stock"),
    (re.compile(r"\b(?:suo|vostro|proprio)\s+stock\s+in\s+vendita\b", re.IGNORECASE), "stock in vendita"),
)

# (vi-b) claim di DANNO ai clienti del destinatario (possessivo/specifico, NON il mercato in generale)
FORBIDDEN_CLIENT_HARM = (
    (re.compile(r"\b(?:danneggia|danneggiano|penalizza|penalizzano|colpisce|colpiscono|truffa|truffano|raggira|raggirano|frega|fregano|inganna|ingannano)\s+i\s+(?:suoi|vostri)\s+client", re.IGNORECASE), "danno ai suoi clienti"),
    (re.compile(r"\b(?:danneggia|danneggiano|penalizza|penalizzano|colpisce|colpiscono)\s+i\s+client[ie]\s+d(?:ei|egli|el|elle)\s+concessionar", re.IGNORECASE), "danno ai clienti del concessionario"),
    (re.compile(r"\bdann[oi]\s+(?:ai|per\s+i)\s+(?:suoi|vostri)\s+client", re.IGNORECASE), "danno ai suoi clienti"),
    (re.compile(r"\ba\s+scapito\s+d(?:ei|elle)\s+(?:suoi\s+|vostri\s+)?client", re.IGNORECASE), "a scapito dei suoi clienti"),
)

NUM_RE = re.compile(r"\d[\d.,]*")


def _canon_num(tok):
    """Normalizza un token numerico (convenzione IT: '.'=migliaia, ','=decimale) → float o None."""
    s = tok.strip().strip(".,")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s:
        s = s.replace(".", "")  # solo migliaia (i decimali IT usano la virgola)
    try:
        return round(float(s), 3)
    except ValueError:
        return None


def _numbers_in(text):
    """Set di numeri canonici presenti in una stringa."""
    out = set()
    for m in NUM_RE.finditer(text):
        c = _canon_num(m.group(0))
        if c is not None:
            out.add(c)
    return out


def _brands_in(text):
    """Marche auto presenti (case-insensitive)."""
    low = text.lower()
    return {b for b in CAR_BRANDS_LOWER if re.search(r"\b" + re.escape(b) + r"\b", low)}


# ── estrazione fonti di verità ────────────────────────────────────────────────

def profile_numbers(profile):
    nums = set()
    sc = profile.get("stock_count")
    if isinstance(sc, (int, float)):
        nums.add(round(float(sc), 3))
    for ev in profile.get("example_vehicles") or []:
        for k in ("year", "price_eur"):
            v = ev.get(k)
            if isinstance(v, (int, float)):
                nums.add(round(float(v), 3))
    return nums


def profile_brands(profile):
    brands = set()
    for b in profile.get("top_brands") or []:
        if b and b.strip():
            brands.add(b.strip().lower())
    for ev in profile.get("example_vehicles") or []:
        mk = ev.get("make")
        if mk and mk.strip():
            brands.add(mk.strip().lower())
    for tm in profile.get("top_models") or []:
        if tm and tm.strip():
            first = tm.strip().split()[0].lower()
            if first in CAR_BRANDS_LOWER:
                brands.add(first)
    return brands


def kb_facts_from_lines(lines):
    """Ritorna lista di dict {numbers:set, tiers:set, text:str} per ogni FATTO valido."""
    facts = []
    for raw in lines:
        line = raw.rstrip("\n")
        if not FACT_RE.match(line):
            continue
        try:
            tags = parse_fact(line)
        except ValueError:
            continue
        text = (tags.get("FATTO", "") + " " + tags.get("NUMERO", ""))
        m = TIER_RE.search(line.rstrip())
        tiers = set(re.findall(r"T[123]", m.group(0))) if m else set()
        facts.append({"numbers": _numbers_in(text), "tiers": tiers, "text": line})
    return facts


def load_kb_lines(kb_dir):
    lines = []
    for path in sorted(glob.glob(os.path.join(kb_dir, "*.md"))):
        if os.path.basename(path) == "RUBRICA.md":
            continue
        with open(path, "r", encoding="utf-8") as fh:
            lines.extend(fh.readlines())
    return lines


# ── il gate ───────────────────────────────────────────────────────────────────

def validate_day1(message, profile, kb_lines):
    """Ritorna lista di violazioni (vuota = conforme). FUNZIONE PURA."""
    problems = []
    facts = kb_facts_from_lines(kb_lines)

    kb_numbers = set()
    num_tiers = {}
    kb_brand_pool = set()
    for f in facts:
        kb_brand_pool |= _brands_in(f["text"])
        for n in f["numbers"]:
            kb_numbers.add(n)
            num_tiers.setdefault(n, []).append(f["tiers"])
    # numero "solo-T3" = ogni FATTO che lo contiene è puramente [T3]
    t3_only = {n for n, tl in num_tiers.items() if tl and all(t == {"T3"} for t in tl)}

    pnums = profile_numbers(profile)
    pbrands = profile_brands(profile)
    allowed_numbers = pnums | kb_numbers

    low = message.lower()

    # (i-a) TRACCIABILITÀ NUMERI
    for m in NUM_RE.finditer(message):
        c = _canon_num(m.group(0))
        if c is None:
            continue
        if c not in allowed_numbers:
            problems.append(
                f"(i) claim orfano: numero '{m.group(0)}' non traccia né al profilo "
                f"(stock/veicoli) né a un FATTO KB → invenzione"
            )

    # (iv) FATTI [T3] SPACCIATI PER CERTI — a livello di FRASE:
    # una parola di certezza nella stessa frase di un numero che traccia SOLO a [T3].
    for sent in re.split(r"[.\n!?]+", message):
        slow = sent.lower()
        hit = next((w for w in CERTAINTY_WORDS if w in slow), None)
        if not hit:
            continue
        t3_hit = sorted(_numbers_in(sent) & t3_only)
        if t3_hit:
            problems.append(
                f"(iv) fatto [T3] spacciato per certo: numero {t3_hit} (fonte solo T3) "
                f"nella stessa frase di '{hit}' — usare 'circa/ordine di grandezza'"
            )

    # (i-b) TRACCIABILITÀ MARCHE (stock-claim → deve stare nel profilo)
    for b in CAR_BRANDS:
        for m in re.finditer(r"\b" + re.escape(b.lower()) + r"\b", low):
            a, z = max(0, m.start() - 30), m.end() + 30
            window = low[a:z]
            in_profile = b.lower() in pbrands
            in_kb = b.lower() in kb_brand_pool
            is_stock_claim = any(w in window for w in STOCK_CONTEXT)
            if is_stock_claim:
                if not in_profile:
                    problems.append(
                        f"(i) claim orfano: marca '{b}' presentata come stock del dealer "
                        f"ma NON in profile.top_brands ({profile.get('top_brands')}) → invenzione"
                    )
            elif not (in_profile or in_kb):
                problems.append(
                    f"(i) claim orfano: marca '{b}' non traccia a profilo né a KB"
                )
            break  # una violazione per marca è sufficiente

    # (ii) LESSICO VIETATO
    for rx, label in FORBIDDEN_LEXICON:
        if rx.search(message):
            problems.append(f"(ii) lessico vietato: '{label}' presente")

    # (v) PROVENIENZA ESTERA/IMPORT — termini diretti + perifrasi eufemistiche
    for rx, label in FORBIDDEN_PROVENANCE:
        if rx.search(message):
            problems.append(
                f"(v) provenienza estera/import vietata (Day-1): '{label}' presente"
            )

    # (vi) DIREZIONE-SERVIZIO — verifica km = ACQUISTI del dealer, MAI il suo stock;
    #      niente claim di danno ai suoi clienti (forme letterali; semantica → grader).
    for rx, label in FORBIDDEN_STOCK_TARGET:
        if rx.search(message):
            problems.append(
                f"(vi) direzione-servizio: verifica km riferita allo stock/auto-in-vendita "
                f"del destinatario ('{label}') — il gancio km riguarda SOLO gli acquisti del "
                f"dealer (permute/approvvigionamento/valutazioni), mai le sue auto in vendita"
            )
    for rx, label in FORBIDDEN_CLIENT_HARM:
        if rx.search(message):
            problems.append(
                f"(vi) direzione-servizio: claim di danno ai clienti del destinatario "
                f"('{label}') — vietato affermare o implicare danno ai suoi clienti"
            )

    # (iii) OPT-OUT + IDENTITÀ
    if not any(mk in low for mk in OPT_OUT_MARKERS):
        problems.append("(iii) opt-out assente: manca una via d'uscita esplicita ('no grazie'…)")
    if IDENTITY_TOKEN not in low:
        problems.append("(iii) firma/identità 'Azzurra' assente")

    return problems


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Gate anti-invenzione messaggio Day-1")
    ap.add_argument("--message", required=True, help="File di testo col messaggio Day-1")
    ap.add_argument("--profile", required=True, help="dealer_profile.json (da dealer_profile.py)")
    ap.add_argument("--kb-dir", default=os.path.join("kb", "dominio"),
                    help="Directory FATTI KB (default kb/dominio)")
    args = ap.parse_args()

    with open(args.message, "r", encoding="utf-8") as f:
        message = f.read()
    with open(args.profile, "r", encoding="utf-8") as f:
        profile = json.load(f)
    kb_lines = load_kb_lines(args.kb_dir)

    problems = validate_day1(message, profile, kb_lines)
    if problems:
        print(f"❌ validate_day1: FAIL — {len(problems)} violazione/i")
        for p in problems:
            print(f"   → {p}")
        return 1
    print("✅ validate_day1: OK — ogni claim tracciato, lessico pulito, opt-out+identità presenti")
    return 0


if __name__ == "__main__":
    sys.exit(main())
