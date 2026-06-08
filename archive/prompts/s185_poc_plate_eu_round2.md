# S185 — Round-2 PoC plate-detector EU-specifico

**Contesto S184**: Round-1 con `Koushim/yolov8-license-plate-detection` = NO-GO.
È un detector di rettangoli-testo-alto-contrasto, non plate-detector. 67% FP rate.
Perde la targa DE autentica nera-su-veicolo-nero (sample 2: 5 box su watermark URL,
0 sulla targa vera BMW Baum). Diagnosi: low-contrast targhe DE + Koushim trained
su targhe generic alto-contrasto.

Sample R1 viziato: 0/5 targhe autentiche (e0a268224633 usa cartelli promo dealer
"Spar-Deal" in posizione targa). Domanda APERTA: modello plate-detector EU-specifico
trova la targa DE/IT vera?

**Artefatti R1 disponibili**:
- `/tmp/poc_yolo_plate.py` (script PoC riusabile)
- `/tmp/poc_yolo_out.zip` (5 jpg + json, ispezionato Luke)
- iMac: `/tmp/koushim_yolov8_plate.pt` cached, ultralytics+torch+cv2 installati
- Memory: `poc_yolo_plate_round1_koushim_nogo.md`

## TIME-BOX HARD 45 min con CHECK-POINT a 30 min

A 30 min: riporta stato anche se STEP 2 non finito (sample confermati + modello scelto
+ partial annotate se possibili). A 45 min: stop comunque, anche se non concluso.
NON sforare.

## STEP 0 — Selezione sample (max 15 min)

Apri visivamente (NO assunzioni layout AS24, vincolo #10) le foto **_00 E _02 E _03**
di 10-15 listing diversi (= 30-45 foto candidate) in
`~/Documents/app-antigravity-auto/releases/20260502_195919/dossiers/safe_images/raw/`
su iMac. Motivo bias: foto _00 spesso ha promo dealer, _02/_03 (posteriore, lato
passeggero) più frequentemente ha targa vera.

Cerca **5-8 foto con TARGA DE/IT AUTENTICA visibile**:
- NON cartelli promo dealer (Spar-Deal, Garantie, ecc.)
- NON watermark URL
- NON slide marketing (skip pattern `2,99% effektiver Jahreszins` ecc.)
- targa vera anche angolata/scura/parziale

Strategia ispezione veloce: usa Read tool multimodale su batch di 5 immagini per
volta, decidi sì/no in 1 sguardo. Non scaricare zip per ogni immagine.

Stampa path confermati + per ognuna "targa vera confermata, posizione X/Y".

**Stop condition**: se non trovi ≥3 foto con targa DE autentica su 30-45 candidate →
fermati e segnala. Significa che il dominio reale ARGOS ha pochissime targhe vere
(per lo più promo dealer) e cambia la decisione tutta (no plate-detector serve,
solo cartello-promo-detector + upstream filter slides).

## STEP 1 — Modello EU (max 10 min)

Cerca su HF 1 modello plate-detection trained su targhe EUROPEE (German/EU plates
dataset), MIT/Apache, usabile con ultralytics o onnxruntime installati su iMac.
Query: "german license plate yolo", "EU plate detection", "ANPR Europe".

Usa `mcp__claude_ai_Hugging_Face__hub_repo_search` con sort=downloads + ispeziona
README/files top 3 candidate.

Se non trovi modello EU-specifico scaricabile <10 min → usa miglior candidato
disponibile e dichiaralo esplicitamente. NON inventare.

## STEP 2 — Test + annotate + baseline Vision (max 15 min)

Per ogni sample STEP 0 esegui **DUE detector in parallelo** sullo stesso input:
1. **Modello EU** scelto STEP 1
2. **Apple Vision OCR** (già integrato in `tools/scripts/vision_ocr.py`, baseline
   confronto apple-to-apple)

Per ogni foto stampa tabella:
| path | EU n_box | EU conf | EU bbox | EU ms | Vision n_text | Vision text | Vision bbox | Vision ms |

Salva annotate (entrambi i canali sovrapposti, colori diversi: verde=EU, rosso=Vision)
in `/tmp/poc_yolo_eu_out/` + zip `/tmp/poc_yolo_eu_out.zip` per Luke download.

Motivo baseline: se EU performa come Vision, STRADA 1 è inutile (Vision già installata,
non aggiunge valore). Se EU >> Vision sulle targhe vere, evidenza solida per STRADA 1.

## GATE (Luke decide su ispezione visiva)
- detection ≥70% sulle targhe DE/IT autentiche confermate
- box DAVVERO sulla targa, non su promo/watermark/loghi
- FP accettabilmente bassi
- delta EU vs Vision visibile (altrimenti non vale aggiungere canale)

## Vincoli operativi
- NO integrazione, NO modifiche `image_sanitizer.py` ANCHE SE GATE PASS
- Tutto su iMac via SSH (libs installate lì)
- Script su `/tmp/`, mai in `src/`
- Output Luke download via `/tmp/*.zip`

## Output sessione richiesti
1. Path sample confermati STEP 0 con label "targa vera posizione X/Y"
2. Modello EU usato STEP 1 (nome HF + dimensioni + license)
3. Tabella comparativa EU vs Vision + zip annotate STEP 2
4. Verdetto raccomandato (GO/NO-GO STRADA 1 / pivot STRADA 2) motivato sui dati

Se NO-GO R2 confermato → S186 pivot STRADA 2 (alert + manual_review flag) +
promozione BACKLOG #upstream-filter-AS24-slides al primo posto.

## Budget context partenza S185
Sessione S184 chiusa al ~53% context post-PoC R1 + zip + memory update.
Apertura S185 dovrebbe stare <40% (skill ARGOS + memory + prompt = ~25-30%).
Se opening >45% → prune skill non rilevanti prima di eseguire STEP 0.
