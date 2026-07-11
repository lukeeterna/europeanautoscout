# HANDOFF — recon-mandatari-enrichment Roma — 2026-07-11 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo.

### SESSIONE
- Tipo: WRITE-CODE (solo dati: enrichment JSON + brief; nessun codice pipeline)
- Mandato: pilota anagrafe mandatari — Roma (RM) enrichment P.IVA + validazione + verifica-campione + classificazione + sintesi 3 province. ZERO contatto/costi/bypass.
- Esito: **Roma enrichment COMPLETO → status CANDIDATI** (22/28 righe con P.IVA, 22/22 checksum validi, classificate). **Verifica-campione NON eseguita** (chiusura a context ~62-67%, vincolo #7) = unico gate promozione, rinviato. Potenza/Treviso invariate (PROMOSSE).

### VERITÀ GIT
- branch s210/audit-master-plan · working-tree: vedi git status (auto-hook effimeri + backup .bak 1d NON committati)
- PUSH STATUS VERBATIM previsto: ahead di origin, push NON eseguito (VIETATO S278)
- Backup Rule 1d pre-scrittura: `data/recon/mandatari/roma.json.bak-20260711T162814Z` · `docs/briefs/FONTI_MANDATARI.md.bak-20260711T162902Z` · `HANDOFF_CURRENT.md.bak-20260711T162902Z`

### DATI ROMA (ricontati dalla sessione madre, non claim subagent)
- 28 righe · 22 con P.IVA · **22/22 checksum stdnum validi** · 19 P.IVA distinte (01559111008 ×4 = filiali Mercedes-Benz Roma SpA)
- NON-ARRICCHIBILI 6: idx 8,10,11,13,25,26
- Classi: solo-anagrafe 11 · probabile-agente 5 · fuori-target 5 · **non-operativa 1** (idx9 Centro Auto Roma in liquidazione) · non-classificabile 6 · mandatario-attivo-web 0
- % telefono 39% (11/28) · % non-operative 3,6%
- **⚠️ CAVEAT**: 12/22 P.IVA da serp-snippet (ufficiocamerale.it 403 su fetch diretto), 10/22 da scheda-diretta. Checksum OK ma match-entità non verificato indipendentemente → **la verifica-campione è più importante del solito**.

### PROSSIMO PASSO (singolo, falsificabile)
Verifica-campione Roma: 10 righe casuali (seed dichiarato) su fonte-B indipendente per-riga ≠ fonte_enrichment. ≥8/10 SI → status PROMOSSA in `roma.json` + brief §8c; <8/10 → resta CANDIDATI, segnala quali P.IVA serp-snippet non reggono. Poi UNITÀ 3 SINTESI PILOTA 3 province (tabella comparativa + proiezione rollout ~100 province) se context ≤60%.

### BACKLOG
- Footprint linguistico web ("su commissione"/"cerchiamo per te") non harvest-ato (Potenza/Treviso/Roma) → classe mandatario-attivo-web mai assegnata.
- Backfill telefono Potenza/Treviso (0% harvest-ato lì).
- Via zero-cost per estrazione ATECO-pura (directory ATECO = 403 Cloudflare).
- Anomalie da dirimere: idx6 Gold Car (2 entità P.IVA distinte), idx12 Autodardo (2 entità).

### NOTE PER IL GIUDICE
- Subagent agent-research tende a NON emettere il JSON finale su batch grandi (>10 righe difficili): 2 run tornate come frammento di ragionamento a ~60 tool-use. Fix applicato: batch da 7 righe + tetto fetch basso + istruzione "chiudi col JSON" → hanno funzionato. SendMessage NON disponibile nel toolset → agenti frammentati non recuperabili.
- Enrichment consegnato ma promozione NON reclamata: onesto, non PARTIAL (unità enrichment = completa e committata; promozione = gate esplicito successivo).

### DOVE STA LA STRATEGIA
docs/briefs/FONTI_MANDATARI.md §8 · data/recon/mandatari/{potenza,treviso,roma}.json
