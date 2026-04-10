# S112 — Soft Launch Resume + TG Alert Setup

## Contesto

S111 ha completato e deployato il sanitizer v3 su iMac con PaddleOCR 3.x.
Il soft launch (Fasi 0-4 da S110) era bloccato dal sanitizer ed ora puo' procedere.

## Prerequisiti

- iMac ONLINE, WA CONNECTED
- Sanitizer v3 deployato e testato (KORDICK 2/2 OK)
- PM2 SSH: `export PATH=$HOME/.npm-global/bin:/usr/local/bin:$PATH`
- Leggere: `memory/MEMORY.md` sezione S111

---

## FASE 0 — Setup TG alerts per sanitizer

**Priorita':** Alta (il sanitizer manda alert ma TG_BOT_TOKEN non e' settato)

1. Verificare TG_BOT_TOKEN e TG_CHAT_ID nel .env su iMac
2. Se non presenti, aggiungerli (valori dal bot TG gia' attivo)
3. Testare alert con una foto che ha testo residuo

---

## FASE 1 — Deploy on_demand_runner.py su iMac

Gap noto da S110: `tools/on_demand_runner.py` non deployato.
```
rsync -avz tools/on_demand_runner.py gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/tools/
```

---

## FASE 2 — Test WA reale su TEST_FOUNDER

Unico test mancante da S110. Business hours 8-20.
```
python3 tools/on_demand_runner.py --marca BMW --budget 40000 --dealer "TEST_FOUNDER"
```

---

## FASE 3 — Recovery Car Plus AV

Dealer REALE, ha risposto con FOTO 2026-04-07, poi silenzio.
- dealer_id: TIER0_AV_001
- Stato: ENGAGED
- Azione: reply MANUALE da telefono (non automatica)
- Messaggio pronto in `research/s108_day1_messages_top5.md`

---

## FASE 4 — Import 13 dealer enriched + Soft Launch

1. Import 13 dealer da `research/s108_enrichment_13_dealer_validati.json` nel DB conversations
2. Soft launch 1 dealer: Stefano Auto FG (RELAZIONALE, 4.98/5)
3. Se OK → outreach scaglionato 1/giorno

Dettagli in: `prompts/s110_soft_launch_outreach.md`

---

## Note tecniche sanitizer v3 (per reference)

- PaddleOCR 3.x: `ocr.predict()` (non `ocr.ocr()`)
- Init: `PP-OCRv5_mobile_det` + `en_PP-OCRv5_mobile_rec`
- `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` obbligatorio
- Post-verify solo se has_mask (salta se solo crop banner)
- Timing: 20s/foto dopo model init, ~30s model init one-time
