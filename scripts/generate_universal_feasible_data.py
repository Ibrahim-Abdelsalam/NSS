import pandas as pd
import numpy as np

np.random.seed(42)  # For reproducibility

days = 14
scenarios = 5
shifts = ['E', 'D', 'L', 'N']

# SIGNIFICANTLY REDUCED demand for universal feasibility
# With 20 nurses and strict CVaR/fatigue params, need lower demand
base_demand = {
    'E': 2,    # Early: reduced from 3
    'D': 3,    # Day: reduced from 4  
    'L': 2,    # Late: reduced from 3
    'N': 2     # Night: unchanged
}

data = []

for s in range(1, scenarios + 1):
    for d in range(1, days + 1):
        # Weekend indicator (days 6,7,13,14 assuming Monday start)
        is_weekend = (d % 7 in [6, 0])
        
        for shift in shifts:
            # Small variation
            variation = np.random.randint(-1, 2)  # -1, 0, or 1
            weekend_adj = -1 if (is_weekend and shift != 'N') else 0
            
            demand = base_demand[shift] + variation + weekend_adj
            
            # Ensure demand is between 1 and 5 (conservative ceiling)
            demand = max(1, min(5, demand))
            
            data.append({
                'scenario': s,
                'day': d,
                'shift': shift,
                'demand': demand
            })

df = pd.DataFrame(data)

# Save to CSV - FIXED: save to scenarios not nurses!
df.to_csv('data/experiment_scenarios.csv', index=False)

print(f'[OK] Created {len(df)} rows in experiment_scenarios.csv')
print('\nDemand statistics by shift:')
stats = df.groupby('shift')['demand'].agg(['mean', 'min', 'max'])
print(stats)

print(f'\nTotal demand per scenario-day:')
daily_demand = df.groupby(["scenario", "day"])["demand"].sum()
print(f'  Average: {daily_demand.mean():.1f} nurses/day')
print(f'  Maximum: {daily_demand.max()} nurses/day')
print(f'  Minimum: {daily_demand.min()} nurses/day')

print(f'\nCapacity analysis:')
print(f'  20 nurses × 15 max shifts = 300 total capacity')
total_demand_avg = df.groupby("scenario")["demand"].sum().mean()
print(f'  Total demand (avg per scenario): {total_demand_avg:.0f} shifts')
print(f'  Utilization: {total_demand_avg/300*100:.1f}%')

print(f'\n[OK] Reduced demand should work with strict CVaR (mu=50) and fatigue (0.70) params!')
