import pulp
from typing import List, Dict, Any, Tuple, Union

def build_frost_ns_model(
    nurses: List[str],
    days: List[int],
    shifts: List[str],
    scenarios: List[int],
    demand: Dict,  # (day, shift, skill, scenario)->int  OR  (day, shift, scenario)->int (legacy)
    params: Dict[str, Any]
) -> pulp.LpProblem:
    """
    Builds the Simplified FROST-NS mathematical model using PuLP.
    """
    # ------------------------------------------------------------------
    # 1. Sets and Parameters
    # ------------------------------------------------------------------
    I = nurses
    J = days
    K = shifts
    Omega = scenarios
    
    # Identify the night shift indicator
    N_shift = params.get('night_shift_id', 'N')
    
    # Probabilities p_omega
    # Default to equally likely if not provided
    p = params.get('p_omega', {omega: 1.0 / len(Omega) for omega in Omega})
    
    # Extract limits and tolerances from params
    W_bar_global = params.get('W_bar', 10)
    N_bar_global = params.get('N_bar', 3)
    C_bar = params.get('C_bar', 4)
    F_bar = params.get('F_bar', 12)
    Delta_W = params.get('Delta_W', 2)
    Delta_N = params.get('Delta_N', 1)
    
    # Per-nurse shift and night caps (from heterogeneous contracts)
    # Falls back to global W_bar / N_bar if not provided
    W_bar_i = params.get('W_bar_i', {i: W_bar_global for i in I})
    N_bar_i = params.get('N_bar_i', {i: N_bar_global for i in I})
    # Ensure every nurse has a value (handles partial dicts)
    for i in I:
        W_bar_i.setdefault(i, W_bar_global)
        N_bar_i.setdefault(i, N_bar_global)
    
    # Cost parameters
    c_planned = params.get('c_planned', 100)
    c_emergency = params.get('c_emergency', 200)
    c_unmet = params.get('c_unmet', 300)
    
    # Qualifications: q_{ik}
    # Default: all planned nurses are qualified for all shifts
    q = params.get('q', {(i, k): 1 for i in I for k in K})
    
    # Emergency capacity: a_bar_{jk} (assume a single scalar if provided as int)
    # Default to 2
    a_bar_val = params.get('a_bar', 2)
    
    # Shortage priorities: w_k
    # Default to 1.0 for all shifts
    w = params.get('w', {k: 1.0 for k in K})
    
    # CVaR parameters
    alpha = params.get('alpha', 0.80)
    tau = params.get('tau', 100) # Maximum permitted CVaR limit
    
    # ------------------------------------------------------------------
    # 1b. Skill-aware coverage parameters
    # ------------------------------------------------------------------
    # Skill hierarchy: HN > RN > CNA  (downward substitution)
    L_skills = params.get('skill_levels', ['HN', 'RN', 'CNA'])
    
    # Nurse-to-skill mapping: nurse_id -> skill string
    # Default: all nurses are 'RN' if not provided
    nurse_skill = params.get('nurse_skill', {i: 'RN' for i in I})
    for i in I:
        nurse_skill.setdefault(i, 'RN')
    
    # Build sets of nurses per skill level
    I_by_skill = {l: [i for i in I if nurse_skill[i] == l] for l in L_skills}
    
    # Detect whether demand is skill-indexed (4-tuple) or flat (3-tuple)
    _sample_key = next(iter(demand), None)
    skill_aware_demand = (_sample_key is not None and len(_sample_key) == 4)
    
    # If demand is flat (day, shift, scenario), convert to skill-indexed
    # by assigning all demand to the lowest tier (CNA) — same as before
    if not skill_aware_demand:
        demand_by_skill = {}
        for (j, k, omega), val in demand.items():
            demand_by_skill[(j, k, 'CNA', omega)] = val
            for l in L_skills:
                if l != 'CNA':
                    demand_by_skill.setdefault((j, k, l, omega), 0)
        demand = demand_by_skill
    
    # Per-skill cost multipliers for emergency and unmet demand
    # Higher skill = more expensive to hire / more dangerous to be short
    c_emergency_skill = params.get('c_emergency_skill', {
        'HN': c_emergency * 1.5,
        'RN': c_emergency * 1.0,
        'CNA': c_emergency * 0.6,
    })
    c_unmet_skill = params.get('c_unmet_skill', {
        'HN': c_unmet * 3.0,
        'RN': c_unmet * 2.0,
        'CNA': c_unmet * 1.0,
    })
    
    # Per-skill emergency capacity (default: same cap for all skills)
    a_bar_skill = params.get('a_bar_skill', {l: a_bar_val for l in L_skills})
    
    # CVaR unmet-demand clinical severity weights
    w_skill = params.get('w_skill', {'HN': 3.0, 'RN': 2.0, 'CNA': 1.0})
    
    # ------------------------------------------------------------------
    # 2. Model Initialization
    # ------------------------------------------------------------------
    prob = pulp.LpProblem("FROST_NS_Model", pulp.LpMinimize)
    
    # ------------------------------------------------------------------
    # 3. Decision Variables
    # ------------------------------------------------------------------
    
    # First-stage assignment: x_{ijk} in {0, 1}
    x = pulp.LpVariable.dicts("x", (I, J, K), cat=pulp.LpBinary)
    
    # Fatigue intermediate variables
    y_QR = pulp.LpVariable.dicts("y_QR", (I, J), cat=pulp.LpBinary)
    y_CN = pulp.LpVariable.dicts("y_CN", (I, J), cat=pulp.LpBinary)
    
    # Second-stage variables for demand response — now per skill tier
    a = pulp.LpVariable.dicts("a", (J, K, L_skills, Omega), lowBound=0, cat=pulp.LpInteger)
    u = pulp.LpVariable.dicts("u", (J, K, L_skills, Omega), lowBound=0, cat=pulp.LpInteger)
    s = pulp.LpVariable.dicts("s", (J, K, L_skills, Omega), lowBound=0, cat=pulp.LpInteger)
    
    # Surplus flow variables: overflow from higher skill tiers cascading down
    # HN surplus flows to RN tier, RN surplus flows to CNA tier
    # CNA has no outgoing surplus (bottom of hierarchy)
    surplus_skills = [l for l in L_skills if l != L_skills[-1]]  # ['HN', 'RN']
    surplus = pulp.LpVariable.dicts("surplus", (J, K, surplus_skills, Omega), lowBound=0, cat=pulp.LpContinuous)
    
    # Fatigue and fairness variables
    W = pulp.LpVariable.dicts("W", I, lowBound=0, cat=pulp.LpContinuous)
    W_max = pulp.LpVariable("W_max", lowBound=0, cat=pulp.LpContinuous)
    W_min = pulp.LpVariable("W_min", lowBound=0, cat=pulp.LpContinuous)
    
    N_var = pulp.LpVariable.dicts("N_var", I, lowBound=0, cat=pulp.LpContinuous)
    N_max = pulp.LpVariable("N_max", lowBound=0, cat=pulp.LpContinuous)
    N_min = pulp.LpVariable("N_min", lowBound=0, cat=pulp.LpContinuous)
    
    F = pulp.LpVariable.dicts("F", I, lowBound=0, cat=pulp.LpContinuous)
    
    # CVaR variables (Clinical)
    L_var = pulp.LpVariable.dicts("L_var", Omega, lowBound=0, cat=pulp.LpContinuous)
    eta = pulp.LpVariable("eta", cat=pulp.LpContinuous)
    z = pulp.LpVariable.dicts("z", Omega, lowBound=0, cat=pulp.LpContinuous)
    
    # CVaR variables (Financial)
    L_fin = pulp.LpVariable.dicts("L_fin", Omega, lowBound=0, cat=pulp.LpContinuous)
    eta_fin = pulp.LpVariable("eta_fin", cat=pulp.LpContinuous)
    z_fin = pulp.LpVariable.dicts("z_fin", Omega, lowBound=0, cat=pulp.LpContinuous)
    
    # Store variables in the problem object to retrieve them easily
    prob._vars = {
        'x': x, 'a': a, 'u': u, 's': s, 'surplus': surplus,
        'W': W, 'N': N_var, 'F': F,
        'L': L_var, 'eta': eta, 'z': z,
        'L_fin': L_fin, 'eta_fin': eta_fin, 'z_fin': z_fin,
        'y_QR': y_QR, 'y_CN': y_CN,
    }
    prob._skill_levels = L_skills
    prob._nurse_skill = nurse_skill
    prob._I_by_skill = I_by_skill

    # ------------------------------------------------------------------
    # 4. Objective Function — Dual-CVaR Architecture
    # ------------------------------------------------------------------
    # Stage 1: planned assignment cost (same for all nurses)
    obj_planned = pulp.lpSum(c_planned * x[i][j][k] for i in I for j in J for k in K)
    
    # Stage 2: Financial Recourse Cost per Scenario
    for omega in Omega:
        prob += L_fin[omega] == pulp.lpSum(
            c_emergency_skill[l] * a[j][k][l][omega] + c_unmet_skill[l] * u[j][k][l][omega]
            for j in J for k in K for l in L_skills
        ), f"FinLoss_def_{omega}"
        
    obj_expected_recourse = pulp.lpSum(p[omega] * L_fin[omega] for omega in Omega)
    
    # Financial CVaR Linearization
    for omega in Omega:
        prob += z_fin[omega] >= L_fin[omega] - eta_fin, f"FinExcess_loss_{omega}"
        
    cvar_financial = eta_fin + (1.0 / (1.0 - alpha)) * pulp.lpSum(p[omega] * z_fin[omega] for omega in Omega) if alpha < 1.0 else 0
    
    # Fatigue & Fairness tie-breakers
    obj_fatigue_penalty = 0.001 * pulp.lpSum(F[i] for i in I)
    obj_fairness_penalty = 0.001 * (W_max - W_min) + 0.001 * (N_max - N_min)
    
    # Lambda weight for EV vs CVaR trade-off
    lambda_weight = params.get('lambda_weight', 0.5)
    
    if alpha < 1.0:
        prob += obj_planned + lambda_weight * obj_expected_recourse + (1.0 - lambda_weight) * cvar_financial + obj_fatigue_penalty + obj_fairness_penalty, "Total_Cost"
    else:
        prob += obj_planned + obj_expected_recourse + obj_fatigue_penalty + obj_fairness_penalty, "Total_Cost"
    
    # ------------------------------------------------------------------
    # 5. First-stage baseline roster constraints
    # ------------------------------------------------------------------
    # Eq (1): Max one shift per day & qualification
    for i in I:
        for j in J:
            prob += pulp.lpSum(x[i][j][k] for k in K) <= 1, f"Max_one_shift_{i}_{j}"
            for k in K:
                prob += x[i][j][k] <= q.get((i, k), 1), f"Qual_{i}_{j}_{k}"
                
    # Eq (2): Max total assigned shifts and max night shifts (per-nurse limits)
    for i in I:
        prob += pulp.lpSum(x[i][j][k] for j in J for k in K) <= W_bar_i[i], f"Max_shifts_{i}"
        prob += pulp.lpSum(x[i][j][N_shift] for j in J) <= N_bar_i[i], f"Max_nights_{i}"
        
    # Eq (3): Max consecutive working days
    for i in I:
        for j_idx in range(len(J) - C_bar):
            consec_days = J[j_idx:j_idx + C_bar + 1]
            prob += pulp.lpSum(x[i][t][k] for t in consec_days for k in K) <= C_bar, f"Max_consec_{i}_{J[j_idx]}"
            
    # ------------------------------------------------------------------
    # 6. Fatigue-risk proxy and fairness
    # ------------------------------------------------------------------
    # Composite Fatigue Risk Score (SD-CFRS) parameters
    w_k_weights = {'E': 1.0, 'D': 1.0, 'L': 1.1, 'N': 1.5}
    gamma_N = 0.5
    gamma_QR = 2.0
    gamma_CN = 1.5

    for i in I:
        # Quick-return detection
        for j_idx in range(len(J) - 1):
            j1 = J[j_idx]
            j2 = J[j_idx + 1]
            if 'L' in K and 'E' in K:
                prob += x[i][j1]['L'] + x[i][j2]['E'] <= 1 + y_QR[i][j1], f"QR_LE_{i}_{j1}"
            if 'L' in K and 'D' in K:
                prob += x[i][j1]['L'] + x[i][j2]['D'] <= 1 + y_QR[i][j1], f"QR_LD_{i}_{j1}"
            if 'N' in K and 'E' in K:
                prob += x[i][j1]['N'] + x[i][j2]['E'] <= 1 + y_QR[i][j1], f"QR_NE_{i}_{j1}"
            if 'N' in K and 'D' in K:
                prob += x[i][j1]['N'] + x[i][j2]['D'] <= 1 + y_QR[i][j1], f"QR_ND_{i}_{j1}"
                
        # Consecutive night detection
        for j_idx in range(len(J) - 2):
            j1 = J[j_idx]
            j2 = J[j_idx + 1]
            j3 = J[j_idx + 2]
            if 'N' in K:
                prob += x[i][j1]['N'] + x[i][j2]['N'] + x[i][j3]['N'] - 2 <= y_CN[i][j1], f"CN_{i}_{j1}"
                
        # Mandatory post-night rest block
        for j_idx in range(len(J) - 3):
            j1 = J[j_idx]
            j2 = J[j_idx + 1]
            j3 = J[j_idx + 2]
            j4 = J[j_idx + 3]
            if 'N' in K:
                prob += x[i][j1]['N'] + x[i][j2]['N'] - 1 <= 2 - (pulp.lpSum(x[i][j3][k] for k in K) + pulp.lpSum(x[i][j4][k] for k in K)), f"Rest_After_Nights_{i}_{j1}"

        # Eq (4): New Composite Fatigue Risk Score (SD-CFRS)
        fatigue_workload = pulp.lpSum(w_k_weights.get(k, 1.0) * x[i][j][k] for j in J for k in K)
        fatigue_night = gamma_N * pulp.lpSum(x[i][j][N_shift] for j in J) if N_shift in K else 0
        fatigue_qr = gamma_QR * pulp.lpSum(y_QR[i][j] for j in J)
        fatigue_cn = gamma_CN * pulp.lpSum(y_CN[i][j] for j in J)
        
        prob += F[i] == fatigue_workload + fatigue_night + fatigue_qr + fatigue_cn, f"Fatigue_def_{i}"
        prob += F[i] <= F_bar, f"Fatigue_cap_{i}"
        
    # Eq (5): Workload fairness
    for i in I:
        prob += W[i] == pulp.lpSum(x[i][j][k] for j in J for k in K), f"Workload_def_{i}"
        prob += W_max >= W[i], f"W_max_ge_{i}"
        prob += W_min <= W[i], f"W_min_le_{i}"
    prob += W_max - W_min <= Delta_W, "Workload_gap"
    
    # Eq (6): Night-work fairness
    for i in I:
        prob += N_var[i] == pulp.lpSum(x[i][j][N_shift] for j in J), f"Night_def_{i}"
        prob += N_max >= N_var[i], f"N_max_ge_{i}"
        prob += N_min <= N_var[i], f"N_min_le_{i}"
    prob += N_max - N_min <= Delta_N, "Night_gap"
    
    # ------------------------------------------------------------------
    # 7. Second-stage demand response — cascading skill coverage
    # ------------------------------------------------------------------
    # Skill hierarchy: HN (index 0) > RN (index 1) > CNA (index 2)
    # Surplus from tier l cascades into tier l+1
    #
    # Tier HN:  supply_HN + a_HN + u_HN - surplus_HN = d_HN + s_HN
    # Tier RN:  supply_RN + surplus_HN + a_RN + u_RN - surplus_RN = d_RN + s_RN
    # Tier CNA: supply_CNA + surplus_RN + a_CNA + u_CNA = d_CNA + s_CNA
    
    for j in J:
        for k in K:
            for omega in Omega:
                for l_idx, l in enumerate(L_skills):
                    # Supply: count of nurses with this exact skill assigned to (j, k)
                    supply_l = pulp.lpSum(x[i][j][k] for i in I_by_skill.get(l, []))
                    
                    # Inflow: surplus cascading down from the tier above
                    allow_cascading = params.get('allow_skill_cascading', True)
                    if l_idx == 0 or not allow_cascading:
                        inflow = 0  # top tier (HN) has no inflow
                    else:
                        higher_skill = L_skills[l_idx - 1]
                        inflow = surplus[j][k][higher_skill][omega]
                    
                    # Outflow: surplus cascading to the tier below
                    if l in surplus_skills:
                        outflow = surplus[j][k][l][omega]
                    else:
                        outflow = 0  # bottom tier (CNA) has no outflow
                    
                    d_jkl_omega = demand.get((j, k, l, omega), 0)
                    
                    prob += (
                        supply_l + inflow + a[j][k][l][omega] + u[j][k][l][omega]
                        - outflow
                        == d_jkl_omega + s[j][k][l][omega]
                    ), f"Coverage_{j}_{k}_{l}_{omega}"
    
    # Eq (8): Emergency bounds per skill tier
    for j in J:
        for k in K:
            for l in L_skills:
                for omega in Omega:
                    limit = a_bar_skill.get(l, a_bar_val)
                    if limit != float('inf'):
                        prob += a[j][k][l][omega] <= limit, f"Emergency_cap_{j}_{k}_{l}_{omega}"
    
    # ------------------------------------------------------------------
    # 8. CVaR control of unmet demand — with clinical severity weights
    # ------------------------------------------------------------------
    # Eq (9): Scenario loss weighted by skill severity
    for omega in Omega:
        prob += L_var[omega] == pulp.lpSum(
            w_skill.get(l, 1.0) * u[j][k][l][omega]
            for j in J for k in K for l in L_skills
        ), f"Loss_def_{omega}"
        
    # Eq (10): CVaR linearization
    for omega in Omega:
        prob += z[omega] >= L_var[omega] - eta, f"Excess_loss_{omega}"
        
    # Eq (11): CVaR limit constraint
    if alpha < 1.0:
        cvar_expr = eta + (1.0 / (1.0 - alpha)) * pulp.lpSum(p[omega] * z[omega] for omega in Omega)
        prob += cvar_expr <= tau, "CVaR_limit"
        
    return prob
