import sys
sys.path.append('/Users/ibrahim/Documents/GitHub/NSS')

import pulp
from typing import Dict, Any, Tuple
from core.data_generator import generate_sample_data
from experiments.frost_ns_submodel.model import build_frost_ns_model

def run():
    print("======================================================")
    print(" Simplified FROST-NS Prototype Execution")
    print("======================================================")
    
    # 1. Generate Context Data
    print("Generating synthetic data for prototype context...")
    # As per corrections: 10 nurses, 14 days, 5 scenarios
    num_nurses = 10
    num_days = 14
    num_scenarios = 5
    nurses_list, scenarios_df = generate_sample_data(num_nurses=num_nurses, num_days=num_days, num_scenarios=num_scenarios, seed=42)
    
    days = list(range(1, num_days + 1))
    shifts = ['E', 'D', 'L', 'N']
    scenarios = list(range(1, num_scenarios + 1))
    
    # Format demand dictionary
    demand = {}
    for _, row in scenarios_df.iterrows():
        j = int(row['day'])
        k = row['shift']
        omega = int(row['scenario'])
        demand[(j, k, omega)] = int(row['demand'])
        
    # 2. Define Prototype Parameters (as corrected)
    params = {
        'W_bar': 10,       # maximum total shifts per nurse
        'N_bar': 3,        # maximum night shifts per nurse
        'C_bar': 4,        # maximum consecutive working days
        'F_bar': 12,       # common fatigue-risk cap
        'Delta_W': 2,      # workload fairness gap
        'Delta_N': 1,      # night-work fairness gap
        'alpha': 0.80,     # CVaR confidence level for 5 scenarios
        'tau': 20,         # Maximum permitted CVaR limit (adjust if infeasible)
        'a_bar': 2,        # maximum emergency nurses per day-shift
        'c_planned': 100,  # illustrative planned assignment cost
        'c_emergency': 200,# illustrative emergency nurse cost
        'c_unmet': 300     # illustrative unmet-demand penalty
    }
    
    print("\nParameters:")
    for k, v in params.items():
        print(f"  {k} = {v}")
    print("\nBuilding mathematical model...")
    
    # 3. Build Model
    prob = build_frost_ns_model(nurses_list, days, shifts, scenarios, demand, params)
    
    # 4. Solve Model
    print("Solving model...")
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=60)
    prob.solve(solver)
    
    print(f"\nSolver Status: {pulp.LpStatus[prob.status]}")
    if prob.status != pulp.LpStatusOptimal:
        print("Model did not find an optimal solution. It might be infeasible with these tight parameters.")
        return
        
    print(f"Objective Value: {pulp.value(prob.objective)}")
    
    # Extract variables
    x = prob._vars['x']
    W = prob._vars['W']
    N_var = prob._vars['N']
    F = prob._vars['F']
    a = prob._vars['a']
    u = prob._vars['u']
    L = prob._vars['L']
    z = prob._vars['z']
    eta = pulp.value(prob._vars['eta'])
    
    print("\n======================================================")
    print(" Results & Automated Verification")
    print("======================================================")
    
    # Check automated bounds and compute achieved gaps
    w_vals = []
    n_vals = []
    f_vals = []
    
    for i in nurses_list:
        w_val = pulp.value(W[i])
        n_val = pulp.value(N_var[i])
        f_val = pulp.value(F[i])
        
        w_vals.append(w_val)
        n_vals.append(n_val)
        f_vals.append(f_val)
        
        # Automated checks
        assert w_val <= params['W_bar'], f"Nurse {i} exceeded W_bar!"
        assert n_val <= params['N_bar'], f"Nurse {i} exceeded N_bar!"
        assert f_val <= params['F_bar'], f"Nurse {i} exceeded F_bar!"
        
    w_gap = max(w_vals) - min(w_vals)
    n_gap = max(n_vals) - min(n_vals)
    
    assert w_gap <= params['Delta_W'], f"Workload gap {w_gap} exceeded Delta_W!"
    assert n_gap <= params['Delta_N'], f"Night gap {n_gap} exceeded Delta_N!"
    
    print(f"Constraints Verification: PASSED")
    print(f"Achieved Workload Gap (W_max - W_min): {w_gap} (Limit: {params['Delta_W']})")
    print(f"Achieved Night-work Gap (N_max - N_min): {n_gap} (Limit: {params['Delta_N']})")
    print(f"Max Fatigue Score: {max(f_vals)} (Limit: {params['F_bar']})")
    
    # Verify emergency limits
    for j in days:
        for k in shifts:
            for omega in scenarios:
                assert pulp.value(a[j][k][omega]) <= params['a_bar'], f"Emergency capacity exceeded on Day {j}, Shift {k}, Scenario {omega}"
    print(f"Emergency Capacity Constraints: PASSED (Max {params['a_bar']} per day-shift)")
    
    # CVaR and Scenario Loss
    print("\nScenario Losses (Weighted Unmet Demand):")
    losses = []
    for omega in scenarios:
        l_val = pulp.value(L[omega])
        z_val = pulp.value(z[omega])
        losses.append(l_val)
        print(f"  Scenario {omega}: Loss = {l_val}, Excess (z) = {z_val}")
        
    print(f"\nValue-at-Risk (eta) = {eta}")
    
    cvar_achieved = eta + (1.0 / (1.0 - params['alpha'])) * sum((1.0 / num_scenarios) * pulp.value(z[omega]) for omega in scenarios)
    print(f"Achieved CVaR (alpha={params['alpha']}): {cvar_achieved} (Limit: {params['tau']})")
    assert cvar_achieved <= params['tau'] + 1e-5, f"CVaR limit exceeded!"
    
    print("\n======================================================")
    print("This prototype will demonstrate computational feasibility")
    print("of the simplified formulation on synthetic data and verify")
    print("that the implemented constraints are satisfied.")
    print("Note: The cost values (100, 200, 300) are illustrative only.")
    print("======================================================")

if __name__ == "__main__":
    run()
