"""
Comparison Test: With vs Without Fatigue
Tests the impact of enabling patient safety constraints
"""

from model import build_and_solve_model, extract_results, generate_sample_data, get_default_params

print('='*70)
print('FATIGUE COMPARISON TEST')
print('Testing impact of patient safety constraints')
print('='*70)

# Generate test data
print('\n1. Generating test data (5 nurses, 7 days, 3 scenarios)...')
nurses, scenarios = generate_sample_data(5, 7, 3)

# Test WITHOUT fatigue
print('\n2. Running baseline model (WITHOUT fatigue constraints)...')
params_baseline = get_default_params()
params_baseline['patient_safety_enabled'] = False

prob_baseline, status_baseline = build_and_solve_model(nurses, scenarios, params_baseline)
result_baseline = extract_results(prob_baseline, nurses, scenarios, params_baseline)

print(f'   Status: {status_baseline}')
print(f'   Total Cost: ${result_baseline["cost_breakdown"]["total_cost"]:.2f}')
print(f'   Solve Time: {result_baseline["solve_time"]:.2f} seconds')

# Test WITH fatigue
print('\n3. Running fatigue model (WITH patient safety constraints)...')
params_fatigue = get_default_params()
params_fatigue['patient_safety_enabled'] = True
params_fatigue['shift_duration'] = 12
params_fatigue['fatigue_lambda'] = 0.03
params_fatigue['max_fatigue_threshold'] = 0.70
params_fatigue['patient_safety_weight'] = 50.0

prob_fatigue, status_fatigue = build_and_solve_model(nurses, scenarios, params_fatigue)
result_fatigue = extract_results(prob_fatigue, nurses, scenarios, params_fatigue)

print(f'   Status: {status_fatigue}')
print(f'   Total Cost: ${result_fatigue["cost_breakdown"]["total_cost"]:.2f}')
print(f'   Solve Time: {result_fatigue["solve_time"]:.2f} seconds')

# Compare results
print(f'\n{"="*70}')
print('COMPARISON RESULTS')
print('='*70)

if status_baseline == "Optimal" and status_fatigue == "Optimal":
    cost_increase = result_fatigue["cost_breakdown"]["total_cost"] - result_baseline["cost_breakdown"]["total_cost"]
    cost_increase_pct = (cost_increase / result_baseline["cost_breakdown"]["total_cost"]) * 100
    
    print(f'\nCost Analysis:')
    print(f'  - Baseline Cost: ${result_baseline["cost_breakdown"]["total_cost"]:.2f}')
    print(f'  - Fatigue Cost: ${result_fatigue["cost_breakdown"]["total_cost"]:.2f}')
    print(f'  - Increase: ${cost_increase:.2f} ({cost_increase_pct:.2f}%)')
    
    if 'fatigue_metrics' in result_fatigue:
        fm = result_fatigue['fatigue_metrics']
        if fm.get('enabled'):
            print(f'\nFatigue Metrics:')
            print(f'  - Max Fatigue: {fm["max_fatigue"]:.3f} ({fm["max_fatigue"]*100:.1f}%)')
            print(f'  - Avg Fatigue: {fm["avg_fatigue"]:.3f} ({fm["avg_fatigue"]*100:.1f}%)')
            print(f'  - High Fatigue Days: {fm["high_fatigue_days"]}')
            print(f'  - Patient Safety Cost: ${fm["patient_safety_cost"]:.2f}')
    
    print(f'\nSolve Time:')
    print(f'  - Baseline: {result_baseline["solve_time"]:.2f}s')
    print(f'  - Fatigue: {result_fatigue["solve_time"]:.2f}s')
    print(f'  - Increase: {result_fatigue["solve_time"] - result_baseline["solve_time"]:.2f}s')
    
    # Validate expected behavior
    print(f'\nValidation:')
    if cost_increase > 0:
        print(f'  ✓ Cost increased (expected with safety constraints)')
    else:
        print(f'  ⚠ Cost did not increase (unexpected)')
    
    if cost_increase_pct < 10:
        print(f'  ✓ Cost increase < 10% (acceptable trade-off)')
    else:
        print(f'  ⚠ Cost increase > 10% (may need tuning)')
    
    print('\n✅ Comparison test completed successfully')
else:
    print('\n❌ One or both models failed to solve')
    print(f'  - Baseline: {result_baseline["status"]}')
    print(f'  - Fatigue: {result_fatigue["status"]}')

print('\n' + '='*70)
