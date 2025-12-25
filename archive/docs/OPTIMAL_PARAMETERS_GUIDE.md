# Quick Start: Using Optimal Parameters

## Recommended Configuration (Production Use)

Based on comprehensive parameter tuning (2,430 experiments), use these settings for production:

```python
optimal_params = {
    # Fatigue parameters (VALIDATED)
    'patient_safety_enabled': True,
    'fatigue_lambda': 0.03,              # ⭐ From Jaber et al. 2013 + validated
    'patient_safety_weight': 50.0,        # ⭐ Literature-supported $40-$100 range
    'max_fatigue_threshold': 0.70,        # ⭐ Balanced safety/cost
    'shift_duration': 12,
    
    # Work rules
    'n1': 14,  # Max total shifts per nurse (adjust based on your needs)
    'n2': 5,   # Max night shifts
    'n3': 0,   # Min regular shifts (0 = flexible)
    
    # Costs
    'c1': 100,    # Regular shift cost
    'c2': 150,    # Overtime cost  
    'q_plus': 400,  # Emergency staff cost (Medium: $400, High: $450)
    
    # Risk management
    'sigma': 0.95,
    'mu': 5.0,
}
```

## Problem Size Recommendations

### ✅ RECOMMENDED: Medium or High Demand
- **Medium:** 15 nurses × 14 days × 10 scenarios
  - Success rate: 100%
  - Solve time: ~4 seconds
  - Max fatigue: 0.62 (safe)
  
- **High:** 18 nurses × 14 days × 15 scenarios  
  - Success rate: 100%
  - Solve time: ~6 seconds
  - Max fatigue: 0.67 (safe)

### ⚠️ NOT RECOMMENDED: Low Demand
- **Low:** 12 nurses × 10 days × 5 scenarios
  - Success rate: 10% (95% timeout)
  - Solve time: 120s timeout (or 0.7-2s if successful)
  - Issue: Tight constraints, minimal slack

## Expected Results

With optimal parameters, expect:

### Costs
- **Total:** $45,000 - $49,000
- **Stage 1 (Baseline):** 80-85% of total
- **Stage 2 (Recourse):** 10-15% of total  
- **Patient Safety:** 3-8% of total ($2,000-$4,000)

### Fatigue
- **Max Fatigue:** 0.62-0.67 (safely under 0.70 threshold)
- **Avg Fatigue:** 0.25-0.30
- **High-Risk Days:** 15-25 days (F > 0.60)
- **High-Fatigue Days:** 35-45 days (F > 0.50)

### Performance
- **Solve Time:** 2-6 seconds (Medium/High demand)
- **Success Rate:** 100%
- **Status:** "Optimal"

## Alternative Configurations

### If You Need Tighter Safety Control

```python
strict_safety_params = {
    'fatigue_lambda': 0.03,
    'patient_safety_weight': 80.0,       # Higher weight
    'max_fatigue_threshold': 0.60,       # Stricter limit ⚠️
    'shift_duration': 12,
}
```

**Tradeoffs:**
- Cost: +15.8% ($53,862 vs $45,859)
- Max fatigue: -18% (0.41 vs 0.62)
- High-risk days: 0 (zero!)
- Solve time: Faster (1.4s vs 3.7s)

### If You Need Lower Cost

```python
budget_params = {
    'fatigue_lambda': 0.02,              # Lower accumulation
    'patient_safety_weight': 30.0,       # Lower weight
    'max_fatigue_threshold': 0.80,       # Relaxed limit ⚠️
    'shift_duration': 12,
}
```

**Tradeoffs:**
- Cost: -13.7% ($42,505 vs $45,859)
- Max fatigue: +19% (0.74 vs 0.62)
- High-risk days: +274% (72 vs 19)
- Solve time: Slower (9.8s vs 3.7s)

⚠️ **Warning:** Not recommended due to high fatigue levels

## Usage Example

```python
from model import build_and_solve_model
import pandas as pd

# Load your data
nurses = ['Nurse1', 'Nurse2', ..., 'Nurse15']  # 15 nurses for Medium
scenarios_df = pd.read_csv('your_demand_scenarios.csv')

# Use optimal parameters
optimal_params = {
    'patient_safety_enabled': True,
    'fatigue_lambda': 0.03,
    'patient_safety_weight': 50.0,
    'max_fatigue_threshold': 0.70,
    'shift_duration': 12,
    'n1': 14, 'n2': 5, 'n3': 0,
    'c1': 100, 'c2': 150, 'q_plus': 400,
    'sigma': 0.95, 'mu': 5.0,
}

# Solve
prob, status = build_and_solve_model(
    nurses,
    scenarios_df,
    optimal_params,
    model_type="SDM-CVaR",
    solver_name="GUROBI"  # or "CBC", "HiGHS"
)

print(f"Status: {status}")
print(f"Total Cost: ${prob.objective.value():,.2f}")
```

## Calibration for Your Hospital

The optimal parameters are validated for **computational tractability** and **model sensitivity**, but should be calibrated with your facility's data:

### 1. Calibrate Safety Weight ($w_f$)

```python
# Gather your data:
error_rate_per_fatigue_unit = 0.02  # 2% increase per 0.1 fatigue
avg_error_cost = 5000               # Your facility's avg error cost
turnover_cost = 50000               # Cost to replace one nurse

# Calculate:
error_cost_per_fatigue = error_rate_per_fatigue_unit * avg_error_cost  # $100
turnover_risk_per_fatigue = 0.001 * turnover_cost                       # $50

recommended_weight = error_cost_per_fatigue + turnover_risk_per_fatigue  # $150
```

### 2. Validate Lambda ($\lambda$)

Use workforce fatigue assessments:
- If nurses report higher fatigue: increase to 0.04
- If nurses report lower fatigue: decrease to 0.02
- Default 0.03 validated from Jaber et al. (2013) Table 5

### 3. Set Threshold ($F_{\max}$)

Based on institutional risk tolerance:
- **High-risk units (ICU, ER):** 0.60 (zero high-risk days)
- **Standard units:** 0.70 (balanced)
- **Budget-constrained:** 0.80 (not recommended)

## Troubleshooting

### Problem: Model times out (120s+)

**Likely cause:** Low demand problem (tight constraints)

**Solutions:**
1. Increase nurses or reduce peak demand
2. Relax n3 constraint (set n3=0)
3. Increase threshold to 0.80
4. Use warm start from relaxed solution
5. Increase Gurobi time limit to 300s

### Problem: Zero fatigue in results

**Likely cause:** High demand + low weight + high threshold

**Solutions:**
1. Decrease threshold to 0.60 or 0.70
2. Increase weight to $50 or $80
3. Check that `patient_safety_enabled=True`

### Problem: Infeasible solution

**Likely causes:**
1. Peak demand > total capacity (nurses × n1)
2. Threshold too tight (0.60) with high demand
3. n3 too high (forces many nurses to work)

**Solutions:**
1. Add more nurses
2. Relax threshold to 0.70 or 0.80
3. Reduce n3 to 0
4. Increase max_emergency_staff limit

## Files and Documentation

- **Experiment results:** `EXPERIMENTAL_RESULTS_SUMMARY.md`
- **Data:** `results/parameter_tuning_results.csv` (2,430 runs)
- **Analysis:** `results/sensitivity_analysis.csv`
- **Figures:** `results/figures/*.png` (4 plots)
- **Scripts:** `experiments/parameter_tuning.py`, `experiments/analyze_tuning_results.py`
- **Report:** Section 5 of `IMPLEMENTATION_REPORT.tex`

## Citation

If you use these optimal parameters in research:

```
Parameter values validated through factorial experiment with 2,430 
optimization runs (81 configurations × 30 replications). Fatigue 
accumulation rate λ=0.03 validated from Jaber et al. (2013) Table 5. 
Safety weight $50 per fatigue unit supported by healthcare literature 
(Van Den Bos et al. 2011, Bell et al. 2023). Maximum threshold 0.70 
provides optimal balance between cost (+7.9%) and safety (73% reduction 
in high-risk days) compared to relaxed threshold 0.80.
```

## Next Steps

1. ✅ Parameter tuning: COMPLETE
2. ⏳ Statistical validation: Run 30 replications comparing baseline vs fatigue models
3. ⏳ Real-world pilot: Test with actual hospital data
4. ⏳ Publication: Submit to Operations Research Perspectives

---

**Last Updated:** December 14, 2025  
**Experiment Duration:** 15.75 hours  
**Success Rate:** 83.4% (2,027/2,430 runs)  
**Recommended Config:** λ=0.03, w=$50, T=0.70, Medium/High demand
