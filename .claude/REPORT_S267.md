# REPORT S267 — ARGOS · item (b) gate keystone PROVATO + brief S268
> Branch `s210/audit-master-plan` · 2026-06-11 · Autorità: Luke · Fonte verità: codice + git.
> Commit di lavoro: **`5645db6`** (pushato). Chiusura VERDE su **item (b)** del brief S266/S267.

---

# PARTE 1 — REPORT S267 (cosa è stato fatto)

## Esito: VERDE su item (b) — il gate non è più "affermato-non-provato"
S266 aveva lasciato il gate **AFFERMATO-NON-PROVATO**: i 2 veicoli reali della fixture
(320d N=13, 330i N=5) NON discriminano il gate composto da un `min_n` nudo (320d passa con
min_n 8 e 5; 330i cade su N e width insieme). I rami che PROVANO la composizione non erano toccati.
S267 li chiude con test sintetici in-memoria sulla decisione gate estratta in funzione PURA.

## Modifiche
1. **`tools/it_market_price.py`** — decisione gate estratta in funzione PURA:
   `_decide(n, min_n, relaxation_level, spread_pool, spread_infra_trim, median, *, spec_aware=True)`
   → ritorna `(no_verdict, width_nature, confidence)`.
   La PRODUZIONE ci passa attraverso (rami `n==0` e `n>=1`): **nessun calcolo gate inline residuo**.
   Questo è il punto: il test ora guarda la PRODUZIONE, non una copia parallela della logica.
2. **`tools/tests/test_gate_decide.py`** (NUOVO, no rete) — 3 falsificatori della tavola di verità.
3. **`.claude/NEXT_SESSION_PROMPT.manual.md`** — brief S268 (PARTE 3 sotto).

## Perché ci si è fermati a item (b)
Context al 60% (vincolo #7 CLAUDE.md → chiusura ordinata). Item (b) è il pezzo che il brief
sottolineava di più ("Gate (b) chiuso PRIMA di DoD#4"), è autocontenuto e verde. I PDF (DoD #2/#3)
sono un blocco a sé → in sessione fresca, non a budget saturo (vincolo #6: no stati PARTIAL).

---

# PARTE 2 — EVIDENZE E2E REALI DELLA SESSIONE (output catturato, non narrato)

### EVIDENZA E2E-1 — `python3 -m tools.tests.test_gate_decide` (item b, no rete)
```
=== S267 (b) — tavola di verita' gate _decide (no rete) ===
  OK: T-A: N=10 L3 indeterminato -> NO_VERDICT (nv=True width=indeterminato conf=NO_VERDICT)
  OK: T-B: N=7 incertezza_campione @min_n=8 -> NO_VERDICT (nv=True width=incertezza_campione)
  OK: T-B/ctrl: stesso caso @min_n=5 NON e' NO_VERDICT (nv=False) -> soglia=8 attiva
  OK: T-C: N=8 incertezza_campione -> verdetto conf=media (nv=False width=incertezza_campione conf=media)

TUTTI I CONTROLLI OK
RC=0
```
- **T-A** falsificatore del braccio width: N≥min_n MA L3-indeterminato → DEVE NO_VERDICT.
  Togliendo il braccio width da `no_verdict`, T-A fallisce → il braccio è provato attivo.
- **T-B** soglia: N=7 incertezza_campione → NO_VERDICT @min_n=8; lo stesso caso @min_n=5 NON è
  NO_VERDICT → prova che la soglia ratificata è 8, non 5.
- **T-C** ramo MAI esercitato dai 2 veicoli: N=8 incertezza_campione → verdetto, confidence=media.

### EVIDENZA E2E-2 — `python3 -m tools.tests.test_it_distribution_fixture` (regression S266, no rete)
```
=== fixture it_dist_bmw_serie3_2021.json (scrape_date=2026-06-11, n_raw=325) ===
  [320d xDrive] n=13 level=L3 no_verdict=False band=33200.0..39950.0 conf=bassa width=fusione_trim
  [330i] n=5 level=L3 no_verdict=True band=25299.0..30900.0 conf=NO_VERDICT width=indeterminato

=== invarianti (no rete) ===
  OK: scrape_date dalla fixture (2026-06-11), non da date.today()
  OK: due chiamate identiche -> stesso N e stessa banda (deterministico)
  OK: [320d] no_verdict=False coerente col gate composto
  OK: [330i] no_verdict=True coerente col gate composto
  OK: [320d] L3 non e' mai 'alta' (anti falso-PASS)
  OK: [330i] L3 non e' mai 'alta' (anti falso-PASS)
  OK: [320d] band_low <= median <= band_high

TUTTI I CONTROLLI OK
RC=0
```
Il refactor `_decide` NON ha cambiato il comportamento reale: 320d banda €33.200–39.950 invariata,
330i NO_VERDICT invariato.

### EVIDENZA E2E-3 — commit S267
```
$ git log --oneline (commit di lavoro)
5645db6 S267 item(b): gate keystone provato — _decide pura + 3 test sintetici (no rete)
 3 files changed, 186 insertions(+), 69 deletions(-)
 create mode 100644 tools/tests/test_gate_decide.py
Pushato: 5bd549a..5645db6  s210/audit-master-plan -> s210/audit-master-plan
```
NB: HEAD ora è `d6058cf` (breadcrumb auto-close hook), il lavoro è in `5645db6`.

### CAVEAT ONESTO (non regressione)
`python3 -m tools.it_market_price` (selftest `__main__`) resta **rc=1** ma SOLO per la parte
**live-scrape** (rete assente in-sessione: "una mediana è None — scraper IT down"). Il blocco
no-rete `_test_confidence_honesty` passa. In S268 conviene verificarlo con rete per chiudere il cerchio.

---

# PARTE 3 — BRIEF S268 (prossima sessione)

## DA FARE
### DoD #2/#3 — PDF reali nel repo (dalla fixture, NO rete) — PRIORITÀ
Sezioni già esistenti in `tools/scripts/pdf_generator_enterprise.py`:
`_create_margin_verdict_section` (~riga 883) + `_create_it_distribution_section` (~riga 950).
Oggi mostrano mediana PUNTUALE + p25/p75, NON banda-come-prodotto né intervallo-margine.
Wiring `best['_it_distribution']`→`VehicleData` ~riga 1946-1986.
1. Aggiungi a `VehicleData` (~riga 118-135): `it_band_low`, `it_band_high`, `it_confidence`(str),
   `it_width_nature`, `it_n_by_level`(dict), `it_scrape_date`, `margine_netto_low`, `margine_netto_high`.
2. Wiring ~1980-1986: leggi banda/confidence/width_nature/n_by_level/scrape_date da `it_dist`;
   INTERVALLO margine con `evaluate_margin(prezzo_de, band_low)`..`(prezzo_de, band_high)`
   (`tools/margin_gate.py:54`, pura) → `margine_netto_low/high`.
3. Rilavora le 2 sezioni: BANDA come PRODOTTO in cima (headline "rifai-il-conto", banda+N+livello),
   NON mediana-puntuale-con-asterisco. Margine = INTERVALLO. Mostra data-scrape (GAP-2).
   Riga d'onestà se L3 (n_by_level, width_nature). NO_VERDICT → label N+livello, NESSUNA banda fittizia.
4. Build script `tools/scripts/build_s268_dossier.py` (NUOVO): `get_it_distribution(...fixture_path=...)`
   per 320d xDrive e 330i → 2 PDF reali NEL REPO. Pre-flight reportlab.
   Fixture: `tests/fixtures/it_dist_bmw_serie3_2021.json`.

### Item (c) — PAVIMENTI (esaurito-o-cap)
325 = CAP `max_pages=20`, NON esaurimento → 320d=13/330i=5 sono PAVIMENTI. Decidere:
(i) scrape più profonda fino a pagina corta → ri-committa fixture esaurita, OPPURE
(ii) etichetta gli N come PAVIMENTI in PDF + REPORT. **Raccomandato (ii)** (zero-cost, no rete).

### Item 3 — STATE.md header (GATED — NON forzare)
Header fermo a S245/S246, non allineato a S264-S267. È SoT → l'edit innesca Gate E `overwrite_sot`
(BLOCCA + `pending_review/<slug>.md` + serve `! python3 .harness/gate_e.py approve <slug>` da Luke).

### DoD #4 (primo dossier davanti a dealer reale) = decisione Luke, NON tecnica. Gate (b) chiuso → sbloccabile.

## REGOLE
- NON delegare a subagent (S258). Main context, output E2E > /tmp/s268.txt.
- Rule 1d: backup verificato prima di overwrite SoT. NON reintrodurre precisione finta. NON allargare scope.
- Report precedente: `.claude/REPORT_S266.md` (banda+N+livello+riconciliazione pool).
