# 🧪 Overtime Test Instance - Quick Reference

## 📁 Files Created
- **Nurses:** `data/overtime_test_nurses.csv` (10 nurses)
- **Scenarios:** `data/overtime_test_scenarios.csv` (3 scenarios, 14 days, 2 shifts)

## 🎯 How to Test in Streamlit Interface

### **Step 1: Upload Files**
1. Go to Streamlit app (run `streamlit run app.py`)
2. Upload `overtime_test_nurses.csv`
3. Upload `overtime_test_scenarios.csv`

### **Step 2: Configure Parameters**

#### **To See Overtime - Use These Settings:**

**Cost Parameters:**
- Regular shift cost (c1): `100`
- Overtime shift cost (c2): `150`
- Emergency staff cost (q+): `300` ← Higher to make overtime attractive

**Work Rules:**
- Max total shifts per nurse (n1): `14`
- Max night shifts per nurse (n2): `7`
- Min regular shifts per nurse (n3): `5` ← Key parameter!
- ⭐ **CRITICAL:** Check "**Enforce Max Regular Shifts (Force Overtime)**" ✅

**Why These Settings Work:**
- Total demand: ~126 shifts (3 scenarios avg)
- 10 nurses × 5 regular = 50 regular shifts max
- Remaining ~76 shifts must use overtime or emergency
- With high q+ (£300), model prefers overtime (£150) over emergency

### **Step 3: Expected Results**

**With `enforce_max_regular=True`:**
```
Regular shifts: 50 (exactly 10 × 5)
Overtime shifts: 40-50 (depends on scenarios)
Emergency staff: 20-30 (for peak demands)
Total cost: ~£22,000-£25,000
```

**Without `enforce_max_regular` (comparison):**
```
Regular shifts: 90-100 (model uses all regular)
Overtime shifts: 0 (never used - economically inferior)
Emergency staff: 30-40
Total cost: ~£18,000-£20,000 (lower but no overtime)
```

## 📊 Problem Statistics

**Nurses:** 10
- Alice, Bob, Carol, Dave, Eve, Frank, Grace, Henry, Iris, Jack

**Days:** 14 (2 weeks)

**Shifts:** 2 (D=Day, N=Night)

**Scenarios:** 3 (Low, Medium, High demand)
- Scenario 1 (Low): ~84 shifts total
- Scenario 2 (Medium): ~126 shifts total  
- Scenario 3 (High): ~168 shifts total

**Average demand per shift:**
- Day shift: 6-8 nurses
- Night shift: 3-4 nurses

## 🎛️ Parameter Sensitivity Tests

### **Test 1: Vary n3 (Min Regular Shifts)**
- n3=3: 30 regular, 60+ overtime
- n3=5: 50 regular, 40+ overtime ✅ **RECOMMENDED**
- n3=7: 70 regular, 20+ overtime
- n3=10: 100 regular, 0 overtime (tight constraint)

### **Test 2: Vary Emergency Cost (q+)**
- q+=200: May prefer emergency over overtime
- q+=300: Good balance ✅ **RECOMMENDED**
- q+=500: Strong preference for overtime

### **Test 3: With/Without Max Regular Enforcement**
| Setting | Regular | Overtime | Result |
|---------|---------|----------|--------|
| enforce_max_regular=False | 90-100 | 0 | ❌ No overtime |
| enforce_max_regular=True | 50 | 40-50 | ✅ Overtime works! |

## 🔍 What to Look For in Results

**In the Schedule Table:**
- Look for shifts marked "D (OT)" or "N (OT)"
- Each nurse should have exactly 5 regular shifts
- Remaining shifts should be overtime

**In the Cost Breakdown:**
- Stage 1 Regular Cost: £5,000 (50 × £100)
- Stage 1 Overtime Cost: £6,000-£7,500 (40-50 × £150)
- Stage 2 Emergency Cost: £6,000-£9,000

**In the Nurse Summary:**
- Total Regular: Should show 50
- Total Overtime: Should show 40-50
- Each nurse: 5 regular + 4-5 overtime

## ⚡ Quick Copy-Paste Settings

```
c1 = 100
c2 = 150
q_plus = 300
n1 = 14
n2 = 7
n3 = 5
☑️ Enforce Max Regular Shifts (Force Overtime)
```

## 🐛 Troubleshooting

**Problem:** No overtime showing
- ✅ Check: "Enforce Max Regular Shifts" is CHECKED
- ✅ Check: n3 < average shifts per nurse
- ✅ Check: q+ > c2 (emergency more expensive than overtime)

**Problem:** Too much emergency staff
- Lower q+ (make emergency cheaper)
- Increase n1 (allow more shifts per nurse)
- Add more nurses

**Problem:** Model infeasible
- Increase n1 (max shifts per nurse)
- Add more nurses
- Check n3 ≤ n1

---

**File:** OVERTIME_TEST_GUIDE.md  
**Date:** December 8, 2025  
**Purpose:** Quick reference for testing overtime functionality in Streamlit
