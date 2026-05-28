# S205 — Deploy iMac S202/S203 + E2E TEST_FOUNDER fisico Luke

**Sessione**: S205
**Data target**: 2026-05-29 (T-5gg Day 1 Stile Car 2026-06-03)
**Owner**: CC tecnico + Luke fisico (TEST_FOUNDER 393314928901)
**Gate finale**: Luke dichiara "pienamente soddisfatto" su E2E completo (memoria `feedback_e2e_full_test_founder`).
**Critique da chiudere**: `C-DEPLOY-S203` (PLAN.md). Se gate verde, sblocca Day 1 Stile Car.

---

## PRE-FLIGHT (10 min, BLOCCANTE)

PF1. Verifica commit presenti locale:
```
git log --oneline -5
# atteso: ecd677c (S203 anello #9 bridge_outbound HITL), ab6da39 (S202 classifier P1+P2+P3)
```
PF2. Verifica PM2 iMac stato (atteso 4/4 online):
```
ssh imac "zsh -lc 'pm2 list'"
```
PF3. Verifica WA daemon connected + daily remaining ≥1:
```
ssh imac "curl -s localhost:9191/status"
# atteso: wa_status=connected, daily_remaining ≥1
```
PF4. Verifica TEST_FOUNDER whitelist daemon attiva (memoria `feedback_test_founder_3314928901_argos_authorized`):
```
ssh imac "grep -n '393314928901' ~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js | head -3"
```
PF5. Backup DB iMac PRIMA del deploy (rules/security.md):
```
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite '.backup /tmp/dnet.s205_pre.bak'"
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite '.backup /tmp/bridge.s205_pre.bak'"
```

Se uno PF fallisce → STOP, indaga root cause, NON proseguire.

---

## STEP A — Deploy codice S202+S203 su iMac (45-60 min)

A1. Rsync atomico (rules/security.md: symlink swap, MAI scp singoli file). Verifica `deploy/sync.sh` esiste e funziona:
```
cat deploy/sync.sh | head -30
bash deploy/sync.sh --dry-run  # se supportato
```
Se sync.sh non sufficiente: rsync mirato file modificati S202/S203:
- `wa-intelligence/response-analyzer.py` (classifier P1+P2+P3)
- `wa-intelligence/wa-daemon.js` (anello #9 bridge_outbound INSERT)
- `comm-broker/wa_bridge.py` (action_type whitelist)
- `comm-broker/migrations/s203_bridge_outbound_action_type.sql`

A2. Applica migration SQL se non ancora applicata:
```
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite < ~/Documents/app-antigravity-auto/comm-broker/migrations/s203_bridge_outbound_action_type.sql"
# poi PRAGMA table_info(bridge_outbound) verifica colonna action_type presente
```

A3. PM2 reload (NON restart): mantiene WA session:
```
ssh imac "zsh -lc 'pm2 reload argos-wa-daemon && pm2 reload argos-dashboard'"
sleep 5
ssh imac "curl -s localhost:9191/status"  # connected + uptime resettato
```

A4. Smoke post-deploy: log clean ultimi 30 righe daemon, no exception:
```
ssh imac "zsh -lc 'pm2 logs argos-wa-daemon --lines 30 --nostream 2>&1 | tail -40'"
```

**Gate A**: 4/4 PM2 online + /status 200 connected + log clean. Se rosso → rollback symlink (rules/security.md "rollback in 1 secondo").

---

## STEP B — Smoke classifier P1/P2/P3 (20 min)

B1. Esegui `tools/test_ambra_5scenarios.py` su MacBook (script 305 righe, memoria `s198_step7_rosso`):
```
python3 tools/test_ambra_5scenarios.py
# atteso: 5/5 PASS dopo fix S202 P1 (bonifico/pagamento) + P2 (non scrivere più) + P3 (opt_out)
```
Se ≠ 5/5 → STOP. Apri ticket P4, NON proseguire a STEP C.

---

## STEP C — E2E TEST_FOUNDER fisico Luke (90-120 min)

**Direzione corretta**: Luke da TEST_FOUNDER 3314928901 → ARGOS 3281536308 (UX gotcha memoria `s176_finalize_red`).

C1. Trigger pipeline scrape→CoVe→PDF→send-doc su modello target (memoria `s198_step7` usare BMW X1 €18000 o equivalente):
```
python3 tools/on_demand_runner.py --marca BMW --modello X1 --budget 25000 --dealer "TEST_FOUNDER"
# atteso: PDF dossier generato, send-doc OK su 3314928901
```
**Verifica**: dashboard:8080 mostra dossier PENDING su HITL gate (S190+S203 anello #9).

C2. Luke fisico approva su dashboard:8080 → bridge_outbound INSERT con action_type=DOSSIER_SEND.
**Verifica**: messaggio WA arriva a Luke + state DOSSIER_SENT su current_step (memoria `s177a_state_fix`).

C3. Luke fisico risponde da TEST_FOUNDER:
- C3a. Reply POSITIVE "mi interessa" → AMBRA classifier POSITIVE → reply auto contract_request o follow-up.
- C3b. Reply CONTRACT_REQUEST "ok mando bonifico" (test P1 fix S202) → handler crea contract DRAFT su argos-proxy → sign_url consegnato.
- C3c. Reply NEGATIVE "non mi scrivere più" (test P2 fix S202) → opt_out=1 + zero auto-reply.

**Verifica per ognuna**: log response-analyzer.py + DB `messages` direction=OUTBOUND per reply auto + AMBRA NO hallucination (memoria `s175_0_e2e_red_ambra_hallucination`).

C4. Luke fisico firma contract via landing/contract/?token=<token>:
```
# Verifica Pages function attiva
curl -s -o /dev/null -w "%{http_code}\n" https://argos-automotive.pages.dev/contract/$TOKEN
# atteso: 302 redirect a /contract/?token=$TOKEN
```
Luke seleziona font signature + submit → worker /api/v1/contract/:id/sign → contract SIGNED.

C5. Luke fisico simula mark-paid via dashboard:8080 (memoria `s175_0_prompt_prepared` form):
```
# Verifica worker mark-paid
curl -s https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/$ID/mark-paid -X POST [...]
```
**Gate C**: contract state = PAID, audit_log iMac entry presente.

---

## STEP D — UAT sanitizer 1 sample reale (30 min, OPZIONALE se context <55%)

D1. Apri PDF dossier generato in C1, verifica visual:
- Targa coperta correttamente (no over-mask paraurti, memoria `s187_closure_overmask_nogo`)
- Seller_name coperto
- Watermark dealer presente
- "xDrive 25e" o badge modello NON cancellato (memoria `s176_partial`)

D2. Luke decide: GO/NO-GO su C-SAN-001.
- GO: chiudi critique in PLAN.md
- NO-GO: lascia OPEN, handoff S206 per fix mirato

---

## STEP E — Closure VERDE / handoff S206 (15 min)

E1. Aggiorna PLAN.md:
- C-DEPLOY-S203 → [ADDRESSED]
- C-E2E-ZERO → [ADDRESSED] se STEP C 5/5 verde
- C-SAN-001 → secondo verdict STEP D
- ultimo_update + PROSSIMA_AZIONE

E2. Aggiorna MEMORY.md con project memory `s205_closure_*.md` (PASS criteria evidence).

E3. Commit + push:
```
git add PLAN.md prompts/s205_*.md
git commit -m "feat(S205 close): deploy S202+S203 iMac + E2E TEST_FOUNDER 5/5 verde"
git push
```

E4. Se gate VERDE: Day 1 Stile Car SBLOCCATO per 2026-06-03 (T-5gg). Crea `prompts/s206_day1_stile_car_live.md`.
   Se gate ROSSO/PARTIAL: handoff strutturato `prompts/s206_*.md` con stato preciso (vincolo #6 mai PARTIAL/ARANCIONE).

---

## VINCOLI SESSIONE (non sindacabili)

- TEST_FOUNDER unico destinatario WA reale per tutta S205. Stile Car (3935xxx) NON contattabile finché Luke pienamente soddisfatto.
- Max 1 messaggio Day 1 per numero (rules/identity.md).
- Linguaggio Day 1: MAI "Germania" "import" "premium" "ARGOS" come primo elemento.
- Budget LLM hard cap €30/mese (CLAUDE.md vincolo zero-cost).
- Context budget: /context periodicamente, chiusura a 60%.
- Gate qualitativo Luke "pienamente soddisfatto" > checklist meccaniche (feedback_e2e_full_test_founder).

## OUTPUT ATTESI

1. Codice S202+S203 live su iMac (verificato via /status + log).
2. Smoke classifier 5/5 PASS.
3. E2E TEST_FOUNDER 5/5 verde (C1-C5) + audit trail DB.
4. Decisione C-SAN-001 GO/NO-GO con evidence visuale.
5. PLAN.md aggiornato (critique closed) + commit pushato.
6. Verdict Luke su Day 1 Stile Car: SBLOCCATO o BLOCCATO con motivo strutturale.

## FILE DA TOCCARE (read prima di edit)

- `wa-intelligence/response-analyzer.py` (verify P1/P2/P3 applicato post-deploy)
- `wa-intelligence/wa-daemon.js` (verify anello #9 INSERT bridge_outbound)
- `comm-broker/wa_bridge.py` (verify action_type whitelist)
- `wa-intelligence/dashboard/app.py` (verify HITL gate dossier UI)
- `tools/on_demand_runner.py` (entry point pipeline)
- `deploy/sync.sh` (deploy iMac)

## NON FARE

- NO modifica `cove_engine_v4.py` (rules/cove.md).
- NO nuove skill/agent/framework (rules vincolo invariate).
- NO test su dealer reali diversi da TEST_FOUNDER.
- NO commit con working tree dirty out-of-scope.
- NO PARTIAL closure (vincolo #6).
