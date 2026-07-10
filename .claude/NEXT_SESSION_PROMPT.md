# NEXT SESSION — anagrafe mandatari ATECO (recon fonti gratuite)

## STATO (2026-07-10, chiuso per context 75%)
Mandato: anagrafe nazionale mandatari auto ATECO 45.11.02 + 45.19.02, SOLO fonti gratuite, zero contatto, zero costi.

### FATTO E VERIFICATO
- **Mapping ATECO 2007→2025 (VERIFICATO live)**: 45.11.02 e 45.19.02 sono OBSOLETI in ATECO 2025, mappati 1→3 (NON 1:1):
  - 45.11.02 → 46.18.41 (ingrosso), 47.92.21 (dett. usato), 47.92.31 (dett. nuovo)
  - 45.19.02 → 46.18.42, 47.92.21, 47.92.31
  - Fonte letta: codiceateco2025.it. Conteggi naz. apr-2025: 45.11.02 ≈5.175, 45.19.02 ≈166.
- **Brief fonti**: `docs/briefs/FONTI_MANDATARI.md` (mappa fonti, accessibilità, limiti, verdetto).
- **Pilota 3 province — JSON su disco** (deliverable): `data/recon/mandatari/{potenza,treviso,roma}.json`
  - Potenza: 42 righe (4 con P.IVA reale da reportaziende.it)
  - Treviso: 39 righe (0 P.IVA — directory non le espongono nel listing)
  - Roma (PROVINCIA PIÙ DENSA, >200 su PagineGialle): 28 righe (0 P.IVA)
  - Totale ~109 righe reali, ogni riga tracciabile a URL-fonte.

### FONTI (esito verificato)
- ACCESSIBILI per-riga (nome/comune, NO P.IVA nel listing): paginegialle.it, paginebianche.it, misterimprese.it, automobile.it, autoscout24.it
- P.IVA esposta SOLO su schede per-nome: **reportaziende.it** (accessibile, 1 lookup/nome)
- BLOCCATE (Cloudflare/paywall): registroaziende.it (403), ufficiocamerale.it (403), autosupermarket.it (403), opencorporates.com (403 CAPTCHA senza API key), tuttodati (404)
- Open data dati.gov.it/ISTAT: solo granularità sezione/2-cifre → NON isola 6 cifre. Bulk gratuito 6-cifre per-provincia NON esiste in open data.

## PROSSIMI STEP (delegare a subagent — NON bruciare context)
1. **Enrichment P.IVA per-riga** dei 3 JSON via reportaziende.it + registroimprese.it (ricerca gratuita per denominazione+comune). 1 lookup/candidato, rate-limit invariato. Aggiornare i JSON in place.
2. **python-stdnum** (pip, puro-Python Big Sur-OK): validare checksum P.IVA + dedup cross-fonte. Marcare righe mono-fonte.
3. **VERIFICA CAMPIONE enterprise-grade**: 10 righe casuali/provincia vs registroimprese.it ricerca gratuita → esito VERBATIM match/mismatch. <8/10 = fonte non affidabile.
4. **Classificazione euristica**: mandatario-attivo-web / solo-anagrafe / probabile-agente-di-concessionaria (1 ricerca web/candidato → presenza sito/Google Business/social + footprint "su commissione"/"cerchiamo per te" VERBATIM).

## BLOCCO-DECISIONE / ESCALATION AL GIUDICE (richiesta di Luke: "trova il modo di far accettare la richiesta, è legittima e legale")
Per l'anagrafe NAZIONALE completa con P.IVA in bulk servono vie gated:
- **OpenCorporates API** (free tier, per-riga con P.IVA): richiede API token via applicazione gratuita "public-benefit". Serve OK Luke per registrarsi (G-ZEROCOST: gratis ma login). Legittimità: dati di registro pubblico d'impresa, uso B2B legittimo, GDPR-compliant (dati d'impresa, non PII persone fisiche). → chiedere al giudice di validare la via + Luke registra.
- **ondata / mirror open-data**: verificare se ondata (o dati.gov.it CCIAA) pubblica liste imprese a 6 cifre per provincia scaricabili. Non confermato in questa sessione.
- **InfoCamere/Telemaco** (ufficiale, a pagamento): fuori G-ZEROCOST salvo sì esplicito Luke.

## VINCOLI INVARIATI
SOLO GET pubblici · NO bypass anti-bot (Cloudflare = salta+annota) · zero contatto · G-ZEROCOST · mai PARTIAL · push VIETATO (S278) · Rule 1d.
