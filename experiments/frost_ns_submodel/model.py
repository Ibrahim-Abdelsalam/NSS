import pulp
from typing import List, Dict, Any, Tuple

def build_frost_ns_model(
    nurses: List[str],
    days: List[int],
    shifts: List[str],
    scenarios: List[int],
    demand: Dict[Tuple[int, str, int], int],  # (day, shift, scenario) -> demand
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
    W_bar = params.get('W_bar', 10)
    N_bar = params.get('N_bar', 3)
    C_bar = params.get('C_bar', 4)
    F_bar = params.get('F_bar', 12)
    Delta_W = params.get('Delta_W', 2)
    Delta_N = params.get('Delta_N', 1)
    
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
    # 2. Model Initialization
    # ------------------------------------------------------------------
    prob = pulp.LpProblem("FROST_NS_Model", pulp.LpMinimize)
    
    # ------------------------------------------------------------------
    # 3. Decision Variables
    # ------------------------------------------------------------------
    
    # First-stage assignment: x_{ijk} in {0, 1}
    x = pulp.LpVariable.dicts("x", (I, J, K), cat=pulp.LpBinary)
    
    # Second-stage variables for demand response
    # a_{jk}^\omega: generic emergency staffing
    a = pulp.LpVariable.dicts("a", (J, K, Omega), lowBound=0, cat=pulp.LpInteger)
    # u_{jk}^\omega: unmet demand
    u = pulp.LpVariable.dicts("u", (J, K, Omega), lowBound=0, cat=pulp.LpInteger)
    # s_{jk}^\omega: surplus coverage
    s = pulp.LpVariable.dicts("s", (J, K, Omega), lowBound=0, cat=pulp.LpInteger)
    
    # Fatigue and fairness variables
    W = pulp.LpVariable.dicts("W", I, lowBound=0, cat=pulp.LpContinuous)
    W_max = pulp.LpVariable("W_max", lowBound=0, cat=pulp.LpContinuous)
    W_min = pulp.LpVariable("W_min", lowBound=0, cat=pulp.LpContinuous)
    
    N_var = pulp.LpVariable.dicts("N_var", I, lowBound=0, cat=pulp.LpContinuous)
    N_max = pulp.LpVariable("N_max", lowBound=0, cat=pulp.LpContinuous)
    N_min = pulp.LpVariable("N_min", lowBound=0, cat=pulp.LpContinuous)
    
    F = pulp.LpVariable.dicts("F", I, lowBound=0, cat=pulp.LpContinuous)
    
    # CVaR variables
    L = pulp.LpVariable.dicts("L", Omega, lowBound=0, cat=pulp.LpContinuous)
    eta = pulp.LpVariable("eta", cat=pulp.LpContinuous)
    z = pulp.LpVariable.dicts("z", Omega, lowBound=0, cat=pulp.LpContinuous)
    
    # Store variables in the problem object to retrieve them easily
    prob._vars = {'x': x, 'a': a, 'u': u, 's': s, 'W': W, 'N': N_var, 'F': F, 'L': L, 'eta': eta, 'z': z}

    # ------------------------------------------------------------------
    # 4. Objective Function (12)
    # ------------------------------------------------------------------
    # min sum(c*x) + sum(p*(c^A*a + c^U*u))
    obj_planned = pulp.lpSum(c_planned * x[i][j][k] for i in I for j in J for k in K)
    obj_expected_recourse = pulp.lpSum(
        p[omega] * (c_emergency * a[j][k][omega] + c_unmet * u[j][k][omega])
        for omega in Omega for j in J for k in K
    )
    prob += obj_planned + obj_expected_recourse, "Total_Cost"
    
    # ------------------------------------------------------------------
    # 5. First-stage baseline roster constraints
    # ------------------------------------------------------------------
    # Eq (1): Max one shift per day & qualification
    for i in I:
        for j in J:
            prob += pulp.lpSum(x[i][j][k] for k in K) <= 1, f"Max_one_shift_{i}_{j}"
            for k in K:
                prob += x[i][j][k] <= q.get((i, k), 1), f"Qual_{i}_{j}_{k}"
                
    # Eq (2): Max total assigned shifts and max night shifts
    for i in I:
        prob += pulp.lpSum(x[i][j][k] for j in J for k in K) <= W_bar, f"Max_shifts_{i}"
        prob += pulp.lpSum(x[i][j][N_shift] for j in J) <= N_bar, f"Max_nights_{i}"
        
    # Eq (3): Max consecutive working days
    for i in I:
        for j_idx in range(len(J) - C_bar):
            consec_days = J[j_idx:j_idx + C_bar + 1]
            prob += pulp.lpSum(x[i][t][k] for t in consec_days for k in K) <= C_bar, f"Max_consec_{i}_{J[j_idx]}"
            
    # ------------------------------------------------------------------
    # 6. Fatigue-risk proxy and fairness
    # ------------------------------------------------------------------
    # Eq (4): Fatigue score
    for i in I:
        prob += F[i] == pulp.lpSum(x[i][j][k] for j in J for k in K) + pulp.lpSum(x[i][j][N_shift] for j in J), f"Fatigue_def_{i}"
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
    # 7. Second-stage demand response
    # ------------------------------------------------------------------
    # Eq (7): Coverage balance
    for j in J:
        for k in K:
            for omega in Omega:
                prob += (
                    pulp.lpSum(q.get((i, k), 1) * x[i][j][k] for i in I) + a[j][k][omega] + u[j][k][omega] 
                    == demand[(j, k, omega)] + s[j][k][omega]
                ), f"Coverage_{j}_{k}_{omega}"
                
    # Eq (8): Emergency bounds
    for j in J:
        for k in K:
            for omega in Omega:
                prob += a[j][k][omega] <= a_bar_val, f"Emergency_cap_{j}_{k}_{omega}"
                
    # ------------------------------------------------------------------
    # 8. CVaR control of unmet demand
    # ------------------------------------------------------------------
    # Eq (9): Scenario loss
    for omega in Omega:
        prob += L[omega] == pulp.lpSum(w.get(k, 1.0) * u[j][k][omega] for j in J for k in K), f"Loss_def_{omega}"
        
    # Eq (10): CVaR linearization
    for omega in Omega:
        prob += z[omega] >= L[omega] - eta, f"Excess_loss_{omega}"
        
    # Eq (11): CVaR limit constraint
    if alpha < 1.0:
        cvar_expr = eta + (1.0 / (1.0 - alpha)) * pulp.lpSum(p[omega] * z[omega] for omega in Omega)
        prob += cvar_expr <= tau, "CVaR_limit"
        
    return prob
