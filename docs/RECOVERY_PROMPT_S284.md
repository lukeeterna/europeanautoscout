# RECOVERY_PROMPT_S284 — ripartenza a freddo ([A1] cont., DEDICATA, budget PIENO)

Lancia con `ARGOS_HARNESS_UNLOCK=1`. Sessione DEDICATA a [A1] (anello E2E 6-7).
Routing: STATE.md → docs/ROADMAP.md → docs/briefs/BRIEF_A_e2e_67_testfounder.md. In conflitto vince STATE/ROADMAP.
⚠️ Context: la sessione boota già pesante (~50% al primo turno per auto-load). Delega lo scrape rumoroso
ai subagent (context isolato) e tieni il main per verdetto-render + checkpoint.

## Chiuso in S283 (questa) — G1 e G2 LANDED + verificati al render/output, NON committati→committati locale
- **[A0] daemon `connected`** VERIFICATO via curl letterale (`wa_status: connected`, business_hours true). Precond [A1] OK.
- **G1 — dossier degradato thin-pool: FATTO.** `tools/on_demand_runner.py` (loop margin gate):
  i candidati NO-VERDICT (`it['no_verdict']`, n<min_n=8) ora finiscono in `thin_pool` invece di `continue`.
  Se `margin_passed` vuoto MA thin_pool non vuoto → dossier DEGRADATO del best deterministico (n↓ poi CoVe),
  con flag `_degraded_thin_pool`/`_thin_pool_n`. REJECT-margine (surplus≤0) resta SOPPRESSO (`return None`).
  `min_n=8` INVARIATO. **Verificato al render** (pypdf su PDF reale scrape Serie 3, 247 listing, 4 NO-VERDICT 0 REJECT):
  il PDF stampa "Comparabili insufficienti (N=…) — nessuna banda emessa" + "NO_VERDICT", ZERO banda p25-p75/margine fidati.
  Zero modifiche a `pdf_generator_enterprise.py` (la logica no_verdict→nessuna banda esisteva già ~2139/2152).
- **G2 — cold Day-1 parametrico Azzurra: FATTO.** `wa-intelligence/templates.py`: DAY1_PREMIUM/MIXED/GENERALIST/
  INTRO + IDENTITY_RESPONSE corretti da "sono Luca Ferretti" (1ª persona, vietato S277) → "sono Azzurra, assistente
  di Luca Ferretti"; promessa margine secca "3-5.000 euro" → condizionale; aggiunto opt-out ("mi scriva 'no'").
  Nuova `generate_cold_day1(dealer_brands, source, dealer_name)` offline zero-LLM. **Verificato sull'output reale**:
  grep superlativi (`eccezion|migliore|unico|best|top|garantito`)=0, nessun "sono Luca" 1ª persona, disclosure+opt-out presenti.

## RESTANO (i 4-5 della sequenza BRIEF_A — richiedono Luke fisico + giudice esterno, NON auto-eseguibili)
1. **Render-verify 7 punti COMPLETO** (BRIEF_A 17-28) sull'ARTEFATTO REALE: rigenera PDF degradato + messaggio
   cold Day-1, leggi entrambi (pypdf + output `generate_cold_day1`), spunta i 7 punti VERBATIM. Punti 1-6 da CC.
   NB: G1/G2 verificati separatamente in S283, ma la checklist a 7 punti va spuntata sull'artefatto UNICO e finale.
2. **CHECKPOINT GIUDICE** (vincolo #4): TextEdit con INLINE (a) 7 punti verbatim, (b) Day-1 reale, (c) testo dossier
   renderizzato → GO/NO-GO esterno Claude AI. Procedi all'invio SOLO con GO.
3. **Invio TEST_FOUNDER 393314928901 via Gate-E** (classe `outreach_real` → BLOCCA → packet → Luke incolla
   verdetto + `! python3 .harness/gate_e.py approve <slug>`). Gate-E che NON scatta = bug del breaker.
4. **Done-condition [A1]** = 7 punti VERDE sull'artefatto reale + invio passato per Gate-E. Verde o handoff (mai PARTIAL).

## Precondizioni invarianti
- PRIMA AZIONE: `ssh gianlucadistasi@192.168.1.2 'curl -s localhost:9191/status'` → `"wa_status": "connected"`. Se no → [A0] wa-daemon-ops.
- Orario lavorativo + Luke fisico sulla SIM 393314928901. SOLO TEST_FOUNDER, nessun altro numero.
- Single-writer: solo la sessione [A1] scrive su branch s210/audit-master-plan.
- Commit S283 = SOLO locale (push bloccato da scrub history GATE-0/[F], filter-repo non fatto). NON forzare il push.
- NB ops iMac ssh: pm2 in `~/.npm-global/bin`, node v20 in `~/.nvm/versions/node/v20.11.0/bin` (daemon usa better-sqlite3 ABI node v20).
