# 📋 Complete Parameter Guide

## Based on Your Streamlit App Interface (December 8, 2025)

---

## 💰 **Cost Parameters**

These define the **cost hierarchy** that drives the model's decisions:

```
Regular (c1) < Overtime (c2) < Emergency (q+)
```

### **Stage 1 Costs** (Planned in advance)
| Parameter | Symbol | Your Value | Description |
|-----------|--------|------------|-------------|
| **Regular Shift Cost** | `c1` | £100.00 | Cost per regular shift (cheapest) |
| **Overtime Shift Cost** | `c2` | £150.00 | Cost per overtime shift |

### **Stage 2 Costs** (Recourse/adjustment)
| Parameter | Symbol | Your Value | Description |
|-----------|--------|------------|-------------|
| **Emergency Shift Cost** | `q+` | £200.00 | Cost to call in emergency staff (most expensive) |
| **Cancellation Cost** | `q-` | £0.00 | Cost to cancel a planned shift (usually 0) |

**💡 How the model chooses:**
1. First preference: **Regular shifts** (£100) ✅
2. Second preference: **Overtime** (£150) - but limited by `n1 - n3`
3. Last resort: **Emergency staff** (£200) - unlimited but costly

---

## 📋 **Work Rules (Hard Constraints)**

### **⚖️ Basic Shift Constraints**

| Parameter | Symbol | Your Value | Range | Description |
|-----------|--------|------------|-------|-------------|
| **Max Total Shifts** | `n1` | **15** | 1-30 | Max shifts per nurse in planning period |
| **Max Night Shifts** | `n2` | **7** | 1-15 | Max night shifts per nurse (health limit) |
| **Min Regular Shifts** | `n3` | **8** | 0-20 | Min regular shifts IF nurse works at all |
| **Enforce Max Regular** | `enforce_max_regular` | **False** | True/False | If True, caps regular shifts at n3 (forces overtime) |

**📊 Overtime Behavior:**

Without `enforce_max_regular` (default):
```
Regular shifts: 0 to n1 per nurse (model chooses cheapest)
Overtime shifts: Rarely used (more expensive than regular)
→ Model assigns all Stage 1 shifts as "regular" (£100)
```

With `enforce_max_regular=True`:
```
Regular shifts: Exactly n3 per nurse (if working)
Overtime shifts: n3+1 to n1 per nurse
Overtime capacity = n1 - n3 = 15 - 8 = 7 shifts/nurse
→ Model MUST use overtime for shifts beyond n3
```

**⚠️ Your Current Issue:**
- With **n3 = 8**, each working nurse MUST do ≥8 regular shifts
- For a **7-day period**, that's more than 1 shift/day on average
- With **low nurse count** and **high demand**, the model finds it cheaper to use **100% emergency staff** instead

**💡 Solution:**
```python
# Option 1: Lower n3 to allow part-time work
'n3': 4  # Now nurses can do 4-15 shifts (more flexible)

# Option 2: Add more nurses
# 10+ nurses instead of 5-6

# Option 3: Reduce planning period
# Use 3-4 days instead of 7 days
```

---

## 📊 **Data Structure**

Based on your uploaded files:

```
✓ Loaded 10 nurses        (sample_nurses.csv)
✓ Loaded 84 demand records (sample_scenarios.csv)
✓ Structure: 3 scenarios × 7 days × 4 shifts
```

### **Nurses CSV Format:**
```csv
Nurse
Alice
Bob
Charlie
Diana
Emma
Frank
George
Helen
Iris
Jack
```

### **Scenarios CSV Format:**
```csv
scenario,day,shift,demand
1,1,E,2
1,1,D,3
1,1,L,2
1,1,N,2
2,1,E,3
2,1,D,4
...
```

**Column Definitions:**
- `scenario`: Scenario number (1, 2, 3, ...)
- `day`: Day in planning period (1-7)
- `shift`: Shift type (E=Early, D=Day, L=Late, N=Night)
- `demand`: Number of nurses needed

---

## 🎯 **Optimization Model Types**

### **1. Cost Optimization (SDM)** ← *You selected this*
- Minimizes expected total cost
- Simple and fast
- Best for: Normal operations

### **2. Risk-Averse (SDM-CVaR)**
- Minimizes cost + controls worst-case risk
- Requires additional parameters:
  - `sigma`: Confidence level (e.g., 0.95 = 95%)
  - `mu`: Max acceptable shortage in worst scenarios

---

## ⚙️ **Solver Configuration**

### **Your Selection: AUTO (Recommended)**
- Auto-selected: **GUROBI** (10-20× faster than CBC)
- You have Gurobi academic license ✅
- Solve time: **0.1 seconds** (extremely fast!)

### **Available Solvers:**
| Solver | Speed | License | Best For |
|--------|-------|---------|----------|
| **GUROBI** | ⚡⚡⚡ Fastest | Academic (free) | Large problems |
| HiGHS | ⚡⚡ Fast | Free | Medium problems |
| CBC | ⚡ Slow | Free | Small problems |

---

## 🚨 **Advanced Constraints** (All Disabled in Your Test)

### **🏖️ Weekend Constraints**
```python
'n4': 0  # Min complete weekends off (DISABLED)
'start_date': None
```
- When `n4 > 0`: Requires nurses to have full weekends (Sat+Sun) off
- Needs `start_date` to detect which days are weekends

### **🌙 Night Shift Rest Rules**
```python
'night_rest_enabled': False  # DISABLED
'min_consecutive_nights': 2
'days_off_after_nights': 2
```
- Prevents isolated single night shifts (health hazard)
- Ensures recovery time after night sequences

### **📊 Shift Type Quotas**
```python
'shift_quotas': {}  # DISABLED
```
Example when enabled:
```python
'shift_quotas': {
    'E': {'min': 2, 'max': 8},  # Each nurse: 2-8 Early shifts
    'D': {'min': 3, 'max': 10}  # Each nurse: 3-10 Day shifts
}
```

### **⚠️ Quality Penalties (Soft Constraints)**
```python
'c3': 10.0   # Penalty for stand-alone shifts (isolated working days)
'c4': 15.0   # Penalty for unwanted patterns (D→E, L→E, etc.)
```
These don't prevent solutions, just make them less desirable.

### **🚨 Recourse Bounds**
```python
'max_emergency_staff': inf  # UNLIMITED (default)
'max_cancellations': inf    # UNLIMITED (default)
```
Set finite values to cap emergency staff usage:
```python
'max_emergency_staff': 3  # Max 3 emergency nurses per shift
```

---

## 🔍 **Your Current Results**

### **Problem:**
```
✅ Optimal solution found in 0.1s
❌ Schedule dataframe is empty!
❌ 0 assigned shifts (100% emergency staff)
```

### **Why This Happened:**

With your parameters:
- `n1 = 15`: Max 15 shifts per nurse
- `n3 = 8`: Must do ≥8 regular shifts if working
- **7-day period** with **high demand** (avg 8.7 nurses/day)
- Only **10 nurses** available

**Model's calculation:**
```
If nurse works: Must do ≥8 regular shifts @ £100 = £800 minimum
7-day period means: Limited overtime capacity (15-8 = 7 overtime shifts)
High demand spikes: Need 12+ nurses on some days

Cost comparison:
- Option A: Schedule nurses (£800+ per nurse)
- Option B: Use emergency staff (£200/shift as needed)

Result: Option B is cheaper! Use 100% emergency staff.
```

---

## ✅ **Recommended Fix**

### **Option 1: Lower n3 (More Flexible Scheduling)**
```python
'n3': 4  # Allow part-time work (4-15 shifts instead of 8-15)
```
This makes regular/overtime more attractive.

### **Option 2: Add More Nurses**
Use **15-20 nurses** instead of 10 for a 7-day period.

### **Option 3: Shorter Planning Period**
Use **3-4 days** instead of 7 days.

### **Option 4: Make Emergency More Expensive**
```python
'q_plus': 300  # Increase from £200 to £300
```
This forces the model to prefer regular/overtime.

---

## 📊 **Expected Output (After Fix)**

With `n3 = 4`:
```
Total Cost: £4,000-£6,000
Regular Shifts: 30-40 (60-80%)
Overtime Shifts: 5-10 (10-15%)
Emergency Shifts: 10-15 (20-25%)
Capacity Used: 60-80%
```

---

## 🎯 **Quick Reference Card**

```
PROBLEM SIZE:
├─ 730 decision variables
├─ 672 constraints  
└─ Complexity: Fast (<1 second)

CURRENT SETTINGS:
├─ Costs: £100 / £150 / £200
├─ Work rules: n1=15, n2=7, n3=8
├─ Advanced: All disabled
└─ Model: SDM (cost optimization)

RESULT:
├─ Status: Optimal ✅
├─ Solve time: 0.1s ⚡
├─ Strategy: 100% emergency (cost-optimal given constraints)
└─ Action needed: Adjust n3 or add nurses
```

---

## 📝 **Test Again**

1. In Streamlit app, change **Min Regular Shifts (n3)** to **4**
2. Click **Generate Schedule**
3. You should now see:
   - ✅ Nurses scheduled with regular/overtime shifts
   - ✅ Lower reliance on emergency staff
   - ✅ Non-empty roster dataframe

---

**Generated:** December 8, 2025  
**Your Setup:** 10 nurses, 7 days, 3 scenarios, Gurobi solver
