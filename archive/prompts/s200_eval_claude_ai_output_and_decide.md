# S200 — Cross-check output Claude AI web + decisione finale stack AMBRA-NEXT + Track A classifier fix

> **Apertura sessione**: leggi in ordine
> 1. `memory/s199_closure_handoff_s200_design_eval.md` (closure S199 + autocritica strutturale 4 punti)
> 2. `memory/s199_research_agentic_stack_findings.md` (mie findings WebSearch 7 query 2026-05-27)
> 3. `memory/s198_step7_rosso_3_5_classifier_gaps.md` (BLOCKER Day 1 classifier)
> 4. `prompts/s199_claude_ai_prompt_idempotent_v2.md` (prompt consegnato a Luke)
> 5. `prompts/s199_claude_ai_output_v2_<data>.md` (**output Claude AI atteso da Luke, da incollare STEP 0**)
>
> **Stato in ingresso**: research mia completata + memorizzata. Track A classifier fix S199 NON eseguito (Luke pivot strategico irremovibile su agente autonomo). Stile Car Day 1 deadline 2026-06-03.
>
> **Risposta follow-up già consegnata in S199**: Luke ha inoltrato a Claude AI web la domanda "vincolo prioritario stack-stitch?" e ho risposto **Opzione 1 — agent loop Python puro LangGraph-style, no servizi esterni** con 5 caveat (SQLite checkpointer no Postgres, memoria minima in-process Sprint 1 con swap Mem0 Sprint 3, tool use diretti moduli AMBRA, riuso bridge_outbound single-writer, persona classifier custom ≤200 righe). L'output Claude AI v2 atteso DEVE rispecchiare questi vincoli.
>
> **Gate qualità output Claude AI v2**: se NON rispecchia Opzione 1 + 5 caveat → rifiuta + chiedi a Luke di rieseguire claude.ai con feedback "manca aderenza Opzione 1 stack Python puro".

---

## STEP 0 — Verifica pre-condizioni (5 min)

1. **File output Claude AI esistente?**
   ```bash
   ls -1 prompts/s199_claude_ai_output_v2_*.md 2>&1
   ```
   - SE assente → STOP. Chiedi a Luke di incollare output Claude AI come `prompts/s199_claude_ai_output_v2_<YYYYMMDD>.md` prima di procedere.
   - SE presente → procedi STEP 1.

2. **Deadline check**:
   ```bash
   python3 -c "from datetime import date; print('giorni a Stile Car:', (date(2026,6,3) - date.today()).days)"
   ```
   Se ≤3 → priorità switch a Track A classifier urgente (vedi STEP 5-fallback).

3. **pm2 iMac health 4/4**:
   ```bash
   ssh gianlucadistasi@192.168.1.2 "export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH && pm2 list" | grep -E "(online|stopped|errored)"
   ```

4. **Git status**:
   ```bash
   git status -s | grep -E "(s199|test_ambra)"
   ```
   4 asset S198/S199 untracked attesi.

---

## STEP 1 — Parse output Claude AI sezione 9 JSON (10 min)

Output Claude AI deve avere sezione 9 JSON-parseable. Estrai e valida:

```bash
python3 -c "
import re, json
with open('prompts/s199_claude_ai_output_v2_<YYYYMMDD>.md') as f:
    content = f.read()
m = re.search(r'\`\`\`json\s*(\{.*?\})\s*\`\`\`', content, re.DOTALL)
if not m:
    print('FAIL: no JSON section 9')
    exit(1)
data = json.loads(m.group(1))
print('version:', data.get('version'))
print('agent_loop_pattern:', data.get('agent_loop_pattern'))
print('repos_stitched:', len(data.get('repos_stitched', [])))
print('cold_contact_hooks:', len(data.get('cold_contact_hooks', [])))
print('gap_coverage:', len(data.get('gap_coverage', [])))
print('metrics with source_url:', sum(1 for m in data.get('metrics',[]) if m.get('source_url')))
print('open_questions:', len(data.get('open_questions_for_luke', [])))
"
```

**Gate quality output Claude AI**:
- ≥6 repo_stitched con `last_commit` + `stars` + `license`
- ≥3 cold_contact_hooks
- ≥15 gap_coverage (su 17)
- ≥5 metrics di cui ≥3 con source_url verificabile
- agent_loop_pattern definito (no "TBD")

SE gate FAIL → chiedi Luke se rieseguire Claude AI con feedback o procedere best-effort.

---

## STEP 2 — Matrix cross-check Claude AI vs mie findings (20 min)

Per ogni elemento Claude AI confronta con `memory/s199_research_agentic_stack_findings.md`:

| Dimensione | Claude AI propone | Mia research | Status |
|---|---|---|---|
| Agent loop framework | <da JSON> | LangGraph leader 2026 | VERIFIED / DISPUTED / NOVEL |
| Memory layer | <da JSON> | Mem0 / Letta / Zep | VERIFIED / DISPUTED / NOVEL |
| WA channel base | <da JSON> | b2b-sdr-agent-template + wakit | VERIFIED / DISPUTED / NOVEL |
| Persona detection | <da JSON> | Custom classifier (no production repo) | VERIFIED / DISPUTED / NOVEL |
| HITL pattern | <da JSON> | LangGraph `interrupt()` + threshold empirico | VERIFIED / DISPUTED / NOVEL |
| DATI WA Italia | <da JSON> | >50% response rate (outreaches.ai) | VERIFIED / DISPUTED / NOVEL |
| Cold hook proattivo | <da JSON> | (gap G14, Claude AI doveva inventare) | VALUTA QUALITÀ |

Salva matrix in `prompts/s200_cross_check_matrix.md`.

---

## STEP 3 — Verifica repo Claude AI proposti (15 min)

Per ogni repo nel JSON `repos_stitched`:
1. WebFetch homepage → conferma esistenza, licenza, ultima commit, ⭐
2. Flag repo abbandonati (>12 mesi senza commit) → SCARTATI
3. Flag licenze restrittive (GPL/AGPL se ARGOS commerciale) → AUDIT
4. Cross-check con mia lista (b2b-sdr-agent-template, wakit, mem0, langgraph, etc.)

Tabella output in `prompts/s200_repo_audit.md`.

---

## STEP 4 — Decisione architetturale finale (30 min)

**Vincolo #3**: una raccomandazione singola motivata con DATI. NO liste A/B/C.

Output: `prompts/s200_decision_architecture_ambra_next.md`

Struttura obbligatoria:
1. **Stack scelto** (3-5 componenti core stitched + AMBRA riusata)
2. **Razionale 5 punti** (perché questa combo vs alternative, con DATI Claude AI + mie)
3. **Autocritica 4 punti** (vincolo #4)
4. **Sprint 1 MVP scope** (cold hook + persona auto)
5. **Costo stimato LLM/mese** (vs hard cap €30)
6. **Compat Big Sur + iMac 2012** verificata per ogni dep
7. **HITL gate plan** (quali nodi interrupt, threshold)
8. **Open questions to Luke** (decisioni founder pending)

---

## STEP 5 — Pre-handoff Track A urgente Day 1 Stile Car (CRITICO)

**Track A è SEPARATO da decisione architetturale**. Day 1 Stile Car NON aspetta AMBRA-NEXT.

Se deadline ≤ 5 giorni (STEP 0 punto 2):
- **STOP STEP 4** se non chiuso
- **Esegui Track A classifier fix** da `prompts/s199_resume_classifier_fix_and_claude_ai_eval.md`:
  - P1 CONTRACT_REQUEST_PATTERNS regex bonifico/pagamento
  - P2 PATTERNS['NEGATIVE']['exact'] 6 entry clitici
  - P3 handler NEGATIVE popola opt_out=1
  - Re-run `tools/test_ambra_5scenarios.py` → 5/5
  - E2E Luke fisico TEST_FOUNDER (9 step `prompts/s190_e2e_physical_close.md`)
  - Matrix decisione Day 1

Se deadline >5gg: completa STEP 4 (decisione architettura) PRIMA di Track A.

---

## STEP 6 — Commit asset S198+S199+S200 (10 min)

Se STEP 0-5 verde:
```bash
git add prompts/s199_*.md prompts/s200_*.md tools/test_ambra_5scenarios.py
git commit -m "feat(S199-S200): AMBRA-NEXT design eval + Claude AI cross-check + decision"
```

Asset attesi:
- `prompts/s199_claude_ai_prompt_idempotent_v2.md`
- `prompts/s199_claude_ai_output_v2_<data>.md` (incollato da Luke)
- `prompts/s199_resume_classifier_fix_and_claude_ai_eval.md`
- `prompts/s199_claude_ai_design_autonomous_sales_agent.md`
- `prompts/s199_claude_ai_output_20260527.md`
- `prompts/s200_cross_check_matrix.md`
- `prompts/s200_repo_audit.md`
- `prompts/s200_decision_architecture_ambra_next.md`
- `tools/test_ambra_5scenarios.py`

---

## Vincoli S200

- Italiano verso Luke
- Mai PARTIAL/ARANCIONE
- Una raccomandazione singola motivata con DATI (vincolo #3)
- Autocritica 4 punti su ogni proposta (vincolo #4)
- Zero costi, HITL immutato
- TEST_FOUNDER 39<TEST_FOUNDER_NUM> SIM FLUXION
- Domenica 2026-05-31 OFF
- REGOLA #0 delegation-first: tool-evaluator per scelta framework, code-reviewer per integrazione
- Context >50% → handoff S201 con stato preciso

---

## Risorse

- Mie findings research: `memory/s199_research_agentic_stack_findings.md`
- Prompt Claude AI consegnato: `prompts/s199_claude_ai_prompt_idempotent_v2.md`
- AMBRA inventario 23 capability: dentro prompt v2 sopra
- 17 Gap target: dentro prompt v2 sopra
- BLOCKER classifier Day 1: `memory/s198_step7_rosso_3_5_classifier_gaps.md`
- E2E Luke fisico ref: `prompts/s190_e2e_physical_close.md`
- DECISIONS founder ARGOS: `~/venture-os/wiki/projects/ARGOS/DECISIONS.md`
