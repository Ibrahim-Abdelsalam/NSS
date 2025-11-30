import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

import model


def main():
    np.random.seed(1)
    workspace = Path(__file__).resolve().parents[1]
    data_dir = workspace / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    # Test parameters chosen to exercise CVaR tail behavior
    num_nurses = 20
    num_days = 14
    num_scenarios = 6
    shifts = ['E', 'D', 'L', 'N']

    # Generate nurse list
    nurses = [f"N{i+1}" for i in range(num_nurses)]

    # Construct scenarios such that a couple scenarios are high-demand (tail)
    scenario_rows = []
    base_demand = {'E': 3, 'D': 4, 'L': 3, 'N': 2}

    # Create 4 'typical' scenarios and 2 'stress' scenarios
    for s in range(1, num_scenarios + 1):
        is_stress = s > 4  # scenarios 5 and 6 are stress
        for day in range(1, num_days + 1):
            weekend = (day % 7) in (0, 6)
            for shift in shifts:
                if is_stress:
                    # Stress scenario: increase demand by 50% and add noise
                    demand = max(1, int(base_demand[shift] * 1.5 + (np.random.randint(0, 2))))
                else:
                    # Typical scenario: base with small noise
                    demand = max(1, base_demand[shift] + (np.random.randint(-1, 2)))
                if weekend:
                    demand = max(1, int(demand * 0.9))
                scenario_rows.append({
                    'scenario': s,
                    'day': day,
                    'shift': shift,
                    'demand': int(demand)
                })

    scenarios_df = pd.DataFrame(scenario_rows)

    # File paths
    nurses_file = data_dir / 'cvar_nurses.csv'
    scenarios_file = data_dir / 'cvar_scenarios.csv'

    # Write nurse list and scenarios
    with open(nurses_file, 'w') as f:
        for n in nurses:
            f.write(n + '\n')

    scenarios_df.to_csv(scenarios_file, index=False)

    print(f"Wrote nurses -> {nurses_file}")
    print(f"Wrote scenarios -> {scenarios_file} (rows: {len(scenarios_df)})")

    # Model parameters for CVaR test
    params = model.get_default_params()
    params['n1'] = 12   # max shifts per nurse
    params['n2'] = 4    # max nights
    params['n3'] = 2    # min regular shifts per nurse
    params['c1'] = 100.0
    params['c2'] = 150.0
    params['q_plus'] = 300.0  # higher emergency cost to emphasize CVaR
    params['sigma'] = 0.90
    params['mu'] = 5.0

    # Run model with SDM-CVaR
    print("Running SDM-CVaR model (sigma=0.90, mu=5.0)...")
    prob, status = model.build_and_solve_model(nurses, scenarios_df, params, model_type='SDM-CVaR', solver_name='AUTO')
    print('Solver status:', status)

    results = None
    if status == 'Optimal':
        results = model.extract_results(prob, nurses, scenarios_df, params, model_type='SDM-CVaR')

    # Save expected output
    out_dir = workspace / 'expected_outputs'
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        'status': status,
        'cost_breakdown': results['cost_breakdown'] if results else None,
        'scenario_df': results['scenario_df'].to_dict(orient='records') if results else None,
        'risk_metrics': results.get('risk_metrics') if results else None
    }

    with open(out_dir / 'cvar_expected.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print('\nSummary:')
    print('Status:', status)
    if results:
        cb = results['cost_breakdown']
        print(f"Total cost: {cb['total_cost']}")
        print(f"Stage1 total: {cb['stage1_total']}")
        print(f"Stage2 expected cost: {cb['stage2_expected_cost']}")
        print(f"Total regular shifts: {cb['total_regular_shifts']}")
        print('\nPer-scenario shortages (shortage_shifts, recourse_cost):')
        print(results['scenario_df'][['scenario', 'shortage_shifts', 'recourse_cost']])
        print('\nRisk metrics:')
        print(results['risk_metrics'])
    else:
        print('No results (model not optimal) - check solver logs or parameters')


if __name__ == '__main__':
    main()
