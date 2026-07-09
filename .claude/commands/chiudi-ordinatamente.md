# chiudi-ordinatamente — protocollo di chiusura idempotente

Esegui SEMPRE questi passi in ordine. Sovrascrivi gli artefatti per intero; mai append. Due esecuzioni di fila a parità di stato-disco = stesso risultato.

## REGOLE FERME
- Popola SOLO da git/disco verificati. VIETATO rigenerare la conoscenza commerciale/strategica (vive in docs/ROADMAP.md e docs/briefs/): qui solo PUNTATORI.
- VIETATO dichiarare "verde/done/passa" senza prova git o output di test grezzo.
- Autorità = git/disco. Questo handoff è un RENDER, non una fonte.
- Dato mancante su disco → "ASSENTE", non inventare. No sub-agent. CC-MAIN.
- CAMPI GATE/ANELLI = OUTPUT VERBATIM di comando (`last_status` da `state/rings.json`; riga gate via `grep` da `HANDOFF_CURRENT.md`). MAI prosa riformulata. Il falso-verde `[A]=CHIUSO` (S310) nacque da re-narrazione nel RENDER, non dal disco: il render è la superficie da cablare.

## PASSI
1. FASE 0: pwd (=root) · git branch · git log -1 · git status --short · git diff --stat.
2. Tipo sessione: READ-ONLY | DOCS-ONLY | WRITE-CODE (da cosa hai modificato).
3. Identifica i file che TU hai toccato (non quelli già dirty all'avvio).
4. Tue modifiche non committate: mostra git diff --stat dei tuoi file, proponi commit "session-close: <1 riga>", attendi conferma y/n nativa, committa SOLO i tuoi file. File già dirty all'avvio e non tuoi → riportali, NON committarli.
5. Rigenera l'handoff su disco sovrascrivendo HANDOFF_CURRENT.md (root; se la catena di autorità indica altro file canonico, usa quello) col TEMPLATE sotto, popolato da disco.
6. Stampa in chat il blocco handoff identico al file, preceduto da: "RENDER di <path>. Incollalo al giudice."

## TEMPLATE HANDOFF
# HANDOFF — <SESSION_ID> — <DATA UTC>
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: <READ-ONLY|DOCS-ONLY|WRITE-CODE>
- Mandato: <1 riga>
- Esito: <1 riga, solo fatti verificati>

### VERITÀ GIT
- branch <…> · HEAD <hash> <data> · working-tree <clean | dirty: file…>
- commit di questa sessione: <hash msg | nessuno>

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (OUTPUT VERBATIM da `state/rings.json` last_status — non re-narrare)
<incolla last_status di ogni anello letto da state/rings.json; output di comando, MAI prosa>

### GATE A DEALER REALE (OUTPUT VERBATIM — non re-narrare)
<riga gate via grep da HANDOFF_CURRENT.md. Un gate NON raggiunto = "= APERTO/BLOCKED-ON", MAI "= CHIUSO">
[A] <cond>=<valore> · [E] <cond>=<valore> · [D] <cond>=<valore>

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
<1 azione>

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
<lista | nessuno>

### BACKLOG (differito, NON prerequisito del primo invio)
<lista>

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- <osservazioni>
- discordanze disco vs ultimo stato assunto in chat (se note)

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (S<…>) · docs/briefs/<…> · <altro>
