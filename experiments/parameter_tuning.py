#!/usr/bin/env python3
"""
Parameter Tuning Experiments for PWL Fatigue Implementation

Factorial Design: 3×3×3×3 = 81 configurations
- Fatigue lambda (λ): {0.02, 0.03, 0.04}
- Safety weight ($): {30, 50, 80}
- Max threshold: {0.60, 0.70, 0.80}
- Demand level: {Low, Medium, High}

Each configuration runs 3 replications = 243 total runs

Usage:
    python experiments/parameter_tuning.py --mode test     # Quick test (9 runs)
    python experiments/parameter_tuning.py --mode full     # Full experiment (243 runs)
"""

import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import build_and_solve_model, generate_sample_data, get_default_params, extract_results
from datetime import datetime
import itertools
import time
import argparse



# ====================================================================================
# EXPERIMENTAL DESIGN
# ====================================================================================

# Factor levels
LAMBDA_VALUES = [0.02, 0.03, 0.04]  # Fatigue accumulation rate
WEIGHT_VALUES = [30, 50, 80]        # Patient safety cost ($/unit)
THRESHOLD_VALUES = [0.60, 0.70, 0.80]  # Maximum fatigue allowed
DEMAND_LEVELS = ['Low', 'Medium', 'High']  # Demand uncertainty

REPLICATIONS = 30  # Replications per configuration (min 30 for Central Limit Theorem)

# Problem instance sizes by demand level
# NOTE: n3=0 removes minimum commitment, allowing flexible nurse usage
#       High q_plus forces model to prefer baseline nurses over emergency
INSTANCE_CONFIG = {
    'Low': {
        'nurses': 12,
        'days': 10,
        'scenarios': 5,
        'n3': 0,  # NO minimum commitment - allows SR[i]=1 with few shifts
        'q_plus': 400,  # Emergency cost >> regular cost
    },
    'Medium': {
        'nurses': 15,
        'days': 14,
        'scenarios': 10,
        'n3': 0,  # NO minimum commitment
        'q_plus': 400,
    },
    'High': {
        'nurses': 18,
        'days': 14,
        'scenarios': 15,
        'n3': 0,  # NO minimum commitment
        'q_plus': 450,
    }
}


# ====================================================================================
# METRICS COLLECTION
# ====================================================================================

def collect_metrics(results, model, nurses, scenarios, solve_time, status):
    """Extract comprehensive metrics from solved model"""
    
    metrics = {
        'status': status,
        'solve_time': solve_time,
    }
    
    # Handle timeout/no solution case
    if results is None:
        return {
            'status': 'NO_SOLUTION',
            'solve_time': solve_time,
            'error': 'Solver timed out or no feasible solution found',
            'total_cost': None,
            'stage1_cost': None,
            'stage2_cost': None,
            'regular_shifts': None,
            'overtime_shifts': None,
            'patient_safety_cost': None,
            'max_fatigue': None,
            'avg_fatigue': None,
            'high_fatigue_days': None,
            'fatigue_threshold': None,
            'working_nurses': None,
            'regular_shift_count': None,
            'overtime_shift_count': None,
            'avg_shortage': None,
            'max_shortage': None,
            'avg_recourse_cost': None,
            'avg_consecutive_shifts': None,
            'max_consecutive_shifts': None,
        }
    
    # Cost breakdown
    cost = results.get('cost_breakdown', {})
    metrics['total_cost'] = cost.get('total_cost', 0)
    metrics['stage1_cost'] = cost.get('stage1_total', 0)
    metrics['stage2_cost'] = cost.get('stage2_expected_cost', 0)
    metrics['regular_shifts'] = cost.get('total_regular_shifts', 0)
    metrics['overtime_shifts'] = cost.get('total_overtime_shifts', 0)
    
    # Fatigue metrics
    fm = results.get('fatigue_metrics', {})
    if fm and fm.get('enabled'):
        metrics['patient_safety_cost'] = fm.get('patient_safety_cost', 0)
        metrics['max_fatigue'] = fm.get('max_fatigue', 0)
        metrics['avg_fatigue'] = fm.get('avg_fatigue', 0)
        metrics['high_fatigue_days'] = fm.get('high_fatigue_days', 0)
        metrics['fatigue_threshold'] = fm.get('fatigue_threshold', 0)
    else:
        metrics['patient_safety_cost'] = 0
        metrics['max_fatigue'] = 0
        metrics['avg_fatigue'] = 0
        metrics['high_fatigue_days'] = 0
        metrics['fatigue_threshold'] = 0
    
    # Count working nurses
    sr_vars = [v for v in model.variables() if v.name.startswith('SR_') and 'Link' not in v.name]
    metrics['working_nurses'] = sum(1 for v in sr_vars if v.varValue and v.varValue > 0.5)
    
    # Count shifts
    regular_shift_vars = [v for v in model.variables() if 'RegularShift' in v.name and v.varValue and v.varValue > 0.5]
    overtime_shift_vars = [v for v in model.variables() if 'OvertimeShift' in v.name and v.varValue and v.varValue > 0.5]
    metrics['regular_shift_count'] = len(regular_shift_vars)
    metrics['overtime_shift_count'] = len(overtime_shift_vars)
    
    # Scenario analysis
    scenario_df = results.get('scenario_df', pd.DataFrame())
    if not scenario_df.empty:
        metrics['avg_shortage'] = scenario_df['shortage_shifts'].mean()
        metrics['max_shortage'] = scenario_df['shortage_shifts'].max()
        metrics['avg_recourse_cost'] = scenario_df['recourse_cost'].mean()
    else:
        metrics['avg_shortage'] = 0
        metrics['max_shortage'] = 0
        metrics['avg_recourse_cost'] = 0
    
    # Schedule quality - consecutive shifts
    roster_df = results.get('roster_df', pd.DataFrame())
    if not roster_df.empty:
        consecutive_shifts = []
        for _, nurse_row in roster_df.iterrows():
            # Count consecutive working days
            shift_cols = [col for col in roster_df.columns if col.startswith('D')]
            working_days = [1 if nurse_row[col] != 'OFF' else 0 for col in shift_cols]
            
            # Find consecutive sequences
            current_streak = 0
            max_streak = 0
            for working in working_days:
                if working:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            
            if max_streak > 0:
                consecutive_shifts.append(max_streak)
        
        metrics['avg_consecutive_shifts'] = np.mean(consecutive_shifts) if consecutive_shifts else 0
        metrics['max_consecutive_shifts'] = np.max(consecutive_shifts) if consecutive_shifts else 0
    else:
        metrics['avg_consecutive_shifts'] = 0
        metrics['max_consecutive_shifts'] = 0
    
    return metrics


# ====================================================================================
# RUN SINGLE EXPERIMENT
# ====================================================================================

def run_experiment(config_id, lambda_val, weight_val, threshold_val, demand_level, rep, seed=None, time_limit=None):
    """Run a single experimental configuration"""
    
    print(f'\n{"="*80}')
    print(f'Config {config_id} | λ={lambda_val} w=${weight_val} T={threshold_val} D={demand_level} Rep={rep}')
    print(f'{"="*80}')
    
    # Set random seed for reproducibility
    if seed is None:
        seed = 1000 + rep  # Default seed based on replication number
    np.random.seed(seed)
    
    # Get instance configuration
    inst_config = INSTANCE_CONFIG[demand_level]
    nurses_count = inst_config['nurses']
    days_count = inst_config['days']
    scenarios_count = inst_config['scenarios']
    
    # Generate problem instance
    print(f'Generating instance: {nurses_count} nurses × {days_count} days × {scenarios_count} scenarios')
    nurses, scenarios = generate_sample_data(nurses_count, days_count, scenarios_count)
    
    # Configure parameters
    params = get_default_params()
    params['patient_safety_enabled'] = True
    params['fatigue_lambda'] = lambda_val
    params['patient_safety_weight'] = weight_val
    params['max_fatigue_threshold'] = threshold_val
    params['shift_duration'] = 12
    params['n1'] = 15
    params['n3'] = inst_config['n3']
    params['q_plus'] = inst_config['q_plus']
    
    # Set time limit (use provided or default to 60 seconds)
    if time_limit is not None:
        params['time_limit'] = time_limit
    elif time_limit is None and seed != 1000 + rep:  # Retry case (different seed pattern)
        params['time_limit'] = None  # Unlimited for retries
    else:
        params['time_limit'] = 60  # 1 minute for regular runs
    
    print(f'Parameters: λ={lambda_val}, weight=${weight_val}, threshold={threshold_val}')
    print(f'Work rules: n3={params["n3"]}, q_plus=${params["q_plus"]}')
    
    # Solve model
    print('Solving model...')
    start_time = time.time()
    
    try:
        model, status = build_and_solve_model(nurses, scenarios, params)
        solve_time = time.time() - start_time
        
        print(f'Status: {status}')
        print(f'Solve time: {solve_time:.2f}s')
        
        # Extract results
        results = extract_results(model, nurses, scenarios, params)
        
        # Collect metrics
        metrics = collect_metrics(results, model, nurses, scenarios, solve_time, status)
        
        # Add configuration info
        metrics['config_id'] = config_id
        metrics['lambda'] = lambda_val
        metrics['weight'] = weight_val
        metrics['threshold'] = threshold_val
        metrics['demand_level'] = demand_level
        metrics['replication'] = rep
        metrics['seed'] = seed
        # Check if metrics collection succeeded
        if metrics is None:
            # Solver failed - return error metrics
            return {
                'config_id': config_id,
                'lambda': lambda_val,
                'weight': weight_val,
                'threshold': threshold_val,
                'demand_level': demand_level,
                'replication': rep,
                'seed': seed,
                'nurses': nurses_count,
                'days': days_count,
                'scenarios': scenarios_count,
                'status': status,
                'solve_time': solve_time,
                'error': 'Solver failed to find solution',
            }
        
        metrics['nurses'] = nurses_count
        metrics['days'] = days_count
        metrics['scenarios'] = scenarios_count
        
        # Print key results
        print(f'\nResults:')
        if metrics.get("total_cost") is not None:
            print(f'  Total Cost: ${metrics["total_cost"]:,.2f}')
            print(f'  Patient Safety Cost: ${metrics["patient_safety_cost"]:,.2f}')
            print(f'  Max Fatigue: {metrics["max_fatigue"]:.4f}')
            print(f'  Avg Fatigue: {metrics["avg_fatigue"]:.4f}')
            print(f'  Working Nurses: {metrics["working_nurses"]}/{nurses_count}')
            print(f'  High-Fatigue Days: {metrics["high_fatigue_days"]}')
        else:
            print(f'  Status: {metrics.get("status", "UNKNOWN")}')
            print(f'  No solution found (solver timeout or infeasible)')
        
        return metrics
        
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
        
        # Return error metrics
        return {
            'config_id': config_id,
            'lambda': lambda_val,
            'weight': weight_val,
            'threshold': threshold_val,
            'demand_level': demand_level,
            'replication': rep,
            'seed': seed,
            'nurses': nurses_count,
            'days': days_count,
            'scenarios': scenarios_count,
            'status': 'ERROR',
            'solve_time': time.time() - start_time,
            'error': str(e),
        }


# ====================================================================================
# MAIN EXPERIMENT RUNNER
# ====================================================================================

def run_all_experiments(output_file='results/parameter_tuning_results.csv'):
    """Run full factorial experiment"""
    
    print('='*80)
    print('PARAMETER TUNING EXPERIMENTS')
    print('='*80)
    print(f'\nFactorial Design: 3×3×3×3 = 81 configurations')
    print(f'Replications per config: {REPLICATIONS}')
    print(f'Total runs: {81 * REPLICATIONS} (2,430 experiments)')
    print(f'Estimated time: ~2-3 hours with 60s timeout per run')
    print(f'\nFactors:')
    print(f'  Lambda: {LAMBDA_VALUES}')
    print(f'  Weight: {WEIGHT_VALUES}')
    print(f'  Threshold: {THRESHOLD_VALUES}')
    print(f'  Demand: {DEMAND_LEVELS}')
    print(f'\nStarted: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*80)
    
    # Generate all configurations
    configs = list(itertools.product(LAMBDA_VALUES, WEIGHT_VALUES, THRESHOLD_VALUES, DEMAND_LEVELS))
    total_configs = len(configs)
    
    print(f'\nGenerated {total_configs} unique configurations')
    
    # Storage for all results
    all_results = []
    
    # Run experiments
    config_id = 1
    total_runs = total_configs * REPLICATIONS
    current_run = 0
    
    for lambda_val, weight_val, threshold_val, demand_level in configs:
        for rep in range(1, REPLICATIONS + 1):
            current_run += 1
            
            # Generate seed for reproducibility
            seed = config_id * 1000 + rep
            
            print(f'\n[Run {current_run}/{total_runs}] Config {config_id}/{total_configs}')
            
            # Run experiment
            metrics = run_experiment(
                config_id, 
                lambda_val, 
                weight_val, 
                threshold_val, 
                demand_level, 
                rep, 
                seed
            )
            
            all_results.append(metrics)
            
            # Save intermediate results every 10 runs
            if current_run % 10 == 0:
                df_temp = pd.DataFrame(all_results)
                os.makedirs('results', exist_ok=True)
                df_temp.to_csv(output_file.replace('.csv', '_temp.csv'), index=False)
                print(f'\n✓ Intermediate results saved ({current_run} runs)')
        
        config_id += 1
    
    # Save final results
    df_results = pd.DataFrame(all_results)
    os.makedirs('results', exist_ok=True)
    df_results.to_csv(output_file, index=False)
    
    print('\n' + '='*80)
    print('EXPERIMENTS COMPLETE')
    print('='*80)
    print(f'\nCompleted: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Total runs: {len(all_results)}')
    print(f'Successful: {sum(1 for r in all_results if r.get("status") == "Optimal")}')
    print(f'Failed: {sum(1 for r in all_results if r.get("status") != "Optimal")}')
    print(f'\nResults saved to: {output_file}')
    print('='*80)
    
    return df_results


# ====================================================================================
# QUICK TEST MODE
# ====================================================================================

def run_quick_test():
    """Run a small subset for testing (9 configs × 1 rep = 9 runs)"""
    
    print('='*80)
    print('QUICK TEST MODE - 9 Configurations')
    print('='*80)
    
    # Test subset: 3×3×1×1 = 9 configs
    test_lambdas = [0.02, 0.03, 0.04]
    test_weights = [30, 50, 80]
    test_thresholds = [0.70]  # Just one
    test_demands = ['Medium']  # Just one
    
    configs = list(itertools.product(test_lambdas, test_weights, test_thresholds, test_demands))
    all_results = []
    
    for i, (lambda_val, weight_val, threshold_val, demand_level) in enumerate(configs, 1):
        seed = i * 1000
        
        print(f'\n[Test {i}/{len(configs)}]')
        
        metrics = run_experiment(
            i, lambda_val, weight_val, threshold_val, demand_level, 1, seed
        )
        
        all_results.append(metrics)
    
    # Save test results
    df_test = pd.DataFrame(all_results)
    os.makedirs('results', exist_ok=True)
    df_test.to_csv('results/parameter_tuning_test.csv', index=False)
    
    print(f'\n✓ Test results saved to: results/parameter_tuning_test.csv')
    
    return df_test



# ====================================================================================
# COMMAND LINE INTERFACE
# ====================================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parameter Tuning Experiments')
    parser.add_argument('--mode', choices=['full', 'test'], default='test',
                       help='Run mode: full (2,430 runs) or test (9 runs)')
    parser.add_argument('--output', default='results/parameter_tuning_results.csv',
                       help='Output CSV file path')
    parser.add_argument('--yes', action='store_true',
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if args.mode == 'full':
        if not args.yes:
            print(f'\n⚠️  FULL MODE: This will run {81 * REPLICATIONS} experiments (15-30 hours)')
            response = input('Continue? (yes/no): ')
            if response.lower() != 'yes':
                print('Cancelled.')
                sys.exit(0)
        df = run_all_experiments(args.output)
        print(f'\n✅ Full experiment complete!')
    else:
        print('\n▶️  TEST MODE: Running 9 quick configurations')
        df = run_quick_test()
        print(f'\n✅ Test complete!')

