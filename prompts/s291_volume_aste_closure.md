# S291 — CHIUSURA VOLUME ASTE (la sola metrica che decide il canale)

MANDATO: READ-ONLY (chiusura probe-volume aste, nessuna scrittura oltre il report).
RIGA-1 SESSION-KILLER: apri da ROOT (~/Documents/combaretrovamiauto-enterprise), NON da .claude/.
PRIMA AZIONE: `pwd`; se non root → FERMATI.

Branch s210/audit-master-plan, no push. CC-MAIN, no sub-agent. NON costruire collector: questa
sessione chiude SOLO il VOLUME rimasto BLOCKED-ON in S290 — l'unica metrica che decide se il canale
aste è reale o un rivolo. Infra: curl_cffi chrome120 (resilient_fetcher.py). Nessun proxy.

CONTESTO (da S290, ri-validare in FASE 0): fonte scelta = astegiudiziarie.it (PVP scartato:
token-gated + WAF). Endpoint volume identificato = POST https://webapi.astegiudiziarie.it/api/search/Data
(JSON, filtri searchParameters: idGenere=2=Mobili, prezzoDa, idTribunale...). In S290 tornava HTTP 500:
manca un dettaglio (probabile header Authorization Bearer anonimo, o casing search/data, o un campo
obbligatorio del body). NEXT-STEP già diagnosticato: replicare la XHR reale.
NB stealth (S290): il browser headless reale viene BLOCCATO dal WAF di PVP; per astegiudiziarie va
usato curl_cffi. Per CATTURARE la XHR su astegiudiziarie usa Playwright SOLO per leggere gli header/body
della chiamata (network capture), poi REPLICA con curl_cffi — non lasciare il collector su browser.

FASE 0 (riporta, NON agire): pwd root + git HEAD + git status (working-tree solo rumore-hook;
se codice non committato → FERMATI).

PARTE A — CHIUSURA VOLUME (1 obiettivo):
1. Cattura la XHR REALE di search/Data: esegui sul sito una ricerca "Mobili" (idGenere=2) con
   prezzo ≥ 25.000 e ispeziona la chiamata reale (header completi + body JSON esatto che il sito invia
   e che ottiene 200). Replica ESATTAMENTE quegli header+body con curl_cffi finché ottieni 200.
   Riporta: cosa mancava al 500 (header/casing/campo), così è documentato.
2. Leggi il campo `total` (o equivalente conteggio) nella risposta JSON 200 → VOLUME auto totali
   categoria Mobili. Poi restringi il filtro al premium europeo (prezzoDa=25000 e/o brand
   BMW/Mercedes/Audi/Porsche/Volvo/Land Rover/Jaguar nel campo descrizione) → stima VOLUME PREMIUM.
   Riporta i due numeri grezzi. Se anche dopo la cattura resta non ottenibile → BLOCKED-ON onesto,
   NON un numero inventato (vincolo #10).
3. CAMPIONE: estrai 2-3 lotti-auto reali dalla risposta 200 coi campi: marca/modello, prezzo-base,
   tribunale, data scadenza, link pagina-lotto. → conferma cosa un futuro collector estrarrebbe.

NIENTE collector, NIENTE persistenza DB, NIENTE roadmap (resta "PROBE IN CORSO" finché il numero c'è).

DONE-CONDITION (evidenza incollata):
1. La chiamata search/Data restituisce 200 → incolla cosa mancava al 500 + lo status 200.
2. VOLUME: `total` Mobili + stima premium, numeri grezzi (oppure BLOCKED-ON motivato, no invenzioni).
3. CAMPIONE 2-3 lotti-auto coi campi reali.
4. commit del solo HANDOFF_CURRENT.md; no push; nessun proxy.

OUTPUT: report in HANDOFF_CURRENT.md (nuovo formato), aprilo in TextEdit. In testa, 1 riga netta:
VOLUME PREMIUM ASTE = <numero> → canale CONFERMATO / SCARTATO / ANCORA-BLOCKED.
