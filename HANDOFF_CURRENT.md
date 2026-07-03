# HANDOFF — s210/audit-master-plan — 2026-07-03 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: FASE-A KB dominio — backup bundle→iMac, upgrade RUBRICA tier-fonti, seed frode_km da payload giudice, validate_kb.py.
- Esito: 4/4 step VERDI. Bundle su iMac + restore-test 701 = HEAD. RUBRICA tier-fonti aggiunta. frode_km 6 fatti conformi (validate exit 0). Commit 1e0d6c6.

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 1e0d6c6 2026-07-03 18:35 · working-tree dirty: .claude/NEXT_SESSION_PROMPT.md, STATE.md, state/rings.json (TUTTI dirty all'avvio da hook, NON miei — non committati)
- commit di questa sessione: 1e0d6c6 "kb: seed frode_km GRADED-BY-GIUDICE + tier-fonti RUBRICA (payload giudice 2026-07-03)" (4 file: kb/dominio/frode_km_verifica.md, kb/dominio/RUBRICA.md, validate_kb.py, .gitignore). No push (da mandato).

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md, verbatim — non re-narrare)
| # | Anello | Stato |
|---|--------|-------|
| 1 | invio Day1 WA | UNVERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED (smoke) |
| 9A | approve -> send | VERIFIED (smoke) |
| 9B | reject -> abort | UNVERIFIED |
| 5 | generazione dossier PDF | VERIFIED (smoke) |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED |
| 8 | contract -> sign_url | BLOCKED (sign_url firmato dal dealer reale — fatto esterno non raggiungibile in-sessione) |

### GATE A DEALER REALE
[A/D] state_guard.py Gate A–D = ATTIVO (S245, 11 test PASS) · [E] gate_e.py PreToolUse = ATTIVO (S247, selftest 33/33) · [LEGALE/PERSONA] = BLOCKED-ON-LUKE (parere legale base giuridica primo contatto + 2-path) — blocca invio a dealer REALE, non la E2E test.

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
6-7 E2E: gate HITL dossier su iMac (fastapi presente) + invio PDF a TEST_FOUNDER 393314928901 → prima azione che innesca Gate E (classe outreach_real). Fatto terminale = Luke conferma ricezione PDF sulla SIM.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Anello 8: sign_url firmato dal dealer reale (HITL fisico Luke o terzo).
- Gate legale/persona: parere legale sulla base giuridica del primo contatto (azione Luke).

### BACKLOG (differito, NON prerequisito del primo invio)
- Seed restanti stub KB dominio (allestimenti_valore, iva_margine_dealer, prezzo_arbitraggio_eu) — "nessun fatto", in attesa payload gradato dal giudice.
- Base-mercato BMW Serie3 NON affidabile (cap-truncated, S273-cont): pool valido richiede completezza DEEP_PAGES≥80 fino a pagina vuota + purezza geo==IT. Blocca dossier REALE (non la E2E test).

### NOTE PER IL GIUDICE (INCOLLA-AL-GIUDICE)
- Discordanza payload↔RUBRICA risolta con adattamento-FORMA (mai numeri/fonti), documentata dentro frode_km_verifica.md:
  (a) DATA ISO = giorno esatto dove il payload lo dà (Belgio 2006-12-01, Italia 2018-06-01); altrimenti FLOOR del periodo (mar 2025→2025-03-01, 2025→2025-01-01, dic 2025→2025-12-01) — periodo reale resta in FONTE.
  (b) VERIFICA = metodo del payload ("report VIN") + verbo azionabile aggiunto per il gate.
  (c) 4 righe qualitative senza numero (RDW Olanda, Histovec Francia, Germania, Implicazione ARGOS) tenute come note ">" (non statistiche, non passano il gate come fatti) → NON contano tra i "6 fatti conformi".
- Giudizio da confermare: i 4 fatti "Dimensione fenomeno IT" sono TUTTI [T3] carVertical (fonte unica interessata). DISCLAIMER nel file. Prima di copy pubblico serve corroborazione T1/T2 indipendente (Altroconsumo/ACI/ADAC) NON ancora trovata.
- Belgio dato -97% (2016): da ri-corroborare su fonte Car-Pass corrente prima dell'uso pubblico (nota già nella riga-fatto).
- Extra autorizzato (check leggero): aggiunto a validate_kb.py check TIER a fine riga-fatto ([T1]/[T2]/[T3]), falsifier verificato. Backup RUBRICA.md.bak-20260703 + validate_kb.py.bak-20260703 (gitignored via *.bak-*), NON committati.
- Dirty all'avvio (STATE.md, state/rings.json, .claude/NEXT_SESSION_PROMPT.md) = da hook auto-close, non toccati.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md · docs/briefs/ · STATE.md (S278) · kb/dominio/RUBRICA.md (standard formato KB)
