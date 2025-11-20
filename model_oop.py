"""
Object-Oriented Implementation of Nurse Scheduling Optimization Model

This module provides a clean OOP interface to the two-stage stochastic nurse scheduling
problem from He et al. (2019). It refactors the functional code into reusable classes.

Classes:
    ModelParameters: Encapsulates all model parameters with validation
    NurseSchedulingModel: Main optimization model with build/solve/results methods
    OptimizationResults: Encapsulates solution data with convenient accessors

Usage:
    >>> params = ModelParameters(c1=100, c2=150, q_plus=200, n1=24, n2=3, n3=16)
    >>> model = NurseSchedulingModel(nurses_list, scenarios_df, params)
    >>> model.build(model_type="SDM")
    >>> status = model.solve(solver='highs')
    >>> results = model.get_results()
    >>> print(results.total_cost)
"""

import pulp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from solver_config import create_solver


@dataclass
class ModelParameters:
    """
    Encapsulates all parameters for the nurse scheduling optimization model.
    
    Attributes:
        Cost Parameters:
            c1: Regular shift cost per nurse
            c2: Overtime shift cost per nurse
            q_plus: Emergency staff cost per shift
            q_minus: Shift cancellation cost (default 0)
            c3: Penalty for stand-alone shifts
            c4: Penalty for unwanted shift patterns
        
        Work Rules:
            n1: Maximum total shifts per nurse
            n2: Maximum night shifts per nurse
            n3: Minimum regular (non-overtime) shifts per nurse
            n4: Minimum complete weekends off (0 = disabled)
        
        CVaR Parameters:
            sigma: Confidence level for CVaR (e.g., 0.95)
            mu: Maximum acceptable shortage in worst-case scenarios
        
        Advanced Constraints:
            shift_quotas: Min/max per shift type
            night_rest_enabled: Enable night shift rest requirements
            min_consecutive_nights: Min consecutive night shifts
            days_off_after_nights: Required days off after nights
            start_date: Start date for weekend detection
            max_emergency_staff: Max emergency nurses per shift
            max_cancellations: Max shift cancellations per shift
    """
    
    # Cost parameters
    c1: float
    c2: float
    q_plus: float
    q_minus: float = 0.0
    c3: float = 10.0
    c4: float = 15.0
    
    # Work rules
    n1: int = 24
    n2: int = 3
    n3: int = 16
    n4: int = 0
    
    # CVaR parameters
    sigma: float = 0.95
    mu: float = 5.0
    
    # Advanced constraints
    shift_quotas: Dict[str, Dict[str, int]] = field(default_factory=dict)
    night_rest_enabled: bool = False
    min_consecutive_nights: int = 2
    days_off_after_nights: int = 2
    start_date: Optional[str] = None
    max_emergency_staff: float = float('inf')
    max_cancellations: float = float('inf')
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate all parameters are within acceptable ranges.
        
        Raises:
            ValueError: If any parameter is invalid
        """
        if self.c1 <= 0:
            raise ValueError(f"c1 must be positive, got {self.c1}")
        if self.c2 < self.c1:
            raise ValueError(f"c2 ({self.c2}) should be >= c1 ({self.c1}) for overtime premium")
        if self.q_plus < 0:
            raise ValueError(f"q_plus must be non-negative, got {self.q_plus}")
        if self.q_minus < 0:
            raise ValueError(f"q_minus must be non-negative, got {self.q_minus}")
        
        if self.n1 <= 0:
            raise ValueError(f"n1 must be positive, got {self.n1}")
        if self.n2 < 0 or self.n2 > self.n1:
            raise ValueError(f"n2 must be in [0, n1={self.n1}], got {self.n2}")
        if self.n3 < 0 or self.n3 > self.n1:
            raise ValueError(f"n3 must be in [0, n1={self.n1}], got {self.n3}")
        if self.n4 < 0:
            raise ValueError(f"n4 must be non-negative, got {self.n4}")
        
        if self.sigma is not None and not (0 < self.sigma < 1):
            raise ValueError(f"sigma must be in (0, 1), got {self.sigma}")
        if self.mu is not None and self.mu < 0:
            raise ValueError(f"mu must be non-negative, got {self.mu}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary format (for backward compatibility)."""
        return {
            'c1': self.c1,
            'c2': self.c2,
            'q_plus': self.q_plus,
            'q_minus': self.q_minus,
            'c3': self.c3,
            'c4': self.c4,
            'n1': self.n1,
            'n2': self.n2,
            'n3': self.n3,
            'n4': self.n4,
            'sigma': self.sigma,
            'mu': self.mu,
            'shift_quotas': self.shift_quotas,
            'night_rest_enabled': self.night_rest_enabled,
            'min_consecutive_nights': self.min_consecutive_nights,
            'days_off_after_nights': self.days_off_after_nights,
            'start_date': self.start_date,
            'max_emergency_staff': self.max_emergency_staff,
            'max_cancellations': self.max_cancellations,
        }


class NurseSchedulingModel:
    """
    Two-stage stochastic nurse scheduling optimization model.
    
    This class encapsulates the complete optimization model from He et al. (2019).
    It provides a clean interface for building, solving, and extracting results.
    
    Attributes:
        nurses (List[str]): List of nurse names/IDs
        scenarios (pd.DataFrame): Demand scenarios data
        params (ModelParameters): Model parameters object
        model_type (str): 'SDM' or 'SDM-CVaR'
        prob (pulp.LpProblem): PuLP optimization problem (after build())
        status (str): Solver status (after solve())
        
    Example:
        >>> params = ModelParameters(c1=100, c2=150, q_plus=200, n1=24, n2=3, n3=16)
        >>> model = NurseSchedulingModel(nurses_list, scenarios_df, params)
        >>> model.build(model_type="SDM")
        >>> status = model.solve()
        >>> if status == "Optimal":
        ...     results = model.get_results()
        ...     print(f"Total cost: ${results.total_cost:.2f}")
    """
    
    def __init__(self, 
                 nurses: List[str],
                 scenarios: pd.DataFrame,
                 params: Union[ModelParameters, Dict[str, Any]]):
        """
        Initialize the nurse scheduling model.
        
        Args:
            nurses: List of nurse names/IDs
            scenarios: DataFrame with columns: scenario, day, shift, demand
            params: ModelParameters object or dictionary of parameters
        """
        self.nurses = nurses
        self.scenarios = scenarios.copy()
        
        # Convert dict to ModelParameters if needed
        if isinstance(params, dict):
            self.params = ModelParameters(**params)
        else:
            self.params = params
        
        # Model components (initialized in build())
        self.prob: Optional[pulp.LpProblem] = None
        self.model_type: Optional[str] = None
        self.status: Optional[str] = None
        
        # Sets extracted from data
        self.I_nurses: List[str] = []
        self.J_days: np.ndarray = np.array([])
        self.K_shifts: np.ndarray = np.array([])
        self.W_scenarios: np.ndarray = np.array([])
        self.R_demand: Dict = {}
        self.scenario_probability: Dict = {}
        
        # Decision variables (created in build())
        self.sr: Optional[Dict] = None  # Regular shifts
        self.so: Optional[Dict] = None  # Overtime shifts
        self.alpha: Optional[Dict] = None  # Emergency staff
        self.beta: Optional[Dict] = None  # Cancellations
        self.xi: Optional[pulp.LpVariable] = None  # CVaR VaR threshold
        self.z: Optional[Dict] = None  # CVaR excess loss
        self.dev1: Optional[Dict] = None  # Stand-alone shift penalties
        self.dev2: Optional[Dict] = None  # Unwanted pattern penalties
        
        # Helper variables for advanced constraints
        self.SR: Optional[Dict] = None  # Binary: nurse works any regular shifts
        self.SO: Optional[Dict] = None  # Binary: nurse works any overtime shifts
        self.weekend_off: Optional[Dict] = None  # Binary: complete weekend off
        self.weekends: List[Tuple[int, int]] = []  # List of (Saturday, Sunday) pairs
        
        # Validate input data
        self._validate_inputs()
    
    def _validate_inputs(self) -> None:
        """Validate input data format and completeness."""
        required_cols = ['scenario', 'day', 'shift', 'demand']
        missing_cols = [col for col in required_cols if col not in self.scenarios.columns]
        if missing_cols:
            raise ValueError(f"Scenarios DataFrame missing columns: {missing_cols}")
        
        if len(self.nurses) == 0:
            raise ValueError("Nurses list cannot be empty")
        
        if len(self.scenarios) == 0:
            raise ValueError("Scenarios DataFrame cannot be empty")
        
        if self.scenarios['demand'].isnull().any():
            raise ValueError("Scenarios contain missing demand values")
        
        if (self.scenarios['demand'] < 0).any():
            raise ValueError("Demand values cannot be negative")
    
    def build(self, model_type: str = "SDM") -> None:
        """
        Build the optimization model.
        
        This method creates all decision variables, constraints, and the objective function.
        
        Args:
            model_type: 'SDM' for basic model or 'SDM-CVaR' for CVaR risk management
        
        Raises:
            ValueError: If model_type is not recognized
        """
        if model_type not in ["SDM", "SDM-CVaR"]:
            raise ValueError(f"model_type must be 'SDM' or 'SDM-CVaR', got '{model_type}'")
        
        self.model_type = model_type
        
        # Extract sets from data
        self._extract_sets()
        
        # Create PuLP problem
        self.prob = pulp.LpProblem("NurseScheduling", pulp.LpMinimize)
        
        # Build model components
        self._create_variables()
        self._add_constraints()
        self._set_objective()
    
    def _extract_sets(self) -> None:
        """Extract sets (nurses, days, shifts, scenarios) from input data."""
        self.I_nurses = self.nurses
        self.J_days = self.scenarios['day'].unique()
        self.K_shifts = self.scenarios['shift'].unique()
        self.W_scenarios = self.scenarios['scenario'].unique()
        
        # Create fast lookup dictionary for demand
        self.R_demand = self.scenarios.set_index(['day', 'shift', 'scenario'])['demand'].to_dict()
        
        # Equal probability for all scenarios
        self.scenario_probability = {w: 1.0 / len(self.W_scenarios) for w in self.W_scenarios}
        
        # Detect weekends if n4 > 0
        if self.params.n4 > 0 and self.params.start_date:
            self._detect_weekends()
    
    def _detect_weekends(self) -> None:
        """Detect weekend (Saturday-Sunday) pairs in the planning period."""
        if self.params.start_date is None:
            return
        start_dt = datetime.strptime(self.params.start_date, '%Y-%m-%d')
        self.weekends = []
        
        for day_num in self.J_days:
            current_date = start_dt + timedelta(days=int(day_num) - 1)
            if current_date.weekday() == 5:  # Saturday
                saturday = day_num
                sunday = day_num + 1
                if sunday in self.J_days:
                    self.weekends.append((saturday, sunday))
    
    def _create_variables(self) -> None:
        """Create all decision variables for the optimization model."""
        # Stage 1 variables
        self.sr = pulp.LpVariable.dicts("RegularShift",
                                       (self.I_nurses, self.J_days, self.K_shifts),
                                       cat=pulp.LpBinary)
        
        self.so = pulp.LpVariable.dicts("OvertimeShift",
                                       (self.I_nurses, self.J_days, self.K_shifts),
                                       cat=pulp.LpBinary)
        
        # Stage 2 variables (recourse)
        self.alpha = pulp.LpVariable.dicts("EmergencyStaff",
                                          (self.J_days, self.K_shifts, self.W_scenarios),
                                          lowBound=0,
                                          cat=pulp.LpContinuous)
        
        self.beta = pulp.LpVariable.dicts("Cancellation",
                                         (self.J_days, self.K_shifts, self.W_scenarios),
                                         lowBound=0,
                                         cat=pulp.LpContinuous)
        
        # Soft constraint penalty variables
        self.dev1 = pulp.LpVariable.dicts("StandAloneDeviation",
                                         (self.I_nurses, self.J_days),
                                         lowBound=0,
                                         cat=pulp.LpContinuous)
        
        self.dev2 = pulp.LpVariable.dicts("PatternDeviation",
                                         (self.I_nurses, self.J_days, self.K_shifts),
                                         lowBound=0,
                                         cat=pulp.LpContinuous)
        
        # Helper variables
        self.SR = pulp.LpVariable.dicts("WorksRegular",
                                       (self.I_nurses),
                                       cat=pulp.LpBinary)
        
        self.SO = pulp.LpVariable.dicts("WorksOvertime",
                                       (self.I_nurses),
                                       cat=pulp.LpBinary)
        
        # Weekend variables
        if self.params.n4 > 0 and self.weekends:
            self.weekend_off = pulp.LpVariable.dicts("WeekendOff",
                                                    (self.I_nurses, range(len(self.weekends))),
                                                    cat=pulp.LpBinary)
        
        # CVaR variables
        if self.model_type == "SDM-CVaR":
            self.xi = pulp.LpVariable("VaR_xi", cat=pulp.LpContinuous)
            self.z = pulp.LpVariable.dicts("ExcessLoss_z",
                                          (self.W_scenarios),
                                          lowBound=0,
                                          cat=pulp.LpContinuous)
    
    def _add_constraints(self) -> None:
        """Add all constraints to the model."""
        self._add_one_shift_per_day()
        self._add_shift_quotas()
        self._add_max_total_shifts()
        self._add_max_night_shifts()
        self._add_min_regular_shifts()
        self._add_min_weekends_off()
        self._add_night_rest_constraints()
        self._add_soft_constraints()
        self._add_helper_constraints()
        self._add_demand_coverage()
        self._add_recourse_bounds()
        self._add_cvar_constraints()
    
    def _add_one_shift_per_day(self) -> None:
        """Constraint: At most one shift per nurse per day."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        
        for i in self.I_nurses:
            for j in self.J_days:
                self.prob += (
                    pulp.lpSum(self.sr[i][j][k] + self.so[i][j][k] for k in self.K_shifts) <= 1,
                    f"OneShiftPerDay_{i}_{j}"
                )
    
    def _add_shift_quotas(self) -> None:
        """Constraints: Min/max shifts per shift type."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        
        for shift_type, quotas in self.params.shift_quotas.items():
            if shift_type in self.K_shifts:
                shift_min = quotas.get('min', 0)
                shift_max = quotas.get('max', self.params.n1)
                
                for i in self.I_nurses:
                    if shift_min > 0:
                        self.prob += (
                            pulp.lpSum(self.sr[i][j][shift_type] + self.so[i][j][shift_type] 
                                      for j in self.J_days) >= shift_min,
                            f"MinShifts_{shift_type}_{i}"
                        )
                    
                    self.prob += (
                        pulp.lpSum(self.sr[i][j][shift_type] + self.so[i][j][shift_type] 
                                  for j in self.J_days) <= shift_max,
                        f"MaxShifts_{shift_type}_{i}"
                    )
    
    def _add_max_total_shifts(self) -> None:
        """Constraint: Maximum total shifts per nurse."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        
        for i in self.I_nurses:
            self.prob += (
                pulp.lpSum(self.sr[i][j][k] + self.so[i][j][k] 
                          for j in self.J_days for k in self.K_shifts) <= self.params.n1,
                f"MaxTotalShifts_{i}"
            )
    
    def _add_max_night_shifts(self) -> None:
        """Constraint: Maximum night shifts per nurse."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        
        if 'N' in self.K_shifts:
            for i in self.I_nurses:
                self.prob += (
                    pulp.lpSum(self.sr[i][j]['N'] + self.so[i][j]['N'] 
                              for j in self.J_days) <= self.params.n2,
                    f"MaxNightShifts_{i}"
                )
    
    def _add_min_regular_shifts(self) -> None:
        """Constraint: Minimum regular (non-overtime) shifts per nurse."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        
        for i in self.I_nurses:
            self.prob += (
                pulp.lpSum(self.sr[i][j][k] 
                          for j in self.J_days for k in self.K_shifts) >= self.params.n3,
                f"MinRegularShifts_{i}"
            )
    
    def _add_min_weekends_off(self) -> None:
        """Constraint: Minimum complete weekends off."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        
        if self.params.n4 > 0 and self.weekends and self.weekend_off is not None:
            for i in self.I_nurses:
                for w_idx, (sat, sun) in enumerate(self.weekends):
                    # Weekend off = 1 only if no work on Saturday AND Sunday
                    for day in [sat, sun]:
                        if day in self.J_days:
                            self.prob += (
                                pulp.lpSum(self.sr[i][day][k] + self.so[i][day][k] 
                                          for k in self.K_shifts) <= 1 - self.weekend_off[i][w_idx],
                                f"WeekendOff_{i}_{w_idx}_{day}"
                            )
                
                # Require minimum weekends off
                self.prob += (
                    pulp.lpSum(self.weekend_off[i][w_idx] for w_idx in range(len(self.weekends))) >= self.params.n4,
                    f"MinWeekendsOff_{i}"
                )
    
    def _add_night_rest_constraints(self) -> None:
        """Constraint: Rest requirements after night shifts."""
        if not self.params.night_rest_enabled or 'N' not in self.K_shifts:
            return
        
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        
        # Add night shift rest constraints if enabled
        for i in self.I_nurses:
            for j in self.J_days:
                if j + self.params.days_off_after_nights <= max(self.J_days):
                    night_worked = self.sr[i][j]['N'] + self.so[i][j]['N']
                    for offset in range(1, self.params.days_off_after_nights + 1):
                        next_day = j + offset
                        if next_day in self.J_days:
                            self.prob += (
                                pulp.lpSum(self.sr[i][next_day][k] + self.so[i][next_day][k] 
                                          for k in self.K_shifts) <= 1 - night_worked,
                                f"NightRest_{i}_{j}_{next_day}"
                            )
    
    def _add_soft_constraints(self) -> None:
        """Soft constraints: Stand-alone shifts and unwanted patterns."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        assert self.dev1 is not None, "dev1 must be initialized"
        assert self.dev2 is not None, "dev2 must be initialized"
        
        # Stand-alone shift penalty
        for i in self.I_nurses:
            for j in self.J_days:
                if j > min(self.J_days) and j < max(self.J_days):
                    works_today = pulp.lpSum(self.sr[i][j][k] + self.so[i][j][k] for k in self.K_shifts)
                    works_yesterday = pulp.lpSum(self.sr[i][j-1][k] + self.so[i][j-1][k] for k in self.K_shifts)
                    works_tomorrow = pulp.lpSum(self.sr[i][j+1][k] + self.so[i][j+1][k] for k in self.K_shifts)
                    
                    self.prob += (
                        self.dev1[i][j] >= works_today - works_yesterday - works_tomorrow,
                        f"StandAlone_{i}_{j}"
                    )
    
    def _add_helper_constraints(self) -> None:
        """Helper binary variables for SR and SO."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        assert self.SR is not None, "SR must be initialized"
        assert self.SO is not None, "SO must be initialized"
        
        for i in self.I_nurses:
            # SR = 1 if nurse works any regular shifts
            self.prob += (
                pulp.lpSum(self.sr[i][j][k] for j in self.J_days for k in self.K_shifts) >= self.SR[i],
                f"SR_Lower_{i}"
            )
            self.prob += (
                pulp.lpSum(self.sr[i][j][k] for j in self.J_days for k in self.K_shifts) <= 
                len(self.J_days) * len(self.K_shifts) * self.SR[i],
                f"SR_Upper_{i}"
            )
            
            # SO = 1 if nurse works any overtime shifts
            self.prob += (
                pulp.lpSum(self.so[i][j][k] for j in self.J_days for k in self.K_shifts) >= self.SO[i],
                f"SO_Lower_{i}"
            )
            self.prob += (
                pulp.lpSum(self.so[i][j][k] for j in self.J_days for k in self.K_shifts) <= 
                len(self.J_days) * len(self.K_shifts) * self.SO[i],
                f"SO_Upper_{i}"
            )
    
    def _add_demand_coverage(self) -> None:
        """Constraint: Demand coverage with recourse variables."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        assert self.alpha is not None, "alpha must be initialized"
        assert self.beta is not None, "beta must be initialized"
        
        for w in self.W_scenarios:
            for j in self.J_days:
                for k in self.K_shifts:
                    demand = self.R_demand.get((j, k, w), 0)
                    
                    self.prob += (
                        pulp.lpSum(self.sr[i][j][k] + self.so[i][j][k] for i in self.I_nurses) + 
                        self.alpha[j][k][w] - self.beta[j][k][w] >= demand,
                        f"DemandCoverage_{w}_{j}_{k}"
                    )
    
    def _add_recourse_bounds(self) -> None:
        """Constraint: Bounds on recourse variables."""
        assert self.prob is not None, "prob must be initialized"
        assert self.alpha is not None, "alpha must be initialized"
        assert self.beta is not None, "beta must be initialized"
        
        for w in self.W_scenarios:
            for j in self.J_days:
                for k in self.K_shifts:
                    if self.params.max_emergency_staff < float('inf'):
                        self.prob += (
                            self.alpha[j][k][w] <= self.params.max_emergency_staff,
                            f"MaxEmergency_{w}_{j}_{k}"
                        )
                    
                    if self.params.max_cancellations < float('inf'):
                        self.prob += (
                            self.beta[j][k][w] <= self.params.max_cancellations,
                            f"MaxCancellations_{w}_{j}_{k}"
                        )
    
    def _add_cvar_constraints(self) -> None:
        """CVaR constraints (if model_type is SDM-CVaR)."""
        if self.model_type != "SDM-CVaR" or self.xi is None or self.z is None:
            return
        
        assert self.prob is not None, "prob must be initialized"
        assert self.alpha is not None, "alpha must be initialized"
        
        # Define shortage for each scenario
        for w in self.W_scenarios:
            shortage_w = pulp.lpSum(
                self.alpha[j][k][w] 
                for j in self.J_days 
                for k in self.K_shifts
            )
            
            # Excess loss: z[w] >= shortage - VaR (xi)
            self.prob += (
                self.z[w] >= shortage_w - self.xi,
                f"CVaR_ExcessLoss_{w}"
            )
        
        # CVaR upper bound constraint: VaR + (1/alpha)*E[z] <= mu
        alpha_cvar = 1 - self.params.sigma
        self.prob += (
            self.xi + (1.0 / alpha_cvar) * pulp.lpSum(
                self.scenario_probability[w] * self.z[w] 
                for w in self.W_scenarios
            ) <= self.params.mu,
            "CVaR_UpperBound"
        )
    
    def _set_objective(self) -> None:
        """Set the optimization objective function."""
        assert self.prob is not None, "prob must be initialized"
        assert self.sr is not None, "sr must be initialized"
        assert self.so is not None, "so must be initialized"
        assert self.alpha is not None, "alpha must be initialized"
        assert self.beta is not None, "beta must be initialized"
        assert self.dev1 is not None, "dev1 must be initialized"
        assert self.dev2 is not None, "dev2 must be initialized"
        
        # Stage 1 cost: regular and overtime shifts
        stage1_cost = (
            self.params.c1 * pulp.lpSum(self.sr[i][j][k] 
                                       for i in self.I_nurses 
                                       for j in self.J_days 
                                       for k in self.K_shifts) +
            self.params.c2 * pulp.lpSum(self.so[i][j][k] 
                                       for i in self.I_nurses 
                                       for j in self.J_days 
                                       for k in self.K_shifts)
        )
        
        # Penalty cost for soft constraints
        penalty_cost = (
            self.params.c3 * pulp.lpSum(self.dev1[i][j] 
                                       for i in self.I_nurses 
                                       for j in self.J_days) +
            self.params.c4 * pulp.lpSum(self.dev2[i][j][k] 
                                       for i in self.I_nurses 
                                       for j in self.J_days 
                                       for k in self.K_shifts)
        )
        
        # Stage 2 expected recourse cost
        stage2_cost = pulp.lpSum(
            self.scenario_probability[w] * (
                self.params.q_plus * self.alpha[j][k][w] + 
                self.params.q_minus * self.beta[j][k][w]
            )
            for w in self.W_scenarios
            for j in self.J_days
            for k in self.K_shifts
        )
        
        # Set objective
        self.prob += stage1_cost + penalty_cost + stage2_cost
    
    def solve(self, solver_name: str = "highs", time_limit: int = 600, mip_gap: float = 0.05, verbose: bool = False) -> str:
        """
        Solve the optimization model.
        
        Args:
            solver_name: Name of solver to use ('highs', 'cbc', etc.)
            time_limit: Maximum solve time in seconds
            mip_gap: Relative MIP gap tolerance
            verbose: Print solver output
        
        Returns:
            str: Solution status ('Optimal', 'Feasible', 'Infeasible', etc.)
        
        Raises:
            RuntimeError: If build() has not been called first
        """
        if self.prob is None:
            raise RuntimeError("Model has not been built. Call build() first.")
        
        # Create solver
        solver = create_solver(solver_name, time_limit, mip_gap, verbose=verbose)
        
        # Solve
        self.prob.solve(solver)
        self.status = pulp.LpStatus[self.prob.status]
        
        return self.status
    
    def get_results(self) -> 'OptimizationResults':
        """
        Extract and return optimization results.
        
        Returns:
            OptimizationResults: Object containing all solution data
        
        Raises:
            RuntimeError: If solve() has not been called or solution is not optimal
        """
        if self.prob is None or self.status is None:
            raise RuntimeError("Model has not been solved. Call solve() first.")
        
        if self.status != "Optimal":
            raise RuntimeError(f"Cannot extract results from non-optimal solution (status: {self.status})")
        
        # Import here to avoid circular dependency
        from model import extract_results
        
        # Use existing extraction function (temporary - will refactor later)
        results_dict = extract_results(self.prob, self.nurses, self.scenarios, self.params.to_dict())
        
        if results_dict is None:
            raise RuntimeError("Failed to extract results from the solved model")
        
        return OptimizationResults(results_dict)


class OptimizationResults:
    """
    Encapsulates optimization results with convenient accessor methods.
    
    Attributes:
        total_cost: Total optimization cost
        schedule: DataFrame with nurse schedules
        cost_breakdown: Dictionary of cost components
        coverage: DataFrame showing shift coverage
        shortage_analysis: Dictionary with shortage statistics
    """
    
    def __init__(self, results_dict: Dict[str, Any]):
        """
        Initialize from results dictionary.
        
        Args:
            results_dict: Dictionary from extract_results() function
        """
        self._data = results_dict
    
    @property
    def total_cost(self) -> float:
        """Total optimization cost."""
        return self._data['cost_breakdown']['total_cost']
    
    @property
    def schedule(self) -> pd.DataFrame:
        """Nurse schedule DataFrame."""
        return self._data['schedule']
    
    @property
    def cost_breakdown(self) -> Dict[str, float]:
        """Detailed cost breakdown."""
        return self._data['cost_breakdown']
    
    @property
    def coverage(self) -> pd.DataFrame:
        """Shift coverage analysis."""
        return self._data.get('coverage', pd.DataFrame())
    
    @property
    def shortage_per_scenario(self) -> Dict[int, float]:
        """Shortage for each scenario."""
        return self._data.get('shortage_per_scenario', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Return raw results dictionary."""
        return self._data
    
    def __repr__(self) -> str:
        """String representation."""
        return f"OptimizationResults(total_cost=${self.total_cost:.2f}, nurses={len(self.schedule)})"
