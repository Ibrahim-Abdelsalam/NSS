"""
Medium Instance Test: 10 nurses × 14 days × 5 scenarios
Tests realistic hospital ward scheduling with fatigue constraints
"""

from model import build_and_solve_model, generate_sample_data, get_default_params
import time

print('='*70)
print('MEDIUM INSTANCE TEST')
print('Hospital Ward: 10 nurses × 14 days × 5 demand scenarios')
print('='*70)

# Generate realistic medium-sized dataset
print('\n1. Generating test data...')
nurses, scenarios = generate_sample_data(10, 14, 5)
print(f'   ✓ {len(nurses)} nurses')
print(f'   ✓ {len(scenarios)} scenario-day-shift combinations')
print(f'   ✓ {len(scenarios["scenario"].unique())} scenarios')

# Configure with fatigue enabled
print('\n2. Configuring model with fatigue...')
params = get_default_params()
params['patient_safety_enabled'] = True
params['shift_duration'] = 12
params['fatigue_lambda'] = 0.03
params['max_fatigue_threshold'] = 0.70
params['patient_safety_weight'] = 50.0

print(f'   ✓ Patient Safety: ENABLED')
print(f'   ✓ Shift Duration: {params["shift_duration"]} hours')
print(f'   ✓ Lambda (λ): {params["fatigue_lambda"]}')
print(f'   ✓ Max Threshold: {params["max_fatigue_threshold"]} (70%)')
print(f'   ✓ Cost Weight: ${params["patient_safety_weight"]}/fatigue unit')

# Solve model
print('\n3. Building and solving optimization model...')
print('   (Expected solve time: 1-3 minutes with PWL constraints)')
start_time = time.time()

try:
    result = build_and_solve_model(nurses, scenarios, params)
    solve_time = time.time() - start_time
    
    print(f'\n{"="*70}')
    print('RESULTS')
    print('='*70)
    print(f'Status: {result["status"]}')
    print(f'Solve Time: {solve_time:.2f} seconds ({solve_time/60:.1f} minutes)')
    
    if result["status"] == "Optimal":
        print(f'\n📊 Cost Breakdown:')
        print(f'   Total Cost:          ${result["total_cost"]:,.2f}')
        if 'stage1_cost' in result:
            print(f'   - Stage 1 (wages):   ${result["stage1_cost"]:,.2f}')
            print(f'   - Stage 2 (recourse):${result["stage2_cost"]:,.2f}')
        if 'patient_safety_cost' in result:
            print(f'   - Patient Safety:    ${result["patient_safety_cost"]:,.2f}')
            pct = (result["patient_safety_cost"] / result["total_cost"]) * 100
            print(f'     ({pct:.1f}% of total cost)')
        
        if 'fatigue_metrics' in result and result['fatigue_metrics'].get('enabled'):
            fm = result['fatigue_metrics']
            print(f'\n😊 Fatigue Analysis:')
            print(f'   Max Fatigue:         {fm["max_fatigue"]:.3f} ({fm["max_fatigue"]*100:.1f}%)')
            print(f'   Avg Fatigue:         {fm["avg_fatigue"]:.3f} ({fm["avg_fatigue"]*100:.1f}%)')
            print(f'   High-Risk Days:      {fm["high_fatigue_days"]} (F > {fm["high_fatigue_threshold"]})')
            print(f'   Max Work Hours:      {fm["max_work_hours"]:.1f} hours')
            print(f'   Avg Work Hours:      {fm["avg_work_hours"]:.1f} hours')
            
            # Validation checks
            print(f'\n✅ Validation Checks:')
            if fm["max_fatigue"] <= params["max_fatigue_threshold"]:
                print(f'   ✓ Max fatigue within threshold ({fm["max_fatigue"]:.2f} ≤ {params["max_fatigue_threshold"]})')
            else:
                print(f'   ✗ Max fatigue EXCEEDS threshold! ({fm["max_fatigue"]:.2f} > {params["max_fatigue_threshold"]})')
            
            if fm["avg_fatigue"] < 0.50:
                print(f'   ✓ Average fatigue reasonable ({fm["avg_fatigue"]:.2f} < 0.50)')
            else:
                print(f'   ⚠ Average fatigue high ({fm["avg_fatigue"]:.2f} ≥ 0.50)')
            
            if solve_time < 300:  # 5 minutes
                print(f'   ✓ Solve time acceptable ({solve_time:.1f}s < 300s)')
            else:
                print(f'   ⚠ Solve time long ({solve_time:.1f}s ≥ 300s)')
        
        # Expected values check (from checklist)
        print(f'\n📋 Expected vs Actual (from Implementation Checklist):')
        print(f'   Expected Solve Time: < 5 minutes')
        print(f'   Actual Solve Time:   {solve_time/60:.2f} minutes')
        
        print(f'\n   Expected Max Fatigue: 0.60-0.68')
        if 'fatigue_metrics' in result:
            actual_max = result['fatigue_metrics'].get('max_fatigue', 0)
            print(f'   Actual Max Fatigue:   {actual_max:.3f}')
            if 0.60 <= actual_max <= 0.68:
                print(f'   ✓ Within expected range!')
        
        print(f'\n✅ TEST PASSED: Medium instance solved successfully')
        print(f'✅ Model ready for parameter tuning and statistical validation')
        
    else:
        print(f'\n❌ TEST FAILED: Model did not solve optimally')
        print(f'Status: {result["status"]}')
        
except Exception as e:
    print(f'\n❌ ERROR during model execution:')
    print(f'{e}')
    import traceback
    traceback.print_exc()

print('\n' + '='*70)
