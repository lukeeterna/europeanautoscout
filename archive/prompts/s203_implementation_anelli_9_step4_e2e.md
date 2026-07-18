# S203 — Implementation anelli #9 bridge_outbound + Step 4 Pillow+piexif + E2E TEST_FOUNDER

> **Apertura sessione**: leggi in ordine
> 1. `memory/s202_closure_2of5_handoff_s203.md` (stato 2/5 sub-step S202 done + commit ab6da39 + 7e0521f)
> 2. `memory/s201_closure_pivot_architect_findings.md` (decisioni CTO 5/5, anello #9 root cause subprocess bypass)
> 3. `memory/feedback_pipeline_test_founder_specs_corrected.md` (Step 2 Luke sceglie modello + Step 4 prezzo visibile/posizione nascosta)
> 4. `memory/feedback_e2e_full_test_founder_before_day1.md` (STEP 0 TEST_FOUNDER + Luke pienamente soddisfatto — recidiva infinite volte)
> 5. `prompts/s202_implementation_execution.md` sezioni Sub-step 3 + 4 + 5

---

## STEP 0 ASSOLUTO (non sindacabile, recidiva infinite volte)

**TEST_FOUNDER 39<TEST_FOUNDER_NUM> (SIM FLUXION fisica Luke) + Luke dichiara "pienamente soddisfatto"**.

Day 1 Stile Car BLOCKED finché gate qualitativo Luke superato. Gate qualitativo > deadline T-6gg.

## Decisioni S201 confermate (NO re-discussione)

- Mark-paid + contratto + prezzo fuori range = **HITL Luke**
- Soglie: `price_floor = target × 0.95` (−5%) + `margin_min_dealer = €500 netti`
- **LangGraph DEFERRED** Sprint 2 post-Stile Car. S203 = hardcoded reactive
- Stack Step 4 = **Pillow 11.3.0 (già installato) + piexif 1.1.3** + `imagehash 4.3.2` smoke gate

## Stato ingresso S203

### COMPLETATO S202
- Sub-step 1 (anello #2 classifier P1+P2+P3) commit `ab6da39`
- Sub-step 2 (anello #6 ALTER messages 3 col + 3 idx) commit `7e0521f`
- Migration SQL iMac VERIFIED: PRAGMA 11→14 col + 3 indici nuovi

### PENDING S203
- Sub-step 3 (anello #9 bridge_outbound + deprecate subprocess /send, ~2h)
- Sub-step 4 (Step 4 Pillow+piexif anti-reverse + report parziale, ~2-3h)
- Sub-step 5 (E2E TEST_FOUNDER osservato Luke + deploy iMac, gate)

## Blocker da risolvere PRIMA di sub-step 4

### BLOCKER #1 — piexif install PEP 668

Pip blocca `pip install piexif imagehash` su Big Sur MacBook (externally-managed).

Path tentati:
1. `pip install piexif imagehash` → PEP 668 error
2. `pip install --break-system-packages piexif imagehash` → Permission denied `/usr/local/images`
3. `pip install --user piexif imagehash` → PEP 668 error

Path da provare S203 (in ordine):
1. `pip install --user --break-system-packages piexif==1.1.3 imagehash==4.3.2`
2. Se #1 fail: usare venv ARGOS esistente (`~/.argos-sanitizer-venv/bin/python` se attivo, vedi `feedback_smoke_test_not_uat_gate`)
3. Se #2 fail: creare nuovo venv `python3 -m venv ~/.argos-s203-venv && ~/.argos-s203-venv/bin/pip install Pillow piexif imagehash`

Pre-flight env check (vincolo #8): `pip install --dry-run --report - piexif imagehash` già verificato VERDE su S202 (wheel py2.py3 universal, Big Sur compat).

### BLOCKER #2 — Deploy iMac patch S202

I 3 file commit S202 sono su master MacBook ma iMac runtime ha SOLO migration SQL applicata. Codice no.

Pre-sub-step 5: `bash deploy/sync.sh` o equivalent push wa-daemon.js + response-analyzer.py + dashboard/db.py + restart PM2 wa-daemon.

Verifica deploy: `ssh imac "pm2 list | grep wa-daemon"` post-restart → online.

## Critical path S203 (3 sub-step)

### Sub-step 3 — Anello #9 ALTER bridge_outbound + deprecate subprocess /send (~2h)

**Delegate**: `implementer` con piano architect S201.

**Migration**:
```sql
-- comm-broker/bridge.sqlite (iMac autorevole)
ALTER TABLE bridge_outbound ADD COLUMN action_type TEXT DEFAULT 'agent_auto';
```

Pattern idempotent stesso di S202 sub-step 2 (PRAGMA table_info check).

**Patch codice**:

A) `comm-broker/wa_bridge.py:64-78` (`ensureBridgeOutboundSchema`):
   - ALTER idempotent via PRAGMA table_info check

B) `wa-intelligence/wa-daemon.js:378-401` (`insertBridgeOutbound`):
   - Accetta `action_type` param (default 'agent_auto')
   - Setta `approved_ts=now` se in whitelist auto-approve: `day1_send, day3_followup, day7_followup, objection_reply, partial_report`

C) `wa-intelligence/wa-daemon.js:466` (`ensureBridgeOutboundSchemaS171`):
   - ALTER idempotent per backward compat

D) `wa-intelligence/response-analyzer.py:1650-1794`:
   - **DEPRECATE** subprocess HTTP `/send` fire-and-forget linea 1780
   - Sostituisci con INSERT bridge_outbound diretto con `action_type` corretto e `approved_ts=now` se auto-approve
   - HITL actions (`contract_create, mark_paid, price_override`) → INSERT con `approved_ts=NULL` (dashboard popola)

**Gate**:
- `grep -n "SET sent" wa-intelligence/response-analyzer.py` → 0 match operativi (zero subprocess /send residui)
- Smoke: invio Day 1 TEST_FOUNDER (post deploy iMac) → `SELECT action_type, approved_ts, sent_ts, sent_status FROM bridge_outbound ORDER BY id DESC LIMIT 1` → `day1_send, NOT NULL, NOT NULL, ok`

Post-implementer: `code-reviewer` + `validator` E2E + commit `feat(S203-HITL): action_type policy + deprecate subprocess /send`.

### Sub-step 4 — Step 4 Pillow+piexif + integrate generate_opportunity_dossier (~2-3h)

**Pre-condition obbligatoria** (pattern S179/S183-bis recidiva):
1. Risolvi BLOCKER #1 piexif install
2. `grep -rn "generate_opportunity_dossier" /Users/macbook/Documents/combaretrovamiauto-enterprise/src /Users/macbook/Documents/combaretrovamiauto-enterprise/tools` → identifica callsite reale
3. `grep -n "sanitize_image" src/cove/image_sanitizer.py` → identifica entry point esistente

**NO codice prima di queste 3 pre-condizioni risolte.**

**Delegate**: `implementer` con piano tool-evaluator S201.

**Estensione `src/cove/image_sanitizer.py`**:
```python
def _anti_reverse_search(img: Image.Image) -> Image.Image:
    """Step 4 anti-reverse-image: strip EXIF + re-encode + crop asimmetrico."""
    # 1. Strip EXIF (Pillow nativo)
    img.save(buf, format="JPEG", quality=82, subsampling=2, exif=b"")
    # 2. Re-encode (encoder Pillow diverso da sorgente AS24/Mobile.de)
    # 3. Crop bordi 5px asimmetrico
    img = img.crop((5, 5, w-5, h-5))
    # 4. Watermark opaco >30% targa+venditore (scope D-32 esistente — già integrato?)
    # 5. Optional resize ±8px + color-shift ±8% SOLO se gate pHash fail
```

**Generator PDF "report parziale"** (componente nuovo):
- File: `tools/scripts/pdf_generator_report_parziale.py` o estensione `pdf_generator_enterprise.py` con flag `--tier=partial`
- Tier VISIBILE: prezzo, marca, modello, anno, km, margine stimato
- Tier NASCOSTO: posizione geografica, nome venditore, URL inserzione, immagini reverse-searchable

**Gate smoke locale**:
```python
import imagehash
from PIL import Image
delta = imagehash.phash(Image.open('orig.jpg')) - imagehash.phash(Image.open('safe.jpg'))
assert delta >= 10, f"pHash troppo simile: {delta}"
```
Esegui su 5 sample AS24 reali presenti in repo (es. `/Volumes/MontereyT7/argos-poc/`).

**Gate UAT finale**: Luke manuale upload 3 sample su Google Images + TinEye → 0 match.

Post-implementer: `code-reviewer` + commit `feat(S203-PARTIAL-REPORT): Pillow+piexif anti-reverse + report parziale scaffold`.

### Sub-step 5 — E2E TEST_FOUNDER osservato Luke (gate STEP 0)

Solo dopo #3 + #4 VERDI + deploy iMac VERIFIED.

**Deploy iMac pre-sub-step 5**:
1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise && git push origin master`
2. `ssh imac "cd ~/Documents/app-antigravity-auto && git pull origin master && pm2 reload wa-daemon"`
3. Verifica: `ssh imac "pm2 list | grep wa-daemon"` → online; `curl -s http://192.168.1.2:9191/status` → connected

**Flow E2E**:
1. Luke sceglie modello auto manualmente (es. "Audi Q5 2021")
2. Pipeline invia Day 1 al 39<TEST_FOUNDER_NUM> **AUTO** (no approvazione TG, `action_type=day1_send` whitelist)
3. Luke risponde fisico dalla SIM FLUXION
4. Daemon persiste in `messages` (con raw_payload + classifier popola intent/confidence post-classify)
5. Reactive: `classifier_intent=VEHICLE_REQUEST` → CoVe search → genera report parziale (Pillow+piexif anti-reverse) → invia AUTO (`action_type=partial_report`)
6. Luke firma contratto via dashboard (HITL — `action_type=contract_create`)
7. Mark-paid simulato dashboard (HITL — `action_type=mark_paid`)
8. Sistema invia dossier completo (full PDF post-pagamento)
9. **Luke dichiara "pienamente soddisfatto"** → gate STEP 0 superato → Day 1 Stile Car SBLOCCATO

## Commit attesi S203

```
feat(S203-HITL): action_type policy + deprecate subprocess /send (anello #9)
feat(S203-PARTIAL-REPORT): Pillow+piexif anti-reverse + report parziale scaffold (Step 4)
docs(S202 closure): pivot 2/5 sub-step done + handoff S203 strutturato
```

Inoltre git mv prompts asset:
```bash
git mv /Users/macbook/Downloads/s199_claude_ai_output_v2_2026-05-27.md prompts/s199_claude_ai_output_v2_20260527.md
git add prompts/s199_*.md prompts/s200_*.md prompts/s201_*.md prompts/s202_*.md prompts/s203_*.md tools/test_ambra_5scenarios.py
```

## Vincoli S203

- Italiano verso Luke
- Mai PARTIAL/ARANCIONE (vincolo #6)
- Raccomandazione singola motivata (vincolo #3) — no lista A/B su decisioni tecniche
- Autocritica 4 punti su ogni proposta (vincolo #4)
- Zero costi (vincolo #5)
- Pre-flight env check piexif (vincolo #8) — Big Sur Python 3.13
- Mai "hai ragione" diplomatico (vincolo #9)
- Pattern recognition strutturale (vincolo #11) — STEP 0 TEST_FOUNDER prima riga
- TEST_FOUNDER 39<TEST_FOUNDER_NUM> SIM FLUXION whitelist
- Domenica 2026-05-31 OFF (no scadenze Luke-fisico)
- Context >50% → handoff S204 con stato preciso
- REGOLA #0 delegation-first → minimo 3 Task delegate (implementer×2 + code-reviewer×2 + validator E2E)

## Day 1 Stile Car deadline

T-6gg al 2026-05-28. 5gg lavorativi residui (28-29 maggio + 1-2-3 giugno).
Gate qualitativo Luke > deadline numerica. Domenica 2026-05-31 OFF.
