#!/usr/bin/env python3
"""
state_guard.py — PreToolUse hook (Gate A/B/C). Protegge il substrato di stato ARGOS
dalla *scrittura manuale di Claude Code* (Write/Edit). NON tocca Bash.

Threat-model: sbadataggine di CC (riscrivere a mano una verita' GENERATA), non evasione
attiva. Quindi: applica a Write/Edit/MultiEdit; il generatore legittimo (state/refresh.py
invocato via Bash) scrive STATE.md/rings.json fuori dal raggio di questo hook -> nessun
conflitto. La protezione Bash-level e' fuori scope (la romperebbe refresh.py stesso).

Gate A — STATE.md: rifiuta ogni edit che ALTERI il blocco tra i marker
         <!-- GENERATED:rings:start --> / :end -->. Il resto del file resta editabile.
Gate B — state/rings.json: rifiuta edit CC ai campi machine-owned
         (last_status / last_run_ts / last_run_session) e ai campi founder-frozen
         (blocked_on / revalidation_forbidden quando revalidation_forbidden=true = Gate D).
         I campi config (name/check_cmd/tier/note) restano editabili.
Gate C — guard + generatori (questo file, refresh.py, refresh.sh): rifiuta edit.
         Escape deliberato: env ARGOS_HARNESS_UNLOCK=1 (manutenzione voluta da Luke).

Output deny (contratto CC moderno):
  {"hookSpecificOutput": {"hookEventName": "PreToolUse",
   "permissionDecision": "deny", "permissionDecisionReason": "..."}}
exit 0 sempre (deny via payload, non via exit code). Allow = nessun payload.

Fail-open sugli errori INTERNI dell'hook (un bug del guard non deve brickare l'editing):
le violazioni chiare denegano, gli imprevisti lasciano passare con nota su stderr.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE_MD = os.path.realpath(os.path.join(ROOT, "STATE.md"))
RINGS_JSON = os.path.realpath(os.path.join(ROOT, "state", "rings.json"))
SELF = os.path.realpath(os.path.join(HERE, "state_guard.py"))
REFRESH_PY = os.path.realpath(os.path.join(ROOT, "state", "refresh.py"))
REFRESH_SH = os.path.realpath(os.path.join(ROOT, "state", "refresh.sh"))
PROTECTED_FILES = {SELF, REFRESH_PY, REFRESH_SH}

MARK_START = "<!-- GENERATED:rings:start -->"
MARK_END = "<!-- GENERATED:rings:end -->"

MACHINE_FIELDS = ("last_status", "last_run_ts", "last_run_session")
FROZEN_FIELDS = ("blocked_on", "revalidation_forbidden")


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def allow():
    sys.exit(0)


def real(path):
    if not path:
        return ""
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    return os.path.realpath(p)


def gen_block(content):
    """Estrae il blocco GENERATED (marker inclusi) o None se i marker mancano."""
    s = content.find(MARK_START)
    e = content.find(MARK_END)
    if s == -1 or e == -1 or e < s:
        return None
    return content[s:e + len(MARK_END)]


def apply_edit(content, old, new, replace_all):
    """Calcola il contenuto risultante di un Edit. None se old non e' presente
    (l'Edit fallirebbe comunque lato CC -> lasciamo passare)."""
    if old is None or old == "" or old not in content:
        return None
    if replace_all:
        return content.replace(old, new if new is not None else "")
    return content.replace(old, new if new is not None else "", 1)


def proposed_content(tool_name, tool_input, current):
    """Contenuto risultante dopo l'operazione, o None se non calcolabile/non applicabile."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name in ("Edit", "MultiEdit"):
        if tool_name == "MultiEdit":
            c = current
            for ed in tool_input.get("edits", []):
                r = apply_edit(c, ed.get("old_string"), ed.get("new_string"),
                               ed.get("replace_all", False))
                if r is None:
                    return None
                c = r
            return c
        return apply_edit(current, tool_input.get("old_string"),
                          tool_input.get("new_string"),
                          tool_input.get("replace_all", False))
    return None


def gate_a(tool_name, tool_input):
    """STATE.md: il blocco GENERATED deve restare invariato."""
    try:
        current = open(STATE_MD, encoding="utf-8").read()
    except OSError:
        return  # STATE.md assente -> niente da proteggere
    prop = proposed_content(tool_name, tool_input, current)
    if prop is None:
        return  # non calcolabile -> fail-open
    cur_block = gen_block(current)
    new_block = gen_block(prop)
    if cur_block is None:
        return  # stato gia' anomalo, non e' compito di questo gate
    if new_block is None:
        deny("Gate A: questo edit rimuove/spezza i marker "
             "<!-- GENERATED:rings --> in STATE.md. La tabella anelli e' GENERATA "
             "da `bash state/refresh.sh`, non scrivibile a mano. Modifica le sezioni "
             "FUORI dal blocco, oppure rigenera con refresh.sh.")
    if new_block != cur_block:
        deny("Gate A: questo edit altera il blocco GENERATED:rings in STATE.md. "
             "'VERIFIED' = check passato in sessione, non testo digitato. "
             "Per cambiare la tabella esegui `bash state/refresh.sh <SESSION_ID>`; "
             "le sezioni narrative fuori dal blocco restano editabili.")


def result_fields(rings):
    """Mappa id -> (machine_fields..., frozen_fields...) per confronto."""
    out = {}
    for r in rings:
        rid = str(r.get("id"))
        out[rid] = {f: r.get(f) for f in (MACHINE_FIELDS + FROZEN_FIELDS)}
        out[rid]["_was_frozen"] = bool(r.get("revalidation_forbidden"))
    return out


def gate_b(tool_name, tool_input):
    """rings.json: campi machine-owned e founder-frozen non editabili da CC."""
    try:
        current = open(RINGS_JSON, encoding="utf-8").read()
    except OSError:
        return
    prop = proposed_content(tool_name, tool_input, current)
    if prop is None:
        return
    try:
        cur = json.loads(current)
        new = json.loads(prop)
    except (json.JSONDecodeError, ValueError):
        deny("Gate B: la modifica produce rings.json NON valido come JSON. "
             "rings.json e' la sorgente dati del substrato: deve restare JSON valido.")
        return
    cf = result_fields(cur)
    nf = result_fields(new)
    for rid, cvals in cf.items():
        nvals = nf.get(rid)
        if nvals is None:
            continue  # ring rimosso: gestione altrove, non e' questo gate
        for f in MACHINE_FIELDS:
            if cvals.get(f) != nvals.get(f):
                deny(f"Gate B: tentativo di scrivere a mano il campo machine-owned "
                     f"'{f}' dell'anello {rid} in rings.json. Lo status e' CALCOLATO da "
                     f"refresh.py eseguendo il check, non digitabile. "
                     f"Esegui `bash state/refresh.sh <SESSION_ID>`. "
                     f"I campi config (name/check_cmd/tier/note) restano editabili.")
        if cvals.get("_was_frozen"):
            for f in FROZEN_FIELDS:
                if cvals.get(f) != nvals.get(f):
                    deny(f"Gate D (via Gate B): l'anello {rid} e' founder-frozen "
                         f"(revalidation_forbidden=true). Il campo '{f}' non puo' essere "
                         f"cambiato da CC: lo sblocco e' una decisione di Luke (fatto "
                         f"esterno). Se Luke sblocca, editare rings.json con "
                         f"ARGOS_HARNESS_UNLOCK=1.")


def gate_c(tool_input):
    """Guard + generatori: non editabili da CC senza unlock esplicito."""
    if os.environ.get("ARGOS_HARNESS_UNLOCK") == "1":
        return
    tgt = real(tool_input.get("file_path"))
    if tgt in PROTECTED_FILES:
        deny("Gate C: stai per modificare un file-guard/generatore "
             f"({os.path.relpath(tgt, ROOT)}). E' la protezione che impedisce di "
             "falsificare lo stato: non auto-disabilitarla. Per manutenzione "
             "deliberata, Luke rilancia CC con ARGOS_HARNESS_UNLOCK=1.")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        allow()
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        allow()

    tgt = real(tool_input.get("file_path"))

    try:
        gate_c(tool_input)            # self-protection per primo
        if tgt == STATE_MD:
            gate_a(tool_name, tool_input)
        elif tgt == RINGS_JSON:
            gate_b(tool_name, tool_input)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — fail-open su bug interni del guard
        print(f"state_guard: errore interno, fail-open: {exc}", file=sys.stderr)
    allow()


if __name__ == "__main__":
    main()
