import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import model_2  as m  # Back to using the unified model
# `model_oop` removed — use functional API in `model.py` instead
from io import BytesIO
import json
import base64
from solver_config import get_available_solvers, recommend_solver, get_installation_instructions

ASSETS_IMAGE_DIR = "assets/images"
HERO_BANNER_PATH = f"{ASSETS_IMAGE_DIR}/banner.png"
LOADING_GIF_PATH = f"{ASSETS_IMAGE_DIR}/loading.gif"

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Nurse Scheduler", 
    page_icon="🩺",  
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Engineering Interface
st.markdown("""
    <style>
     #MainMenu {visibility: hidden;}
     footer {visibility: hidden;}
    
    /* Global Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        --hover-gradient: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%);
        --bg-color: #f8fafc;
        --card-bg: #ffffff;
        --text-primary: #0f172a; /* Darker slate for better visibility */
        --text-secondary: #334155; /* Higher contrast slate */
    }

    html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Outfit', sans-serif;
        color: var(--text-primary) !important;
        background-color: var(--bg-color) !important;
    }
    
    /* Ensure all labels and text are visible */
    label[data-testid="stWidgetLabel"], .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown span {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    /* Force text color for Streamlit widgets */
    .stTextInput p, .stNumberInput p, .stSelectbox p, .stRadio p {
        color: var(--text-primary) !important;
    }
    
    /* Hero Section */
    .hero-wrapper {
        position: relative;
        height: 250px;
        border-radius: 20px;
        overflow: hidden;
        margin-bottom: 3rem;
        /* background-image set dynamically in python */
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .hero-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        /* Removed full overlay to focus on text background */
        background: transparent; 
        z-index: 1;
    }

    .hero-content {
        position: absolute;
        top: 0; 
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 2;
        padding: 2rem;
        background: rgba(15, 23, 42, 0.45); /* Dark blue overlay, adjusted for visibility */
        backdrop-filter: blur(4px);       /* Subtle blur to keep image visible but text readable */
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: none;
        border-radius: 0;
        box-shadow: none;
        max-width: none;
    }

    .hero-title {
        font-size: 4rem !important;
        font-weight: 800 !important;
        background: linear-gradient(to right, #ffffff, #e2e8f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 4px 12px rgba(0,0,0,0.1);
        letter-spacing: -0.03em !important;
    }

    .hero-subtitle {
        font-size: 1.5rem;
        color: #f8fafc;
        font-weight: 500;
        opacity: 0.9;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* Cards */
    .stMarkdown {
        border-radius: 1px; /* Reset */
    }
    
    div[data-testid="stExpander"] {
        background: var(--card-bg);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        overflow: hidden;
    }
    
    div[data-testid="stExpander"] > details > summary {
        font-weight: 600;
        color: var(--text-primary);
        padding: 1rem;
    }
    
    div[data-testid="stExpander"] > details > div {
        padding: 1.5rem;
        padding-top: 0;
    }

    /* Buttons - PRIMARY (Gradient) */
    .stButton > button[kind="primary"] {
        background: var(--primary-gradient) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        border-radius: 12px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3), 0 2px 4px -1px rgba(79, 70, 229, 0.15) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        width: 100%;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: var(--hover-gradient) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.4), 0 4px 6px -2px rgba(79, 70, 229, 0.2) !important;
    }

    .stButton > button[kind="primary"]:active {
        transform: translateY(0);
    }
    
    /* Buttons - SECONDARY (Default) */
    .stButton > button[kind="secondary"] {
        background: white !important;
        border: 1px solid #cbd5e1 !important;
        color: #475569 !important;
        font-weight: 500 !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        border-color: #94a3b8 !important;
        background: #f8fafc !important;
        color: #1e293b !important;
    }

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stDateInput input {
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }

    /* Force dark text for all sidebar elements to ensure visibility */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] li {
        color: #0f172a !important;
    }
    
    /* Exception: Keep primary button text white */
    [data-testid="stSidebar"] button[kind="primary"] p,
    [data-testid="stSidebar"] button[kind="primary"] span,
    [data-testid="stSidebar"] button[kind="primary"] div {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] label[data-testid="stWidgetLabel"] {
        color: #0f172a !important;
        font-weight: 600 !important;
    }
    
    /* Fix Expander Headers in Sidebar */
    [data-testid="stSidebar"] div[data-testid="stExpander"] > details > summary {
        color: #0f172a !important;
    }
    
    /* Feature Cards - Gradient & Premium */
    .feature-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem 1.5rem;
        text-align: center;
        height: 100%;
        border: 1px solid rgba(226, 232, 240, 0.8);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: var(--primary-gradient);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #cbd5e1;
    }
    
    .feature-card:hover::before {
        opacity: 1;
    }
    
    .feature-icon-wrapper {
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: center;
    }
    
    .feature-icon {
        font-size: 2rem;
        color: white;
        background: var(--primary-gradient);
        width: 64px;
        height: 64px;
        line-height: 64px;
        border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover .feature-icon {
        transform: scale(1.1) rotate(5deg);
    }
    
    .feature-title {
        font-size: 1.1rem;
        font-weight: 700; /* Bolder */
        margin-bottom: 0.5rem;
        color: #0f172a; /* Darker */
    }
    
    .feature-desc {
        font-size: 0.95rem;
        color: #334155; /* Darker for higher contrast */
        line-height: 1.6;
    }


    </style>
""", unsafe_allow_html=True)

# --- 2. TITLE & BRANDING ---
# Function to get base64 image
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

# Load banner image
hero_bg_base64 = get_base64_image(HERO_BANNER_PATH)

st.markdown(f"""
<style>
    /* Hero Section */
    .hero-wrapper {{
        background-image: url("data:image/png;base64,{hero_bg_base64}");
    }}
</style>
<div class="hero-wrapper">
    <div class="hero-overlay"></div>
    <div class="hero-content">
        <h1 class="hero-title">NURSE SCHEDULER</h1>
        <div class="hero-subtitle">Optimize • Analyze • Manage</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'prob' not in st.session_state:
    st.session_state.prob = None
if 'num_scenarios' not in st.session_state:
    st.session_state.num_scenarios = 5  # Default value


# --- 3. SIDEBAR FOR ALL USER INPUTS ---
with st.sidebar:
    # Sidebar header - clean and professional
    st.markdown("""
        <div style="text-align: center; padding: 0 0 2rem 0;">
            <h1 style="color: #1e293b; margin: 0; font-size: 2rem; font-weight: 700;">Configuration</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Data Source Selection
    st.header("Data Source")
    data_source = st.radio(
        "Choose data input method:",
        ["Use Sample Data (Quick Start)", "Upload Custom Data"],
        help="Sample data provides a pre-configured example. Upload for real scenarios."
    )
    
    nurses_list = None
    scenarios_df = None
    
    if data_source == "Use Sample Data (Quick Start)":
        st.success("Using sample data")
        
        col1, col2 = st.columns(2)
        with col1:
            num_nurses = st.number_input("Number of Nurses", 1, 200, 10, 1)
        with col2:
            num_days = st.number_input("Planning Days", 1, 90, 14, 1)
        
        num_scenarios = st.number_input(
            "Demand Scenarios", 
            1, 300, 
            st.session_state.get('num_scenarios', 5), 
            1
        )
        
        if st.button("🎲 Generate Sample Data", type="primary", use_container_width=True):
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
                # ============================================================
                # LOAD AND VALIDATE NURSE FILE (robust parsing)
                # Supports: one-name-per-line, single-line comma-separated list, or small CSV
                # ============================================================
                nurses_list = []
                try:
                        # Ensure file pointer is at start (uploaded file may have been read)
                        try:
                            nurse_file.seek(0)
                        except Exception:
                            pass

                        # First try: read with pandas (common case: one name per line)
                        try:
                            nurses_df = pd.read_csv(nurse_file, header=None)
                            # If dataframe has one column, assume one name per row
                            if nurses_df.shape[1] == 1:
                                nurses_list = nurses_df.iloc[:, 0].astype(str).tolist()
                            else:
                                # If multiple columns (e.g., single-row comma-separated), flatten values
                                vals = nurses_df.values.flatten()
                                nurses_list = [str(v).strip() for v in vals if str(v).strip()]
                        except pd.errors.EmptyDataError:
                            # re-raise to outer handler to use raw parsing
                            raise
                except pd.errors.EmptyDataError:
                    # File may be empty according to pandas or not standard CSV - fallthrough to raw parsing below
                    pass

                except Exception:
                    # Generic exception during pandas parsing — fall through to raw parsing
                    pass

                # ---------------------------
                # RAW PARSING FALLBACK
                # ---------------------------
                if not nurses_list:
                    try:
                        # Reset pointer then get raw bytes/text
                        try:
                            nurse_file.seek(0)
                        except Exception:
                            pass

                        # UploadedFile in Streamlit exposes getvalue(); try that first
                        if hasattr(nurse_file, 'getvalue'):
                            raw = nurse_file.getvalue()
                        else:
                            raw = nurse_file.read()

                        if isinstance(raw, (bytes, bytearray)):
                            try:
                                text = raw.decode('utf-8')
                            except Exception:
                                text = raw.decode('latin-1', errors='ignore')
                        else:
                            text = str(raw)

                        text = text.strip()
                        if not text:
                            nurses_list = []
                        else:
                            # If a single-line comma list, split on commas
                            if '\n' not in text and ',' in text:
                                nurses_list = [s.strip() for s in text.split(',') if s.strip()]
                            else:
                                # Use csv module to robustly parse rows (handles quoted values)
                                import csv
                                from io import StringIO
                                reader = csv.reader(StringIO(text))
                                rows = list(reader)
                                if not rows:
                                    nurses_list = []
                                else:
                                    # If each row is single column, take first col per row
                                    if all(len(r) == 1 for r in rows):
                                        nurses_list = [r[0].strip() for r in rows if r and r[0].strip()]
                                    else:
                                        # Flatten and dedupe
                                        flat = [cell.strip() for r in rows for cell in r if cell.strip()]
                                        nurses_list = flat
                    except Exception as e:
                        st.error(f"Failed to parse nurse file: {e}")
                        st.stop()

                # Final cleaning and validation
                nurses_list = [n for n in nurses_list if str(n).strip()]
                if len(nurses_list) == 0:
                    st.error("Nurse file is empty or could not be parsed. Ensure it contains one name per line or a comma-separated list.")
                    st.stop()

                # Check for duplicates

                # Check for duplicates and auto-remove
                duplicates = [name for name in set(nurses_list) if nurses_list.count(name) > 1]
                if duplicates:
                    st.warning(f"Duplicate nurse names found: {set(duplicates)}")
                    st.info("Automatically removing duplicates (keeping first occurrence)")
                    # Remove duplicates while preserving order
                    seen = set()
                    nurses_list = [x for x in nurses_list if not (x in seen or seen.add(x))]
                    st.success(f"Cleaned to {len(nurses_list)} unique nurses")
                st.success(f"Loaded {len(nurses_list)} nurses")
                
                # ============================================================
                # LOAD AND VALIDATE SCENARIO FILE
                # ============================================================
                scenarios_df = pd.read_csv(scenario_file)
                
                # Check required columns
                required_cols = ['scenario', 'day', 'shift', 'demand']
                missing_cols = [col for col in required_cols if col not in scenarios_df.columns]
                
                if missing_cols:
                    st.error(f"Scenario file missing required columns: {missing_cols}")
                    st.error(f"**Required columns:** {required_cols}")
                    st.error(f"**Found columns:** {list(scenarios_df.columns)}")
                    st.stop()
                
                # Check for empty dataframe
                if len(scenarios_df) == 0:
                    st.error("Scenario file is empty!")
                    st.stop()
                
                # Check for NaN values
                if scenarios_df.isnull().any().any():
                    null_counts = scenarios_df.isnull().sum()
                    null_cols = null_counts[null_counts > 0]
                    st.error(f"Scenario file contains missing values:")
                    for col, count in null_cols.items():
                        st.error(f"   - {col}: {count} missing values")
                    st.stop()
                
                # Check for negative demands
                if (scenarios_df['demand'] < 0).any():
                    negative_rows = scenarios_df[scenarios_df['demand'] < 0]
                    st.error(f"Found {len(negative_rows)} rows with negative demand!")
                    st.dataframe(negative_rows.head())
                    st.stop()
                
                # Validate data consistency
                num_scenarios = len(scenarios_df['scenario'].unique())
                num_days = len(scenarios_df['day'].unique())
                num_shifts = len(scenarios_df['shift'].unique())
                expected_rows = num_scenarios * num_days * num_shifts
                actual_rows = len(scenarios_df)
                
                if actual_rows != expected_rows:
                    st.warning(f"**Data completeness check:**")
                    st.warning(f"   - Expected rows: {expected_rows} ({num_scenarios} scenarios × {num_days} days × {num_shifts} shifts)")
                    st.warning(f"   - Actual rows: {actual_rows}")
                    st.warning(f"   - Missing or extra: {abs(expected_rows - actual_rows)} rows")
                    
                    if actual_rows < expected_rows:
                        st.error("Data appears incomplete! Some scenario/day/shift combinations are missing.")
                        
                        # Show which combinations are missing
                        from itertools import product
                        all_combos = set(product(
                            scenarios_df['scenario'].unique(),
                            scenarios_df['day'].unique(),
                            scenarios_df['shift'].unique()
                        ))
                        actual_combos = set(scenarios_df[['scenario', 'day', 'shift']].itertuples(index=False, name=None))
                        missing = all_combos - actual_combos
                        
                        if len(missing) <= 10:
                            st.error(f"**Missing combinations:** {missing}")
                        else:
                            st.error(f"**{len(missing)} combinations are missing** (showing first 10):")
                            st.error(str(list(missing)[:10]))
                
                st.success(f"Loaded {len(scenarios_df)} demand records")
                st.info(f"   Data structure: {num_scenarios} scenarios × {num_days} days × {num_shifts} shifts")
                
                # Store in session state for use in results display
                st.session_state.nurses_list = nurses_list
                st.session_state.scenarios_df = scenarios_df
                
            except Exception as e:
                st.error(f"Error loading files: {e}")
                st.exception(e)
                st.stop()
    
    st.divider()
    
    # --- Model Parameters ---
    st.header("Cost Parameters")
    
    with st.expander("Wage Costs", expanded=True):
        st.markdown("""
        **Cost hierarchy determines when each type is used:**
        - Stage 1: Regular ($c_1$) and Overtime ($c_2$) planned in advance
        - Stage 2: Emergency ($q^+$) used when actual demand exceeds plan
        
        💡 **Overtime vs Emergency:** 
        - Overtime is cheaper than emergency staff ($c_2 < q^+$)
        - The model will choose the optimal mix based on these costs and demand risk
        """)
        c1 = st.number_input("Regular Shift Cost ($c_1$)", 0.0, 10000.0, 100.0, 1.0)
        c2 = st.number_input("Overtime Shift Cost ($c_2$)", 0.0, 10000.0, 150.0, 1.0)
        q_plus = st.number_input("Emergency Shift Cost ($q^+$)", 0.0, 10000.0, 200.0, 1.0)
        q_minus = st.number_input("Shift Cancellation Cost ($q^-$)", 0.0, 100.0, 2.0, 1.0,
            help="Cost per cancelled shift (paper: q⁻=2). Set to 0 to ignore cancellation costs.")
    
    with st.expander("Quality Penalties (Soft Constraints)", expanded=False):
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
    
    with st.expander("Recourse Bounds (Optional)", expanded=False):
        st.caption("Limit emergency staffing and cancellations per shift (leave unchecked for unlimited)")
        
        enable_recourse_bounds = st.checkbox(
            "Enable recourse bounds",
            value=False,
            help="Add hard limits on emergency staff and cancellations"
        )
        
        if enable_recourse_bounds:
            col1, col2 = st.columns(2)
            with col1:
                max_emergency_staff = st.number_input(
                    "Max Emergency Staff per Shift",
                    1, 20, 5, 1,
                    help="Maximum additional nurses that can be added per shift (Constraint 17)"
                )
            with col2:
                max_cancellations = st.number_input(
                    "Max Cancellations per Shift",
                    1, 20, 3, 1,
                    help="Maximum shifts that can be cancelled per shift (Constraint 18)"
                )
        else:
            max_emergency_staff = float('inf')
            max_cancellations = float('inf')
    
    st.header("📋 Work Rules")
    
    with st.expander("Basic Shift Constraints", expanded=True):
        n1 = st.slider("Max Total Shifts ($n_1$)", 1, 30, 15, 1)
        n2 = st.slider("Max Night Shifts ($n_2$)", 0, 15, 5, 1)
        n3 = st.slider("Min Regular Shifts ($n_3$)", 0, 20, 5, 1)
        
        # Show overtime capacity info
        overtime_capacity = n1 - n3
        st.info(f"Overtime capacity: Up to {overtime_capacity} overtime shifts per nurse (= $n_1$ - $n_3$)")
        
    
    # NEW: Advanced constraints for university project
    with st.expander("Weekend Constraints (Advanced)", expanded=False):
        st.caption("Constraint 9: Minimum Complete Weekends Off")
        n4 = st.number_input(
            "Min Complete Weekends Off ($n_4$)", 
            0, 4, 0, 1,
            help="Number of complete weekends (Sat+Sun) each nurse must have off. Set to 0 to disable."
        )
        
        if n4 > 0:
            st.info("Weekend detection requires a start date")
            start_date = st.date_input(
                "Planning Period Start Date",
                help="Used to determine which days are weekends"
            )
            start_date_str = start_date.strftime('%Y-%m-%d')
        else:
            start_date_str = None
    
    with st.expander("Night Shift Rest Rules (Advanced)", expanded=False):
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
    
    with st.expander("Shift Type Quotas (Advanced)", expanded=False):
        st.caption("Constraints 2-5: Min/Max for each specific shift type")
        st.warning("Setting quotas can make the problem infeasible! Use carefully.")
        
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
                st.success(f"Quotas set for {len(shift_quotas)} shift types")
    
    st.divider()
    
    # --- Model Selection ---
    st.header("Optimization Model")
    
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
        with st.expander("Risk Parameters", expanded=True):
            sigma = st.slider(
                "Confidence Level (σ)", 
                0.90, 0.99, 0.95, 0.01,
                help="Higher = more conservative"
            )
            mu = st.number_input(
                "Max Acceptable Shortage (μ)", 
                0.0, 150.0, 5.0, 0.5,
                help="Maximum shortage in worst-case scenarios"
            )
    
    st.divider()
    
    # --- Fatigue Modeling ---
    st.header("Fatigue Modeling")
    
    enable_fatigue = st.checkbox(
        "Enable Fatigue Modeling",
        value=True,
        help="Include exponential fatigue model (Jaber et al., 2013) in optimization. "
             "When enabled, considers nurse fatigue accumulation and patient safety costs."
    )
    
    # Fatigue parameters (only shown if fatigue enabled)
    if enable_fatigue:
        with st.expander("Fatigue Parameters", expanded=False):
            st.caption("Configure the exponential fatigue model: F(t) = 1 - e^(-λt)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                lambda_param = st.number_input(
                    "Fatigue Rate (λ)",
                    0.01, 0.10, 0.03, 0.01,
                    help="Rate of fatigue accumulation. Default: 0.03 from Jaber et al. (2013)"
                )
                
                patient_safety_weight = st.number_input(
                    "Patient Safety Weight ($)",
                    0.0, 200.0, 50.0, 5.0,
                    help="Cost per unit of fatigue (penalty for patient safety risk)"
                )
            
            with col2:
                max_fatigue_threshold = st.slider(
                    "Max Fatigue Threshold",
                    0.50, 0.90, 0.70, 0.05,
                    help="Maximum allowed fatigue level (0=fresh, 1=exhausted). Nurses cannot exceed this."
                )
                
                shift_duration = st.number_input(
                    "Shift Duration (hours)",
                    6, 16, 12, 1,
                    help="Duration of each shift in hours"
                )
            
            st.info(f"PWL Approximation: Using 8 segments (0.713% max error, 0.398% avg error)")
    else:
        # Set defaults when fatigue disabled
        lambda_param = 0.03
        patient_safety_weight = 0.0  # Key: weight=0 effectively disables fatigue cost
        max_fatigue_threshold = 0.70
        shift_duration = 12
        
        st.warning("Fatigue modeling disabled. The system will optimize costs without considering nurse fatigue or patient safety.")
    
    st.divider()
    
    # --- Solver Selection ---
    st.header("Solver Configuration")
    
    from solver_config import auto_select_solver, get_available_solvers
    
    # Get available solvers
    available_solvers = get_available_solvers()
    
    # Create list of working solvers
    working_solvers = ['AUTO (Recommended)']
    solver_details = {}
    
    for name, info in available_solvers.items():
        if info['available']:
            working_solvers.append(name)
            solver_details[name] = info
    
    # Solver selection dropdown
    solver_choice = st.selectbox(
        "Select Solver:",
        working_solvers,
        help="AUTO automatically selects the fastest available solver. Manual selection available if you encounter issues."
    )
    
    # Determine which solver to use
    if solver_choice == 'AUTO (Recommended)':
        selected_solver = auto_select_solver()
        st.info(f"Auto-selected: {selected_solver} ({solver_details.get(selected_solver, {}).get('speed', 'Standard')})")
    else:
        selected_solver = solver_choice
        st.success(f"Using: {selected_solver}")
    
    st.divider()
    
    # --- Solve Button ---
    st.markdown("### Generate Schedule")
    st.markdown("")  # Spacing
    
    if nurses_list is None or scenarios_df is None:
        st.warning("Please configure your data in the sidebar first")
        st.button("⚡ Optimize Schedule", type="primary", use_container_width=True, disabled=True)
        solve_button = False
    else:
        st.success(f"Ready: {len(nurses_list)} nurses • {len(scenarios_df)} scenarios")
        st.markdown("")  # Spacing
        
        solve_button = st.button(
            "⚡ Optimize Schedule",  
            type="primary", 
            use_container_width=True,
            help="Generate optimal nurse schedule"
        )




# --- 4. MAIN CONTENT AREA ---
# --- SIDEBAR FALLBACK (handles intermittent missing sidebar) ---
# Some Streamlit layouts or client-side collapses can make the sidebar
# appear hidden to users. If the sidebar variables were not set (which
# is a common symptom), show a compact fallback settings expander in
# the main page so the app remains usable.
if ('data_source' not in locals()) and ('data_source' not in st.session_state):
    st.warning("⚙️ Settings sidebar not detected — showing quick settings here.")

    with st.expander("Quick Settings (Sidebar fallback)", expanded=True):
        fb_data_source = st.radio(
            "Choose data input method:",
            ["Use Sample Data (Quick Start)", "Upload Custom Data"],
            key="fb_data_source"
        )

        if fb_data_source == "Use Sample Data (Quick Start)":
            st.caption("Quick sample-data controls (same defaults as sidebar)")
            fb_num_nurses = st.number_input("Number of Nurses", 5, 200, 10, 1, key="fb_num_nurses")
            fb_num_days = st.number_input("Planning Days", 7, 90, 14, 1, key="fb_num_days")
            fb_num_scenarios = st.slider("Demand Scenarios", 3, 300, 5, 1, key="fb_num_scenarios")

            if st.button("🎲 Generate Sample Data (Fallback)", type="primary", key="fb_generate"):
                try:
                    nurses_list, scenarios_df = m.generate_sample_data(fb_num_nurses, fb_num_days, fb_num_scenarios)
                    st.session_state.nurses_list = nurses_list
                    st.session_state.scenarios_df = scenarios_df
                    st.success(f"Generated {len(nurses_list)} nurses with {len(scenarios_df)} demand records!")
                except Exception as e:
                    st.error(f"Failed to generate sample data: {e}")
        else:
            st.info("If you need to upload custom files, please open the sidebar (click the ⋮ menu at top-left if hidden) and use the Upload option there.")

# --- LANDING PAGE CARDS (Moved to Main Area) ---
# Display only if we haven't solved yet and don't have results
if not solve_button and 'results' in st.session_state and st.session_state.results is None:
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem; margin-top: 1rem;">
        <h2 style="font-size: 2rem; background: var(--primary-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Powerful Features</h2>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">Everything you need to optimize your workforce</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Row 1
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon-wrapper"><div class="feature-icon">📊</div></div>
            <div class="feature-title">Data Driven</div>
            <div class="feature-desc">Upload your own data or use our smart sample generator to model complex staffing scenarios instantly.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon-wrapper"><div class="feature-icon">⚡</div></div>
            <div class="feature-title">Fast Solver</div>
            <div class="feature-desc">Powered by advanced algorithms to find the optimal schedule in seconds, minimizing costs and conflicts.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon-wrapper"><div class="feature-icon">🛡️</div></div>
            <div class="feature-title">Risk Aware</div>
            <div class="feature-desc">Manage uncertainty with CVaR optimization to robustly handle unexpected demand spikes.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 2
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon-wrapper"><div class="feature-icon">✨</div></div>
            <div class="feature-title">Fatigue Model</div>
            <div class="feature-desc">Ensure patient safety by tracking nurse fatigue levels with our exponential fatigue modeling system.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon-wrapper"><div class="feature-icon">📈</div></div>
            <div class="feature-title">Visual Analytics</div>
            <div class="feature-desc">Interactive charts and heatmaps provide deep insights into schedule quality and resource allocation.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col6:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon-wrapper"><div class="feature-icon">📄</div></div>
            <div class="feature-title">Export Reports</div>
            <div class="feature-desc">Download professional Excel and PDF reports ready for administrative review and distribution.</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)


if solve_button and nurses_list is not None and scenarios_df is not None:
    
    # Build model parameters (filter out None values to use defaults)
    model_params = {
        'c1': c1, 'c2': c2, 'q_plus': q_plus, 'q_minus': q_minus,
        'c3': c3, 'c4': c4,  # Soft constraint penalties
        'n1': n1, 'n2': n2, 'n3': n3,
        
        # Fatigue modeling parameters (LFFR Model - Jaber et al. 2013)
        'patient_safety_enabled': enable_fatigue,  # KEY FLAG - enables fatigue constraints
        'fatigue_lambda': lambda_param,  # λ: Fatigue accumulation rate
        'recovery_mu': 0.05,  # μ': Recovery rate (faster than fatigue)
        'patient_safety_weight': patient_safety_weight,
        'max_fatigue_threshold': max_fatigue_threshold,
        'shift_duration': shift_duration,
        
        # Advanced constraints (NEW for university project)
        'n4': n4,
        'shift_quotas': shift_quotas,
        'night_rest_enabled': night_rest_enabled,
        'min_consecutive_nights': min_consecutive_nights,
        'days_off_after_nights': days_off_after_nights,
        
        # Recourse bounds (Constraints 17-18 from paper)
        'max_emergency_staff': max_emergency_staff,
        'max_cancellations': max_cancellations,
    }
    
    # Add optional parameters only if they are not None (to use defaults from ModelParameters)
    if sigma is not None:
        model_params['sigma'] = sigma
    if mu is not None:
        model_params['mu'] = mu
    if start_date_str is not None:
        model_params['start_date'] = start_date_str
    
    # ============================================================================
    # VALIDATE PARAMETERS BEFORE OPTIMIZATION
    # ============================================================================
    st.markdown("### 🔍 Validating Parameters...")
    
    errors, warnings = m.validate_parameters(model_params, nurses_list, scenarios_df)
    
    # Display errors (blocking)
    if errors:
        st.error("### ❌ Validation Errors - Cannot Proceed")
        for error in errors:
            st.error(error)
        st.info("💡 **Fix the errors above and try again.**")
        st.stop()  # Stop execution - don't run optimization
    
    # Display warnings (non-blocking)
    if warnings:
        st.warning("### ⚠️ Parameter Warnings")
        for warning in warnings:
            st.warning(warning)
        st.info("💡 **These are warnings, not errors.** The model will still run, but results may not be optimal.")
    else:
        st.success("✅ All parameters validated successfully!")
    
    st.markdown("")  # Spacing
    
    # Show warning if advanced constraints are enabled
    advanced_enabled = []
    if n4 > 0:
        advanced_enabled.append(f"Minimum {n4} complete weekends off")
    if shift_quotas:
        advanced_enabled.append(f"Shift type quotas for {len(shift_quotas)} shift types")
    if night_rest_enabled:
        advanced_enabled.append(f"Night rest rules ({min_consecutive_nights} consecutive, {days_off_after_nights} days off after)")
    if max_emergency_staff < float('inf') or max_cancellations < float('inf'):
        bounds_info = []
        if max_emergency_staff < float('inf'):
            bounds_info.append(f"max {int(max_emergency_staff)} emergency staff/shift")
        if max_cancellations < float('inf'):
            bounds_info.append(f"max {int(max_cancellations)} cancellations/shift")
        advanced_enabled.append(f"Recourse bounds ({', '.join(bounds_info)})")
    
    if advanced_enabled:
        st.info("🎓 **Advanced Constraints Enabled:**\n" + "\n".join(f"- {item}" for item in advanced_enabled))
        st.warning("⚠️ Advanced constraints may increase solve time and reduce feasibility. If solver fails, try relaxing some constraints.")
    
    # Solve
    
    # Solve
    
    
    # Enhanced progress indicator
    progress_placeholder = st.empty()
    with progress_placeholder.container():
        # --- Robust GIF display ---
        import base64
        import os
        
        gif_html = ""
        try:
            # Read the GIF file and encode it in base64
            with open(LOADING_GIF_PATH, "rb") as f:
                gif_bytes = f.read()
            gif_base64 = base64.b64encode(gif_bytes).decode("utf-8")
            gif_html = f'<img src="data:image/gif;base64,{gif_base64}" alt="loading" width="150">'
        except Exception:
            # Fallback emoji if GIF is not found
            gif_html = '<div style="font-size: 5rem;">⚡</div>'

        # Combine everything into a single HTML block for correct rendering
        st.markdown(f"""
        <div style="background: #667eea; border-radius: 16px; padding: 2rem; margin: 2rem 0; display: flex; align-items: center;">
            <div style="flex: 1; text-align: center; padding-right: 1rem;">
                {gif_html}
            </div>
            <div style="flex: 2; text-align: left;">
                <h1 style="color: white; font-size: 2.5rem; margin: 0;">Optimizing...</h1>
                <p style="color: white; font-size: 1.3rem; opacity: 0.9; margin-top: 0.5rem;">Building model and finding optimal solution</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ============================================================================
    # SOLVE MODEL WITH COMPREHENSIVE ERROR HANDLING
    # ============================================================================
    try:
        import time
        import traceback
        
        # Time the model building and solving
        start_time = time.time()
        
        try:
            # Use the functional API in `model.py` to build and solve the model.
            # This avoids dependency on the legacy `model_oop` module.
            prob, status = m.build_and_solve_model(
                nurses_list,
                scenarios_df,
                model_params,
                model_type=model_type_code,
                solver_name=selected_solver
            )

            # If the selected solver did not return an optimal solution and
            # we didn't already try CBC, attempt a single fallback to CBC.
            if status != "Optimal" and selected_solver != 'CBC':
                st.warning(f"⚠️ {selected_solver} did not return Optimal (status: {status}). Trying CBC as fallback...")
                prob, status = m.build_and_solve_model(
                    nurses_list,
                    scenarios_df,
                    model_params,
                    model_type=model_type_code,
                    solver_name='CBC'
                )
        except MemoryError:
            progress_placeholder.empty()
            
            st.error("❌ **Out of Memory Error**")
            st.error("### The problem is too large for available memory")
            st.warning("""
            **Possible solutions:**
            1. 🔻 Reduce number of nurses
            2. 🔻 Reduce planning period (number of days)
            3. 🔻 Reduce number of scenarios
            4. 🔻 Disable advanced constraints
            5. 💻 Try running on a machine with more RAM
            """)
            st.stop()
            
        except ImportError as e:
            progress_placeholder.empty()
            
            st.error(f"❌ **Import Error:** {e}")
            st.error("### Missing required package")
            st.warning("""
            **Fix:** Run this command in your terminal:
            ```bash
            pip install --upgrade -r requirements.txt
            ```
            """)
            st.stop()
            
        except Exception as solver_error:
            # Log the full error for debugging
            error_details = traceback.format_exc()
            
            progress_placeholder.empty()
            
            st.error(f"❌ **Solver Error:** {type(solver_error).__name__}")
            st.error(f"### {str(solver_error)}")
            
            # Check for common solver issues
            error_str = str(solver_error).lower()
            
            if 'solver' in error_str and 'not found' in error_str:
                st.warning("""
                **Solver Not Found**
                
                The selected solver is not installed on your system.
                
                **Quick Fix:**
                1. Go back to solver selection
                2. Choose "AUTO" to automatically select an available solver
                3. Or install the solver following instructions in the sidebar
                """)
            elif 'license' in error_str:
                st.warning("""
                **License Error**
                
                Commercial solvers (Gurobi, CPLEX) require valid licenses.
                
                **Solutions:**
                1. Use FREE solvers: HiGHS or CBC (select "AUTO")
                2. Obtain academic license if you're a student/researcher
                3. Purchase commercial license
                """)
            else:
                # Show expandable error details for debugging
                with st.expander("🐛 Technical Error Details (for debugging)"):
                    st.code(error_details, language='python')
                
                st.info("""
                **Troubleshooting Steps:**
                1. Try reducing problem size
                2. Try different solver (select "AUTO")
                3. Check your data for unusual values
                4. Disable advanced constraints
                5. Contact support with the error details above
                """)
            
            st.stop()
        
        solve_time = time.time() - start_time
        
        # Clear progress indicator
        progress_placeholder.empty()
        
        if status == "Optimal":
            st.success(f"✅ **Optimization Complete!** Status: **{status}** (Solver: {selected_solver}, Time: {solve_time:.1f}s)")
            
            # Extract results - Use OOP get_results() if model exists, otherwise fallback to functional
            extract_start = time.time()
            # Prefer OOP results if available, otherwise use functional extractor
            model_obj = locals().get('model', None)
            if model_obj is not None and hasattr(model_obj, 'get_results'):
                results_obj = model_obj.get_results()
                # If get_results returns an object with to_dict(), use it
                if hasattr(results_obj, 'to_dict'):
                    results = results_obj.to_dict()
                else:
                    results = results_obj
            elif prob is not None:
                # Functional approach: extract results from PuLP problem
                results = m.extract_results(prob, nurses_list, scenarios_df, model_params, model_type_code)
            else:
                raise RuntimeError("No valid model or problem object available")
            extract_time = time.time() - extract_start
            st.session_state.results = results
            
            # Show timing breakdown
            st.info(f"⏱️ **Performance:** Solving: {solve_time:.1f}s | Results extraction: {extract_time:.1f}s | Total: {solve_time + extract_time:.1f}s")
            st.session_state.prob = prob
            st.session_state.model_params = model_params
            
            # ================================================================
            # VALIDATE RESULTS
            # ================================================================
            st.markdown("### ✅ Validating Results...")
            
            if results is not None:
                result_errors, result_warnings = m.validate_results(results, model_params)
            else:
                result_errors = ["Results extraction returned None"]
                result_warnings = []
            
            # Display errors (should not happen if solver is correct)
            if result_errors:
                st.error("### ❌ Result Validation Errors")
                st.error("**Critical constraint violations detected!** This may indicate a solver bug or model issue.")
                for error in result_errors:
                    st.error(error)
            
            # Display warnings (potential issues worth noting)
            if result_warnings:
                with st.expander("⚠️ Result Validation Warnings (click to expand)"):
                    for warning in result_warnings:
                        st.warning(warning)
            
            # Show success if no issues
            if not result_errors and not result_warnings:
                st.success("✅ All constraints validated - results look good!")
            elif not result_errors:
                st.success("✅ All critical constraints satisfied")
            
            st.markdown("")  # Spacing
            
        else:
            # ================================================================
            # INFEASIBILITY DIAGNOSTICS
            # ================================================================
            st.error(f"❌ **Solver Status: {status}**")
            st.error("### The model could not find an optimal solution.")
            
            st.markdown("---")
            st.warning("### 🔍 Diagnostic Checklist")
            
            # Calculate diagnostic metrics
            num_nurses = len(nurses_list)
            num_days = len(scenarios_df['day'].unique())
            num_scenarios = len(scenarios_df['scenario'].unique())
            total_capacity = num_nurses * n1
            
            # Demand analysis
            total_demand_per_scenario = scenarios_df.groupby('scenario')['demand'].sum()
            avg_demand = total_demand_per_scenario.mean()
            max_demand = total_demand_per_scenario.max()
            
            # Daily demand (max across all scenarios)
            max_daily_demand = scenarios_df.groupby(['scenario', 'day'])['demand'].sum().max()
            
            # Display diagnostics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💼 Demand vs Capacity")
                utilization = avg_demand / total_capacity * 100 if total_capacity > 0 else 0
                st.info(f"""
                - **Average Total Demand:** {avg_demand:.0f} shifts/scenario
                - **Maximum Total Demand:** {max_demand:.0f} shifts/scenario
                - **Max Daily Demand:** {max_daily_demand:.0f} shifts/day
                - **Utilization:** {utilization:.1f}%
                """)
                
                if max_daily_demand > total_capacity:
                    st.error(f"⚠️ **Max daily demand ({max_daily_demand:.0f}) exceeds capacity ({total_capacity})!**")
                
                st.markdown("#### ⚙️ Constraint Tightness")
                st.info(f"""
                - **Max total shifts (n₁):** {n1}
                - **Min regular shifts (n₃):** {n3}
                - **Max night shifts (n₂):** {n2}
                - **Constraint ratio (n₃/n₁):** {n3/n1*100:.0f}%
                """)
                
                if n3/n1 > 0.8:
                    st.error("⚠️ **Very tight constraint:** n₃ is {:.0f}% of n₁".format(n3/n1*100))
                
                # Advanced constraints
                if n4 > 0:
                    max_weekends = num_days // 7
                    st.info(f"""
                    **Weekend Constraint:**
                    - Required weekends off: {n4}
                    - Max possible: {max_weekends}
                    """)
                    if n4 > max_weekends:
                        st.error(f"⚠️ **Impossible:** Need {n4} weekends in {num_days} days!")
                
                if shift_quotas:
                    st.info(f"**Shift Quotas:** {len(shift_quotas)} types constrained")
                    quota_sum = sum(q.get('min', 0) for q in shift_quotas.values())
                    if quota_sum > n1:
                        st.error(f"⚠️ **Quota conflict:** Sum of mins ({quota_sum}) > n₁ ({n1})")
            
            st.markdown("---")
            st.success("### 💡 Suggested Actions")
            
            suggestions = []
            
            # Suggestion 1: Check capacity
            if max_daily_demand > total_capacity:
                suggestions.append("🔴 **Add more nurses** or **increase n₁** (max shifts) - demand exceeds capacity!")
            
            # Suggestion 2: Relax min shifts
            if n3/n1 > 0.7:
                suggestions.append(f"🟡 **Reduce n₃** (min regular shifts) from {n3} to {int(n1*0.6)} or lower")
            
            # Suggestion 3: Relax night shifts
            if n2/n1 < 0.3:
                suggestions.append(f"🟡 **Increase n₂** (max night shifts) from {n2} to {int(n1*0.4)} or higher")
            
            # Suggestion 4: Weekend constraints
            if n4 > 0:
                max_weekends = num_days // 7
                if n4 >= max_weekends:
                    suggestions.append(f"🔴 **Reduce n₄** (weekend requirement) from {n4} to {max(0, max_weekends-1)}")
            
            # Suggestion 5: Shift quotas
            if shift_quotas:
                suggestions.append("🟡 **Disable shift quotas** temporarily to test feasibility")
            
            # Suggestion 6: Night rest
            if night_rest_enabled:
                suggestions.append("🟡 **Disable night rest constraints** temporarily")
            
            # Suggestion 7: Reduce scenarios
            if num_scenarios > 10:
                suggestions.append(f"🟢 **Reduce scenarios** from {num_scenarios} to 5-10 for faster testing")
            
            # General suggestion
            suggestions.append("🟢 **Try default parameters** first, then gradually add constraints")
            
            for i, suggestion in enumerate(suggestions, 1):
                st.markdown(f"{i}. {suggestion}")
            
            st.markdown("---")
            st.info("""
            ### 📚 Understanding Infeasibility
            
            **Infeasible** means there's no way to satisfy all constraints simultaneously. Common causes:
            
            - **Too much demand** for available nurses
            - **Conflicting constraints** (e.g., min shifts > max shifts)
            - **Impossible requirements** (e.g., more weekends off than exist)
            - **Over-constrained quotas** (too many min/max rules)
            
            **Fix approach:**
            1. Start with minimal constraints
            2. Add constraints one-by-one
            3. Test after each addition
            4. Identify which constraint breaks feasibility
            """)
            
            # Stop execution to prevent showing welcome message
            st.stop()
            
    except Exception as e:
        # Final catch-all for unexpected errors
        import traceback
        
        progress_placeholder.empty()
        
        st.error("❌ **Unexpected Error**")
        st.error(f"### {type(e).__name__}: {str(e)}")
        
        error_details = traceback.format_exc()
        
        with st.expander("🐛 Full Error Traceback (for debugging)"):
            st.code(error_details, language='python')
        
        st.warning("""
        **This is an unexpected error. Please:**
        1. Check the error details above
        2. Try reducing problem size
        3. Try using sample data first
        4. Report this error if it persists
        """)

# --- 5. DISPLAY RESULTS ---
# Predeclare `tabs` to satisfy static analysis tools that may warn
# about forward references in complex files. It is assigned later
# when results are available.
tabs = None
if st.session_state.results is not None:
    results = st.session_state.results
    model_params = st.session_state.get('model_params', {})
    
    # Key Metrics at the top
    st.header("📊 Summary Metrics")
    
    # Calculate demand statistics for better context
    scenarios_df = st.session_state.get('scenarios_df')
    nurses_list = st.session_state.get('nurses_list', [])
    
    if scenarios_df is not None:
        total_demand = scenarios_df['demand'].sum()
        num_scenarios = len(scenarios_df['scenario'].unique())
        avg_demand_per_scenario = total_demand / num_scenarios
    else:
        avg_demand_per_scenario = 0
    
    st.divider()

    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Cost",
            f"${results['cost_breakdown']['total_cost']:,.0f}",
            help="Total optimization cost inclusive of regular, overtime, and expected recourse costs."
        )
    
    with col2:
        st.metric(
            "Expected Shortage",
            f"{results.get('expected_shortage', 0):.1f} nurses",
            help="Average understaffing across all scenarios."
        )

    # Secondary metrics for Fatigue if enabled
    if results.get('fatigue_metrics', {}).get('enabled'):
        st.write("---")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.metric("Average Fatigue", f"{results['fatigue_metrics'].get('avg_fatigue', 0):.2f}")
        with f_col2:
            st.metric("Peak Fatigue", f"{results['fatigue_metrics'].get('max_fatigue', 0):.2f}")
    
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

        # --- Advanced Weekend Highlighting ---
        styler = roster_df.style
        start_date_str = model_params.get('start_date')
        weekend_cols = []
        complete_weekends = [] # List of (saturday_col, sunday_col) tuples

        # Define the highlighting function early so it's always available
        def highlight_off_weekends(row):
            # Default style is empty
            styles = pd.Series('', index=row.index)
            for sat_col, sun_col in complete_weekends:
                if sat_col in row.index and sun_col in row.index:
                    if row[sat_col] == 'OFF' and row[sun_col] == 'OFF':
                        styles[sat_col] = 'background-color: #fff8c4' # Light yellow
                        styles[sun_col] = 'background-color: #fff8c4' # Light yellow
            return styles

        if start_date_str:
            try:
                from datetime import datetime, timedelta
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                
                day_cols = [col for col in roster_df.columns if col.startswith("D") and col[1:].isdigit()]
                day_nums_sorted = sorted([int(col[1:]) for col in day_cols])

                # 1. Identify all weekend columns (for general column highlight)
                for day_num in day_nums_sorted:
                    current_date = start_date + timedelta(days=day_num - 1)
                    # 5 = Saturday, 6 = Sunday
                    if current_date.weekday() >= 5:
                        weekend_cols.append(f"D{day_num}")

                # 2. Identify complete weekend pairs (for specific cell highlight)
                for i in range(len(day_nums_sorted) - 1):
                    day1_num, day2_num = day_nums_sorted[i], day_nums_sorted[i+1]
                    date1 = start_date + timedelta(days=day1_num - 1)
                    date2 = start_date + timedelta(days=day2_num - 1)
                    if date1.weekday() == 5 and date2.weekday() == 6 and (day2_num - day1_num == 1):
                        complete_weekends.append((f"D{day1_num}", f"D{day2_num}"))

                # 3. Apply a light purple background to all weekend columns
                if weekend_cols:
                    styler = styler.set_properties(
                        subset=weekend_cols, 
                        **{'background-color': '#f5f3ff', 'font-weight': 'bold'}
                    )

                # 4. Apply the cell-specific highlighting
                if complete_weekends:
                    styler = styler.apply(highlight_off_weekends, axis=1)

            except Exception as e:
                st.warning(f"Could not highlight weekends: {e}")
        
        if show_summary:
            st.dataframe(
                styler,
                use_container_width=True,
                height=400
            )
        else:
            # Hide summary columns - show only day columns (D1, D2, D3, etc.)
            day_cols = [col for col in roster_df.columns if col.startswith("D") and col[1:].isdigit()]
            # When hiding columns, we need to re-apply the styles to the subsetted dataframe
            display_df = roster_df[["Nurse"] + day_cols].copy()
            styler = display_df.style
            if weekend_cols:
                 styler = styler.set_properties(
                    subset=[c for c in weekend_cols if c in display_df.columns], 
                    **{'background-color': '#f5f3ff', 'font-weight': 'bold'})
            if complete_weekends:
                styler = styler.apply(highlight_off_weekends, axis=1)

            st.dataframe(
                styler,
                use_container_width=True,
                height=400
            )
        
        # Download roster - Multiple formats
        st.subheader("💾 Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV download
            csv_roster = roster_df.to_csv(index=False)
            st.download_button(
                "⬇️ CSV Format",
                csv_roster,
                "nurse_roster.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            # Excel download
            from openpyxl.utils import get_column_letter
            
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                roster_df.to_excel(writer, sheet_name='Roster', index=False)
                # Auto-adjust column widths
                worksheet = writer.sheets['Roster']
                for idx, col in enumerate(roster_df.columns, start=1):
                    max_length = max(
                        roster_df[col].astype(str).apply(len).max(),
                        len(col)
                    ) + 2
                    column_letter = get_column_letter(idx)
                    worksheet.column_dimensions[column_letter].width = min(max_length, 20)
            
            st.download_button(
                "⬇️ Excel Format",
                excel_buffer.getvalue(),
                "nurse_roster.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col3:
            # Placeholder for heatmap image (will add after creating the heatmap)
            st.write("")  # Spacing
        
        # Roster heatmap
        st.subheader("📊 Shift Distribution Heatmap")
        
        # Prepare data for heatmap - get day columns (D1, D2, D3, etc.)
        day_cols = [col for col in roster_df.columns if col.startswith("D") and col[1:].isdigit()]
        heatmap_data = roster_df[["Nurse"] + day_cols].set_index("Nurse")
        
        # Convert shift labels to full descriptive names for better readability
        shift_names = {
            'OFF': 'Off Day',
            'E': 'Early Shift',
            'D': 'Day Shift',
            'L': 'Late Shift',
            'N': 'Night Shift',
            'E (OT)': 'Early (Overtime)',
            'D (OT)': 'Day (Overtime)',
            'L (OT)': 'Late (Overtime)',
            'N (OT)': 'Night (Overtime)'
        }
        
        # Create descriptive heatmap data for display
        heatmap_display = heatmap_data.replace(shift_names)
        
        # Let user choose color mode: discrete (categorical shifts) or perceptual sequential
        color_mode = st.radio(
            "Heatmap color mode",
            options=["Discrete (categorical shifts)", "Perceptual (Viridis)"],
            index=0,
            horizontal=True
        )

        # Discrete mapping: map every distinct shift label to an integer code
        shift_categories = [
            'Off Day', 'Early Shift', 'Early (OT)', 'Day Shift', 'Day (OT)',
            'Late Shift', 'Late (OT)', 'Night Shift', 'Night (OT)'
        ]
        # Map original raw labels to display names (must match heatmap_display mapping above)
        raw_to_display = {
            'OFF': 'Off Day', 'E': 'Early Shift', 'E (OT)': 'Early (OT)',
            'D': 'Day Shift', 'D (OT)': 'Day (OT)', 'L': 'Late Shift',
            'L (OT)': 'Late (OT)', 'N': 'Night Shift', 'N (OT)': 'Night (OT)'
        }

        # Initialize category_colors for discrete mode (used in colorbar later)
        category_colors = [
            '#ffffff',  # 0: Off Day (white - stands out clearly)
            '#87CEEB',  # 1: Early (sky blue - morning)
            '#4682B4',  # 2: Early (OT) (steel blue - darker morning)
            '#FFD700',  # 3: Day (gold - bright daytime)
            '#FFA500',  # 4: Day (OT) (orange - darker day)
            '#FF8C00',  # 5: Late (dark orange - evening)
            '#FF6347',  # 6: Late (OT) (tomato - darker evening)
            '#8B008B',  # 7: Night (dark magenta - nighttime)
            '#4B0082',  # 8: Night (OT) (indigo - darker night)
        ]

        # Build numeric matrix according to selected mode
        if color_mode == "Perceptual (Viridis)":
            # Backwards-compatible mapping to numeric continuum (keeps earlier behavior)
            shift_map = {'OFF': 0, 'E': 1, 'D': 2, 'L': 3, 'N': 4,
                         'E (OT)': 1.5, 'D (OT)': 2.5, 'L (OT)': 3.5, 'N (OT)': 4.5}
            heatmap_numeric = heatmap_data.replace(shift_map)

            fig_heatmap = px.imshow(
                heatmap_numeric,
                labels=dict(x="Day", y="Nurse", color="Shift Type"),
                x=day_cols,
                y=heatmap_data.index,
                color_continuous_scale="Viridis",
                aspect="auto",
                title="Nurse Schedule - Color-Coded Heatmap"
            )
        else:
            # Discrete categorical mode: assign integer codes 0..N-1
            cat_map = {raw: idx for idx, raw in enumerate(['OFF', 'E', 'E (OT)', 'D', 'D (OT)', 'L', 'L (OT)', 'N', 'N (OT)'])}
            heatmap_numeric = heatmap_data.replace(cat_map)

            # Build a stepped colorscale so each integer maps to a solid color block
            n = len(category_colors)
            stepped_colorscale = []
            for i, col in enumerate(category_colors):
                start = i / n
                end = (i + 1) / n
                stepped_colorscale.append([start, col])
                stepped_colorscale.append([end, col])

            fig_heatmap = px.imshow(
                heatmap_numeric,
                labels=dict(x="Day", y="Nurse", color="Shift Type"),
                x=day_cols,
                y=heatmap_data.index,
                color_continuous_scale=stepped_colorscale,
                zmin=-0.5,
                zmax=n - 0.5,
                aspect="auto",
                title="Nurse Schedule - Color-Coded Heatmap (Discrete)"
            )

        # --- Add highlighting to heatmap for OFF weekends ---
        if start_date_str and complete_weekends:
            heatmap_x_axis = day_cols
            heatmap_y_axis = list(heatmap_data.index)

            for nurse_idx, nurse_name in enumerate(heatmap_y_axis):
                nurse_row = roster_df[roster_df['Nurse'] == nurse_name].iloc[0]
                for sat_col, sun_col in complete_weekends:
                    if sat_col in nurse_row and sun_col in nurse_row:
                        if nurse_row[sat_col] == 'OFF' and nurse_row[sun_col] == 'OFF':
                            try:
                                sat_x_idx = heatmap_x_axis.index(sat_col)
                                fig_heatmap.add_shape(
                                    type="rect",
                                    xref="x", yref="y",
                                    x0=sat_x_idx - 0.5, y0=nurse_idx - 0.5,
                                    x1=sat_x_idx + 1.5, y1=nurse_idx + 0.5, # Span 2 days
                                    line=dict(color="gold", width=3),
                                    fillcolor="yellow",
                                    opacity=0.3,
                                    layer="above"
                                )
                            except (ValueError, IndexError):
                                pass # Day not in heatmap axis
        
        # Update hover template to show descriptive shift names
        fig_heatmap.update_traces(
            customdata=heatmap_display.values,
            hovertemplate='<b>%{y}</b><br>Day: %{x}<br>Shift: %{customdata}<extra></extra>',
            xgap=1,  # Add horizontal gap between cells
            ygap=1   # Add vertical gap between cells
        )
        
        # Update colorbar ticks/labels depending on chosen mode
        if color_mode == "Perceptual (Viridis)":
            fig_heatmap.update_coloraxes(
                colorbar=dict(
                    tickmode='array',
                    tickvals=[0, 1, 2, 3, 4],
                    ticktext=['Off Day', 'Early', 'Day', 'Late', 'Night']
                )
            )
        else:
            # Discrete mode: show all category ticks
            fig_heatmap.update_coloraxes(
                colorbar=dict(
                    tickmode='array',
                    tickvals=list(range(len(category_colors))),
                    ticktext=[
                        'Off Day', 'Early', 'Early (OT)', 'Day', 'Day (OT)',
                        'Late', 'Late (OT)', 'Night', 'Night (OT)'
                    ]
                )
            )
        
        fig_heatmap.update_layout(
            height=max(400, len(nurses_list or []) * 20),
            font=dict(size=12),
            title_font_size=16,
            plot_bgcolor='white',
            paper_bgcolor='white',
            coloraxis=dict(
                colorbar=dict(
                    title="Shift",
                    thickness=15,
                    len=0.7
                )
            )
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Download heatmap as image (optional - requires kaleido package)
        try:
            img_bytes = fig_heatmap.to_image(format="png", width=1400, height=max(600, len(nurses_list or []) * 25))
            st.download_button(
                "⬇️ Download Heatmap (PNG Image)",
                img_bytes,
                "nurse_schedule_heatmap.png",
                "image/png",
                use_container_width=True
            )
        except (ValueError, ImportError):
            # Silently skip if kaleido is not installed
            st.write("")
    
    # ===== TAB 2: COST ANALYSIS =====
    with tabs[1]:
        st.header("💵 Detailed Cost Breakdown")
        
        cost = results['cost_breakdown']
        
        # Add overtime vs emergency usage insight box
        total_overtime = cost['total_overtime_shifts']
        total_emergency = sum(results['scenario_df']['shortage_shifts'])
        
        if total_emergency > 0 and total_overtime == 0:
            num_nurses = len(results.get('roster_df', []))
            baseline_demand = cost.get('total_regular_shifts', 0)
            max_regular = num_nurses * model_params.get('n1', 15)
            
            if baseline_demand < max_regular * 0.8:
                st.info(f"""
                ℹ️ **No overtime needed - regular shifts sufficient**
                
                Baseline demand ({baseline_demand:.0f} shifts) is low enough to be covered by regular shifts alone.
                Emergency staff ({total_emergency:.0f} shifts) handles excess demand in high-demand scenarios.
                
                **Why no overtime?** Overtime (${model_params.get('c2', 150)}) is more expensive than regular (${model_params.get('c1', 100)}), so the model only uses 
                it when forced by capacity constraints.
                
                **To see overtime in action:** Increase baseline demand or reduce available nurses.
                """)
            else:
                st.warning(f"""
                ⚠️ **No overtime used, all extra demand handled by emergency staff!**
                
                Your current settings forced the model to use expensive emergency staff ({total_emergency:.0f} shifts) 
                instead of planned overtime.
                
                **Why?** Constraint $n_3$ (min regular shifts) = {model_params.get('n3', 'N/A')} may be limiting 
                overtime flexibility.
                
                **To enable overtime:** Try reducing $n_3$ or increasing baseline demand.
                """)
        elif total_overtime > 0 and total_emergency > 0:
            overtime_pct = total_overtime / (total_overtime + total_emergency) * 100
            st.info(f"""
            ℹ️ **Mix of overtime and emergency staff used**
            - Planned overtime: {total_overtime:.0f} shifts ({overtime_pct:.1f}%)
            - Emergency staff: {total_emergency:.0f} shifts ({100-overtime_pct:.1f}%)
            """)
        elif total_overtime > 0:
            st.success(f"""
            ✅ **Overtime effectively utilized!**
            - Planned overtime: {total_overtime:.0f} shifts
            - No emergency staff needed
            """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Stage 1: Baseline Costs")
            st.metric("Regular Shift Costs", f"${cost['stage1_regular_cost']:,.0f}")
            st.metric("Overtime Shift Costs", f"${cost['stage1_overtime_cost']:,.0f}")
            st.metric("Stage 1 Total", f"${cost['stage1_total']:,.0f}")
        
        with col2:
            st.subheader("Stage 2: Recourse Costs")
            st.metric("Expected Recourse Cost", f"${cost['stage2_expected_cost']:,.0f}")
            st.metric("Cost per Nurse", f"${cost['avg_cost_per_nurse']:,.0f}")
            st.metric("Grand Total", f"${cost['total_cost']:,.0f}")
        
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
        
        # Calculate Average Emergency Staffing (Mean across scenarios)
        scenario_df = results['scenario_df']
        avg_emergency = scenario_df['shortage_shifts'].mean() if not scenario_df.empty else 0
        
        shift_data = pd.DataFrame({
            'Category': ['Regular', 'Overtime', 'Emergency (Avg)'],
            'Count': [
                cost['total_regular_shifts'], 
                cost['total_overtime_shifts'],
                avg_emergency
            ],
            'Color': ['#6366F1', '#818CF8', '#EF4444'] # Indigo, Indigo-Light, Red-Rose
        })
        
        # Professional Horizontal Bar Chart
        fig_bar = px.bar(
            shift_data,
            y='Category',
            x='Count',
            orientation='h',
            text='Count',
            color='Category',
            color_discrete_map={
                'Regular': '#6366F1',
                'Overtime': '#A5B4FC',
                'Emergency (Avg)': '#F87171'
            },
            template='plotly_white'
        )
        
        fig_bar.update_traces(
            texttemplate='<b>%{text:.1f}</b> Shifts', 
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Count: %{x:.1f} shifts<extra></extra>',
            marker_line_width=0,
            width=0.6 # Adjust bar thickness
        )
        
        fig_bar.update_layout(
            title={
                'text': "<b>Staffing Mix Distribution</b>",
                'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top',
                'font': {'size': 20, 'color': '#1E293B'}
            },
            bargap=0.15,
            height=350,
            showlegend=False,
            xaxis_visible=False, # Hide x-axis as we have text labels
            yaxis_title="",
            yaxis_autorange="reversed", # Keep Regular on top
            margin=dict(l=20, r=80, t=60, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif", size=14, color="#475569")
        )
        
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    
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
        **Total Nurses:** {len(nurses_list) if nurses_list else 0}  
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
        
        # Generate comprehensive downloadable PDF report
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        
        pdf_buffer = BytesIO()
        # Narrow margins: 0.5 inch on all sides
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, 
                               rightMargin=0.5*inch, leftMargin=0.5*inch, 
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for PDF elements
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=12,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=6,
            spaceBefore=12
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=6,
            spaceBefore=8
        )
        
        # Title
        story.append(Paragraph("NURSE SCHEDULING OPTIMIZATION REPORT", title_style))
        story.append(Paragraph(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        summary_data = [
            ['Model Type:', results['risk_metrics']['model_type']],
            ['Total Nurses:', str(len(nurses_list) if nurses_list else 0)],
            ['Planning Period:', f"{len(results['coverage_df']['day'].unique())} days"],
            ['Demand Scenarios:', str(results['risk_metrics']['num_scenarios'])]
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Financial Summary
        story.append(Paragraph("FINANCIAL SUMMARY", heading_style))
        financial_data = [
            ['Total Cost:', f"${results['cost_breakdown']['total_cost']:,.2f}"],
            ['Stage 1 Cost:', f"${results['cost_breakdown']['stage1_total']:,.2f}"],
            ['  Regular Wages:', f"${results['cost_breakdown']['stage1_regular_cost']:,.2f}"],
            ['  Overtime Wages:', f"${results['cost_breakdown']['stage1_overtime_cost']:,.2f}"],
            ['Stage 2 Recourse:', f"${results['cost_breakdown']['stage2_expected_cost']:,.2f}"],
            ['Cost per Nurse:', f"${results['cost_breakdown']['avg_cost_per_nurse']:,.2f}"]
        ]
        financial_table = Table(financial_data, colWidths=[2*inch, 2.5*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e6f2ff')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(financial_table)
        story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.15*inch))
        
        # Staffing Summary
        story.append(Paragraph("STAFFING SUMMARY", heading_style))
        staffing_data = [
            ['Regular Shifts:', str(int(results['cost_breakdown']['total_regular_shifts']))],
            ['Overtime Shifts:', str(int(results['cost_breakdown']['total_overtime_shifts']))],
            ['Total Shifts:', str(int(results['cost_breakdown']['total_regular_shifts'] + results['cost_breakdown']['total_overtime_shifts']))]
        ]
        staffing_table = Table(staffing_data, colWidths=[2*inch, 2.5*inch])
        staffing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(staffing_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Risk Summary
        story.append(Paragraph("RISK SUMMARY", heading_style))
        risk_data = [
            ['Average Shortage:', f"{results['scenario_df']['shortage_shifts'].mean():.2f} shifts"],
            ['Maximum Shortage:', f"{results['scenario_df']['shortage_shifts'].max():.0f} shifts"],
            ['Std Deviation:', f"{results['scenario_df']['shortage_shifts'].std():.2f}"]
        ]
        risk_table = Table(risk_data, colWidths=[2*inch, 2.5*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(risk_table)
        story.append(PageBreak())
        
        # NURSE ROSTER - Full schedule
        story.append(Paragraph("COMPLETE NURSE ROSTER", heading_style))
        roster_df = results['roster_df']
        
        # Prepare roster data for PDF (Split into Schedule and Summary)
        
        # 1. Daily Schedule Table
        day_cols = [col for col in roster_df.columns if col.startswith("D")]
        schedule_cols = ['Nurse'] + day_cols
        schedule_view = roster_df[schedule_cols]
        
        schedule_data = [schedule_view.columns.tolist()]  # Header
        for _, row in schedule_view.iterrows():
            schedule_data.append(row.tolist())
        
        # Determine column widths for schedule
        num_sched_cols = len(schedule_cols)
        available_width = 7.5 * inch
        # Nurse column wider, days narrower
        nurse_col_width = 1.0 * inch
        day_col_width = (available_width - nurse_col_width) / (num_sched_cols - 1)
        sched_col_widths = [nurse_col_width] + [day_col_width] * (num_sched_cols - 1)
        
        roster_table = Table(schedule_data, colWidths=sched_col_widths, repeatRows=1)
        roster_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 6),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 5),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(roster_table)
        story.append(Spacer(1, 0.2*inch))
        
        # 2. Summary Metrics Table
        story.append(Paragraph("WORKLOAD SUMMARY", heading_style))
        summary_cols = ['Nurse', 'Total_Regular', 'Total_Overtime', 'Total_Nights', 'Total_Shifts']
        summary_view = roster_df[summary_cols]
        
        summary_data_list = [summary_view.columns.tolist()]
        for _, row in summary_view.iterrows():
            summary_data_list.append(row.tolist())
            
        summary_col_widths = [1.5*inch] + [1.2*inch] * (len(summary_cols) - 1)
        
        metrics_table = Table(summary_data_list, colWidths=summary_col_widths, repeatRows=1)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')])
        ]))
        story.append(metrics_table)
        story.append(PageBreak())
        
        # COVERAGE ANALYSIS
        story.append(Paragraph("COVERAGE ANALYSIS BY DAY AND SHIFT", heading_style))
        coverage_df = results['coverage_df']
        
        # Pivot coverage data for better display
        coverage_pivot = coverage_df.pivot(index='day', columns='shift', values='assigned_nurses')
        coverage_pivot = coverage_pivot.reset_index()
        
        # Prepare coverage data
        coverage_data = [coverage_pivot.columns.tolist()]
        for _, row in coverage_pivot.iterrows():
            coverage_data.append(row.tolist())
        
        coverage_col_widths = [0.8*inch] + [1.2*inch] * (len(coverage_pivot.columns) - 1)
        coverage_table = Table(coverage_data, colWidths=coverage_col_widths, repeatRows=1)
        coverage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(coverage_table)
        story.append(Spacer(1, 0.2*inch))
        
        # SCENARIO ANALYSIS
        story.append(Paragraph("SCENARIO-BY-SCENARIO ANALYSIS", heading_style))
        scenario_df = results['scenario_df']
        
        scenario_data = [['Scenario', 'Shortage Shifts', 'Overage Shifts', 'Recourse Cost']]
        for _, row in scenario_df.iterrows():
            scenario_data.append([
                str(row['scenario']),
                f"{row['shortage_shifts']:.2f}",
                f"{row['overage_shifts']:.2f}",
                f"${row['recourse_cost']:.2f}"
            ])
        
        scenario_table = Table(scenario_data, colWidths=[1.2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        scenario_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(scenario_table)
        
        # Build PDF
        doc.build(story)
        
        st.download_button(
            "⬇️ Download Complete Report (PDF)",
            pdf_buffer.getvalue(),
            "nurse_scheduling_complete_report.pdf",
            "application/pdf",
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