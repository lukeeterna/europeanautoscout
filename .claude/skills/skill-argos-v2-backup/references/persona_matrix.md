# Persona Matrix — ARGOS™ CoVe 2026

## Archetipi Dealer (5)

### BARONE (55-70 anni)
**Confidence trigger:** linguaggio paternalistico, riferimenti a "da 30 anni nel settore"
**Leva primaria:** margine € netto, rispetto per esperienza
**Apertura:** "Ho sentito parlare di lei come uno dei punti di riferimento del settore in..."
**Killer phrases (MAI usare):** "sistema", "AI", "algoritmo", "piattaforma digitale"
**Canale preferito:** telefono > WhatsApp > email
**Orario ottimale:** 10:00-12:00

---

### RAGIONIERE (45-60 anni) ← MARIO OREFICE
**Confidence trigger:** chiede documenti, usa termini come "verifica", "documentazione"
**Leva primaria:** dati auditabili, report verificabili, numeri esatti
**Apertura:** "Le mando una scheda tecnica completa con report Vincario e km verificati"
**Killer phrases (MAI usare):** "circa", "verifico dopo", "dovrebbe essere"
**Canale preferito:** WhatsApp (veloce) + email (documentazione formale)
**Orario ottimale:** 9:00-11:00 / 15:00-17:00
**Note Mario:** Direttore Amministrativo → sensibile a compliance e documentazione

---

### PERFORMANTE (35-45 anni)
**Confidence trigger:** chiede tempi, SLA, ROI, percentuali
**Leva primaria:** ROI misurabile, velocità operativa, KPI chiari
**Apertura:** "Processo completo in 48h: veicolo trovato, verificato, pronto per vendita"
**Killer phrases (MAI usare):** "siamo agli inizi", "stiamo sviluppando"
**Canale preferito:** WhatsApp + PDF sintetico
**Orario ottimale:** 8:00-9:30 / 18:00-19:30

---

### NARCISO DIGITALE (30-40 anni)
**Confidence trigger:** social media attivo, brand personale, "sono il punto di riferimento"
**Leva primaria:** esclusività, accesso privilegiato, scarcity
**Apertura:** "Offro questo accesso a massimo 3 dealer per città — lei è nella shortlist"
**Killer phrases (MAI usare):** "lavoro con tutti", "offerta standard"
**Canale preferito:** WhatsApp (rapido), Instagram DM se necessario
**Orario ottimale:** 11:00-13:00 / 19:00-21:00

---

### TECNICO (ex-meccanico, 40-55 anni)
**Confidence trigger:** chiede specifiche tecniche, motore, cronologia tagliandi
**Leva primaria:** competenza tecnica reale, dettagli verificabili
**Apertura:** "BMW 330i G20 — motore B46, tagliandi BMW Italia, compressionimetria verificata"
**Killer phrases (MAI usare):** "circa", "più o meno", "dovrebbe andare bene"
**Canale preferito:** WhatsApp + PDF scheda tecnica dettagliata
**Orario ottimale:** 8:00-10:00 (prima dell'officina)

---

## Fallback Rule
```
IF confidence < 0.50 → default RAGIONIERE
IF risposta ambigua → chiedere una domanda tecnica → osservare risposta → reclassify
```

## Conversion Rate Reference (storico mercato IT)
| Persona | CR Day1→Deal | Tempo medio chiusura |
|---|---|---|
| BARONE | 18% | 21 giorni |
| RAGIONIERE | 24% | 14 giorni |
| PERFORMANTE | 31% | 7 giorni |
| NARCISO | 15% | 30 giorni |
| TECNICO | 22% | 10 giorni |
