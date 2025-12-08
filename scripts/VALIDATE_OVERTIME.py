"""
COMPREHENSIVE VALIDATION TEST

This test validates the overtime fix across multiple scenarios.
"""

import pandas as pd
from model import build_and_solve_model, extract_results

# Load test data
nurses_df = pd.read_csv('data/test_overtime_nurses.csv')
scenarios_df = pd.read_csv('data/test_overtime_scenarios.csv')
nurses_list = nurses_df['nurse_id'].tolist()

print("=" * 90)
print("COMPREHENSIVE OVERTIME VALIDATION")
print("=" * 90)

test_cases = [
    {
        'name': 'Default Mode (Paper-Compliant)',
        'params': {
            'c1': 100, 'c2': 150, 'q_plus': 200, 'q_minus': 0,
            'n1': 15, 'n2': 10, 'n3': 5, 'n4': 0,
            'enforce_max_regular': False,
            'shift_quotas': {}, 'night_rest_enabled': False, 'start_date': None,
        },
        'expected_overtime': False,
        'reason': 'Model prefers cheap regular shifts over overtime'
    },
    {
        'name': 'Overtime Enforced (Practical Mode)',
        'params': {
            'c1': 100, 'c2': 150, 'q_plus': 200, 'q_minus': 0,
            'n1': 15, 'n2': 10, 'n3': 5, 'n4': 0,
            'enforce_max_regular': True,  # ⭐
            'shift_quotas': {}, 'night_rest_enabled': False, 'start_date': None,
        },
        'expected_overtime': True,
        'reason': 'Regular shifts capped at n3=5, forcing overtime'
    },
    {
        'name': 'Low n3 with Enforcement',
        'params': {
            'c1': 100, 'c2': 150, 'q_plus': 200, 'q_minus': 0,
            'n1': 15, 'n2': 10, 'n3': 3, 'n4': 0,
            'enforce_max_regular': True,  # ⭐
            'shift_quotas': {}, 'night_rest_enabled': False, 'start_date': None,
        },
        'expected_overtime': True,
        'reason': 'Only 3 regular shifts allowed, more overtime capacity'
    },
    {
        'name': 'High n3 with Enforcement',
        'params': {
            'c1': 100, 'c2': 150, 'q_plus': 200, 'q_minus': 0,
            'n1': 15, 'n2': 10, 'n3': 10, 'n4': 0,
            'enforce_max_regular': True,  # ⭐
            'shift_quotas': {}, 'night_rest_enabled': False, 'start_date': None,
        },
        'expected_overtime': True,
        'reason': 'High commitment but still allows some overtime'
    },
]

results_summary = []

for test in test_cases:
    print(f"\n{'=' * 90}")
    print(f"TEST: {test['name']}")
    print(f"{'=' * 90}")
    print(f"Reason: {test['reason']}")
    print(f"Parameters: n1={test['params']['n1']}, n3={test['params']['n3']}, "
          f"enforce_max_regular={test['params']['enforce_max_regular']}")
    
    prob, status = build_and_solve_model(nurses_list, scenarios_df, test['params'])
    
    if status == "Optimal":
        res = extract_results(prob, nurses_list, scenarios_df, test['params'])
        cost = res['cost_breakdown']
        
        regular = cost['total_regular_shifts']
        overtime = cost['total_overtime_shifts']
        total_stage1 = regular + overtime
        total_cost = cost['total_cost']
        
        has_overtime = overtime > 0
        test_passed = has_overtime == test['expected_overtime']
        
        print(f"\nResults:")
        print(f"  Regular:  {regular:>3} shifts")
        print(f"  Overtime: {overtime:>3} shifts {'✅' if has_overtime else '⚠️ '}")
        print(f"  Stage 1:  {total_stage1:>3} total")
        print(f"  Cost:     £{total_cost:,.2f}")
        print(f"\n  Expected overtime: {test['expected_overtime']}")
        print(f"  Got overtime: {has_overtime}")
        print(f"  Status: {'✅ PASS' if test_passed else '❌ FAIL'}")
        
        results_summary.append({
            'test': test['name'],
            'regular': regular,
            'overtime': overtime,
            'expected_ot': test['expected_overtime'],
            'got_ot': has_overtime,
            'passed': test_passed
        })
    else:
        print(f"  ❌ Status: {status}")
        results_summary.append({
            'test': test['name'],
            'regular': 0,
            'overtime': 0,
            'expected_ot': test['expected_overtime'],
            'got_ot': False,
            'passed': False
        })

print(f"\n{'=' * 90}")
print("SUMMARY")
print(f"{'=' * 90}")
print(f"\n{'Test':<40} {'Regular':>8} {'Overtime':>8} {'Expected':>10} {'Result':>8}")
print(f"{'-'*90}")
for r in results_summary:
    status_symbol = '✅' if r['passed'] else '❌'
    expected_str = 'Yes' if r['expected_ot'] else 'No'
    got_str = 'Yes' if r['got_ot'] else 'No'
    print(f"{r['test']:<40} {r['regular']:>8} {r['overtime']:>8} {expected_str:>10} {got_str:>8} {status_symbol}")

all_passed = all(r['passed'] for r in results_summary)
print(f"\n{'=' * 90}")
if all_passed:
    print("✅✅✅ ALL TESTS PASSED! ✅✅✅")
    print("\nOvertime functionality is working correctly!")
    print("The model now supports both modes:")
    print("  • enforce_max_regular=False: Paper-compliant (no overtime)")
    print("  • enforce_max_regular=True: Practical mode (overtime activated)")
else:
    print("❌ SOME TESTS FAILED")
    failed = [r for r in results_summary if not r['passed']]
    print(f"\nFailed tests: {[r['test'] for r in failed]}")
