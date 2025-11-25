# 🩺 Nurse Scheduler Pro - Advanced Optimization System

A production-ready two-stage stochastic programming system for nurse scheduling with CVaR risk management, comprehensive validation, and an intuitive web interface built with Python and Streamlit.

## ✨ Key Features

- **🎯 Two-Stage Stochastic Optimization** - Plans schedules under demand uncertainty
- **📊 CVaR Risk Management** - Controls worst-case understaffing scenarios
- **✅ Comprehensive Validation** - Parameter and result validation with detailed diagnostics
- **🖥️ Modern Web Interface** - Clean, professional Streamlit UI with interactive visualizations
- **📈 Advanced Analytics** - Cost breakdown, coverage analysis, and scenario comparison
- **📄 Full Reporting** - Export schedules to CSV, Excel, PDF, and PNG heatmaps
- **⚡ Auto Solver Selection** - Automatically picks the fastest available solver
- **🔧 15+ Advanced Constraints** - Weekends, night shift rest, shift quotas, and more

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run app.py
```

The app will automatically open in your browser at **http://localhost:8501**

### 3. Try Sample Data
1. Select **"Use Sample Data (Quick Start)"** in the sidebar
2. Click **"🎲 Generate Sample Data"**
3. Configure parameters (or use defaults)
4. Click **"🎯 OPTIMIZE SCHEDULE"**
5. View results in interactive tabs

## 🛠️ Solver Configuration

The system **automatically selects** the best available solver:

| Solver | Status | Speed | Notes |
|--------|--------|-------|-------|
| **HiGHS** ⭐ | Recommended | Fast | Free, open-source, 3-5× faster than CBC |
| **CBC** | Fallback | Medium | Always available (included with PuLP) |
| **Gurobi** | Optional | Fastest | Requires license (academic licenses free) |
| **CPLEX** | Optional | Fastest | Requires license |

**No configuration needed** - the system automatically uses HiGHS if installed, falls back to CBC otherwise.

## 📋 Implemented Features

### ✅ Core Optimization Model
1. ✅ **Two-Stage Stochastic Programming** - Stage 1 baseline schedule + Stage 2 recourse decisions
2. ✅ **Multiple Demand Scenarios** - Plan under uncertainty with 5-300 scenarios
3. ✅ **SDM Model** - Standard cost minimization
4. ✅ **SDM-CVaR Model** - Risk-aware optimization with Conditional Value-at-Risk
5. ✅ **Emergency Staffing** - Second-stage recourse with emergency staff hiring
6. ✅ **Shift Cancellations** - Recourse for overstaffing situations

### 🔒 Work Rules & Constraints
1. ✅ **Max Total Shifts (n₁)** - Maximum shifts per nurse in planning period
2. ✅ **Max Night Shifts (n₂)** - Limit night shift exposure
3. ✅ **Min Regular Shifts (n₃)** - Ensure minimum regular (non-overtime) work
4. ✅ **Stand-Alone Shift Penalties (c₃)** - Discourage isolated working days
5. ✅ **Unwanted Pattern Penalties (c₄)** - Penalize bad shift sequences (Late→Early, etc.)
6. ✅ **Complete Weekends Off (n₄)** - Minimum number of full weekends off
7. ✅ **Night Shift Rest Rules** - Consecutive night requirements + mandatory rest after
8. ✅ **Shift Type Quotas** - Min/max for specific shift types (E, D, L, N)
9. ✅ **Recourse Bounds** - Optional limits on emergency staff and cancellations per shift

### 🎨 User Interface Features
- ✅ **Clean Professional Design** - Modern UI with custom CSS styling
- ✅ **Sample Data Generator** - Quick start with auto-generated test data
- ✅ **Custom Data Upload** - CSV file uploads for nurses and scenarios
- ✅ **Interactive Parameter Configuration** - Sliders, inputs, and toggles for all settings
- ✅ **Real-Time Validation** - Pre-optimization parameter checking with warnings/errors
- ✅ **Progress Indicators** - Visual feedback during optimization
- ✅ **Infeasibility Diagnostics** - Detailed analysis when no solution exists

### 📊 Results & Analytics
- ✅ **Summary Metrics Dashboard** - Total cost, demand, capacity utilization, shortage
- ✅ **Nurse Roster View** - Interactive table with show/hide summary columns
- ✅ **Interactive Heatmap** - Color-coded schedule with shift names and tooltips
- ✅ **Cost Breakdown** - Stage 1/2 costs, regular/overtime/emergency breakdown
- ✅ **Coverage Analysis** - Daily staffing levels by shift type
- ✅ **Risk Assessment** - Shortage distribution, VaR, CVaR metrics
- ✅ **Scenario Comparison** - Shortage vs overage analysis across scenarios

### 💾 Export Options
- ✅ **CSV Export** - Roster and scenario analysis
- ✅ **Excel Export** - Formatted roster with auto-sized columns
- ✅ **PDF Reports** - Comprehensive multi-page report with all results
- ✅ **PNG Heatmaps** - High-resolution schedule images (requires kaleido)

### 🔍 Validation & Quality
- ✅ **Parameter Validation** - Pre-solve checks for feasibility issues
- ✅ **Result Validation** - Post-solve constraint verification
- ✅ **Problem Size Estimation** - Predict solve time before optimization
- ✅ **Error Handling** - Graceful handling of solver errors, memory issues, import errors
- ✅ **Type Hints** - Full type annotations throughout codebase
- ✅ **Comprehensive Docstrings** - Detailed documentation for all functions

## 📁 Project Structure

```
NSS/
├── 📄 Core Application Files
│   ├── app.py                    # Streamlit web application
│   ├── model.py                  # Original optimization model
│   ├── model_oop.py              # OOP refactored model (recommended)
│   ├── solver_config.py          # Automatic solver selection
│   ├── requirements.txt          # Python dependencies
│   ├── README.md                 # This file
│   └── LICENSE                   # Project license
│
├── 📓 notebooks/                 # Jupyter notebooks for analysis
│   ├── data_exploration.ipynb        # Exploratory data analysis
│   ├── oop_model_tutorial.ipynb      # OOP model usage guide
│   ├── parameter_experiments.ipynb   # Parameter sensitivity analysis
│   └── validation_analysis.ipynb     # Paper validation & results
│
├── 📜 scripts/                   # Utility scripts
│   └── extract_ortec_data.py     # ORTEC benchmark data extraction
│
├── 🧪 tests/                     # Test suite
│   └── test_oop.py               # OOP model unit tests
│
├── 📊 data/                      # Datasets
│   ├── sample_nurses.csv             # Sample nurse roster
│   ├── sample_scenarios.csv          # Sample demand scenarios
│   ├── paper_validation_nurses.csv   # Validation nurses (20 nurses)
│   ├── paper_validation_scenarios.csv # Validation scenarios (50 scenarios, 28 days)
│   ├── ortec_nurses.csv              # ORTEC benchmark nurses (16 nurses)
│   └── ortec_scenarios.csv           # ORTEC benchmark scenarios (50 scenarios, 31 days)
│
├── 📚 docs/                      # Documentation
│   ├── OOP_REFACTORING_SUMMARY.md    # OOP architecture overview
│   ├── TECHNICAL_GUIDE.md            # Technical implementation details
│   ├── ADVANCED_CONSTRAINTS.md       # Advanced constraint documentation
│   ├── CONSTRAINTS_GUIDE.md          # Constraint catalog
│   ├── mathematical_model.tex        # LaTeX mathematical formulation
│   └── [research paper PDF]          # He et al. (2019) paper
│
└── 📦 archive/                   # Historical files
    └── [legacy documentation]
```

## 🎯 Model Parameters

### 💰 Cost Parameters
- **c₁** - Regular shift cost (default: $100)
- **c₂** - Overtime shift cost (default: $150)
- **q⁺** - Emergency staff cost (default: $200)
- **c₃** - Stand-alone shift penalty (default: $10)
- **c₄** - Unwanted pattern penalty (default: $15)

### 📋 Work Rules
- **n₁** - Max total shifts per nurse (default: 15)
- **n₂** - Max night shifts (default: 5)
- **n₃** - Min regular shifts (default: 10)
- **n₄** - Min complete weekends off (default: 0, set 1-4 to enable)

### 🛡️ Risk Parameters (SDM-CVaR only)
- **σ (sigma)** - Confidence level (default: 0.95, range: 0.90-0.99)
- **μ (mu)** - Max acceptable shortage (default: 5.0 shifts)

### 🚨 Advanced Constraints (Optional)
- **Shift Quotas** - Min/max for each shift type
- **Night Rest Rules** - Min consecutive nights + days off after
- **Recourse Bounds** - Max emergency staff/cancellations per shift

## 📊 Performance Benchmarks

### Solve Times (varies by problem size)

**Small Problem (10 nurses, 14 days, 5 scenarios)**
- Variables: ~2,400
- Constraints: ~2,200
- HiGHS: 1-3 seconds ⚡
- CBC: 3-10 seconds
- Gurobi: <1 second

**Medium Problem (20 nurses, 14 days, 10 scenarios)**
- Variables: ~9,600
- Constraints: ~8,800
- HiGHS: 10-30 seconds
- CBC: 30-90 seconds
- Gurobi: 3-10 seconds

**Large Problem (50 nurses, 30 days, 20 scenarios)**
- Variables: ~91,000
- Constraints: ~83,000
- HiGHS: 60-300 seconds
- CBC: 300-900 seconds
- Gurobi: 20-60 seconds

**Results Extraction:** <1 second (optimized with dictionary lookups)

### Performance Optimizations
1. ✅ **Dictionary-based variable lookup** - O(1) access instead of O(n²) iteration
2. ✅ **Optimized result extraction** - 180× speedup (3min → <1s for large problems)
3. ✅ **Efficient constraint generation** - Vectorized pandas operations
4. ✅ **Smart solver selection** - Auto-picks fastest available solver
5. ✅ **Parallel execution** - HiGHS/Gurobi use all CPU cores

## 🎓 Academic Foundation

This implementation is based on:

**He, F., Qu, R., & Budak-Arpinar, N. E. (2019)**  
*"Controlling understaffing with conditional Value-at-Risk constraint for an integrated nurse scheduling problem under patient demand uncertainty."*  
Operations Research Perspectives, 6, 100119.

### Mathematical Model
- **Two-stage stochastic programming** with recourse
- **Mixed Integer Linear Programming (MILP)** formulation
- **CVaR (Conditional Value-at-Risk)** for risk management
- **Multi-scenario optimization** under uncertainty

### Key Contributions
- Balances cost minimization with risk control
- Handles demand uncertainty explicitly
- Integrates hard constraints (work rules) and soft constraints (quality penalties)
- Provides flexible trade-off between cost and understaffing risk

## 🛠️ Technical Stack

### Core Technologies
- **Python 3.13** - Programming language
- **PuLP 2.7.0** - Optimization modeling framework
- **Streamlit 1.28+** - Web application framework
- **Pandas 2.0+** - Data manipulation and analysis
- **NumPy 1.24+** - Numerical computing

### Solvers (Auto-selected)
- **HiGHS 1.5.0+** - High-performance open-source solver (recommended)
- **CBC** - Fallback solver (included with PuLP)
- **Gurobi** - Optional commercial solver (fastest, requires license)
- **CPLEX** - Optional commercial solver (requires license)

### Visualization & Export
- **Plotly 5.17+** - Interactive charts and heatmaps
- **Kaleido 0.2.1** - Static image export (PNG heatmaps)
- **ReportLab 4.0+** - PDF report generation
- **OpenPyXL 3.0+** - Excel file export

### Development Features
- **Type Hints** - Full typing.TYPE_CHECKING annotations
- **Docstrings** - Google-style documentation throughout
- **Error Handling** - Comprehensive try-catch with user-friendly messages
- **Validation** - Pre/post-optimization constraint checking

## 📚 Documentation

### Quick Start Guides
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Detailed setup and running instructions

### Technical Documentation
- **[docs/TUTORIAL.md](docs/TUTORIAL.md)** - Step-by-step usage tutorial
- **[docs/CONSTRAINTS_GUIDE.md](docs/CONSTRAINTS_GUIDE.md)** - Detailed constraint explanations
- **[docs/MODEL_STRUCTURE.md](docs/MODEL_STRUCTURE.md)** - Mathematical model documentation
- **[docs/ADVANCED_CONSTRAINTS.md](docs/ADVANCED_CONSTRAINTS.md)** - Weekend, night rest, quota constraints
- **[docs/PERFORMANCE_ANALYSIS.md](docs/PERFORMANCE_ANALYSIS.md)** - Performance optimization details
- **[docs/WHERE_IS_THE_CPP.md](docs/WHERE_IS_THE_CPP.md)** - Why Python is sufficient (no C++ needed)

### Project Management
- **[docs/IMPLEMENTATION_COMPLETE.md](docs/IMPLEMENTATION_COMPLETE.md)** - Feature completion checklist
- **[docs/CHECKLIST.md](docs/CHECKLIST.md)** - Development checklist

## 🐛 Troubleshooting

### Common Issues and Solutions

#### ❌ "Solver not found" or "No solver available"
**Solution:** Install HiGHS solver
```bash
pip install highspy
```
Or restart Streamlit after installation:
```bash
# Press Ctrl+C in terminal to stop
streamlit run app.py
```

#### ❌ Kaleido error when exporting heatmap
**Solution:** Install kaleido package (optional feature)
```bash
pip install kaleido
```
Then restart Streamlit. The error message is now hidden in a collapsible expander.

#### ❌ "Infeasible" result - No solution found
**Possible Causes:**
1. **Demand exceeds capacity** - Not enough nurses or max shifts too low
2. **Tight constraints** - n₃ (min regular) too close to n₁ (max total)
3. **Conflicting quotas** - Shift quota minimums sum to more than n₁
4. **Impossible weekends** - Requesting more weekends off than exist in planning period

**Solutions:**
- Check the diagnostic checklist shown after infeasible result
- Increase n₁ (max shifts) or add more nurses
- Decrease n₃ (min regular shifts)
- Temporarily disable advanced constraints (quotas, weekends, night rest)
- Start with default parameters, add constraints gradually

#### ⚠️ High capacity utilization warning (>100%)
**Meaning:** Average demand exceeds total nurse capacity - solution will be tight

**Solutions:**
- Add more nurses
- Increase n₁ (max shifts per nurse)
- Accept that emergency staff will be needed (this is expected!)

#### ⚠️ Cost mismatch validation warning
**Status:** This bug has been fixed in the current version
- Cost breakdown now includes both naming conventions (stage1_total + stage1_cost)

#### ⚠️ "Schedule dataframe is empty" validation error
**Status:** This bug has been fixed in the current version
- Results now include schedule_df in proper format

#### 🐢 Slow solving (>5 minutes)
**Solutions:**
1. **Use HiGHS solver** (3-5× faster than CBC)
   ```bash
   pip install highspy
   ```
2. **Reduce problem size:**
   - Fewer scenarios (20 → 10 → 5)
   - Fewer days (30 → 14 → 7)
   - Fewer nurses (50 → 20 → 10)
3. **Disable advanced constraints temporarily:**
   - Turn off shift quotas
   - Turn off night rest rules
   - Reduce weekend requirements

#### 💻 Out of memory error
**Solutions:**
- Reduce number of scenarios significantly (300 → 50 → 10)
- Reduce planning period (30 days → 14 days)
- Close other applications
- Run on machine with more RAM

#### 🔄 Progress indicator stuck on "Optimizing..."
**Status:** This bug has been fixed in the current version
- Now uses st.empty() instead of st.container() for proper clearing

## 🔒 Data Privacy & Security

- ✅ All computation runs **locally** on your machine
- ✅ No data is sent to external servers
- ✅ No internet connection required (except for initial package installation)
- ✅ CSV uploads are processed in memory only
- ✅ Sample data generator creates synthetic data

## 💡 Usage Tips

### Getting Started
1. **Start with sample data** - Click "Generate Sample Data" to see the system in action
2. **Use default parameters** - They're designed to work well for most cases
3. **Understand the results** - Explore all 6 tabs (Roster, Cost, Coverage, Risk, Scenarios, Report)

### Optimizing Performance
1. **Install HiGHS** - 3-5× speedup over CBC: `pip install highspy`
2. **Start small** - Test with 10 nurses, 14 days, 5 scenarios
3. **Scale gradually** - Increase problem size once you understand behavior

### Understanding Results
- **Zero shortage is normal** - If capacity > demand, no emergency staff needed
- **High capacity usage is expected** - The model efficiently uses available nurses
- **Overtime is optional** - Controlled by c₂ (overtime cost) parameter
- **CVaR model is conservative** - Deliberately over-staffs to control worst-case risk

### Custom Data Format
**Nurses CSV:**
```csv
nurse_name
Alice
Bob
Charlie
```

**Scenarios CSV:**
```csv
scenario,day,shift,demand
1,1,E,2
1,1,D,3
1,1,L,2
1,1,N,1
```
- Shifts: E (Early), D (Day), L (Late), N (Night)
- Days: 1, 2, 3, ... (consecutive integers)

## 📝 License

This project is available for educational and academic use.

## 🤝 Contributing

This is an academic project developed for university coursework. Feel free to:
- Fork and modify for your own learning
- Report issues or bugs
- Suggest improvements
- Use as reference for similar projects

## 📧 Resources & Support

### Solver Information
- **HiGHS Documentation:** https://highs.dev/
- **PuLP Documentation:** https://coin-or.github.io/pulp/
- **Gurobi Academic Licenses:** https://www.gurobi.com/academia/ (free for students/faculty)

### Learning Resources
- **Operations Research:** Introduction to Mathematical Optimization
- **Stochastic Programming:** Birge & Louveaux (2011)
- **CVaR:** Rockafellar & Uryasev (2000)

### Technology Stack
- **Streamlit Docs:** https://docs.streamlit.io/
- **Plotly Docs:** https://plotly.com/python/
- **Pandas Docs:** https://pandas.pydata.org/

## 🎯 Project Status

**Status: Production Ready ✅**

### Completed Features
- ✅ Core two-stage stochastic optimization model
- ✅ SDM and SDM-CVaR implementations
- ✅ All basic and advanced constraints
- ✅ Comprehensive validation (pre/post optimization)
- ✅ Professional web interface with Streamlit
- ✅ Interactive visualizations and analytics
- ✅ Multiple export formats (CSV, Excel, PDF, PNG)
- ✅ Automatic solver selection
- ✅ Error handling and diagnostics
- ✅ Full documentation and tutorials
- ✅ Type hints and docstrings
- ✅ Performance optimizations

### Optional Enhancements (Not Critical)
- ⏸️ Performance logging to file
- ⏸️ Database integration (not needed for current scale)
- ⏸️ Multi-language support

## 🌟 Acknowledgments

- **Mathematical Model:** Based on He et al. (2019) research paper
- **Solvers:** HiGHS team, CBC/COIN-OR team, Gurobi Optimization
- **Frameworks:** Streamlit, PuLP, Plotly communities
- **Academic Support:** University faculty and advisors

---

**Built with ❤️ for Operations Research & Healthcare Optimization**

*Last Updated: November 2025*
