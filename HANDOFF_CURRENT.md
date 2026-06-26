# HANDOFF_CURRENT — S291 CHIUSURA VOLUME ASTE

**VOLUME PREMIUM ASTE = ~12 lotti ≥€25k in tutta Italia (di cui ~1 sola auto passeggeri premium europea) → canale SCARTATO**

Fonte: astegiudiziarie.it · Metodo: cattura XHR reale (Playwright) + replica curl_cffi chrome120 · No proxy · 2026-06-26

---

## 1. La chiamata 200 + cosa mancava al 500 (S290)

L'ipotesi S290 era SBAGLIATA sull'endpoint. Il flusso reale è a 2 fasi:

- **`POST https://webapi.astegiudiziarie.it/api/search/map`** → endpoint-VOLUME. Body = `searchParameters`
  completi (JSON). Ritorna **l'INTERA lista** dei lotti che matchano (ogni elemento: `idLotto`,
  `prezzoBase`, lat/long, date). **Il totale = lunghezza dell'array.** HTTP **200** con curl_cffi.
- **`POST .../api/search/Data`** → NON è l'endpoint-volume. Body = **array di ~20 `idLotto`**
  (es. `[2327566,2327529,...]`). Hydrata solo i dettagli di UNA pagina. HTTP **200**.

**Cosa mancava al 500 in S290**: a `search/Data` venivano passati i `searchParameters` invece di un
array di ID → 500 (body type sbagliato). Il volume non era MAI ottenibile da `search/Data`: va preso
da `search/map`. Header minimi che bastano per il 200 (curl_cffi `impersonate=chrome120`):
`content-type: application/json`, `accept: application/json, text/plain, */*`,
`referer: https://www.astegiudiziarie.it/`, `x-referer: https://www.astegiudiziarie.it/mobili`.
Nessun Authorization/Bearer, nessun token, nessun cookie richiesto. Endpoint pubblico.

Body chiave (mobili): `tipoRicerca:2` (=Mobili), `idTipologie:[6]` (=Autoveicoli e cicli),
`prezzoDa:<n>`, `orderBy:6`. Tutti gli altri campi `null`/`false`.

## 2. VOLUMI grezzi (stock attivo, 2026-06-26)

| Filtro (search/map) | Totale lotti |
|---|---|
| Mobili — tutte le categorie (`idTipologie:[]`) | **914** |
| Autoveicoli e cicli (`idTipologie:[6]`) | **174** |
| Autoveicoli `prezzoDa:25000` (server-side) | **12** |
| Autoveicoli `prezzoBase>=25000` (filtro client, conferma) | **12 / 174** |

## 3. CAMPIONE — cosa sono davvero i 12 "premium" (hydrate search/Data, campi reali)

| idLotto | prezzoBase | Cosa è (descrizione reale) | Tribunale/Comune |
|---|---|---|---|
| 2314075 | €642.625 | **20 veicoli INDUSTRIALI** (autocarri, piattaforme, gru) — lotto cumulativo | Grosseto |
| 2319870 | €267.750 | **Porsche 911 Carrera RS 3.6 (964) 1992, 18.937 km** — unica vera auto premium | Catania |
| 2319145 | €105.500 | **9 trattori stradali + motrice + furgone + rimorchi** — industriale | Cuneo / Andezeno (TO) |
| 2324263 | €86.400 | Lotto **misto** (mobili + miniescavatore + automezzi) | Nocera Inferiore (SA) |
| 2326394 | €66.000 | **Autocarro MAN** (targa EK733HA) | Nuoro |

Link pagina-lotto ricostruibile dallo slug `urlSchedaDettagliata` presente nel record search/Data.

## VERDETTO

Canale **SCARTATO**. Il bucket ≥€25k (12 lotti su tutta Italia) è dominato da **veicoli
industriali / lotti cumulativi**, non da auto passeggeri premium europee target ARGOS
(BMW/Mercedes/Audi/Porsche di gamma). Nello stock attivo c'è **~1 sola** auto premium reale
(Porsche 911 classica da collezione, fuori dal profilo scout EU→IT). Non giustifica un collector.

## Cosa estrarrebbe un futuro collector (NON costruito, per memoria)
Endpoint `search/map` (volume+prezzi+geo, 1 chiamata) → poi `search/Data` a batch di ID per
descrizione/tribunale/date/foto. Zero token, zero proxy, curl_cffi chrome120. Parametri:
`tipoRicerca:2, idTipologie:[6], prezzoDa, orderBy`.

## Stato
PROBE CHIUSA. Numero ottenuto, non inventato. Nessun collector, nessuna persistenza DB. No push.
