# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 65 — 2026-03-19

---

## S65 COMPLETATA — PIVOT STRATEGICO + MARKET INTELLIGENCE

### FIX DEPLOYATI (iMac, daemon riavviato)
- `response-analyzer.py`: auto-invio via `curl POST http://127.0.0.1:9191/send` (daemon session)
- `wa-daemon.js`: analyzer log su `/tmp/argos-analyzer.log`
- TEST_FOUNDER: `393314928901`, Day 1 inviato

### MARKET INTELLIGENCE SYSTEM (tools/scrapers/ — 10 file, 190KB)
- AutoScout24 (7 paesi) + Mobile.de + orchestratore + trend analyzer + Telegram digest
- 8 marchi (BMW/Merc/Audi/Porsche/Lambo/Ferrari/McLaren/Range Rover), 33 modelli
- Test reale AutoScout24 DE: 200 OK, __NEXT_DATA__ con 20 listing/pagina
- BUG: interfaccia BaseScraper disallineata → fixare nomi metodi

### 4 RICERCHE (research/s65_*)
1. Dealer buying behavior: on-demand, holding cost €350-460/mese, fee ARGOS < DIY
2. Dealer portals: ALL-INCLUSIVE, Sud = blue ocean, nessun competitor full-service IT
3. Credibilità: OUE Estonia €600-1.200, carVertical €30, DEKRA €121, trasporto €600-900
4. 60+ portali EU mappati, CZ sottovalutato, Carapis API per 25+ mercati

### DECISIONI FOUNDER
- NO P.IVA → pagamento Revolut/BBVA
- DEKRA/DAT tolti dai messaggi
- TUTTI i portali senza limiti
- Disposto a drive-it-home

---

## ROADMAP S66+

```
S66: Fix scraper + primo run reale + test E2E WA + riscrittura Day 1 con veicolo reale
S67: Scraper aggiuntivi (willhaben/Marktplaats/Sauto.cz) + deploy PM2 iMac + Day 3 live
S68: Day 1 nuovi Salerno con dati reali + risposte live + carVertical integration
S69+: Primo deal → sourcing EU → consegna → fee incassata
```
