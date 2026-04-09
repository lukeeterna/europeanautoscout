# PIANO OPERATIVO ARGOS — VALIDATO V2 (S107)
# Output della validazione agent-first del 2026-04-09

## Premessa

5 agenti hanno analizzato in parallelo il piano 4 blocchi prodotto in S106.
Risultato: il piano era PARZIALMENTE CORRETTO. Modifiche critiche sotto.

---

## SETTIMANA 0 — Azioni immediate (prima di qualsiasi outreach)

### 0.1 VERIFICA LEAD (BLOCCANTE)
Solo 4 dealer su 30 sono VALIDATI. Il dataset e' insufficiente.

**Azione:** Per i 10 dealer DUBBIO Sud Italia:
1. AS24 ricerca dealer → contare annunci attivi (soglia: >= 20)
2. Google Maps → stelle, n. recensioni, anno apertura
3. Se AS24 > 20 annunci AND Google > 30 recensioni → VALIDATO

**Azione parallela:** Recuperare dealer da scouting S78/S79:
- Stile Car (FG) — gia' con dossier generato
- Top Cars (CS) — score 7.5+ multi-fonte
- BD Auto (CE), Delta Automotive (BN), Car Plus (AV)
Questi hanno intel piu' profonda dei 30 attuali.

**Target:** 7-8 dealer VALIDATI con stock confermato prima di Day 1.

### 0.2 ENRICHMENT MANUALE TOP 10 (BLOCCANTE)
Per ogni dealer validato: email, website, Facebook, n. annunci AS24.
Tempo stimato: 2-3 ore.

### 0.3 CONTRATTO — Aggiungere clausole mancanti
Il contratto `tools/materiali/contratto_incarico_scouting.html` esiste ma MANCA:
- **Art. 5-bis: Clausola anti-bypass** — penale 100% fee se dealer compra senza pagare
- **Definizione "veicolo segnalato"** = qualsiasi veicolo incluso in dossier inviato
- **Protezione 90 giorni** dalla segnalazione, anche post-scadenza contratto

Non serve avvocato per le prime operazioni. Aggiungere le 3 clausole al template.

### 0.4 REQUIREMENTS.TXT
Creare `wa-intelligence/requirements.txt`:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
itsdangerous==2.1.2
```

### 0.5 TEMPLATE CASE STUDY
Preparare struttura vuota (1 pagina PDF):
- Veicolo trovato (marca, modello, anno, km)
- Prezzo EU vs IT (delta netto)
- Tempo dalla richiesta alla consegna
- Margine dealer netto
Da riempire appena il primo deal chiude.

---

## SETTIMANA 1 — Deploy + Test (quando iMac online)

### 1.1 DEPLOY S106 SU IMAC
`bash deploy/sync.sh` — CONFERMATO funzionante.
Tutti i file S106 inclusi nel rsync. PM2 restart automatico.

### 1.2 TEST E2E SU IMAC
Eseguire `test_pipeline_s106.py` (36 test) + `test_e2e_full.py` su iMac live.

### 1.3 CREARE MOCK DAEMON (post-deploy, non bloccante)
wa-daemon.js ha ZERO test automatici. Creare mock per:
- runOutboundGuard() / runPostSendUpdate()
- Anti-ban queue (DAILY_LIMIT, sleep timing)
- Listener incoming message
Priorita': dopo il primo outreach, non prima.

---

## SETTIMANA 2 — Primo Contatto

### 2.1 PRIMO INVIO DAY1 a 5 dealer validati
Ordine di contatto:
1. AZ Auto Evolution (AV) — piu' verificato
2. AutoQuarta Monteroni (LE) — trifecta, Salento
3. MOTORVIP (ME) — Sicilia
4. Greco Auto (CS) — Cosenza
5. 2F Motors Lamezia (CZ) — Calabria

Template: DAY1_PREMIUM per tutti (100% premium brand).
Flusso: fill_template → validate → /send (tutto implementato e testato).

### 2.2 MATERIALI DI SUPPORTO
- Day 1: Messaggio WA personalizzato
- Se risponde: one-pager PDF + link landing
- Se interessato: dossier PDF personalizzato per veicolo specifico
- Pitch deck: NON necessario in questa fase

### 2.3 FORMAZIONE DEALER (se interesse)
Impacchettare materiali esistenti in PDF:
- `tools/materiali/import_eu_6_step.html`
- `tools/materiali/guida_vendita_premium_import.html`
- Tabelle costi per paese da `s105_servizio_argos_definizione.md`
Non creare contenuto nuovo — solo packaging.

---

## MESE 2 — Robustezza (dopo primi contatti)

| Priorita' | Item | Costo |
|-----------|------|-------|
| 1 | Scraping sistematico Mercedes/Audi (on-demand basta per prime 5 ops) | 1 giorno |
| 2 | CI/CD test gate prima di deploy | 1-2 giorni |
| 3 | Log persistenti (spostare da /tmp) | 30 min |
| 4 | Rollback automatico deploy | 0.5 giorni |
| 5 | Mock daemon completo (Jest) | 1 giorno |

---

## MESE 2-3 — Scala (dopo primi deal chiusi)

| Item | Trigger | Note |
|------|---------|------|
| Case study completo | Primo deal chiuso | Template gia' pronto |
| Discovery espansa (1.118 lead) | 3+ dealer attivi | Solo dopo modello validato |
| Formazione strutturata | 5+ dealer | Ora basta materiale esistente |
| argos.py entry point | Secondo operatore | Solo developer experience |
| Dashboard KPI | 20+ dealer | Query SQL bastano fino ad allora |

---

## COSA E' STATO ELIMINATO dal piano originale

1. **D3 Dashboard KPI** — eliminato, query SQL ad hoc sufficienti
2. **Pitch deck formale** — non serve per primi dealer (dossier + landing bastano)
3. **Profilazione archetipo pre-invio** — confermato da founder S106: utile post-risposta, non pre-invio

## COSA E' STATO AGGIUNTO

1. **Verifica AS24 dei 10 dealer DUBBIO** — bloccante, i 4 validati non bastano
2. **Recupero dealer S78/S79** — intel superiore ai 30 attuali
3. **3 clausole contratto anti-bypass** — critico per protezione fee
4. **Template case study** — pronto PRIMA del deal, non dopo
5. **Packaging formazione esistente** — zero contenuto nuovo

## ANOMALIE DA RISOLVERE

1. `scheduler.py` usa DuckDB mentre S106 usa SQLite — migrare o deprecare
2. DAY1_MIXED ha 6 righe (regola ARGOS = max 5) — accorciare
3. 14 dealer Centro/Nord nel dataset — rimuovere da pipeline lancio Sud

---

## TIMELINE RIEPILOGATIVA

```
Sett. 0: Verifica lead + enrichment + contratto + requirements.txt
Sett. 1: Deploy iMac + test E2E live
Sett. 2: Primo outreach 5 dealer + materiali supporto
Sett. 3-4: Scraping sistematico + mock daemon
Mese 2: CI/CD + log + discovery espansa (se modello validato)
Mese 3+: Scala (case study, formazione, entry point)
```
