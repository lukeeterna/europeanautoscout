# Risposta alla tua critica — S259

Hai ragione su tutto. Non era cosmetico, era il verdetto. Ho eseguito il trace che chiedevi PRIMA di chiudere — ha deciso, e ha deciso contro di me.

## Il trace (320d xDrive, pool reale 19)
```
TARGET = 320/awd/base/diesel
L0 engine+dt+trim+fuel+km, anno±1   N=0
L1 -km, anno±1                      N=0
L2 anno±2                           N=0
L3 -trim_line                       N=1  median=36000  drivetrains={awd}        ← puro
L4 -drivetrain                      N=3  median=29990  drivetrains={awd, rwd}   ← FUSI
```
Il 29.990 nasceva a **L4, fondendo awd+rwd**. Esattamente la tua diagnosi. Il blend schiaccia il premio xDrive verso il basso (falso-REJECT). E la contraddizione €14k: il dump N=4/44.025 non aveva filtro anno e ignorava il trim → misurava un'altra popolazione. Due numeri "veri" su due popolazioni diverse = nessun numero certificabile. **DoD#1 NON era chiuso.** Lo riconosco senza sconti.

## Fix applicato (non rimandato a S260)
Principio recepito: **non si rilassa MAI attraverso le dimensioni che muovono il prezzo.** trim_line si molla presto (L3); drivetrain e classe-motore MAI. Ho **rimosso L4** dalla scaletta. Ora se per arrivare a min_n dovresti fondere drivetrain diversi → **NO-VERDICT**, non un blend.

Riverifica post-fix (min_n=3):
```
320d xDrive  trim=320/awd/base/diesel  N=1  relax=L3  median=36000  no_verdict=TRUE
318d         trim=318/rwd/base/diesel  N=1  relax=L3  median=34900  no_verdict=TRUE
```
Il 29.990 fuso è sparito. Su un pool da 19, lo spec-aware onesto dà NO-VERDICT quasi ovunque. Che è il punto.

## Cosa resta vero
- **Falso-PASS neutralizzato**: M340d → NO-VERDICT, non più ~36.000 come nel trim-blind S258. Il cuore regge.
- **Regex**: la deviazione era corretta, ancorata al terminal fact.
- **Gate E ha tenuto**: STATE.md col diff mostrato, PLAN.md intoccato, zero overwrite ciechi.

## min_n
D'accordo: **NO a 3 in produzione.** Default resta 8. 3 solo come pavimento di test, etichetta dura: nessun verdetto a N=3 esce verso un dealer. E con L4 rimosso, anche i pochi numeri che escono non sono più blend.

## Il pivot che sposta S260
Il collo di bottiglia non è più la logica — è la **profondità del pool IT**. curl_cffi prende solo il batch SSR (~19); su 19 listing lo spec-aware corretto dà NO-VERDICT o mediane fragili. **ARGOS oggi emette un verdetto affidabile per pochissime auto → non è un prodotto.** Quindi **B3 (paginazione Selenium sullo scrape IT) NON è più backlog: è il critical path** per un verdetto vendibile. Solo dopo che il pool cresce ha senso alzare min_n a un valore difendibile e fidarsi delle mediane esatte senza rilassare.

## In una riga
Logica del verdetto: a posto (L4 fuso rimosso). Falso-PASS: neutralizzato. Mediana certificabile: **non ancora**, ma la causa ora è nota e isolata (pool a 19). DoD#1 resta **BLOCKED-ON profondità pool**, non "chiuso".

## S260 (proposta, idempotente)
1. Critical path = **B3 pool depth**: paginazione reale sullo scrape IT (Selenium/altra via), portare il pool da ~19 a centinaia.
2. Poi rifare il trace 320d xDrive: a pool grande deve fermarsi a L0/L1 con N≥min_n, drivetrain={awd} puro → mediana certificabile.
3. Solo allora ratificare min_n difendibile (≥8) e chiudere DoD#1/#2/#3 sul PDF reale.
