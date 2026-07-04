# HANDOFF — S296 · template dossier v2 — 2026-07-04 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: DOCS-ONLY (code-edit tentato ma RIPRISTINATO a HEAD; netto = 1 doc handoff aggiunto)
- Mandato: cablare template dossier v2 (firma Azzurra, leva anti-frode, certezza A/B/C, banda onesta, data reale)
- Esito: reality-check completo + piano-edit 12-passi consegnato; 0 edit applicati (chiusura a soglia context #7 a metà unità-edit indivisibile, vincolo #6 anti-PARTIAL)

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 3b15421 2026-07-04 19:23 · working-tree dirty: `.claude/NEXT_SESSION_PROMPT.md` (già dirty all'avvio, NON mio — breadcrumb auto)
- commit di questa sessione: 3b15421 "session-close S296: reality-check template dossier v2 + piano-edit (0 edit applicati)"

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md, verbatim — non re-narrare)
| # | Anello | Stato | Tier |
|---|--------|-------|------|
| 1 | invio Day1 WA | UNVERIFIED | full |
| 2 | classifier intent (AMBRA) | VERIFIED | smoke |
| 9A | approve -> send | VERIFIED | smoke |
| 9B | reject -> abort | UNVERIFIED | full |
| 5 | generazione dossier PDF | VERIFIED | smoke |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED | full |
| 8 | contract -> sign_url | BLOCKED | full |
_Rigenerato 2026-07-04T16:49:29Z · sessione auto-20260704T184929Z_

### GATE A DEALER REALE
[A] E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto" = anelli 1/6-7/9B UNVERIFIED · non soddisfatto
[E] trasparenza Azzurra DEPLOYATA produzione (commit 118343b, 2026-06-30) = CHIUSO
[D] base-mercato fidata (scrape esaustivo + geo==IT + experiment-OFF, finding cont3) = NON chiuso (base Serie3 cap-truncated)

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Eseguire i 12 edit di `research/S296_HANDOFF_template_v2.md` su `tools/scripts/pdf_generator_enterprise.py` (backup 1d prima), poi `python3 -c "import ast;ast.parse(open(...).read())"` PASS, poi generare i 3 PDF UNITÀ B su disco.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Decisione Luke su tensione C-GATE-FONTE-001: la certezza A/B/C country-driven (nomi RDW/Car-Pass/Histovec) RIVELA il paese di origine che il dossier pre-pagamento nasconde. Scegliere: (a) certezza solo post-pagamento; (b) pre-pagamento solo classe-regime senza nominare paese/documento. Gli edit certezza/leva vanno applicati dopo la scelta.
- Anello 8 (sign_url firmato da dealer reale) — freeze fisico.

### BACKLOG (differito, NON prerequisito del primo invio)
- Far rispettare `approved_ts` a `/send` stesso (single-writer vero) — gated su autonomia-invio.
- Verificare che on_demand_runner NON salti la generazione se il PDF esiste già (skip-if-exists non riscontrato ma non letto E2E).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Discordanza #3 RISOLTA su disco: la data NON viene riusata. È `datetime.now()` al render (pdf_generator_enterprise.py:1395/1756) + filename ts fresco (2074-2076). Il "01/07 su re-run 03/07" era lo STESSO PDF riaperto, non rigenerato → punto 5 mandato già soddisfatto, nessun fix.
- Discordanza #2: il PDF NON consuma `gate_it_band` (validate_band.py S295, fuori runtime) ma `_it_distribution` da `get_it_distribution` (it_market_price.py:248). `fallback_declared` non è un campo letterale → derivato da `relaxation_level==3 and not no_verdict`.
- `.claude/NEXT_SESSION_PROMPT.md` è breadcrumb auto-rigenerato dall'hook di chiusura: l'handoff ricco vive in `research/S296_HANDOFF_template_v2.md` (durevole) per non essere clobberato.
- Commit locale NON pushato: branch discende da lineage con secret in history (S278/PLAN_FILTER_REPO) → push bloccato finché scrub.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md · research/S296_HANDOFF_template_v2.md (piano-edit 12 passi) · kb/dominio/frode_km_verifica.md (copy leva/matrice certezza) · STATE.md §3 (gate legale/persona)
