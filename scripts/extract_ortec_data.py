"""
Extract ORTEC01 benchmark data and generate stochastic scenarios.

Based on ORTEC01 specifications from schedulingbenchmarks.org:
- 16 nurses (A-P)
- 31 days planning horizon
- 4 shifts: E (Early), D (Day), L (Late), N (Night)
- Demand pattern: E/D/L = 3 nurses (weekdays), 2 (weekends); N = 1 (all days)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# ORTEC01 Configuration
NUM_NURSES = 16
NUM_DAYS = 31
NUM_SCENARIOS = 50
SHIFTS = ['E', 'D', 'L', 'N']

# Base demand from ORTEC01 specification
# Weekday pattern: E=3, D=3, L=3, N=1
# Weekend pattern: E=2, D=2, L=2, N=1
BASE_DEMAND_WEEKDAY = {'E': 3, 'D': 3, 'L': 3, 'N': 1}
BASE_DEMAND_WEEKEND = {'E': 2, 'D': 2, 'L': 2, 'N': 1}

# Stochastic variation (±20% as mentioned in He et al. 2019)
DEMAND_VARIABILITY = 0.20


def create_ortec_nurses():
    """Create ORTEC nurses dataset (A-P)."""
    nurse_ids = [chr(65 + i) for i in range(NUM_NURSES)]  # A, B, C, ..., P
    
    nurses_df = pd.DataFrame({
        'nurse_id': nurse_ids
    })
    
    return nurses_df


def is_weekend(day):
    """
    Determine if a day is weekend.
    ORTEC01 starts on a specific day - we'll assume day 1 is Monday.
    Weekend = Saturday (day 6, 13, 20, 27) and Sunday (day 7, 14, 21, 28)
    """
    day_of_week = (day - 1) % 7  # 0=Monday, 6=Sunday
    return day_of_week >= 5  # Saturday or Sunday


def generate_stochastic_scenarios():
    """
    Generate stochastic demand scenarios based on ORTEC01 base demand.
    
    Adds variability to the deterministic ORTEC demand to create
    two-stage stochastic scenarios as used in He et al. (2019).
    """
    scenarios = []
    
    for scenario in range(1, NUM_SCENARIOS + 1):
        for day in range(1, NUM_DAYS + 1):
            # Select base demand based on weekday/weekend
            if is_weekend(day):
                base_demand = BASE_DEMAND_WEEKEND
            else:
                base_demand = BASE_DEMAND_WEEKDAY
            
            for shift in SHIFTS:
                base = base_demand[shift]
                
                # Add stochastic variation
                # Use normal distribution with mean=base, std=base*variability
                # Round to nearest integer and ensure non-negative
                if base > 0:
                    std_dev = base * DEMAND_VARIABILITY
                    demand = np.random.normal(base, std_dev)
                    demand = max(1, round(demand))  # At least 1 nurse needed
                else:
                    demand = base
                
                scenarios.append({
                    'scenario': scenario,
                    'day': day,
                    'shift': shift,
                    'demand': demand
                })
    
    scenarios_df = pd.DataFrame(scenarios)
    return scenarios_df


def create_ortec_validation_data():
    """Main function to create ORTEC validation datasets."""
    
    print("="*80)
    print("ORTEC01 DATA EXTRACTION")
    print("="*80)
    
    # Create nurses dataset
    print("\n1. Creating nurses dataset...")
    nurses_df = create_ortec_nurses()
    print(f"   ✅ Created {len(nurses_df)} nurses (A-P)")
    
    # Create scenarios dataset
    print("\n2. Generating stochastic scenarios...")
    scenarios_df = generate_stochastic_scenarios()
    print(f"   ✅ Generated {NUM_SCENARIOS} scenarios")
    print(f"   ✅ Planning horizon: {NUM_DAYS} days")
    print(f"   ✅ Total demand records: {len(scenarios_df)}")
    
    # Calculate statistics
    print("\n3. Demand statistics:")
    demand_stats = scenarios_df.groupby('shift')['demand'].agg(['mean', 'std', 'min', 'max'])
    print(demand_stats)
    
    # Save to CSV
    print("\n4. Saving to CSV files...")
    nurses_df.to_csv('data/ortec_nurses.csv', index=False)
    scenarios_df.to_csv('data/ortec_scenarios.csv', index=False)
    print("   ✅ Saved: data/ortec_nurses.csv")
    print("   ✅ Saved: data/ortec_scenarios.csv")
    
    # Display sample data
    print("\n5. Sample data preview:")
    print("\nNurses (first 10):")
    print(nurses_df.head(10))
    
    print("\nScenarios (first 20 rows):")
    print(scenarios_df.head(20))
    
    # Summary by day type
    print("\n6. Demand summary by day type:")
    scenarios_df['is_weekend'] = scenarios_df['day'].apply(is_weekend)
    weekend_demand = scenarios_df[scenarios_df['is_weekend']].groupby('shift')['demand'].mean()
    weekday_demand = scenarios_df[~scenarios_df['is_weekend']].groupby('shift')['demand'].mean()
    
    summary = pd.DataFrame({
        'Weekday_Avg': weekday_demand,
        'Weekend_Avg': weekend_demand,
        'Overall_Avg': scenarios_df.groupby('shift')['demand'].mean()
    })
    print(summary)
    
    print("\n" + "="*80)
    print("ORTEC DATA EXTRACTION COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Load data with: pd.read_csv('data/ortec_nurses.csv')")
    print("  2. Load scenarios with: pd.read_csv('data/ortec_scenarios.csv')")
    print("  3. Run validation with NurseSchedulingModel")
    print("="*80)
    
    return nurses_df, scenarios_df


if __name__ == "__main__":
    nurses_df, scenarios_df = create_ortec_validation_data()
