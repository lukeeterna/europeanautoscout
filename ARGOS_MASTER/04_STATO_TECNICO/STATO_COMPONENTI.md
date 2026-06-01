# ARGOS — STATO TECNICO COMPONENTI
> Supporto a 00_INDEX/ARGOS_MASTER_PLAN.md
> ⚠ CC è l'autorità su questo file. I valori qui sono l'ultima fotografia nota a Claude AI ed è ESPLICITAMENTE fallibile.
> Legenda: [VERIFICATO] = girato su dati reali · [PARZIALE] = esiste ma incompleto/non testato · [DA FARE] = non esiste o non funziona · [BUG NOTO] = esiste ma rotto.

---

## WORKSPACE
- Path reale: `~/Documents/combaretrovamiauto-enterprise` (NON app-antigravity-auto — quello è stale). [VERIFICATO via audit]

## FASE 3 — SOURCING
- **AS24 source=DE → `__NEXT_DATA__` JSON da IP italiano**: [VERIFICATO] — chiude il guardrail 0-cost senza IP esteri né servizi a pagamento. È il pezzo più solido.
- **"100+ portali europei"**: [DA FARE] come numero. È un TARGET, non lo stato. Realmente mappati molti meno. Subito (403/captcha) e automobile.it (404, schema URL cambiato) non integrati. Non scrivere "100 portali" come fatto.
- **Motore scoring CoVe v4**: [VERIFICATO in produzione 2026-03-03] — Bayesian Si=μ−λ·σ (λ=0.25), soglie DEALER_PREMIUM=0.75 / VIN_CHECK=0.60, fraud flags, logging DuckDB. Nota storica: "CoVe v4 untested in practice" emerse in un audit pre-pivot → confermare con CC se è stato testato su volume reale dopo la messa in produzione.

## NODO PAGAMENTO — SANITIZER IMMAGINI (Fase 4)
- **Sanitizer anti reverse-image-search**: [PARZIALE]. Esiste un sanitizer (riferimenti S179b). Lo scopo giusto è rendere le foto non rintracciabili + secretare la fonte.
- **Plate-detection (oscurare targhe)**: [BUG NOTO]. Nei test di maggio il detector beccava i **watermark URL** dei seller (es. "www.baum-automobile.de") invece delle **targhe vere**: 5 falsi positivi / 0 veri positivi su un sample, targa reale non presa. Il modello (Koushim/generico) NON copre il dominio targhe-europee. Serve un modello plate-detection europeo specifico o un fine-tuning. → NON dare "ARGOS modifica le immagini in automatico" come fatto: è codice da sistemare.
- **Lezione strategica (sessione Stile Car, mag)**: nascondere il *venditore* in un dossier dealer-to-dealer è fragile (il dealer esperto capisce che ARGOS è broker). La leva forte NON è nascondere il watermark, è **non dare la posizione/fonte fino a fee pagata**. Il sanitizer-immagini è il secondo strato; la secretazione-fonte è il primo.

## FASE 5 — PAGAMENTI
- **Stack pagamento controllato**: [DA FARE per ARGOS]. Esiste uno stack maturo su FLUXION (Stripe + Worker WebCrypto Ed25519, webhook idempotenza INSERT→generate→email→UPDATE, D1, replay-dedup). Verificare con CC quanto è riusabile per ARGOS. Il gating "rilascio-fonte SOLO post-pagamento-confermato" è da progettare e implementare.

## FASE 1 — ACQUISIZIONE / SALES AGENT + SCRAPER MARCHE (pilota)
- **SALES AGENT (contatto dealer automatizzato)**: [DA FARE/VERIFICARE]. È il componente che contatta i dealer con KB pre-addestrata (persona Luca Ferretti, persone-dealer, obiezioni, leve scarsità). NON il founder. Verificare con CC cosa esiste già: c'era un agente conversazionale n8n (escalation/success handler, stage, turni, Telegram HITL) costruito nella fase brokerage — quanto è riusabile per il modello attuale? La KB pre-addestrata è assemblata? Lo stato reale lo dà CC.
- **Scraper s206 Marche**: [PARZIALE]. Ultimo run S209 (2026-06-01): fix telefono applicato e verificato sul diff; 0→135 prospect (SPOF telefono eliminato). MA: con telefono vero solo 4; 131 da recuperare manuale; 30 plausibili (1-8 auto).
- **Root cause confermata**: AS24 non espone seller.phone e le description sono testo marketing senza numeri. Il regex è corretto, il dato non c'è nella fonte. I 4 telefoni vengono da Subito/Automobile.it.
  - ⚠ DA VERIFICARE con CC: come fanno Subito/Automobile.it a dare 4 numeri se a S208 davano 403/404? Controllare che non siano artefatti di parsing su pagine d'errore PRIMA di chiamarli.
- **Decisione**: lo scraper NON è il modo giusto per costruire la lista-prospect del campione (vedi INTELLIGENCE_DEALER.md). Serve per il sourcing (Fase 3). La lista-prospect su cui gira il sales agent si costruisce dai portali (manuale/reverse).
- **corpus_register.md**: [VERIFICATO committato] — 171 frasi corpus reali AS24, commit 5ac1214 (S208), branch s206/marche-register. Contenuto verbatim da dumpare con CC; serve per montare la traccia colloquio.

## FASE 2 — CONTENUTI
- **Pipeline contenuti per ARGOS**: [DA FARE/PARZIALE]. Esiste build_video.py + storyboard.json su FLUXION (9 verticali, parrucchiere completato). Da tarare per il premium-auto ARGOS. Verificare riuso con CC.

## INFRA STORICA (riferimento)
- whatsapp-web.js + WAHA WEBJS su iMac (browser-based, no API ufficiale). Anti-ban: SIM italiana, warm-up 14gg, max 5 contatti/giorno. Hard limits: sleep(15), Semaphore(5), DAILY_LIMIT=30. Bug dedup daemon WA: noto, fix pending.
- DuckDB schema: `recommendation` (non verdict), `analyzed_at` (non created_at).
- Telegram Chat ID 931063621 = HITL ARGOS, riservato.

---

## CHECKLIST "NON DARE PER FATTO"
Prima di scrivere in qualsiasi sessione che un componente è pronto, verifica con CC. I tre più a rischio di falso-positivo storico:
1. "100+ portali" → realmente molti meno.
2. "ARGOS sanitizza le immagini" → plate-detection ha bug noto.
3. "stack pagamenti pronto" → è di FLUXION, per ARGOS è da fare.
