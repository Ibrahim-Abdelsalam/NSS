"""Optimization model wrapper for the NSS core layer.

ARCHITECTURE NOTE: model_2.py Delegation
=========================================
This module wraps the 2254-line solver implementation in model_2.py. While model_2.py
is technically a separate file, it is NOT part of the public API and should be considered
an internal implementation detail. All external code should:

1. Import from core.model (this file), not directly from model_2
2. Use create_model() to instantiate the model
3. Call model.build() and model.solve() to orchestrate solving

Future refactoring can extract model_2.py logic incrementally into smaller, focused
solver modules within the core package without breaking the public API (since core.model
is the facade).

Legacy users can still use the build_and_solve_model() wrapper function.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from core import SolveResult


@dataclass
class _BuildArtifacts:
    """Internal storage for the built optimization model."""

    problem: Any
    status: str


class NurseSchedulingModel:
    """Build and solve the nurse scheduling optimization model."""

    def __init__(
        self,
        parameters: Dict[str, Any],
        nurses_list: Optional[List[str]] = None,
        scenarios_df: Optional[pd.DataFrame] = None,
        model_type: str = "SDM",
        solver_name: str = "AUTO",
    ):
        """Initialize the model wrapper."""
        self.parameters = dict(parameters)
        self.nurses_list = list(nurses_list) if nurses_list is not None else []
        self.scenarios_df = scenarios_df.copy() if scenarios_df is not None else pd.DataFrame()
        self.model_type = model_type
        self.solver_name = solver_name
        self.fatigue_enabled = bool(self.parameters.get("patient_safety_enabled", False))
        self._artifacts: Optional[_BuildArtifacts] = None
        self._solve_result: Optional[SolveResult] = None

    @property
    def problem(self) -> Any:
        """Return the built optimization problem, if available."""
        return None if self._artifacts is None else self._artifacts.problem

    @property
    def status(self) -> Optional[str]:
        """Return the current solve status, if available."""
        return None if self._artifacts is None else self._artifacts.status

    @property
    def solve_result(self) -> Optional[SolveResult]:
        """Return the cached solve result, if available."""
        return self._solve_result

    def build(self) -> "NurseSchedulingModel":
        """Build the optimization model using the existing implementation."""
        from core._model_core import build_and_solve_model

        problem, status = build_and_solve_model(
            self.nurses_list,
            self.scenarios_df,
            self.parameters,
            model_type=self.model_type,
            solver_name=self.solver_name,
        )
        self._artifacts = _BuildArtifacts(problem=problem, status=status)
        return self

    def solve(self) -> SolveResult:
        """Solve the model and return a structured solve result."""
        if self._artifacts is None:
            self.build()

        assert self._artifacts is not None
        problem = self._artifacts.problem
        status = self._artifacts.status

        objective_value: Optional[float] = None
        if hasattr(problem, "objective"):
            try:
                raw_value = problem.objective.value()
                objective_value = float(raw_value) if raw_value is not None else None
            except Exception:
                objective_value = None

        variable_values: Dict[str, Any] = {}
        if hasattr(problem, "variables"):
            for variable in problem.variables():
                variable_values[variable.name] = variable.varValue if variable.varValue else 0

        solve_time_seconds = float(self.parameters.get("solve_time_seconds", 0.0))
        metadata = {
            "model_type": self.model_type,
            "solver_name": self.solver_name,
        }

        self._solve_result = SolveResult(
            status=status,
            objective_value=objective_value,
            solve_time_seconds=solve_time_seconds,
            solver_name=self.solver_name,
            variable_values=variable_values,
            metadata=metadata,
        )
        return self._solve_result

    def with_data(
        self,
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
    ) -> "NurseSchedulingModel":
        """Attach dataset inputs to the model wrapper."""
        self.nurses_list = list(nurses_list)
        self.scenarios_df = scenarios_df.copy()
        return self


class FatigueAwareNurseSchedulingModel(NurseSchedulingModel):
    """Model variant with fatigue-aware scheduling enabled."""

    def __init__(
        self,
        parameters: Dict[str, Any],
        nurses_list: Optional[List[str]] = None,
        scenarios_df: Optional[pd.DataFrame] = None,
        model_type: str = "SDM",
        solver_name: str = "AUTO",
    ):
        """Initialize the fatigue-aware model variant."""
        params = dict(parameters)
        params["patient_safety_enabled"] = True
        super().__init__(params, nurses_list, scenarios_df, model_type=model_type, solver_name=solver_name)


def create_model(
    parameters: Dict[str, Any],
    nurses_list: Optional[List[str]] = None,
    scenarios_df: Optional[pd.DataFrame] = None,
    model_type: str = "SDM",
    solver_name: str = "AUTO",
) -> NurseSchedulingModel:
    """Create the appropriate model variant based on fatigue settings."""
    if parameters.get("patient_safety_enabled", False):
        return FatigueAwareNurseSchedulingModel(
            parameters,
            nurses_list,
            scenarios_df,
            model_type=model_type,
            solver_name=solver_name,
        )

    return NurseSchedulingModel(
        parameters,
        nurses_list,
        scenarios_df,
        model_type=model_type,
        solver_name=solver_name,
    )


# Backward-compatible helper for callers that still use the functional API.
def build_and_solve_model(
    nurses_list: List[str],
    scenarios_df: pd.DataFrame,
    model_params: Dict[str, Any],
    model_type: str = "SDM",
    solver_name: str = "AUTO",
):
    """Backward-compatible wrapper around the existing implementation."""
    from core._model_core import build_and_solve_model as legacy_build_and_solve_model

    return legacy_build_and_solve_model(
        nurses_list,
        scenarios_df,
        model_params,
        model_type=model_type,
        solver_name=solver_name,
    )
