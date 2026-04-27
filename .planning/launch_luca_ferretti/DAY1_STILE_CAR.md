# Day 1 WhatsApp — Stile Car (Orta Nova FG)

**Persona** (DA DB iMac, S144): **NARCISO**, score 8.5 — discrepanza con MEMORY S140 (diceva RELAZIONALE). DB è source of truth.
**Stock noto (da MEMORY S130)**: BMW X4, BMW 118d, BMW 216d — specializzato compatte BMW (stock_size 40 in DB)
**Città**: Orta Nova (FG, Puglia)
**Numero WA**: 393334254654 (DB: phone `333-4254654`, formato WA `39` + numero)
**Pipeline status DB**: COLD (mai contattato realmente)

⚠️ **NON inviare prima di aver**:
1. Attivato profilo LinkedIn Luca Ferretti e fatto follow a Stile Car
2. Aspettato 3 giorni di pre-warming passive LinkedIn (like + 1 commento non-pitch)
3. Verificato che il listing reale sotto sia ancora attivo (il dossier ha link)

---

## VEICOLO REALE — scrape S144 (2026-04-27 11:29)

- **Modello**: BMW X3 xDrive20i 2022, 66.419 km, automatico, benzina
- **Configurazione**: AHK (gancio traino), HiFi, Sportsitze, nera
- **Prezzo listing**: €34.904
- **Origine**: Autohaus Becker-Tiemann Schaumburg GmbH (dealer professionale)
- **CoVe**: PROCEED, confidence 0.84
- **MarketVerifier IT**: €36.025 (n=337 listing IT 2022, σ=0.05) — base solida
- **Listing**: https://www.autoscout24.de/angebote/bmw-x3-xdrive20i-ahk-hifi-sportsitze-benzin-schwarz-70dcd99b-3d68-45ac-ae20-2113e8f3d719
- **Dossier PDF**: `dossiers/ARGOS_BMW_X3_2022_Stile_Car_20260427_112932.pdf`

**Pricing ARGOS** (fee_calculator Tier 1 "Scouting Only", region=sud):
- Margine dealer stimato: €4.188 (12% di €34.904)
- Fee ARGOS: €800 success-only
- **Margine netto dealer: €3.388**

---

## DAY 1 — messaggio (5 righe + firma, calibrato NARCISO, NO trigger words)

```
Buongiorno, ho visto Stile Car su AS24 — siete tra i pochi a Foggia che gestiscono BMW compatte con continuità.

X3 xDrive20i 2022, 66.000 km, €34.900 — automatica, AHK, HiFi, sport. Su AS24 in Italia la stessa configurazione parte da €37.000.

Margine netto per voi: ~€3.400, fee €800 a consegna.

La voglio proporre prima a voi. Le interessa la scheda?

Luca
```

**Calibrazione NARCISO** (vs il messaggio RELAZIONALE precedente):
- "siete tra i pochi a Foggia che gestiscono [...] con continuità" → riconoscimento competenza, no lusinga grossolana
- "voi" e "vostro" (anziché "lei") → riconoscimento dell'attività come entità di valore
- "voglio proporre prima a voi" → esclusività, status

**Verifica regole prima di inviare**:
- ✅ NO "Germania", "import", "premium", "cerco auto", "estero"
- ✅ Max 5 righe corpo
- ✅ Domanda chiusa ("Le interessa la scheda?")
- ✅ Veicolo REALE con numeri REALI (scrape live S144, listing attivo)
- ✅ Personalizzato (NARCISO + riferimento a BMW compatte = stock noto)
- ✅ Persona reale (Luca firma)
- ✅ ARGOS NON è il primo elemento
- ✅ Numeri in EUR netti, no percentuali

**Pre-flight check listing**: prima dell'invio verifica con `curl -sI "<listing_url>" | head -1` che ritorni 200 (auto ancora disponibile). Se 404 → rieseguire scrape e scegliere nuovo top candidate.

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
Luca Ferretti, Import Manager ARGOS Automotive.
Sito: argos-automotive.pages.dev
LinkedIn: linkedin.com/in/luca-ferretti-53b6513b9

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
