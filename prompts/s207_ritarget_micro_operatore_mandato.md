# S207 — Ri-mirare target prospect Marche (allineamento modello mandato)

## CONTESTO DI INGRESSO

Sessione precedente: **S206** ha lanciato Ondata 1 Marche (deep-research + scraping nativo). Findings preliminary OK ma scoring prospect basato su modello broker supply-side **da abbandonare**.

Stato fine S206:
- Branch git attivo: `s206/marche-register` (NON committato master)
- Deliverable presenti (untracked):
  - `research/s206_marche_register/preliminary_findings.md` (deep-research output — utile per portali/keyword/blacklist, NON per scoring)
  - `research/s206_marche_register/HANDOFF_FROM_DEEP_RESEARCH.md` (mio handoff a lead-researcher)
  - `tools/s206_marche_scraper.py` (1645 righe — scraper multi-portale, da ri-targare)
  - `tools/scrapers/detail_enricher.py` (esteso: campo `description` verbatim — OK, riusabile)
- Agent background lanciato S206: `lead-researcher` (agentId `aad663e74bf19a031`) — output finali (corpus_register.md, prospect_list.csv, ecc.) NON ricevuti a chiusura S206. Verificare se esistono in branch alla ripresa, altrimenti rilanciare con scope S207.

## DIRETTIVA LUKE (testo integrale)

> Il modello ARGOS è cambiato e lo scraper S206 sta selezionando il target SBAGLIATO.
> Lo scraper attuale premia "stock visibile 5-30 veicoli" e cerca auto sottoprezzo da
> rivendere (filtro F5 margine EU→IT). Questo è il vecchio modello broker supply-side,
> ABBANDONATO. Non ricostruirlo.
>
> MODELLO CORRETTO: il nostro cliente è un MICRO-OPERATORE che vende auto premium SU
> MANDATO. Non tiene stock (0-2 auto). Compra solo DOPO che un cliente altospendente
> ha già chiesto un modello specifico. Il valore che cerchiamo in lui NON è "quanto
> stock premium ha" — è "ha accesso a clienti altospendenti che gli chiedono auto".
>
> PROBLEMA STRUTTURALE DA ACCETTARE (non aggirare):
> L'accesso ai compratori NON è visibile in un annuncio. Quindi `flag_target_alto`
> basato sui dati di annuncio è intrinsecamente debole. Non inventare un proxy che
> finga di misurarlo. La verità su quel segnale si ottiene solo dalle chiamate di Luke.

## 5 DIRETTIVE OPERATIVE

### D1 — RIDEFINISCI flag_target_alto (inverti logica stock)
- Target plausibile = micro-operatore con P.IVA ma stock **PICCOLO (1-8 auto)**, possibilmente **multi-brand**, NON specializzato in un solo premium.
- Stock grande (>15-20) = rivenditore-con-magazzino = MENO interessante (vecchio target). NON escludere del tutto, solo deprioritizzare.
- Mantieni blacklist concessionari ufficiali (Carpoint, Cascioli, Delta Motors, Domina, Luxcar, Fratelli Giacomel) — corretta.

### D2 — DISATTIVA filtro F5 (anomalia prezzo / margine EU→IT)
Appartiene al modello broker. NON deve influenzare scoring prospect. Rimuovi codice o gating boolean disattivato. AutoUncle cross-check resta utile per CoVe veicoli ma NON per scoring prospect.

### D3 — RINOMINA flag per non illudere
- Da `flag_target_alto` → **`flag_micro_operatore_plausibile`**.
- Aggiungi colonna esplicita `accesso_clienti = "DA_VERIFICARE_AL_TELEFONO"` su ogni riga.
- Documenta nell'EXECUTION_REPORT che la lista è **grezza, NON qualificata**.

### D4 — PRIORITÀ DATO: TELEFONO
- `telefono` = colonna più importante (chiave dedup + canale chiamata Luke).
- Subito nasconde telefono in lista → recupera da pagina detail.
- Se non recuperabile: segnala esplicitamente % righe senza numero nell'EXECUTION_REPORT.
- **Prospect senza telefono = riga inutile**.

### D5 — GATE ONESTO
Gate "VERDE" NON deve scattare su zero o dati fantasma. EXECUTION_REPORT deve dichiarare a chiare lettere:
- Listing fetched per portale (vs atteso)
- % righe con telefono presente
- % righe con description verbatim presente
- Eventuali 403/captcha/schema __NEXT_DATA__ cambiato → flag esplicito
- Meglio GIALLO onesto che VERDE su pipeline rotta.

## VINCOLI
- Idempotente: re-run non duplica (dedup su telefono normalizzato +39 — verifica regga con nuovo schema flag).
- Branch dedicato `s206/marche-register` (continua, NON nuovo). NO push master.
- Nessun contatto operatori. Luke chiama a mano.
- NO Ondata 2 (Puglia/Basilicata) finché Luke non conferma target ri-mirato Marche.

## OUTPUT ATTESO
1. `tools/s206_marche_scraper.py` patched (D1+D2+D3+D4 applicate)
2. `research/s206_marche_register/prospect_list.csv` ri-targato (colonne nuove: `flag_micro_operatore_plausibile`, `accesso_clienti`, `stock_visibile`, `telefono`)
3. `research/s206_marche_register/EXECUTION_REPORT.md` con sezione "Cambio modello S206→S207" + tabella onestà (D5)
4. Commit branch `s206/marche-register` con messaggio `feat(S207): ri-target prospect modello mandato — invert stock + drop F5 + rename flag`

## GATE CHIUSURA S207
- Codice D1+D2+D3 applicato e verificabile via `grep`
- prospect_list.csv contiene colonna `flag_micro_operatore_plausibile` + colonna `accesso_clienti`
- EXECUTION_REPORT contiene tabella onestà 4 metriche (listing/portale, %telefono, %description, status flag)
- Se gate non raggiungibile → handoff S208 strutturato, NO stato PARTIAL/ARANCIONE (vincolo #6)

## VERIFICHE PRELIMINARI S207 STEP 0 (max 10 min)
1. `git log --oneline -5` + `git status` su branch `s206/marche-register`
2. Verifica se lead-researcher background ha lasciato output in branch o solo i 4 file noti
3. Lettura `tools/s206_marche_scraper.py` sezioni `flag_target_alto` + `F5` + `stock` (grep mirato, NO read intero file 1645 righe)
4. Decidi: patch surgical su scraper esistente VS rewrite parziale

## RIFERIMENTI
- Modello mandato confermato: `~/.claude/rules/identity.md` (success-fee B2B €800-1200)
- Persona Luca Ferretti: `~/.claude/rules/communication.md`
- DECISIONS founder S206→S207: pivot da broker supply-side → mandato demand-side (NUOVA D-XX da registrare)
- Memory entry chiusura S206: `memory/s206_marche_register_pivot_demand_side.md`
