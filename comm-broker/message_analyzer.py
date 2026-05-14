"""ARGOS comm-broker message analyzer — D-22 F2 implementation.

1-call LLM combinata via src/llm_cascade.py (Groq llama-3.3-70b-versatile primary,
5-level fallback). Single message → JSON structured output:

  - intent: 8-way classification
  - sentiment: positive/neutral/negative/frustrated
  - scam_flag: bool + reason
  - translation: cross-lang IT↔EN per audit
  - summary: 1-line per dashboard

Vincoli (D-22 F2 verified S167 Thread 4):
- Groq free tier 30 RPM / 6k TPM / 1000 RPD = ~10 deal attivi/giorno cap
- 1-call combinata = ~70% riduzione vs 4 chiamate separate
- Cache deterministica per identical message (anti double-call)
- JSON parsing robust (markdown wrapped, hallucinated fields, missing keys)

Integration:
- comm-broker/wa_bridge.py ingest_inbound → analyze() → mark_processed(intent, sentiment)
- Output salvato in bridge_inbound (intent, sentiment columns)
- Scam flag → alert founder via Telegram (TBD S168 via telegram-handler.py)
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

# Importa LLMCascade da ARGOS src (parent dir relative)
_ARGOS_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_ARGOS_SRC))
from llm_cascade import LLMCascade, get_cascade, AllProvidersDown


logger = logging.getLogger("argos.message_analyzer")


# ── Intent taxonomy (D-22 F2 spec) ──────────────────────────────────────────

INTENTS = [
    "greeting",          # saluto iniziale, presentazione
    "offer",             # interesse, richiesta auto specifica
    "negotiation",       # counter-offer, prezzo, sconto
    "docs_request",      # richiesta documenti, EUROCOC, libretto
    "payment",           # proposta/conferma modalità pagamento
    "delivery",          # trasporto, tempi consegna, pickup
    "objection",         # obiezione, dubbi, problemi
    "scam",              # red flag truffa detected
]

SENTIMENTS = ["positive", "neutral", "negative", "frustrated"]


# ── System prompt (verified anti-pattern: no chain-of-thought leak) ─────────

SYSTEM_PROMPT = """Sei un classificatore esperto di conversazioni B2B automotive Italia-EU per ARGOS, intermediario tra dealer italiani e venditori europei.

Riceverai 1 messaggio. Produrrai 1 oggetto JSON valido (no markdown wrap, no testo extra) con questi 5 campi:

{
  "intent": "<one of: greeting|offer|negotiation|docs_request|payment|delivery|objection|scam>",
  "sentiment": "<one of: positive|neutral|negative|frustrated>",
  "scam_flag": <true|false>,
  "scam_reason": "<short string if scam_flag=true else empty string>",
  "translation": "<traduzione del messaggio nella lingua opposta (IT→EN o EN→IT)>",
  "summary": "<riepilogo 1 frase max 80 char>"
}

Regole intent:
- greeting: saluto, presentazione iniziale, "buongiorno", "ciao"
- offer: interesse genuino, "mi interessa", "mandami dossier", marca/modello citata
- negotiation: contro-offerta, "posso a X euro?", "fai sconto?"
- docs_request: chiede documenti specifici (EUROCOC, libretto, foto VIN, ispezione)
- payment: discute modalità pagamento, "bonifico", "contanti", "cash a consegna"
- delivery: trasporto, "quando arriva", "dove ritiro", "Macingo"
- objection: "non mi convince", "troppo caro", "ci penso", dubbi
- scam: red flag - anticipo richiesto non standard, "Western Union", VIN diverso da foto, fiduciario sospetto, urgenza forzata, dati incoerenti, payment off-platform

Regole sentiment:
- frustrated solo se aperto contrasto: "non risponde mai", "scocciato", linguaggio forte
- negative: scettico, dubbioso ma educato
- neutral: factuale, no emotion
- positive: entusiasta, conferma, "perfetto"

Output SOLO il JSON. No spiegazioni. No markdown."""


# ── Data types ──────────────────────────────────────────────────────────────

@dataclass
class AnalysisResult:
    intent: str
    sentiment: str
    scam_flag: bool
    scam_reason: str
    translation: str
    summary: str
    provider: str          # quale provider della cascade ha risposto
    tokens_used: int
    cached: bool = False
    raw_response: str = ""  # per debug/audit, salvato in cache solo se needed


# ── Cache layer (deterministico per msg identico) ───────────────────────────

CACHE_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyzer_cache (
    msg_hash       TEXT PRIMARY KEY,  -- sha256(source_lang|body|target_lang)
    intent         TEXT NOT NULL,
    sentiment      TEXT NOT NULL,
    scam_flag      INTEGER NOT NULL,
    scam_reason    TEXT,
    translation    TEXT,
    summary        TEXT,
    provider       TEXT NOT NULL,
    tokens_used    INTEGER NOT NULL,
    created_ts     INTEGER NOT NULL
);
"""


def _msg_hash(body: str, source_lang: str, target_lang: str) -> str:
    return hashlib.sha256(f"{source_lang}|{body}|{target_lang}".encode("utf-8")).hexdigest()


def _cache_lookup(db_path: Path, key: str) -> Optional[AnalysisResult]:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(CACHE_SCHEMA)
        cur = conn.execute(
            """SELECT intent, sentiment, scam_flag, scam_reason, translation, summary,
                      provider, tokens_used
               FROM analyzer_cache WHERE msg_hash = ?""",
            (key,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return AnalysisResult(
            intent=row[0], sentiment=row[1], scam_flag=bool(row[2]),
            scam_reason=row[3] or "", translation=row[4] or "",
            summary=row[5] or "", provider=row[6], tokens_used=row[7],
            cached=True,
        )
    finally:
        conn.close()


def _cache_store(db_path: Path, key: str, r: AnalysisResult) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(CACHE_SCHEMA)
        conn.execute(
            """INSERT INTO analyzer_cache
               (msg_hash, intent, sentiment, scam_flag, scam_reason, translation,
                summary, provider, tokens_used, created_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(msg_hash) DO NOTHING""",
            (key, r.intent, r.sentiment, int(r.scam_flag), r.scam_reason,
             r.translation, r.summary, r.provider, r.tokens_used, int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()


# ── JSON parser robust (anti-hallucination) ─────────────────────────────────

def _parse_response(text: str) -> dict:
    """Parse LLM output. Strip markdown fences, extract first {…} block."""
    # Strip ```json ... ``` o ``` ... ``` wrapper
    text = text.strip()
    if text.startswith("```"):
        # remove first fence line + last fence
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Find first balanced JSON object (in case LLM wraps with extra text)
    start = text.find("{")
    if start == -1:
        raise ValueError(f"no JSON object found in response: {text[:200]}")
    depth = 0
    end = -1
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        raise ValueError(f"unbalanced JSON in response: {text[:200]}")

    blob = text[start:end]
    return json.loads(blob)


def _normalize(parsed: dict) -> dict:
    """Normalize parsed JSON: enforce schema, fill missing fields, validate enums."""
    intent = (parsed.get("intent") or "").lower().strip()
    if intent not in INTENTS:
        # Fallback heuristic: if unknown intent, default to "objection" (safe — triggers HITL)
        logger.warning(f"unknown intent '{intent}', defaulting to 'objection'")
        intent = "objection"

    sentiment = (parsed.get("sentiment") or "neutral").lower().strip()
    if sentiment not in SENTIMENTS:
        sentiment = "neutral"

    scam_flag = bool(parsed.get("scam_flag", False))
    scam_reason = str(parsed.get("scam_reason", "")).strip()
    translation = str(parsed.get("translation", "")).strip()
    summary = str(parsed.get("summary", "")).strip()[:200]

    return {
        "intent": intent,
        "sentiment": sentiment,
        "scam_flag": scam_flag,
        "scam_reason": scam_reason,
        "translation": translation,
        "summary": summary,
    }


# ── Main analyzer class ─────────────────────────────────────────────────────

class MessageAnalyzer:
    """Single-call combined LLM analysis per messaggio WA."""

    def __init__(self, cache_db: str | Path = "/tmp/argos-analyzer-cache.sqlite",
                 cascade: Optional[LLMCascade] = None,
                 max_tokens: int = 400):
        self.cache_db = Path(cache_db)
        self.cascade = cascade or get_cascade()
        self.max_tokens = max_tokens

    def analyze(self, body: str, source_lang: str = "it",
                target_lang: str = "en", use_cache: bool = True) -> AnalysisResult:
        """Analizza singolo messaggio. Returns AnalysisResult.

        source_lang: lingua del body (it | en | de)
        target_lang: lingua per translation field (default opposite di source)
        """
        key = _msg_hash(body, source_lang, target_lang)

        # Cache check
        if use_cache:
            cached = _cache_lookup(self.cache_db, key)
            if cached:
                logger.debug(f"cache hit for msg_hash={key[:12]}")
                return cached

        user_prompt = f"""LINGUA SORGENTE: {source_lang}
LINGUA TARGET TRANSLATION: {target_lang}

MESSAGGIO:
{body}

OUTPUT JSON:"""

        try:
            response = self.cascade.chat(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_prompt,
                max_tokens=self.max_tokens,
            )
        except AllProvidersDown as e:
            logger.error(f"cascade exhausted: {e}")
            raise

        raw_text = response["text"]
        try:
            parsed = _parse_response(raw_text)
            norm = _normalize(parsed)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"parse fail (provider={response['provider']}): {e}")
            logger.error(f"raw response (first 400 chars): {raw_text[:400]}")
            # Fail-safe: return neutral analysis con scam_flag=False
            norm = {
                "intent": "objection",  # forza HITL review
                "sentiment": "neutral",
                "scam_flag": False,
                "scam_reason": f"parse_error: {e}",
                "translation": "",
                "summary": f"[parse error] {body[:60]}",
            }

        result = AnalysisResult(
            intent=norm["intent"],
            sentiment=norm["sentiment"],
            scam_flag=norm["scam_flag"],
            scam_reason=norm["scam_reason"],
            translation=norm["translation"],
            summary=norm["summary"],
            provider=response["provider"],
            tokens_used=response.get("tokens_used", 0),
            cached=False,
            raw_response=raw_text[:500],
        )

        if use_cache:
            _cache_store(self.cache_db, key, result)

        return result


# ── CLI diagnostics ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    ap = argparse.ArgumentParser()
    ap.add_argument("--msg", required=True, help="Messaggio da analizzare")
    ap.add_argument("--source", default="it", help="Lingua sorgente (it/en/de)")
    ap.add_argument("--target", default="en", help="Lingua target translation")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--cache-db", default="/tmp/argos-analyzer-cache.sqlite")
    args = ap.parse_args()

    analyzer = MessageAnalyzer(cache_db=args.cache_db)
    result = analyzer.analyze(args.msg, args.source, args.target, use_cache=not args.no_cache)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
