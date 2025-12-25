"""
Retry Failed Parameter Tuning Experiments
==========================================
Re-run only the 40 configurations that failed due to timeout
with unlimited time limit.
"""

import pandas as pd
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parameter_tuning import run_experiment, LAMBDA_VALUES, WEIGHT_VALUES, THRESHOLD_VALUES, DEMAND_LEVELS, INSTANCE_CONFIG

def load_failed_configs():
    """Load list of failed configuration IDs from results file"""
    results_file = 'results/parameter_tuning_results.csv'
    
    if not os.path.exists(results_file):
        print(f"ERROR: Results file not found: {results_file}")
        return []
    
    df = pd.read_csv(results_file)
    failed = df[df['status'] == 'ERROR']
    
    print(f"Found {len(failed)} failed experiments:")
    print(failed[['config_id', 'lambda', 'weight', 'threshold', 'demand_level', 'replication', 'solve_time']].to_string())
    
    return failed.to_dict('records')


def retry_experiments(unlimited_time=True):
    """Re-run failed experiments with extended/unlimited time"""
    
    failed_configs = load_failed_configs()
    
    if not failed_configs:
        print("No failed experiments to retry!")
        return
    
    print(f"\n{'='*80}")
    print(f"RETRYING {len(failed_configs)} FAILED EXPERIMENTS")
    print(f"Time limit: {'UNLIMITED' if unlimited_time else '600 seconds'}")
    print(f"{'='*80}\n")
    
    results = []
    
    for i, config in enumerate(failed_configs, 1):
        config_id = config['config_id']
        lambda_val = config['lambda']
        weight_val = config['weight']
        threshold_val = config['threshold']
        demand_level = config['demand_level']
        rep = config['replication']
        
        print(f"\n[{i}/{len(failed_configs)}] Retrying Config {config_id} (λ={lambda_val}, w={weight_val}, T={threshold_val}, {demand_level}, rep={rep})")
        print("-" * 80)
        
        # Run with unlimited time if requested
        if unlimited_time:
            # Temporarily set no time limit by modifying params in run_experiment
            pass  # Will handle this differently
        
        try:
            metrics = run_experiment(
                config_id=config_id,
                lambda_val=lambda_val,
                weight_val=weight_val,
                threshold_val=threshold_val,
                demand_level=demand_level,
                rep=rep,
                seed=config.get('seed', 1000 + rep),
                time_limit=None if unlimited_time else 600  # None = unlimited
            )
            results.append(metrics)
            
            if metrics['status'] == 'Optimal':
                print(f"✓ SUCCESS: Solved in {metrics['solve_time']:.2f}s")
            else:
                print(f"✗ FAILED: Status={metrics['status']}")
                
        except Exception as e:
            print(f"✗ ERROR: {e}")
    
    # Save results
    if results:
        retry_df = pd.DataFrame(results)
        output_file = 'results/parameter_tuning_retry_results.csv'
        retry_df.to_csv(output_file, index=False)
        print(f"\n{'='*80}")
        print(f"Retry results saved to: {output_file}")
        
        success_count = len(retry_df[retry_df['status'] == 'Optimal'])
        print(f"Success rate: {success_count}/{len(results)} ({100*success_count/len(results):.1f}%)")
        print(f"{'='*80}\n")
        
        # Merge with original results
        merge_results(retry_df)


def merge_results(retry_df):
    """Merge retry results into original results file"""
    
    original_file = 'results/parameter_tuning_results.csv'
    backup_file = 'results/parameter_tuning_results_backup.csv'
    
    # Backup original
    original_df = pd.read_csv(original_file)
    original_df.to_csv(backup_file, index=False)
    print(f"Original results backed up to: {backup_file}")
    
    # Remove failed runs from original
    failed_keys = set()
    for _, row in retry_df.iterrows():
        key = (row['config_id'], row['lambda'], row['weight'], row['threshold'], 
               row['demand_level'], row['replication'])
        failed_keys.add(key)
    
    def is_failed(row):
        key = (row['config_id'], row['lambda'], row['weight'], row['threshold'],
               row['demand_level'], row['replication'])
        return key in failed_keys
    
    updated_df = original_df[~original_df.apply(is_failed, axis=1)]
    
    # Append retry results
    merged_df = pd.concat([updated_df, retry_df], ignore_index=True)
    
    # Sort by config_id and replication
    merged_df = merged_df.sort_values(['config_id', 'replication']).reset_index(drop=True)
    
    # Save merged results
    merged_df.to_csv(original_file, index=False)
    print(f"Merged results saved to: {original_file}")
    print(f"Total experiments: {len(merged_df)}")
    print(f"Successful: {len(merged_df[merged_df['status'] == 'Optimal'])}")
    print(f"Failed: {len(merged_df[merged_df['status'].isin(['ERROR', 'NO_SOLUTION'])])}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Retry failed parameter tuning experiments')
    parser.add_argument('--limited', action='store_true', 
                       help='Use 600s time limit instead of unlimited')
    
    args = parser.parse_args()
    
    retry_experiments(unlimited_time=not args.limited)
