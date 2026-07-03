# HANDOFF — S294 — 2026-07-04 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: fix price-extraction path cont4 per sbloccare leveling 330i (Gate [3]).
- Esito: causa reale trovata (NON price-parse) + fix applicato compile-verified; banda NON producibile — pool raw 332 mai persistito su disco.

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 2c5ad90 2026-07-03 · working-tree dirty
- commit di questa sessione: <s273cont4 fix — hash da commit close>
- dirty NON mio (hook refresh, non committato): .claude/NEXT_SESSION_PROMPT.md, STATE.md, state/rings.json

### DIAGNOSI VERIFICATA
- `price_of` è identico tra probe (cont2/cont3, mediane 30-37k OK) e cont4: NON è un bug prezzo.
- 0/332 causato da `raw_to_listing` (s273cont4_exhaustive_geo.py) che chiamava `scraper._parse_next_data_listing` INESISTENTE (reale: `_next_data_item_to_listing`, autoscout_scraper.py:799) → AttributeError → fallback rotto che non setta `power_hp` (→ 330i 258CV vuota a L0 anche col prezzo giusto).
- Prova: evidence/s273cont4_report.txt:14-33 med_IT OK per-pagina, :55 "post-parse: 0 (parse fail: 332)".

### FIX APPLICATO (tools/scripts/s273cont4_exhaustive_geo.py, compile OK)
1. `raw_to_listing` → parser canonico `_next_data_item_to_listing` (produzione S157). NON E2E-verificato (serve re-scrape).
2. Root-cause: script ora salva pool RAW (`tests/fixtures/it_dist_bmw_serie3_2021_s273cont4_RAW.json`) subito dopo scrape.
3. CoVe/scoring NON toccati (Rule 1d).

### STATO E2E (da startup hook / STATE.md)
1 UNVERIFIED · 2 VERIFIED · 5 VERIFIED · 6-7 UNVERIFIED · 8 BLOCKED · 9A VERIFIED · 9B UNVERIFIED

### GATE A DEALER REALE
[A] base-mercato 330i affidabile = NO (banda non emessa, blocked su pool) · [E] E2E 6-7 su TEST_FOUNDER = UNVERIFIED · [D] Luke "pienamente soddisfatto" = NO

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Se Luke autorizza: `python3 -m tools.scripts.s273cont4_exhaustive_geo` (~5 min, geo-puro) → verificare n_priced ≈332 → emettere banda 330i p25-p75 o dichiarare fallback config-adiacente se N<soglia.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Pool raw 332 NON su disco (git 62a1a91 committò solo il report) → banda 330i richiede 1 re-scrape autorizzato da Luke. Mandato lo vietava su premessa falsa ("pool committato").

### BACKLOG (differito, NON prerequisito del primo invio)
- nessuno nuovo

### NOTE PER IL GIUDICE
- Discordanza disco vs mandato: il mandato assume "332 GIÀ scrapati dal pool committato" — quel pool NON esiste. Solo evidence/s273cont4_report.txt fu committato. Fix #2 impedisce la ricaduta.
- Il fix cambia più del solo prezzo (anche power_hp/variant): NECESSARIO, altrimenti 330i vuota a L0 per power_hp=0, non per scarsità di mercato (sarebbe stato falso-NO).

### DOVE STA LA STRATEGIA (puntatori)
docs/ROADMAP.md (S292 fonte autoritativa segmento/geo) · .claude/rules/cove.md · MEMORY.md s273_fixture_truncated_cap
