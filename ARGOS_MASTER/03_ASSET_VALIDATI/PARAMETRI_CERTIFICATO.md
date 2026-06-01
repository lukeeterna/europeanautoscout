# ARGOS — PARAMETRI CERTIFICATO (i 47, di cui 10 chiave)
> Asset validato, recuperato da sessione "Opportunità import auto premium da Germania" (mar 2026).
> Uso: contenuto del CERTIFICATO™ generato in Fase 4. Sono il "perché" della fee.

---

## I 10 PARAMETRI CHIAVE (quelli che si citano al dealer premium)
1. Delta prezzo vs media 90 giorni del mercato di origine.
2. Coerenza km/anno vs benchmark KBA 2023.
3. Numero di proprietari precedenti.
4. Sinistri dichiarati — cross-check su 3 database EU.
5. Storia tagliandi — continuità e ufficialità.
6. Mercato di prima immatricolazione (flotta vs privato).
7. Anomalie geografiche (es. auto tedesca con storia in Romania = flag).
8. Tempi di permanenza dell'annuncio (>90 giorni = segnale).
9. Coerenza optional dichiarati vs foto.
10. Verifica VIN su database furto EU.

## I RESTANTI 37
Riguardano: pricing avanzato, liquidità di mercato, e scoring comparativo tra veicoli simili disponibili contemporaneamente. (Set completo da mantenere/versionare con CC nel codice del motore CoVe.)

---

## COLLEGAMENTO AL MOTORE
- Il certificato è l'output leggibile del motore di scoring **CoVe v4** (in produzione dal 2026-03-03).
- Scoring Bayesiano: Si = μ − λ·σ, λ=0.25. Soglie: DEALER_PREMIUM=0.75, VIN_CHECK=0.60.
- Branding pubblico SOLO: Protocollo ARGOS™ / CERTIFICATO™ / VERIFICA ESTESA™ / ESCLUSO™.
- MAI esporre al dealer: CoVe, Chain-of-Verification, Claude, Anthropic, nomi di metodologia interna.

## NOTA SU COSA IL CERTIFICATO NON CONTIENE (vedi nodo pagamento)
- NON contiene la posizione/fonte dell'auto (rilasciata solo post-fee).
- Le immagini sono sanitizzate (anti reverse-image-search).
- I parametri sì, le coordinate per trovarla no. Questo è il punto.

## GAMMA VEICOLI TARGET (da landing storica)
- BMW (Serie 1·3·5·X1·X3·X5, ~60% volume), Mercedes (C·E·GLC·GLE, ~25%), Audi (A4·A6·Q3·Q5·Q7, ~15%).
- Anni 2018-2023. Range €15.000-60.000. Km max discusso: 60.000-150.000 (da fissare).
- Mercati: DE · BE · NL · AT · FR · SE · CZ.
