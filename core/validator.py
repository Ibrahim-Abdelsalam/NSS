"""Validation utilities for the NSS core layer."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from core import SolveResult, ValidationResult


class ParameterValidator:
    """Validate model inputs and outputs for the nurse scheduling system."""

    def __init__(self, strict_mode: bool = True):
        """Initialize the validator."""
        self.strict_mode = strict_mode
        self.validation_log: list[dict[str, Any]] = []
        self.last_changes: list[str] = []

    def validate_inputs(
        self,
        params: Dict[str, Any],
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        verbose: bool = True,
    ) -> ValidationResult:
        """Validate parameters and input data before solving."""
        pre_validation = self._validate_all(nurses_list, scenarios_df, params, verbose=verbose)
        sanitized_params = None

        if not pre_validation.is_valid and self.strict_mode is False:
            sanitized_params = self.sanitize(params, nurses_list, scenarios_df)
            post_validation = self._validate_all(nurses_list, scenarios_df, sanitized_params, verbose=False)
            if post_validation.is_valid:
                pre_validation = post_validation

        return ValidationResult(
            is_valid=pre_validation.is_valid,
            errors=pre_validation.errors,
            warnings=pre_validation.warnings,
            sanitized_params=sanitized_params,
        )

    def validate_outputs(
        self,
        result: SolveResult,
        verbose: bool = True,
    ) -> ValidationResult:
        """Validate the high-level solve result after optimization."""
        errors: list[str] = []
        warnings: list[str] = []

        if result.status not in {"Optimal", "Feasible", "Infeasible"}:
            warnings.append(f"Unexpected solve status: {result.status}")

        if result.objective_value is None:
            errors.append("Objective value is missing")

        if result.solve_time_seconds < 0:
            errors.append("Solve time cannot be negative")

        if not result.solver_name:
            errors.append("Solver name is missing")

        is_valid = len(errors) == 0
        if verbose:
            self._print_output_validation_report(result, errors, warnings)

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_params=None,
        )

    def sanitize(
        self,
        params: Dict[str, Any],
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Auto-fix obvious parameter problems."""
        sanitized_params, changes = self._sanitize_parameters(params, nurses_list, scenarios_df)
        self.last_changes = changes
        return sanitized_params

    def _validate_all(
        self,
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        model_params: Dict[str, Any],
        verbose: bool = True,
    ) -> ValidationResult:
        """Run the full pre-run validation suite."""
        errors: list[str] = []
        warnings: list[str] = []
        checks_passed = 0
        checks_failed = 0
        problem_size: Dict[str, Any] = {}

        try:
            if not nurses_list or len(nurses_list) == 0:
                errors.append("CHECK 1A: Nurse list is empty")
                checks_failed += 1
            elif len(set(nurses_list)) < len(nurses_list):
                errors.append("CHECK 1A: Duplicate nurse IDs found")
                checks_failed += 1
            else:
                checks_passed += 1

            required_cols = {"scenario", "day", "shift", "demand"}
            missing_cols = required_cols - set(scenarios_df.columns)
            if missing_cols:
                errors.append(f"CHECK 1B: Missing columns in scenarios_df: {missing_cols}")
                checks_failed += 1
            elif len(scenarios_df) == 0:
                errors.append("CHECK 1B: scenarios_df is empty")
                checks_failed += 1
            else:
                checks_passed += 1

            if (scenarios_df["demand"] < 0).any():
                errors.append("CHECK 1C: Negative demand values found")
                checks_failed += 1
            else:
                checks_passed += 1

            days = sorted(scenarios_df["day"].unique())
            if len(days) > 1 and (np.diff(days) != 1).any():
                warnings.append(f"CHECK 1D: Days are not continuous: {days}")
                checks_failed += 1
            else:
                checks_passed += 1

        except Exception as e:
            errors.append(f"CHECK 1: Data validation failed: {str(e)}")
            checks_failed += 1

        try:
            c1 = model_params.get("c1", 100.0)
            c2 = model_params.get("c2", 150.0)
            q_plus = model_params.get("q_plus", 200.0)

            if not (c1 > 0):
                errors.append(f"CHECK 2A: c1 (regular cost) must be positive (got {c1})")
                checks_failed += 1
            elif not (c1 < c2):
                errors.append(f"CHECK 2A: Cost hierarchy violated: c1({c1}) should be < c2({c2})")
                checks_failed += 1
            elif not (c2 < q_plus):
                errors.append(f"CHECK 2A: Cost hierarchy violated: c2({c2}) should be < q_plus({q_plus})")
                checks_failed += 1
            else:
                checks_passed += 1

            n1 = model_params.get("n1")
            n2 = model_params.get("n2")
            n3 = model_params.get("n3")

            if n1 is None or n1 <= 0:
                errors.append(f"CHECK 2B: n1 (max total shifts) must be positive (got {n1})")
                checks_failed += 1
            elif n1 < n2:
                errors.append(f"CHECK 2B: n1({n1}) must be ≥ n2({n2})")
                checks_failed += 1
            elif n1 < n3:
                errors.append(f"CHECK 2B: n1({n1}) must be ≥ n3({n3})")
                checks_failed += 1
            elif n2 < 0 or n3 < 0:
                errors.append(f"CHECK 2B: n2({n2}) and n3({n3}) must be non-negative")
                checks_failed += 1
            else:
                checks_passed += 1

            if n3 > 0 and n1 > 0 and n3 / n1 > 0.85:
                warnings.append(
                    f"CHECK 2C: High minimum commitment ratio (n3/n1 = {n3/n1:.1%}) "
                    f"may cause infeasibility. Consider n3 < 0.8 × n1"
                )
                checks_failed += 1
            else:
                checks_passed += 1

            sigma = model_params.get("sigma")
            mu = model_params.get("mu")

            if sigma is not None:
                if not (0.5 <= sigma <= 0.99):
                    warnings.append(f"CHECK 2D: Unusual σ={sigma}. Standard range: [0.90, 0.99]")
                    checks_failed += 1
                else:
                    checks_passed += 1

            if mu is not None and mu < 0:
                errors.append(f"CHECK 2E: μ (shortage limit) cannot be negative (got {mu})")
                checks_failed += 1
            else:
                checks_passed += 1

        except Exception as e:
            errors.append(f"CHECK 2: Parameter validation failed: {str(e)}")
            checks_failed += 1

        try:
            feasible, feasibility_msg, details = self._check_capacity_feasibility(
                nurses_list, scenarios_df, model_params
            )

            if not feasible:
<<<<<<< HEAD
                warnings.append(f"CHECK 3: Capacity warning: {feasibility_msg} (Recourse/emergency staff will be used)")
                checks_passed += 1
=======
                errors.append(f"CHECK 3: Capacity infeasibility: {feasibility_msg}")
                checks_failed += 1
>>>>>>> 74ea8bacae8f330b86ef6f5e56f1ba7ab4858ff5
            else:
                checks_passed += 1
                if details.get("utilization_percent", 0) > 80:
                    warnings.append(
                        f"CHECK 3: High utilization ({details['utilization_percent']:.1f}%) "
                        f"may cause solver difficulty"
                    )
                    checks_failed += 1
                else:
                    checks_passed += 1

        except Exception as e:
            errors.append(f"CHECK 3: Feasibility check failed: {str(e)}")
            checks_failed += 1

        try:
            num_nurses = len(nurses_list)
            num_days = len(scenarios_df["day"].unique())
            num_shifts = len(scenarios_df["shift"].unique())
            num_scenarios = len(scenarios_df["scenario"].unique())

            if num_nurses < 2:
                warnings.append(f"CHECK 4A: Very small nurse pool ({num_nurses} nurses)")
                checks_failed += 1
            elif num_days < 3:
                errors.append(f"CHECK 4A: Planning horizon too short ({num_days} days, need ≥7)")
                checks_failed += 1
            elif num_scenarios < 2:
                warnings.append(f"CHECK 4A: Very few scenarios ({num_scenarios}), stochastic effects limited")
                checks_failed += 1
            else:
                checks_passed += 1

            problem_size = self._estimate_problem_size(
                num_nurses, num_days, num_shifts, num_scenarios, model_params
            )

            if problem_size["problem_complexity"] == "VeryLarge":
                warnings.append(
                    f"CHECK 4B: Problem is very large ({problem_size['num_variables']:.0e} vars). "
                    f"Solve may take 10+ minutes"
                )
                checks_failed += 1
            else:
                checks_passed += 1

        except Exception as e:
            errors.append(f"CHECK 4: Problem size analysis failed: {str(e)}")
            checks_failed += 1

        is_valid = len(errors) == 0
        if self.strict_mode:
            is_valid = is_valid and len(warnings) == 0

        if not is_valid:
            recommendation = "FIX ERRORS BEFORE RUNNING"
            if len(warnings) > 0 and len(errors) == 0:
                recommendation = "PROCEED WITH CAUTION (warnings present)"
        else:
            recommendation = "READY TO RUN"

        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_params=None,
        )

        if verbose:
            self._print_validation_report(
                {
                    "is_valid": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "checks_passed": checks_passed,
                    "checks_failed": checks_failed,
                    "recommendation": recommendation,
                    "problem_size": problem_size,
                }
            )

        self.validation_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "result": {
                    "is_valid": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "checks_passed": checks_passed,
                    "checks_failed": checks_failed,
                    "recommendation": recommendation,
                    "problem_size": problem_size,
                },
            }
        )

        return result

    @staticmethod
    def _check_capacity_feasibility(
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        model_params: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if demand can feasibly be met."""
        n1 = model_params.get("n1", 15)
        n2 = model_params.get("n2", 5)
        num_nurses = len(nurses_list)
        num_days = len(scenarios_df["day"].unique())

        total_capacity_shifts = num_nurses * n1
        peak_demand = scenarios_df.groupby(["day", "shift"])["demand"].max().sum()

        if peak_demand > total_capacity_shifts:
            utilization = 100 * peak_demand / total_capacity_shifts if total_capacity_shifts > 0 else np.inf
            return False, f"Peak demand ({peak_demand} shifts) exceeds capacity ({total_capacity_shifts})", {
                "peak_demand": peak_demand,
                "total_capacity": total_capacity_shifts,
                "utilization_percent": utilization,
                "num_nurses": num_nurses,
            }

        # Note: night_demand is summed across scenarios/days; n2 is per-nurse max nights
        # A direct sum vs per-nurse cap comparison is informational only — not a hard block.
        night_demand = scenarios_df[scenarios_df["shift"] == "N"]["demand"].sum()
        night_capacity = num_nurses * n2

        utilization = 100 * peak_demand / total_capacity_shifts if total_capacity_shifts > 0 else 0
        return True, "", {
            "peak_demand": peak_demand,
            "total_capacity": total_capacity_shifts,
            "utilization_percent": utilization,
            "night_capacity": night_capacity,
            "night_demand": night_demand,
        }

    @staticmethod
    def _estimate_problem_size(
        num_nurses: int,
        num_days: int,
        num_shifts: int,
        num_scenarios: int,
        model_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Estimate problem size metrics."""
        stage1_vars = num_nurses * num_days * num_shifts * 2
        stage1_vars += num_nurses * num_days
        stage1_vars += num_nurses * num_days * num_shifts

        stage2_vars = num_days * num_shifts * num_scenarios * 2
        cvar_vars = 1 + num_scenarios

        total_vars = stage1_vars + stage2_vars + cvar_vars
        total_constraints = num_nurses * num_days * num_shifts * 5
        total_constraints += num_scenarios * num_days * num_shifts * 2

        problem_size = total_vars * total_constraints

        if problem_size < 1_000_000:
            complexity = "Small"
            estimated_time = "< 10 seconds"
        elif problem_size < 10_000_000:
            complexity = "Medium"
            estimated_time = "10-60 seconds"
        elif problem_size < 50_000_000:
            complexity = "Large"
            estimated_time = "1-5 minutes"
        else:
            complexity = "VeryLarge"
            estimated_time = "5-30 minutes"

        return {
            "num_variables": total_vars,
            "num_constraints": total_constraints,
            "problem_size": problem_size,
            "problem_complexity": complexity,
            "estimated_solve_time": estimated_time,
        }

    @staticmethod
    def _print_validation_report(result: Dict[str, Any]) -> None:
        """Pretty-print validation report."""
        print("\n" + "=" * 80)
        print("PRE-RUN VALIDATION REPORT")
        print("=" * 80)

        print(f"\nChecks: {result['checks_passed']} passed, {result['checks_failed']} failed")
        print(f"Status: {result['recommendation']}\n")

        if result["errors"]:
            print("ERRORS:")
            for error in result["errors"]:
                print(f"   {error}")

        if result["warnings"]:
            print("\nWARNINGS:")
            for warning in result["warnings"]:
                print(f"   {warning}")

        problem_size = result.get("problem_size", {})
        if problem_size:
            print("\nProblem Size:")
            print(f"   Variables:    {problem_size['num_variables']:,.0f}")
            print(f"   Constraints:  {problem_size['num_constraints']:,.0f}")
            print(f"   Complexity:   {problem_size['problem_complexity']}")
            print(f"   Est. Time:    {problem_size['estimated_solve_time']}")

        print("\n" + "=" * 80 + "\n")

    def _sanitize_parameters(
        self,
        model_params: Dict[str, Any],
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Auto-fix obvious parameter problems."""
        params = model_params.copy()
        changes: list[str] = []

        c1 = params.get("c1", 100.0)
        c2 = params.get("c2", 150.0)
        q_plus = params.get("q_plus", 200.0)

        if c2 <= c1:
            params["c2"] = c1 * 1.5
            changes.append(f"Fixed cost hierarchy: Set c2 = {params['c2']:.1f} (was {c2})")

        if q_plus <= c2:
            params["q_plus"] = c2 * 1.5
            changes.append(f"Fixed cost hierarchy: Set q_plus = {params['q_plus']:.1f} (was {q_plus})")

        n1 = params.get("n1")
        n2 = params.get("n2", 5)
        n3 = params.get("n3", 10)

        if n1 is None or n1 <= 0:
            max_shifts_possible = len(scenarios_df["day"].unique())
            params["n1"] = max(10, int(0.8 * max_shifts_possible))
            changes.append(f"Fixed n1: Set to {params['n1']} (was None/invalid)")

        if n2 > params["n1"]:
            params["n2"] = int(0.3 * params["n1"])
            changes.append(f"Fixed n2: Set to {params['n2']} (was {n2}, exceeds n1)")

        if n3 > params["n1"]:
            params["n3"] = int(0.6 * params["n1"])
            changes.append(f"Fixed n3: Set to {params['n3']} (was {n3}, exceeds n1)")

        sigma = params.get("sigma")
        if sigma is not None:
            if sigma < 0.5:
                params["sigma"] = 0.95
                changes.append(f"Fixed σ: Set to 0.95 (was {sigma}, too low)")
            elif sigma > 0.99:
                params["sigma"] = 0.99
                changes.append(f"Fixed σ: Set to 0.99 (was {sigma}, too high)")

        mu = params.get("mu")
        if mu is not None and mu < 0:
            params["mu"] = 50.0
            changes.append(f"Fixed μ: Set to 50.0 (was {mu}, can't be negative)")

        time_limit = params.get("time_limit")
        if time_limit is not None and time_limit < 0:
            params["time_limit"] = 300
            changes.append(f"Fixed time_limit: Set to 300s (was {time_limit})")

        mip_gap = params.get("mip_gap")
        if mip_gap is not None:
            if mip_gap < 0 or mip_gap > 1:
                params["mip_gap"] = 0.01
                changes.append(f"Fixed mip_gap: Set to 0.01 (was {mip_gap}, out of range)")

        return params, changes

    def _print_output_validation_report(
        self,
        result: SolveResult,
        errors: List[str],
        warnings: List[str],
    ) -> None:
        """Pretty-print solve-result validation output."""
        print("\n" + "=" * 80)
        print("RESULT VALIDATION REPORT")
        print("=" * 80)
        print(f"Status: {result.status}")
        print(f"Objective: {result.objective_value}")
        print(f"Solve Time: {result.solve_time_seconds:.2f}s")

        if errors:
            print("\nERRORS:")
            for error in errors:
                print(f"   {error}")

        if warnings:
            print("\nWARNINGS:")
            for warning in warnings:
                print(f"   {warning}")

        print("\n" + "=" * 80 + "\n")


def sanitize_parameters(
    model_params: Dict[str, Any],
    nurses_list: List[str],
    scenarios_df: pd.DataFrame,
) -> Tuple[Dict[str, Any], List[str]]:
    """Backward-compatible module-level sanitization helper."""
    validator = ParameterValidator(strict_mode=False)
    return validator._sanitize_parameters(model_params, nurses_list, scenarios_df)


def run_complete_validation(
    nurses_list: List[str],
    scenarios_df: pd.DataFrame,
    model_params: Dict[str, Any],
    auto_fix: bool = True,
) -> Dict[str, Any]:
    """Backward-compatible validation harness."""
    validator = ParameterValidator(strict_mode=False)
    pre_validation = validator._validate_all(nurses_list, scenarios_df, model_params, verbose=True)

    if auto_fix and not pre_validation.is_valid:
        print("🔧 AUTO-FIXING PARAMETERS...")
        fixed_params, changes = validator._sanitize_parameters(model_params, nurses_list, scenarios_df)

        if changes:
            print(f"Made {len(changes)} parameter adjustments:")
            for change in changes:
                print(f"   - {change}")

        final_params = fixed_params
        sanitization = (fixed_params, changes)
        post_validation = validator._validate_all(nurses_list, scenarios_df, final_params, verbose=False)
        ready_to_run = post_validation.is_valid
    else:
        final_params = model_params
        sanitization = (model_params, [])
        ready_to_run = pre_validation.is_valid

    summary = "Ready to run model" if ready_to_run else "Fix errors before running"

    return {
        "pre_validation": {
            "is_valid": pre_validation.is_valid,
            "errors": pre_validation.errors,
            "warnings": pre_validation.warnings,
        },
        "sanitization": sanitization,
        "ready_to_run": ready_to_run,
        "final_params": final_params,
        "summary": summary,
    }


class PreRunValidator:
    """Backward-compatible wrapper for pre-run validation."""

    def __init__(self, strict_mode: bool = True):
        self.validator = ParameterValidator(strict_mode=strict_mode)

    def validate_all(
        self,
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        model_params: Dict[str, Any],
        verbose: bool = True,
    ) -> Dict[str, Any]:
        result = self.validator.validate_inputs(model_params, nurses_list, scenarios_df, verbose=verbose)
        return {
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "sanitized_params": result.sanitized_params,
        }


class ResultValidator:
    """Backward-compatible wrapper for post-solve validation."""

    @staticmethod
    def validate_solution(
        prob: Any,
        results: Dict[str, Any],
        model_params: Dict[str, Any],
        verbose: bool = True,
    ) -> Dict[str, Any]:
        status = results.get("status", "Unknown")
        objective_value = results.get("objective_value")
        solve_time_seconds = float(model_params.get("solve_time_seconds", 0.0))
        solver_name = model_params.get("solver_name", "AUTO")

        mock_result = SolveResult(
            status=status,
            objective_value=objective_value,
            solve_time_seconds=solve_time_seconds,
            solver_name=solver_name,
            variable_values={},
            metadata={},
        )
        validator = ParameterValidator(strict_mode=False)
        result = validator.validate_outputs(mock_result, verbose=verbose)

        return {
            "is_valid": result.is_valid,
            "solver_status": status,
            "optimality_gap": 0.0,
            "constraint_violations": result.errors,
            "warnings": result.warnings,
        }
