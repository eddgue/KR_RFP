"""C2 — the sealed-run input hash must be tamper-evident over the FULL config, not a subset.

Before, `_inputs_manifest` hand-listed a few config fields, so a post-seal change to a previously
un-hashed field (per-lot premium thresholds, the premium bands, exclusions, custom overrides,
preferred rules, single-supplier-per-lot, active TFs) would NOT change the input hash. Now the whole
frozen config is sealed, so any input change is detectable. Pure (no DB).
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.eng.runner import _canonical_hash, _inputs_manifest
from app.engine.interface import EngineConfig, EngineInputs


def _hash(config: EngineConfig) -> str:
    return _canonical_hash(
        _inputs_manifest(EngineInputs(cycle_id="cyc-1", round_code="R1", config=config))
    )


def test_identical_config_seals_identically() -> None:
    # Determinism: equal inputs seal identically, so only a real change can move the hash.
    assert _hash(EngineConfig()) == _hash(EngineConfig())


def test_per_lot_threshold_change_changes_the_seal() -> None:
    # `lot_premium_thresholds` was previously omitted from the manifest.
    base = EngineConfig()
    changed = base.model_copy(update={"lot_premium_thresholds": (("LOT1", Decimal("0.10")),)})
    assert _hash(base) != _hash(changed)


def test_premium_band_change_changes_the_seal() -> None:
    # Premium bands were omitted before; they change scores, so they must change the seal.
    base = EngineConfig()
    changed = base.model_copy(update={"premium_band_max": Decimal("0.15")})
    assert _hash(base) != _hash(changed)


def test_single_supplier_per_lot_change_changes_the_seal() -> None:
    base = EngineConfig()
    changed = base.model_copy(update={"single_supplier_per_lot": not base.single_supplier_per_lot})
    assert _hash(base) != _hash(changed)
