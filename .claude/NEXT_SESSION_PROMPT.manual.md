# S224 — Fix #9 guard atomico (legacy) + E2E TEST_FOUNDER → VERIFIED verso 3/9

## STATO CHIUSO S223
### Verifica anelli su CODICE/DB REALE (no fix, solo verifica)
- **#6 inbox `messages` → VERIFIED EXISTS.** Conflitto S222 risolto: il gate "MISSING" guardava il DB SBAGLIATO.
  - DB iMac AUTORITATIVO `~/Documents/app-antigravity-auto/dealer_network.sqlite`: `messages` esiste, 14 col (11+3 ALTER) + 3 idx, **81 righe**. → memory S201/S202 corretta.
  - DB locale repo `./dealer_network.sqlite` = DB scraping (`dealers`+`market_*`), NO `messages`. Gate guardava questo. Lezione S204 (path identity.md ingannevole).
  - **#6 NON richiede fix.**
- **#9 HITL `sent=1/approved=0` → CONFERMATO ma confinato a path LEGACY.**
  - Riprodotto: 1 violazione `reply_e9be3ac6` (Test Concessionaria Founder, 2026-05-16) su `pending_replies` iMac.
  - **Bridge canonico = SAFE**: `wa-daemon.js:310-311` `WHERE approved_ts IS NOT NULL AND sent_ts IS NULL` (D-07 HITL strict). NON può inviare non approvato.
  - **Path UNSAFE (legacy)**: `telegram-handler.py:246` (subprocess `/approva`), `response-analyzer.py:1816` (send_script multi-msg) → scrivono `sent=1` senza ri-controllo `approved`. + `cmd_rifiuta` telegram-handler.py:302 manca guard `AND approved IS NULL` (la dashboard `db.py:406` ce l'ha).

### Gate
VERIFIED = **2/9** (#1 scrape + #6 inbox). #9 = bug safety reale ma già mitigato sul flusso produzione (bridge). Memory: `s223_verifica_anelli_6_9.md`.

## PROSSIMI STEP S224 (CTO raccomanda fix minimo, Luke ha chiesto opzione (a))
1. **Fix #9 guard atomico minimo (locale, NO deploy fino a E2E):**
   - `response-analyzer.py:1816` (send_script): `UPDATE pending_replies SET sent=1 WHERE id=? AND approved=1`; se `rowcount==0` → NON considerare inviato, log ERROR (il msg era stato rifiutato durante lo sleep).
   - `telegram-handler.py:246` (subprocess `/approva`): stesso guard `AND approved=1`.
   - `telegram-handler.py:302` (`cmd_rifiuta`): aggiungi `AND approved IS NULL` come la dashboard.
   - Code-review delegato (code-reviewer) prima del commit.
2. **E2E su TEST_FOUNDER 393314928901** (Luke FISICO — vedi feedback memory `test_founder_means_real_interactive`): scenario approva→rifiuta-durante-sleep deve risultare in NESSUN invio + `sent=0`. Gate qualitativo: Luke dichiara "soddisfatto".
3. **Solo dopo E2E verde** → deploy iMac (rsync atomico + healthcheck, vedi security.md). Prima del deploy: `lsof`/pm2 check.

## BACKLOG (non in scope S224)
- Migrare i path legacy multi-msg + Telegram diretto al bridge canonico (single-writer S173) → elimina la classe di bug invece del singolo guard. Coerente `feedback_single_writer_principle_bridge`.
- Verifica anelli #2..#5, #7, #8 per salire oltre 3/9.

## NON toccare
image_sanitizer.py / scope partner-unico (landing/Gemini/trasporto) CONGELATO. NO deploy landing/PDF.

## Vincoli sessione
- Context: S223 chiusa ~50%. Partire fresca.
- TEST_FOUNDER prima di qualsiasi dealer reale. Domenica = OFF Luke.
- Day 1 Stile Car blocker invariati: C-SAN-001, C-E2E-ZERO, C-COMM-INTEL-001, C-GATE-FONTE-001.
