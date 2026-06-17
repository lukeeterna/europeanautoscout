# ROADMAP.md — ARGOS · sequenza ufficiale (SoT unico). Aggiornato S280.
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
#   [B] TOOL-RESEARCH → KB voce AMBRA          → docs/briefs/BRIEF_B_research_tool.md   (alimenta [A])
#   [C] MONITOR FONTI SOURCING B2B (weekly)    → docs/briefs/BRIEF_C_sourcing_monitor.md
#   [D] BASE-MERCATO FIDATA (gate-3 dossier reale): scrape DEEP_PAGES≥80 fino a pagina-vuota,
#       experiment-OFF, geo==IT su location.countryCode + ADD-1 (config-esatta thin o artefatto del cap? min_n=8 regge?).
#   [E] DEPLOY trasparenza in PRODUZIONE: sync.sh (pre-flight symlink wa-sender/, memoria S252). Dopo [A] verde.
#   [F] filter-repo: bonifica history (rotazione gia' in GATE-0). Sessione dedicata. Sblocca push.
#
# BACKLOG (gated, FUORI sequenza): ITEM-ASTE-GIUDIZIARIE (canale sourcing #2, post primo-dealer-reale) → BACKLOG.md.
#
# 3 GATE A INVIO DEALER REALE (tutti tecnici): [A] verde + Luke soddisfatto · [E] trasparenza live · [D] base-mercato fidata.
