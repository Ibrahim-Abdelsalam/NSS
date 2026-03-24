# 📊 Real Data Sources for Nurse Scheduling Research

Since the hospital doesn't have historical data, here are **publicly available real datasets** you can use.

---

## 🥇 Recommended: Scheduling Benchmarks (Already Downloaded!)

**Source:** https://www.schedulingbenchmarks.org/nrp/

**Status:** ✅ Downloaded to `data/benchmark_instances/`

### What's Included
| Instance | Nurses | Days | Shifts | Complexity |
|----------|--------|------|--------|------------|
| Instance1 | 8 | 14 | 1 | Very Small |
| Instance2 | 14 | 14 | 2 | Small |
| Instance3 | 20 | 14 | 3 | Small |
| Instance4-7 | 10-20 | 28 | 2-3 | Medium |
| **Instance8** | **30** | **28** | **4** | **Medium (Recommended)** |
| Instance9-13 | 36-120 | 28 | 4-18 | Large |
| Instance14-24 | 20-150 | 42-364 | 3-32 | Very Large |

### How to Use
```bash
cd /Users/ibrahim/Documents/GitHub/NSS/data
python convert_benchmark_to_nss.py --instance 8 --scenarios 20
```

This generates:
- `benchmark8_nurses.csv` (30 nurses)
- `benchmark8_scenarios.csv` (2240 demand records)

### Advantages
- ✅ **Real-world based** - designed by operations research experts
- ✅ **Complete** - includes all constraints (shifts, rotations, weekends)
- ✅ **Validated** - published solutions available for comparison
- ✅ **Already converted** - works with your NSS system

---

## 🏥 Government Healthcare Data (US)

### 1. Payroll Based Journal Daily Nurse Staffing
**Source:** https://healthdata.gov/d/4p48-axvp

**What it contains:**
- Daily nurse staffing hours by nursing home facility
- Staff categories: RN, LPN, CNA, etc.
- Daily patient census
- Quarterly updates

**Format:** CSV download available

**How to use:**
```python
import pandas as pd
# Download from healthdata.gov
df = pd.read_csv('pbj_daily_nurse_staffing.csv')
# Convert hours to nurse counts: hours / 8 = FTE nurses
df['nurses_needed'] = df['hours'] / 8
```

### 2. California Hospital Staffing (2009-2013)
**Source:** https://healthdata.gov/d/n6u8-qvp7

**What it contains:**
- Hours worked by employee classification
- By hospital cost center
- Adjusted patient days

### 3. New York State Hospital Bed Capacity
**Source:** https://healthdata.gov/d/cvrn-b3j2

**What it contains:**
- Operational, occupied, available staffed beds
- Daily updates
- Facility-level data

**Updated:** March 2026 (current!)

### 4. COVID-19 Hospital Capacity (Historical)
**Source:** https://healthdata.gov/d/anag-cw7u

**What it contains:**
- Daily staffed beds (ICU and general)
- Bed utilization percentages
- Staffing shortage indicators
- 2020-2024 data (great for capturing variation!)

---

## 📚 Academic Benchmark Instances

### ORTEC Benchmark
**Source:** https://www.schedulingbenchmarks.org (included in download)
- 16 employees
- 31 days
- 4 shift types
- Real hospital constraints

### GPOST Benchmark
- 8 employees
- 28 days (4 weeks)
- 3 shift types
- Simpler constraints, good for testing

### Ikegami Instances
- 25-28 employees
- 30 days
- Skill-based coverage requirements
- More complex than ORTEC

---

## 🔄 How to Generate Scenarios from Real Data

Since benchmark data is **deterministic** (single demand per day/shift), convert to **stochastic scenarios**:

### Method 1: Historical Periods as Scenarios
```python
# If you have 12 months of data:
# Each month (28-30 days) becomes one scenario
for month in range(1, 13):
    scenario_data = historical_df[historical_df['month'] == month]
    # Renumber days 1-28
```

### Method 2: Add Stochastic Variation
```python
# Add ±15% random variation to base demand
import numpy as np
for scenario in range(1, num_scenarios + 1):
    variation = np.random.uniform(-0.15, 0.15)
    demand = base_demand * (1 + variation)
```

### Method 3: Bootstrap from Real Data
```python
# Randomly sample from historical observations
for scenario in range(num_scenarios):
    for day in days:
        for shift in shifts:
            historical_samples = df[(df['shift']==shift)]['demand']
            demand = np.random.choice(historical_samples)
```

---

## 📥 Quick Download Commands

### Scheduling Benchmarks (Done!)
```bash
curl -L -o instances.zip https://www.schedulingbenchmarks.org/nrp/data/instances1_24.zip
unzip instances.zip
```

### HealthData.gov Datasets
```bash
# PBJ Daily Nurse Staffing
curl -o pbj_staffing.csv "https://data.cms.gov/provider-data/sites/default/files/resources/[FILE_ID]/PBJ_Daily_Nurse_Staffing.csv"

# NY Hospital Capacity
curl -o ny_beds.csv "https://health.data.ny.gov/api/views/cvrn-b3j2/rows.csv"
```

---

## 📊 Data Comparison

| Source | Type | Real Hospital Data? | Stochastic? | Size |
|--------|------|---------------------|-------------|------|
| **Benchmarks (Downloaded)** | Academic | Based on real patterns | Deterministic | 8-150 nurses |
| PBJ Nurse Staffing | Government | Yes (nursing homes) | Historical | 15,000+ facilities |
| NY Bed Capacity | Government | Yes (NY hospitals) | Time series | 200+ hospitals |
| COVID Capacity | Government | Yes (ICU focus) | Time series | National |

---

## 🎯 Recommendation for Your Research

**Use the benchmark instances** because:

1. ✅ **Already formatted** - the converter script is ready
2. ✅ **Research-standard** - allows comparison with published papers  
3. ✅ **Complete constraints** - includes all work rules
4. ✅ **Multiple sizes** - test small to large instances
5. ✅ **Published solutions** - verify your model correctness

**For the CVaR risk model**, generate 20-50 stochastic scenarios from the deterministic benchmark using the variation method—this matches the paper's methodology.

---

## 📁 Files Created

```
data/
├── benchmark_instances/
│   └── instances1_24/
│       ├── Instance1.txt ... Instance24.txt  (raw benchmark)
│       └── Instance1.ros ... Instance24.ros  (XML format)
├── convert_benchmark_to_nss.py  (converter script)
├── benchmark8_nurses.csv        (NSS format - 30 nurses)
└── benchmark8_scenarios.csv     (NSS format - 20 scenarios)
```

Ready to use with your app!
