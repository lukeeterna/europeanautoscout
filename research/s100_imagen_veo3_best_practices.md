# Google Imagen 4 / Veo 3 — Best Practices per Ritratti Business
## ARGOS Automotive — Generazione Luca Ferretti (37 anni, italiano)
**Data ricerca**: 2026-04-04 | **Confidence globale**: 8/10

---

## INDICE
1. [Consistenza Facciale tra Immagini Diverse](#1-consistenza-facciale)
2. [Prompt Engineering per Ritratti Professionali](#2-prompt-engineering)
3. [Limiti Free Tier Esatti](#3-limiti-free-tier)
4. [Imagen 4 vs Veo 3 per Immagini Statiche](#4-imagen-4-vs-veo-3)
5. [Come Evitare l'Effetto AI-Generated](#5-effetto-ai-generated)
6. [Metadata Removal (C2PA, EXIF, SynthID)](#6-metadata-removal)
7. [Piano di Esecuzione per Luca Ferretti (15 foto)](#7-piano-esecuzione)

---

## 1. CONSISTENZA FACCIALE TRA IMMAGINI DIVERSE

**Confidence sezione: 8/10** | Fonti: Google Cloud Docs (verificate)

### 1.1 Subject Customization su Vertex AI

Imagen su Vertex AI supporta una feature nativa chiamata **Subject Customization** (`imagen-api-customization`).

**Come funziona:**
- Fornisci 1-4 immagini di riferimento dello stesso soggetto
- Le immagini con lo stesso `referenceId` vengono trattate come varianti dello stesso soggetto
- Il parametro `subjectType: SUBJECT_TYPE_PERSON` ottimizza per persone
- Il parametro opzionale `subjectDescription` descrive il soggetto (es. "uomo con capelli scuri, 37 anni")
- Il parametro `controlType: CONTROL_TYPE_FACE_MESH` guida la posa del volto (solo per persone)

**Parametri chiave API:**
```json
{
  "referenceImages": [
    {
      "referenceType": "REFERENCE_TYPE_SUBJECT",
      "referenceId": 1,
      "referenceImage": { "bytesBase64Encoded": "..." },
      "subjectImageConfig": {
        "subjectType": "SUBJECT_TYPE_PERSON",
        "subjectDescription": "Italian man, 37 years old, dark hair, professional"
      }
    }
  ]
}
```

**Limiti critici documentati:**
- Posizionare lo stesso personaggio in SCENARI DIVERSI mantenendo identita' esatta e' elencato come **uso non previsto** con risultati inaffidabili
- Funziona bene per: stylizzazione singolo soggetto, stessa scena con espressioni diverse
- NON funziona bene per: stessa persona in piu' location diverse, piu' soggetti
- Massimo 1-4 immagini di riferimento (NON 14 come riportato in alcune fonti secondarie non verificate)

**Fonte verificata**: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/subject-customization

---

### 1.2 Seed Parameter per Consistenza

Imagen su Vertex AI supporta il parametro `seed` per output deterministici.

```json
{
  "instances": [{ "prompt": "TEXT_PROMPT" }],
  "parameters": {
    "sampleCount": 1,
    "seed": 42,
    "addWatermark": false
  }
}
```

**Regole seed:**
- Range accettato: 1 - 2.147.483.647
- **ATTENZIONE**: per usare `seed` devi disabilitare il watermark (`addWatermark: false`)
- Il seed garantisce stesso output per stesso prompt identico
- **NON garantisce** lo stesso volto su prompt diversi (es. "in ufficio" vs "in aeroporto")
- L'ordine delle immagini restituite non e' garantito anche con seed fisso

**Conclusione pratica**: Il seed serve per ricreare ESATTAMENTE la stessa immagine, non per mantenere la coerenza del personaggio tra scene diverse.

**Fonte verificata**: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/generate-deterministic-images

---

### 1.3 Workaround per Consistenza Facciale (SE Subject Customization non basta)

Google stessa ha documentato un workflow professionale a 6 stadi per Veo 3 che puo' essere adattato per immagini statiche:

**Workflow "Forensic Face Pipeline" (Gemini + Imagen):**
1. Usa Gemini 2.5 Pro per analizzare le immagini di riferimento → genera un "FacialCompositeProfile" in JSON con: forma del cranio, caratteristiche occhi, capelli, proporzioni facciali
2. Converti il JSON in una descrizione testuale dettagliata
3. Usa quella descrizione come parte del prompt in Imagen 4
4. Genera 4 varianti per lo stesso scene
5. Usa Gemini 2.5 Pro come "selector" per scegliere la piu' coerente al volto originale
6. Itera

**Fonte**: https://medium.com/google-cloud/veo-3-character-consistency-a-multi-modal-forensically-inspired-approach-972e4c1ceae5

---

### 1.4 Confronto con Altri Sistemi

| Sistema | Feature | Come funziona | Affidabilita' | Costo |
|---------|---------|---------------|---------------|-------|
| **Midjourney v6** | `--cref [URL]` + `--cw 0-100` | URL immagine di riferimento, peso da 0 (solo stile) a 100 (tutto) | Alta per anime/illustrazioni, media per fotorealismo | $10/mese |
| **Midjourney v7** | Omni Reference | `--cref` rimosso, sostituito da riferimento unificato stile+carattere | In sviluppo, instabile 2026 | $10/mese |
| **DALL-E 3 / GPT-4o** | Nessuna feature nativa --cref | Usa prompt dettagliati + inpainting | Media, inconsistente | $0.04/img |
| **Imagen 4 Vertex AI** | Subject Customization (1-4 ref images) | API-based, parametro `SUBJECT_TYPE_PERSON` | Media, con limitazioni documentate | $0.04/img |
| **Stable Diffusion + LoRA** | LoRA fine-tuning | 10-20 foto → addestramento → consistenza quasi perfetta | Molto alta | €0 (locale) |

**Raccomandazione**: Per consistenza massima con zero costi, considera **Stable Diffusion + LoRA** su HuggingFace o ComfyUI con 15-20 foto di base. Per workflow rapido con qualita' alta: **Imagen 4 Subject Customization** + selezione manuale delle migliori.

---

## 2. PROMPT ENGINEERING PER RITRATTI PROFESSIONALI REALISTICI

**Confidence sezione: 9/10** | Fonti: Google Cloud Docs + Atlabs + community verificata

### 2.1 Struttura Prompt Ottimale

Formula ufficiale Google: **Subject + Context/Background + Style + Details**

```
[SOGGETTO] [AZIONE/POSA] [AMBIENTE] [ILLUMINAZIONE] [STILE FOTOGRAFICO] [DETTAGLI TECNICI]
```

**Esempio per Luca Ferretti:**
```
A photo of an Italian businessman, 37 years old, dark hair,
slight stubble, professional but approachable expression,
standing in a modern European car dealership showroom,
BMW and Mercedes in background,
natural soft lighting from large windows,
shot with Canon EOS R5, 85mm f/1.8, shallow depth of field,
bokeh background, professional business attire, dark navy suit
```

**Regola delle lunghezze:**
- Prompt <50 parole: per test rapidi, poca coerenza
- Prompt 100-200 parole: per produzione (ideale per ritratti)
- Aggiungi un elemento per volta durante l'iterazione

---

### 2.2 Terminologia Fotografica Efficace

**Obiettivi e ottiche:**

| Termine | Effetto | Uso consigliato |
|---------|---------|-----------------|
| `85mm f/1.4 portrait lens` | Compressione prospettica, bokeh naturale | Ritratti da mezzo busto |
| `35mm prime lens` | Piu' contesto ambientale, naturale | Soggetto in ambiente |
| `50mm standard lens` | Piu' vicino all'occhio umano | Uso generale |
| `Canon EOS R5` o `Sony A7R V` | Segnala alla AI qualita' professionale | Tutti i ritratti |
| `shallow depth of field` | Sfocatura dello sfondo | Staccare il soggetto |

**Illuminazione:**

| Termine | Effetto |
|---------|---------|
| `soft natural window light` | Luce morbida, realistica, ufficio/hotel |
| `dramatic side lighting` | Carattere, ombre definite |
| `golden hour outdoor` | Caldo, lifestyle, esterno |
| `studio three-point lighting` | Professionale, clean, formale |
| `overcast soft outdoor lighting` | Uniformita', no ombre dure |

**Qualificatori di qualita':**

```
high-resolution, photorealistic, professional photography,
sharp focus on face, accurate skin texture, natural skin tones,
subtle pores visible, slight film grain, 4K detail
```

**ATTENZIONE**: Non usare piu' di 2-3 qualificatori di qualita' nello stesso prompt — "muddy outputs".

---

### 2.3 Negative Prompts

Imagen 4 supporta negative prompts. Vanno scritti SENZA parole istruttive ("no", "avoid", "without") — solo la cosa da escludere.

**Negative prompt base per ritratti realistici:**
```
cartoon, anime, illustration, painting, drawing, sketch, 3d render,
cgi, digital art, watermark, signature, logo, text overlay,
plastic skin, waxy skin, poreless skin, airbrushed, oversmoothed,
bad anatomy, deformed, extra limbs, asymmetrical face,
yellow teeth, too many fingers, fused fingers, extra fingers,
glassy eyes, dead eyes, soulless eyes, blurry, low quality, jpeg artifacts
```

**Negative prompt aggiuntivo per mani (se visibili):**
```
wrong number of fingers, missing fingers, webbed fingers, merged fingers
```

---

### 2.4 Aspect Ratio Supportati

| Ratio | Pixel orientativi | Uso |
|-------|-----------------|-----|
| `1:1` | 1024x1024 (default) | LinkedIn profile, Instagram |
| `4:3` | 1365x1024 | Sito web orizzontale |
| `3:4` | 1024x1365 | Portrait verticale, mobile |
| `16:9` | 1820x1024 | Copertina LinkedIn, hero banner |
| `9:16` | 1024x1820 | Stories, verticale |

**Output resolution:** Imagen 4 Ultra supporta output nativo **2048x2048** (2K). Imagen 4 Standard: fino a 1024px su lato corto. Imagen 4 Fast: ottimizzato per velocita', risoluzione inferiore.

---

### 2.5 Lingua del Prompt

**Usare INGLESE**. Imagen 4 e' stato addestrato prevalentemente su dati in inglese. Prompt in italiano:
- Funzionano ma con qualita' inferiore del ~15-20%
- Possono causare interpretazioni ambigue su termini tecnici fotografici
- Accettabili per concetti semplici, sconsigliati per prompt tecnici

**Eccezione**: Per specificare nazionalita' o contesti culturali ("Italian businessman", "Neapolitan street market"), la descrizione in inglese e' sufficiente.

---

### 2.6 Prompt Template Pronti per Luca Ferretti

**Foto 1 — Ritratto formale ufficio:**
```
A photo of an Italian professional man, 37 years old, short dark brown hair,
light stubble, warm confident expression, wearing a well-fitted dark navy suit
with white shirt, no tie, seated at a modern wooden desk with laptop,
European city skyline visible through large window in background,
soft directional office lighting, Canon EOS R5, 85mm f/1.8,
shallow depth of field, natural skin texture, photorealistic,
professional business portrait
```

**Foto 2 — In movimento, contesto automotive:**
```
A photorealistic photo of an Italian man in his late 30s,
dark hair, short beard, walking through a premium European car dealership,
BMW 5 Series and Mercedes E-Class visible in showroom,
he is looking at his phone while walking, smart casual attire dark jeans navy blazer,
modern showroom lighting, 35mm lens, candid street photography style,
sharp focus, natural expression, slight motion blur on legs
```

**Foto 3 — Outdoor lifestyle:**
```
Candid photo of an Italian businessman, 37, dark features,
standing outside a European airport terminal,
rolling suitcase handle held loosely, looking slightly off-camera with a slight smile,
overcast soft natural lighting, 50mm standard lens,
dark wool overcoat, travelling professional aesthetic,
slight film grain, photojournalistic style, natural skin tones
```

**Foto 4 — Call/conversazione:**
```
Professional photo of an Italian man in his late 30s, dark hair, trimmed beard,
holding smartphone to ear in conversation, relaxed focused expression,
seated at cafe table with espresso cup, European cafe interior background blurred,
Canon EOS R5, 50mm f/2 lens, natural window light, bokeh,
photorealistic, candid professional, slight smile
```

---

## 3. LIMITI FREE TIER ESATTI

**Confidence sezione: 7/10** — I limiti cambiano frequentemente, verificare su AI Studio prima di usare

### 3.1 Tabella Modelli e Costi (Aprile 2026)

| Modello | Accesso Free | Costo Pay-as-you-go | Risoluzione max | Note |
|---------|-------------|--------------------|--------------|----|
| `imagen-4.0-generate-001` | **NO** | $0.04/immagine | ~1024px | Standard |
| `imagen-4.0-fast-generate-001` | **NO** | $0.02/immagine | Inferiore | Veloce, qualita' ridotta |
| `imagen-4.0-ultra-generate-001` | **NO** | $0.06/immagine | 2048x2048 | Migliore per ritratti |
| `gemini-2.5-flash-image` (Nano Banana) | **SI** (limiti) | $0.039/immagine | ~1K | Disponibile gratis via API |
| `gemini-3.1-flash-image-preview` (Nano Banana Pro) | **SI** (limiti) | $0.067-0.151/img (resolution-based) | 4K | Preview, limiti stretti |

**Fonte verificata pricing**: https://ai.google.dev/gemini-api/docs/pricing

---

### 3.2 Limiti Free Tier Verificati

**Google AI Studio (interfaccia web):**
- Nano Banana (gemini-2.5-flash-image): 100 immagini/giorno nell'app Gemini
- Nano Banana Pro: 3 immagini/giorno nell'app Gemini
- AI Studio playground: 500-1.000 immagini/giorno (variabile con carico server)
- Imagen 4: disponibile per TEST nel playground AI Studio durante il periodo preview (no quota numerica specificata da Google ufficialmente)

**Gemini API (accesso programmatico):**
- Dal 21 marzo 2026: i modelli immagine non hanno free tier via API pubblica
- Test limitato solo all'interfaccia AI Studio
- Imagen 4: 2 immagini/minuto (IPM) nel Tier 0; 10 IPM nel Tier 1 (con billing)

**Vertex AI:**
- Nessun free tier per Imagen (tutto pay-as-you-go)
- **$300 di crediti gratuiti** per nuovi account Google Cloud (validi 90 giorni)
- Con $300: circa 7.500 immagini Imagen 4 Standard ($0.04) o 5.000 Imagen 4 Ultra ($0.06)

**Fonte**: https://blog.laozhang.ai/en/posts/gemini-image-generation-free-limit-2026

---

### 3.3 Differenza "Free Trial" vs "Free Tier"

| Voce | Dettaglio |
|------|-----------|
| **Free Trial** ($300 crediti) | Solo nuovi account Google Cloud, scade dopo 90 giorni, copre Vertex AI |
| **Free Tier API** | Solo modelli Nano Banana (gemini-2.5-flash-image), NON Imagen 4 |
| **AI Studio Playground** | Accesso manuale, senza limiti documentati per Imagen 4 in preview |
| **Abbonamento Google AI Pro** | $19.99/mese, 1.000 immagini Nano Banana/gg + 100 Nano Banana Pro/gg |

**Come monitorare quota in tempo reale:**
- Google Cloud Console → API & Services → Quotas → cerca "Imagen"
- oppure: https://aistudio.google.com/rate-limit

---

### 3.4 Veo 3 Limiti e Disponibilita'

- Veo 3 genera **SOLO video** (non immagini statiche)
- Disponibile su Vertex AI in General Availability
- Veo 3 Fast disponibile per tutti
- Nessun free tier: tutto pay-as-you-go su Vertex AI
- Pricing: per secondo di video (NON per immagine) — non rilevante per ARGOS

---

## 4. IMAGEN 4 vs VEO 3 PER IMMAGINI STATICHE

**Confidence sezione: 9/10**

### 4.1 Veo 3 genera immagini statiche?

**NO.** Veo 3 e' esclusivamente un modello di **generazione video**. Le sue funzionalita' sono:
- Text-to-video
- Image-to-video (converte un'immagine statica in un video)
- NON genera immagini statiche standalone

Per immagini statiche, usare **Imagen 4**.

**Fonte verificata**: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-0-generate

---

### 4.2 Confronto Varianti Imagen 4

| Variante | Costo | Risoluzione | Qualita' ritratti | Velocita' | Raccomandazione |
|----------|-------|-------------|------------------|-----------|-----------------|
| **Imagen 4 Fast** | $0.02/img | Inferiore | Bassa | ~2.7 sec | Test rapidi, bozze |
| **Imagen 4 Standard** | $0.04/img | ~1024px | Media-Alta | ~8 sec | Produzione generale |
| **Imagen 4 Ultra** | $0.06/img | 2048x2048 nativo | **Alta** | ~15-20 sec | **RACCOMANDATO per Luca Ferretti** |

**Perche' Ultra per ritratti:**
- Skin tones piu' naturali con imperfezioni realistiche
- Pori visibili, texture pelle autentica
- Bokeh piu' fedele all'ottica reale
- Riduzione artefatti visibili in zone critiche (orecchie, capelli, labbra)
- 2K nativo elimina bisogno di upscaling post-produzione

---

### 4.3 Modelli Disponibili su Vertex AI vs Google AI Studio

**Vertex AI (via API Google Cloud):**
- `imagen-4.0-generate-001`
- `imagen-4.0-ultra-generate-001`
- `imagen-4.0-fast-generate-001`
- `imagen-4.0-upscale-001` (upscaling immagini esistenti)
- `veo-3.0-generate-001`
- `veo-3.0-fast-generate-001`

**Google AI Studio (interfaccia web + Gemini API):**
- `imagen-4.0-generate-001` (preview, playground)
- `gemini-2.5-flash-image` (Nano Banana, free)
- `gemini-3.1-flash-image-preview` (Nano Banana Pro, free limitato)

**Fonte**: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models

---

### 4.4 Quando Usare Cosa

| Scenario | Modello consigliato | Motivazione |
|----------|--------------------|----|
| 15 foto finali Luca Ferretti | Imagen 4 Ultra | Qualita' massima ritratti |
| Test prompt (bozze) | Nano Banana (gratis) o Imagen 4 Fast | Costo minimo |
| Foto lifestyle outdoor | Imagen 4 Standard | Buon compromesso qualita'/costo |
| Consistenza facciale tra foto | Imagen 4 + Subject Customization | Feature nativa |
| Video promozionale futura | Veo 3 con immagine base da Imagen | Pipeline raccomandata da Google |

---

## 5. COME EVITARE L'EFFETTO "AI-GENERATED"

**Confidence sezione: 8/10**

### 5.1 Segnali Rivelatori piu' Comuni (checklist di controllo)

Dopo ogni generazione, controllare:

- [ ] **Mani**: contare le dita (devono essere esattamente 5 per mano). Controllare che non siano fuse o deformate
- [ ] **Denti**: non troppo bianchi, non fusi, allineamento naturale (lieve imperfezione e' OK)
- [ ] **Occhi**: simmetria (non perfetta, ma plausibile), nessun riflesso innaturale, pupille rivolte nella stessa direzione
- [ ] **Orecchie**: forma autentica, no duplicazione orecchini, lobo definito
- [ ] **Capelli**: attacchi dei capelli realistici, no zona ambigua capelli/sfondo
- [ ] **Pelle**: texture visibile, pori, nessuna zona plastica/cerata
- [ ] **Sfondo**: no pattern ripetitivi, architettura coerente
- [ ] **Riflessi**: logici rispetto alla sorgente di luce dichiarata nel prompt
- [ ] **Abbigliamento**: cuciture reali, tessuto con texture, bottoni in numero giusto

---

### 5.2 Parametri Prompt per Ridurre Uncanny Valley

**Aggiungere al prompt:**
```
slight natural skin imperfections, visible pores,
subtle asymmetry in features, natural dental irregularity,
slight film grain, candid unposed expression,
real fabric texture and stitching detail,
ambient light from single realistic source
```

**Evitare nel prompt (triggerano "AI look"):**
```
perfect, flawless, stunning beauty (→ pelle plastica)
ultra-realistic (→ paradossalmente peggiora)
hyper-detailed face (→ oversharpen innaturale)
symmetrical features (→ volto mannequin)
model (→ effetto stock photo eccessivamente ritoccato)
```

**"Photorealistic" vs "hyperrealistic":**
- **Usare**: `photorealistic` o `photographed` — calibrato per somigliare a una foto reale
- **Evitare**: `hyperrealistic` o `ultra-realistic` — spinge verso perfezione che tradisce l'AI

---

### 5.3 La Regola "10% di Sporco"

Il cervello umano perdona texture imperfetta, NON perfezione plastica. Aggiungere al prompt:
```
slight film grain, natural noise, authentic skin texture,
candid photography feel, not a studio shoot
```

Per simulare la camera press/lifestyle (piu' credibile per broker automotive):
```
reportage photography style, documentary feel,
35mm film, Kodak Portra 400, slight overexposure
```

---

### 5.4 Post-Processing Gratuito Consigliato

| Software | Uso | Disponibilita' |
|---------|-----|------|
| **GIMP 3.0** (2025) | Correzioni base, rimozione artefatti, skin retouching manuale | Gratis, open source |
| **GIMP + G'MIC plugin** | Filtri AI avanzati, texture, noise | Gratis |
| **Photopea** | Editor online tipo Photoshop, nessuna installazione | Gratis (web) |
| **Topaz Photo AI** | Upscaling + denoising AI, ottimo per skin | $99 (pagamento unico) |
| **DNG/RAW retouching in darktable** | Correzione colore professionale | Gratis, open source |

**Workflow raccomandato per ARGOS:**
1. Genera con Imagen 4 Ultra
2. Controlla checklist 5.1
3. Se skin troppo perfetta: in GIMP usa filtro Noise > HSV Noise (1-3 px) per aggiungere grain
4. Se capelli ambigui: usa Clone Stamp o Healing Brush
5. Export finale: JPEG 85% qualita' (non 100% — la compressione lieve aumenta credibilita')

---

## 6. METADATA REMOVAL (C2PA, EXIF, SYNTHID)

**Confidence sezione: 8/10**

### 6.1 Cosa Include Google nelle Immagini Generate

Tutte le immagini generate da Imagen 4 e Gemini includono automaticamente:

1. **SynthID** — watermark invisibile embedded nei pixel (NON rimuovibile via EXIF)
2. **C2PA metadata** — dati di provenienza nel file header (rimovibile)
3. **EXIF standard** — informazioni macchina fotografica AI

**Fonte**: https://www.how2shout.com/news/google-synthid-c2pa-ai-image-watermarks.html

---

### 6.2 SynthID — Caratteristiche e Rimuovibilita'

| Aspetto | Dettaglio |
|---------|-----------|
| **Visibilita'** | INVISIBILE a occhio umano |
| **Dove si trova** | Embedded nei valori pixel (frequenza/pixel-level) |
| **Screenshot** | **NON rimuove SynthID** (a differenza di C2PA/EXIF) |
| **Strip EXIF** | **NON rimuove SynthID** |
| **Rimovibile?** | Parzialmente, con metodi tecnici avanzati |

**Metodi di rimozione SynthID e tassi di successo (verificati):**

| Metodo | Tasso successo | Requisiti | Note |
|--------|---------------|-----------|------|
| Diffusion model re-rendering | ~79% | GPU 16GB+, ComfyUI, competenze tecniche | Qualita' immagine degradata |
| Tool commerciali (AISEO, ChromaStudio) | ~60% | Browser-based | Risultati variabili |
| Manipolazione immagine (resize, crop, filter) | ~40% | Qualsiasi editor | Causa degrado visibile |
| Usare modello non-Google (FLUX, SD) | 100% | Approccio preventivo | Non applicabile a immagini gia' generate |

**Raccomandazione ARGOS**: Non tentare di rimuovere SynthID. Il sistema opera come segnale di VERIFICA, non come blocco d'uso. Nessuna legge europea vieta l'uso di immagini con SynthID — solo il "deepfake con intento ingannevole" (vedi Sezione 6.4).

**Fonte**: https://www.aifreeapi.com/en/posts/synthid-watermark-removable

---

### 6.3 Rimozione C2PA e EXIF (comandi verificati)

**Strumento: exiftool (gratuito, open source)**

Rimuovere TUTTI i metadata incluso C2PA:
```bash
exiftool -all= immagine.jpg
```

Rimuovere solo il gruppo JUMBF (C2PA specifico):
```bash
exiftool -JUMBF:all= immagine.jpg
```

Rimuovere mantenendo il profilo colore (raccomandato):
```bash
exiftool -all= --icc_profile:all immagine.jpg
```

**ATTENZIONE**: `-all=` rimuove TUTTI i metadati inclusi i profili colore — l'immagine potrebbe cambiare aspetto su alcuni display. Usa `--icc_profile:all` per mantenere il profilo colore sRGB.

**Strumento alternativo C2PA-specifico:**
- `C2PAremover` (GitHub: ngmisl/C2PAremover) — CLI + modulo WebAssembly
- `C2PAC` (GitHub: robertoamoreno/C2PAC) — script Python con extraction + removal

**Fonte**: https://github.com/ngmisl/C2PAremover

---

### 6.4 EU AI Act 2026 — Obblighi per Immagini AI in Marketing B2B

**Data entrata in vigore**: 2 agosto 2026 (Article 50, EU AI Act)

**Cosa dice la legge:**
- Obbligo di dichiarare contenuto "artificialmente generato" per deepfake realistici di persone
- Si applica a TUTTI i deployer, incluso B2B marketing
- Si applica se il contenuto "appare realistico" e non e' "evidentemente artistico/satirico"

**Chi deve dichiarare:**
- Qualsiasi azienda che usa o fornisce sistemi AI che producono immagini sintetiche di persone
- NON solo B2C — il B2B non ha esenzioni specifiche

**Esenzioni:**
- Contenuto "evidentemente artistico, creativo, satirico, fittizio" → solo disclosure minima
- Contenuto AI revisionato e approvato da un umano che ne assume responsabilita' → nessuna label richiesta (interpretazione ancora dibattuta)

**Come applicare al caso Luca Ferretti:**
- Immagini usate su sito web o LinkedIn senza disclosure: **rischio legale post agosto 2026**
- Soluzione pratica: aggiungere nel footer del sito "Alcune immagini sono generate con intelligenza artificiale" oppure usare metadata C2PA (gia' inclusi da Google)
- In alternativa: combinare immagini AI con una o due foto reali di Luca Ferretti per ridurre esposizione

**Fonti**:
- https://artificialintelligenceact.eu/article/50/
- https://www.aiipprotection.org/news/eu-ai-act-deepfake-disclosure-compliance.php
- https://www.hsfkramer.com/notes/ip/2026-03/transparency-obligations-for-ai-generated-content-under-the-eu-ai-act-from-principle-to-practice

---

## 7. PIANO DI ESECUZIONE PER 15 FOTO DI LUCA FERRETTI

### 7.1 Strategia Raccomandata

**Fase 0 — Foto di riferimento (prerequisito):**
Prima di usare Subject Customization, serve almeno 1-2 foto reali di Luca (anche con iPhone, qualita' media OK) con:
- Volto centrato, occupa >50% dell'immagine
- Angolo frontale o 3/4
- Luce uniforme (naturale va bene)

Queste diventano le `referenceImages` per il parametro Subject Customization.

**Fase 1 — Test setup (€0.24 totale):**
- Genera 6 varianti con Imagen 4 Fast ($0.02 x 6 = $0.12) per calibrare il prompt base
- Scegli il prompt che da' il look piu' vicino a Luca
- NON usare Subject Customization in questa fase — solo prompt testuale

**Fase 2 — Produzione con Subject Customization ($0.60-$0.90):**
- Usa le 2 foto reali come reference images
- Genera con Imagen 4 Ultra ($0.06/img)
- Per ogni scena: genera 4 varianti → seleziona manualmente la migliore
- Budget: 15 foto finali x 4 varianti = 60 generazioni x $0.06 = $3.60

**Budget totale stimato:** ~$4 con Vertex AI (nuovi account: coperto dai $300 crediti free trial)

---

### 7.2 Set di 15 Foto Consigliato

| # | Scenario | Sfondo | Stile | Uso |
|---|---------|--------|-------|-----|
| 1 | Ritratto formale | Ufficio moderno | Business portrait | LinkedIn profile, sito |
| 2 | Al telefono | Interno auto premium | Candid/lifestyle | Instagram Stories |
| 3 | Showroom automotive | BMW/Mercedes in bgd | Automotive professional | Sito hero |
| 4 | Outdoor aeroporto | Terminal moderno | Traveller professional | About page |
| 5 | Lavoro su laptop | Cafe europeo | Lifestyle business | About page |
| 6 | Stretta di mano | Ufficio neutro | Deal closing | Case study |
| 7 | Osserva un'auto | Concessionario EU | Expert evaluating | Trust |
| 8 | Su tablet/phone | Asta auto europea | Digital workflow | Features |
| 9 | Conferenza/evento | Sala convention | Speaker/expert | Credibilita' |
| 10 | Primo piano sorriso | Sfondo bokeh neutro | Approachable | WhatsApp profile |
| 11 | Outdoor citta' EU | Francoforte/Monaco | International | Background credibilita' |
| 12 | In macchina al telefono | Interno premium | Mobile professional | Lifestyle |
| 13 | Firma documenti | Scrivania legno | Trust/professional | Contratti |
| 14 | Con collega EU | Ufficio open space | Team/partnership | B2B credibilita' |
| 15 | Casual smart | Esterno con luce naturale | Human/relatable | Social media |

---

### 7.3 Modello di Referral Prompt (da adattare per ogni foto)

```
A photo of an Italian man in his late 30s, [DESCRIZIONE SPECIFICA LUCA],
[AZIONE/POSA specifica per scena],
[AMBIENTE: es. "modern European car dealership showroom, luxury vehicles visible"],
[ILLUMINAZIONE: es. "soft directional window light"],
shot on Canon EOS R5, [OTTICA: es. "85mm f/1.8"], [STILE: es. "shallow depth of field"],
photorealistic, professional photography, natural skin texture, slight film grain,
business casual attire [DETTAGLIO ABBIGLIAMENTO]

Negative: cartoon, plastic skin, waxy, over-smoothed, bad anatomy,
wrong number of fingers, extra limbs, asymmetrical face, glassy eyes,
watermark, signature, low quality, blurry
```

**[DESCRIZIONE SPECIFICA LUCA]** — compilare con i dati reali dopo aver visto le foto di riferimento:
```
[eta'] years old, [colore capelli], [lunghezza capelli],
[barba: clean shaved / light stubble / short beard],
[carnagione: olive/fair/mediterranean],
[costituzione: slim/athletic/medium build],
[tratto distintivo se presente]
```

---

## FONTI PRINCIPALI CITATE

| Fonte | URL | Tipo |
|-------|-----|------|
| Imagen Subject Customization Docs | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/subject-customization | Ufficiale Google |
| Imagen Seed/Deterministic Docs | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/generate-deterministic-images | Ufficiale Google |
| Imagen Prompt Guide Vertex AI | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/img-gen-prompt-guide | Ufficiale Google |
| Imagen API (Gemini API) | https://ai.google.dev/gemini-api/docs/imagen | Ufficiale Google |
| Gemini API Pricing | https://ai.google.dev/gemini-api/docs/pricing | Ufficiale Google |
| Vertex AI Models List | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models | Ufficiale Google |
| Veo 3 Docs | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-0-generate | Ufficiale Google |
| Imagen 4 Generate Docs | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/4-0-generate | Ufficiale Google |
| Atlabs Imagen 4 Prompting Guide | https://www.atlabs.ai/blog/imagen-4-prompting-guide | Community/verificato |
| Imagen 4 Ultra vs Standard | https://magichour.ai/blog/imagen-4-vs-imagen-4-ultra | Community |
| Veo 3 Character Consistency Pipeline | https://medium.com/google-cloud/veo-3-character-consistency-a-multi-modal-forensically-inspired-approach-972e4c1ceae5 | Google Cloud Community |
| SynthID Removability Analysis | https://www.aifreeapi.com/en/posts/synthid-watermark-removable | Community |
| C2PA Removal Guide | https://aimetadatacleaner.com/blog/remove-content-credentials-c2pa-guide-2025 | Community |
| C2PAremover GitHub | https://github.com/ngmisl/C2PAremover | Open source |
| EU AI Act Article 50 | https://artificialintelligenceact.eu/article/50/ | Legale |
| EU AI Act Enforcement Aug 2026 | https://www.aiipprotection.org/news/eu-ai-act-deepfake-disclosure-compliance.php | Legale |
| Negative Prompts Guide | https://pxz.ai/blog/best-negative-prompts-for-realistic-ai-images | Community |
| Free Tier Limits 2026 | https://blog.laozhang.ai/en/posts/gemini-image-generation-free-limit-2026 | Community |
| Google SynthID + C2PA announcement | https://www.how2shout.com/news/google-synthid-c2pa-ai-image-watermarks.html | News |

---

*Ultimo aggiornamento: 2026-04-04 | Prossima verifica consigliata: 2026-07-01 (i limiti free tier cambiano spesso)*
