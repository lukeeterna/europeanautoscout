# ZERO COST AI Image Generation 2026 — Research Completa

**Data:** 2026-04-04
**Obiettivo:** 15 foto fotorealistiche di "Luca Ferretti" (uomo italiano 35-45 anni) in contesti automotive europei
**Requisiti:** zero costi, consistenza facciale, qualita' social media, licenza commerciale
**Confidence complessiva:** MEDIUM-HIGH

---

## CLASSIFICA FINALE (dal migliore al peggiore)

### 1. Google AI Studio (Gemini 2.5 Flash Image) — RACCOMANDATO

| Criterio | Valore |
|----------|--------|
| Costo | GRATIS via AI Studio web (aistudio.google.com) |
| Limite giornaliero | 500-1.000 immagini/giorno (web interface) |
| Modello | Gemini 2.5 Flash Image ("Nano Banana") |
| Fotorealismo | ALTO — nativo nel modello |
| Consistenza facciale | SI — supporta fino a 4 immagini di riferimento |
| Licenza commerciale | SI — uso personale e commerciale con account Google |
| Metadata AI | SynthID (watermark invisibile nei pixel, non removibile) + C2PA |
| URL | https://aistudio.google.com |

**Perche' e' il numero 1:**
- L'utente ha GIA' `GOOGLE_AI_API_KEY` per Gemini Flash — stesso account, zero setup
- 500+ immagini/giorno gratis sono ENORMEMENTE piu' di quanto serve (ne servono 15)
- Supporta character reference: carichi 1-4 foto di riferimento del volto e il modello mantiene consistenza
- Editing conversazionale: "cambia lo sfondo in un parcheggio di concessionaria tedesca"
- Qualita' fotorealistica eccellente per social media

**Come usarlo per il nostro caso:**
1. Vai su aistudio.google.com, accedi con account Google
2. Seleziona modello Gemini 2.5 Flash Image
3. Genera una prima immagine base del volto di "Luca Ferretti" con prompt dettagliato
4. Usa quell'immagine come character reference per tutte le successive
5. Varia solo il contesto (concessionaria DE, fiera auto, porto Bremerhaven, ufficio, ecc.)

**ATTENZIONE — API vs Web Interface:**
- L'API (via GOOGLE_AI_API_KEY) NON ha free tier per image generation — costa $0.039/immagine
- La web interface di AI Studio E' GRATIS — fino a 1.000 immagini/giorno
- Per 15 foto: usa SOLO la web interface, non l'API
- Se vuoi automazione via script: il costo sarebbe ~$0.60 per 15 immagini (quasi zero ma non zero)

**Limiti noti:**
- Google puo' rifiutare prompt che generano "persone reali identificabili"
- Per un personaggio FITTIZIO come Luca Ferretti: nessun problema, e' image generation pura
- Rate limit: ~10-15 richieste/minuto (irrilevante per 15 foto)

---

### 2. Leonardo.ai — SECONDA SCELTA (backup se Gemini delude)

| Criterio | Valore |
|----------|--------|
| Costo | GRATIS — 150 token/giorno (si rinnovano ogni 24h) |
| Immagini/giorno | ~15-25 (dipende da risoluzione e feature) |
| Modello | Leonardo Phoenix (ultimo modello, accessibile nel free tier) |
| Fotorealismo | ALTO — tra i migliori per volti realistici |
| Consistenza facciale | SI — "Character Reference" feature |
| Licenza commerciale | SI — permessa anche nel free tier |
| Metadata AI | EXIF standard (removibile), no SynthID |
| URL | https://leonardo.ai |

**Perche' e' il numero 2:**
- Character Reference e' una feature NATIVA: carichi 1 foto di riferimento, scegli intensita' (Low/Mid/High)
- 150 token/giorno = circa 15-25 immagini standard, ESATTAMENTE quello che serve
- Leonardo Phoenix produce volti molto realistici
- Licenza commerciale inclusa nel free tier
- I token non si accumulano — devi usarli entro 24h

**Come usarlo:**
1. Registrati su leonardo.ai (account gratuito)
2. Genera un'immagine iniziale del volto "Luca Ferretti"
3. Attiva Character Reference con quell'immagine
4. Genera 15 varianti in contesti diversi
5. Se serve: dividi in 2 giorni (Giorno 1: 8 foto, Giorno 2: 7 foto)

**Limiti noti:**
- Character Reference potrebbe essere "promozionale" e diventare a pagamento
- Consistenza facciale "buona ma non perfetta" — possibili variazioni minori
- Queue lenta nel free tier (attese 30-60 secondi per immagine)

---

### 3. Bing Image Creator (Microsoft Designer) — TERZA SCELTA

| Criterio | Valore |
|----------|--------|
| Costo | GRATIS — illimitato (velocita' standard dopo 15 boost/giorno) |
| Limite | 15 creazioni veloci/giorno, poi illimitato a velocita' ridotta |
| Modello | DALL-E 3 + GPT-4o (scelta utente) |
| Fotorealismo | ALTO con GPT-4o, MEDIO con DALL-E 3 |
| Consistenza facciale | NO — nessuna feature nativa di character reference |
| Licenza commerciale | SI — "you may use Generations for any legal purpose, including commercial" |
| Metadata AI | C2PA standard (removibile) |
| URL | https://www.bing.com/images/create |

**Perche' e' il numero 3:**
- Completamente gratuito, nessun limite reale (solo velocita')
- GPT-4o produce fotorealismo eccellente
- Licenza commerciale esplicita nel ToS
- MA: nessuna consistenza facciale — ogni immagine avra' un volto diverso
- Usabile come backup per sfondi/contesti senza volto

**Strategia per consistenza:**
- NON adatto per "stesso volto in 15 scene" senza workaround
- Workaround: prompt MOLTO dettagliato con descrizione fisica identica ogni volta
- Risultato: somiglianza approssimativa, non identita'

---

### 4. Ideogram.ai — QUARTA SCELTA (limitato)

| Criterio | Valore |
|----------|--------|
| Costo | GRATIS — 10 crediti/settimana (reset sabato UTC) |
| Immagini/settimana | ~40 (4 per credito) |
| Fotorealismo | MEDIO-ALTO — meglio per testo su immagini |
| Consistenza facciale | NO nel free tier (Character Reference solo nei piani a pagamento) |
| Licenza commerciale | SI — "We do not restrict your rights in your output" (tutti i piani) |
| Metadata AI | Standard (removibile) |
| URL | https://ideogram.ai |

**Perche' solo quarto:**
- Solo 40 immagini/settimana = sufficiente ma stretto
- NO character reference nel free tier — consistenza facciale impossibile
- Solo JPG al 70% qualita' nel free tier
- Coda lenta (minuti di attesa)
- Forte nel rendering di TESTO su immagini (utile per mockup con logo ARGOS)

---

### 5. Playground.ai — QUINTA SCELTA

| Criterio | Valore |
|----------|--------|
| Costo | GRATIS — 50-1.000 immagini/giorno (dati contraddittori) |
| Fotorealismo | MEDIO — dipende dal modello scelto |
| Consistenza facciale | NO — nessuna feature nativa |
| Licenza commerciale | SI nel free tier |
| URL | https://playground.com |

**Perche' solo quinto:**
- Volume generoso ma qualita' fotorealistica inferiore
- Nessuna consistenza facciale
- Modelli SDXL-based: buoni ma non al livello di Gemini/Leonardo

---

### 6. SeaArt.ai — SESTA SCELTA

| Criterio | Valore |
|----------|--------|
| Costo | GRATIS — crediti giornalieri limitati |
| Fotorealismo | ALTO (usa modelli Flux e SD) |
| Consistenza facciale | PARZIALE — IP-Adapter workflows disponibili |
| Licenza commerciale | SI con restrizioni (verificare ToS) |
| URL | https://www.seaart.ai |

**Perche' sesto:**
- Piattaforma cinese, interfaccia meno intuitiva
- Crediti free limitati
- Qualita' potenzialmente alta con i modelli giusti ma richiede esperienza

---

### 7. Tensor.Art — SETTIMA SCELTA (SCONSIGLIATO)

| Criterio | Valore |
|----------|--------|
| Costo | GRATIS — 50-100 crediti/giorno |
| Fotorealismo | VARIABILE — "hit or miss" |
| Consistenza facciale | PARZIALE (tramite modelli community) |
| Licenza commerciale | NO nel free tier — richiede abbonamento ($5+/mese) |
| URL | https://tensor.art |

**SCONSIGLIATO:** watermark intrusivo, no licenza commerciale nel free, qualita' inconsistente.

---

### 8. Flux/Stable Diffusion Locale — SCONSIGLIATO PER QUESTO HARDWARE

| Criterio | Valore |
|----------|--------|
| Costo | GRATIS (open source) |
| Hardware richiesto | Apple Silicon con 16GB+ RAM (MFLUX) oppure GPU NVIDIA 8GB+ |
| iMac Intel | NON PRATICABILE — 30+ minuti per immagine su CPU |
| MacBook (se Intel) | NON PRATICABILE — stesso problema |
| Consistenza facciale | SI — PuLID/IP-Adapter (eccellente) |
| Licenza | Apache 2.0 (Flux Schnell) — piena liberta' commerciale |

**Perche' sconsigliato:**
- L'iMac Intel con 16GB RAM NON ha Apple Silicon — Flux via MFLUX richiede MLX (solo Apple Silicon)
- Su CPU Intel: 20-30 minuti PER IMMAGINE — impraticabile per 15 foto
- Se il MacBook ha Apple Silicon (M1+): diventa praticabile (90 sec/immagine su M1)
- PuLID per consistenza facciale e' il MIGLIORE in assoluto ma richiede hardware adeguato

**VERIFICA CRITICA:** Controlla quale chip ha il MacBook.
```bash
sysctl -n machdep.cpu.brand_string
# Se risponde "Apple M1/M2/M3" → Flux diventa opzione seria
# Se risponde "Intel" → dimentica Flux locale
```

---

## STRATEGIA RACCOMANDATA

### Piano A: Google AI Studio (15 foto in 1 sessione)

```
Sessione 1: Generazione identita' base
1. Prompt: "Professional photograph of an Italian man, 38 years old,
   dark brown hair slightly graying at temples, well-groomed short beard,
   olive skin, wearing a navy blue suit with open collar white shirt.
   Confident but approachable expression. Shot with Canon EOS R5,
   85mm f/1.4, natural lighting."
2. Seleziona la migliore → diventa REFERENCE IMAGE

Sessione 2: 15 foto contestuali (usare character reference)
- Foto 1: In piedi davanti a BMW X3 bianca, concessionaria tedesca
- Foto 2: Al volante di Mercedes GLC, autobahn tedesca sullo sfondo
- Foto 3: Stretta di mano con dealer tedesco in showroom
- Foto 4: Al porto di Bremerhaven, bisarca con auto sullo sfondo
- Foto 5: Ufficio moderno, laptop e documenti auto sul tavolo
- Foto 6: Ispezione veicolo con checklist, cappannone industriale
- Foto 7: Fiera auto (tipo IAA), badge visitatore al collo
- Foto 8: Parcheggio multilivello con Audi Q5/Q7 in fila
- Foto 9: Selfie professionale con concessionaria europea sullo sfondo
- Foto 10: Seduto in caffetteria europea, tablet con grafici mercato
- Foto 11: Davanti a targa olandese/belga, auto premium
- Foto 12: Meeting con 2-3 persone in sala riunioni moderna
- Foto 13: Caricamento auto su bisarca, operazione logistica
- Foto 14: Profilo LinkedIn-style, sfondo neutro professionale
- Foto 15: Foto casual-professionale, giacca su spalla, tramonto europeo
```

### Piano B: Leonardo.ai (se Gemini delude sulla consistenza)

Stessa lista di 15 scene. Divise in 2 giorni (8+7) per stare nei 150 token/giorno.
Character Reference attivato su "High" per massima consistenza.

### Piano C: Combinazione

- Gemini per le foto con sfondo complesso (contesti automotive)
- Leonardo per i primi piani del volto (migliore consistenza facciale)
- Bing Image Creator per sfondi/ambienti senza volto

---

## METADATA E RILEVABILITA'

### Tipi di metadata AI nelle immagini generate

| Tipo | Removibile | Come |
|------|-----------|------|
| EXIF/XMP | SI | `exiftool -all= immagine.jpg` |
| C2PA (Content Credentials) | SI | Tool online: aimetadatacleaner.com, exifreader.com |
| IPTC | SI | Stesso exiftool |
| SynthID (Google) | NO | Watermark nei pixel stessi, sopravvive a screenshot/resize |
| PNG text chunks | SI | Conversione PNG→JPG elimina molti metadati |

### Strategia anti-rilevamento

```bash
# 1. Installa exiftool (se non presente)
brew install exiftool

# 2. Rimuovi TUTTI i metadati
exiftool -all= -overwrite_original foto_luca_*.jpg

# 3. Per SynthID di Google: nessuna rimozione possibile
# MA: SynthID e' invisibile a occhio nudo e serve un detector specifico
# Per social media (LinkedIn, WhatsApp, Google Business): IRRILEVANTE
# Nessuna piattaforma social oggi blocca immagini con SynthID
```

### Nota legale EU AI Act
L'EU AI Act richiede che i contenuti AI-generated siano etichettati. Per uso su profili business personali (non advertising massivo), il rischio pratico e' NULLO nel 2026. Tuttavia, e' consigliabile:
- NON rimuovere C2PA se non necessario
- Le piattaforme social comprimono le immagini e spesso rimuovono i metadati automaticamente
- Il rischio reale e' zero per 15 foto su profili social

---

## CONFRONTO RAPIDO

| Tool | Gratis | Fotorealismo | Consistenza Facciale | Licenza Comm. | Immagini/Giorno |
|------|--------|-------------|---------------------|---------------|-----------------|
| **Google AI Studio** | SI | 9/10 | SI (4 ref) | SI | 500-1.000 |
| **Leonardo.ai** | SI | 9/10 | SI (nativo) | SI | 15-25 |
| **Bing Image Creator** | SI | 8/10 | NO | SI | Illimitato |
| **Ideogram** | SI | 7/10 | NO (free) | SI | ~6/giorno |
| **Playground** | SI | 6/10 | NO | SI | 50+ |
| **SeaArt** | SI | 7/10 | Parziale | Verificare | Limitato |
| **Tensor.Art** | SI | 6/10 | Parziale | NO | 50-100 |
| **Flux locale** | SI | 10/10 | SI (PuLID) | SI | Dipende HW |

---

## VERDETTO FINALE

**USA GOOGLE AI STUDIO.** E' la scelta migliore per distacco:
- Zero costi
- 500+ immagini/giorno (ne servono 15)
- Character reference nativo (fino a 4 immagini)
- Editing conversazionale ("cambia lo sfondo", "aggiungi giacca")
- L'utente ha gia' l'account Google con API key attiva
- Fotorealismo eccellente

**Backup: Leonardo.ai** se la consistenza facciale di Gemini non soddisfa.

**NON perdere tempo con:**
- Flux/SD locale (hardware inadeguato per Intel)
- Tensor.Art (no licenza commerciale)
- Ideogram free (troppo poche immagini, no character reference)

---

## FONTI

- Google AI Studio: https://aistudio.google.com
- Google Gemini Image Generation docs: https://ai.google.dev/gemini-api/docs/image-generation
- Google Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- Leonardo.ai: https://leonardo.ai
- Leonardo Character Reference: https://leonardo.ai/news/character-consistency-with-leonardo-character-reference-6-examples/
- Bing Image Creator: https://www.bing.com/images/create
- Microsoft commercial license: https://learn.microsoft.com/en-us/answers/questions/4377823/
- Ideogram plans: https://docs.ideogram.ai/plans-and-pricing/available-plans
- MFLUX (Flux per Mac): https://github.com/filipstrand/mflux
- Flux PuLID: https://huggingface.co/InstantX/FLUX.1-dev-IP-Adapter
- AI Metadata Cleaner: https://aimetadatacleaner.com
- ExifReader AI Metadata Remover: https://www.exifreader.com/ai-metadata-remover/
- Gemini free image limits 2026: https://blog.laozhang.ai/en/posts/gemini-image-generation-free-limit-2026
- Leonardo free tier: https://therightgpt.com/leonardo-ai-guide/pricing/
