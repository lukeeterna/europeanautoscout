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

## DoD #2 — PDF 320d xDrive (banda+N+livello+margine-intervallo) — BLOCKED-ON fase PDF
## DoD #3 — PDF 330i NO_VERDICT — BLOCKED-ON fase PDF
Wiring `pdf_generator_enterprise.py` (`_create_margin_verdict_section` + `_create_it_distribution_section`):
aggiungere campi a `VehicleData`, leggerli da `best['_it_distribution']` (righe ~1980-1986). Margine come
INTERVALLO: `evaluate_margin(prezzo_de, band_low)`..`evaluate_margin(prezzo_de, band_high)`.
I 2 PDF reali NEL REPO si generano dalla fixture (no rete). DoD #4 (primo dossier davanti a dealer) = decisione Luke, NON sessione tecnica.

## DEBITO RESIDUO
- STATE.md header fermo a S246/S248, non allineato a S264/S265/S266 → aggiornare diff-first (Gate E `overwrite_sot`).
- Fase PDF: prossima sessione, vedi `.claude/NEXT_SESSION_PROMPT.manual.md` (brief S266) FASE 2.
