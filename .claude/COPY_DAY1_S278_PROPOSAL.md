# COPY DAY-1 — PROPOSTA S278 (da approvare Luke, NON wirata)

> Stato: **PROPOSTA**. NON è in `response-analyzer.py` né in nessun runtime.
> Si wira SOLO dopo OK esplicito di Luke (C1, S277). È anche il **sostrato del
> balancing test** legittimo-interesse (GDPR, Garante/Federprivacy 2026, S249):
> i 3 elementi di trasparenza qui sotto sono ciò che rende difendibile il primo contatto.

## Vincoli che la copy DEVE rispettare (da `.claude/rules/communication.md` + S277)
- Max 5 righe WA · primo contenuto = **veicolo reale con numeri reali** (mai presentazione).
- Domanda chiusa finale (risposta monosillabica).
- Numeri in **EUR netti** (mai percentuali). Lessico: "macchina/auto", "margine", "ci guadagna €X", "km certificati".
- VIETATO Day-1: "Germania", "import", "premium", "cerco auto", "estero", "veicolo EU", "ROI", "pipeline", "algoritmo", "reimportazione".
- **Firma = Azzurra**, assistente *dichiarata* di Luca Ferretti (S277). Mai "Luca" in 1ª persona sul testo WA.

## I 3 elementi di trasparenza (sostrato balancing test)
1. **Identità** → "Sono Azzurra, assistente di Luca Ferretti" (titolare del trattamento dichiarato).
2. **Provenienza del contatto** → numero da fonte pubblica del dealer (pagina/Google Business).
3. **Opt-out immediato** → "me lo dica e non la contatto più" (diritto di opposizione, 1 frase).

I 3 elementi stanno in 2 righe, così il veicolo resta il primo contenuto e il messaggio atterra "caldo".

---

## ⚠️ CORREZIONE S279 — la copy deve essere onesta come il dossier (verificato vs codice)
La v1 (sotto, BARRATA) quotava **prezzo-punto + margine-netto-punto-come-promessa**. Contraddice la
struttura del dossier verificata in `pdf_generator_enterprise.py:228-334`: **banda p25–p75** (non punto)
+ verdetto **CONDIZIONATO** ("valido solo se prezzo IT realizzato >= breakeven", es. 320d 35.699).
Promettere "≈€X netti" alla porta = falso-PASS + bait-and-switch + esposizione. **Regola: nessun numero
nel cold message che non regga la verifica del dossier.** Inoltre `km certificati` → `km dichiarati`
(prima del ritiro il km viene dall'annuncio, "verificabile al ritiro").

### v1 — SCARTATA (mente alla porta)
~~"...{KM} km certificati: oggi sul mercato italiano gira sui {€PREZZO_IT}, a lei arriverebbe pronta con circa {€MARGINE} netti di margine..."~~

## PROPOSTA v2 (raccomandazione singola — path (i): banda + tetto, RAGIONIERE numeri-driven onesto)

> Placeholder `{...}` = riempiti a invio dai dati di **uno scrape fidato** (gate-3:
> DEEP_PAGES≥80 + geo==IT + experiment-OFF). NESSUN numero inventato a mano.
> `{€BANDA_LOW}–{€BANDA_HIGH}` = p25–p75 dal motore. `{€MARG_HIGH}` = margine al band_high (TETTO, mai punto promesso).

```
Buongiorno, ho una {MODELLO} {ANNO}, {KM} km dichiarati: sul mercato italiano gli annunci
di pari configurazione stanno in una fascia di {€BANDA_LOW}–{€BANDA_HIGH}; a lei arriverebbe
pronta, con un margine fino a {€MARG_HIGH} a seconda del prezzo di vendita. Le scrivo perché
ho visto la sua attività a {CITTA}, ho preso il numero dalla {FONTE_REALE}. Sono Azzurra,
assistente di Luca Ferretti — se non le interessa me lo dica e non la contatto più. Le mando la scheda?
```

Veicolo+fascia (gancio onesto) → margine come TETTO condizionato → provenienza → identità Azzurra + opt-out → domanda chiusa.

### Alternativa (1 riga): path (ii) — gancio qualitativo, numeri solo nel dossier
"...c'è un margine interessante, glielo mostro nella scheda con i numeri e le fonti." Più sicura ma più
debole per il RAGIONIERE (un archetipo numbers-driven legge il qualitativo come sales-talk vago) →
**raccomando (i)**; (ii) è il fallback se la fascia sembra ancora troppo impegnativa.

## Nodi per OK Luke
- **N1 — provenienza (`{FONTE_REALE}`)**: dev'essere LETTERALMENTE il canale reale. Se prendi il numero
  da DB scrapato/AutoScout, la riga deve dirlo — una bugia sulla provenienza distrugge la credibilità che
  il messaggio costruisce. NB (paletto, non riapro il canale): "pubblico" NON è base giuridica — la
  provenienza dichiarata serve a trasparenza/balancing test, non sana il rischio cold WA (deciso-finale).
- **N2 — archetipo (differito)**: tuning NARCISO/BARONE DOPO. Vincolo invariante per OGNI archetipo:
  niente superlativi non verificabili ("occasione unica/eccezionale" — già vietati `_LLM_BANNED_WORDS:94`),
  **banda non punto, nessun margine promesso**.
- **N3 — wiring**: a OK, runtime SOLO con i 3 gate tecnici verdi. Prima resta proposta.
- **N-pick — (i) o (ii)?**: raccomando (i). Serve scelta Luke.

> Nota delega (REGOLA #0): bozza scritta in main-context e non delegata a `dealer-outreach`/
> `outreach-day1` perché deve incrociare le decisioni S277 (Azzurra) + il sostrato legale, che
> non vivono in quelle skill. Il tuning per-archetipo (N2) è invece delegabile.
