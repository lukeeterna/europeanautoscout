# EXECUTION REPORT — S207 Marche Register (ri-target modello mandato)
_Data: 2026-06-01 10:31 | Elapsed: 982s_

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
| % listing con description (>50 char) | 11% | >=40% | GIALLO |
| Prospect con telefono (post-skip) | 135 | >=10 | VERDE |
| Plausibili (1-8 auto, no big dealer) | 30 | >=3 | VERDE |

**Listing per portale:**
- autoscout24: 209 listing  [OK]
- subito: 0 listing  [403/captcha?]
- automobile.it: 0 listing  [403/captcha?]

---
## 2. Conteggi prospect (schema S207)

- Listing grezzi totali: **209**
- Listing in range prezzo 40,000-100,000€: **209**
- Operatori unici con telefono: **135** (riga senza telefono = scartata)
- Multi-brand (>=2 brand nel stock visibile): **17**

**Breakdown flag_micro_operatore_plausibile:**
- plausibile (1-8 auto, no big dealer): **30**  ← TARGET PRIMARIO chiamate Luke
- borderline (9-15 auto): **0**
- deprioritizzato (16+ auto): **0**
- escluso (big dealer ufficiale): **105**

**Plausibili per provincia:**
  - AN (Ancona): 23
  - MC (Macerata): 1
  - PU (Pesaro-Urbino): 3
  - AP (Ascoli Piceno): 2
  - FM (Fermo): 1

---
## 3. Top frasi ricorrenti per funzione

**Descrizione auto** (172 totali):
  - "Services [6AE] (DI SERIE)<br />- BMW Widescreen [6WC] (DI SERIE)<br />- Bracciolo centrale anteriore con vano portaogget"
  - "cerchi in lega [2PA] (DI SERIE)<br />- Calandra a doppio rene in nero lucido senza cornice con listelli doppi M e badge "
  - "forgiati M doppi raggi st"
  - "trazione (DI SERIE)<br />- Copertura motore con badge M (DI SERIE)<br />- Correttore assetto fari (DI SERIE)<br />- Crui"
  - "LED (DI SERIE)<br />- Fari fendinebbia (DI SERIE)<br />- Filtro antiparticolato OPF per motori benzina (DI SERIE)<br />-"

**Garanzia** (20 totali):
  - "garanzia fino a 60 mesi e tutta l’assistenza di cui hai bisogno in ogni momento, ovunque"
  - "GARANZIA certificata, controlli tecnici attestati, offerte finanziarie personalizzate, a"
  - "GARANZIA UFFICIALE BMW FINO A FEBBRAIO 2029</strong><br /><br /><strong>ALIMENTAZIONE IB"
  - "GARANZIA BMW BEST SINO AL 05/2029<br />MOTORIZZAZIONE IBRIDO MHEV DIESEL/ELETTRICO <br /"
  - "GARANZIA UFFICIALE BMW BEST4 FIN A 07/2029 OPPURE 150"

**Trattativa / contatto** (22 totali):
  - "VISIONABILE PRESSO LO SHOW ROOM DI VIA BICE CREMAGNANI 54, VIMERCATE (MB)<br /><br />CERCHI IN LEGA 19&quot"
  - "finanziamento e leasing personalizzate, piani assicurativi adatti ad ogni specifica esigenza, per privati e azien"
  - "Finanziamento calibrate secondo le TUE esigenze"
  - "permuta, esclusa IPT e MSS"
  - "Finanziamento/Leasing)"

**Pattern contatto** (9 totali):
  - "ore 20d efficiente e performante<br />* Trazione integrale xDrive<br />* Allestimento M Sport<br />* Cambi"
  - "DISPONIBILE IN PRONTA CONSEGNA<br /><br />IVA ESPOSTA<br /><br />GARANZIA UFFICIALE BMW BEST4 FIN A 07/2029 OPP"
  - "sabato, con i seguenti orari:</strong><br /><strong>da lunedi a Venerdi orari 09:30 – 12:30 | 14:30 – 18:3"
  - "Sabato: dalle ore 9:30-alle 13:00</strong><br /><strong>------------------------------------------------</"
  - "disponibile presso la nostra sede"

---
## 4. Osservazioni qualitative sul register marchigiano

1. Mix venditore: 0% privati / 100% dealer tra listing con tipo noto.
2. Copertura descrizione verbatim: 25/209 listing (11%).
3. Distribuzione brand: Audi:57, Mercedes-Benz:55, Porsche:50, BMW:47.
4. Province piu' attive: AN:174, MC:15, PU:12.
5. Pattern garanzia frequenti: formule ibride 'garanzia ufficiale + mesi estesi' visibili. Segnale di professionalità pur in micro-operatori.
6. Register marchigiano: 30 micro-operatori plausibili (1-8 auto). Liste grezze pronte per chiamate Luke — qualifica reale (accesso clienti altospendenti) verificabile SOLO al telefono.

---
## 6. Gate chiusura S207

- Onestà 4 metriche: vedi tabella sezione 1
- corpus_register.md: 223 frasi totali (informativo, non gate)
- prospect_list.csv: 135 con telefono, 30 plausibili
- EXECUTION_REPORT.md: presente

**GATE STATUS: GIALLO — pipeline produce dati parziali, vedi tabella sezione 1**

_Vincolo Luke #6: mai stati PARTIAL/ARANCIONE. GIALLO onesto > VERDE su pipeline rotta._