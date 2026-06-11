# BRIEF CC — ARGOS · Sessione S266 (IDEMPOTENTE) — FASE 2: REPORT VERIFICABILE DAL DEALER
# FASE 1 (verdetto a banda) E' CHIUSA E RATIFICATA in S265. Qui si chiude il report + i 2 PDF reali su FIXTURE COMMITTATA.
# Progetto: /Users/macbook/Documents/combaretrovamiauto-enterprise (MacBook, macOS Big Sur)
# Branch: s210/audit-master-plan · Autorita': Luke · Fonte di verita': PLAN.md + STATE.md + git. Chat/"OK" NON sono fonte.

## EREDITATO DA S265 — FASE 1 FATTA E RATIFICATA (verificato offline, commit f7efad8 + fix ratifica)
`tools/it_market_price.py` · `get_it_distribution` restituisce ora:
band_low/band_high (p25-p75), band_width_pct, spread_pool, spread_infra_trim (L2),
width_nature {config_esatta|fusione_trim|incertezza_campione|indeterminato},
confidence onesta, scrape_date, n_by_level {0..3}.
TEST DoD#1 `_test_confidence_honesty()` (no rete) rc=0: vieta "alta" su N<20 / L3,
e (Luke S265) vieta "media" su L3 `indeterminato` -> NO_VERDICT.

## DECISIONI LUKE RATIFICATE S265 (LOCKED — non riaprire, sono founder-DECIDED)
- **min_n = 8** (non 5). Gate COMPOSTO: NO_VERDICT salvo (N>=min_n AND width_nature != indeterminato).
  Motivo: a N=5 il sub-pool trim-esatto (L2) e' 0-2 punti -> width_nature non distingue fusione da incertezza
  = narrativa al posto del fatto. 8 = cuscinetto contro la sotto-raccolta short-page (probe vede > campo reale).
- **a L3 `indeterminato` -> NO_VERDICT (mai media)**. GIA' IMPLEMENTATO S265 (gate composto + _confidence_label).
  Protegge il caso vetrina: 320d xDrive ha L2=2 -> la natura della banda si decide su 2 punti; se 0-1 -> NO_VERDICT.
- **Percentili p25-p75 confermati** (non p10-p90: su N=8-14 p10/p90 = singoli annunci di coda mossi da 2 outlier).
- **Conseguenza ACCETTATA per design**: con "alta solo se N>=20" e il mercato che a L3 non passa 14, il ramo "alta"
  e' codice morto sui pool veri -> ARGOS gira sempre a media/sotto. E' la FIRMA ONESTA del dominio (usato a config
  esatta = mai molto sicuri), scelta non incidente. NON "aggiustare" per far comparire "alta".

## SCRAPE AUTORIZZATA + PERSISTENZA FIXTURE (il fix vero al debito S264)
S264 ha prodotto il fatto fondante (310 listing) e poi ha BUTTATO la prova (override revertito, /tmp pulito):
il DoD non era riproducibile. Stavolta:
- Scrape profonda AUTORIZZATA (lettura dato pubblico, banda tecnica — NON azione esterna verso dealer).
- Tecnica S264: override `results_per_page=1` (bypassa short-page break `base_scraper:374`), LOCALE, poi `git restore`.
- **COMMITTA L'OUTPUT come fixture reale** (es. `tests/fixtures/it_dist_320d_xdrive_2021.json` + `..._330i_2021.json`):
  i listing/distribuzione reali su disco, una volta sola. DoD #2/#3 e i test girano su quel dato committato,
  NON ri-scrapando ogni sessione.

## FASE 2 — REPORT VERIFICABILE (pdf_generator_enterprise.py · _create_margin_verdict_section + _create_it_distribution_section)
Mostrare in chiaro (wiring: aggiungere campi a VehicleData, leggerli da best['_it_distribution'], righe ~1980-1986):
- **BANDA prezzo IT** (band_low-band_high) invece/oltre la mediana puntuale.
- **N + livello** (es. "14 comparabili, stesso motore e trazione; allestimento non vincolato — livello L3").
- **MARGINE come INTERVALLO**: `evaluate_margin(prezzo_de, band_low)` ... `evaluate_margin(prezzo_de, band_high)`
  -> margine_min..margine_max. NON un punto. (margin_gate.evaluate_margin e' puro e riusabile.)
- **[GAP-2] data-scrape**: "fascia calcolata il <scrape_date> su <N> annunci AutoScout24.it".
- **Riga d'onesta'**: se L3 -> "configurazione esatta sotto-rappresentata (N_L0=.., N_L1=.. da n_by_level):
  stima su famiglia allargata" + [GAP-1] quale dispersione domina (width_nature). Se NO_VERDICT -> label N+livello.

## DoD (terminal fact reali)
1. Fixture reale COMMITTATA nel repo (320d xDrive 2021 + 330i 2021), path incollato. [chiude il debito riproducibilita' S264]
2. 1 PDF reale NEL REPO (non /tmp) — 320d xDrive L3 N=14: banda + N + livello + margine-INTERVALLO + data-scrape + riga onesta'. Path incollato.
3. 1 PDF reale NEL REPO — 330i N<=3: NO_VERDICT con N+livello reali. Path incollato.
4. [GAP-3] Il passo DOPO S266 NON e' un'altra sessione tecnica: e' il PRIMO dossier reale davanti a un dealer vero (decisione Luke).
Se uno manca -> BLOCKED-ON in STATE.md (diff-first), NON "completato".

## REGOLE / ANTI-PATTERN
- NON delegare a subagent (lezione S258). Main context, output E2E rediretto su file (> /tmp/s266.txt 2>&1).
- Source-of-truth (STATE.md/PLAN.md): diff-first, mostra il diff a Luke; edit SoT = ULTIMO passo (Gate E falsi positivi su backup).
- Reversibilita' (Rule 1d): backup verificato prima di ogni overwrite; override scraper -> `git restore` subito dopo.
- NON reintrodurre precisione finta (banda stretta non supportata da N). NON allargare scope (no fix short-page, no mobile.de).
- Debito ereditato: header STATE.md non allineato a S264/S265 -> Gate E diff-first.

## OUTPUT FINE SESSIONE
- <repo>/.claude/REPORT_S266.md (4 DoD con path/numeri reali, fixture, ogni diff SoT mostrato, debito residuo).
- open -a TextEdit "<repo>/.claude/REPORT_S266.md" · STATE.md diff-first.
