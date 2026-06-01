# S217 — Test empirico reverse-search anti-tracciamento foto preview

## Stato (chiuso a context 60%, vincolo #7)

Validato output Gemini Deep Research su anti-reverse foto preview. Posizione CTO:
- **img2img ESCLUSO** (verificato): Draw Things 12.4+ / DiffusionBee 13.1+ incompat Big Sur 11;
  rischio legale reale D.Lgs 145/2007 → AGCM €5.000–500.000 se rimuove difetti reali (pubblicità ingannevole B2B).
- **Macro-crop dettagli reali = protezione STRUTTURALE** (no geometria globale → no exact match; zero
  alterazione pixel → zero rischio legale). È il cuore raccomandato.
- **Line-art esterno = NON verificato** ("100%" di Gemini = stesso claim non testato di S216). Da misurare.
- Principio Luke: solo i DATI validano. Domanda A (tecnica) testabile ora a costo zero; Domanda B (il dealer
  reverse-searcha davvero?) = N=0 dealer, dato non forzabile → non sovra-ingegnerizzare prima del Day 1 reale.

## Artefatti pronti (throwaway, /tmp — NON in repo)
- Script: `/tmp/s217_revtest.py` (scraper reale AS24 DE → 3 varianti, solo PIL+numpy, no cv2, Big Sur OK).
- Sample in `/tmp/s217_revtest/` da listing REALE BMW X5 xDrive40d grigio (DE):
  - `00_original.jpg` (1280×960, foto sorgente reale)
  - `01_macrocrop.jpg` (crop centrale 400×400)
  - `02_lineart.png` (adaptive gaussian threshold)
  - Listing sorgente: autoscout24.de/.../d8924ac1-44fe-40c5-a150-09573b3188ec

## PROSSIMO STEP (manuale Luke — TinEye/Lens non hanno API free)
1. Caricare i 3 sample su **TinEye** + **Google Lens**.
2. Annotare per ciascuno: match con la listing AS24 sorgente? (SI/NO).
3. Esito atteso/ipotesi:
   - macro-crop → NO match (protezione strutturale confermata) = va in produzione.
   - line-art → da verificare. Se SI match → morto come S216. Se NO → candidato.
   - original → SI match (baseline, conferma che il test funziona).
4. Solo le varianti NO-match = protezione VERIFICATA. Le altre fuori.

## NON modificare
- `image_sanitizer.py` e codice produzione: INTATTI. Il test è throwaway. Integrazione discussa solo
  DOPO che il test dà il dato.

## Decisione di scope aperta (Luke)
Il fossato ARGOS è "il dealer non trova l'annuncio" o "anche se lo trova, scavalcarti non conviene"
(import/IVA/trasporto, come Bolidem/AUTO1 che NON nascondono le foto)? Determina quanto investire in anti-reverse.

## Riferimenti memory
- `s216_anti_reverse_transform_refuted.md` (TinEye becca processed 2/2; no-foto rifiutato da Luke)
