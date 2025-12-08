# Proposed Research Contributions - Feasibility Analysis

**Date:** December 8, 2025  
**Analysis:** Deep assessment of 7 proposed extensions to He et al. (2019) NSS model  
**Current Model:** Two-stage stochastic programming with CVaR for nurse scheduling

---

## Summary Table

| # | Contribution | Feasibility | Complexity | Research Value | Implementation Effort | Recommendation |
|---|--------------|-------------|------------|----------------|----------------------|----------------|
| 1 | Nurse Skills (Heterogeneous) | ✅ **HIGH** | Medium | ⭐⭐⭐⭐⭐ Excellent | 2-3 weeks | **🟢 HIGHLY RECOMMENDED** |
| 2 | Hiring/Firing Decisions | ✅ **HIGH** | High | ⭐⭐⭐⭐⭐ Excellent | 3-4 weeks | **🟢 HIGHLY RECOMMENDED** |
| 3 | Nurse Preferences | ✅ **HIGH** | Low | ⭐⭐⭐ Good | 1 week | **🟢 RECOMMENDED** |
| 4 | Gender Considerations | ⚠️ **MEDIUM** | Low | ⭐⭐ Fair | 1 week | **🟡 CONDITIONAL** |
| 5 | Absenteeism (Uncertain Supply) | ✅ **HIGH** | Very High | ⭐⭐⭐⭐⭐ Excellent | 4-6 weeks | **🟢 HIGHLY RECOMMENDED** |
| 6 | Fatigue Modeling | ✅ **HIGH** | Medium | ⭐⭐⭐⭐ Very Good | 2-3 weeks | **🟢 RECOMMENDED** |
| 7 | GAM Prediction Model | ⚠️ **MEDIUM** | Very High | ⭐⭐⭐ Good | 4-6 weeks | **🟡 CONDITIONAL** |

---

## Detailed Analysis

### 1. ✅ Nurse Skills (Heterogeneous Workforce) - **HIGHLY RECOMMENDED**

**Description:** Differentiate nurses by skill level (e.g., Senior, Junior, Intermediate)

**Research Value:** ⭐⭐⭐⭐⭐ **EXCELLENT**
- **Novel contribution:** He et al. (2019) assumes homogeneous nurses - this is unrealistic
- **Real-world impact:** Hospitals have skill hierarchies critical for quality care
- **Academic novelty:** Few stochastic nurse scheduling papers incorporate skill levels

**Implementation Feasibility:** ✅ **HIGH**

#### Required Changes:

**Data Structure:**
```python
# Current: nurses_df has only 'name' column
# NEW: Add skill_level column
nurses_df:
    name        skill_level
    Alice       Senior
    Bob         Junior
    Charlie     Senior
    Diana       Intermediate
```

**Model Modifications:**

1. **New Sets:**
```python
S_skills = ['Senior', 'Junior', 'Intermediate']  # Skill levels
skill_mapping = {'Alice': 'Senior', 'Bob': 'Junior', ...}
```

2. **New Constraints:**
```python
# Constraint: Junior nurses cannot work alone (need senior supervision)
# For each shift requiring supervision:
for j in J_days:
    for k in K_shifts:  # E.g., Night shift requires supervision
        for w in W_scenarios:
            # Count junior nurses working
            juniors_working = sum(sr[i][j][k] + so[i][j][k] 
                                 for i in I_nurses if skill_mapping[i] == 'Junior')
            
            # Count senior nurses working
            seniors_working = sum(sr[i][j][k] + so[i][j][k] 
                                 for i in I_nurses if skill_mapping[i] in ['Senior', 'Intermediate'])
            
            # Constraint: juniors ≤ seniors (or juniors ≤ 2*seniors, etc.)
            prob += (juniors_working <= seniors_working, 
                    f"JuniorSupervision_{j}_{k}_{w}")
```

3. **Modified Demand Constraints:**
```python
# Constraint 16 becomes skill-aware:
# Instead of: Σᵢ(sr+so) + α - β ≥ R_{jk}^ω
# NEW: Σᵢ∈Senior(sr+so)×skill_weight + Σᵢ∈Junior(sr+so)×skill_weight + α - β ≥ R_{jk}^ω

# Where skill_weight: Senior=1.0, Intermediate=0.8, Junior=0.5
# (1 senior = 2 juniors in terms of capacity)
```

4. **Cost Differentiation:**
```python
# Current: c1 (regular), c2 (overtime) - same for all nurses
# NEW: Skill-based costs
c1_senior = 120     # Higher base wage
c1_intermediate = 100
c1_junior = 80      # Lower base wage

# Objective becomes:
stage1_cost = sum(c1_skill[skill_mapping[i]] * sr[i][j][k] 
                 for i,j,k in combinations)
```

**App.py Changes:**
- Add skill_level column upload in CSV
- Add skill distribution visualization
- Add supervision constraint toggle in parameters

**Example Paper Contribution:**
> "We extend He et al. (2019) to incorporate nurse skill heterogeneity, where nurses are classified as Senior (100% capacity), Intermediate (80%), or Junior (50%). We introduce supervision constraints requiring at least one senior nurse for every two junior nurses on critical shifts (nights, weekends). Results show 12% cost reduction by optimally utilizing junior nurses while maintaining quality standards."

**Estimated Effort:** 2-3 weeks (Medium complexity)

---

### 2. ✅ Hiring/Firing Decisions - **HIGHLY RECOMMENDED**

**Description:** Add strategic workforce decisions: hire/fire nurses with associated costs vs. emergency staff costs

**Research Value:** ⭐⭐⭐⭐⭐ **EXCELLENT**
- **Novel contribution:** Transforms operational model into tactical/strategic planning
- **Real-world impact:** Hospital administrators face this tradeoff constantly
- **Academic novelty:** Very few papers combine scheduling + workforce sizing decisions

**Implementation Feasibility:** ✅ **HIGH** (but complex)

#### Required Changes:

**New Decision Variables:**

1. **Hiring/Firing Variables:**
```python
# h_i: Binary, = 1 if nurse i is hired
h = pulp.LpVariable.dicts("Hire", I_potential_nurses, cat=pulp.LpBinary)

# f_i: Binary, = 1 if nurse i is fired
f = pulp.LpVariable.dicts("Fire", I_current_nurses, cat=pulp.LpBinary)

# employed_i: Binary, = 1 if nurse i is employed in this period
employed = pulp.LpVariable.dicts("Employed", I_all_nurses, cat=pulp.LpBinary)
```

2. **Employment Status Linking:**
```python
# For existing nurses:
for i in I_current_nurses:
    # employed = 1 - fired
    prob += (employed[i] == 1 - f[i], f"Employment_Current_{i}")

# For potential new hires:
for i in I_potential_nurses:
    # employed = hired
    prob += (employed[i] == h[i], f"Employment_New_{i}")

# Nurses can only work if employed:
for i in I_all_nurses:
    for j in J_days:
        for k in K_shifts:
            prob += (sr[i][j][k] <= employed[i], f"WorkIfEmployed_{i}_{j}_{k}")
```

**New Costs in Objective:**

```python
# Hiring cost (recruitment, training, onboarding)
c_hire = 5000  # One-time cost per hire

# Firing cost (severance, legal, morale)
c_fire = 3000  # One-time cost per termination

# Steady-state employment cost (benefits, overhead) per planning period
c_employ = 200  # Per nurse per period (e.g., per month)

# Modified objective:
total_cost = (
    # Stage 1: Regular + Overtime (only for employed nurses)
    stage1_cost +
    
    # Hiring/Firing costs
    c_hire * sum(h[i] for i in I_potential_nurses) +
    c_fire * sum(f[i] for i in I_current_nurses) +
    c_employ * sum(employed[i] for i in I_all_nurses) +
    
    # Stage 2: Emergency staff (recourse)
    stage2_cost +
    
    # Soft penalties
    soft_penalty_cost
)
```

**Tradeoff Analysis:**

The model will automatically decide:
- **Option A:** Hire 5 new nurses ($25k hiring cost + $1k/month wages) → reduces emergency staff needs
- **Option B:** Keep current staff + use emergency staff ($200/shift) → flexibility but expensive
- **Option C:** Fire 3 underutilized nurses ($9k severance) → saves $600/month wages

**New Constraints:**

```python
# Budget constraint (optional):
prob += (
    c_hire * sum(h[i] for i in I_potential) + 
    c_fire * sum(f[i] for i in I_current) <= hiring_budget,
    "HiringBudget"
)

# Workforce size limits:
prob += (
    sum(employed[i] for i in I_all) >= min_workforce_size,
    "MinWorkforce"
)
prob += (
    sum(employed[i] for i in I_all) <= max_workforce_size,
    "MaxWorkforce"
)

# Stability constraint (avoid mass layoffs):
prob += (
    sum(f[i] for i in I_current) <= 0.2 * len(I_current),  # Max 20% turnover
    "TurnoverLimit"
)
```

**Example Paper Contribution:**
> "We extend the two-stage stochastic model to incorporate hiring and firing decisions, creating a three-stage framework: (1) workforce sizing, (2) baseline scheduling, (3) demand-based recourse. Using hospital data with hiring costs ($5,000), firing costs ($3,000), and emergency shift costs ($200), we find the optimal workforce size is 87 nurses (vs. current 100), reducing annual costs by $450,000 while maintaining 95% service level."

**Estimated Effort:** 3-4 weeks (High complexity, requires data on hiring/firing costs)

---

### 3. ✅ Nurse Preferences - **RECOMMENDED**

**Description:** Incorporate nurse shift preferences (preferred/avoided shifts)

**Research Value:** ⭐⭐⭐ **GOOD**
- **Real-world impact:** Improves nurse satisfaction and retention
- **Academic novelty:** Common in deterministic models, but less explored in stochastic settings
- **Practical value:** Easy to collect preference data via surveys

**Implementation Feasibility:** ✅ **HIGH** (Low complexity)

#### Required Changes:

**Data Structure:**
```python
# preferences_df: nurse preferences matrix
preferences_df:
    nurse   shift   preference_score
    Alice   E       +2  (strongly prefer)
    Alice   N       -2  (strongly avoid)
    Bob     L       +1  (prefer)
    Bob     D       0   (neutral)
```

**Model Modification:**

```python
# Penalty for assigning unpreferred shifts
c_pref = 5  # Cost per unit of preference violation

# Preference deviation variables
pref_violation = pulp.LpVariable.dicts("PrefViolation",
                                       (I_nurses, J_days, K_shifts),
                                       lowBound=0,
                                       cat=pulp.LpContinuous)

# Constraint: violation ≥ -(preference_score) when shift assigned
for i in I_nurses:
    for j in J_days:
        for k in K_shifts:
            pref_score = preferences.get((i, k), 0)  # Default neutral
            if pref_score < 0:  # Only penalize negative preferences
                prob += (
                    pref_violation[i][j][k] >= -pref_score * (sr[i][j][k] + so[i][j][k]),
                    f"PrefViolation_{i}_{j}_{k}"
                )

# Add to objective:
preference_penalty = c_pref * sum(pref_violation[i][j][k] 
                                  for i,j,k in combinations)
total_cost += preference_penalty
```

**Alternative: Soft Constraint (Maximize Satisfaction):**
```python
# Instead of penalty, add satisfaction bonus
satisfaction_bonus = sum(pref_score[i][k] * (sr[i][j][k] + so[i][j][k])
                        for i,j,k if pref_score[i][k] > 0)

# Multi-objective: minimize cost, maximize satisfaction
# Use weighted sum:
prob += total_cost - 0.1 * satisfaction_bonus, "Objective"
```

**App.py Changes:**
- Upload preferences CSV
- Add preference weight slider (tradeoff: cost vs. satisfaction)
- Visualize: nurse satisfaction scores in results

**Example Paper Contribution:**
> "We incorporate nurse shift preferences using a preference score matrix (-2 to +2). By adding a preference violation penalty (weight = 0.1), we achieve 78% preference satisfaction while increasing costs by only 3.2%. Sensitivity analysis shows the cost-satisfaction Pareto frontier."

**Estimated Effort:** 1 week (Low complexity)

---

### 4. ⚠️ Gender Considerations - **CONDITIONAL RECOMMENDATION**

**Description:** Account for gender-specific constraints (e.g., night shift safety, diversity requirements)

**Research Value:** ⭐⭐ **FAIR**
- **Real-world relevance:** Some jurisdictions have gender-related labor laws
- **Academic caution:** Risk of appearing discriminatory; needs careful framing
- **Practical value:** Could model genuine safety/diversity concerns

**Implementation Feasibility:** ⚠️ **MEDIUM** (Easy technically, but ethically sensitive)

⚠️ **CAUTION:** This requires very careful framing to avoid discrimination. Only recommend if:
1. Based on legitimate safety concerns (e.g., "minimum 2 staff on night shifts for safety")
2. Diversity requirements are institutional policy (e.g., "balanced gender representation")
3. Paper explicitly states this models **existing constraints**, not recommending them

#### Possible Use Cases:

**1. Safety Constraint (Gender-Neutral Framing):**
```python
# Better framing: "Minimum 2 staff on night shifts for safety"
# (Happens to address concerns about solo female night workers)
for j in J_days:
    prob += (
        sum(sr[i][j]['N'] + so[i][j]['N'] for i in I_nurses) >= 2,
        f"MinNightStaff_{j}"
    )
```

**2. Diversity Requirement (Institutional Policy):**
```python
# "Hospital requires balanced gender representation (40-60% each gender)"
male_count = sum(employed[i] for i in I_nurses if gender[i] == 'M')
female_count = sum(employed[i] for i in I_nurses if gender[i] == 'F')
total_count = sum(employed[i] for i in I_nurses)

prob += (male_count >= 0.4 * total_count, "MinMaleRepresentation")
prob += (male_count <= 0.6 * total_count, "MaxMaleRepresentation")
```

**Recommendation:** 
- **🟡 Only pursue if:**
  - You have real hospital data requiring this
  - Can frame as modeling existing policies (not recommending them)
  - Include disclaimer in paper about ethical considerations
  
- **🔴 Avoid if:**
  - No institutional requirement exists
  - Cannot justify beyond "might be interesting"
  - Could appear discriminatory

**Estimated Effort:** 1 week (Low complexity, but high ethical consideration needed)

---

### 5. ✅ Absenteeism (Uncertain Supply) - **HIGHLY RECOMMENDED**

**Description:** Model nurse no-shows/sick leave as stochastic supply (uncertainty on BOTH demand AND supply)

**Research Value:** ⭐⭐⭐⭐⭐ **EXCELLENT**
- **Novel contribution:** He et al. (2019) only has uncertain DEMAND; adding uncertain SUPPLY is highly novel
- **Real-world impact:** Absenteeism is a major operational challenge (5-10% typical rate)
- **Academic novelty:** Very few papers model both demand and supply uncertainty in scheduling

**Implementation Feasibility:** ✅ **HIGH** (but very complex)

#### Conceptual Framework:

Current model: **Demand uncertainty only**
- Stage 1: Schedule nurses (deterministic availability)
- Stage 2: Realize demand scenarios → adjust with emergency staff

**NEW:** **Joint demand-supply uncertainty**
- Stage 1: Schedule nurses (assumes full availability)
- Stage 2: Realize (demand scenario, absence scenario) → adjust with emergency staff + on-call nurses

#### Required Changes:

**1. Absence Scenarios:**
```python
# Current: W_scenarios (demand scenarios)
# NEW: Ω_scenarios = (demand_scenario, absence_scenario) joint scenarios

# Example: 10 demand scenarios × 5 absence scenarios = 50 joint scenarios
absence_scenarios = {
    'Low': 0.02,    # 2% absence rate (probability 0.5)
    'Medium': 0.05, # 5% absence rate (probability 0.3)
    'High': 0.10,   # 10% absence rate (probability 0.15)
    'Crisis': 0.20  # 20% absence (flu outbreak) (probability 0.05)
}

# Joint probability: P(demand, absence) = P(demand) × P(absence)
# (if independent, otherwise use conditional probabilities)
```

**2. Absence Realization Variables:**
```python
# absent_{i,ω}: Binary, = 1 if nurse i is absent in scenario ω
# This is a PARAMETER (scenario realization), not a decision variable

# Generate scenarios:
for omega in Omega_scenarios:
    demand_scenario = omega['demand']
    absence_rate = omega['absence_rate']
    
    # Randomly sample which nurses are absent (Monte Carlo)
    absent_nurses[omega] = randomly_select_nurses(I_nurses, absence_rate)
```

**3. Availability Constraints:**
```python
# Stage 2 constraint: Scheduled nurses may be absent
# Effective staffing = scheduled - absences + emergency

for omega in Omega_scenarios:
    for j in J_days:
        for k in K_shifts:
            # Effective staff = (scheduled who actually show up) + emergency - cancellations
            effective_staff = (
                sum((sr[i][j][k] + so[i][j][k]) * (1 - absent[i][omega]) 
                    for i in I_nurses) +
                alpha[j][k][omega] - 
                beta[j][k][omega]
            )
            
            # Must meet demand
            prob += (
                effective_staff >= R_demand[j, k, omega['demand']],
                f"StaffingWithAbsences_{j}_{k}_{omega}"
            )
```

**4. On-Call Pool (Optional Enhancement):**
```python
# Add on-call nurses (cheaper than emergency, but must be pre-designated)
c_oncall = 120  # Cost: regular < on-call < emergency

# Decision: designate nurses for on-call duty
oncall = pulp.LpVariable.dicts("OnCall", (I_nurses, J_days), cat=pulp.LpBinary)

# On-call nurses cannot be scheduled for regular/overtime
for i in I_nurses:
    for j in J_days:
        prob += (
            oncall[i][j] + sum(sr[i][j][k] + so[i][j][k] for k in K_shifts) <= 1,
            f"OnCallExclusive_{i}_{j}"
        )

# Stage 2: can activate on-call nurses to cover absences
oncall_activated = pulp.LpVariable.dicts("OnCallActivated",
                                         (I_nurses, J_days, K_shifts, Omega_scenarios),
                                         cat=pulp.LpBinary)

# Can only activate if designated on-call:
for i,j,k,omega in combinations:
    prob += (
        oncall_activated[i][j][k][omega] <= oncall[i][j],
        f"OnCallActivation_{i}_{j}_{k}_{omega}"
    )

# Add to objective:
oncall_cost = c_oncall * sum(oncall[i][j] for i,j)
oncall_activation_cost = (c_oncall/2) * sum(oncall_activated[i][j][k][omega] 
                                            for i,j,k,omega)
```

**Data Requirements:**
- Historical absence rates by season/day (e.g., Mondays have higher absence)
- Absence duration distribution (single day vs. multi-day sick leave)
- Correlation: Are absences independent or clustered? (e.g., flu outbreak affects multiple nurses)

**Example Paper Contribution:**
> "We extend He et al. (2019) to model joint demand-supply uncertainty by incorporating nurse absenteeism scenarios. Using hospital data showing 5% average absence rate (ranging 2-15% during flu season), we generate 100 joint scenarios (20 demand × 5 absence). Results show that ignoring absenteeism leads to 18% understaffing incidents, while our joint optimization reduces this to 3% by optimal on-call nurse allocation, with only 7% cost increase."

**Estimated Effort:** 4-6 weeks (Very high complexity - this is PhD-level contribution)

---

### 6. ✅ Fatigue Modeling - **RECOMMENDED**

**Description:** Model nurse fatigue accumulation based on shift sequences, impacting performance/costs

**Research Value:** ⭐⭐⭐⭐ **VERY GOOD**
- **Novel contribution:** Realistic modeling of fatigue → quality/safety
- **Real-world impact:** Fatigue-related errors are a major healthcare concern
- **Academic novelty:** Few scheduling papers explicitly model fatigue accumulation

**Implementation Feasibility:** ✅ **HIGH** (Medium complexity)

#### Conceptual Framework:

**Fatigue Accumulation:**
- Night shifts: +3 fatigue
- Day shifts: +2 fatigue
- Evening shifts: +1.5 fatigue
- Day off: -4 fatigue recovery
- Fatigue > threshold → decreased productivity, increased error risk

#### Required Changes:

**1. Fatigue Tracking Variables:**
```python
# fatigue_{ij}: Continuous, accumulated fatigue for nurse i by day j
fatigue = pulp.LpVariable.dicts("Fatigue",
                                (I_nurses, J_days),
                                lowBound=0,
                                upBound=20,  # Max fatigue threshold
                                cat=pulp.LpContinuous)

# Fatigue accumulation weights
fatigue_weights = {
    'E': 2.0,   # Early shift
    'D': 2.0,   # Day shift
    'L': 2.5,   # Late shift (more tiring)
    'N': 4.0    # Night shift (most tiring)
}

recovery_rate = 3.0  # Fatigue recovered per day off
```

**2. Fatigue Dynamics Constraints:**
```python
J_days_sorted = sorted(list(J_days))

for i in I_nurses:
    # Initial fatigue
    prob += (fatigue[i][J_days_sorted[0]] == 0, f"InitialFatigue_{i}")
    
    # Fatigue evolution
    for idx, j in enumerate(J_days_sorted[1:], start=1):
        j_prev = J_days_sorted[idx - 1]
        
        # fatigue_j = fatigue_{j-1} + shift_fatigue - recovery
        shift_fatigue = sum(fatigue_weights[k] * (sr[i][j_prev][k] + so[i][j_prev][k])
                           for k in K_shifts)
        
        working_today = sum(sr[i][j_prev][k] + so[i][j_prev][k] for k in K_shifts)
        recovery = recovery_rate * (1 - working_today)  # Only recover if OFF
        
        prob += (
            fatigue[i][j] == fatigue[i][j_prev] + shift_fatigue - recovery,
            f"FatigueEvolution_{i}_{j}"
        )
```

**3. Fatigue-Based Constraints:**
```python
# Option A: Hard constraint (fatigue cannot exceed threshold)
max_fatigue = 15.0
for i in I_nurses:
    for j in J_days:
        prob += (fatigue[i][j] <= max_fatigue, f"MaxFatigue_{i}_{j}")

# Option B: Soft constraint (penalize high fatigue)
fatigue_penalty = pulp.LpVariable.dicts("FatiguePenalty",
                                        (I_nurses, J_days),
                                        lowBound=0,
                                        cat=pulp.LpContinuous)

for i in I_nurses:
    for j in J_days:
        # Penalty kicks in above threshold
        prob += (
            fatigue_penalty[i][j] >= fatigue[i][j] - max_fatigue,
            f"FatiguePenaltyDef_{i}_{j}"
        )

# Add to objective
c_fatigue = 20  # Cost per unit of excess fatigue
total_cost += c_fatigue * sum(fatigue_penalty[i][j] for i,j)
```

**4. Fatigue-Dependent Emergency Staff Costs:**
```python
# Higher fatigue → lower effective capacity → more emergency staff needed
# Model: effective capacity = scheduled × fatigue_efficiency

fatigue_efficiency = {
    (0, 5): 1.0,    # Low fatigue: 100% efficiency
    (5, 10): 0.95,  # Moderate: 95%
    (10, 15): 0.85, # High: 85%
    (15, 20): 0.70  # Extreme: 70%
}

# Modify Constraint 16:
# Instead of: Σᵢ(sr+so) + α - β ≥ R
# NEW: Σᵢ(sr+so)×efficiency(fatigue_i) + α - β ≥ R

# (Requires piecewise linear approximation or Big-M formulation)
```

**Data Requirements:**
- Fatigue accumulation rates per shift type (literature-based or empirical)
- Recovery rates during off days
- Performance degradation curves (fatigue → error rates)

**Example Paper Contribution:**
> "We incorporate fatigue dynamics into the stochastic nurse scheduling model, where fatigue accumulates based on shift type (night +4, day +2, off -3) and affects nurse productivity. Fatigue exceeding 15 units incurs a $20/unit penalty representing increased error risk. Results show that fatigue-aware scheduling reduces maximum fatigue by 38% with only 5% cost increase, improving patient safety."

**Estimated Effort:** 2-3 weeks (Medium complexity, requires literature on fatigue modeling)

---

### 7. ⚠️ GAM Prediction Model - **CONDITIONAL RECOMMENDATION**

**Description:** Use Generalized Additive Models (GAM) to predict patient demand scenarios instead of historical data

**Research Value:** ⭐⭐⭐ **GOOD**
- **Novel contribution:** Advanced demand forecasting for scenario generation
- **Academic value:** Combines ML (GAM) with optimization (stochastic programming)
- **Practical value:** Could improve scenario quality if done well

**Implementation Feasibility:** ⚠️ **MEDIUM** (Very high complexity + data requirements)

⚠️ **MAJOR CHALLENGE:** Requires substantial historical data (2+ years of hourly patient arrivals)

#### What GAM Would Do:

**Current Approach:** Scenarios from historical data or simple patterns
```python
# Example: current scenario generation
demand[scenario_1] = historical_week_1
demand[scenario_2] = historical_week_2 + noise
```

**GAM Approach:** Predict demand based on external factors
```python
# GAM model: demand ~ s(hour) + s(day_of_week) + s(month) + s(temperature) + ...
# Where s() = smooth functions

from pygam import GAM, s, f

# Features
X = [hour, day_of_week, month, temperature, flu_index, holiday_flag, ...]
y = historical_demand

# Fit GAM
gam = GAM(s(0) + s(1) + s(2) + f(3) + s(4) + f(5))
gam.fit(X, y)

# Generate scenarios by predicting with different feature values
scenarios = []
for i in range(100):
    # Vary temperature, flu index, etc.
    X_scenario = create_scenario_features(temp=sample(), flu=sample(), ...)
    demand_scenario = gam.predict(X_scenario)
    scenarios.append(demand_scenario)
```

#### Required Components:

**1. Data Collection (BIGGEST CHALLENGE):**
```
Minimum 2 years of hourly data:
- Patient arrivals by hour/shift
- Day of week, month, holidays
- External factors:
  - Weather (temperature, precipitation)
  - Flu/disease prevalence
  - Local events (sports, festivals)
  - Economic indicators
```

**2. GAM Training Pipeline:**
```python
# New file: demand_forecasting.py

import pandas as pd
from pygam import GAM, s, f, te
from sklearn.model_selection import TimeSeriesSplit

def train_gam_model(historical_data):
    """
    Train GAM to predict shift demand
    
    Features:
    - Temporal: hour, day_of_week, week_of_year
    - Calendar: is_holiday, is_weekend
    - External: temperature, flu_index
    - Lagged: demand_yesterday, demand_last_week
    """
    
    # Feature engineering
    X = extract_features(historical_data)
    y = historical_data['demand']
    
    # GAM with smooth terms
    gam = GAM(
        s(0, n_splines=24) +      # Hour (cyclical)
        s(1, n_splines=7) +       # Day of week
        s(2, n_splines=12) +      # Month
        f(3) +                     # Holiday (categorical)
        s(4) +                     # Temperature
        s(5) +                     # Flu index
        te(0, 1)                   # Hour-Day interaction
    )
    
    # Cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    mape_scores = []
    
    for train_idx, test_idx in tscv.split(X):
        gam.fit(X[train_idx], y[train_idx])
        pred = gam.predict(X[test_idx])
        mape = mean_absolute_percentage_error(y[test_idx], pred)
        mape_scores.append(mape)
    
    print(f"GAM CV MAPE: {np.mean(mape_scores):.2%}")
    
    # Final model on all data
    gam.fit(X, y)
    return gam

def generate_scenarios_with_gam(gam_model, n_scenarios=100):
    """
    Generate demand scenarios using trained GAM
    
    Strategy:
    1. Sample from historical feature distributions
    2. Add stochastic perturbations (weather variability, flu outbreaks)
    3. Predict demand with GAM
    4. Add residual noise (GAM prediction error)
    """
    
    scenarios = []
    
    for i in range(n_scenarios):
        # Sample features
        features = sample_scenario_features(
            temperature=np.random.normal(70, 15),
            flu_index=np.random.gamma(2, 2),  # Skewed distribution
            is_holiday=np.random.choice([0, 1], p=[0.95, 0.05]),
            # ...
        )
        
        # Predict with GAM
        demand_mean = gam_model.predict(features)
        
        # Add noise (residual uncertainty)
        demand_scenario = demand_mean + np.random.normal(0, residual_std)
        
        scenarios.append({
            'scenario_id': i,
            'demand': demand_scenario,
            'features': features,
            'probability': 1/n_scenarios
        })
    
    return scenarios
```

**3. Integration with Model:**
```python
# In app.py: Add "Generate Scenarios with GAM" option

if st.button("Generate GAM-Based Scenarios"):
    if not gam_model_exists():
        st.error("Please train GAM model first (requires historical data)")
    else:
        gam = load_trained_gam()
        scenarios_df = generate_scenarios_with_gam(gam, n_scenarios=100)
        st.success(f"Generated {len(scenarios_df)} scenarios using GAM")
```

**Challenges:**

1. **Data Requirements:** 
   - Need 2+ years of granular data (most hospitals don't have this readily available)
   - External data (weather, flu rates) requires API integration

2. **Validation:**
   - How to prove GAM scenarios are better than historical?
   - Need out-of-sample testing (hold out recent months)

3. **Complexity:**
   - GAM training, tuning, validation = mini research project itself
   - Risk: Spend 60% of effort on GAM, only 40% on scheduling contribution

**Recommendation:**
- **🟡 Only pursue if:**
  - You have access to high-quality historical data (2+ years)
  - Have time for substantial ML component (4-6 weeks just for GAM)
  - Can demonstrate GAM scenarios improve upon simpler methods
  
- **🔴 Avoid if:**
  - No historical data available
  - Time-constrained (better to focus on other contributions)
  - GAM becomes the focus instead of the scheduling innovation

**Alternative (Easier):** Use ARIMA or simple time series instead of GAM
```python
# Simpler: ARIMA for scenario generation
from statsmodels.tsa.arima.model import ARIMA

model = ARIMA(historical_demand, order=(5, 1, 2))
fitted = model.fit()

# Generate scenarios via simulation
scenarios = fitted.simulate(nsimulations=100, repetitions=100)
```

**Example Paper Contribution (if pursued):**
> "We develop a GAM-based demand forecasting module to generate realistic scenarios, incorporating temporal patterns (hour, day, season) and external factors (temperature, flu prevalence). The GAM achieves 8.3% MAPE on out-of-sample data, outperforming ARIMA (12.1%) and historical sampling (15.4%). When integrated into the stochastic scheduling model, GAM scenarios reduce actual understaffing by 22% compared to historical-based scenarios."

**Estimated Effort:** 4-6 weeks (Very high complexity, data-dependent)

---

## 📋 Implementation Priority Ranking

Based on **research value**, **feasibility**, and **implementation effort**, here's the recommended priority:

### Tier 1: Highest Priority (Do These First) 🏆

1. **Nurse Skills (Heterogeneous Workforce)**
   - ⭐ Research Value: Excellent
   - ⏱️ Effort: 2-3 weeks
   - 💡 Why: High novelty, realistic, medium complexity
   - 📝 Status: **START HERE**

2. **Nurse Preferences**
   - ⭐ Research Value: Good
   - ⏱️ Effort: 1 week
   - 💡 Why: Easy win, improves practitioner appeal
   - 📝 Status: **Quick add-on**

3. **Fatigue Modeling**
   - ⭐ Research Value: Very Good
   - ⏱️ Effort: 2-3 weeks
   - 💡 Why: Safety-focused, novel constraint type
   - 📝 Status: **Strong contribution**

### Tier 2: High Value but More Effort 🥈

4. **Hiring/Firing Decisions**
   - ⭐ Research Value: Excellent
   - ⏱️ Effort: 3-4 weeks
   - 💡 Why: Transforms problem scope (operational → strategic)
   - ⚠️ Caution: Requires cost data (hiring/firing/employment costs)
   - 📝 Status: **Do if time permits**

5. **Absenteeism (Uncertain Supply)**
   - ⭐ Research Value: Excellent
   - ⏱️ Effort: 4-6 weeks
   - 💡 Why: Highly novel (joint demand-supply uncertainty)
   - ⚠️ Caution: Very complex, PhD-level contribution
   - 📝 Status: **Do if pursuing PhD/strong publication**

### Tier 3: Conditional (Assess Carefully) ⚠️

6. **Gender Considerations**
   - ⭐ Research Value: Fair
   - ⏱️ Effort: 1 week
   - 💡 Why: Easy technically
   - ⚠️ Caution: Ethically sensitive, needs careful framing
   - 📝 Status: **Only if institutional requirement exists**

7. **GAM Demand Forecasting**
   - ⭐ Research Value: Good
   - ⏱️ Effort: 4-6 weeks
   - 💡 Why: ML integration
   - ⚠️ Caution: Data-intensive, risk of overshadowing main contribution
   - 📝 Status: **Only if data available + sufficient time**

---

## 🎯 Recommended Roadmap

### Option A: **Focused Contribution** (6-8 weeks)
Perfect for master's thesis or conference paper
```
Week 1-3:   Nurse Skills (Heterogeneous Workforce)
Week 4:     Nurse Preferences
Week 5-7:   Fatigue Modeling
Week 8:     Integration, testing, paper writing
```
**Result:** 3 solid contributions, well-integrated, publishable

---

### Option B: **Ambitious Contribution** (12-16 weeks)
For PhD students or journal publication
```
Week 1-3:   Nurse Skills
Week 4:     Nurse Preferences
Week 5-7:   Fatigue Modeling
Week 8-11:  Hiring/Firing Decisions
Week 12-15: Absenteeism (Uncertain Supply)
Week 16:    Integration, comparison, paper writing
```
**Result:** 5 major contributions, highly novel, journal-quality

---

### Option C: **ML-Focused** (10-12 weeks)
If you have data and want ML angle
```
Week 1-5:   GAM Development & Validation
Week 6-8:   Nurse Skills Implementation
Week 9-10:  Fatigue Modeling
Week 11-12: Integration & paper writing
```
**Result:** ML + optimization hybrid, unique angle

---

## 📚 Data Requirements Summary

| Contribution | Required Data | Availability |
|--------------|---------------|--------------|
| **Nurse Skills** | Skill level per nurse (can create synthetic) | ✅ Easy |
| **Hiring/Firing** | Hiring cost, firing cost, employment cost | ⚠️ Hospital HR data needed |
| **Nurse Preferences** | Preference survey (can create synthetic) | ✅ Easy |
| **Gender** | Gender per nurse | ✅ Easy (but ethically sensitive) |
| **Absenteeism** | Historical absence rates by season/day | ⚠️ 1+ year history needed |
| **Fatigue** | Fatigue weights (from literature) | ✅ Medium (literature-based) |
| **GAM** | 2+ years hourly demand + external factors | ⚠️ Very difficult |

---

## 🎓 Academic Contribution Angle

### Paper Title Suggestions:

1. **Skills + Preferences + Fatigue:**
   > "Human-Centric Extensions to Stochastic Nurse Scheduling: Incorporating Skill Heterogeneity, Preferences, and Fatigue Dynamics"

2. **Hiring + Absenteeism:**
   > "Strategic Workforce Planning under Joint Demand-Supply Uncertainty: A Three-Stage Stochastic Programming Approach"

3. **ML Integration:**
   > "GAM-Enhanced Scenario Generation for Stochastic Nurse Scheduling with Fatigue and Skill Considerations"

---

## ✅ Final Recommendation

**Recommended Configuration: Option A (Focused)**

Implement in this order:
1. ✅ **Nurse Skills** (3 weeks) - Core contribution
2. ✅ **Nurse Preferences** (1 week) - Easy add-on
3. ✅ **Fatigue Modeling** (3 weeks) - Safety angle

**Total: 7 weeks + 1 week buffer = 8 weeks**

**Why this works:**
- ✅ All three are highly feasible
- ✅ No major data requirements (can use synthetic)
- ✅ Strong academic novelty (skills + fatigue = new)
- ✅ Practical appeal (preferences = practitioner buy-in)
- ✅ Reasonable scope for thesis/paper

**If you want to go further:**
Add **Hiring/Firing Decisions** (+4 weeks) for strategic angle

**Skip:**
- Gender (unless institutional requirement)
- GAM (unless you have data + time)

---

## 📝 Next Steps

1. **Confirm contributions:** Which 2-3 do you want to pursue?
2. **Check data availability:** Do you have real hospital data, or will we generate synthetic?
3. **Set timeline:** How many weeks do you have?

Let me know your choice and I can provide detailed implementation plans for each selected contribution!
