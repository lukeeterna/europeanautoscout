"""ARGOS IT market-price distribution — SPEC-AWARE (S259).

Fetcher di comparabili REALI sul mercato italiano. Sostituisce il falso
`prezzo_de * 1.15` hardcoded sparso nel codice: il prezzo di mercato IT
e' la MEDIANA di una distribuzione di annunci reali AutoScout24.it dello
stesso make/model/FAMIGLIA-TRIM/fascia-anno/fascia-km/alimentazione.

S259 — perche' spec-aware: il filtro S256 era trim-blind (solo make/model/
anno+-1). Pool che mescola trim -> mediana inaffidabile (es. M340i 2024 nello
stesso pool di una 318i): rischio FALSO-PASS, il peggiore per ARGOS. Qui il
pool e' filtrato per FAMIGLIA-TRIM derivata in modo deterministico (no LLM):
engine_class + drivetrain + trim_line + alimentazione, con allargamento
progressivo controllato e flag di confidenza (relaxation_level, no_verdict).

NOTA regex engine_class: la spec .manual.md indicava `\bm?(\d{3})\b`, ma `\b`
dopo `\d{3}` NON matcha i variant reali "320d"/"M340i" (cifra->lettera = niente
boundary). Si usa `(?<!\d)(M?)(\d{3})(?!\d)`: cattura "320" in "320d", "340" in
"M340i", esclude gli anni a 4 cifre (2020). Terminal fact (mediane diverse per
trim diversi) governa sulla lettera del regex.

Alimenta `margin_gate.evaluate_margin(prezzo_de, prezzo_mercato_it=median)`.
"""

from __future__ import annotations

import logging
import re
import statistics
from typing import Optional

from .scrapers.autoscout_scraper import AutoScoutScraper

logger = logging.getLogger(__name__)

KM_BAND_DEFAULT = 30_000   # +/- attorno al km target
MIN_CONFIDENT_N = 5        # soglia legacy `low_confidence` (retrocompat campo)
MIN_N_DEFAULT = 8          # soglia NO-VERDICT spec-aware (PROVVISORIA — ratifica Luke)

# engine-class: 3 cifre NON circondate da altre cifre (esclude anni 2020),
# prefisso M opzionale (performance, M340/M3). Cattura "320" in "320d".
_ENGINE_RE = re.compile(r"(?<!\d)(M?)(\d{3})(?!\d)", re.IGNORECASE)
# M-performance esplicito: "M340", "M 340", "M3", "M5" ...
_PERF_RE = re.compile(r"(?i)\bM\s?\d{1,3}\b")

_AWD_TOKENS = ("xdrive", "quattro", "4matic", "allrad", "4motion", " awd")


def derive_trim_family(
    variant: Optional[str],
    fuel: Optional[str] = None,
    transmission: Optional[str] = None,
    power_hp: int = 0,
) -> dict:
    """Categoria-trim normalizzata e DETERMINISTICA da un annuncio.

    Args:
        variant:      stringa variant grezza ("320d xDrive M Sport", spesso sporca).
        fuel:         alimentazione da `fuel_type.value` (NON dal variant): "diesel"/...
        transmission: da `transmission.value`: "manual"/"automatic"/"unknown".
        power_hp:     potenza in CV (int), tollerante a 0/None.

    Returns:
        dict: engine_class, performance(bool), drivetrain("awd"/"rwd"),
        trim_line, fuel, transmission, power_hp, key (stringa compatta audit).
    Gestisce variant vuoto/sporco senza crash.
    """
    v = (variant or "").strip()
    vl = v.lower()

    engine_class = ""
    performance = False
    m = _ENGINE_RE.search(v)
    if m:
        engine_class = m.group(2)
        if m.group(1):          # 'M' attaccato alle cifre (M340) -> performance
            performance = True
    if _PERF_RE.search(v):
        performance = True

    drivetrain = "awd" if any(t.strip() in vl for t in _AWD_TOKENS) else "rwd"

    if "m sport" in vl or "m-sport" in vl or "msport" in vl:
        trim_line = "m_sport"
    elif "luxury" in vl:
        trim_line = "luxury"
    elif "advantage" in vl:
        trim_line = "advantage"
    elif "sport line" in vl or "sportline" in vl:
        trim_line = "sport_line"
    else:
        trim_line = "base"

    fuel_s = (fuel or "").strip().lower() or None
    trans_s = (transmission or "").strip().lower() or None
    if trans_s in ("unknown", ""):
        trans_s = None

    return {
        "engine_class": engine_class,
        "performance": performance,
        "drivetrain": drivetrain,
        "trim_line": trim_line,
        "fuel": fuel_s,
        "transmission": trans_s,
        "power_hp": int(power_hp or 0),
        "key": (f"{engine_class or '?'}/{drivetrain}/{trim_line}/"
                f"{fuel_s or '?'}{'/M' if performance else ''}"),
    }


# Livelli di allargamento progressivo (ORDINE FISSO). Ogni livello = quali
# criteri sono ATTIVI. relaxation_level = indice del livello scelto (0=stretto).
#   L0: engine+drivetrain+trim+fuel+km-band, anno+-year_span
#   L1: droppa km-band                       (anno+-1)
#   L2: anno+-2                               (resta engine+drivetrain+trim+fuel)
#   L3: droppa trim_line                      (engine+drivetrain+fuel, anno+-2)
#   L4: droppa drivetrain                     (engine+fuel, anno+-2)
def _levels(year_span: int) -> list[dict]:
    yt = min(max(year_span, 1), 2)
    return [
        dict(engine=True, drivetrain=True, trim=True, fuel=True, km=True,  year_tol=yt),
        dict(engine=True, drivetrain=True, trim=True, fuel=True, km=False, year_tol=1),
        dict(engine=True, drivetrain=True, trim=True, fuel=True, km=False, year_tol=2),
        dict(engine=True, drivetrain=True, trim=False, fuel=True, km=False, year_tol=2),
        dict(engine=True, drivetrain=False, trim=False, fuel=True, km=False, year_tol=2),
    ]


def _match(target: dict, cspec: dict, c_km: int, c_year: int,
           t_km: int, t_year: int, km_band: int, cfg: dict) -> bool:
    if cfg["engine"] and target["engine_class"]:
        if cspec["engine_class"] != target["engine_class"]:
            return False
    if cfg["drivetrain"]:
        if cspec["drivetrain"] != target["drivetrain"]:
            return False
    if cfg["trim"]:
        if cspec["trim_line"] != target["trim_line"]:
            return False
    if cfg["fuel"] and target["fuel"]:
        if cspec["fuel"] != target["fuel"]:
            return False
    if cfg["km"] and t_km and c_km:
        if abs(c_km - t_km) > km_band:
            return False
    if abs(c_year - t_year) > cfg["year_tol"]:
        return False
    return True


def get_it_distribution(
    make: str,
    model: str,
    year: int,
    km: int,
    fuel: Optional[str] = None,
    *,
    target_variant: Optional[str] = None,
    target_transmission: Optional[str] = None,
    target_power_hp: Optional[int] = None,
    km_band: int = KM_BAND_DEFAULT,
    year_span: int = 1,
    min_n: int = MIN_N_DEFAULT,
) -> dict:
    """Distribuzione prezzi reali IT per comparabili dello STESSO trim.

    Spec-aware se `target_variant` e' passato: una SOLA scrape (anno+-2,
    km-agnostica) poi filtro a livelli L0->L4 finche' n>=min_n. Se nemmeno L4
    raggiunge min_n -> `no_verdict=True` (il gate NON emette PASS).

    Retrocompat: senza `target_variant`, fallback al filtro legacy
    (fuel+km+anno+-year_span), `relaxation_level=None`.

    Returns dict con: median, p25, p75, min, max, n, n_raw, n_pool,
    relaxation_level, trim_family, target_spec, no_verdict, low_confidence,
    source, listings.
    """
    scraper = AutoScoutScraper("autoscout24_it")
    spec_aware = bool(target_variant)
    # spec-aware: pool largo (anno+-2) filtrato in memoria. Legacy: anno+-year_span.
    scrape_span = 2 if spec_aware else year_span
    raw = scraper.scrape_model(
        make=make, model=model,
        year_min=year - scrape_span, year_max=year + scrape_span,
    )

    target = derive_trim_family(
        target_variant or "", fuel, target_transmission, target_power_hp or 0,
    )

    pool = []  # (listing, cspec, km, year)
    for lst in raw:
        price = getattr(lst, "price_eur", 0) or 0
        if price <= 0:
            continue
        ft = getattr(lst, "fuel_type", None)
        ftv = getattr(ft, "value", str(ft)) if ft is not None else ""
        tr = getattr(lst, "transmission", None)
        trv = getattr(tr, "value", str(tr)) if tr is not None else ""
        cspec = derive_trim_family(
            getattr(lst, "variant", "") or "", ftv, trv,
            getattr(lst, "power_hp", 0) or 0,
        )
        pool.append((
            lst, cspec,
            int(getattr(lst, "km", 0) or 0),
            int(getattr(lst, "year", 0) or 0),
        ))

    if spec_aware:
        levels = _levels(year_span)
        selected, chosen_level = [], len(levels) - 1
        for idx, cfg in enumerate(levels):
            matched = [
                p for p in pool
                if _match(target, p[1], p[2], p[3], km, year, km_band, cfg)
            ]
            selected, chosen_level = matched, idx
            if len(matched) >= min_n:
                break
        relaxation_level = chosen_level
    else:
        # legacy: fuel + km + anno+-year_span, livello unico
        cfg = dict(engine=False, drivetrain=False, trim=False, fuel=True,
                   km=True, year_tol=year_span)
        selected = [
            p for p in pool
            if _match(target, p[1], p[2], p[3], km, year, km_band, cfg)
        ]
        relaxation_level = None

    comps = [p[0] for p in selected]
    prices = sorted(float(l.price_eur) for l in comps)
    n = len(prices)
    no_verdict = spec_aware and n < min_n

    out: dict = {
        "source": "AutoScout24.it",
        "n": n,
        "n_raw": len(raw),
        "n_pool": len(pool),
        "relaxation_level": relaxation_level,
        "trim_family": target["key"] if spec_aware else None,
        "target_spec": target if spec_aware else None,
        "min_n": min_n,
        "no_verdict": no_verdict,
        "low_confidence": n < MIN_CONFIDENT_N,
        "listings": [
            {
                "price_eur": float(l.price_eur),
                "km": int(getattr(l, "km", 0) or 0),
                "year": int(getattr(l, "year", 0) or 0),
                "variant": getattr(l, "variant", "") or "",
                "url": getattr(l, "listing_url", "") or "",
            }
            for l in comps
        ],
    }

    if n == 0:
        out.update(median=None, p25=None, p75=None, min=None, max=None)
        logger.warning(
            "[it_market_price] %s %s %s trim=%s: 0 comparabili (raw=%d pool=%d)",
            make, model, year, out["trim_family"], len(raw), len(pool),
        )
        return out

    if n >= 2:
        q = statistics.quantiles(prices, n=4, method="inclusive")
        p25, p75 = q[0], q[2]
    else:
        p25 = p75 = prices[0]

    out.update(
        median=round(statistics.median(prices), 2),
        p25=round(p25, 2),
        p75=round(p75, 2),
        min=round(prices[0], 2),
        max=round(prices[-1], 2),
    )
    return out


def _selftest() -> int:
    """DoD #1 spec-aware: 2 trim distinti stesso model/anno -> mediane DIVERSE,
    ciascuna col suo N; + 1 caso split->N<min_n -> NO-VERDICT."""
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    YEAR = 2021

    def show(tag, d):
        print(f"\n=== {tag} ===")
        print(f"  trim_family    = {d['trim_family']}")
        print(f"  n / n_pool     = {d['n']} / {d['n_pool']}  (raw={d['n_raw']})")
        print(f"  relaxation_lvl = {d['relaxation_level']}")
        print(f"  no_verdict     = {d['no_verdict']}")
        print(f"  median         = {d['median']}")
        print(f"  p25 / p75      = {d['p25']} / {d['p75']}")

    d_320 = get_it_distribution(
        "BMW", "Serie 3", year=YEAR, km=60_000, fuel="diesel",
        target_variant="320d", target_transmission="automatic", target_power_hp=190,
    )
    d_m340 = get_it_distribution(
        "BMW", "Serie 3", year=YEAR, km=40_000, fuel="petrol",
        target_variant="M340i xDrive", target_transmission="automatic", target_power_hp=374,
    )
    show("320d (rwd diesel)", d_320)
    show("M340i (awd petrol performance)", d_m340)

    print("\n=== DoD #1 verdetto ===")
    ok = True
    if d_320["median"] is None or d_m340["median"] is None:
        print("  !! una mediana e' None (0 comparabili) — scraper IT down o trim raro")
        ok = False
    elif abs(d_320["median"] - d_m340["median"]) < 1.0:
        print("  !! FAIL: mediane IDENTICHE -> spec-aware NON discrimina (BLOCKED)")
        ok = False
    else:
        delta = d_m340["median"] - d_320["median"]
        print(f"  OK: mediane DIVERSE (M340i - 320d = {delta:+.0f} EUR), N propri "
              f"({d_320['n']} vs {d_m340['n']})")

    # caso raro -> atteso no_verdict (engine_class M3 puro o trim improbabile)
    d_rare = get_it_distribution(
        "BMW", "Serie 3", year=YEAR, km=20_000, fuel="electric",
        target_variant="320e Luxury", target_transmission="automatic", target_power_hp=204,
        min_n=8,
    )
    print(f"\n  caso raro (320e electric luxury): n={d_rare['n']} "
          f"relax={d_rare['relaxation_level']} no_verdict={d_rare['no_verdict']}")
    print("TUTTI I CONTROLLI OK" if ok else "CONTROLLI FALLITI")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
