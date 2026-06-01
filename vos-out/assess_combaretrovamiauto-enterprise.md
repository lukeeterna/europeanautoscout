# ASSESS — combaretrovamiauto-enterprise

- generato: 2026-05-28T07:27:14Z
- path: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- file planning rilevati: 99
- conflitti sospetti: 10
- file dormienti (>90gg): 0
- **maturità SOSPETTATA (non verdetto)**: `mature`

> Il filesystem può mentire. Le domande sotto vanno confermate da CC-in-sessione + Luke.
> Salvare le risposte in `vos-out/assess_<project>.answers.md`.

## DOMANDE

### Conflitti sospetti (più file con tema affine)

**Q1.** Tema `roadmap` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `.planning/ROADMAP.md` (mtime 2026-05-21)
  - `docs/dev/ROADMAP.md` (mtime 2026-03-14)
  - `tools/gsd/get-shit-done/templates/roadmap.md` (mtime 2026-03-12)

**Q2.** Tema `requirements` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `.planning/REQUIREMENTS.md` (mtime 2026-04-15)
  - `wa-intelligence/requirements.txt` (mtime 2026-04-09)
  - `src/bot/requirements.txt` (mtime 2026-03-13)
  - `tools/gsd/get-shit-done/templates/requirements.md` (mtime 2026-03-12)

**Q3.** Tema `04-plan` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `.planning/phases/04-primo-outreach-stile-car/04-04-PLAN.md` (mtime 2026-04-15)
  - `.planning/phases/06-ambra-agent-wa-autonomo/06-04-PLAN.md` (mtime 2026-03-27)
  - `.planning/phases/01-validazione-tool-gratuiti/01-04-PLAN.md` (mtime 2026-03-24)

**Q4.** Tema `03-plan` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `.planning/phases/04-primo-outreach-stile-car/04-03-PLAN.md` (mtime 2026-04-15)
  - `.planning/phases/06-ambra-agent-wa-autonomo/06-03-PLAN.md` (mtime 2026-03-27)
  - `.planning/phases/01-validazione-tool-gratuiti/01-03-PLAN.md` (mtime 2026-03-24)

**Q5.** Tema `02-plan` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `.planning/phases/04-primo-outreach-stile-car/04-02-PLAN.md` (mtime 2026-04-15)
  - `.planning/phases/06-ambra-agent-wa-autonomo/06-02-PLAN.md` (mtime 2026-03-27)
  - `.planning/phases/03-argos-grade-pdf-enterprise-v2/03-02-PLAN.md` (mtime 2026-03-24)
  - `.planning/phases/02-schema-db-detail-enricher/02-02-PLAN.md` (mtime 2026-03-24)
  - `.planning/phases/01-validazione-tool-gratuiti/01-02-PLAN.md` (mtime 2026-03-24)

**Q6.** Tema `01-plan` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `.planning/phases/04-primo-outreach-stile-car/04-01-PLAN.md` (mtime 2026-04-15)
  - `.planning/phases/06-ambra-agent-wa-autonomo/06-01-PLAN.md` (mtime 2026-03-27)
  - `.planning/phases/03-argos-grade-pdf-enterprise-v2/03-01-PLAN.md` (mtime 2026-03-24)
  - `.planning/phases/02-schema-db-detail-enricher/02-01-PLAN.md` (mtime 2026-03-24)
  - `.planning/phases/01-validazione-tool-gratuiti/01-01-PLAN.md` (mtime 2026-03-24)

**Q7.** Tema `research` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `.planning/phases/10-deep-research-mercato-dealer/10-RESEARCH.md` (mtime 2026-03-31)
  - `.planning/phases/11-automazione-comunicazione-dealer/11-RESEARCH.md` (mtime 2026-03-31)
  - `.planning/phases/10-dealer-discovery-automation/10-RESEARCH.md` (mtime 2026-03-31)
  - `.planning/phases/09-fiducia-dealer-sud-italia/09-RESEARCH.md` (mtime 2026-03-31)
  - `.planning/phases/08-trasporto-veicolo-eu-sud-italia/08-RESEARCH.md` (mtime 2026-03-31)
  - `.planning/phases/07-image-sanitizer-v9/07-RESEARCH.md` (mtime 2026-03-30)
  - `.planning/phases/05-pipeline-orchestrator/RESEARCH.md` (mtime 2026-03-26)
  - `tools/gsd/get-shit-done/templates/research.md` (mtime 2026-03-12)

**Q8.** Tema `research-phase` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `tools/gsd/get-shit-done/workflows/research-phase.md` (mtime 2026-03-12)
  - `tools/gsd/commands/gsd/research-phase.md` (mtime 2026-03-12)

**Q9.** Tema `plan-phase` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `tools/gsd/get-shit-done/workflows/plan-phase.md` (mtime 2026-03-12)
  - `tools/gsd/commands/gsd/plan-phase.md` (mtime 2026-03-12)

**Q10.** Tema `plan-milestone-gaps` — quale è attuale? Gli altri sono `[SUPERSEDED]` o ESCLUDERE?
  - `tools/gsd/get-shit-done/workflows/plan-milestone-gaps.md` (mtime 2026-03-12)
  - `tools/gsd/commands/gsd/plan-milestone-gaps.md` (mtime 2026-03-12)

### Verdetto maturità

**Q11.** Maturità SOSPETTATA = `mature`. Confermi? Se no: `mature` | `maturing` | `greenfield`?

### Direzione attuale

**Q12.** Qual è la direzione attuale del progetto? (1 frase, sarà OBIETTIVO del PLAN.md)

## OUTPUT ATTESO

Dopo conferma, rieseguire con i flag (vedi `vos_plan assess --help`):
```
vos_plan adopt|create|greenfield /Users/macbook/Documents/combaretrovamiauto-enterprise
```
e marcare i file `[SUPERSEDED]`/esclusi nel file `.answers.md`.
