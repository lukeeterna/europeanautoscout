"""
fb_collector.py -- PARTE A: collector Facebook pubblico (additivo).

Strategia PROVATA sul campo: fetch HTML pubblico (curl_cffi/chrome120) ->
parse og:title / og:description / og:url + campi business nel body
(categoria, telefono, email, sito, data ultimo post).

Degradazione (NON errore):
  - campi login-gated (email/sito/orari/data-post) -> vuoti.
  - og: assente (pagina JS-rendered) -> source = "js_only", pipeline NON fallisce.

Persistenza: upsert in dealer_operational_profile (idempotente su dealer_id).
"""
from __future__ import annotations

import argparse
import html as _html
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))
from resilient_fetcher import ResilientFetcher  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema import connect, recompute_sources_ok  # noqa: E402

_UA_MOBILE = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def _meta(html: str, prop: str) -> str | None:
    m = re.search(r'<meta property="%s" content="([^"]*)"' % re.escape(prop), html)
    return _html.unescape(m.group(1)).strip() if m else None


def _first(pattern: str, html: str, group: int = 1) -> str | None:
    m = re.search(pattern, html)
    return m.group(group) if m else None


def _to_int(s: str | None) -> int | None:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else None


def _normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith("http"):
        return url
    m = re.search(r"facebook\.com/(.+)$", url, re.I)
    if m:  # gia' contiene il dominio (es. "facebook.com/handle")
        return "https://www.facebook.com/" + m.group(1)
    return "https://www.facebook.com/" + url.lstrip("/")  # solo handle


def collect_fb(fb_url: str) -> dict:
    """Ritorna i campi FB pubblici. Mai solleva: degrada a source=error/js_only."""
    fb_url = _normalize_url(fb_url)
    out = {
        "fb_url": fb_url, "fb_name": None, "fb_category": None,
        "fb_likes": None, "fb_talking": None, "fb_phone": None,
        "fb_email": None, "fb_website": None, "fb_last_post": None,
        "fb_source": "error",
    }
    fetcher = ResilientFetcher(timeout=25)
    try:
        html = fetcher.fetch(fb_url, accept_language="it-IT,it;q=0.9",
                             extra_headers={"User-Agent": _UA_MOBILE})
    except Exception as exc:  # noqa: BLE001
        out["fb_error"] = str(exc)[:200]
        return out
    finally:
        try:
            fetcher.close()
        except Exception:  # noqa: BLE001
            pass

    if not html:
        return out

    title = _meta(html, "og:title")
    desc = _meta(html, "og:description")
    if not title and not desc:
        # Pagina servita ma senza og: -> JS-rendered
        out["fb_source"] = "js_only"
        return out

    out["fb_name"] = title
    out["fb_category"] = _first(r'"category_name":"([^"]*)"', html)

    # og:description tipico: "Nome, Citta'. Mi piace: 13.952 . 271 persone ne parlano ..."
    if desc:
        out["fb_likes"] = _to_int(_first(r"Mi piace:\s*([\d.\u00a0 ]+)", desc))
        out["fb_talking"] = _to_int(_first(r"([\d.\u00a0 ]+)\s+persone ne parlano", desc))

    # telefono italiano pubblico
    phone = _first(r"(\+39[\s\d]{6,15})", html)
    if phone:
        out["fb_phone"] = re.sub(r"\s+", " ", phone).strip()

    # email pubblica (se non login-gated)
    email = _first(r'"email":"([^"]+@[^"]+)"', html)
    if not email:
        email = _first(r"([\w.\-]+@[\w.\-]+\.[a-zA-Z]{2,})", html)
    if email and "facebook" not in email and "fbcdn" not in email:
        out["fb_email"] = email

    # sito esterno (link-out via l.facebook.com redirect)
    ext = _first(r'l\.facebook\.com\\?/l\\?/[^"]*[?&]u=(https?[^"&\\]+)', html)
    if ext:
        from urllib.parse import unquote
        out["fb_website"] = unquote(ext.replace("\\", ""))

    out["fb_source"] = "ok"
    return out


def persist_fb(conn: sqlite3.Connection, dealer_id: str, prof: dict) -> None:
    cols = ["fb_url", "fb_name", "fb_category", "fb_likes", "fb_talking",
            "fb_phone", "fb_email", "fb_website", "fb_last_post", "fb_source"]
    set_clause = ", ".join(f"{c}=excluded.{c}" for c in cols)
    placeholders = ", ".join(["?"] * (len(cols) + 1))
    conn.execute(
        f"""INSERT INTO dealer_operational_profile
            (dealer_id, {", ".join(cols)})
            VALUES ({placeholders})
            ON CONFLICT(dealer_id) DO UPDATE SET
            {set_clause}, updated_at=datetime('now')""",
        [dealer_id] + [prof.get(c) for c in cols],
    )
    conn.commit()
    recompute_sources_ok(conn, dealer_id)


def run(dealer_ids: list[str] | None = None, limit: int = 5) -> list[dict]:
    conn = connect()
    if dealer_ids:
        q = ("SELECT dealer_id, name, facebook FROM dealers "
             f"WHERE dealer_id IN ({','.join('?' * len(dealer_ids))})")
        rows = conn.execute(q, dealer_ids).fetchall()
    else:
        rows = conn.execute(
            "SELECT dealer_id, name, facebook FROM dealers "
            "WHERE facebook IS NOT NULL AND facebook != '' "
            "ORDER BY dealer_id LIMIT ?", (limit,)).fetchall()
    results = []
    for r in rows:
        prof = collect_fb(r["facebook"])
        persist_fb(conn, r["dealer_id"], prof)
        prof["dealer_id"] = r["dealer_id"]
        prof["name"] = r["name"]
        results.append(prof)
        print(f"[fb] {r['dealer_id']:16} {prof['fb_source']:11} "
              f"cat={prof['fb_category']!r} likes={prof['fb_likes']} "
              f"tel={prof['fb_phone']!r}", flush=True)
    conn.close()
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", help="dealer_id specifici")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = run(a.ids, a.limit)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
