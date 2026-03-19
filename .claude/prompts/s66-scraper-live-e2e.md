Session 66 — SCRAPER TOTALI EU + PDF DOSSIER + INFRASTRUTTURA COMPLETA

CONTESTO RAPIDO:
- S65: costruito Market Intelligence System base (tools/scrapers/, 10 file, 190KB)
- AutoScout24 DE testato LIVE: 200 OK, __NEXT_DATA__ con 20 listing/pagina
- BUG NOTO: interfaccia BaseScraper vs scraper concreti disallineata (nomi metodi)
- URL AutoScout24: formato corretto è `?make=bmw&model=3er` (NON `/lst/bmw/3er-reihe`)
- 60+ portali EU mappati in research/s65_all_eu_car_portals.md
- Auto-invio WA fixato ma test E2E non ancora eseguito
- Fondatore: TUTTI i portali, dati reali, no cazzate, enterprise grade

ROADMAP AGGIORNATA (messaggistica dealer POSTICIPATA):
```
S66: Fix scraper base + TUTTI gli scraper EU + PDF dossier professionale
S67: Deploy scraper iMac PM2 + primo run reale + trend DB + Telegram digest
S68: Test E2E WA + riscrittura Day 1 con veicolo reale da scraper
S69: Day 1 nuovi Salerno con dati reali + carVertical integration
S70+: Primo deal → sourcing EU → consegna → fee
```

═══════════════════════════════════════════════════════════════════
TASK S66 — ORDINE DI ESECUZIONE
═══════════════════════════════════════════════════════════════════

FASE 1 — FIX SCRAPER BASE (prerequisito per tutto il resto)
─────────────────────────────────────────────────────────────
1a. Fix interfaccia BaseScraper:
    - `_fetch` → `fetch` (pubblico)
    - `scrape_model` deve essere il metodo standard che tutti usano
    - AutoScoutScraper e MobileDeScraper devono implementare stessa interfaccia

1b. Fix URL builder AutoScout24:
    - Formato corretto: `?make=bmw&model=3er` (testato live, funziona)
    - NON `/lst/bmw/3er-reihe` (testato, dà 404)

1c. Fix parser AutoScout24 per struttura __NEXT_DATA__ reale:
    - listing.vehicle.make, listing.vehicle.model
    - listing.vehicle.mileageInKm, listing.vehicle.modelVersionInput
    - listing.price.priceFormatted ("€ 27.800")
    - listing.url, listing.images, listing.location.countryCode
    - listing.seller (tipo venditore)

1d. Test reale: BMW Serie 3 DE → parsing → salvataggio DB → OK

FASE 2 — TUTTI GLI SCRAPER EU (priorità massima S66)
─────────────────────────────────────────────────────
Per OGNI portale: crea scraper dedicato. Usa agent/subagent in parallelo.
Riferimento completo: research/s65_all_eu_car_portals.md

GERMANIA (mercato primario):
  ✅ AutoScout24.de — già fatto, da fixare
  ✅ Mobile.de — già fatto, da fixare interfaccia
  ☐ eBay Kleinanzeigen (kleinanzeigen.de) — 800K+ auto, privati gems

OLANDA:
  ☐ Marktplaats.nl — 200K+ auto, principale NL
  ☐ AutoTrack.nl — 150K+, ora AutoScout24 Group

BELGIO:
  ✅ AutoScout24.be — coperto dal multi-country
  ☐ 2dehands.be — 80K+ auto, privati belgi

AUSTRIA:
  ✅ AutoScout24.at — coperto dal multi-country
  ☐ willhaben.at — 188K+ auto, principale AT

FRANCIA:
  ✅ AutoScout24.fr — coperto dal multi-country
  ☐ LaCentrale.fr — 350K+ listing, dealer focus
  ☐ LeBonCoin.fr — 500K+ auto (a pagamento per venditori dal 2025)

SVEZIA:
  ✅ AutoScout24.se — coperto dal multi-country
  ☐ Blocket.se — 100K+ auto, principale SE
  ☐ Bytbil.com — 80K+, dealer SE

REPUBBLICA CECA (sottovalutato: -15/20% vs DE):
  ☐ Sauto.cz — principale CZ
  ☐ TipCars.com — secondo CZ

POLONIA (volume enorme, ATTENZIONE km):
  ☐ Otomoto.pl — 300K+ listing

ITALIA (per confronto prezzi):
  ✅ AutoScout24.it — coperto
  ☐ Subito.it — per benchmark prezzi IT

SPAGNA:
  ☐ Coches.net — principale ES

B2B / ASTE:
  ☐ eCarsTrade — 18K+ auto/settimana, flotte leasing EU
  ☐ CarOnSale — B2B, registrazione gratuita
  ☐ Carvago.com — cross-border EU, aggregatore

OEM CERTIFIED (per premium/supercar):
  ☐ BMW Premium Selection (bmw-selection.com)
  ☐ Mercedes-Benz Certified
  ☐ Audi Approved Plus
  ☐ Porsche Approved

AGGREGATORI:
  ☐ TheParking.eu — aggrega tutti i portali EU
  ☐ car.info — dati tecnici e prezzi

Totale: ~20 nuovi scraper da costruire. Lanciarli con agent in parallelo (4-5 alla volta).

FASE 3 — PDF DOSSIER PROFESSIONALE (tools/scripts/pdf_generator_enterprise.py)
────────────────────────────────────────────────────────────────────────────────
Esiste già uno skeleton (467 righe, reportlab). VA RISCRITTO completamente:

3a. Layout professionale A4:
    - Header ARGOS™ con logo
    - Sezione immagini: grid 2x2 o 3x2, HIGH DEFINITION
    - Dettagli veicolo: tabella completa (make, model, anno, km, fuel, cambio, colore, potenza)
    - ARGOS Score™ breakdown con grafica (barre colorate, non solo numeri)
    - Analisi finanziaria: prezzo fonte, stima IT, margine, fee, margine netto
    - Sezione verifica: check effettuati, stato
    - Footer: contatto Luca Ferretti, timestamp generazione

3b. SISTEMA IMMAGINI AUTOMATICO:
    - Lo scraper già cattura image_urls dal listing
    - Scaricare TUTTE le immagini in alta risoluzione (non thumbnail)
    - AutoScout24/Mobile.de hanno immagini HD accessibili via URL diretto
    - Salvare in /tmp/argos_images/{listing_id}/ per generazione PDF
    - Nel PDF: immagini full-width per la prima, grid per le altre
    - 360° se disponibile (alcuni listing hanno foto multi-angolo)

3c. REGOLA CRITICA — NESSUN RIFERIMENTO ALLA FONTE:
    - Il PDF NON deve contenere: URL del listing, nome venditore, città del venditore
    - Solo: paese di provenienza generico (es. "Germania"), nessun dettaglio identificativo
    - Il dealer NON deve poter trovare l'auto da solo prima di pagare la fee
    - Dopo il pagamento: disclosure completa con tutti i dettagli

3d. Output:
    - PDF professionale A4, 2-3 pagine
    - Invio via WA come documento allegato (il daemon supporta già media)
    - CLI: `python3 tools/scripts/pdf_generator_enterprise.py --listing-id XXX --dealer-id YYY`

FASE 4 — FIX E TEST E2E (completamento S65)
─────────────────────────────────────────────
4a. Test E2E WA: founder invia dal 393314928901 → daemon → analyzer → auto-invio
4b. Verificare /tmp/argos-analyzer.log
4c. Verificare Day 3 scheduler per SALERNO_001/002 (21 marzo)

FASE 5 — DEPLOY + SCHEDULING
─────────────────────────────
5a. Deploy tutti gli scraper su iMac
5b. Creare ecosystem.market.config.js per PM2
5c. Cron: scraping alle 05:00 lun-ven
5d. Digest Telegram alle 08:00 con trend + deal alerts
5e. Primo run reale su TUTTI i portali → popolamento DB

═══════════════════════════════════════════════════════════════════
REGOLE IMMUTABILI
═══════════════════════════════════════════════════════════════════
- DATI REALI O NIENTE — mai placeholder, mai TODO, mai "da implementare"
- Agent/subagent per OGNI task complesso (in parallelo quando possibile)
- Per OGNI task: cerca/crea skill enterprise grade
- Code review (/simplify) dopo ogni build
- Tutto gira su iMac (ssh gianlucadistasi@192.168.1.2)
- MAI CoVe/Claude/AI nei messaggi dealer
- MAI DEKRA/DAT nei messaggi finché non operativi
- MAI fonte/URL/venditore nel PDF prima del pagamento fee
- "TUTTO SI PUÒ FARE, BISOGNA SOLO TROVARE IL MODO"
- NON dire "non possiamo" — cerca come si fa
- COSTRUISCI, NON PARLARE
Procedi autonomamente. Sei il CTO.
