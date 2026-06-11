# REPORT SESSIONE S265 — VERDETTO A BANDA (FASE 1 chiusa) + handoff FASE 2

2026-06-11 · branch s210/audit-master-plan
Stato: **FASE 1 VERDE (DoD #1 raggiunto). FASE 2 + DoD #2/#3 in HANDOFF** (richiedono ratifica Luke + dati reali). Chiusura per context budget (vincolo #7, 59%).

---

## FASE 0 — GROUND TRUTH (verde, sola lettura)
- repo + branch `s210/audit-master-plan` corretti.
- `get_it_distribution` esiste, livelli L0→L3 (L4 RIMOSSO nel codice: `_levels` ritorna 4 livelli, indici 0-3).
- Ramo `NO_VERDICT` del PDF presente (pdf_generator_enterprise.py:897-903, 1988-1991).
- Falsificazione X1 live: `python3 -m tools.margin_gate` → **REJECT, EXIT 0**. ✓
- Debito doc minore (non in scope): docstring `get_it_distribution` righe ~170-172 cita ancora "L4" (stale, il codice è L3).

## FASE 1 — VERDETTO A BANDA (FATTO, file `tools/it_market_price.py`)
`get_it_distribution` ora restituisce, oltre a quanto già produceva:
- `band_low`, `band_high` = p25-p75 del pool al livello usato.
- `band_width_pct` = (band_high-band_low)/median ·100.
- `spread_pool` = spread IQR del pool selezionato.
- **[GAP-1]** `spread_infra_trim` = spread IQR a trim ESATTO (livello L2) + `width_nature`:
  a L3 confronta spread pool vs spread trim-esatto → `fusione_trim` (mescolamento allestimenti = precisione finta) | `incertezza_campione` | `indeterminato`. Fuori L3 → `config_esatta`.
- `confidence` ONESTA e monotona (`_confidence_label`):
  - `no_verdict` → `"NO_VERDICT"`
  - L3 (trim fuso) → MAI `"alta"`; `fusione_trim` → `"bassa"`, altrimenti `"media"`.
  - altrimenti → `"alta"` solo se N≥20, `"media"` se N≥10, `"bassa"` sotto.
- **[GAP-2]** `scrape_date` = data della scrape (la banda è una FOTOGRAFIA).
- `n_by_level` = {0:N_L0, 1:N_L1, 2:N_L2, 3:N_L3} (per la riga d'onestà del report).
- NESSUN allargamento via drivetrain/motore (L4 resta vietato).

### DoD #1 — RAGGIUNTO (test che VIETA il falso-PASS)
Test `_test_confidence_honesty()` in `it_market_price.py`. Invariante protetta:
`confidence=="alta" ⇒ level∈{0,1,2} AND n≥20 AND not no_verdict`.
**FALLISCE (rc>0) se** "confidence alta" coesiste con banda stretta / N piccolo / L3 (il bug ucciso S256-S262).
Verificato OFFLINE (no rete): `python3 -c "import tools.it_market_price as m; m._test_confidence_honesty()"` → `OK: invariante confidence onesta rispettata`, rc=0.
Agganciato anche a `_selftest()` (return non-zero se l'invariante si rompe).

---

## DUE RATIFICHE CHE ASPETTANO TE (brief: "NON ratificare di nascosto")
1. **min_n** — proposta CC dai numeri S264: a L0/L1 tutto <8 anche su 310 listing → i comparabili vivono solo a L3.
   Raccomandazione: **min_n = 5 applicato di fatto a L3** (con `confidence` che dichiara la fusione trim), invece di 8.
   Con i dati S264: 320d xDrive L3 N=14 → verdetto a banda (confidence ≤ media); 330i N≤3 → NO_VERDICT.
   NON ho cambiato il default `MIN_N_DEFAULT=8` nel codice: lo cambio solo dopo tuo OK.
2. **Percentili banda** — proposta p25-p75 (implementata). Se vuoi p10-p90 (banda più larga/onesta su pool sottili) lo cambio: 1 riga.

---

## HANDOFF FASE 2 (PDF) + DoD #2/#3 — prossima sessione
Restano da fare (codice + dati):
- **FASE 2**: in `pdf_generator_enterprise.py` mostrare la BANDA (band_low-band_high) invece/oltre la mediana puntuale; il margine come INTERVALLO (`evaluate_margin` valutato a band_low e band_high → margine_min..margine_max); **[GAP-2]** stampare `scrape_date` + "fascia calcolata il <data> su <N> annunci AutoScout24.it"; riga d'onestà sul campione con N_L0/N_L1 (da `n_by_level`) + **[GAP-1]** quale dispersione domina (`width_nature`). Wiring: aggiungere campi a `VehicleData` e leggerli da `best['_it_distribution']` (già passato, righe 1980-1986).
- **DoD #2/#3 (2 PDF reali nel repo)**: richiedono dati di distribuzione REALI. **I dati S264 (310 listing) NON sono persistiti** (probe con override `results_per_page=1` poi revertito; log /tmp cancellati). Per riprodurre 320d xDrive L3 N=14 e 330i N≤3 serve **una scrape profonda** → decisione tua: il bug short-page (`base_scraper:374`) sotto-raccoglie ~1/2, quindi serve ri-applicare la tecnica S264 (override `results_per_page=1`, locale, poi `git restore`). È lettura di dato pubblico, non azione esterna verso dealer — ma te lo segnalo perché tocca un file base condiviso e il brief diceva "nessuno scraping nuovo".
- **[GAP-3]** DoD #4: il passo DOPO S265 NON è un'altra sessione tecnica → è il **PRIMO dossier reale davanti a un dealer vero** (decisione Luke). Confermato nel handoff.

## DEBITO RESIDUO
- STATE.md header non allineato a S264 (ereditato): lasciato al Gate E diff-first, fuori da questa chiusura.
- STATE.md/rings.json: solo rigenerazione timestamp da refresh.sh di SessionStart (churn harness, non lavoro).
