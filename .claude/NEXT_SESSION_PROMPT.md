# S206 — E2E TEST_FOUNDER fisico Luke (STEP C/D/E post-S205)

**Generato**: 2026-05-29T13:55:00Z (S205 chiusura ordinata @ context 60%)
**Data target**: 2026-05-30 (T-4gg Day 1 Stile Car 2026-06-03)
**Owner**: CC tecnico + Luke fisico TEST_FOUNDER 393314928901
**Gate finale**: Luke dichiara "pienamente soddisfatto" (memoria `feedback_e2e_full_test_founder`)

---

## STATO POST-S205 ✅

### STEP A deploy iMac VERDE
- Rsync sha-verified 3/3: response-analyzer.py + wa-daemon.js + wa_bridge.py
- Migration S203 idempotente applicata `comm-broker/bridge.sqlite` (col `action_type` verified)
- PM2 reload daemon+dashboard, 4/4 online, `/status` connected
- Log clean (S202 ALTER messages classifier_intent/confidence/raw_payload OK)
- Backup: `imac:/tmp/argos_s205_backup_20260529_133521/` + `/tmp/{dnet,bridge}.s205_pre.bak`

### STEP B smoke offline VERDE 5/5
`python3 tools/test_ambra_5scenarios.py` → 5/5 PASS:
- VEHICLE_REQUEST conf 0.9, PRICE_NEGOTIATION→CURIOSITY, CONTRACT_REQUEST state-gated (P1 fix), NEGATIVE conf 0.95 (P2 fix), AMBIGUOUS→UNKNOWN
- F1 benigno: opt_out col non impostato dal test offline (handler main() lo fa — atteso)

### FINDING strutturale S205 → C-DB-ENV-001 (PLAN.md)
PM2 env `ARGOS_DB_PATH=releases/20260527_083951/dealer_network.sqlite` (28KB, 0 messages runtime). DB root `~/Documents/app-antigravity-auto/dealer_network.sqlite` 389KB con 81 messages history (max 2026-05-16) DISGIUNTO. Daemon+dashboard convergono su releases/ DB → consistenti per E2E S206, ma storia legacy persa. **Consolidare DB autoritativo unico prima dealer reali.**

### PM2 cwd autoritativo (conferma S204)
- script: `~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js`
- cwd: `~/Documents/app-antigravity-auto/wa-intelligence`
- `current/` → `releases/20260527_083951/` symlink invariato. sync.sh deploya in releases/ ma daemon legge path autoritativo → **usare rsync diretto come S205**.

---

## PRE-FLIGHT S206 (5 min, BLOCCANTE)

PF1. PM2 4/4 online:
```
ssh imac "PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH pm2 list"
```
PF2. `/status` connected + daily_remaining ≥1:
```
ssh imac "curl -s localhost:9191/status"
```
PF3. Verifica sha S202+S203 LIVE (no drift):
```
REMOTE="/Users/gianlucadistasi/Documents/app-antigravity-auto"
for f in wa-intelligence/response-analyzer.py wa-intelligence/wa-daemon.js comm-broker/wa_bridge.py; do
  L=$(shasum -a 256 "$f" | awk '{print $1}')
  R=$(ssh imac "shasum -a 256 $REMOTE/$f | awk '{print \$1}'")
  [ "$L" = "$R" ] && echo "✓ $f" || echo "⚠ DRIFT $f"
done
```
PF4. `action_type` col bridge:
```
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite 'PRAGMA table_info(bridge_outbound)' | grep action_type"
```

---

## STEP C — E2E TEST_FOUNDER fisico (90-120 min)

**Direzione**: Luke 3314928901 → ARGOS 3281536308 (memoria `s176_finalize_red`).

**C1**. Trigger pipeline (BMW X1 €25000, memoria `s198_step7`):
```
python3 tools/on_demand_runner.py --marca BMW --modello X1 --budget 25000 --dealer "TEST_FOUNDER"
```
Verifica: dashboard:8080 mostra dossier PENDING su HITL gate (anello #9 S203).

**C2**. Luke approva dashboard:8080 → bridge_outbound INSERT `action_type=DOSSIER_SEND` `approved_ts=NOW`. Verifica: WA arriva + `current_step=DOSSIER_SENT` (memoria `s177a_state_fix`).

**C3** (3 sub-test sequenziali):
- C3a POSITIVE "mi interessa" → reply auto
- C3b CONTRACT_REQUEST "ok mando bonifico" (P1 fix S202) → contract DRAFT + sign_url
- C3c NEGATIVE "non mi scrivere più" (P2 fix S202) → opt_out=1 + zero auto-reply

Verifica: log + `messages` direction=OUTBOUND + AMBRA NO hallucination (memoria `s175_0_e2e_red_ambra_hallucination`).

**C4**. Luke firma `landing/contract/?token=$TOKEN`:
```
curl -s -o /dev/null -w "%{http_code}\n" https://argos-automotive.pages.dev/contract/$TOKEN  # 302
```
Submit firma → worker `/api/v1/contract/:id/sign` → SIGNED.

**C5**. Luke mark-paid via dashboard:8080 (action_type=mark_paid HITL).
**Gate C**: contract PAID + audit_log iMac.

---

## STEP D — UAT sanitizer 1 sample (30 min, opzionale context <55%)

D1. PDF dossier C1, visual check:
- Targa coperta no over-mask (memoria `s187_closure_overmask_nogo`)
- Seller_name coperto
- Watermark dealer
- "xDrive 25e"/badge NON cancellato (memoria `s176_partial`)

D2. Luke decide GO/NO-GO C-SAN-001.

---

## STEP E — Closure (15 min)

E1. PLAN.md:
- C-E2E-ZERO → [ADDRESSED] se C 5/5 verde
- C-SAN-001 → verdict D
- ultimo_update + PROSSIMA_AZIONE

E2. Memory project `s206_closure_*.md` evidence.

E3. Commit:
```
git add PLAN.md prompts/s206_*.md .claude/NEXT_SESSION_PROMPT.md
git commit -m "feat(S206 close): E2E TEST_FOUNDER 5/5 verde — Day 1 Stile Car SBLOCCATO"
git push
```

E4. VERDE → `prompts/s207_day1_stile_car_live.md`. ROSSO → handoff `prompts/s207_*.md` (vincolo #6 mai PARTIAL).

---

## VINCOLI (non sindacabili)
- TEST_FOUNDER unico destinatario WA. Stile Car NON contattabile finché Luke "pienamente soddisfatto".
- Max 1 messaggio Day 1 per numero.
- Linguaggio: MAI "Germania" "import" "premium" "ARGOS" primo elemento.
- Budget LLM hard cap €30/mese.
- Context budget: chiusura a 60%.

## FILE CRITICI (read prima edit)
- `wa-intelligence/response-analyzer.py` (P1/P2/P3 S202 LIVE)
- `wa-intelligence/wa-daemon.js` (anello #9 S203 LIVE)
- `comm-broker/wa_bridge.py` (action_type whitelist LIVE)
- `wa-intelligence/dashboard/app.py` (HITL gate UI)
- `tools/on_demand_runner.py` (entry pipeline)

## NON FARE
- NO modifica `cove_engine_v4.py`
- NO nuove skill/agent
- NO test su dealer reali ≠ TEST_FOUNDER
- NO PARTIAL closure (vincolo #6)
