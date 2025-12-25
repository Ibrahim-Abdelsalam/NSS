"""
Test script to verify PWL approximation accuracy for fatigue model.

This script validates that our piecewise linear approximation achieves <1% error
compared to the exact exponential fatigue function F(t) = 1 - e^(-λt).
"""

import numpy as np
import matplotlib.pyplot as plt
from model import create_pwl_fatigue_approximation


def test_pwl_accuracy():
    """Test PWL approximation accuracy at various time points."""
    
    # Parameters from Jaber et al. (2013) Table 5
    lambda_param = 0.03  # Medium fatigue rate
    max_hours = 48       # 4 consecutive 12-hour shifts
    num_segments = 6     # Default configuration
    
    print("=" * 70)
    print("PWL FATIGUE APPROXIMATION ACCURACY TEST")
    print("=" * 70)
    print(f"\nParameters:")
    print(f"  λ (lambda):      {lambda_param}")
    print(f"  Max hours:       {max_hours}")
    print(f"  PWL segments:    {num_segments}")
    
    # Generate PWL approximation
    breakpoints, slopes, exact_values = create_pwl_fatigue_approximation(
        lambda_param, max_hours, num_segments
    )
    
    print(f"\nBreakpoints (hours): {[f'{b:.1f}' for b in breakpoints]}")
    print(f"\nExact F(t) values:")
    for i, (t, f) in enumerate(zip(breakpoints, exact_values)):
        print(f"  t={t:5.1f}h → F(t)={f:.4f}")
    
    # Test accuracy at intermediate points
    print("\n" + "=" * 70)
    print("ACCURACY VERIFICATION AT TEST POINTS")
    print("=" * 70)
    print(f"{'Hours':>8} | {'Exact F(t)':>12} | {'PWL F(t)':>12} | {'Error %':>10}")
    print("-" * 70)
    
    test_points = [6, 12, 18, 24, 30, 36, 42]  # Test at shift boundaries
    max_error = 0.0
    
    for t_test in test_points:
        # Exact exponential value
        exact = 1.0 - np.exp(-lambda_param * t_test)
        
        # PWL approximation: find which segment t_test falls into
        pwl_value = 0.0
        for i in range(len(breakpoints) - 1):
            if breakpoints[i] <= t_test <= breakpoints[i + 1]:
                # Linear interpolation between breakpoints i and i+1
                t0, t1 = breakpoints[i], breakpoints[i + 1]
                f0, f1 = exact_values[i], exact_values[i + 1]
                weight = (t_test - t0) / (t1 - t0)
                pwl_value = f0 + weight * (f1 - f0)
                break
        
        # Calculate error
        error_pct = abs(exact - pwl_value) / exact * 100 if exact > 0 else 0
        max_error = max(max_error, error_pct)
        
        print(f"{t_test:8.1f} | {exact:12.4f} | {pwl_value:12.4f} | {error_pct:9.2f}%")
    
    print("-" * 70)
    print(f"Maximum error: {max_error:.2f}%")
    
    if max_error < 1.0:
        print("\n✅ SUCCESS: PWL achieves <1% error target!")
    else:
        print(f"\n⚠️  WARNING: PWL error {max_error:.2f}% exceeds 1% target")
    
    # Visualization
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATION...")
    print("=" * 70)
    
    # Create fine-grained time points for smooth curves
    t_fine = np.linspace(0, max_hours, 1000)
    exact_fine = 1.0 - np.exp(-lambda_param * t_fine)
    
    # Create PWL curve
    pwl_fine = np.zeros_like(t_fine)
    for i, t in enumerate(t_fine):
        for j in range(len(breakpoints) - 1):
            if breakpoints[j] <= t <= breakpoints[j + 1]:
                t0, t1 = breakpoints[j], breakpoints[j + 1]
                f0, f1 = exact_values[j], exact_values[j + 1]
                weight = (t - t0) / (t1 - t0)
                pwl_fine[i] = f0 + weight * (f1 - f0)
                break
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Subplot 1: Exact vs PWL
    plt.subplot(2, 1, 1)
    plt.plot(t_fine, exact_fine, 'b-', linewidth=2, label='Exact: F(t) = 1 - e^(-λt)')
    plt.plot(t_fine, pwl_fine, 'r--', linewidth=2, label=f'PWL ({num_segments} segments)')
    plt.scatter(breakpoints, exact_values, color='red', s=100, zorder=5, 
                label='PWL breakpoints')
    plt.axhline(y=0.70, color='orange', linestyle=':', linewidth=2, 
                label='Safety threshold (0.70)')
    plt.xlabel('Cumulative Work Hours', fontsize=12)
    plt.ylabel('Fatigue Level F(t)', fontsize=12)
    plt.title('Exponential Fatigue Function and PWL Approximation', fontsize=14, fontweight='bold')
    plt.legend(loc='lower right', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, max_hours)
    plt.ylim(0, 0.85)
    
    # Subplot 2: Approximation Error
    error_fine = np.abs(exact_fine - pwl_fine) / exact_fine * 100
    plt.subplot(2, 1, 2)
    plt.plot(t_fine, error_fine, 'g-', linewidth=2)
    plt.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='1% error threshold')
    plt.axhline(y=max_error, color='orange', linestyle=':', linewidth=1, 
                label=f'Max error: {max_error:.2f}%')
    plt.xlabel('Cumulative Work Hours', fontsize=12)
    plt.ylabel('Approximation Error (%)', fontsize=12)
    plt.title('PWL Approximation Error', fontsize=14, fontweight='bold')
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, max_hours)
    plt.ylim(0, max(2.0, max_error * 1.2))
    
    plt.tight_layout()
    plt.savefig('results/pwl_accuracy_test.png', dpi=150, bbox_inches='tight')
    print(f"\n✅ Plot saved to: results/pwl_accuracy_test.png")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    return max_error < 1.0


if __name__ == "__main__":
    # Create results directory if it doesn't exist
    import os
    os.makedirs('results', exist_ok=True)
    
    success = test_pwl_accuracy()
    
    if success:
        print("\n🎉 All tests passed! PWL approximation ready for implementation.")
    else:
        print("\n⚠️  Tests failed. Consider increasing num_segments.")
