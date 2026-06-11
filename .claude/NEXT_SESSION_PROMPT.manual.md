# BRIEF CC — ARGOS · S268 — FASE 2 PDF (DoD #2/#3) + item (c) PAVIMENTI + STATE.md
# Branch s210/audit-master-plan · Fonte verità: codice + git + STATE.md. Chat NON è fonte.

## CHIUSO IN S267 (VERDE — non riaprire)
**Item (b) gate keystone — il gate non è più "affermato-non-provato".**
- `tools/it_market_price.py`: decisione gate estratta in funzione PURA
  `_decide(n, min_n, relaxation_level, spread_pool, spread_infra_trim, median, *, spec_aware=True)`
  → ritorna `(no_verdict, width_nature, confidence)`. La PRODUZIONE ci passa attraverso
  (rami n==0 e n>=1): nessun calcolo gate inline residuo, quindi il test guarda davvero la produzione.
- `tools/tests/test_gate_decide.py` (NUOVO, no rete) **rc=0**:
  - T-A falsificatore: N=10 L3 indeterminato → NO_VERDICT (togliendo il braccio width, T-A rompe).
  - T-B: N=7 incertezza_campione @min_n=8 → NO_VERDICT; @min_n=5 NON lo è (prova soglia=8).
  - T-C: N=8 incertezza_campione → verdetto, confidence=media (ramo mai esercitato dai 2 veicoli reali).
- Regression `tools/tests/test_it_distribution_fixture.py` **rc=0** (320d N=13 banda invariata, 330i NO_VERDICT invariato).
- VERIFICA: `python3 -m tools.tests.test_gate_decide && python3 -m tools.tests.test_it_distribution_fixture` → rc=0.
- NB: `python3 -m tools.it_market_price` (selftest __main__) resta rc=1 SOLO per la parte live-scrape
  (rete assente in-sessione); `_test_confidence_honesty` no-rete passa. NON è regressione.

**Item (a) — già fatto:** FATTO LETTERALE (`MIN_N_DEFAULT=8` + gate) già in `.claude/REPORT_S266.md`
sez. "FATTO LETTERALE". NB righe gate ora ~289-291 dopo il refactor (verificare, non fidarsi del numero).

## DA FARE S268
### DoD #2/#3 — PDF reali nel repo (dalla fixture, NO rete) — PRIORITÀ
Le 2 sezioni ESISTONO: `tools/scripts/pdf_generator_enterprise.py`
`_create_margin_verdict_section` (~riga 883) + `_create_it_distribution_section` (~riga 950).
Oggi mostrano mediana PUNTUALE + p25/p75, NON banda-come-prodotto né intervallo-margine.
Wiring `best['_it_distribution']`→`VehicleData` ~riga 1946-1986 (`it_median/p25/p75/n/relaxation_level/no_verdict` già letti).
1. Aggiungi a `VehicleData` (~riga 118-135): `it_band_low`, `it_band_high`, `it_confidence`(str),
   `it_width_nature`, `it_n_by_level`(dict), `it_scrape_date`, `margine_netto_low`, `margine_netto_high`.
2. Wiring ~1980-1986: leggi `band_low/band_high/confidence/width_nature/n_by_level/scrape_date` da `it_dist`;
   INTERVALLO margine con `evaluate_margin(prezzo_de, band_low)`..`(prezzo_de, band_high)`
   (`tools/margin_gate.py:54`, pura) → popola `margine_netto_low/high`.
3. Rilavora le 2 sezioni: BANDA (band_low–band_high) come PRODOTTO in cima (headline "rifai-il-conto",
   banda+N+livello), NON mediana-puntuale-con-asterisco. Margine = INTERVALLO. Mostra data-scrape (GAP-2).
   Riga d'onestà se L3 (n_by_level, width_nature). NO_VERDICT → label N+livello, NESSUNA banda fittizia.
   Caso vetrina (320d) gira a `bassa`, spread €6.75k su ~36k: è il dominio onesto, non un difetto da nascondere.
4. Build script `tools/scripts/build_s268_dossier.py` (NUOVO): chiama `get_it_distribution(...fixture_path=...)`
   per 320d xDrive e 330i, assembla dict veicolo con `_it_distribution`+`_margin_*`, genera 2 PDF NEL REPO.
   Pre-flight reportlab. DoD = 2 path PDF reali committati. Fixture: `tests/fixtures/it_dist_bmw_serie3_2021.json`.

### Item (c) — PAVIMENTI (esaurito-o-cap)
325 = CAP `max_pages=20`, NON esaurimento → 320d=13/330i=5 sono PAVIMENTI (REPORT_S266 sez. RICONCILIAZIONE).
Decidere: (i) scrape più profonda fino a pagina corta → ri-committa fixture esaurita, OPPURE
(ii) etichetta gli N come PAVIMENTI in PDF + REPORT. Raccomandato (ii) (zero-cost, no rete, no scope creep).

### Item 3 — STATE.md header (GATED — NON forzare)
Header fermo a S245/S246, non allineato a S264-S267. È SoT → l'edit innesca Gate E `overwrite_sot`
(BLOCCA + `pending_review/<slug>.md` + serve `! python3 .harness/gate_e.py approve <slug>` da Luke).
Diff-first, backup Rule 1d, edit = ULTIMO passo.

### DoD #4 (primo dossier davanti a dealer reale) = decisione Luke, NON sessione tecnica.
NB (DELTA-3): Gate (b) chiuso = LOGICA sana, NON dato sano. DoD#4 NON sbloccabile finché scrape esaustiva non fatta.

## REGOLE
- NON delegare a subagent (S258). Main context, output E2E > /tmp/s268.txt 2>&1.
- Rule 1d: backup verificato prima di overwrite SoT. NON reintrodurre precisione finta. NON allargare scope (no fix short-page, no mobile.de).
- Report S266 (banda+N+livello+riconciliazione): `.claude/REPORT_S266.md`. Report S267: `.claude/REPORT_S267.md`.

---

# CORREZIONE BRIEF S268 (validazione Luke S267 — ADDITIVA, il brief sopra resta valido)
Sintesi: item (b) sostanzialmente vinto; l'arco S264→S267 poggia su campione che SAPPIAMO tagliato
(cap 20 pagine). I PDF possono nascere sopra; il PRIMO dossier a un dealer NO, finché non sappiamo
se la sottigliezza (330i NO_VERDICT) è del mercato o dello scraper.

## DELTA-1 — prova STRUTTURALE che la produzione usa _decide (GIÀ ESEGUITO E VERDE in S267)
Incollare in REPORT_S268 a conferma:
  grep -nE "no_verdict\s*=|width_nature\s*=|confidence\s*=" tools/it_market_price.py
Esito S267: CALCOLO solo dentro _decide (righe 216-226); due soli unpack al call-site (riga 386 ramo
n==0, riga 419 ramo n>=1); il resto sono kwargs di out.update e confronti in _confidence_label.
Nessun terzo sito che calcola il gate fuori da _decide → item (b) CHIUSO col fatto, non con la frase.
Regola permanente: se ricompare un sito di CALCOLO fuori da _decide = gate residuo da instradare.

## DELTA-2 — item (c): PAVIMENTI resi onesti NEL PDF (non solo nel REPORT)
325 = CAP max_pages=20, non esaurimento → 320d=13 / 330i=5 sono PAVIMENTI (>=), non conteggi.
Nei 2 PDF DoD #2/#3 il numero NON va nudo:
- Verdetto:   ">=13 comparabili (campione cap 20 pagine / 325 annunci AS24.it, non esaustivo)".
- NO_VERDICT: ">=5 comparabili a config esatta sotto-rappresentata (campione non esaustivo)".
- La riga d'onestà deve dire che N è un PAVIMENTO, non un totale di mercato.
Motivo: il dealer "rifà il conto"; se trova più auto di quante ne dichiari, salta la credibilità del
perito, che È il prodotto. La precisione DICHIARATA include la dichiarazione del cap.

## DELTA-3 — nuovo BLOCKED-ON esplicito PRIMA di DoD#4 (in STATE.md, diff-first / Gate E)
Gate (min_n=8, percentili, soglie width_nature) e 330i→NO_VERDICT calibrati su campione CAP.
Registra in STATE.md come prerequisito di DoD#4:
  "BLOCKED-ON DoD#4: scrape ESAUSTIVA (override results_per_page=1 fino a pagina corta, NESSUN cap
   max_pages) sulla famiglia vetrina, per falsificare che NO_VERDICT 330i e min_n=8 NON siano
   artefatti del cap. Finché non fatto: NO_VERDICT può essere falso-NO_VERDICT (rifiuto di affare
   reale). Fatto terminale = pagina corta raggiunta."
NON è lavoro di S268 (FASE 2 PDF resta priorità): è la nomina del gate empirico che separa
"logica onesta" da "verdetto onesto sul mercato vero".

## INVARIATO
- FASE 2 PDF (DoD #2/#3 dalla fixture, no rete) procede come da brief S268.
- Item 3 STATE.md header resta gated Gate E overwrite_sot. DELTA-3 = stessa scrittura SoT, stesso gate.
- DoD#4 NON sbloccabile finché DELTA-3 non soddisfatto (logica sana ≠ dato sano).
