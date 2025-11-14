# 📐 Mathematical Model Structure - Code Mapping

This document shows exactly where each mathematical component is implemented in `model.py`.

---

## 🎯 **OBJECTIVE FUNCTION**

### **Location in Code:** Lines ~85-110

### **Mathematical Formula:**
```
minimize: c₁ Σᵢⱼₖ sr_{ijk} + c₂ Σᵢⱼₖ so_{ijk} 
          + Σ_ω p^ω · (q⁺ Σⱼₖ α_{jk}^ω + q⁻ Σⱼₖ β_{jk}^ω)
```

### **Code Implementation:**
```python
# STAGE 1 COST: Regular wages + Overtime wages
stage1_cost = (
    c1 * pulp.lpSum(sr[i][j][k] for i in I_nurses for j in J_days for k in K_shifts) +
    c2 * pulp.lpSum(so[i][j][k] for i in I_nurses for j in J_days for k in K_shifts)
)

# STAGE 2 COST: Expected recourse cost
stage2_cost = pulp.lpSum(
    scenario_probability[w] * (
        q_plus * pulp.lpSum(alpha[j][k][w] for j in J_days for k in K_shifts) +
        q_minus * pulp.lpSum(beta[j][k][w] for j in J_days for k in K_shifts)
    )
    for w in W_scenarios
)

# TOTAL OBJECTIVE
prob += stage1_cost + stage2_cost, "Total_Cost"
```

### **Components:**
- **Stage 1 Cost**: Baseline schedule cost (before knowing demand)
- **Stage 2 Cost**: Expected adjustment cost (after observing demand)
- **c₁**: Regular shift wage ($)
- **c₂**: Overtime shift wage ($)
- **q⁺**: Emergency shift cost ($)
- **p^ω**: Probability of scenario ω

---

## 📊 **DECISION VARIABLES**

### **STAGE 1 VARIABLES** (First-Stage / Here-and-Now)
**Location:** Lines ~45-55

#### **Variable: sr_{ijk}**
```python
sr = pulp.LpVariable.dicts("RegularShift", 
                          (I_nurses, J_days, K_shifts), 
                          cat=pulp.LpBinary)
```
- **Type**: Binary (0 or 1)
- **Meaning**: 1 if nurse i works regular shift k on day j
- **Count**: |I| × |J| × |K| variables

#### **Variable: so_{ijk}**
```python
so = pulp.LpVariable.dicts("OvertimeShift", 
                          (I_nurses, J_days, K_shifts), 
                          cat=pulp.LpBinary)
```
- **Type**: Binary (0 or 1)
- **Meaning**: 1 if nurse i works overtime shift k on day j
- **Count**: |I| × |J| × |K| variables

---

### **STAGE 2 VARIABLES** (Second-Stage / Recourse)
**Location:** Lines ~60-75

#### **Variable: α_{jk}^ω**
```python
alpha = pulp.LpVariable.dicts("AddShift", 
                             (J_days, K_shifts, W_scenarios), 
                             lowBound=0, 
                             cat=pulp.LpContinuous)
```
- **Type**: Continuous (≥ 0)
- **Meaning**: Number of emergency shifts added in scenario ω
- **Count**: |J| × |K| × |Ω| variables

#### **Variable: β_{jk}^ω**
```python
beta = pulp.LpVariable.dicts("CancelShift", 
                            (J_days, K_shifts, W_scenarios), 
                            lowBound=0, 
                            cat=pulp.LpContinuous)
```
- **Type**: Continuous (≥ 0)
- **Meaning**: Number of shifts cancelled in scenario ω
- **Count**: |J| × |K| × |Ω| variables

---

### **CVaR VARIABLES** (Risk Management)
**Location:** Lines ~80-95 (only if SDM-CVaR)

#### **Variable: ξ (xi)**
```python
xi = pulp.LpVariable("VaR_xi", cat=pulp.LpContinuous)
```
- **Type**: Continuous (unbounded)
- **Meaning**: Value-at-Risk threshold at confidence level σ
- **Count**: 1 variable

#### **Variable: z^ω**
```python
z = pulp.LpVariable.dicts("ExcessLoss_z", 
                         (W_scenarios), 
                         lowBound=0, 
                         cat=pulp.LpContinuous)
```
- **Type**: Continuous (≥ 0)
- **Meaning**: Excess loss beyond VaR in scenario ω
- **Count**: |Ω| variables

---

## 🔗 **CONSTRAINTS**

### **Constraint 1: One Shift Per Day**
**Location:** Lines ~130-140  
**Paper Equation:** (1)

```
Mathematical: Σₖ (sr_{ijk} + so_{ijk}) ≤ 1  ∀i ∈ I, j ∈ J
```

```python
for i in I_nurses:
    for j in J_days:
        prob += (
            pulp.lpSum(sr[i][j][k] + so[i][j][k] for k in K_shifts) <= 1,
            f"OneShiftPerDay_{i}_{j}"
        )
```

**Count**: |I| × |J| constraints  
**Meaning**: Each nurse works at most one shift per day

---

### **Constraint 6: Maximum Total Shifts**
**Location:** Lines ~145-155  
**Paper Equation:** (6)

```
Mathematical: Σⱼₖ (sr_{ijk} + so_{ijk}) ≤ n₁  ∀i ∈ I
```

```python
for i in I_nurses:
    prob += (
        pulp.lpSum(sr[i][j][k] + so[i][j][k] for j in J_days for k in K_shifts) <= n1,
        f"MaxTotalShifts_{i}"
    )
```

**Count**: |I| constraints  
**Meaning**: Each nurse works at most n₁ shifts total

---

### **Constraint 7: Maximum Night Shifts**
**Location:** Lines ~160-170  
**Paper Equation:** (7)

```
Mathematical: Σⱼ (sr_{ijN} + so_{ijN}) ≤ n₂  ∀i ∈ I
```

```python
if 'N' in K_shifts:
    for i in I_nurses:
        prob += (
            pulp.lpSum(sr[i][j]['N'] + so[i][j]['N'] for j in J_days) <= n2,
            f"MaxNightShifts_{i}"
        )
```

**Count**: |I| constraints (if night shift exists)  
**Meaning**: Each nurse works at most n₂ night shifts

---

### **Constraint 8: Minimum Regular Shifts**
**Location:** Lines ~175-185  
**Paper Equation:** (8)

```
Mathematical: Σⱼₖ sr_{ijk} ≥ n₃  ∀i ∈ I
```

```python
for i in I_nurses:
    prob += (
        pulp.lpSum(sr[i][j][k] for j in J_days for k in K_shifts) >= n3,
        f"MinRegularShifts_{i}"
    )
```

**Count**: |I| constraints  
**Meaning**: Each nurse works at least n₃ regular shifts

---

### **Constraint 9: Minimum Weekends Off**
**Paper Equation:** (9)  
**Status**: ❌ **NOT IMPLEMENTED** (complex calendar logic required)

---

### **Constraints 10-13: Night Shift Rest**
**Paper Equations:** (10), (11), (12), (13)  
**Status**: ❌ **NOT IMPLEMENTED** (would add significant complexity)

---

### **Constraints 14-15: Soft Constraints**
**Paper Equations:** (14), (15)  
**Status**: ❌ **NOT IMPLEMENTED** (penalty terms omitted for simplicity)

---

### **Constraint 16: Demand Fulfillment (KEY RECOURSE CONSTRAINT)**
**Location:** Lines ~240-260  
**Paper Equation:** (16)

```
Mathematical: Σᵢ (sr_{ijk} + so_{ijk}) + α_{jk}^ω - β_{jk}^ω ≥ R_{jk}^ω
              ∀ω ∈ Ω, j ∈ J, k ∈ K
```

```python
for w in W_scenarios:
    for j in J_days:
        for k in K_shifts:
            prob += (
                pulp.lpSum(sr[i][j][k] + so[i][j][k] for i in I_nurses) +
                alpha[j][k][w] - beta[j][k][w]
                >= R_demand.get((j, k, w), 0),
                f"StaffingMet_{j}_{k}_{w}"
            )
```

**Count**: |Ω| × |J| × |K| constraints  
**Meaning**: Planned staff + emergency adds - cancellations ≥ demand  
**Importance**: ⭐⭐⭐ **CRITICAL** - Links Stage 1 and Stage 2!

---

### **Constraint 19: CVaR Upper Bound**
**Location:** Lines ~280-300  
**Paper Equation:** (19)  
**Only for**: SDM-CVaR model

```
Mathematical: ξ + (1/(1-σ)) Σ_ω p^ω z^ω ≤ μ
```

```python
if model_type == "SDM-CVaR":
    prob += (
        xi + (1.0 / (1.0 - sigma)) * 
        pulp.lpSum(scenario_probability[w] * z[w] for w in W_scenarios)
        <= mu,
        "CVaR_Constraint"
    )
```

**Count**: 1 constraint (CVaR model only)  
**Meaning**: Expected shortage in worst (1-σ)% scenarios ≤ μ

---

### **Constraint 20: Excess Loss Non-Negativity**
**Paper Equation:** (20)  
**Status**: ✅ Enforced by `lowBound=0` in variable definition

---

### **Constraint 22: Excess Loss Definition**
**Location:** Lines ~320-335  
**Paper Equation:** (22)  
**Only for**: SDM-CVaR model

```
Mathematical: z^ω ≥ Σⱼₖ α_{jk}^ω - ξ  ∀ω ∈ Ω
```

```python
if model_type == "SDM-CVaR":
    for w in W_scenarios:
        loss_function = pulp.lpSum(alpha[j][k][w] for j in J_days for k in K_shifts)
        
        prob += (
            z[w] >= loss_function - xi,
            f"ExcessLoss_{w}"
        )
```

**Count**: |Ω| constraints (CVaR model only)  
**Meaning**: z^ω captures loss exceeding VaR threshold

---

## 📈 **TWO-STAGE STRUCTURE**

### **STAGE 1: Here-and-Now Decisions**
**When**: Before observing actual demand  
**Variables**: sr_{ijk}, so_{ijk}  
**Decides**: Baseline nurse schedule

### **STAGE 2: Wait-and-See Decisions**
**When**: After observing demand in each scenario  
**Variables**: α_{jk}^ω, β_{jk}^ω  
**Decides**: Emergency adjustments

### **Linkage**: Constraint 16 connects both stages

---

## 🛡️ **CVaR RISK MANAGEMENT**

### **Standard Model (SDM)**
- Minimizes expected cost
- No risk control
- May have high variance in outcomes

### **CVaR Model (SDM-CVaR)**
- Minimizes expected cost
- **+ Controls tail risk**
- Guarantees: "Worst (1-σ)% scenarios have shortage ≤ μ"

### **CVaR Components**
1. **ξ (VaR)**: Threshold separating "normal" from "bad" scenarios
2. **z^ω**: How much scenario ω exceeds the threshold
3. **CVaR constraint**: Limits expected excess loss

---

## 📊 **MODEL SIZE SUMMARY**

For typical instance (10 nurses, 14 days, 4 shifts, 5 scenarios):

### **Variables**
- **Stage 1**: 10 × 14 × 4 × 2 = 1,120 binary variables
- **Stage 2**: 14 × 4 × 5 × 2 = 560 continuous variables
- **CVaR** (if used): 1 + 5 = 6 continuous variables
- **Total**: ~1,680 variables

### **Constraints**
- **Constraint 1**: 10 × 14 = 140
- **Constraint 6**: 10 = 10
- **Constraint 7**: 10 = 10
- **Constraint 8**: 10 = 10
- **Constraint 16**: 5 × 14 × 4 = 280
- **CVaR** (if used): 1 + 5 = 6
- **Total**: ~450 constraints

---

## 🎯 **IMPLEMENTED vs NOT IMPLEMENTED**

### ✅ **Implemented (Core Model)**
1. Objective function (Stage 1 + Stage 2 costs)
2. Constraint 1 (One shift per day)
3. Constraint 6 (Max total shifts)
4. Constraint 7 (Max night shifts)
5. Constraint 8 (Min regular shifts)
6. Constraint 16 (Demand fulfillment) ⭐ **CRITICAL**
7. Constraint 19 (CVaR limit - if SDM-CVaR)
8. Constraint 22 (Excess loss - if SDM-CVaR)

### ❌ **Not Implemented (Can be added)**
1. Constraint 9 (Min weekends off)
2. Constraints 10-13 (Night shift rest requirements)
3. Constraints 14-15 (Soft constraints with penalties)
4. Linking constraints 2-4 (SR_i, SO_i indicator variables)

### **Impact of Omissions**
- Model is still **valid and functional**
- Solutions meet core requirements
- May have some undesirable patterns (no consecutive night shifts enforced)
- Weekend distribution not explicitly controlled

---

## 🔍 **Finding Components in Code**

### **Quick Reference**
- **Objective Function**: Search for `"Total_Cost"`
- **Stage 1 Variables**: Search for `"RegularShift"` and `"OvertimeShift"`
- **Stage 2 Variables**: Search for `"AddShift"` and `"CancelShift"`
- **CVaR Variables**: Search for `"VaR_xi"` and `"ExcessLoss_z"`
- **Constraint 1**: Search for `"OneShiftPerDay"`
- **Constraint 16**: Search for `"StaffingMet"` ⭐
- **CVaR Constraint**: Search for `"CVaR_Constraint"`

---

## 📚 **Mathematical Notation Guide**

| Symbol | Code Variable | Meaning |
|--------|---------------|---------|
| sr_{ijk} | `sr[i][j][k]` | Regular shift assignment |
| so_{ijk} | `so[i][j][k]` | Overtime shift assignment |
| α_{jk}^ω | `alpha[j][k][w]` | Emergency shifts added |
| β_{jk}^ω | `beta[j][k][w]` | Shifts cancelled |
| ξ | `xi` | Value-at-Risk threshold |
| z^ω | `z[w]` | Excess loss in scenario ω |
| c₁ | `c1` | Regular shift cost |
| c₂ | `c2` | Overtime shift cost |
| q⁺ | `q_plus` | Emergency shift cost |
| n₁ | `n1` | Max total shifts |
| n₂ | `n2` | Max night shifts |
| n₃ | `n3` | Min regular shifts |
| σ | `sigma` | CVaR confidence level |
| μ | `mu` | CVaR upper bound |
| R_{jk}^ω | `R_demand[(j,k,w)]` | Demand in scenario ω |

---

**This mapping shows exactly how the mathematical model from the paper is translated into working code!**
