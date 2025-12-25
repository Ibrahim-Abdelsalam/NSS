#!/usr/bin/env python3
"""Minimal test - just import and check syntax"""
import sys
sys.path.insert(0, '/Users/ibrahim/Documents/GitHub/NSS')

try:
    print("Testing imports...")
    from model import get_default_params, create_pwl_fatigue_approximation
    
    print("✓ Imports successful")
    
    print("\nTesting get_default_params()...")
    params = get_default_params()
    
    print(f"✓ Parameters retrieved: {len(params)} keys")
    print(f"  - patient_safety_enabled: {params.get('patient_safety_enabled')}")
    print(f"  - fatigue_lambda: {params.get('fatigue_lambda')}")
    
    print("\nTesting PWL helper function...")
    breakpoints, slopes, exact_values = create_pwl_fatigue_approximation(0.03, 48, 8)
    
    print(f"✓ PWL function working:")
    print(f"  - Breakpoints: {len(breakpoints)} points")
    print(f"  - Segments: {len(slopes)}")
    print(f"  - First breakpoint: {breakpoints[0]}")
    print(f"  - Last breakpoint: {breakpoints[-1]}")
    print(f"  - Max fatigue value: {exact_values[-1]:.4f}")
    
    print("\n✅ ALL SYNTAX CHECKS PASSED")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
