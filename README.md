# FROST-NS 🏥📊

**Fatigue-Aware Risk Optimization for Stochastic Task Allocation in Nurse Scheduling**

An open-source, Python-based mathematical optimization framework designed to solve one of healthcare's hardest problems: scheduling nurses while balancing financial budgets, unpredictable patient demand, and dangerous nurse exhaustion.

---

## 📖 The Problem
Hospital ward managers must build next month's schedule without knowing exactly how many patients will arrive. 
* If they schedule too many nurses "just in case," the hospital wastes money.
* If they schedule too few, they must hire wildly expensive emergency agency nurses at the last minute.
* If they overwork their permanent staff to cover gaps, nurses suffer from burnout and fatigue, leading to medical errors.

**FROST-NS** solves this using advanced operations research: **Two-Stage Stochastic Mixed-Integer Linear Programming (MILP)** combined with **Conditional Value-at-Risk (CVaR)**.

---

## ✨ Core Mathematical Innovations

1. **Two-Stage Stochastic Optimization (The "Wedding Planner" Logic)**
   * **Stage 1 (Here-and-Now):** Assigns permanent nurses to Regular ($sr$) and Overtime ($so$) shifts *before* the month begins.
   * **Stage 2 (Wait-and-See):** Dynamically allocates Emergency Staff ($\alpha$) and cancels shifts ($\beta$) across dozens of simulated future disaster scenarios (e.g., flu outbreaks).

2. **The Fatigue Circuit Breaker (McCormick Envelopes)**
   * Instead of basic shift-counting, FROST-NS treats human energy like a battery. Working charges the "exhaustion battery"; resting drains it.
   * Because industrial solvers hate curves (non-linear math), the system uses **McCormick Envelopes** to mathematically linearize biological decay. If a schedule pushes a nurse's schedule-based fatigue proxy beyond a strict biological limit, the solver physically destroys that schedule and rebuilds it.

3. **Disaster Risk Control (CVaR)**
   * Optimizing for the "average" day will bankrupt a hospital when a pandemic hits. 
   * FROST-NS uses the **Rockafellar-Uryasev CVaR formulation** to isolate the absolute worst 5% of simulated scenarios, strictly capping the maximum allowable financial loss during extreme disasters.

---

## 📂 Repository Architecture

The codebase is strictly separated into mathematical processing, data extraction, and user interface rendering:

```text
/NSS/
├── core/                  # The Mathematical Brain
│   ├── _model_core.py     # 2,300+ line MILP engine (PuLP)
│   ├── scheduler.py       # Extracts raw solver 1s and 0s back into DataFrames
│   ├── validator.py       # Data integrity bouncer (catches negative demand, etc.)
│   └── solver_config.py   # Connects to industrial C++ solvers (HiGHS / CBC)
├── ui/                    # The Streamlit Dashboard
│   ├── upload_view.py     # CSV sanitization and ingestion
│   ├── sidebar.py         # Dynamic parameter injection
│   └── results_view.py    # Plotly heatmaps and ReportLab PDF generation
├── experiments/           # Automation for Academic Reproducibility
│   └── pipeline.py        # Automated parameter sweeping and baseline comparisons
├── data/                  # Synthetic proof-of-concept demand & nurse parameters
└── main.py                # Application entry point
```

---

## 🚀 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/NSS.git
   cd NSS
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure you have an optimization solver like HiGHS or CBC installed on your system. The code automatically detects available solvers via PuLP).*

3. **Run the Application:**
   ```bash
   streamlit run main.py
   ```
   This will launch the interactive web dashboard where you can upload CSVs, adjust fatigue limits, and visualize the optimized rosters.

---

## 🔬 Academic Research & Reproducibility
This repository serves as a **synthetic proof-of-concept** for researchers extending stochastic rostering models. 

**For Peer Reviewers & Researchers:**
* **Synthetic Demand Generation:** The `data/` folder contains generated instances reflecting $\pm10\%, 20\%, 30\%$ uniform demand variance across discrete scenarios.
* **Sensitivity Analysis:** Use the scripts in the `experiments/` directory to run automated batch-tests. The framework supports sweeping parameters for Fatigue limits ($F$), Workload limits ($W$), CVaR confidence levels ($\alpha$), and financial cost penalties to measure the trade-off between financial cost and clinical unmet demand.
* **Baseline Comparisons:** The solver hooks allow disabling CVaR or Fairness constraints to establish deterministic performance baselines.

---

## 📄 License
This project is open-source and available under the standard MIT License.
