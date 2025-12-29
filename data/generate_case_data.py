
import numpy as np
import pandas as pd
import os

# Set seed for reproducibility
np.random.seed(42)

# Instance parameters
NUM_NURSES = 20
NUM_DAYS = 14
NUM_SCENARIOS = 10
SHIFTS = ['E', 'D', 'L', 'N']

# Base demand as percentage of nurse pool
BASE_DEMAND_PCT = {
    'E': 0.25,
    'D': 0.30,
    'L': 0.25,
    'N': 0.15
}

def generate_nurses():
    return [f"Nurse_{i+1}" for i in range(NUM_NURSES)]

def generate_scenarios():
    scenario_data = []
    
    for scenario in range(1, NUM_SCENARIOS + 1):
        for day in range(1, NUM_DAYS + 1):
            for shift in SHIFTS:
                base = max(1, int(NUM_NURSES * BASE_DEMAND_PCT[shift]))
                variation = np.random.uniform(-0.15, 0.15)
                demand = max(1, int(base * (1 + variation)))
                
                # Weekend reduction
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
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Nurses
    nurses = generate_nurses()
    nurses_df = pd.DataFrame({'nurse': nurses})
    nurses_file = os.path.join(output_dir, 'case_nurses.csv')
    nurses_df.to_csv(nurses_file, index=False, header=False)
    print(f"Generated {nurses_file}")
    
    # Scenarios
    scenarios = generate_scenarios()
    scenarios_file = os.path.join(output_dir, 'case_scenarios.csv')
    scenarios.to_csv(scenarios_file, index=False)
    print(f"Generated {scenarios_file}")

if __name__ == "__main__":
    main()
