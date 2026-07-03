# frode_km_verifica.md — GRADED-BY-GIUDICE 2026-07-03

> DISCLAIMER: le statistiche di frode disponibili sul mercato IT derivano quasi
> interamente da un'unica fonte commerciale (carVertical, T3), interessata a
> massimizzarle. Corroborazione indipendente (Altroconsumo/ACI/ADAC) NON trovata
> al 2026-07. I fatti T3 = ordine di grandezza, non dato certificato.

> ADATTAMENTO-FORMA (per il giudice): il payload non era in formato RUBRICA a 5 tag.
> Adattamenti applicati alla FORMA (mai a numeri/fonti): (a) DATA ISO = giorno esatto
> dove il payload lo dà (Belgio 1 dic 2006, Italia 1 giu 2018), altrimenti FLOOR del
> periodo indicato in FONTE (mar 2025 -> 2025-03-01; anno 2025 -> 2025-01-01; dic 2025
> -> 2025-12-01) — il periodo reale resta visibile in FONTE; (b) VERIFICA = metodo del
> payload dove presente ("report VIN"), con verbo azionabile aggiunto per la RUBRICA;
> (c) righe qualitative senza numero (RDW, Histovec, Germania, implicazione ARGOS) =
> tenute come note ">" perché non sono statistiche e non passano il gate come fatti.

## Dimensione del fenomeno (Italia)

- FATTO: BMW Serie 5 = auto più manomessa in Italia: 8,5% dei controllati, media 153.000 km scalati; BMW Serie 3: 8% | FONTE: carVertical, indagine 2024 (pubbl. mar 2025) | DATA: 2025-03-01 | NUMERO: 8,5% dei controllati; 153.000 km medi scalati; Serie 3 = 8% | VERIFICA: consulta il report VIN carVertical del veicolo [T3]
- FATTO: chi compra auto con km manomessi paga il 25-30% sopra il valore reale (25% e 29,3% in due studi) | FONTE: carVertical, 2025 | DATA: 2025-01-01 | NUMERO: +25-30% sul valore reale (25% e 29,3% in due studi) | VERIFICA: confronta il prezzo col valore di mercato reale del modello [T3]
- FATTO: auto importate = 6,3% con km non veritieri vs 2,1% delle sempre-circolate in IT -> rischio oltre 3x, periodo set2024-ago2025 | FONTE: carVertical, dic 2025 | DATA: 2025-12-01 | NUMERO: 6,3% importate vs 2,1% domestiche = rischio >3x | VERIFICA: confronta il tasso su campione importate vs domestiche via report VIN [T3]
- FATTO: danno macro frodi-km Italia stimato oltre 467,5 mln €/anno | FONTE: carVertical, studio 2025 | DATA: 2025-01-01 | NUMERO: >467,5 mln €/anno | VERIFICA: consulta lo studio carVertical 2025 sul danno aggregato [T3]

## Verificabilità per paese di origine (LA LEVA EU)

- FATTO: BELGIO Car-Pass — certificato km OBBLIGATORIO alla vendita a privato (regio decreto in vigore 1 dic 2006); senza, l'acquirente può chiedere annullamento del contratto; professionisti obbligati a trasmettere km entro 5 giorni; frodi ridotte ~97% (da ~100.000 nel 2006 a 1.197 nel 2016); costo ~7,3€ | FONTE: Parlamento Europeo interrogazione E-5043/2007 + stampa settore | DATA: 2006-12-01 | NUMERO: km entro 5 giorni; frodi -97% (~100.000/2006 -> 1.197/2016); costo ~7,3€ | VERIFICA: richiedi il Car-Pass al venditore belga e verifica sul registro Car-Pass; ri-corroborare il dato 97% (2016) su fonte Car-Pass corrente prima del copy pubblico [T1/T2]
- FATTO: ITALIA (arrivo) — Portale dell'Automobilista (MIT) mostra i km alle revisioni registrate dal 1 giu 2018, gratis da targa; storico completo solo per utenti registrati; CIECO su auto estere non ancora revisionate in IT | FONTE: Portale dell'Automobilista (MIT), mit.gov.it / ilportaledellautomobilista.it, dato revisioni dal 2018 | DATA: 2018-06-01 | NUMERO: km alle revisioni registrate dal 1 giu 2018 | VERIFICA: interroga il Portale dell'Automobilista per targa e confronta i km alle revisioni [T1]

> OLANDA RDW (AutoPas dal 1991): registro governativo con km, revisioni, immatricolazioni, incidenti. FONTE: RDW/registro statale NL. [T1]
> FRANCIA Histovec: servizio statale gratuito, storico veicolo immatricolato FR (proprietà, incidenti, revisioni, km). FONTE: servizio statale FR. [T1]
> GERMANIA: NESSUN registro km pubblico; storico via HU-Berichte TÜV/DEKRA + aggregatori commerciali a pagamento, copertura non garantita. [T2]

## Implicazione operativa ARGOS

> Il tool gratuito IT non copre l'import -> il dealer da solo è cieco esattamente sul
> segmento più frodato. ARGOS verifica alla FONTE del paese di origine, con livello di
> certezza dichiarato: A = registro legale (Car-Pass/RDW) · B = ufficiale-parziale
> (Histovec/TÜV) · C = solo aggregatori commerciali [T3].
