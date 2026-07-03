# Real-World Data for NSS (Nurse Scheduling System)

This folder contains **real-world data and converters** for testing the NSS optimization model with genuine demand uncertainty, as close as possible to the ORTEC data used in He et al. (2019).

---

## 📁 Folder Structure

```
real_world_data/
├── 📊 RAW DATA SOURCES
│   ├── PBJ_nurse_staffing_2024Q1.csv  # ⭐ ACTUAL NURSE HOURS (CMS)
│   ├── pbj_sample_100k.csv            # Sample for quick testing
│   ├── covid_hospital.json            # US hospital bed data
│   ├── covid_hospital_ca.json         # California bed data
│   └── benchmark_instances/           # Academic benchmark problems
│
├── 🔧 CONVERTER SCRIPTS
│   ├── convert_pbj_nurses.py          # ⭐ BEST: Real nurse hours → NSS
│   ├── convert_real_demand.py         # Bed proxy → NSS
│   └── convert_benchmark_to_nss.py    # Benchmarks → NSS
│
├── ✅ READY-TO-USE (Real Nurse Hours) ⭐ RECOMMENDED
│   ├── pbj_california_nurses.csv      # 43 nurses
│   └── pbj_california_scenarios.csv   # 25 scenarios from REAL staffing
│
├── ✅ READY-TO-USE (Bed Proxy)
│   ├── real_california_nurses.csv     # 37 nurses
│   └── real_california_scenarios.csv  # 25 scenarios from bed occupancy
│
└── ✅ READY-TO-USE (Benchmark/Synthetic)
    ├── benchmark3_*.csv               # 20 nurses (small)
    ├── benchmark8_*.csv               # 30 nurses (medium)
    └── benchmark10_*.csv              # 40 nurses (large)
```

---

## ⭐ RECOMMENDED: PBJ Nurse Staffing Data

### What It Is

**CMS Payroll Based Journal (PBJ)** - actual nurse hours worked at US nursing facilities, reported quarterly to the federal government.

### `pbj_california_*.csv` 

| Property | Value |
|----------|-------|
| **Data Type** | ⭐ **ACTUAL NURSE HOURS** |
| **Facility** | Bridgewood Post Acute (California) |
| **Period** | January - March 2024 |
| **Nurses** | 43 |
| **Scenarios** | 25 (from different time windows) |
| **Horizon** | 28 days |
| **Shifts** | E (Early), D (Day), L (Late), N (Night) |
| **CV (Coefficient of Variation)** | 8-13% (realistic for staffing) |

### Why This Is Better

| Previous (Bed Proxy) | **Now (Nurse Hours)** |
|----------------------|----------------------|
| Beds occupied | **Hours worked by RN, LPN, CNA** |
| Indirect estimate | **Direct measurement** |
| State aggregate | **Single facility** |
| CV: 19.5% (high) | **CV: 8-13% (realistic)** |

### Example of Real Variation

For **Day 10, Shift D** (Day shift):
```
Scenario 1:  8 nurses actually scheduled
Scenario 5:  7 nurses actually scheduled  
Scenario 7:  9 nurses actually scheduled
```

This variation reflects **real staffing decisions** made at the facility.

---

## 📄 Converter Scripts

### 1. `convert_pbj_nurses.py` ⭐ RECOMMENDED

Converts CMS PBJ nurse staffing data to NSS format.

**Usage**:
```bash
python convert_pbj_nurses.py \
    --input PBJ_nurse_staffing_2024Q1.csv \
    --output my_scenarios \
    --state CA \
    --size medium \
    --scenarios 30 \
    --days 28
```

**Options**:
| Flag | Description | Default |
|------|-------------|---------|
| `--input` | PBJ CSV file | PBJ_nurse_staffing_2024Q1.csv |
| `--output` | Output prefix | pbj_real |
| `--state` | Filter to state (CA, TX, NY...) | Any |
| `--size` | Facility size: small/medium/large | medium |
| `--scenarios` | Number of scenarios | 20 |
| `--days` | Planning horizon | 28 |

### 2. `convert_real_demand.py`

Converts hospital bed occupancy to NSS format (proxy method).

### 3. `convert_benchmark_to_nss.py`

Converts academic benchmarks to NSS format (synthetic variation).

---

## 🎯 Which Data to Use?

| Goal | Recommended Data | Uncertainty Type |
|------|------------------|------------------|
| **Research publication** | `pbj_california_*` ⭐ | Real nurse hours |
| **Methodology validation** | `pbj_california_*` ⭐ | Real nurse hours |
| **Quick testing** | `benchmark3_*` | Synthetic |
| **Scalability testing** | `benchmark10_*` | Synthetic |

---

## 📈 Comparison of Data Sources

| Aspect | PBJ (Nurse Hours) ⭐ | Bed Proxy | Synthetic |
|--------|---------------------|-----------|-----------|
| **Measures** | RN + LPN + CNA hours | Beds occupied | Random ±15% |
| **Source** | CMS federal data | healthdata.gov | Generated |
| **Facility Level** | Single nursing home | State aggregate | N/A |
| **CV Range** | 8-13% | ~20% | ~8-10% |
| **Research Validity** | ⭐ Highest | Medium | Lower |
| **Closest to Paper** | ⭐ Yes | Partial | No |

---

## 🔗 Data Sources & Citations

1. **CMS PBJ Nurse Staffing** ⭐
   - https://data.cms.gov/quality-of-care/payroll-based-journal-daily-nurse-staffing
   - Contains actual nurse hours (RN, LPN, CNA) + patient census
   - 15,000+ nursing facilities, quarterly updates
   - License: Public Domain

2. **Hospital Bed Capacity**:
   - https://healthdata.gov/Hospital/COVID-19-Reported-Patient-Impact-and-Hospital-Capa/g62h-syeh
   - Daily bed occupancy (proxy for nurse demand)

3. **Benchmark Instances**:
   - https://www.schedulingbenchmarks.org/nrp/

4. **Reference Paper**:
   - He, F. et al. (2019). "Controlling understaffing with conditional Value-at-Risk constraint..."
   - DOI: 10.1016/j.orp.2019.100119
