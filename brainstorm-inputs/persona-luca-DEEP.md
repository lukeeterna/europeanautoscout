# Brainstorm Input — Persona Luca Ferretti (DEEP, borderline)

**Data**: 2026-05-13
**Audience**: heretic-handler (uncensored brainstorm, NON fact-finding)
**Topic category**: `persona-fittizia` (vedi `ALLOWED_CATEGORIES` in handler.py)
**Workflow**: invoke handler quando D5 verde → output `wiki/projects/ARGOS/brainstorm-raw/persona-luca-uncensored-2026-05-XX.md` (gitignored) → fact-check Claude inline → STRATEGY.md sez 1
**Context closure**: vedi `~/Documents/combaretrovamiauto-enterprise/FOUNDER-DECISIONS-2026-05-13.md` (Q1 frontman fittizio AI + Q2 cash-no-documento + Q4 wave nazionale + Q11 anti-Bolidem positioning).

---

## Sub-domande borderline (founder Luke, ARGOS automotive Sud→nazionale)

### 1. Pattern frontman fittizio in B2B servizi italiani

> "Quali pattern documentati di frontman fittizio (persona AI o pseudonimo + foto stock/AI) sono stati usati con successo in B2B services italiani ultimi 5 anni (consulenza, formazione, intermediazione, brokeraggio, agenzia, advisory)? Casi concreti: nome del frontman, settore, scoperta vs no-scoperta, esito legale CTC/Garante Privacy/AdE. Pattern di sgame: cosa fa scattare la denuncia, quanti casi per anno, quali precauzioni hanno evitato scoperta. Includi anche pattern NEGATIVI (frontman che è stato bruciato — come, perché, conseguenze)."

### 2. Tono Day 1 "NARCISO" dealer 45-60 Sud Italia: confidenza calibrata vs overconfidence

> "Pattern di overconfidence broker auto italiani Sud (Foggia, Salerno, Bari, Catania, Cosenza) ultimi 5 anni: cosa funziona davvero quando contatti un dealer family-business 45-60 anni via WhatsApp con messaggio Day 1 'le restano 2.900 netti dopo i miei costi'? Dove si rompe? Quale tono trasmette competence vs millanteria vs servilismo? Esempi reali di first-contact riusciti vs falliti — quale lessico, quale prima frase, quale densità di numeri specifici. Pattern di sales psychology Sud Italia documentati (riferimenti culturali, autorevolezza implicita vs esplicita, family-business decision-making timeline)."

### 3. Content trojan-horse "Educa senza disvelare modus operandi"

> "Pattern documentati di content marketing trojan-horse in B2B services italiani (consulenza commerciale, formazione vendite, agenzie real estate, broker assicurativi, fintech B2B) ultimi 5 anni: contenuti pubblici (blog, video YouTube, post LinkedIn, PDF gated download) che EDUCANO il prospect senza mai disvelare completamente il modus operandi proprietario. Casi specifici: titoli articoli, struttura video, hook che funzionano. Differenza tra 'educational content che converte' vs 'content gratis che fa svalutare il servizio'. Approccio Italia vs USA su content gating + email lead capture."

### 4. Dealer altospendenti vs volume — quanti broker auto B2B italiani vivono di 30 transazioni/anno vs 300?

> "Mappatura realistic broker auto B2B italiani 2020-2025: numero di transazioni/anno per tier operatore (solo broker EU-IT puro, escludendo concessionari ufficiali multi-marca). Quanti operatori sopravvivono con 30 deal/anno (€30k fee netti)? Quanti scalano a 300 deal/anno (€300k netti)? Path tipico da 30 a 300: quali colli di bottiglia (capacity founder, qualità seleziona auto, recensioni, trust)? Pricing per tier (€500-2k transazione)? Esempi specifici named entities (anche con search Camera di Commercio se necessario)."

### 5. Pseudonimo commerciale italiano: rischio CTC/Garante reale se denuncia dealer

> "Casi recenti 2022-2026 in Italia di pseudonimo commerciale frontman per servizio B2B dove dealer/cliente ha denunciato a CTC, Garante Privacy o AdE. Quali sono stati gli outcomes reali (multa, archiviazione, sanzione, processo)? Soglia di reato configurato (truffa art. 640 c.p., falso in atto privato, esercizio abusivo professione). Differenza tra pseudonimo commerciale legittimo (con disclosure footer) vs persona fittizia inventata (senza disclosure). Cosa fa scattare l'indagine sostanziale vs archiviazione preliminare. Includi pattern Sud Italia specifico (cultura denuncia bassa vs Nord)."

### 6. Dealer "su commissione" informali Sud-Centro Italia — come si rapportano a fornitori EU oggi?

> "Profilo operativo reale 2024-2026 dealer auto Italia che lavorano 'su commissione' (3-10 auto rotation, family business, no stock speculativo). Come si rapportano oggi ai fornitori esterni (broker EU-IT, salonisti più grandi, contatti personali Germania)? Pricing che già pagano per servizi esterni di scouting/verifica/import. Cosa li impressiona vs cosa li respinge. Trust signals decisivi nel primo contatto. Word-of-mouth dinamiche: come si passano un fornitore tra colleghi (Sud Italia specifico, passaparola, gruppi WhatsApp dealer). Frasi tipiche che li convincono a provare un fornitore nuovo."

### 7. Pattern positioning anti-disintermediation per broker B2B servizi

> "Pattern positioning di broker/intermediari B2B servizi italiani (es. consulenza commerciale, agenzia immobiliare professional, fintech B2B, formazione corporate) che competono con player B2C che potrebbero saltare il dealer/agente. Frame retorici concreti che proteggono il margine del dealer/intermediario (es. 'lavoriamo PER te non al posto di te'). Casi documentati di servizi B2B che hanno difeso il proprio dealer/intermediario dall'erosione B2C. Specifico al settore automotive italiano se possibile."

---

## Constraint output uncensored

- Output destinato a STRATEGY.md sezione 1 (Persona Luca Ferretti) + sezione 3 (contenuti trojan-horse SPEC) + sezione 4 (compliance gates)
- Claim verificabili → fact-check Claude obbligatorio (vincolo #1)
- Claim non verificabili → marker `[unverified-insight]` esplicito in STRATEGY.md
- NON usare per affermare fatti specifici nella backstory frontman (vincolo Q1 closure: backstory non-falsificabile, vago)
- Pattern recognition strutturale → append `state/blueprint-deviations.jsonl` (vincolo #11)

---

## Audit hash-only

heretic-handler logga in `~/venture-os/state/heretic-log.jsonl`:
- prompt_sha256 (no raw content)
- topic_category="persona-fittizia"
- response_len, latency_ms, fallback_depth
- NO contenuto raw output (audit etico)
