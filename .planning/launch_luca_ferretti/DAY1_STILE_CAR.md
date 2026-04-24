# Day 1 WhatsApp — Stile Car (Orta Nova FG)

**Persona**: RELAZIONALE, score 8.5 (il più alto dei 5 cold)
**Stock noto (da MEMORY S130)**: BMW X4, BMW 118d, BMW 216d — specializzato compatte BMW
**Città**: Orta Nova (FG, Puglia) — piccolo centro, lavoro di prossimità importante
**Numero WA**: 393334254654

⚠️ **NON inviare prima di aver**:
1. Attivato profilo LinkedIn Luca Ferretti e fatto follow allo stile Car
2. Verificato che un veicolo X4 recente esista realmente con DAT report (vedi bottom)
3. Aspettato 3 giorni di pre-warming passive LinkedIn

---

## DAY 1 — messaggio (max 5 righe + firma)

```
Buongiorno, ho visto che tratta molto BMW — X4 e Serie 1 in particolare.

Ho trovato una X4 xDrive20d 2023, 58.000 km, nera — €29.800 a Monaco di Baviera. In Puglia la stessa parte da €35.500. DAT report pulito, 1 proprietario, tagliandi regolari BMW.

Margine netto stimato per lei: ~€4.200, bisarca e pratiche incluse.

Le mando la scheda?

Luca
```

**⚠️ PRIMA DI INVIARE**: il veicolo X4 2023 €29.800 Monaco è TEMPLATE. Esegui scrape live autoscout_scraper.py su X4 2022-2023 Germania <€32k, scegli un'unità reale, aggiorna prezzo/km/città di provenienza nel messaggio.

---

## Risposte pronte (inviare dopo WA inbound del dealer)

### "Quanto costa?"
```
€1.000 a consegna avvenuta. Zero anticipo.

Se il veicolo non la convince dopo averlo visto, lei non paga nulla.

Il bonifico lo fa quando la macchina è nel suo piazzale con documenti in mano.
```

### "Chi sei? Referenze?"
```
Luca Ferretti, Import Manager ARGOS Automotive — argos-automotive.pages.dev

Sto partendo adesso come servizio dedicato al Sud, quindi niente 200 recensioni ancora. È vero.

Quello che posso dirle: ispeziono io il veicolo prima che parta dalla Germania, le mando foto originali e DAT report, lei decide. Se una cosa non torna, stoppa tutto e zero costi.
```

### "Dove ha preso il mio numero?"
```
Ho visto il suo piazzale su AutoScout24 e Google, profilo Stile Car. Tratta esattamente il segmento che seguo io — BMW compatte e sport.

Ho preferito WhatsApp invece del telefono per non essere invadente in orario lavoro. Se preferisce una chiamata, mi dice quando e chiamo io.
```

### "Già importiamo da soli / abbiamo un fornitore"
```
Capito. Se il fornitore attuale funziona, è già a metà dell'opera — io mi pago solo se porto qualcosa in più.

Cosa succede se per una volta le mando una proposta a fianco della sua e confronta prezzo netto + storia veicolo? Zero impegno. Se il mio è peggio, tiene il suo fornitore e abbiamo perso 5 minuti.
```

### "Non mi interessa / Nulla"
```
Capito, grazie per la risposta chiara.

Se più avanti le serve un X4 o Serie 3 tedesca con DAT pulito, il mio numero ce l'ha già.

Buon lavoro.

Luca
```

(Uscita dignitosa. NON insistere.)

---

## Post-invio

- Annota nel DB dealer_network.sqlite: outbound_count++, last_contact_at, messaggio inviato
- Attendi 48h senza follow-up
- Se risposta: segui albero risposte pronte
- Se silenzio a 7 giorni: Day 3 soft (da definire con founder)
- Se silenzio a 14 giorni: break-up message
