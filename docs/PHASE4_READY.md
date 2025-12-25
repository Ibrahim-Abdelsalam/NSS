# Phase 4 Complete: Ready to Execute

**Date:** December 10, 2025  
**Status:** Experimental design complete, scripts ready

---

## What We've Accomplished

### ✅ Phase 3: Testing & Validation (COMPLETE)
- PWL accuracy validated: 0.713% max error (better than expected)
- All variables created correctly (F, T, λ)
- All 6 constraints implemented and enforced (F1-F6)
- Economic behavior validated (zero-fatigue is optimal in some scenarios)
- 4 comprehensive documentation files created

### ✅ Phase 4.1: Experimental Design (COMPLETE)
- Factorial design: 3×3×3×3 = 81 configurations
- 3 replications per config = 243 total runs
- Two complete scripts ready:
  1. `parameter_tuning.py` (430+ lines) - Run experiments
  2. `analyze_tuning_results.py` (460+ lines) - Analyze results
- Quick start guide created
- Checklist updated

---

## What You Can Do Now

### Option 1: Run Test Mode (Recommended First)
Quick validation with 9 configurations (~10 minutes):

```bash
cd /Users/ibrahim/Documents/GitHub/NSS
python experiments/parameter_tuning.py --mode test
```

This will:
- Test 3 lambda values × 3 weight values (Medium demand only)
- Verify all components work correctly
- Generate `results/parameter_tuning_test.csv`
- Take approximately 10 minutes

### Option 2: Run Full Experiment
Complete 243 experiments (~4-8 hours):

```bash
cd /Users/ibrahim/Documents/GitHub/NSS
python experiments/parameter_tuning.py --mode full
```

This will:
- Run all 81 configurations × 3 replications
- Save intermediate results every 10 runs
- Generate `results/parameter_tuning_results.csv`
- Take approximately 4-8 hours (depending on solver speed)

**Note:** You'll be prompted to confirm before starting (type "yes")

### Option 3: Analyze Existing Results
If you've already run experiments:

```bash
cd /Users/ibrahim/Documents/GitHub/NSS
python experiments/analyze_tuning_results.py
```

This will:
- Load results from `results/parameter_tuning_results.csv`
- Perform sensitivity analysis (ANOVA)
- Identify optimal configurations
- Generate 4 publication-quality plots
- Create summary CSV files

---

## Expected Outputs

### From parameter_tuning.py

**Test Mode:**
```
results/
└── parameter_tuning_test.csv     (9 rows, ~30 columns)
```

**Full Mode:**
```
results/
├── parameter_tuning_results.csv       (243 rows, ~30 columns)
└── parameter_tuning_results_temp.csv  (intermediate saves)
```

**Columns in CSV:**
- Configuration: `config_id`, `lambda`, `weight`, `threshold`, `demand_level`
- Replication: `replication`, `seed`, `nurses`, `days`, `scenarios`
- Costs: `total_cost`, `stage1_cost`, `stage2_cost`, `patient_safety_cost`
- Fatigue: `max_fatigue`, `avg_fatigue`, `high_fatigue_days`, `fatigue_threshold`
- Operations: `working_nurses`, `regular_shift_count`, `overtime_shift_count`
- Quality: `avg_consecutive_shifts`, `max_consecutive_shifts`
- Performance: `solve_time`, `status`

### From analyze_tuning_results.py

```
results/
├── sensitivity_analysis.csv           (Summary statistics & ANOVA)
├── optimal_configurations.csv         (Best configs for 3 strategies)
└── figures/
    ├── main_effects.png               (4-panel factor effects)
    ├── cost_fatigue_tradeoff.png     (Pareto frontier)
    ├── solve_time.png                 (Computational performance)
    └── lambda_weight_interaction.png  (Heatmap)
```

---

## Recommended Workflow

### Step 1: Test Mode (10 minutes)
```bash
python experiments/parameter_tuning.py --mode test
```

**Check:**
- All 9 runs completed successfully
- Status = "Optimal" for most/all runs
- Fatigue values are reasonable (0.0-0.7)
- Solve times < 60 seconds
- No Python errors

**If issues:** Debug before full experiment

### Step 2: Full Experiment (4-8 hours)
```bash
python experiments/parameter_tuning.py --mode full
# Type "yes" when prompted
```

**Monitor:**
- Progress printed every run
- Intermediate saves every 10 runs
- Can interrupt with Ctrl+C and resume (check temp file)

**Tip:** Run overnight or during work hours

### Step 3: Analysis (30 minutes)
```bash
python experiments/analyze_tuning_results.py
```

**Review:**
1. Console output for summary statistics
2. `sensitivity_analysis.csv` for significant factors
3. `optimal_configurations.csv` for best parameters
4. `figures/` for visualizations

### Step 4: Documentation (2-3 hours)
Create `docs/PARAMETER_SELECTION.md`:
- Report optimal parameters
- Include sensitivity plots
- Justify selection with statistics
- Document cost-fatigue tradeoff

---

## What to Expect

### Test Mode Results (9 configs)

**Expected patterns:**
- Higher λ → Higher max fatigue
- Higher weight → Higher total cost (stronger fatigue penalty)
- Similar patterns across all 9 configurations
- Solve times: 5-30 seconds per run

**Sample output:**
```
Config 1 | λ=0.02 w=$30 T=0.70 D=Medium Rep=1
Generating instance: 10 nurses × 14 days × 10 scenarios
Parameters: λ=0.02, weight=$30, threshold=0.70
Solving model...
Status: Optimal
Solve time: 12.34s

Results:
  Total Cost: $18,450.00
  Patient Safety Cost: $245.50
  Max Fatigue: 0.4523
  Avg Fatigue: 0.2834
  Working Nurses: 7/10
  High-Fatigue Days: 1
```

### Full Experiment Results (243 runs)

**Anticipated findings:**

1. **Lambda Effect:** Significant (p < 0.001)
   - λ=0.02: Lower fatigue, lower safety cost
   - λ=0.04: Higher fatigue, higher safety cost
   - Optimal: λ=0.03 (middle ground)

2. **Weight Effect:** Significant (p < 0.001)
   - w=$30: Lower total cost, higher fatigue
   - w=$80: Higher total cost, lower fatigue
   - Optimal: w=$50 (balanced)

3. **Threshold Effect:** Moderate (p < 0.01)
   - T=0.60: More restrictive, higher cost
   - T=0.80: Less restrictive, similar results
   - Optimal: T=0.70 (literature standard)

4. **Demand Effect:** Significant (p < 0.001)
   - Low: Faster solve, lower cost
   - High: Slower solve, higher cost
   - Test with Medium for analysis

5. **Interactions:**
   - Lambda × Weight: Moderate interaction
   - Other interactions: Weak

**Optimal Configuration (predicted):**
```
Lambda:       0.03
Weight:       $50
Threshold:    0.70
Demand:       Medium (for testing)
```

---

## Troubleshooting

### Q: Test mode fails with "No module named 'model'"
**A:** Make sure you're in the correct directory:
```bash
cd /Users/ibrahim/Documents/GitHub/NSS
```

### Q: Solver takes very long (> 5 minutes per run)
**A:** Check solver configuration:
```bash
python solver_config.py
```
Ensure you're using Gurobi or HiGHS (not default CBC).

### Q: Many infeasible solutions
**A:** This can happen with:
- High demand + low threshold + high n3
- Review instance configuration in parameter_tuning.py
- May need to adjust n3 or q_plus

### Q: All fatigue values are zero
**A:** This is EXPECTED for High demand scenarios!
- When demand >> capacity, model uses emergency-only
- See PHASE3_COMPLETE.md for full explanation
- Test/Medium/Low demand will show non-zero fatigue

### Q: Analysis script gives "File not found"
**A:** Run experiments first:
```bash
python experiments/parameter_tuning.py --mode test
# Then:
python experiments/analyze_tuning_results.py --input results/parameter_tuning_test.csv
```

---

## Next Steps After Phase 4

Once experiments complete and you have optimal parameters:

### 1. Document Selection
Create `docs/PARAMETER_SELECTION.md`:
```markdown
# Optimal Parameter Selection

## Selected Configuration
- Lambda (λ): 0.03
- Safety Weight: $50
- Threshold: 0.70
- PWL Segments: 8

## Statistical Justification
[Include ANOVA results, effect sizes]

## Sensitivity Analysis
[Include main effects plots]

## Cost-Fatigue Tradeoff
[Include Pareto frontier plot]
```

### 2. Update Model Defaults
In `model.py`, update `get_default_params()`:
```python
'fatigue_lambda': 0.03,  # From Phase 4
'patient_safety_weight': 50,  # From Phase 4
'max_fatigue_threshold': 0.70,  # From Phase 4
```

### 3. Phase 5: Statistical Validation
- Run 30 replications with optimal parameters
- Compare baseline (no fatigue) vs proposed
- Paired t-test for significance
- Compute effect size (Cohen's d)
- Target: Cost increase 3-5%, Fatigue reduction 40%+

### 4. Phase 6: Paper Writing
- Begin manuscript (Operations Research Perspectives)
- Introduction & Literature Review (Week 6)
- Methodology & Model Formulation (Week 6-7)
- Computational Study (Week 7)
- Results & Discussion (Week 7-8)
- Target: 25 pages, submit Week 8

---

## Summary

**Current Status:**
- Phase 3: ✅ COMPLETE (implementation validated)
- Phase 4.1: ✅ COMPLETE (experimental design ready)
- Phase 4.2: ⏳ READY TO START (your next action)

**Your Next Command:**
```bash
python experiments/parameter_tuning.py --mode test
```

**Estimated Time to Phase 4 Completion:**
- Test mode: 10 minutes
- Full experiment: 4-8 hours
- Analysis: 30 minutes
- Documentation: 2-3 hours
- **Total: 1-2 days**

**You are here:** Ready to execute experiments and find optimal parameters! 🚀

---

## Files Created This Session

1. ✅ `experiments/parameter_tuning.py` (430+ lines)
2. ✅ `experiments/analyze_tuning_results.py` (460+ lines)
3. ✅ `docs/PHASE4_QUICKSTART.md` (comprehensive guide)
4. ✅ `docs/PHASE4_READY.md` (this file)
5. ✅ Updated `IMPLEMENTATION_CHECKLIST.md` (Phase 4 section)

**Total Lines Added:** ~1,000+ lines of experiment and analysis code

---

**Ready to proceed!** Run the test mode command above to begin Phase 4 experiments.
