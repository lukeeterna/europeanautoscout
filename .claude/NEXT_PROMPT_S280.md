# PROMPT RIPARTENZA — S280

## Cosa è successo in S279 (control-plane + correzione copy)
- **Step [1] PRIORITÀ 0 CHIUSO** (commit `12b117b`, locale): MEMORY.md riga-indice 11 allineata a s273
  (2 garanzie separate completezza/purezza); STATE.md → S278 (firma Azzurra `ee0694f` CHIUSO-in-repo
  ma NON deployato iMac; enforcement secret `6a01884` nei vincoli). Backup Rule 1d fatti.
- **Copy Day-1 RISCRITTA (correzione strutturale, verificata vs codice)** in `.claude/COPY_DAY1_S278_PROPOSAL.md`:
  la v1 quotava prezzo-punto + margine-netto-punto-come-promessa → contraddiceva il dossier
  (`pdf_generator_enterprise.py:228-334`: banda p25–p75 + verdetto CONDIZIONATO, 320d breakeven 35.699).
  Falso-VERDE dell'arco un layer sopra (messaggio d'acquisto). v2 = **banda non punto + margine come TETTO
  condizionato + "km dichiarati"**. Regola: nessun numero nel cold message che non regga il dossier.

## In attesa di OK Luke (NON wirare prima)
- **N-pick (i) vs (ii)**: raccomando (i) banda+tetto (tiene il gancio numerico del RAGIONIERE, onesto).
  (ii) qualitativo è il fallback.
- **N1 `{FONTE_REALE}`**: qual è il canale reale da cui prendi il numero? La riga deve dirlo letteralmente
  (DB scrapato / AutoScout / pagina dealer). NB: "pubblico" ≠ base giuridica (canale deciso-finale, non riapro).
- **N2** differito (tuning archetipo dopo). **N3** wiring solo a 3 gate verdi.

## PRIMA AZIONE S280 (rinviata da S279 per context-budget): applicare nuovo token bot
Luke ha (ri)generato il token bot Telegram via @BotFather e lo incolla in `~/argos_new_bot_token_S280.txt`
(fuori repo, chmod 600). **Applicare a inizio S280 in finestra pulita** (NON fatto in S279: era context 59%,
mutazione shared-state vietata a saturazione):
**Token già VERIFICATO vivo in S279** (`getMe` OK → @Argosautomotivebot id 8691360619). Resta solo applicarlo.
1. leggere il token dallo scratch (MAI stamparlo); 2. aggiornare `ARGOS_TELEGRAM_TOKEN` in iMac
   `current/wa-intelligence/.env` (consultare `reference_imac_deploy_paths.md`); 3. restart daemon tg;
   4. verificare `getMe` OK; 5. **cancellare lo scratch**.
GitHub PAT — **RISOLTO S279, rischio NON vivo**: il token ARGOS = PAT "Antigravity (repo workflow)"
(nome = progetto app-antigravity-auto), **Expired May 11 2026 → morto**. Grep su tutta la history NON
trova `ghp_zgws…` raggiungibile (già scrubbato o prefix parziale) → niente chiave GH viva. Nessuna azione.
Igiene FLUXION (non bloccante): PAT eterni con scope admin larghi e inutilizzati → `stack_locale` (never
used, delete_repo+admin) da cancellare; valutare `fluxion-desktop`/`DropEvolutionPushToken`/`fluxion2`.

## GATE CHE BRUCIA — prima di [3] e [4]: ROTAZIONE 3 TOKEN (azione Luke)
S279 NON ha conferma che i 3 token siano revocati (la lista l'ha prodotta CC; la rotazione è azione tua).
Se NON fatto, è l'unica cosa urgente adesso (chiavi vive), precede tutto:
- OpenRouter `sk-or-v1-…2f13` (dato per ruotato S221 — CONFERMARE), GitHub PAT `ghp_zgws…` (dato per morto —
  CONFERMARE), bot Telegram @Argosautomotivebot (vivo per STATE.md §6 — RUOTARE via @BotFather se token in
  history == quello attuale su iMac `current/wa-intelligence/.env`). NON pastare i token interi.
Il push bloccato NON è il rischio; la chiave viva sì. Lo scrub (filter-repo) è igiene separata, non rotazione.

## Esegui DOPO conferma rotazione — ORDINE
[4] **E2E anelli 6-7** (raccomandato su [3]): gate HITL iMac + invio PDF a **TEST_FOUNDER 393314928901**.
   Sicuro (solo TEST_FOUNDER), muove un anello vero, e dà la **prima prova al RENDER** che Azzurra atterra
   nell'output generato (non solo nei literal — gap statico-vs-render del bundle Q3). ⚠️ Il PDF di test usa
   la base-mercato NON-fidata (gate-3) → è test di MECCANICA + render Azzurra, NON dei numeri (non leggere
   gli importi come reali). Prima azione che innesca Gate-E classe `outreach_real`.

[3] **filter-repo** — sessione DEDICATA, non "scegliamo qualcosa da fare". Chirurgia history distruttiva
   (commit ahead + force-push su più branch), finestra pulita. Meno urgente della rotazione.
   Piano: `.claude/PLAN_FILTER_REPO_S278.md`.

## Stato E2E (INVARIATO)
2/9A/5 VERIFIED(smoke) · 1/9B/6-7 UNVERIFIED · 8 BLOCKED(esterno). SoT = STATE.md.

## 3 gate tecnici a invio dealer REALE (nessuno legale: WA cold = deciso-finale)
(1) E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto"; (2) trasparenza in PRODUZIONE (Azzurra→sync.sh);
(3) base-mercato fidata (DEEP_PAGES≥80 + geo==IT + experiment-OFF).
