import sys
import os
import pulp
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model import build_and_solve_model, generate_sample_data, get_default_params

def debug_nss_mode():
    print("Testing NSS Mode with n3=5, c1=100, q_plus=200")
    nurses, scenarios = generate_sample_data(num_nurses=5, num_days=7, num_scenarios=1)
    # Total demand in 7 days for 5 nurses will be around 10-15 shifts.
    
    params = get_default_params()
    params['n1'] = 7
    params['n3'] = 5
    params['c1'] = 100
    params['q_plus'] = 200
    
    # NSS mode is now hardcoded in model.py
    prob, status = build_and_solve_model(nurses, scenarios, params, "SDM", solver_name="CBC")
    
    print(f"Status: {status}")
    if status == "Optimal":
        # Test manual extraction (the one I did before)
        reg_manual = sum(pulp.value(var) for var in prob.variables() if var.name.startswith("RegularShift"))
        print(f"Manual Regular: {reg_manual}")
        
        # Test the actual extractor used in app.py
        from model import extract_results
        results = extract_results(prob, nurses, scenarios, params, "SDM")
        
        if results:
            reg_extracted = results['cost_breakdown']['total_regular_shifts']
            ot_extracted = results['cost_breakdown']['total_overtime_shifts']
            print(f"Extracted Regular: {reg_extracted}")
            print(f"Extracted Overtime: {ot_extracted}")
        else:
            print("Extracted Results: NONE")
        
        print("\nSample Variable Names:")
        sample_vars = [v.name for v in prob.variables() if v.name.startswith("RegularShift")][:5]
        for name in sample_vars:
            print(f"  {name}")
        
        if reg == 0:
            print("ALERT: Model chose ZERO regular shifts despite them being cheaper!")
            # Investigate why
            for i in nurses:
                sr_val = pulp.value(prob.variablesDict()[f"SR_{i}"])
                print(f"  SR_{i} value: {sr_val}")

if __name__ == "__main__":
    debug_nss_mode()
