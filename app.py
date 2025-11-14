import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import model as m
from io import BytesIO
import json
from solver_config import get_available_solvers, recommend_solver, get_installation_instructions

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Nurse Scheduler Pro", 
    page_icon="🩺", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean professional interface
st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main Container */
    .main {
        padding: 2rem 3rem;
        background: linear-gradient(to bottom, #e6f2ff 0%, #f0f8ff 100%);
        border-left: 4px solid #4299e1;
        min-height: 100vh;
    }
    
    /* Content wrapper with light blue frame */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1400px;
        background: white;
        border-radius: 16px;
        border: 3px solid #bee3f8;
        box-shadow: 0 4px 20px rgba(66, 153, 225, 0.15);
        margin: 1rem auto;
    }
    
    /* Main Header - Clean & Bold */
    .main-header {
        font-size: 4rem;
        font-weight: 800;
        color: #1a1a2e;
        text-align: center;
        padding: 2rem 0 1rem 0;
        letter-spacing: -1px;
    }
    
    /* Subtitle - Clean */
    .sub-header {
        font-size: 1.4rem;
        color: #718096;
        text-align: center;
        padding-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Large Buttons */
    .stButton > button {
        height: 4rem;
        font-size: 1.3rem;
        font-weight: 700;
        border-radius: 12px;
        border: none;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Metric Cards - Clean & Spacious */
    .metric-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        border: 2px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s;
    }
    
    .metric-card:hover {
        border-color: #667eea;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    }
    
    /* Section Headers - Larger */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1a1a2e !important;
        margin-top: 2rem !important;
    }
    
    h2 {
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
    }
    
    h3 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #4a5568 !important;
    }
    
    /* Tabs - Larger & Cleaner */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: transparent;
        padding: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        padding: 0 2.5rem;
        font-size: 1.2rem;
        font-weight: 600;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        background: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: #667eea !important;
        color: white !important;
        border-color: #667eea !important;
    }
    
    /* Sidebar - Clean & Professional */
    [data-testid="stSidebar"] {
        background: #f7fafc;
        border-right: 1px solid #e2e8f0;
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] h1 {
        font-size: 1.8rem !important;
    }
    
    [data-testid="stSidebar"] h2 {
        font-size: 1.4rem !important;
        margin-top: 2rem !important;
    }
    
    /* Input Fields - Larger */
    .stNumberInput input, .stTextInput input, .stSelectbox select {
        font-size: 1.1rem !important;
        height: 3rem !important;
        border-radius: 8px !important;
        border: 2px solid #e2e8f0 !important;
    }
    
    .stSlider {
        padding: 1rem 0;
    }
    
    /* Success/Info boxes - Larger */
    .stSuccess, .stInfo, .stWarning, .stError {
        padding: 1.5rem !important;
        font-size: 1.1rem !important;
        border-radius: 12px !important;
        border-width: 0 0 0 6px !important;
    }
    
    /* Expander - Larger */
    .streamlit-expanderHeader {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        padding: 1rem 1.5rem !important;
        background: #f7fafc !important;
        border-radius: 10px !important;
    }
    
    /* Dataframe - Clean */
    .dataframe {
        font-size: 1rem !important;
        border-radius: 10px !important;
    }
    
    /* Metrics - Larger */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1.2rem !important;
        font-weight: 500 !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 3rem 0 2rem 0;
        color: #718096;
        font-size: 1rem;
        border-top: 2px solid #e2e8f0;
        margin-top: 4rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. TITLE & BRANDING ---
st.markdown('<h1 class="main-header">🩺 Nurse Scheduler</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced Optimization System for Healthcare Scheduling</p>', unsafe_allow_html=True)

st.markdown("")  # Spacing
st.markdown("---")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'prob' not in st.session_state:
    st.session_state.prob = None


# --- 3. SIDEBAR FOR ALL USER INPUTS ---
with st.sidebar:
    # Sidebar header - clean and professional
    st.markdown("""
        <div style="text-align: center; padding: 0 0 2rem 0;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚙️</div>
            <h1 style="color: #1a1a2e; margin: 0; font-size: 2rem; font-weight: 700;">Settings</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Data Source Selection
    st.header("📊 Data Source")
    data_source = st.radio(
        "Choose data input method:",
        ["Use Sample Data (Quick Start)", "Upload Custom Data"],
        help="Sample data provides a pre-configured example. Upload for real scenarios."
    )
    
    nurses_list = None
    scenarios_df = None
    
    if data_source == "Use Sample Data (Quick Start)":
        st.success("✓ Using sample data")
        
        col1, col2 = st.columns(2)
        with col1:
            num_nurses = st.number_input("Number of Nurses", 5, 50, 10, 1)
        with col2:
            num_days = st.number_input("Planning Days", 7, 30, 14, 1)
        
        num_scenarios = st.slider("Demand Scenarios", 3, 20, 5, 1)
        
        if st.button("🎲 Generate Sample Data", type="secondary", use_container_width=True):
            nurses_list, scenarios_df = m.generate_sample_data(num_nurses, num_days, num_scenarios)
            st.session_state.nurses_list = nurses_list
            st.session_state.scenarios_df = scenarios_df
            st.success(f"Generated {len(nurses_list)} nurses with {len(scenarios_df)} demand records!")
        
        # Use previously generated data
        if 'nurses_list' in st.session_state:
            nurses_list = st.session_state.nurses_list
            scenarios_df = st.session_state.scenarios_df
    
    else:
        st.subheader("📁 Upload Files")
        nurse_file = st.file_uploader(
            "Nurse List (CSV/TXT)", 
            type=["csv", "txt"],
            help="One nurse name per line"
        )
        scenario_file = st.file_uploader(
            "Demand Scenarios (CSV)", 
            type=["csv"],
            help="Columns: scenario, day, shift, demand"
        )
        
        if nurse_file and scenario_file:
            try:
                nurses_df = pd.read_csv(nurse_file, header=None)
                nurses_list = nurses_df.iloc[:, 0].tolist()
                scenarios_df = pd.read_csv(scenario_file)
                st.success(f"✓ Loaded {len(nurses_list)} nurses")
                st.success(f"✓ Loaded {len(scenarios_df)} demand records")
            except Exception as e:
                st.error(f"Error loading files: {e}")
    
    st.divider()
    
    # --- Model Parameters ---
    st.header("💰 Cost Parameters")
    
    with st.expander("💵 Wage Costs", expanded=True):
        c1 = st.number_input("Regular Shift Cost ($c_1$)", 50.0, 500.0, 100.0, 10.0)
        c2 = st.number_input("Overtime Shift Cost ($c_2$)", 50.0, 500.0, 150.0, 10.0)
        q_plus = st.number_input("Emergency Shift Cost ($q^+$)", 100.0, 1000.0, 200.0, 10.0)
    
    with st.expander("⚠️ Quality Penalties (Soft Constraints)", expanded=False):
        st.caption("These penalties discourage undesirable schedule patterns without making them impossible")
        c3 = st.number_input(
            "Stand-Alone Shift Penalty ($c_3$)", 
            0.0, 100.0, 10.0, 1.0,
            help="Penalty for isolated working days (e.g., work Mon, off Tue-Thu, work Fri)"
        )
        c4 = st.number_input(
            "Unwanted Pattern Penalty ($c_4$)", 
            0.0, 100.0, 15.0, 1.0,
            help="Penalty for bad shift sequences (e.g., Late→Early, Day→Early)"
        )
    
    st.header("📋 Work Rules")
    
    with st.expander("⚖️ Basic Shift Constraints", expanded=True):
        n1 = st.slider("Max Total Shifts ($n_1$)", 5, 30, 15, 1)
        n2 = st.slider("Max Night Shifts ($n_2$)", 1, 15, 5, 1)
        n3 = st.slider("Min Regular Shifts ($n_3$)", 1, 20, 10, 1)
    
    # NEW: Advanced constraints for university project
    with st.expander("🏖️ Weekend Constraints (Advanced)", expanded=False):
        st.caption("Constraint 9: Minimum Complete Weekends Off")
        n4 = st.number_input(
            "Min Complete Weekends Off ($n_4$)", 
            0, 4, 0, 1,
            help="Number of complete weekends (Sat+Sun) each nurse must have off. Set to 0 to disable."
        )
        
        if n4 > 0:
            st.info("💡 Weekend detection requires a start date")
            start_date = st.date_input(
                "Planning Period Start Date",
                help="Used to determine which days are weekends"
            )
            start_date_str = start_date.strftime('%Y-%m-%d')
        else:
            start_date_str = None
    
    with st.expander("🌙 Night Shift Rest Rules (Advanced)", expanded=False):
        st.caption("Constraints 10-13: Night shift safety and rest requirements")
        night_rest_enabled = st.checkbox(
            "Enable Night Shift Rest Constraints",
            value=False,
            help="Enforces consecutive night shifts and mandatory rest periods"
        )
        
        if night_rest_enabled:
            min_consecutive_nights = st.number_input(
                "Minimum Consecutive Night Shifts",
                1, 5, 2, 1,
                help="Night shifts must come in sequences of at least N consecutive nights (prevents single isolated nights)"
            )
            days_off_after_nights = st.number_input(
                "Days Off Required After Night Sequence",
                1, 5, 2, 1,
                help="Nurses must be completely off for N days after a sequence of night shifts"
            )
        else:
            min_consecutive_nights = 2
            days_off_after_nights = 2
    
    with st.expander("📊 Shift Type Quotas (Advanced)", expanded=False):
        st.caption("Constraints 2-5: Min/Max for each specific shift type")
        st.warning("⚠️ Setting quotas can make the problem infeasible! Use carefully.")
        
        use_shift_quotas = st.checkbox(
            "Enable Shift Type Quotas",
            value=False,
            help="Set min/max limits for each shift type (E, D, L, N)"
        )
        
        shift_quotas = {}
        if use_shift_quotas:
            st.write("**Set quotas for each shift type:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Early (E) Shifts")
                e_min = st.number_input("Min Early Shifts", 0, 20, 0, 1, key="e_min")
                e_max = st.number_input("Max Early Shifts", 0, 30, 10, 1, key="e_max")
                if e_max >= e_min and e_max > 0:
                    shift_quotas['E'] = {'min': e_min, 'max': e_max}
                
                st.subheader("Day (D) Shifts")
                d_min = st.number_input("Min Day Shifts", 0, 20, 0, 1, key="d_min")
                d_max = st.number_input("Max Day Shifts", 0, 30, 10, 1, key="d_max")
                if d_max >= d_min and d_max > 0:
                    shift_quotas['D'] = {'min': d_min, 'max': d_max}
            
            with col2:
                st.subheader("Late (L) Shifts")
                l_min = st.number_input("Min Late Shifts", 0, 20, 0, 1, key="l_min")
                l_max = st.number_input("Max Late Shifts", 0, 30, 10, 1, key="l_max")
                if l_max >= l_min and l_max > 0:
                    shift_quotas['L'] = {'min': l_min, 'max': l_max}
                
                st.subheader("Night (N) Shifts")
                n_min = st.number_input("Min Night Shifts", 0, 20, 0, 1, key="n_min")
                n_max = st.number_input("Max Night Shifts", 0, 30, 5, 1, key="n_max")
                if n_max >= n_min and n_max > 0:
                    shift_quotas['N'] = {'min': n_min, 'max': n_max}
            
            if shift_quotas:
                st.success(f"✓ Quotas set for {len(shift_quotas)} shift types")
    
    st.divider()
    
    # --- Model Selection ---
    st.header("🎯 Optimization Model")
    
    model_choice = st.selectbox(
        "Select Model Type:",
        [
            "Cost Optimization (SDM)",
            "Risk-Aware with CVaR (SDM-CVaR)"
        ],
        help="SDM minimizes cost. SDM-CVaR also controls worst-case understaffing risk."
    )
    
    model_type_code = "SDM"
    sigma = None
    mu = None
    
    if "CVaR" in model_choice:
        model_type_code = "SDM-CVaR"
        with st.expander("🛡️ Risk Parameters", expanded=True):
            sigma = st.slider(
                "Confidence Level (σ)", 
                0.90, 0.99, 0.95, 0.01,
                help="Higher = more conservative"
            )
            mu = st.number_input(
                "Max Acceptable Shortage (μ)", 
                0.0, 50.0, 5.0, 0.5,
                help="Maximum shortage in worst-case scenarios"
            )
    
    st.divider()
    
    # --- Solver Selection ---
    st.header("⚡ Solver Configuration")
    
    # Detect available solvers
    available_solvers = get_available_solvers()
    
    # Create solver options list
    solver_options = []
    solver_display_names = {}
    for solver, info in available_solvers.items():
        if info['available']:
            display_name = f"{solver} - {info['speed']}"
            solver_options.append(solver)
            solver_display_names[solver] = display_name
        else:
            display_name = f"{solver} - Not Installed"
            solver_options.append(solver)
            solver_display_names[solver] = display_name
    
    # Recommend solver based on problem size if data is loaded
    if nurses_list is not None and scenarios_df is not None:
        num_nurses = len(nurses_list)
        num_days = len(scenarios_df['day'].unique())
        num_scenarios = len(scenarios_df['scenario'].unique())
        recommended, reason = recommend_solver(num_nurses, num_days, num_scenarios)
        st.info(f"💡 **Recommended**: {recommended} - {reason}")
    
    # Find default solver index (prefer Gurobi if available, then CBC)
    default_index = 0
    if 'GUROBI' in solver_options and available_solvers.get('GUROBI', {}).get('available', False):
        default_index = solver_options.index('GUROBI')
    elif 'CBC' in solver_options:
        default_index = solver_options.index('CBC')
    
    # Solver selection
    selected_solver = st.selectbox(
        "Select Solver",
        options=solver_options,
        format_func=lambda x: solver_display_names[x],
        index=default_index,
        help="Gurobi is 10-100× faster than CBC and is now installed!"
    )
    
    # Show installation instructions if solver not available
    if not available_solvers.get(selected_solver, {}).get('available', False):
        with st.expander("📦 Installation Instructions", expanded=True):
            st.markdown(get_installation_instructions(selected_solver))
            st.warning(f"⚠️ {selected_solver} is not installed. Falling back to CBC.")
            selected_solver = 'CBC'  # Fallback
    
    st.divider()
    
    # --- Solve Button ---
    st.markdown("### 🚀 Generate Schedule")
    st.markdown("")  # Spacing
    
    if nurses_list is None or scenarios_df is None:
        st.warning("⚠️ Please configure your data in the sidebar first")
        st.button("🎯 OPTIMIZE SCHEDULE", type="primary", use_container_width=True, disabled=True)
        solve_button = False
    else:
        st.success(f"✅ Ready: {len(nurses_list)} nurses • {len(scenarios_df)} scenarios")
        st.markdown("")  # Spacing
        
        solve_button = st.button(
            "🎯 OPTIMIZE SCHEDULE", 
            type="primary", 
            use_container_width=True,
            help="Generate optimal nurse schedule"
        )


# --- 4. MAIN CONTENT AREA ---
if solve_button and nurses_list is not None and scenarios_df is not None:
    
    # Build model parameters
    model_params = {
        'c1': c1, 'c2': c2, 'q_plus': q_plus,
        'c3': c3, 'c4': c4,  # Soft constraint penalties
        'n1': n1, 'n2': n2, 'n3': n3,
        'sigma': sigma, 'mu': mu,
        
        # Advanced constraints (NEW for university project)
        'n4': n4,
        'start_date': start_date_str,
        'shift_quotas': shift_quotas,
        'night_rest_enabled': night_rest_enabled,
        'min_consecutive_nights': min_consecutive_nights,
        'days_off_after_nights': days_off_after_nights,
    }
    
    # Show warning if advanced constraints are enabled
    advanced_enabled = []
    if n4 > 0:
        advanced_enabled.append(f"Minimum {n4} complete weekends off")
    if shift_quotas:
        advanced_enabled.append(f"Shift type quotas for {len(shift_quotas)} shift types")
    if night_rest_enabled:
        advanced_enabled.append(f"Night rest rules ({min_consecutive_nights} consecutive, {days_off_after_nights} days off after)")
    
    if advanced_enabled:
        st.info("🎓 **Advanced Constraints Enabled:**\n" + "\n".join(f"- {item}" for item in advanced_enabled))
        st.warning("⚠️ Advanced constraints may increase solve time and reduce feasibility. If solver fails, try relaxing some constraints.")
    
    # Solve
    problem_size = len(nurses_list) * len(scenarios_df['day'].unique()) * len(scenarios_df['scenario'].unique())
    
    if problem_size > 5000:
        st.info(f"⚠️ Large problem detected ({len(nurses_list)} nurses × {len(scenarios_df['day'].unique())} days × {len(scenarios_df['scenario'].unique())} scenarios). Solver may find a near-optimal solution (within 5%) for faster results.")
    
    # Double-check solver availability before solving
    available_solvers_check = get_available_solvers()
    if not available_solvers_check.get(selected_solver, {}).get('available', False):
        st.warning(f"⚠️ {selected_solver} is not available. Using CBC instead.")
        selected_solver = 'CBC'
    
    # Enhanced progress indicator
    progress_container = st.container()
    with progress_container:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 2rem; background: #667eea; 
                    border-radius: 16px; color: white; margin: 2rem 0;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
            <h1 style="margin: 0; color: white; font-size: 2.5rem;">Optimizing...</h1>
            <p style="margin: 1.5rem 0 0 0; font-size: 1.3rem; opacity: 0.9;">
                Building model and finding optimal solution
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate progress updates (since we can't get real-time from solver)
        import time
        import threading
        
        def update_progress():
            steps = [
                (0.25, "📊 Loading data..."),
                (0.5, "🏗️ Building model..."),
                (0.75, "🔍 Solving..."),
            ]
            for prog, msg in steps:
                if not hasattr(st.session_state, 'solve_complete'):
                    progress_bar.progress(prog)
                    status_text.info(msg)
                    time.sleep(0.3)
        
        # Start progress animation in background
        progress_thread = threading.Thread(target=update_progress, daemon=True)
        progress_thread.start()
    
    try:
        import time
        
        # Time the model building and solving
        start_time = time.time()
        prob, status = m.build_and_solve_model(
            nurses_list,
            scenarios_df,
            model_params,
            model_type_code,
            solver_name=selected_solver  # Pass selected solver
        )
        solve_time = time.time() - start_time
        st.session_state.solve_complete = True
        
        # Clear progress indicator
        progress_container.empty()
        
        if status == "Optimal":
            st.balloons()  # Celebration animation!
            st.success(f"✅ **Optimization Complete!** Status: **{status}** (Solver: {selected_solver}, Time: {solve_time:.1f}s)")
            
            # Extract results
            extract_start = time.time()
            results = m.extract_results(prob, nurses_list, scenarios_df, model_params, model_type_code)
            extract_time = time.time() - extract_start
            st.session_state.results = results
            
            # Show timing breakdown
            st.info(f"⏱️ **Performance:** Solving: {solve_time:.1f}s | Results extraction: {extract_time:.1f}s | Total: {solve_time + extract_time:.1f}s")
            st.session_state.prob = prob
            st.session_state.model_params = model_params
            
        else:
            st.error(f"❌ Solver finished with status: **{status}**")
            st.warning("The model could not find an optimal solution. Try relaxing constraints or checking your data.")
            
    except Exception as e:
        st.error(f"Error during optimization: {e}")
        st.exception(e)

# --- 5. DISPLAY RESULTS ---
if st.session_state.results is not None:
    results = st.session_state.results
    
    # Key Metrics at the top
    st.header("📊 Summary Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Cost",
            f"${results['cost_breakdown']['total_cost']:,.0f}",
            help="Total optimization cost"
        )
    
    with col2:
        st.metric(
            "Regular Shifts",
            int(results['cost_breakdown']['total_regular_shifts']),
            help="Total regular shifts assigned"
        )
    
    with col3:
        st.metric(
            "Overtime Shifts",
            int(results['cost_breakdown']['total_overtime_shifts']),
            help="Total overtime shifts assigned"
        )
    
    with col4:
        avg_shortage = results['scenario_df']['shortage_shifts'].mean()
        st.metric(
            "Avg. Shortage",
            f"{avg_shortage:.1f}",
            help="Average shortage across scenarios"
        )
    
    st.divider()
    
    # Tabbed interface for detailed results
    tabs = st.tabs([
        "📅 Nurse Roster", 
        "💰 Cost Analysis", 
        "📈 Coverage Analysis",
        "⚠️ Risk Assessment",
        "📊 Scenario Comparison",
        "📄 Full Report"
    ])
    
    # ===== TAB 1: ROSTER =====
    with tabs[0]:
        st.header("👥 Nurse Work Schedule")
        
        roster_df = results['roster_df']
        
        # Display options
        col1, col2 = st.columns([3, 1])
        with col2:
            show_summary = st.checkbox("Show Summary Columns", value=True)
        
        if show_summary:
            st.dataframe(
                roster_df,
                use_container_width=True,
                height=400
            )
        else:
            # Hide summary columns
            day_cols = [col for col in roster_df.columns if col.startswith("Day_")]
            st.dataframe(
                roster_df[["Nurse"] + day_cols],
                use_container_width=True,
                height=400
            )
        
        # Download roster
        csv_roster = roster_df.to_csv(index=False)
        st.download_button(
            "⬇️ Download Roster (CSV)",
            csv_roster,
            "nurse_roster.csv",
            "text/csv",
            use_container_width=True
        )
        
        # Roster heatmap
        st.subheader("📊 Shift Distribution Heatmap")
        
        # Prepare data for heatmap
        day_cols = [col for col in roster_df.columns if col.startswith("Day_")]
        heatmap_data = roster_df[["Nurse"] + day_cols].set_index("Nurse")
        
        # Convert shift labels to numeric for visualization
        shift_map = {'OFF': 0, 'E': 1, 'D': 2, 'L': 3, 'N': 4, 
                     'E (OT)': 1.5, 'D (OT)': 2.5, 'L (OT)': 3.5, 'N (OT)': 4.5}
        
        heatmap_numeric = heatmap_data.replace(shift_map)
        
        fig_heatmap = px.imshow(
            heatmap_numeric,
            labels=dict(x="Day", y="Nurse", color="Shift Type"),
            x=day_cols,
            y=heatmap_data.index,
            color_continuous_scale="RdYlGn_r",
            aspect="auto"
        )
        fig_heatmap.update_layout(height=max(400, len(nurses_list) * 20))
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # ===== TAB 2: COST ANALYSIS =====
    with tabs[1]:
        st.header("💵 Detailed Cost Breakdown")
        
        cost = results['cost_breakdown']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Stage 1: Baseline Costs")
            st.metric("Regular Shift Costs", f"${cost['stage1_regular_cost']:,.0f}")
            st.metric("Overtime Shift Costs", f"${cost['stage1_overtime_cost']:,.0f}")
            st.metric("**Stage 1 Total**", f"**${cost['stage1_total']:,.0f}**")
        
        with col2:
            st.subheader("Stage 2: Recourse Costs")
            st.metric("Expected Recourse Cost", f"${cost['stage2_expected_cost']:,.0f}")
            st.metric("Cost per Nurse", f"${cost['avg_cost_per_nurse']:,.0f}")
            st.metric("**Grand Total**", f"**${cost['total_cost']:,.0f}**")
        
        # Cost breakdown pie chart
        st.subheader("📊 Cost Distribution")
        
        cost_data = pd.DataFrame({
            'Category': ['Regular Wages', 'Overtime Wages', 'Emergency Recourse'],
            'Amount': [
                cost['stage1_regular_cost'],
                cost['stage1_overtime_cost'],
                cost['stage2_expected_cost']
            ]
        })
        
        fig_pie = px.pie(
            cost_data,
            values='Amount',
            names='Category',
            title='Cost Distribution',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Shift distribution
        st.subheader("📈 Shift Allocation")
        
        shift_data = pd.DataFrame({
            'Type': ['Regular', 'Overtime'],
            'Count': [cost['total_regular_shifts'], cost['total_overtime_shifts']]
        })
        
        fig_bar = px.bar(
            shift_data,
            x='Type',
            y='Count',
            title='Regular vs Overtime Shifts',
            color='Type',
            text='Count'
        )
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # ===== TAB 3: COVERAGE ANALYSIS =====
    with tabs[2]:
        st.header("📊 Daily Coverage Analysis")
        
        coverage_df = results['coverage_df']
        
        # Coverage by shift type
        fig_coverage = px.bar(
            coverage_df,
            x='day',
            y='assigned_nurses',
            color='shift',
            title='Assigned Nurses by Day and Shift',
            labels={'assigned_nurses': 'Number of Nurses', 'day': 'Day'},
            barmode='group'
        )
        st.plotly_chart(fig_coverage, use_container_width=True)
        
        # Coverage table
        st.subheader("📋 Coverage Details")
        coverage_pivot = coverage_df.pivot(index='shift', columns='day', values='assigned_nurses')
        st.dataframe(coverage_pivot, use_container_width=True)
    
    # ===== TAB 4: RISK ASSESSMENT =====
    with tabs[3]:
        st.header("⚠️ Risk Metrics & Analysis")
        
        risk = results['risk_metrics']
        scenario_df = results['scenario_df']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Model Configuration")
            st.info(f"**Model Type:** {risk['model_type']}")
            st.info(f"**Scenarios Analyzed:** {risk['num_scenarios']}")
            
            if risk['model_type'] == "SDM-CVaR":
                st.success(f"**Confidence Level (σ):** {risk['confidence_level']:.1%}")
                st.success(f"**CVaR Limit (μ):** {risk['cvar_limit']:.2f} shifts")
                st.success(f"**Actual VaR (ξ):** {risk.get('var_value', 0):.2f} shifts")
        
        with col2:
            st.subheader("Shortage Statistics")
            st.metric("Mean Shortage", f"{scenario_df['shortage_shifts'].mean():.2f}")
            st.metric("Max Shortage", f"{scenario_df['shortage_shifts'].max():.0f}")
            st.metric("Std Dev", f"{scenario_df['shortage_shifts'].std():.2f}")
        
        # Distribution plot
        st.subheader("📊 Shortage Distribution")
        
        fig_dist = px.histogram(
            scenario_df,
            x='shortage_shifts',
            nbins=20,
            title='Distribution of Shortages Across Scenarios',
            labels={'shortage_shifts': 'Shortage (shifts)'},
            marginal='box'
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # ===== TAB 5: SCENARIO COMPARISON =====
    with tabs[4]:
        st.header("🔬 Scenario-by-Scenario Analysis")
        
        scenario_df = results['scenario_df']
        
        # Scenario comparison chart
        fig_scenarios = go.Figure()
        
        fig_scenarios.add_trace(go.Bar(
            name='Shortage',
            x=scenario_df['scenario'],
            y=scenario_df['shortage_shifts'],
            marker_color='indianred'
        ))
        
        fig_scenarios.add_trace(go.Bar(
            name='Overage',
            x=scenario_df['scenario'],
            y=scenario_df['overage_shifts'],
            marker_color='lightseagreen'
        ))
        
        fig_scenarios.update_layout(
            title='Shortage vs Overage by Scenario',
            xaxis_title='Scenario',
            yaxis_title='Number of Shifts',
            barmode='group'
        )
        
        st.plotly_chart(fig_scenarios, use_container_width=True)
        
        # Detailed table
        st.subheader("📋 Detailed Scenario Results")
        st.dataframe(scenario_df, use_container_width=True)
        
        # Download scenario data
        csv_scenarios = scenario_df.to_csv(index=False)
        st.download_button(
            "⬇️ Download Scenario Analysis (CSV)",
            csv_scenarios,
            "scenario_analysis.csv",
            "text/csv"
        )
    
    # ===== TAB 6: FULL REPORT =====
    with tabs[5]:
        st.header("📄 Comprehensive Report")
        
        st.markdown(f"""
        ## Executive Summary
        
        **Optimization Model:** {results['risk_metrics']['model_type']}  
        **Total Nurses:** {len(nurses_list)}  
        **Planning Period:** {len(results['coverage_df']['day'].unique())} days  
        **Demand Scenarios:** {results['risk_metrics']['num_scenarios']}
        
        ---
        
        ### Financial Summary
        
        - **Total Cost:** ${results['cost_breakdown']['total_cost']:,.2f}
        - **Stage 1 (Baseline):** ${results['cost_breakdown']['stage1_total']:,.2f}
          - Regular Shifts: ${results['cost_breakdown']['stage1_regular_cost']:,.2f}
          - Overtime Shifts: ${results['cost_breakdown']['stage1_overtime_cost']:,.2f}
        - **Stage 2 (Expected Recourse):** ${results['cost_breakdown']['stage2_expected_cost']:,.2f}
        - **Average Cost per Nurse:** ${results['cost_breakdown']['avg_cost_per_nurse']:,.2f}
        
        ---
        
        ### Staffing Summary
        
        - **Total Regular Shifts:** {int(results['cost_breakdown']['total_regular_shifts'])}
        - **Total Overtime Shifts:** {int(results['cost_breakdown']['total_overtime_shifts'])}
        - **Total Shifts:** {int(results['cost_breakdown']['total_regular_shifts'] + results['cost_breakdown']['total_overtime_shifts'])}
        
        ---
        
        ### Risk Summary
        
        - **Average Shortage:** {results['scenario_df']['shortage_shifts'].mean():.2f} shifts
        - **Maximum Shortage:** {results['scenario_df']['shortage_shifts'].max():.0f} shifts
        - **Shortage Std Dev:** {results['scenario_df']['shortage_shifts'].std():.2f}
        
        """)
        
        if results['risk_metrics']['model_type'] == "SDM-CVaR":
            st.markdown(f"""
            ### CVaR Risk Metrics
            
            - **Confidence Level (σ):** {results['risk_metrics']['confidence_level']:.1%}
            - **Target CVaR Limit (μ):** {results['risk_metrics']['cvar_limit']:.2f} shifts
            - **Actual VaR (ξ):** {results['risk_metrics'].get('var_value', 0):.2f} shifts
            
            The model successfully controlled the worst-case shortage risk.
            """)
        
        # Generate downloadable report
        report_text = f"""
NURSE SCHEDULING OPTIMIZATION REPORT
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
EXECUTIVE SUMMARY
{'='*60}

Model Type: {results['risk_metrics']['model_type']}
Total Nurses: {len(nurses_list)}
Planning Period: {len(results['coverage_df']['day'].unique())} days
Demand Scenarios: {results['risk_metrics']['num_scenarios']}

{'='*60}
FINANCIAL SUMMARY
{'='*60}

Total Cost: ${results['cost_breakdown']['total_cost']:,.2f}
Stage 1 Cost: ${results['cost_breakdown']['stage1_total']:,.2f}
  - Regular Wages: ${results['cost_breakdown']['stage1_regular_cost']:,.2f}
  - Overtime Wages: ${results['cost_breakdown']['stage1_overtime_cost']:,.2f}
Stage 2 Expected Recourse: ${results['cost_breakdown']['stage2_expected_cost']:,.2f}
Average Cost per Nurse: ${results['cost_breakdown']['avg_cost_per_nurse']:,.2f}

{'='*60}
STAFFING SUMMARY
{'='*60}

Regular Shifts: {int(results['cost_breakdown']['total_regular_shifts'])}
Overtime Shifts: {int(results['cost_breakdown']['total_overtime_shifts'])}
Total Shifts: {int(results['cost_breakdown']['total_regular_shifts'] + results['cost_breakdown']['total_overtime_shifts'])}

{'='*60}
RISK SUMMARY
{'='*60}

Average Shortage: {results['scenario_df']['shortage_shifts'].mean():.2f} shifts
Maximum Shortage: {results['scenario_df']['shortage_shifts'].max():.0f} shifts
Standard Deviation: {results['scenario_df']['shortage_shifts'].std():.2f}

"""
        
        st.download_button(
            "⬇️ Download Full Report (TXT)",
            report_text,
            "optimization_report.txt",
            "text/plain",
            use_container_width=True
        )

else:
    # Welcome screen when no results
    st.info("""
    ### 👋 Welcome to the Nurse Scheduling Optimization System!
    
    This application uses advanced **Two-Stage Stochastic Programming** to create optimal nurse schedules 
    while managing uncertainty in patient demand.
    
    #### 🚀 Quick Start:
    1. **Choose your data source** in the left sidebar (Sample Data or Upload)
    2. **Configure cost parameters** and work rules
    3. **Select optimization model** (Cost-focused or Risk-aware)
    4. **Click "RUN OPTIMIZATION"** to generate schedules
    
    #### 📊 What You'll Get:
    - ✅ Optimal nurse work schedules
    - 💰 Detailed cost breakdowns
    - 📈 Coverage analysis
    - ⚠️ Risk assessments
    - 📄 Downloadable reports
    
    #### 🎯 Model Types:
    - **SDM (Stochastic Demand Model):** Minimizes total cost
    - **SDM-CVaR:** Minimizes cost while controlling worst-case shortage risk
    
    ---
    
    💡 **Tip:** Start with sample data to explore the system's capabilities!
    """)

# Footer
st.divider()
st.markdown("""
<div class="footer">
    <h2 style="color: #1a1a2e; margin-bottom: 1.5rem; font-size: 2rem;">Nurse Scheduling System</h2>
    <p style="font-size: 1.1rem; margin: 1rem 0; color: #4a5568;">
        <strong>Technology:</strong> Python • PuLP • Streamlit • HiGHS • Plotly
    </p>
    <p style="font-size: 1rem; color: #718096; margin: 1rem 0;">
        Two-Stage Stochastic Programming with CVaR Risk Management
    </p>
</div>
""", unsafe_allow_html=True)