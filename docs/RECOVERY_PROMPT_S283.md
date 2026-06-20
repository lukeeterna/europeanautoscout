# RECOVERY_PROMPT_S283 — ripartenza a freddo (prossima sessione = [A1] cont., DEDICATA)

Lancia con `ARGOS_HARNESS_UNLOCK=1`. Sessione DEDICATA a [A1] (anello critico E2E 6-7), budget PIENO.
Routing freddo: STATE.md → docs/ROADMAP.md → docs/briefs/BRIEF_A_e2e_67_testfounder.md. In conflitto vince STATE/ROADMAP.

## Stato chiuso in S282 (questa)
- **[A0] WA daemon = `connected`** VERIFICATO da CC (curl letterale, due volte). Era bloccato `initializing`
  (uptime 16.5h, sessione viva) → restart pulito via wa-daemon-ops `initializing→connected`, NO QR. Precond [A1] soddisfatta.
- **[A1] NON verde — handoff strutturato (NON PARTIAL).** Scrape AS24 reale ESEGUITO: BMW Serie 3,
  243 listing, 32 PROCEED CoVe, 5 top qualificati A4. Pipeline poi ritorna `None`. Due gap di codice
  CONFERMATI col codice, che BRIEF_A e RECOVERY_S282 assumevano GIÀ ESISTENTI ma NON esistono:

### G1 — Thin-pool SOPPRIME il dossier (non lo rende degradato). BLOCCANTE per step 2.
- `tools/on_demand_runner.py:502-507` → `if it.get('no_verdict'): continue` (scarta il veicolo).
- `tools/on_demand_runner.py:526-528` → `if not margin_passed: return None` (zero PDF).
- `min_n=8` = `MIN_N_DEFAULT` in `tools/it_market_price.py:38` (RATIFICATO Luke S265, NON abbassare).
- Realtà Serie 3 OGGI: comparabili IT spec-aware (trim esatto) danno n=3-6 sui 5 top → tutti NO-VERDICT
  → return None. Il RAMO THIN-POOL del recovery prompt ("dossier rende ESPLICITO 'comparabili
  insufficienti (N=x)', NON emette banda come fidata; basta UN veicolo che renderizza") **non è nel codice**.
- **FIX richiesto (build, non bypass):** quando `not margin_passed` per soli NO-VERDICT (thin pool, NON
  per REJECT sotto-pavimento), generare un dossier DEGRADATO del miglior candidato che (a) dichiara
  "comparabili insufficienti (N=x)", (b) NON stampa banda p25-p75/margine come fidati, (c) resta valido
  come test di MECCANICA+RENDER. Distinguere thin-pool (n<min_n) da REJECT-margine (affare sotto pavimento):
  il secondo DEVE restare soppresso. ⚠️ NON abbassare min_n, NON usare PDF stale, NON spingere numeri non
  fidati nel layer banda (pattern-errore S268/S271 — l'artefatto [A1] diventa il template del 1° dealer reale).

### G2 — RETTIFICATO da verifica giudice S282-bis. Il generatore parametrico ESISTE, ma in voce sbagliata.
- `tools/outreach/send_day1_stile_car.py` = hardcoded per-dealer (Stile Car, DEALER_PHONE 393334254654) + INVIA (POST :9191/send, riga ~191). NON parametrico, NON usabile offline.
- `wa-intelligence/response-analyzer.py` = AMBRA reale ma reply-oriented + LLM-cascade-gated (Groq/Gemini live). Banned-words check = `_validate_llm_response` ~:100-109 (NON `_check_banned_words`).
- **ESISTE GIÀ** `wa-intelligence/templates.py`: `select_day1_variant(dealer_brands)` ~:242-263 + 3 template DAY1 (PREMIUM/MIXED/GENERALIST) ~:14-52, `str.format` puro, ZERO LLM, OFFLINE. **MA firma "sono Luca Ferretti" in 1ª persona** → viola S277/Azzurra → **fallirebbe il punto 1 dei 7**. Quindi G2 NON è "build da zero": è (a) correggere la firma di templates.py → Azzurra + disclosure/provenienza/opt-out, O (b) cablare il path AMBRA (response-analyzer) per cold-gen offline. Scelta da fare in sessione [A1].
- **G1 nota verificata**: la distinzione thin-pool (`no_verdict`→continue, :502-507) vs REJECT-margine (`surplus<=0`→REJECT in margin_gate.py:72) ESISTE già nel codice → il fix G1 si aggancia pulito al flag `no_verdict` senza nuova logica di classificazione.
- **S277 Azzurra CONFERMATO in repo:** `response-analyzer.py:67 ARGOS_PERSONA='Luca Ferretti'`, `:68 ARGOS_ASSISTANT='Azzurra'`.
- **G2-bis:** lo scrape non persiste i top listing su file (return None prima di ogni dump) → numeri del
  candidato non isolabili dal log. Il fix G1 (dossier degradato) o un dump-top pre-margin-gate risolve anche questo.

### Artefatto di riferimento (solo per capire il render atteso, NON è output di oggi):
`dossiers/ARGOS_BMW_Serie 3_2021_TEST_FOUNDER_20260609_165235.pdf` (09/06, N=19, PASS legittimo).
Estraibile con pypdf — mostra la struttura del dossier "pieno". Il dossier degradato (G1-fix) avrà la stessa
macchina ma con la fascia comparabili marcata insufficiente.

## SEQUENZA PROSSIMA SESSIONE (build-prima-di-run)
1. **G1**: implementa il dossier degradato thin-pool (file/righe sopra). Verifica: scrape Serie 3 → PDF che
   rende "comparabili insufficienti (N=x)" senza banda fidata. Delega l'esecuzione rumorosa, verdetto-render a CC.
2. **G2**: entry-point cold Day-1 AMBRA parametrico (no-invio, passa banned-words). Genera il messaggio reale.
3. **Render-verify 7 punti** (BRIEF_A 17-28) LEGGENDO PDF (pypdf) + messaggio reale. Punti 1-6 da CC.
4. **CHECKPOINT GIUDICE** (vincolo #4): TextEdit con INLINE (a) 7 punti VERBATIM, (b) Day-1 reale, (c) testo
   dossier renderizzato. GO/NO-GO esterno Claude AI. Procedi all'invio SOLO con GO.
5. **Invio TEST_FOUNDER 393314928901 via Gate-E** (classe outreach_real → BLOCCA → packet → Luke incolla
   verdetto + `! python3 .harness/gate_e.py approve <slug>`). Gate-E che NON scatta = bug del breaker.
6. Done-condition [A1] = 7 punti VERDE sull'artefatto reale. Verde o handoff strutturato (mai PARTIAL).

## Precondizioni invarianti
- PRIMA AZIONE: curl letterale `ssh gianlucadistasi@192.168.1.2 'curl -s localhost:9191/status'` → deve
  mostrare `"wa_status": "connected"`. Se no → [A0] restart (wa-daemon-ops). Interpretazione stato = autorità CC.
- Orario lavorativo + Luke fisico sulla SIM 393314928901. SOLO TEST_FOUNDER, nessun altro numero.
- Single-writer: solo questa sessione scrive su branch s210/audit-master-plan.
- NB ops iMac ssh non-interattivo: pm2 in `~/.npm-global/bin`, node v20 in `~/.nvm/versions/node/v20.11.0/bin`
  (il daemon usa better-sqlite3 ABI node v20 — NON node v22 di /usr/local/bin per il processo).
