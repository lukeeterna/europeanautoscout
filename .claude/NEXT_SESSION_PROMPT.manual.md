# BRIEF CC — ARGOS · Sessione S265 (IDEMPOTENTE) — DESIGN VERDETTO L3 + DECISIONE PRIMO DOSSIER
# Progetto: /Users/macbook/Documents/combaretrovamiauto-enterprise (MacBook, macOS Big Sur)
# Branch: s210/audit-master-plan · Autorità: Luke · NESSUNA azione esterna.
# Fonte di verità: PLAN.md + STATE.md + .claude/REPORT_S264.md + git.

## EREDITATO DA S264 (verificato E2E, non assunto)
- DE-GATE RISOLTO: il muro "19 listing" NON era get_total_pages né il gate Selenium.
  Era lo short-page break `base_scraper.py:374-375` (`len(page)<results_per_page=20 → break`):
  quando pagina-1 AS24.it rende 19, lo scrape stock si ferma a 19. Aggirato probe-local
  (`tools/_s263_probe.py`, results_per_page=1) → 310 listing dedup, 20 pagine.
- PROBE 310 listing, esito MISTO/FRAMMENTATO (tabella in REPORT_S264.md §1):
  320d/318d/M340 → N≥8 SOLO a L3 (trim droppato); 330i → MAI; NESSUNA a L0/L1.
- BUG PRODUZIONE APERTO: `base_scraper:374-375` sotto-raccoglie AS24.it ~½ delle volte
  (3 run: pagina-1 = 19,20,19). Tocca il base condiviso da 28 portali → decisione Luke.
- Edit force_deep su autoscout_scraper.py REVERTITO (Selenium cappa 5 pag, regressione 305→90).
  Produzione INVARIATA. Backup /tmp/autoscout_scraper.py.s264.bak.
- STATE.md NON aggiornato in S264 (Gate E + budget). Header da allineare a S264.

## DECISIONI APERTE PER LUKE (portare numeri, NON eseguire design da solo)
1. VERDETTO PREZZO a L3: i comparabili reggono N≥8 solo a trim-droppato. Accettare L3
   come livello-comparable (mediana dove regge / bande dove thin tipo 330i)? Scelta di
   PRODOTTO. CC porta la distribuzione, Luke decide la regola.
2. min_n: parcheggiato. A L0/L1 near-zero su 310 → ratifica solo se Luke accetta L3.
3. FIX PRODUZIONE short-page break: applicarlo per AS24 (rompi solo su pagina VUOTA,
   non su pagina-corta)? Sblocca raccolta piena su TUTTI i modelli/paesi. Cambio in
   base_scraper condiviso → backup + verifica su ≥2 portali prima di chiudere.

## SCOPE S265 (proposto, Luke conferma)
A) Allineare STATE.md header a S264 (diff-first; Gate E token a Luke se blocca).
B) Se Luke accetta L3 → ratificare min_n e nominare la regola-verdetto.
C) Decidere se applicare il fix produzione short-page (scope tecnico isolato).
D) Se B chiude → puntare al PRIMO DOSSIER REALE su una famiglia che regge (320d/318d/M340
   a L3): generare dossier che passa il gate HITL e decidere se metterlo davanti a un dealer.

## ANTI-PATTERN (da REPORT_S264 §3-4)
- NON re-imputare il muro a get_total_pages/Selenium: smentito sul codice.
- NON forzare il path Selenium (regressione 305→90).
- NON abbassare min_n né allargare le chiavi per forzare un Esito A: il MISTO è il vero risultato.
- NON toccare cove_engine_v4.py. NESSUNA azione esterna.

## OUTPUT FINE S265
- STATE.md allineato. Se design-verdetto deciso → in PLAN.md + REPORT_S265.md.
- git add -A && commit + push.
