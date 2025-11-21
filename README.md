# 🩺 Nurse Scheduling System - Optimization Prototype

A web-based nurse scheduling prototype using Mixed Integer Linear Programming (MILP) to generate optimized schedules that balance cost minimization, staffing coverage, regulatory compliance, and fairness. Built with Python, PuLP, and Streamlit.

## ✨ Key Features

- **🎯 MILP Optimization** - Automated schedule generation using mathematical optimization
- **✅ Constraint Satisfaction** - Enforces work regulations, coverage requirements, and fairness criteria
- **🖥️ Web Interface** - Accessible Streamlit-based UI requiring no programming knowledge
- **📈 Visualization** - Interactive Gantt charts and schedule heatmaps
- **📄 Export Options** - Generate schedules in CSV and Excel formats
- **⚡ Dual Solver Support** - Uses Gurobi (commercial) or HiGHS (free) solver backends
- **🔧 Configurable Constraints** - Adjustable maximum shifts, rest periods, and scheduling rules

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

### 3. Generate a Schedule
1. Upload nurse availability CSV or use sample data
2. Define shift requirements
3. Configure constraints (max consecutive shifts, rest periods, etc.)
4. Click optimize to generate schedule
5. View results as interactive charts or export to CSV/Excel

## 🛠️ Solver Configuration

The system supports multiple optimization solvers:

| Solver | Status | Performance | Notes |
|--------|--------|-------------|-------|
| **Gurobi** | Recommended | Fastest (1-60s) | Commercial license required (free academic licenses available) |
| **HiGHS** | Free Alternative | Good (5-600s) | Open-source, no license needed |

Install HiGHS for free solving:
```bash
pip install highspy
```

For Gurobi (faster performance), obtain academic license at: https://www.gurobi.com/academia/

## 📋 Implemented Features

### ✅ Core Optimization Model
1. ✅ **MILP Formulation** - Mixed Integer Linear Programming for nurse-to-shift assignment
2. ✅ **Cost Minimization** - Minimize total staffing costs while meeting coverage
3. ✅ **Multiple Shift Types** - Support for Early, Day, Late, and Night shifts
4. ✅ **Configurable Planning Horizon** - Adjustable schedule duration (14-28 days typical)
5. ✅ **Synthetic Data Generation** - Random test case generation for validation

### 🔒 Constraints Implemented
1. ✅ **Coverage Requirements** - Minimum staffing per shift type per day
2. ✅ **Single Assignment** - One shift maximum per nurse per day
3. ✅ **Maximum Consecutive Shifts** - Limit continuous work periods (5-7 days)
4. ✅ **Rest Period Rules** - Mandatory time off between shift blocks
5. ✅ **Shift Type Restrictions** - Control night shift exposure and patterns
6. ✅ **Fairness Criteria** - Balanced workload distribution across nurses

### 🎨 User Interface Features
- ✅ **Streamlit Web Interface** - Accessible browser-based application
- ✅ **CSV Data Upload** - Import nurse availability and shift requirements
- ✅ **Interactive Configuration** - Adjust constraints without coding
- ✅ **Real-Time Validation** - Input checking before optimization
- ✅ **Visual Feedback** - Progress indicators during solving

### 📊 Visualization & Results
- ✅ **Schedule Heatmap** - Color-coded visual schedule representation
- ✅ **Gantt Charts** - Timeline view of nurse assignments
- ✅ **Coverage Analysis** - Staffing level visualization by shift
- ✅ **Cost Breakdown** - Summary of optimization costs
- ✅ **Constraint Verification** - Post-solve validation reporting

### 💾 Export Capabilities
- ✅ **CSV Export** - Nurse roster and schedule data
- ✅ **Excel Export** - Formatted spreadsheet output
- ✅ **PNG Heatmaps** - Static schedule images (requires Kaleido)

## 📁 Project Structure

```
NSS/
├── 📄 Core Application Files
│   ├── app.py                    # Streamlit web application
│   ├── model.py                  # MILP optimization model
│   ├── model_oop.py              # Object-oriented model implementation
│   ├── solver_config.py          # Solver configuration and selection
│   ├── requirements.txt          # Python dependencies
│   ├── methodology.tex           # LaTeX methodology document
│   ├── README.md                 # This file
│   └── LICENSE                   # Project license
│
├── 📓 notebooks/                 # Jupyter notebooks for analysis
│   └── [analysis notebooks]
│
├── 📜 scripts/                   # Utility scripts
│   └── [helper scripts]
│
├── 🧪 tests/                     # Test suite
│   └── test_oop.py               # Unit tests
│
├── 📊 data/                      # Sample datasets
│   ├── sample_nurses.csv         # Sample nurse roster
│   └── sample_scenarios.csv      # Sample shift requirements
│
├── 📚 docs/                      # Documentation
│   ├── ADVANCED_CONSTRAINTS.md       # Advanced constraint details
│   ├── CONSTRAINTS_GUIDE.md          # Constraint catalog
│   ├── OOP_REFACTORING_SUMMARY.md    # Code architecture overview
│   ├── TECHNICAL_GUIDE.md            # Implementation details
│   ├── mathematical_model.tex        # LaTeX math formulation
│   └── [research paper PDF]          # Reference paper
│
└── 📦 archive/                   # Legacy documentation
    └── [historical files]
```

## 🎯 Model Parameters

### 💰 Cost Parameters
- **Regular Shift Cost** - Base cost per scheduled shift
- **Overtime Cost** - Premium cost for additional shifts
- **Penalty Costs** - Soft constraint violation penalties

### 📋 Constraint Configuration
- **Max Consecutive Shifts** - Maximum continuous work days (default: 5-7)
- **Rest Period Requirements** - Minimum days off between shift blocks
- **Shift Type Limits** - Maximum night shifts, shift quotas
- **Coverage Requirements** - Minimum staff per shift type per day

### 📊 Problem Scale
- **Nurses** - Number of staff members (10-50 typical)
- **Planning Horizon** - Schedule duration in days (14-28 typical)
- **Shift Types** - Early, Day, Late, Night (4 types standard)

## 📊 Performance Benchmarks

### Solve Times (Initial Tests)

**Small Problem (10 nurses, 14 days)**
- Variables: ~560
- Constraints: ~500
- Gurobi: 1-5 seconds ⚡
- HiGHS: 5-20 seconds

**Medium Problem (20 nurses, 28 days)**
- Variables: ~2,240
- Constraints: ~2,000
- Gurobi: 5-20 seconds
- HiGHS: 30-60 seconds

**Large Problem (50 nurses, 28 days)**
- Variables: ~5,600
- Constraints: ~5,000
- Gurobi: 20-60 seconds
- HiGHS: 60-600 seconds

**Note:** These are preliminary results based on synthetic test data. Performance will vary based on constraint complexity and hardware specifications.

## 🎓 Academic Foundation

This prototype implements nurse scheduling optimization using established operations research methodologies. The implementation draws from academic literature on the Nurse Scheduling Problem (NSP), an NP-hard combinatorial optimization challenge.

### Mathematical Approach
- **Mixed Integer Linear Programming (MILP)** formulation
- **Deterministic optimization** with configurable constraints
- **Multi-objective balancing** of cost, coverage, and fairness

### Key References
Referenced literature includes works on:
- Integer programming approaches for nurse rostering
- Constraint satisfaction in healthcare scheduling
- Workload balancing and fairness optimization
- Hybrid optimization algorithms

**Note:** This is a proof-of-concept prototype requiring validation with real hospital data before clinical deployment.

## 🛠️ Technical Stack

### Core Technologies
- **Python 3.13.5** - Programming language
- **PuLP 3.3.0** - Optimization modeling framework
- **Streamlit 1.45.1** - Web application framework
- **Pandas 2.2.3** - Data manipulation and analysis

### Solvers
- **Gurobi 13.0.0** - Commercial solver (recommended, requires license)
- **HiGHS 1.12.0** - Open-source solver (free alternative)

### Visualization & Export
- **Plotly 5.24.1** - Interactive charts and heatmaps
- **Matplotlib 3.10.0** - Static visualizations
- **Kaleido 0.2.1** - PNG export (optional)
- **OpenPyXL 3.0+** - Excel file export
- **ReportLab 4.0+** - PDF generation (optional)

## 📚 Documentation

### Project Documentation
- **[methodology.tex](methodology.tex)** - LaTeX methodology document describing the prototype

### Technical Documentation
- **[docs/CONSTRAINTS_GUIDE.md](docs/CONSTRAINTS_GUIDE.md)** - Detailed constraint explanations
- **[docs/ADVANCED_CONSTRAINTS.md](docs/ADVANCED_CONSTRAINTS.md)** - Advanced constraint details
- **[docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md)** - Technical implementation guide
- **[docs/OOP_REFACTORING_SUMMARY.md](docs/OOP_REFACTORING_SUMMARY.md)** - Code architecture overview

## 🐛 Troubleshooting

### Common Issues and Solutions

#### ❌ "Solver not found"
**Solution:** Install a solver
```bash
# For free HiGHS solver
pip install highspy

# Or obtain Gurobi academic license
# Visit: https://www.gurobi.com/academia/
```

#### ❌ Kaleido error when exporting images
**Solution:** Install kaleido (optional for PNG export)
```bash
pip install kaleido
```

#### ❌ "Infeasible" result - No solution found
**Possible Causes:**
1. **Demand exceeds capacity** - Not enough nurses or max shifts too low
2. **Conflicting constraints** - Mutually exclusive requirements
3. **Over-constrained problem** - Too many restrictive rules

**Solutions:**
- Increase maximum shifts per nurse
- Add more nurses to the roster
- Reduce constraint strictness
- Check shift requirements are realistic

#### 🐢 Slow solving
**Solutions:**
1. **Use Gurobi if available** (significantly faster than HiGHS)
2. **Reduce problem size:**
   - Fewer nurses
   - Shorter planning period
   - Simpler constraints
3. **Upgrade hardware** - More RAM and faster CPU help

#### ❌ CSV upload errors
**Solutions:**
- Verify CSV format matches required structure
- Check for special characters or encoding issues
- Ensure column names match expected format
- Use sample CSV files as templates

## 🔒 Data Privacy & Security

- ✅ All computation runs **locally** on your machine
- ✅ No data sent to external servers
- ✅ No internet connection required after installation
- ✅ CSV uploads processed in memory only
- ✅ Sample data generator creates synthetic test data

## 💡 Usage Tips

### Getting Started
1. **Start with sample data** - Use provided sample CSV files to understand the system
2. **Use default parameters** - Begin with reasonable default constraints
3. **Understand the model** - Review documentation before complex configurations

### Data Requirements
**Nurse availability CSV:**
```csv
nurse_name
Alice
Bob
Charlie
```

**Shift requirements CSV:**
```csv
day,shift,demand
1,E,2
1,D,3
1,L,2
1,N,1
```
- Shifts: E (Early), D (Day), L (Late), N (Night)
- Days: consecutive integers starting from 1

### Optimization Tips
- **Validate inputs** - Check CSV format before optimization
- **Start simple** - Add constraints gradually
- **Monitor solve time** - Large problems may require several minutes
- **Verify results** - Review generated schedules for practical feasibility

## 📝 License

This project is available for educational and academic use.

## 🤝 Contributing

This is an academic prototype developed for university coursework. The codebase is provided as-is for educational purposes.

## 📧 Contact & Support

### Development Team
- MennaTallah Amin (120220027)
- Khadiga Mohamed (120220039)  
- Ibrahim Magdy (120220077)
- Rahmatullah Mohamed (120220079)

### Resources
- **PuLP Documentation:** https://coin-or.github.io/pulp/
- **Gurobi Academic Licenses:** https://www.gurobi.com/academia/
- **HiGHS Documentation:** https://highs.dev/
- **Streamlit Docs:** https://docs.streamlit.io/

## 🎯 Project Status

**Status: Proof-of-Concept Prototype**

### ⚠️ Important Limitations
This is a **prototype system** requiring significant additional work before clinical deployment:

- ❗ **No real hospital data validation** - Tested only with synthetic data
- ❗ **Requires field testing** - Needs validation with actual healthcare professionals
- ❗ **Limited constraint coverage** - May not capture all real-world hospital policies
- ❗ **No regulatory compliance verification** - Requires validation against local labor laws
- ❗ **Scalability untested** - Performance with 100+ nurses not validated
- ❗ **Deterministic only** - Does not handle demand uncertainty or stochastic scenarios

### ✅ Completed Features
- ✅ Core MILP optimization engine
- ✅ Web-based user interface
- ✅ Basic constraint implementation
- ✅ Visualization and export capabilities
- ✅ Dual solver support (Gurobi/HiGHS)
- ✅ Modular codebase architecture

### 🔄 Future Work Required
- Integration with hospital information systems
- Validation with real clinical data
- User acceptance testing with healthcare staff
- Enhanced constraint modeling
- Regulatory compliance verification
- Performance optimization for large-scale deployment
- Security and data privacy enhancements

---

**Built for Operations Research & Healthcare Scheduling Education**

*Last Updated: November 2025*
