"""
Generate Simple Benchmark Data Compatible with NSS Model

Creates realistic nurse scheduling data that matches NSS constraints
(based on He et al. 2019 paper) without specialized benchmark constraints.
"""

import pandas as pd
import numpy as np


def generate_nss_compatible_benchmark(num_nurses=20, num_days=14, num_scenarios=5):
    """
    Generate benchmark data that matches NSS model structure.
    
    NSS Model Constraints (He et al. 2019):
    - Max total shifts (n1)
    - Max night shifts (n2)
    - Min regular shifts if working (n3)
    - Min complete weekends off (n4)
    - No per-nurse restrictions
    - No fixed unavailability
    - All nurses can work all shift types
    """
    
    # Create nurses list
    nurses = [f"Nurse_{i+1:02d}" for i in range(num_nurses)]
    nurses_df = pd.DataFrame({'nurse_name': nurses})
    
    # Create realistic demand patterns
    scenarios_data = []
    shift_types = ['E', 'D', 'L', 'N']
    
    for scenario in range(1, num_scenarios + 1):
        for day in range(1, num_days + 1):
            # Base demand pattern (varies by day of week)
            day_of_week = (day - 1) % 7
            is_weekend = day_of_week >= 5
            
            # Weekend has lower demand
            demand_multiplier = 0.7 if is_weekend else 1.0
            
            for shift in shift_types:
                # Base demand by shift type
                if shift == 'E':  # Early (7am-3pm)
                    base_demand = int(num_nurses * 0.25 * demand_multiplier)
                elif shift == 'D':  # Day (9am-5pm)
                    base_demand = int(num_nurses * 0.30 * demand_multiplier)
                elif shift == 'L':  # Late (3pm-11pm)
                    base_demand = int(num_nurses * 0.25 * demand_multiplier)
                else:  # Night (11pm-7am)
                    base_demand = int(num_nurses * 0.15 * demand_multiplier)
                
                # Add scenario variation (±15%)
                if scenario == 1:
                    demand = base_demand
                else:
                    np.random.seed(scenario * 1000 + day * 10 + ord(shift))
                    variation = np.random.uniform(-0.15, 0.15)
                    demand = max(1, int(base_demand * (1 + variation)))
                
                scenarios_data.append({
                    'scenario': scenario,
                    'day': day,
                    'shift': shift,
                    'demand': demand
                })
    
    scenarios_df = pd.DataFrame(scenarios_data)
    
    return nurses_df, scenarios_df


def print_benchmark_info(nurses_df, scenarios_df):
    """Print benchmark information."""
    print("\n" + "="*70)
    print("NSS-COMPATIBLE BENCHMARK DATA GENERATED")
    print("="*70)
    
    print(f"\n📊 Problem Size:")
    print(f"  Nurses:         {len(nurses_df)}")
    print(f"  Planning Days:  {scenarios_df['day'].nunique()}")
    print(f"  Shift Types:    {scenarios_df['shift'].nunique()} (E, D, L, N)")
    print(f"  Scenarios:      {scenarios_df['scenario'].nunique()}")
    
    print(f"\n📈 Demand Statistics:")
    total_demand = scenarios_df.groupby('scenario')['demand'].sum()
    print(f"  Total Demand (avg):     {total_demand.mean():.1f} shifts")
    print(f"  Total Demand (min):     {total_demand.min()}")
    print(f"  Total Demand (max):     {total_demand.max()}")
    
    avg_daily_demand = scenarios_df.groupby(['scenario', 'day'])['demand'].sum()
    print(f"  Avg Daily Demand:       {avg_daily_demand.mean():.1f}")
    print(f"  Min Daily Demand:       {avg_daily_demand.min()}")
    print(f"  Max Daily Demand:       {avg_daily_demand.max()}")
    
    # Capacity analysis
    num_nurses = len(nurses_df)
    num_days = scenarios_df['day'].nunique()
    
    print(f"\n💼 Capacity Analysis:")
    print(f"  Total nurse capacity (n1=15):  {num_nurses * 15} shifts")
    print(f"  Required demand (avg):         {total_demand.mean():.1f} shifts")
    print(f"  Utilization:                   {(total_demand.mean() / (num_nurses * 15)) * 100:.1f}%")
    
    print(f"\n✅ Compatible with NSS constraints:")
    print(f"  ✓ No per-nurse restrictions (all nurses can work all shifts)")
    print(f"  ✓ No fixed unavailability (no mandatory days off)")
    print(f"  ✓ No shift preferences (only coverage requirements)")
    print(f"  ✓ Matches He et al. (2019) paper structure")
    
    print(f"\n🔧 Suggested NSS Parameters:")
    print(f"  n1 (Max Total Shifts):     15 (realistic full-time)")
    print(f"  n2 (Max Night Shifts):     5 (limit night work)")
    print(f"  n3 (Min Regular Shifts):   10 (ensure min commitment)")
    print(f"  n4 (Min Weekends Off):     1 (work-life balance)")
    print(f"  c1 (Regular Cost):         100")
    print(f"  c2 (Overtime Cost):        150")
    print(f"  q_plus (Emergency Cost):   200")
    
    print("\n" + "="*70)


def main():
    import sys
    
    # Parse arguments
    num_nurses = 20
    num_days = 14
    num_scenarios = 5
    
    if '--nurses' in sys.argv:
        idx = sys.argv.index('--nurses')
        num_nurses = int(sys.argv[idx + 1])
    
    if '--days' in sys.argv:
        idx = sys.argv.index('--days')
        num_days = int(sys.argv[idx + 1])
    
    if '--scenarios' in sys.argv:
        idx = sys.argv.index('--scenarios')
        num_scenarios = int(sys.argv[idx + 1])
    
    print(f"Generating NSS-compatible benchmark...")
    print(f"  Nurses: {num_nurses}")
    print(f"  Days: {num_days}")
    print(f"  Scenarios: {num_scenarios}")
    
    # Generate data
    nurses_df, scenarios_df = generate_nss_compatible_benchmark(
        num_nurses, num_days, num_scenarios
    )
    
    # Save to CSV
    nurses_df.to_csv('data/nss_benchmark_nurses.csv', index=False)
    scenarios_df.to_csv('data/nss_benchmark_scenarios.csv', index=False)
    
    # Print info
    print_benchmark_info(nurses_df, scenarios_df)
    
    print(f"\n✅ Files saved:")
    print(f"  - data/nss_benchmark_nurses.csv")
    print(f"  - data/nss_benchmark_scenarios.csv")
    
    print(f"\n📝 Next Steps:")
    print(f"  1. Run: streamlit run app.py")
    print(f"  2. Upload the generated CSV files")
    print(f"  3. Use the suggested parameters above")
    print(f"  4. Click 'OPTIMIZE SCHEDULE'")
    print(f"\n🎯 This data is designed specifically for your NSS model!")


if __name__ == '__main__':
    main()
