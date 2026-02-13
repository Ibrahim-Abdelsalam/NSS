# Experiment Results and Documentation

## Input Parameters

### Common Parameters
- **Nurses**: 20
- **Planning Horizon**: 14 Days
- **Scenarios**: 10 (Stochastic Demand)
- **Shifts**: 4 (Early, Day, Late, Night)
- **Costs**:
    - Regular Shift ($c_1$): 100
    - Overtime Shift ($c_2$): 150
    - Emergency Shift ($q^+$): 200
    - Cancellation ($q^-$): 0
- **Work Rules**:
    - Max Shifts ($n_1$): 15
    - Max Night Shifts ($n_2$): 5
    - Min Regular Shifts ($n_3$): 5

### Case Specifics

| **Case Name** | **Model Type** | **Fatigue** | **Risk Control (CVaR)** | **Feasibility** | **Notes** |
|:---|:---:|:---:|:---:|:---:|:---|
| **SDM-FATIGUE** | SDM | ✅ Yes | N/A | ✅ **Feasible** | Minimizes Cost + Safety |
| **SDM-NO FATIGUE**| SDM | ❌ No | N/A | ✅ **Feasible** | Minimizes Cost Only |
| **CVAR-FATIGUE** | SDM-CVaR | ✅ Yes | $\mu=150.0$ (relaxed) | ✅ **Feasible** | Controls Safety & Tail Risk |
| **CVAR-NO FATIGUE**| SDM-CVaR | ❌ No | $\mu=150.0$ (relaxed) | ✅ **Feasible** | Controls Tail Risk Only |
| **CVAR-STRICT** | SDM-CVaR | Any | $\mu=50.0$ (strict) | ❌ **Infeasible**| Demonstrates Resource Limit |

## Input Data (Samples)

### Nurse List (`case_nurses.csv`)
20 Nurses Generated (`Nurse_1` to `Nurse_20`)
```csv
Nurse_1
Nurse_2
Nurse_3
...
Nurse_20
```

### Demand Scenarios (`case_scenarios.csv`)
10 Scenarios × 14 Days × 4 Shifts
```csv
scenario,day,shift,demand
1,1,E,4
1,1,D,6
1,1,L,5
1,1,N,3
1,2,E,4
...
```

---

## Output Calculations & Solutions

### 1. SDM-FATIGUE
- **Objective Value**: 36,232.29
- **Status**: Optimal
- **Analysis**:
    - The inclusion of fatigue costs increases the objective value compared to the NO FATIGUE case.
    - This reflects the "patient safety cost" component ($\text{Weight} \times \text{Cumulative Fatigue}$).
    - The model likely adjusted schedules to allow for more recovery, potentially incurring slightly higher staffing costs or just accepting the fatigue penalty.

### 2. SDM-NO FATIGUE
- **Objective Value**: 32,240.00
- **Status**: Optimal
- **Analysis**:
    - Lower cost because fatigue penalties are ignored.
    - Schedules may be more compressed, potentially leading to higher nurse fatigue in reality (though not measured in the objective).


### 3. CVAR-FATIGUE
- **Objective Value**: 38,784.58
- **Status**: Optimal / Feasible
- **Analysis**:
    - Feasible after relaxing $\mu$ to 150.0.
    - Higher cost than SDM-FATIGUE (38.8k vs 36.2k) because the CVaR constraint forces the model to make more expensive scheduling decisions (e.g., more overtime, less risky staffing) to avoid large shortages in worst-case scenarios.

### 4. CVAR-NO FATIGUE
- **Objective Value**: 34,792.29
- **Status**: Optimal / Feasible
- **Analysis**:
    - Feasible after relaxing $\mu$ to 150.0.
    - Higher cost than SDM-NO FATIGUE (34.8k vs 32.2k) due to risk mitigation.
    - As expected, "NO FATIGUE" is cheaper than "FATIGUE" (34.8k vs 38.8k) because it ignores the hidden costs of nurse fatigue.

### 5. CVAR-STRICT (Infeasible Case)
- **Status**: **Infeasible**
- **Analysis**:
    - This case used the original strict parameter **$\mu=50.0$** (max acceptable shortage).
    - The solver could not find a solution where the worst-case shortage across all scenarios was $\le 50$.
    - This demonstrates that the current workforce (20 nurses) is too small to strictly guarantee that emergency staff usage stays below 50 in 95% of worst-case demand spikes.
    - **Lesson**: Strict risk controls require either (a) larger baseline capacity or (b) relaxed constraints (as done in Cases 3 & 4).


## Model Comparison & Trade-offs

| **Model Case** | **Advantages (Pros)** | **Disadvantages (Cons)** |
|:---|:---|:---|
| **SDM-FATIGUE** | 🟢 **Safe & Efficient**<br>Balances costs with patient safety.<br>🟢 **Realistic**<br>Accounts for fatigue accumulation.<br>🟢 **Solved**<br>Easier to solve than CVaR models. | 🔴 **Higher Cost**<br>~12% more expensive than ignoring fatigue.<br>🔴 **No Risk Guarantee**<br>Does not strictly limit "worst-case" shortages. |
| **SDM-NO FATIGUE**| 🟢 **Lowest Cost**<br>Cheapest objective value.<br>🟢 **Fastest Solve**<br>Simplest mathematical model. | 🔴 **Unsafe**<br>Ignores burnout/safety risks.<br>🔴 **Unrealistic**<br>Schedules may be physically exhausting.<br>🔴 **High Risk**<br>Unlimited worst-case understaffing. |
| **CVAR-FATIGUE** | 🟢 **Robust & Safe**<br>Controls BOTH fatigue and shortage risk.<br>🟢 **Guaranteed**<br>Statistical confidence on worst outcomes. | 🔴 **Most Expensive**<br>Highest cost due to dual constraints.<br>🔴 **Complex**<br>Computationally intensive to solve.<br>🔴 **Strict**<br>Can be infeasible with tight resources. |
| **CVAR-NO FATIGUE**| 🟢 **Risk-Controlled**<br>Guarantees limits on shortages.<br>🟢 **Cheaper than Fatigue**<br>Lower cost than full safety model. | 🔴 **Unsafe**<br>Trades nurse well-being for coverage.<br>🔴 **Inconsistent**<br>Manages quantitative risk but ignores fatigue. |
| **CVAR-STRICT** | 🟢 **Ideal Robustness**<br>Attempts strict security against shortages. | 🔴 **Infeasible**<br>Impossible without infinite resources.<br>🔴 **Impractical**<br>Proves zero-risk is unattainable. |




## Conclusion and Recommendations

1.  **Feasibility**: The current workforce (20 nurses) is insufficient to meet the strict risk constraints ($\mu=50$) under the generated stochastic demand. The SDM model solves by using "emergency staff" (which corresponds to shortage/understaffing), but the CVaR model rejects high usage of emergency staff in worst-case scenarios.
2.  **Fatigue Impact**: Enabling fatigue constraints adds ~12% to the objective value (36k vs 32k), representing the "cost" of maintaining safer, less fatiguing schedules.
3.  **Next Steps**:
    - **Run with relaxed CVaR**: Try $\mu=100$.
    - **Add Capacity**: Add 2-5 more nurses to the pool.

