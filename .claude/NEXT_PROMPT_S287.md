MANDATO: BUILD
RIGA-1 SESSION-KILLER: apri Claude Code DALLA ROOT del repo
(~/Documents/combaretrovamiauto-enterprise), NON da .claude/. Se parti da .claude/, gli hook
(gate_e.py / state_guard.py, path relativi .harness/…) non risolvono → ogni Bash/Write
bloccato → il build muore. PRIMA AZIONE: verifica `pwd` = root del repo; se no, FERMATI.

IDEMPOTENTE: CREATE TABLE IF NOT EXISTS + upsert per dealer_id (re-run = stesso stato).
MOTORE DB = SQLite (deciso): data/dealers.db è separato dal CRM per scopo, niente analitica
colonnare qui → upsert via INSERT ... ON CONFLICT(dealer_id) DO UPDATE. NON DuckDB.
FIX SCHEMA (load-bearing per l'idempotenza): dealer_id deve essere PRIMARY KEY (o UNIQUE) —
ON CONFLICT(dealer_id) esige un indice PK/UNIQUE che combaci, altrimenti SQLite alza
"ON CONFLICT clause does not match any PRIMARY KEY or UNIQUE constraint" e la re-run NON è idempotente.
NB onesto: l'UPSERT ON CONFLICT è standard SQLite dalla 3.24 (2018), Python 3.13 imbarca SQLite
molto più recente → sicuro per-standard, NON verificato sulla macchina; la FASE 0 lo intercetta al primo run.
Codice ADDITIVO: NON toccare il path ricerca (build_search_url / parse_listings ramo
item.price restano intatti). Branch single-writer s210/audit-master-plan, no push.
ESECUZIONE: CC-MAIN. NIENTE delega a sub-agent per scrittura file (storico "FILE SCRITTO"
fabbricati). Ogni done-condition verificata RILEGGENDO l'artefatto reale.

CONTESTO (sessione nuova, autoconsistente — verificato da 2 fetch reali in S286:
REPORT_S286 dealer ariel-car-bologna n=50 + PROBE_S286_RUN2 dealer Ceccato n=627):
Fase 1 [S4]. SCOPE TAGLIATO A 1 SESSIONE: si costruisce il collector pagina-dealer
ICP-AGNOSTICO + il DB + UNA query verde. Day-1 e gap-analysis = S288, FUORI da questa sessione.
FATTI VERIFICATI (= IPOTESI da ri-validare in FASE 0 contro il disco, NON a scatola chiusa):
- parsing-path pagina-dealer = SÌ: inventario nello stesso __NEXT_DATA__ → props.pageProps.listings[]
  + numberOfResults. Riusa _parse_next_data + get_total_pages AS-IS.
- URL dealer derivabile dai dati di ricerca: seller.links.infoPage → /concessionari/{slug}.
- ADATTATORE chiavi (mapping, NON rewrite) — su pagina-dealer le chiavi differiscono:
  · prezzo:  listing.prices.public.priceRaw  (+ prices.dealer.priceRaw)  — NON item.price (null → estrae 0)
  · anno:    vehicle.firstRegistrationDate.{raw,formatted}
  · km:      vehicle.mileageInKm.formatted
  · nome dealer: pageProps.dealerInfoPage  (NON nel listing-item)
- MINA: AutoScoutScraper.fetch (~riga 486) è CODICE MORTO/ROTTO (super().fetch non esiste in
  BaseScraper). Il collector DEVE usare _fetch(dealer_url) diretto + _parse_next_data/get_total_pages.
  NON costruire su fetch().
FUORI SCOPE (ICP deciso = piccolo dealer che ARGOS gradua da forfettario a ordinario; collector
ICP-agnostico): NON assemblare liste target, NON automatizzare discovery, NON inviare. E in
QUESTA sessione: NON costruire Day-1 né gap-analysis (rimandati a S288).
Rif su disco: docs/ARCHITETTURA_E2E.md sez.4/6, report sessione S286.

═══════════════════════════════════
FASE 0 — HEAD VERO + RE-GROUNDING + PARERE TECNICO (riporta, NON costruire)
═══════════════════════════════════
1. HEAD VERO: riporta il commit HEAD reale. S286 ha lasciato hash divergenti da hook auto-close
   (1b6ffdb mio commit, poi 28d771b auto-close = rumore). Working-tree pulito a parte
   .claude/NEXT_SESSION_PROMPT.md (rumore-hook)? Se esiste QUALSIASI codice non committato
   oltre al rumore-hook → FERMATI e riporta (sessione precedente ha lasciato lavoro aperto).
2. RE-GROUND i fatti sopra contro il codice reale (cita riga):
   - _fetch (curl_cffi chrome120, ~147/172), _parse_next_data (~742), get_total_pages (~503)
     esistono? firme?
   - AutoScoutScraper.fetch ~486 davvero morto/rotto (super().fetch assente)? conferma o correggi.
   - chiavi pagina-dealer (prices.public.priceRaw, firstRegistrationDate, mileageInKm,
     dealerInfoPage) esistono come dichiarato? conferma o correggi.
3. PARERE TECNICO: l'adattatore-chiavi + paginazione è il punto d'integrazione giusto, o c'è
   una giuntura migliore? Conferma data/dealers.db (SQLite) separato da
   data/db/dealer_network.duckdb. Segnala file morti / blueprint superati / conflitti.
   Se la procedura è sbagliata → proponi correzione e FERMATI.

═══════════════════════════════════
FASE 1 — BUILD (perno + DB + 1 query verde, CC-MAIN)
═══════════════════════════════════
Anchor ristretto: collector funzionante → 1 dealer reale persistito → 1 query che lo rilegge.
NIENTE Day-1, NIENTE gap, NIENTE breadth.
Scegli un dealer con 20–60 annunci (così la PAGINAZIONE è esercitata ma il fetch resta leggero;
NON Ceccato 627 = ~32 pagine). Il dealer-prova è SOLO fonte-dati pubblica.

1. [perno] Collector dealer_url → inventario: _fetch(dealer_url) diretto + _parse_next_data +
   get_total_pages (NON fetch() morto). Adattatore chiavi pagina-dealer (prezzo/anno/km) +
   nome da dealerInfoPage + paginazione (numberOfResults → pagine). NON toccare il ramo ricerca.
2. data/dealers.db (SQLite, CREATE TABLE IF NOT EXISTS) schema Dealer + DealerProfile (sez.4),
   dealer_id PRIMARY KEY (requisito dell'upsert ON CONFLICT).
   GDPR HARD: SOLO campi commerciali (business_name, brands, inventario, prezzi, anzianità).
   dealerInfoPage contiene contact_person/phone/email → NON persisterli. Verificabile: schema
   DB con ZERO colonne personali.
3. Persisti il dealer-prova + esegui 1 query di rilettura che restituisce
   business_name + brand_focus + active_listings + avg_listing_age.

SPEC PER S288 (NON costruire ora, solo annotare nel report come prossimo passo):
- Gap-Analysis: gap = segmento premium-tedesco (BMW/Merc/Audi) che il dealer SOTTO-PESA
  rispetto al proprio brand-mix o alla supply ARGOS — dato RELATIVO, non assoluto ("non ha
  Ferrari" = gap-spazzatura, vietato).
- Estensione generate_cold_day1 (templates.py:273) con payload-profilo + Day-1 personalizzato.

NESSUN INVIO. Gate-E intatto. Se il context si esaurisce: FERMATI, committa solo il verificato,
riporta lo stato reale — NON chiudere a metà spacciando verde.

═══════════════════════════════════
DONE-CONDITION (esterna, falsificabile — verifica RILEGGENDO l'artefatto, riporta punto per punto):
- data/dealers.db esiste (SQLite); la query di rilettura restituisce 1 dealer con business_name
  + brand_focus + active_listings + avg_listing_age → INCOLLA l'output della query.
- la paginazione è stata esercitata (dealer >20 annunci): active_listings persistito == numberOfResults
  della pagina-dealer → riporta i due numeri.
- schema DB: 0 colonne di dati personali → MOSTRA lo schema (output di .schema o equivalente).
- re-run del collector sullo stesso dealer = stesso stato DB (idempotenza upsert) → riporta che
  la seconda esecuzione non duplica la riga.
- commit dei soli file nominati; no push.
═══════════════════════════════════
OUTPUT: scrivi il REPORT in un file e APRILO in TextEdit (open -a TextEdit <path>).
Includi FASE 0 (HEAD vero, re-grounding, parere tecnico) + done-condition verificata punto
per punto CON evidenza incollata + la spec-S288 annotata come prossimo passo.
═══════════════════════════════════
