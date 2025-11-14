# 🏥 Nurse Scheduler - Stochastic Optimization System

A comprehensive two-stage stochastic programming system for nurse scheduling with CVaR risk management, built with Python and Streamlit.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Automatic Solver Selection

The system automatically selects the best available free solver:

**HiGHS** (Recommended - installed by default) ⭐
```bash
pip install highspy
```
- ✅ Completely free
- ✅ 3-5× faster than CBC
- ✅ Automatically selected if available

**CBC** (Fallback - included with PuLP)
- ✅ Always available
- ✅ Automatically used if HiGHS not installed

**No manual selection needed** - the framework chooses automatically!

### 3. Run the App
```bash
streamlit run app.py
```

Open browser at: **http://localhost:8501**

## 📋 Features

### ✅ Implemented Constraints (15/18)
1. ✅ **Coverage Requirements** - Minimum nurses per shift
2. ✅ **Max Hours per Day** - Prevent overwork
3. ✅ **Min Rest Between Shifts** - 12-hour rest periods
4. ✅ **Max Consecutive Days** - Prevent burnout
5. ✅ **Min Days Off per Period** - Ensure work-life balance
9. ✅ **Weekend Coverage** - Fair weekend distribution
10. ✅ **Shift Distribution** - Balanced assignment across nurses
11. ✅ **Nurse Preferences** - Preferred shifts
12. ✅ **Nurse Availability** - Unavailable days
13. ✅ **Minimum Hours per Week** - Part-time/full-time requirements
14. ✅ **Two-Stage Stochastic Programming** - Uncertainty modeling
15. ✅ **CVaR Risk Management** - Risk-averse optimization

### 📊 Advanced Features
- **Multi-scenario planning** - Handle demand uncertainty
- **Risk-based optimization** - CVaR (Conditional Value at Risk)
- **Performance optimization** - Results extraction in <1 second
- **Automatic solver selection** - Picks the fastest free solver available
- **Interactive web UI** - Built with Streamlit
- **Real-time performance metrics** - Solving time tracking

## 📁 Project Structure

```
nurse-scheduler/
├── app.py                    # Streamlit web application
├── model.py                  # Optimization model (928 lines)
├── solver_config.py          # Solver configuration
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── QUICKSTART.md             # Quick start guide
├── HOW_TO_RUN.md            # Detailed running instructions
├── data/                     # Sample data files
│   └── sample_schedule.csv
├── docs/                     # Technical documentation
│   ├── ADVANCED_CONSTRAINTS.md
│   ├── CONSTRAINTS_GUIDE.md
│   ├── MODEL_STRUCTURE.md
│   ├── TUTORIAL.md
│   ├── PERFORMANCE_ANALYSIS.md
│   └── WHERE_IS_THE_CPP.md
└── archive/                  # Old documentation
```

## 🔧 Configuration

### Automatic Solver Selection
The system automatically detects and uses the fastest available free solver:
1. **HiGHS** - Automatically selected if installed (3-5× faster than CBC)
2. **CBC** - Automatic fallback (always available)

**No configuration needed** - works out of the box!

### Risk Settings
- **α (Alpha)**: Confidence level for CVaR (default: 0.95)
- **λ (Lambda)**: Risk aversion weight (0-1, default: 0.5)
  - 0 = Risk-neutral
  - 1 = Fully risk-averse

### Solver Settings
- **Time Limit**: Maximum solving time (60-600 seconds)
- **MIP Gap**: Optimality tolerance (0.01-0.10)

## 📊 Performance

### Expected Solve Times (20 nurses, 14 days, 10 scenarios)

| Solver | Time | Speedup |
|--------|------|---------|
| CBC | 60-180s | 1× |
| HiGHS | 20-40s | 3-5× |
| Gurobi | 5-15s | 10-30× |

*Note: Results extraction is optimized to <1 second*

## 🎓 Academic Context

This is a university project implementing advanced optimization techniques:
- Two-stage stochastic programming
- Conditional Value at Risk (CVaR)
- Mixed Integer Linear Programming (MILP)
- Multi-scenario optimization

## 📚 Documentation

- **QUICKSTART.md** - Get started in 5 minutes
- **HOW_TO_RUN.md** - Detailed setup instructions
- **docs/TUTORIAL.md** - Step-by-step tutorial
- **docs/CONSTRAINTS_GUIDE.md** - Constraint explanations
- **docs/MODEL_STRUCTURE.md** - Technical model details
- **docs/PERFORMANCE_ANALYSIS.md** - Performance optimization guide

## 🛠️ Technical Stack

- **Python 3.13** - Programming language
- **Streamlit 1.45.1** - Web framework
- **PuLP 2.7.0** - Optimization modeling
- **HiGHS 1.12.0** - Solver (recommended)
- **Gurobi 13.0.0** - Solver (optional)
- **Pandas** - Data handling
- **NumPy** - Numerical operations

## ⚡ Performance Optimizations

1. **Dictionary-based variable lookup** - O(1) instead of O(n²)
2. **Optimized result extraction** - 180× speedup (3min → <1s)
3. **Efficient constraint generation** - Vectorized operations
4. **Multi-threaded solving** - Uses all CPU cores
5. **Aggressive presolve** - Reduces problem size

## 🐛 Troubleshooting

### "Model too large for size-limited license"
- You're using Gurobi trial/web license (2,000 variable limit)
- **Solution**: Use HiGHS (`pip install highspy`) or get academic license

### "Solver not available"
- **Solution**: Install solver: `pip install highspy` or `pip install gurobipy`

### Slow solving (>3 minutes)
- **Solution**: Switch to HiGHS or Gurobi solver
- Reduce scenarios (10 → 5) or days (14 → 7)

### Results take long to appear
- Fixed in current version (dictionary-based lookup)
- Should be <1 second now

## 📝 License

Academic project - Free to use for educational purposes

## 🤝 Contributing

This is a university project. For questions or improvements, feel free to modify and extend!

## 📧 Support

For Gurobi academic licenses: https://www.gurobi.com/academia/
For HiGHS documentation: https://highs.dev/

---

**Built with ❤️ for Operations Research & Optimization**
