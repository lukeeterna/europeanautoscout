#!/usr/bin/env python3
"""
validate_kb.py — gate deterministico di FORMATO per i fatti in kb/dominio/*.md.

Applica lo standard di kb/dominio/RUBRICA.md. NON verifica la verità delle fonti:
controlla solo che ogni fatto abbia FONTE citabile + DATA ISO + NUMERO con cifra +
VERIFICA azionabile, e rigetta i pattern spazzatura. RUBRICA.md è escluso.

Uso:
  python3 validate_kb.py                 # scansiona kb/dominio/*.md
  python3 validate_kb.py file1 file2 ... # valida solo i file passati (per pre-commit)

Exit-code: 0 = tutto conforme (anche "nessun fatto"); 1 = almeno una violazione.
Stdlib only. Compatibile python3.11+.
"""
import sys
import os
import re
import glob
from datetime import datetime

KB_DOMINIO = os.path.join("kb", "dominio")
RUBRICA_NAME = "RUBRICA.md"

REQUIRED_TAGS = ("FONTE", "DATA", "NUMERO", "VERIFICA")

# --- pattern spazzatura -------------------------------------------------------
SOURCE_GARBAGE = (
    "reddit", "facebook", "instagram", "twitter", "x.com", "tiktok", "forum",
    "quora", "whatsapp", "telegram", "un amico", "gruppo", "sentito", "si dice",
    "dicono", "tizio", "403", "404", "link morto", "pagina vuota",
    "pagina non disponibile", "n/a", "tbd", "todo",
)
CITATION_MARKERS = (
    "art.", "art ", "reg.", "reg ", "direttiva", "d.lgs", "d.m", "decreto",
    "comma", "§", "iso", " en ", "uni", "cds", "sentenza", "report", "rapporto",
    "studio", "bollettino", "gazzetta",
)
VERIFY_VERBS = (
    "controlla", "verifica", "confronta", "richiedi", "calcola", "ricalcola",
    "cerca", "consulta", "interroga", "incrocia", "confrontando",
)
VERIFY_VAGUE = ("fidati", "ovvio", "tutti sanno", "è così", "e' cosi")
SOURCE_EMPTY = ("", "?", "-", "--")

URL_RE = re.compile(r"https?://", re.IGNORECASE)
DIGIT_RE = re.compile(r"[0-9]")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
ALPHA_RE = re.compile(r"[A-Za-zÀ-ÿ]")
FACT_RE = re.compile(r"^\s*(?:-\s+)?FATTO:", re.IGNORECASE)


def _has(substrings, text):
    low = text.lower()
    return any(s in low for s in substrings)


def _source_ok(val):
    if val.strip().lower() in SOURCE_EMPTY or not val.strip():
        return False, "FONTE vuota (no-fonte)"
    if _has(SOURCE_GARBAGE, val):
        return False, "FONTE spazzatura (social/forum/sentito-dire/403/vuota)"
    if URL_RE.search(val):
        return True, ""
    if _has(CITATION_MARKERS, val):
        return True, ""
    if YEAR_RE.search(val) and len(ALPHA_RE.findall(val)) >= 6:
        return True, ""
    return False, "FONTE non citabile (manca url / marcatore / anno+nome)"


def _date_ok(val):
    v = val.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return False, "DATA non in formato YYYY-MM-DD (no-data/vago)"
    try:
        datetime.strptime(v, "%Y-%m-%d")
    except ValueError:
        return False, "DATA impossibile"
    return True, ""


def _numero_ok(val):
    if not val.strip():
        return False, "NUMERO vuoto (vago)"
    if not DIGIT_RE.search(val):
        return False, "NUMERO senza cifra: meccanismo non quantificato (vago)"
    return True, ""


def _verifica_ok(val):
    if not val.strip():
        return False, "VERIFICA vuota (plausibile-non-verificabile)"
    if _has(VERIFY_VAGUE, val):
        return False, "VERIFICA vaga (fidati/ovvio/tutti-sanno)"
    if URL_RE.search(val) or _has(VERIFY_VERBS, val):
        return True, ""
    return False, "VERIFICA senza metodo azionabile (plausibile-non-verificabile)"


FIELD_CHECKS = {
    "FONTE": _source_ok,
    "DATA": _date_ok,
    "NUMERO": _numero_ok,
    "VERIFICA": _verifica_ok,
}


def parse_fact(line):
    """Ritorna dict tag->valore per una riga FATTO:. Solleva ValueError se malformata."""
    body = re.sub(r"^\s*(?:-\s+)?", "", line).rstrip("\n")
    segments = [s.strip() for s in body.split("|")]
    tags = {}
    for seg in segments:
        m = re.match(r"^([A-Za-zÀ-ÿ]+)\s*:\s*(.*)$", seg)
        if not m:
            raise ValueError(f"segmento senza tag 'CHIAVE: valore': '{seg}'")
        tags[m.group(1).upper()] = m.group(2)
    if "FATTO" not in tags:
        raise ValueError("manca il tag FATTO:")
    return tags


def validate_fact(line):
    """Ritorna lista di violazioni (vuota = ok)."""
    problems = []
    try:
        tags = parse_fact(line)
    except ValueError as e:
        return [str(e)]
    if not tags.get("FATTO", "").strip():
        problems.append("claim FATTO vuoto")
    for tag in REQUIRED_TAGS:
        if tag not in tags:
            problems.append(f"tag mancante: {tag}")
            continue
        ok, msg = FIELD_CHECKS[tag](tags[tag])
        if not ok:
            problems.append(msg)
    return problems


def validate_file(path):
    """Ritorna (n_fatti, lista_violazioni[(lineno, testo, [msg])])."""
    violations = []
    n_facts = 0
    in_comment = False
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            stripped = line.strip()
            if in_comment:
                if "-->" in stripped:
                    in_comment = False
                continue
            if not stripped:
                continue
            if stripped.startswith("<!--"):
                if "-->" not in stripped:
                    in_comment = True
                continue
            if stripped.startswith("#") or stripped.startswith(">"):
                continue
            if FACT_RE.match(line):
                n_facts += 1
                probs = validate_fact(line)
                if probs:
                    violations.append((lineno, stripped, probs))
                continue
            # riga non classificabile = contenuto non strutturato
            violations.append(
                (lineno, stripped,
                 ["riga non conforme: usa 'FATTO: ...' oppure header/nota/commento"])
            )
    return n_facts, violations


def target_files(argv):
    if argv:
        out = []
        for p in argv:
            norm = os.path.normpath(p)
            if not norm.endswith(".md"):
                continue
            if os.path.basename(norm) == RUBRICA_NAME:
                continue
            if os.sep + "dominio" + os.sep not in os.sep + norm + os.sep and \
               not norm.startswith(KB_DOMINIO):
                continue
            if os.path.isfile(norm):
                out.append(norm)
        return out
    files = sorted(glob.glob(os.path.join(KB_DOMINIO, "*.md")))
    return [f for f in files if os.path.basename(f) != RUBRICA_NAME]


def main():
    files = target_files(sys.argv[1:])
    if not files:
        print("validate_kb: nessun file kb/dominio/*.md da controllare — OK")
        return 0
    total_facts = 0
    total_viol = 0
    for path in files:
        n_facts, violations = validate_file(path)
        total_facts += n_facts
        if violations:
            total_viol += len(violations)
            print(f"❌ {path}: {len(violations)} violazione/i")
            for lineno, text, probs in violations:
                print(f"   L{lineno}: {text}")
                for p in probs:
                    print(f"        → {p}")
        else:
            state = f"{n_facts} fatto/i conforme/i" if n_facts else "nessun fatto (stub)"
            print(f"✅ {path}: {state}")
    print("---")
    if total_viol:
        print(f"validate_kb: FAIL — {total_viol} violazione/i su {len(files)} file")
        return 1
    if total_facts == 0:
        print(f"validate_kb: OK — nessun fatto negli {len(files)} file (stub vuoti)")
    else:
        print(f"validate_kb: OK — {total_facts} fatto/i conforme/i su {len(files)} file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
