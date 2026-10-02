"""Sidebar rendering for the NSS Streamlit UI."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.solver_config import auto_select_solver, get_available_solvers


def render_sidebar() -> Dict[str, Any]:
    """Render the configuration sidebar and return model parameters."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 0 0 2rem 0;">
                <h1 style="color: #1e293b; margin: 0; font-size: 2rem; font-weight: 700;">Configuration</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.header("Cost Parameters")
        with st.expander("Wage Costs", expanded=True):
            st.markdown(
                """
                **Cost hierarchy determines when each type is used:**
                - Stage 1: Regular ($c_1$) and Overtime ($c_2$) planned in advance
                - Stage 2: Emergency ($q^+$) used when actual demand exceeds plan

                💡 **Overtime vs Emergency:**
                - Overtime is cheaper than emergency staff ($c_2 < q^+$)
                - The model will choose the optimal mix based on these costs and demand risk
                """
            )
            c1 = st.number_input("Regular Shift Cost ($c_1$)", 0.0, 10000000.0, 100.0, 1.0)
            c2 = st.number_input("Overtime Shift Cost ($c_2$)", 0.0, 10000000.0, 150.0, 1.0)
            q_plus = st.number_input("Emergency Shift Cost ($q^+$)", 0.0, 10000000.0, 200.0, 1.0)
            q_minus = st.number_input(
                "Shift Cancellation Cost ($q^-$)",
                0.0,
                10000000.0,
                2.0,
                1.0,
                help="Cost per cancelled shift (paper: q⁻=2). Set to 0 to ignore cancellation costs.",
            )

        with st.expander("Quality Penalties (Soft Constraints)", expanded=False):
            st.caption("These penalties discourage undesirable schedule patterns without making them impossible")
            c3 = st.number_input(
                "Stand-Alone Shift Penalty ($c_3$)",
                0.0,
                100.0,
                10.0,
                1.0,
                help="Penalty for isolated working days (e.g., work Mon, off Tue-Thu, work Fri)",
            )
            c4 = st.number_input(
                "Unwanted Pattern Penalty ($c_4$)",
                0.0,
                100.0,
                15.0,
                1.0,
                help="Penalty for bad shift sequences (e.g., Late→Early, Day→Early)",
            )

        with st.expander("Recourse Bounds (Optional)", expanded=False):
            st.caption("Limit emergency staffing and cancellations per shift (leave unchecked for unlimited)")
            enable_recourse_bounds = st.checkbox(
                "Enable recourse bounds",
                value=False,
                help="Add hard limits on emergency staff and cancellations",
            )

            if enable_recourse_bounds:
                col1, col2 = st.columns(2)
                with col1:
                    max_emergency_staff = st.number_input(
                        "Max Emergency Staff per Shift",
                        1,
                        20,
                        5,
                        1,
                        help="Maximum additional nurses that can be added per shift (Constraint 17)",
                    )
                with col2:
                    max_cancellations = st.number_input(
                        "Max Cancellations per Shift",
                        1,
                        20,
                        3,
                        1,
                        help="Maximum shifts that can be cancelled per shift (Constraint 18)",
                    )
            else:
                max_emergency_staff = float("inf")
                max_cancellations = float("inf")

        st.header("📋 Work Rules")
        with st.expander("Fairness & Workload Balancing", expanded=True):
            delta_w = st.number_input(
                "Max Shift Spread (ΔW)", 
                0, 100, 100, 1,
                help="Maximum allowed difference in total shifts between the most-worked and least-worked nurse. (100 = disabled)"
            )
            delta_n = st.number_input(
                "Max Night Shift Spread (ΔN)", 
                0, 100, 100, 1,
                help="Maximum allowed difference in night shifts between nurses. (100 = disabled)"
            )
            
        with st.expander("Basic Shift Constraints", expanded=True):
            n1 = st.slider("Max Total Shifts ($n_1$)", 1, 30, 15, 1)
            n2 = st.slider("Max Night Shifts ($n_2$)", 0, 15, 5, 1)
            n3 = st.slider("Min Regular Shifts ($n_3$)", 0, 20, 5, 1)
            c_bar = st.slider("Max Consecutive Working Days ($C_{bar}$)", 1, 14, 4, 1)
            overtime_capacity = n1 - n3
            st.info(f"Overtime capacity: Up to {overtime_capacity} overtime shifts per nurse (= $n_1$ - $n_3$)")

        with st.expander("Weekend Constraints (Advanced)", expanded=False):
            st.caption("Constraint 9: Minimum Complete Weekends Off")
            n4 = st.number_input(
                "Min Complete Weekends Off ($n_4$)",
                0,
                4,
                0,
                1,
                help="Number of complete weekends (Sat+Sun) each nurse must have off. Set to 0 to disable.",
            )

            if n4 > 0:
                st.info("Weekend detection requires a start date")
                start_date = st.date_input(
                    "Planning Period Start Date",
                    help="Used to determine which days are weekends",
                )
                start_date_str = start_date.strftime("%Y-%m-%d")
            else:
                start_date_str = None

        with st.expander("Night Shift Rest Rules (Advanced)", expanded=False):
            st.caption("Constraints 10-13: Night shift safety and rest requirements")
            night_rest_enabled = st.checkbox(
                "Enable Night Shift Rest Constraints",
                value=False,
                help="Enforces consecutive night shifts and mandatory rest periods",
            )

            if night_rest_enabled:
                min_consecutive_nights = st.number_input(
                    "Minimum Consecutive Night Shifts",
                    1,
                    5,
                    2,
                    1,
                    help="Night shifts must come in sequences of at least N consecutive nights (prevents single isolated nights)",
                )
                days_off_after_nights = st.number_input(
                    "Days Off Required After Night Sequence",
                    1,
                    5,
                    2,
                    1,
                    help="Nurses must be completely off for N days after a sequence of night shifts",
                )
            else:
                min_consecutive_nights = 2
                days_off_after_nights = 2

        with st.expander("Shift Type Quotas (Advanced)", expanded=False):
            st.caption("Constraints 2-5: Min/Max for each specific shift type")
            st.warning("Setting quotas can make the problem infeasible! Use carefully.")

            use_shift_quotas = st.checkbox(
                "Enable Shift Type Quotas",
                value=False,
                help="Set min/max limits for each shift type (E, D, L, N)",
            )

            shift_quotas: Dict[str, Dict[str, int]] = {}
            if use_shift_quotas:
                st.write("**Set quotas for each shift type:**")
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Early (E) Shifts")
                    e_min = st.number_input("Min Early Shifts", 0, 20, 0, 1, key="e_min")
                    e_max = st.number_input("Max Early Shifts", 0, 30, 10, 1, key="e_max")
                    if e_max >= e_min and e_max > 0:
                        shift_quotas["E"] = {"min": e_min, "max": e_max}

                    st.subheader("Day (D) Shifts")
                    d_min = st.number_input("Min Day Shifts", 0, 20, 0, 1, key="d_min")
                    d_max = st.number_input("Max Day Shifts", 0, 30, 10, 1, key="d_max")
                    if d_max >= d_min and d_max > 0:
                        shift_quotas["D"] = {"min": d_min, "max": d_max}

                with col2:
                    st.subheader("Late (L) Shifts")
                    l_min = st.number_input("Min Late Shifts", 0, 20, 0, 1, key="l_min")
                    l_max = st.number_input("Max Late Shifts", 0, 30, 10, 1, key="l_max")
                    if l_max >= l_min and l_max > 0:
                        shift_quotas["L"] = {"min": l_min, "max": l_max}

                    st.subheader("Night (N) Shifts")
                    n_min = st.number_input("Min Night Shifts", 0, 20, 0, 1, key="n_min")
                    n_max = st.number_input("Max Night Shifts", 0, 30, 5, 1, key="n_max")
                    if n_max >= n_min and n_max > 0:
                        shift_quotas["N"] = {"min": n_min, "max": n_max}

                if shift_quotas:
                    st.success(f"Quotas set for {len(shift_quotas)} shift types")

        st.divider()
        st.header("Optimization Model")

        model_choice = st.selectbox(
            "Select Model Type:",
            ["Deterministic (Expected Value)", "Two-Stage Stochastic (SDM)", "Risk-Aware with CVaR (SDM-CVaR)"],
            index=2,
            help="Deterministic averages all scenarios. SDM optimizes across all stochastic scenarios. SDM-CVaR controls tail-risk.",
        )

        model_type_code = "SDM"
        sigma = None
        mu = None
        
        if "Deterministic" in model_choice:
            model_type_code = "Deterministic"
        elif "CVaR" in model_choice:
            model_type_code = "SDM-CVaR"
            with st.expander("Risk Parameters", expanded=True):
                sigma = st.slider(
                    "Confidence Level (σ)",
                    0.90,
                    0.99,
                    0.95,
                    0.01,
                    help="Higher = more conservative",
                )
                mu = st.number_input(
                    "Max Acceptable Shortage (μ)",
                    0.0,
                    150.0,
                    5.0,
                    0.5,
                    help="Maximum shortage in worst-case scenarios",
                )

        st.divider()
        st.header("Fatigue Modeling")

        enable_fatigue = st.checkbox(
            "Enable Fatigue Modeling",
            value=True,
            help="Include exponential fatigue model (Jaber et al., 2013) in optimization. When enabled, considers nurse fatigue accumulation and patient safety costs.",
        )

        if enable_fatigue:
            with st.expander("Fatigue Parameters", expanded=False):
                st.caption("Configure the exponential fatigue model: F(t) = 1 - e^(-λt)")
                col1, col2 = st.columns(2)

                with col1:
                    lambda_param = st.number_input(
                        "Fatigue Rate (λ)",
                        0.01,
                        0.10,
                        0.03,
                        0.01,
                        help="Rate of fatigue accumulation. Default: 0.03 from Jaber et al. (2013)",
                    )
                    patient_safety_weight = st.number_input(
                        "Patient Safety Weight ($)",
                        0.0,
                        200.0,
                        50.0,
                        5.0,
                        help="Cost per unit of fatigue (penalty for patient safety risk)",
                    )

                with col2:
                    max_fatigue_threshold = st.slider(
                        "Max Fatigue Threshold",
                        0.50,
                        0.90,
                        0.70,
                        0.05,
                        help="Maximum allowed fatigue level (0=fresh, 1=exhausted). Nurses cannot exceed this.",
                    )
                    shift_duration = st.number_input(
                        "Shift Duration (hours)",
                        6,
                        16,
                        12,
                        1,
                        help="Duration of each shift in hours",
                    )

                st.info("PWL Approximation: Using 8 segments (0.713% max error, 0.398% avg error)")
        else:
            lambda_param = 0.03
            patient_safety_weight = 0.0
            max_fatigue_threshold = 0.70
            shift_duration = 12
            st.warning("Fatigue modeling disabled. The system will optimize costs without considering nurse fatigue or patient safety.")

        st.divider()
        st.header("Solver Configuration")

        available_solvers = get_available_solvers()
        working_solvers = ["AUTO (Recommended)"]
        solver_details: Dict[str, Dict[str, Any]] = {}

        for name, info in available_solvers.items():
            if info["available"]:
                working_solvers.append(name)
                solver_details[name] = info

        solver_choice = st.selectbox(
            "Select Solver:",
            working_solvers,
            help="AUTO automatically selects the fastest available solver. Manual selection available if you encounter issues.",
        )

        solve_time_limit = st.number_input(
            "Solve Time Limit (seconds)",
            value=0,
            min_value=0,
            help="Maximum time allowed for the solver. Enter 0 for NO LIMIT.",
            step=10
        )


        if solver_choice == "AUTO (Recommended)":
            selected_solver = auto_select_solver()
            st.info(f"Auto-selected: {selected_solver} ({solver_details.get(selected_solver, {}).get('speed', 'Standard')})")
        else:
            selected_solver = solver_choice
            st.success(f"Using: {selected_solver}")

        st.divider()

        params: Dict[str, Any] = {
            "c1": c1,
            "c2": c2,
            "q_plus": q_plus,
            "q_minus": q_minus,
            "c3": c3,
            "c4": c4,
            "Delta_W": delta_w,
            "Delta_N": delta_n,
            "n1": n1,
            "n2": n2,
            "n3": n3,
            "C_bar": c_bar,
            "patient_safety_enabled": enable_fatigue,
            "fatigue_lambda": lambda_param,
            "recovery_mu": 0.05,
            "patient_safety_weight": patient_safety_weight,
            "max_fatigue_threshold": max_fatigue_threshold,
            "shift_duration": shift_duration,
            "n4": n4,
            "shift_quotas": shift_quotas,
            "night_rest_enabled": night_rest_enabled,
            "min_consecutive_nights": min_consecutive_nights,
            "days_off_after_nights": days_off_after_nights,
            "max_emergency_staff": max_emergency_staff,
            "max_cancellations": max_cancellations,
            "model_type": model_type_code,
            "solver_name": selected_solver,
        }

        if sigma is not None:
            params["sigma"] = sigma
        if mu is not None:
            params["mu"] = mu
        if start_date_str is not None:
            params["start_date"] = start_date_str

        return params
