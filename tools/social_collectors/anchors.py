"""
anchors.py -- Deriva le 4 ancore operative dai dati FB/IG raccolti.

Ancore (operational_anchors), una riga per (dealer_id, anchor):
  - qualifica : e' davvero un concessionario auto?      (fb/ig category)
  - canale    : quale canale di contatto e' vivo?        (fb_phone / ig link wa.me / website)
  - vivo      : segnale di attivita' recente             (ig_last_post_ts / fb_talking)
  - volume    : proxy di dimensione/reach                (fb_likes / ig_followers)

Idempotente: upsert su (dealer_id, anchor). Solo dati reali, 0 PII.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from schema import connect

_AUTO_KW = ("auto", "car", "motor", "veicol", "concession", "dealer")


def _upsert(conn: sqlite3.Connection, did: str, anchor: str,
            value: str | None, source: str) -> None:
    conn.execute(
        """INSERT INTO operational_anchors (dealer_id, anchor, value, source)
           VALUES (?,?,?,?)
           ON CONFLICT(dealer_id, anchor) DO UPDATE SET
           value=excluded.value, source=excluded.source,
           updated_at=datetime('now')""",
        (did, anchor, value, source))


def derive(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    did = row["dealer_id"]
    res = {}

    # qualifica
    cat = row["fb_category"] or row["ig_category"]
    src = "fb" if row["fb_category"] else ("ig" if row["ig_category"] else "db")
    if cat and any(k in cat.lower() for k in _AUTO_KW):
        res["qualifica"] = (f"auto:{cat}", src)
    elif cat:
        res["qualifica"] = (f"altro:{cat}", src)
    else:
        res["qualifica"] = (None, "db")

    # canale
    link = (row["ig_external_url"] or "")
    if row["fb_phone"]:
        res["canale"] = (f"tel:{row['fb_phone']}", "fb")
    elif "wa.me" in link:
        res["canale"] = (f"whatsapp:{link}", "ig")
    elif row["fb_website"] or link:
        res["canale"] = (f"web:{row['fb_website'] or link}", "fb" if row["fb_website"] else "ig")
    else:
        res["canale"] = (None, "db")

    # vivo
    if row["ig_last_post_ts"]:
        days = (datetime.now(timezone.utc).timestamp() - row["ig_last_post_ts"]) / 86400
        res["vivo"] = (f"ig_post_{int(days)}gg_fa", "ig")
    elif row["fb_talking"] and row["fb_talking"] > 0:
        res["vivo"] = (f"fb_talking:{row['fb_talking']}", "fb")
    else:
        res["vivo"] = (None, "db")

    # volume
    if row["ig_followers"]:
        res["volume"] = (f"ig_foll:{row['ig_followers']}", "ig")
    elif row["fb_likes"]:
        res["volume"] = (f"fb_likes:{row['fb_likes']}", "fb")
    else:
        res["volume"] = (None, "db")

    for anchor, (val, source) in res.items():
        _upsert(conn, did, anchor, val, source)
    conn.commit()
    return {a: v for a, (v, _) in res.items()}


def run() -> None:
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM dealer_operational_profile ORDER BY dealer_id").fetchall()
    for r in rows:
        res = derive(conn, r)
        print(f"[anchor] {r['dealer_id']:16} "
              + " | ".join(f"{a}={res[a]}" for a in
                           ("qualifica", "canale", "vivo", "volume")))
    conn.close()


if __name__ == "__main__":
    run()
