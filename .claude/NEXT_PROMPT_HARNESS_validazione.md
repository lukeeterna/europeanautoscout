# PER IL GIUDICE — richiesta validazione prima di girare il mandato

Sessione precedente: a03f49f6 (PARTE A sospesa correttamente). CC ha valutato il tuo
next-prompt: **APPROVATO con 2 rilievi minori**, già integrati sotto come riga aggiunta
(marcata `[CC-ADD]`). Prima che il founder lo incolli a sessione fresca, conferma o correggi.

## I 2 rilievi CC (da validare)

**R1 — accoppiamento di PROPOSTA 1.** Far emettere a `combine.sh` *solo* il report della
sessione corrente richiede che quel report sia identificabile dall'hook (SESSION_ID nel
nome/path, o "ultimo per mtime"). Se oggi CC scrive l'handoff senza tag-sessione, la fix-1
è accoppiata: serve anche che CC scriva l'handoff in path noto con SESSION_ID. → riga `[CC-ADD]`
in PARTE B.1.

**R2 — naming `HANDOFF_S<n>`.** `<n>` non ha fonte deterministica per un hook (oggi S-numerato
a mano). CC propone `HANDOFF_<SESSION_ID>.md` (UUID già disponibile); il founder rinomina con
etichetta S<n> se vuole. → riga `[CC-ADD]`.

**Anche**: la lettura (c) deve mappare TUTTI i consumatori del nome `NEXT_SESSION_PROMPT.md`
(non solo SessionStart), per non rompere lettori esterni alla sessione.

**DOMANDA**: R1+R2 sono giuste o sovradimensionate? Procedo col prompt qui sotto?

═══════════════════════════════════════════════════════════════════
## MANDATO (con [CC-ADD]) — da incollare a SESSIONE FRESCA dalla root
═══════════════════════════════════════════════════════════════════

MANDATO: VALUTA-POI-BUILD (completamento PARTE A → build se conferma)
RIGA-1 SESSION-KILLER: apri Claude Code DALLA ROOT (~/Documents/combaretrovamiauto-enterprise),
NON da .claude/. PRIMA AZIONE: stampa `pwd`; se non è la root → FERMATI e dillo.

INTERVENTO SU HARNESS (non ARGOS). Ripresa della sessione harness a03f49f6 fermata correttamente
a PARTE A parziale per gate-context. Branch single-writer s210/audit-master-plan, no push.
ESECUZIONE: CC-MAIN, nessuna delega sub-agent per scrittura file. Il verdetto SOSPESO precedente
era corretto. Questa sessione legge i 3 corpi-script mancanti, POI verdetto, POI build se conferma.

FASE 0 — riallineo (riporta, NON modificare):
`pwd` root + `git rev-parse HEAD` (sopra b4c5ed6 = S288 reale) + `git status` (solo rumore-hook).
Se codice non committato oltre al rumore → FERMATI.

PARTE A (completamento) — 3 LETTURE MIRATE, poi verdetto. Per ciascuno cita le righe:
(a) `~/.claude/hooks/session_reports_combine.sh` — COME seleziona i report (tutti i .md / ultimi N
    / glob / filtro data-sessione)? È la causa del dump dei ~25 REPORT_S*.md vecchi. Riga esatta.
(b) `~/.claude/hooks/session_start_wrapper.sh` — SessionStart LEGGE NEXT_SESSION_PROMPT.md come
    istruzione, o lo scrive/ignora soltanto? Cita il punto.
(c) `~/.claude/hooks/global_session_end.sh` + hook `Stop` in `.claude/settings.json` — chi invoca
    global_session_end (scrive NEXT_SESSION_PROMPT + commit "auto-close")?
    [CC-ADD] In (c) mappa TUTTI i consumatori del nome `NEXT_SESSION_PROMPT.md` (grep su ~/.claude/
    e sul repo), non solo SessionStart: serve per non rompere lettori esterni alla rinomina.

VERDETTO PARTE A (obbligatorio):
- PROPOSTA 1 (handoff 1-file fisso, header SESSION_ID/HEAD/git-status + done-condition con output
  grezzo, NON il dump combinato): CONFERMO / CORREGGO (sul codice letto) / SCONSIGLIO.
- PROPOSTA 2 (proposta-next declassata a NOTA: rinomina + header "NON è un mandato" + SessionStart
  che NON la legge come istruzione): CONFERMO / CORREGGO / SCONSIGLIO.
- RISCHIO-AVVIO: cosa si rompe rinominando/cambiando combine.sh; quali hook dipendono dai
  nomi/percorsi vecchi; come lo eviti.
Se una richiede correzione STRUTTURALE o è sconsigliata → FERMATI dopo il verdetto, non costruire.

PARTE B — BUILD (SOLO se Parte A CONFERMA entrambe; applica le correzioni emerse):
Backup verificato PRIMA di toccare ogni file-hook (vincolo 1d): copia in *.bak, conferma esiste.
1. PROPOSTA 1: SessionEnd/combine scrive UN solo handoff della sessione CORRENTE (non il dump di
   tutti i .md), header fisso SESSION_ID + HEAD + git-status + done-condition(comando+output).
   La vecchia combine NON ri-emette più i report storici.
   [CC-ADD] Se la lettura (a) mostra che il report-corrente NON è SESSION_ID-tagged, la fix-1
   INCLUDE lo step di far scrivere a CC l'handoff in path noto con SESSION_ID. Nome file =
   `HANDOFF_<SESSION_ID>.md` (UUID già disponibile), NON `HANDOFF_S<n>` (S<n> non ha fonte
   deterministica per l'hook); il founder rinomina con etichetta S<n> a mano se vuole.
2. PROPOSTA 2: rinomina + header "NON è un mandato" + SessionStart che non la carica come
   istruzione (se (b) mostra che la legge, stacca la lettura; se non la legge, basta rinominare +
   header).
3. NON toccare altro della harness. ARGOS (collector/DB/scraper) NON si tocca.

DONE-CONDITION (esterna, falsificabile — prova su SESSIONE VUOTA):
1. Backup *.bak dei file-hook toccati → `ls -la`.
2. PROVA HANDOFF: forza una chiusura → UN solo `HANDOFF_<SESSION_ID>.md` col nuovo header →
   INCOLLA le prime 15 righe. Verifica che NON ri-emetta i ~25 REPORT_S*.md vecchi.
3. PROVA NO-AUTO-MANDATO: il file proposta-next esiste col nuovo nome + header "NON è un mandato"
   → INCOLLA l'header. Dimostra che SessionStart NON lo carica come istruzione (cita codice
   prima/dopo, o conferma che già non lo leggeva).
4. PROVA AVVIO NON ROTTO: apri sessione pulita da root → SessionStart gira senza errori, `pwd` ok,
   gate_e/state_guard risolvono i path → INCOLLA evidenza (nessun AttributeError/path-fail).
5. Commit dei soli file-hook nominati + backup non committato; no push.

OUTPUT: scrivi il REPORT nel nuovo `HANDOFF_<SESSION_ID>.md` (prima prova del formato) e APRILO
in TextEdit. Includi le 3 letture + verdetto Parte A + Parte B done-condition con evidenza.
