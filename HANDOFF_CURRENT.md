# HANDOFF — s210/audit-master-plan — 2026-07-03 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE (KB, 1 file) + READ-ONLY (diagnosi STATE)
- Mandato: (1) KB-update matrice-EU su frode_km_verifica.md da payload gradato dal giudice; (2) diagnosi read-only discordanza STATE.md anelli 1 e 6-7.
- Esito: (1) VERDE — validate_kb.py EXIT=0, 9 fatti conformi, commit 3d6491c. (2) VERDETTO (ii): re-run 6-7 necessario; UNVERIFIED è by-design, NON bug da riconciliare.

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 3d6491c 2026-07-03 · working-tree dirty: STATE.md, state/rings.json, .claude/NEXT_SESSION_PROMPT.md (riscritti dal SessionStart hook al boot — NON toccati in questa sessione)
- commit di questa sessione: 3d6491c "kb: matrice-EU accesso-per-paese GRADED-BY-GIUDICE-MATRICE-EU (payload giudice 2026-07-03)"

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md, verbatim — non re-narrare)
| 1 | invio Day1 WA | UNVERIFIED | full | — | — |
| 2 | classifier intent (AMBRA) | VERIFIED | smoke | `python3 tools/test_ambra_5scenarios.py` | auto-20260703T190305Z |
| 9A | approve -> send | VERIFIED | smoke | `python3 tools/tests/test_approve_reply_runtime.py` | auto-20260703T190305Z |
| 9B | reject -> abort | UNVERIFIED | full | — | — |
| 5 | generazione dossier PDF | VERIFIED | smoke | `python3 tools/tests/test_dossier_hitl_smoke.py` | auto-20260703T190305Z |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED | full | — | — |
| 8 | contract -> sign_url | BLOCKED | full | freeze: sign_url firmato dal dealer reale (HITL fisico) | — |

### GATE A DEALER REALE
[A] E2E verde su TEST_FOUNDER 393314928901 = FALSE (anelli 1/6-7/9B UNVERIFIED)
[E] Gate E attivo (S247/S249 selftest 33/33) = TRUE
[D] Luke "pienamente soddisfatto" = FALSE (non dichiarato)

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Re-run E2E anelli 6-7 su TEST_FOUNDER (403 PENDING -> approve -> 200 sent -> PDF ricevuto da Luke), attraversando Gate E attivo. Riguadagna VERIFIED in-sessione. NON riconciliare il generatore.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Anelli 1, 6-7, 9B = tier full, check_cmd:null -> VERIFIED solo con re-run in-sessione + Luke fisico su TEST_FOUNDER.
- Anello 8 = sign_url firmato dal dealer reale (freeze Gate D).

### BACKLOG (differito, NON prerequisito del primo invio)
- BELGIO Car-Pass costo ~7,3€ (dato 2018) = RI-CORROBORARE prezzo corrente prima di copy pubblico (flag già nel FATTO KB).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- KB: GERMANIA e Implicazione ARGOS del payload TENUTE come note ">" (non FATTO): Germania non coperta come fatto numerato; Implicazione ha FONTE="sintesi delle righe sopra" [T1-derivato] non citabile -> non passerebbero il gate RUBRICA. Zero fatti/numeri/fonti aggiunti oltre il payload.
- DIAGNOSI STATE: STATE.md è generato da state/refresh.py da state/rings.json. Regola: check_cmd==null -> UNVERIFIED forzato; PASS -> VERIFIED solo se last_run_session==sessione corrente, else STALE. Anelli 1 e 6-7 hanno check_cmd:null -> UNVERIFIED by-design.
- Discordanza handoff-storici (6-7 "verdi con test [A]") vs STATE UNVERIFIED = APPARENTE: il test [A] avvenne in sessione passata (memoria s_a_20260701), è tier full fisico non-ri-eseguibile, non persistito in campi che il generatore legge (rings.json 6-7: last_run_ts/session=null). VERDETTO (ii): re-run necessario; riconciliare il generatore VIOLEREBBE l'invariante anti-stale.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (fonte autoritativa segmento/geografia/anni/stock) · kb/dominio/frode_km_verifica.md (matrice-EU) · ~/.claude/projects/.../memory/MEMORY.md (s_a_20260701_rings67_live_verified)
