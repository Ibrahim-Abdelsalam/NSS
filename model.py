import pulp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from solver_config import create_solver

def build_and_solve_model(
    nurses_list, 
    scenarios_df, 
    model_params, 
    model_type="SDM",
    solver_name="CBC"
):
    """
    Builds and solves the stochastic nurse scheduling model.

    Args:
        nurses_list (list): A list of nurse names (e.g., ['Alice', 'Bob']).
        scenarios_df (pd.DataFrame): A DataFrame with columns 
                                     ['scenario', 'day', 'shift', 'demand'].
        model_params (dict): A dictionary of all cost and rule parameters.
        model_type (str): "SDM" or "SDM-CVaR".
        solver_name (str): Solver to use: "CBC", "GUROBI", or "CPLEX". Default: "CBC"

    Returns:
        prob (pulp.LpProblem): The solved PuLP model.
        status (str): The solution status ('Optimal', 'Infeasible', etc.).
    """

    # --- 1. EXTRACT DATA & CREATE SETS ---
    
    # Get sets from the scenario data
    I_nurses = nurses_list
    J_days = scenarios_df['day'].unique()
    K_shifts = scenarios_df['shift'].unique()
    W_scenarios = scenarios_df['scenario'].unique()
    
    # Create a fast lookup dictionary for R_jk_omega (Demand)
    # This is the R_jk^ω from the paper
    R_demand = scenarios_df.set_index(['day', 'shift', 'scenario'])['demand'].to_dict()

    # Get probabilities (assume all scenarios are equally likely for this prototype)
    scenario_probability = {w: 1.0 / len(W_scenarios) for w in W_scenarios}
    
    # Extract model parameters from the dictionary
    c1, c2 = model_params['c1'], model_params['c2']
    q_plus, q_minus = model_params['q_plus'], 0.0 # q_minus is 0 for now
    n1, n2, n3 = model_params['n1'], model_params['n2'], model_params['n3']
    
    # Soft constraint penalty costs
    c3 = model_params.get('c3', 10.0)  # Penalty for stand-alone shifts
    c4 = model_params.get('c4', 15.0)  # Penalty for unwanted shift patterns
    
    # CVaR parameters (if used)
    sigma = model_params.get('sigma', 0.95) # Default 0.95
    mu = model_params.get('mu', 5.0)       # Default 5.0
    
    # NEW ADVANCED CONSTRAINTS PARAMETERS
    # Constraint 9: Minimum complete weekends off
    n4 = model_params.get('n4', 0)  # Min complete weekends off (0 = disabled)
    start_date = model_params.get('start_date', None)  # Start date for weekend detection
    
    # Constraints 2-5: Min/Max for each shift type
    shift_quotas = model_params.get('shift_quotas', {})
    # Format: {'E': {'min': 2, 'max': 8}, 'D': {'min': 3, 'max': 10}, ...}
    
    # Constraints 10-13: Night shift rest requirements
    night_rest_enabled = model_params.get('night_rest_enabled', False)
    min_consecutive_nights = model_params.get('min_consecutive_nights', 2)  # Constraint 10
    days_off_after_nights = model_params.get('days_off_after_nights', 2)   # Constraint 11
    
    # Define unwanted shift patterns (K' in the paper)
    # These are consecutive shift combinations to avoid
    unwanted_patterns = [
        ('D', 'E'),  # Day followed by Early
        ('L', 'E'),  # Late followed by Early
        ('L', 'D'),  # Late followed by Day
        ('E', 'N'),  # Early followed by Night
    ]

    # --- 2. INSTANTIATE THE MODEL ---
    prob = pulp.LpProblem("NurseScheduling", pulp.LpMinimize)

    # ============================================================================
    # STAGE 1 VARIABLES (FIRST-STAGE / HERE-AND-NOW DECISIONS)
    # ============================================================================
    # These decisions are made BEFORE knowing the actual patient demand
    # They represent the baseline nurse schedule
    
    # --- 3. DEFINE STAGE 1 VARIABLES (x) ---
    # sr_ijk: Binary variable = 1 if nurse i works regular shift k on day j
    # Corresponds to: sr_{ijk} ∈ {0,1} in the mathematical model
    sr = pulp.LpVariable.dicts("RegularShift", 
                              (I_nurses, J_days, K_shifts), 
                              cat=pulp.LpBinary)

    # so_ijk: Binary variable = 1 if nurse i works overtime shift k on day j
    # Corresponds to: so_{ijk} ∈ {0,1} in the mathematical model
    so = pulp.LpVariable.dicts("OvertimeShift", 
                              (I_nurses, J_days, K_shifts), 
                              cat=pulp.LpBinary)
    
    # ============================================================================
    # SOFT CONSTRAINT DEVIATION VARIABLES
    # ============================================================================
    # These variables measure violations of "soft" constraints that are
    # penalized in the objective rather than strictly enforced
    
    # dev1_ij: Deviation variable for stand-alone shift penalty
    # Penalizes isolated working days (shifts surrounded by days off)
    # Corresponds to: dev1_{ij} ∈ ℤ⁺ in the mathematical model
    dev1 = pulp.LpVariable.dicts("Dev_StandAlone",
                                 (I_nurses, J_days),
                                 lowBound=0,
                                 cat=pulp.LpInteger)
    
    # dev2_ijk: Deviation variable for unwanted shift pattern penalty
    # Penalizes undesirable consecutive shift combinations (e.g., D-E, L-E, L-D, E-N)
    # Corresponds to: dev2_{ijk} ∈ ℤ⁺ in the mathematical model
    dev2 = pulp.LpVariable.dicts("Dev_UnwantedPattern",
                                 (I_nurses, J_days, K_shifts),
                                 lowBound=0,
                                 cat=pulp.LpInteger)

    # ============================================================================
    # ADVANCED CONSTRAINT AUXILIARY VARIABLES
    # ============================================================================
    # These variables are needed for implementing complex constraints
    
    # For Constraint 9: Weekend off tracking
    weekend_off = {}
    weekends = []
    if n4 > 0 and start_date:
        # Create day metadata with calendar information
        from datetime import datetime, timedelta
        base_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Identify complete weekends (Saturday + Sunday pairs)
        J_days_sorted = sorted(list(J_days))
        for idx, j in enumerate(J_days_sorted):
            day_date = base_date + timedelta(days=int(j) - 1)
            is_saturday = day_date.weekday() == 5
            
            # Check if next day exists and is Sunday
            if idx + 1 < len(J_days_sorted):
                next_j = J_days_sorted[idx + 1]
                next_date = base_date + timedelta(days=int(next_j) - 1)
                is_sunday = next_date.weekday() == 6
                
                if is_saturday and is_sunday and (int(next_j) - int(j)) == 1:
                    weekends.append((j, next_j))
        
        # Create binary variables: weekend_off[i][w] = 1 if nurse i has weekend w completely off
        if weekends:
            weekend_off = pulp.LpVariable.dicts("WeekendOff",
                                                (I_nurses, range(len(weekends))),
                                                cat=pulp.LpBinary)
    
    # For Constraints 10-13: Night shift sequence tracking
    night_sequence_start = {}
    night_sequence_end = {}
    if night_rest_enabled and 'N' in K_shifts:
        J_days_sorted = sorted(list(J_days))
        
        # Binary variable: = 1 if night shift sequence starts on day j
        night_sequence_start = pulp.LpVariable.dicts("NightSeqStart",
                                                     (I_nurses, J_days),
                                                     cat=pulp.LpBinary)
        
        # Binary variable: = 1 if night shift sequence ends on day j
        night_sequence_end = pulp.LpVariable.dicts("NightSeqEnd",
                                                   (I_nurses, J_days),
                                                   cat=pulp.LpBinary)

    # ============================================================================
    # STAGE 2 VARIABLES (SECOND-STAGE / RECOURSE DECISIONS)
    # ============================================================================
    # These decisions are made AFTER observing the actual demand in each scenario
    # They represent adjustments to the baseline schedule
    
    # --- 4. DEFINE STAGE 2 VARIABLES (y^ω) ---
    # alpha_jk_omega: Number of emergency shifts ADDED for scenario ω on day j, shift k
    # Corresponds to: α_{jk}^ω ≥ 0 in the mathematical model
    alpha = pulp.LpVariable.dicts("AddShift", 
                                 (J_days, K_shifts, W_scenarios), 
                                 lowBound=0, 
                                 cat=pulp.LpContinuous)

    # beta_jk_omega: Number of shifts CANCELLED for scenario ω on day j, shift k
    # Corresponds to: β_{jk}^ω ≥ 0 in the mathematical model
    beta = pulp.LpVariable.dicts("CancelShift", 
                                (J_days, K_shifts, W_scenarios), 
                                lowBound=0, 
                                cat=pulp.LpContinuous)

    # ============================================================================
    # CVaR VARIABLES (CONDITIONAL VALUE-AT-RISK)
    # ============================================================================
    # These variables are only used if model_type == "SDM-CVaR"
    # They enable risk management by controlling worst-case shortages
    
    # --- 5. DEFINE CVaR VARIABLES (if needed) ---
    if model_type == "SDM-CVaR":
        # xi: The Value-at-Risk (VaR) threshold at confidence level σ
        # Corresponds to: ξ ∈ ℝ in the mathematical model
        # This represents the σ-quantile of the loss distribution
        xi = pulp.LpVariable("VaR_xi", cat=pulp.LpContinuous)
        
        # z_omega: The "excess loss" beyond VaR for scenario ω
        # Corresponds to: z^ω ≥ 0 in the mathematical model
        # z^ω = max(0, Loss^ω - ξ)
        z = pulp.LpVariable.dicts("ExcessLoss_z", 
                                 (W_scenarios), 
                                 lowBound=0, 
                                 cat=pulp.LpContinuous)

    # ============================================================================
    # OBJECTIVE FUNCTION
    # ============================================================================
    # Minimize: Stage 1 Cost + Soft Constraint Penalties + Expected Stage 2 Cost
    #
    # Mathematical formulation:
    # min  c₁ Σᵢⱼₖ sr_{ijk} + c₂ Σᵢⱼₖ so_{ijk} 
    #      + c₃ Σᵢⱼ dev1_{ij} + c₄ Σᵢⱼₖ dev2_{ijk}
    #      + Σ_ω p^ω · (q⁺ Σⱼₖ α_{jk}^ω + q⁻ Σⱼₖ β_{jk}^ω)
    #
    # Where:
    #   c₁ = regular shift cost
    #   c₂ = overtime shift cost
    #   c₃ = penalty for stand-alone shifts
    #   c₄ = penalty for unwanted shift patterns
    #   q⁺ = cost to add emergency shift
    #   q⁻ = cost to cancel shift (typically 0)
    #   p^ω = probability of scenario ω
    # ============================================================================
    
    # --- 6. DEFINE OBJECTIVE FUNCTION ---
    
    # STAGE 1 COST: Regular wages + Overtime wages
    # This is the cost of the baseline schedule decided before demand is known
    stage1_cost = (
        c1 * pulp.lpSum(sr[i][j][k] for i in I_nurses for j in J_days for k in K_shifts) +
        c2 * pulp.lpSum(so[i][j][k] for i in I_nurses for j in J_days for k in K_shifts)
    )
    
    # SOFT CONSTRAINT PENALTIES
    # These penalize undesirable schedule patterns without making them infeasible
    soft_penalty_cost = (
        c3 * pulp.lpSum(dev1[i][j] for i in I_nurses for j in J_days) +
        c4 * pulp.lpSum(dev2[i][j][k] for i in I_nurses for j in J_days for k in K_shifts)
    )

    # STAGE 2 COST: Expected recourse cost across all scenarios
    # This is the expected cost of adjustments after demand is revealed
    stage2_cost = pulp.lpSum(
        scenario_probability[w] * (
            q_plus * pulp.lpSum(alpha[j][k][w] for j in J_days for k in K_shifts) +
            q_minus * pulp.lpSum(beta[j][k][w] for j in J_days for k in K_shifts)
        )
        for w in W_scenarios
    )
    
    # TOTAL OBJECTIVE: Minimize total expected cost including penalties
    prob += stage1_cost + soft_penalty_cost + stage2_cost, "Total_Cost"

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    # The paper presents 18+ constraints. We implement the core hard constraints here.
    # Soft constraints (dev1, dev2) are omitted for simplicity.
    # ============================================================================

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    # The paper presents 18+ constraints. We implement the core hard constraints here.
    # Soft constraints (dev1, dev2) are omitted for simplicity.
    # ============================================================================

    # ============================================================================
    # CONSTRAINT 1: One Shift Per Day Maximum
    # ============================================================================
    # Mathematical: Σₖ (sr_{ijk} + so_{ijk}) ≤ 1  ∀i ∈ I, j ∈ J
    # Meaning: Each nurse can work at most one shift per day
    # ============================================================================
    for i in I_nurses:
        for j in J_days:
            prob += (
                pulp.lpSum(sr[i][j][k] + so[i][j][k] for k in K_shifts) <= 1,
                f"OneShiftPerDay_{i}_{j}"
            )

    # ============================================================================
    # CONSTRAINTS 2-5: Min/Max Shifts per Shift Type (ADVANCED)
    # ============================================================================
    # Mathematical: n_{k,min} ≤ Σⱼ (sr_{ijk} + so_{ijk}) ≤ n_{k,max}  ∀i ∈ I, k ∈ K
    # Meaning: Each nurse must work within min/max bounds for each shift type
    # Status: NEWLY IMPLEMENTED for university project
    # User provides: shift_quotas = {'E': {'min': 2, 'max': 8}, 'D': {...}, ...}
    # ============================================================================
    for shift_type, quotas in shift_quotas.items():
        if shift_type in K_shifts:
            shift_min = quotas.get('min', 0)
            shift_max = quotas.get('max', n1)  # Default to overall max
            
            for i in I_nurses:
                # Minimum shifts of this type
                if shift_min > 0:
                    prob += (
                        pulp.lpSum(sr[i][j][shift_type] + so[i][j][shift_type] for j in J_days) >= shift_min,
                        f"MinShifts_{shift_type}_{i}"
                    )
                
                # Maximum shifts of this type
                prob += (
                    pulp.lpSum(sr[i][j][shift_type] + so[i][j][shift_type] for j in J_days) <= shift_max,
                    f"MaxShifts_{shift_type}_{i}"
                )

    # ============================================================================
    # CONSTRAINT 6: Maximum Total Shifts per Nurse
    # ============================================================================
    # Mathematical: Σⱼₖ (sr_{ijk} + so_{ijk}) ≤ n₁  ∀i ∈ I
    # Meaning: Each nurse works at most n₁ shifts in the planning period
    # ============================================================================
    for i in I_nurses:
        prob += (
            pulp.lpSum(sr[i][j][k] + so[i][j][k] for j in J_days for k in K_shifts) <= n1,
            f"MaxTotalShifts_{i}"
        )

    # ============================================================================
    # CONSTRAINT 7: Maximum Night Shifts per Nurse
    # ============================================================================
    # Mathematical: Σⱼ (sr_{ijN} + so_{ijN}) ≤ n₂  ∀i ∈ I
    # Meaning: Each nurse works at most n₂ night shifts
    # Note: Only applies if 'N' (night shift) exists in shift types
    # ============================================================================
    if 'N' in K_shifts:
        for i in I_nurses:
            prob += (
                pulp.lpSum(sr[i][j]['N'] + so[i][j]['N'] for j in J_days) <= n2,
                f"MaxNightShifts_{i}"
            )

    # ============================================================================
    # CONSTRAINT 8: Minimum Regular Shifts per Nurse
    # ============================================================================
    # Mathematical: Σⱼₖ sr_{ijk} ≥ n₃  ∀i ∈ I
    # Meaning: Each nurse works at least n₃ regular (non-overtime) shifts
    # Purpose: Ensures fair work distribution and job security
    # ============================================================================
    for i in I_nurses:
        prob += (
            pulp.lpSum(sr[i][j][k] for j in J_days for k in K_shifts) >= n3,
            f"MinRegularShifts_{i}"
        )
        
    # ============================================================================
    # CONSTRAINT 9: Minimum Complete Weekends Off (ADVANCED)
    # ============================================================================
    # Mathematical: Σ_w weekend_off_{iw} ≥ n₄  ∀i ∈ I
    # Meaning: Each nurse must have at least n₄ complete weekends (Sat+Sun) off
    # Status: NEWLY IMPLEMENTED for university project
    # Requires: start_date parameter to detect which days are weekends
    # ============================================================================
    if n4 > 0 and weekends:
        for i in I_nurses:
            for w_idx, (sat, sun) in enumerate(weekends):
                # weekend_off[i][w_idx] = 1 only if OFF on BOTH Saturday AND Sunday
                # This means: no work on Saturday AND no work on Sunday
                
                # If working on Saturday, weekend is NOT off
                prob += (
                    weekend_off[i][w_idx] <= 1 - pulp.lpSum(sr[i][sat][k] + so[i][sat][k] for k in K_shifts),
                    f"WeekendOff_Sat_{i}_{w_idx}"
                )
                
                # If working on Sunday, weekend is NOT off
                prob += (
                    weekend_off[i][w_idx] <= 1 - pulp.lpSum(sr[i][sun][k] + so[i][sun][k] for k in K_shifts),
                    f"WeekendOff_Sun_{i}_{w_idx}"
                )
            
            # Require minimum number of complete weekends off
            prob += (
                pulp.lpSum(weekend_off[i][w] for w in range(len(weekends))) >= n4,
                f"MinCompleteWeekendsOff_{i}"
            )

    # ============================================================================
    # CONSTRAINTS 10-13: Night Shift Rest Requirements (ADVANCED)
    # ============================================================================
    # These constraints ensure nurses get adequate rest after night shifts
    # Status: NEWLY IMPLEMENTED for university project
    # Paper constraints:
    #   - Constraint 10: No stand-alone night shifts (must be consecutive)
    #   - Constraint 11: At least N days off after night shift sequence
    #   - Constraints 12-13: No other shifts immediately before/after night (handled by unwanted patterns)
    # ============================================================================
    if night_rest_enabled and 'N' in K_shifts:
        J_days_sorted = sorted(list(J_days))
        
        for i in I_nurses:
            for idx, j in enumerate(J_days_sorted):
                # Get night shift status for previous, current, next days
                working_night_current = sr[i][j]['N'] + so[i][j]['N']
                
                j_prev = J_days_sorted[idx - 1] if idx > 0 else None
                j_next = J_days_sorted[idx + 1] if idx < len(J_days_sorted) - 1 else None
                
                working_night_prev = (sr[i][j_prev]['N'] + so[i][j_prev]['N']) if j_prev else 0
                working_night_next = (sr[i][j_next]['N'] + so[i][j_next]['N']) if j_next else 0
                
                # ========================================================================
                # CONSTRAINT 10: No Stand-Alone Night Shifts
                # ========================================================================
                # If working night on day j, must work night on j-1 OR j+1
                # (Ensures night shifts come in sequences of at least min_consecutive_nights)
                # ========================================================================
                if min_consecutive_nights >= 2 and j_prev and j_next:
                    # Detect sequence start: working tonight but not last night
                    prob += (
                        night_sequence_start[i][j] >= working_night_current - working_night_prev,
                        f"NightSeqStart_Detect_{i}_{j}"
                    )
                    prob += (
                        night_sequence_start[i][j] <= working_night_current,
                        f"NightSeqStart_Bound1_{i}_{j}"
                    )
                    prob += (
                        night_sequence_start[i][j] <= 1 - working_night_prev,
                        f"NightSeqStart_Bound2_{i}_{j}"
                    )
                    
                    # If starting a sequence, must work at least min_consecutive_nights nights
                    for offset in range(1, min_consecutive_nights):
                        if idx + offset < len(J_days_sorted):
                            j_future = J_days_sorted[idx + offset]
                            prob += (
                                sr[i][j_future]['N'] + so[i][j_future]['N'] >= night_sequence_start[i][j],
                                f"MinConsecutiveNights_{i}_{j}_offset{offset}"
                            )
                
                # ========================================================================
                # CONSTRAINT 11: Days Off After Night Shift Sequence
                # ========================================================================
                # If night shift sequence ends on day j, must be OFF for next N days
                # ========================================================================
                if days_off_after_nights > 0 and j_next:
                    # Detect sequence end: working tonight but not tomorrow night
                    prob += (
                        night_sequence_end[i][j] >= working_night_current - working_night_next,
                        f"NightSeqEnd_Detect_{i}_{j}"
                    )
                    prob += (
                        night_sequence_end[i][j] <= working_night_current,
                        f"NightSeqEnd_Bound1_{i}_{j}"
                    )
                    prob += (
                        night_sequence_end[i][j] <= 1 - working_night_next,
                        f"NightSeqEnd_Bound2_{i}_{j}"
                    )
                    
                    # If sequence ends, enforce days off
                    for offset in range(1, days_off_after_nights + 1):
                        if idx + offset < len(J_days_sorted):
                            j_future = J_days_sorted[idx + offset]
                            # Must be completely off (no shifts of any type)
                            for k in K_shifts:
                                prob += (
                                    sr[i][j_future][k] + so[i][j_future][k] <= 1 - night_sequence_end[i][j],
                                    f"DaysOffAfterNights_{i}_{j}_day{offset}_shift{k}"
                                )

    # ============================================================================
    # CONSTRAINTS 14-15: Soft Constraints (Penalized in Objective)
    # ============================================================================
    # These use deviation variables dev1, dev2 to penalize undesirable patterns
    # without making them strictly infeasible
    # ============================================================================
    
    # ========================================================================
    # CONSTRAINT 14: Stand-Alone Shift Penalty
    # ========================================================================
    # Mathematical: Σₖ (sr_{i,j-1,k} + sr_{i,j,k} + sr_{i,j+1,k}) + dev1_{ij} ≥ 2·sr_{i,j,·}
    #               ∀i ∈ I, j ∈ {2,...,|J|-1}
    #
    # Simplified form (from paper):
    #   Σₖ (sr_{i,j-1,k} - sr_{i,j,k} + sr_{i,j+1,k}) + dev1_{ij} ≥ 0
    #
    # Interpretation:
    #   If a nurse works on day j but NOT on j-1 or j+1, then dev1_{ij} > 0
    #   This creates a penalty for isolated working days
    #   Encourages consecutive working days (better for nurses and operations)
    # ========================================================================
    J_days_list = sorted(list(J_days))
    for i in I_nurses:
        for idx in range(1, len(J_days_list) - 1):
            j_prev = J_days_list[idx - 1]
            j_curr = J_days_list[idx]
            j_next = J_days_list[idx + 1]
            
            prob += (
                pulp.lpSum(sr[i][j_prev][k] for k in K_shifts) -
                pulp.lpSum(sr[i][j_curr][k] for k in K_shifts) +
                pulp.lpSum(sr[i][j_next][k] for k in K_shifts) +
                dev1[i][j_curr] >= 0,
                f"StandAlonePenalty_{i}_{j_curr}"
            )
    
    # ========================================================================
    # CONSTRAINT 15: Unwanted Shift Pattern Penalty
    # ========================================================================
    # Mathematical: sr_{i,j,k₁} + sr_{i,j+1,k₂} - dev2_{ijk₁} ≤ 1
    #               ∀i ∈ I, j ∈ {1,...,|J|-1}, (k₁,k₂) ∈ K'
    #
    # Where K' is the set of unwanted consecutive shift combinations:
    #   - D followed by E (Day → Early): Too short rest
    #   - L followed by E (Late → Early): Too short rest  
    #   - L followed by D (Late → Day): Too short rest
    #   - E followed by N (Early → Night): Disruptive pattern
    #
    # Interpretation:
    #   If nurse works k₁ on day j and k₂ on day j+1, dev2_{ijk₁} must be ≥ 1
    #   This creates a penalty for these undesirable patterns
    # ========================================================================
    for i in I_nurses:
        for idx in range(len(J_days_list) - 1):
            j_curr = J_days_list[idx]
            j_next = J_days_list[idx + 1]
            
            for (k1, k2) in unwanted_patterns:
                # Only add constraint if both shifts exist
                if k1 in K_shifts and k2 in K_shifts:
                    prob += (
                        sr[i][j_curr][k1] + sr[i][j_next][k2] - dev2[i][j_curr][k1] <= 1,
                        f"UnwantedPattern_{i}_{j_curr}_{k1}_{k2}"
                    )

    # ============================================================================
    # CONSTRAINT 16: DEMAND FULFILLMENT (THE KEY RECOURSE CONSTRAINT)
    # ============================================================================
    # Mathematical: Σᵢ (sr_{ijk} + so_{ijk}) + α_{jk}^ω - β_{jk}^ω ≥ R_{jk}^ω
    #               ∀ω ∈ Ω, j ∈ J, k ∈ K
    #
    # This is the CRITICAL constraint that links Stage 1 and Stage 2!
    #
    # Components:
    #   - Σᵢ (sr_{ijk} + so_{ijk}) = Planned staff (Stage 1 decision)
    #   - α_{jk}^ω = Emergency staff added (Stage 2 recourse)
    #   - β_{jk}^ω = Staff cancelled (Stage 2 recourse)
    #   - R_{jk}^ω = Actual demand in scenario ω
    #
    # Interpretation:
    #   "Planned staff + Additions - Cancellations ≥ Demand"
    #   The model can add emergency staff (costly) or cancel shifts
    #   to meet the uncertain demand in each scenario
    # ============================================================================
    for w in W_scenarios:
        for j in J_days:
            for k in K_shifts:
                prob += (
                    pulp.lpSum(sr[i][j][k] + so[i][j][k] for i in I_nurses) +
                    alpha[j][k][w] - beta[j][k][w]
                    >= R_demand.get((j, k, w), 0), # Use .get for safety
                    f"StaffingMet_{j}_{k}_{w}"
                )

    # ============================================================================
    # CVaR CONSTRAINTS (CONDITIONAL VALUE-AT-RISK)
    # ============================================================================
    # These constraints are ONLY added if model_type == "SDM-CVaR"
    # They control the worst-case shortage risk using the CVaR measure
    #
    # CVaR Definition:
    #   CVaR_σ = E[Loss | Loss ≥ VaR_σ]
    #   = σ-quantile tail expectation
    #
    # Linearization (Rockafellar & Uryasev, 2000):
    #   CVaR_σ ≤ μ  is equivalent to:
    #   ξ + (1/(1-σ)) Σ_ω p^ω z^ω ≤ μ
    #   where z^ω ≥ max(0, Loss^ω - ξ)
    # ============================================================================
    
    # --- 8. DEFINE CVaR CONSTRAINTS (if needed) ---
    if model_type == "SDM-CVaR":
        
        # ========================================================================
        # CONSTRAINT 19: CVaR Upper Bound
        # ========================================================================
        # Mathematical: ξ + (1/(1-σ)) Σ_ω p^ω z^ω ≤ μ
        #
        # Components:
        #   ξ = Value-at-Risk (VaR) threshold
        #   σ = Confidence level (e.g., 0.95)
        #   z^ω = Excess loss in scenario ω beyond VaR
        #   μ = User-specified upper bound on CVaR
        #
        # Interpretation:
        #   "The expected shortage in the worst (1-σ)% of scenarios
        #    must not exceed μ"
        #
        # Example: If σ=0.95 and μ=5:
        #   "In the worst 5% of scenarios, expected shortage ≤ 5 shifts"
        # ========================================================================
        prob += (
            xi + (1.0 / (1.0 - sigma)) * pulp.lpSum(scenario_probability[w] * z[w] for w in W_scenarios)
            <= mu,
            "CVaR_Constraint"
        )
        
        # ========================================================================
        # CONSTRAINT 20: Excess Loss Non-Negativity
        # ========================================================================
        # Mathematical: z^ω ≥ 0  ∀ω ∈ Ω
        # Note: This is automatically enforced by lowBound=0 in variable definition
        # No explicit constraint needed
        # ========================================================================
        
        # ========================================================================
        # CONSTRAINT 22: Excess Loss Definition
        # ========================================================================
        # Mathematical: z^ω ≥ Loss^ω - ξ  ∀ω ∈ Ω
        #
        # Loss Function:
        #   Loss^ω = Total shortage in scenario ω
        #          = Σⱼₖ α_{jk}^ω
        #
        # Combined with z^ω ≥ 0, this gives:
        #   z^ω = max(0, Loss^ω - ξ)
        #
        # Interpretation:
        #   z^ω captures how much the loss in scenario ω exceeds VaR
        #   If Loss^ω ≤ ξ, then z^ω = 0 (not in the tail)
        #   If Loss^ω > ξ, then z^ω = Loss^ω - ξ (in the tail)
        # ========================================================================
        for w in W_scenarios:
            # Loss function L(w) is total understaffing: sum(alpha_jk_omega)
            loss_function = pulp.lpSum(alpha[j][k][w] for j in J_days for k in K_shifts)
            
            prob += (
                z[w] >= loss_function - xi,
                f"ExcessLoss_{w}"
            )
            # The (Eq 20) z[w] >= 0 is already handled by the variable's lowBound.

    # ============================================================================
    # SOLVE THE MODEL WITH OPTIMIZATIONS
    # ============================================================================
    # Performance optimizations for large instances:
    # 1. Set time limit to prevent excessive solving
    # 2. Use parallel threads
    # 3. Set MIP gap tolerance for faster solutions
    # 4. Enable preprocessing
    # 5. Disable verbose output
    # ============================================================================
    
    # --- 9. SOLVE THE MODEL ---
    # Determine solver options based on problem size
    num_nurses = len(I_nurses)
    num_days = len(J_days)
    num_scenarios = len(W_scenarios)
    
    # Estimate problem difficulty
    problem_size = num_nurses * num_days * num_scenarios
    
    # Configure solver based on problem size
    if problem_size < 1000:
        # Small problems: Solve to optimality
        time_limit = 120  # 2 minutes
        mip_gap = 0.0     # Optimal solution
    elif problem_size < 5000:
        # Medium problems: Allow small optimality gap
        time_limit = 300  # 5 minutes
        mip_gap = 0.01    # 1% gap acceptable
    else:
        # Large problems: Use larger gap for speed
        time_limit = 600  # 10 minutes
        mip_gap = 0.05    # 5% gap acceptable
    
    # Create solver using flexible solver configuration
    # Supports: CBC (free), Gurobi (free academic), CPLEX (free academic)
    solver = create_solver(
        solver_name=solver_name,
        time_limit=time_limit,
        mip_gap=mip_gap,
        verbose=False  # Set to True to see solver output
    )
    
    # Solve the model
    prob.solve(solver)
    
    status = pulp.LpStatus[prob.status]
    
    return prob, status


def extract_results(prob, nurses_list, scenarios_df, model_params, model_type="SDM"):
    """
    Extract comprehensive results from the solved model.
    
    Returns:
        dict: Contains roster_df, cost_breakdown, risk_metrics, and scenario_analysis
    """
    if pulp.LpStatus[prob.status] != "Optimal":
        return None
    
    # Recreate sets
    J_days = sorted(scenarios_df['day'].unique())
    K_shifts = sorted(scenarios_df['shift'].unique())
    W_scenarios = sorted(scenarios_df['scenario'].unique())
    
    # ===== PERFORMANCE OPTIMIZATION: Create variable lookup dictionary =====
    # This prevents O(n²) lookups - reduces 3 minutes to <1 second!
    var_dict = {}
    for v in prob.variables():
        var_dict[v.name] = v.varValue if v.varValue else 0
    
    # ===== 1. ROSTER EXTRACTION =====
    roster_data = []
    total_regular_shifts = 0
    total_overtime_shifts = 0
    
    for i in nurses_list:
        nurse_schedule = {"Nurse": i}
        regular_count = 0
        overtime_count = 0
        night_count = 0
        
        for j in J_days:
            assigned_shift = "OFF"
            for k in K_shifts:
                # Use direct dictionary lookup instead of searching through all variables
                var_name_sr = f"RegularShift_{i}_{j}_{k}".replace("'", "").replace(" ", "")
                var_name_so = f"OvertimeShift_{i}_{j}_{k}".replace("'", "").replace(" ", "")
                
                sr_val = var_dict.get(var_name_sr, 0)
                so_val = var_dict.get(var_name_so, 0)
                
                if sr_val > 0.5:
                    assigned_shift = k
                    regular_count += 1
                    if k == 'N':
                        night_count += 1
                elif so_val > 0.5:
                    assigned_shift = f"{k} (OT)"
                    overtime_count += 1
                    if k == 'N':
                        night_count += 1
                        
            nurse_schedule[f"Day_{j}"] = assigned_shift
        
        nurse_schedule["Total_Regular"] = regular_count
        nurse_schedule["Total_Overtime"] = overtime_count
        nurse_schedule["Total_Nights"] = night_count
        nurse_schedule["Total_Shifts"] = regular_count + overtime_count
        
        total_regular_shifts += regular_count
        total_overtime_shifts += overtime_count
        
        roster_data.append(nurse_schedule)
    
    roster_df = pd.DataFrame(roster_data)
    
    # ===== 2. COST BREAKDOWN =====
    c1 = model_params['c1']
    c2 = model_params['c2']
    q_plus = model_params['q_plus']
    
    stage1_regular_cost = total_regular_shifts * c1
    stage1_overtime_cost = total_overtime_shifts * c2
    stage1_total = stage1_regular_cost + stage1_overtime_cost
    
    # Calculate expected recourse cost - use dictionary lookup
    total_added_shifts = sum(v for k, v in var_dict.items() if "AddShift" in k)
    
    # Expected value across scenarios
    stage2_cost = (total_added_shifts / len(W_scenarios)) * q_plus
    
    total_cost = pulp.value(prob.objective)
    
    cost_breakdown = {
        "total_cost": total_cost,
        "stage1_total": stage1_total,
        "stage1_regular_cost": stage1_regular_cost,
        "stage1_overtime_cost": stage1_overtime_cost,
        "stage2_expected_cost": stage2_cost,
        "total_regular_shifts": total_regular_shifts,
        "total_overtime_shifts": total_overtime_shifts,
        "avg_cost_per_nurse": total_cost / len(nurses_list) if nurses_list else 0
    }
    
    # ===== 3. RISK METRICS =====
    risk_metrics = {
        "model_type": model_type,
        "num_scenarios": len(W_scenarios)
    }
    
    if model_type == "SDM-CVaR":
        risk_metrics["var_value"] = var_dict.get("VaR_xi", 0)
        risk_metrics["cvar_limit"] = model_params.get('mu', 0)
        risk_metrics["confidence_level"] = model_params.get('sigma', 0.95)
    
    # ===== 4. SCENARIO ANALYSIS =====
    scenario_results = []
    for w in W_scenarios:
        # Use dictionary comprehension - much faster than nested loops
        total_shortage = sum(v for k, v in var_dict.items() if "AddShift" in k and f"_{w}_" in k)
        total_overage = sum(v for k, v in var_dict.items() if "CancelShift" in k and f"_{w}_" in k)
        
        scenario_results.append({
            "scenario": w,
            "shortage_shifts": total_shortage,
            "overage_shifts": total_overage,
            "recourse_cost": total_shortage * q_plus
        })
    
    scenario_df = pd.DataFrame(scenario_results)
    
    # ===== 5. DAILY COVERAGE ANALYSIS =====
    daily_coverage = []
    for j in J_days:
        for k in K_shifts:
            # Use dictionary lookup instead of nested loops
            assigned = 0
            for i in nurses_list:
                var_name_sr = f"RegularShift_{i}_{j}_{k}".replace("'", "").replace(" ", "")
                var_name_so = f"OvertimeShift_{i}_{j}_{k}".replace("'", "").replace(" ", "")
                assigned += var_dict.get(var_name_sr, 0) + var_dict.get(var_name_so, 0)
            
            daily_coverage.append({
                "day": j,
                "shift": k,
                "assigned_nurses": int(assigned)
            })
    
    coverage_df = pd.DataFrame(daily_coverage)
    
    return {
        "roster_df": roster_df,
        "cost_breakdown": cost_breakdown,
        "risk_metrics": risk_metrics,
        "scenario_df": scenario_df,
        "coverage_df": coverage_df
    }


def generate_sample_data(num_nurses=10, num_days=14, num_scenarios=5):
    """
    Generate sample data for testing the model.
    
    Returns:
        tuple: (nurses_list, scenarios_df)
    """
    # Generate nurse names
    nurses_list = [f"Nurse_{i+1}" for i in range(num_nurses)]
    
    # Define shifts
    shifts = ['E', 'D', 'L', 'N']  # Early, Day, Late, Night
    
    # Generate demand scenarios
    scenario_data = []
    
    for scenario in range(1, num_scenarios + 1):
        for day in range(1, num_days + 1):
            for shift in shifts:
                # Base demand with some randomness
                base_demand = {
                    'E': 3,
                    'D': 4,
                    'L': 3,
                    'N': 2
                }
                
                # Add variability
                demand = max(1, base_demand[shift] + np.random.randint(-1, 2))
                
                # Weekend adjustments
                if day % 7 in [0, 6]:  # Weekend
                    demand = max(1, int(demand * 0.8))
                
                scenario_data.append({
                    'scenario': scenario,
                    'day': day,
                    'shift': shift,
                    'demand': demand
                })
    
    scenarios_df = pd.DataFrame(scenario_data)
    
    return nurses_list, scenarios_df


def get_default_params():
    """
    Get default model parameters including advanced constraints.
    """
    return {
        'c1': 100.0,      # Regular shift cost
        'c2': 150.0,      # Overtime shift cost
        'q_plus': 200.0,  # Emergency shift cost
        'c3': 10.0,       # Stand-alone shift penalty
        'c4': 15.0,       # Unwanted pattern penalty
        'n1': 15,         # Max total shifts
        'n2': 5,          # Max night shifts
        'n3': 10,         # Min regular shifts
        'sigma': 0.95,    # CVaR confidence level
        'mu': 5.0,        # Max acceptable shortage
        
        # Advanced constraints (NEW for university project)
        'n4': 0,          # Min complete weekends off (0 = disabled)
        'start_date': None,  # Start date for weekend detection (format: 'YYYY-MM-DD')
        'shift_quotas': {},  # Min/max per shift type: {'E': {'min': 2, 'max': 8}, ...}
        'night_rest_enabled': False,  # Enable night shift rest constraints
        'min_consecutive_nights': 2,  # Minimum consecutive night shifts
        'days_off_after_nights': 2,   # Days off required after night sequence
    }