# BRIEF CC — ARGOS · Sessione S265 (IDEMPOTENTE) — VERDETTO A BANDA + REPORT VERIFICABILE DAL DEALER
# Obiettivo: sostituire la mediana-puntuale (morta: i dati non la reggono) con un VERDETTO A BANDA onesto,
#            e un report che mostra il CAMPIONE così il dealer può RIFARE il conto, non solo fidarsi.
# NON-obiettivo: nessuna azione esterna, nessun invio dossier, nessuno scraping nuovo (pool depth già risolto S264).
# Progetto: /Users/macbook/Documents/combaretrovamiauto-enterprise (MacBook, macOS Big Sur)
# Branch: s210/audit-master-plan · Autorità: Luke · NESSUNA azione esterna.
# Fonte di verità: PLAN.md + STATE.md + git. Chat e "OK" passati NON sono fonte di verità.

## EREDITATO DA S264 (verificato su dati reali, non assunto)
- Pool depth RISOLTO: probe su 310 listing reali (vs 19) via override probe-local results_per_page=1.
- FATTO DI MERCATO: a config ESATTA (L0/L1) NESSUNA famiglia tocca N>=8, neanche su 310 listing. I comparabili vivono a L3 (trim droppato). La 330i resta thin pure a L3 (max 3).
- DECISIONE RATIFICATA (Luke): mediana puntuale per config esatta ABBANDONATA. Verdetto = BANDA + livello + N dichiarati.
- BUG PROD NOTO (NON in scope qui): base_scraper.py:374-375 short-page break sotto-raccoglie AS24.it ~1 volta su 2. Sessione dedicata (tocca base condiviso da 28 portali).

## PRINCIPIO DI PRODOTTO (il "perche'", non saltarlo)
Il dealer non si fida di un numero secco su un usato. Si fida di un PERITO che dichiara il campione.
Arma competitiva = trasparenza verificabile: N, quali comparabili, e una banda la cui LARGHEZZA racconta la verita' sul campione.
- Tanti comparabili -> banda STRETTA ("siamo sicuri").
- Pochi -> banda LARGA e onesta ("mercato sottile, attenzione").
- Pochissimi -> NO_VERDICT (gia' costruito): sigillo di serieta', non rinuncia.
DIVIETO ETICO STRUTTURALE: la banda NON deve mai sembrare piu' sicura di quanto il campione consente. Banda stretta su N piccolo = falso-PASS travestito (lo stesso bug ucciso in S256-S262). Vietato, e protetto da test.

## 3 GAP DA CHIUDERE (critica strutturale S264-closure — incorporati, non opzionali)
- GAP-1 (dispersione doppia a L3): la banda a L3 confonde dispersione-da-pochezza con dispersione-da-fusione-trim
  (L3 droppa il trim -> fonde allestimenti con prezzi diversi -> p25-p75 si allarga per MESCOLAMENTO, non per incertezza).
  REQUISITO: la banda deve separare i due, o almeno la riga d'onesta' DEVE dichiarare quale domina
  (es. spread infra-trim a L2 vs spread del pool L3). Senza, la banda L3 e' precisione finta travestita da onesta'.
- GAP-2 (snapshot di un giorno): la banda e' UNA scrape (310 listing, 10/06/2026). Il "dealer rifa il conto" si rompe a 7-30gg
  perche' i listing cambiano. REQUISITO: il report STAMPA la data-scrape + dichiara che e' una fotografia
  ("fascia calcolata il <data> su <N> annunci"). Senza data, "verificabile" e' falso.
- GAP-3 (ultima lucidatura interna prima del reale): il valore "il dealer si fida del campione" e' validato N=0.
  REQUISITO: il DoD nomina esplicitamente che il passo DOPO S265 NON e' un'altra sessione tecnica, ma il PRIMO dossier
  davanti a un dealer vero.

## REGOLE DI ESECUZIONE (idempotenza)
- Sicuro da rieseguire: nessun doppio effetto. Step guardati: se una modifica e' gia' applicata, salta.
- Converge su STATO FINALE (sez. DoD). Se gia' soddisfatto -> riportalo e FERMATI.
- NON delegare a subagent (lezione S258). Main context, output E2E rediretto su file (> /tmp/s265.txt 2>&1).
- Source-of-truth (STATE.md/PLAN.md): solo diff-first, mostra il diff a Luke prima di scrivere. Gate E da' falsi positivi anche su cp di backup: tieni l'edit SoT come ULTIMO passo.
- Reversibilita' (Rule 1d): backup verificato prima di ogni overwrite.

## FASE 0 - GROUND TRUTH (sola lettura)
a) git rev-parse --show-toplevel + branch corretti; git status pulito.
b) Conferma esistenti e NON regrediti: get_it_distribution (L0->L3, L4 RIMOSSO), ramo NO_VERDICT del PDF (S262), margin_gate (X1->REJECT).
c) Falsificazione X1 live: python3 -m tools.margin_gate -> REJECT EXIT 0. Se NO -> FERMATI.
Solo dopo a-c verdi si procede.

## FASE 1 - VERDETTO A BANDA (sostituisce la mediana puntuale come output del prezzo IT)
In tools/it_market_price.py, get_it_distribution deve restituire, oltre a quanto gia' produce:
- band_low, band_high: percentili del pool al livello usato (proposta p25-p75; Luke ratifica i percentili).
- band_width_pct = (band_high - band_low) / mediana.
- relaxation_level (L0..L3) e n gia' presenti.
- [GAP-1] spread infra-trim (L2) vs spread pool (L3) per dichiarare la natura della larghezza.
- confidence derivata DA N e dal livello, monotona e onesta:
    n < min_n               -> "NO_VERDICT"
    livello L3 (trim fuso)   -> confidence MAI "alta", a prescindere da N (dichiara la fusione del trim)
    altrimenti               -> scala con N.
  Aggiungi un TEST che FALLISCE se "confidence alta" coesiste con banda stretta su N piccolo.
- NESSUN allargamento attraverso drivetrain/motore per gonfiare N (L4 resta vietato).

## FASE 2 - REPORT VERIFICABILE DAL DEALER (il dealer RIFA il conto)
In pdf_generator_enterprise.py, la sezione verdetto deve mostrare in chiaro:
- La BANDA prezzo IT (band_low-band_high) invece/oltre la mediana puntuale.
- N comparabili + livello (es. "14 comparabili, stesso motore e trazione; allestimento non vincolato - livello L3").
- Il MARGINE come INTERVALLO derivato dalla banda: margine_min ... margine_max. NON un punto.
- [GAP-2] data-scrape + "fotografia": "fascia calcolata il <data> su <N> annunci AutoScout24.it".
- Riga di onesta' sul campione: se L3 -> "configurazione esatta sotto-rappresentata (N_L0=.., N_L1=..): stima su famiglia allargata" + [GAP-1] quale dispersione domina. Se NO_VERDICT -> label N+livello esistente.
- Il dealer deve poter leggere: quante auto, quali (motore/trazione/anno/km-band), e da dove deriva la fascia.
NON mostrare un numero puntuale spacciato per certo. La precisione DICHIARATA e' il prodotto.

## min_n - RATIFICA POSSIBILE QUI (con i dati S264)
Esiste ora una distribuzione reale (310 listing). PROPONI min_n difendibile dai numeri.
RACCOMANDAZIONE CC (dai numeri S264): a L0/L1 quasi tutto <8 -> min_n basso (~5) applicato SOLO a L3,
altrimenti NO_VERDICT domina a L0/L1. Luke ratifica. NON ratificare di nascosto.

## DoD (terminal fact reali; + FASE 0 verde)
1. get_it_distribution restituisce band_low/high/width + confidence onesta, col TEST che VIETA "confidence alta + banda stretta + N piccolo" (incolla il test che fallirebbe).
2. 1 PDF reale NEL REPO (non /tmp) su auto S264 reale (es. 320d xDrive, L3, N=14): banda prezzo + N + livello + margine-intervallo + data-scrape + riga onesta' campione. Path incollato.
3. 1 PDF reale NEL REPO sul caso thin (330i, N<=3): NO_VERDICT con N+livello reali. Path incollato.
4. [GAP-3] DoD nomina il passo successivo: PRIMO dossier reale a un dealer vero (decisione Luke), NON altra sessione tecnica.
Se uno manca -> BLOCKED-ON in STATE.md (diff-first), NON "completato".

## OUTPUT FINE SESSIONE
- <repo>/.claude/REPORT_S265.md: cosa costruito, 4 DoD con numeri/path reali, proposta min_n, ogni diff SoT mostrato, debito residuo.
- open -a TextEdit "<repo>/.claude/REPORT_S265.md"
- STATE.md diff-first.

## VINCOLI / ANTI-PATTERN
- Prova al layer giusto: PDF reali nel repo + test che vieta la banda-finta, NON "compila".
- NON reintrodurre precisione finta sotto forma di banda stretta non supportata da N.
- NON allargare lo scope: solo banda + report. Niente scraping nuovo, niente fix short-page (sessione dedicata), niente mobile.de.
- NON toccare cove_engine_v4.py distruttivamente. NESSUNA azione esterna.

## FUORI SCOPE (dopo S265)
- Fix bug prod short-page break (base_scraper:374) - sessione dedicata, tocca 28 portali.
- Primo dossier reale a un dealer reale - decisione di Luke, dopo che la banda e' verificabile.
- mobile.de / Vincario / stealth-scaling.
