════════════════════════════════════════════════════════════
MANDATO — ARGOS — HARVESTER DEALER FB/IG ITALIA (pilota 3 province)
(sessione WRITE-CODE fresca; aprire <50% context)
════════════════════════════════════════════════════════════

TESTATA
- accept-edits OFF. Alle richieste di edit rispondere sempre '1'
  (yes, questa volta) — MAI 'allow all edits this session'.
- G-ZEROCOST: nessun acquisto/abbonamento. Account/tool gratuiti = IL percorso.
- G-ENTERPRISE-GRADE: provenienza-URL per riga, fonte-B indipendente per
  ogni candidato PROMOSSO, ogni claim tracciata. Niente numeri inventati.
- PUSH VIETATO (S278): nessun push, nessun hook di push creato.
- GATE E: file source-of-truth (MEMORY.md, DECISIONS.md, PLAN.md, *.db,
  CLAUDE.md) sono protetti → NON ritentare se l'hook blocca; serve approve
  esterno. NB pendente: index memory FB bloccato = packet
  overwrite_sot-dc04f63aaf (approva con
  `! python3 .harness/gate_e.py approve overwrite_sot-dc04f63aaf` se lo vuoi).
- REGOLA-SUBAGENT: ogni numero da subagent è CLAIM → la madre riconta da
  disco prima dell'uso.

CONTESTO GIÀ VERIFICATO (sessione precedente — NON ri-litigare, solo riusare)
- AUTH FB RISOLTA: venv `~/.argos-fb-venv` ha `browser_cookie3`.
  `browser_cookie3.chrome(domain_name='facebook.com')` decritta i cookie di
  sessione dal profilo Chrome **Default** (gianlucanewtech@gmail.com) su Big
  Sur — VERIFICATO (c_user/xs/datr, 9 cookie). Iniettare in Playwright via
  `context.add_cookies(...)` (xs è HttpOnly → solo da profilo, non da console).
- WebFetch NON basta su FB (JS-render → solo il nome). Playwright OBBLIGATORIO.
  Vista pubblica → login-wall dopo 1-2 post; da loggato il wall non scatta.
- Dettaglio riusabile: memory `reference_fb_harvest_auth.md`.

TARGET (fonte autoritativa docs/ROADMAP.md S292 — NON i valori inline SUPERSEDED)
- LEAD DA TROVARE = micro-dealer <20 auto, family-business proprietario-
  decisore, TUTTA ITALIA.
- FILTRO AUTO (qualifica se il dealer è in-target): premium SUV/executive
  €25k-90k, anni 2018-2023, diesel/benzina/mild-hybrid (NO BEV).
  Tier A: Macan/Cayenne, RR Sport/Velar/Evoque, Q7/Q8, X5, GLE/GLC (allest.alti).
  Tier B: A6, Serie 5, Classe E, Panamera.
  ESCLUSI: compatti (A3/Serie1/ClasseA/Q3/A1), esotico (Ferrari/Lambo/
  Maserati/McLaren), lusso-BEV.

FASE 0 — REALITY-CHECK (output comando VERBATIM, mai prosa)
0.1 git status -sb (prima riga)
0.2 Riprova auth: `~/.argos-fb-venv/bin/python -c "import browser_cookie3 as
    bc; print(len(list(bc.chrome(domain_name='facebook.com'))))"` → atteso >=1.
    Se 0 → cookie scaduti: STOP, chiedi a Luke di riaprire FB nel profilo
    Default, non "aggiustare" in corsa.
0.3 Elencare i path che si toccheranno. Confermare che
    data/recon/dealers_fb/ NON esiste ancora (o è vuoto).

CLAUSOLA DISCORDANZA
Se l'auth-probe 0.2 torna 0, o Playwright non naviga loggato → STOP,
riportare VERBATIM, non procedere.

────────────────────────────────────────────────────────────
UNITÀ 1 — HARVESTER + PILOTA 3 PROVINCE  (atomica, committabile)
────────────────────────────────────────────────────────────
Scrivere modulo Playwright (Python, venv ~/.argos-fb-venv) che:
  a) carica cookie via browser_cookie3 → context.add_cookies;
  b) per ciascuna delle 3 PROVINCE PILOTA (Milano, Roma, Napoli — alta
     densità, dichiarate a verbale), interroga FB
     /search/pages/?q="concessionaria auto <provincia>" (+ varianti:
     "auto usate", "automobili"), cap-scroll BASSO;
  c) per ogni Pagina candidata estrae, CON URL-provenienza per riga:
     nome · categoria FB · città/provincia · telefono (bio + commenti
     "prezzo?/recapito") · sito · N. auto Tier-A/B osservate nei post
     (segnale-stock premium);
  d) QUALIFICA in-target = categoria concessionaria ∧ >=1 auto nel filtro
     S292 (€25-90k, 2018-2023, no BEV, Tier A/B). Esito riga:
     IN-TARGET / FUORI-TARGET / INCERTA.

BACKUP RULE 1d: output in file NUOVO per provincia, MAI overwrite. Dedup
contro data/recon/ esistente (mandatari/*.json) su telefono+nome
normalizzati — non ri-emettere lead già noti.
OUTPUT: data/recon/dealers_fb/<provincia>.json (path versionato).

Fonte-B per-riga solo sui candidati IN-TARGET (≠ FB): P.IVA/ragione
sociale corrente via registro camerale o PagineGialle. ufficiocamerale.it
ESCLUSO in ogni forma.

SOGLIA PROMOZIONE: se >=1 provincia produce >=3 lead IN-TARGET con telefono
→ PILOTA PROMOSSO (il canale FB funziona su scala nazionale). Sotto → resta
CANDIDATI, diagnosi onesta del perché (login-wall? categoria assente?
segmento raro su FB?), nessun falso-verde.

FASE CHIUSURA U1: git add dei soli file toccati dichiarati + commit d'unità
+ git status finale pulito salvo effimeri dichiarati. Fatto terminale = hash.
Se PROMOSSO e context <=60% → prosegui U2. Se CANDIDATI o context >60% →
CHIUDI qui col verdetto.

────────────────────────────────────────────────────────────
UNITÀ 2 — NOTA COPERTURA + PROIEZIONE ROLLOUT  (solo se U1 = PROMOSSO)
────────────────────────────────────────────────────────────
Tabella per Milano/Roma/Napoli: Pagine trovate · IN-TARGET · %telefono ·
distribuzione Tier-A/B · COPERTURA vs universo concessionari provinciale
CON FONTE (densità PagineGialle/Google Maps a verbale). La proiezione
rollout ~100 province entra SOLO con la riga COPERTURA dentro (senza =
estrapolazione non qualificata, vietata).
OUTPUT: docs/briefs/SINTESI_DEALER_FB.md (path versionato).
FASE CHIUSURA U2: git add + commit d'unità + git status pulito. Hash.

════════════════════════════════════════════════════════════
BLOCCO-CHIUSURA — INCOLLA-AL-GIUDICE (campi fissi, VERBATIM)
════════════════════════════════════════════════════════════
GIT: branch · commit U1 (hash) · commit U2 (hash, se eseguita) ·
     PUSH STATUS VERBATIM (git status -sb) · push NON eseguito
CHECK-HOOK VERBATIM: core.hooksPath · esito pre-commit · Gate E toccato?
AUTH-PROBE 0.2 VERBATIM
BACKUP 1d: file nuovi creati (path), zero overwrite
PROVE GREZZE (riconteggio MADRE, non subagent):
  per provincia: Pagine trovate · IN-TARGET/FUORI/INCERTA · telefoni ·
  fonte-B sui promossi · verdetto PROMOSSO/CANDIDATI
SINTESI (se U2): la tabella con riga COPERTURA
NOTE METODO / discordanze incontrate
CONTEXT % alla chiusura
════════════════════════════════════════════════════════════
