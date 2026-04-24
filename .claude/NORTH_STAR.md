# NORTH STAR — ARGOS Automotive
**Ultimo aggiornamento**: 2026-04-24 (S143)
**Versione**: v1 (evidence-based, con 3 gap strutturali dichiarati)
**Framework**: `PROMPT_CC_ENTERPRISE_UNIVERSALE.md` Sessione B

---

## Chi e' il cliente

**Profilo**: concessionari **family-business** del **Sud Italia** (Puglia, Campania, Basilicata, Calabria, Sicilia), stock **30-80 auto**, proprietario unico decisore.

**TAM dimensionato**:
- 3.264 concessionari totali 5 regioni Sud (Federauto/UNRAE via Perplexity Q1 2026)
- 78% proprietario unico (dato nazionale) → ~2.546 family-business
- Target stock 30-80 → **750-1.300 dealer potenziali**
- Di cui 340-600 **gia' educati al problema** import tedesco (46% import da Germania, sondaggi 2023-24)

**Decisore**: titolare, 40-60 anni, 10+ anni nel settore, decisione pragmatico-emotiva (credibilita' prima di prezzo — vedi `rules/communication.md`).

*Evidence*: MEMORY S141 — Perplexity Q1 output.

---

## Dolore risolto

**Pain dominante quantificato**: frode chilometri su usato importato in Italia = **15,4%** vs 5,3% auto vendute localmente. Una volta esportato dall'EU, il veicolo "ricomincia la storia da zero" — contachilometri alterati post-export.

**Pain secondari** (ordinati per peso):
1. Costi nascosti fai-da-te: **€1.060-1.690 per auto** (bisarca €600-1000 + COC €170-400 + Motorizzazione/PRA €290) — pagati a prescindere dall'esito
2. Tempi immatricolazione 4-30 giorni bloccano capitale del dealer
3. Truffa caparra da falsi fornitori EU con stock fantasma
4. Mito "auto tedesca ben tenuta" smontato (molte reimportate/estere, non originarie)

*Evidence*: MEMORY S140 — agent `dealer-persona-researcher` completato. Fonti: DealerLink, carVertical, SicuraAuto, AlVolante, Quattroruote.

---

## Valore unico (3 claim testabili)

| Claim | Cosa significa | Vs competitor |
|---|---|---|
| **Success fee €800-1.200 post-consegna** | Dealer paga ZERO finche' l'auto non e' nel suo piazzale | Bolidem €950+ upfront, Autotedesche €500-800 upfront, Importami 4%+IVA min €750 upfront. ARGOS **unico senza rischio finanziario** per il dealer. |
| **Scouting proattivo** | ARGOS propone veicoli specifici al dealer | Tutti i competitor (Bolidem/Autotedesche/Importami) **aspettano richiesta cliente**. AUTO1/AutoProff sono marketplace self-service. |
| **B2B Sud Italia con outreach attivo** | Scouting dedicato con contatto diretto WA | Zero competitor con outreach B2B attivo documentato nel Sud Italia (rules/competitors.md). AUTO1 **compra** dal dealer, non source per lui. |

*Evidence*: `.claude/agent-memory/competitive-intel/competitor_status_q1_2026.md` (verificato 2026-04-24 via live fetch).

**Vulnerabilita' riconosciute**:
- Success fee → dealer puo' sospettare prezzo finale gonfiato per recuperare rischio
- Scouting proattivo → "anche io vedo AuthScout24" (risposta: 73 portali, 19 paesi, CoVe pre-filtro)
- B2B Sud → mercato da educare, non sottrarre

---

## Modello di ricavo

- **Unit economics**: €800-1.200 per operazione conclusa (success fee)
- **Frequency target**: 4-8 operazioni/mese per dealer convertito a regime
- **Break-even operativo**: 10 dealer attivi = **~€10k/mese ricorrente**
- **Fascia veicoli**: €25k-€90k (BMW/Mercedes/Audi/Porsche/Range Rover 2018-2025)
- **Pagamento**: solo post-consegna nel piazzale dealer. Nessun anticipo, nessuna penale se dealer rifiuta auto proposta.

*Evidence*: MEMORY S141 + `rules/identity.md`.

---

## NON facciamo (scope exclusions)

1. **Non facciamo IVA/regime margine** — dealer gestisce fiscalita' propria
2. **Non finanziamo** l'acquisto del veicolo — dealer blocca col venditore EU
3. **Non garantiamo** post-vendita al cliente finale del dealer — solo garanzia costruttore UE
4. **Non gestiamo immatricolazione locale** — forniamo documenti (COC, traduzioni), dealer gestisce pratica
5. **Non serviamo B2C** — solo concessionari, mai privati
6. **Non accettiamo fee upfront** — rompe modello di business, riduce vantaggio unico
7. **Non gestiamo contenzioso** post-consegna — fuori perimetro

*Evidence*: MEMORY S140 — scope-out da agent dealer-persona-researcher.

---

## Vincoli immutabili

### Persona & fiscalita' (sotto responsabilita' esplicita Luke)
- **Luca Ferretti** = alias commerciale di **Gianluca Di Stasi** (non persona fittizia)
- Pagamenti: IBAN persona fisica **senza P.IVA** (fase MVP, da sistemare post primo dealer converted)
- Luke "non deve figurare" pubblicamente — gestione via alias

### Comunicazione dealer
- MAI esporre tech stack: CoVe/Claude/Anthropic/RAG/embedding/AI assenti dai materiali dealer
- MAI nel primo messaggio Day 1: "Germania", "import", "premium", "cerco auto", "estero"
- Max 5 righe WhatsApp + domanda chiusa (risposta monosillabica)
- Credibilita' sequenziale Sud: persona reale → referral/specificita' → track record → offerta. **Saltare uno step = ricominciare da capo.**

### Terminologia CoVe
- `recommendation` (non `verdict`), `analyzed_at` (non `created_at`), `confidence` 0.0-1.0
- Soglie: DEALER_PREMIUM_THRESHOLD=0.75, VIN_CHECK_THRESHOLD=0.60, DAILY_LIMIT=30
- `cove_engine_v4.py` non modificare — solo leggere e invocare

### Zero-cost operativo
- Tutto gratuito o gia' pagato (escluso eventuale P.IVA post-MVP)
- Test E2E deve passare prima di ogni outreach dealer reale
- Nessun deploy senza healthcheck

*Evidence*: `rules/identity.md`, `rules/communication.md`, `rules/cove.md`, `rules/security.md`, MEMORY S140 constraints Luke.

---

## Gap strutturali aperti [DA CHIUDERE PER NORTH_STAR v2]

### GAP 1 — Zero dati primari dealer Sud Italia
**Problema**: tutte le assertion sul dolore dealer derivano da fonti secondarie (DealerLink, carVertical, forum B2C). Unico contatto reale: **Enzo Car (Ascoli Satriano FG) 2026-04-15 → "Nulla" → CLOSED_NO**. Un campione non fa statistica ne' validazione.

**Come si chiude**: 3 telefonate dirette a dealer Puglia con script "mi dica il problema piu' grosso quando compra in Germania" (metodo primario proposto in MEMORY S140). 20 minuti di ricerca primaria > 10h web search secondaria.

**Stato**: pianificato, non eseguito.

### GAP 2 — Regime fiscale MVP
**Problema**: forma giuridica per gestire success fee €800-1.200 senza P.IVA in fase MVP non e' stata ancora validata (Q2 Perplexity su "prestazione occasionale vs forfettaria vs mandato" skippata da Luke).

**Come si chiude**: query Perplexity con riferimenti normativi 2026 + validazione con commercialista prima del primo bonifico dealer.

**Stato**: skippato da Luke "sistemiamo dopo che business parte". Rischio: ricevere primo bonifico senza strumento fiscale adeguato.

### GAP 3 — Claim testabili su campo
**Problema**: i 3 vantaggi unici (success fee / scouting proattivo / B2B Sud) sono documentati con evidence competitiva ma **non ancora validati empiricamente** come leve di conversione. Funzioneranno davvero sul campo?

**Come si chiude**: outreach primi 3-5 dealer cold (5 pronti in pipeline — Stile Car, Autoline, GP Cars, Car Plus, Sa.My. Auto) → analisi risposta per claim. Dati empirici > ricerca secondaria.

**Stato**: pipeline pronta, outreach non ancora partito. Blocca anche infrastruttura (scraper X4 non testato live, WA daemon richiede verifica iMac online).

---

## Uso di questo documento

**Per ogni nuova feature, refactor, outreach, decisione significativa**:
1. Leggi NORTH_STAR prima di iniziare
2. Verifica allineamento con: cliente / dolore / valore unico / scope exclusions / vincoli immutabili
3. Se allineato → procedi
4. Se borderline → chiedi a Luke con trade-off 2-3 opzioni
5. Se contraddice vincoli → fermati

**Quando aggiornare questo documento**:
- NORTH_STAR v2 dopo chiusura Gap 1 + Gap 3 (dati empirici primi dealer)
- Vincoli immutabili: modifica solo con OK esplicito Luke
- Scope exclusions: modifica solo con OK esplicito Luke
- Valore unico: aggiornare appena un competitor cambia pricing o modello (verifica Trustpilot/sito ogni trimestre)

**Quando NON toccarlo**:
- Ogni volta che un dealer obietta ("ma il prezzo e' troppo alto") — quello e' PLAYBOOK, non NORTH_STAR
- Ogni volta che scraper si rompe — quello e' operation, non NORTH_STAR
- Ogni volta che si aggiunge un file — documenta in HANDOFF/MEMORY
