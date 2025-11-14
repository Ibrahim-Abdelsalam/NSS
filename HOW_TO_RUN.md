# 🚀 How to Run the Nurse Scheduling App

## Quick Start (One Command)

```bash
streamlit run app.py
```

Then open your browser to: **http://localhost:8503**

---

## ✅ Everything is Already Installed!

### Solvers:
- ✅ **Automatic Selection** - The system picks the best available solver
- ✅ **HiGHS** - Fast & Free (3-5× faster than CBC) - Preferred
- ✅ **CBC** - Fallback option (always available)

**The app automatically detects and uses the fastest solver available!**

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

Wait 5-30 seconds (HiGHS is fast!)

### Step 4: View Results
- See the schedule table
- View visualizations
- Download as CSV

---

## ⚙️ Automatic Solver Selection

**The app automatically picks the best solver** - no configuration needed!

**Priority:**
1. **HiGHS** - Fast, free, open-source (if installed)
2. **CBC** - Reliable fallback (always available)

**No manual selection required** - the framework chooses automatically!

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

### Problem: "Solver taking too long"
**Solution:** The app automatically uses HiGHS if available. If you only have CBC, install HiGHS: `pip install highspy`

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
- HiGHS automatically selected (if installed)
- 10-20 nurses
- 7-14 days
- 5-10 scenarios

### For Medium Problems (30-60 seconds):
- HiGHS automatically selected (if installed)
- 20-30 nurses
- 14-21 days
- 10 scenarios

### For Large Problems (2-5 minutes):
- HiGHS automatically selected (if installed)
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
Solver: Auto (HiGHS preferred)
Advanced Constraints: None
```

### Configuration 2: Realistic Hospital (30 seconds)
```
Nurses: 20
Days: 14
Scenarios: 10
Solver: Auto (HiGHS preferred)
Weekend Constraints: n₄ = 1
Night Rest: Enabled (min 2, rest 2)
```

### Configuration 3: Full Featured (2 minutes)
```
Nurses: 30
Days: 21
Scenarios: 10
Solver: Auto (HiGHS preferred)
Weekend Constraints: n₄ = 2
Night Rest: Enabled (min 2, rest 2)
Shift Quotas: E(2-8), D(2-8), L(2-6), N(2-5)
```

---

## 💡 Important Notes

1. **Automatic Solver Selection**: The system picks the best free solver automatically
2. **HiGHS Preferred**: If installed, HiGHS is automatically used (3-5× faster than CBC)
3. **No Manual Setup**: Everything works out of the box
4. **Auto-Fallback**: If HiGHS isn't installed, CBC is used automatically
5. **Streamlit Auto-Reload**: Changes to code reload the app automatically

---

## 📁 Project Files

```
nurse-scheduler/
├── app.py                          # Main Streamlit application
├── model.py                        # Optimization model (18 constraints)
├── solver_config.py                # Automatic solver selection framework
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
