# Prompt ripartenza S196 — gate fail S195 5.5/10

## STATO APERTURA S196
- **S195 chiusa NO_GO HARD**: revisore esterno claude.ai web bundle V2 INLINE = 5.5/10 (< 7.0 soglia) + `go_no_go=NO_GO` + 3/3 fix PARTIAL + overclaim=true
- **5 red flag diff-grounded** mai visti da CTO interno + code-reviewer agent (vedi `memory/s195_gate_fail_handoff_s196.md`)
- **Pattern strutturale 2 gate consecutivi**: S194 self 7.2→ext 6.3 / S195 self 6.3→ext 5.5. Self-assessment inflation -0.8/-0.9pt
- **Deploy iMac NON eseguito** (gate correttamente bloccante), symlink invariato `releases/20260525_211041`
- **Day 1 Stile Car 2026-06-03 — 7 giorni residui**

## AZIONE PRIMARIA S196
Leggi `prompts/s196_fix_p1_p4_revalidation.md` — handoff completo con:
- P1 runtime functional test approve_reply (CORE, sostituisce py_compile)
- P2 fix semantica return True silent-failure (signature → dict)
- P3 BRIDGE_DB_PATH precondition hard (PM2 env iMac)
- P4 costante SENTINEL_SKIP_PROMO modulo-level (elimina 4 hardcoded)
- STEP 5 re-validation bundle V3 gate ≥7.0/10

---

# Auto-snapshot

**Generato**: `2026-05-26T18:37:24Z`
**Sessione**: `4e9d4fe1-1a86-41b7-8d35-9cedb23b7d78`
**Repo**: `/Users/macbook/Documents/combaretrovamiauto-enterprise` (branch `master`)
**Commit auto**: DIRTY (vedi /Users/macbook/Documents/combaretrovamiauto-enterprise/.claude/SESSION_DIRTY.md)
**Last commit**: `09f615d docs(S194 close): gate STEP 0.5 fail 6.3/10 → handoff S195 con P1-P3 strutturali`

## Ultimi 5 commit
```
09f615d docs(S194 close): gate STEP 0.5 fail 6.3/10 → handoff S195 con P1-P3 strutturali
392d173 docs(S194 STEP 0.5): quality validation gate Claude AI esterno bloccante pre-deploy
3906f04 docs(S194): handoff dettagliato deploy iMac + AMBRA stress + E2E + decisione
44967ec docs(S193 close): NEXT_SESSION_PROMPT S194 + ctx-77% ordered closure
7396e47 feat(S192+S193-fix): sanitizer sentinel + HITL gate + audit-driven fix
```

## File modificati nell'ultimo commit
```
M	.claude/NEXT_SESSION_PROMPT.md
A	prompts/s195_revalidation_full_bundle.md
```

## Ultimo prompt utente (estratto)
```
[{"tool_use_id":"toolu_01DsgRUGkieCjE37xc5nYYvs","type":"tool_result","content":"1\t# Quality validation S193 — bundle V2 paste-ready (auto-sufficiente)\n2\t\n3\t**Versione**: V2 — corregge process gap V1 segnalato da revisore esterno S194 (P1 BLOCCANTE: bundle V1 referenziava allegati senza inlinearli → revisore valutava solo auto-valutazione testuale, non il diff).\n4\t\n5\t**Uso**: S195 STEP 0.5 V2. 8 min Luke (copy-paste su claude.ai web, attendi JSON).\n6\t\n7\t**Cambio gate**: soglia
```

## Ultimi turni assistant
```
# 3. Cmd+V nel prompt, invio, attendi JSON output
```
Vuoi che li esegua io i primi 2 (clipboard + open browser)?
```

## Come riprendere

1. Apri Claude Code da `/Users/macbook/Documents/combaretrovamiauto-enterprise`
2. Leggi questo file (auto-loaded? dipende da config progetto)
3. Continua dal punto indicato negli ultimi turni assistant sopra

Se `SESSION_DIRTY.md` esiste in questa stessa cartella, risolvi PRIMA i conflitti.
