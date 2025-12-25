#!/usr/bin/env python3
"""
Phase 3 Testing Suite
Runs all validation tests for PWL fatigue implementation
"""

import sys
import os
sys.path.insert(0, '/Users/ibrahim/Documents/GitHub/NSS')

from datetime import datetime
import traceback

print('='*70)
print('PHASE 3: TESTING & VALIDATION')
print('Comprehensive Test Suite for PWL Fatigue Implementation')
print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)

# Track results
test_results = []

def run_test(test_name, test_file):
    """Run a test file and capture results"""
    print(f'\n{"="*70}')
    print(f'TEST: {test_name}')
    print('='*70)
    
    try:
        # Execute test file
        with open(test_file, 'r') as f:
            code = f.read()
        
        # Create a clean namespace for execution
        namespace = {'__name__': '__main__'}
        exec(code, namespace)
        
        print(f'\n✅ {test_name} PASSED')
        test_results.append({'name': test_name, 'status': 'PASSED', 'error': None})
        return True
        
    except Exception as e:
        print(f'\n❌ {test_name} FAILED')
        print(f'Error: {e}')
        print('\nTraceback:')
        traceback.print_exc()
        test_results.append({'name': test_name, 'status': 'FAILED', 'error': str(e)})
        return False

# Test 1: Syntax and Imports
print('\n' + '='*70)
print('TEST 1: Syntax and Imports Validation')
print('='*70)
try:
    print('Importing model module...')
    from model import (
        build_and_solve_model, 
        generate_sample_data, 
        get_default_params,
        create_pwl_fatigue_approximation,
        extract_results
    )
    print('✅ All imports successful')
    
    print('\nChecking default parameters...')
    params = get_default_params()
    required = ['patient_safety_enabled', 'patient_safety_weight', 
                'fatigue_lambda', 'max_fatigue_threshold', 'shift_duration']
    
    for param in required:
        assert param in params, f"Missing parameter: {param}"
        print(f'  ✓ {param}: {params[param]}')
    
    print('\n✅ TEST 1 PASSED: Syntax and Imports')
    test_results.append({'name': 'Syntax and Imports', 'status': 'PASSED', 'error': None})
    
except Exception as e:
    print(f'\n❌ TEST 1 FAILED: {e}')
    traceback.print_exc()
    test_results.append({'name': 'Syntax and Imports', 'status': 'FAILED', 'error': str(e)})
    sys.exit(1)

# Test 2: PWL Accuracy Validation
print('\n' + '='*70)
print('TEST 2: PWL Accuracy Calculation')
print('='*70)
try:
    import numpy as np
    
    # Test 8 segments
    breakpoints, slopes, exact_values = create_pwl_fatigue_approximation(0.03, 48, 8)
    
    print(f'Breakpoints: {len(breakpoints)} points')
    print(f'Segments: {len(slopes)}')
    print(f'Max fatigue value: {exact_values[-1]:.4f}')
    
    # Calculate error at test points
    test_hours = [6, 12, 24, 36, 48]
    errors = []
    
    print('\nAccuracy at key hours:')
    for t in test_hours:
        exact = 1 - np.exp(-0.03 * t)
        
        # Find PWL value
        for i in range(len(breakpoints) - 1):
            if breakpoints[i] <= t <= breakpoints[i+1]:
                ratio = (t - breakpoints[i]) / (breakpoints[i+1] - breakpoints[i])
                pwl = exact_values[i] + ratio * (exact_values[i+1] - exact_values[i])
                
                error = abs(pwl - exact) / exact * 100
                errors.append(error)
                print(f'  t={t:2d}h: Error={error:.3f}%')
                break
    
    max_error = max(errors)
    avg_error = sum(errors) / len(errors)
    
    print(f'\nMax Error: {max_error:.3f}%')
    print(f'Avg Error: {avg_error:.3f}%')
    
    assert max_error < 2.0, f"Error too high: {max_error:.3f}%"
    
    print('\n✅ TEST 2 PASSED: PWL Accuracy within acceptable range')
    test_results.append({'name': 'PWL Accuracy', 'status': 'PASSED', 'error': None})
    
except Exception as e:
    print(f'\n❌ TEST 2 FAILED: {e}')
    traceback.print_exc()
    test_results.append({'name': 'PWL Accuracy', 'status': 'FAILED', 'error': str(e)})

# Test 3: Small Instance (5x7x3)
print('\n' + '='*70)
print('TEST 3: Small Instance (5 nurses × 7 days × 3 scenarios)')
print('='*70)
try:
    print('Generating test data...')
    nurses, scenarios = generate_sample_data(5, 7, 3)
    
    print('Configuring model with fatigue...')
    params = get_default_params()
    params['patient_safety_enabled'] = True
    params['shift_duration'] = 12
    
    print('Solving model...')
    result = build_and_solve_model(nurses, scenarios, params)
    
    print(f'\nStatus: {result["status"]}')
    print(f'Total Cost: ${result["total_cost"]:.2f}')
    print(f'Solve Time: {result["solve_time"]:.2f}s')
    
    assert result["status"] == "Optimal", f"Expected Optimal, got {result['status']}"
    assert result["solve_time"] < 120, f"Solve time too long: {result['solve_time']:.2f}s"
    
    if 'fatigue_metrics' in result and result['fatigue_metrics'].get('enabled'):
        fm = result['fatigue_metrics']
        print(f'\nFatigue Metrics:')
        print(f'  Max: {fm["max_fatigue"]:.3f}')
        print(f'  Avg: {fm["avg_fatigue"]:.3f}')
        
        assert fm["max_fatigue"] <= 0.70, f"Max fatigue exceeds threshold: {fm['max_fatigue']:.3f}"
    
    print('\n✅ TEST 3 PASSED: Small instance solved optimally')
    test_results.append({'name': 'Small Instance (5×7×3)', 'status': 'PASSED', 'error': None})
    
except Exception as e:
    print(f'\n❌ TEST 3 FAILED: {e}')
    traceback.print_exc()
    test_results.append({'name': 'Small Instance (5×7×3)', 'status': 'FAILED', 'error': str(e)})

# Test 4: Medium Instance (10x14x5)
print('\n' + '='*70)
print('TEST 4: Medium Instance (10 nurses × 14 days × 5 scenarios)')
print('='*70)
try:
    print('Generating test data...')
    nurses, scenarios = generate_sample_data(10, 14, 5)
    
    print('Configuring model with fatigue...')
    params = get_default_params()
    params['patient_safety_enabled'] = True
    params['shift_duration'] = 12
    
    print('Solving model (may take 1-3 minutes)...')
    result = build_and_solve_model(nurses, scenarios, params)
    
    print(f'\nStatus: {result["status"]}')
    print(f'Total Cost: ${result["total_cost"]:.2f}')
    print(f'Solve Time: {result["solve_time"]:.2f}s ({result["solve_time"]/60:.2f} min)')
    
    assert result["status"] == "Optimal", f"Expected Optimal, got {result['status']}"
    assert result["solve_time"] < 600, f"Solve time too long: {result['solve_time']:.2f}s"
    
    if 'fatigue_metrics' in result and result['fatigue_metrics'].get('enabled'):
        fm = result['fatigue_metrics']
        print(f'\nFatigue Metrics:')
        print(f'  Max: {fm["max_fatigue"]:.3f}')
        print(f'  Avg: {fm["avg_fatigue"]:.3f}')
        print(f'  High-risk days: {fm["high_fatigue_days"]}')
        
        assert fm["max_fatigue"] <= 0.70, f"Max fatigue exceeds threshold: {fm['max_fatigue']:.3f}"
        
        # Expected range from checklist
        if 0.60 <= fm["max_fatigue"] <= 0.68:
            print(f'  ✓ Max fatigue within expected range [0.60, 0.68]')
    
    print('\n✅ TEST 4 PASSED: Medium instance solved optimally')
    test_results.append({'name': 'Medium Instance (10×14×5)', 'status': 'PASSED', 'error': None})
    
except Exception as e:
    print(f'\n❌ TEST 4 FAILED: {e}')
    traceback.print_exc()
    test_results.append({'name': 'Medium Instance (10×14×5)', 'status': 'FAILED', 'error': str(e)})

# Test 5: Baseline Comparison
print('\n' + '='*70)
print('TEST 5: Baseline vs Fatigue Comparison')
print('='*70)
try:
    print('Generating test data...')
    nurses, scenarios = generate_sample_data(5, 7, 3)
    
    # Baseline (no fatigue)
    print('\nRunning baseline model (no fatigue)...')
    params_baseline = get_default_params()
    params_baseline['patient_safety_enabled'] = False
    result_baseline = build_and_solve_model(nurses, scenarios, params_baseline)
    
    # With fatigue
    print('Running fatigue model...')
    params_fatigue = get_default_params()
    params_fatigue['patient_safety_enabled'] = True
    params_fatigue['shift_duration'] = 12
    result_fatigue = build_and_solve_model(nurses, scenarios, params_fatigue)
    
    print(f'\nBaseline Cost: ${result_baseline["total_cost"]:.2f}')
    print(f'Fatigue Cost:  ${result_fatigue["total_cost"]:.2f}')
    
    cost_increase = result_fatigue["total_cost"] - result_baseline["total_cost"]
    cost_increase_pct = (cost_increase / result_baseline["total_cost"]) * 100
    
    print(f'Cost Increase: ${cost_increase:.2f} ({cost_increase_pct:.2f}%)')
    
    assert cost_increase >= 0, "Fatigue model should not decrease cost"
    
    if cost_increase_pct < 10:
        print(f'✓ Cost increase acceptable (<10%)')
    
    print('\n✅ TEST 5 PASSED: Comparison completed successfully')
    test_results.append({'name': 'Baseline Comparison', 'status': 'PASSED', 'error': None})
    
except Exception as e:
    print(f'\n❌ TEST 5 FAILED: {e}')
    traceback.print_exc()
    test_results.append({'name': 'Baseline Comparison', 'status': 'FAILED', 'error': str(e)})

# Final Summary
print('\n' + '='*70)
print('TEST SUMMARY')
print('='*70)

passed = sum(1 for r in test_results if r['status'] == 'PASSED')
failed = sum(1 for r in test_results if r['status'] == 'FAILED')
total = len(test_results)

print(f'\nTotal Tests: {total}')
print(f'Passed: {passed} ✅')
print(f'Failed: {failed} {"❌" if failed > 0 else ""}')

print('\nDetailed Results:')
for i, result in enumerate(test_results, 1):
    status_icon = '✅' if result['status'] == 'PASSED' else '❌'
    print(f'{i}. {status_icon} {result["name"]}: {result["status"]}')
    if result['error']:
        print(f'   Error: {result["error"]}')

print('\n' + '='*70)
if failed == 0:
    print('🎉 ALL TESTS PASSED!')
    print('Phase 3 Testing Complete - Ready for Phase 4 (Parameter Tuning)')
else:
    print(f'⚠️  {failed} TEST(S) FAILED')
    print('Review errors above and fix before proceeding')

print('='*70)
print(f'Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)
