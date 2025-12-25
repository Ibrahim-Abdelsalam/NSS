# 🧠 Deep Dive: `model.py` Line-by-Line Analysis

This document provides a granular analysis of the core optimization logic in `model.py`. It explains *what* the code does, *why* it does it (referencing the He et al. 2019 paper), and *how* it handles practical implementation details.

---

## 1. Helper Functions (Lines 1-179)

### `create_pwl_fatigue_approximation` (Lines 9-70)
*   **Purpose:** Implements the **Jaber et al. (2013)** fatigue model: $F(t) = 1 - e^{-\lambda t}$.
*   **Why specific code?** Exponential functions are non-linear and cannot be solved by standard MIP solvers like CBC/HiGHS.
*   **Solution:** This function generates points for a **Piecewise Linear (PWL)** approximation. It calculates `breakpoints` (time $t$) and `exact_values` ($F(t)$) which are used later in the model to create a linear "approximation envelope" using SOS2 variables.

### `validate_capacity_feasibility` (Lines 72-179)
*   **Purpose:** A "sanity check" before running the expensive optimization.
*   **Logic:**
    *   Calculates `total_capacity = num_nurses * n1` (max shifts).
    *   Compares with `baseline_demand`.
    *   **Crucial Insight (Line 107):** It notes that because of **recourse** (Emergency Staff), the problem is *mathematically* always feasible (you could just hire infinite emergency staff). However, it warns the user if the *regular* workforce is insufficient, as relying on emergency staff is expensive ($q^+$ cost).

---

## 2. Main Optimization Function: `build_and_solve_model` (Lines 180-1431)

This is the heart of the system.

### Data Setup (Lines 301-350)
*   **Sets:** Extracts sets $I$ (nurses), $J$ (days), $K$ (shifts), $\omega$ (scenarios).
*   **Parameters:** Unpacks costs ($c_1, c_2, q^+, q^-$) and constraints ($n_1, n_2, n_3$) from the input dictionary.
*   **Fatigue Params:** loads $\lambda$ and $F_{max}$ if safety is enabled.

### Variable Definitions (Lines 391-590)
*   **Stage 1 (Here-and-Now):**
    *   `sr[i][j][k]`: Regular shift binary variable.
    *   `so[i][j][k]`: Overtime shift binary variable.
    *   `SR[i]`, `SO[i]`: Indicator variables (Did nurse $i$ work *any* regular/overtime?).
*   **Fatigue (Auxiliary):**
    *   `F[i][j]`: Cumulative fatigue level.
    *   `pwl_lambda`: The "weights" for the piecewise linear approximation (SOS2).
    *   `y_segment`: Binary variables to enforce that we only interpolate between adjacent points on the fatigue curve.
*   **Stage 2 (Recourse):**
    *   `alpha[j][k][w]`: Emergency staff added (Integer).
    *   `beta[j][k][w]`: Shifts cancelled (Integer).
*   **CVaR Variables:**
    *   `xi`: The Value-at-Risk ($\text{VaR}_\alpha$) threshold (continuous).
    *   `z[w]`: The "tail loss" for scenario $\omega$.

### Objective Function (Lines 592-646)
The objective is a single minimize statement combining four components:
1.  **Stage 1 Cost:** $\sum (c_1 SR + c_2 SO)$ (Fixed costs).
2.  **Penalties:** $c_3 \times \text{StandAlone} + c_4 \times \text{BadPattern}$ (Soft constraints).
3.  **Expected Stage 2 Cost:** $\sum_{\omega} p_\omega (q^+ \alpha + q^- \beta)$ (Average recourse cost).
4.  **Safety Cost:** Cost of fatigue (if enabled).

### Constraints (Lines 648-1376)

#### Core Constraints (Paper Fidelity)
*   **Constraint 1 (One Shift/Day):** `sum(sr + so) <= 1`.
*   **Constraint 6 (Max Total):** `sum(sr + so) <= n1`.
*   **Constraint 7 (Max Night):** `sum(Night Shifts) <= n2`.

#### The "Missing" Constraints (Implementation Details)
*   **Constraint 16 (Demand):** The most important line in the code (Lines 1055-1064).
    ```python
    Plan + Alpha - Beta >= Demand[scenario]
    ```
    This links the deterministic plan to the stochastic reality.

#### Advanced Constraints (Extensions)
*   **Fatigue (Lines 1202-1376):**
    *   **F1:** Accumulates hours worked: $T_j = T_{j-1} + 12 \times \text{Worked}$.
    *   **SOS2 Logic (F5):** Uses binary variables `y_segment` to ensure that `F` is interpolated correctly from the curve breakpoints. This is a standard MIP technique for non-linear functions.

#### CVaR Logic (Lines 1120-1183)
Only active if `model_type == "SDM-CVaR"`.
*   **Constraint 19:** $\xi + \frac{1}{1-\alpha} \sum p z \le \mu$. This forces the tail risk (CVaR) to be below $\mu$.
*   **Constraint 22:** $z_\omega \ge \text{Loss}_\omega - \xi$. Defines the tail loss.

### Solver Configuration (Lines 1388-1431)
*   **Smart Selection:** Uses `create_solver` (imported) to pick Gurobi > HiGHS > CBC.
*   **Time Limits:** Logic to set `time_limit` based on `problem_size` (Variables $\times$ Constraints). This prevents the UI from hanging on massive instances.

---

## 3. Results Extraction: `extract_results` (Lines 1434-1738)

### O(1) Optimization (Lines 1546-1549)
**Critical Implementation Detail:**
```python
var_dict = {v.name: v.varValue for v in prob.variables()}
```
Instead of looping through `prob.variables()` (which is a list) thousands of times, it creates a dictionary map once.
*   **Result:** Reduces extraction time from ~3 minutes to <1 second for large problems.

### Formatting
*   **Roster:** Converts binary decisions (0/1) into "E", "D", "L", "OFF" strings.
*   **Analysis:** Aggregates costs into "Stage 1" (Fixed) vs "Stage 2" (Risk) buckets.
*   **Scenario Drill-down:** Calculates exactly how many shortages happened in each scenario to show the user "Worst Case" vs "Average Case".

---

## 4. Post-Processing & Validation (Lines 1801-End)

### `estimate_solve_time`
A heuristic function that estimates runtime based on variables/constraints counts. This is purely for UX "loading bar" estimation.

### `validate_results`
A double-check function. It iterates effectively through the *output* dataframe to ensure no constraints were violated. This protects against solver bugs or logical errors in variable extraction.
