import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

import model


def main():
    np.random.seed(0)
    workspace = Path(__file__).resolve().parents[1]
    data_dir = workspace / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    num_nurses = 40
    num_days = 30
    num_scenarios = 5
    shifts = ['E', 'D', 'L', 'N']

    # Generate nurse list
    nurses = [f"Nurse_{i+1}" for i in range(num_nurses)]

    # Deterministic scenario generation with mild variability
    base_demand = {'E': 3, 'D': 4, 'L': 3, 'N': 2}
    scenarios = []
    for s in range(1, num_scenarios + 1):
        for day in range(1, num_days + 1):
            weekend = (day % 7) in (0, 6)
            for shift in shifts:
                # small systematic variation per scenario
                variation = (s - 3) // 2  # yields -1, -1, 0, 0, 1 for s=1..5
                noise = (hash((s, day, shift)) % 3) - 1  # pseudo-random -1..1
                demand = max(1, base_demand[shift] + variation + noise)
                if weekend:
                    demand = max(1, int(demand * 0.8))
                scenarios.append({'scenario': s, 'day': day, 'shift': shift, 'demand': int(demand)})

    scenarios_df = pd.DataFrame(scenarios)

    # Write files
    nurses_file = data_dir / '40_nurses_30days_nurses.csv'
    scenarios_file = data_dir / '40_nurses_30days_scenarios.csv'

    with open(nurses_file, 'w') as f:
        for n in nurses:
            f.write(n + '\n')

    scenarios_df.to_csv(scenarios_file, index=False)

    print(f"Wrote nurses -> {nurses_file}")
    print(f"Wrote scenarios -> {scenarios_file} (rows: {len(scenarios_df)})")

    # Prepare model params (relax per-nurse minimum regular shifts to avoid infeasibility)
    params = model.get_default_params()
    params['n3'] = 0  # no minimum regular shifts per nurse for this stress test
    params['n1'] = 15
    params['c1'] = 100.0
    params['c2'] = 150.0
    params['q_plus'] = 200.0

    # Run model
    print("Running model (this may take up to several minutes)...")
    prob, status = model.build_and_solve_model(nurses, scenarios_df, params, model_type='SDM', solver_name='CBC')
    print("Solver status:", status)

    results = None
    if status == 'Optimal':
        results = model.extract_results(prob, nurses, scenarios_df, params, model_type='SDM')

    # Save expected output
    out_dir = workspace / 'expected_outputs'
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        'status': status,
        'cost_breakdown': results['cost_breakdown'] if results else None,
        'scenario_df': results['scenario_df'].to_dict(orient='records') if results else None,
    }

    with open(out_dir / '40x30_expected.json', 'w') as f:
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
    else:
        print('No results (model not optimal) - check solver logs or parameters')


if __name__ == '__main__':
    main()
