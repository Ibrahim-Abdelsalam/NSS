# App.py Deep Dive - Complete Explanation

**File**: `app.py` (2,372 lines)  
**Purpose**: Streamlit web interface for FROST-NS nurse scheduling system

---

## Overview

`app.py` is the user-facing application split into **7 logical sections**:

1. **Setup & Configuration** (Lines 1-246) - Imports, CSS, page config
2. **Data Input & Validation** (Lines 247-490) - File upload or sample data
3. **Model Parameters** (Lines 491-800) - Cost, constraints, advanced settings
4. **Optimization Execution** (Lines 801-1360) - Solve and handle results  
5. **Results Visualization** (Lines 1361-1900) - Charts, tables, metrics
6. **Export & Download** (Lines 1901-2100) - CSV/JSON export functionality
7. **Additional Tools** (Lines 2101-2372) - Solver config, help sections

---

## Section 1: Setup & Configuration (Lines 1-246)

### Purpose
Configure Streamlit app and define visual styling - the "look and feel"

### Key Components

**Imports** (Lines 1-11):
```python
import streamlit as st         # Web framework
import pandas as pd            # Data tables
import plotly.express as px    # Interactive charts
import model as m              # Core optimization
from solver_config import get_available_solvers, recommend_solver
```

**Page Configuration** (Lines 14-19):
```python
st.set_page_config(
    page_title="Nurse Scheduler",
    page_icon="🩺",
    layout="wide",              # Use full screen width
    initial_sidebar_state="expanded"  # Show sidebar by default
)
```

**Custom CSS** (Lines 22-228):
```css
/* Main container with blue gradient */
.main {
    background: linear-gradient(to bottom, #e6f2ff 0%, #f0f8ff 100%);
    border-left: 4px solid #4299e1;
}

/* Large, prominent buttons */
.stButton > button {
    height: 4rem;
    font-size: 1.3rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Purple theme for dataframes */
.dataframe {
    --dataframe-header-bg: #6b46c1;
    --dataframe-header-color: white;
}
```

**Why Custom CSS?**
- Default Streamlit is basic - custom CSS makes it look professional
- Larger fonts/buttons improve usability
- Consistent color scheme (blue/purple) creates branded experience

**Session State Init** (Lines 238-244):
```python
if 'results' not in st.session_state:
    st.session_state.results = None  # Store optimization results
if 'prob' not in st.session_state:
    st.session_state.prob = None     # Store PuLP problem object
if 'num_scenarios' not in st.session_state:
    st.session_state.num_scenarios = 5  # Default scenario count
```

**Session State**: Streamlit reruns entire script on every interaction. Session state persists data between reruns.

---

## Section 2: Data Input & Validation (Lines 247-490)

### Purpose
Get nurse list and demand scenarios from user (upload or generate)

### Sidebar Structure

**Data Source Selection** (Lines 259-266):
```python
data_source = st.radio(
    "Choose data input method:",
    ["Use Sample Data (Quick Start)", "Upload Custom Data"]
)
```

### Path 1: Sample Data (Lines 267-293)

**UI Controls**:
```python
num_nurses = st.number_input("Number of Nurses", 1, 200, 10, 1)
num_days = st.number_input("Planning Period (days)", 1, 90, 14, 1)
num_scenarios = st.number_input("Demand Scenarios", 1, 100, 5, 1)

if st.button("🎲 Generate Sample Data", key="gen_sample"):
    nurses_list, scenarios_df = m.generate_sample_data(
        num_nurses, num_days, num_scenarios
    )
    # Store in session state
    st.session_state.nurses_list = nurses_list
    st.session_state.scenarios_df = scenarios_df
```

**Flow**:
1. User sets problem size
2. Clicks "Generate"
3. `model.generate_sample_data()` creates synthetic data
4. Data stored in session state
5. Success message shown

### Path 2: File Upload (Lines 295-490)

**UI Controls**:
```python
nurse_file = st.file_uploader(
    "Nurse List (CSV/TXT)",
    type=["csv", "txt"]
)
scenario_file = st.file_uploader(
    "Demand Scenarios (CSV)",
    type=["csv"]
)
```

**Robust Nurse File Parsing** (Lines 314-394):

Handles multiple formats gracefully:

**Format 1**: One name per line
```
Alice
Bob
Charlie
```

**Format 2**: Comma-separated single line
```
Alice, Bob, Charlie
```

**Format 3**: CSV with column
```
name
Alice
Bob
```

**Parsing Logic**:
```python
# Try 1: pandas CSV parsing
try:
    nurses_df = pd.read_csv(nurse_file, header=None)
    if nurses_df.shape[1] == 1:
        nurses_list = nurses_df.iloc[:, 0].tolist()
    else:
        nurses_list = flatten(nurses_df.values)
except:
    # Try 2: Raw text parsing
    raw_text = nurse_file.read().decode('utf-8')
    if ',' in raw_text and '\n' not in raw_text:
        nurses_list = [n.strip() for n in raw_text.split(',')]
    else:
        nurses_list = raw_text.strip().split('\n')
```

**Why so complex?** Real users upload in many formats. Robust parsing = better UX.

**Scenario File Validation** (Lines 411-480):

**Required Columns**:
- `scenario`: Scenario ID (1, 2, 3, ...)
- `day`: Day number (1-28)
- `shift`: Shift type ('E', 'D', 'L', 'N')
- `demand`: Number of nurses needed (≥ 0)

**Validation Checks**:
1. **Column presence**:
   ```python
   required = ['scenario', 'day', 'shift', 'demand']
   missing = set(required) - set(scenarios_df.columns)
   if missing:
       st.error(f"Missing columns: {missing}")
       st.stop()
   ```

2. **No missing values**:
   ```python
   nulls = scenarios_df.isnull().sum()
   if nulls.any():
       st.error("Missing values found!")
       st.stop()
   ```

3. **No negative demand**:
   ```python
   negative = scenarios_df[scenarios_df['demand'] < 0]
   if len(negative) > 0:
       st.error("Negative demand not allowed!")
       st.stop()
   ```

4. **Data completeness** (Lines 445-475):
   ```python
   expected_rows = num_scenarios × num_days × num_shifts
   actual_rows = len(scenarios_df)
   
   if abs(expected_rows - actual_rows) > expected_rows * 0.1:
       st.warning("Data appears incomplete - missing combinations")
   ```

**Duplicate Nurse Handling** (Lines 401-408):
```python
duplicates = [name for name in set(nurses_list) 
              if nurses_list.count(name) > 1]
if duplicates:
    st.warning(f"Duplicate names: {duplicates}")
    st.info("Automatically removing duplicates")
    # Remove duplicates, keep first occurrence
    seen = set()
    nurses_list = [x for x in nurses_list if not (x in seen or seen.add(x))]
    st.success(f"Cleaned to {len(nurses_list)} unique nurses")
```

**Output**: `nurses_list` and `scenarios_df` ready for optimization

---

## Section 3: Model Parameters (Lines 491-800)

### Purpose
Collect all model parameters from user through intuitive UI

### Cost Parameters (Lines 500-550)

**UI Layout**:
```python
st.subheader("💰 Cost Parameters")
col1, col2 = st.columns(2)

with col1:
    c1 = st.number_input(
        "Regular Shift Cost ($)",
        min_value=0, value=100, step=10,
        help="Cost per regular shift"
    )
    c2 = st.number_input(
        "Overtime Shift Cost ($)",
        min_value=0, value=150, step=10,
        help="Premium for overtime (typically 1.5x regular)"
    )

with col2:
    q_plus = st.number_input(
        "Emergency Hire Cost ($)",
        min_value=0, value=200, step=10,
        help="Emergency replacement cost (expensive!)"
    )
    q_minus = st.number_input(
        "Cancellation Penalty ($)",
        min_value=0, value=0, step=10,
        help="Cost to cancel scheduled nurse (paper uses $2)"
    )
```

**Parameter Relationships**:
- `c2 ≥ c1` (overtime should cost more than regular)
- `q_plus > c2` (emergency should be most expensive)
- Visual warnings if relationships violated

### Work Rules (Lines 551-620)

**Basic Constraints**:
```python
n1 = st.slider(
    "Max Total Shifts per Nurse",
    min_value=1, max_value=50, value=15,
    help="Total shifts allowed (regular + overtime)"
)

n2 = st.slider(
    "Max Night Shifts per Nurse",
    min_value=0, max_value=n1, value=5,
    help="Limit night shifts for health/safety"
)

n3 = st.slider(
    "Min Regular Shifts (if working regular)",
    min_value=0, max_value=n1, value=10,
    help="Minimum regular shifts quota"
)
```

**Shift Type Quotas** (Advanced, Lines 621-670):
```python
enable_shift_quotas = st.checkbox(
    "Enable per-shift-type quotas",
    help="Set min/max for each shift type (E, D, L, N)"
)

if enable_shift_quotas:
    shift_quotas = {}
    for shift in ['E', 'D', 'L', 'N']:
        col1, col2 = st.columns(2)
        with col1:
            min_val = st.number_input(f"Min {shift} shifts", 0, n1, 0)
        with col2:
            max_val = st.number_input(f"Max {shift} shifts", 0, n1, n1)
        
        shift_quotas[shift] = {'min': min_val, 'max': max_val}
```

### Model Type Selection (Lines 671-720)

**Radio Button**:
```python
model_type = st.selectbox(
    "Model Type",
    ["SDM", "SDM-CVaR"],
    help="SDM = standard, SDM-CVaR = with risk management"
)

if model_type == "SDM-CVaR":
    st.info("📊 CVaR manages worst-case risk")
    
    sigma = st.slider(
        "Confidence Level (σ)",
        min_value=0.80, max_value=0.99, value=0.95, step=0.01,
        help="95% means 'protect against worst 5% of scenarios'"
    )
    
    mu = st.number_input(
        "Max CVaR Threshold (μ)",
        min_value=0, value=50, step=5,
        help="Maximum acceptable shortage (NEW: default 50)"
    )
```

**CVaR Explanation Helper**:
```python
with st.expander("ℹ️ What is CVaR?"):
    st.markdown("""
    **Conditional Value-at-Risk (CVaR)** limits worst-case outcomes.
    
    - **σ=0.95**: Protects against worst 5% of scenarios
    - **μ=50**: Maximum 50 emergency hires in worst case
    
    **Effect**: More conservative schedule (uses more regular shifts upfront)
    """)
```

### Advanced Constraints (Lines 721-800)

**Overtime Mode** (Lines 730-750):
```python
allow_overtime_paradox = st.checkbox(
    "Allow Overtime Paradox (Paper Mode)",
    value=True,
    help="Uncheck for NSS Strict Mode (forces overtime usage)"
)

if not allow_overtime_paradox:
    st.info("✅ NSS Mode: Overtime will be used after regular quota met")
else:
    st.warning("⚠️ Paper Mode: Overtime likely unused (economic paradox)")
```

**Fatigue Modeling** (Lines 751-795):
```python
patient_safety_enabled = st.checkbox(
    "Enable Fatigue Modeling",
    value=False,
    help="Track nurse fatigue for patient safety (adds solve time)"
)

if patient_safety_enabled:
    max_fatigue_threshold = st.slider(
        "Max Fatigue Threshold",
        min_value=0.50, max_value=1.0, value=0.70, step=0.05,
        help="0.70 = moderate limit (recommended)"
    )
    
    patient_safety_weight = st.number_input(
        "Patient Safety Cost Weight",
        min_value=0, value=100, step=10,
        help="Penalty for high fatigue levels"
    )
    
    # Show warning if threshold too low
    if max_fatigue_threshold < 0.60:
        st.warning("⚠️ Very low threshold may cause infeasibility!")
```

**Weekend Off Constraints** (Lines 796-800):
```python
n4 = st.number_input(
    "Min Complete Weekends Off",
    min_value=0, max_value=10, value=0,
    help="0 = disabled. Set to 1-2 for work-life balance"
)
```

**Parameter Packaging** (Lines 800-850):
```python
model_params = {
    # Costs
    'c1': c1, 'c2': c2, 'q_plus': q_plus, 'q_minus': q_minus,
    
    # Work rules
    'n1': n1, 'n2': n2, 'n3': n3, 'n4': n4,
    
    # CVaR
    'sigma': sigma if model_type == "SDM-CVaR" else None,
    'mu': mu if model_type == "SDM-CVaR" else None,
    
    # Advanced
    'shift_quotas': shift_quotas if enable_shift_quotas else None,
    'patient_safety_enabled': patient_safety_enabled,
    'max_fatigue_threshold': max_fatigue_threshold if patient_safety_enabled else None,
    'allow_overtime_paradox': allow_overtime_paradox
}
```

---

## Section 4: Optimization Execution (Lines 801-1360)

### Purpose
Run optimization and handle all possible outcomes (success, error, infeasible)

### Pre-Optimization Validation (Lines 850-920)

**Parameter Validation**:
```python
errors, warnings = m.validate_parameters(
    model_params, nurses_list, scenarios_df
)

if errors:
    st.error("### ❌ Validation Errors - Cannot Proceed")
    for error in errors:
        st.error(error)
    st.stop()  # Don't run optimization

if warnings:
    st.warning("### ⚠️ Parameter Warnings")
    for warning in warnings:
        st.warning(warning)
```

**Examples of Validation Errors**:
- `c1 <= 0` → "Regular shift cost must be positive"
- `n2 > n1` → "Max night shifts cannot exceed max total shifts"
- `sigma` not in (0,1) → "CVaR confidence must be between 0 and 1"

### Solve Button & Progress (Lines 930-1000)

**"Optimize Schedule" Button**:
```python
if st.button("🚀 Optimize Schedule", type="primary", use_container_width=True):
    
    # Create progress indicator
    progress_placeholder = st.empty()
    progress_placeholder.info("⏳ Building optimization model...")
    
    # Timer
    import time
    start_time = time.time()
    
    try:
        # Call main optimization function
        prob, status = m.build_and_solve_model(
            nurses_list=nurses_list,
            scenarios_df=scenarios_df,
            model_params=model_params,
            model_type=model_type,
            solver_name=selected_solver
        )
        
        solve_time = time.time() - start_time
        progress_placeholder.empty()
        
    except MemoryError:
        st.error("❌ Out of Memory")
        st.warning("Solutions: Reduce nurses/days/scenarios or use bigger machine")
        st.stop()
    
    except Exception as e:
        st.error(f"❌ Solver Error: {e}")
        st.exception(e)  # Show full traceback
        st.stop()
```

**Progress Updates**:
- "Building model..." (0-1s)
- "Solving with {solver}..." (during solve)
- "Extracting results..." (after solve)

### Result Handling (Lines 1000-1150)

**Status: Optimal** (Lines 1010-1080):
```python
if status == "Optimal":
    st.success(f"✅ Optimal solution found in {solve_time:.2f}s!")
    
    # Extract comprehensive results
    results = m.extract_results(
        prob, nurses_list, scenarios_df, model_params
    )
    
    # Store in session state for other tabs
    st.session_state.results = results
    st.session_state.prob = prob
    
    # Show key metrics immediately
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Cost", f"${results['total_cost']:,.0f}")
    with col2:
        st.metric("Regular Shifts", results['regular_shifts'])
    with col3:
        st.metric("Overtime Shifts", results['overtime_shifts'])
    with col4:
        st.metric("Emergency Shifts", results['emergency_shifts'])
```

**Status: Infeasible** (Lines 1090-1150):
```python
elif status == "Infeasible":
    st.error("❌ Problem is INFEASIBLE - No solution exists")
    
    st.warning("""
    **Why Infeasible?**
    
    Common causes:
    1. Demand > Total Capacity (nurses × n1)
    2. Conflicting constraints (e.g., strict quotas + low n1)
    3. Very tight CVaR limit (μ too small)
    4. Fatigue threshold too low (<0.60)
    
    **Solutions**:
    1. Increase nurses or n1 (max shifts)
    2. Relax some constraints
    3. Disable advanced constraints
    4. Increase CVaR μ or decrease σ
    """)
    
    # Show capacity diagnostic
    feasibility = m.validate_capacity_feasibility(
        nurses_list, scenarios_df, model_params
    )
    
    if not feasibility['feasible']:
        st.error("### Capacity Issue Detected:")
        st.error(f"- Baseline demand: {feasibility['baseline_demand']}")
        st.error(f"- Total capacity: {feasibility['total_capacity']}")
        st.error(f"- Shortfall: {feasibility['baseline_demand'] - feasibility['total_capacity']}")
```

**Status: Other** (Lines 1150-1200):
```python
elif status == "Feasible":
    st.warning("⚠️ Feasible solution (not proven optimal)")
    st.info("Solver found a solution but couldn't prove it's the best. Usually good enough!")
    # Continue to show results...

elif status == "Undefined":
    st.error("❌ Solver did not complete")
    st.warning("Possible timeout or numerical issues. Try smaller problem or different solver.")

else:
    st.error(f"❌ Unexpected status: {status}")
```

### Solver Fallback Logic (Lines 1020-1050):
```python
if status != "Optimal" and selected_solver != "CBC":
    st.warning(f"⚠️ {selected_solver} failed. Trying CBC fallback...")
    
    prob, status = m.build_and_solve_model(
        nurses_list, scenarios_df, model_params, model_type,
        solver_name="CBC"  # Always available
    )
    
    if status == "Optimal":
        st.success("✅ CBC found optimal solution!")
```

---

## Section 5: Results Visualization (Lines 1361-1900)

### Purpose
Display optimization results through interactive charts and tables

### Tab Structure (Lines 1370-1400)

```python
if st.session_state.results is not None:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "📅 Schedule",
        "📈 Analytics",
        "🎲 Scenarios",
        "⚙️ Diagnostics"
    ])
```

### Tab 1: Overview (Lines 1410-1520)

**Summary Metrics**:
```python
with tab1:
    st.header("Solution Summary")
    
    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            "Total Cost", 
            f"${results['total_cost']:,.0f}"
        )
    with col2:
        st.metric(
            "Regular Shifts",
            results['regular_shifts'],
            delta=None  # Can show vs baseline
        )
    # ... more metrics
```

**Cost Breakdown Pie Chart**:
```python
cost_breakdown = {
    'Regular Shifts': results['regular_cost'],
    'Overtime Shifts': results['overtime_cost'],
    'Emergency Staff': results['emergency_cost'],
    'Penalties': results['penalty_cost']
}

fig = px.pie(
    values=list(cost_breakdown.values()),
    names=list(cost_breakdown.keys()),
    title="Cost Breakdown",
    color_discrete_sequence=px.colors.qualitative.Set2
)

st.plotly_chart(fig, use_container_width=True)
```

**Shift Distribution Bar Chart**:
```python
shift_data = {
    'Type': ['Regular', 'Overtime', 'Emergency'],
    'Count': [
        results['regular_shifts'],
        results['overtime_shifts'],
        results['emergency_shifts']
    ]
}

fig = px.bar(
    shift_data,
    x='Type', y='Count',
    title="Shift Distribution",
    color='Type',
    color_discrete_map={
        'Regular': '#4299e1',
        'Overtime': '#ed8936',
        'Emergency': '#f56565'
    }
)

st.plotly_chart(fig, use_container_width=True)
```

### Tab 2: Schedule (Lines 1520-1680)

**Individual Nurse Schedules**:
```python
with tab2:
    st.header("Nurse Schedules")
    
    # Nurse selector
    selected_nurse = st.selectbox(
        "Select Nurse",
        options=sorted(nurses_list)
    )
    
    # Filter schedule for selected nurse
    nurse_schedule = results['schedule_df'][
        results['schedule_df']['nurse'] == selected_nurse
    ]
    
    # Display as calendar-style table
    st.dataframe(
        nurse_schedule,
        use_container_width=True,
        hide_index=True
    )
    
    # Gantt chart visualization
    fig = px.timeline(
        nurse_schedule,
        x_start="day",
        x_end="day",  # Single day
        y="shift",
        color="type",
        title=f"{selected_nurse}'s Schedule"
    )
    st.plotly_chart(fig)
```

**Daily Coverage Heatmap**:
```python
# Pivot schedule to day×shift matrix
coverage_matrix = results['schedule_df'].pivot_table(
    index='shift',
    columns='day',
    values='nurse',
    aggfunc='count',
    fill_value=0
)

fig = px.imshow(
    coverage_matrix,
    labels=dict(x="Day", y="Shift", color="Nurses"),
    title="Coverage Heatmap",
    color_continuous_scale="Blues"
)

st.plotly_chart(fig, use_container_width=True)
```

### Tab 3: Analytics (Lines 1680-1800)

**Workload Distribution**:
```python
with tab3:
    # Shifts per nurse histogram
    shifts_per_nurse = results['schedule_df'].groupby('nurse').size()
    
    fig = px.histogram(
        x=shifts_per_nurse.values,
        nbins=20,
        title="Workload Distribution",
        labels={'x': 'Shifts per Nurse', 'y': 'Number of Nurses'}
    )
    st.plotly_chart(fig)
    
    # Fairness metrics
    st.subheader("Fairness Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Shifts", f"{shifts_per_nurse.mean():.1f}")
    with col2:
        st.metric("Std Dev", f"{shifts_per_nurse.std():.1f}")
    with col3:
        st.metric("Range", f"{shifts_per_nurse.max() - shifts_per_nurse.min()}")
```

**Fatigue Analysis** (if enabled):
```python
if 'fatigue_df' in results:
    st.subheader("Fatigue Analysis")
    
    # Line chart: fatigue over time
    fatigue_pivot = results['fatigue_df'].pivot(
        index='day',
        columns='nurse',
        values='fatigue'
    )
    
    fig = px.line(
        fatigue_pivot,
        title="Fatigue Accumulation Over Time",
        labels={'value': 'Fatigue Level', 'variable': 'Nurse'}
    )
    fig.add_hline(
        y=model_params['max_fatigue_threshold'],
        line_dash="dash",
        annotation_text="Threshold"
    )
    st.plotly_chart(fig, use_container_width=True)
```

### Tab 4: Scenarios (Lines 1800-1860)

**Recourse Actions by Scenario**:
```python
with tab4:
    st.header("Scenario Analysis")
    
    scenario_selector = st.selectbox(
        "Select Scenario",
        options=sorted(results['recourse_df']['scenario'].unique())
    )
    
    scenario_recourse = results['recourse_df'][
        results['recourse_df']['scenario'] == scenario_selector
    ]
    
    # Show emergency hires and cancellations
    st.subheader("Recourse Actions Taken")
    st.dataframe(scenario_recourse)
    
    # Bar chart: recourse cost per scenario
    recourse_costs = results['recourse_df'].groupby('scenario').apply(
        lambda x: (x['action'] == 'hire_emergency').sum() * model_params['q_plus']
    )
    
    fig = px.bar(
        x=recourse_costs.index,
        y=recourse_costs.values,
        title="Recourse Cost by Scenario",
        labels={'x': 'Scenario', 'y': 'Cost ($)'}
    )
    st.plotly_chart(fig)
```

### Tab 5: Diagnostics (Lines 1860-1900)

**Model Statistics**:
```python
with tab5:
    st.header("Model Diagnostics")
    
    # Problem size
    st.subheader("Problem Size")
    st.write(f"- Variables: {results['num_variables']:,}")
    st.write(f"- Constraints: {results['num_constraints']:,}")
    st.write(f"- Binary variables: {results['num_binary']:,}")
    
    # Solver info
    st.subheader("Solver Information")
    st.write(f"- Solver: {results['solver_used']}")
    st.write(f"- Status: {results['status']}")
    st.write(f"- Solve time: {results['solve_time']:.2f}s")
    st.write(f"- Gap: {results.get('mip_gap', 'N/A')}")
    
    # Constraint satisfaction
    st.subheader("Constraint Validation")
    validation_errors, validation_warnings = m.validate_results(
        results, model_params
    )
    
    if not validation_errors:
        st.success("✅ All constraints satisfied")
    else:
        for error in validation_errors:
            st.error(error)
```

---

## Section 6: Export & Download (Lines 1901-2100)

### Purpose
Allow users to download results in various formats

### Export Formats (Lines 1910-2000)

**1. CSV Export**:
```python
# Schedule CSV
schedule_csv = results['schedule_df'].to_csv(index=False)

st.download_button(
    label="📥 Download Schedule (CSV)",
    data=schedule_csv,
    file_name=f"nurse_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
```

**2. Excel Export** (Multiple Sheets):
```python
buffer = BytesIO()

with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    results['schedule_df'].to_excel(writer, sheet_name='Schedule', index=False)
    results['recourse_df'].to_excel(writer, sheet_name='Recourse', index=False)
    
    if 'fatigue_df' in results:
        results['fatigue_df'].to_excel(writer, sheet_name='Fatigue', index=False)
    
    # Summary sheet
    summary_df = pd.DataFrame({
        'Metric': ['Total Cost', 'Regular Shifts', 'Overtime', 'Emergency'],
        'Value': [
            results['total_cost'],
            results['regular_shifts'],
            results['overtime_shifts'],
            results['emergency_shifts']
        ]
    })
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

buffer.seek(0)

st.download_button(
    label="📥 Download Full Report (Excel)",
    data=buffer,
    file_name=f"nurse_schedule_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

**3. JSON Export** (Parameters + Results):
```python
export_data = {
    'timestamp': datetime.now().isoformat(),
    'parameters': model_params,
    'results': {
        'status': results['status'],
        'total_cost': results['total_cost'],
        'schedule': results['schedule_df'].to_dict('records'),
        'metrics': results['metrics']
    }
}

json_str = json.dumps(export_data, indent=2)

st.download_button(
    label="📥 Download Results (JSON)",
    data=json_str,
    file_name=f"optimization_results_{datetime.now().strftime('%Y%m%d')}.json",
    mime="application/json"
)
```

---

## Section 7: Additional Tools (Lines 2101-2372)

### Purpose
Helper features: solver selection, help documentation, about section

### Solver Configuration (Lines 2110-2200)

**Available Solvers Display**:
```python
with st.expander("🔧 Solver Configuration"):
    available_solvers = get_available_solvers()
    
    st.write("**Installed Solvers:**")
    for solver in available_solvers:
        st.success(f"✅ {solver}")
    
    recommended = recommend_solver()
    st.info(f"💡 Recommended: {recommended}")
    
    # Manual solver selection
    selected_solver = st.selectbox(
        "Choose Solver",
        options=["AUTO"] + available_solvers,
        help="AUTO uses best available"
    )
    
    # Installation instructions for missing solvers
    if "GUROBI" not in available_solvers:
        st.warning("Gurobi not installed (fastest solver)")
        st.code(get_installation_instructions("GUROBI"))
```

### Help & Documentation (Lines 2200-2320)

**Quick Start Guide**:
```python
with st.expander("📖 Quick Start Guide"):
    st.markdown("""
    ## Getting Started
    
    1. **Choose Data Source**
       - Quick start: Use sample data
       - Production: Upload CSV files
    
    2. **Set Parameters**
       - Costs: Regular < Overtime < Emergency
       - Work rules: n1 (max shifts), n3 (min regular)
    
    3. **Select Model Type**
       - SDM: Standard cost minimization
       - SDM-CVaR: With risk management
    
    4. **Optimize**
       - Click "Optimize Schedule"
       - Wait for results (usually <5 seconds)
    
    5. **Review Results**
       - Check Overview tab for summary
       - View individual schedules in Schedule tab
       - Export to CSV/Excel
    """)
```

**Parameter Tuning Tips**:
```python
with st.expander("💡 Parameter Tuning Tips"):
    st.markdown("""
    ### Cost Parameters
    - **c2 ≥ c1**: Overtime premium (typically 1.5x)
    - **q_plus >> c2**: Emergency very expensive (2-3x)
    
    ### Work Rules
    - **n1**: Start with 14-21 for 2-4 week periods
    - **n3**: Usually 60-70% of n1
    - **n2**: Limit nights to 20-30% of n1
    
    ### CVaR
    - **σ**: Use 0.90-0.95 for risk management
    - **μ**: Start with 50, adjust based on problem size
    
    ### Fatigue
    - **Threshold**: 0.65-0.75 recommended
    - **Below 0.60**: May cause infeasibility
    - **Above 0.80**: Little constraint effect
    """)
```

### About Section (Lines 2320-2372)

**Project Information**:
```python
st.markdown("---")
st.markdown("""
\u003cdiv class="footer"\u003e
\u003ch3\u003e🩺 FROST-NS - Nurse Scheduling System\u003c/h3\u003e
\u003cp\u003eImplementation of He et al. (2019) two-stage stochastic scheduling model\u003c/p\u003e
\u003cp\u003e
    \u003ca href="https://github.com/yourusername/NSS"\u003e📁 GitHub\u003c/a\u003e |
    \u003ca href="/docs"\u003e📖 Documentation\u003c/a\u003e |
    \u003ca href="/about"\u003eℹ️ About\u003c/a\u003e
\u003c/p\u003e
\u003cp style="font-size: 0.9rem; color: #a0aec0;"\u003e
    ⚠️ Research prototype - not for production healthcare use without validation
\u003c/p\u003e
\u003c/div\u003e
""", unsafe_allow_html=True)
```

---

## Summary

### Application Flow

```
User Opens App
    ↓
1. Page loads → Custom CSS applied → Clean UI
    ↓
2. Sidebar: Choose data (sample vs upload)
    ↓
3. If upload → Robust parsing → Validation
    ↓
4. Set parameters (costs, rules, model type)
    ↓
5. Click "Optimize" → Call model.build_and_solve_model()
    ↓
6. Handle result:
   - Optimal → Show visualizations
   - Infeasible → Diagnostic help
   - Error → Retry with fallback
    ↓
7. Explore results in tabs:
   - Overview: Metrics + charts
   - Schedule: Individual assignments
   - Analytics: Workload distribution
   - Scenarios: Recourse actions
   - Diagnostics: Model stats
    ↓
8. Export (CSV/Excel/JSON)
```

### Key Features

**User Experience**:
- ✅ Clean, professional UI with custom CSS
- ✅ Intuitive parameter inputs with help text
- ✅ Robust file parsing (handles multiple formats)
- ✅ Real-time validation with clear error messages
- ✅ Progress indicators during solving

**Visualization**:
- ✅ Interactive Plotly charts (pie, bar, heatmap, timeline)
- ✅ Tabbed interface for organized results
- ✅ Drill-down capability (overall → individual schedules)
- ✅ Color-coded metrics (green=good, red=warning)

**Error Handling**:
- ✅ Comprehensive try-except blocks
- ✅ Specific error messages for each failure mode
- ✅ Solver fallback (Gurobi → HiGHS → CBC)
- ✅ Infeasibility diagnostics with solutions

**Export**:
- ✅ Multiple formats (CSV, Excel, JSON)
- ✅ Timestamped filenames
- ✅ Complete data (schedule + metrics + parameters)

### Code Statistics

- **Lines**: 2,372
- **Functions**: ~15 helper functions
- **Widgets**: ~50 input widgets
- **Charts**: ~12 visualizations
- **Error handlers**: ~8 exception blocks

---

## Comparison: app.py vs model.py

| Aspect | model.py | app.py |
|--------|----------|--------|
| **Purpose** | Math/optimization | UI/interaction |
| **Complexity** | High (algorithms) | Medium (UX logic) |
| **Lines** | 2,382 | 2,372 |
| **Key Skills** | Linear programming | Web development |
| **Testing** | Unit tests | Manual QA |
| **Changes** | Rare (math stable) | Frequent (UX iteration) |

**Together**: Complete end-to-end scheduling system! 🎉

---

**End of app.py Deep Dive**
