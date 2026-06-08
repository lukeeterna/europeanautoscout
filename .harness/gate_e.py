#!/usr/bin/env python3
"""
gate_e.py — PreToolUse hook (Gate E). Circuit-breaker su una CLASSE di azioni
high-stakes/irreversibili. Complementa state_guard.py (Gate A/B/C/D): quello protegge
il *substrato di stato* da Write/Edit; Gate E intercetta anche **Bash** e blocca le
azioni che hanno conseguenze reali fuori dal repo o che disattivano i guardrail.

Verdetto Claude AI S242 §4 Gate E (sequenza step 9): per una classe di azioni
irreversibili un hook BLOCCA, scrive `pending_review/<slug>.md` (packet precompilato),
e CC non procede finche' Luke non incolla un verdetto esterno e un comando registra
l'approvazione. "Non decade perche' lo applica l'harness."

Threat-model: SBADATAGGINE di CC (eseguire testo-decisione sopra la realta', come
l'incidente NEXT_SESSION_PROMPT S241), NON evasione attiva. Quindi il matching su Bash
e' euristico best-effort (Rule 1d: "matching euristico sui vettori nominati e'
sufficiente"). La forcing-function load-bearing e' l'interruzione + il packet, non un
lock crittografico.

RAFFINAMENTO S248 (verdetto Claude AI S247): il gate scatta SOLO sugli OPERANDI reali
di un'operazione lossy (target di una redirezione `>`/`>>` su file; argomenti di
mv/cp/rm/sed -i/tee/truncate/chmod quando il verbo e' in posizione di comando), MAI
sul testo incidentale (nome dello script ESEGUITO, body di un commit-message `-m "..."`,
fd-dup `2>&1`). Il match sulla prosa era un errore di categoria (FP illimitati, zero
veri-positivi extra): ha bloccato 2 volte il commit S247 e l'avvio di S248
(`bash state/refresh.sh ... 2>&1`). Inoltre `*.db` e' ristretto al DB source-of-truth
(non piu' "qualunque .db sotto ROOT", che becca i DB-spazzatura del profilo Chrome).
Escape manutenzione: env ARGOS_HARNESS_UNLOCK=1 (come state_guard.gate_c).

GAP NOTI over-narrow (accettati — threat=sbadataggine di CC, NON evasione attiva; Rule 1d):
il "verbo in posizione di comando" NON intercetta `sudo rm X`, `dd of=X`, ne' un redirect
con path da variabile (`> "$VAR"`). L'env-prefix (`A=1 rm X`) E' gestito (saltiamo le
assegnazioni iniziali). Scritti qui come limite noto, non da scoprire in produzione.
NB il narrowing e' SHELL-scoped: i path di scrittura non-shell (Write tool, `python -c`, MCP)
restano fuori da classify_bash — invariato vs prima (tracciato in coverage-check #2).

CLASSI rilevate:
  - outreach_real   : Bash che invia WA a un numero != TEST_FOUNDER (393314928901).
                      Match volutamente BROAD (classe piu' critica: meglio un FP che
                      chiede approvazione di un FN che lascia partire un invio reale).
  - archive_doc     : Bash che archivia/rimuove doc tracciati (git mv/mv -> archive/, git rm/rm .md).
  - overwrite_sot   : Write/Edit/Bash-lossy su un source-of-truth canonico (CLAUDE.md,
                      MEMORY.md, DECISIONS.md, PLAN.md, DB SoT) — Rule 1d strutturale.
                      STATE.md/rings.json: il loro contenuto e' coperto da state_guard su
                      Write/Edit; qui blocco solo i Bash-lossy sul loro path (gap shell di
                      state_guard, es. `sed -i STATE.md` = flip-VERIFIED via shell).
  - disable_hook    : Write/Edit/Bash-lossy che tocca settings.json (sezione hooks), gli
                      hook globali (~/.claude/hooks/), o i file-harness (state_guard.py,
                      gate_e.py, refresh.*). [flip-VERIFIED editando il blocco GENERATED
                      via Write/Edit resta coperto da Gate A.]

Contratto deny (come state_guard): payload permissionDecision=deny, exit 0.
Allow = nessun payload, exit 0. Fail-open su bug INTERNI dell'hook.

CLI (per Luke, NON per CC):
  python3 .harness/gate_e.py approve <slug> [--verdict "testo"]  -> registra il token
  python3 .harness/gate_e.py list                                -> packet pendenti
  python3 .harness/gate_e.py selftest                            -> smoke interno
"""
import hashlib
import json
import os
import re
import shlex
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOME = os.path.expanduser("~")

PENDING_DIR = os.path.join(HERE, "pending_review")
AUDIT = os.path.join(PENDING_DIR, "gate_e_audit.jsonl")

TEST_FOUNDER = {"393314928901", "3314928901"}

# --- source-of-truth canonici (Rule 1d whitelist) ---------------------------------
SOT_REALPATHS = {
    os.path.realpath(os.path.join(HOME, ".claude", "CLAUDE.md")),
    os.path.realpath(os.path.join(ROOT, "CLAUDE.md")),
    os.path.realpath(os.path.join(ROOT, "PLAN.md")),
}
# Pattern path (basename) valutati con vincolo di directory (memory/ o wiki/projects/)
SOT_BASENAMES = {"CLAUDE.md", "MEMORY.md", "DECISIONS.md", "PLAN.md"}

# --- DB source-of-truth (RISTRETTO, S248): solo i DB di stato operativo, NON i DB
#     spazzatura/rigenerabili (profilo Chrome, argos.db scratch, nhtsa_wmi reference). --
SOT_DB_REALPATHS = {
    os.path.realpath(os.path.join(ROOT, "dealer_network.sqlite")),
    os.path.realpath(os.path.join(ROOT, "comm-broker", "bridge.sqlite")),
    os.path.realpath(os.path.join(ROOT, "src", "cove", "data", "cove_tracker.duckdb")),
}

# --- file la cui modifica = disable_hook ------------------------------------------
PROJ_SETTINGS = os.path.realpath(os.path.join(ROOT, ".claude", "settings.json"))
GLOBAL_SETTINGS = os.path.realpath(os.path.join(HOME, ".claude", "settings.json"))
GLOBAL_HOOKS_DIR = os.path.realpath(os.path.join(HOME, ".claude", "hooks"))
HARNESS_FILES = {
    os.path.realpath(os.path.join(HERE, "state_guard.py")),
    os.path.realpath(os.path.join(HERE, "gate_e.py")),
    os.path.realpath(os.path.join(ROOT, "state", "refresh.py")),
    os.path.realpath(os.path.join(ROOT, "state", "refresh.sh")),
}
HOOK_REALPATHS = {PROJ_SETTINGS, GLOBAL_SETTINGS} | HARNESS_FILES

# --- substrato (gap Bash di state_guard): protetti SOLO su Bash-lossy --------------
STATE_MD = os.path.realpath(os.path.join(ROOT, "STATE.md"))
RINGS_JSON = os.path.realpath(os.path.join(ROOT, "state", "rings.json"))
SOT_BASH_ONLY = {STATE_MD, RINGS_JSON}

# token Bash (heuristica best-effort, classe outreach broad by design)
SEND_SIGNATURES = (":9191/send", "send_message.js", "/send-doc", "/send-multi",
                   "sendMessage(", "bridge_outbound")
# entrypoint outreach eseguiti per FILENAME (la signature di invio vive DENTRO il .py,
# non nel cmd shell -> SEND_SIGNATURES non li vede). Classe outreach = meglio FP che FN.
OUTREACH_SCRIPT_SIGNATURES = ("tools/outreach/", "send_day1", "outreach_scheduler",
                              "wa-intelligence/scheduler.py")
PHONE_RE = re.compile(r"\b(?:39)?3\d{8,9}\b")

# --- estrazione operandi lossy (S248) ---------------------------------------------
# redirezione su FILE: `> path` / `>> path`. Esclude fd-dup (2>&1, >&1) col lookbehind
# (?<![0-9&]) e scartando i target che iniziano con &. Esclude process-substitution
# `>(...)` perche' '(' non e' nella char-class del target.
REDIR_RE = re.compile(r"(?<![0-9&])>>?\s*(['\"]?)([^\s'\"|;&<>()]+)\1")
# split del comando in segmenti: il verbo file-op conta solo se e' il PRIMO token del
# segmento (cosi' "cp"/"mv"/"rm" dentro un -m "..." o una prosa non scattano).
SEGSPLIT_RE = re.compile(r";|&&|\|\||\||\n")
FILEOP_VERBS = ("mv", "cp", "rm", "truncate", "tee", "chmod")


def emit_deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def allow():
    sys.exit(0)


# ---------------------------------------------------------------------------------
# slug / packet / token
# ---------------------------------------------------------------------------------
def make_slug(action_class, target):
    h = hashlib.sha1(f"{action_class}|{target}".encode("utf-8")).hexdigest()[:10]
    return f"{action_class}-{h}"


def token_path(slug):
    return os.path.join(PENDING_DIR, f"{slug}.approved")


def packet_path(slug):
    return os.path.join(PENDING_DIR, f"{slug}.md")


def audit(record):
    try:
        os.makedirs(PENDING_DIR, exist_ok=True)
        record["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(AUDIT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def write_packet(slug, action_class, target, tool_name, detail, session):
    os.makedirs(PENDING_DIR, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    body = f"""# Gate E — review richiesto: `{action_class}`

> Azione HIGH-STAKES bloccata da `.harness/gate_e.py`. CC NON puo' procedere
> finche' un verdetto esterno non e' incollato qui e l'approvazione registrata.

- **slug**: `{slug}`
- **classe**: `{action_class}`
- **tool**: `{tool_name}`
- **target**: `{target}`
- **sessione**: `{session}`
- **bloccato**: {ts}

## Cosa stava per fare CC
```
{detail}
```

## Perche' e' high-stakes
Questa classe (`{action_class}`) ha conseguenze reali fuori dal repo o disattiva un
guardrail: irreversibile o difficile da reversare. Per costruzione (verdetto S242 §4)
richiede un critico ESTERNO, non l'auto-critica di CC (decade — Huang et al.).

## Verdetto esterno (incolla qui — Claude AI / Luke)
<!-- VERDETTO: ... -->

## Come approvare (azione di LUKE, non di CC)
Dopo aver incollato il verdetto, Luke esegue nel prompt con prefisso `!`:

    ! python3 .harness/gate_e.py approve {slug} --verdict "sintesi del verdetto"

Poi CC ritenta la STESSA azione: Gate E trova il token, lo consuma una-tantum, e
lascia passare. Se l'azione cambia (target diverso) il token non combacia.
"""
    with open(packet_path(slug), "w", encoding="utf-8") as fh:
        fh.write(body)


def consume_token_or_block(slug, action_class, target, tool_name, detail, session):
    """Se esiste un token approvato per questo slug -> consuma e allow.
    Altrimenti -> scrivi packet + deny."""
    tp = token_path(slug)
    if os.path.exists(tp):
        try:
            os.replace(tp, tp + f".consumed-{int(time.time())}")
        except OSError:
            pass
        audit({"decision": "allow-approved", "slug": slug,
               "action_class": action_class, "session": session, "target": target})
        allow()
    write_packet(slug, action_class, target, tool_name, detail, session)
    audit({"decision": "deny", "slug": slug, "action_class": action_class,
           "session": session, "target": target})
    emit_deny(
        f"Gate E [{action_class}]: azione high-stakes bloccata. Ho scritto il packet "
        f"di review in `.harness/pending_review/{slug}.md`. STOP: non ritentare. "
        f"Serve un verdetto ESTERNO (Claude AI/Luke) incollato nel packet, poi Luke "
        f"registra l'approvazione con `! python3 .harness/gate_e.py approve {slug}`. "
        f"Solo dopo CC puo' ripetere la stessa azione (token consumato una-tantum)."
    )


# ---------------------------------------------------------------------------------
# detection
# ---------------------------------------------------------------------------------
def real(path):
    if not path:
        return ""
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    return os.path.realpath(p)


def is_sot_file(rp):
    if rp in SOT_REALPATHS:
        return True
    base = os.path.basename(rp)
    if base in SOT_BASENAMES and ("/memory/" in rp or "/wiki/projects/" in rp
                                  or rp in SOT_REALPATHS):
        return True
    if rp in SOT_DB_REALPATHS:
        return True
    return False


def classify_write_edit(rp):
    """Ritorna (action_class, target) o (None, None) per Write/Edit/MultiEdit."""
    if rp in HOOK_REALPATHS or rp.startswith(GLOBAL_HOOKS_DIR + os.sep):
        return "disable_hook", os.path.relpath(rp, ROOT) if rp.startswith(ROOT) else rp
    if is_sot_file(rp):
        return "overwrite_sot", os.path.relpath(rp, ROOT) if rp.startswith(ROOT) else rp
    return None, None


def _split_segment_tokens(seg):
    try:
        return shlex.split(seg, comments=False, posix=True)
    except ValueError:
        return seg.split()


def lossy_operands(cmd):
    """Path che sono OPERANDI reali di un'operazione lossy su file.
    NON include: script ESEGUITI (arg di bash/python), testo dentro un commit-message
    o un argomento quotato, fd-dup redirect (2>&1)."""
    ops = []
    # target di redirezione su file (esclude fd-dup e process-substitution)
    for m in REDIR_RE.finditer(cmd):
        tgt = m.group(2)
        if tgt and not tgt.startswith("&"):
            ops.append(tgt)
    # operandi di un verbo file-op, SOLO se il verbo e' il primo token del segmento
    for seg in SEGSPLIT_RE.split(cmd):
        toks = _split_segment_tokens(seg)
        i = 0
        while i < len(toks) and re.match(r"^\w+=", toks[i]):
            i += 1  # salta assegnazioni env iniziali (VAR=val cmd ...)
        if i >= len(toks):
            continue
        verb = os.path.basename(toks[i])
        rest = toks[i + 1:]
        if verb in FILEOP_VERBS:
            if verb == "chmod" and rest:
                rest = rest[1:]  # salta il mode (000/+x/...)
            ops += [t for t in rest if t and not t.startswith("-")]
        elif verb == "sed" and any(t == "-i" or t.startswith("-i") for t in rest):
            # in modalita' -i: scartate flag e suffisso-backup vuoto, il PRIMO positional
            # e' lo script (s/.../, y/.../, p, d, ...), i RESTANTI sono i file editati.
            # (NON usare "s/" in t: matcha substring in path tipo `.harness/...`)
            positionals = [t for t in rest if t and not t.startswith("-")]
            ops += positionals[1:]
    return ops


def classify_bash(cmd):
    """Ritorna (action_class, target, detail) o (None, None, None)."""
    # --- outreach_real (BROAD by design: classe piu' critica) ---
    hit_sig = any(sig in cmd for sig in SEND_SIGNATURES)
    # entrypoint outreach per FILENAME: --dry-run escluso (non invia). Se lo script gira
    # senza numero esplicito -> ramo "no-number" -> DENY (il numero e' hardcoded nel .py).
    hit_script = (any(sig in cmd for sig in OUTREACH_SCRIPT_SIGNATURES)
                  and "--dry-run" not in cmd)
    if hit_sig or hit_script:
        all_nums = set(PHONE_RE.findall(cmd))
        non_test = [n for n in all_nums if n not in TEST_FOUNDER]
        if non_test:
            return ("outreach_real", non_test[0],
                    f"invio WA a numero reale {non_test[0]}: {cmd[:300]}")
        if not all_nums:
            return ("outreach_real", "no-number",
                    f"comando di invio WA senza numero TEST_FOUNDER esplicito: {cmd[:300]}")
        # solo TEST_FOUNDER -> canale sanzionato, allow
        return None, None, None

    # --- archive_doc ---
    if "archive/" in cmd and re.search(r"\b(git\s+mv|mv|git\s+rm|rm)\b", cmd):
        return ("archive_doc", "archive/",
                f"archiviazione/rimozione doc verso archive/: {cmd[:300]}")
    if re.search(r"\bgit\s+rm\b", cmd) and re.search(r"\.(md|json)\b", cmd):
        return ("archive_doc", "tracked-doc",
                f"git rm di doc tracciato: {cmd[:300]}")

    # --- disable_hook / overwrite_sot: SOLO su operandi reali di op lossy (S248) ---
    for op in lossy_operands(cmd):
        rp = real(op)
        cls, tgt = classify_write_edit(rp)
        if not cls and rp in SOT_BASH_ONLY:
            cls, tgt = "overwrite_sot", os.path.relpath(rp, ROOT)
        if cls:
            return (cls, tgt,
                    f"operazione lossy su {tgt} (operando `{op}`) via shell: {cmd[:300]}")

    return None, None, None


# ---------------------------------------------------------------------------------
# hook entrypoint
# ---------------------------------------------------------------------------------
def run_hook():
    # Escape manutenzione deliberata (come state_guard.gate_c): Luke rilancia CC con
    # ARGOS_HARNESS_UNLOCK=1 per editare/manutenere il harness stesso.
    if os.environ.get("ARGOS_HARNESS_UNLOCK") == "1":
        allow()
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        allow()
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    session = data.get("session_id", "unknown")

    action_class = target = detail = None

    if tool_name in ("Write", "Edit", "MultiEdit"):
        rp = real(tool_input.get("file_path"))
        action_class, target = classify_write_edit(rp)
        if action_class:
            detail = f"{tool_name} su {target}"
    elif tool_name == "Bash":
        cmd = tool_input.get("command", "") or ""
        # non bloccare l'auto-approvazione: e' azione di Luke via ! prefix
        if re.search(r"gate_e\.py\s+approve\b", cmd):
            emit_deny(
                "Gate E: l'approvazione e' un'azione di LUKE (prompt con prefisso `!`), "
                "non di CC. CC non puo' auto-approvare un'azione high-stakes. Fermati e "
                "lascia che sia Luke a registrare l'approvazione dopo il verdetto esterno."
            )
        action_class, target, detail = classify_bash(cmd)

    if not action_class:
        allow()

    slug = make_slug(action_class, target)
    consume_token_or_block(slug, action_class, target, tool_name, detail, session)


# ---------------------------------------------------------------------------------
# CLI (Luke)
# ---------------------------------------------------------------------------------
def cli_approve(argv):
    if not argv:
        print("uso: gate_e.py approve <slug> [--verdict \"testo\"]", file=sys.stderr)
        return 2
    slug = argv[0]
    verdict = ""
    if "--verdict" in argv:
        i = argv.index("--verdict")
        verdict = argv[i + 1] if i + 1 < len(argv) else ""
    os.makedirs(PENDING_DIR, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(token_path(slug), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"slug": slug, "approved_at": ts, "verdict": verdict}) + "\n")
    audit({"decision": "approve-registered", "slug": slug, "by": "luke", "verdict": verdict[:120]})
    print(f"OK: approvazione registrata per '{slug}'. CC puo' ritentare UNA volta "
          f"la stessa azione (token consumato all'uso).")
    return 0


def cli_list():
    if not os.path.isdir(PENDING_DIR):
        print("nessun packet pendente.")
        return 0
    packets = [f for f in os.listdir(PENDING_DIR) if f.endswith(".md")]
    if not packets:
        print("nessun packet pendente.")
        return 0
    for f in sorted(packets):
        slug = f[:-3]
        approved = " [APPROVED]" if os.path.exists(token_path(slug)) else ""
        print(f"  {slug}{approved}")
    return 0


def cli_selftest():
    """Smoke interno: simula payload e verifica deny/allow + packet."""
    import tempfile
    # determinismo: la selftest non deve dipendere da un eventuale unlock di sessione
    os.environ.pop("ARGOS_HARNESS_UNLOCK", None)
    fails = []

    cases = [
        # --- baseline ---
        ({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}, "allow"),
        ({"tool_name": "Bash", "tool_input": {"command": "bash state/refresh.sh S247"}}, "allow"),
        # --- regressioni FP S247/S248 (devono ESSERE allow) ---
        ({"tool_name": "Bash", "tool_input": {"command": "bash state/refresh.sh S248 2>&1"}}, "allow"),
        ({"tool_name": "Bash", "tool_input": {"command": "git commit -m 'refactor gate_e.py + rigenero STATE.md'"}}, "allow"),
        ({"tool_name": "Bash", "tool_input": {"command": "git commit -m 'nota: cp di STATE.md in backup'"}}, "allow"),
        ({"tool_name": "Bash", "tool_input": {"command": "python3 .harness/gate_e.py selftest"}}, "allow"),
        ({"tool_name": "Bash", "tool_input": {"command": "rm wa-intelligence/argos.db"}}, "allow"),
        ({"tool_name": "Bash", "tool_input": {"command": "rm tools/scrapers/.chrome_profile/first_party_sets.db"}}, "allow"),
        # --- veri positivi mantenuti (devono ESSERE deny) ---
        ({"tool_name": "Bash", "tool_input": {"command": "git mv prompts/x.md archive/"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "sed -i '' 's/x/y/' STATE.md"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "echo x > STATE.md"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "cp /tmp/x .harness/gate_e.py"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "echo x > src/cove/data/cove_tracker.duckdb"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "curl :9191/send -d to=393998887766"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "curl :9191/send -d to=393314928901"}}, "allow"),
        # --- #2 fix S251: entrypoint outreach per FILENAME (signature dentro il .py) ---
        ({"tool_name": "Bash", "tool_input": {"command": "python3 tools/outreach/send_day1_stile_car.py"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "python3 tools/outreach/send_day1_stile_car.py --dry-run"}}, "allow"),
        ({"tool_name": "Write", "tool_input": {"file_path": "PLAN.md", "content": "x"}}, "deny"),
        ({"tool_name": "Write", "tool_input": {"file_path": "BACKLOG.md", "content": "x"}}, "allow"),
        ({"tool_name": "Edit", "tool_input": {"file_path": ".claude/settings.json"}}, "deny"),
        ({"tool_name": "Edit", "tool_input": {"file_path": ".harness/gate_e.py"}}, "deny"),
        # --- TP-SoT espliciti vs matcher NUOVO (condizione #1 S249, anti falsi-NEGATIVI) ---
        ({"tool_name": "Write", "tool_input": {"file_path": "CLAUDE.md", "content": "x"}}, "deny"),
        ({"tool_name": "Write", "tool_input": {"file_path": os.path.join(HOME, ".claude/projects/p/memory/MEMORY.md"), "content": "x"}}, "deny"),
        ({"tool_name": "Write", "tool_input": {"file_path": os.path.join(HOME, "venture-os/wiki/projects/G/DECISIONS.md"), "content": "x"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "rm dealer_network.sqlite"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "truncate -s 0 comm-broker/bridge.sqlite"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "sed -i '' 's/a/b/' .harness/state_guard.py"}}, "deny"),
        ({"tool_name": "Bash", "tool_input": {"command": "rm src/cove/data/nhtsa_wmi.duckdb"}}, "allow"),
    ]
    # redirige PENDING_DIR su tmp per non sporcare
    global PENDING_DIR, AUDIT
    real_pending = PENDING_DIR
    with tempfile.TemporaryDirectory() as td:
        PENDING_DIR = td
        AUDIT = os.path.join(td, "audit.jsonl")
        for payload, expect in cases:
            out = _capture_decision(payload)
            if out != expect:
                fails.append(f"{payload['tool_input']} -> {out}, atteso {expect}")
    PENDING_DIR = real_pending
    if fails:
        print("SELFTEST FAIL:")
        for f in fails:
            print("  " + f)
        return 1
    print(f"SELFTEST PASS ({len(cases)}/{len(cases)})")
    return 0


def _capture_decision(payload):
    """Esegue run_hook catturando stdout per capire deny vs allow."""
    import io
    buf_in = io.StringIO(json.dumps(payload))
    buf_out = io.StringIO()
    old_in, old_out = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = buf_in, buf_out
    decision = "allow"
    try:
        run_hook()
    except SystemExit:
        pass
    finally:
        sys.stdin, sys.stdout = old_in, old_out
    if '"permissionDecision": "deny"' in buf_out.getvalue():
        decision = "deny"
    return decision


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "approve":
        sys.exit(cli_approve(argv[1:]))
    if argv and argv[0] == "list":
        sys.exit(cli_list())
    if argv and argv[0] == "selftest":
        sys.exit(cli_selftest())
    # default: hook mode
    try:
        run_hook()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — fail-open su bug interni
        print(f"gate_e: errore interno, fail-open: {exc}", file=sys.stderr)
        allow()


if __name__ == "__main__":
    main()
