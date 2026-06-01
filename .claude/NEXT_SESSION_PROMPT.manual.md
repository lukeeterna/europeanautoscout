# S217 — Gate anti-reverse (esito Luke) + C-E2E-ZERO cablaggio. Day 1 Stile Car

> Branch `s210/audit-master-plan`. S215 diagnosi. S216 = correzione decisione CTO + gate empirico generato.
> Day 1 parte SOLO quando E2E VERDE su TEST_FOUNDER 393314928901 + Luke "pienamente soddisfatto".

## DECISIONE CTO S216 — correzione del reframe S215 (leggere PRIMA di toccare codice)

**Lo stadio anti-reverse pHash/dHash del prompt S215 era basato su premessa FALSA** (vincolo #1, verificato WebSearch S216):
- Google Lens/Reverse Image NON usa pHash/dHash → usa **embedding semantici**, robusti a crop/resize/recompress/color-shift. Trasformare i pixel NON difende da Google.
- TinEye (ImagePrint) è più attaccabile ma solo via perturbazioni adversarial calcolate (Glaze/Fawkes) → richiedono torch (**blacklist Big Sur, vincolo #8**), model-specific, non deterministiche → ESCLUSE.
- È la ragione per cui S176→S187 hanno fallito 6 volte: inseguivano una difesa che non può vincere il matching semantico.

**Decisione**: NON implementare lo stadio anti-reverse. L'intento DECIDED Luke ("immagini non reverse-searchable", gate "0 match") resta valido, ma due fattori del NOSTRO caso vanno MISURATI prima di concludere:
1. Portali di nicchia EU (valore ARGOS) = **mal indicizzati** da Google/TinEye → possibile 0 match per non-indicizzazione.
2. Watermark ARGOS occlude → può perturbare l'embedding. Sconosciuto finché non misurato.

**Luke S216**: foto REALI processate dalle feature ARGOS esistenti (sanitizer + watermark), pseudo-produzione. → si MISURA con gate empirico, NON si costruisce filtro su premessa falsa.

## GATE EMPIRICO — ESITO S216: FALLITO (transform morto)
- Luke ha caricato sample0 + sample1 su TinEye. **PROCESSED beccato su entrambi** (match esatto identico
  all'ORIGINAL: sample0→autoscout24.com/.bg BMW 330; sample1→importemoi.pt/fr + autoscout24.de BMW X1).
- CONCLUSIONE: sanitizer (crop+mask) + watermark ARGOS 0.35 NON rompono TinEye, e Google Lens (embedding
  semantico) è ancora più robusto. La via "foto reale trasformata nel preview" è **empiricamente refutata**.
  NON reintrodurre transform pixel (pHash/crop/watermark) come difesa anti-reverse: provato morto S216.
- VINCOLO PRODOTTO Luke S216: "non possiamo proporre auto senza mostrarla" → no-foto NON accettato.
  Il problema diventa: mostrare l'auto VERA (carrozzeria/interni/km/condizione) senza foto rintracciabile alla sorgente.

## PROSSIMO PASSO S217 = Deep Research (in corso, azione Luke)
- Luke lancia **Gemini Deep Research** (NON modello math/coding) col prompt in `.claude/S217_DEEP_RESEARCH_PROMPT.md`.
- S217 STEP 0: prendere output Deep Research di Luke → **validare claim** (vincolo #1, no fiducia cieca) →
  raccomandazione singola implementabile zero-cost Big Sur-no-GPU.
- Ipotesi CTO da confermare/refutare: img2img regeneration stessa auto (pixel nuovi non matchabili) vs
  car-isolation+sfondo neutro (rischio: corpo-auto resta semantic-matchabile). Background-only NON basta.
- Solo DOPO soluzione foto validata → C-E2E-ZERO (cablaggio create_deal) → E2E TEST_FOUNDER.

## (storico) GATE EMPIRICO — generato S216
- 10 file generati in **`/Volumes/MontereyT7/argos-poc/S216_gate/`** (5 ORIGINAL + 5 PROCESSED).
  - PROCESSED = pipeline ARGOS reale: `sanitize_image` + `apply_watermark` (ciò che il dealer vede).
  - Sample reali AS24.de (sanitizer ha mascherato PII reale: telefono +49, testo dealer).
- Luke carica su **Google Reverse Image (images.google.com) + TinEye** OGNI file:
  - `sampleN_ORIGINAL.jpg` = **controllo positivo** (deve matchare l'inserzione AS24 → prova che è indicizzata)
  - `sampleN_PROCESSED.jpg` = **test** (target: 0 match)
- **Lettura esito**:
  - ORIGINAL matcha + PROCESSED no → **VITTORIA**: feature esistenti sufficienti, C-SAN-001 chiude "verificato empirico", foto reali nel preview. Niente codice nuovo.
  - PROCESSED matcha → fallback data-driven: crop più aggressivo (degrada foto) o no-foto nel preview. MAI trucchi pHash.
  - Né ORIGINAL né PROCESSED matchano → inconcludente (portale non indicizzato): annota, ripeti su sample da portale più indicizzato o accetta rischio basso.

## ORDINE S217
1° Esito gate da Luke (sopra) → chiudi C-SAN-001 con la lettura corrispondente.
2° **C-E2E-ZERO** = vero blocker Day-1. Cablare `create_deal(source_locked=...)` (def `comm-broker/deal_state_machine.py:223`, ZERO call-site oggi) nel punto reale d'invio dossier preview. Garantire che il preview NON esponga fonte (gating S214 ✓) e, secondo esito gate, gestire le foto. Mappa cablaggio dettagliata in handoff S215 (sotto, sezione C-E2E-ZERO).
3° E2E completo TEST_FOUNDER 393314928901.
4° (separato) C-COMM-INTEL-001 — scope onesto, non fix da 2h. Touchpoint Day 3 "Foto HD" = stesso problema reverse-search pre-pagamento, da risolvere QUI con stesso principio.

## C-E2E-ZERO — mappa cablaggio (verificata agente Explore S215)
- `create_deal(deal_id, dealer_alias, seller_alias, vehicle_desc, source_locked: dict, db_path, fee_eur)` def `comm-broker/deal_state_machine.py:223-254`. source_locked = {listing_url, seller_name, seller_city, seller_phone, portal}.
- NESSUN call-site reale (solo def + errore stringa `pdf_gated_source.py:90`).
- FSM stati :79-87 offer_sent→accepted→docs_shared→payment_pending→payment_confirmed(reveal). `confirm_payment` :92-93. Reveal via `release_source_dossier` (chiamato `tools/g_approval.py:199`).
- `comm-broker/wa_bridge.py:295-317` `_open_fsm` assume "Deal già creato altrove" — non esiste.
- Dati: CoVe DuckDB `cove_results` ha SOLO listing_id+source. seller_name/city/phone NON presenti → enrichment da scraper DB (`vehicle_listings`/`vehicle_images`).
- AZIONE: cablare `create_deal(source_locked=...)` nel punto REALE d'invio dossier preview (candidati `tools/batch_runner.py:271` `generate_opportunity_dossier` + flusso send-doc wa-daemon). Persistere deal_id per riconciliare reply WA.

## NOTE
- Working tree molto sporco (prompts/*.md cancellati). NON committare a caso: solo file in-scope.
- Garanzia gating = gating-fonte S214 ✓ + (esito gate anti-reverse). NON serve lo stadio pHash del vecchio prompt.
- Script gate riproducibile: `/tmp/s216_gate_anti_reverse.py`.
