# S201 — Resume anelli critical path ARGOS + pivot agent autonomo no-HITL

> **Apertura sessione**: leggi in ordine
> 1. `memory/s200_closure_handoff_s201_agent_autonomo_pivot.md` (closure S200 + autocritica 4 punti + stato anelli + open questions)
> 2. `memory/feedback_pipeline_test_founder_specs_corrected.md` (Step 2 Luke sceglie modello + Step 4 prezzo visibile/posizione nascosta + scope agent autonomo no-HITL contatto)
> 3. `memory/feedback_e2e_full_test_founder_before_day1.md` (STEP 0 ASSOLUTO TEST_FOUNDER + recidiva infinite volte)
> 4. `memory/s198_step7_rosso_3_5_classifier_gaps.md` (BLOCKER anello #2 classifier P1+P2+P3)
> 5. `/Users/macbook/Downloads/s199_claude_ai_output_v2_2026-05-27.md` (design AMBRA-NEXT validato S200, PASS gate ma 2 errori fattuali + 3 criticità non flaggate)

---

## Gate-state ARGOS in ingresso S201

| Anello | Stato | Owner |
|---|---|---|
| #1 scrape | VERIFIED 2026-05-22 | — |
| #2 classifier intent | EXISTS_BUGGY | fix S199 P1+P2+P3 pending |
| #6 inbox `messages` table | **MISSING** | creazione + integrazione daemon WA |
| #9 HITL gate | **EXISTS_BUGGY CRITICAL** | `sent=1 approvata=0` |
| Step 4 report parziale | NOT_DESIGNED | scope nuovo S201 |
| Safety suite | 0/8 pass | — |
| E2E TEST_FOUNDER osservato Luke | False | obiettivo finale S201/S202 |

## STEP 0 ASSOLUTO (non sindacabile)

**TEST_FOUNDER 393314928901 (SIM FLUXION fisica Luke) + Luke dichiara "pienamente soddisfatto"**.

OGNI mappatura pipeline, OGNI proposta tecnica, OGNI dichiarazione di readiness deve avere TEST_FOUNDER come Step 0 esplicito. Se manca → ricorda recidiva (4 memory ignorate fino S200).

## Pivot scope DECIDED Luke 2026-05-27

**Agent autonomo end-to-end su contatto/vendita** — eliminare approvazione Telegram su:
- Invio Day 1
- Day 3-N follow-up
- Risposte a obiezioni standard
- Generazione + invio report parziale

**Pending decisione Luke S201** (open questions):
1. Mark-paid → HITL o autonomo? (raccomandazione: HITL — pagamento reale)
2. Creazione contratto/sign_url → HITL o autonomo? (raccomandazione: HITL — irreversibile cliente)
3. Modifica prezzo fuori range → HITL o autonomo? (raccomandazione: HITL con range Luke-defined)
4. Range prezzo pre-approvati → quali soglie?

**Allineamento con Claude AI v2**: il design AMBRA-NEXT LangGraph + `interrupt()` calza, MA Day 1 va spostato da HITL ad auto (Claude AI v2 lo metteva HITL).

## Specs Step 2 + Step 4 corrette

### Step 2 — Luke sceglie modello
Test scraper su modello scelto da Luke al momento (es. "Audi Q5 2021" / "Mercedes Classe E 2020"), NON BMW Serie 3 demo hardcoded.

### Step 4 — Report parziale
Mostra:
- ✅ Prezzo target (gancio per dealer)
- ✅ Marca/modello/anno/km
- ✅ Margine stimato dealer
Nasconde:
- ❌ Posizione geografica
- ❌ Nome venditore + contatti
- ❌ URL inserzione originale
- ❌ Immagini reverse-searchable (Google Reverse Image / TinEye / web)

Tecnica anti-reverse-image-search:
- Strip EXIF/metadata completo
- Re-encoding (rompe hash binario)
- Modifica pixel leggera (resize ±10% + crop bordi + color-shift) → rompe pHash/dHash
- Watermark ARGOS visibile
- No referer/link CDN sorgente
- **Gate verifica empirica**: caricare PDF output su Google Reverse Image → 0 match

---

## Critical path S201 (raccomandazione singola — vincolo #3)

**Ordine fisico obbligato**:

### Anello #9 HITL safety bug (CRITICAL — primo)
Bug `sent=1 approvata=0`. Anche se scope pivot è agent autonomo no-HITL Day 1, la colonna `approvata` non deve restare BUGGY: in scope nuovo agent autonomo, `approvata=1` deve essere settato automaticamente dall'agent SE policy auto-approve attiva, oppure restare HITL per mark-paid/contratto. La logica va riprogettata, non rimossa.

**Sub-steps**:
1. Audit codice attuale `sent` + `approvata` columns (dove popolate, race conditions)
2. Decisione architetturale: `approvata` resta colonna semantica ma policy varia per `action_type`
3. Patch + test atomic claim
4. Backfill TEST_FOUNDER + dealer storici
5. delegate `code-reviewer` + `validator`

### Anello #6 inbox `messages` table (MISSING — secondo)
Tabella non esiste né locale né iMac. Daemon WA riceve messaggi inbound MA non li persiste in `messages`. Pipeline reactive S175 era stata progettata ma mai integrata.

**Sub-steps**:
1. Schema `messages` (dealer_id, phone, body, ts, direction, raw_payload, processed_at)
2. Migration locale + iMac
3. Daemon WA patch: on `messages.upsert` → INSERT into `messages`
4. Smoke: invio msg da TEST_FOUNDER → verifica row creata
5. delegate `database-admin` + `wa-daemon-ops` + `validator`

### Anello #2 classifier S199 P1+P2+P3 (terzo)
Patch chirurgica `response-analyzer.py`:
- P1 `CONTRACT_REQUEST_PATTERNS:233-238` + regex bonifico/pagamento/pago/procediamo
- P2 `PATTERNS['NEGATIVE']['exact']:1164-1171` + clitici "non mi scrivere/contattare/cercare più"
- P3 handler NEGATIVE `:2114-2123` popola opt_out=1 + opt_out_at + opt_out_source='auto_negative'
- Re-run `tools/test_ambra_5scenarios.py` → gate 5/5

### Step 4 design report parziale (quarto)
Componente NUOVO non esiste. Spec:
1. Generator PDF "preview" da CoVe data + sanitizer anti-reverse-image
2. Sanitizer D-32 esteso: strip EXIF + re-encoding + pixel shift + watermark
3. Test verifica empirica Google Reverse Image (0 match richiesto)

### Step 5 E2E TEST_FOUNDER osservato Luke (quinto — gate STEP 0)
Una volta #9 + #6 + #2 + Step 4 verdi:
1. Luke sceglie modello (Step 2 corretto)
2. Sistema invia Day 1 al 393314928901 (auto se scope pivot confermato, HITL solo se Luke vuole gradualità)
3. Luke risponde dalla SIM
4. Sistema persiste in `messages`, classifica, triggera CoVe search
5. Sistema genera report parziale (anti-reverse-image), invia
6. Luke firma contratto (HITL pending decisione open questions)
7. Mark-paid simulato dashboard (HITL pending decisione)
8. Sistema invia dossier completo
9. **Luke dichiara "pienamente soddisfatto"** → solo allora gate STEP 0 superato

---

## Delegation-first plan (REGOLA #0)

Debito S200: zero Task delegate. Recuperare in S201:
- `architect` → audit anello #9 + decisione architetturale `approvata` semantica nuovo regime
- `database-admin` → schema `messages` + migration
- `wa-daemon-ops` → patch daemon iMac per persist inbound
- `backend-architect` → design Step 4 report parziale + sanitizer anti-reverse-image
- `implementer` SOLO post-approvazione Luke + architect
- `code-reviewer` su ogni patch
- `validator` E2E pre-commit
- `tool-evaluator` per scelta lib anti-reverse-image (faiss imagehash? PIL re-encoding? sentence-transformers vision?)

## Vincoli S201

- Italiano verso Luke
- Mai PARTIAL/ARANCIONE
- Raccomandazione singola motivata con DATI (vincolo #3)
- Autocritica 4 punti su ogni proposta (vincolo #4)
- Zero costi (vincolo #5)
- Pre-flight env check su lib nuove (vincolo #8) — Big Sur Python 3.13 compat
- Mai "hai ragione" diplomatico (vincolo #9)
- Pattern recognition strutturale (vincolo #11) — STEP 0 TEST_FOUNDER come prima riga ogni mappatura
- TEST_FOUNDER 393314928901 SIM FLUXION whitelist
- Domenica 2026-05-31 OFF (no scadenze Luke-fisico)
- Context >50% → handoff S202 con stato preciso

## Commit attesi fine S201

```
git add prompts/s199_*.md prompts/s200_*.md prompts/s201_*.md tools/test_ambra_5scenarios.py
git mv /Users/macbook/Downloads/s199_claude_ai_output_v2_2026-05-27.md prompts/s199_claude_ai_output_v2_20260527.md
git commit -m "docs(S199-S200-S201 closure): AMBRA-NEXT eval + agent autonomo pivot + anelli critical path"
```

Più (a seconda di cosa si chiude in S201):
- patch anello #9 → `feat(S201-HITL): fix sent_approvata semantica + atomic claim`
- migration anello #6 → `feat(S201-INBOX): messages table + daemon persist`
- patch anello #2 → `feat(S201-CLASSIFIER): P1+P2+P3 bonifico/clitici/opt_out`
- design Step 4 → `feat(S201-PARTIAL-REPORT): scaffold + anti-reverse-image sanitizer`

## Day 1 Stile Car deadline

T-7gg al 2026-05-27. Pipeline TEST_FOUNDER NON gira oggi (#6 MISSING + #9 BUGGY). STEP 0 non superato. Stile Car Day 1 **resta BLOCKED**. Numero giorni a deadline NON è il gate — il gate è "anelli VERIFIED + TEST_FOUNDER E2E + Luke pienamente soddisfatto".
