# 🔬 NSS Model: Validation & Reproducibility Framework
## Complete Guide to Publication-Quality Experiments

---

## Table of Contents

1. [Quick Start (5 minutes)](#quick-start)
2. [Validation Checklist](#validation-checklist)
3. [Reproducible Experiment Pipeline](#reproducible-experiment-pipeline)
4. [Parameter Sanity Guards](#parameter-sanity-guards)
5. [Data Limitations & Publication](#data-limitations--publication)
6. [Common Issues & Solutions](#common-issues--solutions)
7. [File Registry](#file-registry)

---

## Quick Start

### 1️⃣ Get Started in 5 Minutes

```bash
# Example 1: Validate your data before solving
python examples_quickstart.py --mode validate

# Example 2: Run a single complete experiment
python examples_quickstart.py --mode single

# Example 3: Run multiple configurations (sensitivity analysis)
python examples_quickstart.py --mode sweep
```

### 2️⃣ Understand Your Data

All datasets registered in [experiment_pipeline.py](experiments/experiment_pipeline.py):

| Dataset | Size | Realism | Best For |
|---------|------|---------|----------|
| `sample` | 10 nurses, 14 days | ⭐⭐☆ Synthetic | Quick testing |
| `test_small` | 15 nurses, 14 days | ⭐⭐☆ Synthetic | Unit testing |
| `test_medium` | 20 nurses, 14 days | ⭐⭐⭐⭐ Real occupancy | Main results |
| `medium` | 25 nurses, 21 days | ⭐⭐⭐⭐ Real occupancy | 3-week planning |
| `nss_benchmark` | 30 nurses, 30 days | ⭐⭐⭐⭐⭐ Real data | Paper comparison |

**Key note**: See [DATA_LIMITATIONS_GUIDE.md](docs/DATA_LIMITATIONS_GUIDE.md) for detailed source documentation.

### 3️⃣ Choose a Parameter Preset

Pre-configured parameter sets in [experiment_pipeline.py](experiments/experiment_pipeline.py):

```python
# Example: Run with baseline cost minimization
runner = ExperimentRunner()
result = runner.run_experiment(
    dataset_key='test_medium',
    preset_key='baseline',          # Pure cost minimization
    experiment_id='my_experiment_1'
)

# Or: Risk-averse (CVaR) configuration
result = runner.run_experiment(
    dataset_key='test_medium',
    preset_key='conservative',      # Controls worst-case shortage
    experiment_id='my_experiment_2'
)

# Or: Include patient safety via fatigue
result = runner.run_experiment(
    dataset_key='test_medium',
    preset_key='fatigue_aware',     # Jaber et al. (2013) LFFR model
    experiment_id='my_experiment_3'
)
```

---

## Validation Checklist

### Part 1: Pre-Run Validation (4 checks)

**What it does**: Audits parameters and data BEFORE solving to catch impossible settings.

**How to use**:
```python
from validation_framework import run_complete_validation

validation = run_complete_validation(
    nurses_list, scenarios_df, model_params,
    auto_fix=True  # Automatically fix obvious problems
)

if validation['ready_to_run']:
    # Safe to solve
    prob, status = build_and_solve_model(...)
else:
    # Fix issues first
    for error in validation['pre_validation']['errors']:
        print(error)
```

**4 Core Checks**:

| # | Check | Catches | Fix |
|---|-------|---------|-----|
| 1 | Data structure | Missing columns, empty data | ❌ Manual |
| 2 | Parameter ranges | c1<c2<q_plus, n1≥n2, etc. | ✅ Auto |
| 3 | Capacity feasibility | Peak demand > capacity | ❌ Manual |
| 4 | Problem size | Scalability estimate | ⚠️  Warning |

**✅ What you get**:
- Clear error messages with fixes
- Problem size estimation (variables, constraints, solve time)
- Sanity checks on cost relationships

**Example output**:
```
PRE-RUN VALIDATION REPORT
════════════════════════════════════════════════════════
📊 Checks: 18 passed, 2 failed
Status: ⚠️  PROCEED WITH CAUTION

❌ ERRORS:
   ❌ Constraint violation: n1(5) < n2(8) impossible

⚠️  WARNINGS:
   ⚠️  High utilization (92.5%) may cause solver difficulty

📈 Problem Size:
   Variables:    2,847
   Constraints: 5,230
   Complexity:   Medium
   Est. Time:    20-60 seconds
════════════════════════════════════════════════════════
```

---

## Reproducible Experiment Pipeline

### Part 1: One-Line Experiment Runner

**Simple interface for full workflow**:
```bash
# Run experiment with validation + archiving
python experiments/experiment_pipeline.py \
    --dataset test_medium \
    --preset conservative \
    --id my_first_experiment \
    --solver AUTO
```

Automatically:
- ✅ Validates data
- ✅ Solves model
- ✅ Archives results (metadata, parameters, schedule)
- ✅ Generates reproducibility info

**Results stored in**: `experiments/results/my_first_experiment/`
```
📁 my_first_experiment/
   ├─ metadata.json          ← Experiment summary
   ├─ parameters.json        ← Exact parameters used
   ├─ schedule.csv           ← Nurse assignment schedule
   └─ results.json           ← Cost breakdown, statistics
```

### Part 2: Batch Experiments (Sensitivity Analysis)

**Run multiple configurations systematically**:
```python
from experiments.experiment_pipeline import ExperimentRunner, DATASET_REGISTRY

runner = ExperimentRunner()

# Sensitivity: vary cost parameters
for q_plus in [150, 200, 250]:
    result = runner.run_experiment(
        dataset_key='test_medium',
        preset_key='baseline',
        experiment_id=f'sensitivity_qplus_{q_plus}',
        overrides={'q_plus': q_plus}
    )

# Generate summary
print(runner.generate_summary_report())
```

**Output**: Comparison table with all results indexed by experiment ID

---

## Parameter Sanity Guards

### The Problem

Parameter mistakes can silently cause:
- ❌ Infeasible problems (no solver message)
- ❌ Unrealistic solutions (e.g., all emergency staffing)
- ❌ Absurd costs (negative, contradicting constraints)

### The Solution

**Automatic parameter sanitization**:
```python
from validation_framework import sanitize_parameters

# Bad parameters
bad_params = {
    'c1': 200.0,
    'c2': 100.0,    # ← Backwards! Less than c1
    'q_plus': 50.0, # ← Backwards! Less than c2
    'n1': 8,
    'n2': 10,       # ← Impossible! n2 > n1
}

# Fix automatically
fixed_params, changes = sanitize_parameters(
    bad_params, nurses_list, scenarios_df
)

for change in changes:
    print(change)
    # Output:
    # Fixed cost hierarchy: Set c2 = 300.0 (was 100.0)
    # Fixed cost hierarchy: Set q_plus = 450.0 (was 50.0)
    # Fixed n2: Set to 2 (was 10, exceeds n1)
```

**What gets auto-fixed**:
- ✅ Cost hierarchy violations (c1 < c2 < q_plus)
- ✅ Impossible constraints (n2 > n1, n3 > n1)
- ✅ CVaR parameter ranges (0.5 < σ < 0.99)
- ✅ Solver settings (time limit, MIP gap)

**What stays as errors**:
- ❌ Demand exceeds capacity (need more nurses or allow emergency)
- ❌ Missing required data (need to load correct files)
- ❌ Invalid nurse IDs (data quality issue)

---

## Data Limitations & Publication

### Key Resource

**See**: [docs/DATA_LIMITATIONS_GUIDE.md](docs/DATA_LIMITATIONS_GUIDE.md) for:
- Sources of each dataset
- Realism assessment
- Appropriate uses (and misuses)
- Language for paper limitations sections
- Framing real vs. synthetic data

### Quick Reference

#### ✅ STRONG Claims (supported)
- "We tested on synthetic benchmark derived from He et al. (2019)"
- "Validation included real hospital occupancy patterns"
- "Case study applies model to nursing home data"

#### ❌ WEAK Claims (not supported)
- ~~"We solved real hospital scheduling"~~ [if using proxy]
- ~~"Results directly improve patient outcomes"~~ [not validated]
- ~~"This is ready for immediate deployment"~~ [needs clinical validation]

### Recommended Data Selection

| Context | Recommended | Why |
|---------|-------------|-----|
| Paper main results | Benchmark + occupancy proxy | Controlled + realistic |
| Case study appendix | Real CMS PBJ data | Demonstrates applicability |
| Sensitivity analysis | Same dataset throughout | Isolate parameter effects |
| Computational benchmarking | Multiple sizes (small→large) | Show scalability |

---

## Common Issues & Solutions

### 🔴 Problem: Validation Says "Infeasible"

**Symptoms**: Validation reports "peak demand > capacity"

**Diagnosis**:
```python
# Check what validation found
if not validation['is_valid']:
    for error in validation['pre_validation']['errors']:
        if 'Peak demand' in error:
            print(error)
            # Output: "Peak demand (87 shifts) exceeds capacity (80)"
```

**Solutions** (in order of preference):

1. **Add more nurses** (best)
   ```python
   params['n1'] = 16  # Increase max shifts per nurse
   ```

2. **Increase emergency staff budget**
   ```python
   params['q_plus'] = 500  # Make emergency more affordable
   ```

3. **Reduce minimum commitment**
   ```python
   params['n3'] = 0  # Allow flexible scheduling
   ```

---

### 🔴 Problem: Model Runs but Results Look Wrong

**Symptoms**: All-emergency shifts, or nobody gets scheduled

**Diagnosis**: Check if parameters match planning horizon

```python
# If you have 14-day data, these are WRONG:
params['n1'] = 40    # ← Max shifts allowed
params['n3'] = 35    # ← Min shifts required (leaves only 5 free!)

# CORRECT:
num_days = 14
params['n1'] = int(0.8 * num_days)  # ~11 shifts in 14 days
params['n3'] = int(0.5 * n1)        # ~5 as minimum
```

**Use the auto-deriver**:
```python
runner = ExperimentRunner()
# This automatically calculates n1, n2, n3 from data
final_params = runner.prepare_parameters(
    'baseline', nurses_list, scenarios_df
)
```

---

### 🔴 Problem: "Parameter mismatch" Errors

**This was your original issue!**

**Root cause**: Using parameters designed for 30-day horizon with 7-day data

**Prevention**:
```python
# WRONG: Hardcoded for specific test case
params = {
    'n1': 20,    # Works for 30 days
    'n3': 12,    # Assumes 30-day horizon
}

# CORRECT: Data-aware defaults
num_days = len(scenarios_df['day'].unique())
params = {
    'n1': max(8, int(0.8 * num_days)),    # Scales with data
    'n2': max(2, int(0.3 * params['n1'])),
    'n3': max(0, int(0.5 * params['n1'])),
}
```

**Use presets** to avoid this:
```python
# Presets handle this automatically
runner.run_experiment(
    dataset_key='test_medium',
    preset_key='baseline',     # ← Automatically scales
    experiment_id='safe_exp'
)
```

---

### 🔴 Problem: Solver Timeout

**Symptoms**: "Status = Not Solved" after 10 minutes

**Quick fixes**:

1. **Use fewer scenarios**
   ```python
   scenarios_df = scenarios_df[scenarios_df['scenario'] <= 5]
   ```

2. **Use smaller dataset**
   ```python
   runner.load_data('test_medium')  # Not 'nss_benchmark'
   ```

3. **Increase time limit**
   ```python
   params['time_limit'] = 600  # 10 minutes instead of 5
   ```

4. **Use MIP gap**
   ```python
   params['mip_gap'] = 0.01  # Accept 1% suboptimal for speed
   ```

---

## File Registry

### 📋 Core Framework Files

| File | Purpose | When to Use |
|------|---------|------------|
| `validation_framework.py` | Pre/post-run validation | Always before solving |
| `experiments/experiment_pipeline.py` | Reproducible execution | For publication experiments |
| `examples_quickstart.py` | Working code examples | Learning the framework |
| `docs/DATA_LIMITATIONS_GUIDE.md` | Data documentation | Writing papers |

### 📂 Directory Structure

```
NSS/
├── model_2.py                          ← Core optimization model
├── validation_framework.py              ← NEW: Validation tools
├── examples_quickstart.py               ← NEW: Working examples
│
├── experiments/
│   ├── experiment_pipeline.py           ← NEW: Experiment runner
│   ├── results/                         ← Auto-generated outputs
│   │   └── [experiment_id]/
│   │       ├── metadata.json
│   │       ├── parameters.json
│   │       ├── schedule.csv
│   │       └── results.json
│   │
│   └── (existing: parameter_tuning.py, etc.)
│
├── data/                                ← Datasets
│   ├── sample_nurses.csv
│   ├── test_medium_nurses.csv
│   ├── nss_benchmark_nurses.csv
│   └── ...
│
└── docs/
    ├── DATA_LIMITATIONS_GUIDE.md        ← NEW: Publication guide
    ├── (existing: MODEL_WALKTHROUGH.md, etc.)
```

---

## Publication-Quality Workflow

### ✅ Pre-Submission Checklist

```
□ Data validation (all 4 checks pass)
□ Experiment reproducibility (results archived with metadata)
□ Parameter documentation (exact values in paper)
□ Solver & hardware spec (in Methods section)
□ Limitations statement (honest, specific)
□ Sensitivity analysis (show robustness)
□ Appendix: Full solver output logs
□ Appendix: Reproducibility statement (see below)
```

### Example Reproducibility Statement

Include in supplementary materials:

```
REPRODUCIBILITY

Code and data:
- Source code: https://github.com/[user]/NSS
- Commit hash: [abc123...]
- Datasets: Included in repository (data/) or available at [URLs]

Computing environment:
- Python 3.10+, PuLP 2.7.0, HiGHS 1.5.0
- Hardware: CPU [type], [GB] RAM
- OS: [Linux/macOS/Windows]

Reproducing main results:
python experiments/experiment_pipeline.py \
    --dataset nss_benchmark \
    --preset paper_replication \
    --id baseline_replication

Results automatically saved to: experiments/results/baseline_replication/
```

---

## Next Steps

1. **Start simple**: Run `python examples_quickstart.py --mode single`
2. **Read detailed guides**: [DATA_LIMITATIONS_GUIDE.md](docs/DATA_LIMITATIONS_GUIDE.md)
3. **Run your first experiment**: Use `experiment_pipeline.py`
4. **Validate everything**: Use `validation_framework.py` before every solve
5. **Plan paper experiments**: Follow "Publication-Quality Workflow" above

---

## Support & Questions

For issues:
1. Check "[Common Issues & Solutions](#common-issues--solutions)" above
2. Review [docs/DATA_LIMITATIONS_GUIDE.md](docs/DATA_LIMITATIONS_GUIDE.md)
3. Run examples: `python examples_quickstart.py --mode troubleshoot`
4. Check detailed docstrings in code files

---

**Last Updated**: March 2026
**Framework Version**: 1.0
**Model**: He et al. (2019) - Stochastic Demand Model with CVaR
