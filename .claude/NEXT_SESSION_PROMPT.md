# NEXT SESSION — S195 ARGOS

**Generato**: 2026-05-26 (S194 close ordinato post gate fail)
**Repo**: `/Users/macbook/Documents/combaretrovamiauto-enterprise` (branch `master`)
**Day 1 Stile Car deadline**: 2026-06-03 mercoledì (7 giorni utili da S195)

## Stato S194 (chiuso VERDE handoff strutturato)

- HEAD master: `<commit S194 close>` (push GitHub)
- iMac symlink: `releases/20260525_211041` — codice 25 mag, **NON aggiornato**
- S192+S193-fix: NON live in produzione
- Day 1 Stile Car: BLOCKED su S195 GO/NO-GO motivato

**Cosa è successo S194**:
- STEP 0 verifica stato: PASS
- STEP 0.5 quality validation Claude AI esterno: **FAIL** (`external_score=6.3/10 < 6.5` + 3 precondizioni BLOCCANTI P1+P2+P3)
- STEP 1 deploy iMac: NON eseguito (gate fail correttamente bloccante)
- Chiusura VERDE con asset S195 generati strutturalmente

**Lezioni assorbite dal revisore esterno**:
1. Gate process falliti = **moltiplicatori binari** (cappano voto a max 6.5), NON addendi mediabili
2. Near-miss intercettato da Luke ≠ merito del sistema
3. py_compile + code-reviewer GO sono 2 segnali deboli → serve test funzionale runtime

## Come riprendere S195

1. Apri Claude Code da `/Users/macbook/Documents/combaretrovamiauto-enterprise`
2. **Apri prompt S195**: `prompts/s195_revalidation_full_bundle.md`
3. **Bundle V2 paste-ready** (auto-sufficiente, diff+audit INLINE): `/tmp/s195_QUALITY_VALIDATION_PROMPT_v2.md`
4. **Audit S194**: `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s194_gate_fail_handoff_s195.md`

## Sequenza S195 (gated)

1. **STEP 0** verifica stato (5 min)
2. **STEP 0.5 V2** quality validation bundle V2 BLOCCANTE (8 min Luke) — soglia ≥7.0/10
3. **STEP 0.6** AskUserQuestion bloccante pre-deploy (P3 incorporato)
4. **STEP 1** deploy iMac + BRIDGE_DB_PATH + smoke approve_reply runtime (P5)
5. **STEP 2** AMBRA stress 5 scenari TEST_FOUNDER 393314928901 (60 min Luke fisico)
6. **STEP 3** E2E 9-step pipeline contatto→dossier→firma→mark-paid (45 min Luke fisico)
7. **STEP 4** decisione Day 1 Stile Car matrix 4-dim (validazione esterna + STEP 1 + STEP 2 + STEP 3)

## Vincoli operativi

- AskUserQuestion mirata PRIMA di ogni shared-state action (deploy, restart, mark-paid)
- Context budget: warning 50%, closure 60%, MAI deploy mid-saturation >70%
- Mai liste A/B/C/D su decisioni tecniche
- Delegation-first: code-reviewer obbligatorio prima di qualsiasi commit S195-fix
- Stati VERDE/handoff, mai PARTIAL/ARANCIONE

## Asset pronti

- `prompts/s195_revalidation_full_bundle.md` — sequenza completa con P1-P3 strutturalmente risolti
- `/tmp/s195_QUALITY_VALIDATION_PROMPT_v2.md` — bundle V2 paste-ready auto-sufficiente (diff 282 righe + audit 75 righe INLINE)
- Memory `s194_gate_fail_handoff_s195.md` — audit S194 fail + lezioni
