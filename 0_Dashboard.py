"""main.py - Entry point for the Nurse Scheduling System (NSS)
Run with: streamlit run main.py
"""

from __future__ import annotations

import streamlit as st
import base64
import os

from core.model import create_model
from core.scheduler import ResultExtractor
from core.validator import ParameterValidator
from ui.results_view import render_results
from ui.sidebar import render_sidebar
from ui.upload_view import render_upload_section



def get_base64_image(image_path: str) -> str:
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

def render_hero_banner():
    hero_bg_base64 = get_base64_image("assets/banner.png")
    if hero_bg_base64:
        st.markdown(f'''
        <style>
            .hero-wrapper {{
                background-image: url("data:image/png;base64,{hero_bg_base64}");
                background-size: cover;
                background-position: center;
                border-radius: 16px;
                padding: 4rem 2rem;
                margin-bottom: 2rem;
                position: relative;
                overflow: hidden;
                text-align: center;
            }}
            .hero-overlay {{
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(15, 23, 42, 0.45);
                backdrop-filter: blur(4px);
            }}
            .hero-content {{
                position: relative;
                z-index: 1;
            }}
            .hero-title {{
                font-size: 3.5rem !important;
                font-weight: 800 !important;
                color: white !important;
                margin-bottom: 0.5rem !important;
            }}
            .hero-subtitle {{
                font-size: 1.25rem;
                color: #f8fafc;
                font-weight: 500;
                letter-spacing: 0.1em;
                text-transform: uppercase;
            }}
        </style>
        <div class="hero-wrapper">
            <div class="hero-overlay"></div>
            <div class="hero-content">
                <h1 class="hero-title">NURSE SCHEDULER</h1>
                <div class="hero-subtitle">Optimize • Analyze • Manage</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

def main() -> None:
    """Run the Streamlit application."""
    st.set_page_config(page_title="Nurse Scheduling System", page_icon="", layout="wide")
    render_hero_banner()

    params = render_sidebar()
    nurses_list, scenarios_df = render_upload_section()

    st.session_state.setdefault("results", None)
    st.session_state.setdefault("model_params", None)
    st.session_state.setdefault("nurses_list", nurses_list)
    st.session_state.setdefault("scenarios_df", scenarios_df)
    st.session_state.setdefault("validation_errors", [])
    st.session_state.setdefault("validation_warnings", [])

    if st.session_state.validation_errors:
        for error in st.session_state.validation_errors:
            st.error(error)
        if st.session_state.validation_warnings:
            for warning in st.session_state.validation_warnings:
                st.warning(warning)

    if st.button("▶ Optimize Schedule", type="primary", use_container_width=True):
        # Clear previous validation messages
        st.session_state.validation_errors = []
        st.session_state.validation_warnings = []

        if nurses_list is None or scenarios_df is None:
            st.warning("Please load nurse and scenario data first.")
        else:
            validator = ParameterValidator(strict_mode=False)
            validation = validator.validate_inputs(params, nurses_list, scenarios_df, verbose=False)

            if not validation.is_valid:
                st.session_state.validation_errors = validation.errors
                st.session_state.validation_warnings = validation.warnings
            else:
                final_params = validation.sanitized_params or params
                model_type = final_params.get("model_type", "SDM")
                solver_name = final_params.get("solver_name", "AUTO")
                
                # Collapse scenarios for Deterministic baseline
                run_scenarios_df = scenarios_df.copy()
                if model_type == "Deterministic" and not run_scenarios_df.empty:
                    mean_df = run_scenarios_df.groupby(['day', 'shift', 'skill'])['demand'].mean().reset_index()
                    mean_df['demand'] = mean_df['demand'].round().astype(int)
                    run_scenarios_df = mean_df


                progress_placeholder = st.empty()
                with progress_placeholder.container():
                    gif_html = ""
                    try:
                        with open("assets/loading.gif", "rb") as f:
                            gif_bytes = f.read()
                        gif_base64 = base64.b64encode(gif_bytes).decode("utf-8")
                        gif_html = f'<img src="data:image/gif;base64,{gif_base64}" alt="loading" width="150">'
                    except Exception:
                        gif_html = '<div style="font-size: 5rem;">⌛</div>'
                    
                    st.markdown(f'''
                    <div style="background: #667eea; border-radius: 16px; padding: 2rem; margin: 2rem 0; display: flex; align-items: center;">
                        <div style="flex: 1; text-align: center; padding-right: 1rem;">
                            {gif_html}
                        </div>
                        <div style="flex: 2; color: white;">
                            <h3 style="margin-top: 0; color: white;">Optimizing Schedule...</h3>
                            <p style="opacity: 0.9; margin-bottom: 0;">This may take a few moments depending on the problem size and solver selected.</p>
                            <p style="color: #ffcccc; font-weight: bold; margin-top: 10px;">⚠️ To Stop Solving at any time, click the 'Stop' button in the top right corner of the screen.</p>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                try:
                    model = create_model(
                        final_params,
                        nurses_list,
                        scenarios_df,
                        model_type=model_type,
                        solver_name=solver_name,
                        nurses_df=st.session_state.get('nurses_df')
                    )
                    model.build()
                    solve_result = model.solve()
                    extractor = ResultExtractor(model, solve_result)
                    results = extractor.extract()
                    
                    st.session_state.results = results
                    st.session_state.model_params = final_params
                    st.session_state.nurses_list = nurses_list
                    st.session_state.scenarios_df = scenarios_df
                except Exception as e:
                    error_str = str(e)
                    if "size-limited license" in error_str or "Model too large" in error_str:
                        st.error("🚨 **License Restriction Error!**")
                        st.error("You are using Gurobi with a restricted free license, which limits the problem size. Your dataset is too large for this license.")
                        st.info("💡 **FIX:** Open the **Solver Configuration** section in the sidebar and manually select **HiGHS (Open-source)** instead. HiGHS is completely free and has no size restrictions!")
                    else:
                        st.error(f"🚨 **Optimization failed:** {error_str}")
                        st.exception(e)
                finally:
                    progress_placeholder.empty()

    render_results(
        st.session_state.get("results"),
        st.session_state.get("model_params", params),
        st.session_state.get("nurses_list") or [],
        st.session_state.get("scenarios_df"),
    )


if __name__ == "__main__":
    main()
