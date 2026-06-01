# S215 — Sbloccare Day 1 Stile Car: i 3 blocker rimasti

> Branch: `s210/audit-master-plan`. S214 COMMITTATA in `847f76e` (gating reveal VERDE 5/5).
> Day 1 Stile Car (2026-06-03) BLOCCATO da 3 blocker su 4. Il 4° (reveal fonte) è chiuso.

## FATTO in S214 (commit 847f76e)
- `C-GATE-FONTE-001(reveal)` CHIUSO. Il PDF post-pagamento mostra venditore/città/telefono/portale/URL.
- `generate_vehicle_sheet(..., source_dossier=None)`: sezione "FONTE VEICOLO" renderizzata SOLO se source_dossier passato → il path dealer preview non può trapelare la fonte.
- `release_source_dossier` passa `source_dossier=source_locked` (gated su payment_confirmed).
- Verifica reale riproducibile: `~/.argos-sanitizer-venv/bin/python /tmp/s214_verify.py` → VERDE 5/5 (5° PASS = fonte estratta via `fitz`, non `strings`).
- Memoria salvata: Luke preferisce che committi io a fine task verde (no push, reversibile).

## BLOCKER RIMASTI per Day 1 (priorità)

### 1. C-SAN-001 — sanitizer immagini (IL PIÙ CRITICO)
Le foto nel PDF **preview** (quello che il dealer riceve PRIMA di pagare) possono rivelare targa/indirizzo/nome venditore. Finché aperto, il gating-fonte di S214 è aggirabile via foto.
- Storia: refactor Pillow S179 NON chiude D-32 (3 fail mode: watermark sovra-targa, footer brand, tagline). PoC plate-EU CHIUSO ESITO C (S186): Vision OCR non discrimina targa. Pivot tentato = upstream_slide_filter + promo_card_detector.
- Gate: UAT visual Luke su 5 sample dealer-grade reali (MAI smoke auto). Venv `~/.argos-sanitizer-venv/bin/python` + seller_name reale.
- File: `src/cove/image_sanitizer.py`, invocazione in `detail_enricher_v2.py`.

### 2. C-E2E-ZERO — nessun deal live ha la fonte agganciata
Il reveal S214 è testato in isolamento. Nel flusso d'invio reale nessun codice chiama `create_deal(source_locked=...)`. `wa_bridge.py:296` `_open_fsm` assume "Deal già creato altrove" che non esiste.
- Azione: cablare `create_deal` nel punto dove il dossier preview viene inviato al dealer, popolando `source_locked` dai dati scraper (listing_url/seller_name/seller_city/seller_phone/portal).

### 3. C-COMM-INTEL-001 — intelligence comunicazione dealer (aperto)
Vedi PLAN.md / ARGOS_MASTER per scope. Meno bloccante dei due sopra per il rischio-leak.

## ORDINE CONSIGLIATO S215
1° C-SAN-001 (rischio sicurezza diretto sul preview) → 2° C-E2E-ZERO (cablaggio) → 3° C-COMM-INTEL-001.
NON mandare Day 1 finché C-SAN-001 + C-E2E-ZERO non sono VERDI su TEST_FOUNDER 393314928901 E Luke dichiara "pienamente soddisfatto" (gate qualitativo, recidiva nota).

## NOTE / BACKLOG
- BACKLOG `C-PAY-STALE-DB`: `payment_handler.py:38` path DuckDB stale + tabella `dealer_leads` inesistente (fuori scope gating).
- `_city_to_country` in `pdf_gated_source.py` ora quasi inutile (source vera renderizzata da sezione dedicata) → semplificabile, fuori scope.
- Working tree resta molto sporco (centinaia untracked + .bak). S214 ha committato SOLO i 4 file in-scope.
- Garanzia gating = 2 strati: gating-fonte (S214 ✓) + sanitizer (C-SAN-001 ✗). Serve entrambi.
