# Tutorial: Understanding the Nurse Scheduling Model

## Introduction

This document provides a comprehensive tutorial on understanding and using the Nurse Scheduling Optimization System, which implements a sophisticated mathematical model based on two-stage stochastic integer programming.

## Table of Contents

1. [The Problem We're Solving](#the-problem)
2. [Mathematical Foundation](#mathematical-foundation)
3. [Using the System](#using-the-system)
4. [Interpreting Results](#interpreting-results)
5. [Advanced Topics](#advanced-topics)

---

## The Problem

### Real-World Context

Hospitals face a daily challenge: **How many nurses should we schedule, and when?**

This is complicated by:
- **Uncertainty**: We don't know exactly how many patients will arrive
- **Regulations**: Nurses have limits on working hours, night shifts, etc.
- **Costs**: Regular shifts, overtime, and emergency staffing have different costs
- **Fairness**: Schedules should be equitable across nurses

### Traditional Approach vs. Our Approach

**Traditional**: 
- Create a baseline schedule
- Hope it works out
- Scramble when understaffed

**Our Approach**:
- Create a baseline schedule that anticipates uncertainty
- Plan for adjustments in advance
- Minimize both costs AND risks

---

## Mathematical Foundation

### Two-Stage Stochastic Programming

Think of this as making decisions in two phases:

#### Stage 1: "Here-and-Now" Decisions
**When**: Before we know the actual patient demand  
**What**: Baseline nurse schedule  
**Variables**: Who works which shifts on which days

#### Stage 2: "Wait-and-See" Decisions  
**When**: After we observe actual patient demand  
**What**: Adjustments to the baseline  
**Variables**: Emergency staff to add, shifts to cancel

### The Objective Function

We want to minimize total expected cost:

```
Total Cost = Stage 1 Cost + Expected Stage 2 Cost

Stage 1 Cost = (Regular Wages) + (Overtime Wages)

Expected Stage 2 Cost = (Probability of Each Scenario) × (Emergency Staffing Cost)
```

### Key Constraints

#### 1. One Shift Per Day Maximum
A nurse can work at most one shift per day.

**Mathematical**: For each nurse i and day j:
```
Sum over all shifts k: (regular[i][j][k] + overtime[i][j][k]) ≤ 1
```

**Example**: Nurse Alice can work either Early, Day, Late, or Night on Monday, but not multiple.

#### 2. Maximum Total Shifts
A nurse can't work more than n₁ shifts in the planning period.

**Mathematical**: For each nurse i:
```
Sum over all days j and shifts k: (regular[i][j][k] + overtime[i][j][k]) ≤ n₁
```

**Example**: If n₁ = 15 and the planning period is 30 days, nurses work at most half the days.

#### 3. Maximum Night Shifts
Limit on night shifts per nurse (n₂).

**Why**: Night work is taxing; regulations often limit it.

**Mathematical**: For each nurse i:
```
Sum over all days j: (regular[i][j][Night] + overtime[i][j][Night]) ≤ n₂
```

#### 4. Minimum Regular Shifts
Each nurse must work at least n₃ regular (non-overtime) shifts.

**Why**: Job security, fair distribution of work.

**Mathematical**: For each nurse i:
```
Sum over all days j and shifts k: regular[i][j][k] ≥ n₃
```

#### 5. Demand Satisfaction (The Key Recourse Constraint)
For each scenario ω, day j, and shift k, demand must be met:

**Mathematical**:
```
Planned Staff + Emergency Adds - Cancellations ≥ Demand

Sum over nurses i: (regular[i][j][k] + overtime[i][j][k]) 
    + emergency_adds[j][k][ω] 
    - cancellations[j][k][ω] 
    ≥ demand[j][k][ω]
```

**This is the magic**: The model can "adjust" via emergency_adds and cancellations, but pays a cost for it.

### CVaR: Controlling Risk

**What is CVaR?**  
Conditional Value-at-Risk measures the expected loss in the worst-case scenarios.

**Why use it?**  
Even if the average cost is low, we might be exposed to catastrophic shortages in rare events. CVaR protects against this.

**How it works**:
1. We set a confidence level σ (e.g., 95%)
2. We set a limit μ on acceptable worst-case shortage
3. The model ensures that in the worst 5% of scenarios (100% - 95%), the shortage doesn't exceed μ

**Mathematical**:
```
VaR + (1/(1-σ)) × Expected[Excess Loss] ≤ μ

where:
  VaR = Value at Risk (threshold)
  Excess Loss = max(0, Actual Loss - VaR)
  σ = confidence level (e.g., 0.95)
  μ = maximum acceptable shortage
```

---

## Using the System

### Input Data

#### 1. Nurse List
Simple list of nurse names or IDs.

**Format**: One name per line in a CSV/TXT file
```
Alice
Bob
Carol
David
```

#### 2. Demand Scenarios
Describes patient demand across multiple possible scenarios.

**Format**: CSV with columns: `scenario, day, shift, demand`

**Example**:
```csv
scenario,day,shift,demand
1,1,E,3     # Scenario 1, Day 1, Early shift, needs 3 nurses
1,1,D,4     # Scenario 1, Day 1, Day shift, needs 4 nurses
2,1,E,5     # Scenario 2, Day 1, Early shift, needs 5 nurses
...
```

**How to create scenarios**:
- **Historical data**: Sample from past demand
- **Forecasts**: Use ARIMA or similar to predict with error bands
- **Expert judgment**: High/medium/low demand scenarios
- **Use built-in generator**: The app can create realistic random scenarios

### Parameters

#### Cost Parameters
- **c₁ (Regular shift cost)**: Base wage for a regular shift
  - Example: $100
- **c₂ (Overtime shift cost)**: Premium wage for overtime
  - Example: $150 (1.5× regular)
- **q⁺ (Emergency shift cost)**: Cost to bring in emergency staff
  - Example: $200 (2× regular)

**Recommendation**: Set q⁺ > c₂ > c₁ to create proper incentives.

#### Work Rule Parameters
- **n₁ (Max total shifts)**: How many shifts a nurse can work total
  - Example: 15 shifts in a 30-day period
- **n₂ (Max night shifts)**: Limit on night work
  - Example: 5 nights
- **n₃ (Min regular shifts)**: Ensure everyone gets baseline work
  - Example: 10 shifts
- **n₄ (Min weekends off)**: Not fully implemented yet
  - Future feature

#### CVaR Parameters (if using SDM-CVaR)
- **σ (Confidence level)**: Protection level
  - 0.90 = protect worst 10% of scenarios
  - 0.95 = protect worst 5% of scenarios
  - 0.99 = protect worst 1% of scenarios
  - **Recommendation**: Start with 0.95
  
- **μ (Max shortage)**: Acceptable worst-case shortage
  - Example: 5 shifts means "in bad scenarios, we can be short at most 5 shifts"
  - **Recommendation**: Set based on your risk tolerance

### Running the Optimization

1. **Load/Generate Data**: Either upload files or use sample generator
2. **Set Parameters**: Configure costs and constraints
3. **Choose Model**: SDM (cost-focused) or SDM-CVaR (risk-aware)
4. **Click Run**: The solver will find the optimal solution
5. **Wait**: Typically 10 seconds to 5 minutes depending on problem size
6. **Analyze Results**: Explore the interactive tabs

---

## Interpreting Results

### Tab 1: Nurse Roster

**What you see**: A table with nurses as rows, days as columns.

**How to read**:
- **E**: Early shift
- **D**: Day shift
- **L**: Late shift
- **N**: Night shift
- **OFF**: Not working
- **(OT)**: Overtime (e.g., "E (OT)" = Early shift overtime)

**Summary columns**:
- **Total_Regular**: Count of regular shifts
- **Total_Overtime**: Count of overtime shifts
- **Total_Nights**: Count of night shifts
- **Total_Shifts**: All shifts combined

**What to look for**:
- ✅ Fair distribution across nurses
- ✅ No one exceeding max shifts
- ✅ Reasonable work patterns (not too many consecutive days)

### Tab 2: Cost Analysis

**Metrics**:
- **Total Cost**: Overall optimization objective value
- **Stage 1 Total**: Cost of the baseline schedule
  - Regular shift costs
  - Overtime shift costs
- **Stage 2 Expected Cost**: Expected emergency staffing cost
- **Cost per Nurse**: Average cost per nurse

**Charts**:
- **Pie Chart**: Shows proportion of each cost type
- **Bar Chart**: Regular vs Overtime distribution

**What to look for**:
- ✅ Stage 2 cost should be much smaller than Stage 1 (good baseline planning)
- ✅ Compare different runs to see trade-offs

### Tab 3: Coverage Analysis

**What you see**: How many nurses are assigned to each (day, shift) combination.

**Chart**: Bar chart showing assigned nurses by day and shift type.

**What to look for**:
- ✅ Coverage meets or exceeds baseline demand
- ✅ Weekend patterns (often lower staffing)
- ✅ No obvious gaps

### Tab 4: Risk Assessment

**Key Statistics**:
- **Mean Shortage**: Average shortage across all scenarios
- **Max Shortage**: Worst-case shortage observed
- **Std Dev**: Variability in shortages

**Distribution Chart**: Shows how shortages are distributed across scenarios.

**CVaR Metrics** (if using SDM-CVaR):
- **VaR (ξ)**: The threshold for worst-case scenarios
- **CVaR Limit (μ)**: Your specified limit
- **Confidence Level (σ)**: Protection level

**What to look for**:
- ✅ Mean shortage close to 0 is ideal
- ✅ With CVaR: Worst cases are controlled
- ✅ Without CVaR: Compare max shortage across different runs

### Tab 5: Scenario Comparison

**What you see**: Table and chart showing shortage/overage for each scenario.

**Columns**:
- **Scenario**: Scenario ID
- **Shortage**: Shifts where we're understaffed
- **Overage**: Shifts where we're overstaffed
- **Recourse Cost**: Cost of emergency adjustments

**What to look for**:
- ✅ Identify which scenarios are problematic
- ✅ Understand the range of outcomes
- ✅ Validate that CVaR is working (worst scenarios controlled)

### Tab 6: Full Report

**What you get**: Comprehensive text summary of all results.

**Use cases**:
- Share with stakeholders
- Archive results
- Compare multiple optimization runs

---

## Advanced Topics

### Comparing SDM vs SDM-CVaR

**Experiment**: Run the same problem with both models.

**Expected Observations**:
1. **SDM-CVaR will have higher total cost**
   - Why: Paying a premium for risk protection
   
2. **SDM-CVaR will have lower max shortage**
   - Why: Explicitly limiting worst-case scenarios
   
3. **SDM-CVaR will use more overtime**
   - Why: Building a more robust baseline schedule

**When to use SDM**:
- Cost is paramount
- You can handle variability in demand
- Emergency staffing is readily available

**When to use SDM-CVaR**:
- Patient safety is critical
- High cost of shortages (reputation, outcomes)
- Risk-averse organization

### Sensitivity Analysis

Try changing one parameter at a time to understand impacts:

#### Experiment 1: Emergency Cost (q⁺)
- Run with q⁺ = 200, 300, 400, 500
- **Observation**: Higher q⁺ leads to more robust baseline (more overtime)
- **Insight**: Model anticipates uncertainty when emergency is expensive

#### Experiment 2: Confidence Level (σ)
- Run SDM-CVaR with σ = 0.90, 0.95, 0.99
- **Observation**: Higher σ means more conservative, higher cost
- **Insight**: There's a cost to protection

#### Experiment 3: Max Shifts (n₁)
- Run with n₁ = 12, 15, 18, 21
- **Observation**: Tighter limits increase cost
- **Insight**: Flexibility has value

### Understanding Infeasibility

**Problem**: Model returns "Infeasible" status.

**Meaning**: No schedule exists that satisfies all constraints.

**Common Causes**:
1. **Demand too high for available nurses**
   - Fix: Add more nurses or reduce demand
   
2. **Constraints too tight**
   - Fix: Increase n₁ (max shifts) or decrease n₃ (min shifts)
   
3. **Conflicting rules**
   - Fix: Check that n₃ ≤ n₁ and parameters are reasonable

### Scenario Generation Strategies

#### Strategy 1: Historical Sampling
- Take past demand data
- Randomly sample with replacement
- Each sample = one scenario

**Pros**: Based on real data  
**Cons**: Limited to historical range

#### Strategy 2: Forecast + Error
- Use ARIMA/ML to forecast demand
- Add sampled forecast errors
- Creates scenarios around forecast

**Pros**: Forward-looking  
**Cons**: Requires forecasting model

#### Strategy 3: Built-in Generator
- Uses reasonable assumptions
- Adds random variation
- Includes weekend effects

**Pros**: Easy, quick testing  
**Cons**: May not match your specific patterns

### Performance Optimization

**If the solver is taking too long**:

1. **Reduce scenarios**: Start with 3-5, increase gradually
2. **Shorten planning period**: 7-14 days is often sufficient
3. **Aggregate shifts**: Combine similar shifts if possible
4. **Use commercial solver**: CPLEX or Gurobi are faster than CBC

**Typical solve times** (with CBC):
- Small (10 nurses, 7 days, 5 scenarios): 10-30 seconds
- Medium (20 nurses, 14 days, 10 scenarios): 1-3 minutes
- Large (50 nurses, 30 days, 20 scenarios): 5-15 minutes

### Extending the Model

**Possible enhancements**:

1. **Shift preferences**: Allow nurses to specify preferred/unpreferred shifts
2. **Skills**: Different nurses qualified for different roles
3. **Part-time staff**: Custom availability constraints
4. **Fairness objectives**: Minimize variance in shift assignments
5. **Multi-week rolling horizon**: Update schedule weekly with new forecasts

---

## Conclusion

This system provides a powerful framework for nurse scheduling under uncertainty. By understanding the two-stage structure, the role of CVaR, and how to interpret results, you can make better staffing decisions that balance cost, service quality, and risk.

**Key Takeaways**:
1. Two-stage stochastic programming plans for uncertainty
2. CVaR provides risk protection at a cost
3. Parameters encode your organization's priorities
4. Experimentation reveals trade-offs
5. The model is a decision support tool - combine with domain expertise

**Next Steps**:
1. Run sample problems to build intuition
2. Gather your organization's data
3. Calibrate parameters to your context
4. Compare different model configurations
5. Implement the best schedule!

Happy scheduling! 🩺
