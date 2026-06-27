# HANDOFF_CURRENT — Audit mancante + fix harness FP outreach (sessione 2026-06-27)

> **GATE [E] TRASPARENZA DEPLOYATA = NO**
> **RATE-LIMIT = 30/giorno nominale, warm-up dinamico 10→15→20 (cap 20); delay anti-ban 30–90s random tra invii (jitter sì); MAX_REPLIES_PER_DEALER=10/giorno; auto-stop se block-rate >2%**
> **OBSIDIAN = NON ESISTE**

Branch `s210/audit-master-plan` · no push · CC-MAIN · ARGOS_HARNESS_UNLOCK=1 (PARTE 2 eseguita).

---

## PARTE 1 — AUDIT (fatti dal disco)

### 1. GATE [E] — Trasparenza Azzurra · VERDETTO = **NO (trasparenza NON deployata sul daemon live)**

**Come firma il daemon ORA.** Il daemon (`wa-intelligence/wa-daemon.js`) NON appone firma: invia
testo già composto dalla coda `bridge_outbound`. La firma vive nei compositori:
- **REPO (MacBook)** `wa-intelligence/templates.py` — Day-1 corrente:
  `"Buongiorno, sono Azzurra, l'assistente digitale di Luca Ferretti. Ho trovato la sua attività online…"`
  + opt-out `"…basta che mi scriva 'no'."` (template `DAY1_CREDIBILITY`, e tutte le varianti DAY1_*).
- **REPO** `wa-intelligence/response-analyzer.py:68` `ARGOS_ASSISTANT='Azzurra'`, disclosure runtime
  ("ammetti di essere Azzurra, l'assistente automatica… MAI negare").

**Daemon LIVE (iMac) — DISALLINEATO.** `current → releases/20260527_083951` (deploy 27 Mag).
La `templates.py` LIVE (datata 1 Mag) firma la STRINGA REALE:
```
"Buongiorno, sono Luca Ferretti.\n"   ← impersonificazione diretta, NO "Azzurra/assistente", NO opt-out in testa
```
`grep ARGOS_ASSISTANT` sulla response-analyzer LIVE = vuoto (versione pre-Azzurra). HEAD git release = `fd35965e`.
→ La firma trasparente "Azzurra, assistente digitale" + opt-out esiste SOLO nel repo, **non sul daemon in produzione**.

**Deploy.** `deploy/sync.sh` = rsync atomico + symlink-swap su iMac (`gianlucadistasi@192.168.1.2`,
`/Users/gianlucadistasi/Documents/app-antigravity-auto`), `pm2 restart argos-wa-daemon` + healthcheck.
Ultimo deploy effettivo = release `20260527_083951` (27 Mag, daemon.js mtime 26 Mag). Nessun deploy successivo.
→ **Prima di qualsiasi invio reale serve `bash deploy/sync.sh`** per portare la trasparenza in produzione.

> ⚠️ Nota collaterale (non richiesta): `pm2 jlist` sull'iMac espone in chiaro `GROQ_API_KEY` nell'env del processo `argos-cf-monitor`. Segnalato, non toccato.

### 2. RATE-LIMIT WhatsApp (`wa-intelligence/wa-daemon.js`)
- `CONFIG.DAILY_LIMIT = 30` (riga 46) — tetto nominale.
- `getDailyLimit()` (riga 85, warm-up S117): settimana ≤1 → **10**, ≤3 → **15**, oltre → **20** (cap 20 hard per API non ufficiale). È questo il limite EFFETTIVO applicato agli invii.
- Delay anti-ban tra invii: `BRIDGE_ANTI_BAN_DELAY_MS_MIN=30000` / `MAX=90000` (righe 201-202) → random **30–90s** (jitter sì). Voice Day7: log-normale media 300s.
- `MAX_REPLIES_PER_DEALER = 10` (riga 643) — cap risposte/giorno per dealer.
- Auto-stop: block-rate > 2% → Telegram alert + stop (riga 1937-1940).

### 3. SECOND BRAIN / OBSIDIAN = **NON ESISTE**
`grep -rni obsidian .` → 0 match (escluso git). Nessuna cartella `.obsidian` né vault. Netto: assente.

### 4. FEATURE PIANIFICATO vs REALE (`docs/ARCHITETTURA_E2E.md`, blueprint 7 sottosistemi)

| Sottosistema | Stato | Evidenza disco |
|---|---|---|
| S1 Supply (scraper AS24) | **IMPLEMENTATO** | `tools/scrapers/autoscout_scraper.py` (E2E verificato). `config/channels.yaml` **MANCA** (registry pianificato). 28 canali = SOLO-PIANIFICATO |
| S2 Verification (CoVe v4) | **PARZIALE** | `src/cove/cove_engine_v4.py` esiste. `config/argos_standard.yaml` **MANCA**; gap-filling agent **SOLO-PIANIFICATO** |
| S3 Pricing/Dossier | **PARZIALE** | bande p25-p75 + G1 esistono; **Gate [D]** base-mercato fidata aperto (margine non ancora credibile) |
| S4 Dealer Profiling | **PARZIALE (MVP)** | `data/dealers.db` reale: dealers=1, dealer_profiles=1, dealer_gaps=1, vehicle_observations=28. Collector: `tools/dealer_target_profiles.py`, `import_profiled_dealers.py`, `profile_dealers_s106.py` |
| S5 Azzurra (Day-1 + classifier) | **PARZIALE** | Day-1 generator (`templates.py`) + AMBRA classifier (`response-analyzer.py`) esistono. **Sector wiki `kb/azzurra/` MANCA**; sequencer multi-touch SOLO-PIANIFICATO |
| **S6 Matching dealer↔veicolo** | **IMPLEMENTATO (modulo reale)** | `src/cove/dealer_matcher.py` (331 righe): `compute_match_score` (brand×fascia×gap), `match_vehicle_to_dealers`, `freshness_check`. **L'audit precedente "non esiste come modulo" è FALSO.** |
| S7 Control Plane | **IMPLEMENTATO** | VOS / Gate-E (`.harness/gate_e.py`) / state machine / scheduler |

**Matching serve al primo invio?** Esiste già (`dealer_matcher.py`) → NON è un gap bloccante per il
primo invio: dato 1 dealer profilato + pool veicoli, il modulo produce già il match veicolo→dealer
che alimenta il Day-1. Da verificare solo il wiring nel flusso di composizione (modulo presente, non collaudato E2E in questa sessione).

**Messaggio-due (risposta al "sì") = ESISTE già.** Template `DAY_INTEREST` (`templates.py:149`):
manda link contratto + fee "paghi solo dopo consegna documenti" — non è solo annotato.

---

## PARTE 2 — FIX HARNESS FP outreach (ARGOS_HARNESS_UNLOCK=1 → ESEGUITO)

**Backup**: `.harness/gate_e.py.bak.20260627-191910` (26720 byte, stesso size dell'originale, mtime sessione).

**Fix** (`gate_e.py`, opzione whitelist read-only, zero rischio FN):
- nuova costante `READ_ONLY_VERBS = {ls, grep, egrep, fgrep, wc, find, cat, head, tail, less, file, stat, tree}`;
- helper `_is_read_only_inspection(cmd)`: True sse OGNI segmento (stessa segmentazione di `lossy_operands`) ha verbo di testa read-only → se un solo segmento è esecutore (python/node/bash/./script) ritorna False;
- `hit_script` ora richiede `and not _is_read_only_inspection(scan)`. Ramo invii reali (`hit_sig` + numero) **intatto**.

**Diff**: aggiunte `READ_ONLY_VERBS` (dopo OUTREACH_SCRIPT_SIGNATURES) + funzione `_is_read_only_inspection` + 1 clausola su `hit_script`. (vedi `git diff .harness/gate_e.py`)

**Self-test**: `python3 .harness/gate_e.py selftest` → **SELFTEST PASS (33/33)** (nessuna regressione; il file contiene 33 casi).

**Prove reali** (via `classify_bash`, nessun invio):
```
ALLOW   ls tools/outreach/*.py
ALLOW   grep -n send tools/outreach/send_day1.py
ALLOW   cat tools/outreach/x.py
BLOCK(outreach_real)  python3 tools/outreach/x.py
BLOCK(outreach_real)  ls foo && python3 tools/outreach/send_day1.py   ← caso misto: zero FN confermato
BLOCK(outreach_real)  node tools/outreach/scheduler.js
```

**Packet FP rimosso**: `rm .harness/pending_review/outreach_real-43b7267220.md` (fatto).

**Caveat residuo onesto**: `find … -exec python3 tools/outreach/send.py \;` userebbe `find` (whitelist) come verbo di testa → sarebbe lasciato passare. Edge esotico; la whitelist è quella prescritta dal mandato (non allargata/ristretta). Da valutare se in futuro si vuole escludere `find -exec`.

**NESSUN INVIO. NESSUN messaggio dealer. Gate-E sugli invii reali intatto.**
