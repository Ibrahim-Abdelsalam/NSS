"""
COMPLETE TEST INSTANCE - Ready to Run

This provides a complete example with:
1. All input parameters clearly documented
2. Input data (nurses + scenarios)
3. Expected output
4. Step-by-step instructions
"""

import pandas as pd
from model import build_and_solve_model, extract_results

# ============================================================================
# STEP 1: INPUT DATA
# ============================================================================

print("="*90)
print("COMPLETE TEST INSTANCE FOR OVERTIME DEMONSTRATION")
print("="*90)

# Nurses (8 nurses for good capacity)
nurses_list = ['Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank', 'Grace', 'Henry']

# Scenarios: 3 scenarios × 7 days × 2 shifts = 42 demand records
scenarios_data = [
    # Scenario 1 (LOW demand - baseline)
    *[{'scenario': 1, 'day': d, 'shift': 'D', 'demand': 4} for d in range(1, 8)],
    *[{'scenario': 1, 'day': d, 'shift': 'N', 'demand': 2} for d in range(1, 8)],
    
    # Scenario 2 (MEDIUM demand)
    *[{'scenario': 2, 'day': d, 'shift': 'D', 'demand': 5} for d in range(1, 8)],
    *[{'scenario': 2, 'day': d, 'shift': 'N', 'demand': 2} for d in range(1, 8)],
    
    # Scenario 3 (HIGH demand)
    *[{'scenario': 3, 'day': d, 'shift': 'D', 'demand': 6} for d in range(1, 8)],
    *[{'scenario': 3, 'day': d, 'shift': 'N', 'demand': 2} for d in range(1, 8)],
]
scenarios_df = pd.DataFrame(scenarios_data)

# ============================================================================
# STEP 2: MODEL PARAMETERS (All Explicitly Set)
# ============================================================================

params = {
    # ----- COST PARAMETERS -----
    'c1': 100.0,          # Regular shift cost (£100/shift)
    'c2': 150.0,          # Overtime shift cost (£150/shift) - 1.5× regular
    'q_plus': 200.0,      # Emergency staff cost (£200/shift) - most expensive
    'q_minus': 0.0,       # Cancellation cost (£0/shift)
    
    # ----- SOFT CONSTRAINT PENALTIES -----
    'c3': 5.0,            # Penalty for stand-alone working days
    'c4': 5.0,            # Penalty for unwanted shift patterns
    
    # ----- WORK RULES (Hard Constraints) -----
    'n1': 12,             # Max total shifts per nurse (12 shifts in 7 days = ~1.7/day)
    'n2': 5,              # Max night shifts per nurse
    'n3': 5,              # Min regular shifts per nurse (if working)
    'n4': 0,              # Min complete weekends off (disabled for 7-day period)
    
    # ----- OVERTIME ENFORCEMENT (Our Addition) -----
    'enforce_max_regular': True,  # ⭐ Force overtime for shifts > n3
    
    # ----- ADVANCED CONSTRAINTS -----
    'shift_quotas': {},            # No per-shift-type quotas
    'night_rest_enabled': False,   # Disable night rest rules for simplicity
    'min_consecutive_nights': 2,
    'days_off_after_nights': 2,
    'start_date': None,            # No weekend detection needed
    
    # ----- RECOURSE BOUNDS -----
    'max_emergency_staff': float('inf'),  # Unlimited emergency (default)
    'max_cancellations': float('inf'),    # Unlimited cancellations
    
    # ----- CVaR PARAMETERS (for SDM-CVaR model) -----
    'sigma': None,        # Not using CVaR constraint
    'mu': None,
}

# ============================================================================
# STEP 3: DEMAND ANALYSIS
# ============================================================================

print("\n" + "="*90)
print("DEMAND ANALYSIS")
print("="*90)

for scenario in [1, 2, 3]:
    scenario_data = scenarios_df[scenarios_df['scenario'] == scenario]
    total_demand = scenario_data['demand'].sum()
    avg_per_day = scenario_data.groupby('day')['demand'].sum().mean()
    print(f"\nScenario {scenario}:")
    print(f"  Total demand: {total_demand} shifts (over 7 days)")
    print(f"  Avg per day: {avg_per_day:.1f} nurses/day")
    print(f"  Breakdown: {scenario_data.groupby('shift')['demand'].sum().to_dict()}")

# ============================================================================
# STEP 4: CAPACITY ANALYSIS
# ============================================================================

print("\n" + "="*90)
print("CAPACITY ANALYSIS")
print("="*90)

num_nurses = len(nurses_list)
regular_capacity = num_nurses * params['n3']
total_capacity = num_nurses * params['n1']
overtime_capacity = total_capacity - regular_capacity

print(f"\nNurses: {num_nurses}")
print(f"Max shifts per nurse (n1): {params['n1']}")
print(f"Min regular shifts (n3): {params['n3']}")
print(f"\nCapacity Breakdown:")
print(f"  Regular capacity: {num_nurses} × {params['n3']} = {regular_capacity} shifts")
print(f"  Overtime capacity: {num_nurses} × ({params['n1']}-{params['n3']}) = {overtime_capacity} shifts")
print(f"  Total capacity: {total_capacity} shifts")

baseline_demand = scenarios_df[scenarios_df['scenario'] == 1]['demand'].sum()
print(f"\nBaseline demand (Scenario 1): {baseline_demand} shifts")
print(f"Utilization: {baseline_demand}/{total_capacity} = {baseline_demand/total_capacity*100:.1f}%")

if baseline_demand > regular_capacity:
    print(f"\n✅ Demand ({baseline_demand}) > Regular capacity ({regular_capacity})")
    print(f"   → Will use overtime or emergency to cover gap of {baseline_demand - regular_capacity} shifts")

# ============================================================================
# STEP 5: RUN OPTIMIZATION
# ============================================================================

print("\n" + "="*90)
print("RUNNING OPTIMIZATION")
print("="*90)

prob, status = build_and_solve_model(nurses_list, scenarios_df, params)

if status != "Optimal":
    print(f"\n❌ Optimization failed: {status}")
    exit()

# ============================================================================
# STEP 6: EXTRACT AND DISPLAY RESULTS
# ============================================================================

results = extract_results(prob, nurses_list, scenarios_df, params)
cost = results['cost_breakdown']
roster = results['roster_df']

print("\n" + "="*90)
print("RESULTS")
print("="*90)

print("\n💰 COST BREAKDOWN:")
print(f"  Regular shifts:   {cost['total_regular_shifts']:>3} × £{params['c1']:.0f} = £{cost['stage1_regular_cost']:>8,.2f}")
print(f"  Overtime shifts:  {cost['total_overtime_shifts']:>3} × £{params['c2']:.0f} = £{cost['stage1_overtime_cost']:>8,.2f}")
print(f"  Stage 1 subtotal:                      £{cost['stage1_cost']:>8,.2f}")
print(f"  Stage 2 recourse:                      £{cost['stage2_cost']:>8,.2f}")
print(f"  " + "-"*60)
print(f"  TOTAL COST:                            £{cost['total_cost']:>8,.2f}")

print(f"\n📊 SHIFT DISTRIBUTION:")
print(f"  Regular shifts:  {cost['total_regular_shifts']:>3} shifts")
print(f"  Overtime shifts: {cost['total_overtime_shifts']:>3} shifts {'✅' if cost['total_overtime_shifts'] > 0 else '⚠️'}")
print(f"  Stage 1 total:   {cost['total_regular_shifts'] + cost['total_overtime_shifts']:>3} shifts")

if cost['total_overtime_shifts'] > 0:
    print(f"\n  🎉 OVERTIME ACTIVATED!")
    print(f"     Each nurse does ≤{params['n3']} regular shifts")
    print(f"     Additional shifts classified as overtime")

print(f"\n📅 NURSE SCHEDULE:")
schedule_cols = ['Nurse', 'Total_Regular', 'Total_Overtime', 'Total_Shifts']
working_nurses = roster[roster['Total_Shifts'] > 0][schedule_cols].sort_values('Total_Shifts', ascending=False)
print(working_nurses.to_string(index=False))

overtime_nurses = working_nurses[working_nurses['Total_Overtime'] > 0]
if len(overtime_nurses) > 0:
    print(f"\n  Nurses with overtime:")
    for _, row in overtime_nurses.iterrows():
        print(f"    • {row['Nurse']}: {row['Total_Regular']} regular + {row['Total_Overtime']} overtime = {row['Total_Shifts']} total")

# ============================================================================
# STEP 7: EXPECTED OUTPUT (for validation)
# ============================================================================

print("\n" + "="*90)
print("EXPECTED OUTPUT (VALIDATION)")
print("="*90)

print(f"""
✅ EXPECTED RESULTS:

1. Cost Structure:
   - Regular shifts:  ~40 shifts (8 nurses × 5 regular = 40)
   - Overtime shifts: ~20-30 shifts (to cover demand gap)
   - Total Stage 1:   ~60-70 shifts
   - Emergency:       Some recourse for scenario variations

2. Nurse Schedule:
   - Each working nurse: EXACTLY 5 regular shifts (n3 enforced)
   - Some nurses: Additional overtime shifts (beyond n3)
   - Pattern: Mix of D and N shifts

3. Key Validation Points:
   ✓ Total regular ≤ {num_nurses} × {params['n3']} = {regular_capacity}
   ✓ Overtime > 0 (proves constraint 8b works)
   ✓ Total cost ≈ £9,000-£11,000
   ✓ No soft constraint violations (penalty = 0)

ACTUAL RESULTS FROM RUN:
   Regular:  {cost['total_regular_shifts']} shifts {'✅' if cost['total_regular_shifts'] <= regular_capacity else '❌'}
   Overtime: {cost['total_overtime_shifts']} shifts {'✅' if cost['total_overtime_shifts'] > 0 else '❌'}
   Total:    £{cost['total_cost']:,.2f}
""")

# ============================================================================
# STEP 8: COMPARISON WITH PAPER
# ============================================================================

print("\n" + "="*90)
print("COMPARISON WITH HE ET AL. (2019) PAPER")
print("="*90)

print("""
Paper's Case Study (Table 3, Section 5.1):
  - Nurses: Not specified exactly
  - Planning period: 4 weeks (28 days)
  - Shift types: 4 (E, D, L, N)
  - n1 = 24, n2 = 3, n3 = 16, n4 = 4
  - Overtime capacity: 24 - 16 = 8 shifts
  
Paper's Results (Table 4):
  - Regular shifts: 231
  - Overtime shifts: 25 ✅ (They got overtime!)
  
Our Test Instance:
  - Nurses: 8
  - Planning period: 7 days
  - Shift types: 2 (D, N)
  - n1 = 12, n2 = 5, n3 = 5, n4 = 0
  - Overtime capacity: 12 - 5 = 7 shifts
  - enforce_max_regular: True (our addition)
  
Our Results:
  - Regular shifts: {cost['total_regular_shifts']}
  - Overtime shifts: {cost['total_overtime_shifts']} {'✅' if cost['total_overtime_shifts'] > 0 else '❌'}

KEY DIFFERENCE:
  The paper doesn't explain HOW they got overtime to activate.
  We added 'enforce_max_regular' to force the distinction.
""")

print("\n" + "="*90)
print("TEST COMPLETE!")
print("="*90)
