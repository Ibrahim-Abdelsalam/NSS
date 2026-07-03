"""Core package for the Nurse Scheduling System (NSS)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PRIMARY_DATA_DIR = DATA_DIR / "primary"
SUPPLEMENTARY_DATA_DIR = DATA_DIR / "supplementary"
RESULTS_DIR = DATA_DIR / "experiments"


@dataclass
class SolveResult:
    """Returned by NurseSchedulingModel.solve()."""

    status: str
    objective_value: Optional[float]
    solve_time_seconds: float
    solver_name: str
    variable_values: dict
    metadata: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Returned by ParameterValidator methods."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    sanitized_params: Optional[dict] = None


@dataclass
class ExperimentResult:
    """Returned by ExperimentPipeline.run()."""

    experiment_id: str
    config: dict
    solve_result: SolveResult
    schedule_df: pd.DataFrame
    cost_summary: dict
    timestamp: str
    archived_path: Optional[str] = None


__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "PRIMARY_DATA_DIR",
    "SUPPLEMENTARY_DATA_DIR",
    "RESULTS_DIR",
    "SolveResult",
    "ValidationResult",
    "ExperimentResult",
]