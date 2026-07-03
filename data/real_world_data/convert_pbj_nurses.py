#!/usr/bin/env python3
"""
Convert CMS PBJ (Payroll Based Journal) Nurse Staffing Data to NSS Format

This converter uses ACTUAL NURSE STAFFING HOURS from US nursing facilities,
providing REAL demand uncertainty for the nurse scheduling model.

Data contains:
- Daily RN, LPN, CNA hours worked at each facility
- Daily patient census (MDScensus)
- Data from 15,000+ nursing homes

This is as close as we can get to the ORTEC data used in He et al. (2019)
without proprietary hospital data access.

Source: https://data.cms.gov/quality-of-care/payroll-based-journal-daily-nurse-staffing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import os

def load_pbj_data(csv_file: str, sample_size: int = None) -> pd.DataFrame:
    """Load PBJ nurse staffing CSV."""
    
    print(f"Loading data from: {csv_file}")
    
    # Read with specified columns to reduce memory
    cols_to_use = [
        'PROVNUM', 'PROVNAME', 'STATE', 'WorkDate', 'MDScensus',
        'Hrs_RN', 'Hrs_LPN', 'Hrs_CNA'
    ]
    
    try:
        if sample_size:
            df = pd.read_csv(csv_file, usecols=cols_to_use, nrows=sample_size,
                           encoding='latin-1', on_bad_lines='skip')
        else:
            df = pd.read_csv(csv_file, usecols=cols_to_use,
                           encoding='latin-1', on_bad_lines='skip')
    except ValueError:
        # If columns not found, try loading all and selecting
        df = pd.read_csv(csv_file, nrows=sample_size, encoding='latin-1', 
                        on_bad_lines='skip') if sample_size else pd.read_csv(
                            csv_file, encoding='latin-1', on_bad_lines='skip')
        available_cols = [c for c in cols_to_use if c in df.columns]
        df = df[available_cols]
    
    # Parse date
    df['WorkDate'] = pd.to_datetime(df['WorkDate'], format='%Y%m%d')
    
    # Calculate total nurse hours
    for col in ['Hrs_RN', 'Hrs_LPN', 'Hrs_CNA']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['Total_Nurse_Hours'] = df.get('Hrs_RN', 0) + df.get('Hrs_LPN', 0) + df.get('Hrs_CNA', 0)
    
    return df


def select_facility(df: pd.DataFrame, 
                   state: str = None,
                   min_days: int = 60,
                   target_size: str = 'medium') -> pd.DataFrame:
    """
    Select a single facility with good data coverage.
    
    Args:
        df: Full PBJ dataset
        state: Filter to specific state (e.g., 'CA', 'TX')
        min_days: Minimum number of days with data
        target_size: 'small' (20-40 patients), 'medium' (40-80), 'large' (80+)
    """
    
    if state:
        df = df[df['STATE'] == state.upper()]
    
    # Find facilities with enough data
    facility_stats = df.groupby('PROVNUM').agg({
        'WorkDate': 'nunique',  # Number of days
        'MDScensus': 'mean',     # Average census
        'Total_Nurse_Hours': 'mean'
    }).reset_index()
    
    facility_stats.columns = ['PROVNUM', 'num_days', 'avg_census', 'avg_hours']
    
    # Filter by minimum days
    facility_stats = facility_stats[facility_stats['num_days'] >= min_days]
    
    if len(facility_stats) == 0:
        raise ValueError(f"No facilities found with {min_days}+ days of data")
    
    # Filter by target size
    if target_size == 'small':
        facility_stats = facility_stats[(facility_stats['avg_census'] >= 20) & 
                                        (facility_stats['avg_census'] <= 40)]
    elif target_size == 'medium':
        facility_stats = facility_stats[(facility_stats['avg_census'] >= 40) & 
                                        (facility_stats['avg_census'] <= 80)]
    elif target_size == 'large':
        facility_stats = facility_stats[facility_stats['avg_census'] >= 80]
    
    if len(facility_stats) == 0:
        raise ValueError(f"No {target_size} facilities found. Try different size.")
    
    # Select facility with most data
    best_facility = facility_stats.sort_values('num_days', ascending=False).iloc[0]
    
    print(f"\nSelected facility: {best_facility['PROVNUM']}")
    print(f"  Days of data: {int(best_facility['num_days'])}")
    print(f"  Avg patient census: {best_facility['avg_census']:.1f}")
    print(f"  Avg daily nurse hours: {best_facility['avg_hours']:.1f}")
    
    return df[df['PROVNUM'] == best_facility['PROVNUM']].copy()


def calculate_nurse_demand(facility_df: pd.DataFrame, 
                          hours_per_shift: float = 8.0,
                          shifts_per_day: int = 3) -> pd.DataFrame:
    """
    Convert nurse hours to nurse count per shift.
    
    Assumes standard 8-hour shifts and distributes hours across shifts.
    """
    
    # Sort by date
    facility_df = facility_df.sort_values('WorkDate').reset_index(drop=True)
    
    # Calculate nurses needed per day
    facility_df['Total_Nurses_Day'] = np.ceil(
        facility_df['Total_Nurse_Hours'] / hours_per_shift
    ).astype(int)
    
    # Distribute across shifts (Day-heavy distribution)
    shift_ratios = {
        3: {'D': 0.45, 'E': 0.35, 'N': 0.20},  # 3 shifts
        4: {'E': 0.20, 'D': 0.35, 'L': 0.30, 'N': 0.15}  # 4 shifts
    }
    
    ratios = shift_ratios.get(shifts_per_day, shift_ratios[3])
    
    for shift, ratio in ratios.items():
        facility_df[f'Demand_{shift}'] = np.maximum(
            1,
            np.round(facility_df['Total_Nurses_Day'] * ratio)
        ).astype(int)
    
    return facility_df


def create_scenarios_from_facility(facility_df: pd.DataFrame,
                                  horizon_days: int = 28,
                                  num_scenarios: int = 20,
                                  shifts_per_day: int = 4,
                                  seed: int = 42) -> tuple:
    """
    Create scenarios by sampling different time windows from facility data.
    
    Each scenario is a real historical period from the facility.
    """
    np.random.seed(seed)
    
    # Sort by date and ensure contiguous data
    facility_df = facility_df.sort_values('WorkDate').reset_index(drop=True)
    
    available_days = len(facility_df)
    if available_days < horizon_days:
        raise ValueError(f"Only {available_days} days of data, need {horizon_days}")
    
    print(f"\n  Available days: {available_days}")
    print(f"  Date range: {facility_df['WorkDate'].min().date()} to {facility_df['WorkDate'].max().date()}")
    
    # Calculate demand for all days
    facility_df = calculate_nurse_demand(facility_df, shifts_per_day=shifts_per_day)
    
    # Determine shift columns
    demand_cols = [c for c in facility_df.columns if c.startswith('Demand_')]
    shift_names = [c.replace('Demand_', '') for c in demand_cols]
    
    # Sample starting points for scenarios
    max_start = available_days - horizon_days
    if max_start < num_scenarios:
        # Allow overlapping windows
        start_indices = np.random.choice(max(1, max_start), size=num_scenarios, replace=True)
    else:
        # Non-overlapping windows spread across time
        step = max_start // num_scenarios
        start_indices = [i * step for i in range(num_scenarios)]
    
    scenarios_data = []
    
    for scenario_id, start_idx in enumerate(start_indices, 1):
        window = facility_df.iloc[start_idx:start_idx + horizon_days]
        
        for day_num, (_, row) in enumerate(window.iterrows(), 1):
            for shift in shift_names:
                scenarios_data.append({
                    'scenario': scenario_id,
                    'day': day_num,
                    'shift': shift,
                    'demand': int(row[f'Demand_{shift}'])
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


def estimate_nurses_needed(scenarios_df: pd.DataFrame, 
                          horizon_days: int = 28) -> int:
    """Estimate number of nurses needed based on demand."""
    
    daily_demand = scenarios_df.groupby(['scenario', 'day'])['demand'].sum()
    max_daily = daily_demand.max()
    avg_daily = daily_demand.mean()
    
    # Need enough for peak + buffer
    nurses_for_peak = int(np.ceil(max_daily * 1.1))
    
    # Also need total capacity
    n1, n3 = 20, 14  # Typical constraints
    total_demand = avg_daily * horizon_days
    nurses_for_capacity = int(np.ceil(total_demand / ((n1 + n3) / 2) * 1.15))
    
    return max(nurses_for_peak, nurses_for_capacity, 15)


def convert_pbj_to_nss(csv_file: str,
                      output_prefix: str,
                      state: str = None,
                      facility_size: str = 'medium',
                      horizon_days: int = 28,
                      num_scenarios: int = 20,
                      shifts_per_day: int = 4,
                      num_nurses: int = None):
    """
    Main conversion function.
    """
    
    print("\n" + "="*70)
    print("Converting CMS PBJ Nurse Staffing to NSS Format")
    print("="*70)
    print("\nThis is REAL nurse staffing data from US nursing facilities!")
    
    # Load data
    df = load_pbj_data(csv_file)
    print(f"  Total records: {len(df):,}")
    print(f"  Unique facilities: {df['PROVNUM'].nunique():,}")
    
    # Select facility
    print(f"\nSelecting {facility_size} facility" + (f" in {state}" if state else "") + "...")
    facility_df = select_facility(df, state=state, target_size=facility_size)
    
    # Get facility name for reporting
    facility_name = facility_df['PROVNAME'].iloc[0] if 'PROVNAME' in facility_df.columns else "Unknown"
    
    # Create scenarios
    print(f"\nCreating {num_scenarios} scenarios from {horizon_days}-day windows...")
    scenarios_df, shift_stats = create_scenarios_from_facility(
        facility_df,
        horizon_days=horizon_days,
        num_scenarios=num_scenarios,
        shifts_per_day=shifts_per_day
    )
    
    # Estimate nurse count
    if num_nurses is None:
        num_nurses = estimate_nurses_needed(scenarios_df, horizon_days)
        print(f"\nAuto-calculated nurses needed: {num_nurses}")
    
    # Generate nurses
    nurses_df = pd.DataFrame({'Nurse': [f"Nurse_{i+1}" for i in range(num_nurses)]})
    
    # Save files
    nurses_file = f"{output_prefix}_nurses.csv"
    scenarios_file = f"{output_prefix}_scenarios.csv"
    
    nurses_df.to_csv(nurses_file, index=False, header=False)
    scenarios_df.to_csv(scenarios_file, index=False)
    
    print(f"\n" + "-"*70)
    print("Generated Files:")
    print(f"  Nurses: {nurses_file} ({num_nurses} nurses)")
    print(f"  Scenarios: {scenarios_file} ({len(scenarios_df)} records)")
    
    print(f"\nFacility: {facility_name}")
    print(f"Data source: REAL nurse staffing hours (CMS PBJ)")
    
    print(f"\nDemand Statistics (REAL uncertainty from actual staffing):")
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
    
    return scenarios_df, nurses_df


def main():
    parser = argparse.ArgumentParser(
        description='Convert CMS PBJ nurse staffing data to NSS format'
    )
    parser.add_argument('--input', '-i', type=str, default='PBJ_nurse_staffing_2024Q1.csv',
                       help='Input CSV file from CMS PBJ')
    parser.add_argument('--output', '-o', type=str, default='pbj_real',
                       help='Output file prefix')
    parser.add_argument('--state', '-s', type=str, default=None,
                       help='Filter to state (e.g., CA, TX, NY)')
    parser.add_argument('--size', type=str, default='medium',
                       choices=['small', 'medium', 'large'],
                       help='Facility size: small (20-40), medium (40-80), large (80+) patients')
    parser.add_argument('--days', '-d', type=int, default=28,
                       help='Planning horizon in days')
    parser.add_argument('--scenarios', type=int, default=20,
                       help='Number of scenarios')
    parser.add_argument('--shifts', type=int, default=4, choices=[3, 4],
                       help='Number of shifts per day')
    parser.add_argument('--nurses', '-n', type=int, default=None,
                       help='Number of nurses (auto-calculated if not specified)')
    
    args = parser.parse_args()
    
    convert_pbj_to_nss(
        csv_file=args.input,
        output_prefix=args.output,
        state=args.state,
        facility_size=args.size,
        horizon_days=args.days,
        num_scenarios=args.scenarios,
        shifts_per_day=args.shifts,
        num_nurses=args.nurses
    )


if __name__ == '__main__':
    main()
