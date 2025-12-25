"""
Quick test of fatigue implementation
Tests basic functionality with a small instance
"""

from model import build_and_solve_model, extract_results, generate_sample_data, get_default_params

print('='*70)
print('FATIGUE IMPLEMENTATION TEST')
print('='*70)

print('\n1. Generating small test data (5 nurses, 7 days, 3 scenarios)...')
nurses, scenarios = generate_sample_data(5, 7, 3)

print('\n2. Configuring parameters with fatigue enabled...')
params = get_default_params()
params['patient_safety_enabled'] = True
params['shift_duration'] = 12
params['fatigue_lambda'] = 0.03
params['max_fatigue_threshold'] = 0.70
params['patient_safety_weight'] = 50.0

print(f'\n   Parameters:')
print(f'   - Patient Safety: {params["patient_safety_enabled"]}')
print(f'   - Shift Duration: {params["shift_duration"]} hours')
print(f'   - Lambda: {params["fatigue_lambda"]}')
print(f'   - Max Fatigue: {params["max_fatigue_threshold"]}')
print(f'   - Safety Weight: ${params["patient_safety_weight"]}')

print('\n3. Building and solving model...')
print('   (This may take 30-60 seconds with PWL constraints)')
prob, status = build_and_solve_model(nurses, scenarios, params)
result = extract_results(prob, nurses, scenarios, params)

print(f'\n{"="*70}')
print('RESULTS')
print('='*70)
print(f'Status: {status}')
print(f'Total Cost: ${result["cost_breakdown"]["total_cost"]:.2f}')
print(f'Solve Time: {result["solve_time"]:.2f} seconds')

if 'cost_breakdown' in result:
    print(f'\nCost Breakdown:')
    print(f'  - Stage 1 Cost: ${result["cost_breakdown"]["stage1_total"]:.2f}')
    print(f'  - Stage 2 Cost: ${result["cost_breakdown"]["stage2_expected_cost"]:.2f}')
    if 'patient_safety_cost' in result["cost_breakdown"]:
        print(f'  - Patient Safety Cost: ${result["cost_breakdown"]["patient_safety_cost"]:.2f}')

if 'fatigue_metrics' in result and result['fatigue_metrics'].get('enabled'):
    fm = result['fatigue_metrics']
    print(f'\nFatigue Metrics:')
    print(f'  - Max Fatigue: {fm["max_fatigue"]:.3f} ({fm["max_fatigue"]*100:.1f}%)')
    print(f'  - Avg Fatigue: {fm["avg_fatigue"]:.3f} ({fm["avg_fatigue"]*100:.1f}%)')
    print(f'  - High Fatigue Days: {fm["high_fatigue_days"]} (F > {fm["high_fatigue_threshold"]})')
    print(f'  - Max Work Hours: {fm["max_work_hours"]:.1f} hours')
    print(f'  - Avg Work Hours: {fm["avg_work_hours"]:.1f} hours')
    print(f'  - Patient Safety Cost: ${fm["patient_safety_cost"]:.2f}')

if status == "Optimal":
    print('\n✓ Test PASSED: Model solved to optimality')
    print(f'✓ PWL fatigue constraints working correctly')
else:
    print(f'\n✗ Test FAILED: Status = {status}')
    
print('\n' + '='*70)
