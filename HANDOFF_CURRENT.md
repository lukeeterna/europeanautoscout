# HANDOFF — a56a2bd0 — 2026-07-03 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: scrape esaustivo base-mercato IT (BMW Serie 3 / target 330i) per sciogliere Gate [3] — pool affidabile = completezza + purezza geo + experiment-OFF
- Esito: 3 vincoli affidabilità TUTTI PASS (prova grezza); leveling 330i BLOCCATO da bug price-parse nel nuovo script (0/332 priced) → N_L0-L3 non prodotto, banda NON emessa

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 62a1a91 2026-07-03 · working-tree dirty: `.claude/NEXT_SESSION_PROMPT.md` (già dirty all'avvio, breadcrumb auto — NON mio)
- commit di questa sessione: 62a1a91 (script s273cont4_exhaustive_geo.py + evidence/s273cont4_report.txt)

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md, verbatim — non re-narrare)
| # | Anello | Stato |
|---|--------|-------|
| 1 | invio Day1 WA | UNVERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED (smoke) |
| 9A | approve -> send | VERIFIED (smoke) |
| 9B | reject -> abort | UNVERIFIED |
| 5 | generazione dossier PDF | VERIFIED (smoke) |
| 6-7 | approve HITL dossier -> invio PDF dealer | UNVERIFIED |
| 8 | contract -> sign_url | BLOCKED (fatto esterno: firma dealer reale) |

### GATE A DEALER REALE (STATE.md righe 144-145)
[A] fonte affidabile = base-mercato — **NON fidata** (blocco reale) · [E] trasparenza = DEPLOYATA prod 2026-06-30 (commit 118343b, gate CHIUSO) · [D] base-mercato fidata (scrape esaustivo + geo==IT + experiment-OFF) = **PARZIALE**: pool ora completo+puro+experiment-OFF (332 IT) ma banda 330i non emessa per bug parse

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Fixare il price-extraction in `tools/scripts/s273cont4_exhaustive_geo.py` (allineare a `price_of`/tracking.price dei probe s273cont2/3, dove le mediane per-pagina uscivano giuste) → riscrivere fixture geo-pura → `get_it_distribution(target_variant="330i", fuel="petrol", fixture_path=<nuova>)` → leggere N_L0-L3. Fatto terminale: N_L2 330i ≥ 8 SÌ/NO.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Anello 8: sign_url firmato da dealer reale (HITL fisico)

### BACKLOG (differito, NON prerequisito del primo invio)
- Anelli 1 / 9B / 6-7 E2E su TEST_FOUNDER 393314928901

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Il pool base-mercato Serie 3 2019-23 IT è **332 annunci unici** (scrape esaustivo terminato da PAGINA VUOTA reale pag.21), NON ">770" come temuto S273: STATE.md riga 20-23 da aggiornare (era CAP-truncation, ora il vero terminatore è raggiunto).
- Purezza: 384 raw, cc_dist {'IT': 384}, 0 non-IT. Experiment: A/B=False su tutte le 21 pagine. Prova grezza in `evidence/s273cont4_report.txt`.
- Il "NO banda 330i" di oggi NON è scarsità mercato: è un bug di parse-prezzo (0/332 priced nonostante le mediane per-pagina calcolate dal raw). Non dichiarare fallback config-adiacente finché il leveling non gira sul pool vero.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md · STATE.md (Gate [3], righe 20-32 + 144-145) · evidence/s273cont4_report.txt · memoria s293_scrape_esaustivo_geopuro_serie3.md
