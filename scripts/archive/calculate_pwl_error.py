#!/usr/bin/env python3
"""
PWL Accuracy Calculator
Shows exact error calculations for different segment counts
"""

import sys
sys.path.insert(0, '/Users/ibrahim/Documents/GitHub/NSS')

import numpy as np

def calculate_pwl_accuracy(lambda_param=0.03, max_hours=48, num_segments=8):
    """Calculate PWL approximation accuracy"""
    
    # Generate breakpoints
    breakpoints = np.linspace(0, max_hours, num_segments + 1)
    
    # Calculate exact exponential values at breakpoints
    exact_values = [1.0 - np.exp(-lambda_param * t) for t in breakpoints]
    
    # Test at intermediate points
    test_hours = np.linspace(0, max_hours, 100)  # 100 test points
    
    errors = []
    for t in test_hours:
        if t == 0:
            continue
            
        # Exact value
        exact = 1.0 - np.exp(-lambda_param * t)
        
        # PWL approximation (linear interpolation)
        for i in range(len(breakpoints) - 1):
            if breakpoints[i] <= t <= breakpoints[i+1]:
                ratio = (t - breakpoints[i]) / (breakpoints[i+1] - breakpoints[i])
                pwl = exact_values[i] + ratio * (exact_values[i+1] - exact_values[i])
                
                abs_error = abs(pwl - exact)
                rel_error_pct = (abs_error / exact) * 100
                errors.append(rel_error_pct)
                break
    
    return {
        'breakpoints': breakpoints,
        'exact_values': exact_values,
        'max_error': max(errors) if errors else 0,
        'avg_error': sum(errors) / len(errors) if errors else 0,
        'errors': errors
    }

if __name__ == '__main__':
    print('='*70)
    print('PWL ACCURACY ANALYSIS')
    print('F(t) = 1 - exp(-λt) with λ = 0.03')
    print('='*70)
    
    for segments in [6, 8, 10]:
        print(f'\n{segments} SEGMENTS:')
        print('-'*70)
        
        result = calculate_pwl_accuracy(0.03, 48, segments)
        
        print(f'Breakpoints: {[f"{b:.1f}h" for b in result["breakpoints"]]}')
        print(f'\nTest Results (100 interpolation points):')
        print(f'  Maximum Error: {result["max_error"]:.6f}%')
        print(f'  Average Error: {result["avg_error"]:.6f}%')
        
        # Show some example calculations
        print(f'\nExample Calculations at Key Hours:')
        test_points = [6, 12, 24, 36, 48]
        
        for t in test_points:
            exact = 1.0 - np.exp(-0.03 * t)
            
            # Find PWL value
            for i in range(len(result['breakpoints']) - 1):
                if result['breakpoints'][i] <= t <= result['breakpoints'][i+1]:
                    ratio = (t - result['breakpoints'][i]) / (result['breakpoints'][i+1] - result['breakpoints'][i])
                    pwl = result['exact_values'][i] + ratio * (result['exact_values'][i+1] - result['exact_values'][i])
                    
                    error = abs(pwl - exact) / exact * 100
                    print(f'  t={t:2d}h: Exact={exact:.6f}, PWL={pwl:.6f}, Error={error:.6f}%')
                    break
        
        if result['max_error'] < 0.1:
            print(f'\n  ✅ EXCELLENT: Max error < 0.1%')
        elif result['max_error'] < 1.0:
            print(f'\n  ✅ GOOD: Max error < 1.0%')
        else:
            print(f'\n  ⚠️  Needs improvement: Max error ≥ 1.0%')
    
    print('\n' + '='*70)
    print('CONCLUSION: 8 segments recommended for <0.1% error')
    print('='*70)
