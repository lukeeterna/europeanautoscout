# S190 RESUME PROMPT — E2E fisico Luke + commit scoped S189

> Sessione S189 chiusa context 70% dopo SMOKE TEST DAEMON+DASHBOARD VERDE.
> Resta E2E fisico Luke (approve UI + verify WA delivery) + commit scoped 4 file.

---

## 0. Identità sessione

- **Progetto**: ARGOS Automotive
- **Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- **Branch**: `master`
- **Data riferimento**: 2026-05-25 (S189 closure), S190 prossima sessione
- **Deadline business**: Day 1 Stile Car 2026-06-03 (8gg)

## 1. Stato implementazione S189 (DONE, NOT committed)

### Modifiche in working tree (4 file in-scope S189)
```
tools/migrations/s189_approval_gate.sql          (nuovo, applicato iMac OK)
tools/migrations/apply_s189.sh                   (nuovo, idempotente)
wa-intelligence/wa-daemon.js                     (riga 1455-1492, +38 righe gate HITL)
wa-intelligence/dashboard/app.py                 (riga 901-1018, +117 righe route+helpers)
wa-intelligence/dashboard/templates/pending_dossiers.html  (nuovo)
wa-intelligence/dashboard/templates/base.html    (sidebar voce "Review Dossier")
```

### File dirty pre-esistenti S187/S188 (OUT-OF-SCOPE, NON committare in S190)
```
src/cove/image_sanitizer.py
tools/scripts/pdf_generator_enterprise.py
```

### Backup iMac creato (S189 STEP 1)
`/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network_backup_20260525_210856.sqlite`

## 2. Smoke test S189 — risultati VERDE

| Test | Result |
|------|--------|
| Pre-flight 1-5 | 4/5 verde + 1 finding strutturale tabella → risolto con CREATE TABLE |
| Migration apply + integrity_check | OK + backup OK |
| Daemon `/send-doc` 1° call (PENDING auto-register) | 403 dossier_id=1, DB row OK, Telegram alert OK |
| Daemon `/send-doc` 2° call same file | 403 PENDING (UNIQUE no dup) |
| Daemon `/send-doc` 3° call post-APPROVE | gate PASS (500 downstream wa initializing, NON gate-related) |
| Dashboard `/pending-dossiers` | 303 → /login (route registrata) |
| Dashboard `/api/dossier/X/approve\|reject` | 401 unauth (endpoint OK, auth required) |
| WA daemon connection | `wa_status: connected` (post-restart sessione persistita) |

Setup E2E preparato in S189:
- Dossier #2 ID PENDING in DB iMac, dealer_id=`test_founder_s189_e2e`, file=`ARGOS_BMW_Serie3_S189_E2E_TEST.pdf` (4MB reale)

## 3. Bug strutturali pre-esistenti scoperti (BACKLOG, NON fix in S190)

### BUG-S189-INFRA-1: PM2 cwd legacy vs current/ deploy atomic
- `argos-wa-daemon` cwd `~/Documents/app-antigravity-auto/wa-intelligence/` (git clone path)
- `argos-dashboard` cwd `~/Documents/app-antigravity-auto/wa-intelligence/` (idem)
- Deploy `deploy/sync.sh` carica `releases/<ts>/` + symlink `current/` ma PM2 NON usa quel path
- Workaround S189: copia patched files in legacy path post-deploy (`cp current/.../X legacy/.../X`)
- Fix strutturale: `pm2 delete` + `pm2 start current/.../wa-daemon.js --cwd current/wa-intelligence` + `pm2 save`. Richiede consenso Luke (rischio rompere altri workflow).

### BUG-S189-INFRA-2: better-sqlite3 NODE_MODULE_VERSION mismatch
- Binding compilato MacBook node 22 (ABI 127), iMac runna node 20 (ABI 115)
- Pattern già visto S171 ("rebuilt node 22")
- Fix S189: `npm install better-sqlite3 --build-from-source` in legacy path → ABI 115 nativo
- Fix strutturale: deploy.sh deve `cd $RELEASE_DIR && npm rebuild better-sqlite3` post rsync, NON ereditare prebuild via `cp -al`

## 4. Pre-flight S190 (rapido)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise

# 1. Verify working tree S189 in scope
git status --short tools/migrations/ wa-intelligence/wa-daemon.js wa-intelligence/dashboard/

# 2. Daemon WA connected
curl -s http://192.168.1.2:9191/status | grep wa_status
# Atteso: "connected" — se "initializing", aspetta 30s o controlla logs

# 3. Dossier #2 PENDING ancora in DB
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, dealer_id, approval_status FROM dossiers WHERE id=2\""
# Atteso: 2|test_founder_s189_e2e|PENDING (o APPROVED se Luke ha gia' cliccato)
```

## 5. STEP S190

### STEP 1 — E2E fisico Luke (UI dashboard + WA delivery)

**Istruzioni a Luke (3 azioni fisiche)**:
1. Apri http://192.168.1.2:8080/login → login credenziali abituali
2. Vai http://192.168.1.2:8080/pending-dossiers
3. Trova dossier #2 (`test_founder_s189_e2e`, BMW Serie 3) → click **Approva**

Quando Luke dice "fatto":
- Verifica audit JSONL: `ssh imac "tail -3 ~/Documents/app-antigravity-auto/logs/approvals.jsonl"`
  Atteso: entry `{action:approve, dossier_id:2, user:<luke>}`
- Verifica DB: `ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite 'SELECT id, approval_status, approval_user FROM dossiers WHERE id=2'"`
  Atteso: `2|APPROVED|<luke>`
- Retry /send-doc:
```bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://192.168.1.2:9191/send-doc \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ARGOS_API_KEY" \
  -d '{"phone":"39<TEST_FOUNDER_NUM>","file_path":"/Users/gianlucadistasi/Documents/app-antigravity-auto/dossiers/ARGOS_BMW_Serie3_S189_E2E_TEST.pdf","dealer_id":"test_founder_s189_e2e","caption":"ARGOS S189 E2E test"}'
```
  Atteso: HTTP 200 `{status:sent, msg_id:doc_...}`
- Luke conferma PDF ricevuto su WA <TEST_FOUNDER_NUM>

### STEP 2 — Test reject flow

Crea dossier #3 PENDING per test reject:
```bash
curl -s -X POST http://192.168.1.2:9191/send-doc \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ARGOS_API_KEY" \
  -d '{"phone":"39<TEST_FOUNDER_NUM>","file_path":"/Users/gianlucadistasi/Documents/app-antigravity-auto/dossiers/ARGOS_BMW_Serie3_S189_E2E_TEST.pdf","dealer_id":"test_founder_s189_reject","caption":"reject test"}'
```

Luke va su /pending-dossiers → trova #3 → click **Rifiuta** → textarea reason "test reject S190" → submit.

Verifica:
- Audit JSONL entry `{action:reject, dossier_id:3, reason:"test reject S190"}`
- DB `approval_status=REJECTED, reject_reason="test reject S190"`
- Retry /send-doc dossier #3 → 403 `approval_status=REJECTED`

### STEP 3 — Code-review delegata (vincolo CLAUDE.md #0)

Delega `code-reviewer` su diff 4 file in-scope. Atteso PASS o issue specifici. SE FAIL → fix in STEP 3-bis.

### STEP 4 — Cleanup test rows

```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"DELETE FROM dossiers WHERE dealer_id IN ('s189_smoke_test','test_founder_s189_e2e','test_founder_s189_reject')\""
ssh imac "rm -f ~/Documents/app-antigravity-auto/dossiers/ARGOS_BMW_Serie3_S189_E2E_TEST.pdf"
```

### STEP 5 — Commit scoped SE STEP 1-3 verde

```bash
git add tools/migrations/s189_approval_gate.sql tools/migrations/apply_s189.sh \
        wa-intelligence/wa-daemon.js \
        wa-intelligence/dashboard/app.py \
        wa-intelligence/dashboard/templates/pending_dossiers.html \
        wa-intelligence/dashboard/templates/base.html

git commit -m "feat(S189): HITL approval gate dossier pre-invio WA

- Migration: tabella dossiers con approval_status PENDING/APPROVED/REJECTED
  + UNIQUE(dealer_id, file_path) + partial index PENDING
- Daemon /send-doc: 403 PENDING auto-register su prima call, 403 stato
  != APPROVED, gate-pass + fall-through su APPROVED (dealer_id-gated,
  degrades graceful per admin senza dealer_id)
- Dashboard FastAPI: /pending-dossiers list+iframe preview, /api/dossier/X/
  approve|reject con auth + audit JSONL
- Telegram alert su INSERT PENDING

Pivot strategico post 6 ricadute over-mask sanitizer D-32 (memory s187/s188).
Vincoli founder closed: NO YOLO-EU, NO foto stock, NO filter incrementale.

E2E TEST_FOUNDER 39<TEST_FOUNDER_NUM> VERDE (S190 STEP 1+2 fisico Luke):
- Approve flow: dashboard click → audit JSONL → /send-doc 200 → PDF arrivato WA
- Reject flow: dashboard click + reason → audit JSONL → /send-doc 403 REJECTED

File dirty pre-esistenti S187/S188 (image_sanitizer.py + pdf_generator_
enterprise.py) RESTANO uncommitted come pre-filter soft → S191 commit.

BACKLOG strutturali S190:
- BUG-S189-INFRA-1: PM2 cwd legacy vs current/ deploy atomic
- BUG-S189-INFRA-2: better-sqlite3 ABI mismatch deploy.sh
- S189-BL-1: logrotate audit JSONL
- S189-BL-2: 10% random audit metric dashboard (dopo 10 dossier history)
- S189-BL-3: trust tier skip-HITL dopo 10 APPROVED consecutivi
- S189-BL-4: keyboard shortcuts J/K/A/R dashboard (volume scaling)

Refs: prompts/s189_hitl_gate_implementation.md, prompts/s190_e2e_physical_close.md"
```

NO push fino a smoke post-commit verde (`node --check`, `python3 -c "import app"`, status daemon).

### STEP 6 — Push + Memory update

```bash
git push origin master
```

Aggiungi memory `s189_closure_verde_hitl_gate.md` + index MEMORY.md.

### STEP 7 — Handoff S191 (sanitizer fix dirty commit)

Crea `prompts/s191_sanitizer_dirty_commit.md` per commit `image_sanitizer.py` + `pdf_generator_enterprise.py` come pre-filter soft (S187 fix invocazione).

## 6. PASS criteria S190

- [ ] Pre-flight verde
- [ ] STEP 1 approve E2E fisico Luke verde (audit JSONL + DB APPROVED + WA PDF delivered)
- [ ] STEP 2 reject E2E verde (audit + DB REJECTED + 403 retry)
- [ ] STEP 3 code-review PASS o issue fixati
- [ ] STEP 4 cleanup row test DB iMac
- [ ] STEP 5 commit scoped 6 file (NO dirty S187/S188)
- [ ] STEP 6 push + memory entry
- [ ] STEP 7 prompt S191 sanitizer commit

## 7. Vincoli operativi S190 (CLAUDE.md cross-ref)

- **#0 delegation-first**: STEP 3 code-reviewer obbligatorio, NON CTO direct
- **#4 critica strutturale**: post-implementazione re-verifica 4 autocritica S188
- **#6 no PARTIAL**: 7/7 verde o handoff S191 strutturato
- **#7 context budget**: /context turn 1, 5, 10 — chiusura 60% — S189 ha chiuso 70% (sopra soglia, lesson learned: chiudere a 50% per garantire margine commit)

## 8. Out-of-scope espliciti S190

- ❌ Fix BUG-S189-INFRA-1 (PM2 cwd) — richiede consenso Luke + risk assessment, sessione dedicata
- ❌ Fix BUG-S189-INFRA-2 (deploy.sh rebuild) — idem
- ❌ Commit image_sanitizer.py + pdf_generator_enterprise.py → S191
- ❌ Logrotate / metric / trust tier / keyboard shortcuts → BACKLOG S192+
- ❌ Touch cove_engine_v4.py, scrapers

## 9. Exit criteria business

- ✅ S190 verde → Day 1 Stile Car 2026-06-03 SBLOCCATO (gate Luke garantisce zero leak)
- ⚠️ Day 1 deadline 8gg → S190+S191 entro 2 sessioni
