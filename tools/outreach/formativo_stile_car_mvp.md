# Pacchetto Comunicativo ARGOS — Stile Car
**Dealer:** Stile Car Srls — Domenico, Orta Nova (FG)
**Veicolo:** BMW X3 xDrive20d 2022 | 50.000 km | Provenienza Germania
**Data:** 2026-04-16
**Stato:** BOZZA — in attesa validazione TEST_FOUNDER

---

## COME USARE QUESTO PACCHETTO

Allegare al messaggio Day 1. Frame:

> *"Ti propongo questa BMW. Ti mando anche come la puoi comunicare ai tuoi clienti —
> così risparmi 2 ore di lavoro."*

Contenuto: 3 pezzi pronti all'uso — scheda cliente, messaggio WA, post Instagram.

---

## PEZZO 1 — SCHEDA VEICOLO PER I TUOI CLIENTI

> Da stampare o inviare PDF. Sostituisce la scheda tecnica con linguaggio cliente.

---

**BMW X3 xDrive20d 2022**
50.000 km certificati | Provenienza Germania | Trazione integrale

**Perche' vale €38.500**

**1. Km reali, storico documentato**
Il TUV tedesco verifica i km ad ogni revisione biennale.
Nessuna opacita': 50.000 km certificati, tagliandi timbrati dall'officina BMW autorizzata.

**2. Trazione integrale xDrive — optional incluso**
In Italia la stessa configurazione costa €3.000-4.000 in piu'.
Qui e' di serie. Perfetta per chi usa l'auto tutto l'anno, anche in montagna.

**3. Garanzia legale 2 anni — nessuna sorpresa**
Ogni auto venduta da Stile Car include garanzia legale di conformita' 2 anni.
La rete assistenza BMW autorizzata in Italia e' pienamente valida.

**Domande frequenti:**

*"E' stata in Germania — chi sa che storia ha?"*
Abbiamo il report completo: chilometri verificati, revisioni, assenza incidenti.
Stesso controllo di un'auto italiana, con l'aggiunta del sistema TUV.

*"Costa meno perche' ha qualcosa che non va?"*
No. Costa meno perche' in Germania ci sono piu' auto premium disponibili.
Stessa identica auto, stesso allestimento, €3.000-5.000 in meno rispetto al mercato italiano.

*"La garanzia vale in Italia?"*
Si'. La garanzia legale di conformita' e' europea. Qualsiasi officina BMW
autorizzata in Italia interviene. Zero differenze con un'auto acquistata in Italia.

---

## PEZZO 2 — MESSAGGIO WA PER I TUOI CLIENTI

> Inviare via WhatsApp a clienti esistenti che cercano un SUV premium.
> Adattare il nome del cliente nella prima riga.

---

**Testo da copiare e incollare:**

```
Buonasera [Nome],

Ho trovato qualcosa che potrebbe fare al caso suo:
BMW X3 xDrive20d 2022, 50.000 km — appena rientrata dalla Germania.

Trazione integrale, tutto certificato, garanzia 2 anni inclusa.
La tengo da parte qualche giorno prima di metterla in vetrina.

Vuole venire a vederla?

Domenico — Stile Car
```

**Note per il dealer:**
- Usare solo per clienti che hanno gia' cercato un SUV premium (BMW X3/Mercedes GLC/Audi Q5)
- Mandare al mattino (9-11) o sera (19-21), mai a pranzo
- Se risponde "quanto costa?": rispondere con il prezzo e invitare in salone — non negoziare via WA

---

## PEZZO 3 — POST INSTAGRAM

> Caption pronta. Indicazioni foto incluse. Non inserire prezzi nel post.

---

**Caption:**

```
Alcune auto parlano da sole.

BMW X3 xDrive20d 2022 — trazione integrale, 50.000 km certificati,
storico documentato dalla Germania.

Il livello che i vostri clienti cercano, con la garanzia che meritate di offrire.

Disponibile in salone. Scrivete in DM per i dettagli.

#BMW #BMWX3 #AutImport #Puglia #Foggia #AutUsata #Premium
```

**Foto da usare (in ordine):**
1. Foto frontale 3/4 — preferibilmente su fondo neutro o piazzale pulito
2. Interno — plancia con display e sedili
3. Dettaglio logo BMW + targhetta xDrive sul portellone

**Note per il dealer:**
- Non aggiungere il prezzo nella caption — porta in DM, mantieni il controllo della trattativa
- Pubblicare giovedi' o venerdi' pomeriggio (14-17) per massimo reach
- Rispondere ai commenti entro 2-3 ore dalla pubblicazione

---

## MESSAGGIO DAY 1 AGGIORNATO — STILE CAR

> Sostituisce il template precedente. Include riferimento al materiale formativo.

```
Buongiorno Domenico,

ho trovato una BMW X3 xDrive20d 2022, 50.000 km, in Germania — €34.140.
In Puglia gli stessi esemplari partono da €37-39.000.

Sto selezionando 2-3 concessionari della zona per questo tipo di auto —
ho visto il suo stock, tratta questa fascia.

Le mando la scheda completa e come proporla ai suoi clienti, pronta all'uso.
Nessun lavoro aggiuntivo per lei.

Le va bene?

Luca Ferretti
```

**Differenza vs Day 1 originale:**
- Aggiunta riga "Le mando la scheda e come proporla ai suoi clienti, pronta all'uso."
- Aggiunta "Nessun lavoro aggiuntivo per lei." — leva per NARCISO (efficienza senza effort)
- Domanda chiusa mantenuta: "Le va bene?" anziche' "Le mando la scheda completa?"

---

## CHECKLIST PRIMA DI INVIARE

```
[ ] Testato su TEST_FOUNDER (393314928901) — PDF arriva correttamente?
[ ] Tono approvato dal founder
[ ] WA daemon online (curl localhost:9191/status = OK)
[ ] Domenico non ha gia' ricevuto messaggi in DB (verifica: messages table)
[ ] Orario invio: lunedi'-venerdi' 9-11 o 14-17
```

---

## NOTE PRODUZIONE PDF

Per generare il PDF dalla scheda (Pezzo 1 + Pezzo 3 senza note interne):
```bash
python3 tools/scripts/pdf_generator_enterprise.py \
  --input tools/outreach/formativo_stile_car_mvp.md \
  --output dossiers/formativo_stile_car_mvp.pdf \
  --dealer "Stile Car" \
  --vehicle "BMW X3 xDrive20d 2022"
```

Verificare che il PDF non contenga le sezioni "Note per il dealer" (interne).
