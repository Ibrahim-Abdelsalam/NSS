"""Dataset and parameter presets for NSS experiments."""

from __future__ import annotations

from typing import Any, Dict

from core import PRIMARY_DATA_DIR


DATASET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sample": {
        "nurses_file": PRIMARY_DATA_DIR / "sample_nurses.csv",
        "scenarios_file": PRIMARY_DATA_DIR / "sample_scenarios.csv",
        "num_nurses": 10,
        "num_days": 14,
        "num_scenarios": 5,
        "description": "Small benchmark: quick testing, validation",
        "realistic": False,
        "data_source": "Synthetic benchmark conversion",
    },
    "test_small": {
        "nurses_file": PRIMARY_DATA_DIR / "test_small_nurses.csv",
        "scenarios_file": PRIMARY_DATA_DIR / "test_small_scenarios.csv",
        "num_nurses": 15,
        "num_days": 14,
        "num_scenarios": 8,
        "description": "Small-medium synthetic: unit testing",
        "realistic": False,
        "data_source": "Synthetic benchmark conversion",
    },
    "test_medium": {
        "nurses_file": PRIMARY_DATA_DIR / "test_medium_nurses.csv",
        "scenarios_file": PRIMARY_DATA_DIR / "test_medium_scenarios.csv",
        "num_nurses": 20,
        "num_days": 14,
        "num_scenarios": 10,
        "description": "Medium realistic: typical hospital unit",
        "realistic": True,
        "data_source": "Hospital bed occupancy proxy + CMS PBJ data",
    },
    "medium": {
        "nurses_file": PRIMARY_DATA_DIR / "medium_nurses.csv",
        "scenarios_file": PRIMARY_DATA_DIR / "medium_scenarios.csv",
        "num_nurses": 25,
        "num_days": 21,
        "num_scenarios": 12,
        "description": "Medium-large: 3-week planning horizon",
        "realistic": True,
        "data_source": "Hospital bed occupancy proxy + CMS PBJ data",
    },
    "nss_benchmark": {
        "nurses_file": PRIMARY_DATA_DIR / "nss_benchmark_nurses.csv",
        "scenarios_file": PRIMARY_DATA_DIR / "nss_benchmark_scenarios.csv",
        "num_nurses": 30,
        "num_days": 30,
        "num_scenarios": 15,
        "description": "Paper benchmark: He et al. (2019) case study",
        "realistic": True,
        "data_source": "He et al. (2019) publication",
    },
}


PARAMETER_PRESETS: Dict[str, Dict[str, Any]] = {
    "baseline": {
        "description": "Pure cost minimization (expected value model)",
        "model_type": "SDM",
        "params": {
            "c1": 100.0,
            "c2": 150.0,
            "q_plus": 200.0,
            "q_minus": 0.0,
            "c3": 10.0,
            "c4": 15.0,
            "n1": None,
            "n2": None,
            "n3": 0,
            "sigma": 0.95,
            "mu": 50.0,
        },
    },
    "conservative": {
        "description": "Risk-averse: controls worst-case shortages (CVaR)",
        "model_type": "SDM-CVaR",
        "params": {
            "c1": 100.0,
            "c2": 150.0,
            "q_plus": 200.0,
            "q_minus": 0.0,
            "c3": 10.0,
            "c4": 15.0,
            "n1": None,
            "n2": None,
            "n3": 0,
            "sigma": 0.90,
            "mu": 30.0,
        },
    },
    "paper_replication": {
        "description": "He et al. (2019) paper parameters (requires 30-day horizon)",
        "model_type": "SDM-CVaR",
        "params": {
            "c1": 100.0,
            "c2": 150.0,
            "q_plus": 200.0,
            "q_minus": 2.0,
            "c3": 10.0,
            "c4": 15.0,
            "n1": 20,
            "n2": 5,
            "n3": 12,
            "sigma": 0.95,
            "mu": 50.0,
        },
        "requirements": ["30-day horizon", "sufficient nurses"],
    },
    "fatigue_aware": {
        "description": "Includes patient safety via fatigue modeling",
        "model_type": "SDM",
        "params": {
            "c1": 100.0,
            "c2": 150.0,
            "q_plus": 200.0,
            "q_minus": 0.0,
            "c3": 10.0,
            "c4": 15.0,
            "n1": None,
            "n2": None,
            "n3": 0,
            "sigma": 0.95,
            "mu": 50.0,
            "patient_safety_enabled": True,
            "patient_safety_weight": 50.0,
            "fatigue_lambda": 0.03,
            "recovery_mu": 0.05,
            "max_fatigue_threshold": 0.70,
        },
    },
}
