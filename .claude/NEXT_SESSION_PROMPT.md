# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-20T22:15Z` (chiusura S285) · commit corretti: `041e612` (G2 claim) + auto-close

> Lo stato reale (anelli E2E) è in `STATE.md` (`bash state/refresh.sh <SID>`). Sotto = fatti S285 da NON ripetere.

## S285 — FATTO (verificato, NON ripetere)
- **G1 chiuso**: thin_pool ⊆ no_verdict, disgiunto dai REJECT (diff letto).
- **G2 chiuso**: commit `041e612` — claim falsa "concessionari con cui lavoriamo" rimossa da templates.py righe 23 E 57 (DAY1_PREMIUM + DAY1_INTRO). grep claim = 0 su PDF e Day-1.
- **INVIO E2E ESEGUITO** a TEST_FOUNDER 393314928901: `POST /send` → `HTTP 200`, `msg_id=out_1781986351333_evd8h`, `daily_sent:1`, `first_contact:true`. Daemon `connected` al send (getState CONNECTED). Prima volta che la pipeline d'invio gira E2E reale.
- Artefatto: PDF `dossiers/ARGOS_BMW_Serie 3_2022_Concessionaria_Test_Azzurra_20260620_163650.pdf` (fissato, NO-VERDICT degradato) + Day-1 `/tmp/s285_cold_day1.txt`.
- Checklist BRIEF_A 7 punti: **1-6 VERDE** sul render reale + **invio riuscito**.

## 2 BUG DOC-vs-CODICE corretti in S285 (premesse handoff/giudice erano false)
1. **Business-hours**: il daemon HA `TEST_FOUNDER_PHONE=393314928901` (pm2 env) → `isAllowedToSend` (wa-daemon.js:798) bypassa business-hours per quel numero. L'invio parte anche fuori orario. Il blocco "outside business hours" NON si applica a TEST_FOUNDER.
2. **Gate-E**: `gate_e.py` definisce `outreach_real = invio a numero != TEST_FOUNDER`. TEST_FOUNDER è **ESCLUSO** dalla classe. L'invio al test number NON scatta Gate-E e NON crea `pending_review/<slug>.md` — è il design corretto, NON un bug. L'handoff/brief che dicevano "invio a TEST_FOUNDER scatta Gate-E" erano ERRATI. Aggiornare BRIEF_A punto 7.

## RESUME — cosa manca per VERIFIED anello 6-7
1. **[LUKE fisico]** conferma ricezione del Day-1 sulla SIM 393314928901 (gamba umana della done-condition). Lato-send già MET (HTTP 200 + msg-id reale).
2. **[A1] Gate-E dry test** (senza inviare a numeri veri): `python3 .harness/gate_e.py selftest` + verifica che un invio simulato a numero != TEST_FOUNDER classifichi `outreach_real` e scriva il packet. Questo prova il breaker sui dealer reali.
3. Solo allora anello 6-7 = VERIFIED. Correggere BRIEF_A punto 7 (premessa Gate-E).

## Invarianti
- Single-writer branch `s210/audit-master-plan`. Push BLOCCATO (scrub history [F] non fatto). Commit locale, file nominati (mai `git add -A`).
- Per inviare: env daemon ha TEST_FOUNDER_PHONE + ARGOS_API_KEY (lette da `pm2 jlist` → pm2_env, NON dal .env). Header `X-API-Key` obbligatorio su /send.
- ops iMac: `export PATH=$HOME/.npm-global/bin:$HOME/.nvm/versions/node/v20.11.0/bin:$PATH` per pm2.
