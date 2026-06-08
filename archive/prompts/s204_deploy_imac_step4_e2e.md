# S204 — Deploy iMac S203 + Sub-step 4 anti-reverse + E2E TEST_FOUNDER

> **Apertura sessione**: leggi in ordine
> 1. `memory/s203_closure_step_b_done.md` (stato S203 Step A+B done, commit d568118 + ecd677c)
> 2. `memory/s202_closure_2of5_handoff_s203.md` (anelli #2 + #6 done)
> 3. `memory/s201_closure_pivot_architect_findings.md` (decisioni CTO 5/5 closed)
> 4. `prompts/s203_implementation_anelli_9_step4_e2e.md` sezioni Sub-step 4 + 5

---

## STEP 0 ASSOLUTO (non sindacabile)

**TEST_FOUNDER 393314928901 (SIM FLUXION fisica Luke) + Luke dichiara "pienamente soddisfatto"**.

Day 1 Stile Car (2026-06-03, T-5gg) BLOCKED finché gate qualitativo Luke superato.

## Stato ingresso S204

### CHIUSO S202-S203
- S202 Sub-step 1 (anello #2 classifier P1+P2+P3) — commit `ab6da39`
- S202 Sub-step 2 (anello #6 ALTER messages + 3 idx) — commit `7e0521f`
- S203 Step A (commit asset prompts S199-S202) — commit `d568118`
- S203 Step B (Sub-step 3 anello #9 bridge_outbound HITL) — commit `ecd677c`
  - migration SQL + apply_s203_migration.py (idempotent PRAGMA)
  - wa_bridge.py + wa-daemon.js (BRIDGE_AUTO_APPROVE_ACTIONS / BRIDGE_HITL_ACTIONS)
  - response-analyzer.py mono-msg: Popen → bridge INSERT direct
  - code-review 2 MED fixati pre-commit (rowcount→total_changes delta + Telegram alert pre-raise)

### PENDING S204
- **Step C** — deploy iMac (~15min) — push master + ssh pull + apply migration + pm2 reload
- **Step D** — Sub-step 4 Pillow+piexif anti-reverse + report parziale (~2-3h) — implementer + code-reviewer
- **Step E** — E2E TEST_FOUNDER osservato Luke fisico (gate STEP 0)

### Pre-flight già VERDE
- `piexif 1.1.3 + imagehash 4.3.2 + Pillow 11.3.0` GIÀ installati su `/usr/local/opt/python@3.13/bin/python3` (BLOCKER #1 S203 obsoleto)

## Step C — Deploy iMac (~15min)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git push origin master

# Verifica iMac autorevole DB path (riferimento memory feedback S173-S174)
ssh imac "ls -la ~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite ~/Documents/app-antigravity-auto/dealer_network.sqlite"

# Pull + apply migration + reload
ssh imac "cd ~/Documents/app-antigravity-auto && git pull origin master"
ssh imac "cd ~/Documents/app-antigravity-auto && python3 comm-broker/migrations/apply_s203_migration.py comm-broker/bridge.sqlite"
ssh imac "pm2 reload wa-daemon"

# Gate verifica
ssh imac "pm2 list | grep wa-daemon"  # online
ssh imac "curl -s localhost:9191/status"  # connected
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite 'PRAGMA table_info(bridge_outbound)' | grep action_type"  # presente
```

Atteso: action_type column presente + wa-daemon online + status connected.

## Step D — Sub-step 4 anti-reverse Pillow+piexif (~2-3h)

**Pre-condizioni obbligatorie** (pattern ricaduta over-mask S179/S183b/S187/S188):
1. `grep -rn "generate_opportunity_dossier" src/ tools/` → identifica callsite reale
2. `grep -n "sanitize_image" src/cove/image_sanitizer.py` → entry point esistente
3. Sample reali in `/Volumes/MontereyT7/argos-poc/` per gate pHash

**NO codice prima di queste 3 pre-condizioni risolte** (vincolo S179b lesson).

**Delegate**: `implementer` con piano tool-evaluator S201.

### Estensione `src/cove/image_sanitizer.py`
```python
def _anti_reverse_search(img: Image.Image) -> Image.Image:
    """Step 4 anti-reverse-image: strip EXIF + re-encode + crop asimmetrico."""
    # 1. Strip EXIF (Pillow nativo) — save con exif=b""
    # 2. Re-encode JPEG quality=82 subsampling=2 (encoder diverso da AS24/Mobile.de)
    # 3. Crop bordi 5px asimmetrico left/right
    # 4. Watermark opaco >30% targa+venditore (D-32 esistente — verificare già integrato)
    # 5. Optional resize ±8px + color-shift ±8% SOLO se gate pHash fail
```

### Generator PDF report parziale (componente nuovo)
- File: estensione `pdf_generator_enterprise.py` con flag `--tier=partial` (preferito a file nuovo, evita duplicazione)
- Tier VISIBILE: prezzo, marca, modello, anno, km, margine stimato
- Tier NASCOSTO: posizione geografica, nome venditore, URL inserzione, immagini reverse-searchable

### Gate smoke locale (NON UAT)
```python
import imagehash
from PIL import Image
delta = imagehash.phash(Image.open('orig.jpg')) - imagehash.phash(Image.open('safe.jpg'))
assert delta >= 10, f"pHash troppo simile: {delta}"
```
Esegui su 5 sample AS24 reali da `/Volumes/MontereyT7/argos-poc/`.

### Gate UAT finale (BLOCKER E2E)
Luke manuale upload 3 sample su Google Images + TinEye → 0 match.

Post-implementer: `code-reviewer` + commit `feat(S203-PARTIAL-REPORT): Pillow+piexif anti-reverse + report parziale scaffold`.

## Step E — E2E TEST_FOUNDER osservato Luke (gate STEP 0)

Solo dopo Step C + Step D verdi.

**Flow**:
1. Luke sceglie modello auto manualmente (es. "Audi Q5 2021")
2. Pipeline invia Day 1 al 393314928901 AUTO (`action_type=day1_send` whitelist)
3. Luke risponde fisico dalla SIM FLUXION
4. Daemon persiste in `messages` (raw_payload + classifier post-classify)
5. Reactive: `classifier_intent=VEHICLE_REQUEST` → CoVe search → report parziale anti-reverse → invia AUTO (`action_type=partial_report`)
6. Luke firma contratto via dashboard (HITL — `action_type=contract_create`)
7. Mark-paid simulato dashboard (HITL — `action_type=mark_paid`)
8. Sistema invia dossier full PDF
9. **Luke dichiara "pienamente soddisfatto"** → gate STEP 0 superato → Day 1 Stile Car SBLOCCATO

## Scope-out S204

- 64 prompts/ deleted + .planning/ dirty whitespace → SESSIONE FUTURA dedicata cleanup
- BACKLOG #S172-1 multi-msg gating (ramo Day3-voice/Day7) → Sprint 2 post-Stile Car
- LangGraph migration → DEFERRED Sprint 2

## Vincoli S204

- Italiano verso Luke
- Mai PARTIAL/ARANCIONE (vincolo #6)
- Raccomandazione singola (vincolo #3)
- Autocritica 4 punti (vincolo #4)
- Zero costi (vincolo #5)
- Context >50% → handoff S205 con stato preciso
- REGOLA #0 delegation-first → minimo 2 Task (implementer Step D + code-reviewer)
- TEST_FOUNDER 393314928901 SIM FLUXION whitelist
- Domenica 2026-05-31 OFF (no scadenze Luke-fisico)

## Day 1 Stile Car deadline

T-5gg al 2026-05-28 (lun 02-mar 03 giugno fattibili). Domenica 31 OFF.
Gate qualitativo Luke > deadline numerica.
