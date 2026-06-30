# ROADMAP.md — ARGOS · sequenza ufficiale (SoT unico). Aggiornato S292 (integrato MODELLO ARGOS: segmento dati-reali / geografia / anni / iter 8-passi / posizionamento / enablement / PVP canale attivo — vedi blocco S292 in fondo).
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
# DECISIONI FOUNDER S290 (supply + segmento — registrate, NON ridisegnano le fasi; estendono S1/Fase5):
#   - SEGMENTO premium ALLARGATO: da "tedesco (BMW/Mercedes/Audi)" a "PREMIUM EUROPEO" = premium tedesco
#     + Porsche, Volvo, Land Rover, Jaguar. Coerente col fix gap S289b (comparatore di segmento).
#   - SUPPLY PRIVATI: annunci di privati sotto-mercato = canale supply aggiuntivo lato S1.
#   - SUPPLY ASTE GIUDIZIARIE (PVP/astegiudiziarie.it): nuovo canale supply S1 — STATO "PROBE IN CORSO —
#     volume da confermare" (probe S290: stealth+data-path OK; volume premium NON ancora confermato → non confermato).
#
# ============================================================================
# MODELLO ARGOS — INTEGRAZIONE FOUNDER (S292)  [additivo; SUPERSEDED esplicito in fondo al blocco]
# ----------------------------------------------------------------------------
# Riconcilia geografia/stock/anni/segmento/iter/posizionamento col modello deciso dal founder.
# NON ridisegna le fasi S1-S7 né la sequenza [A]..[F]: le ancora al cliente e al prodotto reali.
#
#   GEOGRAFIA: target dealer = TUTTA ITALIA (non solo Sud). [SUPERSEDED "Sud Italia"]
#   TARGET DEALER: micro-dealer <20 auto, family-business proprietario-decisore. ARGOS lo gradua
#     da forfettario a ordinario e lo fidelizza. [SUPERSEDED "stock 30-80"]
#   CLIENTELA FINALE DEL DEALER: altospendente di provincia (professionista/imprenditore);
#     NON collezionista, NON neopatentato.
#
#   SEGMENTO AUTO (derivato da dati reali mercato IT usato/lusso Q1 2026 — ESTENDE e RAFFINA il
#     "premium europeo" S290, che resta valido come ombrello; qui il fuoco data-driven):
#    - TIER A core — SUV premium aspirazionali: Porsche Macan/Cayenne, Range Rover Sport/Velar/Evoque,
#      Audi Q7/Q8, BMW X5, Mercedes GLE/GLC (allestimenti alti). Razionale: Macan = 2° SUV premium
#      usato più cercato IT (domanda usato sproporzionata vs quota nuovo); Range Rover Sport = 1°
#      venduto >100k€; SUV >50% mercato lusso EU. Porsche+Range Rover = alta-domanda-usato + status
#      affluente senza essere trappole-capitale.
#    - TIER B secondario — berline executive: Audi A6, BMW Serie 5, Mercedes Classe E, Porsche Panamera.
#    - ESCLUSI: premium-compatto (A3/Serie1/ClasseA/Q3/A1 = margine sottile, non altospendente);
#      Maserati/esotico (Ferrari/Lambo/McLaren = bassa liquidità, capitale fermo); lusso-BEV
#      (domanda usato marginale, ~8/10 non ricomprano). [SUPERSEDED "supercar incluse"]
#    - FASCIA €25k-90k. ANNI 2018-2023 [SUPERSEDED "2018-2025"]. CARBURANTE diesel/benzina/mild-hybrid (no BEV).
#    - AGGANCIO VALUE-PROP: i Tier-A più liquidi sono tra i più colpiti da frode-km (Range Rover 2°
#      per discrepanze chilometriche, ~3,2%) → scheda-ARGOS verificata + dichiarazione firmata risolve
#      il dolore massimo proprio sul nostro segmento.
#
#   ITER OPERATIVO (8 passi, flusso canonico):
#    1 contatto → 2 scraping profilo dealer (= [S4] DEALER PROFILING) per canale/modo giusto →
#    3 contatto credibile (Azzurra, assistente virtuale di Luca Ferretti + motivazione credibilità) →
#    4 IL DEALER commissiona un veicolo → 5 scheda ARGOS sul veicolo richiesto →
#    6 richiesta automatica foto HD + dati mancanti = scheda completa che nessun altro sistema produce →
#    7 dealer paga la fee → 8 supporto pratiche/importazione/burocrazia → tracking fino all'arrivo in salone.
#    PUNTO CHIAVE: la richiesta nasce DAL dealer DOPO che il contatto è diventato credibile (non outreach alla cieca).
#
#   POSIZIONAMENTO: ARGOS = FACILITATORE (non responsabile dell'auto). Protezione dealer = verifica
#     pre-invio + dichiarazione FIRMATA e specifica del venditore (km/storico/condizioni/regime IVA) →
#     rivalsa diretta sul venditore. Leva = confronto col marketplace (scatola chiusa, km scalati) vs
#     verifica+firma+dati reali PRIMA del pagamento.
#
#   VALORE TRIPLO (supply + ENABLEMENT): 1 TROVA · 2 ABILITA · 3 FORNISCE (+pratiche+trasporto).
#     ENABLEMENT (concretizzato — era il buco): formare il dealer a vendere/relazionarsi con
#     l'altospendente di provincia (diverso dal vendere un'utilitaria) + contenuti gratuiti di
#     fidelizzazione. Primo artefatto: guida "vendere premium a un benestante di provincia".
#     SEQUENZA: l'enablement è layer di RETENTION/differenziazione, si attiva DOPO che il loop-che-
#     chiude-un-affare funziona. NON è prerequisito del primo invio (anti-scope-creep, coerente con
#     ORDINE DI BUILD VINCOLANTE 1→2→3→4→5).
#
#   SUPPLY — CANALI:
#    - Privati sotto-mercato EU (micrositi locali EU, non solo DE). [già S290, qui ribadito]
#    - PVP / ASTE GIUDIZIARIE = canale supply ATTIVO che DEVE FUNZIONARE (decisione founder S292),
#      accanto ai privati-EU. Portale Vendite Pubbliche / aste giudiziarie italiane = supply premium
#      domestico a sconto. [SUPERSEDED il framing "PROBE IN CORSO" come stato terminale: l'intento è
#      canale-attivo; lo STATO IMPLEMENTAZIONE resta però onesto sotto.]
#      STATO IMPLEMENTAZIONE REALE (verità del disco, FASE 0 S292): SOLO-PIANIFICATO. Nessun modulo/
#      scraper PVP o aste è git-tracked (zero file). FASE-0 research (BACKLOG #S273-ASTE) ha concluso
#      NON-FATTIBILE-ORA sul canale-veicoli: astagiudiziaria.com/robots.txt = Disallow:/ ; PVP =
#      token-gated + WAF (browser headless BLOCCATO). Pivot S290→S291: fonte = astegiudiziarie.it,
#      endpoint volume POST webapi.astegiudiziarie.it/api/search/Data IDENTIFICATO ma torna HTTP 500;
#      VOLUME PREMIUM ancora BLOCKED-ON (mai confermato). GAP "deve funzionare" ↔ realtà = il volume
#      che decide il canale non è ancora misurato. L'implementazione del collector PVP/aste, se si
#      procede, è SESSIONE WRITE-CODE separata (questa è DOCS-ONLY): qui si registra solo la strategia
#      e il gap, non si scrive codice.
#
#   DAY-1: sequenza-credibilità (CRED-SEQUENCE / NO-OFFER-DAY1) GIÀ ATTIVA — Azzurra identifica,
#     nomina il veicolo senza prezzo, invita interesse. Veicolo-first RITIRATO. [SUPERSEDED "veicolo-first"]
#
#   SUPERSEDED — LEDGER ESPLICITO (S292):
#     Sud Italia → tutta Italia · stock 30-80 → micro <20 · 2018-2025 → 2018-2023 ·
#     supercar incluse (Ferrari/Lambo/McLaren) → ESCLUSE · veicolo-first → sequenza-credibilità ·
#     PVP "probe" come stato terminale → canale ATTIVO (intento founder) con stato-impl onesto SOLO-PIANIFICATO.
#     + .claude/NORTH_STAR.md e .claude/rules/identity.md marcati SUPERSEDED → puntano a docs/ROADMAP.md (S292).
#
#   NON CAMBIA: gate [A][E][D], sequenza-anelli E2E, ORDINE DI BUILD 1→2→3→4→5, supply privati-EU.
# ============================================================================
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
