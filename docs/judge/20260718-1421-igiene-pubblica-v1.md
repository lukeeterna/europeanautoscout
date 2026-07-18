# Igiene pubblica v1 — CHIUSURA — 2026-07-18 14:21

Repo PUBBLICO `europeanautoscout` (origin github.com/lukeeterna/europeanautoscout).
Branch `s210/audit-master-plan`. Armatura: git -C esplicito su ogni comando, zero fetch web,
archivio combaretrovamiauto-enterprise INTOCCATO, porcelain-check pre-commit.

## I1 — NUMERO TEST → PLACEHOLDER (tree-wide)
- Pattern cercato: le 10 cifre del numero test → `<TEST_FOUNDER_NUM>` (cattura anche i prefissi
  `39…` / `+39…`; il prefisso di country-code non-identificante resta, le 10 cifre no).
- Scope totale in git: **91 file / 213 occorrenze**.
- Sostituiti in **79 file tracciati non-.bak / 178 occorrenze** (4 file avevano già il placeholder
  dalla V5 del 20260718-0730). Verifica: **0** occorrenze del numero grezzo nei file non-.bak.
- I restanti **12 file / 35 occorrenze** erano tutti file `.bak` → rimossi da git in I2 (rimozione
  totale dal working-tree = 91/213).
- **RESIDUO — `state/rings.json` (JSON tracciato)**: contiene il numero (1 occ, campo `note`
  generato). Placeholderato nel working-tree ma **NON staged** per porcelain-guard ("JSON mai
  staged"). File di stato generato (state/refresh.sh) → micro-fix futuro sulla sorgente del note.
- **NOTA file di CODICE toccati** (prima del prossimo E2E fisico vanno letti da `env/.env.local`
  untracked — micro-fix futuro):
  - `.harness/gate_e.py`
  - `argos-proxy/src/lib/wa-daemon.ts`
  - `chaos_db_stress.py`
  - `chaos_test.sh`
  - `tools/test_ambra_5scenarios.py`
  - `tools/test_e2e_full.py`
  - `tools/tests/test_dossier_hitl_smoke.py`

## I2 — .BAK TRACCIATI (23 file)
- Grep segreti sui 2 config (`docs/backups/pre_S134_setup/mcp.json.bak` +
  `settings.json.bak`), pattern `sk-|ghp_|github_pat_|AKIA|xox|[0-9]{8,10}:AA`:
  **0 match su entrambi** → nessun segreto, rimozione sicura.
- `git rm` dei **23** file `.bak` tracciati (git ls-files | grep .bak). Tracked .bak residui: **0**.
- `.gitignore`: aggiunta riga `*.bak*  # igiene: backup mai in git` (le regole preesistenti
  `*.bak` / `*.bak-*` NON coprivano i pattern `.bak_` underscore e `.bak.` dot — motivo per cui i
  23 erano tracciati).

## I3 — ANNOTAZIONI verifica_telefono (residuo F4, file UNTRACKED, fuori git)
- Blocco `verifica_telefono.campione_seed_perga` per-riga (idx, piva, denominazione, tel, esito,
  fonte_b, nota, seed, data 2026-07-18) ricavato VERBATIM da V3 di
  `docs/judge/20260718-1000-backfill-f4.md` + overlap V2. `idx` = indice naturale in `rows[]`.
  Validazione idx→denominazione superata (no fabbricazione).
- `potenza.json`: 8 righe (SÌ=7, NON-VERIFICABILE=1 idx0) — coerente V4 PZ 7/8.
- `treviso.json`: 8 righe (SÌ=7, NON-VERIFICABILE=1 idx13) — coerente V4 TV 7/8.
- `telefono_map_pz.json` / `telefono_map_tv.json`: blocco province-level ereditato dal JSON gemello.
- Tutti e 4 confermati **gitignored** (git status --porcelain su data/recon/ = vuoto).

## I4 — COMMIT + PUSH
- Porcelain-check pre-commit: nessun JSON/map/data/.bak staged come modifica (i .bak solo come
  deletion). rings.json + NEXT_SESSION_PROMPT.manual.md (dirty pre-sessione, non toccato) esclusi.
- Staged: 79 M (78 edit I1 + .gitignore) + 23 D.
- Commit: `igiene pubblica: numero test → placeholder + rimozione .bak tracciati` → `66d143f`.
- Push `origin s210/audit-master-plan`: **exit 0** (`932796d..66d143f`, pre-push guard passato).
