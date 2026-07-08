#!/usr/bin/env python3
"""
generate_day1.py — generatore GROUNDED del messaggio Day-1 per un dealer SELECTED.

Compone il PRIMO messaggio WhatsApp (forma libera, breve) partendo da:
  - un profilo dealer JSON (es. data/pool_icp/SELECTED.json)  → marche/stock REALI
  - i FATTI KB taggati in kb/dominio/*.md                      → statistiche di dominio

Pipeline cablata (mai bypassabile):
    genera (LLM) → validate_day1.validate_day1() → se viola, rigenera passando
    le violazioni nominate al prompt → max 3 tentativi → se ancora KO: STOP+report.
Il messaggio che passa il gate NON viene mai editato a mano per farlo passare.

Vincolo G-NOAPI-AI: generazione via runtime AMBRA (src/llm_cascade.py, provider
GROQ preferito). NESSUNA API Anthropic. La cascata non contiene provider Anthropic.

Uso:
  python3 tools/generate_day1.py --profile data/pool_icp/SELECTED.json \
      --out data/day1/visauto_treviso_day1.txt [--kb-dir kb/dominio] [--max-tries 3]
Exit-code: 0 = messaggio conforme salvato; 1 = gate non superato dopo N tentativi.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from validate_day1 import (  # noqa: E402
    validate_day1, load_kb_lines, kb_facts_from_lines,
    profile_brands, profile_numbers,
)
import llm_cascade as L  # noqa: E402


# ── grounding: fatti KB in forma leggibile per il prompt ──────────────────────

def kb_grounding_block(kb_lines):
    """Rende i FATTI KB (FATTO+NUMERO+tier) come elenco compatto per il prompt."""
    facts = kb_facts_from_lines(kb_lines)
    out = []
    for f in facts:
        line = f["text"]
        # estrai FATTO: ... e NUMERO: ... in forma breve
        mfat = re.search(r"FATTO:\s*(.+?)\s*\|", line)
        mnum = re.search(r"NUMERO:\s*(.+?)\s*\|", line)
        tier = "/".join(sorted(f["tiers"])) or "?"
        claim = (mfat.group(1) if mfat else line)[:180]
        num = (mnum.group(1) if mnum else "")[:80]
        out.append(f"- [{tier}] {claim} (NUMERO: {num})")
    return "\n".join(out)


# ── prompt builder ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sei Azzurra, assistente di Luca Ferretti — ARGOS Automotive.
Componi il PRIMO messaggio WhatsApp a un concessionario auto italiano. Obiettivo:
credibilita' + competenza, breve (max ~5 righe), tono professionale e diretto.
Chiudi con UNA domanda chiusa (risposta si'/no).

REGOLE INVIOLABILI (il messaggio viene passato a un validatore automatico):
1. IDENTITA': il testo DEVE contenere il nome "Azzurra" e dichiararti "assistente di
   Luca Ferretti". Non firmarti come Luca in prima persona.
2. OPT-OUT: includi una via d'uscita con le parole ESATTE "no grazie"
   (es.: un "no grazie" e non la disturbo piu').
3. MARCHE: puoi citare come stock del concessionario SOLO le sue marche reali, che ti
   verranno date. NON inventare altre marche.
4. NUMERI: NON scrivere alcuna cifra, percentuale, prezzo, anno o numero di telefono,
   con UNA SOLA eccezione: puoi dire "circa 3 volte" riferito al maggior rischio di km
   non veritieri sulle auto che arrivano da fuori mercato italiano (dato di ordine di
   grandezza, fonte commerciale). Nessun altro numero.
5. VIETATE le parole: "garanzia", "garantito", "certificato costruttore", "assicuriamo".
   Non promettere alcuna garanzia.
6. Le statistiche sono ORDINE DI GRANDEZZA (fonte commerciale): NON usare parole di
   certezza come "certificato", "dimostrato", "provato", "certo".
7. NON usare le parole "Germania", "import", "importate", "estero", "premium",
   "cerco auto". Se serve, di' "auto che arrivano da fuori mercato italiano".
8. Nessun prezzo, nessuna offerta economica: questo e' solo il primo contatto.

Rispondi SOLO col testo del messaggio, senza virgolette, senza intestazioni, senza note.
"""


def build_user_message(profile, kb_block, prev_msg=None, violations=None):
    company = profile.get("company_name") or profile.get("name") or "il concessionario"
    tier_hits = ((profile.get("_icp") or {}).get("tier_hits")) or []
    brands = sorted({b.title() for b in profile_brands(profile)})
    focus = ", ".join(tier_hits) if tier_hits else ", ".join(brands[:3])

    parts = [
        f"CONCESSIONARIO: {company}",
        f"MARCHE REALI (le UNICHE citabili come suo stock): {', '.join(brands)}",
        f"MARCHE DI RILIEVO da valorizzare: {focus}",
        "",
        "FATTI KB DI DOMINIO (grounding statistico; [T3]=commerciale=ordine di grandezza):",
        kb_block,
        "",
        "Componi ora il messaggio Day-1 rispettando TUTTE le regole inviolabili.",
    ]
    if prev_msg is not None and violations:
        parts += [
            "",
            "IL TUO TENTATIVO PRECEDENTE E' STATO RIFIUTATO dal validatore.",
            "Messaggio precedente:",
            prev_msg,
            "",
            "Violazioni da correggere (NON reintrodurle):",
            *[f"- {v}" for v in violations],
            "",
            "Riscrivi il messaggio da capo eliminando queste violazioni.",
        ]
    return "\n".join(parts)


def _clean(text):
    t = text.strip()
    # rimuove eventuali virgolette/backtick di wrapping
    if len(t) >= 2 and t[0] in "\"'`" and t[-1] in "\"'`":
        t = t[1:-1].strip()
    return t


# ── generazione via GROQ (runtime AMBRA), con fallback cascata non-Anthropic ──

def generate_once(system_prompt, user_message, max_tokens=400):
    """Prova GROQ diretto; se KO, usa la cascata AMBRA (comunque zero-Anthropic)."""
    providers = L._build_providers()
    groq = next((p for p in providers if p["id"] == "groq"), None)
    if groq and groq.get("key"):
        try:
            r = L._call_provider(groq, system_prompt, user_message, max_tokens)
            return _clean(r["text"]), r["provider"]
        except Exception as e:  # noqa: BLE001 — fallback esplicito alla cascata
            sys.stderr.write(f"[generate_day1] GROQ KO ({e}); fallback cascata AMBRA\n")
    r = L.get_cascade().chat(system_prompt, user_message, max_tokens=max_tokens)
    return _clean(r["text"]), r["provider"]


# ── pipeline ──────────────────────────────────────────────────────────────────

def run(profile_path, out_path, kb_dir, max_tries):
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    kb_lines = load_kb_lines(kb_dir)
    kb_block = kb_grounding_block(kb_lines)

    attempts = []          # (msg, provider, violations)
    prev_msg = None
    prev_viol = None
    for i in range(1, max_tries + 1):
        user_msg = build_user_message(profile, kb_block, prev_msg, prev_viol)
        try:
            msg, provider = generate_once(SYSTEM_PROMPT, user_msg)
        except L.AllProvidersDown as e:
            print("\n⛔ BLOCKED-ON: runtime AMBRA non disponibile (nessun provider "
                  "non-Anthropic raggiungibile). Nessun messaggio generato/salvato.",
                  file=sys.stderr)
            print(f"   dettaglio: {e}", file=sys.stderr)
            return 2
        violations = validate_day1(msg, profile, kb_lines)
        attempts.append((msg, provider, violations))
        print(f"── tentativo {i}/{max_tries} — provider={provider} — "
              f"violazioni={len(violations)}", file=sys.stderr)
        for v in violations:
            print(f"     · {v}", file=sys.stderr)
        if not violations:
            _save_success(out_path, msg, provider, i, profile_path)
            return 0
        prev_msg, prev_viol = msg, violations

    _report_failure(out_path, attempts)
    return 1


def _report_success_text(msg, provider, tries, profile_path):
    return (
        "✅ validate_day1: OK — messaggio conforme (gate exit 0)\n"
        f"provider    : {provider}\n"
        f"tentativi   : {tries}\n"
        f"profilo     : {profile_path}\n"
        "claim: ogni numero/marca tracciato al profilo o ai FATTI KB; "
        "lessico pulito; opt-out + identita' 'Azzurra' presenti.\n"
    )


def _save_success(out_path, msg, provider, tries, profile_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(msg.rstrip() + "\n")
    report_path = out_path.rsplit(".", 1)[0] + ".gate.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(_report_success_text(msg, provider, tries, profile_path))
    print(f"\n✅ SALVATO: {out_path}")
    print(f"✅ REPORT : {report_path}")
    print(f"   provider={provider} tentativi={tries}")
    print("\n──────── MESSAGGIO VERBATIM ────────")
    print(msg)
    print("────────────────────────────────────")


def _report_failure(out_path, attempts):
    report_path = out_path.rsplit(".", 1)[0] + ".FAILED.txt"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    lines = ["❌ validate_day1: FAIL dopo tutti i tentativi — nessun salvataggio del msg.\n"]
    for i, (msg, provider, viol) in enumerate(attempts, 1):
        lines.append(f"─── tentativo {i} (provider={provider}) ───")
        lines.append(msg)
        lines.append(f"violazioni ({len(viol)}):")
        lines += [f"  → {v}" for v in viol]
        lines.append("")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n❌ GATE NON SUPERATO dopo tutti i tentativi. Nessun messaggio salvato.")
    print(f"❌ REPORT: {report_path}")
    for i, (_, provider, viol) in enumerate(attempts, 1):
        print(f"   tentativo {i} (provider={provider}): {len(viol)} violazioni")


def main():
    ap = argparse.ArgumentParser(description="Generatore grounded Day-1 (gate-cablato)")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kb-dir", default=os.path.join("kb", "dominio"))
    ap.add_argument("--max-tries", type=int, default=3)
    args = ap.parse_args()
    return run(args.profile, args.out, args.kb_dir, args.max_tries)


if __name__ == "__main__":
    sys.exit(main())
