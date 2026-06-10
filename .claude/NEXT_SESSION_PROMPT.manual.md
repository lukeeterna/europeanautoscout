# RESUME S262 — chiudere l'anello PDF (T2/T3) — ISOLATO. Probe → S263 separato.

**Generato**: 2026-06-10 · chiusura S261 (de-risking) + peer review Claude AI · `PLAN.md` = source-of-truth.

> ORDINE NON NEGOZIABILE (peer review): **S262 = SOLO anello (T1/T2/T3)**. Il probe pool IT
> apre la domanda strategica grossa e se scivola nella stessa sessione si mangia il budget e
> l'anello resta BLOCKED un altro giro. L'anello è il fatto terminale mai prodotto su questo
> asse: chiudilo isolato. **Probe = S263, sessione sua.** NON intrecciarli.

## STATO EREDITATO (verificato live S261, non assunto)
- **S259 spec-aware**: IMPLEMENTATO in `tools/it_market_price.py` (`derive_trim_family` +
  `get_it_distribution` filtro L0→L3). DoD#1 verde (mediane diverse per trim).
- **S260 no-fusione**: VALIDATO. Livelli **L0→L3** (indici 0-3), L4 rimosso. Test
  `tools/tests/test_no_fusion_ladder.py` 4/4. NON reintrodurre L4.
- **S261**: solo de-risking, ZERO edit. Mappa plumbing sotto.

## EDIT ESATTI ANELLO (meccanici, no esplorazione)

### Punto 1 — runner spec-aware (`tools/on_demand_runner.py`, loop ~riga 482)
`v` = dict. Chiavi: `variant`(str), `fuel_type`(str value default 'unknown'),
`transmission`(str value default 'unknown'), `power_hp`(int).
GOTCHA: passare `fuel=None` quando 'unknown' (derive_trim_family non lo normalizza).
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
Dopo `if not it.get('median')`: aggiungere skip su `it.get('no_verdict')` →
log "SKIP NO-VERDICT n<min_n", `continue`. In produzione no_verdict NON deve mai PASS.

### Punto 1-bis — chiudere il gotcha fuel ANCHE in `tools/margin_e2e.py` (STESSO GIRO)
Peer review: il gotcha `fuel 'unknown'` è latente anche in `margin_e2e.py:39` — se
`fuel_type=FuelType.UNKNOWN` → `ftv='unknown'` → over-restringe a comparabili fuel="unknown" (=0).
È la **stessa classe del bug mediana-fusa**: input non normalizzato che falsa silenziosamente il
match (qui over-restringe → NO-VERDICT spurio, là fondeva → falso-PASS). Radice identica.
Fix in `it_for` (margin_e2e.py): `if ftv == 'unknown': ftv = None` prima della call.
NON lasciarlo aperto: trappola che riappare.

### Punto 2 — ramo NO_VERDICT nel PDF (`tools/scripts/pdf_generator_enterprise.py`)
- **`it_n` GIÀ ESISTE** su VehicleData (riga 132, verificato S261) — la label NON stampa 0 default. OK.
- riga 121: commento `# "PASS" | "REJECT" | "NO_VERDICT"`.
- riga ~133 (VehicleData): aggiungere SOLO `relaxation_level: Optional[int] = None`,
  `no_verdict: bool = False`.
- mapping righe 1960-1972: aggiungere `relaxation_level=it_dist.get('relaxation_level')`,
  `no_verdict=bool(it_dist.get('no_verdict'))`. Se `it_dist.get('no_verdict')` → forzare
  `margin_decision='NO_VERDICT'`.
- metodo `_create_margin_verdict_section` (881-906): branch 3 vie. NO_VERDICT label CON
  N e livello REALI (non 0/'-' di default — è il numero che conta):
  `f"NO-VERDICT — comparabili insufficienti (N={vehicle.it_n or 0}, livello L{vehicle.relaxation_level if vehicle.relaxation_level is not None else '-'})"`.

## DoD S262 (terminal fact reali — Rule 1b)
- **T1 [veto prod intatto]**: `python3 -m tools.margin_gate` → X1 REJECT EXIT 0 (non-regressione).
- **T2 [REJECT nel repo]**: harness inietta X1 (21795/22862) via `generate_dossier` diretto →
  PDF NEL REPO, CoVe alto + margine REJECT + decisione finale REJECT. Path incollato.
- **T3 [NO-VERDICT nel repo]**: harness veicolo pool thin (no_verdict=True) → PDF NEL REPO.
  VERIFICA CHIAVE (peer review): che renderizzi **N e livello REALI**, non uno zero/'-' di default.
  Aprire il PDF e leggere il numero. Path incollato.
- T2/T3 via harness diretto (NON il runner reale — ha veto `return None`).

## min_n
Resta 8 (MIN_N_DEFAULT). NON ratificato — ratifica dopo dati probe S263.

## VINCOLI S262
- NON delegare implementazione (S258: subagent esaurì context). Main context, e2e REDIRETTO su
  file (`> /tmp/s262.txt 2>&1`, leggi tail/grep).
- NON toccare `cove_engine_v4.py`. Nessuna azione esterna (dealer/WA). NON shared-state a saturazione.
- FUORI SCOPE S262: probe pool IT (→ S263), stealth scraping, scaling, mobile.de adapter.

---

## S263 (SESSIONE SEPARATA — solo dopo anello verde) — PROBE PROFONDITÀ POOL IT
**Inquadramento (peer review): nessun esito "fallisce".** Esito A → lo scraping enterprise
ripaga, lo costruisci con convinzione. Esito B → ti risparmia l'autostrada verso un pozzo vuoto
e ti dice che il prodotto è un verdetto a BANDE ("questa auto sta nella fascia alta/bassa del
mercato IT per la sua configurazione") — vendibile a un dealer. Scopri QUALE prodotto stai
costruendo. Per questo vale mezza sessione e va PRIMA di qualsiasi riga di stealth.
**Domanda unica**: aumentando profondità le famiglie ESATTE si riempiono (N≥8) o il mercato
non le contiene?
**Metodo idempotente, throwaway, NO infra nuova**:
- Famiglie: 320d xDrive 2021, 318d 2021, 330i petrol 2021, M340 2021.
- Per ciascuna: `AutoScoutScraper("autoscout24_it").scrape_model` anno±2, paginazione profonda.
- Conta N con le STESSE chiavi del gate: `derive_trim_family` + `_match` a OGNI livello L0→L3.
  **Output = riga per famiglia: `L0=.. L1=.. L2=.. L3=..`** (NON N generico: 320d 2021 conta 12,
  ma 320d xDrive 2021 diesel a L0 ne conta 2 — il numero che decide è quello che vede il gate).
- Esito A (N≥8 a L0-L1) → B3 industrializza scraper IT, DoD su famiglie-con-N non listing totali.
- Esito B (N=1-3 pescando tutto) → verdetto a bande, NON mediana puntuale. NON costruire stealth.
