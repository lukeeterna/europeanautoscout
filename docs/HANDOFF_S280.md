# HANDOFF_S280 — INDICE (NON SoT)

FONTE DI VERITA' = STATE.md + docs/ROADMAP.md + git su disco. Questo handoff e' un INDICE di dove
guardare, non una fonte. In conflitto, vince STATE.md/ROADMAP, non questo file.

## Stato anelli (da state/rings.json, non a memoria)
- 2 (classifier AMBRA) PASS-smoke · 9A (approve->send) PASS-smoke · 5 (dossier PDF) PASS-smoke
- 1 (Day1 WA) UNVERIFIED · 9B (reject->abort) UNVERIFIED · 6-7 (HITL dossier->invio) UNVERIFIED
- 8 (contract->sign_url) BLOCKED (fatto esterno: firma dealer reale, Rule 1b)

## Prossima azione = [A0] wa-daemon-ops
WA daemon iMac:9191 = `wa_status: initializing` / `qr_available: false` (verificato S280) = client WA
NON connesso, non puo' spedire. Portarlo initializing->connected (area S252: QR re-scan, Luke fisico
sulla SIM, in orario lavorativo) PRIMA di [A1] E2E 6-7. Brief: docs/briefs/BRIEF_A_e2e_67_testfounder.md.

## Gate aperti
- Token: ✅ FATTO S281 — OpenRouter + bot Telegram APPLICATI su iMac wa-intelligence/.env (symlink unico,
  no split-brain), restart argos-tg-bot+argos-wa-daemon (↺1, online). Verifica: getMe ok=True
  username=Argosautomotivebot + OpenRouter /auth/key http=200. Scratch cancellati. Backup .env.bak-S281-*.
- Push: bloccato dal pre-push (45 commit avanti origin + storico-secret S220, scan per PATTERN non
  liveness). Sblocco reale = item [F] filter-repo, sessione dedicata.
- Memory-index: riga puntatore in MEMORY.md gated da Gate-E (packet overwrite_sot-dc04f63aaf). Il file
  feedback (feedback_A_before_B_e2e_gate_priority.md) e' gia' scritto; manca solo l'indice.

## Le 2 azioni Luke
1. OpenRouter sk-or-v1-...2f13 = RUOTATO (fatto).
2. Account FB di TEST sacrificabile = da creare PRIMA del fetch-test del modulo FB (cookie c_user+xs
   in .env, fuori repo). Repo scelta = MasuRii/FBScrapeIdeas (vedi data/research/repo_selection.md).
