# FROST-NS: Fatigue-aware Risk Optimization for Stochastic Task allocation in Nurse Scheduling

**Nurse Scheduling System with CVaR Risk Control and Fatigue Modeling**

A research-grade implementation of He et al. (2019) with significant enhancements: configurable overtime logic, piecewise-linear fatigue modeling, and comprehensive parameter tuning experiments.

<div align="center">

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45-FF4B4B.svg)](https://streamlit.io)
[![PuLP](https://img.shields.io/badge/PuLP-2.9.0-green.svg)](https://coin-or.github.io/pulp/)
[![Gurobi](https://img.shields.io/badge/Gurobi-11.0-red.svg)](https://www.gurobi.com/)
[![HiGHS](https://img.shields.io/badge/HiGHS-1.7-orange.svg)](https://highs.dev/)

</div>

## Key Features

### Mathematical Foundation
- **Two-Stage Stochastic Programming** - Optimizes under demand uncertainty with recourse decisions
- **CVaR Risk Management** - Controls worst-case shortage risk via Conditional Value-at-Risk
- **Configurable Overtime Logic** - Toggle between paper's formulation and NSS-enhanced strict rules
- **Piecewise-Linear Fatigue Modeling** - SOS2-based exponential fatigue approximation (Jaber et al., 2013)
- **18+ Constraints** - Complete implementation with optional advanced constraints

### Research Contributions
- **Overtime Paradox Analysis** - Identified and resolved mathematical gap in paper's overtime formulation
- **Dual Model Variants** - Paper-faithful mode vs. NSS-enhanced mode with strict overtime enforcement
- **Parameter Tuning Study** - 2,430-run factorial experiment on fatigue modeling sensitivity
- **Solver Configuration Framework** - Auto-detection and optimization for Gurobi/HiGHS/CBC

### User Experience
- **Web Interface** - Professional Streamlit dashboard (no coding  required)
- **Real-Time Optimization** - 5-60 second solve times with Gurobi/HiGHS
- **Interactive Visualizations** - Schedule heatmaps, cost breakdowns, scenario analysis
- **Comprehensive Validation** - Input validation, feasibility checking, result verification
- **Export Options** - CSV, Excel, JSON formats

## Recent Updates (December 2025)

### Major Enhancements
- **Configurable Overtime Logic** - Added UI toggle to switch between paper mode (overtime paradox) and NSS mode (strict enforcement)
- **Fatigue Modeling Experiments** - Completed 2,430-run parameter tuning study testing λ, safety weight, and fatigue thresholds
- **Experimental Results** - Generated sensitivity analysis showing threshold=0.6 causes consistent solver timeouts
- **Enhanced Validation** - Added capacity feasibility checks with detailed warnings
- **Documentation Expansion** - Created Mathematical_Model.tex with line-by-line code correspondence

### Bug Fixes & Refinements
- **Import Path Fixed** - Resolved `scripts.solver_config` → `solver_config` error
- **Baseline Demand Redefined** - Changed from arbitrary scenario to expected demand (statistical mean)
- **Repository Cleanup** - Organized into docs/, scripts/, tests/, experiments/, logs/, archive/ structure

## Quick Start

### 1. Installation
```bash
# Clone repository
git clone https://github.com/Ibrahim-Abdelsalam/NSS.git
cd NSS

# Install dependencies
pip install -r requirements.txt

# Install a solver (choose one)
pip install highspy  # Free solver (recommended for testing)
# OR get Gurobi academic license: https://www.gurobi.com/academia/
```

### 2. Run Application
```bash
streamlit run app.py
```

Opens at **http://localhost:8501**

### 3. Configure Overtime Behavior
In the sidebar under "Work Rules > Basic Shift Constraints":
- **Unchecked** (Default): Paper Mode - demonstrates "Overtime Paradox" (0 overtime usage)
- **Checked**: NSS Mode - enforces strict overtime rules with weekly caps

**Full Guide:** See [OVERTIME_TEST_GUIDE.md](OVERTIME_TEST_GUIDE.md) for detailed testing instructions.

## Project Structure

```
NSS/
├── Core Application
│   ├── app.py                      # Streamlit web interface (2,364 lines)
│   ├── model.py                    # Optimization model (2,376 lines, 11 functions)
│   └── solver_config.py            # Solver detection & configuration
│
├── Experiments & Results
│   ├── experiments/                # Parameter tuning experiments
│   │   ├── parameter_tuning.py         # Factorial design (2,430 runs)
│   │   ├── statistical_validation.py   # ANOVA and sensitivity analysis
│   │   ├── analyze_tuning_results.py   # Results visualization
│   │   ├── visualize_fatigue.py        # Fatigue model visualization
│   │   └── retry_failed.py             # Retry logic for timeouts
│   │
│   ├── results/                    # Experiment outputs
│   │   ├── parameter_tuning_results.csv    # 2,430 experimental runs
│   │   ├── optimal_configurations.csv      # Top performers
│   │   ├── sensitivity_analysis.csv        # Parameter sensitivity
│   │   └── figures/                        # Visualization outputs
│   │
│   └── logs/                       # Execution logs
│       └── parameter_tuning_60s.log        # 2.2MB detailed log
│
├── Data & Tests
│   ├── data/                       # Sample datasets and test cases
│   │   ├── sample_nurses.csv           # Basic test (10 nurses)
│   │   ├── sample_scenarios.csv        # Basic scenarios
│   │   ├── overtime_test_*.csv (2)     # Overtime validation
│   │   ├── 40_nurses_30days_*.csv (2)  # Large-scale test
│   │   └── cvar_*.csv (2)              # CVaR risk test
│   │
│   ├── scripts/                    # Standalone analysis scripts
│   │   ├── VALIDATE_OVERTIME.py        # Overtime test suite
│   │   ├── COMPLETE_TEST_INSTANCE.py   # Full example
│   │   └── model_2.py                  # Paper-pure variant (archived)
│   │
│   └── tests/                      # Unit tests
│       └── test_overtime_revert.py     # Overtime paradox verification
│
├── Documentation
│   ├── Mathematical_Model.tex      # Complete mathematical formulation (47KB)
│   ├── docs/
│   │   ├── CVaR_Explained.tex          # CVaR risk tutorial
│   │   ├── DETAILED_COMPARISON.md      # Line-by-line vs paper (33KB)
│   │   ├── PAPER_ANALYSIS.md           # Overtime paradox analysis
│   │   ├── USER_GUIDE.md               # Complete user guide
│   │   ├── TECHNICAL_GUIDE.md          # Developer documentation
│   │   ├── PARAMETER_GUIDE.md          # All parameters explained
│   │   ├── CONSTRAINTS_GUIDE.md        # Constraint reference
│   │   └── He et al. (2019).pdf        # Original research paper
│   │
│   └── archive/                    # Historical documentation
│       ├── docs/                       # Superseded reports
│       └── results/                    # Previous experiment data
│
├── Project Files
│   ├── README.md                   # This file
│   ├── requirements.txt            # Python dependencies
│   └── LICENSE                     # MIT License
│
└── Support Files
    ├── notebooks/                  # Jupyter analysis notebooks
    ├── Output/                     # User-generated output directory
    └── loading.gif                 # UI loading animation
```

## Solver Configuration

The model supports multiple optimization solvers with automatic detection:

| Solver | License | Speed | Memory | Recommended For |
|--------|---------|-------|--------|-----------------|
| **Gurobi** | Academic (free) / Commercial | Fastest (0.06-60s) | Low | **Production use** |
| **HiGHS** | Open-source (free) | Fast (5-300s) | Low | **Testing & development** |
| **CBC** | Open-source (free) | Moderate (30-600s) | Medium | **Fallback option** |

### Installation

**HiGHS (Recommended for free use):**
```bash
pip install highspy
```

**Gurobi (Fastest, free for academics):**
1. Get academic license: https://www.gurobi.com/academia/
2. Install: `pip install gurobipy`
3. Activate license: `grbgetkey YOUR-LICENSE-KEY`

The system auto-detects and uses the best available solver.

## Mathematical Model

### Two-Stage Stochastic Programming

**Stage 1 (Here-and-Now Decisions):**
- Create baseline nurse schedule **before** knowing actual demand
- Assign regular shifts (`sr_ijk`) and overtime shifts (`so_ijk`)
- Minimize: `c1·sr + c2·so + fatigue_penalty + soft_penalties`

**Stage 2 (Recourse Decisions):**
- Adjust schedule **after** demand is realized in each scenario
- Add emergency staff (`α`) or cancel shifts (`β`)
- Minimize expected recourse cost: `E[q+·α + q-·β]`

**Key Constraint (Demand Fulfillment):**
```
Planned Staff + Emergency - Cancellations ≥ Demand
Σᵢ(sr + so) + α - β ≥ R^ω    ∀ scenario ω
```

### CVaR Risk Management (SDM-CVaR Model)

Controls worst-case shortage risk:
```
CVaR_σ ≤ μ
```
- `σ` = Confidence level (e.g., 0.95 = 95%)
- `μ` = Maximum acceptable shortage in worst 5% of scenarios

**Example:** "In the worst 5% of scenarios, shortage ≤ 5 shifts"

### Fatigue Modeling (Optional)

Piecewise-linear approximation of exponential fatigue function:
```
F(t) = 1 - e^(-λt)
```
- Implemented using SOS2 constraints for exact non-linear modeling
- 8-segment PWL: 0.398% average error, 0.713% max error
- Based on Jaber et al. (2013) learning-forgetting framework

### Complete Formulation

**Decision Variables:**
- `sr_ijk` ∈ {0,1}: Regular shift for nurse i, day j, shift k
- `so_ijk` ∈ {0,1}: Overtime shift
- `α_jk^ω` ≥ 0: Emergency staff added (scenario ω)
- `β_jk^ω` ≥ 0: Shifts cancelled (scenario ω)
- `SR_i, SO_i` ∈ {0,1}: Indicator variables
- `F_ij` ∈ [0,1]: Fatigue level for nurse i on day j (continuous)

**Constraints (22 total):**
1. One shift per day: `Σₖ(sr + so) ≤ 1`
2-5. Shift type quotas (optional)
6. Max total shifts: `Σⱼₖ(sr + so) ≤ n1`
7. Max night shifts: `Σⱼ(sr_N + so_N) ≤ n2`
7.5. **Weekly overtime cap** (NSS mode only): `Σⱼₖ so ≤ 1` per week
8. **Regular shift quota** (configurable):
   - Paper mode: `Σⱼₖ sr ≥ n3·SR` (minimum)
   - NSS mode: `Σⱼₖ sr == n3·SR` (strict)
9. Min weekends off (optional)
10-13. Night rest requirements (optional)
14-15. Soft penalties (stand-alone shifts, unwanted patterns)
F1-F6. Fatigue modeling constraints (optional, SOS2-based)
16. **Demand fulfillment** (key): `Σᵢ(sr + so) + α - β ≥ R^ω`
17-18. Recourse bounds (optional)
19-22. CVaR constraints (SDM-CVaR only)

**See:** [Mathematical_Model.tex](Mathematical_Model.tex) for complete LaTeX formulation with code line references.

## Model Parameters

### Cost Parameters
| Parameter | Symbol | Description | Default | Example |
|-----------|--------|-------------|---------|---------|
| `c1` | c₁ | Regular shift cost | £100 | Base wage |
| `c2` | c₂ | Overtime shift cost | £150 | 1.5× regular |
| `q_plus` | q⁺ | Emergency staff cost | £200 | 2× regular |
| `q_minus` | q⁻ | Shift cancellation cost | £0 | Usually 0 |
| `c3` | c₃ | Stand-alone shift penalty | £10 | Soft constraint |
| `c4` | c₄ | Unwanted pattern penalty | £15 | Soft constraint |

### Work Rules (Hard Constraints)
| Parameter | Symbol | Description | Default | Range |
|-----------|--------|-------------|---------|-------|
| `n1` | n₁ | Max total shifts per nurse | 15 | 10-24 |
| `n2` | n₂ | Max night shifts per nurse | 5 | 3-8 |
| `n3` | n₃ | Min regular shifts (if working) | 10 | 5-20 |
| `n4` | n₄ | Min complete weekends off | 0 | 0-4 |

### Fatigue Parameters (Optional)
| Parameter | Symbol | Description | Default | Range |
|-----------|--------|-------------|---------|-------|
| `fatigue_lambda` | λ | Fatigue accumulation rate | 0.03 | 0.01-0.10 |
| `patient_safety_weight` | $ | Cost per unit fatigue | $50 | $0-$200 |
| `max_fatigue_threshold` | T | Maximum allowed fatigue | 0.70 | 0.50-0.90 |
| `shift_duration` | h | Hours per shift | 12 | 8-16 |

**Caution:** Threshold below 0.65 may cause solver timeouts (see experiment results).

### Overtime Configuration (New!)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `allow_overtime_paradox` | If True: Paper mode (min regular, no OT caps). If False: NSS mode (strict regular quota + weekly OT cap) | True (Paper) |

### CVaR Parameters (SDM-CVaR Model)
| Parameter | Symbol | Description | Default | Range |
|-----------|--------|-------------|---------|-------|
| `sigma` | σ | Confidence level | 0.95 | 0.90-0.99 |
| `mu` | μ | Max acceptable shortage | 5.0 | Varies |

**Complete Guide:** See [PARAMETER_GUIDE.md](docs/PARAMETER_GUIDE.md) for detailed parameter explanations.

## Performance Benchmarks

**Test Configuration:**
- MacBook Pro M1 (8-core)
- 16GB RAM
- Gurobi 11.0 solver

| Problem Size | Variables | Constraints | Solve Time | Status |
|-------------|-----------|-------------|------------|--------|
| Small (10 nurses, 7 days, 3 scenarios) | ~2,400 | ~2,200 | 0.06s | Optimal |
| Medium (20 nurses, 14 days, 5 scenarios) | ~9,600 | ~8,800 | 2.3s | Optimal |
| Large (40 nurses, 30 days, 10 scenarios) | ~91,000 | ~83,000 | 58s | Optimal |
| Very Large (50 nurses, 30 days, 20 scenarios) | ~180,000 | ~165,000 | 5m 23s | Near-optimal (0.5% gap) |

**HiGHS Solver:** ~10× slower than Gurobi but still practical for medium problems.

## Experimental Research

### Parameter Tuning Study (Dec 2025)

**Design:** 3×3×3×3 factorial experiment (81 configurations × 30 replications = 2,430 runs)

**Factors Tested:**
- Fatigue λ: {0.02, 0.03, 0.04}
- Safety weight: {$30, $50, $80}
- Max threshold: {0.60, 0.70, 0.80}
- Demand level: {Low, Medium, High}

**Key Findings:**
1. **Threshold Sensitivity**: T=0.60 causes 100% solver timeouts (60s limit)
2. **Optimal Configuration**: λ=0.03, weight=$50, T=0.70 for Medium demand
3. **Solver Performance**: Higher thresholds dramatically improve convergence
4. **Cost Trade-offs**: Higher safety weights reduce fatigue but increase total cost 15-25%

**Results:** See `results/parameter_tuning_results.csv` (538KB, 2,430 rows)

### Analysis Scripts

```bash
# Run parameter tuning (test mode: 9 configurations)
python experiments/parameter_tuning.py --mode test

# Full experiment (2,430 runs, ~40 hours)
python experiments/parameter_tuning.py --mode full --yes

# Analyze results
python experiments/analyze_tuning_results.py

# Statistical validation (ANOVA)
python experiments/statistical_validation.py

# Visualize fatigue curves
python experiments/visualize_fatigue.py
```

## Testing & Validation

### Test Suite
```bash
# Run comprehensive validation tests
python scripts/VALIDATE_OVERTIME.py
# Expected: 4/4 tests PASSED

# Run complete test instance
python scripts/COMPLETE_TEST_INSTANCE.py
# Expected: 40 regular + 2 overtime = £5,700

# Test with CSV files
python scripts/run_test_with_csv.py
```

### Validation Results
- **All core constraints validated** (Constraints 1-18)  
- **Overtime functionality verified** (Paper mode vs NSS mode)  
- **CVaR risk management tested** (SDM-CVaR model)  
- **Fatigue modeling validated** (PWL approximation accuracy: 0.398% avg error)
- **Parameter tuning complete** (2,430 experimental runs)
- **Paper comparison complete** (see DETAILED_COMPARISON.md)

## Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'scripts.solver_config'**
```bash
# Fixed in latest version - import path corrected
# If you see this, update model.py line 6:
# from solver_config import ...  # Correct
```

**Overtime shifts not being generated**
- Enable "Enable NSS Strict Overtime Rules" checkbox in UI (sidebar under "Work Rules")
- This forces strict regular quota (Constraint 8 as equality)
- Without this, model exhibits "Overtime Paradox" (0 overtime due to cost preference)
- See [PAPER_ANALYSIS.md](docs/PAPER_ANALYSIS.md) for mathematical explanation

**Solver not found / No solver available**
```bash
# Install HiGHS (free):
pip install highspy

# Or install Gurobi (academic license):
# 1. Get license from gurobi.com/academia
# 2. pip install gurobipy
# 3. Run: grbgetkey <your-license-key>
```

**Solver timeout with fatigue modeling**
- Increase `max_fatigue_threshold` above 0.65 (lower thresholds are very hard to satisfy)
- Reduce problem size (fewer nurses, days, or scenarios)
- Use Gurobi instead of HiGHS (10× faster)
- Set longer time limit in parameters

**Infeasible solution / No solution found**
- Check capacity warnings in console output
- Increase available nurses in `sample_nurses.csv`
- Relax hard constraints (decrease `n1`, `n2`, increase `n3`)
- Disable fatigue modeling if threshold is too restrictive

**Very slow solving (>10 minutes)**
- Reduce problem size (fewer scenarios, shorter horizon)
- Use Gurobi instead of HiGHS (10× faster)
- Disable soft constraints (c3=0, c4=0)
- Disable fatigue modeling (`patient_safety_enabled=False`)
- See [PERFORMANCE_ANALYSIS.md](docs/PERFORMANCE_ANALYSIS.md)

## Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [Mathematical_Model.tex](Mathematical_Model.tex) | Complete mathematical formulation with code line references | Complete (47KB) |
| [CVaR_Explained.tex](docs/CVaR_Explained.tex) | CVaR risk management tutorial with examples | Complete |
| [DETAILED_COMPARISON.md](docs/DETAILED_COMPARISON.md) | Line-by-line comparison with He et al. (2019) paper | Complete (33KB) |
| [PAPER_ANALYSIS.md](docs/PAPER_ANALYSIS.md) | Overtime paradox analysis and resolution | Complete |
| [PARAMETER_GUIDE.md](docs/PARAMETER_GUIDE.md) | All parameters explained with examples | Available |
| [CONSTRAINTS_GUIDE.md](docs/CONSTRAINTS_GUIDE.md) | Complete constraint reference (22 constraints) | Available |
| [MODEL_STRUCTURE.md](docs/MODEL_STRUCTURE.md) | Code architecture and design patterns | Available |
| [PERFORMANCE_ANALYSIS.md](docs/PERFORMANCE_ANALYSIS.md) | Solver benchmarks and optimization tips | Available |

## Technical Stack

**Core Dependencies:**
- `gurobipy>=11.0.3` or `highspy>=1.7.0` - MIP solver
- `pulp>=2.9.0` - Mathematical modeling language
- `streamlit>=1.40.2` - Web interface
- `pandas>=2.2.3` - Data handling
- `numpy>=2.2.1` - Numerical operations
- `matplotlib>=3.9.0` - Visualization (for experiments)
- `seaborn>=0.13.0` - Statistical graphics

**Development:**
- Python 3.11+ (tested on 3.11.5 and 3.13)
- macOS/Linux/Windows compatible
- No C++ compilation required (pure Python)

**Solver Comparison:**
| Solver | Speed | License | Memory | Recommended For |
|--------|-------|---------|--------|-----------------|
| **Gurobi** | Fastest | Academic/Commercial | Low | Production use |
| **HiGHS** | Fast | Open-source | Low | Research/testing |
| **CBC** | Moderate | Open-source | Medium | Fallback only |

## Academic Foundation

**Based on:** He, F., Qu, R., & Investigate, S. (2019). A two-stage stochastic mixed-integer program modelling and hybrid solution approach to re-rostering problems under uncertainty. *European Journal of Operational Research*.

**Additional References:**
- Jaber, M. Y., Givi, Z. S., & Neumann, W. P. (2013). Incorporating human fatigue and recovery into the learning–forgetting process. *Applied Mathematical Modelling*, 37(12-13), 7287-7299.
- Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. *Journal of Risk*, 2, 21-42.

**Implementation:** This codebase is a complete implementation of the SDM-CVaR model with significant enhancements:

**Key Extensions & Contributions:**
1. **Overtime Paradox Resolution** - Identified and resolved gap in paper's formulation
2. **Configurable Overtime** - Dual mode system (Paper vs NSS)
3. **Fatigue Modeling** - SOS2-based PWL approximation (not in original paper)
4. **Parameter Tuning Study** - 2,430-run experimental validation
5. **Comprehensive Documentation** - Complete mathematical correspondence
6. **Validation Framework** - Automated feasibility checking and warnings

## Project Status

**Research Proof-of-Concept** (December 2024-2025)

### Intended Use
- **Academic Research**: Demonstrate advanced optimization techniques (CVaR, fatigue modeling, stochastic programming)
- **Educational Tool**: Teaching two-stage stochastic programming and healthcare OR
- **Algorithm Validation**: Benchmark solvers, test parameter configurations, experimental studies
- **Proof-of-Concept**: Show feasibility of fatigue-aware risk-controlled scheduling

### NOT Intended For
- **Production Healthcare Deployment**: Requires extensive validation, regulatory approval, and safety audits
- **Real Patient Safety Decisions**: Clinical validation needed before any healthcare use
- **Compliance with Healthcare Regulations**: HIPAA, patient safety standards not implemented

### Development Status
- Core model: 100% complete (22 constraints including fatigue)
- Validation: 4/4 tests passing
- Documentation: 10+ comprehensive guides
- Experiments: 2,430-run parameter tuning complete
- Analysis: Overtime paradox identified and resolved
- Test coverage: Overtime, CVaR, fatigue, emergency staff, soft constraints

### Recent Milestones (Dec 2025)
- Completed parameter tuning study (2,430 experimental runs)
- Added configurable overtime logic with UI toggle
- Enhanced fatigue modeling with SOS2 constraints
- Created Mathematical_Model.tex with code correspondence
- Generated sensitivity analysis and optimal configurations
- Updated README with experiment results
- Organized project into clear directory structure


## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

- He et al. (2019) for the original SDM-CVaR model
- Jaber et al. (2013) for the fatigue modeling framework
- Gurobi Optimization for academic license
- HiGHS team for open-source solver

---

**Citation:**
```bibtex
@article{he2019two,
  title={A two-stage stochastic mixed-integer program modelling and hybrid solution approach to re-rostering problems under patient demand uncertainty},
  author={He, Fang and Qu, Rong},
  journal={European Journal of Operational Research},
  year={2019}
}

@article{jaber2013incorporating,
  title={Incorporating human fatigue and recovery into the learning–forgetting process},
  author={Jaber, Mohamad Y and Givi, Zaher S and Neumann, W Patrick},
  journal={Applied Mathematical Modelling},
  volume={37},
  number={12-13},
  pages={7287--7299},
  year={2013}
}
```

**Star this repo if you find it useful for your research!**

