#!/usr/bin/env python3
"""
refresh.py — Gate A: la tabella anelli in STATE.md e' GENERATA da check eseguibili,
non scritta a mano. "VERIFIED" = fatto calcolato, non frase digitabile.

Per ogni anello in state/rings.json:
  - blocked_on impostato            -> BLOCKED (check saltato, Gate D)
  - check_cmd == null               -> UNVERIFIED (nessun check in-sessione)
  - check_cmd eseguito, rc==0       -> last_status=PASS  (display VERIFIED se sessione corrente)
  - check_cmd eseguito, rc!=0       -> last_status=FAIL

Render: tabella tra marker <!-- GENERATED:rings:start/end --> in STATE.md.
Un anello e' VERIFIED nel render SOLO se last_run_session == sessione_corrente && PASS,
altrimenti STALE. Cosi' un VERIFIED non puo' sopravvivere a una sessione senza essere riguadagnato.

Uso: python3 state/refresh.py [SESSION_ID]
     SESSION_ID = arg1, fallback env ARGOS_SESSION, fallback unknown-<ts>.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RINGS = os.path.join(HERE, "rings.json")
STATE = os.path.join(ROOT, "STATE.md")
MARK_START = "<!-- GENERATED:rings:start -->"
MARK_END = "<!-- GENERATED:rings:end -->"
TIMEOUT_S = 180


def session_id():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    env = os.environ.get("ARGOS_SESSION", "").strip()
    if env:
        return env
    return "unknown-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_check(cmd):
    try:
        p = subprocess.run(
            cmd, shell=True, cwd=ROOT,
            capture_output=True, text=True, timeout=TIMEOUT_S,
        )
        return "PASS" if p.returncode == 0 else "FAIL"
    except Exception:
        return "FAIL"


def display(r, sess):
    if r.get("blocked_on"):
        return "BLOCKED"
    if not r.get("check_cmd"):
        return "UNVERIFIED"
    if r.get("last_status") == "PASS":
        return "VERIFIED" if r.get("last_run_session") == sess else "STALE"
    return r.get("last_status") or "UNVERIFIED"


def render(rings, sess, now):
    rows = [
        "| # | Anello | Stato | Tier | Check | Ultima sessione |",
        "|---|--------|-------|------|-------|-----------------|",
    ]
    for r in rings:
        d = display(r, sess)
        if r.get("blocked_on"):
            chk = "freeze: " + r["blocked_on"]
        elif r.get("check_cmd"):
            chk = "`" + r["check_cmd"] + "`"
        else:
            chk = "—"
        last = r.get("last_run_session") or "—"
        rows.append(f"| {r['id']} | {r['name']} | {d} | {r.get('tier','—')} | {chk} | {last} |")
    table = "\n".join(rows)
    block = (
        f"{MARK_START}\n"
        f"<!-- NON modificare a mano: rigenerato da `bash state/refresh.sh`. "
        f"VERIFIED = check passato in QUESTA sessione. -->\n"
        f"_Rigenerato {now} · sessione `{sess}`_\n\n"
        f"{table}\n"
        f"{MARK_END}"
    )
    content = open(STATE, encoding="utf-8").read()
    if MARK_START in content and MARK_END in content:
        content = re.sub(
            re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
            lambda _m: block, content, count=1, flags=re.S,
        )
    else:
        raise SystemExit(
            f"ERRORE: marker {MARK_START}/{MARK_END} assenti in STATE.md. "
            "Aggiungili dove deve comparire la tabella."
        )
    open(STATE, "w", encoding="utf-8").write(content)


def main():
    sess = session_id()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(RINGS, encoding="utf-8") as f:
        rings = json.load(f)
    for r in rings:
        if r.get("blocked_on"):
            r["last_status"] = "BLOCKED"
            continue
        if not r.get("check_cmd"):
            r["last_status"] = "UNVERIFIED"
            continue
        r["last_status"] = run_check(r["check_cmd"])
        r["last_run_ts"] = now
        r["last_run_session"] = sess
    with open(RINGS, "w", encoding="utf-8") as f:
        json.dump(rings, f, indent=2, ensure_ascii=False)
        f.write("\n")
    render(rings, sess, now)
    # echo riassunto su stdout per il chiamante (hook/Luke)
    for r in rings:
        print(f"{r['id']:<6} {display(r, sess)}")


if __name__ == "__main__":
    main()
