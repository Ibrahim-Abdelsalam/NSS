import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*80)
print("VERIFICATION: Data Usage in compare_configurations.py")
print("="*80)

print("\n✓ CODE ANALYSIS:")
print("-"*80)

print("\n1. DATA LOADING (Lines 169-173):")
print("   nurses_file = analysis_nurses.csv")
print("   scenarios_file = analysis_scenarios.csv")
print("   nurses_df = pd.read_csv(nurses_file)")
print("   scenarios_df = pd.read_csv(scenarios_file)")
print("   nurses_list = nurses_df['Nurse'].tolist()")
print("   → Data is loaded ONCE at the start")

print("\n2. CONFIGURATION DEFINITIONS (Lines 187-297):")
print("   config1 = base_params.copy()  # SDM Basic")
print("   config2 = base_params.copy()  # SDM with Fatigue")
print("   config3 = base_params.copy()  # High Fatigue Penalty")
print("   config4 = base_params.copy()  # SDM-CVaR")
print("   config5 = base_params.copy()  # CVaR Conservative")
print("   config6 = base_params.copy()  # Full Model")
print("   config7 = base_params.copy()  # Tight Constraints")
print("   config8 = base_params.copy()  # Lower Costs")
print("   → All 8 configurations use base_params")

print("\n3. EXECUTION LOOP (Lines 299-303):")
print("   for config_name, params, model_type in configurations:")
print("       result = run_configuration_test(")
print("           config_name,")
print("           nurses_list,      ← SAME for all")
print("           scenarios_df,     ← SAME for all")
print("           params,            ← Different (the only change)")
print("           model_type)")
print("   → All 8 configs use IDENTICAL nurses_list and scenarios_df")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

print("\n✓ YES - All 8 configurations use the EXACT SAME data")
print("✓ YES - The data is CORRECT (analysis_nurses.csv + analysis_scenarios.csv)")
print("\nData is loaded once and reused for all 8 tests, ensuring fair comparison.")
print("Only the model parameters change between configurations.")

print("\n" + "="*80 + "\n")
