# S218 — Fossato-servizio (decisione anti-reverse CHIUSA)

## DECISIONE BLOCCATA (S217, Luke approvato)
Il fossato ARGOS NON è "il dealer non trova l'annuncio". È **"anche se lo trova, scavalcarti non
conviene"** = gestione import (IVA intracomunitaria + radiazione estera/Zulassung + bisarca + immatricolazione IT).

Dati di mercato a supporto: Bolidem/autotedesche NON nascondono le foto (è il cliente che trova l'auto);
AUTO1 usa foto proprie. Nessun operatore di successo difende il margine nascondendo il pixel.
Anti-reverse refutato S216 (transform) + img2img fuori (Big Sur incompat + AGCM €5k-500k D.Lgs 145/2007).

## CONSEGUENZA OPERATIVA
- **Anti-reverse = minimo sufficiente, costo zero, CHIUSO**:
  - Anteprima = macro-crop dettagli reali (km/usura/gomme) — protezione strutturale, Big Sur OK.
  - Prezzo visibile = gancio; posizione+venditore+URL+foto integrale = gated post-pagamento (`C-GATE-FONTE-001`, già in codice).
  - STOP investimento line-art/img2img. Il test TinEye/Lens serve solo a timbrare "verificato" sul macro-crop.

## PROSSIMI STEP S218
1. **(5 min, manuale Luke — chiude capitolo)** Carica `/tmp/s217_revtest/` (00_original, 01_macrocrop,
   02_lineart) su TinEye + Google Lens. Atteso: original=MATCH, macrocrop=NO-MATCH. Segna esito.
   Se macrocrop NO-MATCH → timbro "verificato", capitolo anti-reverse chiuso definitivamente.
2. **(lavoro vero) Fossato-servizio**: rendere concreto e VISIBILE l'handling import nel materiale dealer
   (landing + messaggi + PDF): "gestisco IVA intracomunitaria, radiazione estera, trasporto assicurato,
   immatricolazione targa IT". È questo che rende lo scavalco antieconomico per family-business.
   Incrociare con i blocker Day 1 residui (vedi memory S214: C-SAN-001 + C-E2E-ZERO + C-COMM-INTEL-001).

## NON modificare
- `image_sanitizer.py` / codice produzione INTATTI finché test macro-crop non dà timbro.

## Riferimenti
- memory: `s217_anti_reverse_validation.md`, `s216_anti_reverse_transform_refuted.md`
- gating fonte: `C-GATE-FONTE-001` (commit 847f76e, parte 2)
- Sample throwaway: `/tmp/s217_revtest/` (BMW X5 xDrive40d AS24 DE reale)
