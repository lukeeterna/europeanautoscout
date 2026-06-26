# ROADMAP.md — ARGOS · sequenza ufficiale (SoT unico). Aggiornato S286 (integrata architettura E2E 5-fasi).
#
# GATE-0 — SICUREZZA (CORRETTO S280, verificato vs git/S279 — NON "ruota 3 token"):
#   - OpenRouter sk-or-v1-…2f13 = UNICO da ruotare (azione Luke, in corso).
#   - GitHub PAT ghp_zgws… = MORTO (Expired 2026-05-11) + valore intero NON in history → NESSUNA azione.
#     gh CLI gira con token gho_ OAuth separato (keyring); i PAT classici non si creano via API/CLI.
#   - bot Telegram @Argosautomotivebot = già rigenerato+verificato vivo (getMe OK, S279) → NON ruotare,
#     solo APPLICARE su iMac: ~/argos_new_bot_token_S280.txt → current/wa-intelligence/.env
#     ARGOS_TELEGRAM_TOKEN, restart daemon tg, getMe, cancellare scratch. (shared-state: finestra pulita.)
#   Push bloccato NON e' il rischio; scrub history = item [F] (igiene separata, non rotazione).
#
# STATO (verificato): motore/dossier onesto chiuso (S271, banda/margine-intervallo/no-superlativi).
#   Trasparenza Azzurra chiusa IN-REPO a tutti i layer (S277), NON in produzione (manca sync.sh).
#   Anelli E2E: 2/9A/5 VERIFIED-smoke · 1/9B/6-7 UNVERIFIED · 8 BLOCKED(esterno).
#
# SEQUENZA (ordine vincolante; ogni item → il suo brief in docs/briefs/):
#   [A] E2E 6-7 su TEST_FOUNDER 393314928901   → docs/briefs/BRIEF_A_e2e_67_testfounder.md
#       PREREQ (scoperto S280): WA daemon = initializing/qr_available:false = client NON connesso.
#       [A] NON parte finche': (i) daemon initializing->connected (area S252: QR re-scan, Luke fisico
#       sulla SIM), (ii) orario lavorativo (anti-ban gate-a fuori orario). → SPLIT:
#         [A0] wa-daemon-ops: connetti il daemon (PRECEDE [A1]).
#         [A1] E2E 6-7: CHIUSO S286 (7a meccanica d'invio VERDE commit 40a5d1e msg_id out_1781986351333_evd8h
#              + 7b breaker DEFERITO a gate-pre-dealer-reale, già nei 3 gate). Done-condition = CHECKLIST BRIEF_A.
#              NB: anello 6-7 nella tabella GENERATA resta UNVERIFIED (check_cmd=null, consegna WA non re-runnabile
#              in-sessione + 7b deferito) — [A1] item chiuso ≠ ring flip. [S4] è ora l'item attivo corrente.
#       FB-GROUPS SOURCING (modulo opzionale isolato): repo = MasuRii/FBScrapeIdeas (selenium, login OBBLIG.,
#         data/research/repo_selection.md). PREREQ fetch-test: account FB TEST sacrificabile (cookie c_user+xs
#         in .env). Senza account-test il modulo NON parte; AS24+sintesi girano lo stesso.
#   [S4] DEALER PROFILING (NUOVO · Fase 1 architettura E2E) — primo item attivo dopo [A1].
#        Layer mancante (causa "outreach alla cieca"); leva max conversione, costo min (riusa scraper AS24).
#        Done-condition = sez.6 di docs/ARCHITETTURA_E2E.md. Mappa 5-fasi completa nel blocco in fondo.
#        S289: gap_analysis RELATIVO FATTO (commit 7f10e2a, tabella dealer_gaps + CLI `gap`, idempotente,
#          GDPR-clean). Evidenza rossettomotors-srl: tedesco-premium 10/28=35.71% vs leader BMW 28.57%.
#        PROSSIMA IMPL IDEMPOTENTE (S290, non speculativa): raffina il COMPARATORE. Oggi = brand-leader
#          singolo → circolare quando il leader e' in-segmento (BMW e' german-premium), under_weight quasi
#          mai true. Fix = comparatore vs AGGREGATO non-segmento (share segmento vs share resto-mix), stesso
#          denominatore. VALUTAZIONE FINALE PRE-IMPL: usa SOLO dati gia' in data/dealers.db (inventory_snapshot),
#          nessuna sorgente nuova, re-run idempotente su PK dealer_id; il numero relativo 35.71% resta valido,
#          cambia solo il flag derivato. Il confronto "vs supply ARGOS" NON ora: la tabella supply non esiste
#          ancora = dipendenza, non questo item. Poi estendi generate_cold_day1 (templates.py:273) col gap osservato.
#   [B] TOOL-RESEARCH → KB voce AMBRA          → docs/briefs/BRIEF_B_research_tool.md   (alimenta [A])
#       [= sottoinsieme "voce" della Fase 3: la SECTOR WIKI (S5) ESTENDE [B]. Vedi blocco ARCHITETTURA E2E.]
#   [C] MONITOR FONTI SOURCING B2B (weekly)    → docs/briefs/BRIEF_C_sourcing_monitor.md
#       [= seed della Fase 5 (S1 breadth 28 canali + S2 gap-filling). La Fase 5 ESTENDE [C]. Vedi blocco sotto.]
#   [D] BASE-MERCATO FIDATA (gate-3 dossier reale): scrape DEEP_PAGES≥80 fino a pagina-vuota,
#       experiment-OFF, geo==IT su location.countryCode + ADD-1 (config-esatta thin o artefatto del cap? min_n=8 regge?).
#       [= Fase 2 architettura E2E (S3 Pricing/Gate D). COLLEGATO, non duplicato: la Fase 2 È questo item [D].]
#   [E] DEPLOY trasparenza in PRODUZIONE: sync.sh (pre-flight symlink wa-sender/, memoria S252). Dopo [A] verde.
#   [F] filter-repo: bonifica history (rotazione gia' in GATE-0). Sessione dedicata. Sblocca push.
#
# SCHEDULING SESSIONI (disciplina shared-state, S279/S280): mutazione sostanziosa + finale-verificato NON
#   convivono a context saturo. Allocazione:
#     S281 = AZIONE 1 (apply 2 chiavi su iMac .env + 1 restart daemon + getMe/probe) + AZIONE 2 (checklist
#            verde gia' in BRIEF_A). Chiudi a 60%.
#     [A0]+[A1] = SESSIONE DEDICATA, orario lavorativo, budget PIENO (l'anello E2E 6-7 che manca da settimane
#            non va aperto a budget gia' speso = rischio PARTIAL su anello critico). Precond: daemon connesso.
#
# BACKLOG (gated, FUORI sequenza): ITEM-ASTE-GIUDIZIARIE (canale sourcing #2, post primo-dealer-reale) → BACKLOG.md.
#
# 3 GATE A INVIO DEALER REALE (tecnici): [A] verde + Luke soddisfatto · [E] trasparenza live · [D] base-mercato fidata.
# NB LEGALE (non "gate sparito"): il rischio GDPR del cold-WA e' NOTO e ACCETTATO da Luke (canale deciso-finale,
#   autorita' su irreversibile), MITIGATO dalla copy con provenienza-contatto + opt-out. Difendibilita' = artefatto
#   lungo il percorso (balancing test legittimo-interesse documentato, S249), NON un re-gate. Rischio accettato ≠ inesistente.
#
# ============================================================================
# ARCHITETTURA E2E — 5 FASI DI BUILD  (blueprint: docs/ARCHITETTURA_E2E.md · integrato S286)
# ----------------------------------------------------------------------------
# Mappa per-DIPENDENZA sui 7 sottosistemi S1-S7. NON sostituisce la SEQUENZA [A]..[F] sopra:
# la ESTENDE con 2 NUOVI item (S4, S6) e COLLEGA gli esistenti. Nessun item rimosso.
#   FASE 1 = [S4] DEALER PROFILING (NUOVO) — primo item attivo dopo [A1]. Intelligence commerciale
#            pre-outreach; leva max conversione, costo min (riusa scraper AS24). Done-condition: sez.6 blueprint.
#   FASE 2 = item [D] BASE-MERCATO FIDATA (S3 Pricing/Gate D). COLLEGA, non duplica.
#   FASE 3 = ESTENDE item [B]: [B] e' il sottoinsieme "voce" (tool-research -> KB); la Fase 3 lo amplia a
#            SECTOR WIKI (S5: margini premium, gergo, obiezioni+risposte, fiscalita' reverse-charge/IPT). [B] NON cancellato.
#   FASE 4 = [S6] MATCHING (NUOVO): dealer-profilo x supply-verificato. Dipende da S1(supply)+S4(profili).
#   FASE 5 = ESTENDE item [C] (seed monitor fonti): S1 breadth 28 canali + S2 gap-filling agent.
#            DECISIONE APERTA (NON risolta qui): build-vs-buy aggregatori (scraper core proprietari vs API di coda).
#
# ORDINE DI BUILD VINCOLANTE: 1 -> 2 -> 3 -> 4 -> 5 (dipendenza, NON preferenza). Loop-che-chiude-UN-affare
#   prima, breadth dopo. Riordinare = rischio #1 documentato (macchina rifinita che non spedisce). NON riordinare.
# ============================================================================
