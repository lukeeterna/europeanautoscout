# RESUME S259 — comparabili IT spec-aware (CRITICAL PATH aperto)

**Generato**: 2026-06-09 · chiusura S258 (context budget) · leggi PLAN.md come source-of-truth, questo è il breadcrumb attuabile.

## STATO A FINE S258 (verificato live in S258, non ereditato)
**FASE 0 VERDE** (numeri reali):
- 0a: commit S255–S257 presenti (eb68342, f219ef3, 1e509c2, 68ac3ef, fd09384). NON ricostruire il gate.
- 0b: `python3 -m tools.margin_gate` → X1 REJECT (chiavi 21795, spread 1067, floor 2743, surplus -1676). EXIT 0.
- 0c: `python3 -m tools.margin_e2e --make BMW --model "Serie 3" --year-min 2021 --year-max 2024 --pages 2 --limit 22` → **8 PASS / 14 REJECT** su 22 annunci DE reali, X1 REJECT. EXIT 0.

**PROBLEMA CONFERMATO da 0c (il bug che S259 chiude):** mediana IT trim-blind e quasi year-blind. Output reale: mercato_IT 2021→43550, 2024→36000 (auto più nuova costa MENO = incoerente), N=19 identico ogni anno. M340i 2024 (DE 51499) vs €36000 pooled → REJECT -48% FALSO.

**LAVORO S258 NON INIZIATO.** Solo backup Rule 1d creati: `tools/it_market_price.py.s258.bak`, `tools/margin_e2e.py.s258.bak` (identici ai sorgenti, nessun edit — riutilizzabili/cancellabili).
**LEZIONE S258:** delega a subagent backend-architect FALLITA (esaurì il suo context leggendo i 2 file senza implementare). In S259 NON delegare: implementazione deterministica, falla in main context con output e2e REDIRETTO su file (`> /tmp/s259_e2e.txt 2>&1`, leggi solo tail/grep — la tabella 22 righe brucia context).

## OBIETTIVO 1 S259 (critical path) — spec-aware in `tools/it_market_price.py`
Deterministico (no LLM, no vector-db):
1. `derive_trim_family(variant, fuel, transmission, power_hp) -> dict`:
   - `engine_class`: regex `(?i)\bm?(\d{3})\b` su variant → "318"/"320"/"330"/"340". "M340"/"M3" → flag performance. Vuoto se assente.
   - `drivetrain`: "awd" se 'xdrive'/'quattro'/'4matic'/'allrad' in variant.lower() else "rwd".
   - `trim_line`: 'm sport'/'m-sport'/'msport'→m_sport; 'luxury'→luxury; 'advantage'→advantage; 'sport line'/'sportline'→sport_line; else base.
   - `fuel`: da fuel.value lower (NON variant). `transmission`: da transmission.value lower. Gestire variant sporco/vuoto senza crash.
2. Filtro spec-aware + allargamento progressivo IN-MEMORY (1 sola scrape: IT con year±2 km-agnostico, poi filtra a livelli):
   - L0: engine_class== AND drivetrain== AND trim_line== AND fuel== AND km±band AND anno±1
   - L1: droppa km-band → L2: anno±2 → L3: droppa trim_line → L4: droppa drivetrain (tieni engine_class+fuel)
   - Itera finché n>=min_n; registra `relaxation_level` nel dict.
3. Dict: aggiungi `relaxation_level`, `trim_family`, **`no_verdict=True`** se n<min_n anche a L4 (gate NON emette PASS → NO-VERDICT). `n` SEMPRE riportato.
4. `min_n`: oggi MIN_CONFIDENT_N=5. Raccogli distribuzione N osservata, PROPONI MIN_N a Luke (default provvisorio 8). NON sacro.
5. Optional NON nel gate (già nel prezzo comparabili stesso-trim) — solo flag qualitativa.
6. Firma retrocompatibile: `get_it_distribution(make, model, year, km, fuel=None, *, target_variant=None, target_transmission=None, target_power_hp=None, km_band=..., year_span=1, min_n=8)`.

### `tools/margin_e2e.py`
`it_for` oggi cache PER ANNO con km=0 → cambiare: cache PER (year, trim_family_key); passare variant/fuel/transmission/power del listing DE. Su `no_verdict` → SKIP (mai PASS). Stampare relaxation_level + N per riga.

## DoD S259 (terminal fact reali — Rule 1b, tutti + FASE 0 verde)
1. [spec-aware] mediane IT DIVERSE per 2 trim distinti stesso model/anno, ognuna col suo N; + ≥1 caso split→N<MIN_N → NO-VERDICT invece di numero. Incolla numeri. 2 trim mediana IDENTICA = BLOCKED.
2. [PASS reale E2E] 1 annuncio reale nel runner COMPLETO (scrape DE→CoVe→Step 2c spec-aware→PDF). PDF NEL REPO (non /tmp) con CoVe + verdetto margine + N comparabili. Path incollato.
3. [veto+falsificazione] X1 dati iniettati (21795/22862) via CoVe→Step 2c→PDF: CoVe alto nel PDF, margine REJECT nel PDF, decisione finale REJECT. PDF nel repo, path incollato.

## OBIETTIVO 2 (dopo Obj 1) — coesistenza CoVe⊕Gate nel runner reale
Gate finora verificato in ISOLAMENTO (DoD#2 S257 chiamò generate_dossier ma SALTÒ il CoVe). Nel PDF entrambi distinti: CoVe (bontà auto) + verdetto margine (bontà affare). VETO indipendente: X1 = CoVe 80/100 "CERTIFICATO" S254 MA margine REJECT → REJECT finale.

## FUORI SCOPE: mobile.de/AS24.de adapter, Vincario v3.2, invio dossier a Luke, precisione premium oltre spec-aware.
## VINCOLI: prova al layer giusto (numeri reali + PDF reale + X1→REJECT live, NON "compila"). NON toccare cove_engine_v4.py distruttivo. Nessuna azione esterna.
