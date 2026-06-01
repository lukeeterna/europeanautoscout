# Maturity — combaretrovamiauto-enterprise

- generato: 2026-05-28T11:55:40Z
- path: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- PLAN.md completo: **True**
- OBIETTIVO: scouting on-demand auto per micro-dealer commissione P.IVA forfettaria Italia, commissione su consegna posizione

## FUNZIONA END-TO-END

> Solo STACK_TOOL confermato come segnale INFERRED. `[ADDRESSED]` ESCLUSO da E2E (bug risolto ≠ feature live, leak confermato 2026-05-28). Conferma E2E sempre richiesta a Luke via questions.md.

- [INFERRED] STACK: Python 3.13
- [INFERRED] STACK: SQLite (`dealer_network.sqlite` — 18 dealers, 41 market_listings al 2026-05-28)
- [INFERRED] STACK: CoVe Engine v4 (production stage)
- [INFERRED] STACK: WA daemon (con bug C-WA-DUP-001 noto)
- [INFERRED] STACK: argos-proxy (proxies per scraping geo-distribuito)
- [ASSUMPTION] (cosa gira E2E oggi davvero? — risposta in questions.md)

## BLOCCATO DA

- [VERIFIED:PLAN.md] C-SAN-001: sanitizer PoC dossier PDF non integrato — fix parser regex + test su 5 dossier reali
- [VERIFIED:PLAN.md] C-WA-DUP-001: WA daemon invia N messaggi identici per ogni outbound (memoria feedback_wa_daemon_duplicate_sends). Blocker test reali V5/D-26: nessuna metrica conversion valida finché non risolto. Verify fix PRIMA wave outreach S171+.

## PROSSIMO PASSO CHE SBLOCCA

- [VERIFIED:PLAN.md] Verificare fix bug WA daemon duplicate sends (C-WA-DUP-001) PRIMA di lanciare test reali V5/D-26: daemon invia N messaggi identici per ogni outbound, bloccando ogni metrica conversion.

## CHI DEVE AGIRE

- C-SAN-001: **CC**  <!-- heuristic keyword, conferma se ASSUMPTION -->
- C-WA-DUP-001: **CC**  <!-- heuristic keyword, conferma se ASSUMPTION -->

## DISTANZA DAL PRIMO RISULTATO

- [INFERRED] 2 blocchi `[OPEN]` aperti tra qui e OBIETTIVO.

## DOMANDE APERTE (ASSUMPTION → vedi questions.md)

- FUNZIONA E2E: cosa gira oggi davvero in produzione/staging? (non bug risolti — feature live)
