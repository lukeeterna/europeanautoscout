# S126 — Materiali Formativi Stile Car + Research Nord/Centro

## Contesto (da S125 — 2026-04-15)

### Allineamento strategico raggiunto con il founder

1. **Direzione**: Opzione C — costruire area formazione come asset ARGOS
2. **Frame**: per macroaree (Nord/Centro/Sud), ma serve più segmentazione → altra research
3. **Sequenza**: materiali formativi PRIMA, poi usarli come leva nel Day 1 (non go-live subito)
4. **Metodo CTO**: parallelizzare — Stile Car come MVP pilota (Sud già researched a 7/10), research Nord/Centro in parallelo

### Cosa è già disponibile

- Research Sud completa: `.planning/research/s105_formazione_dealer_premium.md`
- Self-perception dealer tutta Italia: `memory/project_s125_research_dealer_italia.md`
- 5 gap comunicazione documentati (zero contenuto educativo, zero video, WA reattivo, social proof non usato, import EU invisibile)
- Template Day 1 Stile Car: `tools/outreach/day1_templates/` (veicolo + messaggio Day 1)
- Profilo Stile Car validato: `tools/outreach/dealer_profiles_validated.json`

---

## Agenda S126

### Track 1 — Research Nord/Centro (lanciare subito, agenti in parallelo)

**Domande specifiche da ricercare** (più granulari di S125):

**Nord Italia** (MI/BG/VR/BS/TO):
- Quali dealer indipendenti Nord con stock BMW/Mercedes €25-45k hanno già comunicazione digitale strutturata (IG/sito)? Campione 10+
- Il dealer Nord usa l'import EU come differenziatore esplicito? Con che linguaggio?
- Qual è il profilo tipo del cliente premium Nord (età, canale di scoperta, obiezioni più comuni)?
- Esiste già qualche dealer Nord che fa contenuto educativo su import/garanzia EU?

**Centro Italia** (BO/FI/RM/AN):
- Il dealer Centro si comporta più come Nord o Sud nella comunicazione premium?
- Bologna/Firenze sono davvero più "aspirazionali" come emerso in S125? Dati concreti?
- Roma: quale frame funziona — processo (come Nord) o relazione (come Sud)?

**Dati strutturali da verificare**:
- Volumi usato premium (€25k+) per regione 2024-2025 (AutoScout24, UNRAE)
- Numero dealer indipendenti multi-brand per macroarea con stock premium
- Penetrazione digital (sito web, IG, Google Business) per dealer 30-80 auto per area

### Track 2 — MVP Materiale Formativo Stile Car (costruire)

**Cosa costruiamo**: il primo "pacchetto comunicativo" da allegare alla proposta veicolo.

Struttura MVP (da definire e costruire):
1. **Scheda veicolo comunicabile** — non la scheda tecnica ARGOS, ma la versione "pronta per i tuoi clienti":
   - Titolo: "BMW X3 2022 — perché vale €38.000" (non "BMW X3 xDrive30e specs")
   - 3 punti di valore per il cliente finale (km certificati TUV, optional €X in più rispetto al mercato IT, garanzia legale 2 anni)
   - Risposta alle 3 obiezioni più comuni sull'import (già in s105)
   
2. **Script WA per il dealer** — come proporre ai propri clienti la BMW:
   - Messaggio tipo da inviare via WA a cliente esistente ("Ho trovato qualcosa che fa per te")
   - Adattato al tono Sud Italia (relazionale, non tecnico)

3. **Post IG ready-to-post** — caption + indicazioni foto:
   - Caption 3-4 righe, tono professionale-caldo, nessun prezzo nel post
   - Indicazione: "usa queste 3 foto dell'auto" (quelle già nel dossier ARGOS)

**Output**: file PDF o MD da allegare al messaggio Day 1 Stile Car.
**Formato Day 1 aggiornato**: "Ti propongo questa BMW. Ti mando anche come la puoi comunicare ai tuoi clienti — così risparmi 2 ore di lavoro."

### Track 3 — Validazione su TEST_FOUNDER

Prima di inviare qualsiasi cosa a Stile Car:
- Inviare materiale MVP a TEST_FOUNDER (393314928901)
- Verificare: il formato è leggibile? Il PDF arriva correttamente via WA? Il tono è giusto?
- Approvazione founder → go-live Stile Car

---

## File da leggere all'inizio sessione

```
HANDOFF.md                                          ← stato S125
memory/project_s125_research_dealer_italia.md       ← findings S125 completi
.planning/research/s105_formazione_dealer_premium.md ← base materiale formativo
tools/outreach/dealer_profiles_validated.json       ← profilo Stile Car
tools/outreach/day1_templates/                      ← template Day 1 esistente
```

---

## Stato sistema (fine S125)

- WA daemon: UNREACHABLE a fine sessione (iMac potenzialmente offline)
- Dealer reali: NESSUNO contattato — pipeline ferma su approvazione materiali
- DB: nessuna modifica S125
- GSD milestone v1.0: 82% — Phase 4 aperta (3 piani non eseguiti)
- Nessun commit in S125

## Prossima azione immediata

```
1. Verifica WA daemon online (ssh iMac → curl localhost:9191/status)
2. Lancia research Nord/Centro (3 agent paralleli con domande specifiche sopra)
3. Costruisci MVP materiale formativo Stile Car
4. Test su TEST_FOUNDER → approvazione founder → Day 1 Stile Car
```
