"""
Comprehensive Model Configuration Testing and Comparison
=========================================================
Tests all major configurations available in the Streamlit app and compares results.

Configurations tested:
1. Model Types: SDM (cost optimization) vs SDM-CVaR (risk-aware)
2. Fatigue: Enabled vs Disabled
3. CVaR Parameters: Different confidence levels and risk thresholds
4. Work Constraints: Different n3 (minimum shifts) values
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from model import build_and_solve_model
from datetime import datetime
import json

def run_configuration_test(config_name, nurses_list, scenarios_df, model_params, model_type):
    """Run a single configuration and return results"""
    print(f"\n{'='*80}")
    print(f"Testing Configuration: {config_name}")
    print(f"{'='*80}")
    
    start_time = datetime.now()
    
    try:
        model, status = build_and_solve_model(
            nurses_list=nurses_list,
            scenarios_df=scenarios_df,
            model_params=model_params,
            model_type=model_type,
            solver_name="AUTO"
        )
        
        solve_time = (datetime.now() - start_time).total_seconds()
        
        if status not in ["Optimal", "Feasible"]:
            print(f"❌ Failed: {status}")
            return {
                'config_name': config_name,
                'status': status,
                'feasible': False,
                'solve_time': solve_time
            }
        
        # Extract results
        results = extract_results(model, nurses_list, scenarios_df, model_params)
        results.update({
            'config_name': config_name,
            'status': status,
            'feasible': True,
            'solve_time': solve_time,
            'model_type': model_type
        })
        
        print(f"✓ Status: {status}")
        print(f"✓ Solve time: {solve_time:.2f}s")
        print(f"✓ Total cost: £{results['total_cost']:,.2f}")
        print(f"✓ Regular shifts: {results['regular_shifts']}")
        print(f"✓ Emergency shifts: {results['total_emergency']:.1f}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'config_name': config_name,
            'status': 'Error',
            'feasible': False,
            'error': str(e),
            'solve_time': (datetime.now() - start_time).total_seconds()
        }


def extract_results(model, nurses_list, scenarios_df, model_params):
    """Extract key metrics from solved model"""
    
    results = {
        'regular_shifts': 0,
        'overtime_shifts': 0,
        'total_emergency': 0,
        'total_cancellations': 0,
        'stage1_cost': 0,
        'stage2_cost': 0,
        'total_cost': 0,
        'nurses_working': 0,
        'max_nurse_shifts': 0,
        'min_nurse_shifts': 0,
        'avg_nurse_shifts': 0
    }
    
    # Extract variables
    nurse_shifts = {nurse: 0 for nurse in nurses_list}
    
    for var in model.variables():
        if var.varValue is None or var.varValue < 0.01:
            continue
        
        name = var.name
        
        if name.startswith('RegularShift_'):
            results['regular_shifts'] += var.varValue
            # Extract nurse name
            remainder = name[len('RegularShift_'):]
            parts = remainder.rsplit('_', 2)
            if len(parts) == 3:
                nurse_name = parts[0]
                if nurse_name in nurse_shifts:
                    nurse_shifts[nurse_name] += var.varValue
                    
        elif name.startswith('OvertimeShift_'):
            results['overtime_shifts'] += var.varValue
            remainder = name[len('OvertimeShift_'):]
            parts = remainder.rsplit('_', 2)
            if len(parts) == 3:
                nurse_name = parts[0]
                if nurse_name in nurse_shifts:
                    nurse_shifts[nurse_name] += var.varValue
                    
        elif name.startswith('AddShift_'):
            results['total_emergency'] += var.varValue
            
        elif name.startswith('CancelShift_'):
            results['total_cancellations'] += var.varValue
    
    # Calculate nurse workload statistics
    working_nurses = [s for s in nurse_shifts.values() if s > 0]
    results['nurses_working'] = len(working_nurses)
    if working_nurses:
        results['max_nurse_shifts'] = max(working_nurses)
        results['min_nurse_shifts'] = min(working_nurses)
        results['avg_nurse_shifts'] = sum(working_nurses) / len(working_nurses)
    
    # Calculate costs
    c1 = model_params.get('c1', 100.0)
    c2 = model_params.get('c2', 150.0)
    q_plus = model_params.get('q_plus', 200.0)
    q_minus = model_params.get('q_minus', 0.0)
    
    results['stage1_cost'] = (results['regular_shifts'] * c1 + 
                              results['overtime_shifts'] * c2)
    results['stage2_cost'] = (results['total_emergency'] * q_plus + 
                              results['total_cancellations'] * q_minus)
    results['total_cost'] = results['stage1_cost'] + results['stage2_cost']
    
    # Get objective value
    if model.objective:
        results['objective_value'] = model.objective.value()
    
    return results


def compare_configurations():
    """Run comprehensive configuration comparison"""
    
    print("=" * 80)
    print("COMPREHENSIVE MODEL CONFIGURATION COMPARISON")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load data
    print("Loading test data...")
    nurses_file = r"c:\Users\rahma\Documents\GitHub\NSS\data\analysis_nurses.csv"
    scenarios_file = r"c:\Users\rahma\Documents\GitHub\NSS\data\analysis_scenarios.csv"
    
    nurses_df = pd.read_csv(nurses_file)
    scenarios_df = pd.read_csv(scenarios_file)
    nurses_list = nurses_df['Nurse'].tolist()
    
    num_scenarios = scenarios_df['scenario'].nunique()
    num_days = scenarios_df['day'].nunique()
    
    print(f"✓ {len(nurses_list)} nurses, {num_days} days, {num_scenarios} scenarios")
    print()
    
    # Define test configurations
    configurations = []
    
    # Base parameters
    base_params = {
        'T': num_days,
        'n1': 10,
        'n2': 7,
        'n3': 1,
        'enforce_max_regular': False,
        'min_rest_shifts': 1,
        'c1': 100.0,
        'c2': 150.0,
        'q_plus': 200.0,
        'q_minus': 0.0,
        'scenario_probs': {i: 1.0/num_scenarios for i in range(1, num_scenarios + 1)}
    }
    
    # Configuration 1: Basic SDM (no CVaR, no fatigue)
    config1 = base_params.copy()
    config1.update({
        'use_cvar': False,
        'use_fatigue': False,
        'lambda_fatigue': 0.03,
        'F_max': 0.70,
        'patient_safety_weight': 0.0
    })
    configurations.append(('1. SDM Basic (No CVaR, No Fatigue)', config1, 'SDM'))
    
    # Configuration 2: SDM with Fatigue
    config2 = base_params.copy()
    config2.update({
        'use_cvar': False,
        'use_fatigue': True,
        'lambda_fatigue': 0.03,
        'F_max': 0.70,
        'patient_safety_weight': 50.0
    })
    configurations.append(('2. SDM with Fatigue (λ=0.03, weight=50)', config2, 'SDM'))
    
    # Configuration 3: SDM with High Fatigue Penalty
    config3 = base_params.copy()
    config3.update({
        'use_cvar': False,
        'use_fatigue': True,
        'lambda_fatigue': 0.03,
        'F_max': 0.70,
        'patient_safety_weight': 100.0
    })
    configurations.append(('3. SDM with High Fatigue Penalty (weight=100)', config3, 'SDM'))
    
    # Configuration 4: SDM-CVaR (risk-aware)
    config4 = base_params.copy()
    config4.update({
        'use_cvar': True,
        'beta': 0.95,
        'W': 50.0,
        'use_fatigue': False,
        'lambda_fatigue': 0.03,
        'F_max': 0.70,
        'patient_safety_weight': 0.0
    })
    configurations.append(('4. SDM-CVaR (β=0.95, W=50)', config4, 'SDM-CVaR'))
    
    # Configuration 5: SDM-CVaR with Conservative Risk
    config5 = base_params.copy()
    config5.update({
        'use_cvar': True,
        'beta': 0.99,
        'W': 30.0,
        'use_fatigue': False,
        'lambda_fatigue': 0.03,
        'F_max': 0.70,
        'patient_safety_weight': 0.0
    })
    configurations.append(('5. SDM-CVaR Conservative (β=0.99, W=30)', config5, 'SDM-CVaR'))
    
    # Configuration 6: SDM-CVaR + Fatigue (Full Model)
    config6 = base_params.copy()
    config6.update({
        'use_cvar': True,
        'beta': 0.95,
        'W': 50.0,
        'use_fatigue': True,
        'lambda_fatigue': 0.03,
        'F_max': 0.70,
        'patient_safety_weight': 50.0
    })
    configurations.append(('6. Full Model (CVaR + Fatigue)', config6, 'SDM-CVaR'))
    
    # Configuration 7: Tight Constraints (higher n3)
    config7 = base_params.copy()
    config7['n3'] = 3  # Higher minimum shifts
    config7.update({
        'use_cvar': False,
        'use_fatigue': False,
        'patient_safety_weight': 0.0
    })
    configurations.append(('7. Tight Constraints (n3=3)', config7, 'SDM'))
    
    # Configuration 8: Relaxed Constraints (lower costs)
    config8 = base_params.copy()
    config8.update({
        'c1': 80.0,   # Lower regular cost
        'c2': 120.0,  # Lower overtime cost
        'q_plus': 180.0,  # Lower emergency cost
        'use_cvar': False,
        'use_fatigue': False,
        'patient_safety_weight': 0.0
    })
    configurations.append(('8. Lower Costs (C1=80, C2=120, Q+=180)', config8, 'SDM'))
    
    # Run all configurations
    results_list = []
    
    for config_name, params, model_type in configurations:
        result = run_configuration_test(config_name, nurses_list, scenarios_df, params, model_type)
        results_list.append(result)
    
    # Create comparison report
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    # Create DataFrame for comparison
    comparison_df = pd.DataFrame(results_list)
    
    # Only include feasible solutions
    feasible_df = comparison_df[comparison_df['feasible'] == True].copy()
    
    if len(feasible_df) == 0:
        print("\n❌ No feasible solutions found!")
        return
    
    # Rank by total cost
    feasible_df = feasible_df.sort_values('total_cost')
    
    print("\n📊 RESULTS RANKED BY TOTAL COST:")
    print("-" * 80)
    
    for idx, row in feasible_df.iterrows():
        print(f"\n{row['config_name']}")
        print(f"  Total Cost: £{row['total_cost']:,.2f}")
        print(f"  Stage 1: £{row['stage1_cost']:,.2f} | Stage 2: £{row['stage2_cost']:,.2f}")
        print(f"  Regular Shifts: {row['regular_shifts']:.0f} | Overtime: {row['overtime_shifts']:.0f}")
        print(f"  Emergency: {row['total_emergency']:.1f} shifts")
        print(f"  Nurses Working: {row['nurses_working']}/{len(nurses_list)}")
        print(f"  Workload: Min={row['min_nurse_shifts']:.0f}, Avg={row['avg_nurse_shifts']:.1f}, Max={row['max_nurse_shifts']:.0f}")
        print(f"  Solve Time: {row['solve_time']:.2f}s")
    
    # Best configuration analysis
    print("\n" + "=" * 80)
    print("🏆 BEST CONFIGURATION ANALYSIS")
    print("=" * 80)
    
    best = feasible_df.iloc[0]
    print(f"\nLowest Cost: {best['config_name']}")
    print(f"  Total Cost: £{best['total_cost']:,.2f}")
    
    # Most balanced workload
    feasible_df['workload_std'] = feasible_df['max_nurse_shifts'] - feasible_df['min_nurse_shifts']
    most_balanced = feasible_df.sort_values('workload_std').iloc[0]
    print(f"\nMost Balanced Workload: {most_balanced['config_name']}")
    print(f"  Workload Range: {most_balanced['min_nurse_shifts']:.0f}-{most_balanced['max_nurse_shifts']:.0f} shifts")
    
    # Least emergency staff
    least_emergency = feasible_df.sort_values('total_emergency').iloc[0]
    print(f"\nLeast Emergency Staff: {least_emergency['config_name']}")
    print(f"  Emergency: {least_emergency['total_emergency']:.1f} shifts")
    
    # Fastest solve
    fastest = feasible_df.sort_values('solve_time').iloc[0]
    print(f"\nFastest Solution: {fastest['config_name']}")
    print(f"  Solve Time: {fastest['solve_time']:.2f}s")
    
    # Save detailed results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    comparison_df.to_csv('configuration_comparison.csv', index=False)
    print("✓ Saved: configuration_comparison.csv")
    
    # Create detailed report
    with open('configuration_report.txt', 'w', encoding='utf-8') as f:
        f.write("COMPREHENSIVE MODEL CONFIGURATION COMPARISON REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Data: {len(nurses_list)} nurses, {num_days} days, {num_scenarios} scenarios\n")
        f.write("\n")
        
        for idx, row in feasible_df.iterrows():
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"{row['config_name']}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Status: {row['status']}\n")
            f.write(f"Solve Time: {row['solve_time']:.2f}s\n")
            f.write(f"\nCosts:\n")
            f.write(f"  Total Cost: £{row['total_cost']:,.2f}\n")
            f.write(f"  Stage 1 Cost: £{row['stage1_cost']:,.2f}\n")
            f.write(f"  Stage 2 Cost: £{row['stage2_cost']:,.2f}\n")
            f.write(f"\nShift Allocation:\n")
            f.write(f"  Regular Shifts: {row['regular_shifts']:.0f}\n")
            f.write(f"  Overtime Shifts: {row['overtime_shifts']:.0f}\n")
            f.write(f"  Emergency Shifts: {row['total_emergency']:.1f}\n")
            f.write(f"  Cancellations: {row['total_cancellations']:.1f}\n")
            f.write(f"\nWorkforce Utilization:\n")
            f.write(f"  Nurses Working: {row['nurses_working']}/{len(nurses_list)}\n")
            f.write(f"  Min Shifts per Nurse: {row['min_nurse_shifts']:.0f}\n")
            f.write(f"  Avg Shifts per Nurse: {row['avg_nurse_shifts']:.1f}\n")
            f.write(f"  Max Shifts per Nurse: {row['max_nurse_shifts']:.0f}\n")
            f.write(f"  Workload Range: {row['max_nurse_shifts'] - row['min_nurse_shifts']:.0f}\n")
    
    print("✓ Saved: configuration_report.txt")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nTested {len(configurations)} configurations")
    print(f"Feasible solutions: {len(feasible_df)}")
    print(f"\nRecommendation: {best['config_name']}")
    print(f"  - Lowest total cost: £{best['total_cost']:,.2f}")
    print(f"  - {best['regular_shifts']:.0f} regular shifts, {best['total_emergency']:.1f} emergency shifts")
    print(f"  - Solve time: {best['solve_time']:.2f}s")


if __name__ == "__main__":
    compare_configurations()
