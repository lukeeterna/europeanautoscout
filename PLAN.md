<!-- VOS PLAN — template generico. Compilato da `vos_plan adopt|create|greenfield`.
     Posizione canonica: <project>/PLAN.md (root del progetto).
     Stati CRITIQUE: [OPEN] | [ADDRESSED] | [DEFERRED:motivo]
     Tag confidence TARGET_VALIDATO: VERIFIED:<fonte> | INFERRED | ASSUMPTION
     Non rimuovere le intestazioni `## SECTION` — il motore le usa per il parsing.

     NOTA modalità `adopt`: importa SOLO riferimenti ai file planning esistenti in METODO
     (filesystem mente — vedi Sez. 2.0 spec). OBIETTIVO, GUARDRAIL, METRICHE_SOGLIE,
     TARGET_VALIDATO restano da compilare A MANO dopo adopt: il motore non assorbe
     contenuto dai file importati, solo riferimenti. Popolare prima di lanciare
     `vos_plan maturity` o gate decisionali. -->

# PLAN — combaretrovamiauto-enterprise

## META
- project: combaretrovamiauto-enterprise
- path: /Users/macbook/Documents/combaretrovamiauto-enterprise
- maturità: maturing          <!-- mature | maturing | greenfield, CONFERMATA via assess -->
- creato: 2026-05-28T07:54:59Z
- ultimo_update: 2026-05-29T13:55:00Z
- modalità_ingaggio: adopt  <!-- adopt | create | greenfield -->

## OBIETTIVO
<!-- Una frase netta. Cosa deve produrre il progetto, per chi, in che orizzonte. -->
scouting on-demand auto per micro-dealer commissione P.IVA forfettaria Italia, commissione su consegna posizione

## GUARDRAIL
<!-- Vincoli non derogabili (budget, stack, compat, founder-decisions). Uno per riga. -->
- Scope nazionale Italia: MAI hardcoding territoriale (no Foggia/Basilicata/Sud-only)
- Brand pubblico: ARGOS™ — persona comunicazione: Luca Ferretti (NON Luke/Gianluca)
- Target ESCLUDE dealer stock ≥20 (target reale = micro-dealer commissione P.IVA forfettaria)
- Service-based offer: brand + scouting + import + docs + area formativa (NON SaaS)
- Pricing model: commissione su consegna posizione (pay-on-delivery), NO upfront fee
- Stack: Python 3.13 + SQLite (`dealer_network.sqlite`) — no rewrite
- macOS Big Sur compat MacBook + iMac 2012 server (SSH stateless on-demand)
- Budget LLM hard cap €30/mese, free-tier first (OpenRouter routing)
- HITL via Telegram (riservato ARGOS, mai per VOS o altri progetti)
- Scraping TOS-compliant: rate-limit + UA reali, no aggressive automation

## TARGET_VALIDATO
<!-- Chi è l'utente reale. Ogni claim TAG: VERIFIED:<fonte> | INFERRED | ASSUMPTION -->
- Micro-dealer commissione P.IVA forfettaria, stock <20 [VERIFIED:memoria feedback_argos_target_microdealer_commissione]
- Geografico: tutta Italia (NO restrizione territoriale) [VERIFIED:memoria feedback_argos_scope_italia]
- Service-based: brand + scouting + import + docs + formazione [VERIFIED:memoria project_argos_business_model_real]
- Pay-on-delivery commissione su consegna posizione [VERIFIED:memoria project_argos_business_model_real]
- Buyer side: BMW/Mercedes/Audi DE/BE/NL/AT [VERIFIED:~/.claude/CLAUDE.md]
- 0 paying customer al 2026-05-28 [VERIFIED:memoria feedback_premature_optimization (no payment evidence)]
- Pain primario dealer: accesso a stock estero qualità senza rischio cambio/dogana [ASSUMPTION:nessuna intervista validation done]

## METODO
<!-- Come ci arrivi. Fasi, dipendenze, gate. Niente roadmap-novel: bullet brevi. -->
<!-- importato da .planning/ via assess (file vivi soltanto) -->
- ref: `prompts/s201_resume_anelli_critical_path.md` (mtime 2026-05-27)
- ref: `.planning/ROADMAP.md` (mtime 2026-05-21)
- ref: `prompts/s175_1b_replay_test_founder.md` (mtime 2026-05-16)
- ref: `prompts/s175_0_e2e_reactive_test_founder.md` (mtime 2026-05-15)
- ref: `comm-broker/WA_DAEMON_WIRE_UP_PLAN.md` (mtime 2026-05-14)
- ref: `FOUNDER-DECISIONS-2026-05-13.md` (mtime 2026-05-13)
- ref: `.planning/E2E-SIM-PLAN.md` (mtime 2026-05-01)
- ref: `.planning/research/s126_research_nord_centro_dealer.md` (mtime 2026-04-16)
- ref: `.planning/REQUIREMENTS.md` (mtime 2026-04-15)
- ref: `.planning/phases/04-primo-outreach-stile-car/04-04-PLAN.md` (mtime 2026-04-15)
- ref: `.planning/phases/04-primo-outreach-stile-car/04-03-PLAN.md` (mtime 2026-04-15)
- ref: `.planning/phases/04-primo-outreach-stile-car/04-02-PLAN.md` (mtime 2026-04-15)
- ref: `.planning/phases/04-primo-outreach-stile-car/04-01-PLAN.md` (mtime 2026-04-15)
- ref: `.planning/HIGH-FIXES-RESEARCH.md` (mtime 2026-04-13)
- ref: `.claude/agent-memory/competitive-intel/reference_market_research_file.md` (mtime 2026-04-13)
- ref: `.claude/agent-memory/legal-compliance-checker/user_argos_founder.md` (mtime 2026-04-13)
- ref: `.planning/MARKET-RESEARCH-2026.md` (mtime 2026-04-13)
- ref: `wa-intelligence/requirements.txt` (mtime 2026-04-09)
- ref: `.claude/agents/sales/sales-agent-blueprint.md` (mtime 2026-04-09)
- ref: `.claude/agents/intelligence/deep-researcher.md` (mtime 2026-04-09)
- ref: `.claude/agents/product/trend-researcher.md` (mtime 2026-04-09)
- ref: `research/s96_gap3_orchestrator_research.md` (mtime 2026-04-01)
- ref: `research/s96_gap2_wa_listener_research.md` (mtime 2026-04-01)
- ref: `research/s96_gap4_scheduler_research.md` (mtime 2026-04-01)
- ref: `research/s96_gap1_browser_automation_research.md` (mtime 2026-04-01)
- ref: `research/s94_ACTION_PLAN_NUOVI_TARGET.md` (mtime 2026-03-31)
- ref: `.planning/phases/10-deep-research-mercato-dealer/10-RESEARCH.md` (mtime 2026-03-31)
- ref: `.planning/phases/11-automazione-comunicazione-dealer/11-RESEARCH.md` (mtime 2026-03-31)
- ref: `.planning/phases/10-dealer-discovery-automation/10-RESEARCH.md` (mtime 2026-03-31)
- ref: `.planning/phases/09-fiducia-dealer-sud-italia/09-RESEARCH.md` (mtime 2026-03-31)
- ref: `.planning/phases/08-trasporto-veicolo-eu-sud-italia/08-RESEARCH.md` (mtime 2026-03-31)
- ref: `.planning/phases/07-image-sanitizer-v9/07-RESEARCH.md` (mtime 2026-03-30)
- ref: `.planning/phases/06-ambra-agent-wa-autonomo/06-05-PLAN.md` (mtime 2026-03-27)
- ref: `.planning/phases/06-ambra-agent-wa-autonomo/06-04-PLAN.md` (mtime 2026-03-27)
- ref: `.planning/phases/06-ambra-agent-wa-autonomo/06-03-PLAN.md` (mtime 2026-03-27)
- ref: `.planning/phases/06-ambra-agent-wa-autonomo/06-02-PLAN.md` (mtime 2026-03-27)
- ref: `.planning/phases/06-ambra-agent-wa-autonomo/06-01-PLAN.md` (mtime 2026-03-27)
- ref: `research/s84_transport_options_deep_research.md` (mtime 2026-03-26)
- ref: `.planning/phases/05-pipeline-orchestrator/RESEARCH.md` (mtime 2026-03-26)
- ref: `.planning/phases/03-argos-grade-pdf-enterprise-v2/03-02-PLAN.md` (mtime 2026-03-24)
- ref: `.planning/phases/03-argos-grade-pdf-enterprise-v2/03-01-PLAN.md` (mtime 2026-03-24)
- ref: `.planning/phases/02-schema-db-detail-enricher/02-02-PLAN.md` (mtime 2026-03-24)
- ref: `.planning/phases/02-schema-db-detail-enricher/02-01-PLAN.md` (mtime 2026-03-24)
- ref: `.planning/phases/01-validazione-tool-gratuiti/01-04-PLAN.md` (mtime 2026-03-24)
- ref: `.planning/phases/01-validazione-tool-gratuiti/01-03-PLAN.md` (mtime 2026-03-24)
- ref: `.planning/phases/01-validazione-tool-gratuiti/01-02-PLAN.md` (mtime 2026-03-24)
- ref: `.planning/phases/01-validazione-tool-gratuiti/01-01-PLAN.md` (mtime 2026-03-24)
- ref: `research/s83_dekra_dat_access_research.md` (mtime 2026-03-24)
- ref: `research/s82_sistema_perfetto_blueprint.md` (mtime 2026-03-24)
- ref: `.claude/agents/product/dealer-persona-researcher.md` (mtime 2026-03-23)
- ref: `.claude/agents/product/roadmap-planner.md` (mtime 2026-03-23)
- ref: `.claude/agents/intelligence/lead-researcher.md` (mtime 2026-03-23)
- ref: `landing/.claude/agent-memory/agent-research/research_visual_identity_brand_2026.md` (mtime 2026-03-23)
- ref: `research/s79_linkedin_automation_research.md` (mtime 2026-03-23)
- ref: `landing/.claude/agent-memory/agent-research/research_linkedin_automation_2026.md` (mtime 2026-03-23)
- ref: `research/s73_system_features_roadmap.md` (mtime 2026-03-21)
- ref: `.claude/agent-memory/agent-research/project_s79_deep_research_3_dealer_2026-03-21.md` (mtime 2026-03-21)
- ref: `research/s77_dealer_growth_programs_research.md` (mtime 2026-03-21)
- ref: `research/s73_dealer_silence_outreach_research.md` (mtime 2026-03-21)
- ref: `research/s69_scoring_intelligence_systems_deep_research.md` (mtime 2026-03-20)
- ref: `research/s65_credibility_operations_research.md` (mtime 2026-03-19)
- ref: `.claude/agent-memory/agent-research/project_ai_voice_sara_research_2026-03-18.md` (mtime 2026-03-18)
- ref: `.claude/agent-memory/agent-research/project_ui_dashboard_research_2026-03-18.md` (mtime 2026-03-18)
- ref: `.claude/agent-memory/agent-research/voip_wa_business_research_2026-03-16.md` (mtime 2026-03-16)
- ref: `.claude/agent-memory/agent-research/project_nord_vs_campania_research_2026-03-16.md` (mtime 2026-03-16)
- ref: `.claude/agent-memory/agent-research/project_zona_test_research_2026-03-16.md` (mtime 2026-03-16)
- ref: `docs/dev/ROADMAP.md` (mtime 2026-03-14)
- ref: `.claude/agents/agent-research.md` (mtime 2026-03-14)
- ref: `src/bot/requirements.txt` (mtime 2026-03-13)
- ref: `docs/dev/whatsapp_enterprise_automation_plan.md` (mtime 2026-03-13)
- ref: `docs/dev/SESSION_31_ROADMAP.md` (mtime 2026-03-13)
- ref: `docs/dev/MARIO_ENTERPRISE_ACTION_PLAN.md` (mtime 2026-03-13)
- ref: `docs/dev/DEEP_RESEARCH_CoVe_2026_WHATSAPP_API_INVESTMENT_DECISION.md` (mtime 2026-03-13)
- ref: `docs/dev/DEEP_RESEARCH_CoVe_2026_WAHA_SELF_HOSTED_VALIDATION.md` (mtime 2026-03-13)
- ref: `docs/dev/DEEP_RESEARCH_CoVe_2026_ENTERPRISE_PROJECT_MIGRATION.md` (mtime 2026-03-13)
- ref: `docs/dev/DEEP_RESEARCH_CoVe_2026_ENTERPRISE_FRAMEWORK_ANALYSIS.md` (mtime 2026-03-13)
- ref: `docs/dev/DEEP_RESEARCH_CoVe_2026_DEALER_PIPELINE_AUTOMATION.md` (mtime 2026-03-13)
- ref: `docs/dev/DEEP_RESEARCH_CoVe_2026_CLAUDE_MEM_ENTERPRISE_SOLUTION.md` (mtime 2026-03-13)
- ref: `docs/dev/DEEP_RESEARCH_CLAUDE_MEM_FIX_SESSION40.md` (mtime 2026-03-13)
- ref: `docs/dev/AUTOMOTIVE_DEALER_PERSONALITIES_RESEARCH_COVe_2026.md` (mtime 2026-03-13)
- ref: `tools/gsd/get-shit-done/workflows/research-phase.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/workflows/plan-phase.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/workflows/plan-milestone-gaps.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/workflows/execute-plan.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/templates/roadmap.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/templates/research.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/templates/requirements.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/templates/planner-subagent-prompt.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/references/planning-config.md` (mtime 2026-03-12)
- ref: `tools/gsd/get-shit-done/references/git-planning-commit.md` (mtime 2026-03-12)
- ref: `tools/gsd/commands/gsd/research-phase.md` (mtime 2026-03-12)
- ref: `tools/gsd/commands/gsd/plan-phase.md` (mtime 2026-03-12)
- ref: `tools/gsd/commands/gsd/plan-milestone-gaps.md` (mtime 2026-03-12)
- ref: `tools/gsd/agents/gsd-roadmapper.md` (mtime 2026-03-12)
- ref: `tools/gsd/agents/gsd-research-synthesizer.md` (mtime 2026-03-12)
- ref: `tools/gsd/agents/gsd-project-researcher.md` (mtime 2026-03-12)
- ref: `tools/gsd/agents/gsd-planner.md` (mtime 2026-03-12)
- ref: `tools/gsd/agents/gsd-plan-checker.md` (mtime 2026-03-12)
- ref: `tools/gsd/agents/gsd-phase-researcher.md` (mtime 2026-03-12)

## VARIABILI_PREVISTE
<!-- Cosa puoi controllare/variare durante l'esecuzione. Param scelti consapevolmente. -->
- Brand auto target: BMW / Mercedes / Audi (DE/BE/NL/AT)
- Canale outreach: WA daemon vs LinkedIn vs cold email (default WA, bloccato da C-WA-DUP)
- Volume scouting/settimana (configurabile, default basso pre-revenue)
- Pricing commissione: % o flat (default % su consegna) [DEFERRED:negozia post-prima-vendita]
- Hit dossier per dealer (n. veicoli proposti per outreach)

## STACK_TOOL
<!-- Tecnologia attiva. Una libreria/runtime per riga + versione se vincolante. -->
- Python 3.13
- SQLite (`dealer_network.sqlite` — 18 dealers, 41 market_listings al 2026-05-28)
- CoVe Engine v4 (production stage)
- WA daemon (con bug C-WA-DUP-001 noto)
- argos-proxy (proxies per scraping geo-distribuito)
- Telegram HITL (founder approval workflow)
- LLM routing OpenRouter (free-tier first, hard cap €30/mese)
- Tesseract OCR (Big Sur compat verificata)

## CRITIQUE
- [OPEN] [LUKE] C-SAN-001: sanitizer D-32 over-mask UAT NO-GO 1/5 (S187) + 1/5 ambiguo. Fix non committato. PROVA: src/cove/image_sanitizer.py 1190 righe, 5 .bak files, ultima mod 2026-05-26. Gate: UAT visual 5/5 PASS Luke su sample T7.
- [ADDRESSED] [LUKE] C-WA-DUP-001: dedup single-writer bridge_outbound (memoria s173_dedup_implementation_closed commit 1cdb5e1). PROVA: iMac comm-broker/bridge.sqlite schema 15 col incluso wa_msg_id/sent_ts/approved_ts.
- [OPEN] [CC] C-DB-SPLIT-001: schema split-brain. MacBook dealer_network.sqlite ha `dealers` (18) ma NO `messages`. iMac ~/Documents/app-antigravity-auto/dealer_network.sqlite ha `messages` (81, INBOUND 15/OUTBOUND 66) ma NO `dealers`. Decidere DB autoritativo unico prima outreach reale.
- [OPEN] [CC] C-WA-RESTART-001: argos-wa-daemon 48 restart in 34h (~1/40min), root cause non investigata. PROVA: pm2 list iMac. Rischio anti-ban + perdita session WA.
- [ADDRESSED] [CC] C-DEPLOY-S203: deploy S205 STEP A 2026-05-29 13:50. Rsync sha-verified 3/3 (response-analyzer.py + wa-daemon.js + wa_bridge.py). Migration S203 idempotente applicata bridge.sqlite (action_type col verified). PM2 reload daemon+dashboard, /status connected, log clean (S202 ALTER messages classifier_intent/confidence/raw_payload applied). STEP B smoke 5/5 PASS (test_ambra_5scenarios.py). E2E TEST_FOUNDER fisico Luke = S206 (resta C-E2E-ZERO).
- [OPEN] [CC] C-DB-ENV-001: ARGOS_DB_PATH PM2 env iMac punta a releases/20260527_083951/dealer_network.sqlite (28KB, 0 messages runtime). DB root 389KB con 81 messages history (max 2026-05-16) è disgiunto da daemon. Daemon+dashboard convergono entrambi su releases/ DB → consistenti per E2E, ma storia legacy persa. Finding S205. Consolidamento DB autoritativo unico + history merge prima Day 1 dealer reali.
- [OPEN] [LUKE] C-E2E-ZERO: zero feature provata end-to-end con dealer reale. CoVe gira (2955 rows), WA daemon connected, contract worker /health 200, ma E2E completo scrape→PDF→WA→reply→sign→paid mai chiuso (memoria feedback_e2e_full_test_founder, Day 1 Stile Car BLOCKED).
- [OPEN] [LUKE] C-SCRAPERS-COUNT: CLAUDE.md project dichiara "28 portali", repo ha 3 file `*_scraper.py` (autoscout, mobile_de, generic). Allineare claim a realtà o estendere copertura.
## METRICHE_SOGLIE
<!-- Numeri che dicono "ok" o "rosso". Es: latenza p95 < 500ms, revenue >= €800. -->
- primo €800 commissione dealer

## STATO_FEATURE
<!-- Matrice feature × stato (DONE|WIP|MISSING|BLOCKED|TBD).
     Audit codice-first 2026-05-28T19:00 (CC ARGOS). Stato = runtime verificato, NO doc. -->
- scouting BMW/Mercedes/Audi (CoVe Engine v4): DONE — duckdb cove_results 2955 rows, PROCEED=1046, MAX(analyzed_at)=2026-05-28 17:59. E2E reale = NO.
- WA daemon outreach: WIP — PM2 argos-wa-daemon online uptime 34h, /status connected, daily 0/10. Open: C-WA-RESTART-001 (48 restart/34h).
- sanitizer dossier PDF (D-32): BLOCKED — C-SAN-001 UAT NO-GO 1/5 over-mask.
- dealer_network.sqlite: BLOCKED — C-DB-SPLIT-001 schema split-brain MacBook(dealers=18,listings=41) vs iMac(messages=81, no dealers).
- argos-proxy (contract worker CF): DONE — /health 200, 6 route src/index.ts (create/get/sign/list/send-iban/mark-paid). E2E con dealer reale = NO.
- Telegram HITL: DONE — PM2 argos-tg-bot online 34h, wa-intelligence/telegram-handler.py 758 righe (/approva /modifica /rifiuta /fire /delay /close /status /human).
- LinkedIn automation: MISSING — grep "linkedin" = 0 codice operativo, solo commenti in tools/send_day1_tier1*.py + descrizioni use in generate_luca_ferretti_images.py.
- LLM routing OpenRouter: WIP — env config + reference in response-analyzer.py/templates.py. Nessuna prova log circuit-breaker o spesa <€30 verificabile da codice.
- brand pubblico ARGOS + persona Luca Ferretti: DONE — landing/index.html 200, 5 luca_ferretti_v{1..5}.png + 2 scene (audi_showroom, car_transport).
- contratto commissione pay-on-delivery: WIP — worker routes + landing/contract/{index,sign.js,thank-you} + landing/functions/contract/[token].js + templates jinja IT/EN (offer/negotiation/documents/delivery/payment). E2E reale = NO (S178 verde solo TEST_FOUNDER).
- AMBRA classifier intent (CONTRACT/POSITIVE/NEGATIVE/VEHICLE_REQUEST): WIP — fix P1/P2/P3 commit ab6da39, deploy iMac pending (C-DEPLOY-S203). Stress test post-deploy = NO.
- HITL gate dossier dashboard:8080 (S190+S203 anello #9): WIP — PM2 argos-dashboard online 34h pid 99205, commit ecd677c, deploy iMac pending (C-DEPLOY-S203).
- dedup WA single-writer bridge_outbound (S173): DONE — iMac bridge.sqlite schema 15 col, 6 record. E2E reale = NO.
- 28 scrapers EU portali: MISSING_PARTIAL — claim CLAUDE.md 28 portali, repo ha 3 file *_scraper.py (autoscout, mobile_de, generic) + portal_profiles.py. Vedi C-SCRAPERS-COUNT.
- sales agent WA segmentazione (regione/provincia/città): MISSING — schema dealers ha col region/province/city/archetype/tier ma N=18 troppo basso; nessun runner che filtra+invia per segmento.

## STATO_AUTONOMIA
<!-- Livello di autonomia operativa concesso al motore/CC su questo progetto.
     Es: L0=ask-always, L1=ask-on-write, L2=ask-on-deploy, L3=full-auto. -->
L0=ask-always

## PROSSIMA_AZIONE
<!-- Una sola azione concreta. Quando completata, aggiornare con la successiva. -->
S206 STEP C E2E TEST_FOUNDER fisico Luke: trigger pipeline BMW X1 → HITL approve dashboard:8080 → reply WA POSITIVE/CONTRACT_REQUEST/NEGATIVE → contract sign → mark-paid. Codice S202+S203 LIVE su iMac (S205 STEP A+B verde, gate VERDE). Gate finale: Luke dichiara "pienamente soddisfatto" (memoria feedback_e2e_full_test_founder). Blocca Day 1 Stile Car (T-5gg = 2026-06-03). Dopo: C-SAN-001 UAT visual 5/5 + C-DB-ENV-001 consolidamento DB autoritativo.
