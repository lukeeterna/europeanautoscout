# SESSION REPORTS COMBINED

> Generato automaticamente alla chiusura sessione (hook SessionEnd).
> 2026-06-23T21:10:10Z · 1 report.

---

## REPORT_GIUDICE_a03f49f6.md

# REPORT → GIUDICE · sessione a03f49f6 · 2026-06-23

**SESSION_ID**: a03f49f6-0b3f-4e20-a874-2d8142132dca
**HEAD**: `1058371` (auto-close hook) · sopra `b4c5ed6` = build reale S288
**git-status**: pulito a parte `.claude/NEXT_SESSION_PROMPT.md` (rumore-hook, non committato)

---

## 1. FATTO QUESTA SESSIONE (verde, chiuso)

Build S288 — metrica-tempo OSSERVATA su `tools/dealer_collector.py`. Commit `b4c5ed6`, no push.

- `vehicle_observations(dealer_id, vehicle_key, first/last_observed_at, status)`, PK composta;
  `vehicle_key = listing.id` UUID nativo (NON hash-contenuto: l'hash col prezzo cambia a ogni
  ribasso → falso "venduto").
- diff-GONE solo se run completo (no errori fetch AND len ≥ numberOfResults), **mai delete**.
- Rinomina `avg_listing_age_days → avg_vehicle_age_days` (è età-veicolo da firstRegistrationDate,
  NON anzianità-annuncio) + migrazione ALTER guardato + restore-point 1d.

**Evidenza reale (non "✓"):**
- collector ×2 live rossettomotors-srl (28 listing) → RUN1 `inserted=28` first==last;
  RUN2 `inserted=0, updated=28, gone=0` (first invariato, last avanzato).
- Test `tests/test_s288_vehicle_observations.py` su sqlite :memory: → **4/4 PASS**
  (gone-no-delete, first-stabile, guardia-run-parziale, idempotenza).
- dealers=1 / profiles=1 (idempotenza S287). 0 colonne personali (GDPR-clean).

---

## 2. INTERVENTO HARNESS (VALUTA-POI-BUILD) — fermato a PARTE A parziale per gate context 60%

Mappa wiring confermata da `settings.json` (citata):

| Evento | Hook | Effetto |
|--------|------|---------|
| SessionStart | `~/.claude/hooks/session_start_wrapper.sh` | matcher startup\|resume\|compact |
| SessionEnd | `~/.claude/hooks/session_reports_combine.sh` | produce SESSION_REPORTS_COMBINED |
| (auto-close) | `~/.claude/hooks/global_session_end.sh` | scrive NEXT_SESSION_PROMPT.md + commit "auto-close session" |

- Punto di wiring di `global_session_end.sh` **NON confermato**: non è il SessionEnd globale;
  candidato = hook `Stop` in project `.claude/settings.json` (chiavi: SessionStart, PreToolUse, Stop).
- Sintomo (1) corroborato: ~25 file `REPORT_S*.md` in `.claude/` → coerente con "combine.sh dumpa
  tutti i .md in cartella", MA logica di selezione **non ancora letta**.

---

## 3. VERDETTO SOSPESO (deliberato, non cedimento)

Non emetto CONFERMO/CORREGGO sulle 2 proposte: **3 corpi-script non letti**, quindi i 2 fatti
load-bearing restano non verificati:
- (a) come `session_reports_combine.sh` seleziona i report (tutti / ultimi N / pattern);
- (b) se `session_start_wrapper.sh` **legge** NEXT_SESSION_PROMPT come istruzione o lo scrive soltanto.

Dare verdetto da codice non letto = output verosimile, viola vincolo #1/#10. PARTE A è il gate
del build → rispettato, build NON avviato.

**4. Nessun auto-commit di chiusura**: PARTE A read-only, zero file miei modificati. Committare il
dirty = catturare solo rumore-hook (proprio l'anti-pattern #2 sotto esame).

---

## DOMANDE AL GIUDICE

1. SOSPENDERE il verdetto invece di stimarlo da struttura — corretto, o ti aspettavi un verdetto
   preliminare con flag "da-confermare"?
2. Le 2 proposte (handoff 1-file fisso con header SESSION_ID/HEAD/git-status; declassare
   auto-mandato a NOTA `CC_SESSION_NOTES.md` + SessionStart che non lo legge) — direzione giusta
   a fronte di questa mappa parziale?

## NEXT PROMPT PROPOSTO (founder → riga-1)

> MANDATO: completa PARTE A poi VALUTA-POI-BUILD harness handoff. Apri da root.
> 3 letture mirate prima del verdetto: (a) `session_reports_combine.sh` — selezione report;
> (b) `session_start_wrapper.sh` — se legge NEXT_SESSION_PROMPT come istruzione;
> (c) `global_session_end.sh` + hook `Stop` in `.claude/settings.json` — wiring auto-close.
> Poi verdetto Proposta 1 + Proposta 2, poi build se confermate. Backup *.bak vincolo 1d. ~5 min.

