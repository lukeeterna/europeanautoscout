# S95 — Identità Online Completa + Primo Contatto Dealer

## Contesto

S94 è stata la sessione più massiva del progetto: pivot strategico, 11 deep research, dealer discovery
engine (92 dealer in 8 province), 3 nuove skill, messaggi V3 basati su dati oggettivi, e LinkedIn
completato autonomamente via Playwright.

**LinkedIn Luca Ferretti è LIVE:** linkedin.com/in/luca-ferretti-53b6513b9
- Bio completa, foto profilo, headline, azienda Argos Automotive
- Google indicizzerà in 24-48h

**Cosa MANCA per la credibilità online:**
- Google Business Profile (il dealer cerca su Google Maps!)
- Facebook page
- Il sito argos-automotive.pages.dev non è indicizzato su Google (robots.txt + sitemap deployati, serve tempo)

## Credenziali

Tutte le credenziali sono SOLO in `.env` (gitignored). Vedi variabili:
`GMAIL_PWD`, `LINKEDIN_PWD`, `FACEBOOK_PWD`, `CLOUDFLARE_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.

> NOTA SICUREZZA (S146): le credenziali in chiaro che erano qui sono state rimosse il 2026-04-27. Sono ancora presenti nella storia git al commit `99e826c` (S94). Rotazione e/o `git filter-repo` sono compito di Luke.

## Priorità S95 (in ordine)

### 1. CREARE Google Business Profile (CRITICO)
Il dealer che riceve WA da sconosciuto cerca su Google. Senza GBP = cestino.

Procedura:
- Login su business.google.com con Gmail (il founder deve fare il CAPTCHA dal browser)
- Oppure provare via Playwright se Google non blocca
- Dati pronti in: `tools/google_business_checklist.md` + `copy/google_business_description.txt`
- Foto pronte in: `assets/cover_google_business_v2.png` + `assets/luca_ferretti_v3.png`
- Categoria: "Consulente automobilistico" o "Auto usate"
- Modalità: servizio a domicilio (no sede fisica)
- Aree: Campania, Puglia, Calabria, Basilicata

### 2. CREARE Facebook Page
- Login Facebook con credenziali in .env
- Creare pagina business "Luca Ferretti — Vehicle Sourcing EU"
- Caricare foto profilo + cover
- Pubblicare 3-5 post (assets/post_1-5_v2.png + copy/post_1-5.txt già pronti!)

### 3. Day 7 ai TIER0 (scade 3 aprile!)
Messaggi V3 pronti in: `research/s94_MESSAGGI_DEFINITIVI_V3.md`
Approccio: uscita dignitosa + bridge on-demand + PDF allegato
MA: solo DOPO che GBP è creato (altrimenti il dealer cerca e non trova nulla)

### 4. Primo contatto Enzo Car + Dream Car
Messaggi V3 (CHI-PERCHE'-CHIEDI) pronti in: `research/s94_MESSAGGI_DEFINITIVI_V3.md`
Solo DOPO profili online completi (GBP + Facebook + LinkedIn già fatto)

### 5. Fix bug outreach_scheduler
Il scheduler NON controlla se il dealer ha risposto prima di avanzare la sequenza.
File: `tools/outreach_scheduler.py`

### 6. Ampliare e gestire discovery
92 dealer mappati in 8 province (file: /tmp/discovery_p2.json — SALVARE in data/)
Profilare i top 8 nuovi target con skill `argos-intel-territoriale`
Inserire nel CRM con `discovery_engine.py --insert-crm`

## File critici S94 (LEGGERE PRIMA DI AGIRE)

```
research/S94_MASTER_REFERENCE.md                     ← RIFERIMENTO STRATEGICO
research/s94_MESSAGGI_DEFINITIVI_V3.md               ← Messaggi pronti (framework V3)
research/s94_primo_contatto_b2b_dati_oggettivi.md    ← DATI su cosa funziona
research/s94_presentazione_b2b_primo_contatto.md     ← Come presentarsi (framework CHI-PERCHE'-CHIEDI)
research/s94_top6_dealer_profiles.md                  ← Profili 6 dealer
research/s94_intel_reale_enzo_dream.md               ← Intel Enzo Car + Dream Car
research/s94_dinamiche_territorio_foggiano.md        ← Territorio Foggia
research/s94_verifica_presenza_online.md             ← Stato piattaforme
tools/google_business_checklist.md                    ← Procedura step-by-step GBP
tools/platform_setup_playbook.md                      ← Procedura tutte le piattaforme
copy/                                                 ← Bio, descrizioni, post pronti
assets/                                               ← Foto, cover, post grafici pronti
```

## Skill disponibili

```
skill-argos-orchestrator         ← Flusso discovery→profile→message→send→track
skill-argos-intel-territoriale   ← Intel REALE da fonti primarie
skill-argos-validator            ← Verifica dati prima dell'invio
skill-argos                      ← Automazione outreach WA
skill-cove                       ← Scoring veicoli
skill-deep-research              ← Ricerca approfondita
skill-sales-official             ← Account research + outreach
skill-marketing-official         ← Content per archetipo
```

## Regole NON NEGOZIABILI (da feedback S94)

1. **ZERO fake** — niente recensioni da conoscenti, niente dati inventati
2. **AGIRE autonomamente** — il CTO fa, non chiede al founder di fare
3. **Framework V3** — Day 1 = CHI-PERCHE'-CHIEDI, MAI veicolo a freddo
4. **Credibilità PRIMA di contattare** — GBP + LinkedIn + Facebook PRIMA dei messaggi dealer
5. **Dati REALI** — ogni claim nei messaggi deve essere verificato su AS24.de/it
6. **ZERO documenti inutili** — se puoi fare qualcosa, fallo. Non scrivere un documento su come farlo.

## Test di successo S95
```
- Google Business Profile CREATO e live
- Facebook page CREATA con 3-5 post
- "Luca Ferretti ARGOS" su Google restituisce risultati (LinkedIn + GBP)
- Day 7 inviato ai 3 TIER0 con bridge on-demand + PDF
- Day 1 V3 inviato a Enzo Car e Dream Car
- Bug outreach_scheduler fixato
- Discovery P2 salvato in data/ e top target profilati
```
