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
- ultimo_update: 2026-06-01T13:00:00Z  <!-- S212 riconciliazione delta PLAN↔ARGOS_MASTER (A+B+E), no codice gating -->

- modalità_ingaggio: adopt  <!-- adopt | create | greenfield -->

## OBIETTIVO
<!-- Una frase netta. Cosa deve produrre il progetto, per chi, in che orizzonte. -->
scouting on-demand auto per micro-dealer commissione P.IVA forfettaria Italia, commissione su consegna posizione. Agent (AMBRA) comunica in modo nativo al target: lessico/tono/timing tarati su come parlano i micro-dealer reali per regione/provincia/città, lungo l'intero funnel (cold → credibilità/relazione → proposta), usando KB mercato auto + conoscenza tecnica + psicologia conversione. Approccio cold UNICO definito da dati intel, non da assunzione founder.

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
- Pricing commissione: STARTUP €400 flat → SCALING a salire (€800+) su consegna posizione [VERIFIED:Luke S212]. Negozia upward post-traction.
- Hit dossier per dealer (n. veicoli proposti per outreach)
- Registro/tono AMBRA per fase funnel (cold / relazione / proposta) — derivato da KB intel target
- Geo-tier comunicativo: regione → provincia → città (lessico, dialettalismi, formalità) — derivato da KB intel

## STACK_TOOL
<!-- Tecnologia attiva. Una libreria/runtime per riga + versione se vincolante. -->
- Python 3.13
- SQLite (`dealer_network.sqlite` — 18 dealers, 41 market_listings al 2026-05-28)
- CoVe Engine v4 (production stage)
- WA daemon (con bug C-WA-DUP-001 noto)
- argos-proxy (proxies per scraping geo-distribuito) — NOTA S210: AS24 mercato DE raggiungibile da IP IT via param `cy=D` (non `source=DE`, verificato autoscout_scraper.py:472) → valutare ridondanza/0-cost del proxy
- Telegram HITL (founder approval workflow)
- LLM routing OpenRouter (free-tier first, hard cap €30/mese)
- Tesseract OCR (Big Sur compat verificata)

## CRITIQUE
- [OPEN] [LUKE] C-SAN-001: sanitizer D-32 over-mask UAT NO-GO 1/5 (S187) + 1/5 ambiguo. Fix non committato. PROVA: src/cove/image_sanitizer.py 1190 righe, 5 .bak files, ultima mod 2026-05-26. Gate: UAT visual 5/5 PASS Luke su sample T7. NOTA S210: detection-targa via Vision RIMOSSA (S183 s183_autogen_zones.py:94-99), sostituita da mascheratura cieca fascia bassa ~12% → niente falso-positivo watermark MA nessun vero plate-detector (strato fragile: targa fuori fascia bassa = non coperta). Il sanitizer è il **2° strato** di protezione-fonte; il **1° strato** è il gating pagamento→rilascio-fonte (C-GATE-FONTE-001). Due metà della stessa serratura.
- [ADDRESSED] [LUKE] C-WA-DUP-001: dedup single-writer bridge_outbound (memoria s173_dedup_implementation_closed commit 1cdb5e1). PROVA: iMac comm-broker/bridge.sqlite schema 15 col incluso wa_msg_id/sent_ts/approved_ts.
- [OPEN] [CC] C-DB-SPLIT-001: schema split-brain. MacBook dealer_network.sqlite ha `dealers` (18) ma NO `messages`. iMac ~/Documents/app-antigravity-auto/dealer_network.sqlite ha `messages` (81, INBOUND 15/OUTBOUND 66) ma NO `dealers`. Decidere DB autoritativo unico prima outreach reale.
- [OPEN] [CC] C-WA-RESTART-001: argos-wa-daemon 48 restart in 34h (~1/40min), root cause non investigata. PROVA: pm2 list iMac. Rischio anti-ban + perdita session WA.
- [ADDRESSED] [CC] C-DEPLOY-S203: deploy S205 STEP A 2026-05-29 13:50. Rsync sha-verified 3/3 (response-analyzer.py + wa-daemon.js + wa_bridge.py). Migration S203 idempotente applicata bridge.sqlite (action_type col verified). PM2 reload daemon+dashboard, /status connected, log clean (S202 ALTER messages classifier_intent/confidence/raw_payload applied). STEP B smoke 5/5 PASS (test_ambra_5scenarios.py). E2E TEST_FOUNDER fisico Luke = S206 (resta C-E2E-ZERO).
- [OPEN] [CC] C-DB-ENV-001: ARGOS_DB_PATH PM2 env iMac punta a releases/20260527_083951/dealer_network.sqlite (28KB, 0 messages runtime). DB root 389KB con 81 messages history (max 2026-05-16) è disgiunto da daemon. Daemon+dashboard convergono entrambi su releases/ DB → consistenti per E2E, ma storia legacy persa. Finding S205. Consolidamento DB autoritativo unico + history merge prima Day 1 dealer reali.
- [OPEN] [LUKE] C-E2E-ZERO: zero feature provata end-to-end con dealer reale. CoVe gira (2955 rows), WA daemon connected, contract worker /health 200, ma E2E completo scrape→PDF→WA→reply→sign→paid mai chiuso (memoria feedback_e2e_full_test_founder, Day 1 Stile Car BLOCKED).
- [OPEN] [LUKE] C-SCRAPERS-COUNT: CLAUDE.md project dichiara "28 portali", repo ha 3 file `*_scraper.py` (autoscout, mobile_de, generic). Allineare claim a realtà o estendere copertura.
- [OPEN] [LUKE] C-COMM-INTEL-001: approccio cold + funnel comunicativo AMBRA NON definito da dati. Regole project si contraddicono (communication.md riga "PRIMO CONTENUTO = veicolo REALE" vs sequenza credibilità Sud "chi sei → chi ti ha mandato → cosa hai fatto → cosa offri" vs send_day1_tier1.py "ZERO veicoli Day 1"). MISSING intel-STILE (pattern lessicali pubblici, GDPR-low) + intel-LEAD (anagrafica segmentata, GDPR-high) + KB-mercato-auto (leva credibilità proposta). Vincoli verifiche: (a) precedenti USA Meta v Bright Data ritirata feb 2024 + X v Bright Data mag 2024 = scraping logged-off di dati PUBBLICI legalmente difendibile su base contratto/ToS USA, NON copre GDPR (regime UE governa il TRATTAMENTO dato personale a prescindere dai Terms); (b) ostacolo FB/IG = TECNICO (anti-bot aggressivo), non legale; (c) vincolo vero Luke = GDPR su intel-LEAD (legittimo interesse B2B + minimizzazione + opt-out), non blocco su intel-STILE pattern aggregati. AMBRA oggi compone su template generici → conversione attesa bassa. GATE: build intel-STILE + KB-mercato-auto + tarare AMBRA per fase (cold/relazione/proposta) PRIMA di TEST_FOUNDER cold reale (vincolo Luke S206 2026-05-29). intel-LEAD attesa nota legale.
- [OPEN] [LUKE] C-COMM-CONFLICT-001: deprecare riga "PRIMO CONTENUTO = veicolo REALE con numeri REALI" in .claude/rules/communication.md (conflitto con sequenza credibilità nello stesso file + con send_day1_tier1.py V3). Risolvere dopo C-COMM-INTEL-001 (l'intel decide l'approccio, non assunzione founder).
- [OPEN] [LUKE] C-GATE-FONTE-001: gating pagamento→rilascio-fonte INESISTENTE in codice (solo commento image_sanitizer.py:13 "source revealed ONLY after fee payment"). È il nodo che "protegge il ricavo" (MASTER priorità #1) ed è il pezzo più scoperto. PROVA: payment_handler.py mark_paid() (:251, DuckDB fee_invoices) e deal_state_machine.py confirm_payment (:92, SQLite deals.sqlite) NON si parlano (DB disgiunti), nessun campo source_locked (solo metadata_json free-form :35), secretazione attuale = redazione PASSIVA (source_url='' VehicleData.from_opportunity :164). CAVEAT: garanzia parziale finché C-SAN-001 BLOCKED (gating-fonte + sanitizer = due metà stessa serratura). Implementazione = **S213** (design concordato: innesto state machine + 2° PDF gated su transizione confirm_payment + conferma manuale Luke via G-APPROVAL CLI + source in metadata_json.source_locked). NO codice in S212.
- [OPEN] [CC] C-IDENTITY-RESIDUE-001: .claude/rules/identity.md dichiara target "30-80 auto" (PRE-PIVOT) in conflitto con target validato stock <20 (GUARDRAIL + TARGET_VALIDATO). Correggere identity.md → micro-dealer stock <20. (Fuori scope documentale S212: edit file rules richiede sessione dedicata.)
- [OPEN] [CC] C-MASTER-SYNC-001: 4 dettagli operativi vivono SOLO nel PLAN e vanno backportati nel MASTER (ARGOS_MASTER, sessione separata sul master): (1) CoVe 2955 run/1046 PROCEED, (2) split-brain DB MacBook↔iMac (C-DB-SPLIT/ENV), (3) daemon 48 restart/34h (C-WA-RESTART), (4) footprint GDPR intel-STILE basso / intel-LEAD alto (C-COMM-INTEL). NO edit master in S212.
## METRICHE_SOGLIE
<!-- Numeri che dicono "ok" o "rosso". Es: latenza p95 < 500ms, revenue >= €800. -->
- primo €400 commissione dealer (STARTUP); a salire (€800+) in fase SCALING [Luke S212]
- GATE-CAMPO: conversione validata su campione N dealer reali prima di dichiarare sales-agent / AMBRA funnel-aware DONE (oggi 0 dealer reali contattati → NON validato, vedi C-E2E-ZERO)

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
- sales agent WA segmentazione (regione/provincia/città): MISSING — schema dealers ha col region/province/city/archetype/tier ma N=18 troppo basso; nessun runner che filtra+invia per segmento. NOTA S210: il MASTER lo inquadra OUTBOUND autonomo + KB pre-addestrata; realtà = REATTIVO + HITL Telegram obbligatorio (response-analyzer.py:13-17), n8n ASSENTE. "Outbound autonomo" = TARGET, non stato. Gate prima di DONE = GATE-CAMPO (vedi METRICHE_SOGLIE).
- gating pagamento→rilascio-fonte: MISSING — leva primaria del modello (fonte secretata sbloccata SOLO a pagamento confermato) NON esiste come codice. mark_paid() (payment_handler.py:251, DuckDB) chiude dealer_leads ma non rilascia alcun campo sorgente; confirm_payment (deal_state_machine.py:92, SQLite) avanza stato ma nessun hook rilascia URL; i due DB sono disgiunti, nessun campo source_locked. Secretazione attuale = redazione PASSIVA (source_url='' :164), NON gate. Implementazione S213. Vedi C-GATE-FONTE-001.
- intel-STILE: MISSING — pattern lessicali/tono dealer target da fonti pubbliche (Google Business reviews, TG canali pubblici, post FB/IG pubblici logged-off). Output: `intel/lexicon.jsonl` (pattern, NON identità). Footprint GDPR: basso (no dato personale memorizzato, solo signatures/n-gram). Prerequisito C-COMM-INTEL-001.
- intel-LEAD: MISSING — anagrafica dealer segmentata regione/prov/città. Footprint GDPR: ALTO → richiede base "legittimo interesse" B2B documentata + minimizzazione + opt-out + DPIA-light. NON avviare senza nota legale (legal-compliance-checker). Prerequisito C-COMM-INTEL-001.
- KB-mercato-auto: MISSING — corpus dominio (prezzi/tempi/margini import EU→IT, obiezioni tipiche, terminologia settore, optional cruciali per modello) come LEVA di credibilità AMBRA in fase proposta. Fa suonare AMBRA "del mestiere". Retrieval semplice (`kb/auto_market.jsonl` + grep, NO vector db — vincolo anti-over-engineering). Sorgenti: research/s73* + .claude/agent-memory/ + memorie esistenti, consolidamento. NOTA S210: corpus_register.md (s206) NON usabile come fonte — 223 frammenti-dotazioni AS24 troncati (es. "forgiati M doppi raggi st"), AS24-only, non linguaggio-dealer conversazionale.
- AMBRA funnel-aware (cold / relazione-credibilità / proposta con tono diverso): MISSING — prompt modules esistenti (vehicle_request_broker S175.1) coprono solo VEHICLE_REQUEST reactive, non phase-aware outbound. Consumerà intel-STILE (tono geo-tier) + KB-mercato-auto (credibilità proposta).

## STATO_AUTONOMIA
<!-- Livello di autonomia operativa concesso al motore/CC su questo progetto.
     Es: L0=ask-always, L1=ask-on-write, L2=ask-on-deploy, L3=full-auto. -->
L0=ask-always

## PROSSIMA_AZIONE
<!-- Una sola azione concreta. Quando completata, aggiornare con la successiva. -->
S206 PIVOT (Luke 2026-05-29): risolvere C-COMM-INTEL-001 PRIMA di STEP C cold reale TEST_FOUNDER. Fasi sequenziali:
(1) DEFINIRE perimetro intel: micro-dealer target stock <20 P.IVA forfettaria — fonti TG canali/gruppi auto, FB pagine business, IG profili, Google Business + recensioni — scope geo: tutta Italia con tier regione/provincia/città. Time-box build: 1 sessione decisionale + 2-3 sessioni harvest.
(2) HARVEST: estrarre testi pubblici (post, bio, recensioni, risposte) da N≥30 micro-dealer rappresentativi (selezione stratificata per macro-area Nord/Centro/Sud + ≥3 città per area) — output `intel/micro_dealer_communication_corpus.jsonl` con campi {dealer, geo, source, text, timestamp, archetype_guess}.
(3) ANALISI lessico: top-N termini ricorrenti, formule apertura/chiusura, registro (formale/colloquiale/dialettale), tabù lessicali, time-of-day risposta — output `intel/communication_patterns.md` per regione/provincia.
(4) BUILD KB mercato auto: consolidare research/s73* + .claude/agent-memory in `kb/auto_market/` strutturato (modelli, anni, optional cruciali, prezzi reference, margini tipici, obiezioni dealer, contro-argomenti).
(5) AMBRA funnel-aware: prompt modules separati per phase=cold | phase=relationship | phase=proposal, ognuno consumando lessico geo-tier + KB auto via retrieval semplice (no rewrite stack).
(6) DEPRECARE riga conflittuale communication.md, scrivere policy unica derivata da dati intel.
(7) TEST E2E TEST_FOUNDER cold con messaggio composto da AMBRA funnel-aware (NON template hardcoded) → HITL → reply → relazione → dossier → contract → paid. Gate finale: Luke "pienamente soddisfatto".
Blocca Day 1 Stile Car (T-5gg = 2026-06-03) — possibile slittamento target, decisione Luke. Dopo: C-SAN-001 UAT visual 5/5 + C-DB-ENV-001 consolidamento DB autoritativo + C-SCRAPERS-COUNT allineamento claim 28 portali + **S213 C-GATE-FONTE-001 implementazione gating** (state machine + 2° PDF gated su confirm_payment + conferma manuale Luke via G-APPROVAL CLI + source in metadata_json.source_locked).
