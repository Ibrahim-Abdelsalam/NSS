"""Result extraction utilities for the NSS core layer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import pandas as pd

from core import SolveResult


class ResultExtractor:
    """Extract schedule, cost, coverage, and fatigue summaries from a solved model."""

    def __init__(self, model: Any, solve_result: SolveResult):
        """Initialize the extractor with a solved model and solve result."""
        self.model = model
        self.solve_result = solve_result
        self._cache: Optional[Dict[str, Any]] = None

    @property
    def nurses_list(self) -> List[str]:
        """Return the nurse identifiers used by the model."""
        return list(getattr(self.model, "nurses_list", []))

    @property
    def scenarios_df(self) -> pd.DataFrame:
        """Return the scenarios dataframe used by the model."""
        return getattr(self.model, "scenarios_df", pd.DataFrame())

    @property
    def model_params(self) -> Dict[str, Any]:
        """Return the model parameters used for the solve."""
        return dict(getattr(self.model, "parameters", {}))

    @property
    def model_type(self) -> str:
        """Return the model type associated with the solved instance."""
        metadata = self.solve_result.metadata or {}
        return metadata.get("model_type", getattr(self.model, "model_type", "SDM"))

    def get_schedule_df(self) -> pd.DataFrame:
        """Return the schedule dataframe extracted from the solve result."""
        return self._extract_all()["schedule_df"]

    def get_cost_summary(self) -> Dict[str, Any]:
        """Return the cost breakdown extracted from the solve result."""
        return self._extract_all()["cost_breakdown"]

    def get_coverage_summary(self) -> pd.DataFrame:
        """Return the daily coverage summary extracted from the solve result."""
        return self._extract_all()["coverage_df"]

    def get_fatigue_summary(self) -> pd.DataFrame:
        """Return the fatigue summary extracted from the solve result."""
        fatigue_metrics = self._extract_all()["fatigue_metrics"]
        if not fatigue_metrics.get("enabled"):
            return pd.DataFrame()

        raw_values = fatigue_metrics.get("raw_values", [])
        if not raw_values:
            return pd.DataFrame()

        return pd.DataFrame(
            {
                "metric": [
                    "max_fatigue",
                    "avg_fatigue",
                    "total_fatigue",
                    "high_fatigue_days",
                    "high_fatigue_threshold",
                    "patient_safety_cost",
                    "max_work_hours",
                    "avg_work_hours",
                ],
                "value": [
                    fatigue_metrics.get("max_fatigue"),
                    fatigue_metrics.get("avg_fatigue"),
                    fatigue_metrics.get("total_fatigue"),
                    fatigue_metrics.get("high_fatigue_days"),
                    fatigue_metrics.get("high_fatigue_threshold"),
                    fatigue_metrics.get("patient_safety_cost"),
                    fatigue_metrics.get("max_work_hours"),
                    fatigue_metrics.get("avg_work_hours"),
                ],
            }
        )

    def extract(self) -> Dict[str, Any]:
        """Return the complete extracted result dictionary."""
        return self._extract_all()

    def _extract_all(self) -> Dict[str, Any]:
        """Build and cache all extracted result artifacts."""
        if self._cache is not None:
            return self._cache

        if self.solve_result.status != "Optimal":
            self._cache = {
                "roster_df": pd.DataFrame(),
                "schedule_df": pd.DataFrame(),
                "cost_breakdown": {},
                "risk_metrics": {},
                "scenario_df": pd.DataFrame(),
                "coverage_df": pd.DataFrame(),
                "solution_explanation": None,
                "fatigue_metrics": {},
                "kpi_metadata": {},
            }
            return self._cache

        nurses_list = self.nurses_list
        scenarios_df = self.scenarios_df
        model_params = self.model_params
        model_type = self.model_type
        variable_values = self.solve_result.variable_values or {}

        j_days = sorted(scenarios_df["day"].unique())
        k_shifts = sorted(scenarios_df["shift"].unique())
        w_scenarios = sorted(scenarios_df["scenario"].unique())

        var_dict: Dict[str, Any] = {}
        for name, value in variable_values.items():
            var_dict[name] = value if value else 0

        roster_data = []
        total_regular_shifts = 0
        total_overtime_shifts = 0

        for nurse in nurses_list:
            nurse_schedule: Dict[str, Union[str, int]] = {"Nurse": nurse}
            regular_count = 0
            overtime_count = 0
            night_count = 0

            for day in j_days:
                assigned_shift = "OFF"
                for shift in k_shifts:
                    var_name_sr = f"RegularShift_{nurse}_{day}_{shift}".replace("'", "").replace(" ", "")
                    var_name_so = f"OvertimeShift_{nurse}_{day}_{shift}".replace("'", "").replace(" ", "")

                    sr_val = var_dict.get(var_name_sr, 0)
                    so_val = var_dict.get(var_name_so, 0)

                    if sr_val > 0.5:
                        assigned_shift = shift
                        regular_count += 1
                        if shift == "N":
                            night_count += 1
                    elif so_val > 0.5:
                        assigned_shift = f"{shift} (OT)"
                        overtime_count += 1
                        if shift == "N":
                            night_count += 1

                nurse_schedule[f"D{day}"] = assigned_shift

            nurse_schedule["Total_Regular"] = regular_count
            nurse_schedule["Total_Overtime"] = overtime_count
            nurse_schedule["Total_Nights"] = night_count
            nurse_schedule["Total_Shifts"] = regular_count + overtime_count

            total_regular_shifts += regular_count
            total_overtime_shifts += overtime_count
            roster_data.append(nurse_schedule)

        roster_df = pd.DataFrame(roster_data)

        c1 = model_params["c1"]
        c2 = model_params["c2"]
        q_plus = model_params["q_plus"]

        stage1_regular_cost = total_regular_shifts * c1
        stage1_overtime_cost = total_overtime_shifts * c2
        stage1_total = stage1_regular_cost + stage1_overtime_cost

        total_cost = self.solve_result.objective_value
        if total_cost is None:
            total_cost = 0.0
        stage2_cost = total_cost - stage1_total

        cost_breakdown = {
            "total_cost": total_cost,
            "stage1_cost": stage1_total,
            "stage1_total": stage1_total,
            "stage1_regular_cost": stage1_regular_cost,
            "stage1_overtime_cost": stage1_overtime_cost,
            "stage2_cost": stage2_cost,
            "stage2_expected_cost": stage2_cost,
            "total_regular_shifts": total_regular_shifts,
            "total_overtime_shifts": total_overtime_shifts,
            "avg_cost_per_nurse": total_cost / len(nurses_list) if nurses_list else 0,
        }

        risk_metrics: Dict[str, Any] = {
            "model_type": model_type,
            "num_scenarios": len(w_scenarios),
        }

        if model_type == "SDM-CVaR":
            risk_metrics["var_value"] = var_dict.get("VaR_xi", 0)
            risk_metrics["cvar_limit"] = model_params.get("mu", 0)
            risk_metrics["confidence_level"] = model_params.get("sigma", 0.95)

        scenario_results = []
        for scenario in w_scenarios:
            scenario_str = str(scenario)
            total_shortage = 0
            total_overage = 0

            for key, value in var_dict.items():
                if value <= 0:
                    continue

                parts = key.split("_")
                if len(parts) >= 2 and parts[-1] == scenario_str:
                    if "AddShift" in key or key.startswith("a_"):
                        total_shortage += value
                    elif "CancelShift" in key or key.startswith("u_"):
                        total_overage += value

            scenario_results.append(
                {
                    "scenario": scenario,
                    "shortage_shifts": total_shortage,
                    "overage_shifts": total_overage,
                    "recourse_cost": total_shortage * q_plus,
                }
            )

        scenario_df = pd.DataFrame(scenario_results)

        daily_coverage = []
        for day in j_days:
            for shift in k_shifts:
                assigned = 0
                for nurse in nurses_list:
                    var_name_sr = f"RegularShift_{nurse}_{day}_{shift}".replace("'", "").replace(" ", "")
                    var_name_so = f"OvertimeShift_{nurse}_{day}_{shift}".replace("'", "").replace(" ", "")
                    assigned += var_dict.get(var_name_sr, 0) + var_dict.get(var_name_so, 0)

                daily_coverage.append(
                    {
                        "day": day,
                        "shift": shift,
                        "assigned_nurses": int(assigned),
                    }
                )

        coverage_df = pd.DataFrame(daily_coverage)

        schedule_data = []
        for nurse in nurses_list:
            for day in j_days:
                for shift in k_shifts:
                    var_name_sr = f"RegularShift_{nurse}_{day}_{shift}".replace("'", "").replace(" ", "")
                    var_name_so = f"OvertimeShift_{nurse}_{day}_{shift}".replace("'", "").replace(" ", "")

                    sr_val = var_dict.get(var_name_sr, 0)
                    so_val = var_dict.get(var_name_so, 0)

                    if sr_val > 0.5:
                        schedule_data.append(
                            {
                                "nurse": nurse,
                                "day": day,
                                "shift": shift,
                                "type": "Regular",
                            }
                        )
                    elif so_val > 0.5:
                        schedule_data.append(
                            {
                                "nurse": nurse,
                                "day": day,
                                "shift": shift,
                                "type": "Overtime",
                            }
                        )

        schedule_df = pd.DataFrame(schedule_data)

        try:
            _, _, feasibility_details = self._validate_capacity_feasibility(
                nurses_list, scenarios_df, model_params
            )
        except Exception:
            feasibility_details = {
                "total_capacity": len(nurses_list) * model_params.get("n1", 15),
                "baseline_demand": int(scenarios_df.groupby("scenario")["demand"].sum().mean()) if len(scenarios_df) > 0 else 0,
            }

        def explain_solution_strategy(results: Dict[str, Any], feasibility_details: Dict[str, Any]) -> str:
            """Generate a human-readable explanation of the solution strategy."""
            capacity = feasibility_details.get("total_capacity", 0)
            demand = feasibility_details.get("baseline_demand", 0)

            try:
                _ = float(results.get("scenario_df", pd.DataFrame())["shortage_shifts"].mean())
            except Exception:
                pass

            if demand > capacity:
                return f"""
📈 SOLUTION STRATEGY EXPLANATION:

Since baseline demand ({demand} shifts) exceeds capacity ({capacity} shifts), the model uses:

• Stage 1: Full capacity utilization ({capacity} shifts at regular cost)
• Stage 2: Emergency staff for remaining {demand - capacity:.0f} shifts

This follows the paper's two-stage approach: make cost-effective first-stage decisions,
then handle excess demand with more expensive but flexible emergency staff.
"""
            return "✅ Solution uses optimal balance of regular, overtime, and emergency staff."

        explanation = explain_solution_strategy({"scenario_df": scenario_df}, feasibility_details)

        fatigue_metrics: Dict[str, Any] = {}
        patient_safety_enabled = model_params.get("patient_safety_enabled", False)

        if patient_safety_enabled:
            fatigue_values = []
            work_hours_values = []

            for nurse in nurses_list:
                for day in j_days:
                    fatigue_var_name = f"Fatigue_{nurse}_{day}".replace("'", "").replace(" ", "")
                    fatigue_val = var_dict.get(fatigue_var_name, 0)
                    fatigue_values.append(fatigue_val)

                    workhours_var_name = f"WorkHours_{nurse}_{day}".replace("'", "").replace(" ", "")
                    hours_val = var_dict.get(workhours_var_name, 0)
                    work_hours_values.append(hours_val)

            max_fatigue = max(fatigue_values) if fatigue_values else 0
            avg_fatigue = sum(fatigue_values) / len(fatigue_values) if fatigue_values else 0
            high_fatigue_threshold = 0.60
            high_fatigue_days = sum(1 for f in fatigue_values if f > high_fatigue_threshold)
            total_fatigue = sum(fatigue_values)
            patient_safety_weight = model_params.get("patient_safety_weight", 50.0)
            patient_safety_cost_value = total_fatigue * patient_safety_weight
            max_work_hours = max(work_hours_values) if work_hours_values else 0
            avg_work_hours = sum(work_hours_values) / len(work_hours_values) if work_hours_values else 0

            fatigue_metrics = {
                "enabled": True,
                "max_fatigue": max_fatigue,
                "avg_fatigue": avg_fatigue,
                "total_fatigue": total_fatigue,
                "high_fatigue_days": high_fatigue_days,
                "high_fatigue_threshold": high_fatigue_threshold,
                "patient_safety_cost": patient_safety_cost_value,
                "max_work_hours": max_work_hours,
                "avg_work_hours": avg_work_hours,
                "fatigue_lambda": model_params.get("fatigue_lambda", 0.03),
                "max_fatigue_threshold": model_params.get("max_fatigue_threshold", 0.70),
                "shift_duration": model_params.get("shift_duration", 12),
                "raw_values": fatigue_values,
            }

            for nurse in nurses_list:
                nurse_fatigue_values = []
                for day in j_days:
                    fatigue_var_name = f"Fatigue_{nurse}_{day}".replace("'", "").replace(" ", "")
                    fatigue_val = var_dict.get(fatigue_var_name, 0)
                    nurse_fatigue_values.append(f"{fatigue_val:.3f}")

                roster_idx = roster_df[roster_df["Nurse"] == nurse].index[0]
                for day_idx, day in enumerate(j_days):
                    roster_df.loc[roster_idx, f"Fatigue_D{day}"] = nurse_fatigue_values[day_idx]

            cost_breakdown["patient_safety_cost"] = patient_safety_cost_value
        else:
            fatigue_metrics = {
                "enabled": False,
                "message": "Patient safety feature not enabled",
            }

        self._cache = {
            "roster_df": roster_df,
            "schedule_df": schedule_df,
            "cost_breakdown": cost_breakdown,
            "risk_metrics": risk_metrics,
            "scenario_df": scenario_df,
            "coverage_df": coverage_df,
            "solution_explanation": explanation,
            "fatigue_metrics": fatigue_metrics,
            "kpi_metadata": {
                "regular_shifts": int(total_regular_shifts),
                "overtime_shifts": int(total_overtime_shifts),
                "emergency_shifts": float(scenario_df["shortage_shifts"].mean()),
                "total_demand": float(scenarios_df.groupby("scenario")["demand"].sum().mean()),
                "total_cost": float(total_cost),
                "fatigue_values": fatigue_values if patient_safety_enabled else [],
                "shifts_per_nurse": roster_df["Total_Shifts"].tolist(),
            },
        }
        return self._cache

    @staticmethod
    def _validate_capacity_feasibility(
        nurses_list: List[str],
        scenarios_df: pd.DataFrame,
        model_params: Dict[str, Any],
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Validate capacity feasibility using the same logic as the core model."""
        n1 = model_params.get("n1", 15)
        n2 = model_params.get("n2", 5)
        num_nurses = len(nurses_list)

        total_capacity = num_nurses * n1
        temp_total_demands = scenarios_df.groupby("scenario")["demand"].sum()
        baseline_demand = int(temp_total_demands.mean()) if len(temp_total_demands) else 0
        daily_demands = scenarios_df.groupby(["scenario", "day"])["demand"].sum()
        peak_daily_demand = int(daily_demands.max()) if len(daily_demands) else 0

        is_feasible = True
        issues = []
        warnings = []

        max_emergency = model_params.get("max_emergency_staff", float("inf"))

        if max_emergency < float("inf"):
            for scenario in scenarios_df["scenario"].unique():
                scenario_data = scenarios_df[scenarios_df["scenario"] == scenario]
                for (day, shift), group in scenario_data.groupby(["day", "shift"]):
                    demand = int(group["demand"].sum())
                    max_possible = num_nurses + max_emergency
                    if demand > max_possible:
                        is_feasible = False
                        issues.append(
                            f"❌ Scenario {scenario}, Day {day}, Shift {shift}: Demand ({demand}) exceeds max possible coverage ({max_possible})"
                        )
                        issues.append(
                            f"   → Even with all {num_nurses} nurses + {max_emergency} emergency staff = {max_possible} < {demand}"
                        )

        utilization = (baseline_demand / total_capacity) * 100 if total_capacity > 0 else 0

        if baseline_demand > total_capacity:
            warnings.append(f"⚠️  Baseline demand ({baseline_demand}) > total capacity ({total_capacity})")
            warnings.append("   → Will rely heavily on emergency staff (costly!)")
            warnings.append("   → Consider: more nurses OR higher n1")

        if peak_daily_demand > num_nurses:
            warnings.append(f"⚠️  Peak daily demand ({peak_daily_demand} nurses/day) > available nurses ({num_nurses})")
            warnings.append("   → Some days will require emergency staff")
            warnings.append("   → This is expected - model handles it via recourse (α)")

        details = {
            "num_nurses": num_nurses,
            "max_shifts_per_nurse": n1,
            "total_capacity": total_capacity,
            "baseline_demand": baseline_demand,
            "peak_daily_demand": peak_daily_demand,
            "utilization_percent": utilization,
            "shortage_shifts": max(0, baseline_demand - total_capacity),
            "warnings": warnings,
        }

        message_parts = []
        if issues:
            message_parts.extend(issues)
        if warnings:
            message_parts.append("")
            message_parts.extend(warnings)

        if not issues and not warnings:
            message = "✅ Problem is feasible with good capacity utilization"
        elif issues:
            message = "\n".join(message_parts)
        else:
            message = "✅ Problem is feasible\n" + "\n".join(message_parts)

        return is_feasible, message, details


def extract_results(
    prob: Any,
    nurses_list: List[str],
    scenarios_df: pd.DataFrame,
    model_params: Dict[str, Any],
    model_type: str = "SDM",
) -> Optional[Dict[str, Any]]:
    """Backward-compatible wrapper that mirrors the original extraction function."""
    status = getattr(prob, "status", None)
    if status is None:
        return None

    from pulp import LpStatus  # local import to keep the core module light

    if LpStatus[status] != "Optimal":
        return None

    variable_values: Dict[str, Any] = {}
    if hasattr(prob, "variables"):
        for variable in prob.variables():
            variable_values[variable.name] = variable.varValue if variable.varValue else 0

    objective_value = None
    if hasattr(prob, "objective"):
        try:
            objective_value = float(prob.objective.value()) if prob.objective.value() is not None else None
        except Exception:
            objective_value = None

    solve_result = SolveResult(
        status="Optimal",
        objective_value=objective_value,
        solve_time_seconds=0.0,
        solver_name="",
        variable_values=variable_values,
        metadata={"model_type": model_type},
    )

    model = type(
        "ResultExtractionModel",
        (),
        {
            "nurses_list": nurses_list,
            "scenarios_df": scenarios_df,
            "parameters": model_params,
            "model_type": model_type,
        },
    )()

    return ResultExtractor(model, solve_result).extract()
