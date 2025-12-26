import pandas as pd
import numpy as np

np.random.seed(123)

days = 14
scenarios = 5
# Use 4 shift types like the benchmark
shifts = ['E', 'D', 'L', 'N']

# More conservative demand levels to ensure feasibility
# Based on 16 nurses with max 15 shifts each
base_demand = {
    'E': 3,  # Early shift: 3 nurses
    'D': 4,  # Day shift: 4 nurses (highest demand)
    'L': 3,  # Late shift: 3 nurses
    'N': 2   # Night shift: 2 nurses (lowest demand)
}

data = []

for s in range(1, scenarios + 1):
    for d in range(1, days + 1):
        # Weekend indicator (assuming day 1 starts on Monday)
        # Days 6,7,13,14 are weekends
        is_weekend = (d % 7 in [6, 0])
        
        for shift in shifts:
            # Base demand with small variation
            variation = np.random.randint(-1, 2)  # -1, 0, or 1
            weekend_adj = -1 if (is_weekend and shift != 'N') else 0
            
            demand = base_demand[shift] + variation + weekend_adj
            
            # Ensure demand is between 1 and 6
            demand = max(1, min(6, demand))
            
            data.append({
                'scenario': s,
                'day': d,
                'shift': shift,
                'demand': demand
            })

df = pd.DataFrame(data)

# Save to CSV
df.to_csv('data/experiment_scenarios.csv', index=False)

print(f'Created {len(df)} rows')
print('\nDemand statistics by shift:')
print(df.groupby('shift')['demand'].agg(['mean', 'min', 'max']))

print(f'\nTotal demand per scenario-day (avg): {df.groupby(["scenario", "day"])["demand"].sum().mean():.1f}')
print(f'Max total demand per day: {df.groupby(["scenario", "day"])["demand"].sum().max()}')
print(f'\nWith 16 nurses @ 15 max shifts = 240 total capacity')
print(f'Total demand across all scenarios (avg per scenario): {df.groupby("scenario")["demand"].sum().mean():.0f}')
