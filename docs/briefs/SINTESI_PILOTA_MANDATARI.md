# Sintesi pilota mandatari — 3 province (Potenza · Treviso · Roma) — v4

_Generato 2026-07-18 · fonte: `data/recon/mandatari/{potenza,treviso,roma}.json` · v4 = POST backfill-telefono PZ+TV (fonti pubbliche per-riga) · Roma invariata da v3 (commit af4bab0)._

> **v4 — backfill telefono PZ+TV.** Rispetto alla v3: (a) copertura-campo-telefono e CONTATTABILI-SUBITO ora valorizzate per PZ (18/19) e TV (22/22), non più `n/c`; (b) telefono per-riga da fonti pubbliche con `telefono_fonte`/`telefono_presente`; (c) verifica-campione fonte-B indipendente (PZ 6/8, TV 8/8); (d) le denominazioni nominative di ditte individuali sono sostituite con `idx N · P.IVA <numero>` (igiene doc repo pubblico). Invarianti da v3: nomenclatura funnel, ICP `{solo-anagrafe}`, `n/d` mai `0`, nota ATECO.

> **Clausola RPO (vincolante):** i numeri raccolti NON sono chiamabili finché il check al **Registro Pubblico delle Opposizioni** non sarà eseguito (parcheggio RPO invariato). "CONTATTABILE-SUBITO" = `qualif ∧ telefono presente`, **non** "chiamabile ora".

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
| copertura-campo-telefono | **94,7% (18/19 qualif)** | **100% (22/22 qualif)** | 39,3% (11/28) |
| copertura-STATO | 1/42 | 27/40 | 12/28 |
| %non-operative (su osservate) | **n/c — copertura 1/42 insufficiente** | **11,1% (3/27)** | **8,3% (1/12)** |
| LEAD-QUALIFICABILI `{solo-anagrafe}` | 19 | 22 | 11 |
| **CONTATTABILI-SUBITO** (qualif ∧ tel) | **18** | **22** | **4** |
| VERIFICATI | 0 | 0 | 0 |
| COPERTURA vs universo (con fonte) | N/D | N/D | **<14%** — 28/«>200» PagineGialle (lower-bound) |

**Comparabilità PZ/TV vs RM ora attiva**: il backfill-telefono (2026-07-18) ha valorizzato PZ e TV. CONTATTABILI-SUBITO = 18 (PZ) e 22 (TV), superiori a RM (4) — RM resta indietro sul campo telefono (39,3%) perché arricchita in una passata precedente meno esaustiva, non per scarsità. L'unica riga `n/d` PZ è un'impresa IT (ATECO 62.09), non automotive.

## Funnel (non-euristico)

Funnel operativo: **LEAD → QUALIFICABILE `{solo-anagrafe}` → backfill telefono → CONTATTABILE → verifica indipendente → VERIFICATO**. Nessuna classe euristica è di per sé un target: il target si costruisce lungo il funnel, non si assume dalla classe.

- **Potenza**: LEAD 22 → QUALIFICABILI 19 → CONTATTABILI 18 → VERIFICATI 0.
- **Treviso**: LEAD 34 → QUALIFICABILI 22 → CONTATTABILI 22 → VERIFICATI 0.
- **Roma**: LEAD 22 → QUALIFICABILI 11 → CONTATTABILI 4 → VERIFICATI 0.

Roma — i 4 CONTATTABILI-SUBITO (tutti `solo-anagrafe`, sopravvivono al restringimento ICP): **Gold Car**, **Ve.Ta. Auto 2**, **Autocentri Anzano S.r.l.**, **idx 22 · P.IVA 09248401003** (ditta individuale).

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

- **Potenza**: telefono harvestato 18/19 (1 `n/d` = impresa IT ATECO 62.09 non automotive); 20/42 righe senza P.IVA (`non-classificabile no-P.IVA`); `STATO` popolato su **1 sola riga** (di fatto assente) → `%non-operative` = n/c; P.IVA solo da schede per-nome reportaziende.it (directory-categoria non espongono P.IVA).
- **Treviso**: telefono harvestato 22/22; enrichment P.IVA per-nome PENDING; alcune voci (Autosoccorso Veneto, Basso Ford, Trevisauto Spa, Autobavaria BMW) potenzialmente concessionari ufficiali/carrozzerie, non mandatari puri (ATECO 45.11.02 non verificato); `STATO` popolato 27/40 (provincia più ricca sul campo).
- **Roma**: telefono 39,3% (arricchita in passata precedente meno esaustiva); provenienza riconciliata (11 scheda-diretta / 8 serp-snippet / 3 websearch, caveat 12/10 corretto in af4bab0); RS 4 filiali Autotorino aggiornata; PagineGialle mescola zone adiacenti (righe fuori-RM segnalate in `avvertenza`).

## Nota metodo backfill-telefono (v4 — obbligatoria)

- **Data**: 2026-07-18. **Fonti pubbliche GET** (no contatto imprese, no bypass 403/Cloudflare): reportaziende, ufficiocamerale (403 sistematico → skip), paginegialle, paginebianche, misterimprese, siti aziendali linkati, WebSearch mirata. Ogni riga porta `telefono`, `telefono_fonte` (URL), `telefono_presente`.
- **Tetto fetch dichiarato**: 45/provincia — usati **PZ 43/45**, **TV 41/45**.
- **Null-discipline**: telefono non trovato = `n/d` + motivo per-riga, mai `0`.
- **Verifica-campione** (`verifica_telefono` nei JSON): fonte-B indipendente (URL ≠ `telefono_fonte`), match esatto o prefisso+ultime4. Score agenti **PZ 6/8**, **TV 8/8** (soglia ≥6/8 rispettata). Campione seed-deterministico (seed PZ=202, TV=203) calcolato in main-context; overlap già-confermato PZ 3/8, TV 2/8; **re-verifica indipendente delle restanti righe seed = RESIDUO PARCHEGGIATO** (tetto-fetch saturo + budget-context), non fabbricata.
- **Clausola RPO**: numeri NON chiamabili finché il check Registro Pubblico delle Opposizioni non è eseguito.
