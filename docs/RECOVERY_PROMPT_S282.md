# RECOVERY_PROMPT_S282 — ripartenza a freddo (prossima sessione = [A1] DEDICATA)

Lancia con ARGOS_HARNESS_UNLOCK=1. Sessione DEDICATA a [A1] (ROADMAP: anello critico, budget pieno, non aprire a budget speso).

## Stato chiuso in S281 (questa)
- [A0] WA daemon = `connected` (VERIFIED via probe reale: restart pulito `initializing→authenticated→connected`, niente QR, LocalAuth persistita). Era cache-state bloccata su `authenticated`, sessione viva.
- Token (S281 AZIONE 1) = applicati su iMac .env (OpenRouter + bot TG), getMe ok.
- NB ops iMac: in ssh non-interattivo `pm2`/`node` NON sono nel PATH → `pm2` in `~/.npm-global/bin`, node v20 in `~/.nvm/versions/node/v20.11.0/bin`, node v22 in `/usr/local/bin`.

## Routing freddo (nient'altro è istruzione)
STATE.md → docs/ROADMAP.md → docs/briefs/BRIEF_A_e2e_67_testfounder.md. In conflitto vince STATE/ROADMAP.

---
# PROMPT OPERATIVO [A1] — E2E 6-7 su TEST_FOUNDER

## Precondizioni (lo stato lasciato da [A0] è IPOTESI finché il curl non lo stampa ORA)
- **PRIMA AZIONE ASSOLUTA — curl letterale prima di tutto.** Nessun tocco allo scraper finché questo
  comando non stampa LETTERALMENTE `connected` sotto gli occhi, adesso:
  `ssh gianlucadistasi@192.168.1.2 'export PATH=/usr/local/bin:$PATH; curl -s localhost:9191/status | node -e "let d=JSON.parse(require(0));console.log(d.wa_status)"'`
  → `connected` = procedi. `authenticated` / `initializing` / qualsiasi altra cosa o ambiguità → **STOP**,
  ripeti [A0] (restart daemon), NON improvvisare. L'interpretazione dello stato-macchina del daemon è autorità di CC, non del giudice.
  La PRIMA cosa che Luke vuole vedere incollata è l'output letterale del curl. Da lì, step per step.
- Orario lavorativo (business_hours true) + Luke fisicamente sulla SIM 393314928901.
- SOLO TEST_FOUNDER 393314928901 — NESSUN altro numero, mai.
- **SINGLE-WRITER (sez. 2 standing rule):** nessun altro terminale CC scrive sul branch
  `s210/audit-master-plan` durante [A1]. Letture libere, scritture solo questa sessione.

## Sequenza [A1] (da BRIEF_A)
1. Scraper AS24 → 1 veicolo reale (config esatta, pool experiment-OFF, geo==IT).
2. Dossier onesto: banda p25-p75 (NON punto), margine INTERVALLO, fonte "prezzi richiesti".
   NB: base-mercato è gate-3 [D] non-fidata → questo è test di MECCANICA+RENDER, NON dei numeri.
   **RAMO THIN-POOL (definito PRIMA del lancio, non scoperto a metà):** se N < min_n della config esatta
   (soglia ADD-1, [D]/STATE cont3), il dossier rende ESPLICITO "comparabili insufficienti (N=x)" e NON
   emette banda/margine come se fidata. Il test resta VALIDO come meccanica+render. Per meccanica+render
   basta UN veicolo che renderizza — NON serve N≥soglia. Pattern-errore firmato S268/S271: numeri spinti a
   un layer che non li regge. Conta anche verso TEST_FOUNDER: l'artefatto che passa [A1] diventa il TEMPLATE
   del primo dealer reale — banda non-onesta su pool magro qui = spedita al dealer la volta dopo.
   Il giudice controllerà QUESTO al render.
3. AMBRA genera il Day-1 con voce nuova + disclosure Azzurra assistente di Luca + provenienza contatto + opt-out.
4. RENDER verificato leggendo l'output reale (pypdf / messaggio generato), NON descritto.

## >>> CHECKPOINT GIUDICE (vincolo #4 — azione irreversibile, NON auto-critica come gate finale) <<<
PRIMA dell'invio a TEST_FOUNDER e PRIMA dell'approve Gate-E:
- Genera in TextEdit un prompt per Claude AI web che includa, INLINE, TUTTI E TRE (manca uno → NO-GO
  automatico per insufficienza di artefatto, NON nel merito):
  (a) i 7 punti di BRIEF_A **VERBATIM** (il testo, NON "righe 17-28");
  (b) il messaggio Day-1 reale generato;
  (c) il testo del dossier **renderizzato** (output pypdf/lettura reale, NON descritto).
- Chiedi al giudice un verdetto GO / NO-GO sui 7 punti, con motivazione per ciascuno.
- Procedi all'approve SOLO con GO esterno. NO-GO → fixa e ri-sottoponi.

## Invio
5. Invio a TEST_FOUNDER via Gate-E (classe outreach_real → BLOCCA → packet → Luke incolla verdetto +
   `! python3 .harness/gate_e.py approve <slug>`). Se Gate-E NON scatta = bug del breaker, NON un successo.
6. MOSTRA l'output reale letto dal render (non a parole).

## Done-condition [A1] = checklist 7 punti VERDE sull'artefatto reale (BRIEF_A righe 17-28).
Chiudi verde o handoff strutturato (vincolo #6, mai PARTIAL su anello critico).
