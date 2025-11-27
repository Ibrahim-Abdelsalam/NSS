# Small Validation Test — Calculation Explanation

This document shows an exact, step-by-step calculation for a minimal two-stage nurse-scheduling validation test.

📁 File 1: `small_nurses.csv`

```csv
Nurse_1
Nurse_2
```

📁 File 2: `small_scenarios.csv`

```csv
scenario,day,shift,demand
1,1,E,1
1,1,D,0
1,1,L,1
1,1,N,0
1,2,E,1
1,2,D,0
1,2,L,1
1,2,N,0
1,3,E,1
1,3,D,0
1,3,L,1
1,3,N,0
2,1,E,2
2,1,D,0
2,1,L,1
2,1,N,0
2,2,E,1
2,2,D,0
2,2,L,2
2,2,N,0
2,3,E,2
2,3,D,0
2,3,L,2
2,3,N,0
```

---

⚙️ Application Configuration

After uploading these files, configure your application exactly as follows:

```
📊 Data Source
✓ Upload Custom Data

💰 Cost Parameters
Regular Shift Cost (c1): 100.00
Overtime Shift Cost (c2): 150.00
Emergency Shift Cost (q+): 200.00
Shift Cancellation Cost (q-): 2.00

⚖️ Work Rules
Max Total Shifts (n1): 3
Max Night Shifts (n2): 1
Min Regular Shifts (n3): 1

🎯 Optimization Model
Cost Optimization (SDM)

⚙️ Solver Configuration
AUTO (Recommended)
```

---

## Exact detailed calculations for the small validation test

### Baseline Demand (Scenario 1)

```
Day 1: E=1, L=1
Day 2: E=1, L=1
Day 3: E=1, L=1
Total: 6 shifts
```

### High Demand (Scenario 2)

```
Day 1: E=2, L=1
Day 2: E=1, L=2
Day 3: E=2, L=2
Total: 10 shifts
```

### Probabilities

```
Scenario 1: 50% (0.5)
Scenario 2: 50% (0.5)
```

---

### 🧮 STEP 1: FIRST-STAGE CALCULATIONS

Goal: Meet baseline demand (6 shifts) with available nurses.

- Nurses: `Nurse_1`, `Nurse_2`
- Each nurse max total shifts `n1 = 3` → total capacity = 2 × 3 = 6 shifts

Optimal First-Stage Assignment (feasible and simple):

- `Nurse_1`: E on Day 1, E on Day 2, E on Day 3 → 3 shifts
- `Nurse_2`: L on Day 1, L on Day 2, L on Day 3 → 3 shifts

First-Stage Cost Calculation:

```
Regular shifts: 6 shifts × $100 = $600
Overtime shifts: 0 shifts × $150 = $0

Total First-Stage Cost = $600
```

---

### 🧮 STEP 2: SECOND-STAGE CALCULATIONS

Recourse actions are computed per scenario.

#### Scenario 1 (Low Demand - 50% probability)

The first-stage schedule exactly matches Scenario 1 demands.

Recourse Actions:

- Added shifts (α): 0
- Cancelled shifts (β): 0

Recourse Cost for Scenario 1:

```
Emergency shifts: 0 × $200 = $0
Cancellations: 0 × $2 = $0

Total = $0
```

#### Scenario 2 (High Demand - 50% probability)

Compare first-stage assignments to scenario 2 demands day-by-day.

Day 1:
- Early (E): Have 1, Need 2 → Shortage 1 → Add 1 emergency shift (α)
- Late (L): Have 1, Need 1 → No adjustment

Cost Day 1: 1 × $200 = $200

Day 2:
- Early (E): Have 1, Need 1 → No adjustment
- Late (L): Have 1, Need 2 → Shortage 1 → Add 1 emergency shift (α)

Cost Day 2: 1 × $200 = $200

Day 3:
- Early (E): Have 1, Need 2 → Shortage 1 → Add 1 emergency shift (α)
- Late (L): Have 1, Need 2 → Shortage 1 → Add 1 emergency shift (α)

Cost Day 3: 2 × $200 = $400

Total Recourse Actions for Scenario 2:

```
Added shifts (α): 1 + 1 + 1 + 1 = 4 emergency shifts
Cancelled shifts (β): 0

Recourse Cost for Scenario 2:
Emergency shifts: 4 × $200 = $800
Cancellations: 0 × $2 = $0

Total = $800
```

---

### 🧮 STEP 3: EXPECTED VALUE CALCULATIONS

Expected Recourse Cost:

```
(Probability_Scenario1 × Cost_Scenario1) + (Probability_Scenario2 × Cost_Scenario2)
= (0.5 × $0) + (0.5 × $800)
= $0 + $400
= $400
```

### 🧮 STEP 4: TOTAL COST CALCULATION

```
Total Cost = First-Stage Cost + Expected Recourse Cost
= $600 + $400
= $1,000
```

---

## 📋 SUMMARY OF ALL CALCULATIONS

| Component | Calculation | Amount |
|---|---:|---:|
| First-Stage | 6 regular shifts × $100 | $600 |
| Scenario 1 Recourse | 0.5 × $0 | $0 |
| Scenario 2 Recourse | 0.5 × $800 | $400 |
| Expected Recourse | $0 + $400 | $400 |
| **TOTAL COST** | $600 + $400 | **$1,000** |
