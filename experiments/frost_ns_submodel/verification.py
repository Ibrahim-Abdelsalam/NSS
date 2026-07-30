import pulp
from typing import Dict, Any, List, Tuple

def verify_rostering(
    prob: pulp.LpProblem,
    nurses: List[str],
    days: List[int],
    shifts: List[str],
    scenarios: List[int],
    demand: Dict[Tuple[int, str, int], int],
    params: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Audits satisfaction of every implemented constraint and returns a report.
    """
    report = []
    all_passed = True
    
    def log(msg, passed=True):
        nonlocal all_passed
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        report.append(f"{status} {msg}")

    # If model is not optimal, can't verify fully
    if prob.status != pulp.LpStatusOptimal:
        log("Model is not solved to optimality. Verification aborted.", False)
        return False, "\n".join(report)

    # Extract variables
    x = prob._vars['x']
    W = prob._vars['W']
    N_var = prob._vars['N']
    F = prob._vars['F']
    a = prob._vars['a']
    u = prob._vars['u']
    L = prob._vars['L']
    z = prob._vars['z']
    eta = prob._vars['eta']
    
    # 1. Check one-shift-per-day violations
    one_shift_passed = True
    for i in nurses:
        for j in days:
            shifts_worked = sum(pulp.value(x[i][j][k]) for k in shifts)
            if shifts_worked > 1.0 + 1e-5:
                one_shift_passed = False
                log(f"Nurse {i} worked {shifts_worked} shifts on day {j}", False)
    if one_shift_passed:
        log("One-shift-per-day constraints satisfied.")

    # 2. Check qualification violations
    q = params.get('q', {(i, k): 1 for i in nurses for k in shifts})
    qual_passed = True
    for i in nurses:
        for j in days:
            for k in shifts:
                if pulp.value(x[i][j][k]) > 0.5 and q.get((i, k), 1) == 0:
                    qual_passed = False
                    log(f"Nurse {i} worked unqualified shift {k} on day {j}", False)
    if qual_passed:
        log("Qualification constraints satisfied.")

    # 3. Maximum-shift, night-shift, and consecutive-day limits
    N_shift = params.get('night_shift_id', 'N')
    max_shift_passed = True
    max_night_passed = True
    consec_passed = True
    
    w_vals = []
    n_vals = []
    f_vals = []
    
    for i in nurses:
        # Recompute totals for verification (don't just trust the auxiliary variables)
        total_shifts = sum(pulp.value(x[i][j][k]) for j in days for k in shifts)
        total_nights = sum(pulp.value(x[i][j][N_shift]) for j in days)
        w_vals.append(total_shifts)
        n_vals.append(total_nights)
        f_vals.append(total_shifts + total_nights)
        
        if total_shifts > params['W_bar'] + 1e-5:
            max_shift_passed = False
            log(f"Nurse {i} exceeded W_bar: {total_shifts} > {params['W_bar']}", False)
        if total_nights > params['N_bar'] + 1e-5:
            max_night_passed = False
            log(f"Nurse {i} exceeded N_bar: {total_nights} > {params['N_bar']}", False)
            
        # Consecutive days
        for j_idx in range(len(days) - params['C_bar']):
            consec_sum = sum(pulp.value(x[i][days[t]][k]) for t in range(j_idx, j_idx + params['C_bar'] + 1) for k in shifts)
            if consec_sum > params['C_bar'] + 1e-5:
                consec_passed = False
                log(f"Nurse {i} exceeded consecutive days starting at index {j_idx}: {consec_sum} > {params['C_bar']}", False)

    if max_shift_passed: log(f"Maximum shifts limit (W_bar={params['W_bar']}) satisfied.")
    if max_night_passed: log(f"Maximum night shifts limit (N_bar={params['N_bar']}) satisfied.")
    if consec_passed: log(f"Consecutive days limit (C_bar={params['C_bar']}) satisfied.")

    # 4. Fatigue score for every nurse
    fatigue_passed = True
    for idx, i in enumerate(nurses):
        if f_vals[idx] > params['F_bar'] + 1e-5:
            fatigue_passed = False
            log(f"Nurse {i} exceeded fatigue cap: {f_vals[idx]} > {params['F_bar']}", False)
    if fatigue_passed:
        log(f"Fatigue score limits (F_bar={params['F_bar']}) satisfied. Max score achieved: {max(f_vals)}.")

    # 5. Workload and night-work gaps
    w_gap = max(w_vals) - min(w_vals)
    n_gap = max(n_vals) - min(n_vals)
    
    if w_gap <= params['Delta_W'] + 1e-5:
        log(f"Workload fairness gap satisfied: {w_gap} <= {params['Delta_W']}")
    else:
        log(f"Workload fairness gap failed: {w_gap} > {params['Delta_W']}", False)
        
    if n_gap <= params['Delta_N'] + 1e-5:
        log(f"Night-work fairness gap satisfied: {n_gap} <= {params['Delta_N']}")
    else:
        log(f"Night-work fairness gap failed: {n_gap} > {params['Delta_N']}", False)

    # 6. Scenario unmet demand and emergency staffing
    emerg_passed = True
    a_bar = params.get('a_bar', 2)
    w_weights = params.get('w', {k: 1.0 for k in shifts})
    
    for omega in scenarios:
        scenario_loss = 0
        for j in days:
            for k in shifts:
                a_val = pulp.value(a[j][k][omega])
                u_val = pulp.value(u[j][k][omega])
                scenario_loss += w_weights.get(k, 1.0) * u_val
                
                if a_val > a_bar + 1e-5:
                    emerg_passed = False
                    log(f"Scenario {omega}, Day {j}, Shift {k} exceeded emergency capacity: {a_val} > {a_bar}", False)
        
        # Verify L variable matches calculation
        l_val = pulp.value(L[omega])
        if abs(scenario_loss - l_val) > 1e-5:
            log(f"Scenario loss mismatch for {omega}: calculated {scenario_loss}, model {l_val}", False)

    if emerg_passed:
        log(f"Emergency staffing limits (a_bar={a_bar}) satisfied across all scenarios.")

    # 7. Computed CVaR and tau limit
    alpha = params.get('alpha', 0.80)
    tau = params.get('tau', 100)
    eta_val = pulp.value(eta)
    p = params.get('p_omega', {omega: 1.0 / len(scenarios) for omega in scenarios})
    
    expected_excess = sum(p[omega] * pulp.value(z[omega]) for omega in scenarios)
    cvar_val = eta_val + (1.0 / (1.0 - alpha)) * expected_excess
    
    if cvar_val <= tau + 1e-5:
        log(f"CVaR limit satisfied: {cvar_val:.2f} <= {tau}")
    else:
        log(f"CVaR limit exceeded: {cvar_val:.2f} > {tau}", False)

    return all_passed, "\n".join(report)
