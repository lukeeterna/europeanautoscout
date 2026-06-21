# PROBE S286 — RUN 2 (indipendente) · pre-build Fase 1 [S4]

MANDATO probe: READ-ONLY (fetch + ispezione). Dealer DIVERSI dalla run-1 per corroborazione.
Scopo: verificare su pagina-dealer VERA l'assunzione load-bearing che l'inventario di un dealer
esca dallo STESSO data path JSON dei risultati-ricerca. Rif: docs/ARCHITETTURA_E2E.md sez.4/6.

## FASE 0 — git + procedura
- Branch `s210/audit-master-plan`, commit `b50da58`. Working-tree: 1 file dirty
  `.claude/NEXT_SESSION_PROMPT.md` = rumore-hook auto-close, non codice.
- `build_search_url` (riga 403): solo make/model/params di ricerca; nessun `dealer_url`/`scrape_dealer`. ✓
- Data path veicoli: `parse_listings` (riga 540), strategia 2 `__NEXT_DATA__` (riga 742) →
  `props.pageProps.listings` (righe 764-770). Prezzo parsato da `item.price` come `priceFormatted`/
  `tracking.price` (righe 821-837).
- Fetch reale: `BaseScraper._fetch` (riga 147), `curl_cffi.get(..., impersonate="chrome120")` (riga 172).
- **Verdetto procedura: COERENTE.** Infra fetch riusabile read-only su URL arbitrario (curl_cffi
  chrome120 su pagina-dealer → HTTP 200, 295KB). URL pagina-dealer ricavabile dalla ricerca:
  `seller` → `/concessionari/{slug}`.

## [A] PARSING-PATH = SÌ (con 1 caveat sul mapping chiavi)
La pagina-dealer reale (Ceccato Motors, premium DE-mix) serve l'inventario nello **STESSO**
`__NEXT_DATA__` → `props.pageProps.listings` già parsato (20 item/pagina, `numberOfResults: 627`).
Campione: BMW 225 03/2026 0km €38.900 · Porsche Macan 05/2019 50.648km €49.800 · BMW X3 03/2022
85.016km €39.800. Brand-mix: BMW/MINI/Porsche/Audi/Jaguar/Alfa (premium-misto).

⚠️ **CAVEAT load-bearing (punto di rottura del parser attuale)**: sulla pagina-dealer
- prezzo NON in `item.price` (null) ma in **`item.prices.public.price`** ("€ 38.900") / `prices.public.priceRaw` (38900);
- anno in **`vehicle.firstRegistrationDate.{raw,formatted}`**;
- km in **`vehicle.mileageInKm.formatted`**;
- nome dealer NON nel listing-item → sta in **`pageProps.dealerInfoPage`**.
Il parser attuale (`item.price`/`tracking`) su pagina-dealer estrarrebbe **prezzo 0**.
→ Serve un **adattatore di mapping chiavi**, NON un nuovo data path né un rewrite.

## [B] SEGNALE-ICP (header "N Risultati" dichiarato)
| Dealer | n_annunci |
|---|---|
| Samacar | 25 |
| G.M.A. | 45 |
| Ariel Car Bologna | 50 |
| Gold Lion's Car | 70 |
| Venezia Auto | 98 |
| Avenuecar | 110 |
| Ceccato | 627 |

Fascia micro-dealer **<20: ASSENTE** in questo campione (min 25); dominano lotti 45-110+.
NB metodologico: il campione viene dalla ricerca-PREMIUM → skewato verso dealer medio-grandi.
L'ICP micro-dealer <20 (founder 30-80 auto) **non emerge dalla ricerca-premium, va campionato diversamente**.

## SINTESI RUN 2
Stima S286 "adattamento medio-contenuto" = **RATIFICATA (run indipendente)**: stesso data path
`__NEXT_DATA__`/`pageProps.listings` + stessa infra fetch riusabili; l'adattamento reale è un layer
di re-mapping chiavi (`prices.public.*`, `firstRegistrationDate`, `mileageInKm`, `dealerInfoPage`)
+ paginazione dealer — non un rewrite.

## CONFRONTO CON RUN 1 (REPORT_S286.md)
- **Convergenza**: entrambe SÌ su parsing-path; entrambe RATIFICANO medio-contenuto; entrambe
  isolano il prezzo come punto di rottura (`prices.public/dealer.priceRaw`).
- **Run 2 aggiunge**: altri 3 campi da re-mappare (firstRegistrationDate, mileageInKm, dealerInfoPage)
  → l'adattatore è leggermente più ampio del solo ramo-prezzo, ma resta mapping, non rewrite.
- **Divergenza [B]**: run-1 trovava ag-auto=10 (<20 presente); run-2 min=25 (<20 assente). Causa =
  campionamento (run-2 tutto da ricerca-premium). Conferma: per intercettare l'ICP micro-dealer
  serve una sorgente di discovery diversa dalla sola ricerca-premium.
