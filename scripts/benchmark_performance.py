"""
Performance Benchmark Suite for FROST-NS Model

Systematically tests performance across problem sizes and configurations.
Collects metrics: solve time, cost, variables, constraints, solution quality.

Run: python tests/benchmark_performance.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import time
from datetime import datetime
from model import build_and_solve_model, generate_sample_data, get_default_params


def benchmark_configuration(name, nurses, days, scenarios_count, config_params, model_type="SDM"):
    """Run benchmark for a specific configuration"""
    print(f"\n{'='*80}")
    print(f"BENCHMARK: {name}")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  Nurses: {nurses}, Days: {days}, Scenarios: {scenarios_count}")
    print(f"  Model Type: {model_type}")
    print(f"  Overtime Mode: {'Paper' if config_params.get('allow_overtime_paradox', True) else 'NSS'}")
    print(f"  Fatigue: {'Enabled' if config_params.get('patient_safety_enabled', False) else 'Disabled'}")
    
    # Generate data
    nurses_list, scenarios_df = generate_sample_data(nurses, days, scenarios_count)
    
    # Merge with default params
    params = get_default_params()
    params.update(config_params)
    
    # Run optimization
    start_time = time.time()
    prob, status = build_and_solve_model(nurses_list, scenarios_df, params, model_type)
    solve_time = time.time() - start_time
    
    # Collect metrics
    metrics = {
        'name': name,
        'nurses': nurses,
        'days': days,
        'scenarios': scenarios_count,
        'model_type': model_type,
        'overtime_mode': 'Paper' if config_params.get('allow_overtime_paradox', True) else 'NSS',
        'fatigue_enabled': config_params.get('patient_safety_enabled', False),
        'solve_time_sec': solve_time,
        'status': status,
        'optimal': status == "Optimal",
    }
    
    if status in ["Optimal", "Feasible"]:
        # Count variables
        metrics['total_variables'] = len([v for v in prob.variables()])
        metrics['binary_variables'] = len([v for v in prob.variables() if v.cat == 'Binary'])
        
        # Count constraints
        metrics['total_constraints'] = len(prob.constraints)
        
        # Get objective value
        metrics['objective_value'] = prob.objective.value()
        
        # Count shift types
        regular_shifts = sum(1 for v in prob.variables() 
                           if v.name.startswith("RegularShift") and v.varValue > 0.5)
        overtime_shifts = sum(1 for v in prob.variables() 
                            if v.name.startswith("OvertimeShift") and v.varValue > 0.5)
        emergency_shifts = sum(v.varValue for v in prob.variables() 
                              if v.name.startswith("AddShift") and v.varValue is not None)
        
        metrics['regular_shifts'] = regular_shifts
        metrics['overtime_shifts'] = overtime_shifts
        metrics['emergency_shifts'] = int(emergency_shifts)
        metrics['total_shifts'] = regular_shifts + overtime_shifts + int(emergency_shifts)
        
        # Calculate fatigue if enabled
        if config_params.get('patient_safety_enabled', False):
            fatigue_values = [v.varValue for v in prob.variables() 
                            if v.name.startswith("Fatigue_") and v.varValue is not None]
            if fatigue_values:
                metrics['max_fatigue'] = max(fatigue_values)
                metrics['avg_fatigue'] = sum(fatigue_values) / len(fatigue_values)
        
        # CVaR metrics
        if model_type == "SDM-CVaR":
            for v in prob.variables():
                if v.name == "VaR_xi" and v.varValue is not None:
                    metrics['var_value'] = v.varValue
                    
            z_values = [v.varValue for v in prob.variables() 
                       if v.name.startswith("ExcessLoss_z") and v.varValue is not None]
            if z_values:
                expected_excess = sum(z_values) / scenarios_count
                sigma = config_params.get('sigma', 0.95)
                cvar = metrics.get('var_value', 0) + (1.0 / (1.0 - sigma)) * expected_excess
                metrics['cvar_value'] = cvar
    
    # Print summary
    print(f"\nResults:")
    print(f"  Status: {status}")
    print(f"  Solve Time: {solve_time:.2f}s")
    if status in ["Optimal", "Feasible"]:
        print(f"  Objective: ${metrics['objective_value']:.2f}")
        print(f"  Variables: {metrics['total_variables']} ({metrics['binary_variables']} binary)")
        print(f"  Constraints: {metrics['total_constraints']}")
        print(f"  Shifts: Regular={metrics['regular_shifts']}, "
              f"Overtime={metrics['overtime_shifts']}, Emergency={metrics['emergency_shifts']}")
        if 'max_fatigue' in metrics:
            print(f"  Fatigue: Max={metrics['max_fatigue']:.3f}, Avg={metrics['avg_fatigue']:.3f}")
        if 'cvar_value' in metrics:
            print(f"  CVaR: {metrics['cvar_value']:.2f}")
    
    return metrics


def run_benchmark_suite():
    """Run comprehensive benchmark suite"""
    print("\n" + "="*80)
    print("FROST-NS PERFORMANCE BENCHMARK SUITE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    
    # ========================================================================
    # SMALL PROBLEMS
    # ========================================================================
    print("\n" + "─"*80)
    print("SMALL PROBLEM BENCHMARKS (5 nurses, 7 days)")
    print("─"*80)
    
    # Small - SDM - Paper Mode
    results.append(benchmark_configuration(
        "Small-SDM-Paper",
        nurses=5, days=7, scenarios_count=3,
        config_params={'allow_overtime_paradox': True},
        model_type="SDM"
    ))
    
    # Small - SDM - NSS Mode
    results.append(benchmark_configuration(
        "Small-SDM-NSS",
        nurses=5, days=7, scenarios_count=3,
        config_params={'allow_overtime_paradox': False},
        model_type="SDM"
    ))
    
    # Small - SDM-CVaR - NSS Mode
    results.append(benchmark_configuration(
        "Small-CVaR-NSS",
        nurses=5, days=7, scenarios_count=3,
        config_params={
            'allow_overtime_paradox': False,
            'sigma': 0.95,
            'mu': 5.0
        },
        model_type="SDM-CVaR"
    ))
    
    # Small - Fatigue Enabled
    results.append(benchmark_configuration(
        "Small-Fatigue",
        nurses=5, days=7, scenarios_count=3,
        config_params={
            'allow_overtime_paradox': False,
            'patient_safety_enabled': True,
            'max_fatigue_threshold': 0.70,
            'fatigue_lambda': 0.03
        },
        model_type="SDM"
    ))
    
    # ========================================================================
    # MEDIUM PROBLEMS
    # ========================================================================
    print("\n" + "─"*80)
    print("MEDIUM PROBLEM BENCHMARKS (10 nurses, 14 days)")
    print("─"*80)
    
    # Medium - SDM - NSS Mode
    results.append(benchmark_configuration(
        "Medium-SDM-NSS",
        nurses=10, days=14, scenarios_count=5,
        config_params={'allow_overtime_paradox': False},
        model_type="SDM"
    ))
    
    # Medium - SDM-CVaR
    results.append(benchmark_configuration(
        "Medium-CVaR-NSS",
        nurses=10, days=14, scenarios_count=5,
        config_params={
            'allow_overtime_paradox': False,
            'sigma': 0.95,
            'mu': 10.0
        },
        model_type="SDM-CVaR"
    ))
    
    # Medium - Fatigue Enabled
    results.append(benchmark_configuration(
        "Medium-Fatigue",
        nurses=10, days=14, scenarios_count=5,
        config_params={
            'allow_overtime_paradox': False,
            'patient_safety_enabled': True,
            'max_fatigue_threshold': 0.70,
            'fatigue_lambda': 0.03
        },
        model_type="SDM"
    ))
    
    # ========================================================================
    # LARGE PROBLEMS
    # ========================================================================
    print("\n" + "─"*80)
    print("LARGE PROBLEM BENCHMARKS (20 nurses, 28 days)")
    print("─"*80)
    
    # Large - SDM - NSS Mode
    results.append(benchmark_configuration(
        "Large-SDM-NSS",
        nurses=20, days=28, scenarios_count=10,
        config_params={'allow_overtime_paradox': False, 'n1': 20},
        model_type="SDM"
    ))
    
    # Large - CVaR
    results.append(benchmark_configuration(
        "Large-CVaR-NSS",
        nurses=20, days=28, scenarios_count=10,
        config_params={
            'allow_overtime_paradox': False,
            'n1': 20,
            'sigma': 0.95,
            'mu': 20.0
        },
        model_type="SDM-CVaR"
    ))
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)
    
    df = pd.DataFrame(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'results/benchmark_results_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Print summary table
    print("\nPerformance Summary:")
    print("─"*80)
    
    summary_cols = ['name', 'solve_time_sec', 'status', 'objective_value', 
                   'total_variables', 'total_constraints']
    
    for _, row in df[summary_cols].iterrows():
        print(f"{row['name']:20s} | "
              f"{row['solve_time_sec']:6.2f}s | "
              f"{row['status']:10s} | "
              f"${row.get('objective_value', 0):10.0f} | "
              f"{row.get('total_variables', 0):5.0f} vars | "
              f"{row.get('total_constraints', 0):5.0f} cons")
    
    # Statistics
    print("\n" + "─"*80)
    print("Statistics:")
    optimal_count = df['optimal'].sum()
    total_count = len(df)
    avg_solve_time = df[df['optimal']]['solve_time_sec'].mean()
    
    print(f"  Optimal Solutions: {optimal_count}/{total_count}")
    print(f"  Avg Solve Time (optimal): {avg_solve_time:.2f}s")
    print(f"  Min Solve Time: {df['solve_time_sec'].min():.2f}s")
    print(f"  Max Solve Time: {df['solve_time_sec'].max():.2f}s")
    
    return df


if __name__ == "__main__":
    results_df = run_benchmark_suite()
    
    print("\n✅ Benchmark suite complete!")
