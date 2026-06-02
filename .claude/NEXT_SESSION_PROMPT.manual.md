# S225 — Re-review temp-file rewrite + E2E TEST_FOUNDER fisico → deploy iMac

## STATO CHIUSO S224 (commit f63a1ee, locale, NON deployato)
Fix anello #9 guard atomico HITL su 2 path legacy. 3 modifiche:
1. **`response-analyzer.py` send_script**: re-check `approved` dopo sleep → abort PRIMA del POST se non approvato (`sys.exit(0)` + `[ABORT]`). `UPDATE sent=1 ... AND approved=1` + rowcount (log ERROR se 0). [path già temp-file, quoting OK]
2. **`telegram-handler.py` cmd_approva**: RISCRITTO da bash-chain a **temp-file Python** (`send_script` + Popen `sys.executable`). Re-check `approved` dopo sleep → abort prima di `node sender`; poi `subprocess.run(['node', WA_SENDER, wa_id, reply_text])`; poi `UPDATE sent=1 ... AND approved=1` + rowcount. Aggiunto `import tempfile`.
3. **`telegram-handler.py` cmd_rifiuta**: guard `AND sent=0` (consente revoca durante sleep, blocca revoca post-invio) + early-return se già `sent=1`. NON `approved IS NULL` (rompeva lo scenario approva→rifiuta).

### Scoperte S224 (vincolo #4/#11 — root cause)
- **Il guard prescritto dal handoff S224 era logicamente tardivo**: l'invio WA avveniva PRIMA della `UPDATE sent=1` → registrava `sent=0` ma il msg era già partito. Fix corretto = re-check PRIMA dell'invio.
- **`approved IS NULL` su cmd_rifiuta avrebbe rotto il gate E2E** (lo scenario richiede reject DOPO approve). Usato `sent=0`.
- **LATENT BUG STORICO confermato empiricamente**: il vecchio `python3 -c "..."` in cmd_approva aveva quoting bash rotto (bash chiude le `"` su `os.environ["X"]` → python riceve bareword → SyntaxError). Quindi la `UPDATE sent=1` via path Telegram **non è MAI stata eseguita**: le reply approvate via TG venivano inviate (`node` ok) ma `sent` restava 0. → vedi BACKLOG.

### Verifica fatta (codice, NON E2E reale)
- `py_compile` OK su entrambi i file.
- Simulazione approva-vs-rifiuta-durante-sleep: node invocato SOLO per l'approvato, `sent=1`; per il rifiutato node NON invocato + `sent=0` → **NESSUN invio**. (E2E_GUARD_PASS)
- code-reviewer 1° giro: FAIL su HIGH quoting bash (corretto via rewrite temp-file). **Il rewrite NON è stato ri-revisionato** (chiusura budget).

## PROSSIMI STEP S225 (ordine)
1. **Re-review delegato (code-reviewer)** del NUOVO cmd_approva temp-file rewrite (commit f63a1ee) — sanity su: import tempfile, sys.executable in contesto PM2 python3.13, `node` su PATH dentro subprocess.run, gestione returncode, idempotenza. (1° review era su versione precedente.)
2. **E2E su TEST_FOUNDER 393314928901 — Luke FISICO** (feedback memory `test_founder_means_real_interactive`): 
   - Scenario A: `/approva` → lascia partire → verifica msg ricevuto + `sent=1`.
   - Scenario B: `/approva` → `/rifiuta` DURANTE lo sleep (SLEEP_MIN=90s, ampia finestra) → **NESSUN msg ricevuto** + `sent=0`.
   - Gate qualitativo: Luke dichiara "soddisfatto".
3. **Solo dopo E2E verde** → deploy iMac (rsync atomico + healthcheck, security.md). Pre-deploy: `lsof`/pm2 check. NB: il codice è su MacBook, l'iMac gira la versione vecchia → il fix NON è attivo finché non deployi.

## BACKLOG (non scope S225)
- **[S224-1] Latent bug storico**: reply approvate via Telegram avevano `sent=0` (UPDATE mai eseguita per quoting rotto). Verificare quante righe `pending_replies` iMac hanno `approved=1 AND sent=0` ma msg realmente inviato → reconcile. Non è regressione del fix (il fix lo risolve d'ora in poi), ma i dati storici `sent` del path TG sono inaffidabili.
- Migrare i path legacy multi-msg + Telegram al **bridge canonico** (single-writer S173) → elimina la classe di bug. Coerente `feedback_single_writer_principle_bridge`.
- Verifica anelli #2..#5, #7, #8 per salire VERIFIED oltre 3/9.

## Gate / VERIFIED
- VERIFIED resta 2/9 (#1, #6). #9 = fix scritto+code-verified ma **non chiuso** finché E2E fisico Luke non passa → poi sale a 3/9.

## NON toccare
image_sanitizer.py / scope partner-unico (landing/Gemini/trasporto) CONGELATO. NO deploy landing/PDF.

## Vincoli sessione
- TEST_FOUNDER prima di qualsiasi dealer reale. Domenica = OFF Luke.
- Day 1 Stile Car blocker invariati: C-SAN-001, C-E2E-ZERO, C-COMM-INTEL-001, C-GATE-FONTE-001.
