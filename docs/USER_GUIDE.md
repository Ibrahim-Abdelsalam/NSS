# 🏥 Nurse Scheduling System - Complete User Guide

Everything you need to know to use the system effectively.

---

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
cd NSS

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### First Schedule in 3 Steps

1. **Upload Data** (or use sample data)
   - Nurses: CSV with nurse names
   - Scenarios: CSV with columns `scenario,day,shift,demand`

2. **Set Parameters**
   - Basic constraints: `n1=15` (max shifts), `n3=5` (min regular)
   - Costs: `c1=$100` (regular), `c2=$150` (overtime), `q_plus=$200` (emergency)

3. **Click "🚀 Generate Schedule"**
   - Wait 5-60 seconds depending on problem size
   - View schedule, costs, and analysis

---

## 📊 Understanding the Model

### What Problem Does This Solve?

**The Challenge:** Schedule nurses to meet uncertain patient demand while:
- Minimizing costs (regular pay, overtime, emergency staff)
- Satisfying work rules (max shifts, weekends off, rest requirements)
- Meeting demand across multiple possible scenarios

**The Solution:** Two-stage stochastic optimization
- **Stage 1:** Create baseline schedule before knowing actual demand
- **Stage 2:** Adjust with emergency staff or cancellations after demand revealed
- **Goal:** Minimize expected total cost across all scenarios

### Key Concepts

**Shift Types:**
- `E` = Early (morning)
- `D` = Day (standard)
- `L` = Late (evening)
- `N` = Night (overnight)

**Nurse Types:**
- **Regular shifts:** Baseline schedule (cost = `c1` per shift)
- **Overtime shifts:** Extra shifts for baseline coverage (cost = `c2` per shift)
- **Emergency staff:** Called in after demand known (cost = `q_plus` per shift)

**Scenarios:**
- Each scenario = one possible demand pattern
- Model finds schedule that works well across all scenarios
- More scenarios = more robust but slower to solve

---

## ⚙️ Parameters Explained

### Basic Shift Constraints

**`n1` - Maximum Total Shifts Per Nurse**
- Default: 15 (for 14-day period)
- Higher = more flexible but risks overworking nurses
- Lower = need more nurses

**`n2` - Maximum Night Shifts Per Nurse**
- Default: 5
- Night work is taxing, needs strict limits
- Typical: 20-40% of `n1`

**`n3` - Minimum Regular Shifts Per Nurse**
- Default: 5
- ⚠️ **CRITICAL PARAMETER** - affects overtime vs emergency usage!
- Lower = more overtime capacity
- Higher = more emergency staff needed

**Why `n3` matters:**
```
Overtime capacity = n1 - n3

Example 1:  n1=15, n3=5  → 10 overtime slots available ✓
Example 2:  n1=15, n3=12 → 3 overtime slots available (forces emergency!) ✗
```

**`n4` - Minimum Complete Weekends Off**
- Default: 0 (disabled)
- Set to 1-2 for work-life balance
- Requires start date to detect weekends

### Cost Parameters

**`c1` - Regular Shift Cost**
- Base wage per shift
- Example: $100

**`c2` - Overtime Shift Cost**
- Premium pay for extra baseline shifts
- Typical: 1.2-1.5× regular cost
- Example: $150

**`q_plus` - Emergency Staff Cost**
- Very expensive! Adjusted after demand known
- Typical: 1.5-2× overtime cost
- Example: $200

**`q_minus` - Cancellation Cost**
- Usually 0 (no penalty for sending nurses home)
- Paper uses $2 (small penalty)

### Advanced Constraints

**Shift Type Quotas (Constraints 2-5)**
- Force min/max for each shift type
- Example: Each nurse must work 2-8 Early shifts, 3-10 Day shifts
- ⚠️ Can make problem infeasible if too restrictive!

**Night Rest Rules (Constraints 10-13)**
- No isolated single night shifts
- Minimum consecutive nights (default: 2)
- Mandatory days off after night sequence (default: 2)

**Weekend Rules (Constraint 9)**
- Guarantee complete Saturday+Sunday off
- Requires start date parameter

### Risk Management (CVaR)

**Model Type: SDM vs SDM-CVaR**
- **SDM:** Minimize expected cost only
- **SDM-CVaR:** Also control worst-case risk

**`sigma` - Confidence Level**
- Default: 0.95 (95% confidence)
- Higher = more risk-averse

**`mu` - Maximum Acceptable Shortage**
- Default: 5.0
- Constraint: "In worst (1-sigma)% scenarios, expected shortage ≤ mu"
- Example: sigma=0.95, mu=5 → "In worst 5% of cases, max 5 shifts short"

---

## 🎯 Common Use Cases

### Case 1: Minimize Cost (Standard Hospital)
```python
model_params = {
    'c1': 100,      # Regular: $100
    'c2': 150,      # Overtime: $150 (+50%)
    'q_plus': 200,  # Emergency: $200 (+100%)
    'n1': 15,       # Max shifts
    'n2': 5,        # Max nights
    'n3': 5,        # Min regular (allows 10 overtime)
}
model_type = "SDM"  # Just minimize expected cost
```

### Case 2: Risk-Averse (Critical Care Unit)
```python
model_params = {
    'c1': 120,      # Higher base wage
    'c2': 180,      # Overtime
    'q_plus': 300,  # Very expensive emergency
    'n1': 15,
    'n2': 4,        # Fewer night shifts
    'n3': 6,
    'sigma': 0.95,  # 95% confidence
    'mu': 3.0,      # Max 3 shifts short in worst 5%
}
model_type = "SDM-CVaR"  # Control worst-case risk
```

### Case 3: Work-Life Balance Focus
```python
model_params = {
    'c1': 100,
    'c2': 150,
    'q_plus': 200,
    'n1': 12,       # Lower max (avoid burnout)
    'n2': 3,        # Fewer nights
    'n3': 4,
    'n4': 2,        # Require 2 full weekends off
    'start_date': '2025-01-06',  # For weekend detection
    'night_rest_enabled': True,
    'min_consecutive_nights': 2,
    'days_off_after_nights': 2,
}
```

---

## 🐛 Troubleshooting

### "Infeasible" Result

**Possible causes:**
1. **Not enough nurses:** Total capacity < baseline demand
   - Fix: Add more nurses or reduce demand

2. **Constraints too tight:** Sum of minimums > maximum
   - Example: If shift quotas require min 15 shifts but `n1=12`
   - Fix: Relax shift quotas or increase `n1`

3. **Weekend constraint impossible:** Not enough weekends in period
   - Fix: Reduce `n4` or extend planning period

## 🐛 Troubleshooting

### "Infeasible" Result

**Possible causes:**
1. **Not enough nurses:** Total capacity < demand in worst scenario
   - Fix: Add more nurses or reduce peak demand

2. **Constraints too tight:** Sum of minimums > maximum
   - Example: If shift quotas require min 15 shifts but `n1=12`
   - Fix: Relax shift quotas or increase `n1`

3. **Weekend constraint impossible:** Not enough weekends in period
   - Fix: Reduce `n4` or extend planning period

### No Overtime Being Used (FIXED!)

**Previous Issue:** Model always used emergency staff instead of overtime

**Root Cause:** We incorrectly implemented baseline coverage as a HARD constraint
- Paper only has recourse constraint (Constraint 16): coverage via sr+so+α-β
- We added extra constraint forcing sr+so ≥ baseline demand
- This eliminated the model's flexibility to trade off overtime vs emergency

**Fix Applied (December 7, 2025):**
- Removed baseline coverage hard constraint
- Model now free to choose optimal mix of regular/overtime/emergency
- Overtime will be used when cheaper than emergency staff

**How It Works Now:**
```
Before (WRONG):
  Stage 1: Must schedule sr+so ≥ baseline demand (hard constraint)
  Stage 2: Use emergency (α) for excess demand
  Result: No overtime needed since baseline met

After (CORRECT):
  Stage 1: Schedule sr+so freely (no baseline constraint)
  Stage 2: Add emergency (α) or cancel (β) to meet actual demand
  Result: Model chooses cheapest option per scenario
          → Uses overtime when c2 < q_plus
```

### Solve Time Too Long (>5 minutes)

**For large problems:**
1. Reduce scenarios (100 → 20)
2. Reduce planning period (30 days → 14 days)
3. Use Gurobi solver (much faster than CBC)
4. Accept non-optimal solution (will finish within time limit)

---

## 📈 Interpreting Results

### Cost Breakdown

**Stage 1 Costs (Baseline Schedule):**
- Regular shifts: `total_regular_shifts × c1`
- Overtime shifts: `total_overtime_shifts × c2`
- **Total Stage 1:** Sum of above

**Stage 2 Costs (Recourse):**
- Emergency staff: Expected cost across all scenarios
- Cancellations: Usually $0
- **Total Stage 2:** Expected recourse cost

**Total Cost:** Stage 1 + Stage 2

### Scenario Analysis

**Key metrics per scenario:**
- `shortage_shifts`: Emergency nurses needed
- `overage_shifts`: Cancellations
- `scenario_cost`: Total cost for this scenario

**Look for:**
- High variance → uncertain demand
- Many shortages → need more baseline coverage or overtime capacity
- Pattern in worst scenarios → can adjust baseline schedule

### Risk Metrics (CVaR mode only)

**VaR (Value-at-Risk):**
- σ-quantile of shortage distribution
- Example: VaR₀.₉₅ = 3 means "95% of scenarios have ≤3 shortage"

**CVaR (Conditional VaR):**
- Average shortage in worst (1-σ)% of scenarios
- Example: CVaR₀.₉₅ = 5 means "average shortage in worst 5% = 5 shifts"

---

## 📁 Data Format

### Nurses CSV
```csv
nurse
Alice
Bob
Charlie
```

### Scenarios CSV
```csv
scenario,day,shift,demand
1,1,E,3
1,1,D,5
1,1,L,4
1,1,N,2
2,1,E,4
...
```

**Requirements:**
- `scenario`: Integer (1, 2, 3, ...)
- `day`: Integer (1 to num_days)
- `shift`: String ('E', 'D', 'L', 'N')
- `demand`: Integer (≥0)

---

## 🔧 Technical Details

### Architecture
- **`model.py`**: Optimization engine (PuLP + HiGHS/Gurobi/CBC)
- **`app.py`**: Web interface (Streamlit)
- **`solver_config.py`**: Solver selection and configuration

### Solvers
1. **HiGHS** (free, fastest free solver)
2. **CBC** (free, reliable fallback)
3. **Gurobi** (academic license, 10-100× faster for large problems)

### Problem Size
```
Variables: nurses × days × shifts × 2 (regular + overtime)
           + days × shifts × scenarios × 2 (emergency + cancel)

Constraints: ~100 per nurse + ~10 per day-shift-scenario

Example: 20 nurses, 14 days, 4 shifts, 10 scenarios
  → ~2,400 variables, ~2,200 constraints
  → Solve time: 5-20 seconds (HiGHS), 2-5 seconds (Gurobi)
```

---

## 📚 Further Reading

- **Research Paper:** He et al. (2019) - included in `docs/` folder
- **Test Examples:** `scripts/simple_overtime_test.py`
- **Advanced:** `docs/ADVANCED_CONSTRAINTS.md`

---

**Last Updated:** December 7, 2025
