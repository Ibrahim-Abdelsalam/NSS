# Phase 4: Parameter Tuning - Quick Start Guide

**Status:** Experimental design complete, ready to execute
**Date:** December 10, 2025

---

## Overview

Phase 4 systematically tests 81 parameter configurations to find optimal settings for the PWL fatigue model. Each configuration runs 3 replications for statistical robustness (243 total runs).

## Experimental Design

### Factorial Design: 3×3×3×3 = 81 Configurations

| Factor | Levels | Description |
|--------|--------|-------------|
| **Lambda (λ)** | 0.02, 0.03, 0.04 | Fatigue accumulation rate |
| **Safety Weight** | $30, $50, $80 | Patient safety cost per fatigue unit |
| **Threshold** | 0.60, 0.70, 0.80 | Maximum allowed fatigue |
| **Demand Level** | Low, Medium, High | Problem instance size/demand |

### Instance Configurations

| Demand Level | Nurses | Days | Scenarios | Min Shifts (n3) | Emergency Cost (q_plus) |
|--------------|--------|------|-----------|-----------------|-------------------------|
| **Low** | 8 | 10 | 5 | 6 | $250 |
| **Medium** | 10 | 14 | 10 | 8 | $300 |
| **High** | 12 | 14 | 15 | 10 | $350 |

### Fixed Parameters
- **PWL Segments:** 8 (validated at 0.713% max error)
- **Shift Duration:** 12 hours
- **Time Limit:** 300 seconds (5 minutes per run)
- **Replications:** 3 per configuration

---

## Commands

### Test Mode (Quick Validation)
Runs 9 configurations in ~10 minutes:
```bash
python experiments/parameter_tuning.py --mode test
```

**Output:** `results/parameter_tuning_test.csv`

### Full Experiment
Runs all 243 experiments (~4-8 hours):
```bash
python experiments/parameter_tuning.py --mode full
```

**Output:** 
- `results/parameter_tuning_results.csv` (final)
- `results/parameter_tuning_results_temp.csv` (saves every 10 runs)

### Analysis
After experiments complete:
```bash
python experiments/analyze_tuning_results.py
```

**Outputs:**
- `results/sensitivity_analysis.csv`
- `results/optimal_configurations.csv`
- `results/figures/main_effects.png`
- `results/figures/cost_fatigue_tradeoff.png`
- `results/figures/solve_time.png`
- `results/figures/lambda_weight_interaction.png`

---

## Metrics Collected

### Cost Metrics
- Total cost, Stage 1 cost, Stage 2 cost
- Regular shift cost, Overtime shift cost
- Patient safety cost, Average recourse cost

### Fatigue Metrics
- Max fatigue, Average fatigue
- High-fatigue days (F > threshold)
- Fatigue threshold used

### Operational Metrics
- Working nurses (out of total)
- Regular shift count, Overtime shift count
- Average consecutive shifts, Max consecutive shifts
- Average shortage, Max shortage

### Performance Metrics
- Solve time (seconds)
- Optimization status (Optimal/Infeasible/Timeout)
- Configuration ID, Replication, Seed

---

## Analysis Methods

### 1. Sensitivity Analysis
**Method:** One-way ANOVA for each factor
**Metrics:** F-statistic, p-value, eta-squared (effect size)
**Outcomes:** Total cost, Patient safety cost, Max fatigue, Avg fatigue

**Interpretation:**
- p < 0.05: Factor has significant effect
- η² > 0.14: Large effect size
- η² = 0.06-0.14: Medium effect size
- η² < 0.06: Small effect size

### 2. Interaction Analysis
**Method:** Two-way interaction strength
**Focus:** Lambda × Weight, Lambda × Threshold, Weight × Threshold
**Metric:** Relative interaction strength vs main effects

### 3. Optimal Configuration Selection

**Strategy 1: Minimize Cost**
- Select configuration with lowest total cost
- Use when budget is primary constraint

**Strategy 2: Minimize Fatigue**
- Select configuration with lowest max fatigue
- Use when patient safety is paramount

**Strategy 3: Balanced Approach** (RECOMMENDED)
- Normalize cost, max fatigue, high-fatigue days to [0,1]
- Combined score = (cost_norm + fatigue_norm + risk_norm) / 3
- Select configuration with lowest combined score
- Balances economic and safety objectives

---

## Expected Results

### Hypotheses

**H1:** Lambda (λ) will significantly affect fatigue levels
- Higher λ → Faster fatigue accumulation → Higher max fatigue

**H2:** Safety weight will significantly affect costs
- Higher weight → More expensive to have high fatigue → Lower max fatigue but higher total cost

**H3:** Threshold will affect constraint tightness
- Lower threshold → More restricted schedules → Higher total cost

**H4:** Demand level will affect solve time and feasibility
- Higher demand → Larger instances → Longer solve time

**H5:** Lambda × Weight interaction
- Moderate interaction expected
- Higher λ + Higher weight → Stronger fatigue avoidance

### Anticipated Optimal Configuration
Based on Phase 3 findings and literature:

```
Lambda (λ):        0.03  (medium rate, realistic for 12h shifts)
Safety Weight:     $50   (balances cost and safety)
Threshold:         0.70  (safety literature recommendation)
Demand Level:      Medium (representative problem size)
```

**Expected Performance:**
- Total cost increase: 3-5% vs no-fatigue baseline
- Max fatigue: 0.40-0.60 (well below threshold)
- High-fatigue days: 0-2 (minimal safety violations)
- Solve time: < 60 seconds

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **4.1 Design** | ✅ Complete | Experimental design, script development |
| **4.2 Test** | 10 min | Run test mode, verify correctness |
| **4.3 Execute** | 4-8 hours | Full experiment (243 runs) |
| **4.4 Analyze** | 2-3 hours | Statistical analysis, visualization |
| **4.5 Report** | 2-3 hours | Document findings, select optimal params |

**Total Phase 4 Duration:** 1-2 days

---

## Troubleshooting

### Issue: Experiments running slowly
**Solution:** 
- Check solver performance with `solver_config.py`
- Reduce time_limit in parameter_tuning.py
- Use test mode first to identify bottlenecks

### Issue: Many infeasible solutions
**Solution:**
- Review n3 (min shifts) - may be too high
- Check threshold - may be too restrictive
- Examine demand levels - may exceed capacity

### Issue: All fatigue values near zero
**Solution:** Expected for some configurations!
- When demand >> capacity, model chooses SR[i]=0
- Emergency-only approach avoids baseline commitment
- This is optimal behavior, not a bug
- Will see non-zero fatigue in Medium/Low demand with appropriate q_plus

### Issue: Analysis script fails
**Solution:**
- Ensure all experiments completed successfully
- Check CSV file exists and has correct columns
- Verify pandas/matplotlib/scipy installed
- Check for NaN values in results

---

## Next Steps After Phase 4

1. **Document Optimal Parameters**
   - Create `docs/PARAMETER_SELECTION.md`
   - Justify selection with statistical evidence
   - Include sensitivity plots

2. **Update Default Parameters** (in `model.py`)
   ```python
   def get_default_params():
       return {
           'fatigue_lambda': 0.03,  # From Phase 4
           'patient_safety_weight': 50,  # From Phase 4
           'max_fatigue_threshold': 0.70,  # From Phase 4
           'pwl_segments': 8,  # Fixed
           # ... other params
       }
   ```

3. **Proceed to Phase 5: Statistical Validation**
   - Run 30 independent replications with optimal params
   - Compare baseline (no fatigue) vs proposed (with fatigue)
   - Paired t-test, effect size, confidence intervals
   - Confirm cost increase: 3-5%
   - Confirm fatigue reduction: 40%+

4. **Begin Paper Writing (Phase 6)**
   - Introduction, Literature Review
   - Methodology (PWL formulation)
   - Computational Study (Phase 4 & 5 results)
   - Conclusions and Managerial Insights

---

## Files Reference

### Created for Phase 4
1. `experiments/parameter_tuning.py` (430+ lines)
   - Main experiment script
   - Factorial design implementation
   - Metrics collection

2. `experiments/analyze_tuning_results.py` (460+ lines)
   - Statistical analysis pipeline
   - Visualization generation
   - Optimal configuration selection

3. `docs/PHASE4_QUICKSTART.md` (this file)
   - Quick reference guide
   - Commands and expected outputs

### Updated
1. `IMPLEMENTATION_CHECKLIST.md`
   - Phase 4.1 marked complete
   - Detailed experimental design documented

### To Be Created
1. `docs/PARAMETER_SELECTION.md` (after Phase 4.4)
   - Selected optimal parameters
   - Statistical justification
   - Sensitivity analysis summary

---

## Success Criteria

Phase 4 is complete when:

- [x] Experimental design finalized (81 configs)
- [x] Scripts developed and tested
- [ ] Test mode runs successfully (9 configs)
- [ ] Full experiment completes (243 runs)
- [ ] Analysis pipeline runs successfully
- [ ] Optimal configuration identified
- [ ] Statistical significance confirmed (p < 0.05)
- [ ] Visualizations generated (4 plots)
- [ ] Results documented in PARAMETER_SELECTION.md

**Current Status:** 3/9 criteria met, ready for execution

---

**Last Updated:** December 10, 2025
**Next Action:** Run test mode experiments
