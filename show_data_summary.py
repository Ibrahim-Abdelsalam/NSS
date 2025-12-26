import pandas as pd

# Load the data
nurses_df = pd.read_csv('data/analysis_nurses.csv')
scenarios_df = pd.read_csv('data/analysis_scenarios.csv')

print("\n" + "="*70)
print("DATA USED IN CONFIGURATION ANALYSIS")
print("="*70)

print("\n📋 NURSES DATA (analysis_nurses.csv):")
print("-" * 50)
print(f"Total nurses: {len(nurses_df)}")
print(f"Nurse names: {', '.join(nurses_df['Nurse'].tolist())}")

print("\n📊 SCENARIOS DATA (analysis_scenarios.csv):")
print("-" * 50)
print(f"Total records: {len(scenarios_df)}")
print(f"Scenarios: {scenarios_df['scenario'].nunique()} scenarios (1, 2, 3)")
print(f"Planning horizon: {scenarios_df['day'].nunique()} days")
print(f"Shifts per day: {scenarios_df['shift'].nunique()} shifts {list(scenarios_df['shift'].unique())}")
print(f"\nDemand Statistics:")
print(f"  Minimum demand: {scenarios_df['demand'].min()} nurses")
print(f"  Maximum demand: {scenarios_df['demand'].max()} nurses")
print(f"  Average demand: {scenarios_df['demand'].mean():.2f} nurses per shift")
print(f"  Total demand (all scenarios): {scenarios_df['demand'].sum()} nurse-shifts")
print(f"  Average per scenario: {scenarios_df.groupby('scenario')['demand'].sum().mean():.1f} nurse-shifts")

print("\n📈 Demand by Shift Type:")
print("-" * 50)
shift_stats = scenarios_df.groupby('shift')['demand'].agg(['mean', 'min', 'max'])
for shift in ['E', 'D', 'L', 'N']:
    stats = shift_stats.loc[shift]
    print(f"  {shift} (Early/Day/Late/Night): Avg={stats['mean']:.2f}, Min={int(stats['min'])}, Max={int(stats['max'])}")

print("\n📅 Sample Scenario Data (First 3 days of Scenario 1):")
print("-" * 50)
sample = scenarios_df[scenarios_df['scenario'] == 1].head(12)
print(sample.to_string(index=False))

print("\n💡 DATA CHARACTERISTICS:")
print("-" * 50)
print(f"  • Problem size: 8 nurses × 7 days × 4 shifts = 224 possible shift assignments")
print(f"  • Average utilization: {(scenarios_df['demand'].mean() * 4 / 8 * 100):.1f}% (demand vs. available nurses)")
print(f"  • Stochastic scenarios: 3 equally weighted scenarios")
print(f"  • This is a SMALL test instance for validation purposes")
print("="*70 + "\n")
