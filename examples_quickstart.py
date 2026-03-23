#!/usr/bin/env python3
"""
QUICKSTART: Validation & Experiment Pipeline
==============================================

Practical examples showing the recommended workflow for publication-quality
scheduling experiments.

Usage:
    1. Single experiment with validation:
       python examples_quickstart.py --mode single
    
    2. Validation suite (check data):
       python examples_quickstart.py --mode validate
    
    3. Reproducible sweep (multiple configs):
       python examples_quickstart.py --mode sweep
    
    4. Generate documentation:
       python examples_quickstart.py --mode docs
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import argparse

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import model_2
from validation_framework import (
    PreRunValidator, ResultValidator, run_complete_validation, sanitize_parameters
)
from experiments.experiment_pipeline import (
    ExperimentRunner, DATASET_REGISTRY, PARAMETER_PRESETS
)


# ==============================================================================
# EXAMPLE 1: SIMPLE VALIDATION CHECK (Pre-solve verification)
# ==============================================================================

def example_validate_data():
    """
    Purpose: Quickly check if data + parameters are ready before solving
    Use case: Before running a long solve, make sure inputs are valid
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 1: Validation Check")
    print("="*80)
    
    # Load data
    nurses_df = pd.read_csv('data/sample_nurses.csv')
    scenarios_df = pd.read_csv('data/sample_scenarios.csv')
    nurses_list = nurses_df['nurse_id'].astype(str).tolist()
    
    # Define parameters
    params = {
        'c1': 100.0,
        'c2': 150.0,
        'q_plus': 200.0,
        'q_minus': 0.0,
        'c3': 10.0,
        'c4': 15.0,
        'n1': 12,      # ← Too low! Planning period is 14 days
        'n2': 5,
        'n3': 10,      # ← Will cause issues if n1 is too low
        'sigma': 0.95,
        'mu': 50.0,
    }
    
    # Run validation
    print("\n🔍 Validating data + parameters...")
    validation = run_complete_validation(
        nurses_list, scenarios_df, params, auto_fix=True
    )
    
    print("\n📊 Validation Results:")
    print(f"   Ready to run: {validation['ready_to_run']}")
    print(f"   Issues found: {len(validation['pre_validation']['errors'])} errors, "
          f"{len(validation['pre_validation']['warnings'])} warnings")
    
    # Show auto-fixes if applied
    if validation['sanitization'][1]:
        print("\n   Applied fixes:")
        for fix in validation['sanitization'][1]:
            print(f"      • {fix}")
    
    print(f"\n   Final parameters:")
    for key, val in validation['final_params'].items():
        if not isinstance(val, dict):
            print(f"      {key}: {val}")


# ==============================================================================
# EXAMPLE 2: SINGLE EXPERIMENT (Full workflow)
# ==============================================================================

def example_single_experiment():
    """
    Purpose: Run one complete organized experiment
    Use case: Publishing a single well-organized result
    
    Demonstrates:
    - Data loading
    - Parameter validation
    - Model solving with progress
    - Result archiving
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Single Experiment (Full Workflow)")
    print("="*80)
    
    # Create runner
    runner = ExperimentRunner(output_dir='experiments/results')
    
    # Run experiment with validation
    result = runner.run_experiment(
        dataset_key='sample',              # Use sample data
        preset_key='baseline',             # Cost minimization
        experiment_id='baseline_small',
        overrides={'n1': 12, 'n2': 3},     # Optional parameter tweaks
        solver='AUTO'
    )
    
    # Check if successful
    if result['success']:
        print("\n✅ Experiment succeeded!")
        print(f"\n📈 Results Summary:")
        print(f"   Solver: {result['status']}")
        print(f"   Solve time: {result['solve_time']:.2f}s")
        
        if 'results' in result and result['results']:
            cost_breakdown = result['results'].get('cost_breakdown', {})
            print(f"   Total cost: ${cost_breakdown.get('total_cost', 0):.2f}")
            print(f"   Stage 1 (scheduling): ${cost_breakdown.get('stage1_cost', 0):.2f}")
            print(f"   Stage 2 (adjustments): ${cost_breakdown.get('stage2_cost', 0):.2f}")
        
        print(f"\n💾 Results archived to: {result['archive']['folder']}")
    else:
        print(f"\n❌ Experiment failed: {result.get('error', 'Unknown error')}")


# ==============================================================================
# EXAMPLE 3: REPRODUCIBLE SWEEP (Multiple configurations)
# ==============================================================================

def example_parameter_sweep():
    """
    Purpose: Compare multiple parameter configurations systematically
    Use case: Sensitivity analysis, paper tables
    
    Shows:
    - Running multiple experiments
    - Collecting comparable results
    - Building metrics tables
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 3: Parameter Sweep (Reproducible)")
    print("="*80)
    
    runner = ExperimentRunner()
    
    # Define sweep
    configurations = [
        {
            'id': 'config_baseline',
            'dataset': 'sample',
            'preset': 'baseline',
            'desc': 'Cost minimization'
        },
        {
            'id': 'config_conservative',
            'dataset': 'sample',
            'preset': 'conservative',
            'desc': 'Risk-averse (CVaR)'
        },
        {
            'id': 'config_fatigue',
            'dataset': 'sample',
            'preset': 'fatigue_aware',
            'desc': 'With patient safety'
        },
    ]
    
    print(f"\n🚀 Running {len(configurations)} configurations...")
    results_table = []
    
    for config in configurations:
        print(f"\n   [{config['id']}] {config['desc']}")
        
        result = runner.run_experiment(
            dataset_key=config['dataset'],
            preset_key=config['preset'],
            experiment_id=config['id'],
        )
        
        if result['success']:
            row = {
                'Configuration': config['id'],
                'Status': result['status'],
                'Time (s)': f"{result['solve_time']:.2f}",
                'Cost': f"${result['results'].get('cost_breakdown', {}).get('total_cost', 0):.0f}",
            }
            results_table.append(row)
            print(f"      ✓ Done")
        else:
            print(f"      ✗ Failed: {result.get('error')}")
    
    # Print results table
    if results_table:
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)
        results_df = pd.DataFrame(results_table)
        print(results_df.to_string(index=False))
        
        # Save table
        table_file = 'experiments/results/sweep_comparison.csv'
        results_df.to_csv(table_file, index=False)
        print(f"\nResults table saved to: {table_file}")


# ==============================================================================
# EXAMPLE 4: DATA VALIDATION CHECKLIST
# ==============================================================================

def example_data_validation_checklist():
    """
    Purpose: Validate all datasets before doing any analysis
    Use case: Project startup, data integrity check
    
    Runs pre-validation on all available datasets
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 4: Data Quality Checklist")
    print("="*80)
    
    results = []
    
    for dataset_key, dataset_config in DATASET_REGISTRY.items():
        print(f"\n📊 Checking: {dataset_key}")
        
        try:
            # Load data
            nurses_df = pd.read_csv(dataset_config['nurses_file'])
            scenarios_df = pd.read_csv(dataset_config['scenarios_file'])
            
            nurse_id_col = 'nurse_id' if 'nurse_id' in nurses_df.columns else nurses_df.columns[0]
            nurses_list = nurses_df[nurse_id_col].astype(str).tolist()
            
            # Use default parameters
            base_params = model_2.get_default_params()
            
            # Validate
            validator = PreRunValidator(strict_mode=False)
            validation = validator.validate_all(
                nurses_list, scenarios_df, base_params, verbose=False
            )
            
            # Collect result
            status = '✅ OK' if validation['is_valid'] else '⚠️  Issues'
            results.append({
                'Dataset': dataset_key,
                'Status': status,
                'Nurses': len(nurses_list),
                'Days': len(scenarios_df['day'].unique()),
                'Scenarios': len(scenarios_df['scenario'].unique()),
                'Issues': len(validation['errors']) + len(validation['warnings']),
            })
            
            print(f"   {status}: {len(nurses_list)} nurses, "
                  f"{scenarios_df['day'].max()}-day horizon, "
                  f"{scenarios_df['scenario'].nunique()} scenarios")
            
            if validation['errors']:
                print(f"   Errors: {len(validation['errors'])}")
                for e in validation['errors'][:2]:
                    print(f"      - {e[:70]}...")
            
        except Exception as e:
            results.append({
                'Dataset': dataset_key,
                'Status': '❌ ERROR',
                'Issues': str(e)[:50],
            })
            print(f"   ❌ ERROR: {str(e)}")
    
    # Summary table
    print("\n" + "="*80)
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    print("="*80)


# ==============================================================================
# EXAMPLE 5: BEST PRACTICES WORKFLOW (Publication-ready)
# ==============================================================================

def example_publication_workflow():
    """
    Purpose: Demonstrate recommended workflow for paper-quality results
    Use case: Before submitting paper, ensuring reproducibility
    
    Checklist:
    1. Validate data
    2. Run reproducible experiments
    3. Archive with metadata
    4. Generate reproducibility statement
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 5: Publication-Ready Workflow")
    print("="*80)
    
    # Step 1: Validate data
    print("\n[1/4] Validating core datasets...")
    core_datasets = ['sample', 'test_medium', 'nss_benchmark']
    all_valid = True
    
    for dataset_key in core_datasets:
        datasets_config = DATASET_REGISTRY[dataset_key]
        try:
            nurses_df = pd.read_csv(datasets_config['nurses_file'])
            scenarios_df = pd.read_csv(datasets_config['scenarios_file'])
            print(f"   ✓ {dataset_key}: {len(nurses_df)} nurses, "
                  f"{scenarios_df['day'].max()}-day horizon")
        except Exception as e:
            print(f"   ✗ {dataset_key}: {str(e)}")
            all_valid = False
    
    if not all_valid:
        print("\n❌ Fix data issues above before proceeding")
        return
    
    # Step 2: Run core experiments
    print("\n[2/4] Running core experiments...")
    runner = ExperimentRunner()
    
    core_experiments = [
        ('benchmark_baseline', 'nss_benchmark', 'baseline'),
        ('realistic_conservative', 'test_medium', 'conservative'),
    ]
    
    for exp_id, dataset, preset in core_experiments:
        print(f"   Running: {exp_id}...")
        result = runner.run_experiment(
            dataset_key=dataset,
            preset_key=preset,
            experiment_id=exp_id,
        )
        print(f"      {'✓' if result['success'] else '✗'} Status: {result.get('status', 'Failed')}")
    
    # Step 3: Generate reproducibility metadata
    print("\n[3/4] Generating reproducibility metadata...")
    
    reproducibility_metadata = {
        'generated': datetime.now().isoformat(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
        'model_file': 'model_2.py',
        'model_version': 'v2.0',
        'validation_framework': 'validation_framework.py',
        'source_code': 'https://github.com/[username]/NSS',
        'datasets_used': core_datasets,
        'experiments_run': [e[0] for e in core_experiments],
    }
    
    meta_file = Path('experiments/results/reproducibility_metadata.json')
    with open(meta_file, 'w') as f:
        json.dump(reproducibility_metadata, f, indent=2)
    
    print(f"   ✓ Metadata saved to: {meta_file}")
    
    # Step 4: Summary
    print("\n[4/4] Publication readiness checklist:")
    checklist = [
        ('Data validation', True),
        ('Core experiments run', True),
        ('Results archived with metadata', True),
        ('Reproducibility statement generated', True),
        ('Ready for paper submission', True),
    ]
    
    for item, status in checklist:
        mark = '✓' if status else '✗'
        print(f"   {mark} {item}")
    
    print("\n✅ Workflow complete! You're ready for paper submission.")
    print(f"\nNext steps:")
    print(f"  1. Review results in: experiments/results/")
    print(f"  2. Include reproducibility metadata in supplementary materials")
    print(f"  3. Reference: {meta_file}")


# ==============================================================================
# EXAMPLE 6: TROUBLESHOOTING INFEASIBLE PROBLEMS
# ==============================================================================

def example_troubleshoot_infeasibility():
    """
    Purpose: Diagnose and fix infeasibility issues
    Use case: When validation says "problem might be infeasible"
    
    Shows:
    - How validation detects infeasibility
    - How to interpret messages
    - How to fix problems systematically
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 6: Troubleshooting Infeasibility")
    print("="*80)
    
    # Simulate problematic parameters
    nurses_df = pd.read_csv('data/sample_nurses.csv')
    scenarios_df = pd.read_csv('data/sample_scenarios.csv')
    nurses_list = nurses_df['nurse_id'].astype(str).tolist()
    
    # PROBLEM 1: n1 too low relative to planning horizon
    print("\n🔴 PROBLEM 1: Insufficient capacity")
    bad_params_1 = {
        'c1': 100.0, 'c2': 150.0, 'q_plus': 200.0,
        'n1': 5,      # ← Only 5 shifts in 14-day horizon (unrealistic)
        'n2': 3, 'n3': 4,
    }
    
    print("   Testing with n1=5 (too low)...")
    validator = PreRunValidator()
    result = validator.validate_all(nurses_list, scenarios_df, bad_params_1, verbose=False)
    
    if not result['is_valid']:
        print("\n   ❌ ERRORS DETECTED:")
        for error in result['errors'][:3]:
            print(f"      {error}")
    
    # PROBLEM 2: Cost hierarchy violation
    print("\n🔴 PROBLEM 2: Cost hierarchy violation")
    bad_params_2 = {
        'c1': 200.0,   # ← Too high!
        'c2': 150.0,   # ← Less than c1 (backwards!)
        'q_plus': 100.0, # ← Even less (invalid!)
        'n1': 12, 'n2': 5, 'n3': 8,
    }
    
    print("   Testing with c1=200, c2=150, q+=100 (backwards)...")
    result = validator.validate_all(nurses_list, scenarios_df, bad_params_2, verbose=False)
    
    if not result['is_valid']:
        print("\n   ❌ ERRORS DETECTED:")
        for error in result['errors'][:3]:
            print(f"      {error}")
    
    # Show AUTO-FIX
    print("\n🔧 AUTO-FIX Applied:")
    fixed_params, changes = sanitize_parameters(bad_params_2, nurses_list, scenarios_df)
    for change in changes:
        print(f"   ✓ {change}")
    
    # Re-check
    print("\n   Re-validating with fixes...")
    result = validator.validate_all(nurses_list, scenarios_df, fixed_params, verbose=False)
    print(f"   Status: {'✅ VALID' if result['is_valid'] else '❌ Still invalid'}")


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Quickstart examples for validation & experiment framework'
    )
    
    parser.add_argument(
        '--mode',
        choices=['validate', 'single', 'sweep', 'checklist', 'workflow', 'troubleshoot', 'all'],
        default='single',
        help='Which example to run'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    print("\n" + "█"*80)
    print("QUICKSTART: NSS Validation & Experiment Framework")
    print("█"*80)
    
    try:
        if args.mode in ['validate', 'all']:
            example_validate_data()
        
        if args.mode in ['single', 'all']:
            example_single_experiment()
        
        if args.mode in ['sweep', 'all']:
            example_parameter_sweep()
        
        if args.mode in ['checklist', 'all']:
            example_data_validation_checklist()
        
        if args.mode in ['workflow', 'all']:
            example_publication_workflow()
        
        if args.mode in ['troubleshoot', 'all']:
            example_troubleshoot_infeasibility()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "█"*80)
    print("Quickstart complete!")
    print("█"*80 + "\n")


if __name__ == '__main__':
    main()
