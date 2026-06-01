# S75 — MESSAGGI DAY 1 PRONTI PER I 3 TIER0
## Veicoli REALI da batch runner 20/03/2026
## NON INVIARE finche' Google Business non e' attivo

---

## STATUS BLOCCO

**BLOCCANTE**: Google Business Profile NON ancora attivo.
Quando il dealer riceve il messaggio → Googla "Luca Ferretti" → DEVE trovare:
1. Landing page (FATTO: argos-automotive.pages.dev)
2. Google Business con foto e almeno 5 recensioni (DA FARE)

**Azioni founder PRIMA dell'invio:**
- [ ] Creare Google Business Profile (vedi tools/google_business_checklist.md)
- [ ] Caricare foto professionale
- [ ] Ottenere almeno 5 recensioni dalla rete personale
- [ ] Configurare VoIP 0972 536 918 su Zoiper (rispondere in orario lav.)
- [ ] Registrare segreteria telefonica professionale
- [ ] Deploy landing aggiornata su Cloudflare Pages

---

## TARGET #1: STILE CAR (Orta Nova FG)
**Persona**: Domenico | **Archetipo**: NARCISO | **Stock**: 36 auto BMW/Merc/Audi/Volvo
**WA**: 333-4254654 | **Segnale**: dichiara "importazioni europee dirette" su AS24
**860 recensioni 4.98** = business SOLIDO

### Veicolo selezionato
- **BMW X3 xDrive20d 2022**, 50.058 km
- **Prezzo Germania**: €34.140 (AutoScout24 DE)
- **Prezzo Italia equiv.**: €41.500-43.000
- **CoVe Score**: 81 | Status: PROCEED | Fraud: CLEAN
- **Margine stimato**: €7.423

### Messaggio Day 1 (NARCISO)

```
Buongiorno, ho trovato una BMW X3 xDrive 2022, 50.000 km,
a €34.100 in Germania. In Puglia gli stessi esemplari
partono da €42-43.000.

Ho visto il suo stock su AutoScout — so che tratta gia'
import EU. Sto cercando 2-3 concessionari della zona Foggia.

Le mando la scheda completa?

Luca Ferretti
```

**Perche' questo messaggio per Stile Car:**
- Lui GIA' importa → non serve educare, serve dimostrare valore aggiunto
- "So che tratta gia' import EU" = hai fatto i compiti, non e' spam
- "2-3 concessionari della zona Foggia" = esclusivita' (trigger NARCISO)
- BMW X3 = coerente col suo stock (BMW/Merc/Audi)
- Delta €8-9k = evidente senza dirlo esplicitamente
- "Luca Ferretti" senza ARGOS = persona, non brand

### Orario invio consigliato
Martedi' o mercoledi', 8:30-9:00

---

## TARGET #2: CAR PLUS (Grottaminarda AV)
**Persona**: Luca | **Archetipo**: RAGIONIERE | **Stock**: 19 auto BMW/Merc/Jaguar/LR
**WA**: 328-9617180 | **Segnale**: dichiara "importazioni dall'estero"
**Giovane, in crescita, gia' importa**

### Veicolo selezionato
- **BMW X3 xDrive20d 2022**, 50.058 km
- **Prezzo Germania**: €34.140 (AutoScout24 DE)
- **Trasporto bisarca**: ~€850 (DE→Campania)
- **Fee**: €900
- **Costo totale per il dealer**: €35.890
- **Prezzo Italia equiv.**: €41.500-43.000
- **Margine netto**: ~€5.600-7.100

### Messaggio Day 1 (RAGIONIERE)

```
Buongiorno, ho trovato una BMW X3 20d 2022, 50.000 km
a €34.100 in Germania.

In Italia la stessa auto sta a €42-43.000.
Trasporto Campania: €850. Fee mia: €900.
Margine netto per lei: circa €5.500.

Le interessa?

Luca Ferretti
```

**Perche' questo messaggio per Car Plus:**
- Luca (omonimo) e' giovane e ragiona coi numeri
- TUTTI i costi visibili nella prima lettura = zero sorprese
- "Margine netto circa €5.500" = la riga che fa rispondere il RAGIONIERE
- In EUR, non in % — "circa" = onesto
- Breve e diretto — il RAGIONIERE non ha bisogno di gentilezze

### Orario invio consigliato
Martedi' o mercoledi', 8:30-9:00

---

## TARGET #3: SA.MY. AUTO (Rende CS)
**Persona**: Antonio Salerni | **Archetipo**: PERFORMANTE | **Stock**: 99 auto BMW/Merc/Porsche/Lambo
**WA**: 349-2587423 | **Segnale**: titolare ha vissuto in Germania
**Instagram attivo, ~30 anni, conosce i prezzi tedeschi**

### Veicolo selezionato
- **BMW X3 xDrive20d 2022**, 50.058 km (stesso — BMW nel suo stock)
- **Prezzo Germania**: €34.140
- **Prezzo Italia**: €41.500-43.000
- **Margine**: €7.423

**Nota**: Antonio conosce i prezzi tedeschi MEGLIO della media.
Non puoi bluffarlo. L'approccio deve essere peer-to-peer.
Ideale: un veicolo Porsche o Lambo (fascia alta del suo stock).
Ma serve batch runner per Porsche Macan/Cayenne.

### Messaggio Day 1 (PERFORMANTE → adattamento NARCISO/TECNICO)

```
Buongiorno, ho trovato una BMW X3 20d 2022, 50k km,
a €34.100 su AutoScout DE.

So che ha vissuto in Germania e conosce i prezzi —
questo e' sotto mercato anche per il DE.
Km verificati, disponibile subito.

Le interessa o preferisce che cerchi in un'altra fascia?

Luca Ferretti
```

**Perche' questo messaggio per Sa.My. Auto:**
- "So che ha vissuto in Germania" = ricerca personale specifica su di LUI
- "Conosce i prezzi" = rispetto per la sua competenza (peer-to-peer)
- "Sotto mercato anche per il DE" = argomento che lui puo' verificare in 30 secondi
- "Km verificati, disponibile subito" = concretezza
- "O preferisce che cerchi in un'altra fascia?" = apertura → puo' chiedere Porsche/Lambo
- Non lo tratti da principiante dell'import

### Orario invio consigliato
Martedi' o mercoledi', 8:30-9:00

---

## POST-INVIO CHECKLIST (per ogni dealer)

Dopo l'invio di ogni messaggio:
```bash
# 1. Aggiornare stato pipeline
python3 tools/dealer_crm.py update <id> pipeline_status CONTACTED

# 2. Loggare interazione
python3 tools/dealer_crm.py log <id> WA OUT "Day 1 V2 — BMW X3 2022 €34.100 DE"

# 3. Registrare veicolo proposto
python3 tools/dealer_crm.py propose <id> "BMW X3 xDrive20d 2022 50k km" 34140 42000

# Il sequencer Day 3→30 parte automatico dal wa-daemon
```

### Comandi specifici per ogni dealer:
```bash
# Stile Car
python3 tools/dealer_crm.py update stile_car_fg pipeline_status CONTACTED
python3 tools/dealer_crm.py log stile_car_fg WA OUT "Day 1 V2 — BMW X3 2022 €34.100 DE"
python3 tools/dealer_crm.py propose stile_car_fg "BMW X3 xDrive20d 2022 50k km" 34140 42000

# Car Plus
python3 tools/dealer_crm.py update car_plus_av pipeline_status CONTACTED
python3 tools/dealer_crm.py log car_plus_av WA OUT "Day 1 V2 — BMW X3 2022 €34.100 DE"
python3 tools/dealer_crm.py propose car_plus_av "BMW X3 xDrive20d 2022 50k km" 34140 42000

# Sa.My. Auto
python3 tools/dealer_crm.py update samy_auto_cs pipeline_status CONTACTED
python3 tools/dealer_crm.py log samy_auto_cs WA OUT "Day 1 V2 — BMW X3 2022 €34.100 DE"
python3 tools/dealer_crm.py propose samy_auto_cs "BMW X3 xDrive20d 2022 50k km" 34140 42000
```

---

## NOTA: VEICOLI AGGIUNTIVI CONSIGLIATI

Per avere piu' opzioni e veicoli diversificati per dealer, eseguire:
```bash
# Per Stile Car (Volvo/Mercedes nel suo stock)
python3 tools/batch_runner.py --model "Mercedes GLC" --mode fast

# Per Car Plus (Jaguar/LR nel suo stock)
python3 tools/batch_runner.py --model "Land Rover Velar" --mode fast

# Per Sa.My. Auto (Porsche/Lambo nel suo stock — IL suo trigger)
python3 tools/batch_runner.py --model "Porsche Macan" --mode fast
python3 tools/batch_runner.py --model "Porsche Cayenne" --mode fast
```

Questi batch produrranno veicoli piu' specifici per ogni dealer, utili per il Day 3 (secondo veicolo).
