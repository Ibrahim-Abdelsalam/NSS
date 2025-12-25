"""
CVaR Parameter Diagnostics and Sensitivity Test

Purpose: Diagnose why CVaR constraint causes infeasibility.
Test different μ values to find feasible range.

Run: python tests/test_cvar_sensitivity.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from model import build_and_solve_model, generate_sample_data, get_default_params


def test_cvar_sensitivity():
    """Test CVaR with different μ values to find feasible range"""
    print("\n" + "="*80)
    print("CVaR PARAMETER SENSITIVITY ANALYSIS")
    print("="*80)
    
    # Generate problem
    nurses, scenarios = generate_sample_data(num_nurses=10, num_days=14, num_scenarios=5)
    base_params = get_default_params()
    base_params['allow_overtime_paradox'] = False
    base_params['sigma'] = 0.95
    
    # Test different μ values
    mu_values = [5, 10, 15, 20, 30, 50, 100, 1000]
    
    results = []
    
    for mu in mu_values:
        print(f"\nTesting μ = {mu}")
        print("-" * 40)
        
        params = base_params.copy()
        params['mu'] = mu
        
        prob, status = build_and_solve_model(nurses, scenarios, params, "SDM-CVaR")
        
        result = {
            'mu': mu,
            'status': status,
            'optimal': status == "Optimal"
        }
        
        if status in ["Optimal", "Feasible"]:
            result['objective'] = prob.objective.value()
            
            # Extract CVaR metrics
            for v in prob.variables():
                if v.name == "VaR_xi" and v.varValue is not None:
                    result['var'] = v.varValue
            
            z_values = [v.varValue for v in prob.variables() 
                       if v.name.startswith("ExcessLoss_z") and v.varValue is not None]
            
            if z_values:
                expected_excess = sum(z_values) / len(scenarios['scenario'].unique())
                cvar_value = result.get('var', 0) + (1.0 / (1.0 - params['sigma'])) * expected_excess
                result['cvar'] = cvar_value
                result['expected_excess'] = expected_excess
                
                print(f"  Status: {status}")
                print(f"  VaR: {result['var']:.2f}")
                print(f"  CVaR: {cvar_value:.2f} (limit: {mu})")
                print(f"  Objective: ${result['objective']:.2f}")
        else:
            print(f"  Status: {status} ❌")
        
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("SENSITIVITY SUMMARY")
    print("="*80)
    
    df = pd.DataFrame(results)
    print(df.to_string())
    
    # Find minimum feasible μ
    feasible = df[df['optimal']]
    if not feasible.empty:
        min_mu = feasible['mu'].min()
        print(f"\n✅ Minimum feasible μ: {min_mu}")
        print(f"   CVaR value at minimum: {feasible[feasible['mu'] == min_mu]['cvar'].values[0]:.2f}")
    else:
        print("\n❌ No feasible solutions found")
    
    return df


if __name__ == "__main__":
    results = test_cvar_sensitivity()
