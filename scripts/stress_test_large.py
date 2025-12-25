"""
Stress Test Suite - Extra Large Problem Sizes

Tests model performance at scale to identify limits:
- XL: 30 nurses × 30 days × 20 scenarios
- XXL: 50 nurses × 30 days × 30 scenarios  
- XXXL: 100 nurses × 60 days × 50 scenarios

Run: python tests/stress_test_large.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import time
from datetime import datetime
from model import build_and_solve_model, generate_sample_data, get_default_params


def stress_test_configuration(name, nurses, days, scenarios_count, timeout_sec=300):
    """Run stress test with timeout protection"""
    print(f"\n{'='*80}")
    print(f"STRESS TEST: {name}")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  Nurses: {nurses}, Days: {days}, Scenarios: {scenarios_count}")
    estimated_vars = nurses * days * 4 * 2 + days * 4 * scenarios_count * 2
    estimated_cons = nurses * days + nurses + days * 4 * scenarios_count
    print(f"  Estimated Variables: ~{estimated_vars:,}")
    print(f"  Estimated Constraints: ~{estimated_cons:,}")
    print(f"  Timeout: {timeout_sec}s")
    
    # Generate data
    print("\nGenerating data...", end=" ", flush=True)
    start_gen = time.time()
    nurses_list, scenarios_df = generate_sample_data(nurses, days, scenarios_count)
    gen_time = time.time() - start_gen
    print(f"Done ({gen_time:.2f}s)")
    
    # Setup parameters
    params = get_default_params()
    params['allow_overtime_paradox'] = False
    params['n1'] = max(15, min(days, 20))  # Scale max shifts with days
    
    # Run optimization with simple timeout wrapper
    print("Solving...", flush=True)
    start_solve = time.time()
    
    try:
        prob, status = build_and_solve_model(nurses_list, scenarios_df, params, "SDM")
        solve_time = time.time() - start_solve
        
        metrics = {
            'name': name,
            'nurses': nurses,
            'days': days,
            'scenarios': scenarios_count,
            'data_gen_time': gen_time,
            'solve_time': solve_time,
            'total_time': gen_time + solve_time,
            'status': status,
            'timeout': False
        }
        
        if status in ["Optimal", "Feasible"]:
            metrics['total_variables'] = len([v for v in prob.variables()])
            metrics['total_constraints'] = len(prob.constraints)
            metrics['objective_value'] = prob.objective.value()
            
            # Count shift types
            regular = sum(1 for v in prob.variables() 
                         if v.name.startswith("RegularShift") and v.varValue > 0.5)
            overtime = sum(1 for v in prob.variables() 
                          if v.name.startswith("OvertimeShift") and v.varValue > 0.5)
            emergency = sum(v.varValue for v in prob.variables() 
                           if v.name.startswith("AddShift") and v.varValue is not None)
            
            metrics['regular_shifts'] = regular
            metrics['overtime_shifts'] = overtime
            metrics['emergency_shifts'] = int(emergency)
            
        # Print results
        print(f"\n{'─'*80}")
        print(f"Results:")
        print(f"  Status: {status}")
        print(f"  Data Generation: {gen_time:.2f}s")
        print(f"  Solve Time: {solve_time:.2f}s")
        print(f"  Total Time: {gen_time + solve_time:.2f}s")
        
        if status in ["Optimal", "Feasible"]:
            print(f"  Variables: {metrics['total_variables']:,}")
            print(f"  Constraints: {metrics['total_constraints']:,}")
            print(f"  Objective: ${metrics['objective_value']:,.2f}")
            print(f"  Shifts: R={metrics['regular_shifts']}, "
                  f"OT={metrics['overtime_shifts']}, E={metrics['emergency_shifts']}")
            
        return metrics
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return {
            'name': name,
            'nurses': nurses,
            'days': days,
            'scenarios': scenarios_count,
            'data_gen_time': gen_time,
            'solve_time': None,
            'total_time': None,
            'status': 'Error',
            'timeout': False,
            'error': str(e)
        }


def run_stress_test_suite():
    """Run stress test suite with progressively larger problems"""
    print("\n" + "="*80)
    print("FROST-NS STRESS TEST SUITE - EXTRA LARGE PROBLEMS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print("\nTesting scalability limits with very large problem instances...")
    
    results = []
    
    # ========================================================================
    # XL PROBLEM (30 nurses, 30 days, 20 scenarios)
    # ========================================================================
    results.append(stress_test_configuration(
        "XL-30N-30D-20S",
        nurses=30,
        days=30,
        scenarios_count=20,
        timeout_sec=300
    ))
    
    # ========================================================================
    # XXL PROBLEM (50 nurses, 30 days, 30 scenarios)
    # ========================================================================
    results.append(stress_test_configuration(
        "XXL-50N-30D-30S",
        nurses=50,
        days=30,
        scenarios_count=30,
        timeout_sec=600
    ))
    
    # ========================================================================
    # XXXL PROBLEM (100 nurses, 60 days, 50 scenarios)
    # ========================================================================
    print("\n⚠️  WARNING: Next test is VERY LARGE. May take 10+ minutes...")
    user_input = input("Proceed with XXXL test (100N×60D×50S)? [y/N]: ")
    
    if user_input.lower() == 'y':
        results.append(stress_test_configuration(
            "XXXL-100N-60D-50S",
            nurses=100,
            days=60,
            scenarios_count=50,
            timeout_sec=900
        ))
    else:
        print("Skipping XXXL test.")
        results.append({
            'name': 'XXXL-100N-60D-50S',
            'nurses': 100,
            'days': 60,
            'scenarios': 50,
            'status': 'Skipped',
            'solve_time': None
        })
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("STRESS TEST SUMMARY")
    print("="*80)
    
    df = pd.DataFrame(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'results/stress_test_results_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Print summary table
    print("\nPerformance Summary:")
    print("─"*80)
    print(f"{'Configuration':20s} | {'Status':10s} | {'Solve Time':>10s} | "
          f"{'Variables':>10s} | {'Constraints':>11s}")
    print("─"*80)
    
    for _, row in df.iterrows():
        solve_time_str = f"{row.get('solve_time', 0):.2f}s" if pd.notna(row.get('solve_time')) else "N/A"
        vars_val = row.get('total_variables')
        vars_str = f"{int(vars_val):,}" if pd.notna(vars_val) else "N/A"
        cons_val = row.get('total_constraints')
        cons_str = f"{int(cons_val):,}" if pd.notna(cons_val) else "N/A"
        
        print(f"{row['name']:20s} | {row['status']:10s} | {solve_time_str:>10s} | "
              f"{vars_str:>10s} | {cons_str:>11s}")
    
    # Statistics
    print("\n" + "─"*80)
    print("Statistics:")
    
    completed = df[df['status'].isin(['Optimal', 'Feasible'])]
    if not completed.empty:
        print(f"  Successful solves: {len(completed)}/{len(df)}")
        print(f"  Avg solve time: {completed['solve_time'].mean():.2f}s")
        print(f"  Min solve time: {completed['solve_time'].min():.2f}s")
        print(f"  Max solve time: {completed['solve_time'].max():.2f}s")
        
        max_vars = completed['total_variables'].max()
        max_cons = completed['total_constraints'].max()
        print(f"  Largest problem solved: {int(max_vars):,} vars, {int(max_cons):,} constraints")
    else:
        print("  No successful solves")
    
    return df


if __name__ == "__main__":
    print("\n⚠️  STRESS TEST WARNING ⚠️")
    print("This test suite will attempt very large problem instances.")
    print("Some tests may take 5-15 minutes to complete.")
    print("Press Ctrl+C to abort if needed.\n")
    
    input("Press Enter to continue...")
    
    results_df = run_stress_test_suite()
    
    print("\n✅ Stress test suite complete!")
