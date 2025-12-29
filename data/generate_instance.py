"""
Generate Medium-Sized Instance for Nurse Scheduling Optimization
================================================================
Creates a reproducible instance with:
- 25 nurses
- 14 days (bi-weekly planning)
- 20 stochastic demand scenarios

Output:
- medium_nurses.csv: List of nurse names
- medium_scenarios.csv: Demand scenarios with stochastic variation
"""

import numpy as np
import pandas as pd
import os

# Set seed for reproducibility
np.random.seed(42)

# Instance parameters
NUM_NURSES = 25
NUM_DAYS = 14
NUM_SCENARIOS = 20
SHIFTS = ['E', 'D', 'L', 'N']  # Early, Day, Late, Night

# Base demand as percentage of nurse pool (from model_2.py analysis)
BASE_DEMAND_PCT = {
    'E': 0.25,  # Early shift - 25%
    'D': 0.30,  # Day shift - 30% (peak)
    'L': 0.25,  # Late shift - 25%
    'N': 0.15   # Night shift - 15%
}

def generate_nurses():
    """Generate list of nurse names."""
    return [f"N{i+1}" for i in range(NUM_NURSES)]

def generate_scenarios():
    """Generate stochastic demand scenarios."""
    scenario_data = []
    
    for scenario in range(1, NUM_SCENARIOS + 1):
        for day in range(1, NUM_DAYS + 1):
            for shift in SHIFTS:
                # Base demand from nurse pool percentage
                base = max(1, int(NUM_NURSES * BASE_DEMAND_PCT[shift]))
                
                # Stochastic variation: ±15% (as per paper methodology)
                variation = np.random.uniform(-0.15, 0.15)
                demand = max(1, int(base * (1 + variation)))
                
                # Weekend adjustment: 80% of weekday demand
                # Days 6, 7, 13, 14 are weekends in a 14-day period
                if day % 7 in [0, 6]:
                    demand = max(1, int(demand * 0.8))
                
                scenario_data.append({
                    'scenario': scenario,
                    'day': day,
                    'shift': shift,
                    'demand': demand
                })
    
    return pd.DataFrame(scenario_data)

def main():
    # Output directory
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Generate nurses
    nurses = generate_nurses()
    nurses_df = pd.DataFrame({'nurse': nurses})
    nurses_file = os.path.join(output_dir, 'medium_nurses.csv')
    nurses_df.to_csv(nurses_file, index=False, header=False)
    print(f"Generated {len(nurses)} nurses -> {nurses_file}")
    
    # Generate scenarios
    scenarios_df = generate_scenarios()
    scenarios_file = os.path.join(output_dir, 'medium_scenarios.csv')
    scenarios_df.to_csv(scenarios_file, index=False)
    print(f"Generated {len(scenarios_df)} demand records -> {scenarios_file}")
    
    # Summary statistics
    print("\n--- Instance Summary ---")
    print(f"Nurses: {NUM_NURSES}")
    print(f"Days: {NUM_DAYS}")
    print(f"Scenarios: {NUM_SCENARIOS}")
    print(f"Shifts per day: {len(SHIFTS)}")
    print(f"Total demand records: {NUM_SCENARIOS * NUM_DAYS * len(SHIFTS)}")
    
    # Demand statistics
    print("\n--- Demand Statistics ---")
    for shift in SHIFTS:
        shift_data = scenarios_df[scenarios_df['shift'] == shift]['demand']
        print(f"Shift {shift}: min={shift_data.min()}, max={shift_data.max()}, avg={shift_data.mean():.1f}")
    
    total_demand = scenarios_df.groupby('scenario')['demand'].sum()
    print(f"\nTotal demand per scenario: min={total_demand.min()}, max={total_demand.max()}, avg={total_demand.mean():.1f}")

if __name__ == "__main__":
    main()
