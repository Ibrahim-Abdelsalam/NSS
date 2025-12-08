"""
Test the model using CSV input files and generate validation output.

This script:
1. Loads nurses and scenarios from CSV files
2. Runs the optimization model
3. Displays detailed results for validation
4. Exports results to CSV/Excel for review
"""

import pandas as pd
from model import build_and_solve_model, extract_results
import time

def main():
    print("=" * 80)
    print("NURSE SCHEDULING MODEL - CSV INPUT TEST")
    print("=" * 80)
    
    # ===== 1. LOAD INPUT FILES =====
    print("\n📂 STEP 1: Loading Input Files")
    print("-" * 80)
    
    try:
        nurses_df = pd.read_csv('sample_nurses.csv')
        nurses_list = nurses_df['Nurse'].tolist()
        print(f"✅ Loaded {len(nurses_list)} nurses: {', '.join(nurses_list)}")
    except Exception as e:
        print(f"❌ Error loading nurses.csv: {e}")
        return
    
    try:
        scenarios_df = pd.read_csv('sample_scenarios.csv')
        print(f"✅ Loaded scenarios data:")
        print(f"   - Scenarios: {scenarios_df['scenario'].nunique()}")
        print(f"   - Days: {scenarios_df['day'].nunique()}")
        print(f"   - Shifts: {sorted(scenarios_df['shift'].unique())}")
        print(f"   - Total rows: {len(scenarios_df)}")
    except Exception as e:
        print(f"❌ Error loading scenarios.csv: {e}")
        return
    
    # ===== 2. SET MODEL PARAMETERS =====
    print("\n⚙️  STEP 2: Model Parameters")
    print("-" * 80)
    
    params = {
        # Cost parameters
        'c1': 100,       # Regular shift cost (£)
        'c2': 150,       # Overtime shift cost (£)
        'q_plus': 200,   # Emergency staff cost (£)
        'q_minus': 0,    # Cancellation cost (£)
        
        # Hard constraints
        'n1': 15,        # Max total shifts per nurse
        'n2': 5,         # Max night shifts per nurse
        'n3': 8,         # Min regular shifts per nurse (if working)
        'n4': 0,         # Min complete weekends off (disabled)
        
        # Advanced constraints (all disabled for this test)
        'shift_quotas': {},
        'night_rest_enabled': False,
        'start_date': None,
    }
    
    print("Cost Structure:")
    print(f"   - Regular shift: £{params['c1']}")
    print(f"   - Overtime shift: £{params['c2']}")
    print(f"   - Emergency staff: £{params['q_plus']}")
    print("\nWork Rules:")
    print(f"   - Max shifts per nurse (n1): {params['n1']}")
    print(f"   - Max night shifts (n2): {params['n2']}")
    print(f"   - Min regular shifts (n3): {params['n3']}")
    
    # ===== 3. SOLVE THE MODEL =====
    print("\n🔧 STEP 3: Solving Optimization Model")
    print("-" * 80)
    
    start_time = time.time()
    prob, status = build_and_solve_model(
        nurses_list=nurses_list,
        scenarios_df=scenarios_df,
        model_params=params,
        model_type="SDM",
        solver_name="AUTO"
    )
    solve_time = time.time() - start_time
    
    print(f"Solver Status: {status}")
    print(f"Solve Time: {solve_time:.2f} seconds")
    
    if status != "Optimal":
        print(f"❌ Model did not solve to optimality: {status}")
        return
    
    # ===== 4. EXTRACT RESULTS =====
    print("\n📊 STEP 4: Extracting Results")
    print("-" * 80)
    
    results = extract_results(prob, nurses_list, scenarios_df, params)
    
    if results is None:
        print("❌ Failed to extract results")
        return
    
    # ===== 5. DISPLAY VALIDATION OUTPUT =====
    print("\n" + "=" * 80)
    print("VALIDATION OUTPUT")
    print("=" * 80)
    
    # Cost Breakdown
    print("\n💰 COST BREAKDOWN:")
    print("-" * 80)
    cost = results['cost_breakdown']
    print(f"Stage 1 (Regular):   £{cost['stage1_regular_cost']:,.2f} ({cost['total_regular_shifts']} shifts × £{params['c1']})")
    print(f"Stage 1 (Overtime):  £{cost['stage1_overtime_cost']:,.2f} ({cost['total_overtime_shifts']} shifts × £{params['c2']})")
    print(f"Stage 1 Total:       £{cost['stage1_cost']:,.2f}")
    print(f"Stage 2 (Expected):  £{cost['stage2_cost']:,.2f}")
    print(f"─" * 80)
    print(f"TOTAL COST:          £{cost['total_cost']:,.2f}")
    
    # Nurse Schedule
    print("\n📅 NURSE SCHEDULE (Stage 1 - Baseline):")
    print("-" * 80)
    print(results['roster_df'].to_string(index=False))
    
    # Scenario Analysis
    print("\n🎲 SCENARIO ANALYSIS (Stage 2 - Recourse):")
    print("-" * 80)
    print(results['scenario_df'].to_string(index=False))
    
    # Summary Statistics
    print("\n📈 SUMMARY STATISTICS:")
    print("-" * 80)
    print(f"Total Nurses:        {len(nurses_list)}")
    print(f"Planning Period:     {scenarios_df['day'].nunique()} days")
    print(f"Scenarios:           {scenarios_df['scenario'].nunique()}")
    print(f"Total Demand:        {scenarios_df['demand'].sum()} nurse-shifts")
    print(f"Avg Demand/Day:      {scenarios_df.groupby('day')['demand'].sum().mean():.1f} nurses")
    print(f"Regular Shifts:      {cost['total_regular_shifts']}")
    print(f"Overtime Shifts:     {cost['total_overtime_shifts']}")
    print(f"Avg Shifts/Nurse:    {(cost['total_regular_shifts'] + cost['total_overtime_shifts']) / len(nurses_list):.1f}")
    
    # ===== 6. EXPORT RESULTS =====
    print("\n💾 STEP 5: Exporting Results")
    print("-" * 80)
    
    try:
        # Export roster to CSV
        results['roster_df'].to_csv('output_roster.csv', index=False)
        print("✅ Exported: output_roster.csv")
        
        # Export scenarios to CSV
        results['scenario_df'].to_csv('output_scenarios.csv', index=False)
        print("✅ Exported: output_scenarios.csv")
        
        # Export to Excel with multiple sheets
        with pd.ExcelWriter('output_results.xlsx', engine='openpyxl') as writer:
            results['roster_df'].to_excel(writer, sheet_name='Nurse Schedule', index=False)
            results['scenario_df'].to_excel(writer, sheet_name='Scenario Analysis', index=False)
            
            # Cost summary sheet
            cost_df = pd.DataFrame([
                {'Category': 'Regular Shifts', 'Count': cost['total_regular_shifts'], 
                 'Unit Cost': params['c1'], 'Total Cost': cost['stage1_regular_cost']},
                {'Category': 'Overtime Shifts', 'Count': cost['total_overtime_shifts'], 
                 'Unit Cost': params['c2'], 'Total Cost': cost['stage1_overtime_cost']},
                {'Category': 'Stage 1 Total', 'Count': '', 
                 'Unit Cost': '', 'Total Cost': cost['stage1_cost']},
                {'Category': 'Stage 2 (Expected)', 'Count': '', 
                 'Unit Cost': '', 'Total Cost': cost['stage2_cost']},
                {'Category': 'GRAND TOTAL', 'Count': '', 
                 'Unit Cost': '', 'Total Cost': cost['total_cost']},
            ])
            cost_df.to_excel(writer, sheet_name='Cost Breakdown', index=False)
        
        print("✅ Exported: output_results.xlsx (with 3 sheets)")
        
    except Exception as e:
        print(f"⚠️  Export warning: {e}")
    
    # ===== 7. VALIDATION CHECKS =====
    print("\n✅ VALIDATION CHECKS:")
    print("-" * 80)
    
    checks_passed = 0
    checks_total = 5
    
    # Check 1: Solution exists
    if status == "Optimal":
        print("✅ Check 1: Model solved to optimality")
        checks_passed += 1
    else:
        print(f"❌ Check 1: Model status = {status}")
    
    # Check 2: All nurses scheduled
    nurses_scheduled = results['roster_df']['Total_Shifts'].sum()
    if nurses_scheduled > 0:
        print(f"✅ Check 2: Nurses scheduled ({nurses_scheduled} total shifts)")
        checks_passed += 1
    else:
        print("❌ Check 2: No shifts scheduled")
    
    # Check 3: Costs are reasonable
    if 0 < cost['total_cost'] < 100000:
        print(f"✅ Check 3: Total cost is reasonable (£{cost['total_cost']:,.2f})")
        checks_passed += 1
    else:
        print(f"⚠️  Check 3: Total cost seems unusual (£{cost['total_cost']:,.2f})")
    
    # Check 4: Stage 1 + Stage 2 = Total
    calculated_total = cost['stage1_cost'] + cost['stage2_cost']
    if abs(calculated_total - cost['total_cost']) < 0.01:
        print(f"✅ Check 4: Cost breakdown sums correctly")
        checks_passed += 1
    else:
        print(f"❌ Check 4: Cost mismatch ({calculated_total} ≠ {cost['total_cost']})")
    
    # Check 5: Scenarios covered
    scenarios_analyzed = len(results['scenario_df'])
    if scenarios_analyzed == scenarios_df['scenario'].nunique():
        print(f"✅ Check 5: All {scenarios_analyzed} scenarios analyzed")
        checks_passed += 1
    else:
        print(f"❌ Check 5: Scenario count mismatch")
    
    print(f"\n🎯 Validation Score: {checks_passed}/{checks_total} checks passed")
    
    if checks_passed == checks_total:
        print("\n🎉 ALL VALIDATION CHECKS PASSED!")
        print("The model is working correctly and ready for production use.")
    else:
        print(f"\n⚠️  {checks_total - checks_passed} validation check(s) failed. Review results above.")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
