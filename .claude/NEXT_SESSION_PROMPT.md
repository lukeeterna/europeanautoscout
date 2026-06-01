# S219 — Fossato-servizio import: verifica Gemini + wording materiali

## STATO (chiuso S218 a context 61%)
Research-first su S218 step2 ("rendere visibile handling import"). 3 sub-agent WebSearch a buon
fine (legal/operativo/competitivo), fonti citate. Sintesi in memory `s218_fossato_servizio_import_research.md`.

## SCOPERTA CHIAVE (convergenza 3/3)
**Soggetto IVA intracomunitaria = SEMPRE e SOLO il dealer (acquirente).** F24 Elide esce dalla sua P.IVA.
→ Claim S218 "gestisco IVA intracomunitaria" è FALSO + rischio AGCM D.Lgs 145/2007 (caso Prima Ass. €250k).
"gestisco" è FUORI. Per esserlo davvero ARGOS dovrebbe comprare lui l'auto (mandato senza rappresentanza
→ capitale+VIES, incompat zero-capex).

## MODELLO RACCOMANDATO (non finale, gated su Gemini)
ARGOS = "ufficio acquisti estero": coordina/orchestra, **il dealer compra e resta soggetto fiscale**.
Vero fossato = "trovo + ti QUALIFICO FISCALMENTE l'auto (margine vs IVA → margine netto reale) +
orchestro filiera assicurata; compri TU e tieni margine+regime IVA; paghi solo a deal chiuso".
Anelli orchestrabili a costo zero: targa export €50-80 / trasporto broker €350-900 / CoC €120-300 /
agenzia pratiche IT €300-600. Combo scouting-B2B-proattivo+success-fee+dealer-fiscale = territorio vuoto.

## PROSSIMI STEP S219
1. **Luke incolla in Gemini Deep Research** i 3 prompt consegnati nel thread S218 (priorità PROMPT 1
   FISCALE — è il kill-shot legale). Riporta gli output a CC.
2. **CC**: incrocia output Gemini in matrix VERIFIED/DISPUTED/UNVERIFIABLE (come S217). Chiudi
   raccomandazione finale sul wording esatto materiali.
3. **Solo dopo fiscale blindato**: riconcilia landing/index.html (Step03 :523, FAQ :588, card :476,
   fee :597 dicono OGGI l'opposto — "a parte/gestisci tu"). Poi PDF. Messaggi Day1 NO (rule vieta
   import/Germania/estero + gated C-COMM-INTEL-001).

## 3 VINCOLI da blindare
- L.264/1991: pratiche abituali per terzi = autorizzazione provinciale → ARGOS orchestra agenzia esistente.
- Qualificazione fiscale = "verifica documentale" non "consulenza" (servirebbe commercialista convenzionato).
- Trappola "auto nuova" IVA: <6 mesi O <6.000 km = IVA 22% sempre IT → colpisce premium km0/demo recenti.

## NON toccare
- image_sanitizer.py / codice produzione (S218 step1 TinEye manuale Luke su /tmp/s217_revtest/ ancora pending).
- landing/PDF/messaggi finché fiscale NON blindato (= scrivere claim su terreno non verificato).

## Rif
- memory: `s218_fossato_servizio_import_research.md`, `s217_anti_reverse_validation.md`
- blocker Day1 PLAN.md: C-SAN-001, C-E2E-ZERO, C-COMM-INTEL-001, C-GATE-FONTE-001
