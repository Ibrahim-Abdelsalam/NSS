#!/usr/bin/env python3
"""
Convert Real Hospital Data to NSS Format with Genuine Demand Uncertainty

This converter uses actual hospital bed occupancy time series data from 
healthdata.gov to create scenarios that capture REAL demand uncertainty,
similar to the ORTEC data used in He et al. (2019).

The key insight: historical daily variations in bed occupancy represent
genuine demand uncertainty that can be used to generate realistic scenarios.

Data Source: COVID-19 Reported Patient Impact and Hospital Capacity
https://healthdata.gov/Hospital/COVID-19-Reported-Patient-Impact-and-Hospital-Capa/g62h-syeh
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import os

def load_hospital_data(json_file: str) -> pd.DataFrame:
    """Load and preprocess hospital time series data."""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Parse date
    df['date'] = pd.to_datetime(df['date'])
    
    # Convert numeric columns
    numeric_cols = ['inpatient_beds', 'inpatient_beds_used', 'inpatient_beds_used_covid',
                    'staffed_icu_adult_patients_confirmed_covid', 'total_staffed_adult_icu_beds']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    return df


def extract_demand_scenarios(df: pd.DataFrame, 
                            horizon_days: int = 28,
                            num_scenarios: int = 20,
                            shifts_per_day: int = 4,
                            target_avg_demand: int = 5,
                            seed: int = 42) -> tuple:
    """
    Extract demand scenarios from real hospital time series.
    
    The method:
    1. Sample multiple non-overlapping windows from the time series
    2. Each window becomes a "scenario" representing a possible realization
    3. NORMALIZE to a target ward size while preserving the variation PATTERN
    
    This captures REAL uncertainty patterns:
    - Day-of-week effects (weekends vs weekdays)
    - Seasonal patterns
    - Random daily fluctuations
    
    The key insight: we keep the RELATIVE variation (coefficient of variation)
    from real data but scale to a manageable ward size.
    
    Args:
        df: Hospital data with 'date' and 'inpatient_beds_used' columns
        horizon_days: Planning horizon (default 28 days like paper)
        num_scenarios: Number of scenarios to generate
        shifts_per_day: Number of shifts (default 4: Morning, Day, Evening, Night)
        target_avg_demand: Target average nurses per shift (default 5)
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (scenarios_df, statistics_dict)
    """
    np.random.seed(seed)
    
    # Filter to rows with valid bed data
    df_valid = df[df['inpatient_beds_used'].notna()].copy()
    
    if len(df_valid) < horizon_days * 2:
        raise ValueError(f"Not enough data: {len(df_valid)} days, need at least {horizon_days * 2}")
    
    # Define shift types
    shift_names = ['E', 'D', 'L', 'N'][:shifts_per_day]  # Early, Day, Late, Night
    
    # Shift demand multipliers (relative staffing needs)
    # Based on typical hospital patterns: Day shifts need more staff
    shift_multipliers = {
        'E': 0.85,   # Early morning: 85% of average
        'D': 1.40,   # Day: 140% of average (highest)
        'L': 1.20,   # Late/Evening: 120% 
        'N': 0.55    # Night: 55% (lowest)
    }
    
    # Calculate normalization factor
    # We want the AVERAGE demand per shift to be target_avg_demand
    beds_mean = df_valid['inpatient_beds_used'].mean()
    beds_std = df_valid['inpatient_beds_used'].std()
    coef_variation = beds_std / beds_mean  # This is the REAL uncertainty we preserve
    
    print(f"\n  Original data coefficient of variation: {coef_variation*100:.1f}%")
    print(f"  (This real-world variation pattern is preserved in scenarios)")
    
    # Sample starting points for scenarios
    max_start = len(df_valid) - horizon_days
    if max_start < num_scenarios:
        # Allow overlapping windows if not enough data
        start_indices = np.random.choice(max_start, size=num_scenarios, replace=True)
    else:
        # Prefer non-overlapping windows spread across the time series
        step = max_start // num_scenarios
        start_indices = [i * step for i in range(num_scenarios)]
        np.random.shuffle(start_indices)
    
    scenarios_data = []
    
    for scenario_id, start_idx in enumerate(start_indices, 1):
        window = df_valid.iloc[start_idx:start_idx + horizon_days].copy()
        
        for day_num, (_, row) in enumerate(window.iterrows(), 1):
            beds_used = row['inpatient_beds_used']
            
            # Normalize: convert to z-score, then scale to target
            # This preserves the PATTERN of variation
            z_score = (beds_used - beds_mean) / beds_std if beds_std > 0 else 0
            
            # Distribute across shifts with realistic variation
            for shift in shift_names:
                # Base demand for this shift
                base = target_avg_demand * shift_multipliers[shift]
                
                # Apply the real variation pattern
                # The variation is proportional to the base demand
                variation = z_score * base * coef_variation
                shift_demand = int(np.round(base + variation))
                shift_demand = max(1, shift_demand)  # At least 1 nurse per shift
                
                scenarios_data.append({
                    'scenario': scenario_id,
                    'day': day_num,
                    'shift': shift,
                    'demand': shift_demand
                })
    
    scenarios_df = pd.DataFrame(scenarios_data)
    
    # Calculate statistics
    stats = {}
    for shift in shift_names:
        shift_data = scenarios_df[scenarios_df['shift'] == shift]['demand']
        stats[shift] = {
            'min': int(shift_data.min()),
            'max': int(shift_data.max()),
            'mean': round(shift_data.mean(), 1),
            'std': round(shift_data.std(), 2),
            'cv': round(shift_data.std() / shift_data.mean() * 100, 1) if shift_data.mean() > 0 else 0
        }
    
    return scenarios_df, stats


def generate_nurses(num_nurses: int) -> pd.DataFrame:
    """Generate nurse list."""
    names = [f"Nurse_{i+1}" for i in range(num_nurses)]
    return pd.DataFrame({'Nurse': names})


def estimate_nurses_needed(scenarios_df: pd.DataFrame, 
                          horizon_days: int = 28,
                          n1_max_shifts: int = 20,
                          n3_min_shifts: int = 15) -> int:
    """
    Estimate number of nurses needed based on demand.
    
    Uses the formula: N >= max_daily_demand * num_days / avg_shifts_per_nurse
    With buffer for feasibility.
    """
    # Calculate max demand per day across all scenarios
    daily_demand = scenarios_df.groupby(['scenario', 'day'])['demand'].sum()
    max_daily_demand = daily_demand.max()
    avg_daily_demand = daily_demand.mean()
    
    # Each nurse can work between n3 and n1 shifts
    avg_shifts_per_nurse = (n1_max_shifts + n3_min_shifts) / 2
    
    # Need enough nurses to cover peak demand with some buffer
    nurses_for_peak = int(np.ceil(max_daily_demand * 1.1))
    
    # Also need enough total capacity
    total_demand = avg_daily_demand * horizon_days
    nurses_for_capacity = int(np.ceil(total_demand / avg_shifts_per_nurse * 1.15))
    
    return max(nurses_for_peak, nurses_for_capacity, 15)


def convert_real_data_to_nss(json_file: str, 
                             output_prefix: str,
                             horizon_days: int = 28,
                             num_scenarios: int = 20,
                             num_nurses: int = None,
                             target_avg_demand: int = 5):
    """
    Main conversion function.
    
    Args:
        json_file: Path to COVID hospital JSON data
        output_prefix: Prefix for output files
        horizon_days: Scheduling horizon in days
        num_scenarios: Number of demand scenarios
        num_nurses: Number of nurses (auto-calculated if None)
        target_avg_demand: Target average nurses per shift (scales the problem)
    """
    
    print("\n" + "="*70)
    print("Converting Real Hospital Data to NSS Format")
    print("="*70)
    
    # Load data
    print(f"\nLoading data from: {json_file}")
    df = load_hospital_data(json_file)
    print(f"  Records loaded: {len(df)}")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    
    # Show bed occupancy statistics
    beds_used = df['inpatient_beds_used'].dropna()
    print(f"\nOriginal Bed Occupancy (state-level aggregate):")
    print(f"  Min: {int(beds_used.min()):,}")
    print(f"  Max: {int(beds_used.max()):,}")
    print(f"  Mean: {beds_used.mean():,.0f}")
    print(f"  Std Dev: {beds_used.std():,.0f} ({beds_used.std()/beds_used.mean()*100:.1f}% CV)")
    
    # Extract scenarios
    print(f"\nExtracting {num_scenarios} scenarios from {horizon_days}-day windows...")
    print(f"Scaling to ward-level with avg demand ≈ {target_avg_demand} nurses/shift")
    
    scenarios_df, shift_stats = extract_demand_scenarios(
        df, 
        horizon_days=horizon_days,
        num_scenarios=num_scenarios,
        target_avg_demand=target_avg_demand
    )
    
    # Determine nurse count
    if num_nurses is None:
        num_nurses = estimate_nurses_needed(scenarios_df, horizon_days)
        print(f"\nAuto-calculated nurses needed: {num_nurses}")
    
    # Generate nurses
    nurses_df = generate_nurses(num_nurses)
    
    # Save files
    nurses_file = f"{output_prefix}_nurses.csv"
    scenarios_file = f"{output_prefix}_scenarios.csv"
    
    nurses_df.to_csv(nurses_file, index=False, header=False)
    scenarios_df.to_csv(scenarios_file, index=False)
    
    print(f"\n" + "-"*70)
    print("Generated Files:")
    print(f"  Nurses: {nurses_file} ({num_nurses} nurses)")
    print(f"  Scenarios: {scenarios_file} ({len(scenarios_df)} records)")
    
    print(f"\nDemand Statistics (REAL uncertainty pattern preserved):")
    for shift, stats in shift_stats.items():
        print(f"  Shift {shift}: min={stats['min']}, max={stats['max']}, "
              f"avg={stats['mean']}, std={stats['std']} (CV={stats['cv']}%)")
    
    # Recommended parameters
    n1 = min(20, horizon_days - 5)
    n3 = horizon_days // 2
    print(f"\nRecommended Model Parameters:")
    print(f"  horizon_days: {horizon_days}")
    print(f"  n1 (max total shifts): {n1}")
    print(f"  n2 (max night shifts): {horizon_days // 7}")
    print(f"  n3 (min regular shifts): {n3}")
    print(f"  num_scenarios: {num_scenarios}")
    
    return scenarios_df, nurses_df


def main():
    parser = argparse.ArgumentParser(
        description='Convert real hospital data to NSS format with genuine demand uncertainty'
    )
    parser.add_argument('--input', '-i', type=str, default='covid_hospital_ca.json',
                       help='Input JSON file with hospital time series')
    parser.add_argument('--output', '-o', type=str, default='real_demand',
                       help='Output file prefix')
    parser.add_argument('--days', '-d', type=int, default=28,
                       help='Planning horizon in days')
    parser.add_argument('--scenarios', '-s', type=int, default=20,
                       help='Number of scenarios')
    parser.add_argument('--nurses', '-n', type=int, default=None,
                       help='Number of nurses (auto-calculated if not specified)')
    parser.add_argument('--avg-demand', '-a', type=int, default=5,
                       help='Target average nurses per shift (scales problem size, default 5)')
    
    args = parser.parse_args()
    
    convert_real_data_to_nss(
        json_file=args.input,
        output_prefix=args.output,
        horizon_days=args.days,
        num_scenarios=args.scenarios,
        num_nurses=args.nurses,
        target_avg_demand=args.avg_demand
    )


if __name__ == '__main__':
    main()
