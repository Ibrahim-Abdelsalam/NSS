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
    nurses_df: Optional[pd.DataFrame] = None,
        model_type: str = "SDM",
        solver_name: str = "AUTO",
    ):
        """Initialize the model wrapper."""
        self.parameters = dict(parameters)
        self.nurses_list = list(nurses_list) if nurses_list is not None else []
        self.scenarios_df = scenarios_df.copy() if scenarios_df is not None else pd.DataFrame()
        self.nurses_df = nurses_df.copy() if nurses_df is not None else pd.DataFrame()
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
        """Build the optimization model using the new advanced implementation."""
        from core.frost_model import build_frost_ns_model
        import pulp

        if self.scenarios_df.empty:
            return self

        days_list = sorted(list(self.scenarios_df['day'].unique()))
        shifts_list = sorted(list(self.scenarios_df['shift'].unique()))
        
        if 'scenario' in self.scenarios_df.columns:
            scenarios_list = sorted(list(self.scenarios_df['scenario'].unique()))
        else:
            scenarios_list = [1]
            self.scenarios_df['scenario'] = 1

        demand_dict = {}
        has_skill = 'skill' in self.scenarios_df.columns
        for _, row in self.scenarios_df.iterrows():
            d, s, sc = int(row['day']), row['shift'], int(row['scenario'])
            if has_skill:
                demand_dict[(d, s, row['skill'], sc)] = int(row['demand'])
            else:
                demand_dict[(d, s, sc)] = int(row['demand'])

        
        # Bridge legacy UI parameters to new FROST-NS parameter names
        bridge = {
            'c1': 'c_planned',
            'q_plus': 'c_emergency',
            'q_minus': 'c_unmet',
            'n1': 'W_bar',
            'n2': 'N_bar',
            
            'max_emergency_staff': 'a_bar',
            'sigma': 'alpha',
            'mu': 'tau'
        }
        for old_k, new_k in bridge.items():
            if old_k in self.parameters and new_k not in self.parameters:
                self.parameters[new_k] = self.parameters[old_k]
                
        # Fatigue toggle bridge
        if not self.parameters.get('patient_safety_enabled', True):
            self.parameters['F_bar'] = 999  # Effectively disables fatigue limits
            
        if hasattr(self, 'nurses_df') and not self.nurses_df.empty:
            if 'skill_level' in self.nurses_df.columns:
                self.parameters['nurse_skill'] = dict(zip(self.nurses_df['nurse_id'], self.nurses_df['skill_level']))
            elif 'skill' in self.nurses_df.columns:
                self.parameters['nurse_skill'] = dict(zip(self.nurses_df['nurse_id'], self.nurses_df['skill']))
            if 'max_shifts' in self.nurses_df.columns:
                self.parameters['W_bar_i'] = dict(zip(self.nurses_df['nurse_id'], self.nurses_df['max_shifts']))
            if 'max_nights' in self.nurses_df.columns:
                self.parameters['N_bar_i'] = dict(zip(self.nurses_df['nurse_id'], self.nurses_df['max_nights']))
        problem = build_frost_ns_model(
            nurses=self.nurses_list,
            days=days_list,
            shifts=shifts_list,
            scenarios=scenarios_list,
            demand=demand_dict,
            params=self.parameters
        )
        
        time_limit = self.parameters.get('solve_time_limit')
        if time_limit == 0:
            time_limit = None
            
        solver_name = self.parameters.get('solver_name', 'AUTO')
        print(f"DEBUG: solver_name={solver_name}, GUROBI_available={pulp.GUROBI().available()}")
        if solver_name == 'GUROBI' or (solver_name == 'AUTO' and pulp.GUROBI().available()):
            print("DEBUG: Using GUROBI")
            solver = pulp.GUROBI_CMD(msg=0, timeLimit=time_limit) if hasattr(pulp, 'GUROBI_CMD') else pulp.GUROBI(msg=0, timeLimit=time_limit)
        else:
            print("DEBUG: Using CBC")
            solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
            
        problem.solve(solver)
        
        status = pulp.LpStatus[problem.status]
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
                val = variable.varValue if variable.varValue else 0
                variable_values[variable.name] = val
                
                # Trick the legacy UI into rendering our new FROST-NS model outputs
                # Map x_Nurse_Day_Shift to RegularShift_Nurse_Day_Shift
                if variable.name.startswith("x_"):
                    legacy_name = variable.name.replace("x_", "RegularShift_").replace("'", "").replace(" ", "")
                    variable_values[legacy_name] = val
                
                # Map CVaR eta to legacy VaR_xi so Risk Assessment tab works
                if variable.name == "eta":
                    variable_values["VaR_xi"] = val
        
        # Inject legacy cost parameters so the UI cost breakdown doesn't crash
        self.parameters.setdefault('c1', self.parameters.get('c_planned', 100))
        self.parameters.setdefault('c2', 0)
        self.parameters.setdefault('q_plus', self.parameters.get('c_emergency', 200))

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
    nurses_df: Optional[pd.DataFrame] = None,
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
    nurses_df: Optional[pd.DataFrame] = None,
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
            nurses_df=nurses_df
        )

    return NurseSchedulingModel(
        parameters,
        nurses_list,
        scenarios_df,
        model_type=model_type,
        solver_name=solver_name,
        nurses_df=nurses_df
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
        nurses_df=nurses_df
    )
