# ARGOS comm-broker — MVP foundation

Implementazione D-21..D-25 (ARGOS DECISIONS S167). Communication-broker-garante eBay-style: dealer IT ↔ ARGOS ↔ seller EU con identity masking + state machine + image-shield + templates.

## Stato S167 (2026-05-14)

| Componente | Spec | Status | Test |
|---|---|---|---|
| `image_shield.py` | D-25 Pillow pipeline (crop 65% + watermark grid + HSV shift + JPEG q72) | ✅ shipped | PASS area ratio 0.649, phash hamming 24 |
| `deal_state_machine.py` | D-22 F4 — python-statemachine 3.0.0 + SQLite persistence | ✅ shipped | PASS forward 7-step + restore + abort |
| `templates/*.j2` | D-22 F3 — Jinja2 5 fasi × 2 lang IT+EN | ✅ shipped | PASS 10/10 render |
| Baileys daemon | D-22 F1 messaging proxy | ⏸ S168 | — |
| Groq cascade integration | D-22 F2 NLU intent+sentiment+scam+translate | ⏸ S168 (riusa `src/llm_cascade.py` esistente) | — |
| DocuSeal self-host | D-22 F5 contract layer | ⏸ S168 (Docker iMac) — DEFERRED-pillar2 fino payment evidence (D-24) | — |
| Dashboard founder | D-22 F4 lean HTMX | ⏸ S168 | — |

## Venv

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise/comm-broker
source .venv/bin/activate
```

Deps installate: Pillow 12.2.0, imagehash 4.3.2, python-statemachine 3.0.0, jinja2 3.1.6.

## Run tests

```bash
.venv/bin/python tests/test_mvp.py
```

## Usage smoke

```bash
# Image shield single file
.venv/bin/python image_shield.py path/to/listing.jpg out.jpg --dossier-id ARGOS-2026-001

# State machine smoke (CLI)
.venv/bin/python deal_state_machine.py

# Template render smoke
.venv/bin/python templates/templates_loader.py
```

## Riferimenti

- ARGOS DECISIONS.md D-21..D-25 (workflow + stack tecnico verified)
- VOS `wiki/patterns/data-driven-research-protocol-v2-automated.md` (research methodology)
- VOS handoff S168 `~/venture-os/.claude/PROMPT-S168.md`
