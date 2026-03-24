"""
Benchmark Data Converter for NSS
================================
Converts nurse rostering benchmark instances from schedulingbenchmarks.org
to the NSS format (nurses.csv, scenarios.csv).

Data Source: https://www.schedulingbenchmarks.org/nrp/
Instances: 24 benchmark problems with varying complexity

Usage:
    python convert_benchmark_to_nss.py --instance 8
    python convert_benchmark_to_nss.py --all
"""

import pandas as pd
import numpy as np
import os
import argparse
from pathlib import Path


def parse_benchmark_file(filepath: str) -> dict:
    """
    Parse a benchmark instance file from schedulingbenchmarks.org.
    
    Returns dict with:
        - horizon: int (planning period in days)
        - shifts: list of shift dicts
        - staff: list of employee dicts
        - days_off: dict of employee -> day indexes
        - cover: list of (day, shift, requirement, under_weight, over_weight)
    """
    data = {
        'horizon': 0,
        'shifts': [],
        'staff': [],
        'days_off': {},
        'shift_on_requests': [],
        'shift_off_requests': [],
        'cover': []
    }
    
    current_section = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for section headers
            if line.startswith('SECTION_'):
                current_section = line.replace('SECTION_', '')
                continue
            
            # Parse based on current section
            if current_section == 'HORIZON':
                data['horizon'] = int(line)
            
            elif current_section == 'SHIFTS':
                parts = line.split(',')
                shift = {
                    'id': parts[0],
                    'length_mins': int(parts[1]),
                    'cannot_follow': parts[2].split('|') if len(parts) > 2 and parts[2] else []
                }
                data['shifts'].append(shift)
            
            elif current_section == 'STAFF':
                parts = line.split(',')
                # Parse MaxShifts (e.g., "E=0|D=28|L=0|N=4")
                max_shifts_str = parts[1]
                max_shifts = {}
                for ms in max_shifts_str.split('|'):
                    k, v = ms.split('=')
                    max_shifts[k] = int(v)
                
                staff = {
                    'id': parts[0],
                    'max_shifts': max_shifts,
                    'max_total_mins': int(parts[2]),
                    'min_total_mins': int(parts[3]),
                    'max_consecutive_shifts': int(parts[4]),
                    'min_consecutive_shifts': int(parts[5]),
                    'min_consecutive_days_off': int(parts[6]),
                    'max_weekends': int(parts[7])
                }
                data['staff'].append(staff)
            
            elif current_section == 'DAYS_OFF':
                parts = line.split(',')
                emp_id = parts[0]
                days = [int(d) for d in parts[1:]]
                data['days_off'][emp_id] = days
            
            elif current_section == 'COVER':
                parts = line.split(',')
                cover = {
                    'day': int(parts[0]),
                    'shift': parts[1],
                    'requirement': int(parts[2]),
                    'under_weight': int(parts[3]),
                    'over_weight': int(parts[4])
                }
                data['cover'].append(cover)
            
            elif current_section == 'SHIFT_ON_REQUESTS':
                parts = line.split(',')
                req = {
                    'employee': parts[0],
                    'day': int(parts[1]),
                    'shift': parts[2],
                    'weight': int(parts[3])
                }
                data['shift_on_requests'].append(req)
            
            elif current_section == 'SHIFT_OFF_REQUESTS':
                parts = line.split(',')
                req = {
                    'employee': parts[0],
                    'day': int(parts[1]),
                    'shift': parts[2],
                    'weight': int(parts[3])
                }
                data['shift_off_requests'].append(req)
    
    return data


def convert_to_nss_format(benchmark_data: dict, num_scenarios: int = 10, 
                          variation_pct: float = 0.15, seed: int = 42) -> tuple:
    """
    Convert benchmark data to NSS format.
    
    Since benchmark instances have deterministic demand (cover requirements),
    we generate stochastic scenarios by adding variation to the base demand.
    
    Args:
        benchmark_data: Parsed benchmark data
        num_scenarios: Number of stochastic scenarios to generate
        variation_pct: Percentage variation for stochastic demand (e.g., 0.15 = ±15%)
        seed: Random seed for reproducibility
    
    Returns:
        (nurses_df, scenarios_df)
    """
    np.random.seed(seed)
    
    # Extract nurses
    nurses = [staff['id'] for staff in benchmark_data['staff']]
    nurses_df = pd.DataFrame({'nurse': nurses})
    
    # Extract base demand from COVER section
    base_demand = {}
    for cover in benchmark_data['cover']:
        day = cover['day'] + 1  # Convert to 1-indexed
        shift = cover['shift']
        req = cover['requirement']
        base_demand[(day, shift)] = req
    
    # Get horizon and shifts
    horizon = benchmark_data['horizon']
    shifts = [s['id'] for s in benchmark_data['shifts']]
    
    # Generate stochastic scenarios
    scenario_data = []
    for scenario in range(1, num_scenarios + 1):
        for day in range(1, horizon + 1):
            for shift in shifts:
                base = base_demand.get((day, shift), 0)
                
                # Add stochastic variation
                if scenario == 1:
                    # First scenario = baseline (no variation)
                    demand = base
                else:
                    # Other scenarios have random variation
                    variation = np.random.uniform(-variation_pct, variation_pct)
                    demand = max(1, int(base * (1 + variation)))
                
                scenario_data.append({
                    'scenario': scenario,
                    'day': day,
                    'shift': shift,
                    'demand': demand
                })
    
    scenarios_df = pd.DataFrame(scenario_data)
    
    return nurses_df, scenarios_df


def extract_model_params(benchmark_data: dict) -> dict:
    """
    Extract model parameters from benchmark data.
    """
    # Get first staff member as reference (they often have similar constraints)
    if benchmark_data['staff']:
        sample_staff = benchmark_data['staff'][0]
        
        # Calculate n1 from max_total_mins / shift_length
        shift_length = benchmark_data['shifts'][0]['length_mins'] if benchmark_data['shifts'] else 480
        n1 = sample_staff['max_total_mins'] // shift_length
        n3 = sample_staff['min_total_mins'] // shift_length
        n2 = sample_staff['max_shifts'].get('N', 0)
        
        params = {
            'horizon_days': benchmark_data['horizon'],
            'num_nurses': len(benchmark_data['staff']),
            'num_shifts': len(benchmark_data['shifts']),
            'shift_types': [s['id'] for s in benchmark_data['shifts']],
            'n1_max_total_shifts': n1,
            'n2_max_night_shifts': n2,
            'n3_min_regular_shifts': n3,
            'max_consecutive_shifts': sample_staff['max_consecutive_shifts'],
            'min_consecutive_shifts': sample_staff['min_consecutive_shifts'],
            'min_consecutive_days_off': sample_staff['min_consecutive_days_off'],
            'max_weekends': sample_staff['max_weekends']
        }
        return params
    return {}


def convert_instance(instance_num: int, output_dir: str, num_scenarios: int = 10):
    """
    Convert a single benchmark instance to NSS format.
    """
    # Paths
    script_dir = Path(__file__).parent
    benchmark_dir = script_dir / 'benchmark_instances' / 'instances1_24'
    input_file = benchmark_dir / f'Instance{instance_num}.txt'
    
    if not input_file.exists():
        print(f"Error: Instance {instance_num} not found at {input_file}")
        return None
    
    # Parse benchmark
    print(f"\n{'='*60}")
    print(f"Converting Instance {instance_num}")
    print(f"{'='*60}")
    
    benchmark_data = parse_benchmark_file(input_file)
    
    # Extract parameters
    params = extract_model_params(benchmark_data)
    print(f"\nInstance Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    # Convert to NSS format
    nurses_df, scenarios_df = convert_to_nss_format(
        benchmark_data, 
        num_scenarios=num_scenarios,
        variation_pct=0.15
    )
    
    # Save files
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    nurses_file = output_path / f'benchmark{instance_num}_nurses.csv'
    scenarios_file = output_path / f'benchmark{instance_num}_scenarios.csv'
    
    nurses_df.to_csv(nurses_file, index=False, header=False)
    scenarios_df.to_csv(scenarios_file, index=False)
    
    print(f"\nGenerated files:")
    print(f"  Nurses: {nurses_file} ({len(nurses_df)} nurses)")
    print(f"  Scenarios: {scenarios_file} ({len(scenarios_df)} records)")
    
    # Demand statistics
    print(f"\nDemand Statistics:")
    for shift in params.get('shift_types', []):
        shift_data = scenarios_df[scenarios_df['shift'] == shift]['demand']
        print(f"  Shift {shift}: min={shift_data.min()}, max={shift_data.max()}, avg={shift_data.mean():.1f}")
    
    return nurses_df, scenarios_df


def main():
    parser = argparse.ArgumentParser(description='Convert benchmark instances to NSS format')
    parser.add_argument('--instance', type=int, help='Instance number (1-24)')
    parser.add_argument('--all', action='store_true', help='Convert all instances')
    parser.add_argument('--scenarios', type=int, default=10, help='Number of scenarios to generate')
    parser.add_argument('--output', type=str, default='.',  help='Output directory')
    
    args = parser.parse_args()
    
    if args.all:
        for i in range(1, 25):
            try:
                convert_instance(i, args.output, args.scenarios)
            except Exception as e:
                print(f"Error converting instance {i}: {e}")
    elif args.instance:
        convert_instance(args.instance, args.output, args.scenarios)
    else:
        # Default: convert instance 8 (medium complexity)
        print("No instance specified. Converting Instance 8 as example...")
        convert_instance(8, args.output, args.scenarios)


if __name__ == '__main__':
    main()
