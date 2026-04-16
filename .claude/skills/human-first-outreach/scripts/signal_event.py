"""
signal_event.py — Oggetto unificato SignalEvent
ARGOS human-first-outreach | Phase 2 | S128

Fluisce in: message anchor + LIA data_source + opt-out {data_source}
Gerarchia strength: S+ aged inventory → S price drop → A stock velocity → B review → C new listing
"""

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional


# ── Env vars (soglie calibrabili senza deploy) ────────────────────────────────
SIGNAL_TTL_DAYS = int(os.getenv("ARGOS_SIGNAL_TTL_DAYS", "14"))
ICP_MIN_RATIO   = float(os.getenv("ARGOS_ICP_MIN_RATIO", "0.20"))
ICP_CORE_RATIO  = float(os.getenv("ARGOS_ICP_CORE_RATIO", "0.30"))


# ── SignalEvent ───────────────────────────────────────────────────────────────

@dataclass
class SignalEvent:
    """
    Oggetto unificato che viaggia attraverso tutta la pipeline outreach.

    Mandatory:
      url, days_on_market, vehicle, listing_price, scrape_date,
      signal_strength, signal_observed_at, dealer_id, data_source

    signal_strength gerarchia (S+ > S > A > B > C):
      S+ = aged inventory (>90gg su portale IT senza variazioni)
      S  = price drop recente
      A  = stock velocity anomala
      B  = google review trigger
      C  = new listing (da solo NON giustifica cold outreach Day 1)
    """
    url: str
    days_on_market: int            # ESATTO — mai parafrasare con "diversi mesi"
    vehicle: str                   # es. "BMW X3 30d 2022"
    listing_price: int             # EUR
    scrape_date: date
    signal_strength: str           # S+ | S | A | B | C
    signal_observed_at: datetime   # timestamp scrape — usato per SIGNAL-FRESH-001
    dealer_id: str
    data_source: str               # nome leggibile per opt-out: "AutoScout24.it"

    # Optional — arricchimento se disponibile
    listing_id: Optional[str] = None
    seller_name: Optional[str] = None   # per image_sanitizer
    signal_notes: Optional[str] = None  # es. "prezzo calato €2k in 30gg"

    def is_fresh(self) -> bool:
        """Ritorna True se il signal è entro TTL (SIGNAL-FRESH-001)."""
        now = datetime.now(timezone.utc)
        observed = self.signal_observed_at
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        return (now - observed).days <= SIGNAL_TTL_DAYS

    def anchor_text(self) -> str:
        """Testo anchor per il messaggio Day 1 — usa days_on_market ESATTO."""
        if self.days_on_market >= 90:
            return f"è in listino da {self.days_on_market} giorni senza movimenti"
        elif self.days_on_market >= 60:
            return f"è ferma da {self.days_on_market} giorni"
        elif self.days_on_market >= 30:
            return f"è in listino da {self.days_on_market} giorni"
        else:
            return f"è apparsa {self.days_on_market} giorni fa"

    def opt_out_source_text(self) -> str:
        """Stringa per opt-out GDPR: 'il suo numero è pubblico su {data_source}'."""
        return f"il suo numero è pubblico su {self.data_source}"

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "days_on_market": self.days_on_market,
            "vehicle": self.vehicle,
            "listing_price": self.listing_price,
            "scrape_date": str(self.scrape_date),
            "signal_strength": self.signal_strength,
            "signal_observed_at": self.signal_observed_at.isoformat(),
            "dealer_id": self.dealer_id,
            "data_source": self.data_source,
            "listing_id": self.listing_id,
            "seller_name": self.seller_name,
            "signal_notes": self.signal_notes,
        }


# ── GATE-ICP-001 ──────────────────────────────────────────────────────────────

def gate_icp_001(dealer_stock: dict) -> dict:
    """
    GATE-ICP-001 — Premium concentration check.
    dealer_stock: {"BMW": n, "Mercedes": n, "Audi": n, "total": n, ...}

    Returns:
      {"decision": "block"|"low_priority"|"icp_core", "rule_id": "GATE-ICP-001",
       "motivation": str, "premium_concentration": float}
    """
    total = dealer_stock.get("total", 0)
    if total == 0:
        return {
            "decision": "block",
            "rule_id": "GATE-ICP-001",
            "motivation": "Stock totale = 0, impossibile calcolare premium_concentration",
            "premium_concentration": 0.0,
        }

    premium = (
        dealer_stock.get("BMW", 0)
        + dealer_stock.get("Mercedes", 0)
        + dealer_stock.get("Audi", 0)
    )
    concentration = premium / total

    if concentration < ICP_MIN_RATIO:
        return {
            "decision": "block",
            "rule_id": "GATE-ICP-001",
            "motivation": (
                f"premium_concentration={concentration:.0%} < soglia minima {ICP_MIN_RATIO:.0%}. "
                f"Dealer non ICP-fit. Re-scrape stock o skip."
            ),
            "premium_concentration": concentration,
        }
    elif concentration < ICP_CORE_RATIO:
        return {
            "decision": "low_priority",
            "rule_id": "GATE-ICP-001",
            "motivation": (
                f"premium_concentration={concentration:.0%} tra {ICP_MIN_RATIO:.0%} e {ICP_CORE_RATIO:.0%}. "
                f"Dealer low_priority — procede ma non prioritario."
            ),
            "premium_concentration": concentration,
        }
    else:
        return {
            "decision": "icp_core",
            "rule_id": "GATE-ICP-001",
            "motivation": f"premium_concentration={concentration:.0%} >= {ICP_CORE_RATIO:.0%}. ICP-CORE.",
            "premium_concentration": concentration,
        }


# ── SIGNAL-FRESH-001 ──────────────────────────────────────────────────────────

def signal_fresh_001(signal: SignalEvent) -> dict:
    """
    SIGNAL-FRESH-001 — Signal staleness check.
    Se signal_observed_at > TTL giorni → block (messaggio con veicolo già venduto).

    Returns:
      {"decision": "pass"|"block", "rule_id": "SIGNAL-FRESH-001", "motivation": str}
    """
    now = datetime.now(timezone.utc)
    observed = signal.signal_observed_at
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)

    age_days = (now - observed).days

    if age_days > SIGNAL_TTL_DAYS:
        return {
            "decision": "block",
            "rule_id": "SIGNAL-FRESH-001",
            "motivation": (
                f"Signal scaduto: {age_days}gg fa (TTL={SIGNAL_TTL_DAYS}gg). "
                f"Richiede re-scrape {signal.data_source} prima di procedere."
            ),
        }
    return {
        "decision": "pass",
        "rule_id": "SIGNAL-FRESH-001",
        "motivation": f"Signal fresco: {age_days}gg fa (TTL={SIGNAL_TTL_DAYS}gg).",
    }


# ── Gate conflict resolution — LAYER 0 ───────────────────────────────────────

GATE_PRECEDENCE = [
    "GATE-ICP-001", "SIGNAL-FRESH-001",           # GATE — stop immediato
    "COMP", "BRAND", "FORMAT", "TIMING", "RATE",  # livelli successivi
    "ARCH", "TONE",
]


def run_gates(signal: SignalEvent, dealer_stock: dict) -> dict:
    """
    Esegue GATE-ICP-001 + SIGNAL-FRESH-001 in sequenza.
    Se uno blocca → stop immediato, no layer successivi.

    Returns:
      {"passed": bool, "blocked_by": str|None, "motivation": str, "gates": [...]}
    """
    gates_run = []

    # GATE 1: Signal fresh
    fresh = signal_fresh_001(signal)
    gates_run.append(fresh)
    if fresh["decision"] == "block":
        return {
            "passed": False,
            "blocked_by": "SIGNAL-FRESH-001",
            "motivation": fresh["motivation"],
            "gates": gates_run,
        }

    # GATE 2: ICP
    icp = gate_icp_001(dealer_stock)
    gates_run.append(icp)
    if icp["decision"] == "block":
        return {
            "passed": False,
            "blocked_by": "GATE-ICP-001",
            "motivation": icp["motivation"],
            "gates": gates_run,
        }

    return {
        "passed": True,
        "blocked_by": None,
        "motivation": f"ICP={icp['decision']}, signal_age=OK",
        "gates": gates_run,
        "icp_tier": icp["decision"],
        "premium_concentration": icp.get("premium_concentration"),
    }
