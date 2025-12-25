# 🏥 Overtime vs. Emergency Staffing: Dynamics & Implementation Analysis

This document explores the economic and mathematical relationship between **Overtime (Stage 1)** and **Emergency Staffing (Stage 2)**, comparing the seminal logic in He et al. (2019) with the behavior of our implemented model.

---

## 1. Theoretical Dynamics (The Research Paper)

In a two-stage stochastic model, the decision-maker balances "Here-and-Now" costs against "Wait-and-See" risks.

### A. Economic Decision Rules
The choice between Overtime and Emergency Staffing is primarily driven by the ratio of costs:
1.  **Overtime ($c_2$):** A Stage 1 cost. It is "guaranteed" once decided, regardless of which demand scenario occurs.
2.  **Emergency Staffing ($q^+$):** A Stage 2 cost. It is only incurred in specific scenarios where demand exceeds the planned capacity.

**The Economic Pivot Point:**
> The model will prefer **Overtime** over **Emergency Staffing** only if:
> $$c_2 < q^+ \cdot P(\text{Shortage})$$
> *Where $P(\text{Shortage})$ is the probability of a high-demand scenario.*

### B. The Overtime Paradox in the Paper
The paper defines **Overtime ($so_{ijk}$)** and **Regular ($sr_{ijk}$)** as separate variables, but it lacks a "Cap" on regular shifts. 
- **Paper Logic:** $sr \ge n_3$ (Min Regular).
- **Economic Consequence:** Since $c_1 < c_2$ (Regular is cheaper), and there is no upper limit on $sr$ other than the total capacity $n_1$, the optimizer will mathematically *always* fill $sr$ up to $n_1$ before ever touching $so$.
- **Result:** In the paper's *written* formulation, Overtime is essentially redundant.

---

## 2. Implementation Dynamics (Our Model)

We identified the "Overtime Paradox" and introduced specific features to make the dynamics operational and useful for real-world hospitals.

### A. The "Enforce Max Regular" Fix
We added **Constraint 8b** (Optional): $\sum sr \le n_3$.
*   **Without this:** The model treats all planned shifts as "Regular" because they are cheaper ($100 vs $150).
*   **With this:** The model is forced to classify any shift beyond $n_3$ as "Overtime." This creates the intended distinction found in HR contracts.

### B. Trade-off Dynamics: Planner's Control
Our model allows the user to see the "Economic Pivot" in action through three levers:

| Feature | Dynamic | Impact on Decision |
| :--- | :--- | :--- |
| **Emergency Cost ($q^+$)** | If set very high (e.g., > $500)... | Model will schedule **Overtime** aggressively in Stage 1 to avoid any risk of needing Stage 2 staff. |
| **Demand Variability** | If scenarios have high variance... | The **Expected Cost** of Emergency Staffing rises, making "Guaranteed" Overtime look like a better hedge. |
| **CVaR Risk Control** | If Risk-Aware mode is ON... | The model ignores the "Average" cost and focuses on the **Worst Case**. It will use Overtime to cap the maximum possible shortage. |

---

## 3. Direct Comparison: Paper vs. Implementation

| Feature | Paper (He et al. 2019) | Our Implementation |
| :--- | :--- | :--- |
| **Timing** | Overtime is Stage 1; Emergency is Stage 2. | Matches Paper exactly. |
| **Category Force** | Relies on implicit capacity. | Uses **Constraint 8b** to explicitly force Overtime classification. |
| **Recourse Bounds** | Unbounded (implied). | **Constraint 17-18** allows capping Emergency Staff (e.g., "We can only hire 5 agency nurses"). |
| **User Agency** | Static values. | **Interactive Sliders** allow users to "feel" the pivot point by adjusting costs in real-time. |

---

## 4. Summary Table of Staffing Archetypes

| Scenario | Optimization Result | Decision Rationale |
| :--- | :--- | :--- |
| **"Safe & Cheap"** | High Regular, Low Overtime, Low Emergency | Demand is predictable; $c_1$ handles it. |
| **"Volatile Demand"** | High Overtime (Hedge) | $P(\text{Shortage})$ is high; $c_2$ is cheaper than expected $q^+$. |
| **"Severe Labor Shortage"** | High Emergency | Nurse capacity ($n_1$) is hit; model HAS to hire from outside. |

---

## Conclusion
The paper provides the **mathematical foundation** for the trade-off, but our implementation provides the **operational mechanics**. By using **Constraint 8b**, we fix the paper's underspecification, allowing the "Stage 1 vs. Stage 2" dynamic to actually manifest in the roster as intended.
