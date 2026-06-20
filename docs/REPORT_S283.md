i891================================================================
REPORT SESSIONE S283 — ARGOS [A1] (E2E anelli 6-7)
Data: 2026-06-20 · Branch: s210/audit-master-plan · Commit: f160d78
================================================================


1. RAGIONAMENTO (le decisioni prese e il perché)
----------------------------------------------------------------

a) ROUTING A FREDDO
   Ho letto il recovery prompt (docs/RECOVERY_PROMPT_S283.md) e, come
   imposto dall'autorità di stato, ho seguito la catena:
   STATE.md → docs/ROADMAP.md → docs/briefs/BRIEF_A_e2e_67_testfounder.md.
   Questi dicono: la sessione è DEDICATA all'anello E2E 6-7 verso
   TEST_FOUNDER 393314928901, e per chiuderlo verde servono 7 punti
   spuntati su un artefatto REALE (PDF dossier + messaggio Day-1).

b) DUE GAP DI CODICE DA COSTRUIRE (non bypassare)
   Il recovery prompt aveva già diagnosticato, col codice alla mano, che
   due pezzi che i brief davano per ESISTENTI in realtà NON esistevano:
   - G1: la pipeline, quando i comparabili italiani sono pochi
     (thin-pool), faceva "return None" → ZERO dossier. Mancava il
     "dossier degradato" che dichiara l'incertezza invece di tacere.
   - G2: il generatore del messaggio Day-1 firmava ancora "sono Luca
     Ferretti" in prima persona → viola la decisione founder S277
     (i testi automatici li firma "Azzurra", assistente di Luca).

c) DECISIONE TECNICA SU G2 (vincolo #3: una sola raccomandazione)
   Il recovery prompt lasciava aperta una scelta: (a) correggere la
   firma di templates.py, oppure (b) cablare il path AMBRA (LLM live).
   Ho deciso (a). Motivo con dati: templates.py è str.format puro, ZERO
   LLM, OFFLINE → il messaggio è DETERMINISTICO e quindi i 7 punti della
   checklist sono VERIFICABILI con certezza. Il path (b) dipende dalla
   cascade LLM live (Groq/Gemini) → output non-deterministico, checklist
   non falsificabile. Scartato (b).

d) DECISIONE SU COME LAVORARE (vincolo #7 + REGOLA #0)
   La sessione è partita pesante (~50% di context già al primo turno,
   per via dell'auto-load di CLAUDE.md + memorie + 90 agent/skill).
   Lo scrape reale (243+ annunci) avrebbe saturato il mio context.
   Decisione: DELEGARE i due build (G1, G2) a due subagent
   backend-architect in context isolato e in parallelo, facendomi
   tornare SOLO il diff + l'artefatto verificato. Così lo "scrape
   rumoroso" è girato nel loro context, non nel mio. È esattamente
   ciò che imponevano sia REGOLA #0 (delega obbligatoria) sia il
   recovery prompt ("delega l'esecuzione rumorosa, verdetto-render a CC").

e) VERIFICA (lezione S240: mai fidarsi del verdetto di un subagent)
   Non ho accettato i report degli agent a scatola chiusa. Ho letto il
   DIFF REALE di on_demand_runner.py (git diff) per confermare che la
   logica thin-pool è corretta e che il REJECT-margine resta soppresso,
   e ho preteso che gli agent estraessero il testo VERBATIM (PDF via
   pypdf, messaggio via grep) come fatto terminale.


2. OPERAZIONI ESEGUITE (in ordine)
----------------------------------------------------------------

 1. Letto docs/RECOVERY_PROMPT_S283.md (le istruzioni della sessione).
 2. curl letterale stato daemon WA su iMac → "wa_status": connected
    (precondizione [A0] soddisfatta, verificata da me, non assunta).
 3. Letti STATE.md, ROADMAP.md, BRIEF_A (routing autoritativo).
 4. Letti i file di codice dei due gap:
    - tools/on_demand_runner.py (loop margin gate + generate_dossier)
    - tools/it_market_price.py (flag no_verdict, min_n=8)
    - tools/margin_gate.py (REJECT su surplus<=0)
    - wa-intelligence/templates.py (template Day-1)
 5. Delegato G1 a backend-architect (context isolato): implementa
    dossier degradato + esegue scrape reale Serie 3 + verifica render PDF.
 6. Delegato G2 a backend-architect (context isolato, in parallelo):
    corregge firma → Azzurra + opt-out + margine condizionale + entry
    point offline + verifica output.
 7. Letto git diff REALE di on_demand_runner.py per validare G1.
 8. Scritto docs/RECOVERY_PROMPT_S284.md (handoff prossima sessione).
 9. Commit f160d78 dei SOLI file nominati (2 sorgenti + handoff),
    pre-commit secret-scan PASS. NESSUN push (bloccato da GATE-0).


3. AVANZAMENTI E2E DI SESSIONE
----------------------------------------------------------------

   Anello / Stato PRIMA → DOPO

   [A0] daemon WA connesso ......... initializing(rischio) → CONNECTED ✓
   G1 dossier degradato thin-pool .. MANCANTE → COSTRUITO + render-verif ✓
   G2 cold Day-1 firma Azzurra ..... MANCANTE → COSTRUITO + output-verif ✓
   Anello 6-7 (E2E completo) ....... UNVERIFIED → ANCORA UNVERIFIED *
       * I 7 punti NON sono spuntati end-to-end fino all'invio:
         mancano i passi che richiedono te fisico + giudice esterno.

   PROVE RACCOLTE (fatti terminali, non parole):
   - G1: scrape reale 247 listing (DE 127 + NL 120), 4 candidati
     NO-VERDICT, 0 REJECT-margine → PDF DEGRADATO generato. Testo
     estratto con pypdf mostra "Comparabili insufficienti (N=...) —
     nessuna banda emessa" + "NO_VERDICT", ZERO banda p25-p75/margine
     spacciati come fidati. min_n=8 invariato.
   - G2: messaggio Day-1 generato (esempio PREMIUM, brand BMW+Mercedes):
       "Buongiorno, sono Azzurra, assistente di Luca Ferretti.
        Ho visto il suo salone su AutoScout24 — lavora con BMW e
        Mercedes, giusto? ...
        ... il margine dipende dal veicolo ...
        Se non e' interessato, mi scriva 'no' e non la disturbo piu' ..."
     grep superlativi (eccezion|migliore|unico|best|top|garantito) = 0;
     nessun "sono Luca" in 1a persona; disclosure + opt-out presenti.


4. NEXT STEP / PROMPT PREVISTO (docs/RECOVERY_PROMPT_S284.md)
----------------------------------------------------------------

   Restano i passi che NON posso auto-eseguire (servono te sulla SIM +
   un giudice esterno). In ordine:

   1. RENDER-VERIFY 7 PUNTI COMPLETO sull'artefatto UNICO finale
      (rigenera PDF degradato + messaggio cold, leggi entrambi, spunta
      i 7 punti verbatim). Punti 1-6 li faccio io (CC).

   2. CHECKPOINT GIUDICE (vincolo #4): preparo un TextEdit con dentro
      (a) i 7 punti verbatim, (b) il Day-1 reale, (c) il testo del
      dossier renderizzato → tu lo incolli a Claude AI per un GO/NO-GO
      esterno. Si invia SOLO con GO.

   3. INVIO a TEST_FOUNDER 393314928901 via Gate-E: la classe
      "outreach_real" BLOCCA l'invio e scrive un packet; tu incolli il
      verdetto + lanci  ! python3 .harness/gate_e.py approve <slug>.
      Se Gate-E NON scatta = bug del breaker (non un successo).

   4. DONE-CONDITION [A1] = 7 punti VERDI sull'artefatto reale + invio
      passato per Gate-E. Verde, oppure altro handoff (mai PARTIAL).

   COME RIPARTIRE:
   - Lancia la prossima sessione con  ARGOS_HARNESS_UNLOCK=1
   - Esegui  docs/RECOVERY_PROMPT_S284.md
   - Prima azione: curl stato daemon (deve essere "connected"),
     orario lavorativo, tu fisico sulla SIM.


5. NOTE DI CHIUSURA
----------------------------------------------------------------
   - Commit f160d78 è SOLO locale. Il push resta bloccato finché non si
     fa lo scrub della history (GATE-0/[F], filter-repo) — non è il
     rischio, è igiene separata. Non forzare il push.
   - Context chiuso a 60% (vincolo #7), chiusura ordinata.
   - Stato: handoff strutturato, NON "PARTIAL/arancione" (vincolo #6).
================================================================
