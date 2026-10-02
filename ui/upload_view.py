"""Data upload and sample data UI for the NSS Streamlit app."""

from __future__ import annotations

from io import StringIO
from itertools import product
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st

from core.data_generator import generate_sample_data


def _parse_nurse_file_and_df(nurse_file) -> Tuple[List[str], pd.DataFrame]:
    """Parse uploaded nurse data into a DataFrame, preserving heterogeneous attributes."""
    nurses_df = pd.DataFrame()

    try:
        try:
            nurse_file.seek(0)
        except Exception:
            pass

        try:
            nurses_df = pd.read_csv(nurse_file)
            if nurses_df.shape[1] == 1:
                nurses_df = pd.DataFrame({"nurse_id": nurses_df.iloc[:, 0].astype(str)})
            elif 'nurse_id' not in nurses_df.columns and 'nurse' in nurses_df.columns:
                nurses_df = nurses_df.rename(columns={'nurse': 'nurse_id'})
            elif 'nurse_id' not in nurses_df.columns:
                nurses_df = nurses_df.rename(columns={nurses_df.columns[0]: 'nurse_id'})
        except pd.errors.EmptyDataError:
            raise
    except pd.errors.EmptyDataError:
        pass
    except Exception:
        pass

    if nurses_df.empty:
        try:
            try:
                nurse_file.seek(0)
            except Exception:
                pass

            if hasattr(nurse_file, "getvalue"):
                raw = nurse_file.getvalue()
            else:
                raw = nurse_file.read()

            if isinstance(raw, (bytes, bytearray)):
                text = raw.decode("utf-8", errors="ignore")
            else:
                text = str(raw)

            text = text.strip()
            if not text:
                nurses_df = pd.DataFrame()
            elif "\n" not in text and "," in text:
                nurses_list = [segment.strip() for segment in text.split(",") if segment.strip()]
                nurses_df = pd.DataFrame({"nurse_id": nurses_list})
            else:
                reader = pd.read_csv(StringIO(text))
                if reader.shape[1] == 1:
                    nurses_df = pd.DataFrame({"nurse_id": reader.iloc[:, 0].astype(str)})
                elif 'nurse_id' not in reader.columns and 'nurse' in reader.columns:
                    nurses_df = reader.rename(columns={'nurse': 'nurse_id'})
                elif 'nurse_id' not in reader.columns:
                    nurses_df = reader.rename(columns={reader.columns[0]: 'nurse_id'})
        except Exception as e:
            st.error(f"Failed to parse nurse file: {e}")
            st.stop()

    if not nurses_df.empty:
        nurses_df['nurse_id'] = nurses_df['nurse_id'].astype(str).str.strip()
        nurses_df = nurses_df[nurses_df['nurse_id'] != ""]
        nurses_list = nurses_df['nurse_id'].tolist()
    else:
        nurses_list = []
        
    return nurses_list, nurses_df


def _load_and_validate_scenarios(scenario_file) -> pd.DataFrame:
    """Load and validate the scenario file."""
    scenarios_df = pd.read_csv(scenario_file)

    required_cols = ["scenario", "day", "shift", "demand"]
    missing_cols = [col for col in required_cols if col not in scenarios_df.columns]
    if missing_cols:
        st.error(f"Scenario file missing required columns: {missing_cols}")
        st.error(f"**Required columns:** {required_cols}")
        st.error(f"**Found columns:** {list(scenarios_df.columns)}")
        st.stop()

    if len(scenarios_df) == 0:
        st.error("Scenario file is empty!")
        st.stop()

    if scenarios_df.isnull().any().any():
        null_counts = scenarios_df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        st.error("Scenario file contains missing values:")
        for col, count in null_cols.items():
            st.error(f"   - {col}: {count} missing values")
        st.stop()

    if (scenarios_df["demand"] < 0).any():
        negative_rows = scenarios_df[scenarios_df["demand"] < 0]
        st.error(f"Found {len(negative_rows)} rows with negative demand!")
        st.dataframe(negative_rows.head())
        st.stop()

    num_scenarios = len(scenarios_df["scenario"].unique())
    num_days = len(scenarios_df["day"].unique())
    num_shifts = len(scenarios_df["shift"].unique())
    expected_rows = num_scenarios * num_days * num_shifts
    actual_rows = len(scenarios_df)

    if actual_rows != expected_rows:
        st.warning("**Data completeness check:**")
        st.warning(f"   - Expected rows: {expected_rows} ({num_scenarios} scenarios × {num_days} days × {num_shifts} shifts)")
        st.warning(f"   - Actual rows: {actual_rows}")
        st.warning(f"   - Missing or extra: {abs(expected_rows - actual_rows)} rows")

        if actual_rows < expected_rows:
            st.error("Data appears incomplete! Some scenario/day/shift combinations are missing.")
            all_combos = set(product(scenarios_df["scenario"].unique(), scenarios_df["day"].unique(), scenarios_df["shift"].unique()))
            actual_combos = set(scenarios_df[["scenario", "day", "shift"]].itertuples(index=False, name=None))
            missing = all_combos - actual_combos

            if len(missing) <= 10:
                st.error(f"**Missing combinations:** {missing}")
            else:
                st.error(f"**{len(missing)} combinations are missing** (showing first 10):")
                st.error(str(list(missing)[:10]))

    st.success(f"Loaded {len(scenarios_df)} demand records")
    st.info(f"   Data structure: {num_scenarios} scenarios × {num_days} days × {num_shifts} shifts")
    return scenarios_df


def render_upload_section() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Render the data source section and return loaded nurses and scenarios."""
    nurses_list: Optional[List[str]] = None
    scenarios_df: Optional[pd.DataFrame] = None

    st.header("Data Source")
    data_source = st.radio(
        "Choose data input method:",
        ["Use Sample Data (Quick Start)", "Upload Custom Data"],
        help="Sample data provides a pre-configured example. Upload for real scenarios.",
    )

    if data_source == "Use Sample Data (Quick Start)":
        st.success("Using sample data")

        col1, col2 = st.columns(2)
        with col1:
            num_nurses = st.number_input("Number of Nurses", 1, 200, 10, 1)
        with col2:
            num_days = st.number_input("Planning Days", 1, 90, 14, 1)

        num_scenarios = st.number_input(
            "Demand Scenarios",
            1,
            300,
            st.session_state.get("num_scenarios", 5),
            1,
        )
        
        use_seed = st.checkbox("Lock Random Seed (For Reproducibility)", value=True)
        if use_seed:
            seed = st.number_input(
                "Seed Number",
                0,
                999999,
                42,
                help="Generates the exact same random data every time.",
            )
        else:
            seed = None

        if st.button("🎲 Generate Sample Data", type="primary", use_container_width=True):
            nurses_list, scenarios_df, nurses_df = generate_sample_data(num_nurses, num_days, num_scenarios, seed=seed)
            st.session_state.nurses_list = nurses_list
            st.session_state.scenarios_df = scenarios_df
            st.session_state.nurses_df = nurses_df
            st.session_state.num_scenarios = num_scenarios
            st.session_state.validation_errors = []
            st.session_state.validation_warnings = []
            st.success(f"Generated {len(nurses_list)} nurses with {len(scenarios_df)} demand records!")

        if "nurses_list" in st.session_state:
            nurses_list = st.session_state.nurses_list
            scenarios_df = st.session_state.scenarios_df

    else:
        st.subheader("📁 Upload Files")
        nurse_file = st.file_uploader(
            "Nurse List (CSV/TXT)",
            type=["csv", "txt"],
            help="One nurse name per line",
        )
        scenario_file = st.file_uploader(
            "Demand Scenarios (CSV)",
            type=["csv"],
            help="Columns: scenario, day, shift, demand",
        )

        if nurse_file and scenario_file:
            try:
                # Clear previous validation
                st.session_state.validation_errors = []
                st.session_state.validation_warnings = []
                
                nurses_list, nurses_df = _parse_nurse_file_and_df(nurse_file)
                st.session_state.nurses_df = nurses_df

                if len(nurses_list) == 0:
                    st.error("Nurse file is empty or could not be parsed. Ensure it contains one name per line or a comma-separated list.")
                    st.stop()

                duplicates = [name for name in set(nurses_list) if nurses_list.count(name) > 1]
                if duplicates:
                    st.warning(f"Duplicate nurse names found: {set(duplicates)}")
                    st.info("Automatically removing duplicates (keeping first occurrence)")
                    seen = set()
                    nurses_list = [x for x in nurses_list if not (x in seen or seen.add(x))]
                    st.success(f"Cleaned to {len(nurses_list)} unique nurses")

                st.success(f"Loaded {len(nurses_list)} nurses")
                scenarios_df = _load_and_validate_scenarios(scenario_file)

                st.session_state.nurses_list = nurses_list
                st.session_state.scenarios_df = scenarios_df
                st.session_state.nurses_df = nurses_df

            except Exception as e:
                st.error(f"Error loading files: {e}")
                st.exception(e)
                st.stop()

    return nurses_list, scenarios_df
