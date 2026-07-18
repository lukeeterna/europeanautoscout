# S211 — Post-audit: chiudere i delta del MASTER PLAN

> Prerequisito: leggi `AUDIT_E2E.md` (branch `s210/audit-master-plan`) e `ARGOS_MASTER/00_INDEX/ARGOS_MASTER_PLAN.md`. NON ri-eseguire l'audit (già fatto S210, 11 delta verificati).

## Stato di partenza (verificato S210)
- Branch corrente: `s210/audit-master-plan` (2 commit: import MASTER + AUDIT_E2E.md). NON ancora su master/PR.
- Workspace: `~/Documents/combaretrovamiauto-enterprise` (confermato).
- Pipeline E2E core (scrape→CoVe→PDF): funzionante. CoVe v4 testato su 2.955 listing reali.

## I 3 delta che pesano (da decidere con Luke PRIMA di codare)
1. **GATING pagamento→rilascio-fonte NON ESISTE** (solo commento `image_sanitizer.py:13`). È il nodo che "protegge il ricavo" nel MASTER. Decisione scope: lo si progetta ora o resta deferred? `mark_paid()` (`payment_handler.py:251`) non rilascia campi sorgente.
2. **MASTER PLAN ha errori fattuali** da correggere nel source-of-truth: telefoni Marche (AS24 non Subito), param `cy=D` non `?source=DE`, CoVe non più "untested", plate-detection rimossa non "bug aperto". Decidere: si patcha `ARGOS_MASTER/04_STATO_TECNICO/STATO_COMPONENTI.md` con i fix verificati?
3. **Sales agent NON è outbound autonomo** (è AMBRA reattivo+HITL). Il MASTER Fase 1 assume un sales agent che contatta a tappeto. Gap reale: GATE-CAMPO mai eseguito, 0 dealer contattati. Decidere build-order.

## Backlog tecnico minore (da AUDIT)
- corpus_register.md inservibile per "traccia colloquio" (frammenti-dotazioni AS24 troncati). Se serve la traccia, ri-estrarre linguaggio-dealer reale (non liste-optional).
- DB split-brain: `messages` solo su iMac, `dealers`(18) su MacBook. Path iMac hardcoded in 6 file. Valutare consolidamento o documentare come voluto.
- "28/100+ portali" overclaim in identity.md → ~9-10 reali. Allineare doc.

## Vincoli invariati
- Branch dedicato, mai master. Test su TEST_FOUNDER 39<TEST_FOUNDER_NUM> prima di qualsiasi dealer reale.
- Day 1 dealer reale BLOCKED finché E2E verde su TEST_FOUNDER + Luke "pienamente soddisfatto".
- Zero-cost, HITL Telegram obbligatorio su contatto/vendita.
