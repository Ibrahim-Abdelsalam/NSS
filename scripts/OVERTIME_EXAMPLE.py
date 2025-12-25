"""
OVERTIME ACTIVATION - WORKING EXAMPLE

This demonstrates how to activate overtime in the nurse scheduling model.

KEY INSIGHT:
The paper by He et al. (2019) does not explicitly cap regular shifts at n3.
However, in practice, "overtime" means shifts BEYOND the regular minimum.

Solution: Use the optional 'enforce_max_regular' parameter to cap regular
shifts at n3, forcing additional shifts to be classified as overtime.
"""

import pandas as pd
from model import build_and_solve_model, extract_results

# Load test data (8 nurses, 14 days, 2 shifts/day)
nurses_df = pd.read_csv('data/test_overtime_nurses.csv')
scenarios_df = pd.read_csv('data/test_overtime_scenarios.csv')
nurses_list = nurses_df['nurse_id'].tolist()

print("=" * 80)
print("OVERTIME ACTIVATION EXAMPLE")
print("=" * 80)

# Test 1: WITHOUT enforce_max_regular (original behavior)
print("\n" + "="*80)
print("TEST 1: WITHOUT enforce_max_regular (original model)")
print("="*80)

params_no_enforce = {
    'c1': 100,
    'c2': 150,
    'q_plus': 200,
    'q_minus': 0,
    
    'n1': 15,
    'n3': 5,
    'n2': 10,
    'n4': 0,
    
    'enforce_max_regular': False,  # Original behavior
    
    'shift_quotas': {},
    'night_rest_enabled': False,
    'start_date': None,
}

prob, status = build_and_solve_model(nurses_list, scenarios_df, params_no_enforce)

if status == "Optimal":
    results = extract_results(prob, nurses_list, scenarios_df, params_no_enforce)
    cost = results['cost_breakdown']
    
    print(f"\nResults:")
    print(f"  Regular shifts:  {cost['total_regular_shifts']}")
    print(f"  Overtime shifts: {cost['total_overtime_shifts']}")
    print(f"  Total cost: £{cost['total_cost']:,.2f}")
    print(f"\n  → Model treats all Stage 1 shifts as 'regular' (cheaper)")

# Test 2: WITH enforce_max_regular (forces overtime)
print("\n" + "="*80)
print("TEST 2: WITH enforce_max_regular=True (forces overtime)")
print("="*80)

params_with_enforce = {
    'c1': 100,
    'c2': 150,
    'q_plus': 200,
    'q_minus': 0,
    
    'n1': 15,
    'n3': 5,  # First 5 shifts are regular, rest are overtime
    'n2': 10,
    'n4': 0,
    
    'enforce_max_regular': True,  # ⭐ Force overtime for shifts > n3
    
    'shift_quotas': {},
    'night_rest_enabled': False,
    'start_date': None,
}

prob, status = build_and_solve_model(nurses_list, scenarios_df, params_with_enforce)

if status == "Optimal":
    results = extract_results(prob, nurses_list, scenarios_df, params_with_enforce)
    cost = results['cost_breakdown']
    
    print(f"\nResults:")
    print(f"  Regular shifts:  {cost['total_regular_shifts']} (≤ {params_with_enforce['n3']} × {len(nurses_list)} nurses = {params_with_enforce['n3'] * len(nurses_list)})")
    print(f"  Overtime shifts: {cost['total_overtime_shifts']} ⭐")
    print(f"  Total Stage 1:   {cost['total_regular_shifts'] + cost['total_overtime_shifts']}")
    print(f"  Total cost: £{cost['total_cost']:,.2f}")
    
    roster = results['roster_df'][['Nurse', 'Total_Regular', 'Total_Overtime', 'Total_Shifts']]
    roster = roster[roster['Total_Shifts'] > 0].sort_values('Total_Shifts', ascending=False)
    
    print(f"\n  Nurse Schedule:")
    for _, row in roster.head(3).iterrows():
        print(f"    {row['Nurse']}: {row['Total_Regular']} regular + {row['Total_Overtime']} overtime = {row['Total_Shifts']} total")
    
    print(f"\n  ✅ Overtime activated! Each nurse does ≤{params_with_enforce['n3']} regular shifts")
    print(f"     Any additional shifts are classified as overtime (£{params_with_enforce['c2']} vs £{params_with_enforce['c1']})")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("""
The model has two modes:

1. WITHOUT enforce_max_regular (default, per paper):
   - Minimizes cost by using cheap regular shifts (c1)
   - Overtime variable exists but is economically inferior
   - Mathematically correct per He et al. (2019)

2. WITH enforce_max_regular=True:
   - Caps regular shifts at n3 per nurse
   - Forces shifts beyond n3 to use overtime (c2)  
   - Matches practical interpretation: "first n3 are regular, rest overtime"
   
To activate overtime in Streamlit:
   • Add 'enforce_max_regular': True to your parameters
   • Set n3 < (average shifts needed per nurse)
   • Model will schedule n3 regular + overtime for extra shifts
""")
