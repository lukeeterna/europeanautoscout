# BRIEF CC — ARGOS · ROADMAP S273→S275 verso DAY-1 (primo dossier reale a dealer vero)
# Branch s210/audit-master-plan · Fonte verita': codice + git. Chat NON e' fonte.

## STATO INGRESSO (S272 CHIUSA verde — ITEM 1 durabilita' DoD#4-i)
- commit f50d4b0 + ff4763a su origin. test_s271_render_artifact.py 5/5 (rigenera da fixture in
  tempdir, ricomputa i bound dalle helper, asserisce stream pypdf). Falsifier verificato: header
  con margine band_low (falso-PASS S268) -> test 320d FAIL. test_s269 6/6. DoD#4(i) DURABILE-chiuso.
- 2 AZIONI LUKE PENDENTI (una-tantum, dettaglio in .claude/REPORT_S272.txt):
  1) Gate E pointer indice MEMORY.md: `! python3 .harness/gate_e.py approve overwrite_sot-dc04f63aaf`
     (file-memoria topic gia' scritto; manca solo la riga-indice). Poi CC ri-fa l'Edit una volta.
  2) Restore 2 PDF demo (diff SOLO timestamp): `! git checkout -- tests/dossiers_s268/`.

# INQUADRAMENTO (non saltarlo): l'ENGINE (banda+verdetto+artefatto onesto) e' chiuso e durabile (S272).
# Day-1 = lo stesso engine alimentato da UN caso reale con scrape COMPLETE. NON serve fixare lo
# short-page sui 28 portali ne' automatizzare il sourcing DE: quelli gateano lo SCALING, non Day-1.
# Per UN dossier ti puoi permettere uno scrape lento-ma-completo (results_per_page=1, tecnica S264,
# una volta) e sourcing DE manuale (Luke sceglie 1 auto reale).
# REGOLA DANNO-ZERO: nessun dossier va a un dealer se la sua banda poggia su scrape sotto-raccolto
# (short-page) o cap-troncato. Il dealer rifa il conto: piu' comparabili di quanti dichiari = credibilita'
# (= prodotto) morta al primo contatto. SECONDO danno: non farti BLOCCARE da AS24.it (perdi la fonte).

## SEQUENZA (3 sessioni, NON una - non comprimere, no PARTIAL):
##   S273 = ITEM A (calibrazione) [+ ITEM B se avanza budget]
##   S274 = ITEM C (1 dossier reale end-to-end) - richiede 1 input reale da Luke
##   S275 = ITEM D (STATE.md) - housekeeping, NON gatea Day-1

## ITEM A (S273) - CALIBRAZIONE: lo scrape completo dice se il gate e' mercato o artefatto
Gate empirico DoD#4(ii). Famiglia vetrina (BMW Serie 3 2021), scrape ESAUSTIVO:
- "esaustivo" = fatto terminale = PAGINA VUOTA raggiunta SENZA cap (rimuovi max_pages per QUESTA run,
  override results_per_page=1 come S264, locale, non-mutante via object.__setattr__).
- CAVEAT RATE-LIMIT (verifica PRIMA di lanciare, su codice reale): results_per_page=1 = ~325 richieste;
  le costanti di produzione (DAILY_LIMIT=30, sleep, Semaphore) possono bloccare la run O farti bloccare
  da AS24.it. Riconcilia: run deliberata one-off, con throttle, FUORI dal daily-limit ma SENZA martellare.
  Se il rischio-blocco e' reale, FERMA e segnala a Luke prima di bruciare l'accesso.
- Ricomputa la tabella S264 (L0..L3, N per famiglia) sul pool NON troncato.
- FALSIFICA o conferma: 330i resta NO_VERDICT a config esatta, o era il cap? min_n=8 regge sui numeri completi?
- Persisti il pool esaustivo come NUOVA fixture committata.
- Ri-gira test_s271_render_artifact: ricomputa i bound da solo (by design) -> resta verde sulla nuova
  fixture; se il verdetto 330i cambia, il suo PDF cambia: NON e' regressione, e' il test che si risolve.
  Documenta il delta.
ESITO: sai se i verdetti sono veri sul mercato, non su una fetta. Chiudi a 60%.

## ITEM B (S273 se avanza, senno' S273-bis) - DEMO: canonico o campione? (DECISIONE LUKE prima di codice)
I 2 PDF in tests/dossiers_s268/ sono CAMPIONI (esempi di resa) o il DOSSIER CANONICO che mostrerai?
- Campione -> nessuna azione (il test rigenera in tempdir).
- Canonico -> assert in test_s271 "demo committato == rigenerato (timestamp a parte)": un drift
  codice-vs-PDF-mostrato viene preso. (L'incidente di sovrascrittura S272 prova che driftano.)

## ITEM C (S274) - UN DOSSIER REALE END-TO-END = il candidato Day-1
INPUT DA LUKE (se assente -> CC parca BLOCKED-ON-LUKE-INPUT e FERMA, non inventa):
- 1 annuncio DE reale (URL + prezzo + spec: modello/trim/anno/km/alimentazione/drivetrain).
  Sourcing manuale. NON automatizzare il sourcing per Day-1.
CC poi, in PRODUZIONE reale (NON fixture):
- Scrape COMPLETO AS24.it dei comparabili per QUELLA config esatta (results_per_page=1, fino a pagina
  vuota, no cap, throttle come ITEM A: e' UN'auto, lento-ma-completo te lo puoi permettere una volta).
- prezzo_de REALE (annuncio Luke) al posto dell'illustrativo.
- Genera il dossier reale -> render-verify pypdf E lettura umana dell'artefatto (lo stesso rituale che ha
  preso il Frankenstein): banda, verdetto, riga d'onesta', margine-intervallo coerenti e onesti SU DATO VERO?
ESITO: il primo dossier reale, verificato come artefatto. Questo porti a Day-1.

## ITEM D (S275) - STATE.md align (GATED Gate E) - housekeeping, ULTIMO, NON gatea Day-1
[invariato: pre-check hand-edit vs refresh.sh (memoria S243); Rule 1d backup-per-stat; diff-first; slug
Gate E si genera al primo Edit; allinea header S245->S272 + BLOCKED-ON DoD#4(ii)]. Falla quando comoda.

## INVARIATO
- NON allargare scope (no fix short-page-28-portali, no mobile.de, no automazione sourcing = tutti
  SCALING, non Day-1). NON delegare a subagent task atomici. system python3, MAI .venv.
  Output E2E > /tmp/s273.txt. Chiudi a 60% context. No PARTIAL.
- ITEM C dipende da Luke che fornisce 1 auto reale: dipendenza VOLUTA (sourcing a mano = edge di
  dominio), non un buco. Non automatizzare il sourcing per partire.
