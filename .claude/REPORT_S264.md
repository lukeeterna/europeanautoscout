═══════════════════════════════════════════════════════════════════════════════
  ARGOS · REPORT SESSIONE S264 — DE-GATE FETCH PROFONDO IT + RERUN PROBE
  2026-06-10 · branch s210/audit-master-plan
═══════════════════════════════════════════════════════════════════════════════

# ESITO: VERDE su misura — pool IT misurato in profondità (310 listing).
# Esito mercato = MISTO/FRAMMENTATO (confermato su dati veri, non più su rumore-19).

───────────────────────────────────────────────────────────────────────────────
## 1. RISULTATO — TABELLA (probe su 310 listing dedup, vs 19 in S263)
───────────────────────────────────────────────────────────────────────────────

| FAMIGLIA          | grezzi | dedup | L0 | L1 | L2 | L3 | N≥8 a |
|-------------------|:------:|:-----:|:--:|:--:|:--:|:--:|:-----:|
| 320d xDrive 2021  |  310   |  310  |  1 |  1 |  2 | 14 |  L3   |
| 318d 2021         |  310   |  310  |  2 |  2 |  4 | 13 |  L3   |
| 330i 2021         |  310   |  310  |  0 |  0 |  0 |  3 |  MAI  |
| M340 2021         |  310   |  310  |  5 |  6 |  7 |  8 |  L3   |

Livelli: L0=config esatta (trim+drivetrain+fuel+km-band), L3=trim droppato.
Pool dedup per listing_id (VIN assente nel SSR AS24.it: 0/310). km-band default.

───────────────────────────────────────────────────────────────────────────────
## 2. ESITO PER FAMIGLIA (conta, non interpreta)
───────────────────────────────────────────────────────────────────────────────
- 320d xDrive / 318d / M340 → N≥8 raggiunto SOLO a L3 (trim droppato). A config
  ESATTA (L0/L1) restano 1-6: il mercato NON pool-a le config esatte a N≥8.
- 330i → MAI, neanche a L3 (max 3). Thin reale anche su pool 310.
- FATTO TRASVERSALE: con 310 listing reali (16× S263), NESSUNA famiglia tocca N≥8
  a L0/L1. La frammentazione trim/drivetrain domina — confermata su dati veri,
  non più sospettata sul pool-19 troncato (debito S259/S263 sciolto: era reale,
  non artefatto dello scraper).

→ NON è Esito A (config esatte non reggono N≥8 da nessuna parte).
→ È MISTO: i comparabili esistono solo a livello rilassato (L3). Il verdetto prezzo
  (mediana dove regge a L3 / bande dove thin come 330i) è decisione di Luke, coi NUMERI.

───────────────────────────────────────────────────────────────────────────────
## 3. IL MURO REALE — la diagnosi S263 era SBAGLIATA (verificato sul codice)
───────────────────────────────────────────────────────────────────────────────
S263 imputava il tetto-19 a `get_total_pages` (base_scraper:335). FALSO:

EVIDENZA CODICE (FASE 0, sola lettura):
- `base_scraper.py:143` → `get_total_pages` ritorna `None` (nessun override in
  AutoScoutScraper) → la riga 335 `if total_pages is not None and...` NON scatta MAI.
- `build_search_url:459-460` → il param `?page=N` è aggiunto correttamente.
- IL MURO VERO = `base_scraper.py:374-375`:
    `if len(page_listings) < self.config.results_per_page: break`
  `results_per_page=20` (config.py:167). Quando pagina-1 torna 19 (`19<20`) → break
  dopo 1 pagina → "Completato in 1 pagine" (log S263 riga 5). Quando torna 20
  (`20<20` falso) → il curl pagina in profondità.
- Il gate Selenium (autoscout_scraper:1226-1230) NON era il muro: non viene mai
  raggiunto perché il curl si ferma prima.

───────────────────────────────────────────────────────────────────────────────
## 4. EVIDENZA E2E — 3 run live, stessa firma
───────────────────────────────────────────────────────────────────────────────
RUN A (S263, codice stock):           pagina-1=19 → short-page break → 19 listing.
RUN B (FASE 1, force_deep Selenium):   pagina-1=20 → curl pagina TUTTE le 20 pag
                                       → 305 listing; POI Selenium cappa a 5 pag e
                                       RIMPIAZZA → ritorna 90. ⇒ forzare Selenium è
                                       una REGRESSIONE (305→90). Edit REVERTITO.
RUN C (S264, results_per_page=1):      pagina-1=19 (avrebbe rotto nello stock!) ma
                                       lo short-page break NON scatta → curl pagina
                                       fino a 20 pag → 310 listing dedup. ✓

TERMINAL FACT FASE 1 (>19 listing reali): RAGGIUNTO — 310 listing, 20 pagine fetchate.
Log integrali: /tmp/s264.txt (probe), /tmp/s264_fase1.txt (run B 305 vs 90).

───────────────────────────────────────────────────────────────────────────────
## 5. min_n — ANCORA PARCHEGGIATO (onesto)
───────────────────────────────────────────────────────────────────────────────
Default 8 NON ratificato. A L0/L1 tutto near-zero (0-6) anche su 310 listing →
ratificare min_n sulla config esatta = ratificare il vuoto. A L3 è raggiunto, ma L3
fonde via il trim: ratificare lì = decidere che il comparable è "Serie 3 di pari
motore/drivetrain", non "stesso trim". È una scelta di PRODOTTO, di Luke, non di CC.

───────────────────────────────────────────────────────────────────────────────
## 6. BUG DI PRODUZIONE SCOPERTO (non risolto qui — scope)
───────────────────────────────────────────────────────────────────────────────
`base_scraper.py:374-375` short-page break sotto-raccoglie AS24.it ~metà delle volte:
sui 3 run, pagina-1 ha reso 19,20,19 → 2 volte su 3 lo scrape stock si ferma a 19.
Ogni scrape di produzione AS24.it (qualunque modello/paese) è esposto. Fix candidato
(decisione Luke): per AS24 rcompi la pagina solo su pagina VUOTA (break :352 esiste
già) e non su pagina-corta. NON applicato: tocca il base condiviso da 28 portali.
Il probe lo aggira probe-local (results_per_page=1, throwaway). Produzione INVARIATA.

───────────────────────────────────────────────────────────────────────────────
## 7. ARTEFATTI / MODIFICHE
───────────────────────────────────────────────────────────────────────────────
- `tools/_s263_probe.py` — override probe-local `results_per_page=1` + commento (TENUTO).
- `tools/scrapers/autoscout_scraper.py` — edit force_deep REVERTITO (prod invariata).
- Backup scraper: /tmp/autoscout_scraper.py.s264.bak (pre-edit, integro).
- Log E2E: /tmp/s264.txt, /tmp/s264_fase1.txt.
- STATE.md: NON toccato (Gate E + budget) → aggiornamento header rimandato a S265.

───────────────────────────────────────────────────────────────────────────────
## 8. LENTE STRATEGICA — il pool depth è il penultimo miglio
───────────────────────────────────────────────────────────────────────────────
Domanda S264 ("ARGOS vede abbastanza mercato"): RISPOSTA = sì, vede 310 listing; e
il mercato dice che le config ESATTE non pool-ano, i comparabili vivono a L3.
Il fatto terminale mai toccato resta: un dossier REALE, auto VERA, margine VERO, a un
dealer VERO che risponde. Prossimo bivio NON è un'altra sessione tecnica sul pool:
è decidere il design-verdetto a L3 (Luke) e poi puntare al PRIMO dossier reale.
═══════════════════════════════════════════════════════════════════════════════
