# HANDOFF — S295 · Unità C — 2026-07-04 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: READ-ONLY (eseguito gate preesistente `tools/validate_band.py`, nessun file di codice toccato)
- Mandato: Unità C S295 — instradare il 330i ATTRAVERSO validate_band.py (d586f03) sulla fixture geo-pura committata (ebe422e). Chiude Gate [3].
- Esito: 330i passato attraverso `gate_it_band` deterministico. **VERDICT** con banda **25.349,75 – 32.775,00 EUR**, `fallback_declared=true` (source=adjacent, trim droppato). Banda emessa SOLO dal gate.

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD `7f44d33` (2026-07-04, "session-close S295: handoff STATE E2E verbatim") · working-tree dirty (4 file, tutti generati da hook SessionStart, non miei)
- dirty non-miei: `.claude/NEXT_SESSION_PROMPT.md` (M, breadcrumb) · `.claude/scheduled_tasks.lock` (D) · `STATE.md` (M, rings refresh) · `state/rings.json` (M, refresh)
- commit di questa sessione: nessuno (READ-ONLY)

### FIXTURE CONFERMATA (autorità = disco)
- path: `tests/fixtures/it_dist_bmw_serie3_2021_s273cont4.json` (740.851 byte, 4 Lug 18:08)
- struttura: `{meta, listings}` · **count listings = 323** (= n_priced=323 atteso, coerente con ebe422e/S294 parse-fail=0)
- gate: `tools/validate_band.py` presente a `d586f03` (Unità A) · signature reale `gate_it_band(make, model, year, km, fuel, *, target_variant, ...)`

### VERDETTO 330i DAL GATE (output grezzo, una sola chiamata)
`gate_it_band("BMW","Serie 3",2021,40000,"petrol", target_variant="330i", fixture_path=...)`
- verdict: **VERDICT**
- banda p25–p75: **25.349,75 – 32.775,00**
- n_by_level: **L0=3 · L1=3 · L2=4 · L3=20** · soglia_n=8 (da it_market_price.MIN_N_DEFAULT, ratificata Luke S265)
- n_exact=4 (=L2; nessun livello esatto L0/L1/L2 raggiunge 8) · n_adjacent=20 · source=**adjacent**
- fallback_declared: **SÌ** (trim 330i droppato — N esatto sotto soglia, banda dall'adjacent = config esatta Serie 3 2021 petrol senza trim)
- NB: NO_VERDICT NON emesso — il livello adjacent (20 ≥ 8) sostiene una banda onesta con fallback dichiarato. Nessun `if` a mano.

### GATE [3] BASE-MERCATO — CHIUSO SÌ
Base-mercato instradata attraverso il gate deterministico su fixture geo-pura committata (323 IT, parse-fail=0). Il 330i produce un verdetto ONESTO (banda con fallback dichiarato, NON un falso-punto né scarsità inventata). Il finding S293 "leveling 330i bloccato da bug price-parse" è risolto (S294) e verificato E2E qui.

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md, verbatim — rigenerato 2026-07-04T16:28:16Z)
- 1 · invio Day1 WA · UNVERIFIED
- 2 · classifier intent (AMBRA) · VERIFIED (smoke)
- 9A · approve -> send · VERIFIED (smoke)
- 9B · reject -> abort · UNVERIFIED
- 5 · generazione dossier PDF · VERIFIED (smoke)
- 6-7 · approve HITL dossier -> invio PDF al dealer · UNVERIFIED
- 8 · contract -> sign_url · BLOCKED (fatto esterno: sign_url firmato dal dealer reale)

### GATE A DEALER REALE (da STATE.md §3)
- [1] E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto" = OPEN (anelli 1/6-7/9B UNVERIFIED)
- [E] trasparenza deployata in produzione 2026-06-30 (commit 118343b, ARGOS_ASSISTANT='Azzurra') = CHIUSO
- [3] base-mercato fidata (scrape esaustivo + geo==IT + experiment-OFF) = **CHIUSO** (Unità C: 330i attraverso il gate deterministico su fixture geo-pura 323)

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
6-7 E2E: gate HITL su iMac (fastapi) + invio PDF su TEST_FOUNDER 393314928901 (mai dealer reale). Prima azione che innesca Gate E classe `outreach_real`.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Anello 8 (sign_url) = firma del dealer reale (HITL fisico Luke o terzo).
- Gate [1] chiusura = Luke dichiara esplicitamente "pienamente soddisfatto" dopo E2E TEST_FOUNDER verde.

### BACKLOG (differito, NON prerequisito del primo invio)
- Far rispettare `approved_ts` a `/send` stesso (single-writer vero) — gated su autonomia-invio, non blocca 6-7.

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Il 330i esce come banda-fallback (adjacent), non come trim esatto: N_330i esatto = 4 su soglia 8. È esito legittimo e onesto del gate, non un difetto — la banda dichiara il fallback. Una banda 330i-esatta non è ottenibile: il pool esatto (L0-L2 max 4) è troppo piccolo — realtà fixture/mercato, non bug.
- Working-tree dirty = solo artefatti hook SessionStart (rings/STATE refresh, breadcrumb, lock). Nessuna modifica di codice in questa sessione.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (S292 autoritativo segmento/geografia) · STATE.md §3 (gate a dealer reale) · tools/validate_band.py (gate banda) · MEMORY.md (s293/s273 findings base-mercato)
