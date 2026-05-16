# S175.0 E2E Reactive Pipeline Report — TEST_FOUNDER HITL-driven

**Data**: 2026-05-16 ~10:05-10:50 IT
**Durata effettiva**: ~45min wall (chiusura forzata vincolo #7 context 67%)
**Operatore Luke**: phone TEST_FOUNDER 393314928901 + laptop CTO
**Verdict**: **ROSSO** (1 gap critico hallucination veicolo + 1 finding sistemico target_lexicon)

## Step results

| # | Step | Stato | Tempo | Evidence/Note |
|---|------|-------|-------|---------------|
| 0 | Pre-conditions + fix preventivi | VERDE | ~10min | 9/9 check passati, GAP-A dashboard risolto (PM2 `--interpreter /usr/local/opt/python@3.13/bin/python3` + pm2 save) |
| 1 | SQL handoff mystery_shopper | VERDE | <1min | 1 row UPDATE, fields `mystery_shopper|1|HANDOFF_LAYER3` |
| 2 | Day 1 AMBRA Layer 3 post-handoff | GIALLO | ~5min reply | Identity Luca ✓, ban Argos ✓, lexicon FAIL (S174 conferma), multi-msg 3-part borderline D-07 |
| 3 | VEHICLE_REQUEST extraction + reply | **ROSSO** | ~4min | TG alert ✓, ma AMBRA **inventa veicolo X3 2021 89.855km €27.389** (D-21 violation) |
| 4 | Manual on_demand_runner | NON ESEGUITO | — | Chiuso pre-step per context budget |
| 5 | Visual UAT sanitizer | NON ESEGUITO | — | |
| 6 | PDF transfer + WA delivery | NON ESEGUITO | — | |
| 7 | Cost question + target_lexicon | NON ESEGUITO | — | (già confermato GIALLO step 2) |
| 8 | Contract flow web form | NON ESEGUITO | — | |
| 9 | Mark-paid web form | NON ESEGUITO | — | |

## Gap identificati (priorità decrescente)

### GAP-3 — AMBRA inventa veicolo specifico su VEHICLE_REQUEST (CRITICO BLOCKER)
- **Sintomo verbatim**: inbound dealer "Mi serve una BMW X1 del 2020, budget sui 18000 . La trova?" → AMBRA reply (10:44:42): "posso proporti una BMW X3 del 2021 con 89.855 km a 27389, è un bel pezzo, la macchina è pulita, pensi possa interessarti? Luca"
- **Root cause**: prompt LLM AMBRA per inbound classificato VEHICLE_REQUEST genera reply pitch operativo con veicolo dettagliato fittizio invece di confermare ricerca + delegare on_demand_runner (D-15 HITL manuale). Pattern LLM hallucination su numeri specifici (km, prezzo, anno) plausibili ma inventati.
- **Fix singolo motivato** (vincolo #3): patch prompt classifier VEHICLE_REQUEST in `response-analyzer.py` per forzare risposta template: "conferma marca/modello/budget estratti + 'sto cercando ora, le scrivo entro 1-2 giorni'". NO veicoli specifici embedded. Test post-fix: ground-truth utterance "Mi serve X X X" → reply solo conferma + ETA, no km/prezzo/anno inventati.
- **Costo fix stimato**: 1-2h coding + test su TEST_FOUNDER inbound replay
- **Blocker mystery shopper reale**: **SÌ HARD**. Dealer Lucky Cars riceverebbe veicolo inesistente → brand kill istantaneo, recovery impossibile.

### GAP-2 — Target_lexicon FAIL sistemico (CONFERMA S174)
- **Sintomo verbatim**: reply STEP 2 contiene "scheda", "dossier", "5-7 giorni lavorativi", "costi nascosti", "zero anticipo", "trovo la macchina giusta" — lessico marketing/generico vs lessico target D-28 micro-dealer commissione informale ("commissione", "su ordine", "ci guadagna", "macchina pulita", "km certificati")
- **Root cause**: S174 ha trovato target_lexicon FAIL deferred S175 calibration. S175 sospeso. Ora confermato in interazione reale, non solo test isolato.
- **Fix singolo**: implementare S175 calibration target_lexicon (deferred). Richiede update prompt AMBRA con lexicon-rules: ban list ("scheda"/"dossier"/"servizio"/"piattaforma"/"costi nascosti"/"5-7 giorni") + allow list ("commissione"/"su ordine"/"ci guadagna"/"macchina pulita"/"km certificati"/"in regola").
- **Costo fix**: 2-3h prompt engineering + A/B su 5-10 inbound reali.
- **Blocker mystery shopper**: NO HARD ma riduce credibilità Day 1 reactive — dealer percepisce "venditore" non "broker informale".

### Pattern strutturale (vincolo #11)
GAP-3 hallucination + GAP-2 target_lexicon hanno root cause comune: **prompt LLM AMBRA pre-S173/S174 non distingue ruolo `info-broker` da ruolo `seller`**. AMBRA produce output da venditore (pitch + invent veicoli per "chiudere") invece di broker (raccoglie richiesta + delega scouting reale). Fix singolo strutturale: rifare prompt AMBRA con role-binding esplicito "info-broker / NOT seller" + ban list operazioni (no invent vehicles, no quote prices, no commit dates) + delegate-flow esplicito ("conferma estratti → segnala Luke → attendi PDF").

## Verifiche non eseguibili sessione

- AMBRA reply STEP 7 cost question (probe diretto target_lexicon S174)
- on_demand_runner BMW X1 18000 → conferma scraper non broken
- PDF UAT sanitizer S163 visual (24h+ gated)
- Contract flow web form (worker proxy)
- Mark-paid dashboard:8080

## Verdict S175.0 = ROSSO

Pipeline reactive **NON pronta** per Path A mystery shopper LUCKY CARS:
- 1 blocker hard (GAP-3 hallucination veicolo)
- 1 finding sistemico (GAP-2 lexicon, già noto S174)

Handoff condizionale → `prompts/s175_1_fix_ambra_role_binding.md` (fix unico strutturale entrambi gap).

## Findings positivi sessione

1. Pipeline reactive **funziona end-to-end** WA-side: inbound captured → buffer 15s → analyzer triggered → LLM cascade → pending_replies → bridge_outbound → WA send → DELIVERED + LETTO. Architettura solid.
2. Tempo reactive ~4-5min wall coerente con human pacing simulato (multi-msg delays + simulateTyping).
3. Telegram HITL alert dispatched corretto su entrambi inbound (10:25:54 e 10:40:43).
4. `extract_vehicle_request()` LLM-based funziona (marca/modello/budget/anno tutti estratti da inbound conversazionale italiano informal).
5. Dashboard:8080 ora operativa (era blocker hard pre-S175.0, ora fix permanente PM2 dump).
