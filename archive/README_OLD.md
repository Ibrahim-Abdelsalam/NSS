# 🩺 Nurse Scheduling Optimization System

A sophisticated web-based prototype for solving the **Integrated Nurse Staffing and Scheduling Problem** under patient demand uncertainty using **Two-Stage Stochastic Integer Programming** with optional **Conditional Value-at-Risk (CVaR)** constraints.

## 📋 Overview

This system addresses the complex challenge of creating optimal nurse work schedules while:
- Minimizing total staffing costs (regular wages, overtime, emergency shifts)
- Respecting labor regulations and work rules
- Managing uncertainty in patient demand
- Controlling worst-case understaffing risks (optional CVaR model)

### Mathematical Foundation

The system implements two optimization models:

1. **SDM (Stochastic Demand Model)**: Cost-minimizing two-stage stochastic program
2. **SDM-CVaR**: Risk-aware variant with CVaR constraints to limit tail risk

Both models make:
- **Stage 1 (Here-and-Now) Decisions**: Baseline nurse schedule before demand is known
- **Stage 2 (Recourse) Decisions**: Adjustments after uncertain demand is realized

## 🚀 Features

### Core Functionality
- ✅ **Interactive Web Interface** - User-friendly Streamlit dashboard
- ✅ **Flexible Data Input** - Upload custom data or use generated samples
- ✅ **Dual Optimization Models** - Choose between cost-focused or risk-aware optimization
- ✅ **Comprehensive Reporting** - Detailed cost, coverage, and risk analytics

### Optimization Capabilities
- 📊 **Multi-Scenario Planning** - Handles uncertain patient demand across multiple scenarios
- 💰 **Cost Optimization** - Minimizes regular wages, overtime, and emergency staffing costs
- ⚖️ **Work Rule Compliance** - Enforces max shifts, min shifts, night shift limits, etc.
- 🛡️ **Risk Management** - CVaR constraints protect against worst-case shortages

### Reporting & Visualization
- 📅 **Nurse Rosters** - Complete work schedules with shift assignments
- 💵 **Cost Breakdown** - Stage 1 and Stage 2 cost analysis
- 📈 **Coverage Analysis** - Daily staffing levels by shift type
- ⚠️ **Risk Assessment** - Shortage distributions and CVaR metrics
- 📊 **Interactive Charts** - Plotly visualizations for all key metrics
- 📄 **Downloadable Reports** - CSV and TXT export for all results

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone or download this repository**
```bash
cd /Users/ibrahim/Desktop/nurse-scheduler
```

2. **Create a virtual environment (recommended)**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## 🎮 Usage

### Running the Application

Start the Streamlit web application:

```bash
streamlit run app.py
```

The application will open in your default web browser (typically at `http://localhost:8501`).

### Quick Start Guide

#### Option 1: Using Sample Data (Recommended for First Time)

1. In the left sidebar, select **"Use Sample Data (Quick Start)"**
2. Configure the number of nurses (5-50), planning days (7-30), and scenarios (3-20)
3. Click **"🎲 Generate Sample Data"**
4. Adjust cost parameters and work rules as desired
5. Select an optimization model (SDM or SDM-CVaR)
6. Click **"▶️ RUN OPTIMIZATION"**

#### Option 2: Using Custom Data

1. In the left sidebar, select **"Upload Custom Data"**
2. Prepare two CSV files:

**Nurse List File** (`nurses.csv`):
```csv
Alice
Bob
Carol
David
Emma
```

**Demand Scenarios File** (`scenarios.csv`):
```csv
scenario,day,shift,demand
1,1,E,3
1,1,D,4
1,1,L,3
1,1,N,2
1,2,E,3
...
```

3. Upload both files
4. Configure parameters and run optimization

### Understanding the Results

#### Tab 1: Nurse Roster
- Complete work schedule for each nurse
- Summary statistics (total shifts, overtime, nights)
- Downloadable CSV format
- Interactive heatmap visualization

#### Tab 2: Cost Analysis
- Stage 1 costs (regular and overtime wages)
- Stage 2 expected recourse costs
- Cost distribution pie chart
- Shift allocation breakdown

#### Tab 3: Coverage Analysis
- Assigned nurses by day and shift
- Coverage heatmap
- Comparison against demand

#### Tab 4: Risk Assessment
- Shortage statistics across scenarios
- CVaR metrics (if SDM-CVaR model used)
- Distribution plots

#### Tab 5: Scenario Comparison
- Scenario-by-scenario shortage/overage analysis
- Recourse cost breakdown
- Downloadable detailed data

#### Tab 6: Full Report
- Executive summary
- Complete textual report
- Downloadable TXT format

## 📊 Model Parameters

### Cost Parameters
- **c₁**: Regular shift cost ($/shift)
- **c₂**: Overtime shift cost ($/shift)
- **q⁺**: Emergency shift cost ($/shift)

### Work Rules (Hard Constraints)
- **n₁**: Maximum total shifts per nurse
- **n₂**: Maximum night shifts per nurse
- **n₃**: Minimum regular shifts per nurse
- **n₄**: Minimum complete weekends off (⚠️ not fully implemented)

### CVaR Parameters (SDM-CVaR model only)
- **σ**: Confidence level (0.90-0.99)
- **μ**: Maximum acceptable shortage in worst-case scenarios

## 🧮 Mathematical Model

### Decision Variables

**Stage 1 Variables:**
- $sr_{ijk} \in \{0,1\}$: 1 if nurse $i$ works regular shift $k$ on day $j$
- $so_{ijk} \in \{0,1\}$: 1 if nurse $i$ works overtime shift $k$ on day $j$

**Stage 2 Variables:**
- $\alpha_{jk}^\omega \geq 0$: Number of emergency shifts added for scenario $\omega$ on day $j$, shift $k$
- $\beta_{jk}^\omega \geq 0$: Number of shifts cancelled for scenario $\omega$ on day $j$, shift $k$

### Objective Function

$$\min \quad c_1 \sum_{ijk} sr_{ijk} + c_2 \sum_{ijk} so_{ijk} + \sum_\omega p^\omega \sum_{jk} (q^+ \alpha_{jk}^\omega)$$

### Key Constraints

1. **One shift per day**: $\sum_k (sr_{ijk} + so_{ijk}) \leq 1 \quad \forall i,j$

2. **Max total shifts**: $\sum_{jk} (sr_{ijk} + so_{ijk}) \leq n_1 \quad \forall i$

3. **Max night shifts**: $\sum_j (sr_{ijN} + so_{ijN}) \leq n_2 \quad \forall i$

4. **Min regular shifts**: $\sum_{jk} sr_{ijk} \geq n_3 \quad \forall i$

5. **Demand satisfaction**: $\sum_i (sr_{ijk} + so_{ijk}) + \alpha_{jk}^\omega - \beta_{jk}^\omega \geq R_{jk}^\omega \quad \forall \omega,j,k$

6. **CVaR constraint** (SDM-CVaR only): $\xi + \frac{1}{1-\sigma} \sum_\omega p^\omega z^\omega \leq \mu$

## 🔧 Technical Details

### Solver
- **Default**: CBC (Coin-or Branch and Cut) - open-source, included with PuLP
- **Optional**: CPLEX or Gurobi (commercial solvers with academic licenses available)

### Performance
- Typical solve time: 10 seconds to 5 minutes depending on:
  - Number of nurses (5-50)
  - Planning period (7-30 days)
  - Number of scenarios (3-20)
  - Model type (SDM faster than SDM-CVaR)

### Scalability
- **Small instances** (10 nurses, 14 days, 5 scenarios): < 30 seconds
- **Medium instances** (20 nurses, 14 days, 10 scenarios): 1-3 minutes
- **Large instances** (50 nurses, 30 days, 20 scenarios): 5-15 minutes

## 📁 Project Structure

```
nurse-scheduler/
├── app.py                 # Streamlit web application
├── model.py              # Optimization model implementation
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── data/                # (Optional) Sample data files
    ├── nurses.csv
    └── scenarios.csv
```

## 🤝 Contributing

This is a research prototype. Suggestions for improvements:

### Potential Enhancements
- [ ] Implement complete weekend-off constraints (Eq. 9 from paper)
- [ ] Add soft constraints for shift pattern preferences
- [ ] Support for part-time nurses with custom availability
- [ ] Multi-week rolling planning horizon
- [ ] Forecast integration (ARIMA-based scenario generation)
- [ ] Fairness constraints (equitable shift distribution)
- [ ] Advanced visualizations (Gantt charts, etc.)

## 📚 References

This implementation is based on the research paper:

> **"Integrated Nurse Staffing and Scheduling with Conditional Value-at-Risk Constraints"**

Key concepts:
- Two-stage stochastic programming
- Scenario-based demand modeling
- CVaR for risk management in healthcare operations
- Integer programming for workforce scheduling

## ⚠️ Limitations

### Current Implementation
- Weekend constraints (n₄) are not fully implemented
- Soft constraints (stand-alone shifts, unwanted patterns) are omitted for simplicity
- No consecutive day-off requirements
- Limited to single facility/department

### Assumptions
- All scenarios are equally likely (uniform distribution)
- No nurse-specific skills or certifications
- Homogeneous shift types across days
- No mid-shift changes or split shifts

## 📝 License

This project is provided for educational and research purposes.

## 💡 Support

For issues, questions, or contributions, please refer to the project documentation or contact the development team.

## 🙏 Acknowledgments

- Built with [PuLP](https://coin-or.github.io/pulp/) optimization library
- Web interface powered by [Streamlit](https://streamlit.io/)
- Visualizations using [Plotly](https://plotly.com/)

---

**Version**: 1.0  
**Last Updated**: November 2025  
**Status**: Research Prototype
