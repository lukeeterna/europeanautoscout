# REPORT S263 — Probe profondità pool IT (AutoScout24.it)

**Data**: 2026-06-10 · Branch `s210/audit-master-plan` · Sola lettura, zero modifiche source-of-truth.
**Obiettivo**: misurare se le famiglie-trim ESATTE si riempiono (N≥8) o il mercato IT non le contiene.
**Probe**: `tools/_s263_probe.py` (throwaway) · output grezzo `/tmp/s263.txt`.

---

## TABELLA FINALE (BMW Serie 3, anno 2021±2, km≤80k)

| FAMIGLIA            | grezzi | dedup | L0 | L1 | L2 | L3 | N≥8 |
|---------------------|:------:|:-----:|:--:|:--:|:--:|:--:|:---:|
| 320d xDrive 2021    |   19   |  19   |  0 |  0 |  0 |  2 | MAI |
| 318d 2021           |   19   |  19   |  0 |  0 |  1 |  2 | MAI |
| 330i 2021           |   19   |  19   |  0 |  0 |  0 |  1 | MAI |
| M340 2021           |   19   |  19   |  0 |  0 |  0 |  0 | MAI |

Livelli: L0=engine+drivetrain+trim+fuel+km-band+anno±1 · L1=−km · L2=anno±2 · L3=−trim.
Dedup per `listing_id` (VIN reali nel raw = **0** — AS24.it non espone VIN nel listing SSR).

---

## IL FATTO TERMINALE: il muro NON è il mercato, è lo SCRAPER

Lo scraper ha restituito **19 listing in 1 pagina**, nonostante `max_pages=20`.
Causa verificata nel codice (non assunta):
- `base_scraper.scrape_model` a pagina 1 chiama `get_total_pages(html)` → su AS24.it
  (JS-rendered) **curl_cffi vede solo la prima pagina SSR** (~19 risultati) e si ferma.
- Il path Selenium-profondo (`autoscout_scraper.py:1248`, fino a 5 pagine) **esiste ma è
  gated su zero-data**: scatta solo se ≥80% dei listing hanno prezzo/km = 0. I nostri 19
  hanno i dati → il fallback profondo **non scatta mai**.

**Conseguenza**: 19 listing totali per la Serie 3 (uno dei modelli BMW più diffusi) NON è
una misura del mercato IT — è il tetto del fetcher attuale. **Non possiamo dichiarare Esito B
(mercato thin) onestamente, perché non abbiamo "pescato tutto": abbiamo pescato 1 pagina.**

---

## ESITO: C — INCONCLUSIVO sul mercato, CONCLUSIVO sullo scraper

- **NON è Esito A**: le config esatte sono 0 a L0/L1 in tutte e 4 le famiglie. Niente pool denso.
- **NON è Esito B pulito**: il pool=19 è troncato dallo scraper, non dal mercato. Non provato che IT non le contenga.
- **È Esito C**: il vincolo binding è la **profondità di fetch su AS24.it**. Finché lo scraper
  vede 1 pagina, A vs B è **indecidibile**.

### Segnale collaterale che SOPRAVVIVE al muro (e conta)
Anche dentro 19 listing, il **collasso da trim/drivetrain è già visibile**: le config esatte
(L0/L1) sono **zero**, e solo a L3 (trim droppato) si pescano 1–2 comparabili. Questo
anticipa che — anche con un pool 10× più profondo — il filtro esatto diluisce pesantemente:
la dimensione `trim_line` (M Sport vs base) e `drivetrain` (xDrive vs sDrive) frammentano il
pool prima ancora del volume. **Preview di Esito misto** (320d/318d liquide reggono a livelli
rilassati, M340 resta thin a qualunque profondità: a L3 = 0).

---

## min_n — NON RATIFICATO (onestamente)

Default attuale **8** resta **PARCHEGGIATO**. La distribuzione osservata è corrotta dal muro
scraper (tutto near-zero perché pool=19): ratificare min_n su questi numeri sarebbe ratificare
rumore. **Ratifica rimandata** a quando esiste un campione deep-fetch reale. Non è un debito
nuovo: è lo stesso debito S259, che richiede dati che ancora non abbiamo.

---

## RACCOMANDAZIONE (la nomino, non la eseguo)

La prossima decisione NON è "costruire stealth" né "ridisegnare a bande". È una domanda più
piccola e prioritaria: **far paginare lo scraper oltre pagina 1 su AS24.it.**
Il path Selenium-profondo **esiste già** (`autoscout_scraper.py:1250`); va solo **de-gated** per
il caso IT (oggi scatta solo su zero-data). È un cambio di poche righe a un componente esistente,
**non infra nuova** (niente proxy/stealth/retry-framework).

**S264 proposto**: de-gate fetch profondo IT (5 pagine Selenium) → **ri-eseguire QUESTO probe
identico**. Solo allora A vs B/misto è decidibile e min_n ratificabile. Throwaway già pronto:
`python3 -m tools._s263_probe`.

---

## DEBITO RESIDUO
- min_n non ratificato (dipende da deep-fetch).
- VIN assente nel listing SSR AS24.it → dedup futuro resta su `listing_id`/url (dichiarato).
- `tools/_s263_probe.py` è throwaway: tienilo per il rerun S264, poi elimina.
- Limite hard noto: anche col Selenium fallback il cap è 5 pagine (`min(max_pages,5)`); se
  servisse oltre, è una decisione di scope separata (NON in questo filone finché Esito non deciso).
