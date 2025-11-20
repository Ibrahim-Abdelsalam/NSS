# 🏥 Nurse Scheduling System - Technical Guide

A complete explanation of the implementation, from architecture to execution.

---

## 📋 Table of Contents

1. [What This System Does](#what-this-system-does)
2. [Technology Stack](#technology-stack)
3. [Code Architecture](#code-architecture)
4. [Data Flow](#data-flow)
5. [Key Libraries & Their Roles](#key-libraries--their-roles)
6. [How the Optimization Works](#how-the-optimization-works)
7. [Running the Application](#running-the-application)

---

## 🎯 What This System Does

This system solves a complex nurse scheduling problem:

**Input:**
- List of nurses (e.g., 20 nurses)
- Demand scenarios (e.g., 50 different possible demand patterns over 28 days)
- Cost parameters (regular pay, overtime pay, emergency staff costs)
- Work rules (max shifts, min shifts, weekends off, etc.)

**Output:**
- Optimized work schedule for all nurses
- Cost breakdown (regular shifts, overtime, emergency staff)
- Coverage analysis (how well demand is met)
- Risk assessment (worst-case scenarios)

**Goal:** Minimize total cost while satisfying all constraints and meeting patient demand under uncertainty.

---

## 🛠️ Technology Stack

### Programming Language
**Python 3.8+** - Chosen for:
- Excellent optimization libraries (PuLP, NumPy)
- Strong data manipulation (pandas)
- Easy web interface creation (Streamlit)
- Rapid development and testing

### Key Dependencies
```
streamlit==1.40.0      # Web interface
pulp==2.9.0            # Optimization modeling
pandas==2.2.3          # Data handling
numpy==2.1.3           # Numerical computations
```

---

## 🏗️ Code Architecture

The system has **4 main Python files**:

### 1. `model_oop.py` (NEW - ~850 lines) ⭐
**Purpose:** Object-oriented optimization engine - clean, maintainable interface

**Key Classes:**
```python
class ModelParameters:
    """Encapsulates all model parameters with validation"""
    c1, c2, q_plus, q_minus  # Cost parameters
    n1, n2, n3, n4           # Work rules
    sigma, mu                # CVaR parameters
    
    def validate(self):
        """Ensures all parameters are valid"""

class NurseSchedulingModel:
    """Main optimization model"""
    def __init__(self, nurses, scenarios, params):
        """Initialize with data and parameters"""
    
    def build(self, model_type="SDM"):
        """Build the optimization model (variables + constraints)"""
    
    def solve(self, solver='highs'):
        """Solve the model and return status"""
    
    def get_results(self):
        """Extract solution into OptimizationResults object"""

class OptimizationResults:
    """Encapsulates solution data with convenient accessors"""
    @property
    def total_cost(self): ...
    
    @property
    def schedule(self): ...
```

**Usage:**
```python
# Create parameters
params = ModelParameters(c1=100, c2=150, q_plus=200, n1=24, n2=3, n3=16)

# Create and solve model
model = NurseSchedulingModel(nurses_list, scenarios_df, params)
model.build(model_type="SDM")
status = model.solve(solver='highs')

# Get results
if status == "Optimal":
    results = model.get_results()
    print(f"Total cost: ${results.total_cost:.2f}")
    schedule_df = results.schedule
```

### 2. `model.py` (1,648 lines) - Legacy Functional Version
**Purpose:** Original functional implementation (kept for backward compatibility)

**Key Functions:**
```python
def build_and_solve_model(nurses_list, scenarios_df, model_params, 
                          model_type="SDM", solver_name="highs"):
    """
    Builds and solves the model using functional approach.
    Returns: (prob, status)
    """
```

**Note:** `app.py` now uses the OOP version (`model_oop.py`) but falls back to functional if needed.

---

### 3. `app.py` (1,813 lines)
**Purpose:** The optimization engine - builds and solves the mathematical model

**Key Functions:**
```python
solve_nurse_scheduling(
    nurses_list,           # List of nurse names
    scenarios_df,          # Demand data (DataFrame)
    model_params,          # Costs, constraints, settings
    model_type="SDM",      # Model variant (DM, SDM, SDM-CVaR)
    solver_name="highs"    # Optimization solver
)
```

**What it does:**
1. **Creates decision variables** (which nurse works which shift)
2. **Builds constraints** (work rules, coverage requirements)
3. **Defines objective function** (minimize cost)
4. **Calls solver** (HiGHS, CBC, or Gurobi)
5. **Extracts solution** (schedule, costs, metrics)

**Structure:**
- Lines 1-150: Setup and variable creation
- Lines 151-813: 22 constraints implementation
- Lines 814-900: Solver configuration
- Lines 901-1648: Results extraction and formatting

### 3. `app.py` (1,826 lines)
**Purpose:** Web-based user interface using Streamlit

**Flow:**
```
User Input → Parameter Validation → Run Optimization (OOP) → Display Results
```

**Main Sections:**
1. **File Upload** (lines 240-390)
   - Load nurse list and demand scenarios
   - Validate data format and completeness
   
2. **Parameter Settings** (lines 391-670)
   - Cost parameters (c₁, c₂, q⁺, q⁻)
   - Work rules (n₁, n₂, n₃, n₄)
   - Advanced constraints (shift quotas, patterns)
   - CVaR risk parameters (σ, μ)

3. **Optimization Execution** (lines 671-900) **UPDATED TO USE OOP**
   ```python
   # NEW: Object-oriented approach
   params = ModelParameters(**model_params)
   model = NurseSchedulingModel(nurses_list, scenarios_df, params)
   model.build(model_type="SDM")
   status = model.solve(solver=selected_solver)
   results = model.get_results()
   ```

4. **Results Display** (lines 901-1826)
   - Summary metrics
   - Cost analysis charts
   - Coverage visualization
   - Downloadable schedule

---

### 4. `solver_config.py` (243 lines)
**Purpose:** Configure different optimization solvers

**Why this file exists:**
- Different solvers have different syntax
- HiGHS (free, fast) vs CBC (free, slower) vs Gurobi (commercial, fastest)
- This file provides a unified interface

**Function:**
```python
create_solver(solver_name, time_limit, mip_gap, threads)
```

**Supported Solvers:**
- **HiGHS** (default) - Open source, 3-5× faster than CBC
- **CBC** - Backup option, widely available
- **Gurobi** - Best performance, requires license

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT (app.py)                                      │
│    - Upload nurses.csv                                      │
│    - Upload scenarios.csv                                   │
│    - Set parameters via UI sliders/inputs                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. DATA VALIDATION (app.py)                                 │
│    - Check required columns exist                           │
│    - Verify no missing values                               │
│    - Confirm data completeness                              │
│    - Validate parameter ranges                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. MODEL BUILDING (model.py)                                │
│    a) Parse inputs                                          │
│    b) Create decision variables (x, y, α, β, ξ, z)         │
│    c) Build 22 constraints                                  │
│    d) Define objective function                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. SOLVER EXECUTION (solver_config.py + model.py)           │
│    - Convert model to solver format                         │
│    - Run optimization algorithm                             │
│    - Return optimal solution or status (infeasible, etc.)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. RESULTS EXTRACTION (model.py)                            │
│    - Extract variable values from solution                  │
│    - Calculate metrics (total cost, shortage, etc.)         │
│    - Build nurse schedules and coverage tables              │
│    - Format data for visualization                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. VISUALIZATION (app.py)                                   │
│    - Display summary metrics                                │
│    - Generate charts (Plotly)                               │
│    - Show tables (pandas DataFrames)                        │
│    - Provide download buttons                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Key Libraries & Their Roles

### 1. **PuLP** - Optimization Modeling
```python
import pulp

# Create optimization problem
prob = pulp.LpProblem("NurseScheduling", pulp.LpMinimize)

# Create variables
x = pulp.LpVariable("shift", cat=pulp.LpBinary)  # 0 or 1

# Add constraints
prob += x + y <= 1  # At most one shift per day

# Solve
prob.solve()
```

**Why PuLP?**
- ✅ Simple, readable syntax (like mathematical notation)
- ✅ Works with multiple solvers (HiGHS, CBC, Gurobi)
- ✅ Good documentation and community support
- ✅ Free and open source

**Alternative considered:** Google OR-Tools (rejected: more complex API)

---

### 2. **Pandas** - Data Manipulation
```python
import pandas as pd

# Load CSV files
scenarios_df = pd.read_csv('scenarios.csv')

# Filter and group data
demand_per_day = scenarios_df.groupby('day')['demand'].sum()

# Convert to dictionary for fast lookup
demand_dict = scenarios_df.set_index(['day', 'shift'])['demand'].to_dict()
```

**Why Pandas?**
- ✅ Industry standard for tabular data
- ✅ Fast operations on large datasets
- ✅ Easy CSV reading/writing
- ✅ Integrates perfectly with Streamlit

**Use cases in our code:**
- Reading nurse lists and demand scenarios
- Grouping and aggregating results
- Creating summary tables for display

---

### 3. **NumPy** - Numerical Computing
```python
import numpy as np

# Generate random demand with seed for reproducibility
np.random.seed(42)
demand = np.random.randint(1, 5, size=100)

# Statistical operations
avg_demand = np.mean(demand)
std_demand = np.std(demand)
```

**Why NumPy?**
- ✅ Fast array operations (C-level performance)
- ✅ Essential for scientific computing
- ✅ Random number generation with seeds

**Use cases in our code:**
- Generating sample demand data
- Statistical calculations for validation
- Array operations in data processing

---

### 4. **Streamlit** - Web Interface
```python
import streamlit as st

# Create UI elements
nurse_count = st.slider("Number of Nurses", 10, 50, 20)
cost_c1 = st.number_input("Regular Shift Cost", 0.0, 1000.0, 100.0)

if st.button("Optimize"):
    results = solve_nurse_scheduling(...)
    st.success("Optimization complete!")
    st.dataframe(results['schedule'])
```

**Why Streamlit?**
- ✅ Turn Python scripts into web apps in minutes
- ✅ No HTML/CSS/JavaScript knowledge needed
- ✅ Automatic reactive updates
- ✅ Built-in widgets (sliders, buttons, charts)
- ✅ Easy deployment

**Alternative considered:** Flask (rejected: requires more boilerplate code)

---

### 5. **Plotly** - Interactive Visualizations
```python
import plotly.express as px

# Create bar chart
fig = px.bar(cost_df, x='category', y='amount', title='Cost Breakdown')
st.plotly_chart(fig)
```

**Why Plotly?**
- ✅ Interactive charts (zoom, hover, click)
- ✅ Professional appearance
- ✅ Integrates seamlessly with Streamlit
- ✅ Wide variety of chart types

**Charts in our app:**
- Cost breakdown (bar chart)
- Coverage over time (line chart)
- Scenario comparison (scatter plot)
- Risk distribution (box plot)

---

## ⚙️ How the Optimization Works

### Mathematical Model Type
**Two-Stage Stochastic Integer Programming with CVaR**

### Stage 1: Pre-commitment Decisions
**Before** knowing actual demand, decide:
- Which nurses work which shifts (regular)
- Which nurses work overtime

**Variables:** `sr[i][j][k]` (regular), `so[i][j][k]` (overtime)

### Stage 2: Recourse Decisions
**After** seeing actual demand in each scenario, decide:
- How many emergency staff to hire (`α`)
- How many shifts to cancel (`β`)

**Variables:** `α[j][k][ω]` (emergency), `β[j][k][ω]` (cancellation)

---

### Example Execution Flow

**Input:**
- 20 nurses
- 28 days
- 50 demand scenarios
- 4 shift types (Early, Day, Late, Night)

**Variables Created:**
- Decision variables: 18,571
  - Regular shifts: 20 × 28 × 4 = 2,240
  - Overtime shifts: 20 × 28 × 4 = 2,240
  - Emergency staff: 28 × 4 × 50 = 5,600
  - Cancellations: 28 × 4 × 50 = 5,600
  - Helper variables: ~2,891

**Constraints:**
- ~23,296 constraints enforcing:
  - One shift per nurse per day
  - Max/min shift limits
  - Demand coverage
  - Weekend requirements
  - Shift patterns
  - CVaR risk bounds

**Solving:**
- HiGHS solver uses Branch-and-Bound algorithm
- Typical solve time: 5-15 seconds
- Returns optimal or near-optimal solution

---

## 🚀 Running the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Application
```bash
streamlit run app.py
```

### 3. Use the Interface

**Step 1:** Upload data
- `data/paper_validation_nurses.csv` (20 nurses)
- `data/paper_validation_scenarios.csv` (5,600 demand records)

**Step 2:** Set parameters
- Cost parameters: c₁=10, c₂=15, q⁺=18, q⁻=2
- Work rules: n₁=24, n₂=3, n₃=16, n₄=4
- Model type: Choose SDM or SDM-CVaR

**Step 3:** Click "🚀 Optimize Schedule"
- Wait 5-15 seconds for solution
- View results in multiple tabs

**Step 4:** Download results
- Excel file with complete schedule
- CSV files for further analysis

---

## 🔍 Code Walkthrough - Key Functions

### Main Optimization Function
```python
def solve_nurse_scheduling(nurses_list, scenarios_df, model_params, 
                          model_type="SDM", solver_name="highs"):
    """
    Solves the nurse scheduling optimization problem.
    
    Process:
    1. Parse inputs and extract parameters
    2. Identify all nurses, days, shifts, scenarios
    3. Create PuLP problem instance
    4. Define decision variables (x, y, α, β, etc.)
    5. Add 22 constraints
    6. Set objective function (minimize cost)
    7. Configure and run solver
    8. Extract and format results
    9. Return comprehensive results dictionary
    """
```

### Variable Creation Example
```python
# Binary variable: 1 if nurse i works regular shift k on day j
sr = pulp.LpVariable.dicts(
    "RegularShift",
    (nurses_list, days, shifts),
    cat=pulp.LpBinary  # Must be 0 or 1
)

# Continuous variable: number of emergency staff for shift k on day j in scenario ω
alpha = pulp.LpVariable.dicts(
    "EmergencyStaff",
    (days, shifts, scenarios),
    lowBound=0,  # Cannot be negative
    cat=pulp.LpContinuous  # Can be fractional
)
```

### Constraint Example
```python
# CONSTRAINT: At most one shift per nurse per day
for nurse in nurses_list:
    for day in days:
        prob += (
            pulp.lpSum(sr[nurse][day][shift] + so[nurse][day][shift] 
                      for shift in shifts) <= 1,
            f"OneShiftPerDay_{nurse}_{day}"
        )
```

### Objective Function
```python
# Minimize total cost
prob += (
    # Stage 1: Regular and overtime wages
    c1 * pulp.lpSum(sr[i][j][k] for all i,j,k) +
    c2 * pulp.lpSum(so[i][j][k] for all i,j,k) +
    
    # Soft penalties
    c3 * pulp.lpSum(dev1[i][j] for all i,j) +
    c4 * pulp.lpSum(dev2[i][j][k] for all i,j,k) +
    
    # Stage 2: Expected recourse cost
    pulp.lpSum(prob[ω] * (q_plus * alpha[j][k][ω] + 
                          q_minus * beta[j][k][ω]) for all j,k,ω)
)
```

---

## 📈 Performance Considerations

### Problem Size Scaling

| Nurses | Days | Scenarios | Variables | Constraints | Solve Time |
|--------|------|-----------|-----------|-------------|------------|
| 10     | 14   | 10        | ~3,000    | ~4,000      | 1-2 sec    |
| 20     | 28   | 50        | ~18,500   | ~23,000     | 8-15 sec   |
| 30     | 28   | 100       | ~50,000   | ~65,000     | 30-60 sec  |
| 50     | 28   | 200       | ~180,000  | ~230,000    | 3-10 min   |

### Optimization Strategies

**1. Solver Choice:**
- HiGHS: Best for most problems (default)
- CBC: Fallback if HiGHS unavailable
- Gurobi: Best for large problems (requires license)

**2. MIP Gap Tolerance:**
- Small problems: 0% gap (optimal solution)
- Medium problems: 1% gap (near-optimal, faster)
- Large problems: 5% gap (good solution, much faster)

**3. Time Limits:**
- Set based on problem size
- Prevents excessive computation
- Returns best solution found so far

---

## 🐛 Common Issues & Solutions

### Issue 1: Infeasible Solution
**Cause:** Constraints too tight (impossible to satisfy all)

**Solutions:**
- Reduce n₃ (minimum regular shifts)
- Reduce n₄ (minimum weekends off)
- Increase μ (CVaR tolerance)
- Add more nurses

### Issue 2: Very High Costs
**Cause:** Heavy reliance on emergency staff

**Solutions:**
- Increase q⁺ (make emergency more expensive)
- Lower n₃ (allow more flexible scheduling)
- Check if demand is realistic

### Issue 3: Slow Solving
**Cause:** Problem too large

**Solutions:**
- Reduce number of scenarios (50 → 20)
- Reduce planning horizon (28 → 14 days)
- Increase MIP gap tolerance (0% → 5%)
- Use Gurobi instead of CBC

---

## 📖 References

### Research Paper
He, F., Chaussalet, T., & Qu, R. (2019). *Controlling understaffing with conditional Value-at-Risk constraint for an integrated nurse scheduling problem under patient demand uncertainty.* Operations Research Perspectives, 6, 100119.

### Mathematical Formulation
See `docs/mathematical_model.tex` for complete LaTeX equations

### Constraint Details
See `docs/CONSTRAINTS_GUIDE.md` for explanation of all 22 constraints

### Advanced Features
See `docs/ADVANCED_CONSTRAINTS.md` for shift quotas, patterns, etc.

---

## 🎓 For the Team

### What Makes This Implementation Special

1. **Two-Stage Stochastic Programming**
   - Not just "schedule for average demand"
   - Handles uncertainty with multiple scenarios
   - Optimizes expected cost across all possibilities

2. **CVaR Risk Management**
   - Controls worst-case outcomes
   - Ensures reliability even in high-demand scenarios
   - Balances cost vs. service quality

3. **Comprehensive Constraints**
   - 22 different constraint types
   - Labor laws compliance
   - Quality of life for nurses
   - Operational requirements

4. **Production-Ready Interface**
   - No coding required to use
   - Visual parameter tuning
   - Interactive result exploration
   - One-click Excel export

### Skills Demonstrated

- ✅ Mathematical optimization modeling
- ✅ Stochastic programming under uncertainty
- ✅ Large-scale integer programming
- ✅ Data engineering (ETL pipelines)
- ✅ Web application development
- ✅ Software architecture design
- ✅ Performance optimization
- ✅ User interface design
- ✅ Technical documentation

---

**Questions?** Check the code comments - every function and constraint is documented!
