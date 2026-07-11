# HANDOFF — recon-mandatari-enrichment — 2026-07-10 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE (dati: enrichment JSON + brief; nessun codice pipeline toccato)
- Mandato: promozione lista mandatari da candidati ad anagrafe — enrichment P.IVA (fonti gratuite), validazione checksum, verifica-campione, classificazione. Ordine province: Potenza → Treviso → Roma. ZERO contatto, ZERO costi, ZERO bypass.
- Esito: **Treviso COMPLETA e PROMOSSA** (34/40 righe con P.IVA, 34/34 checksum valide, campione 10/10 SI, seed=71). Potenza già PROMOSSA (invariata). Roma NON iniziata (chiusura a context ~59% dopo Treviso, unità atomica = provincia, nessun PARTIAL).

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD d8686be 2026-07-10 · working-tree dirty (NON miei: STATE.md + state/rings.json + .claude/NEXT_SESSION_PROMPT*.md = auto-hook; data/pool_icp/_backup_reapply_20260708T171250Z/ = pre-esistente)
- commit di questa sessione: d8686be "recon-mandatari UNITA' 1+2 Potenza: enrichment P.IVA + verifica-campione → PROMOSSA"
- PUSH STATUS VERBATIM: `## s210/audit-master-plan...origin/s210/audit-master-plan [ahead 229]` · push NON eseguito (VIETATO S278)
- Backup Rule 1d pre-scrittura potenza.json: `data/recon/mandatari/potenza.json.bak-20260710T205817Z` (9667B, mtime precedente all'edit)

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (OUTPUT VERBATIM da `state/rings.json` last_status — non re-narrare)
| # | last_status |
|---|-------------|
| 1 | UNVERIFIED |
| 2 | PASS |
| 9A | PASS |
| 9B | UNVERIFIED |
| 5 | PASS |
| 6-7 | UNVERIFIED |
| 8 | BLOCKED |
| BM | PASS |

### GATE A DEALER REALE (OUTPUT VERBATIM — non re-narrare)
[A] = APERTO/BLOCKED-ON — E2E TEST_FOUNDER mai eseguito (anelli 1/6-7/9B UNVERIFIED); glue Day-1→queue_outbound(phase='DAY1') inesistente · [E] trasparenza deployata = CHIUSO ('Azzurra', 118343b) · [D] base-mercato = VERIFIED

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
UNITÀ 1+2 su **Roma (RM)** (28 righe, 0 con P.IVA): stesso protocollo Treviso — enrichment P.IVA per-nome via subagent research (schede ufficiocamerale.it/<id>/<slug> + reportaziende/bilancioaziende, GET pubblici, tetto fetch dichiarato, mai bypass 403/Cloudflare) → validazione checksum stdnum → verifica-campione seed dichiarato con fonte-B indipendente per-riga → classificazione euristica → aggiorna `data/recon/mandatari/roma.json` + §8c brief. Fatto terminale = roma.json con campi piva/piva_valida/stato/ateco_rilevato/fonte_enrichment/telefono_presente/classificazione + status PROMOSSA/CANDIDATI su esito campione. NON iniziare sopra 55% context. NB: Roma densa (>200 su PagineGialle, lista attuale parziale) — possibile espansione.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Ricerca gratuita `registroimprese.it` per verifica-campione = JS-only, non GET-fetchabile → usato proxy `ufficiocamerale.it` (Infocamere, stessa base-dati). Ratifica Luke sul proxy-metodo pendente.
- Gate [A] E2E TEST_FOUNDER (invariato, fuori scope recon).

### BACKLOG (differito, NON prerequisito del primo invio)
- Footprint linguistico web ("su commissione"/"cerchiamo per te"/"su ordinazione") NON harvest-ato → classe "mandatario-attivo-web" non assegnabile finché non si raccoglie il testo dei siti per-riga.
- Potenza NON-ARRICCHIBILI (20 righe): 7 chiuse per tetto-fetch, ri-tentabili in una passata dedicata (Dream Cars, Car Trade Show, Car Zentrum, G.Q. Automobili, Italy Srl, Moovia, Motor France, Automobili Ferrara [già verificata SI al campione]).
- Roma (RM) 28 righe densa (>200 su PagineGialle, lista attuale parziale) — enrichment + eventuale espansione.

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- **Potenza PROMOSSA con caveat fonte-proxy**: campione 9/10 SI ma cross-check su ufficiocamerale.it (Infocamere) NON su registroimprese.it (frontend gratuito JS-only, non aggirato). È la stessa base-dati del Registro Imprese ma non il canale specificato dal mandato → ratificare il metodo.
- **Due self-count subagent errati, corretti da verifica verbatim mia**: enrichment "20 P.IVA" → reali 18; campione "8 SI" → reali 9 SI. I numeri nei file/commit sono quelli verbatim (22 totali con P.IVA, 9/10 campione).
- **BLOCCO-DECISIONE §7 del brief superato**: FONTI_MANDATARI.md §6-§7 dichiarava l'anagrafe per-riga gratuita "non eseguibile"; il mandato di questa sessione ha scelto di procedere via schede per-nome accessibili (reportaziende.it/ufficiocamerale.it), diverse da registroaziende.it (403). Interpretato come decisione fresca di Luke.
- **Qualità dati**: 3 righe classificate fuori-target (Sanza Motors moto, Carrieri carrozzeria, Officina&Service); Auto Elite ha sede camerale Marsicovetere (PZ) non Potenza-città (provincia OK). ATECO rilevati spesso 45.11.01 (commercio auto) o assenti — nessuna P.IVA con ATECO 45.11.02/successori-mandatario esplicito trovata (le directory espongono l'attività prevalente, spesso commercio non intermediazione).

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (S292 + ORIZZONTI POST-PILOTA) · docs/briefs/FONTI_MANDATARI.md (§1 mapping ATECO 2007→2025, §8 pilota per-riga) · data/recon/mandatari/{potenza,treviso,roma}.json · .claude/rules/communication.md
