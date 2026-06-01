# ARGOS_MASTER — README
> Directory source-of-truth del sistema ARGOS completo. Generata 2026-06-01.

## A COSA SERVE
Questa directory esiste per un motivo preciso: **impedire che il modello ARGOS si perda tra una sessione e l'altra.** Ogni sessione Claude AI ricomincia da zero; gli handoff precedenti catturavano solo pezzi (lo scraping Marche, l'audit pre-pivot) e NON il sistema end-to-end a 5 fasi. Risultato: si ripartiva sempre dallo stesso punto. Questa directory chiude quel buco.

## COME USARLA
1. All'inizio di una sessione Claude AI nuova: incolla o fai aprire `00_INDEX/ARGOS_MASTER_PLAN.md`. È il file che da solo basta a riallineare.
2. Se la sessione tocca un'area specifica, apri anche il file di supporto relativo (vedi ordine sotto).
3. CC mantiene questa directory in git, branch dedicato. Quando lo stato tecnico cambia, **CC aggiorna `04_STATO_TECNICO/STATO_COMPONENTI.md`** — è l'unico file che descrive lo stato reale del codice, e CC ne è l'autorità.

## ORDINE DI LETTURA
1. `00_INDEX/ARGOS_MASTER_PLAN.md` ← SEMPRE per primo. Sistema completo, 5 fasi, vincoli, ordine di build.
2. `01_MODELLO/MODELLO_BUSINESS.md` ← economia e monetizzazione.
3. `02_FASI/PIPELINE_5_FASI_DETTAGLIO.md` ← dettaglio operativo di ogni fase.
4. `04_STATO_TECNICO/STATO_COMPONENTI.md` ← cosa è reale e cosa è da fare. Leggere PRIMA di dare per fatto qualsiasi componente.
5. `05_RISCHI_GATE/RISCHI_E_GATE.md` ← rischi aperti e gate da superare. Leggere prima di "build pesante".
6. `03_ASSET_VALIDATI/*` ← asset di vendita già prodotti e validati (persone, obiezioni, parametri, intelligence, scarsità). Da consultare quando si lavora su Fase 1/2.

## REGOLA D'ORO
Se un file di `03_ASSET_VALIDATI` dice "validato" si intende **validato come strategia/contenuto** (con fonti). NON significa "validato sul campo con dealer reali". La validazione di campo è tracciata solo in `05_RISCHI_GATE`. Non confondere i due.

## STATO CONTRIBUTI
- Modello a 5 fasi, nodo pagamento, lock-in: dettato da Luke (sessione 2026-06-01).
- Persone-dealer, obiezioni, parametri certificato, intelligence, scarsità: recuperati da sessioni passate (mar–mag 2026) via conversation_search.
- Stato tecnico componenti: da verificare/aggiornare con CC. I valori qui sono l'ultima fotografia nota a Claude AI, esplicitamente marcata come fallibile.
