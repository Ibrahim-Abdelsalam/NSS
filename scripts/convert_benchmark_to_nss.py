"""
Convert Nurse Rostering Benchmark Instances to NSS CSV Format

This script converts benchmark files from schedulingbenchmarks.org
(plain text format) to the CSV format used by NSS.

Usage:
    python convert_benchmark_to_nss.py Instance2.txt

Output:
    - benchmark_nurses.csv
    - benchmark_scenarios.csv
"""

import sys
import pandas as pd
from pathlib import Path


def parse_benchmark_file(filepath):
    """
    Parse a nurse rostering benchmark file.
    
    Args:
        filepath: Path to benchmark .txt file
        
    Returns:
        dict with parsed sections
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    data = {
        'horizon': 0,
        'shifts': [],
        'staff': [],
        'days_off': [],
        'shift_on_requests': [],
        'shift_off_requests': [],
        'cover': []
    }
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Detect section headers
        if line.startswith('SECTION_'):
            current_section = line.replace('SECTION_', '').lower()
            continue
        
        # Parse based on current section
        if current_section == 'horizon':
            data['horizon'] = int(line)
        
        elif current_section == 'shifts':
            # Format: ShiftID, Length, Forbidden
            parts = line.split(',')
            data['shifts'].append({
                'id': parts[0].strip(),
                'length': int(parts[1].strip()),
                'forbidden': parts[2].strip() if len(parts) > 2 else ''
            })
        
        elif current_section == 'staff':
            # Format: ID, MaxShifts, MaxTotalMinutes, MinTotalMinutes, MaxConsecutiveShifts, MinConsecutiveShifts, MinConsecutiveDaysOff, MaxWeekends
            parts = line.split(',')
            data['staff'].append({
                'id': parts[0].strip(),
                'max_shifts': parts[1].strip(),
                'max_total_minutes': int(parts[2].strip()),
                'min_total_minutes': int(parts[3].strip()),
                'max_consecutive': int(parts[4].strip()),
                'min_consecutive': int(parts[5].strip()),
                'min_days_off': int(parts[6].strip()),
                'max_weekends': int(parts[7].strip())
            })
        
        elif current_section == 'days_off':
            # Format: EmployeeID, DayIndexes
            parts = line.split(',')
            data['days_off'].append({
                'employee': parts[0].strip(),
                'days': [int(d.strip()) for d in parts[1:]]
            })
        
        elif current_section == 'shift_on_requests':
            # Format: EmployeeID, Day, ShiftID, Weight
            parts = line.split(',')
            data['shift_on_requests'].append({
                'employee': parts[0].strip(),
                'day': int(parts[1].strip()),
                'shift': parts[2].strip(),
                'weight': int(parts[3].strip())
            })
        
        elif current_section == 'shift_off_requests':
            # Format: EmployeeID, Day, ShiftID, Weight
            parts = line.split(',')
            data['shift_off_requests'].append({
                'employee': parts[0].strip(),
                'day': int(parts[1].strip()),
                'shift': parts[2].strip(),
                'weight': int(parts[3].strip())
            })
        
        elif current_section == 'cover':
            # Format: Day, ShiftID, Requirement, Weight_under, Weight_over
            parts = line.split(',')
            data['cover'].append({
                'day': int(parts[0].strip()),
                'shift': parts[1].strip(),
                'demand': int(parts[2].strip()),
                'weight_under': int(parts[3].strip()),
                'weight_over': int(parts[4].strip())
            })
    
    return data
can 

def convert_to_nss_format(data, num_scenarios=5, demand_variation=0.15):
    """
    Convert parsed benchmark data to NSS CSV format.
    
    Args:
        data: Parsed benchmark data
        num_scenarios: Number of stochastic scenarios to generate
        demand_variation: Percentage variation in demand (0.15 = ±15%)
        
    Returns:
        nurses_df, scenarios_df
    """
    import numpy as np
    
    # Create nurses DataFrame
    nurses_list = [staff['id'] for staff in data['staff']]
    nurses_df = pd.DataFrame({'nurse_name': nurses_list})
    
    # Create scenarios DataFrame
    scenarios_data = []
    
    for scenario in range(1, num_scenarios + 1):
        for cover in data['cover']:
            day = cover['day'] + 1  # Convert 0-indexed to 1-indexed
            shift = cover['shift']
            base_demand = cover['demand']
            
            # Add stochastic variation
            if scenario == 1:
                # Scenario 1: Base demand (deterministic)
                demand = base_demand
            else:
                # Other scenarios: Add random variation
                np.random.seed(scenario * 1000 + day * 10 + ord(shift[0]))
                variation = np.random.uniform(-demand_variation, demand_variation)
                demand = max(1, int(base_demand * (1 + variation)))
            
            scenarios_data.append({
                'scenario': scenario,
                'day': day,
                'shift': shift,
                'demand': demand
            })
    
    scenarios_df = pd.DataFrame(scenarios_data)
    
    return nurses_df, scenarios_df


def print_conversion_summary(data, nurses_df, scenarios_df):
    """Print summary of the conversion."""
    print("\n" + "="*60)
    print("BENCHMARK CONVERSION SUMMARY")
    print("="*60)
    
    print(f"\n📊 Problem Size:")
    print(f"  Horizon:        {data['horizon']} days")
    print(f"  Nurses:         {len(nurses_df)} ({', '.join(nurses_df['nurse_name'].tolist())})")
    print(f"  Shift Types:    {len(data['shifts'])} ({', '.join([s['id'] for s in data['shifts']])})")
    print(f"  Scenarios:      {scenarios_df['scenario'].nunique()}")
    
    print(f"\n📋 Constraints (from benchmark):")
    if data['staff']:
        sample_staff = data['staff'][0]
        print(f"  Max Shifts:            {sample_staff['max_shifts']}")
        print(f"  Max Consecutive:       {sample_staff['max_consecutive']} days")
        print(f"  Min Consecutive:       {sample_staff['min_consecutive']} days")
        print(f"  Min Days Off:          {sample_staff['min_days_off']} days")
        print(f"  Max Weekends:          {sample_staff['max_weekends']}")
    
    print(f"\n📈 Demand Statistics:")
    print(f"  Total Demand (avg):    {scenarios_df.groupby('scenario')['demand'].sum().mean():.1f}")
    print(f"  Min Daily Demand:      {scenarios_df.groupby(['scenario', 'day'])['demand'].sum().min()}")
    print(f"  Max Daily Demand:      {scenarios_df.groupby(['scenario', 'day'])['demand'].sum().max()}")
    
    print(f"\n💡 Shift On Requests:   {len(data['shift_on_requests'])} (nurse preferences to work)")
    print(f"⚠️  Shift Off Requests:  {len(data['shift_off_requests'])} (nurse preferences not to work)")
    print(f"🚫 Days Off (fixed):     {len(data['days_off'])} (unavailable days)")
    
    print(f"\n✅ Output Files:")
    print(f"  - benchmark_nurses.csv ({len(nurses_df)} rows)")
    print(f"  - benchmark_scenarios.csv ({len(scenarios_df)} rows)")
    
    print("\n" + "="*60)


def suggest_nss_parameters(data):
    """Suggest NSS parameters based on benchmark constraints."""
    print("\n🔧 SUGGESTED NSS PARAMETERS:")
    print("="*60)
    
    if data['staff']:
        # Extract max shifts from first staff member
        max_shifts_str = data['staff'][0]['max_shifts']
        # Parse "E=14|L=14" format
        shift_limits = {}
        for part in max_shifts_str.split('|'):
            shift, limit = part.split('=')
            shift_limits[shift] = int(limit)
        
        total_max = sum(shift_limits.values())
        
        print(f"\n📋 Work Rules (based on benchmark):")
        print(f"  n1 (Max Total Shifts):     {data['horizon']} (or {total_max} to allow all shifts)")
        print(f"  n2 (Max Night Shifts):     0 (no night shifts in Instance2)")
        print(f"  n3 (Min Regular Shifts):   {data['staff'][0]['min_total_minutes'] // 480} (based on min minutes)")
        print(f"  n4 (Min Weekends Off):     {data['staff'][0]['max_weekends']}")
        
        print(f"\n⚖️  Advanced Constraints:")
        print(f"  Max Consecutive:           {data['staff'][0]['max_consecutive']} days")
        print(f"  Min Consecutive:           {data['staff'][0]['min_consecutive']} days")
        print(f"  Min Days Off:              {data['staff'][0]['min_days_off']} days")
    
    print(f"\n💰 Cost Parameters (suggested):")
    print(f"  c1 (Regular Shift):        100")
    print(f"  c2 (Overtime Shift):       150")
    print(f"  q_plus (Emergency):        200")
    print(f"  c3 (Stand-alone penalty):  10 (benchmark uses shift-on/off requests)")
    print(f"  c4 (Pattern penalty):      15")
    
    print(f"\n⚠️  NOTE: Benchmark uses soft constraints (shift requests) differently than NSS")
    print(f"  Benchmark: Shift-on/off requests with weights")
    print(f"  NSS:       Cost-based penalties (c3, c4) for patterns")
    
    print("\n" + "="*60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_benchmark_to_nss.py Instance2.txt")
        print("\nOptional arguments:")
        print("  --scenarios N     Number of scenarios to generate (default: 5)")
        print("  --variation V     Demand variation percentage (default: 0.15)")
        print("\nExample:")
        print("  python convert_benchmark_to_nss.py Instance2.txt --scenarios 10 --variation 0.20")
        sys.exit(1)
    
    # Parse arguments
    filepath = sys.argv[1]
    num_scenarios = 5
    demand_variation = 0.15
    
    for i, arg in enumerate(sys.argv):
        if arg == '--scenarios' and i + 1 < len(sys.argv):
            num_scenarios = int(sys.argv[i + 1])
        elif arg == '--variation' and i + 1 < len(sys.argv):
            demand_variation = float(sys.argv[i + 1])
    
    if not Path(filepath).exists():
        print(f"❌ Error: File not found: {filepath}")
        sys.exit(1)
    
    print(f"📂 Reading benchmark file: {filepath}")
    print(f"🎲 Generating {num_scenarios} scenarios with ±{demand_variation*100:.0f}% demand variation")
    
    # Parse benchmark file
    data = parse_benchmark_file(filepath)
    
    # Convert to NSS format
    nurses_df, scenarios_df = convert_to_nss_format(data, num_scenarios, demand_variation)
    
    # Save to CSV
    nurses_df.to_csv('benchmark_nurses.csv', index=False)
    scenarios_df.to_csv('benchmark_scenarios.csv', index=False)
    
    # Print summary
    print_conversion_summary(data, nurses_df, scenarios_df)
    
    # Suggest NSS parameters
    suggest_nss_parameters(data)
    
    print("\n✅ Conversion complete!")
    print("\n📝 Next Steps:")
    print("  1. Copy benchmark_nurses.csv and benchmark_scenarios.csv to data/ folder")
    print("  2. Run Streamlit app: streamlit run app.py")
    print("  3. Upload the CSV files in the sidebar")
    print("  4. Use the suggested parameters above")
    print("  5. Click 'OPTIMIZE SCHEDULE'")
    
    print("\n💡 Expected Results for Instance2:")
    print("  - Benchmark optimal cost: 828")
    print("  - NSS may have different cost due to different objective function")
    print("  - Focus on: Constraint satisfaction, solve time, feasibility")
    print("  - NSS solves stochastic problem, benchmark is deterministic")


if __name__ == '__main__':
    main()
