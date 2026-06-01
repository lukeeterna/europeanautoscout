# Prompt Gemini DEEP RESEARCH — soluzione foto-preview non-rintracciabile (S217)

> Modello: **Deep Research** (NON "matematica e programmazione").
> Lanciare in Gemini app, incollare il blocco sotto. Output → input S217 per validazione + implementazione.

---

Sono CTO di un servizio B2B di scouting auto (importazione EU→IT). Trovo annunci di auto usate su
portali (AutoScout24, mobile.de e portali di nicchia EU) e li propongo a concessionari italiani con un
anteprima a pagamento. PROBLEMA: nell'anteprima devo MOSTRARE l'auto reale (carrozzeria, interni, km sul
cruscotto, condizione), ma il concessionario NON deve poter risalire all'annuncio sorgente tramite reverse
image search, altrimenti salta il mio servizio e compra direttamente.

HO GIA' VERIFICATO EMPIRICAMENTE (non ripetere questo, dallo per assodato):
- crop bordi + watermark semi-trasparente + ricompressione JPEG NON rompono il match: TinEye trova
  comunque l'annuncio sorgente esatto, e Google Lens usa embedding semantici robusti a queste trasformazioni.
- Quindi "trasformare i pixel della foto originale" NON funziona.

VINCOLI HARD:
- Costo ZERO o free-tier (no servizi a pagamento).
- Eseguibile su macOS 11 Big Sur SENZA GPU locale (solo CPU locale, oppure API/free-tier cloud).
- L'immagine finale deve restare CREDIBILE e mostrare l'auto vera con la sua condizione reale,
  NON una foto stock generica di un'altra auto dello stesso modello.

RICERCA RICHIESTA (dati concreti, tool con nome, costi, link):
1. Image-to-image / re-rendering: esistono modelli/servizi (es. SDXL img2img, Flux, ControlNet, ecc.) che
   rigenerano la STESSA auto (stesso modello/colore/angolo/condizione) producendo pixel nuovi non
   rintracciabili via reverse search? Quali sono free-tier o eseguibili senza GPU? Qualità e tempo reali?
2. La rigenerazione img2img sfugge davvero a TinEye + Google Lens, o l'embedding semantico ri-matcha
   l'originale perche' il contenuto e' identico? Evidenze/test pubblicati.
3. Isolamento auto + rimozione/sostituzione sfondo (paesaggio, autosalone, loghi, targa): riduce o azzera
   il match reverse, oppure il corpo-auto resta matchabile? Tool free per background removal (es. rembg).
4. Approcci "detail crop" (mostrare solo dettagli di condizione senza la composizione completa): efficaci
   contro reverse search e accettabili commercialmente?
5. Rischi LEGALI/etici di mostrare un'immagine rigenerata o alterata di un'auto reale in contesto B2B
   pre-vendita (misrepresentation, pratiche commerciali scorrette UE/IT).
6. Cosa fanno realmente i broker/mandatari auto (es. Bolidem, autotedesche.it, AUTO1) con le foto prima
   della vendita: mostrano l'originale, lo alterano, usano render?

OUTPUT FINALE: UNA raccomandazione singola motivata con dati (non una lista di opzioni equivalenti), che
indichi il metodo definitivo + tool specifico + costo + fattibilita' su Big Sur senza GPU + livello di
rischio legale. Se nessun metodo soddisfa tutti i vincoli, dillo esplicitamente e indica il miglior
compromesso con il trade-off preciso.
