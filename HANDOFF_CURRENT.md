# HANDOFF — S301 — 2026-07-08 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: (B) `validate_day1.py` + suite sintetica = artefatto di produzione del Day-1, self-contained, zero dati live; poi (A.2-prep) solo piano-scrape pool ICP se budget regge; C non toccata.
- Esito: **UNITÀ B VERDE** — gate anti-invenzione `validate_day1.py` + suite `test_validate_day1.py` 5/5 PASS (exit-code verbatim verificati), commit `5537743`. **A.2-PREP NON FATTO** (checkpoint context >65% → chiusura per mandato). C non iniziata.

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD `5537743` 2026-07-08 · working-tree dirty (solo file auto-refresh SessionStart, NON miei): `.claude/NEXT_SESSION_PROMPT.md` · `STATE.md` · `state/rings.json`
- commit di questa sessione: `5537743` "UNITÀ B: validate_day1.py gate anti-invenzione Day-1 + suite 5/5 PASS" (3 file, +415)
- NON pushato (regola S278: push bloccato finché scrub history secret non fatto).

### UNITÀ B — validate_day1.py (verde)
- `validate_day1.py` (root, 276 righe) — gate di FORMA deterministico, pattern `validate_kb.py` (riusa `parse_fact`/`FACT_RE`/`TIER_RE`). Funzione pura `validate_day1(message, profile, kb_lines)->list[violazioni]` + CLI `--message --profile --kb-dir`.
- Fonti di verità = SOLO `dealer_profile.json` (da `tools/dealer_profile.py`) + `kb/dominio/*.md` (FATTI [T1/T2/T3]). Checks: (i) numeri+marche-stock tracciabili → claim orfano = exit 1 nominato; (ii) lessico vietato `garanzia|garantit*|certificato costruttore|assicuriamo` = 0 match; (iii) opt-out + identità "Azzurra" presenti; (iv) numero che traccia SOLO a [T3] mai nella stessa frase di parola di certezza.
- `tools/tests/test_validate_day1.py` (132 righe, fixture INLINE, zero dati live): (a) pulito→exit0, (b) numero inventato 45→exit1, (c) T3-come-certo→exit1, (d) opt-out assente→exit1, (e) **CASO-COLPEVOLE** stile batch_generator (BMW+~20 da archetipo/fallback su profilo Audi/Mercedes)→exit1. Prova grezza: `SUITE PASS (5/5)`.
- `batch_generator.py` marcato `DEPRECATED-S301` (commento in testa + pointer al path grounded). Non è file SoT-protetto → Gate E non ha bloccato; `ast.parse` OK.

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md, verbatim — non re-narrare)
| # | Anello | Stato |
|---|--------|-------|
| 1 | invio Day1 WA | UNVERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED |
| 9A | approve -> send | VERIFIED |
| 9B | reject -> abort | UNVERIFIED |
| 5 | generazione dossier PDF | VERIFIED |
| 6-7 | approve HITL dossier -> invio PDF | UNVERIFIED |
| 8 | contract -> sign_url | BLOCKED (freeze esterno) |
| BM | base-mercato IT fidata | VERIFIED |

### GATE A DEALER REALE
[A] liceità canale primo contatto = CONFERMATO LUKE 2026-06-16 · [E] trasparenza AMBRA (Azzurra) = CHIUSO (commit 118343b) · [D] base-mercato fidata = VERIFIED. Residuo bloccante = E2E TEST_FOUNDER verde (1/6-7/9B) + Luke "pienamente soddisfatto".

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
A.2-PREP (solo carta, zero scrape): scrivere in `docs/briefs/` il piano-scrape del pool dealer ICP (fonte pagine concessionari AS24, query/percorso, stima richieste vs `daily_request_cap`, criteri stop, output atteso N profili → filtro ICP <20/TIER). NESSUNA richiesta parte.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Pool dealer ICP reale = scrape fresco rate-limited (sessione dedicata con budget) — su disco 1 solo dealer (RossettoMotors, 28 listing → NON ICP micro-<20).
- Input Luke: URL AS24 dealer per A.2 live + testo esatto scheletro Day-1 ratificato (claim fissi: leva "circa 3x, fonte commerciale"; opt-out; slot {dealer_name}/{stock_hint}/{vehicle_hook}).
- E2E TEST_FOUNDER (anelli 1/6-7/9B) — Luke fisico WA/HITL. Anello 8 sign_url — freeze fisico.

### BACKLOG (differito, NON prerequisito del primo invio)
- Parità gate/runtime `/send` `approved_ts` (gated su autonomia-invio, STATE.md §3).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Il gate `validate_day1.py` è la RETE, non il generatore: cattura l'invenzione a valle di qualunque compositore (LLM incluso). Il caso-colpevole (e) dimostra che avrebbe bloccato il bug reale di `batch_generator.py`.
- Limite onesto del gate (deterministico, per FORMA): traccia NUMERI (canonicalizzati IT: '.'=migliaia, ','=decimale) e MARCHE-in-contesto-stock. NON valida claim testuali liberi senza numero/marca (es. un aggettivo qualitativo inventato passa) — è un gate di forma, non un fact-checker semantico. Con KB ricca il rischio è falso-match numerico (numero inventato coincide con una cifra KB): mitigato perché le marche-stock devono tracciare al PROFILO, non alla KB.
- A.2-prep NON eseguito: mandato ha CHECKPOINT >65% → chiudi; context ha superato la soglia durante UNITÀ B. È SOLO carta, riprende a costo nullo la prossima sessione.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (ICP S292: micro <20, TIER A/B, €25-90k, 2018-2023, no BEV) · STATE.md §3 (gate dealer reale) · .claude/rules/communication.md (CRED-SEQUENCE-001 / NO-OFFER-DAY1-001) · memory/s300_day1_capability_recon.md (pattern validate_day1 + colpevole) · validate_kb.py + kb/dominio/frode_km_verifica.md (fatto >3x [T3])
