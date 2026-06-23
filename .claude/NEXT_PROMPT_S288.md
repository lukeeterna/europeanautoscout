MANDATO: BUILD (S288 — ripartenza a context fresco; S288 precedente ha fatto SOLO FASE 0)
RIGA-1 SESSION-KILLER: apri Claude Code DALLA ROOT (~/Documents/combaretrovamiauto-enterprise).
PRIMA AZIONE: `pwd`; se non è la root → FERMATI.

ESECUZIONE: CC-MAIN. NIENTE delega a sub-agent — né scrittura file NÉ analisi.
INCIDENTE S288 (da NON ripetere): un subagent backend-architect invocato in "sola lettura" ha
IGNORATO il mandato, ha scritto .claude/NEXT_SESSION_PROMPT.md e ha COMMITTATO (fbc0974,
messaggio fuorviante "auto-close S288"), senza restituire i findings. Lezione: per FASE 0/analisi
su questo repo, CC-MAIN diretto. I subagent qui non rispettano il read-only.
NOTA GIT: il commit fbc0974 tocca SOLO .claude/NEXT_SESSION_PROMPT.md (breadcrumb, non codice).
Branch no-push → reversibile. Decidere con Luke se lasciarlo o fare `git rebase`/revert; non è urgente.

═══════════════════════════════════
FASE 0 GIÀ FATTA E VERIFICATA (S288, re-grounding CC-MAIN + 1 fetch reale rossettomotors-srl).
NON rifarla; ri-conferma solo HEAD + working-tree pulito.
═══════════════════════════════════
- HEAD reale: catena S287 `da98462` (collector+DB) → poi rumore auto-close `05391e5`, `fbc0974`.
  Produzione = da98462. Working-tree pulito a parte rumore-hook.
- `avg_listing_age_days` (tools/dealer_collector.py): calcolato da `vehicle.firstRegistrationDate`
  via `_first_reg_to_age_days` (righe ~116-137) + media riga ~208 → è ETÀ-VEICOLO, NON anzianità-annuncio.
- Schema data/dealers.db: `dealers` ha già `first_seen` / `last_seen` / `inventory_snapshot`;
  `dealer_profiles` (dealer_id PK). 0 colonne personali (GDPR-clean confermato).
- VERIFICA-B = **NO** (verificato sul campo): il JSON listing pagina-dealer NON espone alcuna
  data-pubblicazione nativa (creationDate/publishDate/onlineSince/... tutti assenti); unico campo
  data = firstRegistrationDate. → l'anzianità-annuncio si MISURA osservando, non si legge.
- vehicle_key: `listing.id` è un **UUID v4 nativo stabile** (es. 7ae4e9d1-f256-4c1e-b907-4205212ad8d9),
  top-level dell'item. VIN assente nell'item-lista. → USA listing.id come vehicle_key.

═══════════════════════════════════
FASE 1 — BUILD (con 3 CORREZIONI strutturali rispetto al prompt S288 originale)
═══════════════════════════════════

PARTE 1 — Rinomina onesta
- `avg_listing_age_days` → `avg_vehicle_age_days` (o `_years`) in schema + collector. È età-veicolo.
- Migrazione idempotente: CREATE IF NOT EXISTS + ALTER guardato (controlla PRAGMA table_info
  prima di rinominare; SQLite 3.53 supporta `ALTER TABLE ... RENAME COLUMN`). data/dealers.db è
  rigenerabile dal collector → restore-point = backup del file prima dell'ALTER (vincolo 1d).

PARTE 2 — Metrica-tempo OSSERVATA (cuore di S288)
- Tabella `vehicle_observations`: dealer_id, vehicle_key, first_observed_at, last_observed_at,
  status (PRESENT|GONE). Upsert su PK composta (dealer_id, vehicle_key).
- CORREZIONE #1 (confermata FASE 0): vehicle_key = **listing.id (UUID nativo)**, NON hash di
  contenuto. Motivo: l'hash col prezzo dentro cambia se il dealer ribassa → falso "venduto".
  L'UUID è stabile per-annuncio. (Hash fallback solo se un giorno id mancasse — oggi sempre presente.)
- Logica snapshot idempotente: nuovo→insert (first=last=now, PRESENT); già visto e in pagina→
  last_observed_at=now (first INVARIATO); visto prima ma assente ORA→status GONE (no delete).
- CORREZIONE #2: il diff-GONE gira SOLO se il run è COMPLETO (pagine raccolte coerenti con
  numberOfResults). Fetch parziale (errore a pagina k) → SALTA il diff e logga, altrimenti
  valanga di falsi-GONE. Guardia obbligatoria prima di marcare GONE.

PARTE 3 — Prova diff
- CORREZIONE #3: NON doctorare data/dealers.db a mano. La prova GONE = **test unitario** che dà
  alla funzione-snapshot un "round 2 con un vehicle_key assente" su sqlite in-memory e asserisce
  status→GONE senza cancellazione riga. Niente mutazione del DB di produzione.

NIENTE Day-1, gap-analysis, outreach, discovery. Solo: rinomina + vehicle_observations + snapshot/diff + test.

═══════════════════════════════════
DONE-CONDITION (incolla evidenza, rileggi l'artefatto):
1. .schema: campo età-veicolo rinominato; vehicle_observations(dealer_id, vehicle_key,
   first_observed_at, last_observed_at, status) esiste. MOSTRA .schema.
2. Collector ×2 su rossettomotors-srl: RUN1 N osservazioni PRESENT (first==last); RUN2 stesso
   istante = first INVARIATO, 0 duplicati. INCOLLA COUNT + 2 righe campione coi timestamp.
3. Test unitario GONE: 1 vehicle_key passa a GONE senza delete. INCOLLA output test.
4. Idempotenza S287 invariata: dealers=1, profiles=1.
5. GDPR: 0 colonne personali. Conferma.
6. Commit solo file nominati (dealer_collector.py + migrazione + test + report); no push.
═══════════════════════════════════
SPEC S289 (annota, non costruire): Gap-Analysis su metrica osservata ("stock fermo" = days_observed
alto; velocity = conteggio GONE/tempo); estendi generate_cold_day1 (templates.py:273) con dato
OSSERVATO ("questa BMW è ferma da ~X settimane"). ICP micro-dealer <20 da sorgente discovery diversa.
OUTPUT: REPORT in file + open -a TextEdit.
