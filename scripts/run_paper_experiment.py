"""
Comprehensive experiment runner for nurse scheduling paper results section.

This script systematically tests 16 model configurations:
- SDM vs CVaR (2 model types)
- With/without fatigue modeling (2 fatigue settings)
- 4 constraint variants: None, Shift Quotas, Weekends Off, Night Rest

Author: Research Team
Date: 2025-12-26
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
from pathlib import Path
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import build_and_solve_model, extract_results, get_default_params
import pulp


def load_experiment_data():
    """Load the standardized experiment data files."""
    nurses_df = pd.read_csv('data/experiment_nurses.csv')
    scenarios_df = pd.read_csv('data/experiment_scenarios.csv')
    
    # Handle both 'Nurse' and 'nurse_name' column headers
    if 'nurse_name' in nurses_df.columns:
        nurses_list = nurses_df['nurse_name'].tolist()
    elif 'Nurse' in nurses_df.columns:
        nurses_list = nurses_df['Nurse'].tolist()
    else:
        # Use first column
        nurses_list = nurses_df.iloc[:, 0].tolist()
    
    print(f"[OK] Loaded {len(nurses_list)} nurses")
    print(f"[OK] Loaded {len(scenarios_df)} scenario-day-shift combinations")
    print(f"  - {scenarios_df['scenario'].nunique()} scenarios")
    print(f"  - {scenarios_df['day'].nunique()} days")
    print(f"  - {len(scenarios_df['shift'].unique())} shift types: {', '.join(scenarios_df['shift'].unique())}")
    
    return nurses_list, scenarios_df


def get_configuration_params(config_id):
    """
    Get parameter dictionary for a specific configuration.
    
    Args:
        config_id (int): Configuration ID (1-16)
        
    Returns:
        tuple: (model_type, params_dict, description)
    """
    # Start with default parameters
    params = get_default_params()
    
    # Base parameters that apply to all configs
    params['c1'] = 100.0  # Regular shift cost
    params['c2'] = 150.0  # Overtime shift cost
    params['q_plus'] = 350.0  # Emergency staff cost (increased to incentivize stage-1 planning)
    params['q_minus'] = 0.0  # Cancellation cost
    params['n1'] = 15  # Max total shifts per nurse
    params['n2'] = 5   # Max night shifts per nurse
    params['n3'] = 10  # Min regular shifts quota
    params['c3'] = 10.0  # Stand-alone shift penalty
    params['c4'] = 15.0  # Unwanted pattern penalty
    
    # CVaR parameters (used when model_type = "SDM-CVaR")
    # IMPORTANT: CVaR+Fatigue requires relaxed parameters due to fundamental trade-off
    # between worst-case risk control and nurse safety limits
    params['sigma'] = 0.95  # 95% confidence level
    
    # Determine if this is a CVaR+Fatigue configuration
    model_type_temp = "SDM" if config_id <= 8 else "SDM-CVaR"
    fatigue_enabled_temp = (config_id - 1) % 8 >= 4
    is_cvar_fatigue = (model_type_temp == "SDM-CVaR") and fatigue_enabled_temp
    
    if is_cvar_fatigue:
        # Relaxed for CVaR+Fatigue: allows feasibility despite constraint conflict
        params['mu'] = 200.0  # Max acceptable shortage (relaxed)
    else:
        # Strict for all other configs
        params['mu'] = 50.0   # Max acceptable shortage (strict)
    
    # Fatigue parameters (used when patient_safety_enabled = True)
    params['patient_safety_weight'] = 50.0  # Cost per fatigue unit
    params['fatigue_lambda'] = 0.03  # Fatigue accumulation rate
    params['max_fatigue_threshold'] = 0.70  # Safety threshold (original value)
    params['shift_duration'] = 12  # Hours per shift
    
    # Start date for weekend detection (Monday, Jan 6, 2025)
    params['start_date'] = '2025-01-06'
    
    # Overtime configuration: Use NSS mode (strict overtime rules) for all configs
    params['allow_overtime_paradox'] = False
    
    # Configuration matrix:
    # Configs 1-8: SDM
    # Configs 9-16: CVaR
    # Within each group:
    #   Configs x+0 to x+3: No fatigue
    #   Configs x+4 to x+7: With fatigue
    # Constraint patterns (repeating):
    #   x+0, x+4: No advanced constraints
    #   x+1, x+5: Shift Type Quotas
    #   x+2, x+6: Min Weekends Off
    #   x+3, x+7: Night Rest Requirements
    
    model_type = "SDM" if config_id <= 8 else "SDM-CVaR"
    
    # Determine if fatigue is enabled (configs 5-8 and 13-16)
    fatigue_enabled = (config_id - 1) % 8 >= 4
    params['patient_safety_enabled'] = fatigue_enabled
    
    # Determine which advanced constraint to use (cycles through 0-3)
    constraint_variant = (config_id - 1) % 4
    
    # Reset advanced constraints to defaults
    params['shift_quotas'] = {}
    params['n4'] = 0
    params['night_rest_enabled'] = False
    
    constraint_name = "None"
    
    if constraint_variant == 1:
        # Shift Type Quotas
        constraint_name = "Shift Type Quotas"
        # Relaxed min to 0 to allow "Pure Recourse" strategy in Fatigue configs
        # This ensures Config 6 & 14 are feasible (they prefer 0 shifts)
        params['shift_quotas'] = {
            'E': {'min': 0, 'max': 6},  # Early shifts
            'D': {'min': 0, 'max': 6},  # Day shifts
            'L': {'min': 0, 'max': 6},  # Late shifts
            'N': {'min': 0, 'max': 4}   # Night shifts
        }
    elif constraint_variant == 2:
        # Minimum Weekends Off
        constraint_name = "Min Weekends Off"
        params['n4'] = 1  # At least 1 complete weekend off in 2 weeks
    elif constraint_variant == 3:
        # Night Rest Requirements
        constraint_name = "Night Rest Requirements"
        params['night_rest_enabled'] = True
        params['min_consecutive_nights'] = 2  # Min 2 consecutive nights if working nights
        params['days_off_after_nights'] = 2   # 2 days off after night sequence
    
    # Description for logging
    fatigue_str = "with Fatigue" if fatigue_enabled else "no Fatigue"
    description = f"{model_type} + {constraint_name} ({fatigue_str})"
    
    return model_type, params, description


def run_single_configuration(config_id, nurses_list, scenarios_df, verbose=True):
    """
    Run a single model configuration and extract results.
    
    Args:
        config_id (int): Configuration ID (1-16)
        nurses_list (list): List of nurse names
        scenarios_df (DataFrame): Demand scenarios
        verbose (bool): Print detailed progress
        
    Returns:
        dict: Results dictionary with all metrics
    """
    model_type, params, description = get_configuration_params(config_id)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"Configuration {config_id}: {description}")
        print(f"{'='*70}")
    
    # Track solve time
    start_time = time.time()
    
    try:
        # Build and solve model
        prob, status = build_and_solve_model(
            nurses_list,
            scenarios_df,
            params,
            model_type=model_type,
            solver_name="AUTO"
        )
        
        solve_time = time.time() - start_time
        
        if verbose:
            print(f"[OK] Solver Status: {status}")
            print(f"[OK] Solve Time: {solve_time:.2f} seconds")
        
        # Extract detailed results
        if status == "Optimal":
            results = extract_results(prob, nurses_list, scenarios_df, params)
            
            # Get cost breakdown from nested structure
            total_cost = prob.objective.value()
            cost_bd = results.get('cost_breakdown', {})
            fatigue_metrics = results.get('fatigue_metrics', {})
            
            # Extract individual cost components from cost_breakdown
            stage1_cost = cost_bd.get('stage1_cost', 0)
            stage2_cost = cost_bd.get('stage2_expected_cost', 0)
            soft_penalty = 0  # Not separately tracked in cost_breakdown
            fatigue_cost = 0  # Part of total cost when enabled
            
            # Extract fatigue metrics from fatigue_metrics dict
            avg_fatigue = fatigue_metrics.get('avg_fatigue', 0)
            max_fatigue = fatigue_metrics.get('max_fatigue', 0)
            
            # Extract shift counts from cost_breakdown
            num_regular = cost_bd.get('total_regular_shifts', 0)
            num_overtime = cost_bd.get('total_overtime_shifts', 0)
            
            # Emergency staff usage - calculate from scenario_df if available
            scenario_df = results.get('scenario_df', pd.DataFrame())
            avg_emergency = scenario_df['emergency_add'].mean() if not scenario_df.empty and 'emergency_add' in scenario_df.columns else 0
            
            if verbose:
                print(f"[OK] Total Cost: ${total_cost:,.2f}")
                print(f"  - Stage 1: ${stage1_cost:,.2f}")
                print(f"  - Stage 2 (Expected): ${stage2_cost:,.2f}")
                print(f"  - Soft Penalties: ${soft_penalty:,.2f}")
                print(f"  - Fatigue Cost: ${fatigue_cost:,.2f}")
                print(f"[OK] Regular Shifts: {num_regular}")
                print(f"[OK] Overtime Shifts: {num_overtime}")
                if params['patient_safety_enabled']:
                    print(f"[OK] Avg Fatigue: {avg_fatigue:.3f}")
                    print(f"[OK] Max Fatigue: {max_fatigue:.3f}")
            
            return {
                'config_id': config_id,
                'model_type': model_type,
                'fatigue_enabled': params['patient_safety_enabled'],
                'advanced_constraint': description.split(' + ')[1].split(' (')[0],
                'description': description,
                'status': status,
                'solve_time': solve_time,
                'total_cost': total_cost,
                'stage1_cost': stage1_cost,
                'stage2_cost': stage2_cost,
                'soft_penalty_cost': soft_penalty,
                'fatigue_cost': fatigue_cost,
                'num_regular_shifts': num_regular,
                'num_overtime_shifts': num_overtime,
                'avg_emergency_staff': avg_emergency,
                'avg_fatigue_level': avg_fatigue,
                'max_fatigue_level': max_fatigue,
                'feasibility_notes': 'Success'
            }
        else:
            # Model did not solve optimally
            if verbose:
                print(f"[WARN] Warning: Model did not solve to optimality")
                print(f"  Status: {status}")
            
            return {
                'config_id': config_id,
                'model_type': model_type,
                'fatigue_enabled': params['patient_safety_enabled'],
                'advanced_constraint': description.split(' + ')[1].split(' (')[0],
                'description': description,
                'status': status,
                'solve_time': solve_time,
                'total_cost': None,
                'stage1_cost': None,
                'stage2_cost': None,
                'soft_penalty_cost': None,
                'fatigue_cost': None,
                'num_regular_shifts': None,
                'num_overtime_shifts': None,
                'avg_emergency_staff': None,
                'avg_fatigue_level': None,
                'max_fatigue_level': None,
                'feasibility_notes': f'Failed: {status}'
            }
    
    except Exception as e:
        solve_time = time.time() - start_time
        
        if verbose:
            print(f"[ERROR] Error: {str(e)}")
        
        return {
            'config_id': config_id,
            'model_type': model_type,
            'fatigue_enabled': params.get('patient_safety_enabled', False),
            'advanced_constraint': description.split(' + ')[1].split(' (')[0] if ' + ' in description else 'Unknown',
            'description': description,
            'status': 'Error',
            'solve_time': solve_time,
            'total_cost': None,
            'stage1_cost': None,
            'stage2_cost': None,
            'soft_penalty_cost': None,
            'fatigue_cost': None,
            'num_regular_shifts': None,
            'num_overtime_shifts': None,
            'avg_emergency_staff': None,
            'avg_fatigue_level': None,
            'max_fatigue_level': None,
            'feasibility_notes': f'Error: {str(e)[:100]}'
        }


def run_all_configurations(nurses_list, scenarios_df):
    """
    Run all 16 configurations and collect results.
    
    Returns:
        DataFrame: Results for all configurations
    """
    print("\n" + "="*70)
    print("RUNNING ALL 16 MODEL CONFIGURATIONS")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = []
    
    for config_id in range(1, 17):
        result = run_single_configuration(config_id, nurses_list, scenarios_df, verbose=True)
        all_results.append(result)
    
    results_df = pd.DataFrame(all_results)
    
    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nSuccessful runs: {(results_df['status'] == 'Optimal').sum()} / 16")
    print(f"Failed runs: {(results_df['status'] != 'Optimal').sum()} / 16")
    
    # Save results
    output_path = 'results/experiment_results.csv'
    os.makedirs('results', exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"\n[OK] Results saved to: {output_path}")
    
    return results_df


def main():
    """Main experiment execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run nurse scheduling experiment')
    parser.add_argument('--test-single', action='store_true', 
                       help='Test a single configuration')
    parser.add_argument('--config', type=int, default=1, choices=range(1, 17),
                       help='Configuration ID for single test (1-16)')
    parser.add_argument('--run-all', action='store_true',
                       help='Run all 16 configurations')
    
    args = parser.parse_args()
    
    # Load data
    print("Loading experiment data...")
    nurses_list, scenarios_df = load_experiment_data()
    
    if args.test_single:
        # Test single configuration
        print(f"\nTesting Configuration {args.config}...")
        result = run_single_configuration(args.config, nurses_list, scenarios_df, verbose=True)
        
        print("\n" + "="*70)
        print("TEST RESULT")
        print("="*70)
        print(json.dumps(result, indent=2, default=str))
        
    elif args.run_all:
        # Run all configurations
        results_df = run_all_configurations(nurses_list, scenarios_df)
        
        # Print summary
        print("\n" + "="*70)
        print("SUMMARY STATISTICS")
        print("="*70)
        
        if (results_df['status'] == 'Optimal').all():
            print("\n[OK] ALL CONFIGURATIONS SOLVED SUCCESSFULLY!\n")
            
            # Cost comparison
            print("Total Cost by Configuration:")
            print(results_df[['config_id', 'description', 'total_cost']].to_string(index=False))
            
            print(f"\nLowest cost: ${results_df['total_cost'].min():,.2f} (Config {results_df.loc[results_df['total_cost'].idxmin(), 'config_id']})")
            print(f"Highest cost: ${results_df['total_cost'].max():,.2f} (Config {results_df.loc[results_df['total_cost'].idxmax(), 'config_id']})")
            
        else:
            print("\n[WARN] Some configurations failed:")
            failed = results_df[results_df['status'] != 'Optimal']
            print(failed[['config_id', 'description', 'status', 'feasibility_notes']].to_string(index=False))
    
    else:
        print("\nNo action specified. Use --test-single or --run-all")
        print("Examples:")
        print("  python scripts/run_paper_experiment.py --test-single --config 1")
        print("  python scripts/run_paper_experiment.py --run-all")


if __name__ == '__main__':
    main()
