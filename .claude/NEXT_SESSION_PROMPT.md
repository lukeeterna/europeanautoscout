# Prompt ripartenza — generato automaticamente

**Generato**: `2026-06-04T16:00:00Z`
**Sessione**: S238-deploy-tg-bot
**Repo**: `/Users/macbook/Documents/combaretrovamiauto-enterprise` (branch `s210/audit-master-plan`)

## Task interrotto: deploy telegram-handler.py su iMac

Sessione chiusa a 60% context PRIMA di eseguire il deploy. Il task è completamente definito.

### File da deployare (già fixato + py_compile PASS locale)
`/Users/macbook/Documents/combaretrovamiauto-enterprise/wa-intelligence/telegram-handler.py`
MD5 locale: `aa1716b8eff984704923e3893e8754fb`

### Procedura da eseguire nella prossima sessione

Connessione iMac: `ssh gianlucadistasi@192.168.1.2`

PATH-SPLIT su iMac (aggiornare ENTRAMBI):
1. RELEASE: `~/Documents/app-antigravity-auto/releases/20260527_083951/wa-intelligence/telegram-handler.py`
2. ROOT: `~/Documents/app-antigravity-auto/wa-intelligence/telegram-handler.py`

**STEP 1 — PRE-baseline (read-only):**
```bash
ssh gianlucadistasi@192.168.1.2 "~/.npm-global/bin/pm2 jlist" | python3 -c "import json,sys; procs=[p for p in json.load(sys.stdin) if p['name'] in ['argos-wa-daemon','argos-tg-bot']]; [print(p['name'], p['pm2_env']['restart_time'], p['pm2_env']['status']) for p in procs]"
```
Atteso: argos-wa-daemon restart_time=50, argos-tg-bot online.

**STEP 2 — BACKUP su iMac:**
```bash
RELEASE="~/Documents/app-antigravity-auto/releases/20260527_083951/wa-intelligence"
ROOT="~/Documents/app-antigravity-auto/wa-intelligence"
ssh gianlucadistasi@192.168.1.2 "cp ${RELEASE}/telegram-handler.py ${RELEASE}/telegram-handler.py.bak-pre-s238 && cp ${ROOT}/telegram-handler.py ${ROOT}/telegram-handler.py.bak-pre-s238 && ls -la ${RELEASE}/telegram-handler.py.bak-pre-s238 ${ROOT}/telegram-handler.py.bak-pre-s238"
```

**STEP 3 — COPIA file su entrambi i path:**
```bash
scp /Users/macbook/Documents/combaretrovamiauto-enterprise/wa-intelligence/telegram-handler.py gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/releases/20260527_083951/wa-intelligence/telegram-handler.py
scp /Users/macbook/Documents/combaretrovamiauto-enterprise/wa-intelligence/telegram-handler.py gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/wa-intelligence/telegram-handler.py
```

**STEP 4 — VERIFICA MD5 (i 3 hash devono essere identici):**
```bash
echo "LOCAL: aa1716b8eff984704923e3893e8754fb"
ssh gianlucadistasi@192.168.1.2 "md5 ~/Documents/app-antigravity-auto/releases/20260527_083951/wa-intelligence/telegram-handler.py && md5 ~/Documents/app-antigravity-auto/wa-intelligence/telegram-handler.py"
```

**STEP 5 — PY_COMPILE REMOTO (Python 3.9):**
```bash
ssh gianlucadistasi@192.168.1.2 "python3 -m py_compile ~/Documents/app-antigravity-auto/releases/20260527_083951/wa-intelligence/telegram-handler.py && python3 -m py_compile ~/Documents/app-antigravity-auto/wa-intelligence/telegram-handler.py && echo OK"
```
Deve stampare solo `OK`. Se fallisce → STOP, ripristina dai .bak.

**STEP 6 — RESTART SOLO argos-tg-bot (NON toccare argos-wa-daemon):**
```bash
ssh gianlucadistasi@192.168.1.2 "~/.npm-global/bin/pm2 restart argos-tg-bot"
```

**STEP 7 — POST-VERIFICA (attendi ~5s):**
```bash
sleep 5 && ssh gianlucadistasi@192.168.1.2 "~/.npm-global/bin/pm2 jlist" | python3 -c "import json,sys; procs=[p for p in json.load(sys.stdin) if p['name'] in ['argos-wa-daemon','argos-tg-bot']]; [print(p['name'], p['pm2_env']['restart_time'], p['pm2_env']['status']) for p in procs]"
```
```bash
ssh gianlucadistasi@192.168.1.2 "tail -30 /tmp/argos-tg-bot-out.log"
```
Verificare: tg-bot online+stabile, nessun traceback/ImportError, wa-daemon restart_time ancora 50.

### Rollback se serve
```bash
ssh gianlucadistasi@192.168.1.2 "cp ~/Documents/app-antigravity-auto/releases/20260527_083951/wa-intelligence/telegram-handler.py.bak-pre-s238 ~/Documents/app-antigravity-auto/releases/20260527_083951/wa-intelligence/telegram-handler.py && cp ~/Documents/app-antigravity-auto/wa-intelligence/telegram-handler.py.bak-pre-s238 ~/Documents/app-antigravity-auto/wa-intelligence/telegram-handler.py && ~/.npm-global/bin/pm2 restart argos-tg-bot"
```

## Ultimi 5 commit
```
d05b950 auto-close session dc7ed4f7-fb71-440a-95c7-bdaf66bfb1d3 @ 2026-06-04T11:30:51Z
c9f2d53 docs(S237c): gate runtime → 🔄 callback OK ma send HTTP 400 Markdown, fix-spec S238
aae273a auto-close session dc7ed4f7-fb71-440a-95c7-bdaf66bfb1d3 @ 2026-06-04T11:12:05Z
bc9e76c fix(S237b): 3° bottone 🔄 Rigenera nelle notifiche PUSH (response-analyzer.py)
93ef283 fix(S237b): add Rigenera button to response-analyzer.py HITL keyboard
```
