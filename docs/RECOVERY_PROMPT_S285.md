MANDATO: BUILD
# RECOVERY_PROMPT_S285 — [A1] cont., invio E2E 6-7 (artefatto già generato in S284)

Lancia con `ARGOS_HARNESS_UNLOCK=1`. Sessione DEDICATA a [A1] (anello E2E 6-7).
Routing: STATE.md → docs/ROADMAP.md → docs/briefs/BRIEF_A_e2e_67_testfounder.md. In conflitto vince STATE/ROADMAP.

## PRIMA AZIONE (invariante)
`ssh gianlucadistasi@192.168.1.2 'curl -s localhost:9191/status'` → atteso `"wa_status": "connected"` + `is_business_hours:true`.
Se no → [A0] wa-daemon-ops. SOLO TEST_FOUNDER 393314928901, mai dealer reale. Mai domenica (giorno OFF Luke).

## FATTO in S284 (verde, NON ripetere)
- [A0] daemon `connected` verificato (curl letterale).
- Artefatto reale UNICO generato su scrape AS24 BMW Serie 3:
  - PDF degradato: `dossiers/ARGOS_BMW_Serie 3_2022_Concessionaria_Test_Azzurra_20260620_163650.pdf`
    (94 listing → 5 candidati tutti NO-VERDICT thin-pool, 0 REJECT, flag degradato scattato; banda+margine soppressi).
  - cold Day-1: `/tmp/s284_cold_day1.txt` (ephemeral — rigenerabile: `generate_cold_day1(['BMW','Mercedes'],'AutoScout24','...')`).
- Checklist BRIEF_A 7 punti: **1-6 VERDE** letti sul render reale (pypdf + Read). Punto 7 = invio, pending.
- Checkpoint giudice composto: `/tmp/s284_giudice_checkpoint.md` + report completo `/tmp/s284_report_completo.md` (entrambi /tmp, ephemeral).

## VERDETTO FASE 0 (verificato su disco fine-S284 — giudice esterno: NO-GO finché non corretto)
Template Day-1 (G2) contiene claim falsa: «i concessionari con cui lavoriamo parlano di cifre interessanti» — ma ARGOS
ha 0 dealer reali (competitors.md "zero track record"). FASE 0 ha accertato:
- **La claim è su DUE righe, non una**: `wa-intelligence/templates.py:23` E `:57` (due varianti di template), verbatim
  identiche. La FASE 1 deve correggere ENTRAMBE, sennò una variante propaga ancora la claim.
- `generate_cold_day1` → `fill_template` = str-format **offline zero-LLM** → rigenerazione Day-1 deterministica. OK.
- **PDF S284 esiste** (`dossiers/ARGOS_BMW_Serie 3_2022_..._163650.pdf`, 2.29MB): da FISSARE, NON rigenerare (scrape live
  = veicolo diverso = checkpoint rotto).
- Git fine-S284: HEAD=`e2a6d05` (commit handoff S285 di S284, non desync esterno), branch ok, tree pulito (solo breadcrumb).
- **Candidato ADOTTABILE con 1 correzione**: il passo-1 dica "righe 23 E 57", non "la riga".

## FASE 1 (sessione dedicata, budget pieno — NON eseguita in S284 per context >60%)
1. CORREGGI templates.py righe 23 E 57: rimuovi la rivendicazione di clientela inesistente → condizionale onesto
   (es. "su questo segmento il margine può essere interessante, dipende dal veicolo"). Nessun'altra modifica. Mostra diff.
2. RIGENERA SOLO il Day-1 (offline). NON rigenerare il PDF (resta ..._163650.pdf fissato). Mostra output verbatim.
3. RI-VERIFICA i 7 punti BRIEF_A su [PDF S284 fissato + Day-1 nuovo], leggendo il render. Atteso: claim falsa sparita,
   punto 7 resta PENDING. Poi prepara packet RE-CHECKPOINT (7 punti + Day-1 nuovo + testo PDF + diff). NON inviare.

## POI (BLOCKED-ON-Luke fisico + giudice esterno)
1. [LUKE] incolla packet re-checkpoint a Claude AI web → GO/NO-GO. Invio SOLO con GO.
3. [SE GO] invio Day-1 a TEST_FOUNDER → scatta **Gate-E** (classe `outreach_real`: BLOCCA → packet `pending_review/<slug>.md`).
   [LUKE] incolla verdetto giudice + `! python3 .harness/gate_e.py approve <slug>` (token one-shot, CC non auto-approva).
   Gate-E che NON scatta = bug del breaker (checklist punto 7).
4. [DONE-CONDITION A1] = 7 punti verde sull'artefatto reale + invio passato per Gate-E → solo allora anello 6-7 = VERIFIED.
   Verde o handoff strutturato, mai PARTIAL (vincolo #6).

## Invarianti
- Single-writer: solo [A1] scrive su branch s210/audit-master-plan.
- Push bloccato (scrub history [F], filter-repo non fatto). NON forzare il push. Commit solo locale, file nominati (mai `git add -A`).
- Base-mercato gate [D] ancora aperto: questo E2E prova MECCANICA+RENDER, NON i numeri. Dossier oggi degradato/NO-VERDICT.
- ops iMac ssh: pm2 in `~/.npm-global/bin`, node v20 in `~/.nvm/versions/node/v20.11.0/bin`.
