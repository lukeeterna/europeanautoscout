# NEXT SESSION — europeanautoscout (stato VERO da git/disco, 2026-07-18 14:21)

## Fatto in questa sessione (igiene pubblica v1)
- **I1** numero test → `<TEST_FOUNDER_NUM>` in **79 file tracciati non-.bak / 178 occ** (0 numeri
  grezzi residui fuori dai .bak). Dettaglio: `docs/judge/20260718-1421-igiene-pubblica-v1.md`.
- **I2** rimossi **23** file `.bak` tracciati (grep segreti sui 2 config = 0 match); `.gitignore`
  esteso con `*.bak*`.
- **I3** (residuo F4 CHIUSO) blocco `verifica_telefono.campione_seed_perga` per-riga annotato nei 4
  file dati untracked (potenza/treviso .json + telefono_map_pz/tv): PZ 7/8, TV 7/8, idx→nome
  validati, valori VERBATIM da judge V3. Restano fuori git (gitignored).
- **I4** commit `66d143f` + push `s210/audit-master-plan` exit 0 (pre-push guard passato).

## RESIDUI (micro-fix futuri, non bloccanti)
1. **`state/rings.json`** (JSON tracciato): contiene ancora il numero (1 occ, campo `note`
   generato). NON toccato in commit per porcelain-guard (JSON mai staged). Fix alla sorgente del
   note (state/refresh.sh genera rings.json).
2. **File di CODICE placeholderati** (`.harness/gate_e.py`, `argos-proxy/src/lib/wa-daemon.ts`,
   `chaos_db_stress.py`, `chaos_test.sh`, `tools/test_ambra_5scenarios.py`,
   `tools/test_e2e_full.py`, `tools/tests/test_dossier_hitl_smoke.py`): prima del prossimo E2E
   fisico devono leggere il numero da `env/.env.local` (untracked), non dal placeholder.
3. **History**: il numero resta nella git history (questo mandato è working-tree level; scrub
   filter-repo è task separato).

## Armatura (ricorda)
- OGNI git con `-C ~/Documents/europeanautoscout`, MAI `cd` nudo (cwd si resetta sull'archivio
  combaretrovamiauto-enterprise = INTOCCABILE).
- PII mai in git: porcelain-check (JSON/map/.bak assenti) prima di ogni commit.
- Solo GET pubblici, zero bypass 403/Cloudflare, zero contatto imprese.

## HEAD
`66d143f` (igiene pubblica) → + commit chiusura doc (vedi git log).
