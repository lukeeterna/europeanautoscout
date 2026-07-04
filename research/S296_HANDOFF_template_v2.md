# S296 HANDOFF — template dossier v2 (blocco #2 pre-pilota)

STATO: reality-check COMPLETO + piano-edit esatto pronto. ZERO edit applicati (generatore
== HEAD, ripristinato da backup a context 61% per non lasciare stato PARTIAL, vincolo #6).
Prossima sessione: eseguire i 12 edit sotto in UN colpo → py_compile → 3 PDF (UNITÀ B).

## VERITÀ GIT
- branch s210/audit-master-plan · HEAD a903d57 · working-tree pulito (solo STATE.md/rings.json/NEXT auto).

## REALITY-CHECK (autorità = disco, verificato leggendo il file)
GENERATORE REALE: `tools/scripts/pdf_generator_enterprise.py` (gira su MacBook, NON iMac;
invocato da `tools/on_demand_runner.py:305-310` come subprocess). Righe incriminate REALI:
- 1394: `<font size="8">Luca Ferretti — ferretti.argosautomotive@gmail.com</font><br/>`
- 1346: `['Check frodi ARGOS', 'Superato' if vin_consistent else 'ALERT', ...]`  ← "Superato generico"
- 1395 + 1756: `Generato il {datetime.now().strftime(...)}` (footer singolo + footer combinato 1754-1757)

AGGANCIO BANDA (discordanza #2): il PDF NON consuma `gate_it_band` (validate_band.py S295 —
self-test only, FUORI dal path runtime). Consuma `_it_distribution` prodotto da
`get_it_distribution` (it_market_price.py:248), settato in `on_demand_runner.py:511/523`.
Campi presenti: `no_verdict`, `relaxation_level` (L0-L2=esatto, L3=adiacente=fallback),
`n_by_level`, `band_low/high`, `n`, `is_floor`, `scrape_date`. NON c'è `fallback_declared`
letterale → DERIVARLO: `fallback = (relaxation_level==3) and not no_verdict`. Assembly dati
in `generate_dossier` (2086-2149); rendering banda in `_margin_verdict_rows` (259) +
`_create_it_distribution_section` (1052). NO_VERDICT già gestito (269-276, 1078-1081).

CAUSA RIUSO DATA/dossier_id (discordanza #3): NON è riuso. Data = `datetime.now()` al RENDER
(1395/1756), filename con ts fresco (`datetime.now().strftime('%Y%m%d_%H%M%S')`, 2074-2076).
NESSUNA cache, nessun record dossier riusato, nessun dossier_id deterministico. "01/07 su
re-run 03/07" = STESSO PDF riaperto, non rigenerato. → Nessun bug data da fixare; punto 5
mandato già soddisfatto dal codice. (Da chiudere: verificare che on_demand_runner NON salti
la generazione se il PDF esiste già — non riscontrato skip-if-exists ma non letto E2E.)

KB anti-frode (LEVA/CERTEZZA): `kb/dominio/frode_km_verifica.md`. Fatti usabili (tag [T*]):
- import ~3x rischio km: 6,3% importate vs 2,1% domestiche, carVertical dic 2025 [T3] (ordine
  di grandezza, fonte commerciale UNICA, NON certificato — mai "certo").
- MATRICE certezza (righe 35-38): NL/RDW=AUTONOMO (da targa, A) · FR/Histovec+BE/Car-Pass=
  SU-RICHIESTA (B) · DE=COMMERCIALE (nessun registro pubblico, C). REGOLA riga 38: "il tier
  A/B/C si assegna sul DOCUMENTO OTTENUTO, non sul paese di targa".
ASSISTANT: `ARGOS_ASSISTANT='Azzurra'` (wa-intelligence/response-analyzer.py:68, commit 118343b);
firma template Day1 "Azzurra, assistente di Luca Ferretti" (templates.py:14-18).

## ⚠️ CRITICA STRUTTURALE (vincolo #4) — TENSIONE DA DECIDERE CON LUKE PRIMA DEGLI EDIT
La certezza A/B/C keyed su `country_code` + i nomi documento (RDW/Car-Pass/Histovec) RIVELANO
il paese di origine. Ma C-GATE-FONTE-001 NASCONDE la fonte (URL/portale/paese) fino a
post-pagamento (source_url="" a 2118). Rischio: LEVA/CERTEZZA nel dossier PRE-pagamento
LEAKA l'origine. DECIDERE: (a) mostrare A/B/C+documento solo nel source_dossier post-pagamento;
oppure (b) pre-pagamento mostrare solo la CLASSE regime (autonomo/su-richiesta/commerciale) +
"documento km ufficiale del paese d'origine" SENZA nominare paese/documento. Il piano sotto è
la versione country-driven (mandato letterale): applicare SOLO dopo scelta Luke (a)/(b).

## PIANO-EDIT ESATTO (12 modifiche, tutte in pdf_generator_enterprise.py)
BACKUP 1d PRIMA: `cp .../pdf_generator_enterprise.py .../.bak-s296` (ls, size>0, cita nell'output).

1. VehicleData (dopo margine_netto_high ~145): `country_code: str = ""` · `fraud_doc_obtained: bool = False` · `fallback_declared: bool = False`.
2. Helper modulo (prima di `def _margin_verdict_rows` ~259) `_fraud_source_certainty(country_code, doc_obtained=False)`:
   NL→("A","RDW kentekencheck","pubblico da targa (autonomo)") · FR→("B","Histovec","su richiesta: link titolare") ·
   BE→("B","Car-Pass","su richiesta/contrattuale, B2B non dovuto") · DE→("C","TÜV HU-Bericht/aggregatore","nessun registro pubblico") ·
   default→("C","documento estero","verificabilità da confermare"). doc_obtained=True→(grade,f"Certezza {grade}",f"{doc} ottenuto — {access}");
   NON ottenuto→("—","Documento non ancora ottenuto",f"{doc}: {access}"). MAI "Superato".
3. `_margin_verdict_rows` NO_VERDICT note (273-274) → "Campione insufficiente per una banda affidabile (N=..., livello L...) — nessuna banda emessa".
4. `_margin_verdict_rows` banda note (281-289): calc `_nbl=vehicle.it_n_by_level or {}; _n_exact=_nbl.get(2,_nbl.get('2',0)); _prov = f'banda su config. adiacente: campione trim insufficiente, N={_n_exact}' if vehicle.fallback_declared else 'banda a config. esatta'`; nota 'Prezzo mercato Italia' → f'Banda p25-p75, {floor}{n} comparabili — {_prov}'.
5. `_create_it_distribution_section` else (1082-1087): suffisso fallback a row1 nota (stesso _n_exact da it_n_by_level).
6. Footer singolo 1394 → `Azzurra — assistente di Luca Ferretti | ferretti.argosautomotive@gmail.com`.
7. Footer combinato 1754: `| Luca Ferretti | Scouting EU esclusivo` → `| Azzurra — assistente di Luca Ferretti`.
8. `_create_verification_section` prima di `verification_data=[` (~1338): `cert_grade,cert_status,cert_note=_fraud_source_certainty(vehicle.country_code, vehicle.fraud_doc_obtained)`.
9. Riga 1346 → DUE righe: `['Coerenza dati/VIN','Coerente' if vin_consistent else 'ALERT', 'Nessuna incoerenza interna' if vin_consistent else (vin_alerts[0][:50] if vin_alerts else 'Verifica manuale')]` + `['Verifica km alla fonte', cert_status, cert_note]`.
10. Loop status_styles (1353-1359): `amber_color=HexColor('#B45309')` + `elif status.startswith('DOCUMENTO NON') or status=='—':` → TEXTCOLOR ambra col1 (non verde-positivo).
11. Nuovo metodo `_create_fraud_leva_section(self, vehicle)` (prima di `_create_footer` ~1383): Table SPAN header "VERIFICA ANTI-FRODE ALLA FONTE" + righe Paragraph: rischio km import [T3 disclaimered], documento richiesto (cert_note), certezza sul documento (cert_status + "il tier A/B/C si assegna sul documento ottenuto, non sul paese"). SOLO copy da KB.
12. Story (dopo executive_summary ~404): `story.append(self._create_fraud_leva_section(vehicle)); story.append(Spacer(1,6*mm))`.
    + Assembly (2086-2149): `_it_fallback=it_dist.get('fallback_declared'); if None: (it_dist.get('relaxation_level')==3) and not bool(it_dist.get('no_verdict'))`; a VehicleData(...): `country_code=best.get('country','') or ''`, `fraud_doc_obtained=bool(best.get('_fraud_doc_obtained',False))`, `fallback_declared=bool(_it_fallback)`.

POST-EDIT: `python3 -c "import ast;ast.parse(open('tools/scripts/pdf_generator_enterprise.py').read())"` + smoke import.

## UNITÀ B — 3 PDF DI PROVA (done falsificabile = file su disco apribili da Luke)
Modello: `tools/scripts/build_s268_dossier.py` costruisce `_it_distribution` inline e chiama il
generatore — riusare quel pattern (o `get_it_distribution(fixture_path=...)`). Generare:
(a) 330i REALE fallback dichiarato: fixture geo-pura Serie3 (memory s293) → mostra "banda su
    config. adiacente" + certezza documento paese reale.
(b) sintetico NO_VERDICT: `_it_distribution` no_verdict=True, band_low/high=None → blocco
    "campione insufficiente per una banda affidabile" visibile.
(c) sintetico exact-config: relaxation_level<=2, band piena, fallback_declared=False.
Consegnare a Luke i 3 path (ls -la incollato). VERIFICA VISIVA = Luke apre i PDF. Nessun "test
passa" senza PDF apribili.

## BLOCKED-ON
Decisione Luke su tensione C-GATE-FONTE-001 (punto ⚠️) prima di esporre certezza country-driven
in dossier pre-pagamento. Tutto il resto è eseguibile subito col piano sopra.
