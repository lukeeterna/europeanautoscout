# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-09` · sessione S258 · task: spec-aware trim filter in it_market_price.py

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Come riprendere

1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>`  — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md`: tabella anelli (GENERATA) + task corrente + prossimi step

Se `SESSION_DIRTY.md` esiste in questa cartella, risolvi PRIMA i conflitti.

---

## Task S258 — INTERROTTO A CONTEXT 66% (lavoro NON iniziato)

### Problema da risolvere
`tools/it_market_price.py` → `get_it_distribution()` filtra comparabili IT solo per make/model/anno±1/fascia-km.
NON filtra per TRIM. Risultato: mediana mescola 318i base + M340i → falso-pass.

### Prova del problema (e2e reale BMW Serie 3 2021-2024)
- Colonna mercato_IT: N=19 identico per ogni anno
- Mediane incoerenti: 2021→43550, 2024→36000 (più nuova costa meno = pool trim-blind)
- M340i 2024 (DE €51499) vs mediana €36000 pooled → REJECT -48% falso

### File da modificare (in questo ordine)
1. `tools/it_market_price.py` — aggiungere `derive_trim_family()` + filtro spec-aware + allargamento progressivo
2. `tools/margin_e2e.py` — aggiornare `it_for()` per passare spec listing DE, cache per (year, trim-family)

### Cosa fare PRIMA di editare (Rule 1d)
```bash
cp tools/it_market_price.py tools/it_market_price.py.s258.bak
cp tools/margin_e2e.py tools/margin_e2e.py.s258.bak
ls -la tools/*.bak
```

### Idempotenza: verifica prima di scrivere
```bash
grep -n "derive_trim_family" tools/it_market_price.py
```
Se esce output, la modifica è già applicata — non duplicare.

### Specifiche derive_trim_family (BMW Serie 3 come reference)
```python
def derive_trim_family(variant: str, fuel, transmission, power_hp) -> dict:
    # engine_class: estrai numero (318/320/330/340/M3...) → fascia
    # drivetrain: "xdrive" case-insensitive → "awd" / "rwd"
    # trim_line: M-Sport / Luxury / Advantage / Sport Line / base
    # fuel: da enum fuel_type.value
    # transmission: da enum transmission.value
    # DEVE gestire stringhe sporche/vuote senza crashare
    # NESSUN LLM/vector-db — solo regex/string matching deterministico
```

### Livelli allargamento progressivo (ordine FISSO)
- L0: engine_class+drivetrain+trim_line+fuel+km-band
- L1: allarga fascia km
- L2: anno ±1 → ±2
- L3: rilassa trim_line (tieni engine_class+drivetrain+fuel)
- L4: rilassa drivetrain → famiglia engine più ampia

Il dict di ritorno include: `relaxation_level`, `no_verdict=True` se N < MIN_N dopo tutto.

### Firma target (retrocompatibile)
```python
get_it_distribution(
    make, model, year, km, fuel=None,
    *, target_variant=None, target_transmission=None,
    target_power_hp=None, km_band=..., year_span=1, min_n=8
)
```

### Definition of Done (con numeri reali)
Esegui:
```bash
python3 -m tools.margin_e2e --make BMW --model "Serie 3" --year-min 2021 --year-max 2024 --pages 2 --limit 22
```
Dimostra:
- (a) Due trim distinti stesso anno → mediane IT diverse, N diverso
- (b) ≥1 caso N < MIN_N → NO-VERDICT emesso (non numero sicuro)
- (c) X1 falsificazione resta REJECT (hardcoded margin_e2e, non toccare)

### Stato file al momento dell'interruzione
- `tools/it_market_price.py` — LETTO, NON modificato (147 righe)
- `tools/margin_e2e.py` — LETTO, NON modificato (97 righe)
- Nessun .bak creato (lavoro non iniziato)

### Vincoli critici
- NON toccare `src/cove/cove_engine_v4.py`
- NON committare (Luke verifica prima)
- MIN_N provvisorio = 8 (proponi aggiornamento basato su distribuzione N reale)
