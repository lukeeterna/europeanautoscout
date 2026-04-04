# S100 — Fase 0: Esecuzione Piano Operativo (Agent-First)

## Contesto

S99 ha prodotto:
- Sprint 1 completato (monitoring, LLM cascade, test E2E — 9 PASS)
- 18 deep research sul nuovo target (micro-dealer su commissione)
- Piano Operativo v2.1 con backstory internazionale (1255 righe)
- API keys Groq + OpenRouter attive su MacBook e iMac

## Protocollo di avvio
1. SessionStart hook verifica skill/CLAUDE.md/daemon
2. Leggi `memory/MEMORY.md` per stato corrente
3. Leggi `research/s99_PIANO_OPERATIVO_COMPLETO.md` — IL DOCUMENTO MASTER
4. Se WA daemon unreachable → fix prima di tutto
5. Procedi con Fase 0

## Fase 0 — ESECUZIONE (Agent-First, parallelizzare tutto)

### Giorno 1 (2-3 ore)

**Agente 1 — Dominio .eu + Email**
- Registrare argosautomotive.eu (~€5-8)
- Setup Zoho Mail gratuito (info@ + luca@)
- Configurare firma email enterprise

**Agente 2 — Landing Page Riscrittura**
- Riscrivere con narrativa "Dall'Europa all'Italia"
- Integrare backstory (vedi piano sezione "Il Backstory")
- Togliere claim non verificabili, aggiungere prove reali
- Deploy su Cloudflare Pages

**Agente 3 — Immagini Luca Ferretti**
- Generare set 15 foto AI con Google AI Studio (Gemini Imagen 3)
- Consistenza facciale: character reference
- Contesti: showroom EU, fiere auto, meeting, auto premium
- Rimuovere metadata AI: `exiftool -all=`
- Deploy su landing + LinkedIn + Google Business

### Giorno 2 (2-3 ore)

**Agente 4 — Prove Presenza EU**
- Iscriversi EUROCOC Affiliate (gratis)
- Creare profilo Europages (gratis)
- Aggiornare LinkedIn headline + about (EU focus)
- Aggiornare Google Business descrizione
- Primo post LinkedIn: trend prezzi BMW X3 in Germania

**Agente 5 — Materiali Formativi**
- Creare Calcolatore Margine Import EU (Google Sheet)
- Creare PDF "5 Obiezioni del Cliente, 5 Risposte"
- Creare PDF "Import EU in 6 Step" (infografica)
- Creare PDF "Come Leggere un Annuncio Tedesco" (glossario)

### Giorno 3 (2-3 ore)

**Agente 6 — Discovery Dealer**
- PagineGialle: "concessionarie auto" per SA, FG, CE, AV, BA
- Google Maps scraper: "autosalone" per province target
- Cross-reference con AutoScout24 dealer (pochi annunci = micro-dealer)
- Output: database 200+ dealer con nome, tel, provincia, segnali

**Agente 7 — Primi Contatti**
- Selezionare 3-4 candidati ideali da Salerno (score 93)
- Preparare messaggio WA personalizzato per archetipo
- Inviare via wa-daemon (con API key auth)
- Tracking in dealer_network.sqlite

### Giorno 4-5

**Agente 8 — Modello B2B**
- Preparare template ricevuta prestazione occasionale
- Preparare template contratto incarico scouting (1 pagina)
- Disclaimer legale per dossier PDF

**Agente 9 — Follow-up + Espansione**
- Follow-up dealer contattati (Day 3: secondo veicolo + foto)
- Nuovi contatti: 3-4/giorno
- Preparare script telefonata Day 7

## KPI Fine Fase 0

| KPI | Target |
|-----|--------|
| Landing riscritta con backstory EU | SI |
| 15 immagini Luca Ferretti generate | 15/15 |
| Dominio .eu + email attivi | SI |
| EUROCOC affiliate attivo | SI |
| Calcolatore margine pronto | SI |
| 5 materiali formativi pronti | 5/5 |
| Database discovery: dealer identificati | > 200 |
| Primi contatti WA inviati (Salerno) | >= 3 |

## Regole Agent-First
- OGNI task va delegato a un sub-agente specializzato
- Parallelizzare tutto ciò che è indipendente
- Model: Sonnet per implementazione, Opus per strategia
- MAI codice prima di research
- MAI outreach senza test E2E green
- ZERO COSTI per tool/software

## Documenti di riferimento
```
Piano master:      research/s99_PIANO_OPERATIVO_COMPLETO.md
Backstory:         research/s99_backstory_internazionale.md
Immagini:          research/s99_ZERO_COST_image_generation.md
                   research/s99_immagini_luca_ferretti.md
Prove EU:          research/s99_prove_presenza_eu.md
Discovery:         research/s99_DATI_CERTI_canali_discovery.md
Archetipi:         research/s99_micro_dealer_archetipo.md
Margini:           research/s99_DATI_CERTI_margini_reali.md
Segmentazione:     research/s99_DATI_CERTI_segmentazione_province.md
Recensioni:        research/s99_DATI_CERTI_strategia_recensioni.md
Modello B2B:       research/s99_DATI_CERTI_modello_b2b.md
Formazione:        research/s99_DATI_CERTI_formazione_modello.md
```
