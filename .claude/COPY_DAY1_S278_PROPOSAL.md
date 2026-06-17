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

## PROPOSTA (raccomandazione singola — variante RAGIONIERE/baseline, numeri-driven)

> Placeholder `{...}` = riempiti a invio dai dati di **uno scrape fidato** (gate-3:
> DEEP_PAGES≥80 + geo==IT + experiment-OFF). NESSUN numero inventato a mano.

```
Buongiorno, ho una {MODELLO} {ANNO}, {KM} km certificati: oggi sul mercato italiano
gira sui {€PREZZO_IT}, a lei arriverebbe pronta con circa {€MARGINE} netti di margine.
Le scrivo perché ho visto la sua attività a {CITTA}, ho preso il numero dalla vostra
pagina pubblica. Sono Azzurra, assistente di Luca Ferretti — se non le interessa me lo
dica e non la contatto più. Le mando la scheda con i dettagli?
```

5 righe. Veicolo+numeri prima (gancio) → provenienza → identità Azzurra + opt-out → domanda chiusa.

### Alternativa scartata (1 riga, perché)
Versione "ultra-corta" senza provenienza/opt-out: massimizza response rate ma **svuota il
balancing test** → scartata. Lo scopo qui non è solo il contatto, è la *difendibilità* del contatto.

## Nodi per OK Luke
- **N1** — provenienza: "pagina pubblica / Google Business" va bene come fonte dichiarata? (deve essere la fonte reale da cui il numero è stato preso).
- **N2** — archetipo: questa è baseline RAGIONIERE. NARCISO/BARONE vogliono meno numeri e più "esclusività" → tuning per-archetipo DOPO l'OK sulla struttura.
- **N3** — wiring: a OK, la copy entra nel runtime SOLO con i 3 gate tecnici verdi (E2E + trasparenza in produzione + base-mercato fidata). Prima resta proposta.

> Nota delega (REGOLA #0): bozza scritta in main-context e non delegata a `dealer-outreach`/
> `outreach-day1` perché deve incrociare le decisioni S277 (Azzurra) + il sostrato legale, che
> non vivono in quelle skill. Il tuning per-archetipo (N2) è invece delegabile.
