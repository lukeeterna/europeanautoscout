# Sintesi pilota mandatari — 3 province (Potenza · Treviso · Roma) — v3

_Generato 2026-07-14 · fonte: `data/recon/mandatari/{potenza,treviso,roma}.json` · Roma = POST riconciliazione provenienza + fix RS Autotorino (commit af4bab0)._

> **v3 — metrica corretta per comparabilità + ICP.** Rispetto alla v1: (a) nomenclatura funnel non-euristica (LEAD → QUALIFICABILE → CONTATTABILE → VERIFICATO); (b) ICP ristretto a `{solo-anagrafe}`, `probabile-agente-di-concessionaria` esclusa off-ICP; (c) `%non-operative` calcolata SOLO sulle righe con STATO osservato (denominatore dichiarato); (d) telefono non harvestato = `n/d`, mai `0`; (e) nota metodologica ATECO.

## Nomenclatura (vincolante)

- **LEAD** = riga con P.IVA valida.
- **QUALIFICABILE** = LEAD con classe candidata ICP ∈ `{solo-anagrafe}`.
- **CONTATTABILE** = QUALIFICABILE con telefono presente.
- **VERIFICATO** = intermediazione auto confermata da fonte indipendente. **Oggi 0 per costruzione** (nessuna verifica indipendente ancora eseguita) su tutte e 3 le province.

`probabile-agente-di-concessionaria` è **esclusa dall'ICP** (filiale/agente di gruppo ufficiale ≠ micro-dealer indipendente — es. le 4 filiali Autotorino). Resta visibile nella distribuzione classi con nota off-ICP, ma NON entra in QUALIFICABILI/CONTATTABILI.

## Tabella comparativa (colonne fisse)

| Metrica | Potenza (PZ) | Treviso (TV) | Roma (RM) |
|---|---|---|---|
| righe | 42 | 40 | 28 |
| P.IVA valide | 22 | 34 | 22 |
| P.IVA **DISTINTE** | 22 | 34 | **19** (−3 = quaterna Autotorino stessa P.IVA) |
| copertura-campo-telefono | **n/d — non harvestato** | **n/d — non harvestato** | 39,3% (11/28) |
| copertura-STATO | 1/42 | 27/40 | 12/28 |
| %non-operative (su osservate) | **n/c — copertura 1/42 insufficiente** | **11,1% (3/27)** | **8,3% (1/12)** |
| LEAD-QUALIFICABILI `{solo-anagrafe}` | 19 | 22 | 11 |
| **CONTATTABILI-SUBITO** (qualif ∧ tel) | **n/c** (telefono n/d) | **n/c** (telefono n/d) | **4** |
| VERIFICATI | 0 | 0 | 0 |
| COPERTURA vs universo (con fonte) | N/D | N/D | **<14%** — 28/«>200» PagineGialle (lower-bound) |

**Comparabilità PZ/TV vs RM sospesa sul telefono**: in PZ e TV il campo telefono NON è stato harvestato in questa passata (`n/d`, non `0`). I QUALIFICABILI esistono (19 PZ, 22 TV), ma senza telefono CONTATTABILI-SUBITO è `n/c` per costruzione — non "0 target". Diventa confrontabile con RM solo dopo il backfill telefono.

## Funnel (non-euristico)

Funnel operativo: **LEAD → QUALIFICABILE `{solo-anagrafe}` → backfill telefono → CONTATTABILE → verifica indipendente → VERIFICATO**. Nessuna classe euristica è di per sé un target: il target si costruisce lungo il funnel, non si assume dalla classe.

- **Potenza**: LEAD 22 → QUALIFICABILI 19 → CONTATTABILI n/c (telefono n/d) → VERIFICATI 0.
- **Treviso**: LEAD 34 → QUALIFICABILI 22 → CONTATTABILI n/c (telefono n/d) → VERIFICATI 0.
- **Roma**: LEAD 22 → QUALIFICABILI 11 → CONTATTABILI 4 → VERIFICATI 0.

Roma — i 4 CONTATTABILI-SUBITO (tutti `solo-anagrafe`, sopravvivono al restringimento ICP): **Gold Car**, **Ve.Ta. Auto 2**, **Autocentri Anzano S.r.l.**, **Cmc Auto di Federico Aprosio**.

## Distribuzione classi (tutte, incl. off-ICP)

- **Potenza**: solo-anagrafe 19 · non-classificabile (no P.IVA) 20 · fuori-target 3
- **Treviso**: solo-anagrafe 22 · probabile-agente-di-concessionaria 6 _(off-ICP)_ · fuori-target 6 · non-classificabile 6
- **Roma**: solo-anagrafe 11 · probabile-agente-di-concessionaria 5 _(off-ICP)_ · fuori-target 5 · non-classificabile 6 · non-operativa 1

Roma P.IVA distinte 19 < 22 valide: dedup di **4 filiali Autotorino** (P.IVA 01559111008, ex Mercedes-Benz Roma S.p.A.) = 1 entità giuridica, classe off-ICP.

## Copertura-STATO per provincia (emendamento E1 — la premessa "solo-RM" è FALSA su disco)

Il campo `STATO` NON è RM-only: su disco è più ricco in Treviso.

- **Treviso**: 27/40 osservate (24 `attiva` + 3 non-operative: 2 `in liquidazione` + 1 `fallita`).
- **Roma**: 12/28 osservate (11 `attiva` + 1 `in liquidazione`).
- **Potenza**: 1/42 osservate (1 `in liquidazione`) → copertura insufficiente, `%non-operative` non calcolabile (`n/c`).

`%non-operative` è calcolata SOLO sul denominatore osservato dichiarato accanto (E2). Nessuna % su righe non osservate; nessun `n/d` reso come `0`.

## Copertura vs universo provinciale (con fonte)

- **Roma**: harvest 28 righe vs universo PagineGialle «più di 200 risultati» (contatore troncato — riferimenti: Milano città 198, Torino 190, Napoli 142; fonte `paginegialle.it/lazio/roma/concessionarie_auto`, censimento 2026-07-10). Copertura **< 14% ed è un LOWER BOUND** (denominatore troncato: il vero universo è ≥200).
- **Potenza** e **Treviso**: **nessuna densità PagineGialle a verbale**. Universo provinciale non stabilito → copertura **N/D**.

## Nota metodologica (ATECO — obbligatoria)

L'anagrafe mandatari è costruita sui codici **ATECO 2007 45.11.02 / 45.19.02**, **SOPPRESSI dal 1/4/2025** (rimappati in ATECO 2025: **46.18.41 + 47.92.21 + 47.92.31**). I denominatori provinciali ufficiali sono **in acquisizione via estrazione camerale**. Finché non disponibili, la riga COPERTURA resta un **lower-bound su fonte PagineGialle** e **le proiezioni sono sospese**.

## Proiezione rollout ~100 province — **NON EMESSA**

Regola mandato: la proiezione entra solo dalla riga COPERTURA-con-fonte (mai da CONTATTABILI). La copertura-con-fonte esiste per **1 provincia su 3** (solo RM) e per RM è un lower-bound troncato. Un solo denominatore, non chiuso, non qualifica un'estrapolazione a ~100 province → **proiezione deliberatamente omessa e sospesa** (vedi nota metodologica ATECO). Prerequisito per abilitarla: universo camerale (o PagineGialle) per almeno PZ e TV.

## Caveat per-provincia

- **Potenza**: telefono non harvestato (`n/d`); 20/42 righe senza P.IVA (`non-classificabile no-P.IVA`); `STATO` popolato su **1 sola riga** (di fatto assente) → `%non-operative` = n/c; P.IVA solo da schede per-nome reportaziende.it (directory-categoria non espongono P.IVA).
- **Treviso**: telefono non harvestato (`n/d`); enrichment P.IVA per-nome PENDING; alcune voci (Autosoccorso Veneto, Basso Ford, Trevisauto Spa, Autobavaria BMW) potenzialmente concessionari ufficiali/carrozzerie, non mandatari puri (ATECO 45.11.02 non verificato); `STATO` popolato 27/40 (provincia più ricca sul campo).
- **Roma**: telefono 39,3% (unica provincia arricchita); provenienza riconciliata (11 scheda-diretta / 8 serp-snippet / 3 websearch, caveat 12/10 corretto in af4bab0); RS 4 filiali Autotorino aggiornata; PagineGialle mescola zone adiacenti (righe fuori-RM segnalate in `avvertenza`).
