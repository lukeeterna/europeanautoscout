"""ARGOS templates loader — D-22 F3 implementation.

Jinja2-based template engine per messaggi pre-caricati 5 fasi standard:
  offer / negotiation / documents / payment / delivery

Lingue: italiano (lato dealer IT, D-04) e inglese (lato seller EU, D-21 universal).

Variable injection: auto specs, prezzi, dates, alias parties.
LLM finishing optional (D-22) — questa è layer template-only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined


PHASES = ["offer", "negotiation", "documents", "payment", "delivery"]
LANGS = ["it", "en"]


def get_env(template_dir: Optional[Path] = None) -> Environment:
    if template_dir is None:
        template_dir = Path(__file__).parent
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )


def render(phase: str, lang: str, **vars) -> str:
    """Render template per (phase, lang) con variable injection.

    Es: render("offer", "it", auto_make="BMW", auto_model="X3", auto_year=2020,
              auto_km=45000, price_eu_eur=32000, margin_estimate_eur=4500,
              country="DE", dossier_id="ARGOS-2026-001")
    """
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}, got {phase!r}")
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}, got {lang!r}")
    env = get_env()
    tpl = env.get_template(f"{phase}.{lang}.j2")
    return tpl.render(**vars)


if __name__ == "__main__":
    # Smoke test all 10 templates (5 phases × 2 langs)
    sample_vars = {
        "dealer_alias": "D-FG-001",
        "seller_alias": "S-DE-042",
        "auto_make": "BMW",
        "auto_model": "X3 xDrive 30d",
        "auto_year": 2020,
        "auto_km": 45000,
        "price_eu_eur": 32000,
        "price_it_market_eur": 38500,
        "margin_estimate_eur": 4500,
        "country": "DE",
        "dossier_id": "ARGOS-2026-001",
        "fee_eur": 1000,
        "delivery_days_est": 20,
        "documents_required": ["EUROCOC", "DAT", "DEKRA", "Libretto"],
        "transport_quote_eur": 850,
    }
    for phase in PHASES:
        for lang in LANGS:
            try:
                out = render(phase, lang, **sample_vars)
                print(f"--- {phase}.{lang} ({len(out)} chars) ---")
                print(out[:200] + ("..." if len(out) > 200 else ""))
                print()
            except Exception as e:
                print(f"FAIL {phase}.{lang}: {e}")
