# S163 sanitizer_colab — LaMa MVP

Notebook Colab standalone per testare la qualita' di **LaMa via IOPaint** sulla rimozione di watermark dealer + targhe dalle foto auto ARGOS.

## Path A (MVP minimo) — scope corrente
- Modello: LaMa (MIT, ~200MB) via `iopaint` pip package
- Detection: **mask manuale** annotata da Luke nella web UI integrata
- Sample: 3 foto (watermark, targa, entrambi)
- Output: GO/NO-GO sulla qualita' inpainting

Detection automatica (Florence-2 / Qwen2-VL / YOLO targhe) e' deferred S164 — solo se Path A chiude verde.

## Come usare

1. Apri `s163_lama_mvp.ipynb` su [Google Colab](https://colab.research.google.com/)
2. Runtime -> Change runtime type -> **T4 GPU**
3. Pannello Secrets (icona chiave a sx) -> aggiungi `NGROK_AUTHTOKEN` (token gia' in `~/.claude/.env.free-gpu` su MacBook)
4. Run all (Ctrl+F9)
5. Aspetta ~3min per install + ~30-60s per download LaMa
6. Cella 5 stampa `IOPAINT WEB UI: https://xxxxx.ngrok-free.app` -> apri nel browser
7. Carica foto, pennello sulle aree da rimuovere, click `Erase`, scarica risultato
8. Salva input + output in `outputs/` per audit

## Criteri decisione

- **GO** -> S164: aggiungi detection automatica come pipeline upstream
- **NO-GO** -> S163-bis: switch modello a BrushNet o PowerPaint v2 (stesso IOPaint, `--model=brushnet`)

## File
- `s163_lama_mvp.ipynb` — notebook Colab pronto
- `inputs/` — (vuota) 3 foto sample da analizzare
- `outputs/` — (vuota) risultati sanitized + audit

## Note tecniche

- IOPaint 1.6.0 (verificato PyPI marzo 2025, web UI integrata, LaMa auto-download)
- Colab T4 free: 12h idle disconnect, accettabile per MVP
- Costo: €0 (Colab + IOPaint MIT + ngrok free tier)
- No estensione skill `~/.claude/skills/free-gpu-api/` — vedi `memory/s163_preflight_blocked.md` per motivazione (skill scaffold non supporta workflow image+mask->image)
