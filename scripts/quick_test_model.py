"""Quick test to see actual model output"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from model import build_and_solve_model, extract_results, get_default_params

# Load data
nurses = pd.read_csv('data/experiment_nurses.csv')
scenarios = pd.read_csv('data/experiment_scenarios.csv')
nurses_list = nurses.iloc[:, 0].tolist()[:16]  # First 16 nurses

# Set parameters
params = get_default_params()
params['q_plus'] = 350
params['allow_overtime_paradox'] = False

# Solve
print("Solving model...")
prob, status = build_and_solve_model(nurses_list, scenarios, params)

print(f'Status: {status}')
print(f'Total Cost: ${prob.objective.value():,.0f}')

if status == "Optimal":
    results = extract_results(prob, nurses_list, scenarios, params)
    
    print(f'\nResults structure:')
    print(f'  cost_breakdown keys: {list(results["cost_breakdown"].keys())}')
    
    # Get cost breakdown
    cbd = results['cost_breakdown']
    print(f'\nCost Breakdown:')
    for key, val in cbd.items():
        print(f'  {key}: {val}')
    
    # Get schedule info
    if 'roster_df' in results:
        roster = results['roster_df']
        print(f'\nRoster shape: {roster.shape}')
        print(roster.head(20))
    
    # Check keys exist
    print(f'\nTop-level keys: {list(results.keys())}')
