# HANDOFF ARGOS — S204 audit codice-first → S205 recovery

> Aggiornato 2026-05-28 18:05 (S204 close).
> Sessione precedente ha eseguito audit codice-first ignorando PLAN/HANDOFF/DECISIONS.
> Memory: `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s204_verita_codice_audit_2026-05-28.md`.
>
> Il vecchio contenuto di questo HANDOFF (C-WA-DUP-001 + C-SAN-001 da VOS PLAN root) è superato:
> WA dup chiuso S173/S173b (commit 1cdb5e1), sanitizer è il blocker reale Day 1.

## Stato verificato S204 (eseguito, non letto)

| Componente | Stato | Prova |
|---|---|---|
| CoVe Engine v4 | VERDE | smoke `BMW Serie 3 2021 €24500` → `PROCEED 0.779` |
| AMBRA classifier | VERDE | `python3 tools/test_ambra_5scenarios.py` → 5/5 PASS |
| PM2 iMac | VERDE | 4/4 online, uptime 33h |
| wa-daemon | inattivo | `daily_sent=0/10`, ultimo msg 2026-05-16 |
| Worker `argos-proxy` + landing | VERDE | HTTP 200, D1 `argos-contracts` UUID `75d63bc9-…` |
| Sanitizer immagini | GIALLO | wired subprocess `pdf_generator_enterprise.py:1635`, UAT S187 NO-GO non rivalidato |
| CONTRACT_REQUEST reactive su TEST_FOUNDER 2026-05-16 | NON VERIFICATO | servirebbe query D1 + iMac messages |

## Discrepanze doc ↔ codice (TRUST CODE)

- Schema `cove.Listing` reale = `listing_id, make, model, year, km, price, vin, source, scraped_at, market_price_ref`. NON quello dei doc s157.
- DB iMac autoritativo = `~/Documents/app-antigravity-auto/dealer_network.sqlite` (no tabella `dealers`).
- `bridge_outbound` ha colonna `action_type` (S203 migration applicata).

## Prossima sessione — S205

Apri: `cd ~/Documents/combaretrovamiauto-enterprise && claude` poi leggi `prompts/s205_codice_first_recovery.md`.

5 step (~2h totali):

1. Pre-flight CoVe + AMBRA + PM2 (15min)
2. Verifica TEST_FOUNDER contract end-to-end via D1 (30min) — CC tecnico
3. Identificare DB sorgente outreach (gap tabella `dealers`) (15min) — CC tecnico
4. Sanitizer UAT 5 sample reali (30-45min) — CC tecnico
5. Micro-patch NEGATIVE → opt_out=1 (15min) — CC tecnico
6. Decisione Day 1 reale vs replay — Luke

Day 1 Stile Car deadline 2026-06-03 (T-6gg).
Domenica 2026-05-31 OFF.
