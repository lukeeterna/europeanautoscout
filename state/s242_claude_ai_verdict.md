# Verdetto gate esterno Claude AI — S242 (ANCORA, non re-litigare)

> Questo è IL PIANO per S243. Eseguire la sequenza in fondo. Non sostituire con giudizio interno di CC.

## Tesi centrale
Il difetto non è nei dettagli auto-isolati da CC. È nel **primitivo scelto**. Un source-of-truth
fatto di prosa non è verificabile contro la realtà in automatico → ogni sessione lo ri-indovina.
Correzione strutturale UNICA: la sezione di stato deve essere **generata da check eseguibili e NON
scrivibile da CC**. "VERIFIED" deve diventare un fatto CALCOLATO, non una frase digitabile.

## Verdetti
**1 — Direzione giusta, esecuzione no.** Consolidare 7→1 è necessario ma da solo non risolve: STATE.md
com'è (label copiate, prosa autoriale) è l'8º doc. Causa vera = "stato asserito come prosa non
ancorata + nessuna forcing function". Sequenza corretta: prima il SUBSTRATO che deriva lo stato dal
codice, poi STATE.md come RENDER di quel substrato, poi archivi. Non il contrario.

**2 — STATE.md copiato = non accettabile.** Copiare le label VERIFIED ricicla claim non verificati in
un doc che sembra autorevole = il veleno degli altri 7. Fix: in generazione, tutto ciò che non è
coperto da un check ESEGUITO-IN-QUESTA-SESSIONE o da un BLOCKED-ON congelato → **UNVERIFIED**. Un doc
che dice "non lo so ancora" è il primo che non mente.

**3 — Né 3 né 7 sezioni: numero = metrica sbagliata.** STATE.md contiene SOLO stato VOLATILE
(status anelli, task, step). Lo STABILE (vincoli, architettura) resta nel file canonico (CLAUDE.md)
e NON va copiato — duplicarlo drifta. Tieni: tabella anelli (GENERATA), task corrente, prossimi 3
step, 1 riga pointer archivio. "File critici" solo se indice-pointer minimale stile MEMORY.md.

**4 — Definizione operativa di "strutturale":** un gate è strutturale sse (a) applicato da uno strato
che CC NON può modificare in-sessione, e (b) ri-deriva una realtà che CC non può falsificare. Tutto
ciò che vive in memoria/istruzioni di CC (inclusa l'auto-critica) decade per costruzione (Huang et
al., self-correction intrinseca peggiora).

- **Gate A — verità generata, non scritta (max leva).** `state/rings.json` = {id, check_cmd,
  last_status, last_run_ts, last_run_session}. `refresh.sh` esegue i check_cmd e scrive
  status+ts+sessione. Tabella in STATE.md rigenerata tra marker `<!-- GENERATED -->`. Anello VERIFIED
  solo se last_run_session==sessione_corrente && pass, altrimenti STALE. Pre-edit hook rifiuta
  scrittura manuale dentro il blocco generato.
- **Gate B — snapshot realtà a session-start.** SessionStart hook esegue refresh (tier smoke veloce)
  PRIMA che CC agisca. Cold start riparte dalla realtà ri-derivata, non da un handoff. Due tier:
  smoke (ogni avvio) e full/E2E-su-numero-reale (on demand). VERIFIED-full chiude un anello.
- **Gate C — token di stato riservati.** Lint hook: se CC scrive "VERIFICATO"/"VERIFIED" in file di
  stato tracciato per anello non-pass-in-sessione → reject. Solo il generatore emette quei token.
- **Gate D — freeze fatto esterno (Rule 1b strutturale).** BLOCKED-ON porta blocked_on:"<fatto
  terminale esterno>" + revalidation_forbidden:true. refresh SALTA questi anelli; hook impedisce a CC
  di flippare BLOCKED-ON→VERIFIED senza sblocco esplicito di Luke.
- **Gate E — critico esterno non-episodico (meta-risposta).** Definisci una CLASSE di azioni
  irreversibili/high-stakes (overwrite source-of-truth, archiviazione doc, outreach reale, flip a
  VERIFIED-full, disattivazione hook). Per quelle, un hook BLOCCA, scrive `pending_review/<azione>.md`
  (packet precompilato come questo) ed esce non-zero: CC non procede finché Luke non incolla un
  verdetto esterno e un comando registra l'approvazione. Non decade perché lo applica l'harness.

**Condizione che tiene i gate:** i file harness (hook, config) stanno in path che CC NON può editare
(`.harness/` + i file-hook); un hook nega le scritture lì; modificarli richiede sì esplicito di Luke
(estensione di G-APPROVAL). Guardrail auto-modificabile = non guardrail.

**5 — Hook: TIENILO, ma reindirizza l'output (correzione che CC non aveva fatto).** L'incidente è la
pistola fumante: CC aveva letto cosa fa l'hook e stava per disattivarlo lo stesso perché il testo-
decisione S241 diceva "co-causa" = ha eseguito il testo sopra la realtà osservata (il pattern, in
diretta). MA NEXT_SESSION_PROMPT auto-generato è tra i 7 doc contraddittori. Quindi non disattivare:
**reindirizza**. Breadcrumb = "leggi STATE.md" + solo task corrente, ZERO ri-asserzione di status.
"Tenere intatto" lascia in piedi un generatore di doc #8.

## Sequenza da eseguire (done-condition falsificabile per step)
1. **Stop.** Non archiviare niente. Non spedire STATE.md con label copiate.
2. **Demote.** Riscrivi la tabella con TUTTO = UNVERIFIED tranne ciò che hai un check da eseguire ora.
   Done: STATE.md non contiene nessun VERIFIED non guadagnato.
3. **Substrato.** rings.json + refresh.sh + render tra marker. Anelli senza check → check_cmd=null →
   UNVERIFIED. Done: `bash state/refresh.sh` rigenera la tabella e una scrittura manuale nel blocco
   viene rifiutata.
4. **Guadagna gli status sui focus (5/6/7).** Scrivi lo smoke check, eseguilo, lascia che refresh
   popoli. Ciò che è rosso = vero gap → chiudilo con E2E sul numero di test. Done: VERIFIED su 5/6/7
   = output di un check passato in sessione.
5. **Freeze #8** come BLOCKED-ON:<fatto terminale esterno reale> + revalidation_forbidden. Done:
   refresh salta #8, hook impedisce il flip.
6. **Installa A–C + protezione .harness.** Done: in sessione nuova refresh parte da solo e CC non può
   editare né il blocco generato né i file-hook.
7. **Reindirizza l'auto-close hook.** Breadcrumb = pointer a STATE.md + task corrente, zero status.
   Done: il prossimo restart non genera prosa di stato.
8. **Ora archivia i 7 doc.** Backup verificato prima (Rule 1d), move in /archive, 1 riga pointer in
   STATE.md, commit git come checkpoint reversibile. Done: git log mostra il checkpoint e l'archivio
   è ripristinabile.
9. **Definisci la classe ad external-review + Gate E.** Done: tentare un'azione della classe blocca
   CC e produce il packet.

**Fatto verificabile che separa "ho risolto" da "ho scritto che ho risolto":** aprire una sessione
nuova a freddo, lasciare partire refresh, e vedere CC procedere dallo stato generato senza riscrivere
un solo handoff.
