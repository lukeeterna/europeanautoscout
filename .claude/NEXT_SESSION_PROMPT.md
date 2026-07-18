# NEXT SESSION — europeanautoscout (stato VERO da git/disco, 2026-07-18 10:00)

## Stato per-fase (F4 backfill telefono)
- **F4 seed VERIFICA = COMPLETATA.** Campione seed-deterministico (pop. ordinata per P.IVA, seed PZ=202/TV=203).
  - PZ idx [0,3,4,14,16,24,26,38] — score fonte-B **7/8 PASS** (NON-VERIFICABILE: idx0 GruppoValluzzi).
  - TV idx [5,12,13,19,23,29,33,35] — score fonte-B **7/8 PASS** (NON-VERIFICABILE: idx13 A27).
  - Dettaglio per-riga + URL fonte-B in `docs/judge/20260718-1000-backfill-f4.md`.
- **V5 igiene** doc giudice v1 = fatto (numero test → <TEST_FOUNDER_NUM>).
- **V6 SINTESI v4.1** nota-verifica aggiornata (git-visibile) = fatto.

## UNICO RESIDUO (1 step, untracked/gitignored, NON git)
Annotare il blocco `verifica_telefono` per-riga (esiti V3: idx→SÌ/NON-VERIFICABILE + URL fonte-B) nei 4 file dati:
`data/recon/mandatari/{potenza.json,treviso.json,telefono_map_pz.json,telefono_map_tv.json}`.
Fonte dei valori = sezione V3 del doc giudice F4. Fare .bak (nella dir gitignored) prima della scrittura (vincolo 1d). Poi F4 chiuso al 100%.

## Armatura (ricorda)
- OGNI git con `-C ~/Documents/europeanautoscout`, MAI `cd` nudo (cwd si resetta sull'archivio combaretrovamiauto-enterprise = INTOCCABILE).
- PII mai in git: porcelain-check (JSON/map/.bak assenti) prima di ogni commit.
- Solo GET pubblici, zero bypass 403/Cloudflare, zero contatto imprese.

## HEAD
Pre-sessione 1b9042e → + commit di chiusura F4 (vedi git log).
