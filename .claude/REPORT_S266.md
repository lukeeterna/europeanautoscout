# REPORT S266 — ARGOS · FASE 2 parziale: FIXTURE REALE COMMITTATA (debito S264 chiuso)

> Branch `s210/audit-master-plan` · 2026-06-11 · Autorità: Luke · Fonte di verità: codice + git.
> Chiusura VERDE su **DoD #1** (keystone). DoD #2/#3 (PDF) = **BLOCKED-ON** fase PDF, handoff sotto.

## DoD #1 — FIXTURE REALE COMMITTATA ✅ (chiude il debito riproducibilità S264)
- **Fixture**: `tests/fixtures/it_dist_bmw_serie3_2021.json` — **325 listing reali** AutoScout24.it
  (BMW Serie 3 2019-2023), scrape_date 2026-06-11, 759KB. Pool unico CONDIVISO: i due veicoli del
  DoD si filtrano entrambi da questo snapshot → più onesto di due scrape separate (stesso giorno,
  stesso mercato). Deviazione motivata dai nomi-file-esempio del brief (raw non è trim-specifico).
- **Tecnica S264 riprodotta + PERSISTITA**: override RUNTIME `results_per_page=1` (bypass break
  short-page `base_scraper.py:374`) via `object.__setattr__` su config frozen — **nessun file editato,
  nessun git restore** (Rule 1d: zero mutazione source-of-truth). Muro S263 (pagina-1 ~19 listing)
  SUPERATO: 20 pagine, 325 listing. Builder committato e ri-eseguibile: `tools/scripts/build_it_fixture.py`.
- **Meccanismo fixture in `get_it_distribution`**: nuovo param `fixture_path`; se presente carica raw da
  disco (round-trip `Listing.to_dict()`/`from_row()`) e usa `scrape_date` della fixture (GAP-2: la banda
  è la fotografia di QUEL giorno, non di `date.today()`). Path live invariato.
- **Test NO-RETE riproducibile**: `tools/tests/test_it_distribution_fixture.py` → `rc=0`. Invarianti
  STRUTTURALI (non N hardcoded): scrape_date=fixture, determinismo, gate composto coerente, mai "alta"
  a L3, banda contiene mediana. Da qui DoD/test girano sul dato vero committato, NON ri-scrapando.

### Numeri reali (dalla fixture, non presunti)
| Veicolo | N | Livello | Verdetto | Banda IT (p25–p75) | Confidence | width_nature |
|---|---|---|---|---|---|---|
| 320d xDrive 2021 | 13 | L3 | verdetto | €33.200–39.950 | bassa | fusione_trim |
| 330i 2021 | 5 | L3 | **NO_VERDICT** | — | NO_VERDICT | indeterminato |

Comportamento = gate composto Luke S265: 330i N=5 ma sub-pool trim-esatto (L2) <2 punti →
`indeterminato` → NO_VERDICT (mai "media"). 320d L3 con dispersione da fusione allestimenti → bassa.

### CORREZIONE ONESTÀ (ratifica Luke S266) — il gate è AFFERMATO-NON-PROVATO
"Gate composto confermato sul vero" era OVERCLAIM. I due punti reali NON discriminano il gate composto
da un `min_n` nudo: 320d (N=13) passa con min_n=8 **e** 5, composto e nudo; 330i (N=5) cade su N **e** su
width insieme — non si vede quale braccio lavora né se sono in AND. I rami che PROVANO la composizione non
sono toccati dalla fixture e restano da chiudere in S267 (test sintetici in-memoria, no rete):
- **N≥8 AND width=indeterminato → NO_VERDICT** (il braccio width che vince su un N che passerebbe). Falsificatore.
- **confine min_n=8**: N=7 AND incertezza_campione → NO_VERDICT (con min_n=5 passerebbe).
- **N=8 AND incertezza_campione → verdetto, confidence=media** (ramo mai esercitato dai due veicoli).

### FATTO LETTERALE (non l'etichetta)
- `MIN_N_DEFAULT = 8` (`tools/it_market_price.py:38`).
- Gate (`it_market_price.py:291-292`):
  `l3_unverifiable = (relaxation_level == 3 and spread_infra_trim is None)`
  `no_verdict = spec_aware and (n < min_n or l3_unverifiable)`

### RICONCILIAZIONE SCRAPE (Luke S266) — 325 è un CAP, gli N sono PAVIMENTI
- `results_per_page` qui NON è la dimensione-pagina: è la **soglia del break short-page** (`base_scraper.py:374`).
  Le pagine rendono ~19-20 listing (SSR AS24); l'override a 1 disabilita solo lo stop prematuro. Quindi
  20 pagine × ~20 = 325 è coerente (NON 20 listing).
- La scrape si è fermata su `max_pages=20` (cap), **NON per esaurimento**: `grep "Pagine totali rilevate"`=0
  e pagina 20/20 piena. **Conseguenza: 320d=13 e 330i=5 sono PAVIMENTI**, non conteggi completi. La tesi
  "config esatta mai N≥8" è un pavimento, non un fatto. Una scrape più profonda (max_pages↑ fino a pagina
  corta) potrebbe alzarli. Da chiudere prima di DoD#4 (verdetto a dealer reale).

## DoD #2 — PDF 320d xDrive (banda+N+livello+margine-intervallo) — BLOCKED-ON fase PDF
## DoD #3 — PDF 330i NO_VERDICT — BLOCKED-ON fase PDF
Wiring `pdf_generator_enterprise.py` (`_create_margin_verdict_section` + `_create_it_distribution_section`):
aggiungere campi a `VehicleData`, leggerli da `best['_it_distribution']` (righe ~1980-1986). Margine come
INTERVALLO: `evaluate_margin(prezzo_de, band_low)`..`evaluate_margin(prezzo_de, band_high)`.
I 2 PDF reali NEL REPO si generano dalla fixture (no rete). DoD #4 (primo dossier davanti a dealer) = decisione Luke, NON sessione tecnica.

## DEBITO RESIDUO
- STATE.md header fermo a S246/S248, non allineato a S264/S265/S266 → aggiornare diff-first (Gate E `overwrite_sot`).
- Fase PDF: prossima sessione, vedi `.claude/NEXT_SESSION_PROMPT.manual.md` (brief S266) FASE 2.
