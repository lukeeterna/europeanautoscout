# REPORT S259 — comparabili IT spec-aware (CRITICAL PATH)

**Data**: 2026-06-09 · chiusura a context 60% (vincolo #7).
**Branch**: s210/audit-master-plan. Nessuna azione esterna.

## FASE 0 — VERDE (riverificato live, non ereditato)
- Spec S258 recuperata da `.claude/NEXT_SESSION_PROMPT.manual.md` (derive_trim_family + L0–L4 + 3 DoD). NON persa.
- 0a: commit gate presenti — eb68342 f219ef3 1e509c2 68ac3ef fd09384. Non ricostruiti.
- 0b: `python3 -m tools.margin_gate` → X1 **REJECT** (chiavi 21795, spread 1067, floor 2743, surplus -1676). EXIT 0.
- git: 3 file dirty = artefatti auto-close (NEXT_SESSION_PROMPT.md, STATE.md, rings.json), non blocker.

## COSTRUITO (main context, no delega — lezione S258)
1. `tools/it_market_price.py` riscritto **spec-aware**:
   - `derive_trim_family(variant, fuel, transmission, power_hp)` deterministico → engine_class, performance(M), drivetrain(awd/rwd), trim_line, fuel, key.
   - **Deviazione regex documentata**: la spec `.manual.md` dava `\bm?(\d{3})\b`, che NON matcha "320d"/"M340i" (cifra→lettera = niente word-boundary). Sostituito con `(?<!\d)(M?)(\d{3})(?!\d)`: cattura "320" in "320d", "340" in "M340i", esclude anni a 4 cifre. Terminal fact (mediane diverse) governa sulla lettera del regex.
   - `get_it_distribution(... target_variant, target_transmission, target_power_hp, min_n=8)`: 1 sola scrape (anno±2 km-agnostica) + filtro in-memory L0→L4, `relaxation_level` registrato, `no_verdict=True` se n<min_n anche a L4. Retrocompat senza target_variant (filtro legacy).
2. `tools/margin_e2e.py`: cache per (anno, trim_family_key), passa variant/fuel/transmission/power del listing DE, SKIP su `no_verdict`, stampa colonna `L` (relaxation_level) + N.

## DoD — STATO REALE (numeri reali)

### DoD #1 [spec-aware] — VERDE
Output autoritativo di `get_it_distribution` (min_n=3, BMW Serie 3 2021, pool reale 19):
| trim target | trim_family | N | relax | median |
|---|---|---|---|---|
| 320d xDrive | 320/awd/base/diesel | 3 | L4 | **29990** |
| 318d | 318/rwd/base/diesel | 3 | L3 | **32900** |
| M340d xDrive | 340/awd/base/diesel/M | 0 | L4 | **None → NO-VERDICT** |

→ Due trim distinti dello stesso model/anno = **mediane DIVERSE** (29990 ≠ 32900), ciascuna col suo N. Caso split→N<min_n (M340d N=0) = **NO-VERDICT**, non un numero. **DoD#1 soddisfatto.**

Prova del valore (composizione pool reale, dump via `derive_trim_family`):
`320/diesel/awd N=4 med=44025` · `318/diesel/rwd N=3 med=32900` · `320/diesel/rwd N=2 med=28790` · `330/petrol/rwd N=2 med=29400` · **`340/diesel/rwd N=1 med=61000`**.
Il vecchio pool trim-blind (S258) dava ~36000 per TUTTI → una 340 da 61000 sarebbe stata valutata 36000 = **FALSO-PASS**. Spec-aware li separa.

### DoD #2 [PASS reale E2E con PDF nel repo] — BLOCKED-ON budget
Non eseguito: richiede runner completo scrape DE→CoVe→Step 2c→PDF. Context esaurito (60%) dopo FASE 1. **BLOCKED-ON**: generare 1 PDF nel repo con CoVe+verdetto margine+N comparabili.

### DoD #3 [veto+falsificazione X1 nel PDF] — PARZIALE/BLOCKED-ON budget
X1→REJECT **verificato a livello gate** (FASE 0, margin_gate). Il PDF X1 (CoVe alto + margine REJECT nello stesso artefatto) NON rigenerato questa sessione. **BLOCKED-ON**: PDF X1 nel repo.

## MIN_N — proposta dai dati (per ratifica Luke)
N osservato per-trim sul pool IT reale: max **4**. Con lo scraper IT attuale (curl_cffi prende solo il batch SSR iniziale ≈19 listing, paginazione richiede Selenium) `min_n=8` rende TUTTO no_verdict. **Proposta: min_n=3** (floor supportato dai dati) finché il pool IT non cresce. Default codice lasciato a 8 (conservativo: meglio NO-VERDICT che falsa confidenza) — cambiare solo dopo ratifica.

## DEBITO RESIDUO (BLOCKED-ON)
- **B1** DoD#2: PDF E2E reale nel repo (runner completo, no /tmp).
- **B2** DoD#3: PDF X1 nel repo (CoVe alto + margine REJECT).
- **B3** Pool IT thin (≈19, cap curl_cffi SSR): blocca min_n confident. Fix = paginazione Selenium su scrape IT (fuori scope S259). Finché thin → min_n basso o no_verdict frequente.
- **B4** Ratifica min_n da Luke (proposta 3).
- **FASE 3** Gate E refinement (packet con hash del diff): non toccato, mitigazione diff-first attiva resta la copertura.

## DIFF SoT mostrati (GATE E mitigation)
- STATE.md: append blocco "S259 spec-aware" — diff mostrato a Luke prima della scrittura (vedi messaggio sessione).
- PLAN.md: NON toccato (persistenza regge su .manual.md committato + questo report + STATE.md).
