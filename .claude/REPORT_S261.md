# REPORT S261 + NEXT PROMPT S262 — ARGOS anello PDF (CoVe⊕margine)

**Data**: 2026-06-10 · **Branch**: s210/audit-master-plan · **Commit**: dd4200a
**Esito**: VERDE-come-handoff (de-risking completo, zero codice dirty). Stop a context 55% pre-edit live.

---

# PARTE 1 — REPORT SESSIONE S261

## Obiettivo entrante
Chiudere l'anello PDF (T2/T3): un dossier reale che mostri sia CoVe (bontà auto) sia
verdetto margine (bontà affare), con veto indipendente. Ereditato da S260 come BLOCKED-ON budget.

## Cosa è stato fatto — DE-RISKING (non codice)
La sessione NON ha prodotto edit. Ha prodotto una mappa di plumbing verificata riga-per-riga
che trasforma S262 da esplorazione (~2h) a esecuzione meccanica (~30 min).

### Le 3 claim del handoff S260 — TUTTE VERIFICATE live
1. `tools/on_demand_runner.py:482` → `get_it_distribution(v_make, v_model, v_year, v_km)`
   è **trim-blind** (call legacy: mancano target_variant/fuel/transmission/power). CONFERMATO.
2. `tools/on_demand_runner.py:507-509` → `if not margin_passed: return None`.
   È **VETO DI PRODUZIONE CORRETTO** (zero-PASS = nessun dossier al dealer). NON va rimosso.
   T2/T3 si fanno con harness separato. CONFERMATO.
3. `tools/scripts/pdf_generator_enterprise.py:892-895` → label binaria PASS/REJECT,
   nessun ramo NO_VERDICT. CONFERMATO.

### Scoperte non ovvie (il vero valore della sessione)
- **Dict vs enum**: nel runner i `v` sono dict (`v.get('fuel_type')` = string value già risolto),
  in `margin_e2e.py` sono oggetti Listing (`l.fuel_type.value` = enum). Path diversi, stessa logica.
- **Gotcha `fuel 'unknown'`**: `derive_trim_family` normalizza `transmission 'unknown'→None`
  ma **NON** `fuel 'unknown'`. Passare fuel='unknown' over-restringe il match a comparabili
  fuel="unknown" (=0 risultati). Va normalizzato a None nel caller. (Latente anche in margin_e2e
  se fuel_type=UNKNOWN → annotato come da risolvere, fuori scope S261.)
- **Livelli L0→L3, non L4**: il manual prompt S259 citava L0-L4, ma S259-bis ha **RIMOSSO L4**
  (droppa drivetrain) su critica Luke — mai fondere awd+rwd o 320+340. `relaxation_level` max = 3.
  Validato da `tools/tests/test_no_fusion_ladder.py` 4/4 (S260). NON reintrodurre L4.
- **`VehicleData` manca `relaxation_level`**: per renderizzare un NO-VERDICT non-muto
  ("N=1 a L3", non "NO-VERDICT" secco) serve aggiungere il campo + mapparlo da `it_dist`
  alle righe 1960-1972 di `pdf_generator_enterprise.py`.

## Decisioni prese
- **Veto produzione intatto + harness separato per T2/T3** (approvato Luke). "Il test vuole un PDF
  NO-VERDICT" ≠ "la produzione deve generarlo": rimuovere `return None` farebbe mandare al dealer
  auto sotto pavimento. Regressione business evitata.
- **NO-VERDICT non-muto** (richiesta Luke): il ramo PDF renderizza N + relaxation_level.
- **Stop pre-edit a 55%**: editare il runner senza poterlo E2E-verificare (serve scrape live)
  avrebbe lasciato stato misto VERDE/UNVERIFIED = PARTIAL (vietato vincolo #6) e shared-state
  mid-saturation (anti-pattern `global_context_gate_lag`). Fork pre-autorizzato da Luke.
- **Probe profondità prima di qualsiasi scraping enterprise** (decisione strategica Luke,
  sottoscritta con dati): il blocker è il pool IT a N=19 che collassa a NO-VERDICT con spec-aware.
  Discrimine "non li prendo tutti" (→ scaling/stealth) vs "non esistono" (→ verdetto a bande).
  Non noto a oggi → probe corto lo risolve. Costruire stealth/scaling prima = ottimizzare
  un collo di bottiglia non ancora confermato.

## Vincoli rispettati
- #1 verifica fattuale: ogni claim controllata su codice reale, non da memoria.
- #4 critica strutturale: autocritica 4 punti sul veto (vedi turno).
- #6 no PARTIAL: chiusura VERDE-come-handoff.
- #7 context budget: stop a 55%, no sforo 60%.
- #9 no "hai ragione" diplomatico: accordo sul probe motivato con dato N=19.
- Delegation: eccezione documentata (S258 subagent fallì → main context deterministico).

## Stato finale anelli (refresh S261)
1 UNVERIFIED · 2 VERIFIED · 9A VERIFIED · 9B UNVERIFIED · 5 VERIFIED · 6-7 UNVERIFIED · 8 BLOCKED

## Artefatti
- `dd4200a` — handoff S262 (questo contenuto, Parte 2).
- STATE.md NON toccato (source-of-truth, richiede OK Luke su diff header S260→S261).

---

# PARTE 2 — NEXT PROMPT S262

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
Pattern già validato: `tools/margin_e2e.py:38-49` (`it_for`).

### Punto 2 — ramo NO_VERDICT nel PDF (`tools/scripts/pdf_generator_enterprise.py`)
- riga 121: commento `# "PASS" | "REJECT" | "NO_VERDICT"`.
- riga ~133 (VehicleData): aggiungere `relaxation_level: Optional[int] = None`, `no_verdict: bool = False`.
- mapping righe 1960-1972: aggiungere `relaxation_level=it_dist.get('relaxation_level')`,
  `no_verdict=bool(it_dist.get('no_verdict'))`. Se `it_dist.get('no_verdict')` → forzare
  `margin_decision='NO_VERDICT'`.
- metodo `_create_margin_verdict_section` (881-906): branch 3 vie. Per NO_VERDICT label CON
  N e livello (richiesta esplicita Luke — NO-VERDICT muto è inutile):
  `f"NO-VERDICT — comparabili insufficienti (N={vehicle.it_n or 0}, livello L{vehicle.relaxation_level if vehicle.relaxation_level is not None else '-'})"`.

## DoD S262 (terminal fact reali — Rule 1b)
- **T1 [veto prod intatto]**: `python3 -m tools.margin_gate` → X1 REJECT EXIT 0 (non-regressione).
- **T2 [REJECT nel repo]**: harness inietta X1 (21795/22862) via `generate_dossier` diretto →
  PDF NEL REPO, CoVe alto + margine REJECT + decisione finale REJECT. Path incollato.
- **T3 [NO-VERDICT nel repo]**: harness veicolo pool thin (no_verdict=True) → PDF NEL REPO
  con "NO-VERDICT N=.. L.." (NON muto). Path incollato.
- T2/T3 via harness diretto (NON il runner reale — ha veto `return None`).

## PROBE PROFONDITÀ POOL IT (dopo anello, o sessione dedicata)
**Domanda unica**: aumentando profondità le famiglie ESATTE si riempiono (N≥8) o il mercato
non le contiene? Decide: industrializzare scraping (stealth/scaling, SOLO se si riempiono)
vs cambiare forma verdetto (bande/intervallo confidenza).
**Metodo idempotente, throwaway, NO infra nuova**:
- Famiglie: 320d xDrive 2021, 318d 2021, 330i petrol 2021, M340 2021.
- Per ciascuna: `AutoScoutScraper("autoscout24_it").scrape_model` anno±2, paginazione profonda.
- Conta N con le STESSE chiavi del gate: `derive_trim_family` + `_match` a OGNI livello L0→L3.
  **Output = riga per famiglia: `L0=.. L1=.. L2=.. L3=..`** (NON N generico: 320d 2021 conta 12,
  ma 320d xDrive 2021 diesel a L0 ne conta 2 — il numero che decide è quello che il gate vede).
- Esito A (N≥8 a L0-L1) → B3 industrializza scraper IT, DoD su famiglie-con-N non listing totali.
- Esito B (N=1-3 pescando tutto) → mercato non li contiene → verdetto a bande, NON mediana puntuale.

## min_n
Resta 8 (MIN_N_DEFAULT). NON ratificato — ratifica dopo dati probe.

## VINCOLI
- NON delegare implementazione (S258: subagent esaurì context). Main context, e2e REDIRETTO su
  file (`> /tmp/s262.txt 2>&1`, leggi tail/grep).
- NON toccare `cove_engine_v4.py`. Nessuna azione esterna (dealer/WA). NON shared-state a saturazione.
- FUORI SCOPE: stealth scraping, scaling, mobile.de adapter → rinviati a Esito A del probe.
