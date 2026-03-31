# S94 — ACTION PLAN NUOVI TARGET
## Dealer identificati, profilati, messaggi pronti
### 2026-03-31

---

## DECISIONE: CHI CONTATTARE

### TIER1 NUOVI — CONTATTARE (priorita' massima)

| # | Dealer | Citta' | Archetipo | Tel | Perche' |
|---|--------|--------|-----------|-----|---------|
| 1 | **Enzo Car** (Enzo Cordisco) | Ascoli Satriano FG | NARCISO | 339 8835656 | 61 auto, Mercedes+Porsche, sito+IG attivo, nome=brand |
| 2 | **Dream Car** (Michele+Vincenzo Cannone) | Cerignola FG | BARONE | 349 453 0357 | 34 recensioni 4.9/5, gia' import EU, famiglia |

### MONITORARE (non contattare ora)

| # | Dealer | Citta' | Motivo |
|---|--------|--------|--------|
| 3 | De Cicco Srl | Casali del Manco CS | Fatturato €1,3M, troppo piccolo per premium EU €35-55k |
| 4 | Luc Auto | Cerignola FG | Utile come referral se Dream Car o Enzo Car entrano |

### ESCLUDERE

| # | Dealer | Motivo |
|---|--------|--------|
| 5 | Automontreal Group | 800 auto, 17.000 mq — troppo grande, gia' strutturato |
| 6 | Link Motors Amantea | Franchising nazionale (97 agenzie), zero-stock puro, incompatibile |

---

## NOTA CRITICA: PROFILO vs TARGET

Il profiling ha rivelato che anche i nuovi target trovati dal discovery sono **dealer con stock**, non puri "su commissione". Enzo Car ha 61 auto, Dream Car ha stock + import EU.

**Questo significa che:**
1. I dealer PURI su commissione (3-5 auto, zero stock) sono TROPPO INVISIBILI per trovarli via scraping
2. Il target realistico e' il dealer MEDIO-PICCOLO (15-60 auto) che FA ANCHE commissione
3. Il modello ibrido (proattivo + on-demand) e' l'approccio corretto per entrambi i tipi
4. La strategia non cambia: il Day 1 propone un veicolo reale, il Day 3-7 introduce l'on-demand

---

## MESSAGGI PRONTI

File completo: `research/s94_messaggi_day1_day3_day7_nuovi_target.md`

### Enzo Car — Day 1 (NARCISO)
```
Buongiorno, ho trovato una Mercedes GLC 220d 2022, 44.000 km
a €33.800 in Germania — in Puglia la stessa auto parte da €41.000.

Trasporto Foggia: €800 circa. Ci guadagna €6.000 netti.
Km certificati, documenti in ordine.

Ha un cliente che cerca questa fascia?

Luca Ferretti
```

### Dream Car — Day 1 (BARONE, gia' importa)
```
Buongiorno Michele, ho trovato un'Audi A6 Avant 40 TDI 2022,
39.000 km a Monaco — €31.400. In Puglia parte da €38.000.

Ho visto il suo stock su AutoScout24 — tratta Audi con cura.
Km certificati, documenti pronti.

Le mando la scheda?

Luca Ferretti
```

**NOTA:** Verificare su AS24/Mobile.de che i veicoli citati esistano ancora a quel prezzo PRIMA di inviare.

---

## SEQUENZA OPERATIVA

### Settimana 1-3 aprile
1. Verificare veicoli reali su AS24 DE per Mercedes GLC e Audi A6
2. Preparare dossier PDF per entrambi (la pipeline lo fa gia')
3. Inviare Day 1 a Enzo Car (martedi 1 aprile, 8:30)
4. Inviare Day 1 a Dream Car (mercoledi 2 aprile, 8:30)
5. Day 3 a TIER0 attuali con bridge on-demand
6. Day 7 a TIER0 attuali (scade 3 aprile)

### Settimana 7-10 aprile
7. Day 3 a Enzo Car + Dream Car
8. Ampliare discovery a province priorita' 2 (avellino, lecce, taranto, salerno)
9. Valutare risposte e aggiustare strategia

### In parallelo
- Fix bug outreach_scheduler (check risposta dealer)
- Costruire request_parser.py per flusso on-demand
- Google Business Profile ARGOS con almeno 5 recensioni (anche da conoscenti)

---

## POLO FOGGIA — STRATEGIA TERRITORIALE

Il discovery ha trovato 3 dealer a Foggia:
- Enzo Car (Ascoli Satriano, 35 km da Cerignola)
- Dream Car (Cerignola)
- Luc Auto (Cerignola)

Se UNO entra → referral verso gli altri. Il polo Foggia potrebbe essere il primo cluster ARGOS.
Il content-creator ha gia' differenziato i veicoli proposti (GLC per Enzo, A6 per Dream) per evitare che parlino tra loro e vedano lo stesso messaggio.
