# EXECUTION REPORT — S207 Marche Register (ri-target modello mandato)
_Data: 2026-05-30 22:59 | Elapsed: 985s_

## 0. Cambio modello S206 → S207 (cosa è cambiato e perchè)

**S206 (vecchio, broker supply-side)**: scoring premiava stock visibile 5-30 auto e segnalava prospect ricaricabili EU→IT (filtro F5 — ereditato dal motore CoVe, NON presente in questo scraper).

**S207 (nuovo, mandato demand-side)**: il cliente ARGOS è un micro-operatore che vende SU MANDATO, non tiene stock (0-2 auto), compra solo dopo richiesta cliente altospendente.

Modifiche operative:
- D1: invertita logica stock → `plausibile` 1-8 auto, `borderline` 9-15, `deprioritizzato` 16+, `escluso` big dealer ufficiale
- D2: filtro F5 (anomalia prezzo EU→IT) verificato NON presente in questo scraper — confermata non-applicabilità a scoring prospect (resta in CoVe per scoring veicoli)
- D3: `flag_target_alto_si_no` → `flag_micro_operatore_plausibile`; aggiunte colonne `multi_brand` e `accesso_clienti=DA_VERIFICARE_AL_TELEFONO`
- D4: telefono mandatory (skip prospect senza numero — riga inutile per Luke)
- D5: tabella onestà 4 metriche + gate VERDE solo su dati reali

**Onestà del segnale**: l'accesso a compratori altospendenti NON è visibile in un annuncio. 
`flag_micro_operatore_plausibile` indica solo la _forma_ del seller (micro/multi-brand/no-big), NON la qualifica reale. 
Verità ottenibile SOLO via telefonata Luke.

---
## 1. Tabella onestà (D5 — gate trasparente)

| Metrica | Valore | Soglia VERDE | Stato |
|---|---|---|---|
| Portali con >=5 listing | 1/3 | >=2 | GIALLO |
| % listing con description (>50 char) | 13% | >=40% | GIALLO |
| Prospect con telefono (post-skip) | 0 | >=10 | GIALLO |
| Plausibili (1-8 auto, no big dealer) | 0 | >=3 | GIALLO |

**Listing per portale:**
- autoscout24: 184 listing  [OK]
- subito: 0 listing  [403/captcha?]
- automobile.it: 0 listing  [403/captcha?]

---
## 2. Conteggi prospect (schema S207)

- Listing grezzi totali: **184**
- Listing in range prezzo 40,000-100,000€: **184**
- Operatori unici con telefono: **0** (riga senza telefono = scartata)
- Multi-brand (>=2 brand nel stock visibile): **0**

**Breakdown flag_micro_operatore_plausibile:**
- plausibile (1-8 auto, no big dealer): **0**  ← TARGET PRIMARIO chiamate Luke
- borderline (9-15 auto): **0**
- deprioritizzato (16+ auto): **0**
- escluso (big dealer ufficiale): **0**

**Plausibili per provincia:**

---
## 3. Top frasi ricorrenti per funzione

**Descrizione auto** (120 totali):
  - "Services [6AE] (DI SERIE)<br />- BMW Widescreen [6WC] (DI SERIE)<br />- Bracciolo centrale anteriore con vano portaogget"
  - "cerchi in lega [2PA] (DI SERIE)<br />- Calandra a doppio rene in nero lucido senza cornice con listelli doppi M e badge "
  - "forgiati M doppi raggi st"
  - "trazione (DI SERIE)<br />- Copertura motore con badge M (DI SERIE)<br />- Correttore assetto fari (DI SERIE)<br />- Crui"
  - "LED (DI SERIE)<br />- Fari fendinebbia (DI SERIE)<br />- Filtro antiparticolato OPF per motori benzina (DI SERIE)<br />-"

**Garanzia** (18 totali):
  - "Garanzia Legale di conformità come previsto dalle leggi vigenti, approvate dall&#x27"
  - "GARANZIA UFFICIALE BMW BEST4 FIN A 07/2029 OPPURE 150"
  - "Garanzia<br />Libretto degli assegni mantenuto<br />Attrezzatura sportiva<br />Cerchi in"
  - "garanzia casa madre PREMIUM SELECTION<br />-auto finanziabile e leasingabile a tasso age"
  - "garanzia</strong> inclusa</li></ul><br /><ul><li><strong>Possibilità di finanziamento pe"

**Trattativa / contatto** (20 totali):
  - "pagamento e Passaggio di Proprietà immediato, senza vincolo di acquisto di un altro veicolo"
  - "permuta, esclusa IPT e MSS"
  - "finanziamento personalizzato</strong></li></ul><br /><ul><li><strong>Gestione completa della vendita anche a dist"
  - "PERMUTARE LA TUA AUTO"
  - "WHATSAPP ) <br /><br />Giuseppe: 3 8 8 4 0 3 6 2 2 7 <br /><br />Toty: 3 4 9 4 6 5 4 0 4 8<br /><br />Siamo"

**Pattern contatto** (13 totali):
  - "disponibile e fissare un appuntamento"
  - "DISPONIBILE IN PRONTA CONSEGNA<br /><br />IVA ESPOSTA<br /><br />GARANZIA UFFICIALE BMW BEST4 FIN A 07/2029 OPP"
  - "sabato, con i seguenti orari:</strong><br /><strong>da lunedi a Venerdi orari 09:30 – 12:30 | 14:30 – 18:3"
  - "Sabato: dalle ore 9:30-alle 13:00</strong><br /><strong>------------------------------------------------</"
  - "Disponibile per qualsiasi verifica e prova presso la nostra sede o tramite servizio di perizia a distanza"

---
## 4. Osservazioni qualitative sul register marchigiano

1. Mix venditore: 0% privati / 100% dealer tra listing con tipo noto.
2. Copertura descrizione verbatim: 24/184 listing (13%).
3. Distribuzione brand: Mercedes-Benz:53, Porsche:50, Audi:41, BMW:40.
4. Province piu' attive: AN:167, MC:10, PU:4.
5. Pattern garanzia frequenti: formule ibride 'garanzia ufficiale + mesi estesi' visibili. Segnale di professionalità pur in micro-operatori.
6. Solo 0 plausibili: sample insufficiente. Possibili cause: portali in 403/captcha, schema __NEXT_DATA__ cambiato, parser tornano vuoti. Verificare 'Listing per portale' sopra.

---
## 6. Gate chiusura S207

- Onestà 4 metriche: vedi tabella sezione 1
- corpus_register.md: 171 frasi totali (informativo, non gate)
- prospect_list.csv: 0 con telefono, 0 plausibili
- EXECUTION_REPORT.md: presente

**GATE STATUS: GIALLO — pipeline produce dati parziali, vedi tabella sezione 1**

_Vincolo Luke #6: mai stati PARTIAL/ARANCIONE. GIALLO onesto > VERDE su pipeline rotta._