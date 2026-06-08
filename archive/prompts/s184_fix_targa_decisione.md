# S184 — Fix targa D-32: fallback geometrico cv2 in Stage 2

**Stato in entrata**: sanitizer Stage 2 (Vision OCR) confermato inconsistente sulle targhe.
Diagnosi 2026-05-23: `~/.claude/projects/.../memory/diag_plate_recovery_2026-05-23.md`.

## Cosa è già stato fatto (NON ripetere)
- Test isolato `/tmp/diag_plate_region.py` su 2 sample BMW 428982234890.
- Risoluzione (1440-1801px) e contrasto (std 61-72) NON sono il problema.
- Vision OCR: foto 00 → "5M UJ769E" conf=0.30 hit. Foto 01 → 0 box anche con conf_min=0.10 + 3x.
- cv2 contour+AR-plate (4.0-5.5): foto 01 → 1 candidato 178×43 ar=4.14. Foto 00 → 0 candidati.
- **Disaccordo Vision↔cv2 = 100%**: mai entrambi hit sulla stessa regione, mai entrambi miss.
- Logo `assets/ARGOS_logo_sobrio_horizontal.png` esiste (1400×380) ma `sanitize_image` non lo usa.

## Decisione: fallback geometrico cv2 OR-logico Vision

### Perché questa, non altre
Sui 2 sample misurati oggi, Vision-solo copre 50% (1/2), cv2-solo copre 50% (1/2), Vision OR cv2 copre 100% (2/2). I due metodi sono complementari, non ridondanti. La data lo dice.

Plate-detector ML dedicato (YOLO-plate, OpenALPR) bocciato dai vincoli operativi:
- vincolo #5 zero-cost: nuova dipendenza ML pesante.
- vincolo #8 preflight: rischio dependency hell macOS 11 già pagato in S159/S162.
- vincolo #11 pattern recognition: ricaduta nel ciclo "lib ML + Big Sur = blocker strutturale".

Mask fissa statistica zona-targa bocciata:
- rovina foto laterali e posteriori (richiede classifier orientamento → introduce un secondo problema irrisolto per risolvere il primo).
- bug-prone su angolazioni 3/4 frontale dove la zona targa si sposta del 15-20% orizzontalmente.

## Implementazione proposta (NO codice ora, solo design)
Estensione di `src/cove/vision_ocr.py:detect_text_regions` con un **secondo path geometrico** che ritorna regioni nello stesso formato `{box, text, conf, is_seller, should_mask}`. Merge con regioni Vision prima del return.

Path geometrico:
1. Solo se `image_index ≤ 3` (foto frontali/laterali statisticamente con targa visibile) — evita interior.
2. Crop zona statistica (x 25-75%, y 55-95%) — più ampio di quello del test isolato per coprire angolazioni.
3. `cv2.equalizeHist` + `cv2.Canny(50,150)` + `findContours`.
4. Filtro candidati: aspect ratio 3.5-5.5 (tolleranza > test isolato per targhe italiane vecchie e angolazioni 3/4), area ≥ 0.5% area crop, altezza ≥ 15px (no rumore).
5. Per ogni candidato → emit region con `text="<plate-candidate>"`, `conf=0.50` (fisso, non-OCR), `should_mask=True`, `is_seller=False`.
6. **Anti-overlap con KEEP_WORDS**: se il candidato cv2 si sovrappone >60% IoU a una regione Vision che è in KEEP_WORDS (es. "xDrive 25e"), scarta — evita di mascherare badge trim auto.

Nessuna modifica a Stage 3 (`_apply_solid_fills`). Le nuove regioni passano per la stessa logica Pillow solid-fill esistente.

## Critica strutturale del piano (vincolo #4)

1. **Assunzione nascosta**: 2 sample non sono statisticamente significativi. Il "100% copertura" è un risultato su n=2, non un'evidenza forte. UAT su minimo 8 sample diversi (BMW/Mercedes/Audi, frontali+laterali, angolazioni varie) è obbligatorio prima di chiamare verde.

2. **Cosa rompe a 30 giorni**: AR filter 3.5-5.5 può falsi-positivi su griglie radiatore (BMW kidney grille ar≈2.5-3.0, borderline), fanali rettangolari, targhetta modello sul portellone. Mitigazione parziale via min-height e IoU con KEEP_WORDS, ma rimane il rischio strutturale di mascherare elementi auto. Soglia di falsi-positivi tollerabile → da definire con Luke (es. ≤1 falso-positivo ogni 20 foto = accettabile).

3. **Pattern errore noto**: in S110 sono state già testate euristiche OpenCV (sky ratio, variance, edge density) e tutte FALLITE 0/10. Il commento riga 238-239 di `image_sanitizer.py` è esplicito: "Do NOT re-add them". Il piano S184 reintroduce un'euristica cv2 nello stesso punto. Devo verificare in S184 se quelle euristiche-bocciate operavano sullo stesso problema (text detection generica) o su uno diverso (classifier interior/exterior); se è lo stesso problema, il piano è da rivedere.

4. **Sovradimensionamento**: anti-overlap con KEEP_WORDS via IoU è in piano da subito, ma potrebbe non servire se UAT mostra zero falsi-positivi su badge trim. Implementare prima la versione minima (no IoU), misurare, aggiungere IoU solo se necessario.

## Step S184 ordinati
1. Verifica claim del punto 3 critica strutturale → grep `S110` in repo, leggere commit/note euristiche bocciate.
2. Se claim conferma "stesso problema bocciato" → S184 si ferma qui, sessione di triage con Luke per ridiscutere.
3. Se claim smentito → estensione `vision_ocr.py` con path geometrico (versione minima senza IoU).
4. UAT su minimo 8 sample reali (download recente, BMW/Mercedes/Audi misti).
5. Misurare: copertura targa, falsi-positivi su badge/grille/fanali.
6. Se metriche OK → IoU aggiunto solo se necessario, poi commit + Luke UAT visivo 5/5 PASS.
7. Se metriche NO → handoff con dati, NO commit.

## Vincoli operativi
- NO modifica `image_sanitizer.py` o `vision_ocr.py` finché step 1-2 non chiusi.
- Venv `~/.argos-sanitizer-venv/bin/python`.
- UAT visivo Luke 5/5 obbligatorio (feedback memory `feedback_smoke_test_not_uat_gate.md`).
- Day 1 Stile Car deadline 2026-06-03 — 11 giorni residui.

## File chiave
- `src/cove/vision_ocr.py:60-195` (target del path geometrico)
- `src/cove/image_sanitizer.py:238-246` (commento S110 da verificare)
- `src/cove/image_sanitizer.py:528-728` (sanitize_image, no modifiche previste)
- `/tmp/diag_plate_region.py` (base riproducibile per estendere a 8 sample)
