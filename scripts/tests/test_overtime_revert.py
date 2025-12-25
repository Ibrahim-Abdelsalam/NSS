import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from model import build_and_solve_model, generate_sample_data, get_default_params, extract_results

def test_overtime_behavior():
    print("🚀 Starting Overtime Behavior Test (Paper-Pure Logic)")
    
    # 1. Setup Parameters
    params = get_default_params()
    params['n1'] = 15  # Max total shifts
    params['n3'] = 5   # Min regular shifts (Feasible in 7 days)
    params['c1'] = 100 # Regular cost
    params['c2'] = 150 # Overtime cost
    
    # 2. Generate small sample data
    # 8 nurses for 7 days
    nurses, scenarios_df = generate_sample_data(num_nurses=8, num_days=7, num_scenarios=3)
    
    print(f"📊 Problem Size: {len(nurses)} nurses, 7 days, 3 scenarios")
    print(f"⚙️  Parameters: n1={params['n1']}, n3={params['n3']} (MIN ONLY)")
    
    # 3. Solve the model
    # Note: We use model_type='SDM' for faster testing of the core logic
    prob, status = build_and_solve_model(
        nurses_list=nurses,
        scenarios_df=scenarios_df,
        model_params=params,
        model_type="SDM"
    )
    
    if status != "Optimal":
        print(f"❌ Solve failed with status: {status}")
        return

    # 4. Extract results and analyze
    results = extract_results(prob, nurses, scenarios_df, params, model_type="SDM")
    
    # Analyze totals
    total_reg = results['roster_df']['Total_Regular'].sum()
    total_ot = results['roster_df']['Total_Overtime'].sum()
    
    # Calculate total emergency shifts (alpha) across all scenarios
    # scenario_df has 'shortage_shifts' which is the sum of alpha for that scenario
    avg_emergency = results['scenario_df']['shortage_shifts'].mean()
    total_emergency_all_scenarios = results['scenario_df']['shortage_shifts'].sum()
    
    print("\n📈 SOLVER RESULTS:")
    print(f"   - Total Regular Shifts: {total_reg}")
    print(f"   - Total Overtime Shifts: {total_ot}")
    print(f"   - Average Emergency Staff (per scenario): {avg_emergency:.2f}")
    print(f"   - Total Emergency Staff (all scenarios): {total_emergency_all_scenarios}")
    
    if total_ot == 0:
        print("\n✅ SUCCESS: The Overtime Paradox is BACK!")
        print("   Explanation: Because c1 < c2 and there is no upper cap on regular shifts (Constraint 8),")
        print("   the solver fulfilled ALL duties using regular shifts and avoided expensive overtime.")
    else:
        print(f"\n⚠️  NOTE: Solver used {total_ot} overtime shifts.")
        print("   This might happen if shift/rest constraints prevented nurses from taking more regular shifts.")

if __name__ == "__main__":
    test_overtime_behavior()
