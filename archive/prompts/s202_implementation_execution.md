# S202 — Implementation execution anelli #2 #6 #9 + Step 4 + E2E TEST_FOUNDER

> **Apertura sessione**: leggi in ordine
> 1. `memory/s201_closure_pivot_architect_findings.md` (pivot critical: anello #6 EXISTS_INCOMPLETE, anello #9 subprocess bypass, decisioni CTO 5/5, stack Pillow+piexif)
> 2. `memory/feedback_pipeline_test_founder_specs_corrected.md` (Step 2 Luke sceglie modello + Step 4 prezzo visibile/posizione nascosta)
> 3. `memory/feedback_e2e_full_test_founder_before_day1.md` (STEP 0 TEST_FOUNDER + Luke pienamente soddisfatto — recidiva infinite volte)
> 4. `prompts/s201_resume_anelli_critical_path.md` (gate-state ingresso S201)

---

## STEP 0 ASSOLUTO (non sindacabile)

**TEST_FOUNDER 393314928901 (SIM FLUXION fisica Luke) + Luke dichiara "pienamente soddisfatto"**.

OGNI mappatura pipeline, OGNI dichiarazione di readiness deve avere TEST_FOUNDER come Step 0 esplicito. Day 1 Stile Car BLOCKED finché gate qualitativo Luke superato.

## Decisioni S201 confermate (NO re-discussione)

- Mark-paid + contratto + prezzo fuori range = **HITL Luke**
- Soglie default: `price_floor = target × 0.95` (−5%) + `margin_min_dealer = €500 netti`
- **LangGraph DEFERRED** Sprint 2 post-Stile Car. S202 = hardcoded reactive
- Stack Step 4 = **Pillow + piexif 1.1.3** + `imagehash 4.3.2` smoke

## Critical path S202 (4 sub-step + E2E gate)

### Sub-step 1 — Anello #2 classifier P1+P2+P3 (indipendente, ~30min)

**Delegate**: `implementer` con piano S198 memory `s198_step7_rosso_3_5_classifier_gaps.md`.

Patch chirurgica `wa-intelligence/response-analyzer.py`:
- **P1** `CONTRACT_REQUEST_PATTERNS:233-238` — aggiungi regex `r'\bbonifico\b|\bpagamento\b|\bpago\b|\bprocediamo\b'`
- **P2** `PATTERNS['NEGATIVE']['exact']:1164-1171` — aggiungi entry: `"non mi scrivere più"`, `"non mi contattare più"`, `"non mi cercare più"`, `"non mi telefonare più"`
- **P3** handler NEGATIVE `:2114-2123` — `UPDATE dealers SET opt_out=1, opt_out_at=CURRENT_TIMESTAMP, opt_out_source='auto_negative', opt_out_raw_message=? WHERE id=?`

Gate: `python3 tools/test_ambra_5scenarios.py` → 5/5 PASS (era 3/5).

Post-implementer: `code-reviewer` + commit `feat(S202-CLASSIFIER): P1+P2+P3 bonifico/clitici/opt_out`.

### Sub-step 2 — Anello #6 ALTER messages (~30min)

**Delegate**: `database-admin` per migration SQL + `implementer` per integrazione daemon.

Migration locale + iMac SSH:
```sql
-- dealer_network.sqlite (locale + iMac autorevole ~/Documents/app-antigravity-auto/dealer_network.sqlite)
ALTER TABLE messages ADD COLUMN classifier_intent TEXT;
ALTER TABLE messages ADD COLUMN classifier_confidence REAL;
ALTER TABLE messages ADD COLUMN raw_payload TEXT;
CREATE INDEX IF NOT EXISTS idx_messages_phone_dir_ts ON messages(phone_number, direction, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_intent ON messages(classifier_intent) WHERE classifier_intent IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_messages_unprocessed ON messages(processed) WHERE processed = 0;
```

Patch:
- `wa-daemon.js:539-557` (`persistInboundMessage`) → popola `raw_payload = JSON.stringify({from, type, hasMedia, timestamp})`
- `wa-daemon.js:460` (`initDb`) → check `PRAGMA table_info(messages)` prima di ALTER (idempotent)
- `dashboard/db.py:33` (`ensure_tables`) → stesso pattern idempotent
- `response-analyzer.py` post-classify → `UPDATE messages SET classifier_intent=?, classifier_confidence=? WHERE id=?` (richiede propagazione `msg_id` da daemon → Python subprocess)

Gate smoke: invio msg da TEST_FOUNDER 393314928901 → riga in `messages` con `classifier_intent` e `classifier_confidence` popolati.

Post-implementer: `code-reviewer` + commit `feat(S202-INBOX): ALTER messages classifier columns + indici reactive`.

### Sub-step 3 — Anello #9 ALTER bridge_outbound + deprecate subprocess /send (~2h)

**Delegate**: `implementer` con piano architect S201.

Migration:
```sql
-- comm-broker/bridge.sqlite (locale + iMac)
ALTER TABLE bridge_outbound ADD COLUMN action_type TEXT DEFAULT 'agent_auto';
```

Patch:
- `comm-broker/wa_bridge.py:64-78` (`ensureBridgeOutboundSchema`) → ALTER idempotent
- `wa-daemon.js:378-401` (`insertBridgeOutbound`) → accetta `action_type` param, setta `approved_ts=now` se in whitelist auto-approve
- `wa-daemon.js:466` (`ensureBridgeOutboundSchemaS171`) → ALTER idempotent
- `response-analyzer.py:1650-1794` → **DEPRECATE** path diretto subprocess HTTP `/send`. Sostituisci con INSERT in `bridge_outbound` con `action_type` corretto e `approved_ts=now` se auto-approve.

Whitelist auto-approve: `day1_send, day3_followup, day7_followup, objection_reply, partial_report`.
HITL: `contract_create, mark_paid, price_override`.

Gate: invio Day 1 TEST_FOUNDER → `SELECT action_type, approved_ts, sent_ts, sent_status FROM bridge_outbound ORDER BY id DESC LIMIT 1` restituisce `day1_send, NOT NULL, NOT NULL, ok`.

Verify zero subprocess /send residui: `grep -n "SET sent" wa-intelligence/response-analyzer.py` → 0 match operativi.

Post-implementer: `code-reviewer` + `validator` E2E + commit `feat(S202-HITL): action_type policy + deprecate subprocess send + bridge single-writer enforced`.

### Sub-step 4 — Step 4 report parziale Pillow+piexif (~2-3h)

**Delegate**: `implementer` con piano tool-evaluator S201.

**Pre-condition obbligatoria**: grep `generate_opportunity_dossier` E `pdf_generator_enterprise.py` → identifica callsite reale `image_sanitizer.sanitize_image()`. NO codice prima di questo step.

Estensione `src/cove/image_sanitizer.py`:
```python
def _anti_reverse_search(img: Image.Image) -> Image.Image:
    # 1. Strip EXIF (Pillow nativo)
    img.save(buf, format="JPEG", quality=82, subsampling=2, exif=b"")
    # 2. Re-encode (encoder Pillow diverso da sorgente)
    # 3. Crop bordi 5px asimmetrico
    img = img.crop((5, 5, w-5, h-5))
    # 4. Watermark opaco >30% targa+venditore (già in scope D-32 esistente)
    # 5. Optional resize ±8px + color-shift ±8% SOLO se gate pHash fail
```

Generator PDF "report parziale" (componente nuovo):
- Tier: prezzo VISIBILE, marca+modello+anno+km VISIBILE, margine stimato VISIBILE
- Nascondi: posizione geografica, nome venditore, URL inserzione, immagini reverse-searchable

Gate smoke locale (imagehash 4.3.2):
```python
delta = imagehash.phash(orig) - imagehash.phash(safe)
assert delta >= 10, f"pHash troppo simile: {delta}"
```

Gate UAT finale: **Luke upload manuale** 3 sample su Google Images + TinEye → 0 match.

Post-implementer: `code-reviewer` + commit `feat(S202-PARTIAL-REPORT): Pillow+piexif anti-reverse-image + report parziale scaffold`.

### Sub-step 5 — E2E TEST_FOUNDER osservato Luke (gate STEP 0)

Solo dopo #2+#6+#9+Step 4 VERDI.

1. Luke sceglie modello auto manualmente (es. "Audi Q5 2021")
2. Pipeline invia Day 1 al 393314928901 **AUTO** (no approvazione TG)
3. Luke risponde fisico dalla SIM FLUXION
4. Daemon persiste in `messages`, classifier popola `classifier_intent`
5. Reactive: classifier_intent=VEHICLE_REQUEST → CoVe search → genera report parziale → invia AUTO
6. Luke firma contratto (HITL — `action_type=contract_create`)
7. Mark-paid simulato dashboard (HITL — `action_type=mark_paid`)
8. Sistema invia dossier completo
9. **Luke dichiara "pienamente soddisfatto"** → gate STEP 0 superato

## Commit attesi S202

```
feat(S202-CLASSIFIER): P1+P2+P3 bonifico/clitici/opt_out
feat(S202-INBOX): ALTER messages classifier columns + indici reactive
feat(S202-HITL): action_type policy + deprecate subprocess send + bridge single-writer
feat(S202-PARTIAL-REPORT): Pillow+piexif anti-reverse + report parziale scaffold
docs(S201 closure): pivot architect findings + decisioni CTO 5/5
```

Inoltre git mv prompts:
```
git mv /Users/macbook/Downloads/s199_claude_ai_output_v2_2026-05-27.md prompts/s199_claude_ai_output_v2_20260527.md
git add prompts/s199_*.md prompts/s200_*.md prompts/s201_*.md prompts/s202_*.md tools/test_ambra_5scenarios.py
```

## Vincoli S202

- Italiano verso Luke
- Mai PARTIAL/ARANCIONE
- Raccomandazione singola motivata (vincolo #3)
- Autocritica 4 punti su ogni proposta (vincolo #4)
- Zero costi (vincolo #5)
- Pre-flight env check pacchetti nuovi (vincolo #8) — Big Sur Python 3.13
- Mai "hai ragione" diplomatico (vincolo #9)
- Pattern recognition strutturale (vincolo #11) — STEP 0 TEST_FOUNDER prima riga ogni mappatura
- TEST_FOUNDER 393314928901 SIM FLUXION whitelist
- Domenica 2026-05-31 OFF (no scadenze Luke-fisico)
- Context >50% → handoff S203 con stato preciso
- REGOLA #0 delegation-first → minimo 4 Task delegate (implementer×4 + code-reviewer×4 + validator + database-admin)

## Day 1 Stile Car deadline

T-7gg al 2026-05-27. Pipeline TEST_FOUNDER eseguibile lun 1/06 + mar 2/06 (5gg lavorativi residui: 28-29 maggio + 1-2-3 giugno). Stile Car Day 1 BLOCKED finché gate STEP 0 superato. Numero giorni NON è il gate.
