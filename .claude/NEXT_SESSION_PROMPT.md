# S226 — Ripartenza (riscritto a mano da CC, supersede stub auto-gen + handoff S225)

**Branch**: `s210/audit-master-plan` · **Generato**: 2026-06-02 · **Last commit**: `f63a1ee` (locale, NON deployato)
Questo file riscrive lo stub auto-generato. Fonte ricca precedente: `.claude/NEXT_SESSION_PROMPT.manual.md` (S225) — qui consolidata e corretta con la governance decisa il 2026-06-02.

---

## DIAGNOSI (condivisa, ancorata ai dati) — il meta-bug è la CONDIZIONE DI CHIUSURA
~130 sessioni (S94→S225), superficie enorme, **E2E integrato = 0**, **VERIFIED 2/9** anelli, e un campo
di stato auto-riportato (`sent` sul path Telegram) si è rivelato **falso**. Pattern reale: ottimismo in
build-mode → audit reattivo che bonifica. La bonifica è ottima ma è governance, non prevenzione.
Tre problemi: (1) costruisce componenti, non chiude la catena; (2) chiude al limite di budget non di
verifica (es. `f63a1ee`: fix di un path verificato-rotto, committato senza ri-review per "chiusura budget");
(3) verifica lo strato sbagliato (py_compile/simulazione, non runtime) → il bug quoting `cmd_approva`
ha tenuto `UPDATE sent=1` MAI eseguita per tempo ignoto, runtime silenziosamente rotto.

## 5 REGOLE OPERATIVE (estensione, NON sostituzione dei meccanismi che già funzionano)
Tieni: evidence path:riga su ogni claim · separazione code-verified vs E2E reale · scope-fence per sessione · self-audit con de-idratazione overclaim.

- **R1 — Chiusura a due binari.**
  • *Runtime-verificabile* (lo provi da solo): DONE solo dopo **esecuzione reale del path** (output reale, non "compila"/simulazione).
  • *Human-gated* (HITL / E2E founder / dealer reale): **MAI VERIFIED**. Commit `PENDING-GATE` + produci **GATE PACKET** pronto (comando esatto, scenario A/B, durata, cosa osservare, criterio pass) così Luke chiude in <10 min. La latenza del gate umano è il vero collo di C-E2E-ZERO: riducila preparando il packet, non aspettando.
- **R2 — Catena prima della superficie.** Percorso canonico unico: `scrape → CoVe → PDF → WA → reply → sign → paid`. Finché C-E2E-ZERO è OPEN: VIETATO aprire file/feature fuori dal percorso. Ogni sessione muove UN anello verso VERIFIED o consolida una fondamenta che lo blocca (R3). Niente espansione laterale (anti S159/S166).
- **R3 — Fondamenta = prerequisito, non feature.** Prima dell'E2E reale: (a) DB autoritativo unico (C-DB-SPLIT-001 + C-DB-ENV-001); (b) daemon stabile (C-WA-RESTART-001). **Time-box obbligatorio** (vedi sotto) o R3 diventa il buco-senza-fondo che vuole prevenire.
- **R4 — Niente stato su dato non riconciliato.** Dopo un bug che corrompe un campo, quel campo è **TAINTED** finché non riconcili. Concreto: `sent` su path TG inaffidabile → NON usarlo come verità. Reconcile = backlog **S224-1**.
- **Budget-rule (il meta-bug).** Se il context finisce PRIMA della verifica runtime R1: NON committare come DONE. Commit su branch + tag `UNVERIFIED-RUNTIME` + handoff dichiara "manca verifica runtime: <cosa>". Mai più una chiusura silenziosa al budget come `f63a1ee`.

## STATO ANELLO #9 (HITL guard) — riclassificato R1
**PENDING-GATE, non DONE.** `f63a1ee` è *code-verified only* (py_compile + simulazione). **VERIFIED resta 2/9** (#1, #6). Sale a 3/9 solo a gate fisico passato. Il fix è su MacBook; **l'iMac gira la versione vecchia** → senza deploy (P0) testi il bug, non la fix.

Comando reale (`wa-intelligence/telegram-handler.py:10-12,171-347`): `/approva <reply_id>`, `/rifiuta <reply_id>`.
Sleep anti-ban **random 90–720s** (`SLEEP_MIN,SLEEP_MAX = 90,720`, riga 52 — NON 90s fisso). Segnale indipendente da `sent`: log `[SENT]`/`[ERROR] rc=`/`[ABORT]` dal send_script (righe 262-277).

## GATE PACKET #9 — v2 (corretto: sent TAINTED + window-integrity)
```
PRE (CC): P0 deploy f63a1ee su iMac (rsync atomico + healthcheck — via devops-automator)
          P1 verifica runtime su iMac: DB di pending_replies · inbound TEST_FOUNDER genera
             riga approved=NULL · /approva accettato come testo (non solo inline button)

SEED (Luke ~1min): WA da SIM TEST_FOUNDER 393314928901 → numero ARGOS Business → annota reply_id da notifica TG

SCENARIO A — invio consentito:
  pm2 jlist → annota restart_time PRE
  /approva <reply_id> · attendi 90–720s
  PASS A (verità primaria) = msg ARRIVATO sulla SIM (osservazione Luke) + log [SENT]
  CONFERMA attesa (tertiaria, TAINTED, non decide) = sent=1
  DIVERGENZA (msg arrivato MA sent=0) = NON FAIL del guard → prova viva del latent bug storico → FINDING, aggancia S224-1
  pm2 jlist → restart_time POST; se ≠ PRE → VOID, retry

SCENARIO B — revoca durante sleep (nuovo reply_id2):
  pm2 jlist → restart_time PRE
  /approva <reply_id2> · SUBITO (<60s) /rifiuta <reply_id2>
  PASS B = NESSUN msg sulla SIM + log [ABORT] + sent=0 + approved=0
  pm2 jlist → restart_time POST; se ≠ PRE → VOID, retry (NON interpretare "no msg" come PASS)

EVIDENCE: osservazione fisica Luke (A+B) | log daemon [SENT]/[ABORT]/[ERROR] |
          SELECT id,approved,sent FROM pending_replies WHERE id IN (r1,r2) | restart_time PRE/POST
CHIUSURA: Luke "soddisfatto" → #9 DONE, VERIFIED 3/9.
```
Nota window-integrity: il gate **non** richiede C-WA-RESTART chiuso, richiede di SAPERE se il daemon è ripartito nei ~12 min del test. Il check `restart_time` PRE/POST (`pm2 jlist` → confermare nome campo sulla versione iMac) rende lo Scenario B interpretabile senza prima stabilizzare del tutto il daemon.

## ORDINE ESECUZIONE S226 (una cosa alla volta, sul percorso canonico)
1. **C-WA-RESTART-001 — time-boxed**: "daemon stabile" = 0 restart non-pianificati in finestra 6h (criterio misurabile, NON "root-cause trovata"). Root-cause time-box = 1 sessione; se non emerge → fallback = window-integrity check nel packet (sufficiente a rendere B interpretabile). Foundation completa resta task R3, **fuori dal critical-path del gate**.
2. **P0 deploy `f63a1ee`** su iMac (devops-automator). NB: codice solo su MacBook ora.
3. **P1 verifica runtime** su iMac (i 3 punti del PRE).
4. **Consegna GATE PACKET v2 a Luke** ed esegui il gate.

## VINCOLI / NON TOCCARE
- TEST_FOUNDER 393314928901 prima di qualsiasi dealer reale. **Domenica = OFF Luke** (no scadenze domenicali).
- `image_sanitizer.py` + scope partner-unico (landing/Gemini/trasporto) **CONGELATO**. No deploy landing/PDF.
- Day 1 Stile Car blocker invarianti: C-SAN-001, **C-E2E-ZERO**, C-COMM-INTEL-001, C-GATE-FONTE-001.
- Fondi di verità: `PLAN.md` (carte C-DB-SPLIT:178, C-WA-RESTART:179, C-E2E-ZERO:182). DB iMac autoritativo = `~/Documents/app-antigravity-auto/dealer_network.sqlite`.

## BACKLOG (non scope S226 salvo R4)
- **[S224-1]** Reconcile path TG: quante righe `pending_replies` con `approved=1 AND sent=0` ma msg realmente inviato (dati `sent` storici inaffidabili). Prerequisito R4 per fidarsi di metriche di invio su path TG.
- Migrare path legacy multi-msg + Telegram al **bridge canonico** (single-writer S173) → elimina la classe di bug.
- Verifica anelli #2..#5, #7, #8 per salire VERIFIED oltre 3/9.
