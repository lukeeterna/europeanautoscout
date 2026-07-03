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

> GERMANIA: NESSUN registro km pubblico; storico via HU-Berichte TÜV/DEKRA + aggregatori commerciali a pagamento, copertura non garantita [T2] — tenuta come NOTA: il payload MATRICE-EU non la dà come fatto numerato, e la nota non ha FONTE/DATA/NUMERO propri per passare il gate RUBRICA (info DE presente anche nella classe COMMERCIALE della nota implicazione sotto).

## Verificabilità per paese — MATRICE OPERATIVA (GRADED-BY-GIUDICE-MATRICE-EU 2026-07-03)

> ADATTAMENTO-FORMA MATRICE-EU (per il giudice): il payload dava le righe in formato 4-part (FATTO|FONTE|VERIFICA|tier), senza tag DATA/NUMERO. Adattamenti applicati SOLO alla FORMA (mai numeri/fonti/sostanza): (a) DATA ISO = giorno esatto dove il payload lo dà (Belgio 2006-12-01), altrimenti FLOOR dell'anno in FONTE (NL/FR "2026" -> 2026-01-01) — il periodo reale resta visibile nel FATTO/FONTE; (b) NUMERO = cifre GIÀ presenti nel FATTO del payload (date rilevazioni/controlli, validità link, costo Car-Pass); (c) VERIFICA = metodo del payload con verbo azionabile per la RUBRICA (query->interroga, richiesta->richiedi); Belgio senza VERIFICA nel payload -> derivata dal documento citato nel FATTO stesso (richiedi il Car-Pass); (d) GERMANIA e Implicazione ARGOS TENUTE come note ">": il payload non le dà come fatti numerati/citabili (Germania senza FONTE/DATA/NUMERO propri; implicazione con FONTE="sintesi delle righe sopra" [T1-derivato] non citabile) -> non passerebbero il gate RUBRICA come FATTO.

- FATTO: OLANDA — RDW kentekencheck pubblico e gratuito: da sola targa, senza account, chiunque ottiene n. proprietari + GIUDIZIO ufficiale sulla serie km (logico/illogico); giudizio basato su rilevazioni dal 2014-01-01 (prima: Stichting NAP, dal 1991); "nessun giudizio" se il veicolo è stato registrato all'estero; dal 2025-01-13 RDW registra anche i km di veicoli importati dal Belgio | FONTE: rdw.nl (kentekencheck + voertuigrapport), 2026 | DATA: 2026-01-01 | NUMERO: rilevazioni km dal 2014-01-01 (Stichting NAP dal 1991); km import BE dal 2025-01-13 | VERIFICA: interroga ovi.rdw.nl per targa e leggi il giudizio ufficiale sulla serie km [T1]
- FATTO: FRANCIA — Histovec (Min. Interno, gratuito): SOLO il titolare del certificato d'immatricolazione può generare il report; l'acquirente lo riceve via link condiviso a validità limitata (15-30 gg, fonti secondarie discordi), senza account; include storico km dai controlli tecnici dal 2021-01-12, sinistri periziati, situazione amministrativa (pegno, opposizione, furto) | FONTE: histovec.interieur.gouv.fr FAQ + service-public.gouv.fr, 2026 | DATA: 2026-01-01 | NUMERO: link valido 15-30 gg; storico km dai controlli tecnici dal 2021-01-12 | VERIFICA: richiedi al venditore il link Histovec e verifica lo storico km [T1]
- FATTO: BELGIO — Car-Pass obbligatorio SOLO nella vendita ad acquirente privato (regio decreto, vigore 2006-12-01); nel B2B tra professionisti NON è legalmente dovuto (dichiarazione piattaforma dealer OPENLANE); rilasciato dai centri revisione, nelle transazioni richiesto non antecedente 2 mesi; costo ~7,3€ (dato 2018, RI-CORROBORARE prezzo corrente prima di uso pubblico) | FONTE: Parlamento EU E-5043/2007 [T1] + OPENLANE FAQ [T3] + guide expat [T3] | DATA: 2006-12-01 | NUMERO: Car-Pass non antecedente 2 mesi; costo ~7,3€ (dato 2018, ri-corroborare) | VERIFICA: richiedi il Car-Pass al venditore belga; nel B2B non è dovuto per legge, pretendilo per contratto [T1/T3]
> Implicazione operativa ARGOS — tenuta come NOTA (FONTE="sintesi delle righe sopra", tier [T1-derivato] non citabile -> derivazione, non passa il gate RUBRICA come FATTO): tre classi di accesso pre-acquisto — AUTONOMO (NL, da targa, zero costo, zero venditore) · SU-RICHIESTA (BE Car-Pass, FR Histovec: da pretendere contrattualmente; rifiuto del venditore = red flag codificato) · COMMERCIALE (DE: nessun registro pubblico, solo TÜV/aggregatori). Il tier di certezza A/B/C del dossier si assegna sul DOCUMENTO OTTENUTO, non sul paese di targa.
