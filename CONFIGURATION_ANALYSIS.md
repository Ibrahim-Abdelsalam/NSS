# Model Configuration Analysis & Testing Strategy

## 1. Problem Dimensions & Boundaries
Based on analysis of `model.py`, `app.py`, and `model_2.py`, the following dimensions define the configuration space of the Nurse Scheduling Problem.

### A. Problem Size
| Dimension | Minimum | Maximum (App Limit) | Typical | Notes |
|-----------|---------|---------------------|---------|-------|
| **Nurses** | 1 | 200 | 10-50 | Number of available staff members (`I_nurses`) |
| **Days** | 1 | 90 | 14-28 | Length of planning horizon (`J_days`) |
| **Scenarios** | 1 | 300 | 5-10 | Number of demand scenarios (`W_scenarios`) |
| **Shift Types** | 1 | Unlimited | 3-4 | Typically Early (E), Day (D), Late (L), Night (N) |

### B. Constraints & Work Rules
| Parameter | Description | Min | Max | Relation |
|-----------|-------------|-----|-----|----------|
| **n1** | Max Total Shifts | 1 | 30 | `n1 <= num_days` |
| **n2** | Max Night Shifts | 0 | 15 | `n2 <= n1` |
| **n3** | Min Regular Shifts | 0 | 20 | `n3 <= n1` |
| **n4** | Min Complete Weekends | 0 | 4 | `n4 <= weeks_in_period` |
| **Quotas** | Min/Max per Shift Type | 0 | n1 | Optional hard constraints |

### C. Cost Parameters
| Parameter | Description | Range | Implication |
|-----------|-------------|-------|-------------|
| **c1** | Regular Shift Cost | $0 - $10k | Base cost |
| **c2** | Overtime Cost | $0 - $10k | Usually `c1 < c2` |
| **q_plus** | Emergency Cost | $0 - $10k | Usually `c2 < q_plus` (Recourse) |
| **q_minus** | Cancellation Cost | $0 - $100 | Usually minimal |

### D. Advanced Features
- **Fatigue Modeling:** Adds `patient_safety_cost` and `F[i][j]` variables. Parameters: `lambda` (0.01-0.10), `weight` (0-200), `threshold` (0.5-0.9).
- **Recourse Bounds:** Hard limits on `alpha` (emergency) and `beta` (cancellations).
- **CVaR Risk Control:** Adds `xi` and `z_omega` variables. Parameters: `sigma` (0.90-0.99), `mu` (0-50).
- **Night Rest Rules:** Adds sequence constraints (e.g., min 2 consecutive nights).

## 2. Comprehensive Test Suite
A systematic test script `scripts/test_comprehensive_configurations.py` has been created to verify the model under various configurations.

### Test Coverage Strategy
The suite tests **13 distinct configurations** covering all major logical branches:

1.  **Baseline:** Default parameters (Small instance).
2.  **Cost Extremes:** 
    -   Zero costs (mathematical validity check).
    -   High penalty costs (impact on objective).
3.  **Constraint Boundaries:**
    -   Strict `n1` (Force understaffing/emergency usage).
    -   High `n2`/`n3` (Force specific allocation patterns).
4.  **Feature Toggles:**
    -   Fatigue Model ON/OFF.
    -   CVaR Risk Model ON.
    -   Recourse Bounds (Hard limits).
5.  **Complex Constraints:**
    -   Night Rest Rules (Consecutive nights + rest days).
    -   Weekend Rules (Complete weekends off).
    -   Shift Quotas (Min/Max per shift).
6.  **Negative Testing:**
    -   Infeasible Quotas (e.g., Min 100 shifts/nurse).

### How to Run Tests
```bash
python3 scripts/test_comprehensive_configurations.py
```
This script will output a table of results, including Pass/Fail status, solve time, and objective values.
