# STATE — MIGRAZIONE-V2
HEAD ATTESO: d3021d714c07e82367eeb0e5152e20583d245efd
DATA: 2026-08-01
## Stato pipeline
E2E TEST_FOUNDER: Day1 + PDF recapitati 31/07 (ring #1 18/20 PASS, check_cmd null = machine-owned).
Debito: `timeout` GNU assente su macOS -> pipeline scrape->CoVe->PDF non eseguita. Fix: brew coreutils.
Daemon WA (iMac :9191): finestra lun-sab 08:00-19:59 Europe/Rome, 20 invii/giorno.
503 = wa_not_connected (wa-daemon.js:1215). Business-hours = 403, NON 503.
Nessun heartbeat, nessun auto-reconnect: wa_status va 'stale' solo al primo invio fallito.
## Rings
#1 UNVERIFIED (funziona, check_cmd null) · #2 PASS · #9A PASS · #9B UNVERIFIED (mai esercitato)
#5 PASS · #6-7 UNVERIFIED (live 01/07, check_cmd null by-design) · #8 BLOCKED sign_url · #BM PASS
## Gate [A] RESPINTO dal founder 31/07
Day1 a template con falsa personalizzazione. Richiesta vera: second brain per dealer da fonti
lecite -> messaggio in sintonia. second_brain.py consegnato da Sol, revisione CC non chiusa.
## Unita' residue
-> docs/judge/ROADMAP-PRODUZIONE.md
