# S209 — Fix estrazione telefono da description AS24 + no-SPOF hard-skip

## STATO IN INGRESSO (da S208)

S208 ha eseguito il run dello scraper S207 ri-targato. Esito **GIALLO onesto**:
- AS24: **184 listing** OK (enrich detail 13%)
- Subito.it: 0 listing (403/captcha)
- automobile.it: 0 listing (HTTP 404 su URL pattern)
- **0 prospect**: AS24 non espone `seller.phone` (dietro reveal-click) → D4 hard-skip
  (`if not phone: continue`, riga 1166) scarta tutti i 184
- corpus_register.md: 171 frasi reali committate (utili a prescindere)

Commit S208: `5ac1214` su branch `s206/marche-register`.

---

## ADDENDUM S209 — note di allineamento (leggere PRIMA del fix)

Contesto: S208 ha dato GIALLO onesto (184 listing AS24, 0 prospect). Bene non aver
falsificato. Prima di correre al fix, tre dritte.

1. **FIX PRIMARIO (vai)**: estrai telefono dalla description AS24 PRIMA dell'hard-skip D4.
   - Gestisci cifre spaziate/offuscate: "3 8 8 4 0 3 6 2 2 7", "388.403.6227",
     "388-403-6227", "tre88..." improbabile ma normalizza spazi/punti/trattini.
   - Fallback ordine: campo seller.phone → regex su description → se entrambi vuoti,
     NON scartare la riga: marcala telefono="" + nota "tel_da_recuperare_manuale" e
     tieni l'url_profilo_venditore. Un prospect con profilo ma senza telefono è
     recuperabile a mano da Luke; scartarlo a priori è il SPOF di S207. Hard-skip
     totale solo se manca SIA telefono SIA url profilo.

2. **LEZIONE DI METODO (applicala sempre)**: rendere un campo "obbligatorio" in pipeline
   è una scommessa che la fonte lo esponga. AS24 non ha MAI esposto seller.phone in
   chiaro — fatto noto. Verifica l'esposizione del campo PRIMA di renderlo mandatory,
   non dopo il run.

3. **NON sprecare ciò che già funziona**: le 171 frasi corpus AS24 sono dati reali validi.
   Assicurati che corpus_register.md sia committato e leggibile a prescindere dal fix
   prospect — serve a Luke ORA, indipendentemente dai telefoni. (Già committato in 5ac1214.)

4. **SECONDARIO (non urgente)**: Subito 403 (captcha/parser) e automobile.it 404 (schema
   URL cambiato) → secondo step. AS24 da solo (184 listing) basta per la regione-pilota.
   Non bloccare S209 su questi due.

---

## DOVE INTERVENIRE

- `tools/s206_marche_scraper.py`
  - riga ~1093-1098: logica selezione `phone` da seller_listings
  - riga ~1164-1167: hard-skip D4 `if not phone: continue` → sostituire con regola
    no-SPOF (skip solo se manca phone E url profilo; altrimenti telefono="" + nota)
  - aggiungere helper estrazione telefono da testo (normalizza spazi/punti/trattini,
    valida prefisso mobile IT 3xx, 9-10 cifre)
  - `normalize_phone` esistente (verificare se gestisce cifre spaziate; probabilmente NO)
  - `build_prospects`: alimentare `desc_combined` già aggregato (riga ~1120) come fonte
    fallback telefono

## GATE S209 (onesto, 4 metriche come S207)

- Re-run scraper (idempotente, dedup telefono + dedup url profilo)
- Atteso: da 0 a N prospect (184 listing AS24 → operatori unici con phone-da-desc +
  prospect "tel_da_recuperare_manuale" con url profilo)
- Se resta GIALLO: spiega cosa è rotto, NON forzare VERDE
- Commit output aggiornato + EXECUTION_REPORT con nuova tabella onestà

## VINCOLI INVARIATI

- Branch `s206/marche-register` (NO push master)
- NO Ondata 2 (Puglia/Basilicata) finché Luke non valida Marche con lista telefoni vera
- NO contatti automatici operatori
- Re-run idempotente

## RIFERIMENTI

- Diagnosi S208: `research/s206_marche_register/EXECUTION_REPORT.md`
- Codice: `tools/s206_marche_scraper.py` (riga 1068 build_prospects, riga 1166 hard-skip)
- Direttiva originale: `prompts/s207_ritarget_micro_operatore_mandato.md`
