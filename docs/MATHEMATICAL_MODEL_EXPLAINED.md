# Mathematical Model Deep Dive: Complete Variable & Constraint Guide

## Table of Contents
1. [Model Overview](#model-overview)
2. [Sets (Index Sets)](#sets-index-sets)
3. [Parameters (Input Data)](#parameters-input-data)
4. [Decision Variables](#decision-variables)
5. [Objective Function](#objective-function)
6. [Constraints Explained](#constraints-explained)
7. [Code-to-Math Mapping](#code-to-math-mapping)

---

## Model Overview

**Type:** Two-Stage Stochastic Mixed Integer Linear Program (MILP)

**Purpose:** Create a nurse schedule that:
- Minimizes total cost (wages + emergency staff)
- Satisfies work rules and regulations
- Handles uncertain patient demand across multiple scenarios
- Optionally controls worst-case shortage risk (CVaR)

**Two-Stage Structure:**
```
Stage 1 (Here-and-Now):
├─ Make decisions BEFORE knowing actual demand
├─ Decide: Which nurses work which shifts on which days?
└─ Variables: sr, so (regular/overtime shift assignments)

Stage 2 (Wait-and-See / Recourse):
├─ Make decisions AFTER demand is revealed (for each scenario)
├─ Decide: Add emergency staff? Cancel shifts?
└─ Variables: α, β (additions/cancellations per scenario)
```

---

## Sets (Index Sets)

Sets define the "dimensions" of our problem. Every decision variable is indexed by combinations of these sets.

### **I_nurses** - Set of Nurses
```python
I_nurses = nurses_list  # e.g., ['Alice', 'Bob', 'Charlie', ...]
```
- **Mathematical notation:** `I` or `i ∈ I`
- **Meaning:** All nurses available for scheduling
- **Cardinality:** `|I|` = number of nurses (e.g., 10, 50, 100)
- **Usage:** Index for "which nurse" in decision variables

### **J_days** - Set of Days
```python
J_days = scenarios_df['day'].unique()  # e.g., [1, 2, 3, ..., 14]
```
- **Mathematical notation:** `J` or `j ∈ J`
- **Meaning:** All days in the planning period
- **Cardinality:** `|J|` = planning horizon length (e.g., 7, 14, 30 days)
- **Usage:** Index for "which day" in decision variables
- **Note:** Days are numbered 1, 2, 3, ... (not dates)

### **K_shifts** - Set of Shift Types
```python
K_shifts = scenarios_df['shift'].unique()  # e.g., ['E', 'D', 'L', 'N']
```
- **Mathematical notation:** `K` or `k ∈ K`
- **Meaning:** Different types of shifts in a day
- **Typical values:**
  - `E` = Early shift (e.g., 6am-2pm)
  - `D` = Day shift (e.g., 9am-5pm)
  - `L` = Late shift (e.g., 2pm-10pm)
  - `N` = Night shift (e.g., 10pm-6am)
- **Cardinality:** `|K|` = 4 (typically)
- **Usage:** Index for "which shift type"

### **W_scenarios** - Set of Demand Scenarios
```python
W_scenarios = scenarios_df['scenario'].unique()  # e.g., [1, 2, 3, ..., 50]
```
- **Mathematical notation:** `Ω` (omega) or `ω ∈ Ω`
- **Meaning:** Different possible realizations of uncertain demand
- **Why needed:** We don't know exact future demand, so we model multiple scenarios
- **Cardinality:** `|Ω|` = number of scenarios (e.g., 5, 20, 50)
- **Usage:** Index for scenario-dependent variables (α, β, z)

**Example:** If we have:
- 10 nurses (`|I|=10`)
- 14 days (`|J|=14`)
- 4 shifts (`|K|=4`)
- 5 scenarios (`|Ω|=5`)

Then we have `10 × 14 × 4 = 560` possible nurse-day-shift combinations, evaluated across 5 scenarios.

---

## Parameters (Input Data)

Parameters are **given constants** that define costs, limits, and demand.

### Cost Parameters

#### **c₁** - Regular Shift Cost
```python
c1 = model_params['c1']  # e.g., 100.0
```
- **Mathematical notation:** `c₁` or `c_1`
- **Unit:** Currency per shift (e.g., $100/shift)
- **Meaning:** How much it costs to schedule one regular shift
- **Usage:** Multiplied by number of regular shifts in objective
- **Typical value:** $80-$150
- **Economic interpretation:** Base nurse wage for standard shift

#### **c₂** - Overtime Shift Cost
```python
c2 = model_params['c2']  # e.g., 150.0
```
- **Mathematical notation:** `c₂` or `c_2`
- **Unit:** Currency per shift
- **Meaning:** Cost to schedule one overtime shift
- **Constraint:** Should satisfy `c₂ > c₁` (overtime costs more)
- **Typical value:** 1.2× to 1.5× regular cost
- **Why needed:** Limits excessive overtime usage

#### **q⁺** - Emergency Staff Cost
```python
q_plus = model_params['q_plus']  # e.g., 200.0
```
- **Mathematical notation:** `q⁺` or `q^+`
- **Unit:** Currency per emergency shift
- **Meaning:** Cost to call in emergency/on-call nurse
- **Constraint:** Should satisfy `q⁺ > c₂ > c₁`
- **Typical value:** 1.5× to 2× overtime cost
- **Why needed:** Heavily penalizes understaffing to encourage good baseline schedules

#### **q⁻** - Shift Cancellation Cost
```python
q_minus = model_params.get('q_minus', 0.0)  # e.g., 2.0 or 0.0
```
- **Mathematical notation:** `q⁻` or `q^-`
- **Unit:** Currency per cancelled shift
- **Meaning:** Cost to cancel a scheduled shift when demand is low
- **Paper value:** 2 (small penalty)
- **Default:** 0 (no cost - overstaffing is acceptable)
- **Why small/zero:** Overstaffing is less problematic than understaffing

#### **c₃** - Stand-Alone Shift Penalty
```python
c3 = model_params.get('c3', 10.0)  # e.g., 10.0
```
- **Mathematical notation:** `c₃` or `c_3`
- **Unit:** Currency per occurrence
- **Meaning:** Penalty for isolated working days
- **Example:** Working Mon, off Tue-Wed, working Thu = stand-alone shifts on Mon and Thu
- **Purpose:** Encourage consecutive working days (better for nurses)
- **Note:** This is a **soft constraint** (penalized, not forbidden)

#### **c₄** - Unwanted Pattern Penalty
```python
c4 = model_params.get('c4', 15.0)  # e.g., 15.0
```
- **Mathematical notation:** `c₄` or `c_4`
- **Unit:** Currency per occurrence
- **Meaning:** Penalty for undesirable consecutive shift patterns
- **Examples:** Late→Early (too short rest), Day→Early, Early→Night
- **Purpose:** Discourage shift patterns that cause fatigue
- **Note:** Soft constraint (penalized if unavoidable)

### Work Rule Parameters

#### **n₁** - Maximum Total Shifts
```python
n1 = model_params['n1']  # e.g., 15
```
- **Mathematical notation:** `n₁` or `n_1`
- **Unit:** Number of shifts
- **Meaning:** Maximum shifts any nurse can work in planning period
- **Constraint type:** Hard limit
- **Example:** If planning period is 14 days and n₁=15, nurse can work at most 15 shifts
- **Purpose:** Prevent overwork, comply with labor laws

#### **n₂** - Maximum Night Shifts
```python
n2 = model_params['n2']  # e.g., 5
```
- **Mathematical notation:** `n₂` or `n_2`
- **Unit:** Number of night shifts
- **Meaning:** Maximum night shifts any nurse can work
- **Constraint:** `n₂ ≤ n₁`
- **Purpose:** Night shifts are especially taxing, limit exposure
- **Typical value:** 30-40% of n₁

#### **n₃** - Minimum Regular Shifts
```python
n3 = model_params['n3']  # e.g., 10
```
- **Mathematical notation:** `n₃` or `n_3`
- **Unit:** Number of shifts
- **Meaning:** Minimum regular (non-overtime) shifts per nurse
- **Constraint:** `n₃ ≤ n₁`
- **Purpose:** Ensure fair work distribution, job security
- **Typical value:** 60-80% of n₁

#### **n₄** - Minimum Complete Weekends Off
```python
n4 = model_params.get('n4', 0)  # e.g., 0 or 2
```
- **Mathematical notation:** `n₄` or `n_4`
- **Unit:** Number of complete weekends
- **Meaning:** Minimum Saturdays+Sundays both off
- **Value:** 0 = disabled, >0 = enabled
- **Purpose:** Work-life balance, family time
- **Note:** Requires `start_date` parameter to detect weekends

### CVaR Risk Parameters

#### **σ** - Confidence Level
```python
sigma = model_params.get('sigma', 0.95)  # e.g., 0.95
```
- **Mathematical notation:** `σ` (sigma)
- **Unit:** Probability (0 to 1)
- **Meaning:** Confidence level for risk measure
- **Interpretation:** If σ=0.95, we control the worst 5% of scenarios
- **Typical values:** 0.90, 0.95, 0.99
- **Usage:** Only used in SDM-CVaR model

#### **μ** - CVaR Shortage Limit
```python
mu = model_params.get('mu', 5.0)  # e.g., 5.0
```
- **Mathematical notation:** `μ` (mu)
- **Unit:** Number of shifts
- **Meaning:** Maximum acceptable average shortage in worst-case scenarios
- **Interpretation:** "In worst 5% of scenarios, average shortage ≤ 5 shifts"
- **Purpose:** Risk management - control disaster scenarios
- **Usage:** Only used in SDM-CVaR model

### Demand Data

#### **R^ω_{jk}** - Demand per Scenario
```python
R_demand = scenarios_df.set_index(['day', 'shift', 'scenario'])['demand'].to_dict()
# Access: R_demand[(j, k, w)]
```
- **Mathematical notation:** `R^ω_{jk}` or `R_{jk}^ω`
- **Unit:** Number of nurses needed
- **Meaning:** Required nurses for day j, shift k, in scenario ω
- **Example:** `R^5_{2,D}` = 8 means "Scenario 5, Day 2, Day shift needs 8 nurses"
- **Data structure:** Dictionary with (day, shift, scenario) as key
- **Why scenarios:** Demand is uncertain, so we model multiple possibilities

---

## Decision Variables

Decision variables are what the optimizer **chooses** to minimize cost while satisfying constraints.

### Stage 1 Variables (First-Stage Decisions)

These are decided **before** knowing actual demand.

#### **sr_{ijk}** - Regular Shift Assignment
```python
sr = pulp.LpVariable.dicts("RegularShift", 
                          (I_nurses, J_days, K_shifts), 
                          cat=pulp.LpBinary)
# Access: sr[nurse_i][day_j][shift_k]
```
- **Mathematical notation:** `sr_{ijk}` or `x^r_{ijk}`
- **Type:** Binary (0 or 1)
- **Meaning:** 
  - `sr[i][j][k] = 1` → Nurse i works regular shift k on day j
  - `sr[i][j][k] = 0` → Nurse i does NOT work that shift
- **Dimensions:** `|I| × |J| × |K|` variables (e.g., 10×14×4 = 560 variables)
- **Cost impact:** Each `sr[i][j][k]=1` adds `c₁` to cost
- **Example:** `sr['Alice'][3]['D'] = 1` means Alice works Day shift on day 3

#### **so_{ijk}** - Overtime Shift Assignment
```python
so = pulp.LpVariable.dicts("OvertimeShift", 
                          (I_nurses, J_days, K_shifts), 
                          cat=pulp.LpBinary)
# Access: so[nurse_i][day_j][shift_k]
```
- **Mathematical notation:** `so_{ijk}` or `x^o_{ijk}`
- **Type:** Binary (0 or 1)
- **Meaning:**
  - `so[i][j][k] = 1` → Nurse i works overtime shift k on day j
  - `so[i][j][k] = 0` → Not overtime
- **Difference from sr:** Higher cost (c₂ > c₁)
- **Purpose:** Provides flexibility beyond regular shifts
- **Constraint:** `sr[i][j][k] + so[i][j][k] ≤ 1` (can't do both for same shift)

### Soft Constraint Deviation Variables

These variables measure **violations** of soft constraints (which are penalized but not forbidden).

#### **dev1_{ij}** - Stand-Alone Shift Deviation
```python
dev1 = pulp.LpVariable.dicts("Dev_StandAlone",
                             (I_nurses, J_days),
                             lowBound=0,
                             cat=pulp.LpInteger)
# Access: dev1[nurse_i][day_j]
```
- **Mathematical notation:** `dev1_{ij}` or `δ¹_{ij}`
- **Type:** Non-negative integer
- **Meaning:** Counts stand-alone shift violations
  - `dev1[i][j] = 0` → Day j is NOT a stand-alone shift for nurse i
  - `dev1[i][j] > 0` → Day j IS isolated (work j, but not j-1 or j+1)
- **Penalty:** Each unit adds `c₃` to objective
- **Why needed:** Stand-alone shifts are undesirable but sometimes unavoidable

#### **dev2_{ijk}** - Unwanted Pattern Deviation
```python
dev2 = pulp.LpVariable.dicts("Dev_UnwantedPattern",
                             (I_nurses, J_days, K_shifts),
                             lowBound=0,
                             cat=pulp.LpInteger)
# Access: dev2[nurse_i][day_j][shift_k]
```
- **Mathematical notation:** `dev2_{ijk}` or `δ²_{ijk}`
- **Type:** Non-negative integer
- **Meaning:** Counts unwanted consecutive shift patterns
  - `dev2[i][j][k] = 0` → No bad pattern starting at day j, shift k
  - `dev2[i][j][k] = 1` → Bad pattern detected (e.g., Late on j, Early on j+1)
- **Penalty:** Each unit adds `c₄` to objective
- **Unwanted patterns:** `{(D,E), (L,E), (L,D), (E,N)}`

### Stage 2 Variables (Second-Stage / Recourse Decisions)

These are decided **after** demand is revealed for each scenario ω.

#### **α^ω_{jk}** - Emergency Staff Added
```python
alpha = pulp.LpVariable.dicts("AddShift", 
                             (J_days, K_shifts, W_scenarios), 
                             lowBound=0, 
                             cat=pulp.LpContinuous)
# Access: alpha[day_j][shift_k][scenario_w]
```
- **Mathematical notation:** `α^ω_{jk}` or `y^+_{jk}^ω`
- **Type:** Non-negative continuous (can be fractional)
- **Meaning:** Number of emergency nurses called in
  - `α^5_{3,D} = 2.5` → In scenario 5, day 3, Day shift: add 2.5 nurses
- **Why continuous:** Relaxation for easier solving (fractional = partial shift)
- **Cost impact:** Each unit adds `q⁺` to scenario cost
- **When used:** When scheduled staff < demand

#### **β^ω_{jk}** - Shifts Cancelled
```python
beta = pulp.LpVariable.dicts("CancelShift", 
                            (J_days, K_shifts, W_scenarios), 
                            lowBound=0, 
                            cat=pulp.LpContinuous)
# Access: beta[day_j][shift_k][scenario_w]
```
- **Mathematical notation:** `β^ω_{jk}` or `y^-_{jk}^ω`
- **Type:** Non-negative continuous
- **Meaning:** Number of scheduled shifts cancelled
  - `β^2_{5,N} = 1.0` → In scenario 2, day 5, Night shift: cancel 1 nurse
- **Cost impact:** Each unit adds `q⁻` to scenario cost (often q⁻=0)
- **When used:** When scheduled staff > demand

### CVaR Variables (Risk Management)

Only used when `model_type = "SDM-CVaR"`.

#### **ξ** - Value-at-Risk (VaR)
```python
xi = pulp.LpVariable("VaR_xi", cat=pulp.LpContinuous)
# Access: xi.varValue (after solving)
```
- **Mathematical notation:** `ξ` (xi)
- **Type:** Continuous (unbounded)
- **Meaning:** The σ-quantile of the shortage distribution
- **Example:** If σ=0.95 and ξ=3, then "95% of scenarios have shortage ≤ 3"
- **Purpose:** Threshold for identifying "tail" scenarios
- **Interpretation:** Separates "normal" scenarios from "worst-case" scenarios

#### **z^ω** - Excess Loss Beyond VaR
```python
z = pulp.LpVariable.dicts("ExcessLoss_z", 
                         (W_scenarios), 
                         lowBound=0, 
                         cat=pulp.LpContinuous)
# Access: z[scenario_w]
```
- **Mathematical notation:** `z^ω` or `z_ω`
- **Type:** Non-negative continuous
- **Meaning:** How much scenario ω's shortage exceeds VaR
  - `z^ω = max(0, Shortage^ω - ξ)`
  - `z^ω = 0` → Scenario is below VaR threshold (not in tail)
  - `z^ω > 0` → Scenario is in the tail (worst-case)
- **Purpose:** Measures tail losses for CVaR calculation
- **CVaR formula:** `CVaR = ξ + (1/(1-σ)) × E[z^ω]`

---

## Objective Function

**Goal:** Minimize total expected cost

### Complete Mathematical Formula

```
Minimize:
    c₁ · Σᵢⱼₖ sr_{ijk}                    [Regular shift costs]
  + c₂ · Σᵢⱼₖ so_{ijk}                    [Overtime shift costs]
  + c₃ · Σᵢⱼ dev1_{ij}                    [Stand-alone penalties]
  + c₄ · Σᵢⱼₖ dev2_{ijk}                  [Pattern penalties]
  + Σ_ω p^ω · (q⁺ Σⱼₖ α^ω_{jk} + q⁻ Σⱼₖ β^ω_{jk})  [Expected recourse cost]
```

### Code Implementation

```python
# STAGE 1 COST: Regular wages + Overtime wages
stage1_cost = (
    c1 * pulp.lpSum(sr[i][j][k] for i in I_nurses for j in J_days for k in K_shifts) +
    c2 * pulp.lpSum(so[i][j][k] for i in I_nurses for j in J_days for k in K_shifts)
)

# SOFT CONSTRAINT PENALTIES
soft_penalty_cost = (
    c3 * pulp.lpSum(dev1[i][j] for i in I_nurses for j in J_days) +
    c4 * pulp.lpSum(dev2[i][j][k] for i in I_nurses for j in J_days for k in K_shifts)
)

# STAGE 2 COST: Expected recourse cost across all scenarios
stage2_cost = pulp.lpSum(
    scenario_probability[w] * (
        q_plus * pulp.lpSum(alpha[j][k][w] for j in J_days for k in K_shifts) +
        q_minus * pulp.lpSum(beta[j][k][w] for j in J_days for k in K_shifts)
    )
    for w in W_scenarios
)

# TOTAL OBJECTIVE
prob += stage1_cost + soft_penalty_cost + stage2_cost, "Total_Cost"
```

### Component Breakdown

1. **`c₁ · Σᵢⱼₖ sr_{ijk}`** - Total regular shift cost
   - Counts all regular shifts across all nurses, days, shifts
   - Example: 50 regular shifts × $100 = $5,000

2. **`c₂ · Σᵢⱼₖ so_{ijk}`** - Total overtime cost
   - Counts all overtime shifts
   - Example: 10 overtime shifts × $150 = $1,500

3. **`c₃ · Σᵢⱼ dev1_{ij}`** - Stand-alone penalties
   - Sums all stand-alone shift violations
   - Example: 5 isolated days × $10 = $50

4. **`c₄ · Σᵢⱼₖ dev2_{ijk}`** - Pattern penalties
   - Sums all unwanted pattern violations
   - Example: 3 bad patterns × $15 = $45

5. **`Σ_ω p^ω · (q⁺ Σⱼₖ α^ω_{jk} + q⁻ Σⱼₖ β^ω_{jk})`** - Expected recourse cost
   - For each scenario ω:
     - Calculate cost of emergency staff: `q⁺ × total_α^ω`
     - Calculate cost of cancellations: `q⁻ × total_β^ω`
     - Weight by scenario probability: `p^ω`
   - Sum across all scenarios
   - Example: Average $1,000 across 5 scenarios = $1,000

**Total Example:** $5,000 + $1,500 + $50 + $45 + $1,000 = **$7,595**

---

## Constraints Explained

### Constraint 1: One Shift Per Day Maximum

**Mathematical Formula:**
```
Σₖ (sr_{ijk} + so_{ijk}) ≤ 1    ∀i ∈ I, j ∈ J
```

**Code:**
```python
for i in I_nurses:
    for j in J_days:
        prob += (
            pulp.lpSum(sr[i][j][k] + so[i][j][k] for k in K_shifts) <= 1,
            f"OneShiftPerDay_{i}_{j}"
        )
```

**Meaning:**
- Each nurse can work AT MOST one shift per day
- Sum of all shifts (regular + overtime) for nurse i on day j ≤ 1
- Prevents: Nurse working Early AND Day shift on same day

**Example:**
- Alice, Day 3: `sr['Alice'][3]['E'] + sr['Alice'][3]['D'] + ... ≤ 1`
- If Alice works Early (`sr['Alice'][3]['E']=1`), all others must be 0

### Constraint 6: Maximum Total Shifts

**Mathematical Formula:**
```
Σⱼₖ (sr_{ijk} + so_{ijk}) ≤ n₁    ∀i ∈ I
```

**Code:**
```python
for i in I_nurses:
    prob += (
        pulp.lpSum(sr[i][j][k] + so[i][j][k] for j in J_days for k in K_shifts) <= n1,
        f"MaxTotalShifts_{i}"
    )
```

**Meaning:**
- Total shifts (regular + overtime) for each nurse ≤ n₁
- Prevents overwork
- Labor law compliance

**Example:**
- If n₁=15 and planning period is 14 days:
- Alice can work maximum 15 shifts out of 14 possible days
- Allows some flexibility (overtime on some days)

### Constraint 7: Maximum Night Shifts

**Mathematical Formula:**
```
Σⱼ (sr_{ijN} + so_{ijN}) ≤ n₂    ∀i ∈ I
```

**Code:**
```python
if 'N' in K_shifts:
    for i in I_nurses:
        prob += (
            pulp.lpSum(sr[i][j]['N'] + so[i][j]['N'] for j in J_days) <= n2,
            f"MaxNightShifts_{i}"
        )
```

**Meaning:**
- Total night shifts for each nurse ≤ n₂
- Night shifts are especially taxing
- Example: If n₂=5, nurse can work max 5 night shifts in the period

### Constraint 8: Minimum Regular Shifts

**Mathematical Formula:**
```
Σⱼₖ sr_{ijk} ≥ n₃    ∀i ∈ I
```

**Code:**
```python
for i in I_nurses:
    prob += (
        pulp.lpSum(sr[i][j][k] for j in J_days for k in K_shifts) >= n3,
        f"MinRegularShifts_{i}"
    )
```

**Meaning:**
- Each nurse must work AT LEAST n₃ **regular** shifts
- Ensures fair work distribution
- Prevents: Some nurses working only overtime (unfair)

**Example:**
- If n₃=10, every nurse must have at least 10 regular shifts
- Can have more (up to n₁), but not fewer

### Constraint 16: Demand Fulfillment (KEY RECOURSE CONSTRAINT)

**Mathematical Formula:**
```
Σᵢ (sr_{ijk} + so_{ijk}) + α^ω_{jk} - β^ω_{jk} ≥ R^ω_{jk}    ∀ω ∈ Ω, j ∈ J, k ∈ K
```

**Code:**
```python
for w in W_scenarios:
    for j in J_days:
        for k in K_shifts:
            demand = R_demand.get((j, k, w), 0)
            prob += (
                pulp.lpSum(sr[i][j][k] + so[i][j][k] for i in I_nurses)
                + alpha[j][k][w] 
                - beta[j][k][w]
                >= demand,
                f"Demand_{j}_{k}_{w}"
            )
```

**Meaning:**
This is the **MOST IMPORTANT** constraint - it links Stage 1 and Stage 2!

**Components:**
- `Σᵢ (sr_{ijk} + so_{ijk})` = Planned staff (Stage 1 decision)
- `α^ω_{jk}` = Emergency staff added (Stage 2 decision)
- `β^ω_{jk}` = Staff cancelled (Stage 2 decision)
- `R^ω_{jk}` = Actual demand in scenario ω

**Interpretation:**
```
Planned Staff + Emergency Additions - Cancellations ≥ Demand
```

**Example Scenario:**
```
Scenario 5, Day 3, Day shift:
- Demand (R^5_{3,D}) = 8 nurses needed
- Planned staff: Alice, Bob, Charlie = 3 nurses
- Too few! Need 5 more
- Solution: α^5_{3,D} = 5 (call in 5 emergency nurses)
- Cost: 5 × $200 = $1,000 recourse cost for this scenario
```

**Why Two-Stage:**
- Stage 1: We don't know if demand will be 5, 8, or 10
- So we make a baseline schedule (sr, so)
- Stage 2: After seeing actual demand, we adjust (α, β)
- Optimizer finds baseline that minimizes expected adjustment cost

### Constraint 19: CVaR Upper Bound (SDM-CVaR only)

**Mathematical Formula:**
```
ξ + (1/(1-σ)) Σ_ω p^ω z^ω ≤ μ
```

**Code:**
```python
if model_type == "SDM-CVaR":
    prob += (
        xi + (1.0 / (1.0 - sigma)) * pulp.lpSum(scenario_probability[w] * z[w] for w in W_scenarios)
        <= mu,
        "CVaR_Constraint"
    )
```

**Meaning:**
Controls worst-case shortage risk using Conditional Value-at-Risk (CVaR).

**Components:**
- `ξ` = Value-at-Risk (VaR) - the σ-quantile threshold
- `σ` = Confidence level (e.g., 0.95)
- `z^ω` = Excess shortage in scenario ω beyond VaR
- `μ` = Upper limit on CVaR

**Interpretation:**
```
VaR + (Average tail loss) ≤ Maximum acceptable shortage
```

**Example:**
- σ=0.95, μ=5
- "In the worst 5% of scenarios, average shortage must be ≤ 5 nurses"
- ξ might be 3 (95% of scenarios have shortage ≤ 3)
- Tail scenarios (worst 5%) average shortage ≤ 5

**Why This Matters:**
- Standard model (SDM) only minimizes expected cost
- A schedule might have low average cost but catastrophic worst-case
- CVaR constraint ensures disaster scenarios are controlled

### Constraint 22: Excess Loss Definition

**Mathematical Formula:**
```
z^ω ≥ Σⱼₖ α^ω_{jk} - ξ    ∀ω ∈ Ω
z^ω ≥ 0                    ∀ω ∈ Ω
```

**Code:**
```python
for w in W_scenarios:
    loss_w = pulp.lpSum(alpha[j][k][w] for j in J_days for k in K_shifts)
    prob += (
        z[w] >= loss_w - xi,
        f"ExcessLoss_{w}"
    )
```

**Meaning:**
Defines how much scenario ω's shortage exceeds the VaR threshold.

**Mathematics:**
```
z^ω = max(0, Loss^ω - ξ)
```
Where `Loss^ω = Σⱼₖ α^ω_{jk}` (total shortage in scenario ω)

**Example:**
```
ξ = 3 (VaR threshold)

Scenario 1: Loss=2, z^1 = max(0, 2-3) = 0 (not in tail)
Scenario 2: Loss=5, z^2 = max(0, 5-3) = 2 (in tail, excess=2)
Scenario 3: Loss=8, z^3 = max(0, 8-3) = 5 (in tail, excess=5)
```

Only scenarios with `Loss^ω > ξ` contribute to CVaR calculation.

---

## Code-to-Math Mapping

### Quick Reference Table

| Code | Math | Type | Meaning |
|------|------|------|---------|
| `I_nurses` | `I` | Set | Nurses |
| `J_days` | `J` | Set | Days |
| `K_shifts` | `K` | Set | Shift types |
| `W_scenarios` | `Ω` | Set | Scenarios |
| `c1` | `c₁` | Parameter | Regular cost |
| `c2` | `c₂` | Parameter | Overtime cost |
| `q_plus` | `q⁺` | Parameter | Emergency cost |
| `q_minus` | `q⁻` | Parameter | Cancellation cost |
| `n1` | `n₁` | Parameter | Max total shifts |
| `n2` | `n₂` | Parameter | Max night shifts |
| `n3` | `n₃` | Parameter | Min regular shifts |
| `sigma` | `σ` | Parameter | Confidence level |
| `mu` | `μ` | Parameter | CVaR limit |
| `sr[i][j][k]` | `sr_{ijk}` | Variable | Regular shift |
| `so[i][j][k]` | `so_{ijk}` | Variable | Overtime shift |
| `alpha[j][k][w]` | `α^ω_{jk}` | Variable | Emergency add |
| `beta[j][k][w]` | `β^ω_{jk}` | Variable | Cancellation |
| `xi` | `ξ` | Variable | VaR threshold |
| `z[w]` | `z^ω` | Variable | Excess loss |
| `dev1[i][j]` | `dev1_{ij}` | Variable | Stand-alone penalty |
| `dev2[i][j][k]` | `dev2_{ijk}` | Variable | Pattern penalty |
| `R_demand[(j,k,w)]` | `R^ω_{jk}` | Data | Demand |

### Index Conventions

```python
# Looping pattern in code matches mathematical summations:

# Math: Σᵢⱼₖ sr_{ijk}
# Code:
pulp.lpSum(sr[i][j][k] for i in I_nurses for j in J_days for k in K_shifts)

# Math: Σ_ω p^ω · (...)
# Code:
pulp.lpSum(scenario_probability[w] * (...) for w in W_scenarios)

# Math: ∀i ∈ I, j ∈ J  (for all i in I, j in J)
# Code:
for i in I_nurses:
    for j in J_days:
        prob += (constraint, f"Name_{i}_{j}")
```

### Variable Naming Convention

```python
# sr = "s"hift "r"egular
# so = "s"hift "o"vertime
# alpha = α (Greek letter, emergency additions)
# beta = β (Greek letter, cancellations)
# xi = ξ (Greek letter, VaR)
# z = excess loss (z is standard in CVaR literature)
# dev1 = deviation type 1 (stand-alone)
# dev2 = deviation type 2 (patterns)
```

---

## Practical Examples

### Example 1: Small Problem Instance

**Setup:**
- 3 nurses: Alice, Bob, Charlie
- 7 days (one week)
- 2 shifts: Day (D), Night (N)
- 2 scenarios: Low demand, High demand

**Parameters:**
- c₁=100, c₂=150, q⁺=200
- n₁=5, n₂=2, n₃=3

**Decision Space:**
- Stage 1: `3 nurses × 7 days × 2 shifts = 42` sr variables + 42 so variables = **84 binary variables**
- Stage 2: `7 days × 2 shifts × 2 scenarios = 28` alpha + 28 beta = **56 continuous variables**
- **Total: 140 variables**

**Sample Solution:**
```
Alice: Day 1-5 (regular), Off 6-7
Bob:   Day 3-7 (regular), Off 1-2  
Charlie: Night 2,4,6 (regular), Off 1,3,5,7

Scenario 1 (Low): No emergency staff needed, α=0
Scenario 2 (High): Day 3 needs +2 nurses, α^2_{3,D}=2

Cost: 13 regular shifts × $100 + 2 emergency × $200 = $1,500
```

### Example 2: Understanding Recourse

**Situation:**
```
Day 5, Day shift:
- Scheduled: Alice, Bob (2 nurses)
- Demand scenarios:
  - Scenario 1: Need 1 nurse  → α=0, β=1 (cancel Bob, cost=$0)
  - Scenario 2: Need 2 nurses → α=0, β=0 (perfect match)
  - Scenario 3: Need 4 nurses → α=2, β=0 (call 2 emergency, cost=$400)
```

**Expected recourse cost (equal probabilities):**
```
(1/3) × $0 + (1/3) × $0 + (1/3) × $400 = $133.33
```

The optimizer chooses the baseline schedule (Alice, Bob) that minimizes this expected cost across all scenarios.

---

## Summary

**Key Takeaways:**

1. **Two-Stage Structure:**
   - Stage 1 (sr, so): Baseline schedule before knowing demand
   - Stage 2 (α, β): Adjustments after demand is revealed

2. **Variable Types:**
   - Binary (sr, so): Shift assignments (yes/no)
   - Continuous (α, β, z): Recourse actions (fractional OK)
   - Integer (dev1, dev2): Penalty counters

3. **Cost Hierarchy:**
   - Regular < Overtime < Emergency
   - c₁ < c₂ < q⁺

4. **Critical Constraints:**
   - One shift/day (Constraint 1)
   - Demand fulfillment (Constraint 16) - links stages
   - Max/min work limits (Constraints 6-8)

5. **Risk Management (CVaR):**
   - ξ = VaR threshold (95% of scenarios below this)
   - z = Tail losses (how bad the worst 5% are)
   - μ = Upper limit on tail average

This model balances:
- ✅ Cost minimization
- ✅ Work rules compliance
- ✅ Demand uncertainty handling
- ✅ Risk management (optional)
