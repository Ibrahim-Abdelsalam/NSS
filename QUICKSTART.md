# Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Launch the Application

```bash
streamlit run app.py
```

Your browser will automatically open to `http://localhost:8501`

### Step 3: Run Your First Optimization

1. **In the sidebar**, select "Use Sample Data (Quick Start)"
2. Click the **"🎲 Generate Sample Data"** button
3. Scroll down and click **"▶️ RUN OPTIMIZATION"**
4. Wait 10-30 seconds for the optimization to complete
5. Explore the results in the tabs!

## 📊 What the Tabs Show

### Tab 1: Nurse Roster
- Complete work schedule for each nurse
- Each cell shows: E (Early), D (Day), L (Late), N (Night), or OFF
- (OT) suffix indicates overtime

### Tab 2: Cost Analysis
- Total optimization cost
- Breakdown of regular wages, overtime, and emergency costs
- Visual pie chart and bar charts

### Tab 3: Coverage Analysis
- How many nurses are assigned to each shift each day
- Ensures demand is met

### Tab 4: Risk Assessment
- Statistics on potential understaffing
- CVaR metrics (if using risk-aware model)

### Tab 5: Scenario Comparison
- How the schedule performs across different demand scenarios
- Shows where shortages might occur

### Tab 6: Full Report
- Comprehensive text summary
- Downloadable reports

## 🎯 Try Different Scenarios

### Experiment 1: Compare Models

1. Run with **"Cost Optimization (SDM)"**
2. Note the total cost
3. Re-run with **"Risk-Aware with CVaR (SDM-CVaR)"**
4. Compare costs and shortage statistics

### Experiment 2: Adjust Costs

- Increase the emergency shift cost (q⁺) to 500
- See how the model tries harder to avoid shortages
- Observe changes in overtime usage

### Experiment 3: Tighten Constraints

- Reduce max total shifts (n₁) to 12
- See how this affects costs and shortages

### Experiment 4: More Uncertainty

- Increase number of scenarios to 10 or 20
- Observe how the model becomes more conservative

## 📁 Using Your Own Data

### Nurse List Format

Create `my_nurses.csv`:
```
Alice Johnson
Bob Smith
Carol White
David Brown
Emma Davis
```

### Demand Scenarios Format

Create `my_scenarios.csv` with columns:
- `scenario`: Integer scenario ID (1, 2, 3, ...)
- `day`: Day number (1, 2, 3, ...)
- `shift`: Shift type (E, D, L, N)
- `demand`: Number of nurses needed (integer)

Example:
```csv
scenario,day,shift,demand
1,1,E,3
1,1,D,5
1,1,L,4
1,1,N,2
...
```

Then upload both files in the sidebar!

## 💡 Tips & Tricks

### Performance
- Start small (10 nurses, 14 days, 5 scenarios)
- Larger problems take longer but give more robust solutions

### Understanding CVaR
- σ = 0.95 means "protect against worst 5% of scenarios"
- μ = 5.0 means "limit worst-case shortage to 5 shifts"
- Higher σ = more conservative
- Lower μ = stricter risk control

### Cost Parameters
- Set q⁺ (emergency cost) > c₂ (overtime cost) > c₁ (regular cost)
- This creates the right incentive structure

### Work Rules
- If model is infeasible, try relaxing constraints
- Common culprits: n₃ too high, n₁ too low

## ⚠️ Troubleshooting

### "No optimal solution found"
- Reduce minimum shifts (n₃)
- Increase maximum shifts (n₁)
- Add more nurses
- Reduce demand

### "Taking too long to solve"
- Reduce number of scenarios
- Reduce planning period
- Reduce number of nurses
- Consider using sample data first

### Import errors
```bash
pip install --upgrade -r requirements.txt
```

## 🎓 Learn More

### Understanding the Math
The system solves:
```
minimize: regular_wages + overtime_wages + expected_emergency_costs
subject to:
  - One shift per nurse per day
  - Min/max shift constraints
  - Demand must be met (with recourse)
  - CVaR risk limits (optional)
```

### Two-Stage Stochastic Programming
- **Stage 1**: Make baseline schedule (before knowing actual demand)
- **Stage 2**: Adjust with emergency staff (after seeing actual demand)

### Why Multiple Scenarios?
Real patient demand is uncertain. By considering multiple possible scenarios, we create a schedule that works well on average while controlling worst-case risk.

## 🎉 Next Steps

- Try different parameter combinations
- Upload your own hospital data
- Compare SDM vs SDM-CVaR models
- Experiment with risk parameters
- Download and analyze the reports

## 📞 Need Help?

Check the full README.md for comprehensive documentation!

Happy scheduling! 🩺
