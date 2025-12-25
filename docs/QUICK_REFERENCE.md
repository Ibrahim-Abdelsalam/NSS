# 🎯 Quick Test Instance - Copy & Paste Ready

## To Test Overtime in Python

```python
import pandas as pd
from model import build_and_solve_model, extract_results

# 1. NURSES (8 nurses)
nurses = ['Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank', 'Grace', 'Henry']

# 2. SCENARIOS (3 scenarios × 7 days × 2 shifts)
scenarios_df = pd.DataFrame([
    # Scenario 1 (Baseline - 42 shifts total)
    *[{'scenario': 1, 'day': d, 'shift': 'D', 'demand': 4} for d in range(1, 8)],
    *[{'scenario': 1, 'day': d, 'shift': 'N', 'demand': 2} for d in range(1, 8)],
    # Scenario 2 (Medium - 49 shifts total)
    *[{'scenario': 2, 'day': d, 'shift': 'D', 'demand': 5} for d in range(1, 8)],
    *[{'scenario': 2, 'day': d, 'shift': 'N', 'demand': 2} for d in range(1, 8)],
    # Scenario 3 (High - 56 shifts total)
    *[{'scenario': 3, 'day': d, 'shift': 'D', 'demand': 6} for d in range(1, 8)],
    *[{'scenario': 3, 'day': d, 'shift': 'N', 'demand': 2} for d in range(1, 8)],
])

# 3. PARAMETERS
params = {
    # Costs
    'c1': 100, 'c2': 150, 'q_plus': 200, 'q_minus': 0,
    'c3': 5, 'c4': 5,
    
    # Work rules
    'n1': 12,  # Max 12 shifts per nurse
    'n3': 5,   # Min 5 regular shifts (if working)
    'n2': 5,   # Max 5 night shifts
    'n4': 0,
    
    # ⭐ KEY: Force overtime for shifts beyond n3
    'enforce_max_regular': True,
    
    # Advanced (disabled for simplicity)
    'shift_quotas': {},
    'night_rest_enabled': False,
    'start_date': None,
    'max_emergency_staff': float('inf'),
}

# 4. RUN
prob, status = build_and_solve_model(nurses, scenarios_df, params)
results = extract_results(prob, nurses, scenarios_df, params)

# 5. SHOW RESULTS
cost = results['cost_breakdown']
print(f"Regular:  {cost['total_regular_shifts']} shifts")
print(f"Overtime: {cost['total_overtime_shifts']} shifts")
print(f"Total:    £{cost['total_cost']:,.2f}")
```

## Expected Output

```
Regular:  40 shifts  (8 nurses × 5 = 40)
Overtime: 2 shifts   ✅ (proves overtime works!)
Total:    £5,700.00
```

## To Test in Streamlit

1. **Upload Files:**
   - `data/test_overtime_nurses.csv` (created by scripts/simple_overtime_test.py)
   - `data/test_overtime_scenarios.csv`

2. **Set Parameters:**
   - Max Total Shifts (n1): **12**
   - Min Regular Shifts (n3): **5**
   - ✅ Check: **"Enforce Max Regular Shifts (Force Overtime)"**
   - Regular cost (c1): **100**
   - Overtime cost (c2): **150**
   - Emergency cost (q+): **200**

3. **Run & Expect:**
   - Regular: ~40 shifts
   - Overtime: >0 shifts (should see some!)
   - Total cost: ~£5,000-£6,000

## Parameter Explanation

| Parameter | Value | Why |
|-----------|-------|-----|
| **n1 = 12** | Max shifts | 12 shifts over 7 days = ~1.7 shifts/day (reasonable) |
| **n3 = 5** | Min regular | 5 shifts is minimum commitment if working |
| **Overtime capacity** | 7 | = n1 - n3 = 12 - 5 = 7 possible overtime shifts/nurse |
| **Regular cap** | 40 | = 8 nurses × 5 = 40 max regular shifts total |
| **Baseline demand** | 42 | Exceeds regular capacity → forces overtime/emergency |
| **enforce_max_regular** | True | ⭐ Without this, model uses 98 regular, 0 overtime |

## What Changes Without enforce_max_regular?

```python
# WITH enforce_max_regular=True:
Regular:  40 shifts (capped at n3 × nurses)
Overtime:  2 shifts (for demand beyond 40)
Result: ✅ Clear separation

# WITHOUT enforce_max_regular=False (paper mode):
Regular:  98 shifts (all Stage 1 shifts)
Overtime:  0 shifts (never used)
Result: ❌ No overtime, but mathematically valid per paper
```

## Quick Diagnosis

**If overtime = 0:**
- ✅ Check `enforce_max_regular = True` is set
- ✅ Check `n3 < average shifts per nurse`
- ✅ Check demand > regular capacity (n3 × nurses)
- ✅ Check c2 > c1 (overtime more expensive than regular)

**If all emergency (0 regular shifts):**
- ⚠️ n3 is too high - reduce it!
- For 7-day period, use n3 = 4-6
- For 28-day period, use n3 = 12-16 (as in paper)

---

**File:** QUICK_REFERENCE.md  
**Run:** `python COMPLETE_TEST_INSTANCE.py` for full demo
