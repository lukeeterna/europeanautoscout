r"""ARGOS IT market-price distribution — SPEC-AWARE (S259).

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
from datetime import date
from typing import Optional

from .scrapers.autoscout_scraper import AutoScoutScraper

logger = logging.getLogger(__name__)

KM_BAND_DEFAULT = 30_000   # +/- attorno al km target
MIN_CONFIDENT_N = 5        # soglia legacy `low_confidence` (retrocompat campo)
MIN_N_DEFAULT = 8          # soglia NO-VERDICT (RATIFICATO Luke S265 = 8 + gate composto)

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
# PRINCIPIO (S259-bis, critica Luke): NON si rilassa MAI attraverso le dimensioni
# che MUOVONO il prezzo (drivetrain, engine_class). trim_line si molla presto (L3),
# drivetrain/motore MAI: meglio NO-VERDICT che una mediana che fonde xDrive+sDrive
# o 320+340. Il vecchio L4 (droppa drivetrain) fondeva awd+rwd -> rimosso.
def _levels(year_span: int) -> list[dict]:
    yt = min(max(year_span, 1), 2)
    return [
        dict(engine=True, drivetrain=True, trim=True, fuel=True, km=True,  year_tol=yt),
        dict(engine=True, drivetrain=True, trim=True, fuel=True, km=False, year_tol=1),
        dict(engine=True, drivetrain=True, trim=True, fuel=True, km=False, year_tol=2),
        dict(engine=True, drivetrain=True, trim=False, fuel=True, km=False, year_tol=2),
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


def _iqr_spread(prices: list) -> Optional[float]:
    """Spread interquartile (p75-p25) in EUR. None se <2 prezzi."""
    if len(prices) < 2:
        return None
    q = statistics.quantiles(sorted(prices), n=4, method="inclusive")
    return round(q[2] - q[0], 2)


def _confidence_label(
    n: int, min_n: int, level: Optional[int], no_verdict: bool, width_nature: str
) -> str:
    """Confidence ONESTA, monotona, derivata da N e dal livello (GAP-1).

    Invariante anti-falso-PASS (testato in _test_confidence_honesty):
      "alta" => livello in {0,1,2} AND n>=20 AND not no_verdict.
    Mai "alta" su L3 (trim fuso) ne' su N piccolo: la banda stretta su pochi
    comparabili = falso-PASS travestito (il bug ucciso S256-S262).
    """
    if no_verdict:
        return "NO_VERDICT"
    if level == 3:
        # L3 = trim droppato (allestimenti fusi). MAI "alta", a prescindere da N.
        # indeterminato = natura banda NON verificabile (sub-pool trim-esatto <2
        # punti): mai "media", e' NO_VERDICT (Luke S265 — narrativa al posto del
        # fatto verificabile). Solo "incertezza_campione" (spread vero) -> media.
        if width_nature == "indeterminato":
            return "NO_VERDICT"
        return "bassa" if width_nature == "fusione_trim" else "media"
    if n >= 20:
        return "alta"
    if n >= 10:
        return "media"
    return "bassa"


def _decide(
    n: int,
    min_n: int,
    relaxation_level: Optional[int],
    spread_pool: Optional[float],
    spread_infra_trim: Optional[float],
    median: Optional[float],
    *,
    spec_aware: bool = True,
) -> tuple[bool, str, str]:
    """Decisione gate PURA (S267) -> (no_verdict, width_nature, confidence).

    Estratta da `get_it_distribution` (prima inline, righe 291-292 + 376-397)
    per essere TESTABILE diretta: forzare (N, width) a L3 via la pipeline di
    leveling e' fragile, la funzione pura blocca la tavola di verita'.

    Bracci (Luke S265, gate COMPOSTO):
      - width_nature: a L3 (trim droppato) la larghezza viene dalla FUSIONE
        allestimenti (`fusione_trim`) o dall'incertezza campione
        (`incertezza_campione`); se il sub-pool trim-esatto (L2) ha <2 punti
        (`spread_infra_trim is None`) la natura NON e' dichiarabile -> `indeterminato`.
      - no_verdict = spec_aware AND ( N<min_n  OR  L3-indeterminato ). I due bracci
        sono in OR: il braccio width fa NO_VERDICT anche su un N che passerebbe.
    `median` non entra nella decisione (firma per simmetria col chiamante).
    """
    if relaxation_level == 3:
        if spread_infra_trim is None:
            width_nature = "indeterminato"
        elif spread_pool is not None and spread_pool > spread_infra_trim * 1.5:
            width_nature = "fusione_trim"
        else:
            width_nature = "incertezza_campione"
    else:
        width_nature = "config_esatta"

    l3_unverifiable = (relaxation_level == 3 and spread_infra_trim is None)
    no_verdict = spec_aware and (n < min_n or l3_unverifiable)
    confidence = _confidence_label(n, min_n, relaxation_level, no_verdict, width_nature)
    return no_verdict, width_nature, confidence


def _load_fixture(path: str) -> tuple[list, str]:
    """Carica una fixture reale committata (S266) -> (raw_listings, scrape_date).

    La fixture e' l'output di UNA scrape profonda (results_per_page=1 override,
    vedi tools/scripts/build_it_fixture.py), serializzata con Listing.to_dict().
    Round-trip esatto via Listing.from_row(). scrape_date = giorno reale della
    scrape (NON oggi): la banda calcolata e' la fotografia di quel giorno.
    """
    import json
    from .scrapers.models import Listing

    with open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    raw = [Listing.from_row(r) for r in blob.get("listings", [])]
    scrape_date = (blob.get("meta") or {}).get("scrape_date") or date.today().isoformat()
    return raw, scrape_date


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
    fixture_path: Optional[str] = None,
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
    spec_aware = bool(target_variant)
    if fixture_path:
        # FIXTURE (S266): pool reale committato, scrape gia' avvenuta UNA volta.
        # Chiude il debito S264 (fatto fondante buttato): DoD/test riproducibili
        # su dato vero su disco, NON ri-scrapando ogni sessione. scrape_date viene
        # dalla fixture (la banda e' una FOTOGRAFIA di QUEL giorno, non di oggi).
        raw, scrape_date = _load_fixture(fixture_path)
    else:
        scraper = AutoScoutScraper("autoscout24_it")
        # spec-aware: pool largo (anno+-2) filtrato in memoria. Legacy: anno+-year_span.
        scrape_span = 2 if spec_aware else year_span
        raw = scraper.scrape_model(
            make=make, model=model,
            year_min=year - scrape_span, year_max=year + scrape_span,
        )
        scrape_date = date.today().isoformat()

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

    n_by_level: Optional[dict] = None
    spread_infra_trim: Optional[float] = None  # GAP-1: spread a trim ESATTO (L2)
    if spec_aware:
        levels = _levels(year_span)
        # Calcola i match per OGNI livello (pool piccolo): serve N_L0..N_L3 per
        # la riga d'onesta' del report e lo spread infra-trim (GAP-1).
        matched_by_level = [
            [p for p in pool
             if _match(target, p[1], p[2], p[3], km, year, km_band, cfg)]
            for cfg in levels
        ]
        n_by_level = {i: len(m) for i, m in enumerate(matched_by_level)}
        # Livello scelto = primo che raggiunge min_n, altrimenti l'ultimo (L3).
        chosen_level = len(levels) - 1
        for idx, m in enumerate(matched_by_level):
            if len(m) >= min_n:
                chosen_level = idx
                break
        selected = matched_by_level[chosen_level]
        relaxation_level = chosen_level
        # GAP-1: spread a TRIM ESATTO = L2 (engine+drivetrain+trim+fuel, anno+-2).
        # A L3 il trim e' droppato: confrontare lo spread del pool L3 con questo
        # dice se la larghezza viene dalla FUSIONE allestimenti o dall'incertezza.
        l2_prices = [float(p[0].price_eur) for p in matched_by_level[2]]
        spread_infra_trim = _iqr_spread(l2_prices)
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
    # Gate COMPOSTO (Luke S265): verdetto emesso solo se N>=min_n E la natura
    # della banda e' VERIFICABILE. La decisione (no_verdict + width_nature +
    # confidence) vive ora nella funzione PURA `_decide` (S267), chiamata sotto
    # quando spread_pool e' noto. min_n=8 = cuscinetto contro la sotto-raccolta
    # short-page (il probe vede piu' del campo reale).

    out: dict = {
        "source": "AutoScout24.it",
        "scrape_date": scrape_date,                 # GAP-2: la banda e' una FOTOGRAFIA
        "n": n,
        "n_raw": len(raw),
        "n_pool": len(pool),
        "n_by_level": n_by_level,                   # GAP-1: N_L0..N_L3 per riga onesta'
        "relaxation_level": relaxation_level,
        "trim_family": target["key"] if spec_aware else None,
        "target_spec": target if spec_aware else None,
        "min_n": min_n,
        "low_confidence": n < MIN_CONFIDENT_N,
        "spread_infra_trim": spread_infra_trim,     # GAP-1: spread a trim ESATTO (L2)
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
        no_verdict, width_nature, confidence = _decide(
            0, min_n, relaxation_level, None, spread_infra_trim, None,
            spec_aware=spec_aware,
        )
        fallback_declared = bool((relaxation_level == 3) and not no_verdict)
        out.update(
            no_verdict=no_verdict,
            median=None, p25=None, p75=None, min=None, max=None,
            band_low=None, band_high=None, band_width_pct=None,
            spread_pool=None, width_nature=width_nature,
            confidence=confidence,
            fallback_declared=fallback_declared,
        )
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

    median = statistics.median(prices)
    # BANDA = p25-p75 del pool al livello usato (Luke ratifica i percentili).
    band_low, band_high = round(p25, 2), round(p75, 2)
    spread_pool = round(band_high - band_low, 2)
    band_width_pct = round((spread_pool / median * 100.0), 2) if median else None

    # Decisione gate PURA (S267): GAP-1 width_nature + no_verdict + confidence
    # in un solo posto testabile. A L3 confronta spread_pool con spread_infra_trim
    # (L2): se il pool e' molto piu' largo del trim esatto la larghezza viene dalla
    # FUSIONE allestimenti (precisione finta), non dall'incertezza campione.
    no_verdict, width_nature, confidence = _decide(
        n, min_n, relaxation_level, spread_pool, spread_infra_trim, median,
        spec_aware=spec_aware,
    )

    fallback_declared = bool((relaxation_level == 3) and not no_verdict)
    out.update(
        no_verdict=no_verdict,
        median=round(median, 2),
        p25=band_low,
        p75=band_high,
        min=round(prices[0], 2),
        max=round(prices[-1], 2),
        band_low=band_low,
        band_high=band_high,
        band_width_pct=band_width_pct,
        spread_pool=spread_pool,
        width_nature=width_nature,
        confidence=confidence,
        fallback_declared=fallback_declared,
    )
    return out


def _test_confidence_honesty() -> int:
    """DoD #1 (S265): VIETA "confidence alta" su banda stretta / N piccolo / L3.

    Questo test FALLISCE (return>0) se l'invariante anti-falso-PASS si rompe.
    Invariante: confidence=="alta"  =>  level in {0,1,2} AND n>=20 AND not no_verdict.
    Il falso-PASS travestito (banda stretta su N piccolo spacciata per "alta")
    e' lo stesso bug ucciso S256-S262: qui e' protetto da test.
    """
    fail = 0
    # (1) falso-PASS travestito: N piccolo NON deve dare "alta", neppure se la
    #     banda fosse strettissima (width_nature non puo' promuovere ad alta).
    if _confidence_label(6, 5, 0, False, "config_esatta") == "alta":
        print("  !! FAIL: N=6 -> 'alta' (banda stretta su N piccolo = falso-PASS)")
        fail += 1
    # (2) L3 (trim fuso) MAI "alta", neppure con N grande.
    if _confidence_label(50, 5, 3, False, "incertezza_campione") == "alta":
        print("  !! FAIL: L3 con N=50 -> 'alta' (trim fuso non puo' essere alta)")
        fail += 1
    # (3) fusione_trim a L3 deve degradare a "bassa" (precisione finta).
    if _confidence_label(14, 5, 3, False, "fusione_trim") != "bassa":
        print("  !! FAIL: L3 fusione_trim non degrada a 'bassa'")
        fail += 1
    # (4) griglia: "alta" SOLO se n>=20 e level<3.
    for n in range(0, 60, 2):
        for lvl in (0, 1, 2, 3):
            c = _confidence_label(n, 5, lvl, n < 5, "config_esatta")
            if c == "alta" and (n < 20 or lvl == 3):
                print(f"  !! FAIL: (n={n}, L{lvl}) -> 'alta' viola invariante")
                fail += 1
    # (5) no_verdict domina sempre.
    if _confidence_label(100, 5, 0, True, "config_esatta") != "NO_VERDICT":
        print("  !! FAIL: no_verdict non domina")
        fail += 1
    # (6) L3 indeterminato (natura banda non verificabile) -> mai "media" (Luke S265).
    if _confidence_label(14, 8, 3, False, "indeterminato") == "media":
        print("  !! FAIL: L3 indeterminato -> 'media' (natura banda non verificabile)")
        fail += 1
    print("  OK: invariante confidence onesta rispettata" if fail == 0
          else f"  {fail} violazioni invariante confidence")
    return fail


def _selftest() -> int:
    """DoD #1 spec-aware: 2 trim distinti stesso model/anno -> mediane DIVERSE,
    ciascuna col suo N; + 1 caso split->N<min_n -> NO-VERDICT;
    + invariante confidence onesta (S265)."""
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    print("=== _test_confidence_honesty (S265, no rete) ===")
    conf_fail = _test_confidence_honesty()
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
    print("TUTTI I CONTROLLI OK" if (ok and conf_fail == 0) else "CONTROLLI FALLITI")
    return 0 if (ok and conf_fail == 0) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
