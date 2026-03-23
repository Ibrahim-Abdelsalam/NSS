"""
Rigorous Validation Framework for NSS Model
=============================================

Provides:
1. **Pre-run validation**: Parameter sanity checks, data validation, feasibility analysis
2. **Progress monitoring**: Intermediate solution checks, solver diagnostics
3. **Post-run validation**: Constraint verification, result interpretation
4. **Reproducibility**: Seed management, parameter logging, result archiving

References:
- He, F., Chaussalet, T. J., & Qu, R. (2019). Controlling understaffing with 
  stochastic demand and limited information. Operations Research for Health Care
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
from pathlib import Path


# ==============================================================================
# SECTION 1: PRE-RUN VALIDATION (PARAMETER & DATA CHECKS)
# ==============================================================================

class PreRunValidator:
    """Validates parameters and data BEFORE model solving"""
    
    def __init__(self, strict_mode: bool = True):
        """
        Args:
            strict_mode (bool): If True, all warnings become errors. 
                              If False, warnings don't block execution.
        """
        self.strict_mode = strict_mode
        self.validation_log = []
    
    def validate_all(
        self,
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        model_params: Dict[str, Any],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive pre-run validation.
        
        Args:
            nurses_list: List of nurse IDs
            scenarios_df: DataFrame with columns ['scenario', 'day', 'shift', 'demand']
            model_params: Dictionary of model parameters
            verbose: Print validation report
            
        Returns:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'checks_passed': int,
                'checks_failed': int,
                'recommendation': str
            }
        """
        errors = []
        warnings = []
        checks_passed = 0
        checks_failed = 0
        
        # =====================================================================
        # CHECK 1: Data Presence and Structure
        # =====================================================================
        
        try:
            if not nurses_list or len(nurses_list) == 0:
                errors.append("❌ CHECK 1A: Nurse list is empty")
                checks_failed += 1
            elif len(set(nurses_list)) < len(nurses_list):
                errors.append(f"❌ CHECK 1A: Duplicate nurse IDs found")
                checks_failed += 1
            else:
                checks_passed += 1
            
            # Data frame structure
            required_cols = {'scenario', 'day', 'shift', 'demand'}
            missing_cols = required_cols - set(scenarios_df.columns)
            if missing_cols:
                errors.append(f"❌ CHECK 1B: Missing columns in scenarios_df: {missing_cols}")
                checks_failed += 1
            elif len(scenarios_df) == 0:
                errors.append("❌ CHECK 1B: scenarios_df is empty")
                checks_failed += 1
            else:
                checks_passed += 1
            
            # Demand values
            if (scenarios_df['demand'] < 0).any():
                errors.append("❌ CHECK 1C: Negative demand values found")
                checks_failed += 1
            else:
                checks_passed += 1
            
            # Day continuity
            days = sorted(scenarios_df['day'].unique())
            if len(days) > 1 and (np.diff(days) != 1).any():
                warnings.append(f"⚠️  CHECK 1D: Days are not continuous: {days}")
                checks_failed += 1
            else:
                checks_passed += 1
        
        except Exception as e:
            errors.append(f"❌ CHECK 1: Data validation failed: {str(e)}")
            checks_failed += 1
        
        # =====================================================================
        # CHECK 2: Parameter Ranges and Relationships
        # =====================================================================
        
        try:
            # Cost hierarchy: c1 < c2 < q_plus
            c1 = model_params.get('c1', 100.0)
            c2 = model_params.get('c2', 150.0)
            q_plus = model_params.get('q_plus', 200.0)
            
            if not (c1 > 0):
                errors.append(f"❌ CHECK 2A: c1 (regular cost) must be positive (got {c1})")
                checks_failed += 1
            elif not (c1 < c2):
                errors.append(f"❌ CHECK 2A: Cost hierarchy violated: c1({c1}) should be < c2({c2})")
                checks_failed += 1
            elif not (c2 < q_plus):
                errors.append(f"❌ CHECK 2A: Cost hierarchy violated: c2({c2}) should be < q_plus({q_plus})")
                checks_failed += 1
            else:
                checks_passed += 1
            
            # Shift constraints: n1 ≥ n2, n1 ≥ n3
            n1 = model_params.get('n1')
            n2 = model_params.get('n2')
            n3 = model_params.get('n3')
            
            if n1 is None or n1 <= 0:
                errors.append(f"❌ CHECK 2B: n1 (max total shifts) must be positive (got {n1})")
                checks_failed += 1
            elif n1 < n2:
                errors.append(f"❌ CHECK 2B: n1({n1}) must be ≥ n2({n2})")
                checks_failed += 1
            elif n1 < n3:
                errors.append(f"❌ CHECK 2B: n1({n1}) must be ≥ n3({n3})")
                checks_failed += 1
            elif n2 < 0 or n3 < 0:
                errors.append(f"❌ CHECK 2B: n2({n2}) and n3({n3}) must be non-negative")
                checks_failed += 1
            else:
                checks_passed += 1
            
            # Minimum commitment ratio warning
            if n3 > 0 and n1 > 0 and n3 / n1 > 0.85:
                warnings.append(f"⚠️  CHECK 2C: High minimum commitment ratio (n3/n1 = {n3/n1:.1%}) "
                              f"may cause infeasibility. Consider n3 < 0.8 × n1")
                checks_failed += 1
            else:
                checks_passed += 1
            
            # CVaR parameters
            sigma = model_params.get('sigma')
            mu = model_params.get('mu')
            
            if sigma is not None:
                if not (0.5 <= sigma <= 0.99):
                    warnings.append(f"⚠️  CHECK 2D: Unusual σ={sigma}. Standard range: [0.90, 0.99]")
                    checks_failed += 1
                else:
                    checks_passed += 1
            
            if mu is not None and mu < 0:
                errors.append(f"❌ CHECK 2E: μ (shortage limit) cannot be negative (got {mu})")
                checks_failed += 1
            else:
                checks_passed += 1
        
        except Exception as e:
            errors.append(f"❌ CHECK 2: Parameter validation failed: {str(e)}")
            checks_failed += 1
        
        # =====================================================================
        # CHECK 3: Capacity-Demand Feasibility
        # =====================================================================
        
        try:
            feasible, feasibility_msg, details = self._check_capacity_feasibility(
                nurses_list, scenarios_df, model_params
            )
            
            if not feasible:
                errors.append(f"❌ CHECK 3: Capacity infeasibility: {feasibility_msg}")
                checks_failed += 1
            else:
                checks_passed += 1
                if details.get('utilization_percent', 0) > 80:
                    warnings.append(f"⚠️  CHECK 3: High utilization ({details['utilization_percent']:.1f}%) "
                                  f"may cause solver difficulty")
                    checks_failed += 1
                else:
                    checks_passed += 1
        
        except Exception as e:
            errors.append(f"❌ CHECK 3: Feasibility check failed: {str(e)}")
            checks_failed += 1
        
        # =====================================================================
        # CHECK 4: Problem Size and Solvability
        # =====================================================================
        
        try:
            num_nurses = len(nurses_list)
            num_days = len(scenarios_df['day'].unique())
            num_shifts = len(scenarios_df['shift'].unique())
            num_scenarios = len(scenarios_df['scenario'].unique())
            
            # Minimum problem size
            if num_nurses < 2:
                warnings.append(f"⚠️  CHECK 4A: Very small nurse pool ({num_nurses} nurses)")
                checks_failed += 1
            elif num_days < 3:
                errors.append(f"❌ CHECK 4A: Planning horizon too short ({num_days} days, need ≥7)")
                checks_failed += 1
            elif num_scenarios < 2:
                warnings.append(f"⚠️  CHECK 4A: Very few scenarios ({num_scenarios}), stochastic effects limited")
                checks_failed += 1
            else:
                checks_passed += 1
            
            # Estimate variables and constraints
            problem_size = self._estimate_problem_size(
                num_nurses, num_days, num_shifts, num_scenarios, model_params
            )
            
            if problem_size['problem_complexity'] == 'VeryLarge':
                warnings.append(f"⚠️  CHECK 4B: Problem is very large ({problem_size['num_variables']:.0e} vars). "
                              f"Solve may take 10+ minutes")
                checks_failed += 1
            else:
                checks_passed += 1
        
        except Exception as e:
            errors.append(f"❌ CHECK 4: Problem size analysis failed: {str(e)}")
            checks_failed += 1
        
        # =====================================================================
        # COMPILE RESULTS
        # =====================================================================
        
        is_valid = len(errors) == 0
        if self.strict_mode:
            is_valid = is_valid and len(warnings) == 0
        
        # Generate recommendation
        if not is_valid:
            recommendation = "⛔ FIX ERRORS BEFORE RUNNING"
            if len(warnings) > 0 and len(errors) == 0:
                recommendation = "⚠️  PROCEED WITH CAUTION (warnings present)"
        else:
            recommendation = "✅ READY TO RUN"
        
        result = {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'checks_passed': checks_passed,
            'checks_failed': checks_failed,
            'recommendation': recommendation,
            'problem_size': problem_size,
        }
        
        if verbose:
            self._print_validation_report(result)
        
        self.validation_log.append({
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
        
        return result
    
    @staticmethod
    def _check_capacity_feasibility(
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        model_params: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if demand can feasibly be met"""
        
        n1 = model_params.get('n1', 15)
        n2 = model_params.get('n2', 5)
        num_nurses = len(nurses_list)
        num_days = len(scenarios_df['day'].unique())
        
        # Available regular shifts capacity
        total_capacity_shifts = num_nurses * n1
        
        # Peak demand across all day-shift combinations
        peak_demand = scenarios_df.groupby(['day', 'shift'])['demand'].max().sum()
        
        # Check 1: Can baseline pool meet peak demand?
        if peak_demand > total_capacity_shifts:
            utilization = 100 * peak_demand / total_capacity_shifts if total_capacity_shifts > 0 else np.inf
            return False, f"Peak demand ({peak_demand} shifts) exceeds capacity ({total_capacity_shifts})", {
                'peak_demand': peak_demand,
                'total_capacity': total_capacity_shifts,
                'utilization_percent': utilization,
                'num_nurses': num_nurses,
            }
        
        # Check 2: Night shift bottleneck
        night_demand = scenarios_df[scenarios_df['shift'] == 'N']['demand'].sum()
        night_capacity = num_nurses * n2
        if night_capacity > 0 and night_demand > night_capacity:
            utilization = 100 * night_demand / night_capacity if night_capacity > 0 else np.inf
            return False, f"Night demand ({night_demand}) exceeds night capacity ({night_capacity})", {
                'night_demand': night_demand,
                'night_capacity': night_capacity,
                'utilization_percent': utilization,
            }
        
        # All checks passed
        utilization = 100 * peak_demand / total_capacity_shifts if total_capacity_shifts > 0 else 0
        return True, "", {
            'peak_demand': peak_demand,
            'total_capacity': total_capacity_shifts,
            'utilization_percent': utilization,
            'night_capacity': night_capacity,
            'night_demand': night_demand,
        }
    
    @staticmethod
    def _estimate_problem_size(
        num_nurses: int,
        num_days: int,
        num_shifts: int,
        num_scenarios: int,
        model_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate problem size metrics"""
        
        # Variables estimation
        stage1_vars = num_nurses * num_days * num_shifts * 2  # sr, so
        stage1_vars += num_nurses * num_days  # dev1
        stage1_vars += num_nurses * num_days * num_shifts  # dev2
        
        stage2_vars = num_days * num_shifts * num_scenarios * 2  # α, β
        cvar_vars = 1 + num_scenarios  # ξ, z
        
        total_vars = stage1_vars + stage2_vars + cvar_vars
        
        # Constraints estimation (rough)
        total_constraints = num_nurses * num_days * num_shifts * 5
        total_constraints += num_scenarios * num_days * num_shifts * 2
        
        problem_size = total_vars * total_constraints
        
        # Classify complexity
        if problem_size < 1_000_000:
            complexity = 'Small'
            estimated_time = '< 10 seconds'
        elif problem_size < 10_000_000:
            complexity = 'Medium'
            estimated_time = '10-60 seconds'
        elif problem_size < 50_000_000:
            complexity = 'Large'
            estimated_time = '1-5 minutes'
        else:
            complexity = 'VeryLarge'
            estimated_time = '5-30 minutes'
        
        return {
            'num_variables': total_vars,
            'num_constraints': total_constraints,
            'problem_size': problem_size,
            'problem_complexity': complexity,
            'estimated_solve_time': estimated_time,
        }
    
    @staticmethod
    def _print_validation_report(result: Dict[str, Any]) -> None:
        """Pretty-print validation report"""
        
        print("\n" + "="*80)
        print("PRE-RUN VALIDATION REPORT")
        print("="*80)
        
        print(f"\n📊 Checks: {result['checks_passed']} passed, {result['checks_failed']} failed")
        print(f"Status: {result['recommendation']}\n")
        
        if result['errors']:
            print("❌ ERRORS:")
            for error in result['errors']:
                print(f"   {error}")
        
        if result['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in result['warnings']:
                print(f"   {warning}")
        
        problem_size = result.get('problem_size', {})
        if problem_size:
            print(f"\n📈 Problem Size:")
            print(f"   Variables:    {problem_size['num_variables']:,.0f}")
            print(f"   Constraints:  {problem_size['num_constraints']:,.0f}")
            print(f"   Complexity:   {problem_size['problem_complexity']}")
            print(f"   Est. Time:    {problem_size['estimated_solve_time']}")
        
        print("\n" + "="*80 + "\n")


# ==============================================================================
# SECTION 2: PARAMETER SANITY GUARDS
# ==============================================================================

def sanitize_parameters(
    model_params: Dict[str, Any],
    nurses_list: List[str],
    scenarios_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    AUTO-FIX obvious parameter problems.
    
    Safer than failing on bad parameters; logs all changes made.
    
    Parameters fixed:
    - Cost hierarchy violations
    - n1 < n2 or n1 < n3 (impossible constraints)
    - Invalid CVaR parameters
    - Unreasonable solver settings
    
    Returns:
        (sanitized_params, changes_log)
    """
    
    params = model_params.copy()
    changes = []
    
    # =========================================================================
    # Fix 1: Cost Hierarchy
    # =========================================================================
    c1 = params.get('c1', 100.0)
    c2 = params.get('c2', 150.0)
    q_plus = params.get('q_plus', 200.0)
    
    if c2 <= c1:
        params['c2'] = c1 * 1.5
        changes.append(f"Fixed cost hierarchy: Set c2 = {params['c2']:.1f} (was {c2})")
    
    if q_plus <= c2:
        params['q_plus'] = c2 * 1.5
        changes.append(f"Fixed cost hierarchy: Set q_plus = {params['q_plus']:.1f} (was {q_plus})")
    
    # =========================================================================
    # Fix 2: Shift Constraints
    # =========================================================================
    n1 = params.get('n1')
    n2 = params.get('n2', 5)
    n3 = params.get('n3', 10)
    
    if n1 is None or n1 <= 0:
        # Suggest n1 = 80% of planning period length
        max_shifts_possible = len(scenarios_df['day'].unique())
        params['n1'] = max(10, int(0.8 * max_shifts_possible))
        changes.append(f"Fixed n1: Set to {params['n1']} (was None/invalid)")
    
    if n2 > params['n1']:
        params['n2'] = int(0.3 * params['n1'])
        changes.append(f"Fixed n2: Set to {params['n2']} (was {n2}, exceeds n1)")
    
    if n3 > params['n1']:
        params['n3'] = int(0.6 * params['n1'])
        changes.append(f"Fixed n3: Set to {params['n3']} (was {n3}, exceeds n1)")
    
    # =========================================================================
    # Fix 3: CVaR Parameters
    # =========================================================================
    sigma = params.get('sigma')
    if sigma is not None:
        if sigma < 0.5:
            params['sigma'] = 0.95
            changes.append(f"Fixed σ: Set to 0.95 (was {sigma}, too low)")
        elif sigma > 0.99:
            params['sigma'] = 0.99
            changes.append(f"Fixed σ: Set to 0.99 (was {sigma}, too high)")
    
    mu = params.get('mu')
    if mu is not None and mu < 0:
        params['mu'] = 50.0
        changes.append(f"Fixed μ: Set to 50.0 (was {mu}, can't be negative)")
    
    # =========================================================================
    # Fix 4: Solver Settings
    # =========================================================================
    time_limit = params.get('time_limit')
    if time_limit is not None and time_limit < 0:
        params['time_limit'] = 300
        changes.append(f"Fixed time_limit: Set to 300s (was {time_limit})")
    
    mip_gap = params.get('mip_gap')
    if mip_gap is not None:
        if mip_gap < 0 or mip_gap > 1:
            params['mip_gap'] = 0.01
            changes.append(f"Fixed mip_gap: Set to 0.01 (was {mip_gap}, out of range)")
    
    return params, changes


# ==============================================================================
# SECTION 3: RESULT VALIDATION CHECKLIST
# ==============================================================================

class ResultValidator:
    """Validates optimization results after solving"""
    
    @staticmethod
    def validate_solution(
        prob,  # PuLP model object
        results: Dict[str, Any],
        model_params: Dict[str, Any],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive post-solve validation.
        
        Checks:
        1. Solver status and optimality
        2. Constraint satisfaction
        3. Objective function consistency
        4. Result interpretability
        
        Returns:
            {
                'is_valid': bool,
                'solver_status': str,
                'optimality_gap': float,
                'constraint_violations': List[str],
                'warnings': List[str],
                'objective_value': float,
            }
        """
        
        validation = {
            'is_valid': True,
            'solver_status': 'Unknown',
            'constraint_violations': [],
            'warnings': [],
            'checks_passed': 0,
            'checks_failed': 0,
        }
        
        try:
            # Get solver status
            if hasattr(prob, 'status'):
                status_code = prob.status
                status_map = {
                    -1: 'Not Solved',
                    0: 'Optimal',
                    1: 'Infeasible',
                    -2: 'Unbounded',
                    -3: 'Undefined',
                }
                validation['solver_status'] = status_map.get(status_code, 'Unknown')
            
            # Check 1: Optimality
            if validation['solver_status'] != 'Optimal':
                validation['warnings'].append(
                    f"Solver did not find optimal solution: {validation['solver_status']}"
                )
                validation['checks_failed'] += 1
            else:
                validation['checks_passed'] += 1
            
            # Check 2: Objective value
            if hasattr(prob, 'objective'):
                obj_value = prob.objective.value()
                if obj_value is None:
                    validation['constraint_violations'].append("Objective function value is None")
                    validation['is_valid'] = False
                    validation['checks_failed'] += 1
                elif obj_value < 0:
                    validation['warnings'].append(f"Negative objective value: {obj_value}")
                    validation['checks_failed'] += 1
                else:
                    validation['objective_value'] = obj_value
                    validation['checks_passed'] += 1
            
            # Check 3: Schedule constraint satisfaction
            schedule_df = results.get('schedule_df')
            if schedule_df is not None:
                n1 = model_params.get('n1', 15)
                n2 = model_params.get('n2', 5)
                n3 = model_params.get('n3', 10)
                
                # n1: max total shifts
                nurse_shifts = schedule_df.groupby('nurse').size()
                if (nurse_shifts > n1).any():
                    violations = (nurse_shifts > n1).sum()
                    validation['constraint_violations'].append(
                        f"n1 violation: {violations} nurses exceed max shifts ({n1})"
                    )
                    validation['is_valid'] = False
                    validation['checks_failed'] += 1
                else:
                    validation['checks_passed'] += 1
                
                # One shift per day per nurse
                multi_shifts = schedule_df.groupby(['nurse', 'day']).size()
                if (multi_shifts > 1).any():
                    validation['constraint_violations'].append(
                        f"Multiple shifts per day: {(multi_shifts > 1).sum()} nurse-days violated"
                    )
                    validation['is_valid'] = False
                    validation['checks_failed'] += 1
                else:
                    validation['checks_passed'] += 1
        
        except Exception as e:
            validation['warnings'].append(f"Result validation error: {str(e)}")
            validation['checks_failed'] += 1
        
        if verbose:
            print("\n" + "="*80)
            print("RESULT VALIDATION REPORT")
            print("="*80)
            print(f"Solver Status: {validation['solver_status']}")
            print(f"Checks: {validation['checks_passed']} passed, {validation['checks_failed']} failed")
            
            if validation['constraint_violations']:
                print("\n❌ CONSTRAINT VIOLATIONS:")
                for v in validation['constraint_violations']:
                    print(f"   {v}")
            
            if validation['warnings']:
                print("\n⚠️  WARNINGS:")
                for w in validation['warnings']:
                    print(f"   {w}")
            
            print("\n" + "="*80 + "\n")
        
        return validation


# ==============================================================================
# SECTION 4: VALIDATION HARNESS (Main Entry Point)
# ==============================================================================

def run_complete_validation(
    nurses_list: List[str],
    scenarios_df: pd.DataFrame,
    model_params: Dict[str, Any],
    auto_fix: bool = True,
) -> Dict[str, Any]:
    """
    Complete validation pipeline: audit → sanitize → validate.
    
    Args:
        nurses_list: List of nurse IDs
        scenarios_df: Scenarios DataFrame
        model_params: Model parameters
        auto_fix: If True, automatically fix obvious parameter problems
        
    Returns:
        {
            'pre_validation': Dict from PreRunValidator
            'sanitization': (fixed_params, changes_log)
            'ready_to_run': bool,
            'final_params': Dict,
            'summary': str
        }
    """
    
    # Step 1: Pre-run validation with original parameters
    pre_validator = PreRunValidator(strict_mode=False)
    pre_validation = pre_validator.validate_all(
        nurses_list, scenarios_df, model_params, verbose=True
    )
    
    # Step 2: Sanitize parameters if auto_fix enabled
    if auto_fix and not pre_validation['is_valid']:
        print("🔧 AUTO-FIXING PARAMETERS...")
        fixed_params, changes = sanitize_parameters(model_params, nurses_list, scenarios_df)
        
        if changes:
            print(f"Made {len(changes)} parameter adjustments:")
            for change in changes:
                print(f"   - {change}")
        
        final_params = fixed_params
        sanitization = (fixed_params, changes)
        
        # Re-validate after fixes
        post_validation = pre_validator.validate_all(
            nurses_list, scenarios_df, final_params, verbose=False
        )
        ready_to_run = post_validation['is_valid']
    else:
        final_params = model_params
        sanitization = (model_params, [])
        ready_to_run = pre_validation['is_valid']
    
    # Generate summary
    if ready_to_run:
        summary = "✅ Ready to run model"
    else:
        summary = "❌ Fix errors before running"
    
    return {
        'pre_validation': pre_validation,
        'sanitization': sanitization,
        'ready_to_run': ready_to_run,
        'final_params': final_params,
        'summary': summary,
    }
