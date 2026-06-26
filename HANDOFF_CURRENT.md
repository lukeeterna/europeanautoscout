# HANDOFF_CURRENT — S290 · PROBE PVP/aste giudiziarie + roadmap supply

Branch: s210/audit-master-plan · no push · CC-MAIN (no sub-agent) · READ-ONLY probe + docs roadmap.
Data: 2026-06-26. Infra fetch: curl_cffi chrome120 (tools/scrapers/resilient_fetcher.py). Nessun proxy installato.

═══════════════════════════════════════════════════════
PARTE A — PROBE (5 esiti)
═══════════════════════════════════════════════════════

## 1. VERDETTO STEALTH — "stealth pesante NON serve; anzi controproducente"
Evidenza diretta, stesso IP casa (151.26.11.207):
- **curl_cffi chrome120 → HTTP 200 PULITO** su `https://pvp.giustizia.it/pvp/` (7.596 byte) e su
  `https://www.astegiudiziarie.it/` (224.574 byte). Nessun captcha / challenge / 403.
- **Browser headless reale (Playwright/Chrome) → BLOCCATO** su PVP: pagina WAF di rete
  "Web Page Blocked! ... Attack ID: 20000051 ... Client IP: 151.26.11.207" (Palo Alto-style).
- CONCLUSIONE: la singola richiesta HTTP impersonata passa; è il **browser pesante** (raffica di
  risorse: maps API, fonts, bundle JS) che fa scattare il WAF. Per un collector futuro → curl_cffi
  leggero, NON undetected-chromedriver/selenium. Fallback noto se mai servisse (NON ora): Scrapfly
  asp=true free-tier, valutazione in sessione separata.

## 2. DATA-PATH
**PVP (pvp.giustizia.it)** — OSTILE:
- SPA Entando. I dati arrivano dal microservizio backend `/bo-5897bc47-986a1b71/bo-ms`.
- Tutti gli endpoint bo-ms testati → **HTTP 401** (Bearer token richiesto). Front-end SPA serve JS,
  ma il browser che lo eseguirebbe è bloccato dal WAF. Doppia barriera (token + WAF-su-browser).

**astegiudiziarie.it (portale ministeriale autorizzato n.1)** — PULITO e PARSABILE:
- Form server-side `POST /results` (CSRF `__RequestVerificationToken` estratto dall'home) → shell HTML
  + app Vue `/assets/scripts/vuejs/ricerca.js`.
- L'app Vue chiama la **Web API JSON**: base `https://webapi.astegiudiziarie.it/api/` (definita in
  `/JSVariable`), endpoint risultati = **`search/Data`** (POST JSON), mappa = `search/map`.
- Campi filtro ricchi nell'oggetto `searchParameters` (60+ campi): `idGenere` (**2 = beni Mobili**),
  `idTipologie`/`idTipologiaBene`, `idCategorie`, **`prezzoDa`/`prezzoA`**, `idTribunale`, `descrizione`,
  `regione`/`provincia`/`comune`, `hasFoto`, `inScadenza`, `dataVenditaDa/A`, `orderBy`. → filtro per
  categoria-veicolo e per prezzo ESISTE nativamente.

## 3. VOLUME — ⚠️ NON CONFERMATO (BLOCKED-ON: chiamata webapi search/Data)
- Endpoint esatto identificato (`POST https://webapi.astegiudiziarie.it/api/search/Data`) ma le chiamate
  fatte in sessione → **HTTP 500 `<Error>`** anche inviando l'oggetto `searchParameters` completo con
  `idGenere=2`. Manca un dettaglio (probabile header `Authorization: Bearer` anonimo, o casing
  `search/data`, o campo richiesto specifico) che non ho chiuso entro il budget context.
- **Per vincolo #10 NON invento un numero.** Volume auto totali + stima premium (>€25k o brand premium
  europei) = DA CONFERMARE. Questa è la metrica che decide il canale: finché il numero non c'è, il
  canale aste resta marcato "PROBE IN CORSO" in roadmap (coerente col mandato).
- NEXT STEP secco (1 chiamata): replicare in DevTools la XHR reale di una ricerca "Mobili + prezzo≥25.000"
  su astegiudiziarie.it/results, copiare header+body esatti di `search/Data`, e rieseguirli con curl_cffi.
  Il `total` nella risposta JSON È il volume.

## 4. CAMPIONE LOTTI-AUTO — non estratto (dipende da #3, stessa chiamata bloccata)
Campi estraibili previsti dallo schema `search/Data` + pagine lotto (`/vendita-asta-...-lNNN-pNNN`):
marca/modello (in `descrizione`/titolo), prezzo-base d'asta, tribunale (`idTribunale`),
data scadenza offerte (`dataVendita`), link perizia/allegati nella pagina-lotto. Estrazione reale =
appena sbloccata la #3.

## 5. PVP vs astegiudiziarie.it — quale fonte per il collector
**astegiudiziarie.it VINCE nettamente.**
- PVP: SPA + API token-gated (401) + WAF che blocca il browser → richiederebbe reverse del token Entando
  o esecuzione browser (proprio ciò che il WAF blocca). Costo alto, fragile.
- astegiudiziarie: HTTP 200 con curl_cffi, API JSON pubblica `search/Data` con filtri nativi
  (genere/tipologia/prezzo/tribunale) + URL-lotto SEO server-side. Stesso bacino aste, struttura
  pulita. → **collector futuro su astegiudiziarie.it/webapi, NON su PVP.**

═══════════════════════════════════════════════════════
PARTE B — ROADMAP (diff)
═══════════════════════════════════════════════════════
docs/ROADMAP.md — aggiunto blocco "DECISIONI FOUNDER S290" dopo la riga BACKLOG aste:
+ SEGMENTO premium ALLARGATO → "premium europeo" (tedesco + Porsche/Volvo/Land Rover/Jaguar), coerente gap S289b.
+ SUPPLY PRIVATI → annunci privati sotto-mercato, canale supply S1.
+ SUPPLY ASTE GIUDIZIARIE (PVP/astegiudiziarie.it) → canale supply S1, STATO "PROBE IN CORSO — volume da
  confermare" (NON confermato finché #3 non dà il numero).

═══════════════════════════════════════════════════════
DONE-CONDITION
═══════════════════════════════════════════════════════
1. STEALTH ............... OK  curl_cffi 200 pulito (PVP+astegiudiziarie); browser headless = WAF block PVP.
2. DATA-PATH ............. OK  PVP=bo-ms 401 token-gated; astegiudiziarie=POST webapi/api/search/Data (JSON, filtri).
3. VOLUME ................ BLOCKED-ON: search/Data → 500; endpoint noto, numero NON inventato (vincolo #10).
4. CAMPIONE 2-3 lotti .... dipende da #3 (stessa chiamata); schema campi documentato.
5. PVP vs astegiudiziarie  OK  astegiudiziarie.it = fonte scelta per il collector.
6. ROADMAP 3 righe ....... OK  blocco DECISIONI FOUNDER S290 aggiunto.
7. commit file nominati ... docs/ROADMAP.md + HANDOFF_CURRENT.md, no push, nessun proxy installato.

NEXT SESSION (1 mossa): catturare la XHR reale `search/Data` (header+body da DevTools su ricerca
Mobili+prezzo≥25k) → rieseguire con curl_cffi → leggere `total` = VOLUME, poi 2-3 lotti campione.
Solo allora il canale aste può passare da "PROBE IN CORSO" a confermato/scartato.
