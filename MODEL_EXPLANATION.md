# Model.py Deep Dive - Sequential Code Analysis

**File**: `model.py`
**Total Lines**: 2,389
**Structure**: Linear analysis from Import to Export.

---

## 1. Setup & Definitions (Lines 1-404)

### Helper Functions
*   **Lines 9-69**: `create_pwl_fatigue_approximation`: Pre-calculates physics for the PWL model.
*   **Lines 72-179**: `validate_capacity_feasibility`: The "Pre-Flight Check". Calculates `Total Supply` vs `Total Demand`.

---

## 2. Variables & Objective (Lines 405-659)

### Stage 1 Variables (Lines 405-490)
```python
# Line 408
sr = pulp.LpVariable.dicts("RegularShift", ...)
# Line 414
so = pulp.LpVariable.dicts("OvertimeShift", ...)
# Line 420
SR = pulp.LpVariable.dicts("SR", ...)
```
**Explanation**: Define the schedule ($x, y$) and participation ($SR$).

### Stage 2 Variables (Lines 556-570)
```python
# Line 560
alpha = pulp.LpVariable.dicts("AddShift", ...)
```
**Explanation**: Recourse variables for each scenario.

### Objective Function (Lines 616-654)
```python
# Line 651
prob += stage1_cost + soft_penalty_cost + stage2_cost + patient_safety_cost
```
**Explanation**: Sums all cost components.

---

## 3. Basic Schedules Constraints (Lines 660-800)

### Constraint 1: One Shift Per Day (Line 668)
```python
prob += pulp.lpSum(sr + so) <= 1
```
**Logic**: Physical impossibility of working two shifts.

### Constraint 6: Max Total Shifts (Line 771)
```python
prob += pulp.lpSum(all_shifts) <= n1
```
**Logic**: Global workload cap.

### Constraint 7: Max Night Shifts (Line 783)
```python
prob += pulp.lpSum(night_shifts) <= n2
```
**Logic**: Burnout prevention.

---

## 4. Advanced Logic Constraints (Lines 839-900)

### Constraint 8: Regular Shift Quota (Line 839)
**The "Zero Shift" Loophole.**
```python
# Line 853
if allow_overtime_paradox:
    prob += sum(...) >= n3 * SR[i]
else:
    prob += sum(...) == n3 * SR[i]
```
**Logic**:
*   `SR=0` $\to$ Quota=0.
*   `SR=1` $\to$ Quota=$n_3$.

### Constraint 9: Weekends Off (Line 867)
```python
# Line 898
prob += sum(weekend_off) >= n4
```
**Logic**: Forces complete weekends (Sat+Sun) free.

---

## 5. Pattern Constraints (Lines 900-1050)

### Constraint 10: No Stand-Alone Nights (Line 930)
```python
prob += night_seq_start >= current - prev
```
**Logic**: Forces nights to happen in blocks (e.g., N-N-N) rather than N-D-N.

### Constraint 14/15: Soft Penalties (Line 998)
**Logic**: Detects "Unwanted Patterns" (e.g., Late-to-Early) via variables `dev1`, `dev2` and adds cost.

---

## 6. Stochastic Constraints (Lines 1056-1130)

### Constraint 16: Supply-Demand (Line 1056)
**The Heart of the Model.**
```python
# Line 1085
prob += sum(sr+so) + alpha[w] - beta[w] >= Demand[w]
```
**Logic**: Ensures every scenario $\omega$ is covered, hiring `alpha` if needed.

---

## 7. CVaR Constraints (Lines 1144-1200)

### Constraint 19: Risk Budget (Line 1151)
```python
# Line 1173
xi + (multiplier * mean_tail_loss) <= mu
```
**Logic**: Only active if `SDM-CVaR` is selected. Limits tail risk.

---

## 8. Fatigue Model (Lines 1210-1400)

### Constraint F1: Accumulation (Line 1231)
```python
# Line 1255
T[j] == T[j-1] + 12 * Worked
```
**Logic**: Tracks cumulative hours.

### Constraint F4: Curve Mapping (Line 1299)
```python
# Line 1307
F[j] == sum(lambda[s] * breakpoints[s])
```
**Logic**: Uses SOS2 to interpolate the exponential fatigue cost.

---

## 9. Solution Processing (Lines 1459-End)

### Extraction (Line 1459)
**Logic**: Iterates over `prob.variables()`. If `varValue == 1`, adds entry to `roster_df`.
