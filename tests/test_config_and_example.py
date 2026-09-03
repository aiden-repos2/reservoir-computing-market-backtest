import json
from pathlib import Path
import subprocess
import sys

from reservoir_market_backtest.model import FROZEN_IKEDA_CONFIGURATION
from reservoir_market_backtest.schema import SYMBOLS, base_feature_columns


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_config_matches_implemented_contract() -> None:
    config = json.loads((ROOT / "config" / "frozen_method.json").read_text())
    ikeda = config["ikeda"]
    implemented = FROZEN_IKEDA_CONFIGURATION
    assert tuple(config["symbols"]) == SYMBOLS
    assert config["input_contract"]["SPY_feature_count"] == len(base_feature_columns("SPY"))
    assert config["input_contract"]["other_symbol_feature_count"] == len(
        base_feature_columns("QQQ")
    )
    assert config["input_contract"]["target_encoding"] == [-1, 0, 1]
    assert config["input_contract"]["missing_feature_policy"] == (
        "replace missing model-input values with 0.0"
    )
    assert ikeda["virtual_nodes"] == implemented.virtual_nodes
    assert ikeda["theta_steps"] == implemented.theta_steps
    assert ikeda["dt"] == implemented.dt
    assert ikeda["feedback_gain_beta"] == implemented.feedback_gain_beta
    assert ikeda["phase_offset"] == implemented.phase_offset
    assert ikeda["input_scale"] == implemented.input_scale
    assert ikeda["auxiliary_delta"] == implemented.auxiliary_delta
    assert ikeda["desynchronization"] == implemented.desynchronization
    assert ikeda["mask_seed"] == implemented.mask_seed
    volatility = config["volatility_sizing"]
    assert volatility["initial_training_sessions"] == 504
    assert volatility["penalty"] == 1e-4
    assert volatility["refit_every_sessions"] == 21
    assert volatility["embargo_sessions"] == 5
    assert config["readout"]["walk_forward_anchor"] == (
        "first row on or after 2016-01-01"
    )
    assert "after continuous scoring" in config["readout"]["reporting_slice"]
    assert "does not reset the prior weight" in config["portfolio"][
        "position_and_cost_stream"
    ]


def test_synthetic_demo_is_labeled_and_runs_without_private_data() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "synthetic_demo.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Synthetic demonstration only" in completed.stdout
    assert "not historical market evidence" in completed.stdout
