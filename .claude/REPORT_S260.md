# REPORT S260 — chiusura anello (FASE 1 verde) + T2/T3 BLOCKED-ON budget

**Data**: 2026-06-09 · chiusura a context 61% (vincolo #7, gate hard 60%).
**Branch**: s210/audit-master-plan. Nessuna azione esterna.

## FASE 0 — GROUND TRUTH — VERDE (riverificato live, non ereditato)
- **a** repo=`/Users/macbook/Documents/combaretrovamiauto-enterprise`, branch=`s210/audit-master-plan`. OK
- **b** spec recuperabile: `grep -rl derive_trim_family .claude/` → `.claude/NEXT_SESSION_PROMPT.manual.md` (+ REPORT_S259.md). OK
- **c** commit gate presenti (non ricostruiti): `eb68342 f219ef3 1e509c2 68ac3ef fd09384`. OK
- **d** falsificazione X1 live: `python3 -m tools.margin_gate` → X1 (chiavi 21795) **REJECT**, surplus **-1676** (atteso -1676), spread 1067, floor 2743. OK
- **e** L4 **RIMOSSO** confermato in codice: `_levels()` (it_market_price.py:121-128) ha solo L0-L3, tutti con `drivetrain=True`+`engine=True`. Il drop drivetrain/engine sopravvive SOLO nel fallback legacy non-spec-aware (riga 226, retrocompat). Nessuna regressione. OK

## FASE 1 — PRINCIPIO NO-FUSIONE — VERDE (1a + 1b)

### 1a — trace 330i (petrol, rwd), ingresso diverso da 320d
Script: `tools/trace_330i_s260.py` · output: `.claude/trace_330i_s260.out`.
Pool reale AutoScout24.it BMW Serie 3 (anno 2019-2023): raw=19, prezzo>0 → 19 comparabili.
Target 330i = `330/rwd/base/petrol`.

| Livello | N | drivetrains | fuels | engines |
|---|---|---|---|---|
| L0 (engine+drive+trim+fuel+km, yt=1) | 0 | [] | [] | [] |
| L1 (droppa km, yt=1)                 | 0 | [] | [] | [] |
| L2 (yt=2)                            | 0 | [] | [] | [] |
| L3 (droppa trim, yt=2)               | 2 | **['rwd']** | **['petrol']** | ['330'] |

→ A nessun livello drivetrains contiene {awd,rwd}, né fuel {petrol,diesel}. **Principio confermato da un secondo ingresso** (330i petrol rwd), non solo sul 320d diesel awd noto da S259.

### 1b — asserzione strutturale (prova durevole, cablata nel test suite)
Test: `tools/tests/test_no_fusion_ladder.py` (OFFLINE, no rete). 4/4 PASS:
- `test_ladder_pins_drivetrain_and_engine`: per OGNI livello (span 1 e 2) `cfg["drivetrain"] is True` e `cfg["engine"] is True`. Fallisce se reintrodotto un L4 che droppa drivetrain/engine.
- `test_matcher_never_fuses_drivetrain`: target rwd non matcha mai candidato awd a nessun livello.
- `test_matcher_never_fuses_fuel`: target petrol non matcha mai candidato diesel a nessun livello.
- `test_canary_would_fail_if_fusion_reintroduced`: un L4 malevolo (`drivetrain=False`) FONDE awd+rwd → prova che l'assertion strutturale è load-bearing (non vacua).

Snippet ladder cablato (it_market_price.py:121-128):
```
def _levels(year_span):
    yt = min(max(year_span,1),2)
    return [
        dict(engine=True, drivetrain=True, trim=True,  fuel=True, km=True,  year_tol=yt),
        dict(engine=True, drivetrain=True, trim=True,  fuel=True, km=False, year_tol=1),
        dict(engine=True, drivetrain=True, trim=True,  fuel=True, km=False, year_tol=2),
        dict(engine=True, drivetrain=True, trim=False, fuel=True, km=False, year_tol=2),
    ]
```
**DoD FASE 1 soddisfatto**: trace pulito + asserzione strutturale. Principio valido su tutta la matrice, cablato contro reintroduzioni future.

## FASE 2 — CHIUDERE L'ANELLO — BLOCKED-ON context budget (gate #7 a 60%)
Non eseguita: il context ha raggiunto il gate hard (60%) dopo FASE 1 + l'investigazione del runner. Avviare un harness live (scrape DE + CoVe + render PDF) a budget esaurito = anti-pattern `global_context_gate_lag` (saturazione a metà operazione). Parcheggiato onesto, NON spacciato per progresso.

### Terminal fact mancanti (invariati da S259)
- **T2** [BLOCKED-ON budget]: PDF X1 nel repo (cifre fisse 21795/22862) attraverso CoVe → Step 2c → pdf_generator, con CoVe alto + margine REJECT + decisione finale REJECT.
- **T3** [BLOCKED-ON budget]: PDF di 1 auto reale DE nel runner completo, con CoVe + margine + N + relaxation_level + verdetto ONESTO (NO-VERDICT atteso e accettato — NON forzare PASS).

### SCOPERTA che de-rischia S261 (gap di plumbing reale nel runner)
Investigando `tools/on_demand_runner.py` Step 2c (righe 466-510) ho trovato DUE gap che bloccano T3 come specificato — vanno chiusi PRIMA che T3 sia significativo:

1. **Step 2c NON è spec-aware** (riga 482): `get_it_distribution(v_make, v_model, v_year, v_km)` è chiamato SENZA `target_variant/target_transmission/target_power_hp/fuel` → cade nel path **legacy trim-blind** (relaxation_level=None, niente no_verdict). È esattamente il path che S259 ha sostituito. Fix richiesto: passare variant/fuel/transmission/power del listing DE per attivare il filtro spec-aware (come fa già `tools/margin_e2e.py:38-49`).
2. **Veto = `return None` su zero PASS** (on_demand_runner.py:507-509): su pool thin tutto è NO-VERDICT/REJECT → `margin_passed` vuoto → `return None` → **nessun PDF**. T3 richiede invece un PDF che RENDERIZZI lo stato NO-VERDICT onesto. Serve un path che generi il dossier onesto (NO-VERDICT/REJECT) per ≥1 veicolo, senza disattivare il veto di produzione (che correttamente protegge il dealer da affari sotto pavimento). Approccio pulito: harness T3 dedicato che invoca le STESSE funzioni (`scrape_portal` → `score_vehicles` CoVe → spec-aware `get_it_distribution`+`evaluate_margin` → `generate_dossier_from_data`) su 1 veicolo e renderizza il verdetto onesto.

Nota rendering: `_create_margin_verdict_section` (pdf_generator_enterprise.py:881-936) oggi distingue solo PASS vs "REJECT — sotto pavimento dealer". NON ha un ramo NO-VERDICT esplicito → per T3 va aggiunto un label NO-VERDICT (con N e relaxation_level) altrimenti un no_verdict verrebbe reso come REJECT generico. Verifica al render-time.

## min_n — NESSUNA RATIFICA (come da brief)
Default resta 8. Ratifica rinviata a dopo B3 (pool profondo). 3 resta solo pavimento di test.

## DoD#1 storico ("due mediane certificabili diverse")
NON in scope S260. Resta BLOCKED-ON pool depth → S261. NB: la mediana 320d=29990 di S259 era prodotta VIA L4 (la fusione poi rimossa) → con L4 rimosso e min_n=8 su pool 19 quasi tutto è NO-VERDICT, quindi DoD#1 non è dimostrabile finché il pool non cresce.

## ARTEFATTI NUOVI (additivi, committati)
- `tools/trace_330i_s260.py` (trace 1a) + `.claude/trace_330i_s260.out`
- `tools/tests/test_no_fusion_ladder.py` (test strutturale 1b) + `.claude/test_no_fusion_s260.out`

## DIFF SoT mostrati (GATE E mitigation)
- STATE.md: aggiornato blocco header S259→S260 (diff mostrato a Luke prima della scrittura).
- PLAN.md: NON toccato.

## DEBITO RESIDUO (BLOCKED-ON)
- **B1** T2: PDF X1 nel repo (CoVe alto + margine REJECT + decisione finale REJECT).
- **B2** T3: PDF 1 auto reale DE, runner completo spec-aware, verdetto onesto NO-VERDICT renderizzato.
- **B2a** [pre-req T3] Step 2c spec-aware (on_demand_runner.py:482) + path dossier-onesto su zero-PASS + label NO-VERDICT nel render (pdf_generator:881-936).
- **B3** Pool IT thin (≈19, cap curl_cffi SSR): critical path S261. DoD-shape = famiglie-con-N-sufficiente, NON listing totali.
- **FASE 3** Gate E refinement: non toccato, mitigazione diff-first resta la copertura.
