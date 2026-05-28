# NEXT SESSION — S205 Deploy iMac + E2E TEST_FOUNDER

**Da**: S204 (audit codice-first ARGOS + update PLAN.md VOS)
**A**: S205 (deploy S202/S203 iMac + E2E TEST_FOUNDER fisico Luke)
**Deadline business**: Day 1 Stile Car 2026-06-03 (T-5gg da S205)
**Prompt completo**: `prompts/s205_deploy_imac_e2e_test_founder.md`

## Stato verificato 2026-05-28T19:15

- PM2 iMac 4/4 online (argos-wa-daemon 34h uptime, 48 restart in 34h — C-WA-RESTART-001 OPEN).
- WA daemon /status connected, daily 0/10.
- CoVe DuckDB 2955 rows, MAX(analyzed_at)=2026-05-28 17:59 (PROCEED=1046).
- Commit locali: ab6da39 (S202 classifier P1/P2/P3), ecd677c (S203 anello #9 bridge_outbound HITL). **DEPLOY IMAC PENDING** (C-DEPLOY-S203).
- PLAN.md aggiornato (audit codice-first): 6 DONE / 5 WIP / 2 BLOCKED / 2 MISSING / 1 MISSING_PARTIAL su 15 feature.
- E2E con dealer reale = 0 (C-E2E-ZERO OPEN).

## Critiche aperte (priorità)

1. **C-DEPLOY-S203** → deploy iMac codice S202/S203 (STEP A prompt S205).
2. **C-E2E-ZERO** → E2E TEST_FOUNDER 5/5 fisico Luke (STEP C, gate "pienamente soddisfatto").
3. **C-SAN-001** → UAT sanitizer 1 sample reale (STEP D).
4. **C-DB-SPLIT-001** → schema split-brain (deferred, decisione Luke post-E2E).
5. **C-WA-RESTART-001** → 48 restart/34h daemon, root cause non investigata.
6. **C-SCRAPERS-COUNT** → 3 scraper reali vs 28 dichiarati.

## STATO_AUTONOMIA

`L0=ask-always` (PLAN.md). Luke ha chiesto "vai dritto verso produzione con parametri VOS" ma:
- Luke fisico = gate hard STEP C non eludibile.
- Memoria `feedback_e2e_full_test_founder` recidiva 2026-05-27 → Day 1 dealer reale BLOCKED finché TEST_FOUNDER verde + Luke "pienamente soddisfatto".
- Memoria `feedback_no_live_without_test` → mai prompt Day 1 reale auto-eseguibile.

Prossima sessione: CC esegue autonomo STEP A+B+D+E del prompt S205, si ferma a STEP C pingando Luke.

## Avvio S205

```
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
cat prompts/s205_deploy_imac_e2e_test_founder.md
# Esegui PRE-FLIGHT PF1-PF5, poi STEP A.
```

## Vincoli non sindacabili S205

- TEST_FOUNDER 393314928901 unico canale WA reale.
- Direzione 3314928901 → 3281536308 (UX gotcha).
- Gate qualitativo Luke "pienamente soddisfatto" > checklist.
- Mai PARTIAL/ARANCIONE (vincolo #6).
- Day 1 Stile Car BLOCKED finché S205 STEP E verde.
