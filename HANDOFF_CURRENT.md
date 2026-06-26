# HANDOFF_CURRENT — S289 · Fase 1 [S4] GAP-ANALYSIS (BUILD)

Branch `s210/audit-master-plan` · no push · CC-MAIN · additivo (ramo ricerca scraper non toccato).

## FASE 0 (riportata, non costruita)
- `pwd` = `/Users/macbook/Documents/combaretrovamiauto-enterprise` (root) ✓
- `git rev-parse HEAD` = `192af6df` (= `3a377fd` + 2 commit rumore-hook: `68917f9` harness gitignore + `192af6d` auto-close; range tocca solo STATE.md/rings.json/.gitignore/HANDOFF, **zero codice**) ✓
- working-tree pre-build = solo `.claude/NEXT_SESSION_PROMPT.md` (rumore-hook) ✓
- **Re-ground schema**: le 3 tabelle vivono in `data/dealers.db` (NON `dealer_network.sqlite`).
  `dealers.inventory_snapshot` = vehicle-lite con `make` per veicolo (→ conteggi brand);
  `dealer_profiles.brand_focus` = brand ordinati per conteggio; `vehicle_observations` 28 righe con
  `first/last_observed_at` (→ days_observed) + `status PRESENT/GONE`. **Nessun dato mancante** → build OK.

## Costruito (additivo su `tools/dealer_collector.py`)
- Tabella `dealer_gaps` (PK `dealer_id` = idempotente) in `init_db`.
- `gap_analysis(conn, dealer_id)`: share RELATIVA del segmento premium-tedesco (BMW/Mercedes/Audi)
  sul totale inventario, vs comparatore esplicito = brand-leader dello stesso dealer. Stock-fermo =
  veicoli del segmento con `days_observed >= 60`. Persiste upsert ON CONFLICT(dealer_id).
- Sub-comando CLI `gap <dealer_id>` (nessun fetch di rete, opera sul dealer già raccolto).

## DONE-CONDITION (evidenza reale, dealer reale)
**1. Gap su `rossettomotors-srl`** (`python3 tools/dealer_collector.py gap rossettomotors-srl`):
```json
{
  "segment": "premium-tedesco (BMW/Mercedes/Audi)",
  "segment_count": 10, "total_count": 28, "segment_share": 0.3571,
  "comparator": "brand-leader del dealer = BMW (8/28)", "comparator_share": 0.2857,
  "under_weight": false, "stale_signal": []
}
```
**Valore RELATIVO** = tedesco-premium 10/28 = **35.71%** · comparatore esplicito = BMW 8/28 = 28.57%.

**2. PROVA-RELATIVO** (conteggi reali da inventory_snapshot):
`BMW 8 · Volvo 4 · Volkswagen 4 · Fiat 3 · Skoda 2 · MINI 2 · Audi 2 · Toyota 1 · Opel 1 · Jaguar 1`
→ tedesco-premium = BMW(8)+Audi(2)+Mercedes(0) = 10. Perché NON è un gap-assoluto-spazzatura: non
dico "manca il brand X di ARGOS", misuro il PESO del segmento sul mix del dealer rapportato al suo
brand-leader (stesso denominatore 28). **Esito reale: under_weight=false** → per questo dealer il
premium-tedesco NON è un buco, è la sua forza (BMW è il brand #1). Output di intelligence valido: l'angolo
outreach è "approfondisci ciò che già funziona", non "riempi un vuoto".

**3. Idempotenza**: re-run → `SELECT COUNT(*) FROM dealer_gaps WHERE dealer_id='rossettomotors-srl'` = **1** (zero duplicati).

**4. GDPR-clean**: colonne `dealer_gaps` = dealer_id, segment, segment_count, total_count, segment_share,
comparator, comparator_share, under_weight, stale_signal, computed_at → **0 colonne personali**. ✓

**5. Commit**: solo `tools/dealer_collector.py` (file nominato); no push. `data/dealers.db` non tracciato (gitignore).

## LIMITE ONESTO (input per S290, NON nascosto)
Il comparatore = brand-leader-singolo è circolare quando il leader è IN-segmento (BMW è german-premium):
`segment_share >= leader_share` è quasi garantito se un brand tedesco guida → `under_weight` raramente
true. Per un gap "sotto-peso" robusto, S290 dovrebbe confrontare il segmento vs **aggregato non-segmento**
o vs **supply ARGOS**, non vs il singolo brand-leader. Per rossettomotors il numero relativo (35.71%) è
comunque corretto e informativo; è il flag booleano derivato che va raffinato.

## SPEC S290 (annotata, NON costruita)
- Estendi `generate_cold_day1` (`templates.py:273`) col gap + stock-fermo come dato osservato.
- ICP micro-dealer da sorgente discovery diversa.
- Raffina comparatore gap (vedi LIMITE ONESTO).

## SCOPE rispettato
Solo gap-analysis. Niente Day-1, niente outreach, niente nuovi dealer, niente nuovi sottosistemi.
