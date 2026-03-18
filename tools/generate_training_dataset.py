#!/usr/bin/env python3.11
"""
ARGOS Automotive — Training Dataset Generator
=============================================
Genera conversazioni sintetiche dealer × archetipo × OBJ × context
usando Ollama qwen2.5:7b in locale su iMac.

Output: data/training/conversations_synthetic_v2.json (~265 conversazioni)

Run: python3.11 tools/generate_training_dataset.py
     nohup python3.11 tools/generate_training_dataset.py > /tmp/argos_gen.log 2>&1 &
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "training" / "conversations_synthetic_v2.json"
SLEEP_BETWEEN = 2  # secondi tra richieste

# ── Matrice di generazione ──────────────────────────────────────────────────

ARCHETYPES = {
    "RAGIONIERE": "un dealer italiano del Sud che pensa sempre in termini di ROI, IVA, struttura fiscale. Prima chiede i numeri, poi tutto il resto. Non si fida delle stime — vuole dati verificabili.",
    "BARONE": "un dealer italiano del Sud con forte senso del territorio e dello status. Risponde in modo difensivo ai contatti freddi, ha già 'i suoi fornitori', non ama gli intermediari. Risponde in modo corto e distaccato.",
    "PERFORMANTE": "un dealer italiano giovane, seconda generazione, vuole risultati rapidi e vantaggio competitivo. Dà deadline esplicite e non negoziabili. Se qualcosa non torna, chiude senza drammi.",
    "NARCISO": "un dealer italiano che punta tutto sull'immagine del suo showroom. Prima pensa a 'come appare' il veicolo, poi al prezzo. Teme di sembrare un rivenditore di import.",
    "TECNICO": "un dealer italiano preciso e rigoroso. Smonta subito terminologia imprecisa. Conosce DEKRA, TÜV, DAT Fahrzeughistorie. Vuole capire chi firma cosa e con quale responsabilità legale.",
    "RELAZIONALE": "un dealer italiano del Sud che lavora solo con persone che conosce. Non fa business con sconosciuti. Risponde in modo caloroso ma non si sbilancia. Vuole costruire un rapporto prima del business.",
    "CONSERVATORE": "un dealer italiano anziano che ha sempre fatto così e non vede motivo di cambiare. Risponde con resistenza al cambiamento. Ha paura del rischio. 'Ho sempre comprato in Italia dai miei fornitori.'",
    "DELEGATORE": "un dealer italiano che non decide mai da solo. Risponde con 'ne parlo con mio fratello/socio/commercialista'. Non è un rifiuto — è il suo modo di operare. Decide sempre con il suo team familiare.",
    "OPPORTUNISTA": "un dealer italiano che pensa solo al prezzo. Prima domanda: quanto costa? Chiede sconti immediatamente. Usa il volume come leva negoziale senza impegno reale.",
    "VISIONARIO": "un dealer italiano giovane che vuole essere il primo nella sua zona. Non gli interessa se lo fanno già tutti — anzi, se lo fanno già tutti non lo vuole. Cerca l'esclusività e il vantaggio competitivo."
}

OBJ_CODES = {
    "OBJ-1": "Ho già fornitori EU / non ho bisogno di altri canali",
    "OBJ-2": "Il prezzo/fee non mi convince / è troppo caro",
    "OBJ-3": "Non ho tempo / non è il momento giusto / ci penso",
    "OBJ-4": "Non capisco come funziona / voglio garanzie / rischio",
    "OBJ-5": "Devo sentire il socio/titolare/fratello — non decido da solo"
}

CONTEXTS = {
    "day1_cold": "Primo contatto WhatsApp. Il dealer non conosce ARGOS. Risponde al messaggio di presentazione.",
    "day1_objection": "Primo contatto WhatsApp. Il dealer risponde con una obiezione immediata.",
    "followup_interest": "Il dealer ha mostrato interesse ma non ha ancora deciso. Secondo contatto.",
    "objection_deep": "Il dealer fa un'obiezione specifica e profonda sul servizio, fee, o processo."
}

OVERLAPS = [
    ("RAGIONIERE", "CONSERVATORE", "Vuole i numeri ma ha paura di cambiare sistema"),
    ("BARONE", "DELEGATORE", "Ha status alto ma decide sempre col socio/famiglia"),
    ("PERFORMANTE", "VISIONARIO", "Vuole velocità E esclusività nella sua zona"),
    ("TECNICO", "RAGIONIERE", "Vuole documentazione precisa E ROI documentato"),
    ("NARCISO", "BARONE", "Vuole immagine premium E status territoriale"),
    ("RELAZIONALE", "CONSERVATORE", "Non ti conosce E non vuole rischiare"),
    ("OPPORTUNISTA", "DELEGATORE", "Chiede sconto ma deve sentire il socio")
]

# ── System prompt ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Sei un esperto di vendite B2B nel settore automotive italiano.
Generi conversazioni realistiche tra un agente di scouting veicoli EU (Luca Ferretti, ARGOS Automotive)
e concessionari italiani del Sud Italia (Campania, Puglia, Sicilia).

ARGOS Automotive:
- Scouting veicoli premium BMW/Mercedes/Audi dal mercato EU (Germania, Belgio, Olanda)
- Fee: €800-1.200 success-only (zero upfront)
- Nessun passaggio di proprietà attraverso ARGOS — dealer compra direttamente dal venditore EU
- Struttura fiscale: acquisto intracomunitario TD18, IVA recuperabile
- Documenti: DAT Fahrzeughistorie, Gutachten DEKRA/TÜV pre-partenza

REGOLE ASSOLUTE:
1. I messaggi WhatsApp sono BREVI: max 5-6 righe per messaggio
2. Il dealer risponde in modo realistico — non sempre cooperativo
3. Luca non menziona mai CoVe, Claude, Anthropic, AI, algoritmi
4. Il linguaggio è informale ma professionale (italiano Sud Italia)
5. Genera SOLO il JSON richiesto — nessun testo aggiuntivo

OUTPUT FORMAT (JSON puro, nessun markdown):
{
  "dealer_message": "messaggio realistico del dealer",
  "signals": ["segnale1", "segnale2"],
  "optimal_response": "risposta ottimale di Luca (max 6 righe WA)",
  "trap_response": "risposta sbagliata che Luca NON deve dare",
  "why_trap": "perché quella risposta è sbagliata per questo archetipo",
  "outcome_predicted": "PROCEED|PROCEED_SLOW|STALL|CONVERTED|NURTURE|CONDITIONAL"
}"""


def call_ollama(prompt: str, max_retries: int = 3) -> str | None:
    """Chiama Ollama API con retry."""
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 600
        }
    }).encode()

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data.get("response", "").strip()
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)

    return None


def build_prompt(archetype: str, archetype_desc: str, obj_code: str, obj_desc: str,
                 context: str, context_desc: str,
                 secondary: str = None, overlap_desc: str = None) -> str:
    """Costruisce il prompt per Ollama."""

    if secondary:
        archetype_section = f"""ARCHETIPO PRIMARIO: {archetype}
{archetype_desc}

ARCHETIPO SECONDARIO: {secondary}
{ARCHETYPES[secondary]}

OVERLAP: {overlap_desc}
Il dealer mostra ENTRAMBI i comportamenti in modo credibile."""
    else:
        archetype_section = f"""ARCHETIPO: {archetype}
{archetype_desc}"""

    return f"""{archetype_section}

OBIEZIONE ATTIVA: {obj_code} — {obj_desc}
CONTESTO: {context_desc}

Genera UNA conversazione realistica. Il dealer fa questa obiezione specifica.
Luca risponde in modo calibrato per questo archetipo.

Rispondi SOLO con il JSON, nessuna spiegazione."""


def parse_json_response(raw: str) -> dict | None:
    """Estrae JSON dalla risposta Ollama."""
    if not raw:
        return None

    # Cerca il JSON nell'output
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        return None

    try:
        return json.loads(raw[start:end])
    except json.JSONDecodeError:
        # Prova a riparare JSON troncato
        try:
            chunk = raw[start:end]
            # Chiudi stringhe aperte
            if chunk.count('"') % 2 != 0:
                chunk += '"'
            chunk += "}"
            return json.loads(chunk)
        except Exception:
            return None


def generate_dataset():
    """Genera l'intero dataset e salva su file."""
    conversations = []
    conv_id = 200  # Parte da 200 per non sovrascrivere v1

    total_planned = (len(ARCHETYPES) * len(OBJ_CODES) * len(CONTEXTS)) + \
                    (len(OVERLAPS) * len(OBJ_CODES) * 3)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Inizio generazione dataset")
    print(f"Target: ~{total_planned} conversazioni | Modello: {MODEL}")
    print(f"Output: {OUTPUT_FILE}\n")

    # ── FASE 1: Archetipi puri ────────────────────────────────────────────
    print("=== FASE 1: Archetipi puri ===")
    for arch_name, arch_desc in ARCHETYPES.items():
        for obj_code, obj_desc in OBJ_CODES.items():
            for ctx_name, ctx_desc in CONTEXTS.items():
                conv_id += 1
                label = f"{arch_name[:4]}-{obj_code}-{ctx_name[:4]}-{conv_id}"
                print(f"  [{conv_id:03d}/{total_planned}] {label} ... ", end="", flush=True)

                prompt = build_prompt(arch_name, arch_desc, obj_code, obj_desc, ctx_name, ctx_desc)
                raw = call_ollama(prompt)
                parsed = parse_json_response(raw)

                if parsed:
                    conv = {
                        "id": label,
                        "primary_archetype": arch_name,
                        "secondary_archetype": None,
                        "context": ctx_name,
                        "obj_triggered": obj_code,
                        **parsed
                    }
                    conversations.append(conv)
                    print(f"OK → {parsed.get('outcome_predicted', '?')}")
                else:
                    print("SKIP (parse error)")

                time.sleep(SLEEP_BETWEEN)

    # ── FASE 2: Overlap ───────────────────────────────────────────────────
    print("\n=== FASE 2: Overlap ===")
    overlap_contexts = list(CONTEXTS.items())[:3]  # Day1 + followup + objection

    for primary, secondary, overlap_desc in OVERLAPS:
        for obj_code, obj_desc in OBJ_CODES.items():
            for ctx_name, ctx_desc in overlap_contexts:
                conv_id += 1
                label = f"{primary[:4]}-{secondary[:4]}-{obj_code}-{conv_id}"
                print(f"  [{conv_id:03d}/{total_planned}] {label} ... ", end="", flush=True)

                prompt = build_prompt(primary, ARCHETYPES[primary], obj_code, obj_desc,
                                      ctx_name, ctx_desc, secondary, overlap_desc)
                raw = call_ollama(prompt)
                parsed = parse_json_response(raw)

                if parsed:
                    conv = {
                        "id": label,
                        "primary_archetype": primary,
                        "secondary_archetype": secondary,
                        "overlap_desc": overlap_desc,
                        "context": ctx_name,
                        "obj_triggered": obj_code,
                        **parsed
                    }
                    conversations.append(conv)
                    print(f"OK → {parsed.get('outcome_predicted', '?')}")
                else:
                    print("SKIP (parse error)")

                time.sleep(SLEEP_BETWEEN)

    # ── Salva output ──────────────────────────────────────────────────────
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "version": "2.0",
        "generated": datetime.now().isoformat(),
        "model": MODEL,
        "total_conversations": len(conversations),
        "conversations": conversations
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] COMPLETATO")
    print(f"Conversazioni generate: {len(conversations)}/{total_planned}")
    print(f"File: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_dataset()
