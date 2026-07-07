# HANDOFF — S298 (UNITÀ B done · C deferita) — 2026-07-07 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: STATE-SUBSTRATE (aggiunto gate base-mercato al substrato generato) + coda S297
- Mandato: (B) riconciliare riga stale gate base-mercato in STATE.md VIA GENERATORE · (C) provenienza numeri PDF dossier (consumare fonte, non ricalcolare)
- Esito: **B VERDE** (anello `BM` VERIFIED via generatore) · **C NON ESEGUITA** (deferita per context budget 60%, come da CHECKPOINT del mandato — B ha priorità)

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD atteso = commit di chiusura S298 (successivo a `cac70b4`)
- dirty MIEI committati: `tools/tests/test_base_mercato_gate.py` (nuovo) · `state/rings.json` (+ring BM) · `STATE.md` (tabella rigenerata) · `HANDOFF_CURRENT.md`
- dirty NON-miei: `.claude/NEXT_SESSION_PROMPT.md` (timestamp auto SessionStart)
- backup 1d NON committato (untracked): `state/rings.json.bak-S298-20260707T205604Z`

### UNITÀ B — FATTA (verde)
- **Discordanza col mandato** (blind-guess falsificato su disco): NON esisteva alcun gate `[D]/[3]` base-mercato in `state/rings.json` — c'erano solo gli anelli E2E. La riga stale vive come PROSA hand-written nel blockquote di testa di STATE.md (righe 20-32), FUORI dal blocco GENERATED.
- Fatti S295-C VERIFICATI su git: `ebe422e` (fixture geo-pura 323, n_priced=323 parse-fail=0), `d586f03` (validate_band.py gate deterministico). Fixture `tests/fixtures/it_dist_bmw_serie3_2021_s273cont4.json` (740KB) e `tools/validate_band.py` presenti.
- Azione: nuovo anello `BM` in rings.json (solo config-field → Gate B permette) con check_cmd DETERMINISTICO `python3 tools/tests/test_base_mercato_gate.py` (fixture esiste + n_priced==323 + `gate_it_band(330i)` emette verdict senza eccezioni). Backup 1d pre-edit. `refresh.py S298` → tabella STATE.md §1 rigenerata: `BM = VERIFIED`.
- Falsificabilità PROVATA: fixture presente → exit 0 (PASS); FIXTURE→path inesistente → exit 1 (FAIL). NON sempre-verde.
- Dati reali gate sul 330i: verdict=VERDICT, fallback_declared=True, `n_by_level {L0:2, L1:3, L2:4, L3:20}`, banda 25.349–32.775.

### RESIDUO B (discordanza da chiudere — NON hand-edito, VIETATO da mandato)
Il blockquote stale STATE.md righe 20-32 ("S273-cont base-mercato NON affidabile (cap-truncated)") è PROSA non-generata: `refresh.py` tocca solo il blocco tra i marker GENERATED (la tabella), non il blockquote. Ora la tabella dice `BM=VERIFIED` mentre il blockquote dice il contrario → STATE.md internamente incoerente. Il generatore NON può rimuovere quel testo. Serve decisione Luke: (opzione) rimuovere/aggiornare il blockquote a mano sotto `ARGOS_HARNESS_UNLOCK=1` (state_guard Gate A LO PERMETTE — protegge solo il blocco marker, "le sezioni narrative fuori dal blocco restano editabili"), oppure spostare quella prosa dentro una regione generata.

### UNITÀ C — NON ESEGUITA (deferita, causa già localizzata)
Causa PRE-individuata (letta, non ancora fixata): il PDF demo (a) è generato da `tools/scripts/build_s296_dossier.py::payload_a_real_fallback` che consuma `get_it_distribution` (tools/it_market_price.py) e passa `dist` a `generate_dossier_from_data`. Il copy stale "325 annunci / cap 20 pagine / non esaustivo" viene dal template `tools/scripts/pdf_generator_enterprise.py` (S273 vecchia fixture n=325), NON dalla fonte cont4 (323). Numeri reali fonte: L0:2/L1:3/L2:4/L3:20, n_priced=323, 21 pagine, terminated_by_empty. Fix minimo C: template consuma i numeri da `dist`/fixture (non ricalcolo parallelo) + rimuove copy stale "325/cap/non esaustivo" + etichetta doppia "Documento richiesto: Documento ottenuto —" + rigenera SOLO il PDF (a). Rule 1d sui file toccati.

### BLOCKED-ON (invariati, fatti esterni)
- E2E TEST_FOUNDER (anelli 1/6-7/9B) — Luke fisico su WA/HITL.
- Anello 8 (sign_url firmato dal dealer reale) — freeze fisico.
- Parità gate/runtime `/send` `approved_ts` — gated su autonomia-invio.

### PROSSIMO PASSO (singolo, falsificabile)
UNITÀ C in sessione fresca: in `pdf_generator_enterprise.py` far consumare al template i campi da `dist` (get_it_distribution) invece di stringhe hardcoded "325 annunci/cap 20 pagine"; rigenerare SOLO `tests/dossiers_s296/ARGOS_DEMO_S296_a_330i_REAL_fallback.pdf`; done = estratto testo del PDF con L0/L1/L2/L3 e count = fonte (323, non 325) e copy stale assente.

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/handoff (SUPERSEDED)
