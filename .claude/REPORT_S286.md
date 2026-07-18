# REPORT S286 — chiusura [A1] + scoping Fase 1 [S4]

Branch: s210/audit-master-plan · Commit A: 9e76158 · No push ([F] bloccato)
Mandato: NEXT_PROMPT_S286.md (VALUTA-POI-BUILD; Parte A docs-only, Parte B read-only)

---

## PARTE A — [A1] CHIUSO (commit 9e76158)

- **Punto 7 splittato** in `docs/briefs/BRIEF_A_e2e_67_testfounder.md`:
  - **7a — MECCANICA D'INVIO = VERDE**: Day-1 consegnato a TEST_FOUNDER 39<TEST_FOUNDER_NUM>,
    HTTP 200 + msg_id `out_1781986351333_evd8h` (commit 40a5d1e) = fatto terminale.
  - **7b — BREAKER VIVO = DEFERITO** a gate-pre-dealer-reale (già nei 3 gate a dealer reale).
    NON è done-condition di [A1].
  - Motivo split (referto forense S285): il punto 7 monolitico ("invio passato per Gate-E")
    era INSODDISFACIBILE su TEST_FOUNDER perché `gate_e.py:37,349` whitelista 39<TEST_FOUNDER_NUM>
    → il breaker non scatta by-design; esercitarlo richiede numero non-whitelist = dealer reale.
- **ROADMAP** (`docs/ROADMAP.md`): marcato [A1] CHIUSO + [S4] item attivo corrente.
- **Anello 6-7 NON flippato**: `state/rings.json` ha `check_cmd: null` (tier full) → nessun check
  reale eseguibile in-sessione, consegna WA non re-runnabile + 7b deferito → resta UNVERIFIED.
  Nessun hand-edit del blocco GENERATED (Rule 1b). `[A1] item chiuso ≠ ring flip`.
- Commit solo file nominati (BRIEF_A + ROADMAP), no `git add -A`, no push. Residui working-tree
  (STATE.md/rings.json/NEXT_SESSION_PROMPT.md) = solo bump-timestamp del SessionStart hook.

---

## PARTE B — Fattibilità Fase 1 [S4]: SÌ-CON-ADATTAMENTO

Verifica read-only sul codice reale (nessun codice scritto, nessun DB creato, nessuno scrape).
**Perno mancante**: lo scraper AS24 oggi fa SOLO ricerca-veicolo, non scrape di pagina-dealer.

| sez.6 done-condition | Fattibile as-is? | Evidenza |
|---|---|---|
| 1. `data/dealers.db` con dealer da scrape pagina-dealer AS24 | **NO** | `build_search_url` accetta solo make/model/params (`tools/scrapers/autoscout_scraper.py:403`); nessun `scrape_dealer`/`dealer_url`. `data/dealers.db` non esiste. |
| 2. `DealerProfile` (brand_focus, active_listings, avg_age, ≥1 gap) | **NO as-is** | dipende dall'estrazione inventario mancante |
| 3. Day-1 con dato specifico di profilo | **NO as-is** | `generate_cold_day1(dealer_brands, source, dealer_name)` (`wa-intelligence/templates.py:273`) non accetta campi profilo; firma da estendere |
| 4. Confine GDPR (solo dati commerciali) | **SÌ** | i campi pagina-dealer (inventario, prezzi, anzianità annunci, brand) sono commerciali, zero personali |
| 5. grep superlativi=0, firma Azzurra+opt-out+provenienza | **SÌ** | coperto dal Day-1 generator esistente |

**DB "dealer" esistente**: `data/db/dealer_network.duckdb` → tabella `dealer_leads`
(id, business_name, city, region, phone, email, website, address, contact_person, tier,
target_flag, business_score, notes, created_at, last_contact, status). È CRM-contatto,
**zero campi inventario** → scopo diverso da `Dealer`/`DealerProfile` di sez.4.

**Quanto adattamento**: medio-contenuto. Si riusa l'infra HTTP/parsing dello scraper;
serve un nuovo punto d'ingresso URL-pagina-dealer → lista-inventario.

---

## Lista minima da costruire in S4 (prossima sessione)

1. **[perno] Collector pagina-dealer AS24**: nuovo metodo `URL-dealer → inventario`
   (active_listings, brands, anzianità, snapshot vehicle-lite). È la capability mancante.
2. **`data/dealers.db`** con schema `Dealer` + `DealerProfile` (sez.4) — separato da
   `dealer_network.duckdb` (scopo CRM diverso).
3. **Gap Analysis**: deriva ≥1 gap dall'inventario.
4. **Estendere `generate_cold_day1`** con campo payload-profilo.
5. Cablare `personalization_payload` nel Day-1 + verificare done-condition 4/5 (GDPR + superlativi) sul render.

---

## VERDETTO FINALE
- **[A1] chiuso**: 7a verde (msg_id out_1781986351333_evd8h) + 7b deferito; anello 6-7 resta
  UNVERIFIED (nessun check in-sessione, no flip a mano).
- **Fase 1 [S4] fattibile: SÌ-CON-ADATTAMENTO** — manca lo scrape pagina-dealer (il perno);
  GDPR rispettabile coi campi che lo scraper estrarrebbe.
- **Build S4**: 5 item sopra. Nessun build eseguito in S286 (solo scoping verificato).

---

## PROBE PRE-BUILD [S4] (read-only, delegato a sub-agent — S286)

Verifica di 2 fatti terminali su AS24.it reale prima di autorizzare il build del collector
pagina-dealer. Nessun file scritto, nessun DB, nessun codice di produzione. Fetch in sola lettura.

**FASE 0 — codice**
- `build_search_url` confermato (`tools/scrapers/autoscout_scraper.py:403`): solo make/model/params,
  nessun `dealer_url`/`scrape_dealer`.
- Data path veicoli: `__NEXT_DATA__` → `props.pageProps.listings[]` via `_parse_next_data` (riga 742);
  conteggio annunci da `get_total_pages` (riga 503, legge `pageProps.numberOfResults`).
- Fetch reale: `BaseScraper._fetch` (riga 147), curl_cffi `impersonate="chrome120"` — supera l'anti-bot
  AS24.it (HTTP 200 su tutte le richieste del probe).
- ⚠️ 2 CORREZIONI NOTE prima del build:
  1. `AutoScoutScraper.fetch` (riga 486) è codice morto/rotto (`super().fetch` non esiste in BaseScraper)
     e `build_search_url` fa solo `/lst/` → il collector dealer deve usare `_fetch(dealer_url)` +
     `_parse_next_data`/`get_total_pages` as-is.
  2. Prezzo pagina-dealer in `listing.prices.public.priceRaw` / `prices.dealer.priceRaw`, NON in
     `price.priceFormatted` (chiave della ricerca, riga 828) → serve un ramo-prezzo aggiuntivo nel collector.

**[A] PARSING-PATH = SÌ (binario)**
L'inventario del dealer è nello STESSO `__NEXT_DATA__` → `props.pageProps.listings[]` + `numberOfResults`
della pagina di ricerca. `_parse_next_data`/`get_total_pages` funzionano senza modifiche strutturali.
URL pagina-dealer derivabile dai dati di ricerca (`seller.links.infoPage` → `/concessionari/{slug}`).
Campione reale (`ariel-car-bologna`, numberOfResults=50): BMW X1 10/2021 92.273 km · BMW i4 06/2023 ·
Kia Sportage 01/2023 €16.550 pubblico/€15.950 dealer. Brand-mix pag.1: BMW 6, VW 3, Ford 3, Audi 1,
Mercedes 1 + altri (multimarca, premium tedesco presente).

**[B] SEGNALE-ICP — fascia <20 PRESENTE (ma campione dominato da 50+)**

| Dealer | n_annunci |
|---|---|
| ag-auto-srl | 10 |
| autofriuli-srl | 23 |
| rossettomotors-srl | 28 |
| ariel-car-bologna | 50 |
| rivoltella-spa | 58 |
| pluricar | 69 |
| car-village-pomponesco | 143 |
| nanni-nember-brescia | 352 |

Range 10→352 → filtro-taglia necessario nel matching.

**SINTESI PROBE**: stima S286 "adattamento medio-contenuto" = **RATIFICATA**. Il perno (parsing inventario
pagina-dealer) riusa lo stesso `__NEXT_DATA__`/`pageProps.listings` già implementato; gli unici adattamenti
reali sono ramo-prezzo (`prices.public/dealer.priceRaw`) + discovery URL dealer (banale, già nei dati di
ricerca). Due correzioni note (sopra). Nessun blocco anti-bot in sola lettura.

⚠️ **DIVERGENZA HEAD**: il probe ha riportato HEAD=`19bf4de` (non `9e76158`, il commit A) → probabile
commit auto-close hook successivo, da verificare a inizio prossima sessione.
