# RESUME S262 — chiudere l'anello PDF (T2/T3) + probe profondità pool IT

**Generato**: 2026-06-10 · chiusura S261 (context budget 50%→stop pre-edit) · `PLAN.md` = source-of-truth, questo è il breadcrumb attuabile.

## STATO EREDITATO (verificato live in S261, non assunto)
- **S259 spec-aware**: IMPLEMENTATO in `tools/it_market_price.py` (`derive_trim_family` + `get_it_distribution` con filtro L0→L3). DoD#1 verde (mediane diverse per trim).
- **S260 no-fusione**: VALIDATO. Livelli sono **L0→L3** (4 livelli, indici 0-3). Il vecchio L4 (droppa drivetrain) è stato RIMOSSO in S259-bis. `relaxation_level` max = 3. Test cablato: `tools/tests/test_no_fusion_ladder.py` 4/4. NON reintrodurre L4.
- **S261**: solo de-risking, ZERO edit. Mappa plumbing verificata sotto.

## PRE-REQ VERIFICATO (le 3 claim S260 reggono — controllate riga per riga in S261)
1. `tools/on_demand_runner.py:482` → `get_it_distribution(v_make, v_model, v_year, v_km)` è **trim-blind** (call legacy, manca target_variant/fuel/transmission/power).
2. `tools/on_demand_runner.py:507-509` → `if not margin_passed: return None`. È VETO DI PRODUZIONE CORRETTO (zero-PASS = nessun dossier al dealer). **NON rimuoverlo.** T2/T3 si fanno con harness separato che invoca `generate_dossier` direttamente.
3. `tools/scripts/pdf_generator_enterprise.py:892-895` → label binaria PASS/REJECT. Manca ramo NO_VERDICT.

## EDIT ESATTI ANELLO (mechanici, no esplorazione)

### Punto 1 — runner spec-aware (`tools/on_demand_runner.py`, dentro il loop a riga ~482)
I `v` sono **dict** (non oggetti Listing). Chiavi: `variant`(str), `fuel_type`(str value, default 'unknown'), `transmission`(str value, default 'unknown'), `power_hp`(int).
GOTCHA: `derive_trim_family` normalizza `transmission 'unknown'→None` ma **NON** `fuel 'unknown'` → passare `fuel=None` quando 'unknown', altrimenti il match over-restringe a comparabili fuel="unknown" (=0).
Sostituire la call:
```python
ftv = v.get('fuel_type') or None
if ftv == 'unknown': ftv = None
trv = v.get('transmission') or None
it = get_it_distribution(
    v_make, v_model, v_year, v_km, fuel=ftv,
    target_variant=v.get('variant') or '',
    target_transmission=trv,
    target_power_hp=int(v.get('power_hp', 0) or 0),
)
```
Poi DOPO `if not it.get('median')`: aggiungere skip su `it.get('no_verdict')` → log "SKIP NO-VERDICT n<min_n", `continue` (in produzione no_verdict NON deve mai PASS). Riferimento pattern già validato: `tools/margin_e2e.py:38-49` (`it_for`), ma lì sono enum con `.value`, qui sono già string nel dict.

### Punto 2 — ramo NO_VERDICT nel PDF (`tools/scripts/pdf_generator_enterprise.py`)
- riga 121: commento `# "PASS" | "REJECT" | "NO_VERDICT"`.
- riga ~133 (dataclass VehicleData): aggiungere `relaxation_level: Optional[int] = None` e `no_verdict: bool = False`.
- mapping riga 1960-1972 (build VehicleData da `best`+`it_dist`): aggiungere `relaxation_level=it_dist.get('relaxation_level')`, `no_verdict=bool(it_dist.get('no_verdict'))`. Se `it_dist.get('no_verdict')` → forzare `margin_decision='NO_VERDICT'`.
- metodo `_create_margin_verdict_section` (881-906): branch a 3 vie. Per NO_VERDICT il `decision_label` DEVE riportare **N e relaxation_level** (richiesta esplicita Luke S261 — un NO-VERDICT muto è inutile):
  `f"NO-VERDICT — comparabili insufficienti (N={vehicle.it_n or 0}, livello L{vehicle.relaxation_level if vehicle.relaxation_level is not None else '-'})"`.
  is_pass resta solo per PASS; REJECT e NO_VERDICT etichette distinte.

## DoD S262 (terminal fact reali — Rule 1b, tutti + FASE 0 verde)
- **T1 [veto prod intatto]**: `python3 -m tools.margin_gate` → X1 REJECT EXIT 0 (smoke, conferma non-regressione).
- **T2 [REJECT nel repo]**: harness che inietta X1 (prezzo 21795 / mercato 22862) via `generate_dossier` diretto → PDF NEL REPO con CoVe alto + margine REJECT + decisione finale REJECT. Path incollato.
- **T3 [NO-VERDICT nel repo]**: harness con veicolo su pool thin (no_verdict=True) → PDF NEL REPO che renderizza "NO-VERDICT N=.. L.." (NON muto). Path incollato.
- T2/T3 via harness diretto (NON il runner reale — quello ha veto `return None`).

## PROBE PROFONDITÀ POOL IT (dopo anello, o sessione dedicata se budget)
**Domanda unica**: aumentando profondità, le famiglie ESATTE si riempiono (N≥8) o il mercato non le contiene? (Discrimine "non li prendo tutti" vs "non esistono".) Decide se industrializzare scraping (stealth/scaling — solo SE famiglie si riempiono) o cambiare forma verdetto (bande prezzo / intervallo confidenza).
**Metodo idempotente, throwaway, NO infra nuova**:
- 3-4 famiglie concrete: 320d xDrive 2021, 318d 2021, 330i petrol 2021, M340 2021.
- Per ciascuna: scrape AutoScout24.it (`AutoScoutScraper("autoscout24_it").scrape_model`) con anno±2, paginazione profonda.
- Conta N usando le STESSE chiavi del gate: `derive_trim_family` + `_match` a OGNI livello L0→L3. **Output = riga per famiglia: `L0=.. L1=.. L2=.. L3=..`**. NON un N generico (320d 2021 ne conta 12, ma 320d xDrive 2021 diesel a L0 ne conta 2 — il numero che decide è quello che il gate vede).
- Esito A (famiglie N≥8 a L0-L1) → B3 = industrializza scraper IT (proxy/fingerprint/rate-limit) con DoD su famiglie-con-N, non listing totali.
- Esito B (N=1-3 anche pescando tutto) → mercato non li contiene → verdetto a bande, NON mediana puntuale. NON costruire scraping enterprise.

## min_n
Resta 8 (MIN_N_DEFAULT). NON ratificato — ratifica dopo dati probe (distribuzione N per famiglia reale).

## VINCOLI
- NON delegare implementazione (S258: subagent esaurì context senza implementare). Main context, e2e REDIRETTO su file (`> /tmp/s262.txt 2>&1`, leggi tail/grep — tabella 22 righe brucia context).
- NON toccare `cove_engine_v4.py`. Nessuna azione esterna (dealer/WA). NON shared-state a saturazione.
- FUORI SCOPE: stealth scraping, scaling, mobile.de adapter — tutto rinviato a Esito A del probe.
