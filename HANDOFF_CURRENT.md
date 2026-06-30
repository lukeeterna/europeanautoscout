# HANDOFF — 9cd35bf2-00be-44f5-8c26-8f3d5daa9f93 — 2026-06-30 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE (mutazioni su iMac PRODUZIONE via SSH; ZERO file repo modificati da me)
- Mandato: OPERATIVO — completare rotazione GROQ + deploy [E] trasparenza (Azzurra) su daemon iMac. Niente outreach.
- Esito: **GROQ ruotato e VERIFICATO live**. Restart ha innescato un **incidente ABI better-sqlite3** (daemon crash-loop) → **recuperato** via `npm rebuild`. **[E] RINVIATO** (context budget + post-incidente; LIVE confermato vecchio, deploy non eseguito).

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD d606725 2026-06-30 · working-tree dirty: `.claude/NEXT_SESSION_PROMPT.md` (non mio — breadcrumb auto-hook).
- commit di questa sessione (miei): **nessuno** (lavoro tutto su iMac, fuori dal repo).

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md, verbatim — non re-narrare)
| 1 | invio Day1 WA | UNVERIFIED | full |
| 2 | classifier intent (AMBRA) | VERIFIED | smoke |
| 9A | approve -> send | VERIFIED | smoke |
| 9B | reject -> abort | UNVERIFIED | full |
| 5 | generazione dossier PDF | VERIFIED | smoke |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED | full |
| 8 | contract -> sign_url | BLOCKED (sign_url firmato dal dealer reale — fatto esterno) |

### GATE A DEALER REALE
[A] daemon = **CONNECTED** (`/status` wa_status:connected, daily_sent:0, no QR; post-recovery ABI) · [E] trasparenza in PRODUZIONE = **NO, ancora vecchia** (LIVE ROOT: `templates.py` "sono Luca Ferretti" r.15/25/34/46; `response-analyzer.py` NESSUN `ARGOS_ASSISTANT`). HEAD MacBook ha il fix (Azzurra) clean — deploy [E] PENDING. · [D] base-mercato = NON affidabile (cap-truncated, S273-cont).

### FATTO QUESTA SESSIONE (verificato)
- **GROQ ruotato:** `.env` ROOT/wa-intelligence riga 9 = chiave NUOVA `gsk_ytZn…len56` (bare). Vecchia `"gsk_oRF…len58"` (quotata) revocata da Luke su console.groq.com (fatto esterno confermato). Consumer reale `response-analyzer.py:_load_dotenv()` fa force-override da `.env` (strip-quote) → chiave effettiva NUOVA verificata 2× (sed riga9 + simulazione loader). `.bak` 1d: `.env.20260630T202850Z.bak` (1076B, 0600, in ROOT/wa-intelligence). Restart mirato `argos-wa-daemon`+`argos-tg-bot --update-env`. File scratch `~/.argos_groq_new.key` **shred+rm** (assente).
- **INCIDENTE + RECOVERY:** il restart ha esposto un mismatch latente `better-sqlite3.node` NODE_MODULE_VERSION 115 (Node 20) vs Node attuale v22.14.0 (ABI 127) → `ERR_DLOPEN_FAILED` → daemon crash-loop (↺10, waiting). Il daemon girava da 7gg in RAM sotto il vecchio node → mismatch latente. Fix: `npm rebuild better-sqlite3` in ROOT/wa-intelligence (Xcode CLT presente, exit 0, ABI load OK) → `pm2 restart` → **connected, daily_sent:0, no QR**. Terza occorrenza del bug (S189/S197/ora).

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
**PART 2 [E] deploy mirato:** `.bak` 1d di ROOT/wa-intelligence/{templates.py,response-analyzer.py} → rsync MIRATO SOLO quei 2 file da HEAD MacBook → ROOT iMac (no --delete) → `pm2 restart argos-wa-daemon --update-env` (auth ROOT intatta → no QR). Falsificabile: `ssh imac grep ARGOS_ASSISTANT response-analyzer.py` = presente + `grep "sono Azzurra|sono Luca Ferretti" templates.py` = Azzurra (non Luca) + `/status` connected, daily_sent ANCORA 0. Pre-cond zero-invio: daily_sent=0, is_business_hours=false, HITL ON, coda bridge_outbound intatta. Chiude il gate produzione (2) trasparenza.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- E2E TEST_FOUNDER 393314928901 verde (anelli 1 / 6-7 / 9B UNVERIFIED) + Luke "pienamente soddisfatto" — gate a dealer reale.
- Anello 8: sign_url firmato dal dealer reale. Gate legale (a) liceità canale = CONFERMATO Luke 2026-06-16 (non più bloccante).

### BACKLOG (differito, NON prerequisito del primo invio)
- **pm2 jlist cache GROQ ancora vecchia** (`"gsk_oRF…len58`): `--update-env` non rilegge ecosystem.config.js → cosmetico (consumer force-legge .env). Allineare: `pm2 restart ecosystem.config.js --only argos-wa-daemon,argos-tg-bot --update-env` (= 1 bounce extra; non fatto per non ribaltare daemon appena recuperato).
- **better-sqlite3 ABI recidiva:** ogni deploy/rsync che ripristina `node_modules` ABI115 rompe al prossimo restart → rebuild nel deploy o pin interpreter node v20. Root = node iMac aggiornato v20→v22 senza rebuild.
- **split-brain DB:** `ARGOS_DB_PATH` (cached) → `releases/20260527_083951/dealer_network.sqlite` mentre cwd daemon = ROOT (S227). Verificare DB canonico via symlink prima di leggere.
- **sync.sh deploia nel vuoto:** daemon gira da ROOT, sync.sh tocca releases/+current → [E] via sync.sh = falso-verde. Usare rsync mirato in ROOT.
- image_sanitizer (D-32) + landing CONGELATI finché anelli E2E non risalgono.

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- **DISCORDANZA done-cond GROQ (onesta):** `pm2 jlist` mostra ancora la chiave VECCHIA in cache (pm2 non rilegge ecosystem su `--update-env`). NON è un fallimento della rotazione: il consumer `response-analyzer.py` force-legge `.env` → effettiva = nuova (verificata). `jlist` è la superficie di verifica sbagliata per questo storage. Allineamento cache = BACKLOG cosmetico.
- **Il restart "innocuo" NON era innocuo:** ha trasformato un mismatch ABI latente (7gg uptime in RAM) in un crash-loop di produzione. Lezione: ogni restart del daemon è un'azione a rischio finché il rebuild non è nel deploy.
- **[E] rinviato deliberatamente** (non dimenticato): context budget 60%+ e cautela post-incidente; nessun messaggio esce stanotte comunque (daily_sent:0, off-hours, HITL ON). Resume prompt completo in `.claude/NEXT_SESSION_PROMPT.md`.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (S292) · STATE.md §3 (gate legale/trasparenza) · memoria `reference_imac_deploy_paths.md` · memoria `s252_e2e67_blocked_deploy_authdir.md`
