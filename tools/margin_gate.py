"""ARGOS Margin Gate (S255).

Asse "bonta' dell'AFFARE" — separato e indipendente dal CoVe Engine
(che misura la "bonta' dell'AUTO"). Potere di VETO: rifiuta i deal in cui
il margine netto del dealer scende sotto il pavimento.

NON modifica cove_engine_v4.py. NON usa la fee flat €900 (abolita): la fee
ARGOS esiste solo dove c'e' surplus reale sopra il pavimento dealer, e ne
prende una quota di MINORANZA.

Formule (founder spec S255, tunabili SOLO da Luke):
    chiavi_in_mano      = prezzo_de + frizione           (frizione = trasporto + immatricolazione)
    spread_lordo        = prezzo_mercato_it - chiavi_in_mano
    dealer_floor_amount = DEALER_FLOOR_PCT * prezzo_mercato_it
    surplus             = spread_lordo - dealer_floor_amount
    se surplus <= 0     -> REJECT ("sotto pavimento dealer")
    fee_argos           = ARGOS_SHARE * surplus
    margine_netto_dealer = spread_lordo - fee_argos       (garantito >= dealer_floor_amount)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

# --- Parametri (default founder S255 — tunabili SOLO da Luke) --------------
# Frizione fissa media DE->IT: trasporto bisarca + immatricolazione/IPT.
# ~€1.915 (founder spec). Override per-deal possibile dal chiamante quando
# trasporto/immatricolazione reali sono disponibili.
DEFAULT_FRICTION_EUR: float = 1915.0
DEALER_FLOOR_PCT: float = 0.12   # il dealer non scende mai sotto il 12% del prezzo mercato IT
ARGOS_SHARE: float = 0.40        # quota ARGOS sul SURPLUS (non sull'intero spread)


@dataclass
class MarginResult:
    prezzo_de: float
    prezzo_mercato_it: float
    friction_eur: float
    chiavi_in_mano: float
    spread_lordo: float
    dealer_floor_amount: float
    surplus: float
    fee_argos: float
    margine_netto_dealer: float
    margine_netto_pct: float      # margine netto dealer in % del prezzo mercato IT
    decision: str                 # "PASS" | "REJECT"
    reject_reason: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_margin(
    prezzo_de: float,
    prezzo_mercato_it: float,
    friction_eur: float = DEFAULT_FRICTION_EUR,
    dealer_floor_pct: float = DEALER_FLOOR_PCT,
    argos_share: float = ARGOS_SHARE,
) -> MarginResult:
    """Valuta la bonta' dell'affare per il dealer.

    prezzo_de         = prezzo annuncio estero (costo di acquisto auto).
    prezzo_mercato_it = prezzo di mercato IT (mediana distribuzione comparabili, NON x1.15).
    friction_eur      = trasporto + immatricolazione. Passare 0 se prezzo_de e' GIA' chiavi-in-mano.
    """
    chiavi_in_mano = prezzo_de + friction_eur
    spread_lordo = prezzo_mercato_it - chiavi_in_mano
    dealer_floor_amount = dealer_floor_pct * prezzo_mercato_it
    surplus = spread_lordo - dealer_floor_amount

    if surplus <= 0:
        # Nessun surplus: l'affare non lascia al dealer nemmeno il pavimento.
        # La fee ARGOS e' ZERO (non si prende fee su un deal che non c'e').
        netto = spread_lordo
        pct = (netto / prezzo_mercato_it * 100.0) if prezzo_mercato_it else 0.0
        return MarginResult(
            prezzo_de=round(prezzo_de, 2),
            prezzo_mercato_it=round(prezzo_mercato_it, 2),
            friction_eur=round(friction_eur, 2),
            chiavi_in_mano=round(chiavi_in_mano, 2),
            spread_lordo=round(spread_lordo, 2),
            dealer_floor_amount=round(dealer_floor_amount, 2),
            surplus=round(surplus, 2),
            fee_argos=0.0,
            margine_netto_dealer=round(netto, 2),
            margine_netto_pct=round(pct, 2),
            decision="REJECT",
            reject_reason="sotto pavimento dealer",
        )

    fee_argos = argos_share * surplus
    margine_netto_dealer = spread_lordo - fee_argos
    pct = (margine_netto_dealer / prezzo_mercato_it * 100.0) if prezzo_mercato_it else 0.0
    return MarginResult(
        prezzo_de=round(prezzo_de, 2),
        prezzo_mercato_it=round(prezzo_mercato_it, 2),
        friction_eur=round(friction_eur, 2),
        chiavi_in_mano=round(chiavi_in_mano, 2),
        spread_lordo=round(spread_lordo, 2),
        dealer_floor_amount=round(dealer_floor_amount, 2),
        surplus=round(surplus, 2),
        fee_argos=round(fee_argos, 2),
        margine_netto_dealer=round(margine_netto_dealer, 2),
        margine_netto_pct=round(pct, 2),
        decision="PASS",
        reject_reason=None,
    )


def _selftest() -> int:
    """DoD #3 — falsificazione: la X1 del dossier S254 DEVE uscire REJECT.

    Founder: chiavi-in-mano €21.795 / mercato IT €22.862.
    21.795 e' GIA' chiavi-in-mano -> friction_eur=0.
    """
    failed = 0

    x1 = evaluate_margin(prezzo_de=21795.0, prezzo_mercato_it=22862.0, friction_eur=0.0)
    print("=== Falsificazione X1 (DoD #3) ===")
    print(f"  chiavi_in_mano      = {x1.chiavi_in_mano:.0f}")
    print(f"  spread_lordo        = {x1.spread_lordo:.0f}  (atteso 1067)")
    print(f"  dealer_floor (12%)  = {x1.dealer_floor_amount:.0f}  (atteso ~2743)")
    print(f"  surplus             = {x1.surplus:.0f}  (atteso ~-1676)")
    print(f"  DECISIONE           = {x1.decision}  (atteso REJECT)")
    if x1.decision != "REJECT":
        print("  !! FAIL: il gate e' ROTTO — la X1 doveva uscire REJECT")
        failed += 1
    else:
        print("  OK: X1 correttamente REJECT")

    # PASS branch (sanity): deal con surplus reale deve passare e lasciare al
    # dealer almeno il pavimento.
    print("\n=== Sanity PASS branch ===")
    p = evaluate_margin(prezzo_de=33000.0, prezzo_mercato_it=42000.0)
    print(f"  spread_lordo        = {p.spread_lordo:.0f}")
    print(f"  dealer_floor (12%)  = {p.dealer_floor_amount:.0f}")
    print(f"  surplus             = {p.surplus:.0f}")
    print(f"  fee_argos (40% surp)= {p.fee_argos:.0f}")
    print(f"  margine_netto_dealer= {p.margine_netto_dealer:.0f} ({p.margine_netto_pct:.1f}%)")
    print(f"  DECISIONE           = {p.decision}  (atteso PASS)")
    if p.decision != "PASS":
        print("  !! FAIL: deal con surplus reale doveva passare")
        failed += 1
    elif p.margine_netto_dealer < p.dealer_floor_amount - 0.01:
        print("  !! FAIL: margine netto dealer SOTTO il pavimento garantito")
        failed += 1
    else:
        print("  OK: PASS e margine netto >= pavimento dealer")

    print(f"\n{'TUTTI I TEST PASSATI' if failed == 0 else f'{failed} TEST FALLITI'}")
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(1 if _selftest() else 0)
