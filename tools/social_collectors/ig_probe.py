"""
ig_probe.py -- PARTE B1: PROBE read-only Instagram web_profile_info.

Verdetto: web_profile_info FUNZIONA DA QUI = SI (>=3/5 a 200) / NO.
NON costruisce nulla. NON persiste. Solo report status + campi se 200.

Endpoint: i.instagram.com/api/v1/users/web_profile_info/?username=<handle>
Header chiave: x-ig-app-id 936619743392459 + UA mobile + Accept-Language it-IT.
Cookie-stripping: nessun cookie inviato (niente cookie vuoti/malformati).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from curl_cffi import requests as curl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import sqlite3

DB = str(Path(__file__).resolve().parents[2] / "dealer_network.sqlite")
ENDPOINT = "https://i.instagram.com/api/v1/users/web_profile_info/?username={}"
APP_ID = "936619743392459"
UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram")


def _headers() -> dict:
    return {
        "User-Agent": UA_MOBILE,
        "x-ig-app-id": APP_ID,
        "Accept": "*/*",
        "Accept-Language": "it-IT,it;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/",
    }


def probe_one(handle: str) -> dict:
    handle = handle.lstrip("@").strip().rstrip("/").split("/")[-1]
    url = ENDPOINT.format(handle)
    rec = {"handle": handle, "status": None, "http": None}
    try:
        # cookie-stripping: NON passiamo alcun cookie
        resp = curl.get(url, headers=_headers(), impersonate="chrome120",
                        timeout=20, allow_redirects=True)
        rec["status"] = resp.status_code
        rec["http"] = getattr(resp, "http_version", None)
        if resp.status_code == 200:
            try:
                u = resp.json().get("data", {}).get("user", {}) or {}
            except Exception:  # noqa: BLE001
                u = {}
            rec["bio"] = (u.get("biography") or "")[:120]
            rec["external_url"] = u.get("external_url")
            rec["category_name"] = u.get("category_name")
            rec["followers"] = (u.get("edge_followed_by") or {}).get("count")
            edges = ((u.get("edge_owner_to_timeline_media") or {})
                     .get("edges") or [])
            if edges:
                node = edges[0].get("node", {})
                rec["last_post_ts"] = node.get("taken_at_timestamp")
    except Exception as exc:  # noqa: BLE001
        rec["error"] = str(exc)[:160]
    return rec


def get_handles(limit: int = 5) -> list[tuple[str, str]]:
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT dealer_id, instagram FROM dealers "
        "WHERE instagram IS NOT NULL AND instagram != '' "
        "ORDER BY dealer_id LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def main() -> None:
    handles = get_handles(5)
    print(f"PROBE IG web_profile_info — {len(handles)} dealer reali\n")
    ok = 0
    for did, ig in handles:
        r = probe_one(ig)
        if r["status"] == 200:
            ok += 1
            print(f"[200] {did:16} @{r['handle']:24} http={r['http']} "
                  f"cat={r.get('category_name')!r} foll={r.get('followers')} "
                  f"link={r.get('external_url')!r} bio={r.get('bio','')!r}")
        else:
            print(f"[{r['status']}] {did:16} @{r['handle']:24} "
                  f"err={r.get('error','-')}")
    n = len(handles)
    verdict = "SI" if ok >= 3 else "NO"
    print(f"\nVERDETTO B1: web_profile_info FUNZIONA DA QUI = {verdict} "
          f"({ok}/{n} a 200)")
    # control account per distinguere blocco-IP da handle errati
    ctrl = probe_one("nasa")
    print(f"CONTROL @nasa -> status {ctrl['status']} "
          f"(se 200: endpoint vivo, fallimenti = handle/page-specific; "
          f"se 4xx: blocco lato IP/macchina)")
    print("__JSON__" + json.dumps({"ok": ok, "n": n, "verdict": verdict,
                                   "control_nasa": ctrl["status"]}))


if __name__ == "__main__":
    main()
