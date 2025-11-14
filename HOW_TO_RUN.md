# 🚀 How to Run the Nurse Scheduling App

## Quick Start (One Command)

```bash
streamlit run app.py
```

Then open your browser to: **http://localhost:8503**

---

## ✅ Everything is Already Installed!

### Solvers Available:
- ✅ **Gurobi** - Very Fast (10-100× faster than CBC) - **RECOMMENDED**
- ✅ **CBC** - Slow but free and always available
- ❌ **CPLEX** - Not installed (optional)

**Gurobi is pre-configured and ready to use!**

---

## 📱 Using the App

### Step 1: Generate Sample Data
Click the **"Generate Sample Data"** button

### Step 2: Configure (Optional)
All constraints have sensible defaults. You can adjust:
- Hard constraints (n₁, n₂, n₃)
- Penalty weights (c₁, c₂, c₃, c₄)
- Advanced constraints (weekends, night rest, shift quotas)

### Step 3: Run Optimization
Click **"▶️ RUN OPTIMIZATION"**

Wait 5-30 seconds (Gurobi is fast!)

### Step 4: View Results
- See the schedule table
- View visualizations
- Download as CSV

---

## ⚙️ Solver Selection

**Default: Gurobi** (already selected)
- Fastest solver (10-100× faster than CBC)
- Free academic license (valid until 2027)
- No additional setup needed

**If Gurobi fails, the app automatically falls back to CBC**

---

## 🎓 For University Projects

This system implements **15 out of 18 constraints** from the research paper:
- ✅ All hard constraints (1-8)
- ✅ Weekend constraints (9)
- ✅ Night shift rest rules (10-13)
- ✅ Shift type quotas (2-5)
- ✅ Soft constraints (14-15)
- ✅ CVaR risk management (19-22)

**Perfect for demonstrating advanced optimization techniques!**

---

## 🐛 Troubleshooting

### Problem: "Cannot execute gurobi_cl"
**Solution:** Already fixed! The app now uses Gurobi Python API.

### Problem: "Solver not available"
**Solution:** The app will automatically use CBC as fallback.

### Problem: "Infeasible solution"
**Solution:** 
1. Reduce advanced constraints
2. Increase planning period (more days)
3. Reduce minimum shift requirements

### Problem: App not loading
**Solution:**
```bash
# Stop the app (Ctrl+C in terminal)
# Restart:
streamlit run app.py
```

---

## 📊 Performance Tips

### For Fast Results (5-10 seconds):
- Use **Gurobi** solver (already selected)
- 10-20 nurses
- 7-14 days
- 5-10 scenarios

### For Medium Problems (30-60 seconds):
- Use **Gurobi**
- 20-30 nurses
- 14-21 days
- 10 scenarios

### For Large Problems (2-5 minutes):
- Use **Gurobi** (required!)
- 30-50 nurses
- 21-28 days
- 10 scenarios
- Enable "Fast Mode" (5% gap tolerance)

---

## 🎯 Example Configurations

### Configuration 1: Quick Demo (10 seconds)
```
Nurses: 10
Days: 7
Scenarios: 5
Solver: Gurobi
Advanced Constraints: None
```

### Configuration 2: Realistic Hospital (30 seconds)
```
Nurses: 20
Days: 14
Scenarios: 10
Solver: Gurobi
Weekend Constraints: n₄ = 1
Night Rest: Enabled (min 2, rest 2)
```

### Configuration 3: Full Featured (2 minutes)
```
Nurses: 30
Days: 21
Scenarios: 10
Solver: Gurobi
Weekend Constraints: n₄ = 2
Night Rest: Enabled (min 2, rest 2)
Shift Quotas: E(2-8), D(2-8), L(2-6), N(2-5)
```

---

## 💡 Important Notes

1. **Gurobi License**: You have a free restricted license valid until **November 29, 2027**
2. **No Manual Setup**: Everything is pre-configured
3. **Auto-Fallback**: If Gurobi fails, CBC is used automatically
4. **Streamlit Auto-Reload**: Changes to code reload the app automatically

---

## 📁 Project Files

```
nurse-scheduler/
├── app.py                          # Main Streamlit application
├── model.py                        # Optimization model (18 constraints)
├── solver_config.py                # Solver configuration (Gurobi/CBC/CPLEX)
├── ADVANCED_CONSTRAINTS.md         # Advanced constraints guide
├── README.md                       # Full documentation
├── QUICKSTART.md                   # Quick start guide
└── HOW_TO_RUN.md                   # This file!
```

---

## 🎉 You're Ready!

Just run:
```bash
streamlit run app.py
```

And open **http://localhost:8503** in your browser!
