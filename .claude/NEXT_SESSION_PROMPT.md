# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-23T20:30:00Z` · sessione S288 · branch `s210/audit-master-plan`

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Come riprendere

1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>`  — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md`: tabella anelli (GENERATA) + task corrente + prossimi step

Se `SESSION_DIRTY.md` esiste in questa cartella, risolvi PRIMA i conflitti.

---

## Contesto S288 — analisi dealer_collector + metrica-tempo

### Stato commit
- HEAD: `05391e5` (auto-close hook), produzione: `da98462 feat(S287): collector pagina-dealer`
- Working tree pulito (solo NEXT_SESSION_PROMPT.md dirty = questo file)

### Findings verificati (fetch reale rossettomotors-srl)

**`avg_listing_age_days` è mal-nominato** — calcola l'ETÀ DEL VEICOLO in giorni
da `vehicle.firstRegistrationDate`, NON i giorni-online dell'annuncio.
- Codice: `_first_reg_to_age_days` righe 116-137 `tools/dealer_collector.py`
- Media calcolata riga 208: `round(sum(ages)/len(ages), 1)`

**AS24 NON espone data-pubblicazione nel JSON listing** (pagina-dealer):
- `TOP_KEYS`: `['id','images','has360Image','prices','seals','superDeal','url','vehicle','location','seller',...]`
- `VEHICLE_KEYS`: solo `firstRegistrationDate` come campo data
- Nessun candidato trovato tra: creationDate, publishDate, listingSince, firstOnlineDate, onlineSince, createdDate
- Stessa limitazione del campo `phone` (S208/S209)

**ID nativo stabile disponibile**:
- `listing.id` = UUID v4 (es. `7ae4e9d1-f256-4c1e-b907-4205212ad8d9`) a livello top-level
- Usabile come chiave-veicolo senza hash di contenuto
- VIN: assente nel listing JSON (solo su pagina-dettaglio)

**Schema DB già ha `first_seen` / `last_seen`** in tabella `dealers` — base per metrica proxy.

### Decisioni da prendere (prossima sessione)

1. **Rinominare `avg_listing_age_days`** → `avg_vehicle_age_days` (corretto semanticamente)

2. **Metrica "giorni-online" — 2 opzioni**:
   - Opzione A (raccomandata): usare `first_seen` locale già in schema come proxy "prima volta che ARGOS ha visto questo annuncio". Richiede salvare `listing.id` in `inventory_snapshot` + tabella `listing_tracking(listing_id, dealer_id, first_seen, last_seen)`.
   - Opzione B: fetch pagina-dettaglio singolo annuncio per verificare se AS24 espone `publishDate` lì. Da verificare PRIMA di costruire (pattern S208: campo non esposto a lista può esserlo a dettaglio).

3. **Usare `listing.id` (UUID) come chiave-veicolo** invece di hash — stabile, nativo, già presente.

### Step immediati prossima sessione

```
STEP 1: Verifica opzione B — fetch 1 pagina-dettaglio annuncio AS24 (read-only)
        es. https://www.autoscout24.it/annunci/bmw-520-d-touring-...-7ae4e9d1-f256-4c1e-b907-4205212ad8d9
        Cerca publishDate/creationDate nel __NEXT_DATA__ della pagina-dettaglio.

STEP 2: Design schema tabella `listing_tracking` + migration reversibile
        Colonne: listing_id TEXT PK, dealer_id TEXT FK, first_seen TEXT, last_seen TEXT,
                 price_history TEXT (JSON), created_at TEXT, updated_at TEXT.

STEP 3: Patch collector — aggiungi listing.id in inventory_snapshot + upsert listing_tracking
STEP 4: Rinomina avg_listing_age_days -> avg_vehicle_age_days in schema + codice
```
