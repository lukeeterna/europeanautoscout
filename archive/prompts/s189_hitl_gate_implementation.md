# S189 RESUME PROMPT — HITL approval gate dossier PRIMA invio WA

> **Incolla in nuova sessione Claude Code. Context vuoto assunto. Idempotente.**
> **S189 = pivot strategico post 6 ricadute over-mask sanitizer D-32. NO altra iterazione filter.**

---

## 0. Identità sessione

- **Progetto**: ARGOS Automotive
- **Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- **Branch**: `master`
- **Data riferimento**: 2026-05-25 (S188 closure)
- **Sessione corrente**: S189
- **Deadline business**: Day 1 Stile Car 2026-06-03 (8gg)

## 1. Vincolo context (vincolo #7 CLAUDE.md)

- `/context` turn 1, 5, 10
- 50% → no scope, findings → BACKLOG
- 60% → handoff S190 strutturato

## 2. Decisione CTO eredita S188 (immutable, evidence-based)

**Pivot strategico**: HITL approval gate Luke su dashboard:8080 PRIMA invio dossier WA.

### Evidence S188 (questa sessione, NON memoria)

| Test | Result |
|------|--------|
| Filter G downstream su 5 UAT sample | net zero gain (-3 sample 05 ma +1 fp sample 03, -1 fn sample 09) |
| Vision OCR conf bipolare 0.30/0.50 | nessun signal discriminante |
| Pattern ricaduta over-mask | **6 iterazioni** (S179b→S183→S183-bis→S183-ter→S187→S188) = struttura, non episodio |
| Upstream keyword filter S187 | F1=0.57 < gate 0.75 (memory `s187_preflight_evidence_pivot_pending`) |

### Constraint founder closed (NON ridiscutere)

- YOLO-plate-EU: **NO** (memory `s186_poc_eu_esito_c_definitive`)
- Foto manufacturer stock: **NO** (CLAUDE.md communication: "veicolo REALE con numeri REALI")
- Filter incrementale ulteriore: **NO** (anti-loop S188 STEP 5)

**Path residuo coerente con vincoli founder = HITL gate.**

## 3. Pre-flight obbligatorio

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise

# 1. Working tree dirty preservato S187/S188 (NON committare ora)
git status --short tools/scripts/pdf_generator_enterprise.py src/cove/image_sanitizer.py
# Atteso: " M" su entrambi → sanitizer S187 fix invocazione resta come pre-filter soft

# 2. Daemon iMac online + endpoint /send-doc attivo
curl -s http://192.168.1.2:9191/status
# Atteso: JSON con wa_connected:true

# 3. Dashboard:8080 raggiungibile
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.1.2:8080/login
# Atteso: 200

# 4. DB iMac path canonical (memory `s174_verify_s173_yellow`: ~/Documents/app-antigravity-auto/dealer_network.sqlite NON ~/argos)
ssh imac "ls -la ~/Documents/app-antigravity-auto/dealer_network.sqlite"

# 5. Schema dossier table (per migration step)
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite '.schema dossiers' 2>&1 || echo 'TABLE DOSSIERS NON EXISTE — verificare tabelle correlate'"
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite '.tables' 2>&1 | tr -s ' ' '\n' | grep -i dossier"
```

Se step 5 mostra che la tabella `dossiers` NON esiste → STOP, leggi `wa-intelligence/dashboard/db.py` per capire dove sono tracciati i PDF generati. Probabilmente in `opportunities` o `dealer_messages`. Adatta schema migration in STEP 2.

## 4. Reading order

1. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` (index)
2. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s186_poc_eu_esito_c_definitive.md`
3. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s187_preflight_evidence_pivot_pending.md`
4. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s187_closure_overmask_nogo.md`
5. `/tmp/s188_evidence/all5_vision_dump.json` (evidence S188 per audit decisione, non per re-implementare filter)
6. `wa-intelligence/wa-daemon.js:1431-1488` `/send-doc` handler attuale
7. `wa-intelligence/dashboard/app.py` (31KB Flask, struttura route)
8. `wa-intelligence/dashboard/db.py` (15KB schema)
9. `.claude/rules/security.md` — vincoli API auth 9191 + rate limit dashboard

## 5. STEP S189

### STEP 1 — Schema migration (architect → implementer)

Aggiungere `approval_status` su tabella dossier/opportunities iMac SQLite:

```sql
-- File migration nuovo: tools/migrations/s189_approval_gate.sql
ALTER TABLE <dossier_table> ADD COLUMN approval_status TEXT DEFAULT 'PENDING'
  CHECK(approval_status IN ('PENDING', 'APPROVED', 'REJECTED'));
ALTER TABLE <dossier_table> ADD COLUMN approval_ts INTEGER;
ALTER TABLE <dossier_table> ADD COLUMN reject_reason TEXT;
CREATE INDEX IF NOT EXISTS idx_dossier_pending ON <dossier_table>(approval_status)
  WHERE approval_status = 'PENDING';
```

Sostituire `<dossier_table>` con nome reale verificato STEP pre-flight 5.

Backup PRIMA migration (regola `.claude/rules/security.md` Database): `sqlite3 .backup`, NO `cp`.

### STEP 2 — wa-daemon gate `/send-doc` (delega implementer)

Patch `wa-intelligence/wa-daemon.js:1432-1488` — aggiungere controllo dopo `if (!fs.existsSync(file_path))` (riga ~1453):

```js
// HITL approval gate (S189)
if (dealer_id) {
    const db = require('better-sqlite3')(DB_PATH);
    const row = db.prepare(
        'SELECT approval_status FROM <dossier_table> WHERE dealer_id = ? AND file_path = ?'
    ).get(dealer_id, file_path);
    db.close();
    if (!row || row.approval_status !== 'APPROVED') {
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            error: 'dossier not approved by Luke',
            approval_status: row ? row.approval_status : 'NOT_FOUND'
        }));
        return;
    }
}
```

Note: `dealer_id` parametro già presente in body (riga 1436). NO breaking change su caller esistenti se ometto check quando `dealer_id` undefined (degrades gracefully verso behavior attuale per send manuali admin).

### STEP 3 — Dashboard route `/pending-dossiers` (delega frontend-developer)

Nuova route in `wa-intelligence/dashboard/app.py`:

```python
@app.route('/pending-dossiers')
@login_required
def pending_dossiers():
    """List + PDF preview per Luke review."""
    rows = db.query(
        "SELECT id, dealer_id, file_path, created_ts FROM <dossier_table> "
        "WHERE approval_status = 'PENDING' ORDER BY created_ts ASC LIMIT 50"
    )
    return render_template('pending_dossiers.html', dossiers=rows)

@app.route('/dossier/<int:dossier_id>/approve', methods=['POST'])
@login_required
def approve_dossier(dossier_id):
    db.execute(
        "UPDATE <dossier_table> SET approval_status='APPROVED', approval_ts=? "
        "WHERE id = ? AND approval_status = 'PENDING'",
        (int(time.time()), dossier_id)
    )
    audit_log({'action': 'approve', 'dossier_id': dossier_id, 'user': session['user']})
    return jsonify({'status': 'approved'})

@app.route('/dossier/<int:dossier_id>/reject', methods=['POST'])
@login_required
def reject_dossier(dossier_id):
    reason = request.json.get('reason', '')
    db.execute(
        "UPDATE <dossier_table> SET approval_status='REJECTED', approval_ts=?, reject_reason=? "
        "WHERE id = ? AND approval_status = 'PENDING'",
        (int(time.time()), reason, dossier_id)
    )
    audit_log({'action': 'reject', 'dossier_id': dossier_id, 'reason': reason})
    return jsonify({'status': 'rejected'})
```

Template `templates/pending_dossiers.html`: list view con embed `<iframe src="/dossier/<id>/preview">` (route preview PDF binary, già esistente?) + 2 button approve/reject + textarea reason.

Keyboard shortcut: `J` next, `K` prev, `A` approve, `R` reject (UX gotcha: Luke review ≥5 dossier/giorno → batch mode).

### STEP 4 — Audit JSONL

`/var/log/argos/approvals.jsonl` (o path equivalente su iMac, verificare permission scrittura PM2):

```json
{"ts": 1748185813, "action": "approve", "dossier_id": 42, "user": "luke", "dealer_id": "stile_car"}
{"ts": 1748185945, "action": "reject", "dossier_id": 43, "reason": "watermark visibile su targa frontale", "user": "luke"}
```

Rotation: logrotate weekly (BACKLOG #S189-1, OUT-OF-SCOPE S189).

### STEP 5 — E2E test TEST_FOUNDER

Scenario verde minimale:
1. Generate dossier su TEST_FOUNDER 39<TEST_FOUNDER_NUM> via `on_demand_runner` → row PENDING in DB
2. Dashboard:8080 `/pending-dossiers` mostra 1 row
3. Luke clicca approve → row APPROVED
4. Tool caller invoca `/send-doc` con `dealer_id=test_founder` → 200 OK, PDF arrivato su WA
5. Verifica DB: nuovo dossier PENDING → invoke `/send-doc` → 403 `dossier not approved by Luke`

Scenario reject:
1. Generate dossier → PENDING
2. Luke clicca reject con reason → REJECTED
3. Invoke `/send-doc` → 403 con `approval_status=REJECTED`

### STEP 6 — Commit scoped SE 5/5 E2E PASS

```bash
git add wa-intelligence/wa-daemon.js wa-intelligence/dashboard/app.py wa-intelligence/dashboard/templates/pending_dossiers.html tools/migrations/s189_approval_gate.sql
git commit -m "feat(S189): HITL approval gate dossier pre-invio WA

- Migration: approval_status PENDING/APPROVED/REJECTED su dossier table
- Daemon /send-doc: 403 se approval_status != APPROVED (dealer_id-gated, degrades graceful per admin)
- Dashboard route /pending-dossiers + approve/reject API
- Audit JSONL per drift detection (10% random review obj BACKLOG)

Pivot strategico post 6 ricadute over-mask sanitizer D-32 (memory s187/s188).
DECISIONS founder: NO YOLO-EU, NO foto stock, NO filter incrementale.
Day 1 Stile Car unblocked: gate Luke binario, rischio leak = 0.

Sanitizer S187 fix invocazione (file dirty pdf_generator_enterprise.py +
image_sanitizer.py) RESTA in posto come pre-filter soft per ridurre review work.
Out-of-scope S189: commit sanitizer fix → S190 dopo HITL stabilization.

Refs: prompts/s189_hitl_gate_implementation.md, memory s187_preflight_evidence_pivot_pending"
```

NO push fino verifica Luke E2E reale.

## 6. PASS criteria S189

- [ ] Pre-flight 1-5 verde
- [ ] Migration applicata + backup pre-migration
- [ ] Daemon `/send-doc` 403 su PENDING (test fisico curl)
- [ ] Daemon `/send-doc` 200 su APPROVED (test fisico curl)
- [ ] Dashboard `/pending-dossiers` mostra PDF preview + 2 button
- [ ] Audit JSONL scrive entry approve/reject
- [ ] E2E scenario verde + reject completi
- [ ] Sanitizer S187 patch resta dirty (NO commit qui)
- [ ] Commit scoped solo 4 file in-scope

## 7. Vincoli operativi (CLAUDE.md cross-ref)

- **#0 delegation-first**: STEP 2 daemon → implementer, STEP 3 dashboard → frontend-developer, STEP 1 schema → backend-architect
- **#1 fact-check**: API better-sqlite3 + Flask route via doc upstream, NON memoria
- **#3 no liste**: design singolo, no opzioni "scegli tu"
- **#4 critica**: 4 punti autocritica già scritti S188 closure (assunzione tempo Luke, scaling 30/60/90, ok-bias, sovradimensionamento). Re-verifica post-implementazione.
- **#5 zero-cost**: tutto in-stack esistente (Flask, SQLite, daemon Node)
- **#6 no PARTIAL**: 5/5 E2E verde o handoff S190
- **#9 no diplomatico**: se Luke dice "complica troppo" rispondi con dati (volume previsto, alternative valutate, time-to-Day-1)

## 8. Out-of-scope espliciti S189

- ❌ Commit `pdf_generator_enterprise.py` + `image_sanitizer.py` dirty (S190 dopo HITL stabile)
- ❌ Filter G o altra patch sanitizer (anti-loop S188)
- ❌ Detector dedicato plate-EU (DECISIONS founder closed)
- ❌ Upstream slide filter calibration (F1=0.57 noto fail)
- ❌ Logrotate audit JSONL (BACKLOG #S189-1)
- ❌ 10% random audit dashboard metric (BACKLOG #S189-2, dopo 10 dossier history)
- ❌ Trust tier unlock skip-HITL (BACKLOG #S189-3, dopo 10 APPROVED consecutivi)
- ❌ Touch `cove_engine_v4.py`, scrapers, `generate_dossier_from_data`

## 9. Exit criteria business

- ✅ S189 verde → Day 1 Stile Car 2026-06-03 SBLOCCATO (gate Luke garantisce zero leak)
- ✅ 10 dossier APPROVED consecutivi senza reject → BACKLOG #S189-3 trust tier
- ⚠️ Volume >100/mese (proiezione 3-6 mesi) → trigger R&D detector V2

## 10. Handoff S190 template (SE incompleto)

Se S189 chiude <5/5 PASS, scrivi `prompts/s190_hitl_gate_finalize.md` con identica struttura + step rimasti + ETA aggiornata. NO PARTIAL/ARANCIONE.

Se S189 verde, S190 prossima sessione = commit sanitizer fix `pdf_generator_enterprise.py` + `image_sanitizer.py` come pre-filter soft (review work reduction Luke), eventuale tuning padding mask.
