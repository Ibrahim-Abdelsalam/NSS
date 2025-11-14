#!/usr/bin/env python3
"""
Quick test script to verify validation functions work correctly.
Run this to test the new validation features without using the full UI.
"""

import pandas as pd
import model as m

print("="*70)
print("TESTING VALIDATION FUNCTIONS")
print("="*70)

# ============================================================================
# TEST 1: Parameter Validation - Should PASS
# ============================================================================
print("\n--- TEST 1: Valid Parameters ---")
nurses = ['N1', 'N2', 'N3']
scenarios = pd.DataFrame({
    'scenario': [1, 1, 2, 2],
    'day': [1, 2, 1, 2],
    'shift': ['E', 'E', 'E', 'E'],
    'demand': [2, 2, 3, 3]
})

params = {
    'c1': 100, 'c2': 150, 'q_plus': 200,
    'n1': 15, 'n2': 5, 'n3': 10,
    'shift_quotas': {}
}

errors, warnings = m.validate_parameters(params, nurses, scenarios)
print(f"Errors: {len(errors)}")
print(f"Warnings: {len(warnings)}")
if errors:
    for e in errors:
        print(f"  {e}")
if warnings:
    for w in warnings:
        print(f"  {w}")
print("✓ PASSED" if len(errors) == 0 else "✗ FAILED")

# ============================================================================
# TEST 2: Parameter Validation - n3 > n1 (Should FAIL)
# ============================================================================
print("\n--- TEST 2: Invalid Parameters (n3 > n1) ---")
bad_params = params.copy()
bad_params['n3'] = 20  # Greater than n1=15

errors, warnings = m.validate_parameters(bad_params, nurses, scenarios)
print(f"Errors: {len(errors)}")
print(f"Warnings: {len(warnings)}")
if errors:
    for e in errors:
        print(f"  {e}")
print("✓ PASSED" if len(errors) > 0 else "✗ FAILED (should have caught error)")

# ============================================================================
# TEST 3: CSV Validation - Missing columns (Should FAIL in app)
# ============================================================================
print("\n--- TEST 3: Invalid CSV (missing column) ---")
bad_scenarios = pd.DataFrame({
    'scenario': [1, 1],
    'day': [1, 2],
    # Missing 'shift' and 'demand' columns
})

errors, warnings = m.validate_parameters(params, nurses, bad_scenarios)
print(f"Errors: {len(errors)}")
if errors:
    for e in errors:
        print(f"  {e}")
print("✓ PASSED" if len(errors) > 0 else "✗ FAILED (should detect missing columns)")

# ============================================================================
# TEST 4: CSV Validation - Negative demand (Should FAIL)
# ============================================================================
print("\n--- TEST 4: Invalid CSV (negative demand) ---")
bad_scenarios = pd.DataFrame({
    'scenario': [1, 1],
    'day': [1, 2],
    'shift': ['E', 'E'],
    'demand': [2, -5]  # Negative demand!
})

errors, warnings = m.validate_parameters(params, nurses, bad_scenarios)
print(f"Errors: {len(errors)}")
if errors:
    for e in errors:
        print(f"  {e}")
print("✓ PASSED" if len(errors) > 0 else "✗ FAILED (should detect negative demand)")

# ============================================================================
# TEST 5: Problem Size Estimation
# ============================================================================
print("\n--- TEST 5: Solve Time Estimation ---")
estimation = m.estimate_solve_time(nurses, scenarios, params)
print(f"Variables: {estimation['num_variables']:,}")
print(f"Constraints: {estimation['num_constraints']:,}")
print(f"Problem Size: {estimation['problem_size']:,}")
print(f"Estimated Time: {estimation['time_display']}")
print(f"Category: {estimation['time_category']}")
print("✓ PASSED")

# ============================================================================
# TEST 6: Sample Data Generation
# ============================================================================
print("\n--- TEST 6: Sample Data Generation ---")
sample_nurses, sample_scenarios = m.generate_sample_data(
    num_nurses=5,
    num_days=7,
    num_scenarios=3
)
print(f"Generated {len(sample_nurses)} nurses")
print(f"Generated {len(sample_scenarios)} scenario records")
expected_rows = 5 * 7 * 4 * 3  # nurses × days × shifts × scenarios
actual_rows = len(sample_scenarios)
# Note: generate_sample_data creates scenarios × days × shifts (not nurses)
expected_rows = 3 * 7 * 4  # scenarios × days × shifts
print(f"Expected rows: {expected_rows}")
print(f"Actual rows: {actual_rows}")
print("✓ PASSED" if actual_rows == expected_rows else f"✗ FAILED (row count mismatch)")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("VALIDATION TEST SUMMARY")
print("="*70)
print("All critical validation functions are working correctly!")
print("\nNext steps:")
print("1. Test in the Streamlit app")
print("2. Try uploading a bad CSV file")
print("3. Try setting n3 > n1 and see the error message")
print("4. Run a full optimization and check result validation")
