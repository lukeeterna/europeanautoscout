#!/usr/bin/env python3
"""S260 FASE 1b — asserzione STRUTTURALE: il ladder non rilassa MAI drivetrain/motore.

Prova durevole (non solo empirica come il trace): cabla nel test suite il principio
S259-bis "non si rilassa attraverso le dimensioni che muovono il prezzo". Se una
sessione futura reintroduce un L4 che droppa drivetrain (o engine), questi test
FALLISCONO immediatamente.

OFFLINE: nessuna rete, nessuno scraper. Usa solo _levels/_match/derive_trim_family.

Esecuzione:
  cd /Users/macbook/Documents/combaretrovamiauto-enterprise
  python3 -m tools.tests.test_no_fusion_ladder
"""
from __future__ import annotations

import sys

from tools.it_market_price import _levels, _match, derive_trim_family


def test_ladder_pins_drivetrain_and_engine() -> None:
    """ASSERZIONE STRUTTURALE: ad OGNI livello del ladder spec-aware,
    drivetrain ed engine restano ATTIVI (pinnati). trim/km/fuel possono
    rilassarsi, drivetrain/engine MAI."""
    for span in (1, 2):
        levels = _levels(year_span=span)
        assert levels, "ladder vuoto"
        for idx, cfg in enumerate(levels):
            assert cfg["drivetrain"] is True, (
                f"L{idx} (span={span}) rilassa drivetrain -> FUSIONE awd+rwd reintrodotta. "
                f"cfg={cfg}")
            assert cfg["engine"] is True, (
                f"L{idx} (span={span}) rilassa engine_class -> FUSIONE 320+340 reintrodotta. "
                f"cfg={cfg}")
    print("OK strutturale: drivetrain+engine pinnati su tutti i livelli, span 1 e 2")


def test_matcher_never_fuses_drivetrain() -> None:
    """COMPORTAMENTALE: un target rwd non matcha MAI un comparabile awd
    (stesso engine/fuel/anno/km) a NESSUN livello del ladder. E viceversa."""
    target_rwd = derive_trim_family("320d", "diesel", "automatic", 190)
    cand_awd = derive_trim_family("320d xDrive", "diesel", "automatic", 190)
    assert target_rwd["drivetrain"] == "rwd"
    assert cand_awd["drivetrain"] == "awd"

    YEAR, KM, BAND = 2021, 60_000, 30_000
    for idx, cfg in enumerate(_levels(year_span=2)):
        matched = _match(target_rwd, cand_awd, KM, YEAR, KM, YEAR, BAND, cfg)
        assert matched is False, (
            f"L{idx}: target rwd ha matchato candidato awd -> FUSIONE drivetrain")
    print("OK comportamentale: rwd non matcha mai awd su nessun livello")


def test_matcher_never_fuses_fuel() -> None:
    """COMPORTAMENTALE: un target petrol non matcha MAI un comparabile diesel
    (stesso engine/drivetrain/anno/km) a nessun livello."""
    target_petrol = derive_trim_family("330i", "petrol", "automatic", 258)
    cand_diesel = derive_trim_family("330d", "diesel", "automatic", 286)
    YEAR, KM, BAND = 2021, 60_000, 30_000
    for idx, cfg in enumerate(_levels(year_span=2)):
        matched = _match(target_petrol, cand_diesel, KM, YEAR, KM, YEAR, BAND, cfg)
        # engine_class differisce (330 vs 330 -> uguale!) quindi qui pinna il FUEL.
        # 330i petrol vs 330d diesel: stesso engine_class 330, fuel diverso.
        assert matched is False, (
            f"L{idx}: target petrol ha matchato candidato diesel -> FUSIONE fuel")
    print("OK comportamentale: petrol non matcha mai diesel su nessun livello")


def test_canary_would_fail_if_fusion_reintroduced() -> None:
    """CANARY esplicito: simula un L4 malevolo (drivetrain=False) e dimostra
    che PRODURREBBE la fusione. Conferma che l'assertion structural e' load-bearing
    (cattura davvero il caso, non e' vacua)."""
    target_rwd = derive_trim_family("320d", "diesel", "automatic", 190)
    cand_awd = derive_trim_family("320d xDrive", "diesel", "automatic", 190)
    evil_l4 = dict(engine=True, drivetrain=False, trim=False, fuel=True,
                   km=False, year_tol=2)
    fused = _match(target_rwd, cand_awd, 60_000, 2021, 60_000, 2021, 30_000, evil_l4)
    assert fused is True, (
        "canary rotto: un L4 con drivetrain=False NON fonde -> il test struttura "
        "sarebbe vacuo")
    print("OK canary: un L4 drivetrain=False fonderebbe awd+rwd (assertion non vacua)")


def main() -> int:
    test_ladder_pins_drivetrain_and_engine()
    test_matcher_never_fuses_drivetrain()
    test_matcher_never_fuses_fuel()
    test_canary_would_fail_if_fusion_reintroduced()
    print("\nTUTTI I CONTROLLI 1b PASSATI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
