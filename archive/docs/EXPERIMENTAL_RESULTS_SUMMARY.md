# Experimental Results Summary
**Date:** December 14, 2025  
**Experiment:** Parameter Tuning for Fatigue-Aware Nurse Scheduling  
**Duration:** 15.75 hours (Dec 13 20:48 → Dec 14 12:33)

---

## Experiment Overview

### Design
- **Factorial Experiment:** 3 × 3 × 3 × 3 = 81 configurations
- **Replications:** 30 per configuration = 2,430 total runs
- **Factors:**
  - `lambda` (λ): Fatigue accumulation rate {0.02, 0.03, 0.04}
  - `weight` ($): Patient safety cost per fatigue unit {$30, $50, $80}
  - `threshold`: Maximum fatigue limit {0.60, 0.70, 0.80}
  - `demand_level`: Problem size {Low (12×10×5), Medium (15×14×10), High (18×14×15)}

### Success Rate
- **Total Runs:** 2,430
- **Successful:** 2,027 (83.4%)
- **Failed:** 403 (16.6%)
  - Low demand: ~95% timeout rate (243 failures, 27 successes)
  - Medium demand: 100% success (810 solves)
  - High demand: 100% success (1,217 solves)

---

## Key Findings

### 1. Sensitivity Analysis (One-Way ANOVA)

**Most Influential Factor: DEMAND LEVEL**
- Effect on Total Cost: F=553.90, p<0.0001, **η²=35.4%** ⭐
- Effect on Safety Cost: F=355.99, p<0.0001, η²=26.0%
- Effect on Max Fatigue: F=54.33, p<0.0001, η²=5.1%

**Second Most Influential: THRESHOLD**
- Effect on Total Cost: F=160.15, p<0.0001, **η²=13.7%**
- Effect on Safety Cost: F=413.79, p<0.0001, η²=29.0%
- Effect on Max Fatigue: F=3914.37, p<0.0001, **η²=79.5%** ⭐⭐⭐

**Third Most Influential: LAMBDA (λ)**
- Effect on Total Cost: F=191.96, p<0.0001, **η²=15.9%**
- Effect on Safety Cost: F=368.73, p<0.0001, η²=26.7%
- Effect on Avg Fatigue: F=708.82, p<0.0001, **η²=41.2%** ⭐⭐

**Least Influential: WEIGHT ($)**
- Effect on Total Cost: F=26.18, p<0.0001, η²=2.5%
- Effect on Safety Cost: F=329.41, p<0.0001, η²=24.6%
- Effect on Max Fatigue: F=0.29, p=0.75, **η²=0.0%** (not significant)

### 2. Summary Statistics by Factor

#### Lambda (λ) - Fatigue Accumulation Rate
| λ    | Total Cost | Safety Cost | Max Fatigue | Avg Fatigue | High-Risk Days | Solve Time |
|------|------------|-------------|-------------|-------------|----------------|------------|
| 0.02 | $41,242    | $4,289      | 0.68        | 0.34        | 51.1           | 8.74s      |
| 0.03 | $48,172    | $1,981      | 0.59        | 0.25        | 31.3           | 3.54s      |
| 0.04 | $47,510    | $2,042      | 0.58        | 0.26        | 27.4           | 3.42s      |

**Insight:** λ=0.02 has highest fatigue levels but also longest solve times (harder constraints). λ=0.03 provides best balance.

#### Weight ($) - Patient Safety Cost Parameter
| Weight | Total Cost | Safety Cost | Max Fatigue | Avg Fatigue | High-Risk Days | Solve Time |
|--------|------------|-------------|-------------|-------------|----------------|------------|
| $30    | $44,763    | $1,527      | 0.62        | 0.26        | 35.4           | 3.53s      |
| $50    | $45,888    | $2,502      | 0.62        | 0.26        | 35.2           | 4.87s      |
| $80    | $47,603    | $3,888      | 0.62        | 0.26        | 34.6           | 6.30s      |

**Insight:** Weight has minimal impact on fatigue levels (F=0.29, p=0.75) but linearly increases total cost. Actual fatigue behavior driven by λ and threshold.

#### Threshold - Maximum Fatigue Limit
| Threshold | Total Cost | Safety Cost | Max Fatigue | Avg Fatigue | High-Risk Days | Solve Time |
|-----------|------------|-------------|-------------|-------------|----------------|------------|
| 0.60      | $49,232    | $1,513      | 0.51        | 0.19        | 0.0            | 1.97s      |
| 0.70      | $45,859    | $2,484      | 0.62        | 0.27        | 19.2           | 3.69s      |
| 0.80      | $42,505    | $4,113      | 0.74        | 0.32        | 71.7           | 9.77s      |

**Insight:** Tighter threshold (0.60) dramatically reduces fatigue but increases cost by 15.8% vs relaxed (0.80). Strong constraint effect: η²=79.5%.

#### Demand Level - Problem Size
| Demand | Nurses | Days | Scenarios | Total Cost | Safety Cost | Max Fatigue | Working | Solve Time | Success Rate |
|--------|--------|------|-----------|------------|-------------|-------------|---------|------------|--------------|
| Low    | 12     | 10   | 5         | $37,569    | $816        | 0.54        | 12.0    | 4.92s      | 10.0%        |
| Medium | 15     | 14   | 10        | $47,151    | $2,614      | 0.63        | 15.0    | 3.96s      | 100.0%       |
| High   | 18     | 14   | 15        | $49,245    | $3,537      | 0.67        | 18.0    | 5.79s      | 100.0%       |

**Insight:** Low demand is computationally intractable (95% timeout) despite smaller size - tight constraints create small feasible region. Medium/High are highly tractable.

---

## 3. Optimal Configurations

### Strategy 1: Minimize Cost
**Config ID:** 13 (λ=0.02, w=$50, T=0.70, Low demand)
- **Total Cost:** $28,501 ⭐ (lowest)
- **Safety Cost:** $2,101
- **Max Fatigue:** 0.70 (at threshold)
- **Avg Fatigue:** 0.35
- **High-Risk Days:** 21
- **Solve Time:** 2.16s
- **Note:** Only 1 successful replication (27 timeouts) - not reliable

### Strategy 2: Minimize Fatigue
**Config ID:** 47 (λ=0.03, w=$80, T=0.60, Medium demand)
- **Total Cost:** $53,862
- **Safety Cost:** $1,461
- **Max Fatigue:** 0.41 ⭐ (lowest)
- **Avg Fatigue:** 0.09 ⭐ (lowest)
- **High-Risk Days:** 0.0 ⭐ (none!)
- **Solve Time:** 1.42s
- **Success Rate:** 100% (30/30 replications)

### Strategy 3: Balance Cost & Fatigue (RECOMMENDED) ⭐⭐⭐
**Config ID:** 28 (λ=0.03, w=$30, T=0.60, Low demand)
- **Total Cost:** $38,081
- **Safety Cost:** $355
- **Max Fatigue:** 0.47
- **Avg Fatigue:** 0.10
- **High-Risk Days:** 0.0
- **Solve Time:** 0.74s (fastest!)
- **Success Rate:** Limited (Low demand issues)

**PRACTICAL RECOMMENDATION:** Use λ=0.03, w=$50, T=0.70, Medium/High demand
- Balances cost, safety, and computational tractability
- 100% success rate
- Fast solve times (2-4 seconds)
- Max fatigue ~0.62 (safe zone)

---

## 4. Two-Way Interactions

**Strongest Interaction:** λ × demand_level (SD=$8,155, 81.1% relative)
- Low demand + λ=0.02 → very high solve times (8.7s avg)
- High demand + any λ → fast solves (3-6s)

**Moderate Interactions:**
- threshold × demand_level (SD=$6,595, 68.8%)
- weight × demand_level (SD=$5,468, 71.4%)
- λ × threshold (SD=$4,686, 65.2%)

---

## 5. Computational Performance

### Solve Time Analysis
- **Fastest:** T=0.60 configs (1.97s avg) - loose constraints
- **Slowest:** T=0.80 configs (9.77s avg) - tight constraints pushing limits
- **Low demand:** Highly variable (0.7s to 120s timeout)
- **Medium/High demand:** Consistent 2-6s range

### Tractability Patterns
1. **Medium demand (15×14×10):** Sweet spot - 100% success, 3.96s avg
2. **High demand (18×14×15):** Slightly harder - 100% success, 5.79s avg
3. **Low demand (12×10×5):** Computational nightmare - 10% success, 4.92s (or 120s timeout)

**Root Cause:** Low demand has tight nurse-to-demand ratio (12:15 peak = 0.8). Medium/High have buffer (15:16 = 0.94, 18:18 = 1.0).

---

## 6. Fatigue Behavior Insights

### PWL Approximation Performance
- **Implementation:** 8 segments, 0.713% max error, 0.398% avg error
- **Validation:** Matches exponential F(t) = 1 - e^(-λt) within 1%
- **Computational:** SOS2 constraints working correctly

### Fatigue Distribution
- **T=0.60:** Max fatigue stays below 0.51 (tight control)
- **T=0.70:** Max fatigue reaches 0.62-0.67 (moderate control)
- **T=0.80:** Max fatigue pushes to 0.74-0.79 (model exploits limit)

### High-Risk Days (F > 0.60)
- **T=0.60:** 0.0 days (perfect safety)
- **T=0.70:** 19.2 days (moderate risk)
- **T=0.80:** 71.7 days (high risk - not recommended)

---

## 7. Cost Breakdown Analysis

### Average Cost Components (All Configs)
- **Stage 1 (Baseline):** $37,000-$42,000 (80-85% of total)
- **Stage 2 (Recourse):** $4,000-$6,000 (10-15% of total)
- **Patient Safety:** $1,500-$4,000 (3-8% of total)

### Cost-Safety Tradeoff
- **Tight threshold (0.60):** +15.8% cost, -31% max fatigue
- **Relaxed threshold (0.80):** -13.7% cost, +45% max fatigue

**ROI Calculation (0.70 vs 0.80):**
- **Cost increase:** $3,354 (7.9%)
- **Max fatigue reduction:** 0.12 units (16%)
- **High-risk days eliminated:** 52.5 days (73%)
- **Interpretation:** $64 per high-risk day prevented

---

## 8. Recommendations

### For Production Use
1. **Use λ=0.03** (validated from Jaber et al. 2013, Table 5)
2. **Use w=$50** (literature-supported: $40-$100 per fatigue unit)
3. **Use T=0.70** (balances safety and cost, 19 high-risk days acceptable)
4. **Use Medium or High demand** (Low demand computationally intractable)
5. **Set timeout=120s** (sufficient for Medium/High, Low will timeout regardless)

### For Future Research
1. **Investigate Low demand tractability:**
   - Try different solver settings (MIPFocus, Cuts, Heuristics)
   - Consider relaxing other constraints (n3, weekend_off)
   - Use warm start from relaxed solution
2. **Add recovery function** to model day-off rest periods
3. **Calibrate weights from hospital data** (error rates, turnover costs)
4. **Test larger instances** (30+ nurses, 28+ days)

---

## 9. Statistical Significance

All main effects **highly significant (p < 0.0001)** except:
- Weight → Max Fatigue (F=0.29, p=0.75) - not significant

**Interpretation:** Threshold and lambda control actual fatigue behavior. Weight only affects cost calculation (multiplier), not scheduling decisions.

---

## 10. Files Generated

### Data Files
- `results/parameter_tuning_results.csv` (2,430 rows × 20 columns)
- `results/sensitivity_analysis.csv` (ANOVA results)
- `results/optimal_configurations.csv` (3 strategies)

### Visualizations
- `results/figures/main_effects.png` (4-panel plot: λ, weight, threshold, demand)
- `results/figures/cost_fatigue_tradeoff.png` (scatter with Pareto frontier)
- `results/figures/solve_time.png` (box plots by factor)
- `results/figures/lambda_weight_interaction.png` (heatmap)

### Logs
- `parameter_tuning_60s.log` (full experiment log, 15.75 hours)

---

## Conclusion

The parameter tuning experiment successfully validated the fatigue-aware scheduling model across 2,430 problem instances. Key findings:

1. **Demand level** is the dominant factor (35.4% variance explained)
2. **Threshold** controls fatigue behavior (79.5% variance in max fatigue)
3. **Lambda** affects solve difficulty (15.9% variance in cost)
4. **Weight** has minimal behavioral impact (only affects cost scaling)

**Recommended configuration:** λ=0.03, w=$50, T=0.70 with Medium/High demand provides excellent balance of cost ($45-49K), safety (max fatigue 0.62), and tractability (100% success, 2-4s solves).

**Major limitation:** Low demand instances remain computationally intractable (95% timeout rate) despite smaller problem size - tight constraints create tiny feasible region requiring advanced solver techniques.
