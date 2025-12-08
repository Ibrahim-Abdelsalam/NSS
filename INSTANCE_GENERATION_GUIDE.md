# 📘 Complete Guide to Generating NSS Instance Files

**Based on:** He et al. (2019) "Controlling understaffing with conditional Value-at-Risk constraint for an integrated nurse scheduling problem under patient demand uncertainty"

**Last Updated:** December 8, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [File Formats](#file-formats)
4. [Instance Size Guidelines](#instance-size-guidelines)
5. [Demand Generation Methods](#demand-generation-methods)
6. [Parameter Selection](#parameter-selection)
7. [Validation Checklist](#validation-checklist)
8. [Example Instances](#example-instances)
9. [Common Mistakes](#common-mistakes)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The NSS (Nurse Scheduling System) requires **two input files**:

1. **Nurse List** - Simple list of nurse names/IDs
2. **Demand Scenarios** - Stochastic demand data (scenario × day × shift)

Both files work together with the **model parameters** to create a complete optimization instance.

---

## Quick Start

### Step 1: Create Nurse List

Create `nurses.csv` with one nurse name per line:

```csv
Alice
Bob
Charlie
Diana
Edward
Frank
Grace
Henry
Iris
Jack
```

**Rules:**
- ✅ One name per line (no header row)
- ✅ Any alphanumeric string
- ✅ Can also use IDs: `N1`, `N2`, `N3`, ...
- ❌ No empty file (minimum 1 nurse)
- ⚠️ Duplicates trigger warning

### Step 2: Create Demand Scenarios

Create `scenarios.csv` with **exact column names**:

```csv
scenario,day,shift,demand
1,1,E,3
1,1,D,4
1,1,L,3
1,1,N,2
1,2,E,3
1,2,D,4
1,2,L,3
1,2,N,2
```

**Rules:**
- ✅ Must have header: `scenario,day,shift,demand`
- ✅ Complete data: Every scenario × every day × every shift
- ✅ Shifts must be: `E`, `D`, `L`, or `N` (case-sensitive)
- ✅ Days start at 1 and are consecutive (1, 2, 3, ...)
- ✅ Demand ≥ 0 (zero allowed, no negatives)
- ❌ No missing rows (gaps in data)
- ❌ No NaN/null values

### Step 3: Verify Completeness

**Expected row count:**
```
Total Rows = num_scenarios × num_days × 4
```

Example: 5 scenarios × 14 days × 4 shifts = **280 rows**

---

## File Formats

### Nurse List File

**Format Options:**

**Option A: CSV (one column, no header)**
```csv
Alice
Bob
Charlie
```

**Option B: TXT (one per line)**
```
Alice
Bob
Charlie
```

**Option C: Comma-separated (single line)**
```
Alice, Bob, Charlie
```

All three are valid and will be parsed correctly.

---

### Scenarios File

**Required Structure:**

| Column | Type | Description | Valid Values |
|--------|------|-------------|--------------|
| `scenario` | int/str | Scenario identifier | 1, 2, 3, ... or "S1", "S2", ... |
| `day` | int | Day number (1-indexed) | 1, 2, 3, ..., num_days |
| `shift` | str | Shift type | 'E', 'D', 'L', 'N' |
| `demand` | int | Required nurses | 0, 1, 2, 3, ... (no negatives) |

**Shift Types (HARDCODED - Cannot be changed):**

- **E** (Early) - 07:00-16:00 - Morning shift
- **D** (Day) - 08:00-17:00 - Standard day shift  
- **L** (Late) - 14:00-23:00 - Evening shift
- **N** (Night) - 23:00-07:00 - Overnight shift

⚠️ **Important:** These exact shift codes are required. Custom shift names will cause errors.

---

## Instance Size Guidelines

### Small Instance (Testing/Development)

**Purpose:** Quick testing, debugging, learning the system

**Recommended:**
- **Nurses:** 10-20
- **Days:** 7-14 (1-2 weeks)
- **Scenarios:** 5-10
- **Total rows:** 140-560

**Characteristics:**
- Solves in 5-30 seconds
- Easy to visualize results
- Good for parameter experimentation

**Example:**
```
10 nurses × 7 days × 5 scenarios × 4 shifts = 140 rows
```

---

### Medium Instance (Realistic Testing)

**Purpose:** Realistic problem size, performance testing

**Recommended:**
- **Nurses:** 30-50
- **Days:** 14-21 (2-3 weeks)
- **Scenarios:** 20-50
- **Total rows:** 1,120-4,200

**Characteristics:**
- Solves in 1-5 minutes
- Represents typical ward size
- Balances realism and speed

**Example:**
```
40 nurses × 14 days × 30 scenarios × 4 shifts = 1,680 rows
```

---

### Large Instance (Production/Research)

**Purpose:** Full-scale optimization, research publication

**Recommended (Paper values):**
- **Nurses:** 90-100
- **Days:** 28 (4 weeks)
- **Scenarios:** 50-300
- **Total rows:** 5,600-33,600

**Characteristics:**
- Solves in 10-60 minutes (Gurobi)
- Matches paper case study
- Publication-quality results

**Example (Paper case):**
```
100 nurses × 28 days × 100 scenarios × 4 shifts = 11,200 rows
```

---

## Demand Generation Methods

### Method 1: Fixed Baseline with Random Variation

**Simplest method - Good for testing**

```python
import pandas as pd
import random

# Baseline demand (from paper)
baseline = {'E': 24, 'D': 24, 'L': 12, 'N': 12}

scenarios = []
for scenario in range(1, 6):  # 5 scenarios
    for day in range(1, 15):  # 14 days
        for shift in ['E', 'D', 'L', 'N']:
            # Add ±15% random variation
            variation = random.uniform(-0.15, 0.15)
            demand = baseline[shift] * (1 + variation)
            demand = max(1, int(demand))  # Ensure ≥ 1
            
            scenarios.append({
                'scenario': scenario,
                'day': day,
                'shift': shift,
                'demand': demand
            })

df = pd.DataFrame(scenarios)
df.to_csv('scenarios.csv', index=False)
```

**Pros:** Simple, fast, reproducible  
**Cons:** No temporal patterns, uniform distribution

---

### Method 2: Weekend-Adjusted Demand (Paper-based)

**More realistic - Captures weekly patterns**

```python
from datetime import datetime, timedelta

# Start on a Monday for clean weekend detection
start_date = datetime(2025, 1, 6)  # Monday, Jan 6, 2025

baseline = {'E': 24, 'D': 24, 'L': 12, 'N': 12}

scenarios = []
for scenario in range(1, 6):
    # Scenario-specific variation factor
    scenario_factor = 1 + random.uniform(-0.10, 0.10)
    
    for day in range(1, 15):
        # Calculate actual date
        current_date = start_date + timedelta(days=day - 1)
        is_weekend = current_date.weekday() >= 5  # 5=Sat, 6=Sun
        
        for shift in ['E', 'D', 'L', 'N']:
            base = baseline[shift]
            
            # Reduce weekend demand by 20%
            if is_weekend:
                base = int(base * 0.8)
            
            # Apply scenario-specific variation
            demand = int(base * scenario_factor)
            demand = max(1, demand)
            
            scenarios.append({
                'scenario': scenario,
                'day': day,
                'shift': shift,
                'demand': demand
            })

df = pd.DataFrame(scenarios)
df.to_csv('scenarios.csv', index=False)
```

**Pros:** Realistic weekly patterns, matches paper  
**Cons:** Requires date calculations

---

### Method 3: Historical Data (Paper Method)

**Most realistic - Use actual hospital data**

```python
# Assume you have historical demand data
historical_df = pd.read_csv('historical_demand.csv')
# Columns: date, shift, actual_demand

# Each time period becomes a scenario
scenarios = []
scenario_id = 1

for month in historical_df['month'].unique():
    month_data = historical_df[historical_df['month'] == month]
    
    for day in range(1, 29):  # 28-day period
        day_data = month_data[month_data['day'] == day]
        
        for shift in ['E', 'D', 'L', 'N']:
            demand = day_data[day_data['shift'] == shift]['actual_demand'].iloc[0]
            
            scenarios.append({
                'scenario': scenario_id,
                'day': day,
                'shift': shift,
                'demand': int(demand)
            })
    
    scenario_id += 1

df = pd.DataFrame(scenarios)
df.to_csv('scenarios.csv', index=False)
```

**Pros:** Real-world patterns, best for research  
**Cons:** Requires historical data

---

### Method 4: Nurse-to-Patient Ratio (Paper-based)

**For sizing demand based on patient load**

```python
# Paper uses 1:4 nurse-to-patient ratio
def calculate_demand(patients, shift_distribution):
    """
    patients: Average number of patients in ward
    shift_distribution: Dict with percentage per shift
    """
    ratio = 4  # 1 nurse per 4 patients
    total_nurses = patients / ratio
    
    demand = {}
    for shift, percentage in shift_distribution.items():
        demand[shift] = int(total_nurses * percentage)
    
    return demand

# Example: 96 patients in ward
patients = 96
distribution = {
    'E': 0.33,  # 33% need morning care
    'D': 0.33,  # 33% need day care
    'L': 0.17,  # 17% need evening care
    'N': 0.17   # 17% need night monitoring
}

baseline = calculate_demand(patients, distribution)
# Result: {'E': 8, 'D': 8, 'L': 4, 'N': 4}

# Then apply Methods 1 or 2 for scenario generation
```

**Pros:** Evidence-based, matches paper methodology  
**Cons:** Requires patient census data

---

## Parameter Selection

### Essential Parameters (Always Required)

**Cost Parameters:**
```python
# Paper values (normalized)
c1 = 10.0      # Regular shift cost
c2 = 15.0      # Overtime shift cost (1.5× regular)
q_plus = 18.0  # Emergency shift cost (1.8× regular)
q_minus = 2.0  # Cancellation cost

# Realistic USD values (scale up proportionally)
c1 = 100.0     # Regular: $100
c2 = 150.0     # Overtime: $150 (1.5× regular)
q_plus = 180.0 # Emergency: $180 (1.8× regular)
q_minus = 20.0 # Cancellation: $20
```

**Work Rules:**
```python
# Paper values (28-day period)
n1 = 24  # Max total shifts
n2 = 3   # Max night shifts
n3 = 16  # Min regular shifts

# Scaled for 14-day period (divide by 2)
n1 = 12  # Max total shifts
n2 = 2   # Max night shifts  
n3 = 8   # Min regular shifts

# Scaled for 7-day period (divide by 4)
n1 = 6   # Max total shifts
n2 = 1   # Max night shifts
n3 = 4   # Min regular shifts
```

**Scaling Rule:**
```
parameter_value = (paper_value / 28) × your_planning_days
```

---

### Advanced Parameters (Optional)

**Weekend Constraints:**
```python
# Paper value (4-week period)
n4 = 4              # Min 4 complete weekends off
start_date = '2025-01-06'  # Monday start

# Scaled for 2-week period
n4 = 2              # Min 2 complete weekends off

# Scaled for 1-week period  
n4 = 1              # Min 1 complete weekend off
```

**Night Rest Constraints:**
```python
# Enable if night shift safety is critical
night_rest_enabled = True
min_consecutive_nights = 2  # No single isolated nights
days_off_after_nights = 2   # 2 days rest after night sequence
```

**Shift Quotas:**
```python
# Only use if specific shift requirements exist
shift_quotas = {
    'E': {'min': 2, 'max': 8},  # Each nurse: 2-8 early shifts
    'D': {'min': 2, 'max': 8},  # Each nurse: 2-8 day shifts
    'L': {'min': 0, 'max': 6},  # Each nurse: 0-6 late shifts
    'N': {'min': 0, 'max': 3}   # Each nurse: 0-3 night shifts
}
```

⚠️ **Warning:** Shift quotas can make problem infeasible. Use carefully!

---

### CVaR Parameters (Risk-Aware Model)

**Paper tested values:**
```python
sigma = 0.95  # 95% confidence level (always use this)
mu = 300      # Max acceptable shortage in worst 5% of scenarios

# Tested values: mu ∈ {300, 400, 500, 600}
# Lower mu = more conservative (higher cost, lower risk)
# Higher mu = more aggressive (lower cost, higher risk)
```

**For smaller instances, scale mu:**
```python
# Paper: 100 scenarios × 28 days → mu=300
# Your instance: 10 scenarios × 14 days → mu=?

scale_factor = (your_scenarios × your_days) / (100 × 28)
mu_scaled = 300 × scale_factor

# Example: 10 scenarios × 14 days
mu_scaled = 300 × (10 × 14) / (100 × 28) = 300 × 0.05 = 15
```

---

## Validation Checklist

### Before Running Optimization

**✅ Nurse List Validation:**
- [ ] File exists and is readable
- [ ] Contains at least 1 nurse
- [ ] No empty lines at end of file
- [ ] Nurse names are unique (or duplicates intentional)

**✅ Scenarios Validation:**
- [ ] File has header row: `scenario,day,shift,demand`
- [ ] All 4 columns present (exact names, case-sensitive)
- [ ] No missing values (NaN)
- [ ] No negative demands
- [ ] Days are consecutive starting from 1
- [ ] Shifts are only: E, D, L, N
- [ ] Row count = scenarios × days × 4

**✅ Completeness Check:**
```python
import pandas as pd
from itertools import product

df = pd.read_csv('scenarios.csv')

scenarios = df['scenario'].unique()
days = df['day'].unique()
shifts = df['shift'].unique()

expected_rows = len(scenarios) * len(days) * len(shifts)
actual_rows = len(df)

print(f"Expected: {expected_rows} rows")
print(f"Actual: {actual_rows} rows")
print(f"Complete: {expected_rows == actual_rows}")

# Check for missing combinations
all_combos = set(product(scenarios, days, shifts))
actual_combos = set(zip(df['scenario'], df['day'], df['shift']))
missing = all_combos - actual_combos

if missing:
    print(f"Missing {len(missing)} combinations:")
    print(list(missing)[:10])  # Show first 10
```

**✅ Parameter Validation:**
- [ ] n3 ≤ n1 (min regular ≤ max total)
- [ ] n2 ≤ n1 (max night ≤ max total)
- [ ] n4 ≤ max_possible_weekends (check planning period)
- [ ] c1 < c2 < q_plus (cost hierarchy)
- [ ] Shift quota mins don't sum > n1

**✅ Feasibility Check:**
```python
# Capacity vs Demand
total_capacity = num_nurses × n1
avg_demand_per_scenario = df.groupby('scenario')['demand'].sum().mean()
utilization = avg_demand_per_scenario / total_capacity

print(f"Capacity: {total_capacity} shifts")
print(f"Avg Demand: {avg_demand_per_scenario:.0f} shifts")
print(f"Utilization: {utilization:.1%}")

if utilization > 1.0:
    print("⚠️ WARNING: Demand exceeds capacity!")
    print("   Consider: Add nurses OR increase n1 OR reduce demand")
elif utilization > 0.9:
    print("⚠️ WARNING: Very tight capacity (>90% utilization)")
    print("   May need emergency staff in most scenarios")
else:
    print("✅ Capacity looks feasible")
```

---

## Example Instances

### Example 1: Minimal Test Instance

**Purpose:** Verify installation, test basic functionality

**Files:**

`nurses.csv`:
```csv
N1
N2
N3
N4
N5
```

`scenarios.csv`: (5 nurses × 3 days × 2 scenarios × 4 shifts = 24 rows)
```csv
scenario,day,shift,demand
1,1,E,2
1,1,D,2
1,1,L,1
1,1,N,1
1,2,E,2
1,2,D,2
1,2,L,1
1,2,N,1
1,3,E,2
1,3,D,2
1,3,L,1
1,3,N,1
2,1,E,3
2,1,D,3
2,1,L,2
2,1,N,1
2,2,E,3
2,2,D,3
2,2,L,2
2,2,N,1
2,3,E,3
2,3,D,3
2,3,L,2
2,3,N,1
```

**Parameters:**
```python
params = {
    'c1': 100, 'c2': 150, 'q_plus': 200,
    'n1': 6, 'n2': 2, 'n3': 4,
    'sigma': 0.95, 'mu': 2.0
}
```

**Expected:** Solves in <5 seconds, all nurses work 4-6 shifts

---

### Example 2: Small Realistic Instance

**Purpose:** Realistic weekly schedule

**Files:**

`nurses.csv`: 15 nurses (N1-N15)

`scenarios.csv`: (15 nurses × 7 days × 5 scenarios × 4 shifts = 140 rows)

**Generation script:**
```python
import pandas as pd
import random

baseline = {'E': 5, 'D': 6, 'L': 4, 'N': 3}

scenarios = []
for s in range(1, 6):
    variation = 1 + random.uniform(-0.15, 0.15)
    for d in range(1, 8):
        for shift in ['E', 'D', 'L', 'N']:
            demand = int(baseline[shift] * variation)
            demand = max(1, demand)
            scenarios.append({
                'scenario': s, 'day': d,
                'shift': shift, 'demand': demand
            })

pd.DataFrame(scenarios).to_csv('scenarios.csv', index=False)
```

**Parameters:**
```python
params = {
    'c1': 100, 'c2': 150, 'q_plus': 200,
    'n1': 12, 'n2': 3, 'n3': 8,
    'n4': 1,  # 1 weekend in 7 days
    'start_date': '2025-01-06',  # Monday
    'sigma': 0.95, 'mu': 5.0
}
```

---

### Example 3: Paper-Scale Instance

**Purpose:** Reproduce paper results, research validation

**Files:**

`nurses.csv`: 100 nurses

`scenarios.csv`: (100 scenarios × 28 days × 4 shifts = 11,200 rows)

**Generation script:**
```python
from datetime import datetime, timedelta
import pandas as pd
import random

start_date = datetime(2025, 1, 6)  # Monday
baseline = {'E': 24, 'D': 24, 'L': 12, 'N': 12}

scenarios = []
for s in range(1, 101):  # 100 scenarios
    # Each scenario has different variation
    s_factor = 1 + random.uniform(-0.10, 0.10)
    
    for d in range(1, 29):  # 28 days
        current_date = start_date + timedelta(days=d-1)
        is_weekend = current_date.weekday() >= 5
        
        for shift in ['E', 'D', 'L', 'N']:
            base = baseline[shift]
            
            # Weekend reduction
            if is_weekend:
                base = int(base * 0.8)
            
            # Scenario variation
            demand = int(base * s_factor)
            demand = max(1, demand)
            
            scenarios.append({
                'scenario': s, 'day': d,
                'shift': shift, 'demand': demand
            })

pd.DataFrame(scenarios).to_csv('scenarios.csv', index=False)
```

**Parameters (from paper):**
```python
params = {
    'c1': 10, 'c2': 15, 'q_plus': 18, 'q_minus': 2,
    'c3': 5, 'c4': 5,
    'n1': 24, 'n2': 3, 'n3': 16, 'n4': 4,
    'start_date': '2025-01-06',
    'sigma': 0.95, 'mu': 400
}
```

**Expected:** 
- Solve time: 10-60 minutes (Gurobi)
- Total cost: ~15,000-20,000 (normalized units)
- Utilization: 70-85%

---

## Common Mistakes

### ❌ Mistake 1: Wrong Column Names

**Wrong:**
```csv
Scenario,Day,Shift,Demand  # Capitalized
scenario_id,day_num,shift_type,nurses_needed  # Different names
```

**Correct:**
```csv
scenario,day,shift,demand  # Exact, lowercase
```

---

### ❌ Mistake 2: Missing Data Rows

**Wrong:**
```csv
scenario,day,shift,demand
1,1,E,5
1,1,D,6
# Missing L and N for day 1!
1,2,E,5
```

**Correct:** Every day must have all 4 shifts:
```csv
scenario,day,shift,demand
1,1,E,5
1,1,D,6
1,1,L,4
1,1,N,3
1,2,E,5
1,2,D,6
1,2,L,4
1,2,N,3
```

---

### ❌ Mistake 3: Day Numbering Gaps

**Wrong:**
```csv
scenario,day,shift,demand
1,1,E,5
1,3,E,5  # Jumped from day 1 to day 3!
1,5,E,5
```

**Correct:** Days must be consecutive starting from 1:
```csv
scenario,day,shift,demand
1,1,E,5
1,2,E,5
1,3,E,5
```

---

### ❌ Mistake 4: Wrong Shift Names

**Wrong:**
```csv
shift
Early    # Full word
EARLY    # All caps
e        # Lowercase
Morning  # Different name
M        # Different code
```

**Correct:** Exact codes only:
```csv
shift
E
D
L
N
```

---

### ❌ Mistake 5: Infeasible Parameters

**Wrong:**
```python
n1 = 10  # Max total shifts
n3 = 15  # Min regular shifts (impossible: 15 > 10!)
```

**Correct:**
```python
n1 = 15  # Max total shifts
n3 = 10  # Min regular shifts (feasible: 10 < 15)
```

---

### ❌ Mistake 6: Insufficient Capacity

**Wrong:**
```python
nurses = 10
n1 = 15
total_capacity = 10 × 15 = 150 shifts

avg_demand = 200 shifts  # Exceeds capacity!
```

**Correct:** Either increase capacity or reduce demand:
```python
# Option A: Add nurses
nurses = 15
total_capacity = 15 × 15 = 225 shifts  # > 200 ✓

# Option B: Reduce demand
avg_demand = 140 shifts  # < 150 ✓
```

---

## Troubleshooting

### Problem: "Missing required columns" error

**Cause:** Column names don't match exactly

**Solution:**
1. Check header row is: `scenario,day,shift,demand`
2. Ensure lowercase, no spaces
3. Ensure no extra columns before these 4
4. Save file as UTF-8 CSV

---

### Problem: "Data appears incomplete" warning

**Cause:** Missing scenario/day/shift combinations

**Solution:**
```python
# Run this validation script
import pandas as pd
from itertools import product

df = pd.read_csv('scenarios.csv')
all_combos = set(product(
    df['scenario'].unique(),
    df['day'].unique(), 
    df['shift'].unique()
))
actual_combos = set(zip(df['scenario'], df['day'], df['shift']))
missing = all_combos - actual_combos

print(f"Missing combinations: {missing}")
# Add the missing rows to your CSV
```

---

### Problem: Solver returns "Infeasible"

**Common causes:**

1. **Demand > Capacity**
   ```python
   # Check utilization
   capacity = num_nurses × n1
   demand = scenarios_df.groupby('scenario')['demand'].sum().mean()
   print(f"Utilization: {demand/capacity:.1%}")
   # If >100%, add nurses or reduce demand
   ```

2. **Conflicting constraints**
   ```python
   # Check: n3 ≤ n1
   # Check: n4 ≤ possible_weekends
   # Check: shift quotas don't over-constrain
   ```

3. **Too many advanced constraints**
   ```python
   # Try disabling one by one:
   n4 = 0  # Disable weekend constraint
   night_rest_enabled = False  # Disable night rest
   shift_quotas = {}  # Disable shift quotas
   ```

---

### Problem: Solve time too long (>10 minutes)

**Solutions:**

1. **Reduce problem size**
   ```python
   # Reduce scenarios: 100 → 20
   # Reduce days: 28 → 14
   # Reduce nurses: 100 → 50
   ```

2. **Use faster solver**
   ```python
   # In app: Select "HiGHS" instead of "CBC"
   # Best: Install Gurobi (academic license free)
   ```

3. **Relax MIP gap**
   ```python
   # In solver_config: Set mip_gap = 0.05 (5% acceptable)
   # Finds near-optimal solution faster
   ```

---

### Problem: Results look unrealistic (all nurses work same shifts)

**Cause:** Demand too low or constraints too loose

**Solution:**
1. **Increase demand variability**
   ```python
   variation = random.uniform(-0.30, 0.30)  # ±30% instead of ±15%
   ```

2. **Add soft constraints**
   ```python
   c3 = 10  # Penalize stand-alone shifts
   c4 = 15  # Penalize unwanted patterns
   ```

3. **Enable advanced constraints**
   ```python
   n4 = 2  # Require weekend breaks
   night_rest_enabled = True  # Enforce night rest
   ```

---

## Summary Checklist

**Before generating instances:**
- [ ] Decide instance size (small/medium/large)
- [ ] Choose demand generation method
- [ ] Calculate appropriate parameters (scale from paper)
- [ ] Verify feasibility (capacity > demand)

**During generation:**
- [ ] Create nurse list with correct format
- [ ] Generate complete scenarios (no missing rows)
- [ ] Use exact shift codes: E, D, L, N
- [ ] Save with correct column names

**Before optimization:**
- [ ] Run validation script (completeness check)
- [ ] Verify no NaN or negative values
- [ ] Check parameter relationships (n3 ≤ n1, etc.)
- [ ] Estimate solve time based on size

**After solving:**
- [ ] Check solution status (Optimal expected)
- [ ] Validate results (constraints satisfied)
- [ ] Review nurse workloads (fair distribution)
- [ ] Analyze cost breakdown (reasonable values)

---

## Additional Resources

**Files in this repository:**
- `scripts/generate_nss_benchmark.py` - Automated instance generator
- `data/nss_benchmark_nurses.csv` - Example nurse list (20 nurses)
- `data/nss_benchmark_scenarios.csv` - Example scenarios (5 scenarios × 14 days)

**Paper reference:**
He, F., Chaussalet, T. J., & Qu, R. (2019). Controlling understaffing with conditional Value-at-Risk constraint for an integrated nurse scheduling problem under patient demand uncertainty. *Operations Research Perspectives*, 6, 100119.

**Need help?**
1. Check error messages in Streamlit app (detailed diagnostics)
2. Review validation checklist above
3. Try minimal test instance first
4. Use sample data generator in app for templates

---

**Last updated:** December 8, 2025  
**Version:** 1.0  
**Compatibility:** NSS v1.0+
