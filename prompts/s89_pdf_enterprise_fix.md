# S89 — Fix PDF Enterprise + Standard Dossier Dealer

## Contesto — LEGGI PRIMA DI TUTTO

S88 ha fixato DEKRA/DAT nel daemon, aggiornato schema DuckDB, e testato la pipeline E2E.
Il PDF e' stato generato ma ha **10 problemi** trovati con audit visivo.
Il founder ha detto: "dobbiamo definire gli standard altrimenti non ci siamo".

**NESSUN PDF deve uscire verso un dealer finche' questi problemi non sono risolti.**

## PDF generato (da ispezionare)
```
dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf  (2 pagine, 303 KB)
Generatore: tools/scripts/pdf_generator_enterprise.py
```

## Cosa funziona (NON toccare)
```
wa-intelligence/wa-daemon.js         ← DEKRA/DAT rimossi, daemon LIVE
wa-intelligence/response-analyzer.py ← DEKRA/DAT rimossi, daemon LIVE
src/cove/vin_verification.py         ← Testato E2E, funziona
src/cove/argos_grade.py              ← Testato E2E, funziona
src/cove/cove_engine_v4.py           ← NON MODIFICARE
```

## 10 PROBLEMI DA FIXARE — in ordine di priorita'

### CRITICI (bloccanti per dealer)

**1. Logo venditore EU visibile nella foto**
La foto principale mostra "AuRa Automobile Rabe" — il dealer vede da chi compriamo.
Viola regola ZERO SOURCE. Soluzioni:
- Crop automatico zona superiore dove di solito c'e' il logo
- Oppure: selezionare foto senza watermark (se ce ne sono multiple)
- Oppure: blur zona logo con PIL
- Il sanitizer gia' esiste (rimuove targhe) — estenderlo ai loghi

**2. Segno margine invertito**
Mostra "€-4,631" nel box Margine Netto. Il meno fa sembrare una PERDITA.
Bug nel calcolo: probabilmente `price_eu - price_it` invece di `price_it - price_eu`.
Fix: verificare la formula in pdf_generator_enterprise.py e invertire.

**3. Recall NHTSA spacciati per richiami EU**
"7 richiami costruttore" viene dal database NHTSA (USA).
Per auto EU i recall NHTSA sono IRRILEVANTI — i richiami EU sono diversi.
Fix:
- NON mostrare recall NHTSA nel PDF dealer (confonde)
- Oppure: disclaimer chiaro "Fonte: database USA — verificare con costruttore per richiami EU"
- Nella sezione "Check frodi" rimuovere il conteggio recall NHTSA

### IMPORTANTI

**4. Grade badge incoerente**
Il box ARGOS in pagina 1 mostra la lettera "A" ma il grade reale e' "C" (score 0.71).
Bug grafico: probabilmente il badge e' hardcoded o usa un campo sbagliato.

**5. Punteggio 76/100 vs 0.71**
Pagina 1 dice "76/100", pagina 2 dice "GRADE C (0.71)".
0.71 * 100 = 71, non 76. Incoerenza — decidere quale e' il valore corretto.

**6. Trasporto bisarca €1,200**
Troppo alto per Monaco→Foggia. La KB dice ~€550-650.
Fix: usare i dati dalla KB (`argos_knowledge_base.md` sezione TRASPORTO) per stima reale basata su tratta.

**7. "Da verificare" su HU/revisione e Proprietari**
Visivamente sembra un difetto del dossier, non uno stato intermedio.
Fix: se il dato non c'e', mostrare "Non disponibile" o omettere la riga.

### MINORI

**8. "HIGH RECALL COUNT" + "Superato" contraddittorio**
Nella sezione "Check frodi ARGOS", status "Superato" ma con alert "HIGH RECALL COUNT: 7 recalls" in rosso. Contraddittorio.

**9. Immatricolazione "€430 IPT + targhe"**
Manca dettaglio. Aggiungere breakdown se possibile.

**10. Nessun disclaimer fonte recall**
Se si mantengono i recall, aggiungere "Fonte: NHTSA (USA)" esplicito.

## Come procedere

1. LEGGERE `tools/scripts/pdf_generator_enterprise.py` completamente
2. Fixare i 3 critici PRIMA di tutto
3. Poi i 4 importanti
4. Poi i 3 minori
5. Rigenerare il PDF: `python3 tools/scripts/pdf_generator_enterprise.py --listing fresh_19bc9cf651e5 --dealer "Stile Car" --output dossiers/`
6. **AUDIT VISIVO OBBLIGATORIO**: convertire in PNG con PyMuPDF e ispezionare ogni pagina
7. Solo quando il PDF passa l'audit → commit

## Dopo il PDF fix

- Monitorare Day 3 follow-up (30/03 lunedi')
- TIER1 outreach (dopo validazione Day 3 TIER0)
- RDW open data NL + Car-Pass BE

## Infra
```
iMac: ssh gianlucadistasi@192.168.1.2 (deploy via SCP, branch divergenti)
PM2 restart: source ~/.zshrc && pm2 restart argos-wa-daemon
DB DuckDB: src/cove/data/cove_tracker.duckdb (colonne VIN aggiunte S88)
DB daemon: /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite
PyMuPDF: installato (pip3 install --break-system-packages pymupdf)
```

## Regole
- L'agente si chiama LUCA FERRETTI, mai "AMBRA"
- ZERO SOURCE: nessun logo/nome venditore EU visibile nel PDF
- Dati nel dossier devono essere REALI e VERIFICABILI
- AUDIT VISIVO dopo ogni generazione PDF
- cove_engine_v4.py NON MODIFICARE
